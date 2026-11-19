"""Tool-path audit.  Reads the G-code the slicer wrote and asks what the moving nozzle does to the parts that matter:
 - seams (where each outer wall starts and stops: a small ridge) that land on a working surface, for four seam settings;
 - bridges and overhanging walls: how long;
 - layers that take too little time to cool (printed alone, and on the full plate);
 - travel moves that cross the slits behind the click springs (each one can leave a string);
 - small islands on the first layer (they can fail to stick), and tall thin parts.
Writes build/pathaudit.json and build/pathaudit.png."""
import sys, os, re, json, subprocess, numpy as np, trimesh, shapely
from shapely.geometry import LineString, Point, Polygon
sys.path.insert(0, "tools"); from slicecheck import parse, offset, LH
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = "build/slice/"; LY = json.load(open("build/layout.json")); B = LY["B"]; A_ = LY["A"]; P = np.array(B["P_S"]); C = np.array(B["c"]); TH = B["THETA"]; H = B["H"]
FLIP = dict(front=1, blade=1, body=1, wheel=-1, back=-1, roller=1, knob=-1, spool=-1)
def slice_(n, extra=(), tag=""):
    g = f"{D}audit_{n}{tag}.gcode"; stl = f"build/print/one135_{n}.stl"
    if not os.path.exists(g) or os.path.getmtime(g) < os.path.getmtime(stl): subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", "125,105", "--output", g] + list(extra), capture_output=True, timeout=3600)
    return g
def moves(g):
    x = y = z = e = 0.0; f = 1500.0; typ = "Custom"; out = []
    for ln in open(g):
        if ln.startswith(";TYPE:"): typ = ln[6:].strip(); continue
        if ln[0] == ";" or not ln.startswith(("G1", "G0", "G92")): continue
        v = {t[0]: float(t[1:]) for t in ln.split(";")[0].split()[1:] if t[0] in "XYZEF" and len(t) > 1}
        if ln.startswith("G92"): e = v.get("E", e); continue
        f = v.get("F", f); nx, ny, nz, ne = v.get("X", x), v.get("Y", y), v.get("Z", z), v.get("E", e)
        if nx != x or ny != y: out.append((round(nz, 2), typ, x, y, nx, ny, ne > e + 1e-6, f))
        x, y, z, e = nx, ny, nz, ne
    return out
