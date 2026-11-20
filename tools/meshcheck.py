"""v2.17: is every print file a sealed solid, and how thin and spread out is each part?

For every STL in build/print (or the folder given as the first argument):
  * topology, read exactly as written (vertices keyed by their text, nothing merged): open edges (used by one face), non-manifold edges (used by
    three faces or more), edges used twice in the same direction (a face turned inside out), zero-area faces;
  * the same after welding vertices within WELD mm (0.001), as a print farm's checker does before it counts: this is where the v2.16 files failed;
  * the shortest edge, watertight (trimesh), volume, and the number of separate solids.
  * two shape measures, the print farm's own (they reproduce its v2.16 numbers: shutter 1.27 mm and 26 %, aperture wheel 1.21 mm):
      average thickness = volume / (surface area / 2): a plate of thickness t gives t;
      fill = volume / volume of the convex hull: how much of its outline the part fills.
A print file passes with 0 open, 0 non-manifold, 0 inverted and 0 zero-area faces, both as written and welded, and watertight.  Exit code 1 if any fails.
Writes build/meshcheck.json."""
import sys, os, glob, json, collections
import numpy as np, trimesh

WELD = 0.001          # mm: a checker's typical weld tolerance; v2.16's files had 16 to 20 edges shorter than this in the body, back and front
WELDS = (1e-5, 1e-4, 1e-3, 2e-3)    # 20 November 2026: the farm reported "4 non-manifold edges" in v2.20's shutter and 2 in its body, which passed here.  Welding leaves faces
                                    # with two corners in one place; this check used to drop those before counting, the farm's does not, and each one puts a third face on
                                    # an edge.  Welding at 0.0001 mm and counting them gives the farm's 4 and 2.  Its tolerance is not published, so a file must now come
                                    # through all of these with nothing collapsed (tools/scadr.py removes every edge under 0.005 mm, so nothing should weld at all)
D = sys.argv[1] if len(sys.argv) > 1 else "build/print"


def read_stl(path):
    """Vertices keyed by their exact text (ASCII) or exact float32 bits (binary): nothing is merged that the file does not merge."""
    raw = open(path, "rb").read()
    V = {}; F = []
    if raw[:5] == b"solid" and b"facet" in raw[:400]:
        tri = []
        for l in raw.decode().splitlines():
            l = l.strip()
            if l.startswith("vertex"):
                tri.append(V.setdefault(tuple(l.split()[1:]), len(V)))
                if len(tri) == 3: F.append(tri); tri = []
    else:
        n = int(np.frombuffer(raw[80:84], "<u4")[0]); rec = np.frombuffer(raw[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        for t in rec["v"]: F.append([V.setdefault(tuple(p.tolist()), len(V)) for p in t])
    P = np.array([[float(x) for x in k] for k in V]); return P, np.array(F, dtype=np.int64).reshape(-1, 3)


def topology(F, P):
    und = collections.Counter(); dire = collections.Counter()
    for a, b, c in F:
        for u, v in ((a, b), (b, c), (c, a)):
            und[(min(u, v), max(u, v))] += 1; dire[(u, v)] += 1
    area = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) / 2 if len(F) else np.zeros(0)
    return dict(open=sum(1 for v in und.values() if v == 1), nonmanifold=sum(1 for v in und.values() if v > 2), inverted=sum(1 for v in dire.values() if v > 1),
                zero_area=int((area < 1e-9).sum()), degenerate=int(sum(1 for a, b, c in F if a == b or b == c or a == c)))


def welded(P, F, tol):
    q = np.round(P / tol).astype(np.int64); _, inv = np.unique(q, axis=0, return_inverse=True); G = inv.ravel()[F]
    keep = (G[:, 0] != G[:, 1]) & (G[:, 1] != G[:, 2]) & (G[:, 0] != G[:, 2])
    Q = np.zeros((int(inv.max()) + 1, 3)); Q[inv.ravel()] = P                     # one position per welded vertex (any of those merged into it)
    t = topology(G[keep], Q); t["collapsed_faces"] = int((~keep).sum()); t.pop("zero_area")
    und = collections.Counter(tuple(sorted(e)) for a, b, c in G for e in ((a, b), (b, c), (c, a)) if e[0] != e[1]); t["as_a_farm_counts"] = sum(1 for v in und.values() if v > 2); return t


def shape(m):
    hull = m.convex_hull.volume
    return dict(avg_thickness_mm=round(float(2 * m.volume / m.area), 3), fill_pct=round(float(100 * m.volume / hull), 1) if hull > 0 else None)


def check(path):
    P, F = read_stl(path)
    m = trimesh.Trimesh(P, F, process=False)
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    r = dict(faces=int(len(F)), exact=topology(F, P), welded=welded(P, F, WELD), farm={("%g" % t): welded(P, F, t)["as_a_farm_counts"] for t in WELDS}, shortest_edge_mm=float("%.3g" % L.min()), watertight=bool(m.is_watertight),
             winding_consistent=bool(m.is_winding_consistent), volume_mm3=round(float(m.volume), 2), solids=int(len(m.split(only_watertight=False))))
    r.update(shape(m))
    bad = [k for k in ("open", "nonmanifold", "inverted", "zero_area", "degenerate") if r["exact"][k]] + ["welded_" + k for k in ("open", "nonmanifold", "inverted") if r["welded"][k]]
    if not r["watertight"]: bad.append("not watertight")
    if max(r["farm"].values()): bad.append("a farm's checker would count %d non-manifold edges (welding at %s mm)" % max((v, k) for k, v in r["farm"].items()))
    r["ok"] = not bad; r["problems"] = bad; return r


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(D, "*.stl"))); out = {}; fails = 0
    print("%-40s %6s %5s %5s %5s %5s | welded %5s %5s | %9s %5s %10s %6s %7s %6s" % ("file", "faces", "open", "nm", "inv", "zero", "open", "nm", "shortest", "tight", "volume", "solids", "thick", "fill"))
    for f in files:
        r = check(f); out[os.path.basename(f)] = r; fails += not r["ok"]
        print("%-40s %6d %5d %5d %5d %5d | welded %5d %5d | %9.2g %5s %10.1f %6d %6.2f %5.1f%% %s" % (os.path.basename(f)[:40], r["faces"], r["exact"]["open"], r["exact"]["nonmanifold"], r["exact"]["inverted"],
              r["exact"]["zero_area"], r["welded"]["open"], r["welded"]["nonmanifold"], r["shortest_edge_mm"], "yes" if r["watertight"] else "NO", r["volume_mm3"], r["solids"],
              r["avg_thickness_mm"], r["fill_pct"], "" if r["ok"] else "FAIL: " + ", ".join(r["problems"])))
    json.dump(dict(folder=D, weld_mm=WELD, files=out, failures=fails), open("build/meshcheck.json" if D == "build/print" else os.path.join(D, "meshcheck.json"), "w"), indent=1)
    print("%d files, %d fail" % (len(files), fails)); sys.exit(1 if fails else 0)
