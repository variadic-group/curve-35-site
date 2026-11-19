"""One picture of the assurance register: every mechanism against every check, with the gaps shown.
Reads build/assure.json, writes build/assurance_matrix.png."""
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
A = json.load(open("build/assure.json")); R = A["register"]
CHECKS = ["FIT", "TOL", "STRENGTH", "FEEL", "PRINT", "PATH", "LIGHT", "FRICTION", "STACK", "MOTION"]; GAPS = ["CREEP", "WEAR", "DROP", "HEAT", "WARP"]
NAMES = dict(FIT="fit", TOL="fat or thin printer", STRENGTH="strength", FEEL="force and feel", PRINT="rebuilt from tool paths", PATH="seams and bridges", LIGHT="light", FRICTION="friction", STACK="random errors", MOTION="motion",
             CREEP="creep", WEAR="wear", DROP="drop", HEAT="heat", WARP="warp")
INK, MUTE, GRID, GAP = "#1f2328", "#8b949e", "#d8dee4", "#b42318"; PX = 1.0
n = len(R); fig, ax = plt.subplots(figsize=(10.4, 0.30 * n + 3.2), dpi=170); X = lambda j: PX * j; XG = lambda j: PX * (len(CHECKS) + 0.9 + j)
for i, r in enumerate(R):
    y = n - 1 - i
    if i % 2 == 0: ax.axhspan(y - 0.5, y + 0.5, color="#f6f8fa", zorder=-5, lw=0)
    ax.text(-0.8, y, f"{r['id']}  {r['name']}", ha="right", va="center", fontsize=8.8, color=INK)
    for j, c in enumerate(CHECKS):
        if c in r["checked"]: ax.plot(X(j), y, marker="s", ms=10.5, color=INK, mew=0)
        else: ax.plot(X(j), y, marker="o", ms=2.2, color=MUTE, mew=0)
    for j, g in enumerate(GAPS):
        if g in r["not_checked"]: ax.plot(XG(j), y, marker="x", ms=7.5, mew=1.9, color=GAP)
for j, c in enumerate(CHECKS): ax.text(X(j) - 0.15, n - 0.3, NAMES[c], ha="left", va="bottom", fontsize=8.4, color=INK, rotation=42, rotation_mode="anchor")
for j, g in enumerate(GAPS): ax.text(XG(j) - 0.15, n - 0.3, NAMES[g], ha="left", va="bottom", fontsize=8.4, color=INK, rotation=42, rotation_mode="anchor")
ax.plot([XG(0) - 0.95, XG(0) - 0.95], [-0.6, n - 0.4], color=GRID, lw=1.0)
ax.text(X(0) - 0.3, n + 4.3, "Checked in software", ha="left", va="bottom", fontsize=9.6, color=INK, fontweight="bold")
ax.text(XG(0) - 0.3, n + 4.3, "Never simulated", ha="left", va="bottom", fontsize=9.6, color=INK, fontweight="bold")
done = sum(len([c for c in r["checked"] if c in CHECKS]) for r in R); gaps = sum(len(r["not_checked"]) for r in R)
ax.plot(X(0), -1.5, marker="s", ms=10.5, color=INK, mew=0); ax.text(X(0) + 0.6, -1.5, f"checked ({done} of {n * len(CHECKS)} cells)", va="center", fontsize=8.6, color=INK)
ax.plot(X(0), -2.5, marker="o", ms=2.2, color=MUTE, mew=0); ax.text(X(0) + 0.6, -2.5, "not run, or does not apply", va="center", fontsize=8.6, color=INK)
ax.plot(X(0), -3.5, marker="x", ms=7.5, mew=1.9, color=GAP); ax.text(X(0) + 0.6, -3.5, f"matters here and was never simulated ({gaps} cells): needs a printed part", va="center", fontsize=8.6, color=INK)
ax.set_xlim(-12.5, XG(len(GAPS)) + 2.2); ax.set_ylim(-4.2, n + 6.4); ax.axis("off")
ax.text(-12.4, n + 5.6, "Every mechanism against every check", fontsize=12.5, fontweight="bold", color=INK, va="bottom")
fig.savefig("build/assurance_matrix.png", bbox_inches="tight", facecolor="white"); print("build/assurance_matrix.png", done, "checked cells,", gaps, "gaps")
