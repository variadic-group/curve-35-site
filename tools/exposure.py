"""Exposure budget for ONE-135: does printer error in the aperture holes and in the shutter's spring compound, and which films and light does
the camera cover?  Everything is computed, nothing is measured: read the assumptions.

1. HOLES.  The aperture wheel is sliced (PrusaSlicer), its top layer is rebuilt bead by bead (as tools/printsim.py does) and every side wall is
   moved by the printer's error e.  The three stops and the blade's window are measured in that rebuilt layer.
2. TIME.   The click's threshold (finite-element stiffness x 1.8 mm, scaled with the spring's printed thickness cubed) and a finger behind it
   accelerate the blade; the window's passage over the stop is integrated (two circles, with the blade hanging on its boss while pressed).
3. LIGHT.  Exposure against the sunny-16 family of light levels for ISO 50 to 800, in stops over (+) or under (-).
Writes build/exposure.json."""
import sys, json, numpy as np, trimesh, shapely
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
sys.path.insert(0, "tools"); import geom
from slicecheck import slice_part, parse, offset, LH
LY = json.load(open("build/layout.json")); B = LY["B"]; C = np.array(B["c"]); F = json.load(open("build/fea.json"))
from scadr import values
WIN_IN = values(["WIN_IN"])["WIN_IN"]                                    # how far the window is drawn toward the pivot (0 up to v2.7)
FOCAL = 32.0; TAU = 0.92; WIN_R = 2.8; HOLE_SHRINK = 0.05                 # lens; its transmission (one uncoated element); the blade's window as drawn; what a small hole loses beyond the wall error (radius)
PRINTERS = [(-0.15, "far too thin"), (-0.08, "thin"), (0.0, "exact"), (0.10, "typical"), (0.15, "fat"), (0.25, "far too fat")]
LIGHT = [(15, "full sun"), (14, "hazy sun"), (13, "bright cloud"), (12, "overcast"), (11, "open shade")]
LATITUDE = (-1.0, 3.0)                                                    # what colour negative film forgives, stops under / over
rng = np.random.default_rng(7)
# ---------------------------------------------------------------- 1. holes
def top_layer():
    layers, _ = parse(slice_part("wheel", True)); m = trimesh.load("build/print/one135_wheel.stl", process=True); off = offset(layers, m)
    seg = np.array(layers[min(layers, key=lambda q: abs(q - 1.0))]); w = np.clip(seg[:, 4], 0.12, 0.95) + LH * (1 - np.pi / 4)
    beads = [LineString([(a - off[0], b - off[1]), (c - off[0], d - off[1])]).buffer(ww / 2, 6) for (a, b, c, d, _), ww in zip(seg, w)]
    return shapely.affinity.scale(unary_union(beads).buffer(0.03).buffer(-0.03), 1, -1, origin=(0, 0))        # the wheel prints mirrored: print (X, Y) -> world (x, -Y)
LAYER = top_layer()
def holes(e):
    lay = LAYER.buffer(e + HOLE_SHRINK, 12); out = []                                # a small hole prints smaller than its wall error alone says
    for i in range(3):
        hc = C + B["R_HOLE"] * np.array([np.cos(np.radians(B["A_AX"] + B["WPOS"][i])), np.sin(np.radians(B["A_AX"] + B["WPOS"][i]))])
        hole = Point(hc).buffer(4.0).difference(lay); hole = max(hole.geoms, key=lambda g: g.area) if hole.geom_type == "MultiPolygon" else hole
        out.append(dict(area_mm2=hole.area, d_equal_area=2 * np.sqrt(hole.area / np.pi), d_inscribed=2 * lay.boundary.distance(Point(hc))))
    return out
