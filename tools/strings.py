"""Stringing: how often the nozzle travels, without printing, across an opening that light has to pass (the three aperture holes, the shutter's window, the lens port).
A travel across open air is where a string can be left.  Sliced twice: as the print card says, and with "avoid crossing perimeters" switched on.  Writes build/strings.json."""
import sys, json, subprocess, os, re, numpy as np, trimesh
sys.path.insert(0, "tools"); import slicecheck
LY = json.load(open("build/layout.json")); B = LY["B"]; C = np.array(B["c"]); P = np.array(B["P_S"]); D = "build/slice/"
hole = lambda k: C + B["R_HOLE"] * np.array([np.cos(np.radians(B["A_AX"] + B["WPOS"][k])), np.sin(np.radians(B["A_AX"] + B["WPOS"][k]))])
sys.path.insert(0, "tools"); from scadr import values
WIN = values(["WIN_IN", "WIN_R"]); AXD = -P / np.linalg.norm(P); win = P + (B["R_PORT"] - WIN["WIN_IN"]) * AXD
OPEN = dict(wheel=[("small hole", hole(0) * [1, -1], B["STOPS"][0]), ("middle hole", hole(1) * [1, -1], B["STOPS"][1]), ("large hole", hole(2) * [1, -1], B["STOPS"][2])],      # the wheel prints mirrored: (x, -z)
            blade=[("window", win, WIN["WIN_R"] - 0.15)], front=[("lens port", np.array([0.0, 0.0]), 3.0)])
def travels(gcode):
    x = y = z = None; out = []
    for ln in open(gcode):
        if not ln.startswith("G1 "): continue
        m = dict(re.findall(r"([XYZEF])(-?[0-9.]+)", ln.split(";")[0])); nx, ny = float(m.get("X", x if x is not None else 0)), float(m.get("Y", y if y is not None else 0))
        if "Z" in m: z = float(m["Z"])
        if x is not None and ("X" in m or "Y" in m) and float(m.get("E", 0)) <= 0 and z is not None: out.append((x, y, nx, ny, z))
        x, y = nx, ny
    return np.array(out)
def crossings(T, c, r):
    a, b = T[:, :2] - c, T[:, 2:4] - c; d = b - a; L2 = (d ** 2).sum(1); t = np.clip(-(a * d).sum(1) / np.maximum(L2, 1e-9), 0, 1); near = np.hypot(*(a + d * t[:, None]).T)
    return int(((near < r - 0.1) & (np.hypot(*a.T) > r) & (np.hypot(*b.T) > r) & (L2 > 1)).sum())
res = {}
for avoid in (0, 1):
    for n in OPEN:
        stl = f"build/print/one135_{n}.stl"; g = D + f"{n}_str{avoid}.gcode"; os.makedirs(D, exist_ok=True)
        subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", "125,105", "--output", g] + (["--avoid-crossing-perimeters"] if avoid else []), capture_output=True)
        layers, _ = slicecheck.parse(g); m = trimesh.load(stl, process=True); off = slicecheck.offset(layers, m); T = travels(g); T[:, [0, 2]] -= off[0]; T[:, [1, 3]] -= off[1]
        for name, c, r in OPEN[n]:
            k = crossings(T, np.asarray(c, float), r); res.setdefault(f"{n}: {name}", {})["avoid crossing perimeters" if avoid else "as on the print card"] = k
for k, v in res.items(): print("   %-22s travels across it: %3d as on the print card, %3d with 'avoid crossing perimeters'" % (k, v["as on the print card"], v["avoid crossing perimeters"]))
json.dump(res, open("build/strings.json", "w"), indent=1)
