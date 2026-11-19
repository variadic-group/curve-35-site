"""Print rules.  Reads every print file layer by layer, the way it lies on the bed, and lists what a desktop printer is likely to get wrong:
  A  walls, ribs and posts thinner than three lines of plastic (1.2 mm);
  B  small free-standing features that are tall for their width (a post under 4 mm wide taller than twice its width, a thicker post three times; a wall taller than four times its thickness);
  C  a part (or a neck in it) that carries more than five times its own width above it;
  F  a first layer in more than one piece, or with an opening under 2 mm;
  S  a floor or a roof thinner than three layers (0.6 mm) over a patch at least 1.5 mm wide.
Narrow strips between 1.2 and 2.2 mm wide (three to five lines) are listed too, and every one in the model is named below (KNOWN): it is either a spring or a
finger that is meant to bend (strength-checked in fea_cases.py) or a low wall joined to the part along its whole length.  A strip with no name is a finding.
    python3 tools/printrules.py                 the model as it is now  -> build/printrules.json, build/printrules/<part>.png
    python3 tools/printrules.py before          the version before (build/old24 here, previous/v2.4 inside the package) -> build/printrules_v24.json
    python3 tools/printrules.py <dir> <tag>     print files in any other folder -> build/printrules_<tag>.json"""
import sys, os, json, collections, numpy as np, trimesh
from shapely.ops import unary_union
from shapely.affinity import affine_transform
from shapely.geometry import Polygon
sys.path.insert(0, "tools"); from printcards import inertia
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LH = 0.2; MIN_WALL = 1.2; STRIP = 2.2; PARTS = ["body", "back", "front", "blade", "wheel", "roller", "knob", "spool"]
NAMES = dict(body="Body", back="Back", front="Front plate", blade="Shutter", wheel="Aperture wheel", roller="Frame wheel", knob="Wind knob", spool="Take-up spool")
# Every narrow strip in the model as it is now: where it lies on the bed (x, y of its largest layer), what kind it is, what it is.
KNOWN = dict(
 body=[((-42.4, -27.2), "wall", "floor under the slot for the cassette's long hub: 2 mm thick"), ((39.0, -27.3), "wall", "floor under the slot for the spool's journal: 2 mm thick"),
       ((-17.0, 27.2), "wall", "rear end of the catch (two posts and their bar), bevelled: 2 mm wide, the last three layers"), ((-17.0, -27.2), "wall", "the same, bottom"), ((3.7, 27.2), "wall", "rear end of the catch's tab, bevelled: 2 mm wide, the last three layers"), ((3.7, -27.2), "wall", "the same, bottom"),
       ((-62.6, 0.0), "wall", "rim lip round the cassette end: 2 mm wide, a kerb 1.2 mm high, joined to the wall along its whole length"), ((62.1, 0.0), "wall", "rim lip round the take-up end: the same kerb"),
       ((-32.5, 27.2), "wall", "rim lip along the top: the same kerb"), ((-32.5, -27.2), "wall", "rim lip along the bottom: the same kerb"),
       ((-17.7, 0.0), "wall", "side of the picture frame, the 0.6 mm below its edge"), ((17.7, 0.0), "wall", "side of the picture frame, the 0.6 mm below its edge"),
       ((28.7, 18.9), "wall", "step under the front edge of the frame wheel's fork, with the tongue that fills the fork's mouth: 2 mm thick, joined to the pocket's front wall along its whole length")],
 back=[((-3.4, -24.3), "spring", "latch finger"), ((-3.4, 24.3), "spring", "latch finger"), ((5.0, -24.6), "spring", "latch finger (the same one, above its first layer)"), ((5.0, 24.6), "spring", "latch finger (the same one, above its first layer)"),
       ((-51.1, 8.0), "wall", "seal band, all round: 2 mm wide; it stands 1.2 mm above the low step beside it"), ((47.6, 10.0), "wall", "seal band, all round (the take-up half)"),
       ((-30.0, -22.8), "wall", "seal band, where it steps inward past a latch"), ((-30.0, 22.8), "wall", "seal band, where it steps inward past a latch")],
 front=[((33.3, -1.6), "wall", "edge of the plate beside the latch leaf's slit: 1.4 mm wide, 5 mm high")], blade=[((-1.4, -5.9), "spring", "click spring round the rim")],
 wheel=[((-23.4, 2.2), "spring", "click spring round the rim"), ((-17.9, 14.7), "wall", "rim of the finger dish on top of the handle: 0.6 mm high, on solid plastic")])
