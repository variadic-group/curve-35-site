"""As sliced: the three upright parts cut down the middle, drawn from the slicer's own tool paths, layer by layer.
Shows what the printer will actually lay down where a part grows outward (the rings and the dial), and how much of each line rests on the layer below.
    python3 tools/aslayers.py [out.png]   -> build/aslayers.png, build/aslayers.json"""
import sys, os, json, subprocess, numpy as np, trimesh
from shapely.geometry import LineString
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
sys.path.insert(0, "tools"); from slicecheck import slice_part, parse, offset
W = 0.45; LH = 0.2
def moves(g):
    """every extruding move: (layer height, kind, x0, y0, x1, y1)"""
    x = y = z = e = 0.0; typ = "Custom"; out = []
    for ln in open(g):
        if ln.startswith(";TYPE:"): typ = ln[6:].strip(); continue
        if ln[0] == ";" or not ln.startswith(("G1", "G0", "G92")): continue
        v = {t[0]: float(t[1:]) for t in ln.split(";")[0].split()[1:] if t[0] in "XYZE" and len(t) > 1}
        if ln.startswith("G92"): e = v.get("E", e); continue
        nx, ny, nz, ne = v.get("X", x), v.get("Y", y), v.get("Z", z), v.get("E", e)
        if (nx != x or ny != y) and ne > e + 1e-6: out.append((round(nz, 2), typ, x, y, nx, ny))
        x, y, z, e = nx, ny, nz, ne
    return out
def cut(n, across=False):
    """the part's middle section as the slicer fills it: {layer: [(x0, x1, wall?)]} in the model's own coordinates, and the model's outline.  across: cut the other way (along y)"""
    g = slice_part(n); m = trimesh.load(f"build/print/one135_{n}.stl", process=True); layers, _ = parse(g); off = offset(layers, m)
    if across: m = m.copy(); m.apply_transform(np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]]))            # turn the part a quarter turn, and its tool paths with it
    c = (m.bounds[0] + m.bounds[1]) / 2; by = {}; turn = (lambda x, y: (y, -x)) if across else (lambda x, y: (x, y))
    for z, typ, x0, y0, x1, y1 in moves(g): by.setdefault(z, {}).setdefault("wall" if "erimeter" in typ else "fill", []).append(LineString([turn(x0 - off[0], y0 - off[1]), turn(x1 - off[0], y1 - off[1])]))
    line = LineString([(m.bounds[0][0] - 2, c[1]), (m.bounds[1][0] + 2, c[1])]); out = {}
    for z, d in sorted(by.items()):
        row = []
        for kind, segs in d.items():
            hit = unary_union([s for s in segs if s.distance(line) < W]).buffer(W / 2).intersection(line) if segs else None
            if hit is None or hit.is_empty: continue
            for q in (hit.geoms if hasattr(hit, "geoms") else [hit]):
                if q.length > 0.05: row.append((q.bounds[0], q.bounds[2], kind == "wall"))
        out[z] = row
    sec = m.section(plane_origin=[0, c[1], 0], plane_normal=[0, 1, 0]); outline = [np.asarray(l)[:, [0, 2]] for l in sec.discrete]
    return out, outline, c, m
def steps(rows, z0, z1):
    """how far the outer edge moves outward from one layer to the next, between two heights: the largest step, on either side"""
    zs = [z for z in sorted(rows) if z0 <= z <= z1 and rows[z]]; worst = 0.0
    for a, b in zip(zs, zs[1:]):
        la, lb = min(r[0] for r in rows[a]), min(r[0] for r in rows[b]); ra, rb = max(r[1] for r in rows[a]), max(r[1] for r in rows[b]); worst = max(worst, la - lb, rb - ra)
    return round(worst, 2)
PARTS = [("roller", "Frame wheel (whole)", None, [("ring", 6.9, 8.3), ("dial", 14.8, 18.2)], False), ("spool", "Take-up spool: knob, stem and ring", (0, 15), [("ring", 9.9, 11.5)], False), ("knob", "Wind knob (whole)", None, [("ring", 9.9, 11.5)], True)]
if __name__ == "__main__":
    fig, axs = plt.subplots(1, 3, figsize=(17, 8.6), gridspec_kw=dict(width_ratios=[1.0, 1.25, 1.05])); res = {}; fig.subplots_adjust(left=0.05, right=0.99, top=0.9, bottom=0.2, wspace=0.14)
    for ax, (n, title, zr, zones, across) in zip(axs, PARTS):
        rows, outline, c, m = cut(n, across); zr = zr or (0, float(m.bounds[1][2]))
        for z, row in rows.items():
            if not (zr[0] - 0.01 <= z <= zr[1] + 0.21): continue
            for x0, x1, wall in row: ax.add_patch(Rectangle((x0 - c[0], z - LH), x1 - x0, LH, facecolor="#3f6db3" if wall else "#b9cdea", edgecolor="white", lw=0.25))
        for l in outline: ax.plot(l[:, 0] - c[0], l[:, 1], color="#111", lw=0.9)
        notes = []
        for name, z0, z1 in zones:
            s = steps(rows, z0, z1); rest = round(100 * (1 - s / W)); res[f"{n} {name}"] = dict(step_mm=s, rests_on_pct=rest); notes.append(f"{name}: each layer steps out {s:.2f} mm at most,\nso {rest} % of its outer line rests on the layer below")
            ax.axhspan(z0, z1, color="#f2a23a", alpha=0.13, lw=0)
        r = max(m.extents[0], m.extents[1]) / 2 + 1.2; ax.set_xlim(-r, r); ax.set_ylim(zr[0] - 0.3, zr[1] + 0.6); ax.set_aspect("equal"); ax.set_title(title, fontsize=13, loc="left", weight="bold")
        ax.set_xlabel("mm"); ax.set_ylabel("height above the bed, mm" if ax is axs[0] else ""); fig.text(ax.get_position().x0 + 0.005, 0.105, "\n".join(notes), va="top", fontsize=10.5, color="#333")
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.suptitle("As sliced: each part cut down the middle.  Every bar is one 0.2 mm layer as the slicer lays it (dark: walls, pale: infill); the black line is the model.  No supports.", fontsize=12.5, x=0.01, ha="left")
    out = sys.argv[1] if len(sys.argv) > 1 else "build/aslayers.png"; fig.savefig(out, dpi=130); json.dump(res, open("build/aslayers.json", "w"), indent=1); print(res)
