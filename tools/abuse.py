"""What handling does to ONE-135: shaking, drops, a warped back, weak layers, wear, creep.  Estimates from the meshes, the finite-element cases (tools/fea_cases.py at four wall
errors) and the end cases (tools/endcases.py).  Nothing here is measured.  Writes build/abuse.json."""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "tools"); import fea
from scadr import values
A = "build/asm/"; LY = json.load(open("build/layout.json")); B = LY["B"]; TH = B["THETA"]; RHO = 1.24e-3; G = 9.81; out = {}
EC = json.load(open("build/endcases.json")); PR = list(EC["shutter"].keys()); L = lambda n: trimesh.load(A + n + ".stl", process=True)
MV = values(["H_RHO", "F_T", "F_X1", "NUB_X0", "NUB_X1", "RIB_X0", "RIB_H", "HORN_GAP", "LAP_IN"])
# ---------------------------------------------------------------- 1. shaking
def unbalance(m, pivot):
    c = m.center_mass; return m.volume * RHO * np.hypot(c[0] - pivot[0], c[2] - pivot[1])            # g mm about an axis along y
bl = L("blade_PHI0.0"); wh = L("wheel_STOP0"); ub, uw = unbalance(bl, B["P_S"]), unbalance(wh, B["c"]); fr = L("front")
plate_g = (fr.volume + bl.volume + wh.volume) * RHO * 0.92 + 2.0                                      # printed 8 % lighter than solid; the lens is about 2 g
print("1. SHAKING: what holds against it, in g (1 g = the part's own weight)")
print("   shutter blade %.2f g, off balance by %.1f g mm; aperture wheel %.2f g, %.1f g mm; front plate with all it carries %.0f g" % (bl.volume * RHO, ub, wh.volume * RHO, uw, plate_g))
out["shake"] = {}
for p in PR:
    s, w, pl = EC["shutter"][p], EC["wheel"][p], EC["plate"][p]
    gs = [h / (ub * 1e-3 * G) for h in s["hold_at_rest_Nmm"]]; gw = [t * MV["H_RHO"] / (uw * 1e-3 * G) for t in w["turn_N"]]; gp = [h / (plate_g * 1e-3 * G) for h in pl["hold_N"]]
    out["shake"][p] = dict(shutter_g=gs, wheel_g=gw, plate_g=gp)
    print("   %-9s shutter stays shut up to %4.1f .. %5.1f g; the aperture wheel stays put up to %4.1f .. %5.1f g; the front plate stays on up to %4.1f .. %5.1f g" % (p, gs[0], gs[2], gw[0], gw[2], gp[0], gp[2]))
