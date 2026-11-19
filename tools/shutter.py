"""ONE-135 v2.1 shutter estimate.  There is no separate spring: the finger drives the blade through a 4:1 lever, and a click (a tooth
on the blade's sprung rim leaving a notch) makes the finger build up a set force before the blade can move.
The spring's stiffness comes from the finite-element model (build/fea.json) and how far the tooth is pushed in from the print
simulation (build/printsim.json).  This is an ESTIMATE: the finger is a mass with a force behind it."""
import json, numpy as np
B = json.load(open("build/layout.json"))["B"]; TH = np.radians(B["THETA"]); R_PORT = B["R_PORT"]; R_OUT = B["R_OUT"]; SPAN = np.radians(B["SPAN"])
H, PZ = B["H"], B["P_S"][1]; WIN_R = 2.8
import geom; FIN_Z0, R_F = geom.tab(B)           # where the finger pushes
F = json.load(open("build/fea.json"))
# v2.7: while the rocker is pressed the blade hangs on its boss, so the tooth is pushed in PRESSED_B on every printer; what a printer changes is the spring's thickness (cubed)
r0 = [v for k, v in F.items() if k.startswith("blade click spring") and "pressed" in k][0]; d0 = B["PRESSED_B"]; K0 = r0["force_N"] / d0; S = r0["peak_strain_pct"] / d0; K = K0
PS = {n: dict(blade=dict(pushed_in=d0), stiff=((B["BL_T"] + 2 * e) / B["BL_T"]) ** 3) for n, e in (("far too thin, walls -0.15", -0.15), ("thin printer, walls -0.08", -0.08), ("exact printer", 0.0), ("typical printer", 0.10), ("fat printer, walls +0.15", 0.15), ("far too fat, walls +0.25", 0.25))}
RW = R_OUT + B["SLIT"] + B["BL_T"] + B["SCL"]                                                       # radius of the click wall
out = dict(gearing=R_PORT / R_F, finger_radius_mm=R_F, finger_throw_mm=2 * TH * R_F, blade_travel_at_lens_mm=2 * TH * R_PORT, spring_N_per_mm=K, strain_pct_per_mm=S)
def click(bend, mu=0.35, ramp=45.0, K=None):
    K = K0 if K is None else K; a = np.radians(ramp); gain = (np.tan(a) + mu) / (1 - mu * np.tan(a)); Ft = K * bend * gain
    return dict(tooth_pushed_in_mm=bend, spring_force_N=K * bend, peak_strain_pct=S * bend, break_force_at_finger_N=float(Ft * RW / geom.lever(B, B["THETA"])), drag_at_finger_N=float(K * bend * mu * RW / R_F), wedges_shut_above_friction=float(1 / np.tan(a)))
rho, t = 1.24e-3, 1.0
I_blade = rho * t * (2 * SPAN) * R_OUT ** 4 / 4 + rho * t * np.radians(B["BL_ARC"] + 5) * ((R_OUT + B["SLIT"] + B["BL_T"]) ** 4 - (R_OUT + B["SLIT"]) ** 4) / 4 + 0.80 * 11.0 ** 2     # g mm2: the sector, its sprung rim, the rocker (v2.7: 0.8 g about 11 mm out)
m_blade = I_blade / R_F ** 2                                                                        # g, as felt at the finger
def swing(F_break, drag, m_finger, follow):
    """constant push = follow x break force, from the point the click lets go; returns the time the window is over the lens"""
    a = max(follow * F_break - drag, 0.02) / ((m_finger + m_blade) * 1e-3) * 1e3                    # mm/s2 at the finger
    mid = TH * R_F; half = WIN_R / R_PORT * R_F; s0 = 0.3
    tt = lambda s: np.sqrt(2 * max(s - s0, 0) / a)
    return (tt(mid + half) - tt(mid - half)), np.sqrt(2 * a * (2 * mid - s0)) * R_PORT / R_F / 1000   # s, blade speed at the lens m/s
print("gearing %.1f : 1   finger throw %.1f mm   window travels %.1f mm at the lens   blade feels like %.1f g at the finger" % (out["gearing"], out["finger_throw_mm"], out["blade_travel_at_lens_mm"], m_blade))
out["printers"] = {}
for name, v in PS.items():
    c = click(max(v["blade"]["pushed_in"], 0.0), K=K0 * v["stiff"]); ts = []
    for mf in (5, 10, 20):
        for fol in (0.5, 0.75, 1.0): ts.append(swing(c["break_force_at_finger_N"], c["drag_at_finger_N"], mf, fol)[0])
    c["exposure"] = dict(fastest="1/%d" % round(1 / min(ts)), typical="1/%d" % round(1 / np.median(ts)), slowest="1/%d" % round(1 / max(ts))); c["exposure_typical_s"] = float(np.median(ts)); out["printers"][name] = c
    print("%-16s tooth pushed in %.2f mm: click %.2f N at the finger, drag %.2f N, spring strain %.2f %% -> about %s s (%s to %s)" % (name, c["tooth_pushed_in_mm"], c["break_force_at_finger_N"], c["drag_at_finger_N"], c["peak_strain_pct"], c["exposure"]["typical"], c["exposure"]["slowest"], c["exposure"]["fastest"]))
tt = [c["exposure_typical_s"] for c in out["printers"].values()]
out["exposure_range"] = dict(fastest_printer="1/%d" % round(1 / min(tt)), typical_printer="1/%d" % round(1 / out["printers"]["typical printer"]["exposure_typical_s"]), slowest_printer="1/%d" % round(1 / max(tt)))
out["slow_push_0.05_m_s"] = "1/%d" % round(1 / (2 * WIN_R / R_PORT * R_F / 50.0))
out["blade_inertia_g_mm2"] = I_blade; out["blade_mass_felt_at_finger_g"] = m_blade
json.dump(out, open("build/shutter.json", "w"), indent=1)
print("exposure by printer:", out["exposure_range"], "| pushed slowly at 5 cm/s:", out["slow_push_0.05_m_s"])
