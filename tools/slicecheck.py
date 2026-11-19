"""Manufacture check: slice each part (PrusaSlicer, build/slice/cfg.ini), then compare the tool path with the model layer by layer.
Reports print time, filament, and every patch of the model that received no plastic (features the slicer dropped)."""
import sys, os, re, json, subprocess, numpy as np, trimesh, shapely
from scipy.spatial import cKDTree
from scipy import ndimage
D = "build/slice/"; A_FIL = np.pi * (1.75 / 2) ** 2; LH = 0.2
def slice_part(n, solid=False):
    """solid=True: 100 % infill, so that anything left without plastic is a real gap and not sparse infill"""
    g = D + n + ("_solid" if solid else "") + ".gcode"; stl = f"build/print/one135_{n}.stl"
    if not os.path.exists(g) or os.path.getmtime(g) < os.path.getmtime(stl):
        subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", "125,105", "--output", g] + (["--fill-density", "100%", "--fill-pattern", "rectilinear"] if solid else []), capture_output=True, timeout=1800)
    return g
def parse(g):
    x = y = z = e = 0.0; layers = {}; meta = {}
    for ln in open(g):
        if ln[0] == ";":
            m = re.match(r"; (estimated printing time \(normal mode\)|total filament used \[g\]) = (.*)", ln)
            if m: meta[m.group(1)] = m.group(2).strip()
            continue
        if not (ln.startswith("G1") or ln.startswith("G0") or ln.startswith("G92")): continue
        v = dict((t[0], float(t[1:])) for t in ln.split(";")[0].split()[1:] if t[0] in "XYZE" and len(t) > 1)
        if ln.startswith("G92"): e = v.get("E", e); continue
        nx, ny, nz, ne = v.get("X", x), v.get("Y", y), v.get("Z", z), v.get("E", e)
        if ne > e + 1e-6 and (nx != x or ny != y):
            L = np.hypot(nx - x, ny - y); layers.setdefault(round(nz, 2), []).append((x, y, nx, ny, (ne - e) * A_FIL / (L * LH)))
        x, y, z, e = nx, ny, nz, ne
    return layers, meta
def offset(layers, m):
    """where the slicer put the part: tool-path coordinates minus model coordinates (measured: the slicer's idea of a part's centre is not always the mesh's)"""
    out = []; zs = sorted(layers)
    for z in zs[1::max(1, len(zs) // 9)]:
        seg = np.array(layers[z]); w = seg[:, 4] + LH * (1 - np.pi / 4); sec = m.section(plane_origin=[0, 0, z - LH / 2], plane_normal=[0, 0, 1])
        if sec is None: continue
        lo = np.minimum(seg[:, :2] - w[:, None] / 2, seg[:, 2:4] - w[:, None] / 2).min(0); hi = np.maximum(seg[:, :2] + w[:, None] / 2, seg[:, 2:4] + w[:, None] / 2).max(0); v = sec.vertices[:, :2]
        out.append((lo + hi) / 2 - (v.min(0) + v.max(0)) / 2)
    return np.median(out, 0)
def check(n, step=0.2):
    _, meta = parse(slice_part(n)); layers, _ = parse(slice_part(n, True)); m = trimesh.load(f"build/print/one135_{n}.stl", process=True)
    off = offset(layers, m); res = dict(time=meta.get("estimated printing time (normal mode)"), grams=float(meta.get("total filament used [g]", 0)), layers=len(layers), missing=[])
    widths = np.concatenate([np.array(s)[:, 4] for s in layers.values()]); res["thin_lines_pct"] = round(100 * float((widths < 0.3).mean()), 1)
    tot_area = 0; miss_area = 0
    for z in sorted(layers):
        seg = np.array(layers[z]); sec = m.section(plane_origin=[0, 0, z - LH / 2], plane_normal=[0, 0, 1])
        if sec is None: continue
        try: p2, T = sec.to_2D() if hasattr(sec, "to_2D") else sec.to_planar()
        except Exception: continue
        polys = [shapely.affinity.affine_transform(p, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]) for p in p2.polygons_full]
        if not polys: continue
        U = shapely.unary_union(polys); x0, y0, x1, y1 = U.bounds
        gx = np.arange(x0 + step / 2, x1, step); gy = np.arange(y0 + step / 2, y1, step); X, Y = np.meshgrid(gx, gy)
        inside = shapely.contains_xy(U.buffer(-0.12), X, Y)                   # ignore the outermost 0.12 mm (rounded bead edges)
        if not inside.any(): continue
        # densify the tool path
        L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]); k = np.maximum(1, np.ceil(L / 0.1).astype(int))
        t = np.concatenate([np.linspace(0, 1, kk + 1) for kk in k]); idx = np.repeat(np.arange(len(seg)), k + 1)
        P = np.c_[seg[idx, 0] + t * (seg[idx, 2] - seg[idx, 0]), seg[idx, 1] + t * (seg[idx, 3] - seg[idx, 1])] - off; W = seg[idx, 4]
        d, j = cKDTree(P).query(np.c_[X[inside], Y[inside]]); cov = d <= W[j] / 2 + 0.1
        miss = np.zeros_like(inside); miss[inside] = ~cov; tot_area += inside.sum() * step ** 2; miss_area += miss.sum() * step ** 2
        lab, nl = ndimage.label(miss)
        for i in range(1, nl + 1):
            a = (lab == i).sum() * step ** 2
            yy, xx = np.nonzero(lab == i)
            if a >= 0.3 and min(np.ptp(gx[xx]), np.ptp(gy[yy])) + step >= 0.45:
                res["missing"].append(dict(z=z, area=round(float(a), 2), x=round(float(gx[xx].mean()), 1), y=round(float(gy[yy].mean()), 1), w=round(float(np.ptp(gx[xx]) + step), 1), h=round(float(np.ptp(gy[yy]) + step), 1)))
    res["model_area_checked_mm2"] = round(float(tot_area)); res["not_printed_pct"] = round(100 * miss_area / max(tot_area, 1), 3)
    return res
if __name__ == "__main__":
    parts = sys.argv[1:] or ["front", "blade", "wheel", "back", "roller", "knob", "spool", "test_slab", "body"]
    out = json.load(open("build/slicecheck.json")) if os.path.exists("build/slicecheck.json") else {}
    for n in parts:
        r = check(n, 0.2 if n not in ("body", "back") else 0.3); out[n] = r
        big = sorted(r["missing"], key=lambda q: -q["area"])
        print(f"{n:9s} {r['time']:>12s} {r['grams']:6.2f} g  {r['layers']:3d} layers  not printed {r['not_printed_pct']:.3f} % of the model  thin lines {r['thin_lines_pct']} %  patches wider than 0.4 mm: {len(big)}")
        for q in big[:6]: print(f"            z {q['z']:5.2f}  {q['area']:5.2f} mm2  {q['w']} x {q['h']} mm at ({q['x']}, {q['y']})")
        json.dump(out, open("build/slicecheck.json", "w"), indent=1)
