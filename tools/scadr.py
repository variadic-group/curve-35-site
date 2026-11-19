"""OpenSCAD helpers: PNG renders (preview via xvfb), STL/DXF export, parallel frame rendering."""
import subprocess, os, sys, json, concurrent.futures as cf
def defs(d):
    out=[]
    for k,v in (d or {}).items():
        if isinstance(v,str): out += ["-D", f'{k}="{v}"']
        elif isinstance(v,bool): out += ["-D", f"{k}={'true' if v else 'false'}"]
        else: out += ["-D", f"{k}={v}"]
    return out
def png(scad, out, d=None, cam="0,0,0,55,0,25,420", size=(1280,720), scheme="Tomorrow", proj="p", render=False):
    cmd=["xvfb-run","-a","openscad","-o",out,f"--imgsize={size[0]},{size[1]}",f"--camera={cam}",
         f"--colorscheme={scheme}",f"--projection={proj}","--autocenter" if False else "--viewall" if cam=="all" else ""]
    cmd=[c for c in cmd if c]
    if cam=="all": cmd=[c for c in cmd if not c.startswith("--camera")]
    if render: cmd.append("--render")
    cmd += defs(d) + [scad]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
    if not os.path.exists(out): print(r.stderr[-1500:]); raise RuntimeError("render failed "+out)
    return out
def canon_stl(path):
    """OpenSCAD writes the same triangles in a different order on every run.  Put them in one fixed order, so that the same model
    always gives the same file, and the slicer (run on one thread) the same tool paths: every number can then be reproduced exactly."""
    L = open(path).read().split("\n")
    if not L or not L[0].startswith("solid"): return
    facets = []; i = 0
    while i < len(L):
        if L[i].lstrip().startswith("facet normal"):
            v = [L[i + 2].strip(), L[i + 3].strip(), L[i + 4].strip()]; num = [tuple(float(x) for x in q.split()[1:]) for q in v]; k = min(range(3), key=lambda j: num[j])
            facets.append((tuple(num[k:] + num[:k]), " ".join("0" if t == "-0" else t for t in L[i].split()), v[k:] + v[:k])); i += 7      # a sliver's normal comes out as 0 or -0 by chance: write 0
        else: i += 1
    facets.sort(key=lambda f: f[0]); out = [L[0].strip()]
    for _, n, v in facets: out += ["  " + n, "    outer loop"] + ["      " + q for q in v] + ["    endloop", "  endfacet"]
    out.append("end" + L[0].strip()); open(path, "w").write("\n".join(out) + "\n")