# Thin places that are kept on purpose, with the reason.
ACCEPT = dict(body=[((-17.4, 0.0), "edge of the picture frame"), ((17.4, 0.0), "edge of the picture frame")],
              blade=[((-5.3, -5.2), "thin half of the shutter's click spring"), ((12.2, -12.9), "foot of the click tooth")],
              roller=[((27.6 + 6.5 * np.cos(np.radians(45 * k)), 5.4 + 6.5 * np.sin(np.radians(45 * k))), "tooth of the frame wheel") for k in range(8)])
ACCEPT_WHY = {"thin half of the shutter's click spring": "since v2.18 the spring tapers from 1.76 mm where it joins the shutter to 0.9 mm (two lines of plastic) at its tooth, so that it bends evenly along its length: 0.35 % strain when pressed "
                                                         "in place of 0.53 % (tools/springsearch.py).  It is a spring, and thin on purpose.  Sliced five ways (Arachne and classic walls, 0.40, 0.45 and 0.50 mm lines, a 0.6 mm nozzle) "
                                                         "it comes out within 0.04 mm of its drawn thickness everywhere, with no gap between its lines",
              "foot of the click tooth": "the corner where the tooth's flank meets the end of the spring, 0.4 mm wide and joined on two sides.  It was there before; the rule finds it now because the spring beside it is under 1.2 mm",
              "edge of the picture frame": "a ridge 0.9 mm wide and 0.6 mm high along each side of the picture, standing on solid plastic.  It is two lines of plastic, it sets the edge of the picture and it carries nothing",
              "tooth of the frame wheel": "each tooth tapers from 1.5 mm at its root to 0.4 mm at its tip, 1.2 mm out from the drum and 1.5 mm tall, standing on the bed.  It has to be narrower than the hole in the film it enters (2.0 mm), "
                                          "and since v2.12 it tapers straight so that it clears the hole's edge on the way in (tools/motion.py).  It carries only the film's pull on a free wheel.  Sliced, the plastic reaches the same radius as the older, stouter tooth"}
def name_them(part, r):
    """give every strip its name and kind; move the thin places that are kept on purpose to their own list"""
    for s_ in r["strips"]:
        k = min(KNOWN.get(part, []), key=lambda q: np.hypot(q[0][0] - s_["at"][0], q[0][1] - s_["at"][1]), default=None)
        if k is not None and np.hypot(k[0][0] - s_["at"][0], k[0][1] - s_["at"][1]) < 6.0: s_["kind"], s_["what"] = k[1], k[2]
        else: s_["kind"], s_["what"] = "not explained", "NOT EXPLAINED"
    keep = [(t, next((a for a in ACCEPT.get(part, []) if np.hypot(a[0][0] - t["at"][0], a[0][1] - t["at"][1]) < 3.0), None)) for t in r["thin"]]
    r["accepted"] = [dict(t, what=a[1], why=ACCEPT_WHY[a[1]]) for t, a in keep if a]; r["thin"] = [t for t, a in keep if not a]

def geoms(g): return [q for q in (g.geoms if hasattr(g, "geoms") else [g]) if q.geom_type == "Polygon" and q.area > 0.02]
def inscribed(p, hi=12.0):
    """diameter of the largest circle that fits in a polygon"""
    lo = 0.0
    for _ in range(10):
        mid = (lo + hi) / 2
        if p.buffer(-mid).is_empty: hi = mid
        else: lo = mid
    return 2 * lo
