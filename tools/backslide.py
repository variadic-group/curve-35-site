"""Could the back slide onto hooks like the front plate?  The back (latch nubs taken off) is set S mm to one side of home, in each of the
four directions it could slide from, and compared with everything it meets: at home depth, and on its way in from behind."""
import json, numpy as np, trimesh, manifold3d as m3
A = "build/asm/"
def load(n): return trimesh.load(A + n + ".stl", process=True)
def man(t): return m3.Manifold(m3.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
back = load("backN_NUB_H0.02"); others = {n: man(load(n)) for n in ["body", "roller", "knob", "spool", "cassette", "film"]}
def at(v): t = back.copy(); t.apply_translation(v); return man(t)
def where(m):                                    # bounding box of an overlap
    b = m.bounding_box(); return [round(float(x), 1) for x in b]
out = {}
for S in (1.5, 3.0):
    for name, d in [("from the right (+x)", (1, 0, 0)), ("from the left (-x)", (-1, 0, 0)), ("from above (+z)", (0, 0, 1)), ("from below (-z)", (0, 0, -1))]:
        row = {}
        for pull in (0.0, 1.0, 2.0, 4.0, 8.0):   # how far behind home the back still is
            b = at([S * d[0], -pull, S * d[2]]); tot = {}
            for n, m in others.items():
                x = b ^ m; v = x.volume()
                if v > 0.002: tot[n] = [round(v, 2)] + where(x)
            row["%.0f mm behind home" % pull] = tot
        out["set %.1f mm %s" % (S, name)] = row
        home = row["0 mm behind home"]
        print("set %.1f mm %-20s at home depth it would stand inside: %s" % (S, name, ", ".join("%s %.1f mm3" % (k, v[0]) for k, v in home.items()) or "nothing"))
        for k, v in home.items(): print("      %-9s x %6.1f..%6.1f  y %6.1f..%6.1f  z %6.1f..%6.1f" % (k, v[1], v[4], v[2], v[5], v[3], v[6]))
json.dump(out, open("build/backslide.json", "w"), indent=1)
