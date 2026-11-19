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
def export(scad, out, d=None, timeout=1200):
    r=subprocess.run(["openscad","-o",out]+defs(d)+[scad],capture_output=True,text=True,timeout=timeout)
    if not os.path.exists(out) or os.path.getsize(out)<50: print(r.stderr[-2000:]); raise RuntimeError("export failed "+out)
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
