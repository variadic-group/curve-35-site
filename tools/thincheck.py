"""Wall thickness the way a print farm's upload checker measures it: from the middle of every facet a ray goes straight into the
part, and the distance to the far side is that facet's thickness.  Facets under the limit (0.5 mm) are grouped by where they are and
listed, so each can be looked at and named.  A knife edge (two faces meeting at 45 degrees) and a part's first-layer relief both
show up here, as they do at the farm.  Writes build/thincheck.json.   python3 tools/thincheck.py [file.stl ...]"""
import sys, json, glob, os, numpy as np, trimesh
LIMIT = 0.5
def thin(path, limit=LIMIT):
    m = trimesh.load(path, process=True); c = m.triangles_center; n = m.face_normals; o = c - n * 1e-4
    loc, ray, tri = m.ray.intersects_location(o, -n, multiple_hits=False)
    t = np.full(len(c), np.inf); t[ray] = np.linalg.norm(loc - o[ray], axis=1)
    bad = np.nonzero((t < limit) & (m.area_faces > 1e-9))[0]
    if not len(bad): return dict(file=os.path.basename(path), area_under_limit_mm2=0.0, thinnest_mm=None, groups=[])
    # group thin facets that share an edge
    adj = m.face_adjacency; keep = np.isin(adj[:, 0], bad) & np.isin(adj[:, 1], bad); import scipy.sparse as sp, scipy.sparse.csgraph as cg
    idx = {f: i for i, f in enumerate(bad)}; a = adj[keep]; g = sp.coo_matrix((np.ones(len(a)), ([idx[x] for x in a[:, 0]], [idx[x] for x in a[:, 1]])), shape=(len(bad), len(bad)))
    k, lab = cg.connected_components(g, directed=False); groups = []
    for j in range(k):
        f = bad[lab == j]; A = float(m.area_faces[f].sum()); v = m.triangles[f].reshape(-1, 3); nz = float(np.average(n[f, 2], weights=m.area_faces[f]))
        groups.append(dict(area_mm2=round(A, 2), thinnest_mm=round(float(t[f].min()), 3), typical_mm=round(float(np.average(t[f], weights=m.area_faces[f])), 3), box_min=[round(float(x), 2) for x in v.min(0)], box_max=[round(float(x), 2) for x in v.max(0)], facing_z=round(nz, 2)))
    groups.sort(key=lambda q: -q["area_mm2"])
    return dict(file=os.path.basename(path), area_under_limit_mm2=round(float(m.area_faces[bad].sum()), 1), thinnest_mm=round(float(t[bad].min()), 3), groups=groups)
if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob("build/print/one135_*.stl")); out = {}
    for p in files:
        r = thin(p); out[r["file"]] = r; print("%-28s under %.1f mm: %6.1f mm2, thinnest %s, in %d places" % (r["file"], LIMIT, r["area_under_limit_mm2"], r["thinnest_mm"], len(r["groups"])))
        for q in r["groups"][:8]: print("      %6.2f mm2  thinnest %.2f  typical %.2f  x %6.1f..%6.1f  y %6.1f..%6.1f  z %5.2f..%5.2f  facing z %+.1f" % (q["area_mm2"], q["thinnest_mm"], q["typical_mm"], q["box_min"][0], q["box_max"][0], q["box_min"][1], q["box_max"][1], q["box_min"][2], q["box_max"][2], q["facing_z"]))
    if not sys.argv[1:]: json.dump(out, open("build/thincheck.json", "w"), indent=1)
