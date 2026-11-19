"""How sharp is the picture, and how much does it depend on the lens sitting in the right place?

The model lens (the 32 mm plastic meniscus the gate was drawn round) is traced through focus on the curved film, at the three dots.
Blur is given as the diameter of the even disc with the same RMS radius, in mm on the film, so it can be read against the usual rule:
  0.03 mm  sharp on a big print (20 x 25 cm)      0.05 mm  sharp on a postcard (10 x 15 cm)      0.11 mm  sharp on a phone
(each is 0.2 mm on the thing you look at, from 30 cm).  Then: what the errors of a real camera do to that, and where the seat should be.
Model only: nothing has been printed or shot."""
import sys, json, re, numpy as np
sys.path.insert(0, "/home/claude/cam/optics"); sys.argv = ["x"]
from design import *
R = "/home/claude/one/"; X = json.load(open("/home/claude/cam/optics/res_plastic_R32.json"))["x"]; EXP = json.load(open(R + "build/exposure.json"))
HOLES = [q["hole_mm"] for q in EXP["printers"]["typical"]["stops"]]; DOTS = ("small", "middle", "large"); NS = [32.0 / h for h in HOLES]
FLD = {"middle": (0, 0), "half-way out": (16 * DEG, 0), "ends": (32 * DEG, 0), "corners": (32 * DEG, 20.5 * DEG)}
DISC = 2 * np.sqrt(2)                                     # RMS radius -> diameter of the even disc
SEAT = float(re.search(r"^LENS_SEAT = ([0-9.]+)", open(R + "scad/one135.scad").read(), re.M).group(1))
PAR = float(efl(plastic_meniscus(X, N=10))[1] - X[4])     # the lens's own far-subject focus (paraxial) lies this far behind the film plane its designer's optimiser chose (0.19 mm)
def L_of(seat): return 0.27 + (seat - 0.8)                # how far the film stands behind that optimiser plane (0.27 at LENS_SEAT = 0.8)
def set_for(seat): return (32.0 ** 2 / (L_of(seat) - PAR) + 32) / 1000 if L_of(seat) > PAR else None
L0 = L_of(SEAT)
GRADES = (("a big print", 0.03), ("a postcard", 0.05), ("a phone", 0.11))
def shift(s_m): return 0.0 if s_m is None else 32.0 ** 2 / (s_m * 1000 - 32.0)      # how far behind the far-subject focus a subject at s metres comes to a focus
US = np.round(np.arange(-2.2, 2.81, 0.05), 3)
def curves(seat):
    out = {}
    for d, N in zip(DOTS, NS):
        s = plastic_meniscus([X[0], X[1], X[2] + seat - 0.8, X[3]], N=N); out[d] = {k: [] for k in FLD}      # the hole is in the wheel: a lens that sits further out is that much further from it
        for u in US:
            sp = spots(s, list(FLD.values()), X[4] + u, 32.0, 6)
            for k, r in zip(FLD, sp): out[d][k].append(float(rms_radius(r)[0]) * DISC)
    return out
CS = {0.8: curves(0.8)}; CS[SEAT] = CS.get(SEAT) or curves(SEAT); C = CS[SEAT]
def use(seat):
    global C, L0; C = CS[seat]; L0 = L_of(seat)
def blur(dot, field, lens, s_m): return float(np.interp(lens - shift(s_m), US, C[dot][field]))     # lens: mm in front of its far-subject place
def grade(b): return next((n for n, lim in GRADES if b <= lim * 1.05), "soft")
print("LENS_SEAT %.1f: film %.2f mm behind the lens's far-subject focus: set for %.1f m.   (At 0.8 it was %.2f mm: set for %.1f m, not the 3.8 m written before.)" % (SEAT, L0 - PAR, set_for(SEAT), L_of(0.8) - PAR, set_for(0.8)))
out = {"model": "ONE-135 v2.14", "lens_seat": SEAT, "set_for_m": round(set_for(SEAT), 1), "at_seat_0.8_set_for_m": round(set_for(0.8), 1), "f_numbers": dict(zip(DOTS, [round(n, 1) for n in NS])), "grades_mm": dict(GRADES)}
DIST = (None, 4, 2, 1.5, 1)
print("0. the seat moved one layer: blur in the middle of the picture, mm (0.8 -> %.1f)" % SEAT); out["seat_change"] = {}
for d in DOTS:
    row = {}
    for lab, s_ in (("far", None), ("4 m", 4), ("2 m", 2), ("1.5 m", 1.5)):
        use(0.8); a = blur(d, "middle", L0, s_); use(SEAT); b = blur(d, "middle", L0, s_); row[lab] = (round(a, 3), round(b, 3))
    out["seat_change"][d] = row; print("  %-7s " % d + "   ".join("%s %.3f -> %.3f" % (k, v[0], v[1]) for k, v in row.items()))