def layers(m):
    zs = np.arange(LH / 2, float(m.bounds[1][2]), LH); out = []
    for s in m.section_multiplane([0, 0, 0], [0, 0, 1], zs):
        if s is None: out.append([]); continue
        T = s.metadata["to_3D"]; out.append([q for p in s.polygons_full for q in geoms(affine_transform(p.buffer(0), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]))])
    return zs, out
def narrow(g, w):
    """the places in a layer that are narrower than w, without the slivers an opening leaves in every corner"""
    r = w / 2 - 0.01; rest = g.difference(g.buffer(-r).buffer(r + 0.02)); return [q for q in geoms(rest) if q.area > 0.3]
def strips(L, zs, w0, w1):
    """places narrower than w1 (and not narrower than w0) that go on for at least three layers: [where, width, length, from z, to z]"""
    per = []
    for comps in L:
        g = unary_union(comps) if comps else None; a = narrow(g, w1) if g is not None else []; b = unary_union(narrow(g, w0)).buffer(0.05) if (g is not None and w0 > 0) else None
        per.append([q for q in a if b is None or b.is_empty or q.difference(b).area > 0.5 * q.area])
    found = []                                                                        # join what lies over each other from layer to layer
    for k, qs in enumerate(per):
        for q in qs:
            t = next((t for t in found if t["k1"] >= k - 1 and t["last"].buffer(0.3).intersects(q)), None)
            if t is None: found.append(dict(k0=k, k1=k, last=q, all=[q]))
            else: t["last"] = unary_union([t["last"], q]) if t["k1"] == k else q; t["k1"] = k; t["all"].append(q)
    for f in found: f["u"] = unary_union(f["all"])
    merged = []                                                                       # one strip can be followed as two (it splits for a layer or two): put together what lies on the same ground
    for f in sorted(found, key=lambda f: -f["u"].area):
        t = next((t for t in merged if t["k0"] <= f["k1"] + 1 and f["k0"] <= t["k1"] + 1 and t["u"].intersection(f["u"]).area > 0.5 * f["u"].area), None)
        if t is None: merged.append(f)
        else: t["all"] += f["all"]; t["k0"] = min(t["k0"], f["k0"]); t["k1"] = max(t["k1"], f["k1"]); t["u"] = unary_union([t["u"], f["u"]])
    out = []
    for f in sorted(merged, key=lambda f: (f["k0"], f["u"].centroid.x, f["u"].centroid.y)):
        if f["k1"] - f["k0"] < 2: continue
        big = max(f["all"], key=lambda q: q.area); u = f["u"]; out.append(dict(at=[round(big.centroid.x, 1), round(big.centroid.y, 1)], width=round(inscribed(big, 3.0), 2), length=round(big.length / 2, 1),
                                                                                             z0=round(float(zs[f["k0"]] - LH / 2), 1), z1=round(float(zs[f["k1"]] + LH / 2), 1), shape=u))
    return out
