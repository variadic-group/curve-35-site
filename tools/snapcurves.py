"""How every click and latch feels: force against travel, from the spring stiffnesses of the finite-element models and the cam
shapes in the model (45-degree notch ramps, the latch ramps), with friction 0.35.  Quasi-static.
Writes build/snapcurves.json and build/snapcurves.png."""
import sys, json, numpy as np
sys.path.insert(0, "tools")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LY = json.load(open("build/layout.json")); B = LY["B"]; F = json.load(open("build/fea.json")); PS = json.load(open("build/printsim.json")); MU = 0.35; TH = np.radians(B["THETA"]); H = B["H"]
fe = lambda key, *has: [v for k, v in F.items() if k.startswith(key) and all(h in k for h in has)][0]
d0 = B["BUMP"] - B["SCL"] - B["HUBC"]; K_BL = fe("blade click spring", "as drawn")["force_N"] / d0; K_WH = fe("wheel click spring", "as drawn")["force_N"] / d0
RWB = B["R_OUT"] + B["SLIT"] + B["BL_T"] + B["SCL"]; RWW = B["WHEEL_R"] + B["SLIT"] + B["WH_T"] + B["SCL"]; geom = __import__("geom"); PX, PZ = geom.press_point(B); ZF = lambda psi: PX * np.sin(psi) + PZ * np.cos(psi); LEV = lambda psi: PX * np.cos(psi) - PZ * np.sin(psi)      # the finger on the raised side of the rocker: its height and its lever arm against the blade's angle
def wall(s, notches):                                  # how deep the wall's surface is at s (0 = its face); notches: [(s0, depth)]
    r = np.zeros_like(s)
    for s0, d in notches: u = np.abs(s - s0); r = np.maximum(r, np.clip(d - np.maximum(u - 0.35, 0), 0, d))
    return r
def cam(s, notches, b, k, rt=0.7):
    """tooth of radius rt, pushed in b on the plain wall: spring deflection and the force along the wall needed to move it in +s"""
    u = np.linspace(-rt, rt, 81); E = np.min(wall(s[:, None] + u[None, :], notches) - np.sqrt(rt ** 2 - u[None, :] ** 2), 1)      # where the wall lets the tooth's centre sit
    d = np.maximum(0, (b - rt) - E); m = np.gradient(d, s); N = k * d; return d, N * (m + MU) / np.maximum(1 - MU * m, 0.05)
CASES = [("thin printer", "#86b6ef"), ("typical printer", "#2a78d6"), ("fattest printer", "#104281")]; out = {}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": "#c9c8c3", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.titlecolor": "#0b0b0b"})
fig, ax = plt.subplots(2, 2, figsize=(13.5, 9.2), facecolor="#fcfcfb")
def style(a, title, xl, yl):
    a.set_facecolor("#fcfcfb"); a.set_title(title, fontsize=13, loc="left", pad=10); a.set_xlabel(xl); a.set_ylabel(yl); a.grid(color="#e9e8e3", lw=0.8); a.axhline(0, color="#c9c8c3", lw=1)
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
# ---- shutter: one sweep of the paddle, closed -> open notch -> closed
s = np.linspace(-TH * RWB - 0.2, TH * RWB + 0.2, 2400); notches = [(-TH * RWB, B["BUMP"]), (0.0, 0.3), (TH * RWB, B["BUMP"])]; a = ax[0, 0]; out["shutter"] = {}
for name, col in CASES:
    b = PS[name]["blade"]["pushed_in"]; d, Ft = cam(s, notches, b, K_BL); psi = -s / RWB; x = ZF(-s[0] / RWB) - ZF(psi); f = Ft * RWB / LEV(psi); a.plot(x, f, color=col, lw=2, label=name)
    out["shutter"][name] = dict(tooth_pushed_in_mm=round(b, 2), click_N=round(float(f.max()), 2), glide_N=round(float(np.median(f[(np.abs(s) > 1.5) & (np.abs(s) < 6)])), 2), finger_travel_mm=round(float(x[-1]), 1), pulled_home_N=round(float(f.min()), 2))
    a.annotate(f"{f.max():.1f} N", (x[np.argmax(f)], f.max()), textcoords="offset points", xytext=(6, 2), color="#0b0b0b", fontsize=10)
style(a, "Shutter tab: one push across", "tab travel, mm", "force on the finger, N"); a.legend(frameon=False, loc="upper right")
a.text(0.52, 0.92, "the tooth climbs out\nof the closed notch", fontsize=9.5, color="#52514e", va="center"); a.text(2.72, 0.72, "open notch\n(time exposures)", fontsize=9.5, color="#52514e", va="center"); a.text(3.3, -0.2, "pulled into\nthe far notch", fontsize=9.5, color="#52514e", va="center")
# ---- aperture handle: P -> S -> C
sw = np.radians(np.array(B["WPOS"])) * RWW; s = np.linspace(-0.2, sw[-1] + 0.2, 2400); notches = [(q, B["BUMP"]) for q in sw]; a = ax[0, 1]; out["aperture"] = {}
for name, col in CASES:
    b = PS[name]["wheel"]["pushed_in"]; d, Ft = cam(s, notches, b, K_WH); x = (s - s[0]) * B["H_RHO"] / RWW; f = Ft * RWW / B["H_RHO"]; a.plot(x, f, color=col, lw=2, label=name)
    out["aperture"][name] = dict(tooth_pushed_in_mm=round(b, 2), click_N=round(float(f.max()), 2)); a.annotate(f"{f.max():.1f} N", (x[np.argmax(f)], f.max()), textcoords="offset points", xytext=(6, 2), color="#0b0b0b", fontsize=10)