print("1. as drawn (lens in its place): blur on the film, mm")
out["as_drawn"] = {}
for d in DOTS:
    out["as_drawn"][d] = {}
    for f in FLD:
        row = [blur(d, f, L0, s) for s in DIST]; out["as_drawn"][d][f] = dict(zip(("far", "4 m", "2 m", "1.5 m", "1 m"), [round(b, 3) for b in row]))
        print("  %-7s %-13s " % (d, f) + "  ".join("%s %.3f" % (("far" if s is None else "%g m" % s), b) for s, b in zip(DIST, row)))
# ---------------------------------------------------------------- 2. how touchy
print("\n2. the lens out of place (+ = too far from the film): middle of the picture")
ERR = (-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 1.0, 1.3, 2.3); out["out_of_place"] = {}
for d in DOTS:
    out["out_of_place"][d] = {}
    for lab, s in (("far", None), ("4 m", 4), ("2 m", 2)):
        row = [blur(d, "middle", L0 + e, s) for e in ERR]; out["out_of_place"][d][lab] = dict(zip(["%+.1f" % e for e in ERR], [round(b, 3) for b in row]))
        print("  %-7s %-4s " % (d, lab) + "  ".join("%+.1f:%.3f" % (e, b) for e, b in zip(ERR, row)))
def window(d, lim, s_list=(None, 4, 2)):                  # how far the lens may sit from its place with far, 4 m and 2 m all inside the limit, in the middle of the picture
    es = np.round(np.arange(-1.5, 2.51, 0.01), 2); ok = [all(blur(d, "middle", L0 + e, s) <= lim for s in s_list) for e in es]
    return (float(es[ok][0]), float(es[ok][-1])) if any(ok) else None
out["room"] = {d: {n: window(d, lim) for n, lim in GRADES} for d in DOTS}
out["sharp_from_m"] = {}
for d in DOTS:
    ss = np.arange(0.5, 30, 0.01); out["sharp_from_m"][d] = {n: (lambda ok: round(float(ss[ok][0]), 2) if ok.any() else None)(np.array([blur(d, "middle", L0, s_) <= lim for s_ in ss])) for n, lim in GRADES}
print("\n   room for the lens (far, 4 m and 2 m all sharp in the middle):")
for d in DOTS: print("  %-7s " % d + "   ".join("%s: %s" % (n, "none" if w is None else "%+.2f to %+.2f mm" % w) for n, w in out["room"][d].items()))
# ---------------------------------------------------------------- 3. real cameras
rng = np.random.default_rng(7); NMC = 20000
def errors(kind):
    e = rng.normal(0, 0.05, NMC) + rng.normal(0, 0.07, NMC)                         # the seat's height in the plate (whole layers); the body, from film rails to its front face
    e += rng.uniform(0, 0.15, NMC)                                                  # the film standing off its rails, behind the picture: one way only
    e += np.where(rng.random(NMC) < 0.1, rng.uniform(0, 0.3, NMC), 0.0)             # one lens in ten not pressed quite home: one way only
    if kind == "kit": e += rng.normal(0, 0.08, NMC) + rng.uniform(-0.1, 0.1, NMC)   # lenses of one batch differ a little; the batch is set to the nearest layer
    if kind == "maker": e += rng.uniform(-0.5, 0.5, NMC)                            # some other 32 mm lens, seat not checked
    if kind == "31 mm": e += 1.0 + rng.uniform(-0.3, 0.3, NMC)                      # a 31 mm lens on the 32 mm seat
    if kind == "30 mm": e += 2.0 + rng.uniform(-0.3, 0.3, NMC)
    return e
