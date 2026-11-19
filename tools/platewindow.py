"""Where can the front plate be, and where does it come off?  Measured on the meshes, printed fat and thin (tolerance.py's way), for the model as it is and for round 5's:
  - the map of (to the side, above home) positions with the plate flat on the face; where it can be set straight on or lifted straight off (free flat, 1 mm and 3 mm off);
    where its feet begin to enter (free 0.3 mm in): the window a hand has to find;
  - how far it can be pulled off the face before something holds it (hooks near home, side lips higher up), by height and by how far across it is.
-> build/platewindow.json (read by platefall.py)"""
import sys, json, time, numpy as np, trimesh, manifold3d as m3
sys.path.insert(0, "tools"); from scadr import values
import tolerance as tol
V = values(["Y_FRONT", "FOOT_D"]); YF = V["Y_FRONT"]; EPS = 0.02
P = [(-0.15, 0.0, "far too thin: walls -0.15"), (-0.08, 0.0, "thin: walls -0.08"), (0.0, 0.0, "as drawn"), (0.10, 0.15, "typical: walls +0.10"), (0.15, 0.20, "fat: walls +0.15"), (0.25, 0.40, "far too fat: walls +0.25")]
box = m3.Manifold.cube((90.0, 9.0, 70.0)).translate((-45.0, YF - 8.0, -35.0)); boxf = m3.Manifold.cube((90.0, 9.0, 70.0)).translate((-45.0, YF - 8.5, -35.0))
def measure(asm, two, show=False):
    out = {}; tol.A = asm
    xs = [round(x, 2) for x in np.arange(-1.2, 5.61, 0.1)] if two else [round(x, 2) for x in np.arange(-1.2, 1.21, 0.1)]; zs = [round(z, 2) for z in np.arange(-0.6, 7.41, 0.1)]
    for e, ef, label in P:
        t0 = time.time(); body = tol.man(tol.grow(tol.load("body"), "body", e, ef)) ^ box; FR = tol.man(tol.grow(tol.load("frontN_TOOTH_H0.02"), "frontN", e, ef)) ^ boxf          # the feet and the post: what goes into the body
        def free(sx, dy, dz): return (FR.translate((-sx, dy, dz)) ^ body).volume() < EPS
        def dmax(sx, dz, hi=3.4):                                                                        # how far off the face before something holds
            if not free(sx, 0.0, dz): return None
            if free(sx, hi, dz) and free(sx, hi / 2, dz) and free(sx, hi / 4, dz): return hi
            a, b = 0.0, hi
            for d_ in (hi / 4, hi / 2):
                if not free(sx, d_, dz): b = d_; break
                a = d_
            for _ in range(7):
                m_ = (a + b) / 2
                if free(sx, m_, dz): a = m_
                else: b = m_
            return round(a, 2)
        G = {dy: np.array([[free(sx, dy, dz) for sx in xs] for dz in zs]) for dy in ((0.0, 1.0, 3.0, V["FOOT_D"] - 0.3) if two else (0.0, 1.0, 3.0))}
        g0 = G[0.0]; on = g0 & G[1.0] & G[3.0]; ii = np.argwhere(on); r = dict(e=e, home=round(2 * e, 2)); i00 = xs.index(0.0); col = np.argwhere(g0[:, i00])[:, 0]; r["top_stop"] = zs[np.argwhere(g0)[:, 0].max()]
        jh = min(range(len(zs)), key=lambda j: abs(zs[j] - (2 * e + 0.6))); row = np.argwhere(g0[jh])[:, 0]; r["side_play_at_home"] = [xs[row.min()], xs[row.max()]]
        j0, j1, i0, i1 = ii[:, 0].min(), ii[:, 0].max(), ii[:, 1].min(), ii[:, 1].max(); r["set_on"] = dict(side=[xs[i0], xs[i1]], up=[zs[j0], zs[j1]], wide=round(xs[i1] - xs[i0] + 0.1, 1), tall=round(zs[j1] - zs[j0] + 0.1, 1))
        if two:
            m = np.argwhere(G[V["FOOT_D"] - 0.3]); r["catches"] = dict(side=[xs[m[:, 1].min()], xs[m[:, 1].max()]], up=[zs[m[:, 0].min()], zs[m[:, 0].max()]], wide=round(xs[m[:, 1].max()] - xs[m[:, 1].min()] + 0.1, 1), tall=round(zs[m[:, 0].max()] - zs[m[:, 0].min()] + 0.1, 1))
            jb = [j for j in range(len(zs)) if g0[j, xs.index(1.5)]]; r["band"] = [zs[min(jb)], zs[max(jb)]]; r["across_to"] = xs[np.argwhere(g0[min(jb) + 2])[:, 0].max()]
        h = 2 * e; r["pull_off_by_height"] = [[round(z, 2), dmax(0.0, h + z)] for z in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.4, 2.8, 3.2)]
        if two:
            zb = (r["band"][0] + r["band"][1]) / 2; r["pull_off_by_side_in_band"] = [[sx, dmax(sx, zb)] for sx in (0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8)]
            r["pull_off_at_side_stop_below_band"] = dmax(max(r["side_play_at_home"][1] - 0.1, 0.0), h + 2.6)
        out[label] = r; print(f"{label:28s} {json.dumps(r)}   {time.time() - t0:.0f} s", flush=True)
        if show and e == 0.0:
            for j in range(len(zs) - 1, -1, -2): print("   %4.1f " % zs[j] + "".join("o" if on[j, i] else ("c" if two and G[V["FOOT_D"] - 0.3][j, i] and not g0[j, i] else ("." if g0[j, i] else "#")) for i in range(len(xs))))
    return out
if __name__ == "__main__":
    res = {}
    if "old" not in sys.argv[1:]: res["now"] = measure("build/asm/", True, True)
    try: res["round5"] = json.load(open("build/platewindow.json"))["round5"]
    except Exception: res["round5"] = None
    if res["round5"] is None or "old" in sys.argv[1:]:
        res["round5"] = measure("build/old29/asm/", False)
        if "now" not in res: res["now"] = json.load(open("build/platewindow.json"))["now"]
    json.dump(res, open("build/platewindow.json", "w"), indent=1)