print("   for scale: turning the camera over is 1 g; walking with it on a strap 2 to 3 g; putting it down on a table 5 to 20 g; a fall of 1 m onto a hard floor several hundred g")
# ---------------------------------------------------------------- 2. drops: what touches the floor first, and what the fall does to the two covers
parts = {n: L(n) for n in ("body", "back", "front", "roller", "knob", "spool", "wheel_STOP1")}; blades = {s_: L(f"blade_PHI{s_ * TH}") for s_ in (1, -1)}
HH = B["H"]; rng = np.random.default_rng(3); d = rng.normal(size=(20000, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
bv, kv, fv = parts["body"].vertices, parts["back"].vertices, parts["front"].vertices
grp = {"body": bv[bv[:, 1] >= -3.3], "back": kv[np.abs(kv[:, 2]) <= HH + 0.3], "front plate": fv[fv[:, 2] <= HH + 0.3],
       "frame dial": parts["roller"].vertices, "wind knob": parts["knob"].vertices, "take-up knob": parts["spool"].vertices, "aperture handle": parts["wheel_STOP1"].vertices,
       "latch pads of the back": kv[np.abs(kv[:, 2]) > HH + 0.3], "catch for the back (posts, bar, tab)": bv[bv[:, 1] < -3.3], "guard on the front plate": fv[fv[:, 2] > HH + 0.3]}
grp = {k: v for k, v in grp.items() if len(v)}; BIG = ("body", "back", "front plate"); hs = {k: (d @ v.T).max(1) for k, v in grp.items()}
hr = {s_: (d @ blades[s_].vertices.T).max(1) for s_ in blades}                                           # the rocker, at rest on either side
print("\n2. DROPS: which part meets a flat floor first, over 20 000 directions of fall (closed camera)")
out["drop"] = {}
def first_share(h_this, others):
    pr = h_this - np.max(others, 0); sel = pr > 0.02; return 100 * float(sel.mean()), (float(pr.max()) if sel.any() else 0.0)
for k in grp:
    if k in BIG: continue
    sh, pr = first_share(hs[k], [hs[j_] for j_ in grp if j_ != k] + [np.maximum(hr[1], hr[-1])]); out["drop"][k] = dict(share_pct=sh, stands_proud_mm=pr)
    print("   %-38s first in %4.1f %% of directions; stands up to %4.1f mm proud of everything else" % (k, sh, pr))
rk = [first_share(hr[s_], list(hs.values())) for s_ in blades]; out["drop"]["shutter rocker"] = dict(share_pct=float(np.mean([q[0] for q in rk])), stands_proud_mm=max(q[1] for q in rk))
print("   %-38s first in %4.1f %% of directions; stands up to %4.1f mm proud of everything else" % ("shutter rocker", out["drop"]["shutter rocker"]["share_pct"], out["drop"]["shutter rocker"]["stands_proud_mm"]))
hall = np.max(list(hs.values()) + [np.maximum(hr[1], hr[-1])], 0); box_first = float((np.max([hs[k] for k in BIG], 0) >= hall - 0.02).mean()); out["drop"]["the three big parts"] = dict(share_pct=100 * box_first)
print("   %-38s first in %4.1f %% of directions" % ("body, back or front plate", 100 * box_first))
mass = 0.1164 + 0.030; print("   camera loaded: about %.0f g; a fall of 1 m is %.2f J, of 0.5 m %.2f J.  A small part that lands first can take a few thousandths of that before it breaks" % (mass * 1000, mass * G * 1.0, mass * G * 0.5))
# lying on its top: the plane a table makes, and what touches it.  The camera settles on the face of its hull that lies under its centre of gravity
allv = np.vstack(list(grp.values())); cg = np.average([parts[n].center_mass for n in ("body", "back", "front")], axis=0, weights=[parts[n].volume for n in ("body", "back", "front")])
out["on_its_top"] = {}
for s_ in blades:
    V = np.vstack([allv, blades[s_].vertices]); hull = trimesh.convex.convex_hull(V); N, O = hull.face_normals, hull.triangles[:, 0]; best = None
    for fi in np.where(N[:, 2] > 0.6)[0]:
        t = hull.triangles[fi]; n = N[fi]; q = cg + n * ((t[0] - cg) @ n)                                 # the centre of gravity dropped onto this face's plane
        b0 = np.cross(t[1] - t[0], q - t[0]) @ n; b1 = np.cross(t[2] - t[1], q - t[1]) @ n; b2 = np.cross(t[0] - t[2], q - t[2]) @ n
        if min(b0, b1, b2) >= -1e-6 and (best is None or n[2] > N[best][2]): best = fi
    n = N[best]; off = hull.triangles[best][0] @ n; touch = [k for k, v in grp.items() if ((v @ n).max() > off - 0.03)]; clear = off - (blades[s_].vertices @ n).max()
    out["on_its_top"]["rocker up on the %s" % ("left" if s_ > 0 else "right")] = dict(rests_on=touch, tilt_deg=float(np.degrees(np.arccos(n[2]))), rocker_clear_mm=float(clear))
    print("   laid on its top (rocker's %s side up): it rests on %s, tilted %.1f degrees; the rocker is %.2f mm clear of the table" % ("left" if s_ > 0 else "right", ", ".join(touch), np.degrees(np.arccos(n[2])), clear) if clear > 0.02 else
          "   laid on its top (rocker's %s side up): it rests on %s and ON THE ROCKER" % ("left" if s_ > 0 else "right", ", ".join(touch)))
# the covers in a fall.  Whatever lands first stops; a cover that is not what landed keeps going until its latch or the floor stops it.
# Back: comes off toward -y, held by two fingers that bend front to back (KYs N/mm each, after SLACK mm).  Plate with shutter, wheel and lens: slides off toward +z after SLIDE mm,
# held by its latch (the work to push it over the bump is taken from the end cases).  The rest of the cover's momentum presses it against the body and rubs: friction MU_F.
SL = json.load(open("build/slicecheck.json")); m_back = SL["back"]["grams"] / 1000; m_plate = (SL["front"]["grams"] + SL["blade"]["grams"] + SL["wheel"]["grams"] + 2.0) / 1000
FJ = json.load(open("build/fea_finger.json")); KYs, EPS_N = FJ["sideways_N_per_mm"], FJ["sideways_strain_pct_per_N"]                # the finger bent front to back: N per mm, and % strain per newton
SLACK = MV["HORN_GAP"]; SLIDE = values(["SLIDE"])["SLIDE"]; h_back = (d @ kv.T).max(1); h_plate = np.maximum((d @ fv.T).max(1), np.maximum(hr[1], hr[-1])); out["covers"] = {}; MU_F = 0.3
print("\n   THE BACK IN A FALL (the body is taken to stop dead; friction %.1f where the cover rubs)" % MU_F)
for Hd in (0.1, 0.3, 0.5, 1.0):
    v = np.sqrt(2 * G * Hd); c = -d[:, 1]; vs = v * np.maximum(c - MU_F * (np.abs(d[:, 0]) + np.abs(d[:, 2])), 0)                         # speed of the back toward the rear once friction has had its share
    thrown = (hall - h_back > 0.02) & (vs > 0); room = np.where(thrown, (hall - h_back) / np.maximum(c, 1e-9), 0.0)                       # how far the back can go before the floor meets it
    E = 0.5 * m_back * vs ** 2 * 1000; x_spring = SLACK + np.sqrt(E / KYs); x = np.where(thrown, np.minimum(room, x_spring), 0.0); eps = np.maximum(x - SLACK, 0) * KYs * EPS_N
    r_ = dict(leaves_its_seat_over_0_6_mm_pct=100 * float((x > 0.6).mean()), past_the_light_trap_pct=100 * float((x > MV["LAP_IN"]).mean()), fingers_over_1_pct=100 * float((eps > 1.0).mean()), fingers_over_1_7_pct=100 * float((eps > 1.7).mean()), worst_strain_pct=float(eps.max()), worst_travel_mm=float(x.max()))
    out["covers"]["%.1f m" % Hd] = r_
    print("   fall of %.1f m (%.1f m/s): the back leaves its seat by more than 0.6 mm in %4.1f %% of directions, opens past its light trap in %4.1f %%; its fingers are strained past 1.0 %% in %4.1f %%, past 1.7 %% in %4.1f %% (worst %.1f %%, %.1f mm)"
          % (Hd, v, r_["leaves_its_seat_over_0_6_mm_pct"], r_["past_the_light_trap_pct"], r_["fingers_over_1_pct"], r_["fingers_over_1_7_pct"], r_["worst_strain_pct"], r_["worst_travel_mm"]))
# the front plate: followed in time by tools/platefall.py (run it first)
import os
if os.path.exists("build/platefall.json"):
    PF = json.load(open("build/platefall.json")); out["plate"] = PF; print("\n   THE FRONT PLATE IN A FALL (tools/platefall.py: %s)" % PF["note"])
    for label in [k for k in PF if k not in ("plate_g", "note", "measured")]:
        for Hd, r in PF[label].items(): print("   %-22s %s: off the camera or left loose in %s (thin slippery / typical / fat rough printer);  left pushed up, still held, in %s" % (label, Hd, " / ".join("%.1f %%" % q["off"] for q in r.values()), " / ".join("%.1f %%" % q["left_up"] for q in r.values())))
# flat on its back: the catch posts stand proud of the back, so they land and the back travels on until the floor meets it
proud = float(-bv[:, 1].min() + kv[:, 1].min()); xb = max(proud - SLACK, 0); out["covers"]["flat on its back"] = dict(catch_proud_mm=proud, finger_bent_mm=xb, strain_pct=xb * KYs * EPS_N, from_height_mm=1000 * (KYs * xb ** 2 / 1000) / (m_back * G))
print("   flat on its back: the catch stands %.1f mm proud of the back, so the back travels that far and each finger is bent %.1f mm front to back: %.2f %% strain, in any fall of more than %.0f mm"
      % (proud, xb, out["covers"]["flat on its back"]["strain_pct"], out["covers"]["flat on its back"]["from_height_mm"]))
# ---------------------------------------------------------------- 3. a warped back
print("\n3. A BACK THAT IS NOT FLAT (printed outside down, its ends curl toward the inside: they meet the rim first and the middle stands off)")
bk = parts["back"]; xs = np.arange(-50, 51, 10.0); I = []
for x in xs:
    sec = bk.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0]); p2, T = sec.to_2D() if hasattr(sec, "to_2D") else sec.to_planar(); a = sum(q.area for q in p2.polygons_full)
    pts = np.vstack([np.c_[np.array(q.exterior.coords)] for q in p2.polygons_full]); yy = (np.c_[pts, np.zeros(len(pts)), np.ones(len(pts))] @ np.linalg.inv(T).T * 0 + 0)   # (placeholder, replaced below)
    gx, gz = np.meshgrid(np.arange(-8, 14, 0.1), np.arange(-30, 30, 0.25)); P3 = np.c_[np.full(gx.size, x), gx.ravel(), gz.ravel()]; ins = bk.contains(P3); y = gx.ravel()[ins]; I.append(float(((y - y.mean()) ** 2).sum() * 0.1 * 0.25))
