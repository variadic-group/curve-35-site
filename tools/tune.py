"""Per-printer tuning.  Print one135_fit_gauge.stl (12 minutes): a comb of slots from 2.7 to 3.8 mm and a 3.0 mm key.
Find the narrowest slot the key drops into; its number N (the marked slot is 0, the next wider 1, ...) says how fat or thin your
printer prints its walls: about 0.025 x N mm.  This script turns N into a slicer setting (XY size compensation) that cancels it,
re-slices the three shutter parts with that setting, rebuilds the plastic from the new tool paths with your printer's error added,
and checks that the clicks land back on the design values.

  python3 tools/tune.py N          write build/printer_profile.json and build/slice/tuned.ini for your printer
  python3 tools/tune.py --demo     show the effect for the five reference printers  (writes build/tune.json)

In OrcaSlicer / Bambu Studio the same number goes into 'X-Y contour compensation' (and, with the sign flipped, 'X-Y hole compensation')."""
import sys, os, json, subprocess, numpy as np, trimesh
sys.path.insert(0, "tools"); import printsim; from slicecheck import parse, offset
D = "build/slice/"; B = printsim.B; P, C, TH = printsim.P, printsim.C, printsim.TH
def wall_error(n): return round(0.025 * n - 0.0125, 3) if n != 0 else 0.0
def solid(n, comp, extra=(), tag=""):
    g = f"{D}tune_{n}_{comp:+.2f}{tag}.gcode"; stl = f"build/print/one135_{n}.stl"
    if not os.path.exists(g) or os.path.getmtime(g) < os.path.getmtime(stl):
        subprocess.run(["prusa-slicer", "--threads", "1", "--export-gcode", stl, "--load", D + "cfg.ini", "--center", "125,105", "--output", g, "--fill-density", "100%", "--fill-pattern", "rectilinear", f"--xy-size-compensation={comp:.2f}"] + list(extra), capture_output=True, timeout=1800)
    return g
def clicks(e, comp, extra=(), tag=""):
    for n in ("blade", "wheel", "front"):
        layers, _ = parse(solid(n, comp, extra, tag)); m = trimesh.load(f"build/print/one135_{n}.stl", process=True); printsim._cache[n] = (layers, m, offset(layers, m))
    bl = printsim.printed("blade", 0.8, e); fr = printsim.printed("front", 3.2, e); wh = printsim.printed("wheel", 0.8, e); fw = printsim.printed("front", 4.4, e)
    b = printsim.click(bl, fr, P, B["R_OUT"], B["BL_T"], B["DB_A"], B["BL_ARC"], B["DB_A"] + TH / 2, B["DB_A"] + TH); w = printsim.click(wh, fw, C, B["WHEEL_R"], B["WH_T"], B["WD_A0"], B["WH_ARC"], B["WD_A0"] - B["WPOS"][1] / 2, B["WD_A0"])
    hole = lambda i, zl: 2 * printsim.printed("wheel", zl, e).boundary.distance(printsim.Point(C + B["R_HOLE"] * np.array([np.cos(np.radians(B["A_AX"] + B["WPOS"][i])), np.sin(np.radians(B["A_AX"] + B["WPOS"][i]))])))
    return dict(blade_pushed_in=round(b["pushed_in"], 2), wheel_pushed_in=round(w["pushed_in"], 2), blade_room=round(b["room_left_behind_spring"], 2), pinhole_mm=round(hole(0, 1.0), 2), sun_hole_mm=round(hole(1, 1.0), 2))
if __name__ == "__main__":
    if sys.argv[1:] == ["--robust"]:                        # the same parts under other slicer settings, on a typical printer (walls +0.10)
        out = {}; V = [("as specified: 0.45 mm lines, Arachne walls", [], ""), ("classic walls", ["--perimeter-generator", "classic"], "_classic"), ("0.40 mm lines", ["--extrusion-width", "0.40", "--perimeter-extrusion-width", "0.40", "--external-perimeter-extrusion-width", "0.40"], "_w40"),
                       ("0.50 mm lines", ["--extrusion-width", "0.50", "--perimeter-extrusion-width", "0.50", "--external-perimeter-extrusion-width", "0.50"], "_w50"),
                       ("0.6 mm nozzle, 0.65 mm lines", ["--nozzle-diameter", "0.6", "--extrusion-width", "0.65", "--perimeter-extrusion-width", "0.65", "--external-perimeter-extrusion-width", "0.65", "--infill-extrusion-width", "0.65", "--solid-infill-extrusion-width", "0.65", "--top-infill-extrusion-width", "0.65", "--first-layer-extrusion-width", "0.65"], "_n06")]
        for name, extra, tag in V:
            try: r = clicks(0.10, 0.0, extra, tag)
            except Exception as ex_: r = dict(error=str(ex_)[:80])
            out[name] = r; print(f"  {name:44s} {r}")
        json.dump(out, open("build/robust.json", "w"), indent=1)
    elif sys.argv[1:] == ["--demo"]:
        out = {}; print("printer (wall error)        untuned: shutter / wheel tooth pushed in, pinhole   ->   tuned")
        for name, e, ef in printsim.PRINTERS:
            a = clicks(e, 0.0); comp = -round(e, 2); t = clicks(e, comp); out[name] = dict(wall_error=e, xy_size_compensation=comp, untuned=a, tuned=t)
            print(f"  {name:16s} {e:+.2f} mm   {a['blade_pushed_in']:.2f} / {a['wheel_pushed_in']:.2f} mm, {a['pinhole_mm']:.2f} mm   ->   compensation {comp:+.2f}: {t['blade_pushed_in']:.2f} / {t['wheel_pushed_in']:.2f} mm, {t['pinhole_mm']:.2f} mm")
        json.dump(out, open("build/tune.json", "w"), indent=1)
    else:
        n = int(sys.argv[1]); e = wall_error(n); comp = -round(e, 2); t = clicks(e, comp)
        cfg = open(D + "cfg.ini").read().rstrip() + f"\nxy_size_compensation = {comp:.2f}\n"; open(D + "tuned.ini", "w").write(cfg)
        prof = dict(gauge_slot=n, wall_error_mm=e, xy_size_compensation_mm=comp, check=t, slicer_settings={"PrusaSlicer": {"xy_size_compensation": comp}, "OrcaSlicer / Bambu Studio": {"xy_contour_compensation": comp, "xy_hole_compensation": -comp}})
        json.dump(prof, open("build/printer_profile.json", "w"), indent=1); print(json.dumps(prof, indent=1)); print("slice with build/slice/tuned.ini")
