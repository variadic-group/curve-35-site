"""The back's small parts as the slicer draws them: the tool path of single layers, zoomed in, over the model's outline.  Shows how many lines of plastic each small part is made of.
    python3 tools/backproof.py [out.png]"""
import sys, json, numpy as np, trimesh, shapely
from shapely.geometry import LineString, box
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
sys.path.insert(0, "tools"); import slicecheck as sc
from scadr import values
V = values(["NUB_X0", "NUB_X1", "PAD_X0", "PAD_X1", "F_X0", "F_X1", "F_T", "H", "CASS", "SPOOL", "ROLLER", "KN_R", "KN_CR", "KSW", "FIT", "RB_HW", "RB_HWL", "Y_RIM", "DOOR_T"])
m = trimesh.load("build/print/one135_back.stl", process=True); layers, _ = sc.parse(sc.slice_part("back")); off = sc.offset(layers, m); ZS = np.array(sorted(layers))
def outline(z):
    sec = m.section(plane_origin=[0, 0, z - 0.1], plane_normal=[0, 0, 1]); p2, T = sec.to_2D()
    return shapely.unary_union([shapely.affinity.affine_transform(p, [T[0, 0], T[0, 1], T[1, 0], T[1, 3 - 3 + 1], T[0, 3], T[1, 3]]) for p in p2.polygons_full])
def panel(ax, z, win, title, note):
    z = float(ZS[np.argmin(np.abs(ZS - z))]); seg = np.array(layers[z]); seg = seg.copy(); seg[:, [0, 2]] -= off[0]; seg[:, [1, 3]] -= off[1]; W = box(*win)
    U = outline(z).intersection(W.buffer(0.5))
    for g in getattr(U, "geoms", [U]):
        if g.geom_type != "Polygon": continue
        ax.add_patch(MP(np.array(g.exterior.coords), closed=True, fc="#e9edf3", ec="#8a93a3", lw=0.8, zorder=1))
        for h in g.interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc="white", ec="#8a93a3", lw=0.8, zorder=1.1))
    k = (np.maximum(seg[:, 0], seg[:, 2]) > win[0] - 1) & (np.minimum(seg[:, 0], seg[:, 2]) < win[2] + 1) & (np.maximum(seg[:, 1], seg[:, 3]) > win[1] - 1) & (np.minimum(seg[:, 1], seg[:, 3]) < win[3] + 1)
    for x0, y0, x1, y1, w in seg[k]:
        w = float(np.clip(w, 0.15, 0.9)); p = LineString([(x0, y0), (x1, y1)]).buffer(w / 2 * 0.86, cap_style=1)
        ax.add_patch(MP(np.array(p.exterior.coords), closed=True, fc="#3b6fb6", ec="#1f3f6e", lw=0.25, alpha=0.78, zorder=2))
    ax.set_xlim(win[0], win[2]); ax.set_ylim(win[1], win[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#c8ccd4")
    ax.plot([win[0] + 0.6, win[0] + 2.6], [win[1] + 0.6, win[1] + 0.6], color="#1a1c20", lw=2.5, solid_capstyle="butt", zorder=5); ax.text(win[0] + 1.6, win[1] + 0.95, "2 mm", ha="center", va="bottom", fontsize=8, color="#1a1c20", zorder=5)
    ax.set_title(title, fontsize=10.5, loc="left", color="#1a1c20", pad=5); ax.text(0.0, -0.04, note, transform=ax.transAxes, fontsize=8.8, va="top", color="#4a4f58", wrap=True)
H, FT = V["H"], V["F_T"]; cx, sx, rx = V["CASS"][0], V["SPOOL"][0], V["ROLLER"][0]
P = [(0.2, (V["NUB_X0"] - 6.5, -H - 2.6, V["PAD_X1"] + 3.5, -H + 7.6), "Latch finger, nub and pad: first layer", "Finger %.1f mm wide: three lines side by side.  Nub 2.0 x 1.6 mm.  Pad %.1f mm wide." % (FT, V["PAD_X1"] - V["PAD_X0"])),
     (2.0, (V["NUB_X0"] - 6.5, -H - 2.6, V["PAD_X1"] + 3.5, -H + 7.6), "The same, 2 mm up", "The slit under the finger is 3.1 mm wide: nothing there to fuse."),
     (8.0, (cx - 9.5, -H - 0.6, cx + 9.5, -H + 7.2), "Block that closes the wind knob's slot, 5 mm above the plate", "13.3 x 5.1 mm at its foot: a solid block, walls and fill."),
     (11.6, (cx - 9.5, -H - 0.6, cx + 9.5, -H + 7.2), "The same block, 8.6 mm above the plate", "It has parted in two round the knob's stem.  Each half: the wide bar's end,\n4.2 x 2.4 mm, and on it the narrow bar's tip, 1.2 mm wide: two lines side by side.\nThat tip is thinner than 2 mm only over its last 0.7 mm."),
     (13.4, (cx - 9.5, -H - 0.6, cx + 9.5, -H + 7.2), "Its last 2 mm: the wide bar's two tips", "2.4 x 2.4 mm each (2.1 at the very top), 2.9 mm tall:\nthe smallest things that stand up on the back."),
     (15.0, (rx - 10.5, -H + 3.6, rx + 9.5, -H + 11.2), "Fork for the frame wheel, 12 mm above the plate", "Prongs 5.2 x 4.1 mm (left) and 4 mm joined to the block beside it (right)."),
     ]
fig, axs = plt.subplots(2, 3, figsize=(15.5, 8.6), dpi=130); fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.10, wspace=0.06, hspace=0.34)
for ax, (z, win, t, n) in zip(axs.ravel(), P): panel(ax, z, win, t, n)
fig.text(0.02, 0.955, "10. Back: its small parts as the slicer draws them", fontsize=19, weight="bold", color="#1a1c20"); fig.text(0.02, 0.02, "CURVE 35 (ONE-135 v2.10), preview round 6.", fontsize=9.5, color="#5f646c")
fig.text(0.02, 0.915, "One layer each, 0.2 mm thick.  Blue: the lines of plastic (0.45 mm wide).  Grey: the model's outline at that height.  Same settings as the print card: 3 walls, 15 % fill.", fontsize=10.5, color="#5f646c")
out = sys.argv[1] if len(sys.argv) > 1 else "build/preview/round6/CURVE-35_round6_10_back_small_parts.png"; fig.savefig(out); print(out)
