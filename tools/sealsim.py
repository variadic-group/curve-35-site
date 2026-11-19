"""How much stray light gets through the joint between body and back?  A cross-section of the joint, light entering the crack from outside,
every surface matt and dark: a ray that hits plastic is scattered in a random direction and loses all but a fraction R of its light.
Counts what reaches the inside.  The same crack, the same plastic and the same gaps for every joint, so the joints can be compared.
(The straight-line test in tools/optics.py only asks whether light can get in WITHOUT touching plastic; this asks how much gets in after bouncing.)
    python3 tools/sealsim.py            -> build/sealsim.json, build/sealsim.png"""
import sys, json, numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

def joint(kind, s, zone="chamber"):
    """body and back in section.  u: inward from the outside face; v: up from the back's inner face.  s: how far the back stands off the rim (0 = pressed home)."""
    B = 12.0; top = 9.0                                              # the section is drawn 12 mm inward and 9 mm up
    def body(steps, end):                                            # steps: [(u0, u1, depth cut from the rim)]; the body ends at `end` (a chamber begins there)
        return unary_union([box(u0, s + d, u1, top) for u0, u1, d in steps])
    plate = box(-3.0, -3.0, B, 0.0)
    if kind == "tongue":                                             # v2.5: a 1.4 mm tongue in a 2.2 mm groove, 2.1 deep
        if zone == "chamber": bd = body([(0, 1.4, 0), (1.4, 3.6, 2.1), (3.6, 5.6, 0)], 5.6); bk = [box(1.8, 0, 3.2, 1.8)]
        else: bd = body([(-3, 0.2, 0), (0.2, 2.4, 2.1), (2.4, 3.9, 0)], 3.9); bk = [box(0.6, 0, 2.0, 1.8)]             # between the latches: the slit is 0.2 mm from the groove, the inner wall is 1.5 mm
    elif kind == "lap":                                              # one step: lip 2.3, band 2.3 wide and 2.2 high in a step 2.4 deep
        if zone == "chamber": bd = body([(0, 2.3, 0), (2.3, 5.6, 2.4)], 5.6); bk = [box(2.6, 0, 4.9, 2.2)]
        else: bd = body([(-3, 1.0, 0), (1.0, 3.9, 2.4)], 3.9); bk = [box(1.3, 0, 3.6, 2.2)]
    elif kind == "two steps":                                        # two steps: lip 2.0, a step 1.2 high and 1.3 wide, a band 2.0 wide and 2.2 high
        if zone == "chamber": bd = body([(0, 2.0, 0), (2.0, 3.3, 1.2), (3.3, 5.6, 2.4)], 5.6); bk = [box(2.3, 0, 3.6, 1.0), box(3.6, 0, 5.6, 2.2)]
        else: bd = body([(-3, 0.3, 0), (0.3, 1.6, 1.2), (1.6, 3.9, 2.4)], 3.9); bk = [box(0.6, 0, 1.9, 1.0), box(1.9, 0, 3.9, 2.2)]
    elif kind == "two steps, snug (as built)":                       # v2.6 as built: the same two steps, but step and band are as high as the body's steps are deep (1.2 and 2.4): pressed home they touch
        if zone == "chamber": bd = body([(0, 2.0, 0), (2.0, 3.3, 1.2), (3.3, 5.6, 2.4)], 5.6); bk = [box(2.3, 0, 3.6, 1.2), box(3.6, 0, 5.6, 2.4)]
        else: bd = body([(-3, 0.3, 0), (0.3, 1.6, 1.2), (1.6, 3.9, 2.4)], 3.9); bk = [box(0.6, 0, 1.9, 1.2), box(1.9, 0, 3.9, 2.4)]
    elif kind == "two steps, tall":                                  # the same, each riser 1.6 mm: 3.2 mm of step in all
        if zone == "chamber": bd = body([(0, 2.0, 0), (2.0, 3.3, 1.6), (3.3, 5.6, 3.2)], 5.6); bk = [box(2.3, 0, 3.6, 1.4), box(3.6, 0, 5.6, 3.0)]
        else: bd = body([(-3, 0.3, 0), (0.3, 1.6, 1.6), (1.6, 3.9, 3.2)], 3.9); bk = [box(0.6, 0, 1.9, 1.4), box(1.9, 0, 3.9, 3.0)]
    elif kind == "three steps":                                      # three steps of 1 mm
        if zone == "chamber": bd = body([(0, 1.6, 0), (1.6, 2.8, 1.0), (2.8, 4.0, 2.0), (4.0, 5.6, 3.0)], 5.6); bk = [box(1.9, 0, 3.1, 0.8), box(3.1, 0, 4.3, 1.8), box(4.3, 0, 5.6, 2.8)]
        else: bd = body([(-3, 0.2, 0), (0.2, 1.2, 1.0), (1.2, 2.2, 2.0), (2.2, 3.9, 3.0)], 3.9); bk = [box(0.5, 0, 1.5, 0.8), box(1.5, 0, 2.5, 1.8), box(2.5, 0, 3.9, 2.8)]
    elif kind == "curb + two steps":                                 # two steps, and a curb on the back outside the body's wall (not possible between the latches: there it is two steps alone)
        if zone == "chamber": bd = body([(0, 2.0, 0), (2.0, 3.3, 1.2), (3.3, 5.6, 2.4)], 5.6); bk = [box(-2.3, 0, -0.3, 2.2), box(2.3, 0, 3.6, 1.0), box(3.6, 0, 5.6, 2.2)]
        else: bd = body([(-3, 0.3, 0), (0.3, 1.6, 1.2), (1.6, 3.9, 2.4)], 3.9); bk = [box(0.6, 0, 1.9, 1.0), box(1.9, 0, 3.9, 2.2)]
    elif kind == "stout tongue":                                     # tongue and groove again, but nothing under 1.6 mm: lip 1.6, tongue 1.8 in a 2.4 groove 2.4 deep, inner wall 1.6
        if zone == "chamber": bd = body([(0, 1.6, 0), (1.6, 4.0, 2.4), (4.0, 5.6, 0)], 5.6); bk = [box(1.9, 0, 3.7, 2.2)]
        else: bd = body([(-3, 0.1, 0), (0.1, 2.3, 2.4), (2.3, 3.9, 0)], 3.9); bk = [box(0.4, 0, 2.0, 2.2)]
    return bd, unary_union([plate] + bk), (-3.0 if zone == "latch" else 0.0)

