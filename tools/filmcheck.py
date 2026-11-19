"""What touches the film, and where.  Points are scattered over both faces of the film along its path (cassette lip -> guide ->
drum -> the turn at the frame wheel -> take-up) and the distance to every printed part is measured.  The picture is the middle 24 mm of the film's width.
Anything nearer than 0.08 mm counts as touching.  Then the turn itself: where the loaded frame wheel settles, and how far the picture stays from the film
post below it.  Writes build/filmcheck.json."""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "tools"); from scadr import values
A = "build/asm/"; LY = json.load(open("build/layout.json"))["A"]; SP = np.array(LY["spool"]); RO = np.array(LY["roller"]); GU = np.array(LY["guide"]) * [-1, 1] if LY["guide"][0] > 0 else np.array(LY["guide"])
film = trimesh.load(A + "film.stl", process=True); P, fi = trimesh.sample.sample_surface(film, 24000, seed=3); n = film.face_normals[fi]
keep = (np.abs(n[:, 2]) < 0.3) & (np.hypot(P[:, 0] - SP[0], P[:, 1] - SP[1]) > 10.6); P, n = P[keep], n[keep]            # the two faces of the strip, not its edges, not the wound roll
CF = np.array([0.0, 32.0]); lens_side = ((CF - P[:, :2]) * n[:, :2]).sum(1) > 0                                         # emulsion faces the lens
atr = np.hypot(P[:, 0] - RO[0], P[:, 1] - RO[1]) < 7.2; lens_side[atr] = (((P[atr, :2] - RO) * n[atr, :2]).sum(1) > 0)      # around the roller the emulsion is the face turned away from the roller
zone = np.where(np.abs(P[:, 2]) <= 12.2, "picture", np.where(np.abs(P[:, 2]) <= 15.6, "perforations", "edge strip"))
where = np.where(np.hypot(P[:, 0] - RO[0], P[:, 1] - RO[1]) < 7.2, "at the frame wheel", np.where(P[:, 0] > RO[0] + 2, "frame wheel to take-up", np.where(P[:, 0] < -20.5, "cassette lip and guide", "gate and drum")))
out = {}; print(f"{len(P)} points on the film")
for part in ("body", "back", "roller", "spool"):
    m = trimesh.load(A + part + ".stl", process=True); d = np.full(len(P), 9.0); near = np.all((P > m.bounds[0] - 1.0) & (P < m.bounds[1] + 1.0), axis=1); idx = np.nonzero(near)[0]
    if part == "spool": idx = idx[np.abs(P[idx, 2]) > 16.0]                       # only its flanges can touch the strip (the roll itself is left out)
    pq = trimesh.proximity.ProximityQuery(m)
    for k in range(0, len(idx), 1500): d[idx[k:k + 1500]] = pq.on_surface(P[idx[k:k + 1500]])[1]
    touch = d < 0.08; res = {}
    for side, sm in (("emulsion side", lens_side), ("base side", ~lens_side)):
        for z in ("picture", "perforations", "edge strip"):
            k = sm & (zone == z)
            if not k.any(): continue
            t = k & touch; res[f"{side}, {z}"] = dict(min_gap_mm=round(float(d[k].min()), 3), touching_pct=round(100 * float(t.sum()) / int(k.sum()), 1), where=sorted(set(where[t])))
    out[part] = res
    for k_, v in res.items():
        if v["touching_pct"] > 0 or "picture" in k_: print(f"  {part:7s} {k_:32s} nearest {v['min_gap_mm']:.2f} mm, touching {v['touching_pct']:4.1f} % {v['where'] if v['where'] else ''}")
pic = {p: {k: v for k, v in r.items() if "picture" in k} for p, r in out.items()}
out["touches_the_picture"] = [f"{p}: {k} ({', '.join(v['where'])})" for p, r in pic.items() for k, v in r.items() if v["touching_pct"] > 0]
# ------------------------------------------------------------------ the turn behind the gate
# The film solid above is drawn round the frame wheel as drawn.  In use the film pushes the wheel toward the back until its neck lies in its two bearings
# (the fork's floor below, the end of the slot in the body's top above); the film's bottom band slides on the film post, whose band is drawn where a
# typical printer's wheel settles.  Across its width the film is then a straight line from that band to the wheel's drum.
V = values(["R_ROLL", "RB_GAP", "SHAFT_R", "SHAFT_CL", "WH_Z", "RB_Z", "H", "NOSE_BAND", "NOSE_MID", "NOSE_TOP", "TOOTH", "TOOTH_Z", "SLOT_Z", "COLLAR_Z"])
c1 = V["RB_GAP"] / 2 - V["SHAFT_R"]; c2 = V["SHAFT_CL"]; a = V["RB_Z"][0] - sum(V["WH_Z"]) / 2; b = V["H"] - V["RB_Z"][0]; zb, zt = -12.6, V["WH_Z"][0]; rows = []
for lab, e in (("exact printer", 0.0), ("typical printer (walls +0.10 mm)", 0.10), ("fattest printer (+0.15 mm)", 0.15), ("thin printer (-0.08 mm)", -0.08)):
    settle = (c1 - 2 * e) + (c1 + c2 - 4 * e) * a / b; step = V["NOSE_BAND"] - settle; gap = V["NOSE_MID"] - V["NOSE_BAND"] + step * (12.0 - zb) / (zt - zb); seat = -(0.2 - e)       # the wheel stands on the post's top: drawn 0.2 above it
    rows.append(dict(printer=lab, wheel_settles_toward_the_back_mm=round(settle, 2), wheel_leans_deg=round(float(np.degrees((c1 + c2 - 4 * e) / b)), 1), drum_stands_proud_of_the_posts_band_mm=round(step, 2),
                     film_tilts_across_its_width_deg=round(float(np.degrees(abs(step) / (zt - zb))), 1), picture_to_the_posts_middle_mm=round(gap, 2), wheel_stands_mm_from_drawn=round(seat, 2),
                     tooth_to_the_edge_of_its_hole_mm=[round(V["WH_Z"][0] + seat - 12.7, 2), round(15.5 - (V["WH_Z"][0] + seat + V["TOOTH_Z"]), 2)]))
out["turn"] = rows; out["turn_note"] = ("teeth %.1f mm high and %.1f mm tall in holes 2.8 mm tall; the film itself has 0.4 mm of play up and down; the wheel can ride %.1f mm up before the ledge in the body stops it" % (V["TOOTH"], V["TOOTH_Z"], V["SLOT_Z"] - V["COLLAR_Z"][1]))
print("the turn behind the gate (the film pushes the frame wheel into its bearings; its bottom band slides on the film post):")
for r in rows: print("  %-34s wheel settles %.2f mm and leans %.1f deg; drum %+.2f mm against the post's band; picture stays %.2f mm off the post; teeth %.2f / %.2f mm inside their holes" % (r["printer"], r["wheel_settles_toward_the_back_mm"], r["wheel_leans_deg"], r["drum_stands_proud_of_the_posts_band_mm"], r["picture_to_the_posts_middle_mm"], *r["tooth_to_the_edge_of_its_hole_mm"]))
if min(r["picture_to_the_posts_middle_mm"] for r in rows) < 0.08: out["touches_the_picture"].append("back: the middle of the film post, at the turn")
print("touches the picture area:", out["touches_the_picture"] or "nothing"); json.dump(out, open("build/filmcheck.json", "w"), indent=1)