I = np.array(I); Lb = 126.0; Ieff = float(1 / np.mean(1 / I)); kb = 48 * fea.E_PLA * Ieff / Lb ** 3
KY = json.load(open("build/fea_finger.json"))["sideways_N_per_mm"]
print("   stiffness of the back as a beam: second moment %.0f to %.0f mm4 along it (harmonic mean %.0f): pushing its middle flat takes %.1f N per mm of bow" % (I.min(), I.max(), Ieff, kb))
out["warp"] = dict(I_mm4=I.tolist(), N_per_mm=kb, finger_N_per_mm=KY, cases={})
for bow in (0.2, 0.4, 0.6):
    f = kb * bow; stand = bow * kb / (kb + 2 * KY); fb = stand * KY; latch_free = bow * 0.93 <= MV["HORN_GAP"]
    out["warp"]["cases"][bow] = dict(press_N=f, stays_off_mm=stand, finger_sideways_N=fb, latches_without_pressing=bool(latch_free))
    print("   bow %.1f mm: %s; pressing it flat takes %.1f N; let go, the latches hold it %.2f mm off at the middle with %.1f N on each finger sideways (the light trap overlaps %.1f mm)" % (bow, "the nubs still reach their bars" if latch_free else "the nubs do NOT reach their bars until the back is pressed", f, stand + (0 if latch_free else 0), fb, MV["LAP_IN"]))
