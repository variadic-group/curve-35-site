"""ONE-135 light checks on the exported meshes.
A. Taking light: rays from points on the stop to points all over the 36 x 24 frame, and the same rays continued forward
   to the lens.  No part may clip them.
B. Light leaks: rays from all over the film (frame, both turns, the full take-up roll) in random directions.
   With the shutter closed and the back on, none may leave the camera in a straight line."""
import sys, json, numpy as np, trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
from trimesh.ray.ray_triangle import RayMeshIntersector as Exact
sys.path.insert(0, "tools"); from scadr import export
A = "build/asm/"; L = lambda n: trimesh.load(A + n + ".stl", process=True)
TH = json.load(open("build/layout.json"))["B"]["THETA"]
RF, CFY, GATE_A, GATE_Z, STOP_Y = 32.0, 32.0, np.degrees(18 / 32), 12.0, 25.47 + 1.05
LB = json.load(open("build/layout.json"))["B"]; STOP_R = [r + 0.15 for r in LB["STOPS"]]              # as drawn (HOLE_COMP larger than they should print)
res = {}
# ---------------------------------------------------------------- A. taking light
def film_pts(nx=13, nz=7, f=0.99):
    return np.array([[RF * np.sin(t), CFY - RF * np.cos(t), z] for t in np.radians(np.linspace(-GATE_A * f, GATE_A * f, nx)) for z in np.linspace(-GATE_Z * f, GATE_Z * f, nz)])
def stop_pts(r, n=12): return np.array([[0, STOP_Y, 0]] + [[0.97 * r * np.cos(a), STOP_Y, 0.97 * r * np.sin(a)] for a in np.linspace(0, 2 * np.pi, n, endpoint=False)])
def clipped(meshes, O, D, Lg):
    out = {}
    for name, m in meshes.items():
        loc, ir, _ = Fast(m).intersects_location(O, D, multiple_hits=False)
        d = np.linalg.norm(loc - O[ir], axis=1); k = (d > 0.02) & (d < Lg[ir] - 0.02)
        if k.any(): out[name] = int(k.sum())
    return out
F = film_pts(); body, front, blade0 = L("body"), L("front"), L("blade_PHI0.0")
sys.path.insert(0, "tools"); from scadr import values
WIN_IN = values(["WIN_IN"])["WIN_IN"]; AXD = -np.array(LB["P_S"]) / np.linalg.norm(LB["P_S"])      # the window is drawn WIN_IN nearer the pivot; AXD points from the pivot to the lens axis
def blade_at(off):
    """the blade as its window passes the lens while the rocker is pressed: it hangs on its boss, which puts the window on the axis (off = 0) on a printer +0.05 fat; off: how far it misses, toward the rim (+)"""
    b = blade0.copy(); b.apply_translation([(WIN_IN + off) * AXD[0], 0, (WIN_IN + off) * AXD[1]]); return b
WIN_MISS = 0.85 * 2 * 0.2                                             # a printer 0.15 thin lets the blade hang 0.34 mm lower than the one the window is drawn for; one 0.25 fat, 0.34 less
def disc(r, n=180):                                                    # even samples over the whole stop
    k = np.arange(n) + 0.5; rr = r * np.sqrt(k / n); a = k * 2.399963; return rr * np.cos(a), rr * np.sin(a)
def unclipped(meshes, O, D, Lg):
    ok = np.ones(len(O), bool)
    for m in meshes:
        loc, ir, _ = Fast(m).intersects_location(O, D, multiple_hits=False); d = np.linalg.norm(loc - O[ir], axis=1); ok[ir[(d > 0.004) & (d < Lg[ir] - 0.02)]] = False
    return ok
