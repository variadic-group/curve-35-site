"""ONE-135 kinematics shared by tools/motion.py (the measurements) and tools/motionfilm.py (the pictures): where each part is at each moment
of each move, as a 4x4 matrix applied to the SAME exported meshes (build/asm/*.stl), and a film strip with its perforations built along the model's own film path.
Nothing here keeps a second copy of a dimension: every number is read from the model (scadr.values)."""
import sys, os, json, numpy as np, trimesh, manifold3d as m3
sys.path.insert(0, "tools"); from scadr import values
SCAD = "scad/one135.scad"; A = "build/asm/"; VJ = "build/motion_values.json"
NAMES = ["P_S", "WHEEL_C", "WPOS", "THETA_S", "ROLLER", "SPOOL", "CASS", "R_ROLL", "FILM_T", "FILM_W", "CORE_R", "ROLL_FULL", "RCH_S", "GUIDE", "R_G", "LIP_TIP", "DELTA_L", "A_L", "A_R", "RF", "CF", "WH_Z", "TOOTH_Z", "TOOTH", "H",
         "SLIDE", "XA", "XUP", "ROLL_LIFT", "Y_RIM", "Y_FRONT", "D_C", "N_C", "TAKE_HEAD", "WIND_HEAD", "DIAL_R", "DIAL_Z", "HEAD_H", "ZC0", "ZC1", "FIT", "SHAFT_R", "SHAFT_CL", "Y_SEAT", "Y_CVF", "LENS_SEAT", "FORK_GAP", "FORK_R", "FORK_Z0", "KN_R", "P1_T", "FZ1"]
if not os.path.exists(VJ) or os.path.getmtime(VJ) < os.path.getmtime(SCAD): json.dump(values(NAMES), open(VJ, "w"))
V = json.load(open(VJ)); TH = V["THETA_S"]; XE = V["XA"] - 0.2; LIFT = 2.5; PITCH = 4.75
PERF_L, PERF_W, PERF_E, PERF_R = 1.981, 2.794, 2.01, 0.5        # KS perforation: along the film, across it, its distance from the film's edge, its corner radius (ISO 491)
RP = V["R_ROLL"] + V["FILM_T"] / 2                                 # the radius the film's middle rides at on the frame wheel: 8 pitches round it
STL = dict(body="body", back="back", backN="backN_NUB_H0.02", front="front", frontN="frontN_TOOTH_H0.02", roller="roller", knob="knob", spool="spool", lens="lens", cassette="cassette", film="film", film_empty="film_empty",
           blade0="bladeN_BL_BUMP0.0_PHI0.0", bladeB="blade_PHI0.0", wheel0="wheelN_STOP0_WH_BUMP0.0", wheelB="wheel_STOP0")
def path(n): return A + STL.get(n, n) + ".stl"
def tomesh(t): return m3.Manifold(m3.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
_T = {}; _M = {}
def tri(n):
    if n not in _T: _T[n] = trimesh.load(path(n), process=True)
    return _T[n]
def man(n):
    if n not in _M: _M[n] = tomesh(tri(n))
    return _M[n]
# ---------------------------------------------------------------- matrices
def Tr(v): M = np.eye(4); M[:3, 3] = v; return M
def RY(c, deg):                                                     # the model's rot_xz(c, deg): about the lens's direction, through (x, z) = c
    a = np.radians(-deg); R = np.eye(4); R[0, 0] = np.cos(a); R[0, 2] = np.sin(a); R[2, 0] = -np.sin(a); R[2, 2] = np.cos(a); return Tr([c[0], 0, c[1]]) @ R @ Tr([-c[0], 0, -c[1]])
def RZ(c, deg):
    a = np.radians(deg); R = np.eye(4); R[0, 0] = np.cos(a); R[0, 1] = -np.sin(a); R[1, 0] = np.sin(a); R[1, 1] = np.cos(a); return Tr([c[0], c[1], 0]) @ R @ Tr([-c[0], -c[1], 0])
def put(n, M=None): return man(n) if M is None else man(n).transform(np.asarray(M)[:3, :])
blade = lambda phi: RY(V["P_S"], phi)                                # applied to blade0 (drawn open)
wheel = lambda ang: RY(V["WHEEL_C"], -ang)                           # applied to wheel0 (drawn at the pinhole stop): ang = 0 .. WPOS[2]
# ---------------------------------------------------------------- the film
def pol(c, r, a): return [c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a))]
def arcp(a, r): return [r * np.sin(np.radians(a)), V["CF"][1] - r * np.cos(np.radians(a))]
def ctan(c1, r1, c2, r2):
    d = np.array(c2) - np.array(c1); D = np.linalg.norm(d); th = np.degrees(np.arctan2(d[1], d[0])); b = np.degrees(np.arccos((r1 + r2) / D)); u = np.array([np.cos(np.radians(th + b)), np.sin(np.radians(th + b))])
    return np.array(c1) + r1 * u, np.array(c2) - r2 * u, th + b
