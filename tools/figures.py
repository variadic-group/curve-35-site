"""Figures for the build sheet: a true section through the film plane (sliced from the meshes) and a labelled exploded view."""
import numpy as np, trimesh, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from PIL import Image, ImageDraw, ImageFont
A = "build/asm/"
def section(name, z=0.0):
    m = trimesh.load(A + name + ".stl", process=True); s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None: return []
    p2, T = s.to_2D(); polys = []
    for poly in p2.polygons_full:
        def lift(c): c = np.asarray(c); c3 = np.c_[c, np.zeros(len(c)), np.ones(len(c))] @ T.T; return c3[:, :2]
        polys.append((lift(poly.exterior.coords), [lift(i.coords) for i in poly.interiors]))
    return polys
def draw(ax, polys, fc, ec="none", lw=0.4, zorder=1, alpha=1.0):
    for ext, holes in polys:
        verts, codes = [], []
        for ring in [ext] + holes:
            verts += list(ring); codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=zorder, alpha=alpha))
fig, ax = plt.subplots(figsize=(12, 5.6), dpi=170)
parts = [("body", "#3a3d44"), ("back", "#6b7280"), ("front_open", "#e8792b"), ("wheel_STOP4", "#f0c83a"), ("blade_PHI24.5", "#1f9d96"), ("lever_BETA20.05", "#d8342f"),
         ("roller", "#3d8bd9"), ("spool", "#3d8bd9"), ("cassette", "#d9a514"), ("lens", "#a9d6ee"), ("film", "#7a4a2a")]
for n, c in parts: draw(ax, section(n), c, zorder=3 if n in ("film", "lens") else 2)
# taking rays
for th in (-0.99, 0, 0.99):
    a = np.radians(th * np.degrees(18 / 32)); fx, fy = 32 * np.sin(a), 32 - 32 * np.cos(a)
    ax.plot([fx, 0], [fy, 26.87], color="#f5d76e", lw=0.9, zorder=4); d = np.array([0 - fx, 26.87 - fy]); d /= np.linalg.norm(d)
    ax.plot([0, 0 + d[0] * 2.3], [26.87, 26.87 + d[1] * 2.3], color="#f5d76e", lw=0.9, zorder=4)
def note(txt, xy, xt, ha="center"):
    ax.annotate(txt, xy=xy, xytext=xt, ha=ha, va="center", fontsize=9.5, color="#111", arrowprops=dict(arrowstyle="-", color="#444", lw=0.7, shrinkA=1, shrinkB=1), zorder=6)
note("film cassette\n(exposed frames wind back in)", (-45, 11), (-52, 44))
note("fixed guide", (-23.2, 4.2), (-26, -17))
note("drum: film curved on R = 32", (9, 1.4), (4, -17))
note("sprocket roller\n+ frame dial", (27.6, 5.4), (30, -17))
note("take-up spool\n(whole roll goes here first)", (44.6, 11), (56, 44))
note("lens (from a disposable)", (0.5, 30.6), (-19, 44))
note("aperture wheel, shutter blade", (6.5, 27.0), (17, 44), ha="center")
note("back: guide, roller cradles, pressure ribs,\nlight-seal tongue, exposure guide", (-40, -4.2), (-66, -17), ha="center")
ax.text(-24, 17.5, "body", fontsize=9.5, color="white", ha="center", va="center", zorder=6); ax.text(21, 17.5, "body", fontsize=9.5, color="white", ha="center", va="center", zorder=6)
ax.set_aspect("equal"); ax.set_xlim(-84, 72); ax.set_ylim(-22, 56); ax.axis("off")
ax.text(-83, 56, "Section through the middle of the film, seen from above (the subject is at the top)", fontsize=10.5, color="#333", va="top")
fig.savefig("build/fig/section.png", bbox_inches="tight", pad_inches=0.05, facecolor="white"); plt.close(fig)
# ---- labelled exploded view
im = Image.open("build/fig/exploded.png").convert("RGB"); d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 30); f2 = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 28)
L = [(1, "lever", (412, 640), (300, 520)), (0, "spring", (470, 640), (430, 800)), (0, "lens", (523, 668), (480, 930)), (2, "front plate + finder", (575, 500), (330, 330)),
     (3, "shutter blade", (650, 660), (660, 1005)), (4, "aperture wheel", (735, 670), (930, 930)), (5, "body", (860, 700), (1130, 1000)),
     (6, "take-up spool", (878, 230), (640, 150)), (7, "sprocket roller + dial", (935, 285), (1150, 190)), (8, "wind knob", (930, 425), (1290, 330)), (9, "back", (1160, 640), (1380, 880))]
for num, name, tip, lab in L:
    d.line([tip, lab], fill=(70, 70, 70), width=2); d.ellipse([tip[0] - 5, tip[1] - 5, tip[0] + 5, tip[1] + 5], fill=(70, 70, 70))
    t = (f"{num}  " if num else "") + name; w = d.textlength(t, font=f2) + 24
    d.rounded_rectangle([lab[0] - w / 2, lab[1] - 22, lab[0] + w / 2, lab[1] + 22], radius=10, fill=(255, 255, 255), outline=(70, 70, 70), width=2)
    d.text((lab[0] - w / 2 + 12, lab[1] - 16), t, fill=(20, 20, 20), font=f2)
im.crop((180, 90, 1560, 1050)).save("build/fig/exploded_labelled.png")
# ---- parts sheet with captions
names = [("1 body", "p_body"), ("9 back", "p_back"), ("2 front plate", "p_front"), ("3 blade", "p_blade"), ("4 wheel", "p_wheel"), ("1 lever", "p_lever"), ("7 roller", "p_roller"), ("8 knob", "p_knob"), ("6 spool", "p_spool")]
names = [("body", "p_body"), ("back", "p_back"), ("front plate", "p_front"), ("shutter blade", "p_blade"), ("aperture wheel", "p_wheel"), ("lever", "p_lever"), ("sprocket roller", "p_roller"), ("wind knob", "p_knob"), ("take-up spool", "p_spool")]
W, Hh = 900, 700; sheet = Image.new("RGB", (W * 3, Hh * 3), "white"); ds = ImageDraw.Draw(sheet); fb = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 44)
for i, (cap, fn) in enumerate(names):
    sheet.paste(Image.open(f"build/v_{fn}.png").convert("RGB"), ((i % 3) * W, (i // 3) * Hh)); ds.text(((i % 3) * W + 30, (i // 3) * Hh + 24), cap, fill=(30, 30, 30), font=fb)
sheet.resize((1800, 1400), Image.LANCZOS).save("build/fig/parts_as_printed.png")
print("figures written")
