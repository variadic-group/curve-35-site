"""Export every part in its print orientation and scan it: bed fit, volume, and any surface that would print in mid-air."""
import sys, os, json, numpy as np, trimesh, concurrent.futures as cf
sys.path.insert(0, "tools"); from scadr import export
SCAD = "scad/one135.scad"; OUT = "build/print"; os.makedirs(OUT, exist_ok=True)
PARTS = ["body", "back", "front", "blade", "wheel", "roller", "knob", "spool"]
def ex(n):
    f = f"{OUT}/one135_{n}.stl"
    if not os.path.exists(f) or os.path.getmtime(f) < max(os.path.getmtime(SCAD), os.path.getmtime("scad/layout.scad")): export(SCAD, f, dict(PART="p_" + n))
    return f
with cf.ThreadPoolExecutor(3) as e: files = dict(zip(PARTS, e.map(ex, PARTS)))
def grams(t, walls, infill, rho=1.24e-3):
    """filament estimate: a skin of `walls` x 0.42 mm (top and bottom about the same) plus sparse infill inside; never more than solid"""
    shell = min(t.volume, t.area * walls * 0.42 * 0.92); return round(float(rho * (shell + infill * (t.volume - shell))), 1)
out = {}
for n in PARTS:
    t = trimesh.load(files[n], process=True); ext = t.bounds[1] - t.bounds[0]
    nz = t.face_normals[:, 2]; a = t.area_faces; c = t.triangles_center
    oh = (nz < -np.cos(np.radians(45.5))) & (c[:, 2] > t.bounds[0][2] + 0.25); flat = oh & (nz < -0.985)
    r = dict(size=[round(float(v), 1) for v in ext], z0=round(float(t.bounds[0][2]), 3), watertight=bool(t.is_watertight), bodies=int(len(t.split(only_watertight=False))),
             volume_cm3=round(float(t.volume) / 1000, 2), grams_solid=round(float(t.volume) * 1.24e-3, 1), grams_4walls_20pct=grams(t, 4, 0.20), grams_3walls_15pct=grams(t, 3, 0.15),
             on_bed_mm2=round(float(a[(nz < -0.99) & (c[:, 2] < t.bounds[0][2] + 0.05)].sum()), 0),
             overhang_mm2=round(float(a[oh].sum()), 1), flat_ceiling_mm2=round(float(a[flat].sum()), 1), sloped_overhang_mm2=round(float(a[oh & ~flat].sum()), 1))
    patches = []
    if oh.any():
        sub = t.submesh([np.nonzero(oh)[0]], append=True)
        for m in sorted(sub.split(only_watertight=False), key=lambda m: -m.area)[:8]:
            e_ = m.bounds[1] - m.bounds[0]; ctr = m.bounds.mean(0)
            patches.append(dict(area=round(float(m.area), 1), span=[round(float(e_[0]), 1), round(float(e_[1]), 1)], z=round(float(m.bounds[0][2]), 2), at=[round(float(ctr[0]), 1), round(float(ctr[1]), 1)],
                                flat=bool(abs(e_[2]) < 0.05)))
    r["patches"] = patches; out[n] = r
    print("%-7s %5.1f x %5.1f x %4.1f mm  %5.1f cm3  bodies %d  watertight %s  bed %4.0f mm2 | ceilings %.0f mm2, sloped overhang %.1f mm2" % (
        n, ext[0], ext[1], ext[2], r["volume_cm3"], r["bodies"], r["watertight"], r["on_bed_mm2"], r["flat_ceiling_mm2"], r["sloped_overhang_mm2"]))
    for q in patches: print("          %s %6.1f mm2  span %4.1f x %4.1f  at z %5.2f  xy %s" % ("ceiling" if q["flat"] else "SLOPED ", q["area"], q["span"][0], q["span"][1], q["z"], q["at"]))
q = {}
for key in ("grams_4walls_20pct", "grams_3walls_15pct"): out["total_" + key] = round(sum(out[n][key] * q.get(n, 1) for n in PARTS), 1)
print("filament, all eight parts: %.0f g at 4 walls / 20 %%, %.0f g at 3 walls / 15 %%" % (out["total_grams_4walls_20pct"], out["total_grams_3walls_15pct"]))
json.dump(out, open("build/printcheck.json", "w"), indent=1)
export(SCAD, f"{OUT}/one135_test_slab.stl", dict(PART="p_test")); export(SCAD, f"{OUT}/one135_lens_gauge.stl", dict(PART="p_lensgauge"))
export(SCAD, f"{OUT}/one135_tower.stl", dict(PART="p_tower")); export(SCAD, f"{OUT}/one135_key_gauge.stl", dict(PART="p_keygauge")); export(SCAD, f"{OUT}/one135_fit_gauge.stl", dict(PART="p_fitgauge"))
for r_, tag in ((2.9, "58"), (3.3, "66")): export(SCAD, f"{OUT}/one135_knob_fork{tag}.stl", dict(PART="p_knob", FORK_R=r_))
for n in ("plate1", "slide1", "nearring", "pinring"): export(SCAD, f"{OUT}/one135_{n}.stl", dict(PART="p_" + n))      # v2.17: the optional parts are exported here too, so every print file is sealed the same way