def segments(g):
    out = []
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        for ring in [p.exterior] + list(p.interiors):
            c = np.array(ring.coords); out.append(np.hstack([c[:-1], c[1:]]))
    return np.vstack(out)

def run(kind, s, zone, R=0.15, n=1000000, seed=1):
    """returns the fraction of the light entering the crack (or the latch slit) that reaches the inside"""
    rng = np.random.default_rng(seed); bd, bk, _ = joint(kind, s, zone); u_in = 6.5 if zone == "chamber" else 4.5; curb = kind.startswith("curb") and zone == "chamber"
    if zone == "latch": bk = bk.difference(box(-1.6, -3.1, 0.0, 0.01))                       # the latch slit: 1.6 mm wide, through the back, just outside the joint
    W = segments(unary_union([bd, bk])); lo_u = -3.6
    # the edge of the section: light that reaches the far right ABOVE the back has got in; everything else that leaves is gone
    E = np.array([[u_in, 0.0, u_in, 9.5], [u_in, -3.6, u_in, 0.0], [lo_u, -3.6, u_in, -3.6], [lo_u, -3.6, lo_u, 9.5], [lo_u, 9.5, u_in, 9.5]]); S = np.vstack([W, E]); kind_of = np.r_[np.zeros(len(W), int), [1, 2, 2, 2, 2]]
    A, Bv = S[:, :2], S[:, 2:] - S[:, :2]; ang = np.arcsin(rng.uniform(-1, 1, n))
    if zone == "latch": o = np.c_[rng.uniform(-1.59, -0.01, n), np.full(n, -3.05)]; d = np.c_[np.sin(ang), np.cos(ang)]
    elif curb: o = np.c_[rng.uniform(-0.294, -0.006, n), np.full(n, 2.2 + 0.001)]; d = np.c_[np.sin(ang), -np.cos(ang)]      # with a curb the way in is the 0.3 mm gap between curb and wall, from above
    else: o = np.c_[np.full(n, -0.001), rng.uniform(0.02 * s, 0.98 * s, n)]; d = np.c_[np.cos(ang), np.sin(ang)]
    w = np.ones(n); alive = np.ones(n, bool); got = 0.0
    for it in range(200):
        idx = np.nonzero(alive)[0]
        if len(idx) == 0: break
        oo, dd = o[idx][:, None, :], d[idx][:, None, :]
        den = dd[..., 0] * Bv[None, :, 1] - dd[..., 1] * Bv[None, :, 0]; ok = np.abs(den) > 1e-14; den = np.where(ok, den, 1.0)
        ao = A[None] - oo; t = (ao[..., 0] * Bv[None, :, 1] - ao[..., 1] * Bv[None, :, 0]) / den; u = (ao[..., 0] * dd[..., 1] - ao[..., 1] * dd[..., 0]) / den
        t = np.where(ok & (t > 1e-9) & (u >= -1e-9) & (u <= 1 + 1e-9), t, np.inf); k = t.argmin(1); tm = t[np.arange(len(idx)), k]
        typ = kind_of[k]; none = ~np.isfinite(tm); inside = (typ == 1) & ~none; gone = (typ == 2) | none
        got += w[idx][inside].sum(); alive[idx[inside | gone]] = False
        go = ~(inside | gone); gi = idx[go]; kk = k[go]; p = o[gi] + d[gi] * tm[go][:, None]
        nn = np.c_[Bv[kk, 1], -Bv[kk, 0]]; nn /= np.linalg.norm(nn, axis=1)[:, None]; flip = (nn * d[gi]).sum(1) > 0; nn[flip] *= -1
        th = np.arcsin(rng.uniform(-1, 1, len(gi))); tg = np.c_[-nn[:, 1], nn[:, 0]]; d[gi] = nn * np.cos(th)[:, None] + tg * np.sin(th)[:, None]; o[gi] = p + nn * 1e-5
        w[gi] *= R; alive[gi[w[gi] < 1e-18]] = False
    return got / n

if __name__ == "__main__":
    KINDS = ["two steps, snug (as built)", "tongue", "stout tongue", "lap", "two steps", "two steps, tall", "curb + two steps"]
    try: out = json.load(open("build/sealsim.json"))                 # cases already computed are kept: delete the file to run them all again
    except Exception: out = {}
    for R in (0.3, 0.15):                                             # how much light a surface throws back: 0.3 is glossy or pale plastic, 0.15 a dark matt one
        for zone in ("chamber", "latch"):
            for s in (0.15, 0.3):
                for kind in KINDS:
                    if f"R {R} | {zone} | off {s} | {kind}" in out: continue
                    r = [run(kind, s, zone, R=R, seed=k, n=500000) for k in (1, 2)]; out[f"R {R} | {zone} | off {s} | {kind}"] = [float(np.mean(r)), float(np.std(r))]
                print(f"R {R}", zone, "back off the rim by", s, "mm:", "   ".join(f"{k}: {out[f'R {R} | {zone} | off {s} | {k}'][0]:.1e}" for k in KINDS), flush=True)
                json.dump(out, open("build/sealsim.json", "w"), indent=1)
