"""One print run: every part of one camera laid out on a single plate (220 x 220 mm bed or larger), as one STL and one 3MF
with named objects, sliced at three machine speeds.  Also the body alone at those speeds.  Writes build/plate.json."""
import os, re, json, subprocess, numpy as np, trimesh
D = "build/slice/"; P = "build/print/one135_"
ROWS = [[("body", 1), ("blade", 1), ("wheel", 1)], [("back", 1), ("front", 1)], [("roller", 1), ("knob", 2), ("spool", 1), ("tower", 1), ("blade", 1)]]; GAP = 5.0      # two wind knobs and two shutters: one of each is a spare; the tower lets the spool cool
TOTAL = {}; SEEN = {}
for row in ROWS:
    for name, qty in row: TOTAL[name] = TOTAL.get(name, 0) + qty
scene = trimesh.Scene(); y = 0.0; boxes = {}
for row in ROWS:
    x = 0.0; h = 0.0
    for name, qty in row:
        m0 = trimesh.load(P + name + ".stl", process=True)
        for i in range(qty):
            m = m0.copy(); b = m.bounds; m.apply_translation([x - b[0][0], y - b[0][1], -b[0][2]]); SEEN[name] = SEEN.get(name, 0) + 1; key = name + ("" if TOTAL[name] == 1 else f"_{SEEN[name]}"); scene.add_geometry(m, node_name=key, geom_name=key)
            boxes[key] = [round(float(x), 1), round(float(y), 1), round(float(b[1][0] - b[0][0]), 1), round(float(b[1][1] - b[0][1]), 1)]; x += b[1][0] - b[0][0] + GAP; h = max(h, b[1][1] - b[0][1])
    y += h + GAP
ext = scene.bounds[1] - scene.bounds[0]; whole = trimesh.util.concatenate(list(scene.geometry.values())); whole.export("build/print/one135_plate.stl"); scene.export("build/print/one135_plate.3mf")
print("plate: %.0f x %.0f mm, %d objects" % (ext[0], ext[1], len(scene.geometry)))
SPEEDS = {"older bed-slinger (45 mm/s walls)": [],
          "current mid-range (120 mm/s walls, input shaping)": ["--perimeter-speed", "120", "--external-perimeter-speed", "80", "--small-perimeter-speed", "60", "--infill-speed", "200", "--solid-infill-speed", "160", "--top-solid-infill-speed", "100",
                                                                "--travel-speed", "300", "--first-layer-speed", "40", "--bridge-speed", "40", "--gap-fill-speed", "60", "--max-volumetric-speed", "15", "--machine-max-acceleration-extruding", "5000",
                                                                "--machine-max-acceleration-travel", "6000", "--machine-max-acceleration-x", "6000", "--machine-max-acceleration-y", "6000", "--machine-max-feedrate-x", "300", "--machine-max-feedrate-y", "300"],
          "fast CoreXY (200 mm/s walls, 22 mm3/s)": ["--perimeter-speed", "200", "--external-perimeter-speed", "150", "--small-perimeter-speed", "80", "--infill-speed", "300", "--solid-infill-speed", "250", "--top-solid-infill-speed", "150",
                                                     "--travel-speed", "500", "--first-layer-speed", "50", "--bridge-speed", "50", "--gap-fill-speed", "80", "--max-volumetric-speed", "22", "--machine-max-acceleration-extruding", "10000",
                                                     "--machine-max-acceleration-travel", "12000", "--machine-max-acceleration-x", "12000", "--machine-max-acceleration-y", "12000", "--machine-max-feedrate-x", "500", "--machine-max-feedrate-y", "500"]}
def slice_(stl, tag, extra, center="110,110"):
    g = f"{D}{tag}.gcode"
    r = subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", center, "--dont-arrange", "--output", g] + extra, capture_output=True, text=True, timeout=3600)
    t = gr = None
    for ln in open(g):
        m = re.match(r"; (estimated printing time \(normal mode\)|total filament used \[g\]) = (.*)", ln)
        if m and "time" in m.group(1): t = m.group(2).strip()
        elif m: gr = float(m.group(2))
    mins = sum(float(q[:-1]) * dict(d=1440, h=60, m=1, s=1 / 60)[q[-1]] for q in t.split()); return dict(minutes=round(mins), grams=gr, gcode=g)
out = dict(plate_mm=[round(float(ext[0])), round(float(ext[1]))], boxes=boxes, speeds={})
for i, (name, extra) in enumerate(SPEEDS.items()):
    a = slice_("build/print/one135_plate.stl", f"plate_{i}", extra); b = slice_(P + "body.stl", f"body_speed_{i}", extra)
    out["speeds"][name] = dict(whole_kit_minutes=a["minutes"], whole_kit_grams=a["grams"], body_minutes=b["minutes"], plate_gcode=a["gcode"])
    print(f"  {name:52s} whole kit in one run {a['minutes'] // 60} h {a['minutes'] % 60:02d} min, {a['grams']:.0f} g | body alone {b['minutes'] // 60} h {b['minutes'] % 60:02d} min")
json.dump(out, open("build/plate.json", "w"), indent=1)