# ---------------------------------------------------------------- 2. time
r0 = [v for k, v in F.items() if k.startswith("blade click spring") and "pressed" in k][0]; K0 = r0["force_N"] / B["PRESSED_B"]
TH = np.radians(B["THETA"]); R_PORT, R_OUT = B["R_PORT"], B["R_OUT"]; RW = R_OUT + B["SLIT"] + B["BL_T"] + B["SCL"]; R_F = geom.tab(B)[1]; LEV = geom.lever(B, B["THETA"])
I_BLADE = 1.24e-3 * (2 * np.radians(B["SPAN"])) * R_OUT ** 4 / 4 + 1.24e-3 * np.radians(B["BL_ARC"] + 5) * ((R_OUT + B["SLIT"] + B["BL_T"]) ** 4 - (R_OUT + B["SLIT"]) ** 4) / 4 + 0.80 * 11.0 ** 2
M_BLADE = I_BLADE / R_F ** 2
def lens(d, r1, r2):
    """area two circles (radii r1, r2, centres d apart) have in common"""
    d = np.abs(d); out = np.zeros_like(d); inside = d <= abs(r1 - r2); out[inside] = np.pi * min(r1, r2) ** 2; k = (~inside) & (d < r1 + r2); dd = d[k]
    a1 = np.arccos(np.clip((dd ** 2 + r1 ** 2 - r2 ** 2) / (2 * dd * r1), -1, 1)); a2 = np.arccos(np.clip((dd ** 2 + r2 ** 2 - r1 ** 2) / (2 * dd * r2), -1, 1))
    out[k] = r1 ** 2 * (a1 - np.sin(2 * a1) / 2) + r2 ** 2 * (a2 - np.sin(2 * a2) / 2); return out
EC = json.load(open("build/endcases.json"))["shutter"]; EC_E = np.array([v["wall_error"] for v in EC.values()]); EC_MU = np.array([0.2, 0.35, 0.45])        # tools/endcases.py: the click followed along its real ramp, at four wall errors
EC_P = np.array([v["press_N"] for v in EC.values()]); EC_K = np.array([v["spring_N_per_mm"] for v in EC.values()]); EC_B = np.array([v["bend_on_wall_pressed"] for v in EC.values()])
def click(e, mu):
    """(force at the finger that lets the click go, N; spring stiffness, N/mm; how far the spring is bent on the wall, mm) for wall error e and friction mu"""
    return float(np.interp(mu, EC_MU, [np.interp(e, EC_E, EC_P[:, j]) for j in range(3)])), float(np.interp(e, EC_E, EC_K)), float(np.interp(e, EC_E, EC_B))
def shot(e, r_stop, mu, m_finger, follow, stiff=1.0):
    """(light through the stop, mm2 s; effective time, s; click at the finger, N)"""
    f0, K, bend = click(e, mu); f_break = stiff * f0; drag = stiff * K * bend * mu * RW / R_F
    acc = max(follow * f_break - drag, 0.02) / ((m_finger + M_BLADE) * 1e-3) * 1e3                   # mm/s2 at the finger
    r_win = WIN_R - (HOLE_SHRINK + e); lateral = 0.85 * max(2 * B["HUBC"] - 2 * e, 0.0) - WIN_IN             # the window prints like any hole; pressed, the blade hangs lower by its hub's play and the window passes that far to one side
    s = np.linspace(0.3, 2 * TH * R_F, 4000); t = np.sqrt(2 * (s - 0.3) / acc); x = (s - TH * R_F) * R_PORT / R_F
    area = lens(np.hypot(x, lateral), r_win, r_stop); light = float(np.trapezoid(area, t)); return light, light / (np.pi * r_stop ** 2), f_break
def stops_over(light_mm2s, ev100, iso):
    """exposure against what the light and the film ask for: the camera gives TAU x light / focal^2 x 4/pi, as t / N^2"""
    t_over_n2 = TAU * light_mm2s * 4 / np.pi / FOCAL ** 2; return float(np.log2(t_over_n2) + ev100 + np.log2(iso / 100))
def spread(e, r_stop, n=400):
    v = np.array([shot(e, r_stop, rng.uniform(0.2, 0.45), rng.uniform(5, 20), rng.uniform(0.5, 1.0))[:2] for _ in range(n)]); return v
out = dict(assumptions=dict(focal_mm=FOCAL, lens_transmission=TAU, friction="0.2 to 0.45", finger="5 to 20 g pushing 0.5 to 1.0 x the click's threshold after it lets go", hole_shrink_mm=HOLE_SHRINK,
                            film_latitude_stops=LATITUDE, spring_N_per_mm=K0), printers={}, coverage={}, budget={})