WELD_TOL = 0.005      # mm: edges shorter than this (5 micrometres, 1/40 of a layer) are collapsed when a print file is sealed
def weld_stl(path, tol=WELD_TOL):
    """v2.17: seal a print file.  OpenSCAD 2021 writes STL coordinates to six significant digits, and its CGAL union keeps faces that two solids put 0.00001 to
    0.001 mm apart (two expressions for one plane that differ in the last digits, the ends of rounded outlines that almost meet a flat face).  The file it writes
    is closed, but it carries edges 10 nanometres long and slivers of zero area; a checker that first welds vertices within its own tolerance turns those into
    edges shared by three or four faces: the "non-manifold edges" a print farm reported (v2.16: back 19, body 8, front 17).  Here the mesh is read exactly as
    written, rebuilt as a manifold by manifold3d (the kernel OpenSCAD's later manifold backend uses; this OpenSCAD 2021 has none), and every edge shorter than
    tol collapsed; the shape moves by less than tol.  Anything manifold3d cannot read as a closed solid is an error, never written."""
    import numpy as np, manifold3d as m3
    V = {}; F = []; tri = []
    for l in open(path):
        l = l.strip()
        if l.startswith("vertex"):
            tri.append(V.setdefault(tuple(l.split()[1:]), len(V)))
            if len(tri) == 3: F.append(tri); tri = []
    P = np.array([[float(x) for x in k] for k in V]); F = np.array(F, dtype=np.uint32)
    M = m3.Manifold(m3.Mesh(vert_properties=P.astype(np.float32), tri_verts=F))
    if M.status() != m3.Error.NoError: raise RuntimeError(f"weld: {path} is not a closed manifold as exported ({M.status()})")
    v0 = M.volume(); M = M.simplify(tol); me = M.to_mesh()
    Q = np.array(me.vert_properties, dtype=float)[:, :3]; T = np.array(me.tri_verts)
    if abs(M.volume() - v0) > 1e-3 * max(1.0, v0) or len(T) == 0: raise RuntimeError(f"weld: {path} changed volume {v0:.3f} -> {M.volume():.3f}")
    # v2.20: simplify() can leave a triangle whose three corners lie on one line (two slopes that end a few nanometres apart on one wall: it fills the joint and has no
    # area).  Each is taken out here, as the file will be written (six decimals): if its shortest edge is under tol that edge is collapsed; if not, the long edge it
    # shares with its neighbour is swapped for the short one across, which moves nothing.  The result must still be one closed solid of the same volume.
    R = np.round(Q, 6); flat = lambda: np.nonzero(np.linalg.norm(np.cross(R[T[:, 1]] - R[T[:, 0]], R[T[:, 2]] - R[T[:, 0]]), axis=1) / 2 < 1e-9)[0]
    for _ in range(400):
        bad = flat()
        if not len(bad): break
        t = T[bad[0]]; E = sorted((float(np.linalg.norm(R[t[k]] - R[t[(k + 1) % 3]])), k) for k in range(3))
        if E[0][0] < tol:
            p_, q_ = t[E[0][1]], t[(E[0][1] + 1) % 3]; T = np.where(T == q_, p_, T); T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 2] != T[:, 0])]
        else:
            k = E[2][1]; u, v, w = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
            nb = [(j, m) for j in range(len(T)) for m in range(3) if T[j][m] == v and T[j][(m + 1) % 3] == u]
            if len(nb) != 1: raise RuntimeError(f"weld: {path} has a face of no area that cannot be taken out")
            j, m = nb[0]; d = T[j][(m + 2) % 3]; T[bad[0]] = [u, d, w]; T[j] = [d, v, w]
    else: raise RuntimeError(f"weld: {path} still has {len(flat())} faces of no area")
    used = np.unique(T); remap = -np.ones(len(Q), dtype=np.int64); remap[used] = np.arange(len(used)); Q = Q[used]; T = remap[T]
    M2 = m3.Manifold(m3.Mesh(vert_properties=Q.astype(np.float32), tri_verts=T.astype(np.uint32)))
    if M2.status() != m3.Error.NoError or abs(M2.volume() - v0) > 1e-3 * max(1.0, v0): raise RuntimeError(f"weld: {path} is not a closed solid of the same volume once its flat faces are out ({M2.status()})")
    n = np.cross(Q[T[:, 1]] - Q[T[:, 0]], Q[T[:, 2]] - Q[T[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-30)
    out = ["solid OpenSCAD_Model"]
    for t, nn in zip(T, n):
        out += ["  facet normal %s" % " ".join("%.6g" % c for c in nn), "    outer loop"] + ["      vertex %s" % " ".join("%.6f" % c for c in Q[i]) for i in t] + ["    endloop", "  endfacet"]
    out.append("endsolid OpenSCAD_Model"); open(path, "w").write("\n".join(out) + "\n")
def export(scad, out, d=None, timeout=1200):
    r=subprocess.run(["openscad","-o",out]+defs(d)+[scad],capture_output=True,text=True,timeout=timeout)
    if not os.path.exists(out) or os.path.getsize(out)<50: print(r.stderr[-2000:]); raise RuntimeError("export failed "+out)
    if out.endswith(".stl") and "build/print" in out.replace(os.sep, "/"): weld_stl(out)      # every print file is sealed (v2.17)
    if out.endswith(".stl"): canon_stl(out)
    w=[l for l in r.stderr.splitlines() if "WARNING" in l or "ERROR" in l]
    return out, w
def frames(scad, outdir, n, dfun, cam, size=(1280,720), workers=2, scheme="Tomorrow"):
    os.makedirs(outdir, exist_ok=True)
    jobs=[(scad, os.path.join(outdir,f"f{i:04d}.png"), dfun(i/(n-1) if n>1 else 0), cam(i/(n-1) if n>1 else 0) if callable(cam) else cam, size, scheme) for i in range(n)]
    with cf.ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda j: png(j[0], j[1], j[2], j[3], j[4], j[5]) if not os.path.exists(j[1]) else j[1], jobs))
    return outdir

def values(names, scad="scad/one135.scad"):
    """The model's own numbers, read from the model: no tool keeps a second copy of a dimension that can go stale."""
    import tempfile, re
    d = tempfile.mkdtemp(); f = os.path.join(d, "v.scad"); o = os.path.join(d, "v.echo")
    open(f, "w").write('include <%s>\necho(VALS = [%s]);\n' % (os.path.abspath(scad), ", ".join(names)))
    r = subprocess.run(["openscad", "-o", o, "-D", 'PART="none"', f], capture_output=True, text=True, timeout=300)
    m = re.search(r"VALS = (\[.*\])", open(o).read() if os.path.exists(o) else r.stderr); return {k: v for k, v in zip(names, json.loads(m.group(1).replace("undef", "null"))) if v is not None}        # a name the model no longer has is simply left out
