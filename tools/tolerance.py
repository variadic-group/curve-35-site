"""Tolerance audit: print every part 'fat' (all side walls grown by e, as an over-extruding printer does, plus elephant's foot on
the first layers) or 'thin' (under-extruding), and test every fit again.  Fat parts show what would bind; thin parts show what
would no longer hold.  Side walls only: FDM is accurate along the layer direction, which is why the shutter stack is built on whole layers."""
import sys, json, numpy as np, trimesh, manifold3d as m3
sys.path.insert(0, "tools"); from scadr import values
A = "build/asm/"; LB = json.load(open("build/layout.json"))["B"]; TH = LB["THETA"]; _v = values(["SLIDE", "XA", "XUP"]); SLIDE, XA, XUP = _v["SLIDE"], _v["XA"], _v["XUP"]
P_S = np.array(LB["P_S"]); WC = np.array(LB["c"]); HUBC = LB["HUBC"]
FV = values(["F_X0", "F_X1", "F_Z0", "H"])
def fingers():
    """the two latch fingers of the back, as boxes: they lie against the body's catches and bend out of the way, so they are left out of the fit tests"""
    b = m3.Manifold.cube((FV["F_X1"] + 2.0 - FV["F_X0"] + 1.5, 20.0, 12.0)).translate((FV["F_X0"] - 1.5, -12.0, FV["F_Z0"] - 0.75)); return b + b.mirror((0, 0, 1))
def _ang(f): v = far(load(f), P_S); return float(np.arctan2(v[1], v[0]))
def far(t, c):
    """unit vector (x, z) from a pivot to the point of a part farthest from it: its click tooth"""
    d = t.vertices[:, [0, 2]] - c; v = d[np.argmax((d ** 2).sum(1))]; return v / np.linalg.norm(v)
AXIS = dict(body=1, back=1, backN=1, front=1, frontN=1, blade=1, bladeN=1, wheel=1, roller=2, knob=2, spool=2, cassette=None)
BED_MIN = {"wheel", "back", "backN"}                                    # these print with their low side on the bed; the rest with their high side
def load(f): return trimesh.load(A + f + ".stl", process=True)
def grow(t, kind, e, ef):
    ax = AXIS[kind]
    if ax is None or (e == 0 and ef == 0): return t.copy()
    V = t.vertices.copy(); F = t.faces; N = t.face_normals.copy(); N[:, ax] = 0; ln = np.linalg.norm(N, axis=1); ok = ln > 0.35; Np = N[ok] / ln[ok][:, None]
    M = np.zeros((len(V), 3, 3)); b = np.zeros((len(V), 3)); outer = Np[:, :, None] * Np[:, None, :]
    for k in range(3): np.add.at(M, F[ok][:, k], outer); np.add.at(b, F[ok][:, k], Np)
    d = np.einsum("nij,nj->ni", np.linalg.pinv(M, rcond=1e-3, hermitian=True), b); ld = np.linalg.norm(d, axis=1); d[ld > 2.5] *= (2.5 / ld[ld > 2.5])[:, None]
    bed = V[:, ax].min() if kind in BED_MIN else V[:, ax].max(); near = np.abs(V[:, ax] - bed) < 0.1          # elephant's foot: the layer on the bed only
    V += d * e; V[near] += d[near] * ef
    return trimesh.Trimesh(V, F, process=False)
