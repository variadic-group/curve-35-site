"""quick 2-D sections of the exported meshes, drawn with matplotlib (to look at fits without waiting for a render)"""
import sys, json, numpy as np, trimesh, shapely
sys.path.insert(0, "tools"); import fea
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
A = "build/asm/"
def draw(ax, stl, origin, normal, axes, color, alpha=0.6, lw=0.6):
    try: p = fea.section(A + stl, origin, normal, axes)
    except Exception as e: return
    if p is None: return
    for g in (p.geoms if hasattr(p, "geoms") else [p]):
        ax.fill(*g.exterior.xy, color=color, alpha=alpha, lw=0)
        ax.plot(*g.exterior.xy, color="k", lw=lw)
        for h in g.interiors: ax.fill(*h.xy, color="w", lw=0); ax.plot(*h.xy, color="k", lw=lw)
if __name__ == "__main__":
    LY = json.load(open("build/layout.json")); TH = LY["B"]["THETA"]; YF = 25.47; YR = LY["A"]["Y_RIM"]; RO = LY["A"]["roller"]
    fig, ax = plt.subplots(2, 3, figsize=(21, 13))
    a = ax[0, 0]; draw(a, "front.stl", [0, YF + 1.75, 0], [0, 1, 0], [0, 2], "#f0a060"); draw(a, f"blade_PHI{TH}.stl", [0, YF + 1.75, 0], [0, 1, 0], [0, 2], "#8145c0"); a.set_title("blade level: plate + blade (closed)")
    a = ax[0, 1]; draw(a, "front.stl", [0, YF + 1.75, 0], [0, 1, 0], [0, 2], "#f0a060"); draw(a, f"blade_PHI{-TH}.stl", [0, YF + 1.75, 0], [0, 1, 0], [0, 2], "#8145c0"); draw(a, "blade_PHI0.0.stl", [0, YF + 1.75, 0], [0, 1, 0], [0, 2], "#8080d0", 0.35); a.set_title("blade level: other side, and open")
    a = ax[0, 2]; draw(a, "front.stl", [0, YF + 0.55, 0], [0, 1, 0], [0, 2], "#f0a060")
    for k, c in ((0, "#e0c040"), (2, "#909090")): draw(a, f"wheel_STOP{k}.stl", [0, YF + 0.55, 0], [0, 1, 0], [0, 2], c, 0.5)
    a.set_title("wheel level: plate + wheel at P and at C")
    a = ax[1, 0]; draw(a, "back.stl", [0, YR - 1.5, 0], [0, 1, 0], [0, 2], "#80b0e0"); draw(a, "body.stl", [0, YR - 1.5, 0], [0, 1, 0], [0, 2], "#d06060"); a.set_title("through the back plate: latch fingers (blue) and the body's catches (red)"); a.set_xlim(-30, 10); a.set_ylim(16, 31)
    a = ax[1, 1]
    for stl, c in (("body.stl", "#d0d0d0"), ("back.stl", "#80b0e0"), ("roller.stl", "#e0a040")): draw(a, stl, [0, 0, 23.0], [0, 0, 1], [0, 1], c)
    a.set_title("z = 23: fork, collar, body slot"); a.set_xlim(RO[0] - 9, RO[0] + 9); a.set_ylim(YR - 4, RO[1] + 9)
    a = ax[1, 2]
    for stl, c in (("body.stl", "#d0d0d0"), ("back.stl", "#80b0e0"), ("roller.stl", "#e0a040")): draw(a, stl, [RO[0], 0, 0], [1, 0, 0], [1, 2], c)
    a.set_title("x = roller axis: side view (y, z)"); a.set_xlim(YR - 4, 16); a.set_ylim(10, 31)
    for a in ax.ravel(): a.set_aspect("equal"); a.grid(alpha=0.25)
    plt.tight_layout(); plt.savefig("build/sections.png", dpi=70)
