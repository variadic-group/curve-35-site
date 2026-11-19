"""Faces that a print farm's upload check says "will need support": facing down, 35 degrees or less from level, and not lying on the bed.
They are grouped by where they are and listed, so each can be looked at and named.  A flat ceiling over a slot is in here even when it
is a short bridge that prints well without support: a farm that adds supports by rule does not make that distinction.
The number to compare with the farm's is "above the first layer": it does not count the underside of a relief one layer up.
Writes build/overhangcheck.json.   python3 tools/overhangcheck.py [file.stl ...]"""
import sys, json, glob, os, numpy as np, trimesh
ANGLE = 35.0
FIRST = 0.205      # the farm's check does not count a face 0.20 mm up (the underside of a first-layer relief); it counts one 0.21 mm up
def over(path, angle=ANGLE, bed=0.05):
    m = trimesh.load(path, process=True); n = m.face_normals; c = m.triangles_center; A = m.area_faces
    zmin = m.triangles[:, :, 2].min(1)
    bad = np.nonzero((n[:, 2] <= -np.cos(np.radians(angle))) & (zmin > bed) & (A > 1e-9))[0]
    if not len(bad): return dict(file=os.path.basename(path), area_mm2=0.0, above_first_layer_mm2=0.0, groups=[])
    adj = m.face_adjacency; keep = np.isin(adj[:, 0], bad) & np.isin(adj[:, 1], bad); import scipy.sparse as sp, scipy.sparse.csgraph as cg
    idx = {f: i for i, f in enumerate(bad)}; a = adj[keep]; g = sp.coo_matrix((np.ones(len(a)), ([idx[x] for x in a[:, 0]], [idx[x] for x in a[:, 1]])), shape=(len(bad), len(bad)))
    k, lab = cg.connected_components(g, directed=False); groups = []
    for j in range(k):
        f = bad[lab == j]; v = m.triangles[f].reshape(-1, 3); lo, hi = v.min(0), v.max(0); ext = hi - lo
        slope = float(np.degrees(np.arccos(np.clip(-np.average(n[f, 2], weights=A[f]), -1, 1))))
        groups.append(dict(area_mm2=round(float(A[f].sum()), 2), z=[round(float(lo[2]), 2), round(float(hi[2]), 2)], x=[round(float(lo[0]), 1), round(float(hi[0]), 1)], y=[round(float(lo[1]), 1), round(float(hi[1]), 1)],
                           short_side_mm=round(float(min(ext[0], ext[1])), 2), long_side_mm=round(float(max(ext[0], ext[1])), 2), from_level_deg=round(slope, 1)))
    groups.sort(key=lambda q: -q["area_mm2"])
    return dict(file=os.path.basename(path), area_mm2=round(float(A[bad].sum()), 1), above_first_layer_mm2=round(sum(q["area_mm2"] for q in groups if q["z"][0] > FIRST), 1), groups=groups)
if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob("build/print/one135_*.stl")); out = {}
    for p in files:
        r = over(p); out[r["file"]] = r; print("%-28s facing down within %d degrees of level: %7.1f mm2 above the first layer (%.1f with it) in %d places" % (r["file"], ANGLE, r["above_first_layer_mm2"], r["area_mm2"], len(r["groups"])))
        for q in r["groups"][:40]: print("      %7.2f mm2  z %5.2f..%5.2f  x %6.1f..%6.1f  y %6.1f..%6.1f  %5.2f x %6.2f mm  %4.1f deg from level" % (q["area_mm2"], q["z"][0], q["z"][1], q["x"][0], q["x"][1], q["y"][0], q["y"][1], q["short_side_mm"], q["long_side_mm"], q["from_level_deg"]))
    if not sys.argv[1:]: json.dump(out, open("build/overhangcheck.json", "w"), indent=1)