A_T0 = _ang("blade_PHI0.0"); S_T = float(np.sign(np.sin(_ang(f"blade_PHI{TH}") - A_T0)))            # where the blade's tooth is at mid-swing, and which way PHI turns it
def man(t): return m3.Manifold(m3.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
def hit(a, b):
    x = a ^ b; v = x.volume()
    if v < 0.003: return 0.0, None
    bb = x.bounding_box(); return round(v, 3), [round(float(c), 1) for c in bb[:3]] + [round(float(c), 1) for c in bb[3:]]
PH = [float(round(x, 3)) for x in np.linspace(-TH, TH, 23)]
def run(e, ef, label):
    G = {}
    def g(name, kind, shift=None):
        key = (name, tuple(shift) if shift else None)
        if key not in G:
            t = grow(load(name), kind, e, ef)
            if shift: t.apply_translation(shift)
            G[key] = man(t)
        return G[key]
    R = {}
    def chk(desc, a, b):
        v, where = hit(a, b); R[desc] = dict(mm3=v, where=where)
    front = g("front", "front"); body = g("body", "body"); back = g("back", "back")
    wh = m3.Manifold.batch_boolean([g(f"wheel_STOP{k}", "wheel") for k in range(3)], m3.OpType.Add)
    play = max(HUBC - 2 * e, 0.0)                                                                      # the blade can sit anywhere in a circle of this radius; its hub hole is drawn off-centre, so the circle's centre is HUBC toward the tooth
    def blades(names, kind, f):                                                                        # f: which way the blade is pushed inside its play (None = by its own spring, away from the tooth: the rest position)
        out = []
        for n in names:
            t0 = load(n); phi = float(n.split("PHI")[1]); ang = A_T0 + S_T * np.radians(phi); u = np.array([np.cos(ang), np.sin(ang)]); t = grow(t0, kind, e, ef)
            d = u * HUBC + (np.array(f, float) if f is not None else -u) * play; t.apply_translation([d[0], 0, d[1]]); out.append(man(t))
        return m3.Manifold.batch_boolean(out, m3.OpType.Add) - HUB_B                                    # (the hub itself is left out: its fit is the 'play' printed below)
    sw = [f"bladeN_BL_BUMP0.0_PHI{p}" for p in PH]; HUB_B = m3.Manifold.cylinder(40, 4.2, 4.2, 48).rotate((90, 0, 0)).translate((P_S[0], 50, P_S[1])); HUB_W = m3.Manifold.cylinder(40, 3.9, 3.9, 48).rotate((90, 0, 0)).translate((WC[0], 50, WC[1]))
    print(f"   hubs: play {HUBC - 2 * e:.2f} mm" + ("   <-- SEIZED" if HUBC - 2 * e < -0.01 else ""))
    for f, w in ((None, "at rest (held up by its own spring)"), ((0, -1), "hanging on its boss (as while it is pressed)"), ((-1, 0), "pushed left as far as it goes"), ((1, 0), "pushed right as far as it goes")):
        t = blades(sw if f is None or f[0] == 0 else sw[1:-1], "blade", f); chk(f"blade (whole swing, tooth removed) {w}", t, front); chk(f"blade {w} against the wheel", t, wh); chk(f"blade {w} against the body's face", t, body)
    for sgn, w in ((1, "one side"), (-1, "other side")):
        chk(f"blade at rest in its notch, {w}, tooth and all (as drawn: 0; fatter: the spring is bent by that much)", blades([f"blade_PHI{sgn * TH}"], "blade", None), front)
    rest = LB["REST_B"] + 4 * e; print(f"   blade click: at rest the tooth is pushed in {rest:.2f} mm (slack {max(-rest + LB['DV_B'] - 0.414 * LB['TIP_R'], 0):.2f} mm in its notch); pressed {LB['PRESSED_B']:.2f} mm; room behind the spring {LB['SLIT'] - 2 * e:.2f} mm" + ("   <-- NO HOLD AT REST" if rest < 0.15 else ""))
    R["blade click: pushed in at rest, mm / pressed, mm / room behind the spring, mm"] = dict(mm3=0.0, where=[round(rest, 2), LB["PRESSED_B"], round(LB["SLIT"] - 2 * e, 2)])
    whs = []
    for k in range(3):                                                                                 # the wheel sits where its spring puts it: 2 x the wall error nearer its click wall
        t0 = load(f"wheelN_STOP{k}_WH_BUMP0.0"); u = far(load(f"wheel_STOP{k}"), WC); t = grow(t0, "wheel", e, ef); t.apply_translation([u[0] * 2 * e, 0, u[1] * 2 * e]); whs.append(man(t))
    whN = m3.Manifold.batch_boolean(whs, m3.OpType.Add) - HUB_W
    chk("wheel (all positions, tooth removed, seated by its spring) in the front plate", whN, front); chk("wheel against body face", wh, body)
    need = LB["BUMP_W"] - LB["SCL_W"] + 4 * e; room = LB["SLIT_W"] - 2 * e; climb = LB["DV_W"] - 0.414 * LB["TIP_R"]
    R["wheel click: tooth pushed in at the top of the ramp, mm / room behind the spring, mm / what is left to climb, mm"] = dict(mm3=0.0, where=[round(need, 2), round(room, 2), round(min(climb, need), 2)])
    print(f"   wheel click: travel {need:.2f} mm, room {room:.2f} mm, climb {min(climb, need):.2f} mm, slack {max(climb - need, 0):.2f} mm" + ("   <-- NO ROOM" if need > room - 0.05 else ""))
    fz = [0, 0, 2 * e]                                                                                # the plate stands on the tips of its hooks: fat or thin moves it by 2 x the error
    chk("front plate home on the body (latch tooth removed)", g("frontN_TOOTH_H0.02", "frontN", fz), body)
    top = XUP + 0.3                                                                                   # v2.10: it goes on XUP or more above home (as high as the pockets let it), to the side; then across; then down
    for sx in (XA - 0.2 - max(2 * e, 0), 2.0, 1.0): chk(f"front plate set on {top} mm above home, {round(sx, 1)} mm to the side (going across)", g("frontN_TOOTH_H0.02", "frontN", [-sx, 0, top + 2 * e]), body)
    for s in [round(top * k / 4, 2) for k in (4, 3, 2, 1)]: chk(f"front plate sliding down, {s} mm above home", g("frontN_TOOTH_H0.02", "frontN", [0, 0, s + 2 * e]), body)
    chk("frame wheel in its fork", g("roller", "roller"), back); chk("frame wheel in the body's pocket and slot", g("roller", "roller"), body)
    for dy in (0.0, 3.0, 8.0): chk(f"frame wheel raised, {dy} mm out of the fork (going in / coming out)", g("roller_ROLL_UP2.5", "roller", [0, dy, 0]), back)
    FG = fingers()
    for dy in (1.0, 4.0, 10.0): chk(f"back + frame wheel (latch fingers left out) {dy} mm off the body", m3.Manifold.batch_boolean([g("backN_NUB_H0.02", "backN", [0, -dy, 0]) - FG.translate((0, -dy, 0)), g("roller", "roller", [0, -dy, 0])], m3.OpType.Add), body)
    kz = max(e, 0.0)                                                                            # the knobs' heads rest on the top of the body: a fat top lifts them
    if e > 0:                                                                                   # v2.14: lift them until the head really stands clear on the fat top (a little more than e: the head's own rim has grown too).  Before, they were lifted by e and what was left of the head in the top was counted as a bind
        for _dz in np.arange(kz, kz + 0.41, 0.05):
            if float((g("knob", "knob", [0, 0, float(_dz)]) ^ body).volume()) < 0.05: break
        kz = float(_dz); print(f"   the knobs ride {kz:.2f} mm up on this printer's thicker top wall"); R["knobs ride up on the top wall, mm"] = dict(mm3=0.0, where=[round(kz, 2)])
    for dy in (1.5, 3.0, 4.5, 6.5):                                                                      # the way in, millimetre by millimetre (up to v2.5 only the home position was looked at)
        chk(f"wind knob sliding in, {dy} mm from home", g("knob", "knob", [0, -dy, kz]), body); chk(f"spool sliding in, {dy} mm from home", g("spool", "spool", [0, -dy, kz]), body)
    chk("wind knob in the body", g("knob", "knob", [0, 0, kz]), body)
    chk("spool in its chamber", g("spool", "spool", [0, 0, kz]), body); chk("spool against the back's blocks", g("spool", "spool", [0, 0, kz]), back); chk("wind knob against the back's blocks", g("knob", "knob", [0, 0, kz]), back)
    chk("back on the body (latch fingers left out)", back - FG, body); print(f"   back latch: each finger is bent {max(2 * e, 0):.2f} mm at rest; play {max(-2 * e, 0):.2f} mm"); chk("cassette in its chamber (resting on the floor)", g("cassette", "cassette", [0, 0, max(e, 0) + 0.001]), body)
    chk("HOLD front plate pulled 0.6 mm off (want > 0)", g("frontN_TOOTH_H0.02", "frontN", [0, 0.6, 2 * e]), body); chk("HOLD front plate pushed 1.2 mm up (want > 0: the latch's tooth meets the bump)", g("front", "front", [0, 0, 1.2 + 2 * e]), body)
    chk("HOLD front plate pushed 3.0 mm up and pulled 2.6 mm off (want > 0: the side lips hold it)", g("frontN_TOOTH_H0.02", "frontN", [0, 2.6, 3.0 + 2 * e]), body)
    chk("HOLD front plate pushed 3.0 mm up, as far to the left as it goes, and pulled 2.6 mm off (want > 0)", g("frontN_TOOTH_H0.02", "frontN", [-max(0.7 - 2 * e, 0.0), 2.6, 3.0 + 2 * e]), body)
    chk("HOLD frame wheel pulled 1.6 mm out of its fork (want > 0)", g("roller", "roller", [0, 1.6, 0]), back)
    chk("HOLD frame wheel pushed 0.9 mm up in the closed camera (want > 0)", g("roller", "roller", [0, 0, 0.9]), body)
    chk("HOLD back pulled 0.6 mm off (want > 0)", g("back", "back", [0, -0.6, 0]), body)
    print(f"--- {label}")
    for k, v in R.items():
        if v["mm3"] or k.startswith("HOLD"): print(f"   {k}: {v['mm3']} mm3" + (f"  box {v['where']}" if v["where"] and not k.startswith("HOLD") else ""))
    return R
if __name__ == "__main__":
    out = {}; todo = sys.argv[1:] or ["0", "1", "2", "3", "4", "5"]
    P = [(0.0, 0.0, "as drawn"), (0.10, 0.15, "typical printer: walls +0.10 mm, elephant's foot 0.15"), (0.15, 0.20, "fat printer: walls +0.15 mm, elephant's foot 0.20"),
         (0.25, 0.40, "far too fat (the edge of what v2.7 aims at): walls +0.25 mm, elephant's foot 0.40"), (-0.08, 0.0, "thin printer: walls -0.08 mm"), (-0.15, 0.0, "far too thin (the edge of what v2.7 aims at): walls -0.15 mm")]
    try: out = json.load(open("build/tolerance.json"))
    except Exception: out = {}
    out = {k: v for k, v in out.items() if k in [q[2] for q in P]}
    for i in todo: out[P[int(i)][2]] = run(*P[int(i)])
    json.dump(out, open("build/tolerance.json", "w"), indent=1)