# ---------------------------------------------------------------- 4. weak layers
print("\n4. WEAK LAYERS (layers bonded half as well as assumed: every load across the layers has half its margin)")
out["weak"] = {}
for e, tag in ((0.0, "as drawn"), (-0.15, "printer 0.15 thin")):
    F = json.load(open("build/fea.json" if e == 0 else "build/fea_wall%+.2f.json" % e)); bad = sorted([(v["margin"] * 0.5, k) for k, v in F.items() if "across" in v.get("criterion", "") and "margin" in v and v["margin"] * 0.5 < 1.0 and not k.endswith("per mm") and "per 0.0" not in k])
    out["weak"][tag] = [dict(case=k, margin=m) for m, k in bad]; print("   %s: %d load cases fall under their limit:" % (tag, len(bad)))
    for m, k in bad[:9]: print("      x%.1f  %s" % (m, k[:150]))
# ---------------------------------------------------------------- 5. wear and creep
print("\n5. WEAR AND CREEP")
s0 = EC["shutter"]["exact"]; RW = B["R_OUT"] + B["SLIT"] + B["BL_T"] + B["SCL"]; path = np.radians(2 * TH) * RW; out["wear"] = {}
for kw, tag in ((1e-4, "smooth PLA on PLA"), (1e-3, "rough or dusty")):
    for p in ("exact", "0.25 fat"):
        s = EC["shutter"][p]; N = s["spring_N_per_mm"] * s["bend_on_wall_pressed"]; vol = kw * N * path * 1e-3 * 10000; depth = vol / (1.0 * 0.6)
        out["wear"][f"{tag}, {p}"] = depth; print("   click tooth of the shutter, %s, printer %s: %.2f N on the wall, %.0f mm a picture; after 10 000 pictures about %.3f mm worn off (it stands %.1f mm deep)" % (tag, p, N, path, depth, s["engagement_at_rest"] + 0))
print("   springs that stay bent at rest (they relax by about half over months; in a hot car, altogether):")
for p in PR:
    print("      %-9s shutter %.2f %% (%.2f mm), aperture wheel %.2f %%, plate leaf %.2f mm, back fingers %.2f mm" % (p, EC["shutter"][p]["strain_at_rest_pct"], EC["shutter"][p]["bend_at_rest"], EC["wheel"][p]["strain_at_rest_pct"], EC["plate"][p]["at_rest"], EC["back"][p]["bent_at_rest"]))
json.dump(out, open("build/abuse.json", "w"), indent=1, default=float)