for k, name in enumerate(["f/%g (%s dot)" % (min((8, 9.5, 11, 13, 16, 19, 22), key=lambda n: abs(n - 32.0 / (2 * r))), d) for r, d in zip(LB["STOPS"], ("small", "middle", "large"))]):       # v2.14: named from the holes themselves (the large one is f/9.5 now)
    wheel = L(f"wheel_STOP{k}"); y0 = STOP_Y; sx, sz = disc(STOP_R[k] * 0.995)
    S = np.c_[sx, np.full(len(sx), y0), sz]; O = np.repeat(S, len(F), 0); T = np.tile(F, (len(S), 1)); v = T - O; Lg = np.linalg.norm(v, axis=1); D = v / Lg[:, None]
    back = unclipped([body, wheel], O + D * 0.002, D, Lg - 0.002)
    ahead = unclipped([blade_at(0.0), front], O - D * 0.002, -D, (28.6 - O[:, 1]) / -D[:, 1])
    t = (back & ahead).reshape(len(S), len(F)).mean(0)                # share of the stop each film point sees
    miss = [float((back & unclipped([blade_at(o), front], O - D * 0.002, -D, (28.6 - O[:, 1]) / -D[:, 1])).reshape(len(S), len(F)).mean(0).min()) for o in (WIN_MISS, -WIN_MISS)]
    by = dict(body_or_wheel=int((~back).sum()), blade_or_front=int((~ahead).sum()))
    res[name] = dict(light_kept_centre=float(t[len(F) // 2]), light_kept_worst_corner=float(t.min()), worst_corner_thin_printer=miss[0], worst_corner_fat_printer=miss[1], rays=len(O), clipped=by)
    print("%-9s hole drawn %.1f mm: centre sees %.0f %% of the hole, worst corner %.0f %% (printer 0.15 thin: %.0f %%, 0.25 fat: %.0f %%)" % (name, 2 * STOP_R[k], 100 * t[len(F) // 2], 100 * t.min(), 100 * miss[0], 100 * miss[1]))
# ---------------------------------------------------------------- B. straight-line light leaks
rng = np.random.default_rng(1)
def sphere(n):
    v = rng.normal(size=(n, 3)); return v / np.linalg.norm(v, axis=1)[:, None]
film = L("film"); N = int(sys.argv[1]) if len(sys.argv) > 1 else 4_000_000
def leak_test(label, names, n=N):
    def LL(x):                                                         # 'name|dx,dz': the part moved that far (the blade inside the play of its hub)
        if "|" not in x: return L(x)
        m = L(x.split("|")[0]); d = [float(q) for q in x.split("|")[1].split(",")]; m.apply_translation([d[0], 0, d[1]]); return m
    scene = trimesh.util.concatenate([LL(x) for x in names])
    P, fi = trimesh.sample.sample_surface(film, n, seed=2); nrm = film.face_normals[fi]
    D = sphere(n); D[(D * nrm).sum(1) < 0] *= -1                       # leave the film surface outward
    O = P + nrm * 0.03
    hit = Fast(scene).intersects_any(O, D)
    idx = np.nonzero(~hit)[0]
    real = []
    if len(idx):                                                       # confirm with the exact intersector (embree can slip through shared edges)
        ex = Exact(scene)
        for j in range(0, len(idx), 2000):
            sub = idx[j:j + 2000]; h2 = ex.intersects_any(O[sub], D[sub]); real += list(sub[~h2])
    real = np.array(real, int)
    out = dict(rays=n, escaped_fast=int(len(idx)), escaped_confirmed=int(len(real)))
    if len(real):
        # where do they leave?  intersect with a box 4 mm outside the camera
        lo = scene.bounds[0] - 4; hi = scene.bounds[1] + 4; o = O[real]; d = D[real]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(d > 0, (hi - o) / d, (lo - o) / d)
        te = t.min(1); X = o + d * te[:, None]
        out["exit_points_sample"] = np.round(X[:12], 1).tolist(); out["from_points_sample"] = np.round(o[:12], 1).tolist()
        out["exit_bbox"] = [np.round(X.min(0), 1).tolist(), np.round(X.max(0), 1).tolist()]
        np.save("build/leak_%s.npy" % label.split()[0], np.hstack([o, d, X]))
    res["leak: " + label] = out; print(label, out)
base = ["body", "back", "front", "roller", "knob", "cassette"]; printed = ["spool"]
leak_test("closed one side, cloud, printed spool", base + printed + [f"blade_PHI{TH}", "wheel_STOP2"])
leak_test("closed other side, cloud, printed spool", base + printed + [f"blade_PHI{-TH}", "wheel_STOP2"])
leak_test("closed one side, T, printed spool", base + printed + [f"blade_PHI{TH}", "wheel_STOP0"], N // 2)
leak_test("closed other side, T, printed spool", base + printed + [f"blade_PHI{-TH}", "wheel_STOP0"], N // 2)
leak_test("closed one side, sun, printed spool", base + printed + [f"blade_PHI{TH}", "wheel_STOP1"], N // 2)
for sg, nm in ((1, "p"), (-1, "n")):
    export("scad/one135.scad", A + f"blade_play_{nm}.stl", dict(PART="blade", PHI=sg * (TH - 1.3))); export("scad/one135.scad", A + f"blade_loose25_{nm}.stl", dict(PART="blade", PHI=sg * (TH - 2.5))); export("scad/one135.scad", A + f"blade_loose40_{nm}.stl", dict(PART="blade", PHI=sg * (TH - 4.0))); export("scad/one135.scad", A + f"blade_over_{nm}.stl", dict(PART="blade", PHI=sg * (TH + 1.2)))
export("scad/one135.scad", A + "roller_float.stl", dict(PART="roller", ROLL_UP=0.6)); export("scad/one135.scad", A + "roller_seated.stl", dict(PART="roller", ROLL_UP=-0.25))     # the wheel can ride 0.6 mm up (to the ledge in the body) and 0.2 down (onto the film post)
leak_test("closed one side, blade 1.3 degrees toward open (twice its play in the notch), cloud", base + printed + ["blade_play_p", "wheel_STOP2"], N // 2)
leak_test("closed other side, blade 1.3 degrees toward open, cloud", base + printed + ["blade_play_n", "wheel_STOP2"], N // 2)
for dg, tg in ((2.5, "loose25"), (4.0, "loose40")):
    for nm, side in (("p", "one"), ("n", "other")): leak_test(f"closed {side} side, blade {dg} degrees toward open (a thin print lets it rest up to 2.3), cloud", base + printed + [f"blade_{tg}_{nm}", "wheel_STOP2"], N // 2)
leak_test("closed one side, blade 1.2 degrees past closed (against its stop), cloud", base + printed + ["blade_over_p", "wheel_STOP2"], N // 2)
leak_test("closed other side, blade 1.2 degrees past closed, cloud", base + printed + ["blade_over_n", "wheel_STOP2"], N // 2)
leak_test("closed, frame wheel at the top of its float, cloud", [b if b != "roller" else "roller_float" for b in base] + printed + [f"blade_PHI{TH}", "wheel_STOP2"], N // 2)
leak_test("closed, frame wheel resting on the film post (the bottom of its float), cloud", [b if b != "roller" else "roller_seated" for b in base] + printed + [f"blade_PHI{TH}", "wheel_STOP2"], N // 2)
C2 = 2 * LB["HUBC"]                                                    # the blade's whole play on its boss: at rest its own spring holds it up; pressed, it hangs this much lower
for sg, side in ((1, "one"), (-1, "other")):
    a = np.radians(LB["DB_A"] + sg * TH); u = np.array([np.cos(a), np.sin(a)])
    for d, w in ((u * C2, "pushed all the way toward its click wall (as while the rocker is pressed)"), (u * C2 / 2 + np.array([C2 / 2, 0]), "pushed sideways, right"), (u * C2 / 2 - np.array([C2 / 2, 0]), "pushed sideways, left")):
        leak_test(f"closed {side} side, blade {w}, cloud", base + printed + [f"blade_PHI{sg * TH}|{d[0]:.3f},{d[1]:.3f}", "wheel_STOP2"], N // 2)
leak_test("open at the middle click (sanity: light must get in, and only through the lens port)", base + printed + ["blade_PHI0.0", "wheel_STOP2"], N // 4)
json.dump(res, open("build/optics.json", "w"), indent=1)