def share(kind, seat=0.0):
    e = errors(kind) + seat; res = {}
    for d in DOTS:
        res[d] = {}
        for lab, s in (("far", None), ("4 m", 4), ("2 m", 2)):
            b = np.interp(L0 + e - shift(s), US, C[d]["middle"]); res[d][lab] = {n: round(float(np.mean(b <= lim * 1.05)), 3) for n, lim in GRADES}
    return res
print("\n3. real cameras: share that are sharp in the middle of the picture (postcard / phone)")
out["cameras"] = {}
for kind, text in (("kit", "kit: our lens, seat set for the batch"), ("maker", "own print, another 32 mm lens, seat not checked"), ("31 mm", "a 31 mm lens in this plate"), ("30 mm", "a 30 mm lens in this plate")):
    out["cameras"][kind] = share(kind); print("  " + text)
    for d in DOTS: print("     %-7s " % d + "   ".join("%s %3.0f %% / %3.0f %%" % (lab, 100 * v["a postcard"], 100 * v["a phone"]) for lab, v in out["cameras"][kind][d].items()))
# ---------------------------------------------------------------- 4. where should the seat be?
print("\n4. kit cameras, seat 0.8 against %.1f: share sharp on a postcard in the middle (far / 4 m / 2 m)" % SEAT)
out["seat_cameras"] = {}
for seat in (0.8, SEAT):
    use(seat); rng = np.random.default_rng(7); r = share("kit"); out["seat_cameras"]["%.1f" % seat] = {d: {k: r[d][k]["a postcard"] for k in r[d]} for d in DOTS}
    print("  seat %.1f:  " % seat + "   ".join("%s %3.0f / %3.0f / %3.0f %%" % (d, 100 * r[d]["far"]["a postcard"], 100 * r[d]["4 m"]["a postcard"], 100 * r[d]["2 m"]["a postcard"]) for d in DOTS))
use(SEAT)
# ---------------------------------------------------------------- 5. reading a check picture; rings
print("\n5. the check picture: five things at 1, 1.5, 2, 4 m and far, large dot.  Which is sharpest, by where the lens really sits")
out["check"] = []; FIVE = (1, 1.5, 2, 4, None); nm = lambda s_: "far" if s_ is None else "%g m" % s_
for lay in range(-3, 5):
    e = 0.2 * lay; b = [blur("large", "middle", L0 + e, s_) for s_ in FIVE]; k = int(np.argmin(b)); out["check"].append(dict(lens_from_its_place_mm=round(e, 1), sharpest=nm(FIVE[k]), blur=[round(q, 3) for q in b], move_seat_layers=-lay))
    print("  lens %+.1f mm: sharpest %-5s (%s)  -> move the seat %+d layers" % (e, nm(FIVE[k]), "  ".join("%s %.3f" % (nm(s_), q) for s_, q in zip(FIVE, b)), -lay))
print("\n6. a ring under the lens")
out["rings"] = {}
for t in (0.4,):
    s0 = (32.0 ** 2 / (L0 + t - PAR) + 32) / 1000; rr = {}
    for d in DOTS:
        ss = np.arange(0.4, 30, 0.01); ok = [blur(d, "middle", L0 + t, s) <= 0.05 for s in ss]; rr[d] = (round(float(ss[ok][0]), 2), round(float(ss[ok][-1]), 2)) if any(ok) else None
    out["rings"]["%.1f" % t] = dict(set_for_m=round(s0, 2), sharp_on_a_postcard_m=rr); print("  %.1f mm: set for %.2f m; sharp on a postcard " % (t, s0) + "  ".join("%s %s" % (d, "%.1f to %.1f m" % rr[d] if rr[d] else "-") for d in DOTS))
out["curves"] = dict(u=[float(u) for u in US], blur={d: {k: [round(b, 4) for b in v] for k, v in C[d].items()} for d in DOTS})
json.dump(out, open(R + "build/focus.json", "w"), indent=1); print("\nbuild/focus.json")
