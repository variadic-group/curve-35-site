"""The printer lottery.  Twenty thousand cameras, each printed on a printer drawn at random, in a plastic drawn at random,
with a friction drawn at random.  For each one: does every moving part work as it comes off the bed, with no tuning?

Nothing is re-run here.  The end cases (tools/endcases.py: every click followed along its real wall at four wall errors),
the fit check (tools/tolerance.py: six printers, and a seventh at +0.20 mm) and the exposure model (tools/exposure.py) are read and interpolated.
A printer outside what those cover (walls thinner than -0.15 mm or fatter than +0.25 mm) counts as a failure.
This is an ESTIMATE of how often the design forgives the printer, not a measurement.  Writes build/lottery.json, LOTTERY.md."""
import json, sys, numpy as np, trimesh
N = 20000; rng = np.random.default_rng(135)
LY = json.load(open("build/layout.json")); B = LY["B"]; EC = json.load(open("build/endcases.json")); EX = json.load(open("build/exposure.json")); TOL = json.load(open("build/tolerance.json"))
MUS = np.array([0.2, 0.35, 0.45]); E0 = np.array([v["wall_error"] for v in EC["shutter"].values()])
def at_e(sec, key, e, mu=None):
    """a result of the end cases, read off at wall error e (and friction mu, where it was run at three)"""
    rows = list(EC[sec].values()); v = np.array([r[key] for r in rows], float)
    if v.ndim == 1: return np.interp(e, E0, v)
    per = np.array([np.interp(e, E0, v[:, j]) for j in range(3)])                              # 3 x n
    w = np.clip((mu - MUS[0]) / (MUS[-1] - MUS[0]), 0, 1); i = np.where(mu < MUS[1], 0, 1); t = np.where(mu < MUS[1], (mu - MUS[0]) / (MUS[1] - MUS[0]), (mu - MUS[1]) / (MUS[2] - MUS[1]))
    return per[i, np.arange(len(e))] * (1 - t) + per[i + 1, np.arange(len(e))] * t
# the blade's own weight tries to turn it when the camera is held on its side: mass x g x (pivot to centre of mass)
bm = trimesh.load("build/asm/blade_PHI%s.stl" % B["THETA"], process=True); cm = bm.center_mass; P = np.array(B["P_S"])
GRAV = bm.volume * 1.24e-3 * 1e-3 * 9.81 * float(np.hypot(cm[0] - P[0], cm[2] - P[1]))            # N mm
# exposure of each printer against the reference card (middle hole), in stops
XE = np.array([v["wall_error"] for v in EX["printers"].values()]); XS = np.array([v["stops_vs_typical"][1] for v in EX["printers"].values()]); o = np.argsort(XE); XE, XS = XE[o], XS[o]
# fits: the worst overlap on each of the six printers of the fit check (0 everywhere means nothing binds)
def printer_e(name): return 0.0 if name == "as drawn" else float(name.split("walls ")[1].split(" mm")[0])
try: TOL.update(json.load(open("build/tolerance_between.json")))                                # a seventh printer, +0.20 mm, to find where fits start to bind (python3 tools/lottery.py --between writes it)
except Exception: pass
BIND = {printer_e(k): max([r["mm3"] for n, r in v.items() if isinstance(r, dict) and "mm3" in r and not n.startswith(("HOLD", "blade click", "wheel click", "blade at rest in its notch"))] or [0.0]) for k, v in TOL.items()}