style(a, "Aperture handle: P to S to C", "handle travel, mm", "force on the finger, N"); a.legend(frameon=False, loc="upper right")
for q, lab in zip(sw * B["H_RHO"] / RWW + 0.2 * B["H_RHO"] / RWW, "PSC"): a.annotate(lab, (q, a.get_ylim()[0]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=12, color="#0b0b0b", fontweight="bold")
# ---- back: pressing it on (two latches), then pinching the pads
kn = fe("back latch finger, nub", "as drawn")["force_N"] / float(fe("back latch finger, nub", "as drawn")["name"].split("pushed down ")[1].split(" mm")[0]); a = ax[1, 0]; out["back"] = {}
_cl = lambda has: float([k for k in F if k.startswith("back latch finger, nub") and "closing the back" in k and has in k][0].split("pushed down ")[1].split(" mm")[0]); E_BK0, E_BK1 = _cl("as drawn"), _cl("0.25 fat")   # v2.14: how far the nub really goes down as the back closes (these were 0.5 and 0.8, from an older latch)
t = np.linspace(0, 5.2, 800)
for name, col, eng in (("as drawn", "#2a78d6", E_BK0), ("fattest printer", "#104281", E_BK1)):
    rise = eng / 0.6; d = np.where(t < 0.5, 0, np.where(t < 0.5 + rise, (t - 0.5) * 0.6, np.where(t < 0.5 + rise + 3.7 - rise, eng, 0.0))); m = np.gradient(d, t); m[m < 0] = 0
    f = 2 * kn * (1.0 if name == "as drawn" else 1.8) * d * (m + MU) / (1 - MU * m); a.plot(t, f, color=col, lw=2, label=name); out["back"][name] = dict(nub_pushed_down_mm=eng, peak_push_N=round(float(f.max()), 2), slide_N=round(float(np.median(f[d >= eng * 0.99])), 2))
    a.annotate(f"{f.max():.1f} N", (t[np.argmax(f)], f.max()), textcoords="offset points", xytext=(6, 2), color="#0b0b0b", fontsize=10)
pad = fe("back latch finger, pad", "clear by 0.1", "as drawn"); out["back"]["to_open_per_pad_N"] = pad["force_N"]; out["back"]["to_open_per_pad_fattest_N"] = fe("back latch finger, pad", "clear by 0.1", "0.25 fat")["force_N"]
style(a, "Back: pressing it on (both latches)", "travel of the back over the last 5 mm, mm", "push, N"); a.legend(frameon=False, loc="upper right")
a.annotate("both nubs snap up\nbehind their bars: click", (0.80, 0.22), xycoords="axes fraction", fontsize=9.5, color="#52514e", ha="center"); a.annotate("to open: pinch the two pads, %.1f N each" % pad["force_N"], (0.03, 0.90), xycoords="axes fraction", fontsize=9.5, color="#52514e")
# ---- front plate: sliding it on
# v2.14: this part still drew the tongue latch that the leaf replaced in v2.9.  Now: the leaf's own spring force (finite elements) on the bump's two faces (62 degrees going on, 38 coming off, from the model)
import re as _re; _sc = open("scad/one135.scad").read(); RAMP, RAKE = (float(_re.search(r"LF_%s = ([0-9.]+)" % n, _sc).group(1)) for n in ("RAMP", "RAKE")); a = ax[1, 1]; out["front_plate"] = {}
face = lambda N, ang, mu: N * (np.tan(np.radians(ang)) + mu) / (1 - mu * np.tan(np.radians(ang)))
for name, col, key in (("as drawn", "#2a78d6", "as drawn"), ("fattest printer", "#104281", "no slack")):
    c = fe("plate latch leaf", key); lift = float(_re.search(r"lifted ([0-9.]+) mm", [k for k in F if k.startswith("plate latch leaf") and key in k][0]).group(1)); t = np.linspace(0, lift, 200); f = face(c["force_N"] * t / lift, RAMP, MU)
    a.plot(t, f, color=col, lw=2, label=name); out["front_plate"][name] = dict(tongue_bent_mm=lift, leaf_force_N=round(c["force_N"], 2), peak_push_N=round(float(f.max()), 2), peak_push_smooth_plastic_N=round(float(face(c["force_N"], RAMP, 0.2)), 2))
    a.annotate(f"{f.max():.1f} N", (t[-1], f.max()), textcoords="offset points", xytext=(-34, 2), color="#0b0b0b", fontsize=10)
out["front_plate"]["to_release_press_N"] = round(float(face(fe("plate latch leaf", "as drawn")["force_N"], RAKE, MU)), 2)
out["front_plate"]["note"] = "estimate: the leaf's spring force from finite elements, on a flat ramp with friction 0.35 (0.2 for smooth plastic).  Sliding the plate back off needs only to_release_press_N: the side lips are what keep a knocked plate on"
style(a, "Front plate: sliding it on (estimate)", "post lifted, mm", "push, N"); a.legend(frameon=False, loc="upper right")
a.annotate("the post drops behind\nthe bump: click", (0.30, 0.72), xycoords="axes fraction", fontsize=9.5, color="#52514e", ha="center"); a.annotate("to take it off: slide it back up (about %.1f N)" % out["front_plate"]["to_release_press_N"], (0.03, 0.90), xycoords="axes fraction", fontsize=9.5, color="#52514e")
fig.suptitle("What each click and latch feels like (calculated)", fontsize=15, x=0.02, ha="left", color="#0b0b0b"); plt.tight_layout(rect=(0, 0, 1, 0.96)); plt.savefig("build/snapcurves.png", dpi=80, facecolor="#fcfcfb")
json.dump(out, open("build/snapcurves.json", "w"), indent=1)
for k, v in out.items(): print(k, json.dumps(v))
