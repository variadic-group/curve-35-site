"""ONE-135 interference audit: every pair of parts in every shutter / aperture state, sweeps of the moving parts,
the front plate sliding on and off, the frame wheel going into its fork, the back coming off, and the things that are meant to hold."""
import sys, os, json, itertools, time, numpy as np, trimesh, manifold3d as m3, concurrent.futures as cf
sys.path.insert(0, "tools"); from scadr import export, values
SCAD = "scad/one135.scad"; OUT = "build/asm"; os.makedirs(OUT, exist_ok=True)
THETA = json.load(open("build/layout.json"))["B"]["THETA"]; _v = values(["SLIDE", "XA", "XUP"]); SLIDE, XA, XUP = _v["SLIDE"], _v["XA"], _v["XUP"]; XE = XA - 0.2; LIFT = 2.5      # XE: how far to the side the plate is set on
def tomesh(t): return m3.Manifold(m3.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
def get(name, d):
    tag = name + "".join(f"_{k}{v}" for k, v in sorted(d.items()) if k != "PART")
    f = f"{OUT}/{tag}.stl"
    if not os.path.exists(f) or os.path.getmtime(f) < max(os.path.getmtime(SCAD), os.path.getmtime("scad/layout.scad")): export(SCAD, f, d)
    return f
jobs = {}
for n in ["body", "back", "front", "roller", "knob", "spool", "lens", "cassette", "film", "film_empty"]: jobs[n] = (n, dict(PART=n))
PHIS = [float(round(x, 3)) for x in np.linspace(-THETA, THETA, 23)]
for p in PHIS: jobs[f"bladeN@{p}"] = ("bladeN", dict(PART="blade", PHI=p, BL_BUMP=0.0))       # no bump: for sweeps
for p in (-THETA, 0.0, THETA): jobs[f"blade@{p}"] = ("blade", dict(PART="blade", PHI=p))
for k in range(3): jobs[f"wheel@{k}"] = ("wheel", dict(PART="wheel", STOP=k))
for k in range(3): jobs[f"wheelN@{k}"] = ("wheelN", dict(PART="wheel", STOP=k, WH_BUMP=0.0))             # no tooth: for the tolerance audit
jobs["frontN"] = ("frontN", dict(PART="front", TOOTH_H=0.02))                                   # no latch tooth: for the slide
jobs["backN"] = ("backN", dict(PART="back", NUB_H=0.02))                                        # latch nubs pressed out of the way: for taking the back off
jobs["roller_up"] = ("roller", dict(PART="roller", ROLL_UP=LIFT))
t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex: files = dict(zip(jobs, ex.map(lambda j: get(*j), jobs.values())))
T = {k: trimesh.load(f, process=True) for k, f in files.items()}
M = {k: tomesh(t) for k, t in T.items()}
print("exported and loaded %d meshes in %.0f s" % (len(M), time.time() - t0))
vol = lambda a, b: (M[a] ^ M[b]).volume()
def moved(key, v): t = T[key].copy(); t.apply_translation(v); return tomesh(t)
# expected contacts: wind fork inside the cassette's spool; film inside the cassette lip; sprocket teeth through the perforations
# (the film solid has none); the lens flange pressed onto three crush ribs
ALLOW = {frozenset(x) for x in [("knob", "cassette"), ("film", "cassette"), ("film_empty", "cassette"), ("film", "roller"), ("film_empty", "roller"), ("front", "lens")]}
report = {"states": {}, "sweeps": {}}
STATES = [("closed one side, cloud", THETA, 2), ("closed other side, sun", -THETA, 1), ("closed one side, pinhole", THETA, 0), ("closed other side, cloud", -THETA, 2)]
static = ["body", "back", "front", "roller", "knob", "spool", "lens", "cassette", "film"]
for label, phi, k in STATES:
    names = static + [f"blade@{phi}", f"wheel@{k}"]; bad = []
    for a, b in itertools.combinations(names, 2):
        if frozenset((a.split("@")[0], b.split("@")[0])) in ALLOW: continue
        v = vol(a, b)
        if v > 0.002: bad.append((a, b, round(v, 4)))
    report["states"][label] = bad
    print(f"[{label}] {len(names)} parts, {len(bad)} overlaps", bad)
S = report["sweeps"]
# open: the blade's bump sits in the shallow middle notch, still pressed 0.15 mm into the wall (that is the soft click)
S["open: blade x everything except the click wall"] = round(sum(vol("bladeN@0.0", n) for n in static + ["wheel@1", "wheel@2"]), 4)
S["open: bump pressed into the click wall, mm3 (expected: a little)"] = round(vol("blade@0.0", "front"), 4)
for a, b in [("film_empty", "body"), ("film_empty", "back"), ("film_empty", "spool")]:
    S[f"{a} x {b}"] = round(vol(a, b), 4)
def sweep(keys): return m3.Manifold.batch_boolean([M[k] for k in keys], m3.OpType.Add)
bl = sweep([f"bladeN@{p}" for p in PHIS]); wh = sweep([f"wheel@{k}" for k in range(3)])
for n in ("front", "body", "lens", "back", "knob", "spool", "roller"): S[f"blade sweep (bump removed) x {n}"] = round((bl ^ M[n]).volume(), 4)
S["blade sweep x wheel sweep (the handle fin stands in the blade's plane)"] = round((bl ^ wh).volume(), 4)
for n in ("front", "body", "lens"): S[f"wheel sweep x {n}"] = round((wh ^ M[n]).volume(), 4)
# the bump between notches: how far it is pressed into the wall (it should never jam: the tongue has 0.6 mm to give)
S["bump x click wall along the swing, mm3 (expected > 0 between notches)"] = [round((moved(f"blade@{THETA}", [0, 0, 0]) ^ M["front"]).volume(), 4)]
# front plate goes on (v2.10): set on SLIDE higher and XE to the side, straight onto the body, slid ACROSS, then slid DOWN until it clicks
sub = ["frontN", f"blade@{THETA}", "wheel@2", "lens"]
for dy in (0.5, 1.0, 2.0, 3.0, 6.0):
    S[f"plate at the put-on position, lifted {dy} mm off x body"] = round(sum((moved(n, [-XE, dy, SLIDE]) ^ M["body"]).volume() for n in sub), 4)
for sx in [round(XE * k / 4, 2) for k in range(4, 0, -1)]:
    S[f"plate + shutter {SLIDE} mm above home x body, {sx} mm to the side"] = round(sum((moved(n, [-sx, 0, SLIDE]) ^ M["body"]).volume() for n in sub), 4)
for s in [round(SLIDE * k / 8, 2) for k in range(8, -1, -1)]:
    S[f"plate + shutter {s} mm above home x body"] = round(sum((moved(n, [0, 0, s]) ^ M["body"]).volume() for n in sub), 4)
S["HOLD: plate pushed up 2.5 mm and pulled 1.5 mm off the body x body (> 0 = the side lips hold it where the hooks have let go)"] = round((moved("frontN", [0, 1.5, 2.5]) ^ M["body"]).volume(), 4)
S[f"HOLD: plate at the top ({SLIDE} mm up, not yet moved across) pulled 1.5 mm off x body (> 0 = the side lips hold)"] = round((moved("frontN", [0, 1.5, SLIDE]) ^ M["body"]).volume(), 4)
S["HOLD: plate home, pushed 1.5 mm sideways x body (> 0 = the pockets' walls stop it), least of both ways"] = round(min((moved("frontN", [q, 0, 0]) ^ M["body"]).volume() for q in (-1.5, 1.5)), 4)
S[f"HOLD: plate pushed up {round(XUP - 0.6, 1)} mm (not far enough) and 1.5 mm across x body (> 0 = the wall under the way out stops it)"] = round((moved("frontN", [-1.5, 0, XUP - 0.6]) ^ M["body"]).volume(), 4)
S["latch tooth x body while sliding (expected > 0: the tongue gives)"] = round((moved("front", [0, 0, SLIDE / 2]) ^ M["body"]).volume(), 4)
S["HOLD: plate home, pulled 0.6 mm off the body x body (> 0 = hooks hold)"] = round((moved("front", [0, 0.6, 0]) ^ M["body"]).volume(), 4)
S["HOLD: plate home, pushed 0.9 mm up, toward unlock x body (> 0 = latch holds)"] = round((moved("front", [0, 0, 0.9]) ^ M["body"]).volume(), 4)
S["HOLD: plate home, pushed 0.5 mm down past home x body (> 0 = feet stop it)"] = round((moved("front", [0, 0, -0.5]) ^ M["body"]).volume(), 4)
# frame wheel: raised LIFT it is free to go in and out of its fork; lowered it is held; in the camera the body keeps it down
S["frame wheel raised to the put-in position x back"] = round(vol("roller_up", "back"), 4)
for dy in (1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 9.0, 12.0): S[f"frame wheel raised, moved {dy} mm out of the fork x back"] = round((moved("roller_up", [0, dy, 0]) ^ M["back"]).volume(), 4)
for dz in (0.5, 1.0, 1.5, 2.0): S[f"frame wheel in its fork, raised {dz} mm (on the way up) x back"] = round((moved("roller", [0, 0, dz]) ^ M["back"]).volume(), 4)
S["HOLD: frame wheel (lowered) pulled 1.6 mm out x back (> 0 = the fork's lips hold it)"] = round((moved("roller", [0, 1.6, 0]) ^ M["back"]).volume(), 4)
S["HOLD: frame wheel pushed 0.6 mm down x back (> 0 = the top of the film post carries it)"] = round((moved("roller", [0, 0, -0.6]) ^ M["back"]).volume(), 4)
S["HOLD: frame wheel pushed 0.9 mm up in the closed camera x body (> 0 = the body keeps it down)"] = round((moved("roller", [0, 0, 0.9]) ^ M["body"]).volume(), 4)
S["frame wheel pushed 0.7 mm back into its seat x back (> 0 = the seat carries it)"] = round((moved("roller", [0, -0.7, 0]) ^ M["back"]).volume(), 4)
# knobs: each slides in from the back with its cassette or spool; in the camera it cannot be pulled out
for dy in (1.0, 2.0, 3.0, 4.0, 5.0, 6.5, 8.0, 12.0, 16.0):        # every millimetre near home: up to v2.5 the slot had a neck narrower than the shaft, and only 3, 8 and 16 mm were looked at
    S[f"wind knob + cassette slid {dy} mm out of the back x body"] = round(sum((moved(n, [0, -dy, 0]) ^ M["body"]).volume() for n in ("knob", "cassette")), 4)
    S[f"take-up spool slid {dy} mm out of the back x body"] = round((moved("spool", [0, -dy, 0]) ^ M["body"]).volume(), 4)

for k in ("knob", "spool"):
    S[f"HOLD: {k} pulled up 1.2 mm x body (> 0 = its collar is caught)"] = round((moved(k, [0, 0, 1.2]) ^ M["body"]).volume(), 4)
    S[f"HOLD: {k} pushed 1.5 mm forward or sideways x body (> 0)"] = round(min((moved(k, v) ^ M["body"]).volume() for v in ([0, 1.5, 0], [1.5, 0, 0], [-1.5, 0, 0])), 4)
    S[f"HOLD: {k} pushed 1.5 mm toward the back x back (> 0 = the back's block keeps it in)"] = round((moved(k, [0, -1.5, 0]) ^ M["back"]).volume(), 4)
# the film roll: the ledge under it carries it (in place of a bottom flange), the ledge above stops it climbing
S["HOLD: full film roll pushed 0.6 mm down x body (> 0 = the lower ledge carries the roll)"] = round((moved("film", [0, 0, -0.6]) ^ M["body"]).volume(), 4)
S["HOLD: full film roll pushed 0.6 mm up x body (> 0 = the upper ledge stops it)"] = round((moved("film", [0, 0, 0.6]) ^ M["body"]).volume(), 4)
# back: with the two nubs pressed in it lifts straight off, roller and all; let go of the pads and it is held
for dy in (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 9.0, 12.0): S[f"back + frame wheel (pads pressed) pulled {dy} mm off x body"] = round(sum((moved(n, [0, -dy, 0]) ^ M["body"]).volume() for n in ("backN", "roller")), 4)
S["HOLD: back pulled 0.6 mm off the body x body (> 0 = latches hold)"] = round((moved("back", [0, -0.6, 0]) ^ M["body"]).volume(), 4)
for k, v in S.items(): print(f"  {k}: {v}")
# every step of every way in and out must be free: these rows must all be zero
FREE = ("out of the back x body", "above home x body", "lifted", "raised", "pulled")
report["must_be_zero"] = {k: v for k, v in S.items() if any(q in k for q in FREE) and not k.startswith("HOLD") and "expected" not in k and isinstance(v, float) and abs(v) > 0.002}
print("ways in and out that are NOT free:", report["must_be_zero"] or "none")
bb = np.array([[min(T[n].bounds[0][i] for n in static + [f"blade@{THETA}", "wheel@2"]) for i in range(3)], [max(T[n].bounds[1][i] for n in static + [f"blade@{THETA}", "wheel@2"]) for i in range(3)]])
report["overall_size_mm"] = [round(float(x), 1) for x in (bb[1] - bb[0])]; print("overall size (w, depth, h):", report["overall_size_mm"])
json.dump(report, open("build/check.json", "w"), indent=1)
print("done in %.0f s" % (time.time() - t0))
