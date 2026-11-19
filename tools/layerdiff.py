"""What a change does to the print: two versions of a print file are cut at the middle of every 0.2 mm layer, as a slicer cuts them, and the
plastic gained and lost on each layer is listed.  A step turned into a slope of the same size shows nothing here; a new roof shows as plastic
lost above the old ceiling.   python3 tools/layerdiff.py old.stl new.stl [layer height]"""
import sys, numpy as np, trimesh, shapely
from shapely.ops import unary_union
def layer(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None: return shapely.geometry.Polygon()
    p, T = s.to_planar()
    return unary_union([shapely.affinity.affine_transform(q, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]) for q in p.polygons_full]).buffer(0)
def diff(a, b, lh=0.2, show=0.05):
    A = trimesh.load(a, process=True); B = trimesh.load(b, process=True); top = max(A.bounds[1][2], B.bounds[1][2]); rows = []
    for k in range(int(round(top / lh)) + 1):
        z = (k + 0.5) * lh
        if z > top: break
        pa, pb = layer(A, z), layer(B, z); g, l = pb.difference(pa), pa.difference(pb)
        if g.area > show or l.area > show:
            def where(x): return "x %.1f..%.1f y %.1f..%.1f" % (x.bounds[0], x.bounds[2], x.bounds[1], x.bounds[3]) if not x.is_empty else ""
            rows.append((k + 1, z, pa.area, g.area, l.area, where(g), where(l)))
    return rows, top
if __name__ == "__main__":
    lh = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2; rows, top = diff(sys.argv[1], sys.argv[2], lh)
    print("%d layers; %d differ by more than 0.05 mm2" % (int(round(top / lh)), len(rows)))
    for n, z, a, g, l, wg, wl in rows: print("  layer %3d (z %5.2f): %8.1f mm2 before; +%6.2f %-34s -%6.2f %s" % (n, z, a, g, wg, l, wl))
    print("in all: %.0f mm3 gained, %.0f mm3 lost (areas x the layer height)" % (sum(r[3] for r in rows) * lh, sum(r[4] for r in rows) * lh))
