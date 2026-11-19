"""Print simulation.  Each part is sliced (PrusaSlicer); the tool path of a layer is turned back into plastic (every bead drawn
at its real width); then printer error is added: all side walls grown or shrunk by e, and elephant's foot on the layer on the bed.
The rebuilt parts are measured where the camera depends on them (how far each click tooth is pushed in, whether the slits stay
open, how big the aperture holes come out) and the results go through the finite-element
numbers of tools/fea_cases.py.  Writes build/printsim.json and build/printsim.png."""
import sys, json, numpy as np, trimesh, shapely, re
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
sys.path.insert(0, "tools"); from slicecheck import slice_part, parse, offset, LH
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LY = json.load(open("build/layout.json")); B = LY["B"]; P = np.array(B["P_S"]); C = np.array(B["c"]); TH = B["THETA"]; H = B["H"]
FLIP = dict(front=1, blade=1, body=1, wheel=-1, back=-1)       # print (X, Y) -> world (x, z): z = FLIP * Y
PRINTERS = [("thin printer", -0.08, 0.00), ("exact printer", 0.0, 0.05), ("good printer", 0.05, 0.10), ("typical printer", 0.10, 0.15), ("fattest printer", 0.15, 0.20)]   # name, wall error e, elephant's foot
_cache = {}
def gcode(n):
    if n not in _cache:
        layers, _ = parse(slice_part(n, True)); m = trimesh.load(f"build/print/one135_{n}.stl", process=True); _cache[n] = (layers, m, offset(layers, m))
    return _cache[n]
def to_world(n, g): return shapely.affinity.scale(g, 1, FLIP[n], origin=(0, 0))
def printed(n, z, e=0.0):
    """the plastic of the layer whose top is at z, in world (x, z) coordinates, with every side wall moved out by e"""
    layers, m, off = gcode(n); seg = np.array(layers[min(layers, key=lambda q: abs(q - z))]); w = np.clip(seg[:, 4], 0.12, 0.95) + LH * (1 - np.pi / 4)
    beads = [LineString([(a - off[0], b - off[1]), (c - off[0], d - off[1])]).buffer(ww / 2, 6) for (a, b, c, d, _), ww in zip(seg, w)]
    u = unary_union(beads).buffer(0.03).buffer(-0.03)             # beads laid side by side fuse
    return to_world(n, u.buffer(e, 8) if e else u)
def cad(n, z):
    layers, m, off = gcode(n); sec = m.section(plane_origin=[0, 0, z - LH / 2], plane_normal=[0, 0, 1]); p2, T = sec.to_2D() if hasattr(sec, "to_2D") else sec.to_planar()
    return to_world(n, unary_union([shapely.affinity.affine_transform(p, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]) for p in p2.polygons_full]))
def ray(poly, c, ang, r0=0.0, r1=60.0):
    """the stretches of a ray from c that lie inside poly, as (start, end) distances"""
    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))]); I = poly.intersection(LineString([c + r0 * d, c + r1 * d])); out = []
    for g in getattr(I, "geoms", [I]):
        if g.geom_type == "LineString" and g.length > 1e-4:
            a, b = (np.hypot(*(np.array(q) - c)) for q in (g.coords[0], g.coords[-1])); out.append((min(a, b), max(a, b)))
    return sorted(out)