def film_pts(roll, t=None, step=1.0):
    """The film's middle line as film_geom() draws it: cassette lip -> guide -> drum -> frame wheel -> take-up roll.  Returns the points and, for each, which stretch it belongs to."""
    t = V["FILM_T"] if t is None else t; CF, GU, RO, SP = V["CF"], V["GUIDE"], V["ROLLER"], V["SPOOL"]; DL = V["DELTA_L"]; rp = V["R_ROLL"] + t / 2
    c0, c1, ang = ctan(RO, rp, SP, roll); a0 = np.degrees(np.arctan2(CF[1] - GU[1], CF[0] - GU[0])); a1 = np.degrees(np.arctan2(CF[1] - RO[1], CF[0] - RO[0]))
    P = [(np.array(V["LIP_TIP"]) + 13 * np.array(V["D_C"])).tolist(), V["LIP_TIP"]]; S = ["lip", "lip"]
    for a in np.arange(90 + DL, a0 - 1e-6, -6.0): P.append(pol(GU, V["R_G"] + 0.22 + t / 2, a)); S.append("guide")
    for a in np.arange(-V["A_L"], V["A_R"] + 1e-6, step): P.append(arcp(a, V["RF"] + 0.02 + t / 2)); S.append("drum")
    for a in np.append(np.arange(a1, ang, -step), ang): P.append(pol(RO, rp, a)); S.append("wheel")
    P.append(c1.tolist()); S.append("run")
    return np.array(P), S, dict(wrap_from=a1, wrap_to=ang, wrap_deg=a1 - ang, land=c1.tolist())
def film_pts_closing(d, roll, t=None, step=1.0):
    """The film while the back is still d mm from home.  The frame wheel rides on the back, so it is d mm short of its place: the film leaves the rails where a straight line can reach
    the wheel (the tangent to both), lies round the wheel's front and runs on to the take-up roll.  Far enough out the wheel does not reach the film at all: it runs straight from rails to roll."""
    t = V["FILM_T"] if t is None else t; CF, GU, SP = V["CF"], V["GUIDE"], V["SPOOL"]; DL = V["DELTA_L"]; rp = V["R_ROLL"] + t / 2; RO = [V["ROLLER"][0], V["ROLLER"][1] - d]; rf = V["RF"] + 0.02 + t / 2
    a0 = np.degrees(np.arctan2(CF[1] - GU[1], CF[0] - GU[0])); P = [(np.array(V["LIP_TIP"]) + 13 * np.array(V["D_C"])).tolist(), V["LIP_TIP"]]; S = ["lip", "lip"]
    for a in np.arange(90 + DL, a0 - 1e-6, -6.0): P.append(pol(GU, V["R_G"] + 0.22 + t / 2, a)); S.append("guide")
    def leave(c2, r2, cross):                                         # where a line tangent to the drum and to the circle (c2, r2) leaves the drum: (film angle on the drum, direction angle of the contact on c2)
        dv = np.array(c2) - np.array(CF); D = np.linalg.norm(dv); th = np.degrees(np.arctan2(dv[1], dv[0])); b = np.degrees(np.arccos(np.clip(((rf + r2) if cross else (rf - r2)) / D, -1, 1))); ua = th - b
        return ua + 90.0, (ua + 180.0) if cross else ua               # a point of the drum in the direction ua from its middle is at film angle ua + 90
    aw, w_from = leave(RO, rp, True); c0, c1, w_to = ctan(RO, rp, SP, roll); wrap = w_from - w_to
    if wrap <= 0.5:                                                   # the wheel does not reach the film: straight from the rails to the roll (the film lies on the far side of the roll, as when it was tucked in)
        al, ua = leave(SP, roll, True)
        for a in np.append(np.arange(-V["A_L"], al, step), al): P.append(arcp(a, rf)); S.append("drum")
        P.append(pol(SP, roll, ua)); S.append("run"); return np.array(P), S, dict(wrap_from=0.0, wrap_to=0.0, wrap_deg=0.0, land=P[-1])
    for a in np.append(np.arange(-V["A_L"], aw, step), aw): P.append(arcp(a, rf)); S.append("drum")
    for a in np.append(np.arange(w_from, w_to, -step), w_to): P.append(pol(RO, rp, a)); S.append("wheel")
    P.append(c1.tolist()); S.append("run")
    return np.array(P), S, dict(wrap_from=w_from, wrap_to=w_to, wrap_deg=wrap, land=c1.tolist())