def pol(c, r, a): return np.array([c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a))])
def ang(p, c): return np.degrees(np.arctan2(p[1] - c[1], p[0] - c[0])) % 360
def near_ang(a, a0, half): return abs((a - a0 + 180) % 360 - 180) <= half
R_B = B["R_OUT"] + B["SLIT"] + B["BL_T"]; R_W = B["WHEEL_R"] + B["SLIT"] + B["WH_T"]; RWB = R_B + B["SCL"]; RWW = R_W + B["SCL"]; RO = np.array(A_["roller"])
FEATURES = {      # name -> test(point in world (x, z) or (x, y), print height)
 "blade": {"click tooth": lambda p, z: np.hypot(*(p - pol(P, R_B + B["BUMP"] - 0.5, B["DB_A"]))) < 1.9, "hole in the hub": lambda p, z: np.hypot(*(p - P)) < 3.15 + 0.5,
           "spring, where it starts": lambda p, z: np.hypot(*(p - pol(P, B["R_OUT"] + 0.6, B["DB_A"] - B["BL_ARC"]))) < 2.2},
 "wheel": {"click tooth": lambda p, z: np.hypot(*(p - pol(C, R_W + B["BUMP"] - 0.5, B["WD_A0"]))) < 1.9, "hole in the hub": lambda p, z: np.hypot(*(p - C)) < 2.75 + 0.5,
           "aperture holes": lambda p, z: any(np.hypot(*(p - pol(C, B["R_HOLE"], B["A_AX"] + w))) < 2.6 for w in B["WPOS"])},
 "front": {"boss the blade turns on": lambda p, z: np.hypot(*(p - P)) < 2.75 + 0.5 and z > 2.6, "boss the wheel turns on": lambda p, z: np.hypot(*(p - C)) < 3.2 + 0.5 and z > 2.6,
           "click wall, blade": lambda p, z: abs(np.hypot(*(p - P)) - RWB) < 1.5 and near_ang(ang(p, P), B["DB_A"], TH + 4) and z > 2.6,
           "click wall, wheel": lambda p, z: abs(np.hypot(*(p - C)) - RWW) < 1.5 and near_ang(ang(p, C), B["WD_A0"] - B["WPOS"][2] / 2, B["WPOS"][2] / 2 + 5) and z > 2.6,
           "hooked feet": lambda p, z: z > 5.05},
 "roller": {"drum and teeth the film rides on": lambda p, z: np.hypot(*(p - RO)) > A_["R_ROLL"] - 0.5 and z < 2.6, "neck and collar": lambda p, z: np.hypot(*(p - RO)) < 4.3 and 2.6 < z < 9.5},
 "knob": {"shaft and collar": lambda p, z: np.hypot(*(p - np.array(A_["cass"]) * [-1, 1])) < 4.8 and z > 7.0},
}
def bridges(mv, layers, m, off):
    """Every bridge line the slicer lays, minus what was printed in the layer below it.  What is left is split in two:
    over open air (the drawn part has nothing there in the layer below: a true bridge, seen from outside) and
    over the part's own sparse infill (the drawn part is solid there: every closed top does this, and nobody sees it)."""
    from shapely.affinity import affine_transform
    air_open, air_fill = [], []; below = {}; solid = {}
    for (z, typ, x0, y0, x1, y1, ex, f) in mv:
        if not (ex and typ == "Bridge infill") or np.hypot(x1 - x0, y1 - y0) < 0.8: continue
        zb = round(z - LH, 2)
        if zb not in below:
            below[zb] = shapely.unary_union([LineString([(q[0], q[1]), (q[2], q[3])]).buffer(q[4] / 2 + 0.05, quad_segs=2) for q in layers.get(zb, [])]) if zb in layers else None
            sec = m.section_multiplane([0, 0, 0], [0, 0, 1], [zb - LH / 2])[0] if zb in layers else None; solid[zb] = None
            if sec is not None:
                T = sec.metadata["to_3D"]; g_ = shapely.unary_union([q.buffer(0) for q in sec.polygons_full]); solid[zb] = affine_transform(g_, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3] + off[0], T[1, 3] + off[1]])
        if below[zb] is None: continue
        air = LineString([(x0, y0), (x1, y1)]).difference(below[zb]); inner = air.intersection(solid[zb].buffer(0.05)) if solid[zb] is not None else LineString(); outer = air.difference(solid[zb].buffer(0.05)) if solid[zb] is not None else air
        air_open.append(max((g_.length for g_ in getattr(outer, "geoms", [outer])), default=0.0)); air_fill.append(max((g_.length for g_ in getattr(inner, "geoms", [inner])), default=0.0))
    return air_open, air_fill
def bridges_of(stl, gcode):
    """the two bridge figures for any print file: (over open air, over its own infill).  tools/printcards.py uses it for the version before"""
    if not os.path.exists(gcode) or os.path.getmtime(gcode) < os.path.getmtime(stl): subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", "125,105", "--output", gcode], capture_output=True, timeout=3600)
    mv = moves(gcode); layers, _ = parse(gcode); m = trimesh.load(stl, process=True); a, b = bridges(mv, layers, m, offset(layers, m)); return round(float(max(a, default=0)), 1), round(float(max(b, default=0)), 1)