def click(part, wall, c, R, t, a_tip, arc, a_flat, a_notch):
    """part: rebuilt blade or wheel (tooth at a_tip); wall: rebuilt plate at the same level"""
    reach = max(ray(part, c, a)[-1][1] for a in np.arange(a_tip - 2.5, a_tip + 2.51, 0.1))                 # top of the tooth
    slit = [(a, min(q[0] for q in s if q[0] > R + 0.5) - max(q[1] for q in s if q[1] < R + 0.5)) for a in np.arange(a_tip - arc + 5, a_tip - 0.5, 0.5) for s in [ray(part, c, a)] if any(q[0] > R + 0.5 for q in s) and any(R - 3 < q[1] < R + 0.5 for q in s)]   # the gap that holds radius R + 0.5, wherever the rim is under the spring
    hole = float(np.mean([ray(part, c, a)[0][0] for a in np.arange(a_tip - 20, a_tip + 21, 5)]))           # hole in the hub, on the tooth's side
    boss = float(np.mean([max(q[1] for q in ray(wall, c, a) if q[0] < 1.5) for a in np.arange(a_tip - 20, a_tip + 21, 5)]))   # v2.18: the boss out to its skin: some line widths leave a hair-wide void at its core, and the first stretch alone then read 0.9 mm short
    face = min(s[0] for a in np.arange(a_flat - 1.5, a_flat + 1.51, 0.25) for s in ray(wall, c, a, R + 1.5) if True)
    floor = max(min(s[0] for s in ray(wall, c, a, R + 1.5)) for a in np.arange(a_notch - 0.3, a_notch + 0.31, 0.1))
    push = reach - face - (hole - boss); u = lambda a: (a - a_tip + arc) / arc                    # a bent beam moves (3u^2 - u^3)/2 of its tip's travel at the fraction u of its length
    return dict(tooth_top=reach, wall_face=face, notch_floor=floor, hub_room=hole - boss, pushed_in=push, slit_min=min(s for _, s in slit), slit_at_tip=float(np.median([s for _, s in slit[-4:]])),
                room_left_behind_spring=min(s - max(push, 0) * (3 * u(a) ** 2 - u(a) ** 3) / 2 for a, s in slit),
                room_over_tooth_in_notch=floor - reach + (hole - boss))