print("lever at the start of a press %.2f mm; spring %.3f N/mm as drawn; blade feels like %.1f g at the finger" % (LEV, K0, M_BLADE))
print("\n1. what each printer makes of the three holes and of the shutter (median of 400 presses; 5 to 95 % in brackets)")
ref = {}
for e, name in PRINTERS:
    hs = holes(e); row = dict(wall_error=e, stops=[]); line = "  %-13s (%+.2f)" % (name, e)
    for i, h in enumerate(hs):
        r = h["d_equal_area"] / 2; v = spread(e, r); light = np.median(v[:, 0]); teff = np.median(v[:, 1]); lo, hi = np.percentile(v[:, 0], [5, 95])
        if name == "typical": ref[i] = light
        row["stops"].append(dict(hole_mm=round(h["d_equal_area"], 2), f_number=round(FOCAL / h["d_equal_area"], 1), time_s=teff, light_mm2s=light, light_5_95=[lo, hi]))
        line += "   %.2f mm f/%-4.1f 1/%-4d" % (h["d_equal_area"], FOCAL / h["d_equal_area"], round(1 / teff))
    row["click_N"] = shot(e, 1.0, 0.35, 10, 0.75)[2]; line += "   click %.1f N" % row["click_N"]; out["printers"][name] = row; print(line)
print("\n   the same, as exposure against the typical printer (stops; + is more light):")
for e, name in PRINTERS:
    r = out["printers"][name]; d = [np.log2(s["light_mm2s"] / ref[i]) for i, s in enumerate(r["stops"])]; sp = [np.log2(s["light_5_95"][1] / s["light_5_95"][0]) / 2 for s in r["stops"]]
    r["stops_vs_typical"] = d; print("  %-13s  small hole %+.2f   middle %+.2f   large %+.2f     (press to press: +/- %.2f)" % (name, d[0], d[1], d[2], np.mean(sp)))
# ---------------------------------------------------------------- 3. coverage
print("\n2. which hole for which film and light, and how far off the exposure is (stops; typical printer [far too fat .. far too thin])")
L = {name: [s["light_mm2s"] for s in r["stops"]] for name, r in out["printers"].items()}
hdr = "  ISO    " + "".join("%-27s" % l for _, l in LIGHT); print(hdr)
for iso in (50, 100, 200, 400, 800):
    line = "  %-6d " % iso; out["coverage"][iso] = {}
    for ev, lname in LIGHT:
        best = min(range(3), key=lambda i: abs(stops_over(L["typical"][i], ev, iso) - 0.5))                     # aim half a stop over: negative film forgives over far better than under
        t = stops_over(L["typical"][best], ev, iso); lo = stops_over(L["far too fat"][best], ev, iso); hi = stops_over(L["far too thin"][best], ev, iso)
        ok = LATITUDE[0] <= lo and hi <= LATITUDE[1]; ok_typ = LATITUDE[0] <= t <= LATITUDE[1]
        out["coverage"][iso][lname] = dict(hole=["small", "middle", "large"][best], typical=t, far_too_fat=lo, far_too_thin=hi, within_latitude_every_printer=bool(ok), within_latitude_typical=bool(ok_typ))
        line += "%-6s %+.1f [%+.1f..%+.1f] %s  " % (["small", "middle", "large"][best], t, lo, hi, "ok " if ok else ("typ" if ok_typ else "NO "))
    print(line)
# ---------------------------------------------------------------- 4. where the error comes from
print("\n3. where the spread comes from (standard deviation in stops, one cause at a time; the printers are drawn from walls +0.05 +/- 0.08 mm, cut at -0.15 and +0.25)")
def pop(n=3000, vary=("e", "hole", "mu", "finger", "plastic")):
    res = []
    for _ in range(n):
        e = float(np.clip(rng.normal(0.05, 0.08), -0.15, 0.25)) if "e" in vary else 0.05; eh = e if "hole" in vary else 0.05; es = e if "e" in vary else 0.05
        mu = rng.uniform(0.2, 0.45) if "mu" in vary else 0.33; mf, fo = (rng.uniform(5, 20), rng.uniform(0.5, 1.0)) if "finger" in vary else (12.0, 0.75)
        r = 1.45 + 0.15 - (HOLE_SHRINK + eh) + (rng.normal(0, 0.04) if "hole" in vary else 0.0)       # the middle hole: drawn 0.15 over size on radius; 0.04 mm of scatter from seam and bead
        st = rng.uniform(0.8, 1.2) if "plastic" in vary else 1.0                                       # PLA from 2400 to 3600 MPa: brand, colour, a cold or a hot day
        res.append(np.log2(shot(es, r, mu, mf, fo, st)[0]))
    return float(np.std(res))