def audit(n, extra=(), tag=""):
    g = slice_(n, extra, tag); mv = moves(g); layers, _ = parse(g); m = trimesh.load(f"build/print/one135_{n}.stl", process=True); off = offset(layers, m)
    w = lambda x, y: np.array([x - off[0], FLIP[n] * (y - off[1])]); seams = []; prev = (None, None, False)
    for (z, typ, x0, y0, x1, y1, ex, f) in mv:
        if typ == "External perimeter" and ex and not (prev[2] and prev[1] == typ and prev[0] == z): seams.append((z, *w(x0, y0)))
        prev = (z, typ, ex)
    on = {k: sum(bool(fn(np.array(s[1:]), s[0])) for s in seams) for k, fn in FEATURES.get(n, {}).items()}
    br, bri = bridges(mv, layers, m, off)
    oh = sum(np.hypot(x1 - x0, y1 - y0) for (z, typ, x0, y0, x1, y1, ex, f) in mv if ex and typ == "Overhang perimeter")
    t = {}
    for (z, typ, x0, y0, x1, y1, ex, f) in mv: t[z] = t.get(z, 0) + np.hypot(x1 - x0, y1 - y0) / max(f / 60, 1)
    zs = sorted(t)[1:]; lt = np.array([t[z] for z in zs]) if zs else np.array([0.0])
    return dict(seams=len(seams), seams_on=on, longest_bridge_mm=round(float(max(br, default=0)), 1), longest_bridge_over_own_infill_mm=round(float(max(bri, default=0)), 1), bridge_total_mm=round(float(sum(br))), overhang_wall_mm=round(float(oh)), layers=len(t),
                shortest_layer_s=round(float(lt.min()), 1), layers_under_8s=int((lt < 8).sum())), seams, mv, w
