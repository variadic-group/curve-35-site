"""ONE-135 aimed light test.  tools/optics.py throws rays from the film in every direction; a hole 0.4 mm across is hit by
about one ray in forty million that way.  This tool AIMS: rays from the film toward the places where two parts meet
(the two knob slots in the top, the joint between back and body all round, the frame wheel's slot, the front plate's edge),
so that each square millimetre of those places gets thousands of rays.  The film itself is left out of the scene, which is
on the safe side (more rays get through than in the real camera).  No ray may leave the closed camera in a straight line.
    python3 tools/aimleak.py [rays per window]"""
import sys, json, numpy as np, trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
from trimesh.ray.ray_triangle import RayMeshIntersector as Exact
sys.path.insert(0, "tools"); from scadr import values
A = "build/asm/"; L = lambda n: trimesh.load(A + n + ".stl", process=True)
V = values(["H", "Y_RIM", "DOOR_T", "SPOOL", "CASS", "ROLLER", "Y_FRONT", "FX0", "FX1", "FZ0", "FZ1", "WALL_E", "RCH_C", "RCH_S"])
TH = json.load(open("build/layout.json"))["B"]["THETA"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000_000; ONLY = sys.argv[2] if len(sys.argv) > 2 else ""      # a word: only the runs whose name holds it ("!word": all but those); results are added to build/aimleak.json
H, YR = V["H"], V["Y_RIM"]; rng = np.random.default_rng(7); film = L("film"); res = {}
def rect(n, lo, hi):                                                   # n random points in the box lo..hi (a flat window when one side has no thickness)
    return rng.uniform(lo, hi, size=(n, 3))
def run(label, names, sel, windows, n=N, move=None):
    if ONLY and ((ONLY[1:] in label) if ONLY.startswith("!") else (ONLY not in label)): return
    meshes = []
    for x in names:
        m = L(x)
        if move and x in move: m.apply_translation(move[x])
        meshes.append(m)
    scene = trimesh.util.concatenate(meshes); fast = Fast(scene); esc = []; total = 0
    for chunk in range(0, n, 4_000_000):
        k = min(4_000_000, n - chunk); P, fi = trimesh.sample.sample_surface(film, 3 * k, seed=int(rng.integers(1 << 30)))
        keep = sel(P); P = P[keep][:k]; fi = fi[keep][:k]; k = len(P)
        if k == 0: continue
        w = rng.integers(len(windows), size=k); T = np.zeros((k, 3))
        for j, (lo, hi) in enumerate(windows):
            m = w == j; T[m] = rect(int(m.sum()), lo, hi)
        v = T - P; D = v / np.linalg.norm(v, axis=1)[:, None]; O = P + film.face_normals[fi] * 0.03
        idx = np.nonzero(~fast.intersects_any(O, D))[0]; total += k
        if len(idx):
            ex = Exact(scene)
            for j in range(0, len(idx), 2000):
                sub = idx[j:j + 2000]; h2 = ex.intersects_any(O[sub], D[sub]); esc += [np.hstack([O[q], D[q]]) for q in sub[~h2]]
    out = dict(rays=total, escaped=len(esc))
    if esc:
        E = np.array(esc); out["from_points_sample"] = np.round(E[:8, :3], 2).tolist(); out["directions_sample"] = np.round(E[:8, 3:], 3).tolist(); np.save("build/aimleak_%s.npy" % label.split(":")[0].replace(" ", "_"), E)
    res[label] = out; print(label, out, flush=True)
base = ["body", "back", "front", "roller", "knob", "cassette", "spool", f"blade_PHI{TH}", "wheel_STOP2"]
sx, sy = V["SPOOL"]; cx, cy = V["CASS"]; rx, ry = V["ROLLER"]
top = lambda c, r=13: [([c[0] - r, YR - 4, H + 0.2], [c[0] + r, c[1] + r, H + 0.2])]
allf = lambda P: np.ones(len(P), bool)
run("spool slot: film on the take-up side toward the slot in the top", base, lambda P: P[:, 0] > 14, top((sx, sy)))
run("knob slot: film on the supply side toward the slot in the top", base, lambda P: P[:, 0] < -14, top((cx, cy)))
run("spool slot, all film: toward the slot in the top", base, allf, top((sx, sy)))
run("knob slot, all film: toward the slot in the top", base, allf, top((cx, cy)))
run("frame wheel: all film toward the wheel's opening in the top", base, allf, [([rx - 12, YR - 6, H + 0.2], [rx + 12, ry + 10, H + 0.2])])
X0, X1 = film.bounds[0][0] - V["WALL_E"] - 14, film.bounds[1][0] + V["WALL_E"] + 14
band = [([X0, YR - 6, H + 1.0], [X1, YR + 3, H + 1.0]), ([X0, YR - 6, -H - 1.0], [X1, YR + 3, -H - 1.0]), ([X0, YR - 6, -H], [X0, YR + 3, H]), ([X1, YR - 6, -H], [X1, YR + 3, H])]
run("joint of back and body: all film toward the joint line all round", base, allf, band)
for off in (0.15, 0.3, 0.6):
    run("joint, back standing %.2f mm off the body: all film toward the joint line all round" % off, base, allf, band, move=dict(back=[0, -off, 0], roller=[0, -off, 0]))
    run("knob and spool slots, back standing %.2f mm off: toward the slots in the top" % off, base, allf, top((sx, sy)) + top((cx, cy)), move=dict(back=[0, -off, 0], roller=[0, -off, 0]))
yf = V["Y_FRONT"]
edge = [([V["FX0"] - 3, yf - 1, V["FZ1"] + 0.5], [V["FX1"] + 3, yf + 5, V["FZ1"] + 0.5]), ([V["FX0"] - 3, yf - 1, V["FZ0"] - 0.5], [V["FX1"] + 3, yf + 5, V["FZ0"] - 0.5]),
        ([V["FX0"] - 0.5, yf - 1, V["FZ0"] - 3], [V["FX0"] - 0.5, yf + 5, V["FZ1"] + 3]), ([V["FX1"] + 0.5, yf - 1, V["FZ0"] - 3], [V["FX1"] + 0.5, yf + 5, V["FZ1"] + 3])]
run("front plate: all film toward the plate's edge all round", base, allf, edge)
run("front plate standing 0.3 mm off: toward its edge all round", base, allf, edge, move=dict(front=[0, 0.3, 0], **{f"blade_PHI{TH}": [0, 0.3, 0], "wheel_STOP2": [0, 0.3, 0]}))
# v2.10: the plate left out of place by a fall.  Where it can be is read from build/platewindow.json (measured on the meshes): at its top stop; there, as far off the face as its lips
# let it; and across to just short of where it comes off, as far off as it can then be.  Rays toward its edge all round and the strip of the body it uncovers, and toward a window
# in front of the whole plate (through whatever opening in plate, shutter and wheel might now line up with the body's port).
PWN = json.load(open("build/platewindow.json"))["now"]
def mvp(dx, dy, up): return dict(front=[dx, dy, up], **{f"blade_PHI{TH}": [dx, dy, up], "wheel_STOP2": [dx, dy, up]})
def edge2(dx, up): return [([V["FX0"] - 3 + dx, yf - 1, V["FZ1"] + up + 0.5], [V["FX1"] + 3, yf + 7, V["FZ1"] + up + 0.5]), ([V["FX0"] - 3 + dx, yf - 1, V["FZ0"] - 1], [V["FX1"] + 3, yf + 7, V["FZ0"] + up + 0.5]),
                           ([V["FX0"] - 0.5 + dx, yf - 1, V["FZ0"] - 3], [V["FX0"] - 0.5 + dx, yf + 7, V["FZ1"] + up + 3]), ([V["FX1"] + 0.5 + dx, yf - 1, V["FZ0"] - 3], [V["FX1"] + 0.5, yf + 7, V["FZ1"] + up + 3])]
def face(dx, up): return [([V["FX0"] - 8 + dx, yf + 14, V["FZ0"] - 6], [V["FX1"] + 8, yf + 14, V["FZ1"] + up + 6])]
for tag, key in (("as drawn", "as drawn"), ("thinnest printer in the range", "far too thin: walls -0.15")):
    w = PWN[key]; up = w["top_stop"]; g = w["pull_off_by_side_in_band"]; g0 = g[0][1]; xf = w["set_on"]["side"][0] - 0.1; gx = [v for x_, v in g if x_ <= xf][-1]
    for what, (dx, dy) in (("at its top stop", (0.0, 0.0)), ("at its top stop and %.2f mm off the face (as far as its side lips let it)" % g0, (0.0, g0)), ("at its top stop, %.1f mm across and %.1f mm off the face (as far as it goes before it comes off)" % (xf, gx), (-xf, gx))):
        run("front plate left out of place, %s: %.1f mm up, %s: toward its edge all round and the strip of the body it uncovers" % (tag, up, what), base, allf, edge2(dx, up), move=mvp(dx, dy, up))
        run("front plate left out of place, %s: %.1f mm up, %s: toward a window in front of the whole plate" % (tag, up, what), base, allf, face(dx, up), move=mvp(dx, dy, up))
if ONLY:
    try: old = json.load(open("build/aimleak.json"))
    except Exception: old = {}
    old = {k: v for k, v in old.items() if "left pushed up" not in k and "pushed up" not in k}; old.update(res); res = old
json.dump(res, open("build/aimleak.json", "w"), indent=1)
bad = [k for k, v in res.items() if v["escaped"]]; print("windows with light getting out:", bad if bad else "none")