for key, vary, text in (("spring", ("e",), "printer's wall error, through the shutter spring's thickness and the window"), ("holes", ("hole",), "printer's wall error and scatter, through the size of the hole"),
                        ("friction", ("mu",), "friction of the click (0.2 to 0.45)"), ("finger", ("finger",), "the finger (how heavy, how it follows)"), ("plastic", ("plastic",), "stiffness of the plastic (brand, colour, temperature: +/- 20 %)"), ("all", ("e", "hole", "mu", "finger", "plastic"), "all of these together")):
    out["budget"][key] = pop(vary=vary); print("  %-78s %.2f" % (text, out["budget"][key]))
print("  for comparison: judging the light by eye (sun, haze, cloud) is good to about one stop")
# ---------------------------------------------------------------- 5. focus
print("\n4. focus by the simple rule (tools/focus.py traces the lens and is the one to read): lens 32 mm, set for 3.7 m; a blur of 0.03 mm on the film counts as sharp")
out["focus"] = {}
for i, name in enumerate(("small", "middle", "large")):
    N = FOCAL / out["printers"]["typical"]["stops"][i]["hole_mm"]; hyper = FOCAL ** 2 / (N * 0.03) + FOCAL; s = 3700.0; near = s * (hyper - FOCAL) / (hyper + s - 2 * FOCAL); far = s * (hyper - FOCAL) / (hyper - s) if hyper > s else np.inf
    tol = N * 0.03                                                                                             # how far the lens may sit from its place before a far subject blurs past 0.03 mm (and the same toward near)
    out["focus"][name] = dict(f_number=N, sharp_from_m=near / 1000, sharp_to_m=None if np.isinf(far) else far / 1000, lens_position_tolerance_mm=tol)
    print("  %-6s f/%-4.1f sharp from %.1f m to %s; the lens may sit +/- %.2f mm from its place" % (name, N, near / 1000, "infinity" if np.isinf(far) else "%.0f m" % (far / 1000), tol))
print("\n5. across the frame (light at the film against the middle of the picture; the film is curved round the lens)")
import os
OPT = json.load(open("build/optics.json")) if os.path.exists("build/optics.json") else {}
S0 = np.array([0.0, 25.47 + 1.05, 0.0]); RF_ = 32.0
def natural(t_deg, z):
    t = np.radians(t_deg); P = np.array([RF_ * np.sin(t), RF_ - RF_ * np.cos(t), z]); v = P - S0; d = np.linalg.norm(v); u = v / d; nf = np.array([-np.sin(t), np.cos(t), 0.0])
    return float(-u[1] * (-u @ nf) * (S0[1] / d) ** 2)
gate = np.degrees(18 / RF_); out["frame"] = dict(end_of_frame=natural(gate, 0), top_edge=natural(0, 12), corner_natural=natural(gate, 12), corner=[])
print("  geometry alone: end of the frame %.0f %% (%.1f stop), top edge %.0f %% (%.1f), corner %.0f %% (%.1f)" % tuple(x for q in (natural(gate, 0), natural(0, 12), natural(gate, 12)) for x in (100 * q, np.log2(q))))
for k, v in OPT.items():
    if isinstance(v, dict) and "light_kept_worst_corner" in v:
        c = natural(gate, 12); row = [c * v["light_kept_worst_corner"], c * v.get("worst_corner_thin_printer", v["light_kept_worst_corner"]), c * v.get("worst_corner_fat_printer", v["light_kept_worst_corner"])]
        out["frame"]["corner"].append(dict(stop=k, typical=row[0], thin=row[1], fat=row[2])); print("  %-16s corner with the parts' shadow: %.0f %% (%.1f stop); printer 0.15 thin %.0f %%, 0.25 fat %.0f %%" % (k, 100 * row[0], np.log2(row[0]), 100 * row[1], 100 * row[2]))
print("  diffraction blur (2.44 x 0.55 um x f-number): small hole %.0f um, large %.0f um; 30 um counts as sharp" % (2.44 * 0.55 * FOCAL / out["printers"]["typical"]["stops"][0]["hole_mm"], 2.44 * 0.55 * FOCAL / out["printers"]["typical"]["stops"][2]["hole_mm"]))
json.dump(out, open("build/exposure.json", "w"), indent=1, default=float)
