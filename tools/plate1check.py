"""The first plate (rung 1) and its slide: does the plate go on and sit as the front plate does, does the slide run free and stop at both ends, is the whole picture lit when the slide is up,
and is there any straight line from outside to the body's port when it is down?  Writes build/plate1.json."""
import sys, json, numpy as np, trimesh, manifold3d as m3
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
sys.path.insert(0, "tools"); import kin; from kin import V, XE, man
T = lambda n: trimesh.load(f"build/asm/{n}.stl", process=True); M = lambda n: kin.tomesh(T(n)); out = {}; SL = V["SLIDE"]
body, p1, p1n, sl, ring = man("body"), M("plate1"), M("plate1N"), M("slide1"), M("pinring"); vol = lambda a, b: float((a ^ b).volume())
out["home"] = dict(plate_x_body=round(vol(p1, body), 4), slide_x_body=round(vol(sl, body), 4), slide_x_plate=round(vol(sl, p1), 4), ring_x_plate_expected=round(vol(ring, p1), 4), ring_x_slide=round(vol(ring, sl), 4),
                   slide_gap_to_body=round(float(sl.min_gap(body, 4)), 3), slide_gap_to_plate=round(float(sl.min_gap(p1, 4)), 3))
sub = m3.Manifold.compose([p1n, sl, ring]); path = [(-XE, d, SL) for d in np.linspace(14, 0, 15)] + [(-s, 0, SL) for s in np.linspace(XE, 0, 12)[1:]] + [(0, 0, s) for s in np.linspace(SL, 0, 14)[1:]]
out["going_on"] = dict(steps=len(path), most_shared_mm3=round(max(vol(sub.translate(list(q)), body) for q in path), 4))
out["holds"] = {"plate pulled 0.6 mm off x body": round(vol(p1.translate([0, 0.6, 0]), body), 4), "plate pushed 0.9 mm up x body": round(vol(p1.translate([0, 0, 0.9]), body), 4)}
tr = []
for u in np.linspace(0, V.get("P1_T", 10.0), 21): s2 = sl.translate([0, 0, float(u)]); tr.append((round(float(u), 1), vol(s2, p1), vol(s2, body), float(s2.min_gap(p1, 4)), float(s2.min_gap(body, 4))))
out["slide_travel"] = dict(steps=len(tr), most_shared_mm3=round(max(max(r[1], r[2]) for r in tr), 4), least_gap_to_plate=round(min(r[3] for r in tr), 3), least_gap_to_body=round(min(r[4] for r in tr), 3))
out["stops"] = {"pushed 0.5 mm past shut x plate": round(vol(sl.translate([0, 0, -0.5]), p1), 4), "lifted 0.5 mm past open x plate": round(vol(sl.translate([0, 0, 10.5]), p1), 4), "pulled 0.5 mm forward x plate": round(vol(sl.translate([0, 0.5, 0]), p1), 4), "pushed 0.5 mm back x body": round(vol(sl.translate([0, -0.5, 0]), body), 4)}
# light, slide up: a straight line from every point of the film to the pinhole
YP = float(T("pinring").bounds[0][1]) - 0.05; RF, CFY, GA, GZ = 32.0, 32.0, 18 / 32, 12.0; nx, nz = 73, 49; TT = np.linspace(-GA, GA, nx); Z = np.linspace(-GZ, GZ, nz)
F = np.array([[RF * np.sin(t), CFY - RF * np.cos(t), z] for t in TT for z in Z]); P = np.array([0.0, YP, 0.0]); v = P - F; Lg = np.linalg.norm(v, axis=1); D = v / Lg[:, None]; ok = np.ones(len(F), bool); who = {}
for n in ("body", "plate1", "slide1_up"):
    loc, ir, _ = Fast(T(n)).intersects_location(F + D * 0.01, D, multiple_hits=False); d = np.linalg.norm(loc - F[ir], axis=1); k = ir[(d > 0.01) & (d < Lg[ir] - 0.02)]; ok[k] = False; who[n] = int(len(k))
g = ok.reshape(nx, nz); out["open"] = dict(picture_lit_pct=round(float(100 * ok.mean()), 1), corners_lit=bool(g[0, 0] and g[0, -1] and g[-1, 0] and g[-1, -1]), blocked_by=who, pinhole_to_film_mm=round(YP, 2))
# light, slide down: rays from the body's port outward, in every direction; one that gets out without meeting plastic is a straight way in
rng = np.random.default_rng(5); n = 400000; r = 2.5 * np.sqrt(rng.uniform(size=n)); a = rng.uniform(0, 2 * np.pi, n); O = np.c_[r * np.cos(a), np.full(n, V["Y_FRONT"] - 0.3), r * np.sin(a)]
u = rng.uniform(size=n); ph = rng.uniform(0, 2 * np.pi, n); st = np.sqrt(u); Dd = np.c_[st * np.cos(ph), np.sqrt(1 - u), st * np.sin(ph)]
scene = trimesh.util.concatenate([T("body"), T("plate1"), T("slide1"), T("pinring")]); hit = Fast(scene).intersects_any(O, Dd); out["shut"] = dict(rays=n, straight_ways_out=int((~hit).sum()))
scene2 = trimesh.util.concatenate([T("body"), T("plate1"), T("slide1_up"), T("pinring")]); hit2 = Fast(scene2).intersects_any(O, Dd); out["shut"]["for_comparison_ways_out_with_the_slide_up"] = int((~hit2).sum())
json.dump(out, open("build/plate1.json", "w"), indent=1)
for k, v_ in out.items(): print(k, v_)