def features(L, zs):
    """free-standing features: a piece of a layer that stands on a much larger piece, or on a piece that carries other pieces as well; followed upward until it ends or joins another"""
    F = []; fid = {}
    for k, comps in enumerate(L):
        prev = L[k - 1] if k else []; par = [[j for j, p in enumerate(prev) if p.intersects(c) and p.intersection(c).area > 0.02] for c in comps]; kids = collections.Counter(j for ps in par for j in ps)
        for i, c in enumerate(comps):
            ps = par[i]
            if len(ps) == 1 and kids[ps[0]] == 1 and c.area >= 0.7 * prev[ps[0]].area: f = fid[(k - 1, ps[0])]                        # the same thing, one layer higher
            elif len(ps) > 1: f = fid[(k - 1, max(ps, key=lambda j: prev[j].area))]                                                     # two things join: a bridge.  It goes on as the larger one
            else: F.append(dict(k0=k, base=c, parent=fid[(k - 1, ps[0])] if ps else None, amin=c.area, small=c)); f = len(F) - 1
            fid[(k, i)] = f; F[f]["k1"] = k
            if c.area < F[f]["amin"]: F[f]["amin"] = c.area; F[f]["small"] = c
    top = [f["k1"] for f in F]
    for i in range(len(F) - 1, -1, -1):
        if F[i]["parent"] is not None: top[F[i]["parent"]] = max(top[F[i]["parent"]], top[i])
    out = []
    for i, f in enumerate(F):
        if f["parent"] is None or f["base"].area > 400: continue
        w = inscribed(f["base"]); h = (top[i] - f["k0"] + 1) * LH                                    # width where it stands; a rounded or pointed top is not held against it
        out.append(dict(at=[round(f["base"].centroid.x, 1), round(f["base"].centroid.y, 1)], width=round(w, 2), height=round(h, 1), from_z=round(float(zs[f["k0"]] - LH / 2), 1), footprint_mm2=round(f["base"].area, 1), wall=bool(f["base"].area > 3 * w * w), shape=f["base"]))
    return out
def skins(L):
    """floors and roofs thinner than three layers: plastic that begins in one layer and has stopped again one or two layers later, over a patch at least
    1.5 mm wide (the thin rings that every sloping surface leaves do not count)"""
    E = Polygon(); U = [unary_union(c) if c else E for c in L]; out = []
    wide = lambda g: [q for q in geoms(g.buffer(-0.75).buffer(0.75)) if q.area > 3.0]
    for k in range(len(U)):
        start = U[k].difference(U[k - 1]) if k else U[k]                                    # what begins in this layer (on the bed: everything)
        if start.is_empty: continue
        for n in (1, 2):
            thin = start.difference(U[k + n] if k + n < len(U) else E)
            if n == 2: thin = thin.intersection(U[k + 1] if k + 1 < len(U) else E)
            out += [dict(at=[round(q.centroid.x, 1), round(q.centroid.y, 1)], z0=round(k * LH, 1), thick_mm=round(n * LH, 1), area_mm2=round(q.area, 1)) for q in wide(thin)]
    return out
def audit(path):
    m = trimesh.load(path, process=True); zs, L = layers(m); H = float(m.bounds[1][2]); r = dict(height_mm=round(H, 1))
    thin = strips(L, zs, 0.0, MIN_WALL); strip = strips(L, zs, MIN_WALL, STRIP); feat = features(L, zs)
    r["skins"] = skins(L)
    r["thin"] = thin; r["strips"] = [s for s in strip if s["length"] >= 12.0]                                                           # short narrow places are steps and lips, not strips
    r["slender"] = [f for f in feat if f["height"] >= 1.0 and f["footprint_mm2"] <= 60 and f["height"] > (4.0 if f["wall"] else 2.0 if f["width"] < 4.0 else 3.0) * f["width"]]   # a post under 4 mm wide may be twice as tall as it is wide, a thicker one three times; a wall (three times longer than thick) four times
    # C: the level that carries the most part above it for its width (width = the round bar that would be as stiff as that layer, as in printcards.py)
    worst = (0.0, 0.0, 0.0)
    for k, comps in enumerate(L):
        above = H - zs[k]
        if above < 5.0 or not comps: continue
        w = (64 * inertia(unary_union(comps))[1] / np.pi) ** 0.25
        if above / w > worst[0]: worst = (above / w, w, above)
    r["carries"] = dict(ratio=round(worst[0], 1), width_mm=round(worst[1], 1), above_mm=round(worst[2], 1))
    first = L[0]; r["first_layer"] = dict(pieces=len(first), openings=sum(len(q.interiors) for q in first), small_openings=sum(1 for q in first for h in q.interiors if inscribed(Polygon(h), 6.0) < 2.0))
    r["footprint"] = unary_union([q for comps in L for q in comps]).simplify(0.05)
    return r
