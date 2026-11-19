"""The sights, measured on the assembled camera.  Rays from the eye over the notch and the blade's top: is the line free in both shutter states, with the plate pushed as far toward
the line as its play lets it?  Then the point aimed at, traced through the lens onto the film.  -> build/sightcheck.json"""
import sys, json, numpy as np, trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
sys.path.insert(0, "tools"); from scadr import values
V = values(["SG_X", "SG_H", "SG_Y0", "SG_W0", "SG_RW", "SB_Y1", "SB_L", "SB_TOP", "SB_DROP", "H", "RF", "GATE_A", "GATE_Z"]); TH = json.load(open("build/layout.json"))["B"]["THETA"]; A = "build/asm/"
L = lambda n: trimesh.load(A + n + ".stl", process=True); lens = L("lens"); lc = (lens.bounds[0] + lens.bounds[1]) / 2; out = {}
body = L("body"); b = body.vertices; yb = V["SB_Y1"] - V["SB_L"]; k = b[(np.abs(b[:, 0] - V["SG_X"]) < 0.7) & (b[:, 1] > yb - 0.1) & (b[:, 1] < V["SB_Y1"] + 0.1)]; zb = k[:, 2].max(); r = b[(np.abs(b[:, 1] - V["SG_Y0"]) < 0.3) & (np.abs(b[:, 0] - V["SG_X"]) < 4)]; zr = r[:, 2].max()
inner = sorted(set(np.round(r[r[:, 2] > zr - 0.05][:, 0], 2))); notch = [x for x in inner if abs(x - V["SG_X"]) < 1.2]
out["measured"] = dict(lens_centre_x=float(lc[0]), lens_centre_z=float(lc[2]), sight_x=V["SG_X"], blade_top_z=float(zb), rails_top_z=float(zr), notch_gap_mm=float(max(notch) - min(notch)) if notch else None, notch_to_blade_mm=yb - V["SG_Y0"], blade_rear_face_y=yb)
print("measured on the body's mesh:", out["measured"])
p0 = np.array([V["SG_X"], V["SG_Y0"], zr]); p1 = np.array([V["SG_X"], yb, zb]); u = (p1 - p0) / np.linalg.norm(p1 - p0); dip = np.degrees(np.arcsin(-u[2])); eye = p0 - u * 300
for state, bl in (("rocker's left end down", f"blade_PHI{TH}"), ("rocker's right end down", f"blade_PHI{-TH}")):
    for play in (0.0, -1.0, -1.5):
        ms = [body, L("back"), L("knob"), L("spool"), L("roller")] + [m.copy().apply_translation([play, 0, 0]) for m in (L("front"), L(bl), L("wheel_STOP2"), lens)]
        rt = Fast(trimesh.util.concatenate(ms)); res = {}
        for name, dz in (("on the line", 0.0), ("0.25 degrees over the blade", 0.25), ("0.5 degrees over", 0.5), ("1 degree over", 1.0)):
            n = 0; tot = 0
            for dx in np.linspace(-0.25, 0.25, 11):                                   # across the blade's top, a quarter of a degree either side
                d = u + np.array([np.tan(np.radians(dx)), 0, np.tan(np.radians(dz + 0.02))]); d /= np.linalg.norm(d); tot += 1; n += int(rt.intersects_any([eye], [d])[0])
            res[name] = "%d of %d blocked" % (n, tot)
        rk = L(bl).vertices; rk = rk[rk[:, 2] > V["H"] + 0.05]; out[f"{state}, plate {abs(play)} mm toward the line"] = dict(rocker_from_x=float(rk[:, 0].min() + play), clear_of_blade_mm=float(rk[:, 0].min() + play - (V["SG_X"] + V["SB_TOP"] / 2)), rays=res)
        print(f"{state}, plate {abs(play)} mm toward the line: rocker starts {rk[:, 0].min() + play - (V['SG_X'] + V['SB_TOP'] / 2):+.1f} mm from the blade's top edge;", res)
print("line of sight dips %.2f degrees" % dip); tab = []
for d in (700, 1400, 2000, 2800, 5000, 10000, 1e7):
    P = p1 + u * (d - (p1[1] - lc[1])) / u[1]; fx = -(P[0] - lc[0]) * V["RF"] / d; fz = -(P[2] - lc[2]) * V["RF"] / d; w = 2 * d * np.tan(np.radians(V["GATE_A"])); h = 2 * d * V["GATE_Z"] / V["RF"]
    tab.append(dict(m=d / 1000, side_mm=float(P[0] - lc[0]), up_mm=float(P[2] - lc[2]), side_pct=float(100 * (P[0] - lc[0]) / w), up_pct=float(100 * (P[2] - lc[2]) / h), film_x=float(fx), film_z=float(fz)))
    print("%8.1f m: aimed point %+.1f mm sideways, %+.1f mm up from the picture's middle = %+.2f %% of width, %+.2f %% of height; on the film %.2f and %.2f mm from the middle" % (d / 1000, P[0] - lc[0], P[2] - lc[2], 100 * (P[0] - lc[0]) / w, 100 * (P[2] - lc[2]) / h, abs(fx), abs(fz)))
out["dip_deg"] = float(dip); out["aim"] = tab; json.dump(out, open("build/sightcheck.json", "w"), indent=1)