def _extr(poly, z0, z1):
    q = np.asarray(poly, float); area = 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    return m3.Manifold.extrude(m3.CrossSection([q if area > 0 else q[::-1]]), z1 - z0).translate([0, 0, z0])
def _strip(P, t, z0, z1):
    from shapely.geometry import LineString
    g = LineString(P).buffer(t / 2, cap_style=2, join_style=1, resolution=3); return _extr(np.array(g.exterior.coords)[:-1], z0, z1)
_cut = None
def _cutter():
    global _cut
    if _cut is None:
        from shapely.geometry import box
        g = box(-PERF_L / 2 + PERF_R, -PERF_W / 2 + PERF_R, PERF_L / 2 - PERF_R, PERF_W / 2 - PERF_R).buffer(PERF_R, resolution=4)
        _cut = _extr(np.array(g.exterior.coords)[:-1], -1.5, 1.5).rotate([90, 0, 0])               # local x along the film, local y across it -> world z; cut through along the film's normal
    return _cut
def film(roll, adv=None, t=None, near=None, shrink=0.0, step=1.0, with_roll=True, path=None, u0=None):
    """The film as a solid.  adv = None: plain (as the model draws it).  adv = a number: with both rows of perforations, moved adv mm toward the take-up.
    The perforations are placed so that at adv = 0 one of them is centred on the frame wheel at the middle of the wrap.  near = (centre, radius): only that part of the strip.
    shrink: each perforation drawn this much smaller all round (a way to ask how much room the teeth have)."""
    t = V["FILM_T"] if t is None else t; W = V["FILM_W"]; P, S, info = film_pts(roll, t, step) if path is None else path; info = dict(info); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); u = np.r_[0, np.cumsum(seg)]
    keep = np.ones(len(P), bool) if near is None else np.hypot(P[:, 0] - near[0][0], P[:, 1] - near[0][1]) < near[1]
    i0, i1 = np.nonzero(keep)[0][[0, -1]]; body = _strip(P[i0:i1 + 1], t, -W / 2, W / 2)
    if with_roll and near is None: body = body + (_extr(np.array([pol(V["SPOOL"], roll, a) for a in np.arange(0, 360, 4)]), -W / 2, W / 2) - _extr(np.array([pol(V["SPOOL"], V["CORE_R"] + 0.05, a) for a in np.arange(0, 360, 6)]), -W / 2 - 1, W / 2 + 1))
    info["length"] = float(u[-1]); iw = [k for k, s in enumerate(S) if s == "wheel"] or [len(S) - 2, len(S) - 2]; info["u_mid"] = float((u[iw[0]] + u[iw[-1]]) / 2); info["u_wheel"] = [float(u[iw[0]]), float(u[iw[-1]])]
    if adv is None: return body, info
    if u0 is not None: info["u_mid"] = float(u0)                       # the perforations are fixed to the film: one of them is u0 + adv from the cassette's lip
    cuts = []; k0 = int(np.floor((u[i0] - info["u_mid"] - adv) / PITCH)) - 1; zc = W / 2 - PERF_E - PERF_W / 2; sc = [(PERF_L - 2 * shrink) / PERF_L, 1, (PERF_W - 2 * shrink) / PERF_W]; centres = []
    for k in range(k0, k0 + int((u[i1] - u[i0]) / PITCH) + 4):
        uu = info["u_mid"] + adv + k * PITCH
        if uu < u[i0] + 1.2 or uu > u[i1] - 1.2: continue
        j = min(np.searchsorted(u, uu) - 1, len(seg) - 1); f = (uu - u[j]) / seg[j]; p = P[j] + f * (P[j + 1] - P[j]); d = P[j + 1] - P[j]; ang = np.degrees(np.arctan2(d[1], d[0])); centres.append([float(p[0]), float(p[1]), float(ang)])
        c = _cutter().scale(sc) if shrink else _cutter()
        for z in (zc, -zc): cuts.append(c.rotate([0, 0, ang]).translate([p[0], p[1], z]))
    info["perfs"] = centres
    return (body - m3.Manifold.batch_boolean(cuts, m3.OpType.Add)) if cuts else body, info
def roll_radius(length_on, t=None): t = V["FILM_T"] if t is None else t; return float(np.sqrt((V["CORE_R"] + 0.3) ** 2 + t * length_on / np.pi))      # tightly wound: area of the roll's end = thickness x length
def wheel_turn(adv): return -np.degrees(adv / RP)                    # how far the film turns the frame wheel (degrees, seen from above) when it moves adv mm toward the take-up
def wheel_phase(info): return info["wrap_from"] - (info["u_mid"] - info["u_wheel"][0]) / RP * 180 / np.pi      # the direction, from the wheel's middle, of the perforation centred on the wrap at adv = 0: a tooth is drawn there
def save(m, f):
    me = m.to_mesh(); trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False).export(f)