def picture(part, r, out, title):
    fig, ax = plt.subplots(figsize=(7.2, 5.0)); fp = r["footprint"]
    for q in geoms(fp):
        ax.fill(*q.exterior.xy, fc="#e9ebef", ec="#7b818c", lw=0.8)
        for h in q.interiors: ax.fill(*h.xy, fc="white", ec="#7b818c", lw=0.6)
    def draw(items, col, label):
        for s in items:
            for q in geoms(s["shape"].buffer(0.25)): ax.fill(*q.exterior.xy, fc=col, ec=col, lw=1.2, alpha=0.9)
            ax.annotate(label(s), s["at"], xytext=(6, 6), textcoords="offset points", fontsize=7, color="#1a1c20")
    draw(r["strips"], "#2a78d6", lambda s: f"strip {s['width']:.1f} wide"); draw(r.get("accepted", []), "#8e44ad", lambda s: f"{s['width']:.1f} mm, kept on purpose"); draw(r["thin"], "#d0342c", lambda s: f"{s['width']:.1f} mm thin, {s['z1'] - s['z0']:.1f} tall"); draw(r["slender"], "#e8641b", lambda s: f"{s['width']:.1f} wide, {s['height']:.1f} tall")
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=10, loc="left"); plt.tight_layout(pad=0.3); plt.savefig(out, dpi=130); plt.close()
def strip_json(r):
    c = dict(r); c.pop("footprint", None)
    for k in ("thin", "strips", "slender", "accepted"): c[k] = [{a: b for a, b in s.items() if a != "shape"} for s in r.get(k, [])]
    return c

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "build/print"; tag = sys.argv[2] if len(sys.argv) > 2 else ""
    if src == "before": import printcards; src, tag = printcards.OLDDIR + "/print", "v24"
    pic = "build/printrules" + ("_" + tag if tag else ""); os.makedirs(pic, exist_ok=True); out = {}
    for p in PARTS:
        f = f"{src}/one135_{p}.stl"
        if not os.path.exists(f): continue
        r = audit(f)
        if not tag: name_them(p, r)
        out[p] = strip_json(r); picture(p, r, f"{pic}/{p}.png", f"{NAMES[p]}: red = thinner than {MIN_WALL} mm, orange = tall for its width, blue = narrow strip" + (", purple = thin, kept on purpose" if r.get("accepted") else ""))
        print(f"{NAMES[p]:15s} thin {len(r['thin']):2d}  tall-for-width {len(r['slender']):2d}  thin floors or roofs {len(r['skins']):2d}  strips {len(r['strips']):2d}  carries {r['carries']['above_mm']:.0f} mm on {r['carries']['width_mm']:.1f} mm (x{r['carries']['ratio']:.1f})  first layer: {r['first_layer']['pieces']} piece(s), {r['first_layer']['small_openings']} small opening(s)")
        for s in r["thin"]: print(f"      thin: {s['width']:.2f} mm wide, {s['length']:.1f} long, z {s['z0']} to {s['z1']}, at {s['at']}")
        for s in r["skins"]: print(f"      floor or roof {s['thick_mm']} mm thick: {s['area_mm2']} mm2 at {s['at']}, z {s['z0']}")
        for s in r["slender"]: print(f"      tall for its width: {s['width']:.2f} mm wide, {s['height']:.1f} tall, from z {s['from_z']}, footprint {s['footprint_mm2']} mm2, at {s['at']}")
        for s in r.get("accepted", []): print(f"      kept on purpose: {s['width']:.2f} mm wide, {s['length']:.1f} long, at {s['at']}: {s['what']}")
        for s in r["strips"]: print(f"      strip: {s['width']:.2f} mm wide, {s['length']:.1f} long, z {s['z0']} to {s['z1']}, at {s['at']}" + (f"  = {s['kind']}: {s['what']}" if "kind" in s else ""))
    json.dump(out, open("build/printrules" + ("_" + tag if tag else "") + ".json", "w"), indent=1)
