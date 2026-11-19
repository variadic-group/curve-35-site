"""Shape search for the shutter's click spring (v2.18).

The spring is the blade's own rim: a curved beam 28 mm long, pushed in by its tooth 2.0 mm on every picture.  Its length is the whole
rim and its outer face is 0.3 mm from the wheel's boss, so a plain beam cannot be made longer or thicker.  This tool searches the one
freedom left: the beam's thickness along its length (BL_T0 at the root, thinning toward the tooth as the square root of the distance
from it, never below BL_T1), for the shape with the lowest peak strain at the SAME force on the tooth, so the click and the shutter's
time do not change.  Every candidate is exported from the model and run through the same finite-element case as tools/fea_cases.py.

    python3 tools/springsearch.py            search, write build/springsearch.json and .png
    python3 tools/springsearch.py 1.74 0.9   one shape
"""
import sys, os, json, itertools, numpy as np, shapely
sys.path.insert(0, os.path.dirname(__file__))
import fea, scadr

LY = json.load(open("build/layout.json")); B = LY["B"]; P = np.array(B["P_S"]); TH = B["THETA"]; YF = 25.47
T_ = B["BL_T"]; R = B["R_OUT"]; PRESSED = B["PRESSED_B"]; REST = B["REST_B"]; LINE = 0.45
os.makedirs("build/springsearch", exist_ok=True)

def arcballs(c, r, a0, a1, step=3.0, rad=2.2, size=0.3):
    n = max(2, int(abs(a1 - a0) * np.pi / 180 * r / step)); return [(c[0] + r * np.cos(np.radians(t)), c[1] + r * np.sin(np.radians(t)), rad, size) for t in np.linspace(a0, a1, n)]

def case(t0, t1, tf=0.0):
    """force per mm at the tooth and peak strain per mm, for one shape (0, 0: the plain beam)"""
    out = f"build/springsearch/blade_{t0:.3f}_{t1:.3f}_{tf:.2f}.stl"
    if not os.path.exists(out): scadr.export("scad/one135.scad", out, dict(PART="blade", PHI=TH, BL_T0=t0, BL_T1=t1, BL_TF=tf))
    bl = fea.section(out, [0, YF + 1.5, 0], [0, 1, 0], [0, 2]); bl = shapely.affinity.rotate(bl, 90 - (B["DB_A"] + TH), origin=tuple(P))
    tip = (P[0], P[1] + R + B["SLIT"] + T_ + B["BUMP"] - 0.02); ra = np.radians(90 - B["BL_ARC"]); root = P + (R + B["SLIT"]) * np.array([np.cos(ra), np.sin(ra)])
    r, f = fea.run(f"spring {t0:.2f} to {t1:.2f}, per 10 mm", bl, lambda x, y: np.where(np.hypot(x - P[0], y - P[1]) < 5.4, 2.0, 1.0), lambda x, y: np.hypot(x - P[0], y - P[1]) < 4.8,
                   [(tip, (None, -10.0))], h=2.5, fine=[(root[0], root[1], 3.5, 0.07)] + arcballs(P, R + B["SLIT"] + T_ / 2, 90 - B["BL_ARC"], 90, step=2.0, rad=2.4, size=0.18))
    return dict(t0=t0, t1=t1, tf=tf, N_per_mm=r["force_N"] / 10, strain_pct_per_mm=r["peak_strain_pct"] / 10,     # pushed 10 mm in the (linear) model, for three more digits
                at=r["at"], area=float(bl.area)), f

def picture(out="build/springsearch.png"):
    """the plain strip and the tapered spring, pressed, side by side on one scale"""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib.colors import LinearSegmentedColormap; from matplotlib.tri import Triangulation
    ramp = LinearSegmentedColormap.from_list("one hue", ["#e8f0fb", "#b7d3f6", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"]); INK, MUTED = "#0b0b0b", "#52514e"; top = 0.55
    shapes = [("Before: a plain strip, 1.35 mm thick", case(0.0, 0.0)), ("v2.18: tapered, 0.9 mm at the tooth to 1.76 mm at the root", case(B["BL_T0"], B["BL_T1"], B["BL_TF"]))]
    fig, axes = plt.subplots(2, 1, figsize=(11, 9.6), dpi=150); fig.patch.set_facecolor("#fcfcfb"); ytop = P[1] + R + B["SLIT"] + T_ + B["BUMP"]; ra = np.radians(90 - B["BL_ARC"])
    for ax, (title, (c, (m, peak, _))) in zip(axes, shapes):
        e = peak / 10 * PRESSED; tri = Triangulation(m.p[0], m.p[1], m.t.T); pc = ax.tripcolor(tri, facecolors=np.clip(e, 0, top), cmap=ramp, vmin=0, vmax=top, edgecolors="none")
        i = int(np.argmax(e)); cx, cy = m.p[:, m.t[:, i]].mean(1); ax.plot([cx], [cy], "o", ms=10, mfc="none", mec=INK, mew=1.6)
        ax.annotate("most bent here: %.2f %%" % e[i], (cx, cy), xytext=(cx + 4.5, cy + 5.5), ha="left", va="center", fontsize=12.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1, shrinkB=6))
        ax.set_xlim(P[0] - 9, P[0] + 44); ax.set_ylim(P[1] + 17.5, ytop + 1.5); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, loc="left", fontsize=14.5, color=INK, weight="bold", pad=26)
        ax.text(0, 1.035, "tooth pushed in %.1f mm: %.2f N at the tooth, %.2f %% strain (the limit for every shot is 0.5 %%)" % (PRESSED, c["N_per_mm"] * PRESSED, e[i]), transform=ax.transAxes, fontsize=11.5, color=MUTED, va="bottom")
        ax.text(P[0] - 2.6, ytop - 1.0, "tooth", fontsize=11.5, color=MUTED, ha="right", va="center")
        ax.text(P[0] + (R + B["SLIT"] + 3.2) * np.cos(ra) + 1.2, P[1] + (R + B["SLIT"] + 3.2) * np.sin(ra) - 2.2, "root: here the spring\njoins the shutter", fontsize=11.5, color=MUTED, ha="left", va="top")
        ax.text(P[0] + 6, P[1] + 22, "shutter", fontsize=11.5, color=MUTED, ha="center", va="center")
    cb = fig.colorbar(pc, ax=axes, orientation="horizontal", fraction=0.035, pad=0.03, aspect=50); cb.set_label("strain in the plastic, % (darker is more; the scale is the same for both)", fontsize=11, color=MUTED); cb.outline.set_visible(False); cb.ax.tick_params(colors=MUTED, labelsize=10)
    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight"); print(out)