def run(sd_e=0.08, mean_e=0.05, label="any printer"):
    e = rng.normal(mean_e, sd_e, N); mu = rng.uniform(0.2, 0.45, N); stiff = np.clip(rng.normal(1.0, 0.10, N), 0.75, 1.25)   # the plastic: brand, colour, room temperature
    inside = (e >= E0.min()) & (e <= E0.max()); ec = np.clip(e, E0.min(), E0.max())
    T = {}
    T["the shutter turns freely on its post"] = at_e("shutter", "hub_play", ec) > 0.05
    T["the shutter stays shut when the camera is carried (its click holds twice its own weight)"] = at_e("shutter", "hold_at_rest_Nmm", ec, mu) * stiff > 2 * GRAV
    press = at_e("shutter", "press_N", ec, mu) * stiff
    T["the rocker clicks, and a finger can press it (0.4 to 5 N)"] = (press > 0.4) & (press < 5.0)
    T["the shutter's spring has room behind it"] = at_e("shutter", "room", ec) - at_e("shutter", "bend_on_wall_pressed", ec) > 0.2
    strain = at_e("shutter", "strain_pressed_pct", ec)
    T["the shutter's spring stays inside the limit for every shot (0.5 % strain)"] = strain <= 0.5
    turn = at_e("wheel", "turn_N", ec, mu) * stiff
    T["the aperture wheel turns and clicks (0.1 to 4 N at its handle)"] = (turn > 0.1) & (turn < 4.0) & (at_e("wheel", "hub_play", ec) > 0.05)
    T["the wheel's spring stays inside its limit (1 % strain, a few hundred turns)"] = at_e("wheel", "strain_pct", ec) <= 1.0
    T["the front plate slides on and holds (under 10 N on, over 1 N to lose)"] = (at_e("plate", "slide_on_N", ec, mu) * stiff < 10) & (at_e("plate", "hold_N", ec, mu) * stiff > 1.0)
    T["the back's latches catch, even with the back pushed away (0.2 mm or more)"] = at_e("back", "nub_engagement_back_pushed_away", ec) >= 0.2
    T["the back's fingers stay inside their limit when it is opened (1 % strain)"] = at_e("back", "strain_opening_pct", ec) <= 1.0
    stops = np.interp(ec, XE, XS)
    T["exposure within one stop of the reference card (before the finger and the light)"] = np.abs(stops) <= 1.0
    T["no two parts are drawn into each other (fit check, seven printers)"] = np.interp(ec, sorted(BIND), [BIND[k] for k in sorted(BIND)]) < 0.05
    ok = inside.copy(); res = {}
    for k, v in T.items(): v = v & inside; res[k] = float(v.mean()); ok &= v
    works = ok | (inside & np.all([v for k, v in T.items() if "inside" not in k and "limit" not in k], axis=0))      # works today; a spring over its long-life limit is counted apart
    return dict(label=label, mean_wall_error=mean_e, sd_wall_error=sd_e, outside_modelled_range=float(1 - inside.mean()), tests=res,
                everything_inside_every_limit=float(ok.mean()), works_as_printed=float(works.mean()),
                press_N_5_50_95=[float(np.percentile(press[inside], q)) for q in (5, 50, 95)], shutter_strain_5_50_95=[float(np.percentile(strain[inside], q)) for q in (5, 50, 95)],
                exposure_stops_5_50_95=[float(np.percentile(stops[inside], q)) for q in (5, 50, 95)])
if __name__ == "__main__":
    if sys.argv[1:] == ["--between"]:
        sys.path.insert(0, "tools"); sys.argv = sys.argv[:1]; import tolerance; lab = "walls +0.20 mm, elephant's foot 0.30"; json.dump({lab: tolerance.run(0.20, 0.30, lab)}, open("build/tolerance_between.json", "w"), indent=1); sys.exit()
    CASES = [run(0.08, 0.05, "any printer, as it comes (walls +0.05 +/- 0.08 mm: the spread tools/exposure.py uses)"),
             run(0.04, 0.05, "a kept printer: a print farm, or a home printer in good order (+0.05 +/- 0.04 mm)"),
             run(0.025, 0.0, "any printer after the fit gauge and tools/tune.py (what is left: +/- 0.025 mm, one slot of the gauge)")]
    out = dict(model=LY.get("model", "ONE-135"), cameras=N, blade_weight_torque_Nmm=GRAV, fit_check_worst_overlap_mm3=BIND, cases=CASES)
    json.dump(out, open("build/lottery.json", "w"), indent=1)
    L = ["# The printer lottery", "", "Twenty thousand cameras, each on a printer, a plastic and a friction drawn at random. Does every moving part work as it",
         "comes off the bed? An estimate from the end cases, the fit check and the exposure model (`tools/lottery.py`); nothing here is measured.", ""]
    for c in CASES:
        L += ["## " + c["label"], "", "| | cameras |", "|---|---|"] + [f"| {k} | {100 * v:.1f} % |" for k, v in c["tests"].items()]
        L += [f"| **works as printed** (everything except the two long-life limits) | **{100 * c['works_as_printed']:.1f} %** |", f"| **and inside every limit** | **{100 * c['everything_inside_every_limit']:.1f} %** |",
              f"| outside what was modelled (walls under -0.15 or over +0.25 mm; counted as failed) | {100 * c['outside_modelled_range']:.1f} % |", "",
              "Rocker's click at the finger: %.1f N (5 %% of cameras under %.1f, 5 %% over %.1f). Shutter spring, pressed: %.2f %% strain (%.2f to %.2f). Exposure against the card: %+.1f stops (%+.1f to %+.1f)."
              % (c["press_N_5_50_95"][1], c["press_N_5_50_95"][0], c["press_N_5_50_95"][2], c["shutter_strain_5_50_95"][1], c["shutter_strain_5_50_95"][0], c["shutter_strain_5_50_95"][2],
                 c["exposure_stops_5_50_95"][1], c["exposure_stops_5_50_95"][0], c["exposure_stops_5_50_95"][2]), ""]
    L += ["## What it does not know", "", "Warping, a bed that is not level, strings, a damp spool, layers that did not bond, supports left on, a part printed in",
          "another direction than its file lies. `tools/printrules.py` and the print cards are there for those; the fit gauge finds the wall error.", ""]
    open("LOTTERY.md", "w").write("\n".join(L)); print("\n".join(L))