if __name__ == "__main__":
    out = {}; F = json.load(open("build/fea.json"))
    def per_mm(key):
        k, r = [(k, v) for k, v in F.items() if k.startswith(key) and "as drawn" in k][0]; d = float(re.search(r"pushed in ([0-9.]+) mm", k).group(1)); return r["force_N"] / d, r["peak_strain_pct"] / d   # v2.18: the travel that case was run at (it was a fixed 0.5 mm, from before the springs were preloaded: strain and force read twice too high)
    import geom; RF = geom.lever(B, B["THETA"])                                                            # lever arm of the finger on the raised side of the rocker, where the press starts
    print("how far the click teeth are pushed in, slits and click force, rebuilt from the sliced tool paths")
    for name, e, ef in PRINTERS:
        bl = printed("blade", 0.8, e); fr = printed("front", 3.2, e); wh = printed("wheel", 0.8, e); fw = printed("front", 4.4, e)
        b = click(bl, fr, P, B["R_OUT"], B["BL_T"], B["DB_A"], B["BL_ARC"], B["DB_A"] + TH / 2, B["DB_A"] + TH)
        w = click(wh, fw, C, B["WHEEL_R"], B["WH_T"], B["WD_A0"], B["WH_ARC"], B["WD_A0"] - B["WPOS"][1] / 2, B["WD_A0"])
        for d, key, lever in ((b, "blade click spring", (B["R_OUT"] + B["SLIT"] + B["BL_T"] + 0.4) / RF), (w, "wheel click spring", (B["WHEEL_R"] + B["SLIT"] + B["WH_T"] + 0.4) / B["H_RHO"])):
            k, s = per_mm(key); x = max(d["pushed_in"], 0); d.update(spring_force_N=k * x, strain_pct=s * x, click_at_finger_N=k * x * (1 + 0.35) / (1 - 0.35) * lever, jams=bool(d["room_left_behind_spring"] <= 0))
        holes = {}
        for i, (lab, zl) in enumerate((("P", 1.0), ("S", 1.0), ("C", 1.0))):
            hc = C + B["R_HOLE"] * np.array([np.cos(np.radians(B["A_AX"] + B["WPOS"][i])), np.sin(np.radians(B["A_AX"] + B["WPOS"][i]))]); lay = printed("wheel", zl, e)
            holes[lab] = 0.0 if lay.contains(Point(hc)) else round(2 * lay.boundary.distance(Point(hc)), 2)
        out[name] = dict(wall_error=e, elephants_foot=ef, blade=b, wheel=w, aperture_holes_mm=holes)
        print(f"  {name:16s} walls {e:+.2f}: BLADE tooth pushed in {b['pushed_in']:.2f} mm, room left behind the spring {b['room_left_behind_spring']:.2f}, strain {b['strain_pct']:.2f} % at rest, {b['click_at_finger_N']:.2f} N at the finger to start it up its ramp (the click itself: tools/exposure.py)"
              f" | WHEEL {w['pushed_in']:.2f} mm, room {w['room_left_behind_spring']:.2f}, strain {w['strain_pct']:.2f} %, click {w['click_at_finger_N']:.2f} N | holes P {holes['P']} S {holes['S']} C {holes['C']} mm")
    # ---- latches (the finger is measured between its nub and its root; the nub against the finger beside it)
    for name, e, ef in PRINTERS:
        bk = printed("back", 1.0, e); fr = printed("front", 1.0, e); o = out[name]
        col = lambda x: ray(bk, np.array([x, H + 3.0]), -90, 0, 14)
        def fin(x):                                                                 # v2.14: the finger is the bar about 1.2 mm thick that starts about 5.5 mm down this line (the top band and the horn lie above it); the old readout took whatever came first
            sg = col(x); k = [i for i, q in enumerate(sg) if 4.8 < q[0] < 6.4 and 0.6 < q[1] - q[0] < 1.8]; return (sg, k[0]) if k else (sg, None)
        fs = [fin(x) for x in (-12, 2, 12)]; fs = [(sg, k) for sg, k in fs if k is not None and k + 1 < len(sg)]
        nub = [fin(-12.0)[0][fin(-12.0)[1]][0] - min(q[0] for q in col(x) if 2.5 < q[0] < 5.3) for x in np.arange(-17.5, -16.0, 0.2) if any(2.5 < q[0] < 5.3 for q in col(x))] if fin(-12.0)[1] is not None else []
        o["back_latch"] = dict(finger_thickness=round(float(np.mean([sg[k][1] - sg[k][0] for sg, k in fs])), 2), slit=round(float(np.mean([sg[k + 1][0] - sg[k][1] for sg, k in fs])), 2), nub_height=round(float(np.mean(nub)), 2) if nub else None)
        colf = lambda z: ray(fr, np.array([27.0 - 2.5, z]), 0, 0, 10)                         # v2.14: the leaf has stood on the plate's right side since v2.10 (x 27.0 to 31.6, root at z -19.1); this line still looked for it at the top edge
        sg = [s for z in (-13, -9, -5) for s in [colf(z)] if len(s) >= 2]
        o["plate_latch"] = dict(tongue_thickness=round(float(np.mean([s[1][1] - s[1][0] for s in sg])), 2) if sg else None, slit=round(float(np.mean([s[1][0] - s[0][1] for s in sg])), 2) if sg else None, measured="the leaf's width and the slit beside it, in the plate's plane")
        print(f"  {name:16s} back latch: finger {o['back_latch']['finger_thickness']} mm, slit {o['back_latch']['slit']} mm, nub {o['back_latch']['nub_height']} mm | plate latch: tongue {o['plate_latch']['tongue_thickness']}, slit {o['plate_latch']['slit']} mm")
    json.dump(out, open("build/printsim.json", "w"), indent=1)
    # ---- picture: the typical printer
    name, e, ef = PRINTERS[3]; rot = lambda g, a, c: shapely.affinity.rotate(g, a, origin=tuple(c))
    def draw(ax, g, col, alpha=0.75):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type != "Polygon": continue
            ax.fill(*q.exterior.xy, color=col, alpha=alpha, lw=0)
            for h in q.interiors: ax.fill(*h.xy, color="w", lw=0)
    def line(ax, g, col="k", lw=0.5):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type != "Polygon": continue
            ax.plot(*q.exterior.xy, color=col, lw=lw)
            for h in q.interiors: ax.plot(*h.xy, color=col, lw=lw)
    fig, ax = plt.subplots(2, 4, figsize=(23, 12.6)); plt.rcParams['axes.titlesize'] = 21
    fr = printed("front", 3.2, e); bl = printed("blade", 0.8, e); frc = cad("front", 3.2); blc = cad("blade", 0.8)
    tip = P + (B["R_OUT"] + 3.6) * np.array([np.cos(np.radians(B["DB_A"] + TH)), np.sin(np.radians(B["DB_A"] + TH))])
    for a_, ctr, half, ttl in ((ax[0, 0], (-2, 2), 33, "front plate and blade"), (ax[0, 1], tip, 5.5, "the blade's tooth in its notch")):
        draw(a_, fr, "#f0a060"); draw(a_, rot(bl, TH, P), "#30a0a0"); line(a_, frc); line(a_, rot(blc, TH, P)); a_.set_xlim(ctr[0] - half, ctr[0] + half); a_.set_ylim(ctr[1] - half, ctr[1] + half); a_.set_title(ttl)
    a_ = ax[0, 2]; rt = P + (B["R_OUT"] + 1.0) * np.array([np.cos(np.radians(B["DB_A"] - B["BL_ARC"])), np.sin(np.radians(B["DB_A"] - B["BL_ARC"]))])
    draw(a_, bl, "#30a0a0"); line(a_, blc); a_.set_xlim(rt[0] - 5.5, rt[0] + 5.5); a_.set_ylim(rt[1] - 5.5, rt[1] + 5.5); a_.set_title("where the blade's spring starts")
    a_ = ax[0, 3]; fw = printed("front", 4.4, e); wh = printed("wheel", 0.8, e); draw(a_, fw, "#f0a060"); draw(a_, wh, "#e0c040"); line(a_, cad("front", 4.4)); line(a_, cad("wheel", 0.8))
    a_.set_xlim(C[0] - 23, C[0] + 19); a_.set_ylim(C[1] - 19, C[1] + 23); a_.set_title("front plate and aperture wheel")
    a_ = ax[1, 0]; hc = [C + B["R_HOLE"] * np.array([np.cos(np.radians(B["A_AX"] + w_)), np.sin(np.radians(B["A_AX"] + w_))]) for w_ in B["WPOS"]]
    draw(a_, printed("wheel", 0.8, e), "#e0c040"); line(a_, cad("wheel", 0.8)); a_.set_xlim(min(h[0] for h in hc) - 4, max(h[0] for h in hc) + 4); a_.set_ylim(min(h[1] for h in hc) - 4, max(h[1] for h in hc) + 4)
    a_.set_title("holes: P %.2f, S %.2f, C %.2f mm" % tuple(out[name]["aperture_holes_mm"][k] for k in "PSC"))
    a_ = ax[1, 1]; draw(a_, printed("back", 0.2, e + ef), "#80b0e0"); line(a_, cad("back", 0.2)); a_.set_xlim(-56, -8); a_.set_ylim(-18, 30); a_.set_title("back, first layer (elephant's foot %.2f)" % ef)
    a_ = ax[1, 2]; draw(a_, printed("back", 1.0, e), "#80b0e0"); line(a_, cad("back", 1.0)); a_.set_xlim(-26, 6); a_.set_ylim(8, 32); a_.set_title("back: latch finger, nub and pad")
    a_ = ax[1, 3]; draw(a_, printed("front", 0.2, e + ef), "#f0a060"); line(a_, cad("front", 0.2)); a_.set_xlim(-31, 8); a_.set_ylim(-27.5, 11.5); a_.set_title("front plate, first layer")
    for a_ in ax.ravel(): a_.set_aspect("equal"); a_.set_xticks([]); a_.set_yticks([])
    fig.suptitle("Print simulation, %s (walls %+.2f mm): colour = plastic rebuilt from the sliced tool path, black line = the model" % (name, e), fontsize=25)
    plt.tight_layout(); plt.savefig("build/printsim.png", dpi=70)