if __name__ == "__main__":
    out = {}; parts = ["front", "blade", "wheel", "back", "body", "roller", "knob", "spool"]; keep = {}
    print("seams on working surfaces, by seam setting (number of seams that land there)")
    for n in parts:
        r, seams, mv, w = audit(n); out[n] = r; keep[n] = (seams, mv, w)
        if FEATURES.get(n):
            r["by_seam_setting"] = {"aligned": r["seams_on"]}
            for s in ("rear", "nearest", "random"): r["by_seam_setting"][s] = audit(n, ["--seam-position", s], "_" + s)[0]["seams_on"]
            print(f"  {n:8s} " + " | ".join(f"{k}: " + ", ".join(f"{v} {q}" for q, v in d.items()) for k, d in r["by_seam_setting"].items()))
    pc = json.load(open("build/printcheck.json"))
    print("bridges, overhangs, cooling, shape")
    for n in parts:
        r = out[n]; s = pc[n]["size"]; r["height_over_base"] = round(s[2] / min(s[0], s[1]), 1); r["bed_contact_mm2"] = pc[n]["on_bed_mm2"]
        print(f"  {n:8s} longest bridge {r['longest_bridge_mm']:5.1f} mm, overhanging wall {r['overhang_wall_mm']:5d} mm, shortest layer {r['shortest_layer_s']:5.1f} s ({r['layers_under_8s']} of {r['layers']} layers under 8 s), height / base {r['height_over_base']}, on the bed {r['bed_contact_mm2']:.0f} mm2")
    # travel across the slits behind the springs
    for n, c, R, a_tip, arc in (("blade", P, B["R_OUT"], B["DB_A"], B["BL_ARC"]), ("wheel", C, B["WHEEL_R"], B["WD_A0"], B["WH_ARC"])):
        a = np.linspace(a_tip - arc + 2, a_tip - 2, 40); slit = Polygon([tuple(pol(c, R + 0.2, t)) for t in a] + [tuple(pol(c, R + B["SLIT"] - 0.2, t)) for t in a[::-1]]); seams, mv, w = keep[n]; cross = {}
        for (z, typ, x0, y0, x1, y1, ex, f) in mv:
            if not ex and z <= 1.0 and LineString([tuple(w(x0, y0)), tuple(w(x1, y1))]).intersects(slit): cross[z] = cross.get(z, 0) + 1
        out[n]["travel_moves_across_the_slit"] = cross; print(f"  {n}: travel moves across the slit behind its spring, by layer: {cross if cross else 'none'}")
    for n in ("blade", "wheel"):                          # does "avoid crossing perimeters" keep the nozzle out of the slits?
        c, R, a_tip, arc = (P, B["R_OUT"], B["DB_A"], B["BL_ARC"]) if n == "blade" else (C, B["WHEEL_R"], B["WD_A0"], B["WH_ARC"])
        a = np.linspace(a_tip - arc + 2, a_tip - 2, 40); slit = Polygon([tuple(pol(c, R + 0.2, t)) for t in a] + [tuple(pol(c, R + B["SLIT"] - 0.2, t)) for t in a[::-1]])
        g = slice_(n, ["--avoid-crossing-perimeters"], "_avoid"); layers2, _ = parse(g); m2 = trimesh.load(f"build/print/one135_{n}.stl", process=True); off2 = offset(layers2, m2); w2 = lambda x, y: np.array([x - off2[0], FLIP[n] * (y - off2[1])])
        k = sum(1 for (z, typ, x0, y0, x1, y1, ex, f) in moves(g) if not ex and z <= 1.0 and LineString([tuple(w2(x0, y0)), tuple(w2(x1, y1))]).intersects(slit))
        out[n]["travel_moves_across_the_slit_with_avoid_crossing_perimeters"] = k; print(f"  {n}: the same with 'avoid crossing perimeters' switched on: {k} in all")
    # the same parts on the full plate: cooling
    pl = json.load(open("build/plate.json")) if os.path.exists("build/plate.json") else None
    if pl:
        g = list(pl["speeds"].values())[0]["plate_gcode"]; t = {}
        for (z, typ, x0, y0, x1, y1, ex, f) in moves(g): t[z] = t.get(z, 0) + np.hypot(x1 - x0, y1 - y0) / max(f / 60, 1)
        lt = np.array([t[z] for z in sorted(t)[1:]]); out["plate"] = dict(shortest_layer_s=round(float(lt.min()), 1), layers_under_8s=int((lt < 8).sum()), layers=len(lt)); print("  whole kit on one plate: shortest layer %.0f s, %d layers under 8 s" % (lt.min(), (lt < 8).sum()))
    # first-layer islands
    from printsim import printed
    for n in ("front", "back", "blade", "wheel"):
        g_ = printed(n, 0.2, 0.0); isl = sorted(q.area for q in getattr(g_, "geoms", [g_]) if q.geom_type == "Polygon"); out[n]["first_layer_islands_mm2"] = [round(a, 1) for a in isl[:-1]][:12]
        print(f"  {n}: islands on the first layer (mm2): {[round(a, 1) for a in isl[:-1]][:10] if len(isl) > 1 else 'none'}")
    json.dump(out, open("build/pathaudit.json", "w"), indent=1)
    fig, ax = plt.subplots(1, 3, figsize=(18, 6.4))
    from printsim import cad
    for a_, n, zc in zip(ax, ("blade", "wheel", "front"), (0.8, 0.8, 3.2)):
        g_ = cad(n, zc)
        for q in getattr(g_, "geoms", [g_]):
            a_.fill(*q.exterior.xy, color="#e6e9ee", lw=0); [a_.fill(*h.xy, color="w", lw=0) for h in q.interiors]; a_.plot(*q.exterior.xy, color="#8a93a3", lw=0.6); [a_.plot(*h.xy, color="#8a93a3", lw=0.6) for h in q.interiors]
        s = np.array(keep[n][0]); hit = np.array([any(fn(p[1:], p[0]) for fn in FEATURES[n].values()) for p in s])
        a_.scatter(s[~hit, 1], s[~hit, 2], s=7, color="#3b6fb6", label="seam, harmless place"); a_.scatter(s[hit, 1], s[hit, 2], s=22, color="#c81e1e", label="seam on a working surface"); a_.set_aspect("equal"); a_.axis("off")
        a_.set_title(f"{n}: {int(hit.sum())} of {len(s)} seams on a working surface", fontsize=15); a_.legend(fontsize=11, loc="lower right", frameon=False)
    plt.tight_layout(); plt.savefig("build/pathaudit.png", dpi=75)
