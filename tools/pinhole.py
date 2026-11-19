"""The pinhole experiment (v2.16): the lens comes out; a thin metal pinhole disc lies on the lens seat and the pinhole ring clamps it there.
1. How much of the picture does the hole reach?  A straight line from every point of the film to the pinhole must miss the body, the front plate, the open
   shutter and the wheel behind it, and carry on out through the ring's bore in front of it.  At each dot, with the hole centred and pushed to one side.
2. The best hole for this distance (Rayleigh), the f-number of the kit's 0.25 mm disc and of a pin-pricked can disc, how even the light is.
3. Does the disc keep the light out?  It must cover the port in the pocket's floor, even pushed to one side, on every printer in the range.
4. The counts: seconds for ISO 400 film in sun, cloud, shade and indoors, with the film's slowing down on long exposures (reciprocity).
Writes build/pinhole.json.  (Uses the assembly meshes that tools/optics.py exports; run that first.)"""
import os, sys, json, numpy as np, trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
sys.path.insert(0, "tools"); from scadr import export, values
A = "build/asm/"; L = lambda n: trimesh.load(A + n + ".stl", process=True)
export("scad/one135.scad", A + "pinring.stl", dict(PART="pinring")); export("scad/one135.scad", A + "pindisc.stl", dict(PART="pindisc"))
export("scad/one135.scad", "build/print/one135_pinring.stl", dict(PART="p_pinring"))
V = values(["Y_SEAT", "PD_D", "PD_T", "PD_HOLE", "PR_H", "PR_BORE", "PR_UP", "LENS_D", "PORT_H", "Y_CVF"])
YP = V["Y_SEAT"] + V["PD_T"] / 2                                                  # the hole: in the middle of the disc's thickness, on the lens seat
RF, CFY, GA, GZ = 32.0, 32.0, 18 / 32, 12.0; nx, nz = 73, 49; T = np.linspace(-GA, GA, nx); Z = np.linspace(-GZ, GZ, nz); LAM = 0.00055
F = np.array([[RF * np.sin(t), CFY - RF * np.cos(t), z] for t in T for z in Z])
ring = L("pinring")
def lit(names, P):
    v = P - F; Lg = np.linalg.norm(v, axis=1); D = v / Lg[:, None]; ok = np.ones(len(F), bool); who = {}
    for n in names:                                                                   # behind the hole: film to hole
        loc, ir, _ = Fast(L(n)).intersects_location(F + D * 0.01, D, multiple_hits=False); d = np.linalg.norm(loc - F[ir], axis=1); k = ir[(d > 0.01) & (d < Lg[ir] - 0.02)]; ok[k] = False; who[n] = int(len(k))
    for n, m in (("pinring", ring), ("front", L("front"))):                           # in front of it: on out through the ring's bore and the pocket's mouth
        loc, ir, _ = Fast(m).intersects_location(np.repeat([P], len(F), 0) + D * 0.06, D, multiple_hits=False); d = np.linalg.norm(loc - P - D[ir] * 0.06, axis=1); k = ir[d < 15]; ok[k] = False; who[n + " (in front)"] = int(len(k))
    return ok, who
