"""Slicing sweep: the body and the back sliced with different wall counts, infill and layer heights; print time and plastic for each.
Answers 'would carving the body out, or other settings, save plastic or time?' with numbers.  Writes build/slicesweep.json."""
import subprocess, re, json, os, itertools, concurrent.futures as cf
D = "build/slice/"; os.makedirs(D + "sweep", exist_ok=True)
def run(part, walls, infill, pattern="gyroid", lh=0.2):
    g = f"{D}sweep/{part}_{walls}_{infill}_{pattern}_{lh}.gcode"
    if not os.path.exists(g) or os.path.getmtime(g) < os.path.getmtime(f"build/print/one135_{part}.stl"):
        subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", f"build/print/one135_{part}.stl", "--load", D + "cfg.ini", "--center", "125,105", "--output", g, "--perimeters", str(walls), "--fill-density", f"{infill}%",
                        "--fill-pattern", pattern, "--layer-height", str(lh)], capture_output=True, timeout=1800)
    t = gr = None
    for ln in open(g):
        m = re.match(r"; (estimated printing time \(normal mode\)|total filament used \[g\]) = (.*)", ln)
        if m and "time" in m.group(1): t = m.group(2).strip()
        elif m: gr = float(m.group(2))
    h = sum(float(x[:-1]) * dict(d=1440, h=60, m=1, s=1 / 60)[x[-1]] for x in t.split()); return dict(part=part, walls=walls, infill=infill, pattern=pattern, layer=lh, minutes=round(h), grams=gr)
jobs = [("body", w, i, "gyroid", 0.2) for w in (2, 3, 4) for i in (10, 15, 20)] + [("body", 3, 15, "gyroid", 0.28), ("body", 3, 0, "gyroid", 0.2), ("body", 3, 100, "rectilinear", 0.2), ("back", 2, 15, "gyroid", 0.2), ("back", 3, 15, "gyroid", 0.2), ("back", 4, 20, "gyroid", 0.2)]
with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(lambda j: run(*j), jobs))
for r in res: print(f"{r['part']:5s} {r['walls']} walls  {r['infill']:3d} % {r['pattern']:11s} layer {r['layer']}: {r['minutes'] // 60} h {r['minutes'] % 60:02d} min  {r['grams']:6.1f} g")
json.dump(res, open("build/slicesweep.json", "w"), indent=1)
