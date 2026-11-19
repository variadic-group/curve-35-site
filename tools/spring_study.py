"""Shape study for the rim springs (blade and wheel): force and peak strain against length, thickness and taper."""
import sys, numpy as np, shapely, io, contextlib
sys.path.insert(0, "tools"); import fea
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
def pol(c, r, a): return (c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a)))
def sector(c, r0, r1, a0, a1, n=60):
    a = np.linspace(a0, a1, n); r0 = np.broadcast_to(r0, a.shape); r1 = np.broadcast_to(r1, a.shape)
    return Polygon([pol(c, r, t) for r, t in zip(r0, a)] + [pol(c, r, t) for r, t in zip(r1[::-1], a[::-1])])
def rimspring(R, L, s_root, s_tip, t_tip, rk=0.8, bump=0.95, c=(0.0, 0.0), root=3.0, rim=5.0):
    """tip (bump) at 90 deg, rooted L mm clockwise of it.  Inner face follows the slit (s_root -> s_tip); the outer face is a circle."""
    rm = R + s_tip + t_tip / 2; arc = np.degrees(L / rm); dr = np.degrees(root / rm); a0 = 90 - arc; ro = R + s_tip + t_tip
    th = np.linspace(a0, 90 + np.degrees(1.0 / rm), 80); s = s_root + (s_tip - s_root) * np.clip((th - a0) / arc, 0, 1)
    beam = Polygon([pol(c, R + q, t) for q, t in zip(s, th)] + [pol(c, ro, t) for t in th[::-1]])
    parts = [sector(c, R - rim, R, a0 - dr - np.degrees(6 / rm), 90 + np.degrees(4 / rm)), sector(c, R - 0.5, ro, a0 - dr, a0 + 0.01), beam, Point(pol(c, ro + bump - 0.7, 90)).buffer(0.7, 24)]
    key = Point(pol(c, R + s_root - rk, a0)).buffer(rk, 32).intersection(sector(c, R - 3, R + s_root + 0.001, a0 - np.degrees(2 * rk / rm), a0 + np.degrees(2 * rk / rm)))
    return unary_union(parts).difference(key).buffer(0), pol(c, ro + bump, 90), pol(c, R + s_root, a0), arc
def study(tag, R, cases, bends, stop_from_slit=True, thick=1.0):
    print(f"{tag}: R {R}\n   L   slit(root>tip)  t(root>tip)  rk |  N/mm | " + " | ".join(f"strain% @{b}" for b in bends) + " | at stop")
    for (L, s0, s1, tt, rk) in cases:
        poly, tip, rootp, arc = rimspring(R, L, s0, s1, tt, rk); buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r, f = fea.run("x", poly, lambda x, y: np.full_like(x, thick), lambda x, y: np.hypot(x, y) < R - 4.0, [(tip, (None, -1.0))], h=1.5, fine=[(rootp[0], rootp[1], 3.5, 0.07), (0, R + 1, L + 2, 0.3)])
        k = r["force_N"]; e = r["peak_strain_pct"]
        print(f"  {L:4.1f}   {s0:.1f} > {s1:.1f}      {tt + s1 - s0:.2f} > {tt:.2f}   {rk:.1f} | {k:5.3f} | " + " | ".join(f"{e * b:5.2f} ({k * b:.2f} N)" for b in bends) + f" | {e * s1:5.2f}   arc {arc:.1f} deg")
if __name__ == "__main__":
    B = (0.3, 0.55, 0.85)
    study("blade", 33.26, [(18, 1.0, 1.0, 1.2, 0.8), (28, 1.0, 1.0, 1.6, 0.8), (28, 1.0, 1.0, 1.8, 0.8), (28, 1.0, 1.0, 2.0, 0.8), (28, 1.2, 1.2, 1.8, 1.0), (28, 0.7, 1.2, 1.3, 0.8), (28, 0.7, 1.2, 1.5, 0.8), (28, 0.7, 1.2, 1.7, 0.8), (28, 0.7, 1.3, 1.5, 1.0), (30, 0.7, 1.2, 1.6, 0.8)], B)
    study("wheel", 15.8, [(15, 1.0, 1.0, 1.2, 0.8), (22, 1.0, 1.0, 1.4, 0.8), (24, 1.0, 1.0, 1.4, 0.8), (24, 1.0, 1.0, 1.6, 0.8), (24, 0.7, 1.2, 1.2, 0.8), (24, 0.7, 1.2, 1.4, 0.8), (26, 0.7, 1.2, 1.4, 0.8), (28, 0.7, 1.2, 1.5, 0.8)], B)