out = dict(model="ONE-135 v2.16", pinhole_to_film_mm=YP, best_hole_mm=float(1.9 * np.sqrt(YP * LAM)), points=len(F), wheel={})
out["f_number_best"] = YP / out["best_hole_mm"]; out["f_number"] = out["f_number_best"]          # (the old name: tools/film.py reads it)
out["holes"] = {k: dict(hole_mm=h, f_number=YP / h, blur_mm=float(np.hypot(h, 2.44 * LAM * YP / h)), stops_from_best=float(2 * np.log2(h / out["best_hole_mm"]))) for k, h in (("best", out["best_hole_mm"]), ("kit disc, laser-drilled", V["PD_HOLE"]), ("can disc, a fine pin", 0.30), ("can disc, a pin pushed too far", 0.45))}
for lab, st in (("large", 2), ("middle", 1), ("small", 0)):
    for off in (0.0, 0.5):
        rows = []
        for ang in ((0,) if off == 0 else (0, 90, 180, 270)):
            P = np.array([off * np.cos(np.radians(ang)), YP, off * np.sin(np.radians(ang))]); ok, who = lit(["body", "front", "blade_PHI0.0", f"wheel_STOP{st}"], P); g = ok.reshape(nx, nz)
            rows.append(dict(frame_lit_pct=float(100 * ok.mean()), blocked_by=who, lit_along_the_middle_mm=float(np.abs(T[g[:, nz // 2]]).max() * RF) if g[:, nz // 2].any() else 0.0, corners_lit=int(g[0, 0]) + int(g[0, -1]) + int(g[-1, 0]) + int(g[-1, -1])))
        out["wheel"][f"{lab} dot, hole {off} mm off centre"] = rows[0] if len(rows) == 1 else dict(worst=min(rows, key=lambda r: r["frame_lit_pct"]), all=[r["frame_lit_pct"] for r in rows])
# how even the light is where it does arrive: the hole seen at an angle, the distance, the tilt of the film (which curves toward the hole)
P = np.array([0, YP, 0]); v = P - F; Lg = np.linalg.norm(v, axis=1); D = v / Lg[:, None]
nrm = np.c_[-F[:, 0] / RF, (CFY - F[:, 1]) / RF, np.zeros(len(F))]; E = np.abs(D[:, 1]) * np.abs((D * nrm).sum(1)) / Lg ** 2; E = (E / E.reshape(nx, nz)[nx // 2, nz // 2]).reshape(nx, nz)
flat = np.cos(np.arctan(18 / YP)) ** 4
out["brightness_against_centre"] = dict(long_end=float(E[0, nz // 2]), corner=float(E[0, 0]), long_end_stops=float(np.log2(E[0, nz // 2])), corner_stops=float(np.log2(E[0, 0])), long_end_if_the_film_were_flat=float(flat), long_end_if_flat_stops=float(np.log2(flat)))
# 3. light: the disc against the port.  The pocket's rib tips stand LENS_D/2 + 0.55 - 0.8 from the axis as drawn; a printer e thin moves them e outward.  The port's widest layer
#    under the disc is the octagon (PORT_H to a flat, PORT_H / cos 22.5 to a corner): its top layer is a slot that runs under the seat to the pocket's rim, and a disc cannot cover
#    that slot's two ends (they lie outside the pocket).  What the disc must cover is the octagon and square below them.
tip = V["LENS_D"] / 2 + 0.55 - 0.8; corner = V["PORT_H"] / np.cos(np.radians(22.5)); cover = {}
for e in (-0.15, -0.08, 0.0, 0.10, 0.25):
    for name, r_in, r_out in (("kit disc %.1f mm" % V["PD_D"], V["PD_D"] / 2, V["PD_D"] / 2), ("can piece: 10 mm square, corners snipped", 5.0, 5.0 / np.cos(np.radians(22.5)))):
        if r_out > tip - e + 1e-9: cover[f"{name}, printer {e:+.2f}"] = "does not drop in: snip the corners a little more" if name.startswith("can") else "does not fit"; continue
        shift = tip - e - r_out                                                             # how far it can slide before its edge (or a corner) meets a rib
        cover[f"{name}, printer {e:+.2f}"] = dict(pushed_to_one_side_mm=round(shift, 2), covers_port_corner_by_mm=round(r_in - shift - corner, 2))
out["light"] = dict(port_corner_mm=corner, rib_tip_mm=tip, cover=cover, ring_stands_proud_mm=V["PR_UP"], note="The ring's underside is flat and the ribs hold it at any depth: pressed down, it stops on the disc and clamps it flat on the seat, whatever the disc's thickness (0.05 to 0.12 mm). Not checked by ray: light that gets down the 0.15 mm gap between ring and pocket wall into the two ends of the port's top slot and under the disc's edge (two turns in a 0.2 mm channel; estimated at no more than about 2 % of the hole's own light as an even fog). A printed camera decides it.")
# 4. counts.  Sunny 16 at ISO 400 is 1/400 s at f/16; each kind of light is that many stops darker; long exposures are stretched by the film's reciprocity
#    (colour negative, Schwarzschild exponent p = 1.3 past 1 s: t_needed = t^1.3).  The f-number is the kit disc's, at the middle of the picture.
N = YP / V["PD_HOLE"]; LIGHT = [("full sun", 0), ("bright cloud", 2), ("overcast or open shade", 4), ("indoors, by a bright window", 7)]
def corrected(t): return t if t <= 1 else t ** 1.3
out["seconds_iso400"] = {k: round(corrected((1 / 400) * (N / 16) ** 2 * 2 ** s), 2) for k, s in LIGHT}
out["seconds_iso400_metered"] = {k: round((1 / 400) * (N / 16) ** 2 * 2 ** s, 2) for k, s in LIGHT}
out["counts_for_the_guide"] = {"full sun": "open and shut (about a quarter of a second)", "bright cloud": "count 1", "overcast or open shade": "count 3", "indoors, by a bright window": "count 40"}
out["f_number_kit_disc"] = N
out["note"] = "the guide's counts round up (negative film forgives two to three stops over and one under); a count is about a second"
json.dump(out, open("build/pinhole.json", "w"), indent=1)
print(f"hole at {YP:.2f} mm from the film: best {out['best_hole_mm']:.3f} mm (f/{out['f_number_best']:.0f}); the kit's {V['PD_HOLE']} mm disc is f/{N:.0f}")
for k, h in out["holes"].items(): print(f"  {k}: {h['hole_mm']:.2f} mm, f/{h['f_number']:.0f}, blur about {h['blur_mm']:.2f} mm (hole and spreading added as squares)")
for k, w in out["wheel"].items(): print(f"  {k}: {w['frame_lit_pct'] if 'frame_lit_pct' in w else w['worst']['frame_lit_pct']:.1f} % lit" + (f"; blocked by {w['blocked_by']}" if 'blocked_by' in w else f" (worst of four sides; all {[round(x, 1) for x in w['all']]})"))
b = out["brightness_against_centre"]; print(f"  long end {b['long_end_stops']:.2f} stops, corner {b['corner_stops']:.2f} stops against the centre")
for k, c in cover.items(): print("  light:", k, c)
print("  seconds, ISO 400:", out["seconds_iso400"], " (before reciprocity:", out["seconds_iso400_metered"], ")")
