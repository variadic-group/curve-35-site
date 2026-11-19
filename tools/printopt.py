"""Last filter: print time and plastic.  Every part sliced with a handful of settings; the layer height stays 0.2 mm (the fits that are counted in layers depend on it).
Writes build/printopt.json."""
import subprocess, re, json, os, sys, concurrent.futures as cf
D = "build/slice/"; os.makedirs(D + "opt", exist_ok=True); PARTS = ["body", "back", "front", "spool", "knob", "roller", "blade", "wheel"]
CFG = {"as on the print card (3 walls, 15 % gyroid)": [],
       "+ avoid crossing perimeters": ["--avoid-crossing-perimeters"],
       "2 walls, 15 %": ["--avoid-crossing-perimeters", "--perimeters", "2"],
       "3 walls, 10 %": ["--avoid-crossing-perimeters", "--fill-density", "10%"],
       "3 walls, lightning infill": ["--avoid-crossing-perimeters", "--fill-pattern", "lightning"],
       "3 walls, 15 %, quicker inside (walls 60, infill 120, solid 90 mm/s; outer walls stay at 30)": ["--avoid-crossing-perimeters", "--perimeter-speed", "60", "--infill-speed", "120", "--solid-infill-speed", "90"],
       "3 walls, lightning, quicker inside": ["--avoid-crossing-perimeters", "--fill-pattern", "lightning", "--perimeter-speed", "60", "--infill-speed", "120", "--solid-infill-speed", "90"]}
def run(job):
    part, name, opts, i = job; g = f"{D}opt/{part}_{i}.gcode"
    if not os.path.exists(g) or os.path.getmtime(g) < os.path.getmtime(f"build/print/one135_{part}.stl"):
        subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", f"build/print/one135_{part}.stl", "--load", D + "cfg.ini", "--center", "125,105", "--output", g] + opts, capture_output=True, timeout=1800)
    t = gr = None
    for ln in open(g):
        m = re.match(r"; (estimated printing time \(normal mode\)|total filament used \[g\]) = (.*)", ln)
        if m and "time" in m.group(1): t = sum(int(v) * k for v, k in re.findall(r"(\d+)([dhms])", m.group(2).replace("d", "d")) for k in [dict(d=86400, h=3600, m=60, s=1)[k]])
        elif m: gr = float(m.group(2))
    return part, name, t, gr
only = sys.argv[1:]; jobs = [(p, n, o, i) for i, (n, o) in enumerate(CFG.items()) for p in PARTS if not only or str(i) in only]
res = json.load(open("build/printopt.json")) if os.path.exists("build/printopt.json") else {}
with cf.ThreadPoolExecutor(2) as ex:
    for part, name, t, gr in ex.map(run, jobs): res.setdefault(name, {})[part] = dict(seconds=t, grams=gr)
json.dump(res, open("build/printopt.json", "w"), indent=1)
base = None
for name, r in res.items():
    if len(r) < len(PARTS): continue
    T = sum(v["seconds"] for v in r.values()); Gm = sum(v["grams"] for v in r.values()); base = base or (T, Gm)
    print("  %-92s %2d h %02d min  %6.1f g   (%+.0f %% time, %+.0f %% plastic)   body %d:%02d %.1f g" % (name, T // 3600, T % 3600 // 60, Gm, 100 * (T / base[0] - 1), 100 * (Gm / base[1] - 1), r["body"]["seconds"] // 3600, r["body"]["seconds"] % 3600 // 60, r["body"]["grams"]))
# the recommended mix: lightning infill for the three hollow parts, 'avoid crossing perimeters' for the three with optical openings, the print card for the two small turned parts
if not only:
    R = json.load(open("build/printopt.json")); K = list(R.keys()); card, avoid, light, lightq = K[0], K[1], K[4], K[6]
    pick = lambda big: {p: R[big][p] for p in ("body", "back", "spool")} | {p: R[avoid][p] for p in ("front", "blade", "wheel")} | {p: R[card][p] for p in ("knob", "roller")}
    M = dict(mix=pick(light), mix_quick=pick(lightq)); json.dump(M, open("build/printopt_mix.json", "w"), indent=1)
    for k, v in M.items(): s = sum(q["seconds"] for q in v.values()); print("  %-10s %d h %02d min  %.1f g" % (k, s // 3600, s % 3600 // 60, sum(q["grams"] for q in v.values())))