if __name__ == "__main__":
    if sys.argv[1:] == ["--picture"]: picture(); sys.exit()
    if sys.argv[1:] == ["--variants"]:
        # Two more shutters for the first print of a new printer or plastic: the same part with its spring a fifth softer and a fifth stiffer.
        # Stiffness goes with thickness cubed, strain with thickness: 7 % in thickness is about 20 % in the click.  Only the spring's inner face moves.
        t0, t1, tf = B["BL_T0"], B["BL_T1"], B["BL_TF"]; base, _ = case(t0, t1, tf); V = {"standard": dict(base, file="one135_blade.stl", scale=1.0)}
        for name, sc in (("soft", 0.93), ("stiff", 1.07)):
            c, _ = case(round(t0 * sc, 3), t1, tf); f = f"build/print/one135_blade_{name}.stl"; scadr.export("scad/one135.scad", f, dict(PART="p_blade", BL_T0=round(t0 * sc, 3))); V[name] = dict(c, file=os.path.basename(f), scale=sc)
        for name, c in V.items():
            c.update(click_ratio=round(c["N_per_mm"] / base["N_per_mm"], 2), pressed_strain_pct=round(c["strain_pct_per_mm"] * PRESSED, 3), root_mm=round(c["t0"] * (1 + tf), 2), slit_at_root_mm=round(B["SLIT"] + T_ - c["t0"] * (1 + tf), 2))
            print("%-9s %-24s click x%.2f, pressed %.2f %% strain (limit 0.5), root %.2f mm, slit at the root %.2f mm" % (name, c["file"], c["click_ratio"], c["pressed_strain_pct"], c["root_mm"], c["slit_at_root_mm"]))
        d = json.load(open("build/springsearch.json")); d["variants"] = V; json.dump(d, open("build/springsearch.json", "w"), indent=1); sys.exit()
    if len(sys.argv) == 3:
        c, _ = case(float(sys.argv[1]), float(sys.argv[2])); print(c, "pressed %.1f mm: %.3f N, %.2f %%" % (PRESSED, c["N_per_mm"] * PRESSED, c["strain_pct_per_mm"] * PRESSED)); sys.exit()
    base, _ = case(0.0, 0.0); k0 = base["N_per_mm"]; rows = []
    print("plain beam %.2f mm: %.4f N/mm, pressed %.2f %% (limit 0.5 every shot)" % (T_, k0, base["strain_pct_per_mm"] * PRESSED))
    for t1 in (2 * LINE, 1.0, 1.1):                                           # the thinnest section: two printed lines, or a little more
        lo, hi = T_, 2.2; klo = case(lo, t1)[0]["N_per_mm"]; khi = case(hi, t1)[0]["N_per_mm"]
        for _ in range(7):                                                    # find the root thickness that gives the plain beam's force (secant steps on the model itself)
            t0 = round(lo + (k0 - klo) * (hi - lo) / (khi - klo), 3); c, _ = case(t0, t1); k = c["N_per_mm"]
            if abs(k / k0 - 1) < 0.01: break
            if k < k0: lo, klo = t0, k
            else: hi, khi = t0, k
        c["force_ratio"] = round(k / k0, 3); c["pressed_strain_pct"] = round(c["strain_pct_per_mm"] * PRESSED, 3); c["rest_strain_pct"] = round(c["strain_pct_per_mm"] * REST, 3)
        c["margin_every_shot"] = round(0.5 / c["pressed_strain_pct"], 2); c["slit_at_root"] = round(B["SLIT"] + T_ - t0, 2); rows.append(c)
        print("  tooth end %.2f mm, root %.3f mm: force x%.3f, pressed %.2f %% (x%.2f of the limit), at rest %.2f %%, slit at the root %.2f mm" % (t1, t0, c["force_ratio"], c["pressed_strain_pct"], c["margin_every_shot"], c["rest_strain_pct"], c["slit_at_root"]))
    best = max(rows, key=lambda c: c["margin_every_shot"])
    json.dump(dict(plain=dict(base, pressed_strain_pct=round(base["strain_pct_per_mm"] * PRESSED, 3), margin_every_shot=round(0.5 / (base["strain_pct_per_mm"] * PRESSED), 2)), shapes=rows, best=best,
                   note="same force on the tooth as the plain beam (within 1 %), so the click force and the shutter's time are unchanged; strain limit 0.5 % for a bend on every picture, in the plane of the layers"),
              open("build/springsearch.json", "w"), indent=1)
    print("best: root %.3f, tooth end %.2f" % (best["t0"], best["t1"]))
