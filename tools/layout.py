"""ONE-135 v2 layout solver: (A) film path in plan view, (B) blade pivot / aperture wheel / handle arc.
Writes build/layout.json (numbers pasted into scad/one135.scad) and build/layout.png."""
import numpy as np, json
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D2R = np.pi / 180
def pol(c, r, a): a = a * D2R; return np.array([c[0] + r * np.cos(a), c[1] + r * np.sin(a)])

# ------------------------------------------------------------------ (A) film path, plan view (X right, Y to subject)
CF = np.array([0.0, 32.0]); RF = 32.0; FILM_T = 0.13
Y_FRONT = 25.47                      # body front face (flat: the body prints on it)
FRONT_WALL = 2.2
GATE_A = np.degrees(18.0 / RF)
def arc(a, r=RF): return CF + r * np.array([np.sin(a * D2R), -np.cos(a * D2R)])

# left: fixed guide on the back (door), then the cassette lip
R_G = 3.0; GAP = 0.35                # guide / roller surface sits 0.35 behind the drum (film 0.13 + 0.22 free)
CASS_R = 12.5; LIP_X, LIP_Y, LIP_T = 13.0, 11.3, 3.0      # lip tip 13.0 along the exit direction; slot mid-plane 11.3 behind the centre
def left(a_t, delta, L):
    """solved in the mirrored frame (x > 0), returns guide centre, film leave point, lip tip, cassette centre"""
    g = arc(a_t, RF + GAP + R_G)
    P = g + (R_G + FILM_T / 2) * np.array([np.sin(delta * D2R), np.cos(delta * D2R)])
    d = np.array([np.cos(delta * D2R), -np.sin(delta * D2R)])
    T = P + L * d
    n = np.array([np.sin(delta * D2R), np.cos(delta * D2R)])       # emulsion side (toward the lens)
    C = T + LIP_X * d + LIP_Y * n
    return g, P, T, C
best = None
for a_t in np.arange(41.0, 46.01, 0.5):
    for delta in np.arange(20.0, 50.01, 0.5):
        for L in (4.0, 5.0):
            g, P, T, C = left(a_t, delta, L)
            if C[1] + CASS_R + 0.6 + FRONT_WALL > Y_FRONT: continue          # shell must sit behind the front wall
            if C[1] - CASS_R < -3.0: continue                                # and not push the back out
            # the lip slab must clear the drum (emulsion side) by 0.6
            lip = LineString([T, T + LIP_X * np.array([np.cos(delta * D2R), -np.sin(delta * D2R)])]).buffer(LIP_T / 2)
            if lip.distance(Point(*CF).buffer(RF, 256)) < 0.6: continue
            if best is None or C[0] < best[0]: best = (C[0], a_t, delta, L)
_, A_L, DELTA_L, L_LIP = best
gL, PL, TL, CL = left(A_L, DELTA_L, L_LIP)
Y_RIM = None   # set once the roller is placed

# right: sprocket roller (8 teeth, film wraps it) then the take-up spool
SPR_PITCH = 4.75 * 8 / (2 * np.pi); R_ROLL = SPR_PITCH - FILM_T / 2; TOOTH = 1.2
A_R = 46.0
CR = arc(A_R, RF + GAP + R_ROLL)
Y_RIM = float(np.floor(min(CL[1] - CASS_R - 0.45, CR[1] - R_ROLL - TOOTH - 0.6) * 10) / 10)     # door inner face / body rim
# take-up: a standard 135 cassette spool (salvaged or printed): 22.5 mm flanges, 11.2 mm core
CORE_R = 5.6; FLANGE_R = 11.25; RCH_S = 12.0; ROLL_FULL = float(np.sqrt(CORE_R ** 2 + 1650 * 0.135 / np.pi))    # 36 exposures
YS = float(np.round(Y_RIM + 0.45 + FLANGE_R, 1))        # the door backs the flanges, as it backs the cassette
XS = CR[0] + np.sqrt((R_ROLL + TOOTH + ROLL_FULL + 0.9) ** 2 - (YS - CR[1]) ** 2)
S = np.array([float(np.ceil(XS * 10) / 10), YS])
def cross_tangent(c1, r1, c2, r2):
    """line from circle 1 (wrapped on its front) to circle 2 (wrapped on its back): returns the two points"""
    d = c2 - c1; D = np.hypot(*d); th = np.arctan2(d[1], d[0]); b = np.arccos((r1 + r2) / D)
    u1 = np.array([np.cos(th + b), np.sin(th + b)]); return c1 + r1 * u1, c2 - r2 * u1
def wrap_right(rho):
    p1, p2 = cross_tangent(CR, R_ROLL, S, rho)
    d = p2 - p1; return p1, p2, float(np.degrees(np.arctan2(-d[1], d[0])))
A = dict(A_L=float(A_L), DELTA_L=float(DELTA_L), L_LIP=float(L_LIP), guide=gL.tolist(), lip_tip=TL.tolist(), cass=CL.tolist(), Y_RIM=Y_RIM,
         A_R=A_R, roller=CR.tolist(), R_ROLL=float(R_ROLL), spool=S.tolist(), CORE_R=CORE_R, ROLL_FULL=ROLL_FULL, FLANGE_R=FLANGE_R, RCH_S=RCH_S,
         wrap_roller_deg=[A_R + wrap_right(CORE_R)[2], A_R + wrap_right(ROLL_FULL)[2]], wrap_guide_deg=float(A_L + DELTA_L),
         cass_front=float(CL[1] + CASS_R), cass_back=float(CL[1] - CASS_R), roller_back=float(CR[1] - R_ROLL - TOOTH))
print("A:", json.dumps(A, indent=1))

# ------------------------------------------------------------------ (B) front plate: blade pivot, wheel, handle, the two click springs
# (x right, z up, seen from behind)
from shapely.geometry import Polygon as Pg
from shapely.ops import unary_union
H = 28.2                                              # half height of the body
FX0, FX1, FZ0, FZ1 = -33.1, 34.0, -H + 1.6, H         # front plate outline: its top edge is flush with the top of the body.  v2.7: 3 mm wider on the left, room for the wheel's larger click
P_S = np.array([16.0, H - 4.6])                       # blade pivot: a stout boss just under the top edge; the blade hangs from it
R_PORT = float(np.hypot(*P_S)); A0 = float(np.degrees(np.arctan2(-P_S[1], -P_S[0])) % 360)
PORT_CV, WIN_R, OVERLAP = 3.15, 2.8, 1.6
WIN_PROJ = WIN_R + 0.75 * np.tan(43.6 * D2R)
THETA = np.ceil(np.degrees(np.arcsin((WIN_R + PORT_CV + OVERLAP) / R_PORT)) * 2) / 2
SPAN = THETA + np.degrees(np.arcsin(PORT_CV / R_PORT)) + np.degrees(OVERLAP / R_PORT)
R_OUT = R_PORT + PORT_CV + OVERLAP
STOPS = [("400", 1.0), ("200", 1.45), ("100", 1.68)]   # v2.14: the large hole is 3.4 mm (f/9.5), not 4.0 (f/8): tools/focus.py, half-way out it is sharp on a phone at f/9.5 and not at f/8.  Its name stays "100"
SPACE_R = [1.0, 1.45, 2.0]                                # the holes stand on the wheel where they stood: the spacing is still worked out for a 4.0 mm hole, so no click, slot or dot moves
_OLD_STOPS = [("400", 1.0), ("200", 1.45), ("100", 2.0)]   # v2.7: f/16, f/11, f/8 as printed: the full-sun opening for ISO 400, 200 and 100 film at about 1/300 s
COLLAR = 2.35                                         # v2.7: the wheel turns on a plain 4.7 mm post (no shoulder: that frees 0.85 mm for the blade's spring)
# v2.7 click springs.  A click between two printed parts is a tab in a slot: tooth, wall, hub hole and boss each move with the printer's wall
# error e, so how far the tooth is pushed in changes by 4 e -- when the spring's own push seats the hub (at rest).  While the rocker is PRESSED the
# finger seats the hub the other way (it pushes eight times harder than the tooth, toward the click wall): the blade hangs on its boss, tooth tip
# and the hub hole's upper wall face the same way, and the error cancels.  The two states differ by the hub's whole play, 2 (HUBC - 2 e).
#   at rest:  pushed in REST + 4 e  (REST = BUMP - SCL = 0.8: from 0.2 on a printer 0.15 thin to 1.8 on one 0.25 fat; it only has to hold the blade shut)
#   pressed:  pushed in REST + 2 HUBC = 1.8 mm on every printer: that sets the force and so the shutter's time
# so the spring must travel 4 x (the whole range of e) + a little: 1.8 mm.  The hub holes are drawn HUBC off-centre, away from the tooth:
# as drawn each part is in its rest position and its tooth just touches both ramps of its V (apex DV deep; a round tip TIP_R seats 0.414 TIP_R above the apex).
TIP_R = 0.8; HUBC = 0.5; WALL = 3.0
SLIT_B, BUMP_B, SCL_B, DV_B = 2.6, 2.25, 1.25, 1.4     # blade: SCL_B = 0.27 (clear of the wall while hanging: the same on every printer) + 2 HUBC.  v2.8: at rest the tooth is 1.0 + 4 e deep (0.8 before: on a printer 0.15 thin gravity could swing the shutter open); pressed 2.0; deeper notches
SLIT_W, BUMP_W, SCL_W, DV_W = 2.9, 2.3, 1.1, 1.5       # wheel: nothing but its spring seats it: pushed in 1.2 + 4 e (v2.8: 0.2 more), up to 2.2; slit 2.9
BL_T, WH_T = 1.35, 1.8                                # spring thickness, blade / wheel: three and four 0.45 mm lines
BL_L, WH_L = 28.0, 32.0                               # spring lengths
SLIT, BUMP, SCL = SLIT_B, BUMP_B, SCL_B               # (old names: the blade's)
def sector(c, r0, r1, a0, a1, n=40):
    a = np.linspace(a0, a1, n); return Pg([tuple(pol(c, r0, t)) for t in a] + [tuple(pol(c, r1, t)) for t in a[::-1]])
BL_ARC = float(np.degrees(BL_L / (R_OUT + SLIT_B + BL_T / 2))); DB_A = A0 + SPAN + 0.8                  # blade spring: bump just past the pie's corner, root BL_ARC before it
R_BL = R_OUT + SLIT + BL_T + BUMP                                                                    # blade's reach
RWB = R_OUT + SLIT + BL_T + SCL
blade_sweep = unary_union([Pg([tuple(P_S)] + [tuple(pol(P_S, R_BL, t)) for t in np.linspace(A0 - SPAN - THETA - 1, DB_A + THETA + 3, 80)])]).buffer(0.6)
btrack = sector(P_S, RWB, RWB + WALL, DB_A - THETA - 4, DB_A + THETA + 4)
bstops = unary_union([sector(P_S, 20, 27, A0 + SPAN + THETA + 1.2, A0 + SPAN + THETA + 6), sector(P_S, 20, 27, A0 - SPAN - THETA - 6, A0 - SPAN - THETA - 1.2)])
LAND_L, LAND_W = 9.8, 6.6
lands = unary_union([Pg([(x, z), (x + LAND_L, z), (x + LAND_L, z + LAND_W), (x, z + LAND_W)]) for x, z in ((FX0, FZ0), (FX1 - LAND_L, FZ0), (FX0, FZ1 - 13.6), (FX1 - LAND_L, FZ1 - 13.6))])   # the slab under each hooked foot must be solid
latch = Pg([(-17.5, FZ1 - 6.8), (5.6, FZ1 - 6.8), (5.6, FZ1), (-17.5, FZ1)])
cavity = Pg([(FX0 + 1.9, FZ0 + 1.9), (FX1 - 1.9, FZ0 + 1.9), (FX1 - 1.9, FZ1 - 1.9), (FX0 + 1.9, FZ1 - 1.9)])
def angdiff(a, b): return (a - b + 180) % 360 - 180
best = None
for R_HOLE in np.arange(10.5, 11.51, 0.25):
    for ang in np.arange(0, 360, 0.5):
        c = pol((0, 0), R_HOLE, ang); dp = float(np.linalg.norm(c - P_S))
        if dp < RWB + COLLAR - 1.0: continue                                     # the wheel's post stands at the edge of the blade's room: at most 1 mm of it is cut flat there
        if abs(angdiff(np.degrees(np.arctan2(c[1] - P_S[1], c[0] - P_S[0])), DB_A)) < THETA + 4 + np.degrees(np.arcsin(COLLAR / dp)) + 2: continue   # ...and the bump's path
        WHEEL_R = float(np.ceil(max(13.5, R_HOLE + WIN_PROJ + 1.0) * 10) / 10)
        if c[0] - WHEEL_R - 0.4 < FX0 + 1.9 or c[1] - WHEEL_R - 0.4 < FZ0 + 1.9 or c[0] + WHEEL_R > FX1 - 2.3 or c[1] + WHEEL_R > FZ1 - 2.3: continue
        need = lambda r_j: 2 * np.degrees(np.arcsin(min(1, (WIN_PROJ + r_j + 0.7) / (2 * R_HOLE))))
        W = [0.0]
        for k in range(1, len(STOPS)): W.append(W[-1] + max(need(SPACE_R[k - 1]), need(SPACE_R[k]), 24.0))
        score = -dp
        if best is None or score < best[0]: best = (score, dict(WHEEL_R=WHEEL_R, R_HOLE=float(R_HOLE), c=c.tolist(), WPOS=[float(w) for w in W], boss_to_spring=float(dp - R_OUT - SLIT - BL_T - COLLAR), dp=dp))
B = best[1]; c = np.array(B["c"]); WHEEL_R = B["WHEEL_R"]; W = B["WPOS"]; B["A_AX"] = float(np.degrees(np.arctan2(-c[1], -c[0])))
WH_ARC = float(np.degrees(WH_L / (WHEEL_R + SLIT_W + WH_T / 2))); RWW = WHEEL_R + SLIT_W + WH_T + SCL_W; HW_SLOT, HW_FIN = 4.0, 4.6; H_RHO = WHEEL_R - HW_FIN - 0.1    # aperture handle: 6.2 mm thick (slot 7.0, foot 8.0)
fixed_full = unary_union([bstops, lands, latch, Pg([tuple(pol(P_S, 5.2, t)) for t in range(0, 360, 10)])])       # full-height things the wheel's spring must miss
# wheel click: bump at WD_A0 (position 0), moving to WD_A0 - W[-1]; its wall is full height, so it must stay out of the blade's sweep
cands = []
for a0 in np.arange(0, 360, 1.0):
    wall = sector(c, RWW, RWW + DV_W + 1.2, a0 - W[-1] - 8, a0 + 8); band = sector(c, WHEEL_R, WHEEL_R + SLIT_W + WH_T + 0.4, a0 - W[-1] - WH_ARC - 11, a0 + 2)   # (the wall is solid out to the plate's rim; the bump only ever sits in front of it)
    inner = sector(c, RWW, RWW + DV_W + 0.3, a0 - W[-1] - 8, a0 + 8)
    if wall.intersects(blade_sweep) or wall.intersects(lands) or wall.intersects(latch) or wall.intersects(bstops): continue
    if not cavity.buffer(1.4).contains(inner) or not cavity.buffer(1.9).contains(wall): continue
    if band.intersects(fixed_full) or not cavity.buffer(-0.3).contains(band): continue
    cands.append(float(a0))
assert cands, "no place for the wheel's click wall"
WD_A0 = cands[len(cands) // 2]; wwall = sector(c, RWW, RWW + DV_W + 1.2, WD_A0 - W[-1] - 8, WD_A0 + 8)
# handle fin: stands in the blade's plane and comes out through a slot in the plate
hc = []; FH = 12.0; LAB_R = 7.2                                    # half length of the aperture handle, degrees: a handle about 11 mm long; the dots sit LAB_R outside the slot's middle
for a0 in np.arange(0, 360, 1.0):
    slot = sector(c, H_RHO - HW_SLOT, H_RHO + HW_SLOT, a0 - W[-1] - FH - 1, a0 + FH + 1); fin = sector(c, H_RHO - HW_FIN, H_RHO + HW_FIN, a0 - W[-1] - FH, a0 + FH)
    if fin.intersects(blade_sweep.buffer(1.5)) or fin.intersects(btrack.buffer(0.6)) or fin.intersects(bstops) or slot.buffer(1.2).intersects(lands) or slot.buffer(1.2).intersects(latch): continue
    if not cavity.buffer(-1.5).contains(slot) or slot.buffer(1.0).intersects(wwall): continue
    if min(np.hypot(*pol(c, H_RHO, a0 - t)) for t in np.linspace(-FH - 1, W[-1] + FH + 1, 30)) < 10.6 + HW_SLOT - 2.4: continue      # lens pocket
    lab = [pol(c, H_RHO + LAB_R, a0 - w) for w in W]                                                        # the three dots, outside the slot, must sit on the plate and clear the lens
    if any(q[0] < FX0 + 2.6 or q[0] > FX1 - 3 or q[1] < FZ0 + 3.0 or q[1] > FZ1 - 3 or np.hypot(*q) < 10.5 for q in lab): continue
    hc.append(float(a0))
assert hc, "no place for the handle"
HANDLE_A0 = hc[len(hc) // 2]; print('handle choices', hc[0], '..', hc[-1], len(hc))
B.update(P_S=P_S.tolist(), R_PORT=R_PORT, A0=A0, H=H, plate=[FX0, FX1, FZ0, FZ1], THETA=float(THETA), SPAN=float(SPAN), R_OUT=float(R_OUT), HANDLE_A0=HANDLE_A0, H_RHO=float(H_RHO), FIN_HALF=FH, HW_SLOT=HW_SLOT, HW_FIN=HW_FIN, LAB_R=LAB_R,
         WD_A0=WD_A0, WH_ARC=WH_ARC, DB_A=float(DB_A), BL_ARC=BL_ARC, BL_T=BL_T, WH_T=WH_T, SLIT=SLIT, BUMP=BUMP, SCL=SCL, HUBC=HUBC, REST_B=BUMP_B - SCL_B, PRESSED_B=BUMP_B - SCL_B + 2 * HUBC, REST_W=BUMP_W - SCL_W, SLIT_W=SLIT_W, BUMP_W=BUMP_W, SCL_W=SCL_W, DV_B=DV_B, DV_W=DV_W, TIP_R=TIP_R, BL_L=BL_L, WH_L=WH_L, STOPS=[q[1] for q in STOPS], wheel_click_range=[cands[0], cands[-1]], handle_choices=len(hc), wheel_click_choices=len(cands))
print("B:", json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in B.items() if k != "c"}), "c", np.round(c, 2))
json.dump(dict(A=A, B=B), open("build/layout.json", "w"), indent=1)
def v(x): return "[" + ", ".join("%.4f" % q for q in x) + "]" if isinstance(x, (list, tuple, np.ndarray)) else "%.4f" % x
L = ["// generated by tools/layout.py -- do not edit by hand",
     "A_L = %s; DELTA_L = %s; L_LIP = %s;" % (v(A_L), v(DELTA_L), v(L_LIP)),
     "GUIDE = %s; LIP_TIP = %s; CASS = %s;" % (v(gL * [-1, 1]), v(TL * [-1, 1]), v(CL * [-1, 1])),
     "Y_FRONT = %s; Y_RIM = %s; A_R = %s; ROLLER = %s; R_ROLL = %s; SPOOL = %s; CORE_R = %s; ROLL_FULL = %s; FLANGE_R = %s; RCH_S = %s;" % (v(Y_FRONT), v(Y_RIM), v(A_R), v(CR), v(R_ROLL), v(S), v(CORE_R), v(ROLL_FULL), v(FLANGE_R), v(RCH_S)),
     "H = %s; FX0 = %s; FX1 = %s; FZ0 = %s; FZ1 = %s;" % (v(H), v(FX0), v(FX1), v(FZ0), v(FZ1)),
     "P_S = %s; R_PORT = %s; A0 = %s; THETA_S = %s; SPAN = %s; R_OUT = %s; OVERLAP = %s;" % (v(P_S), v(R_PORT), v(A0), v(THETA), v(SPAN), v(R_OUT), v(OVERLAP)),
     "WHEEL_R = %s; R_HOLE = %s; WHEEL_C = %s; WPOS = %s; A_AX = %s; HANDLE_A0 = %s; H_RHO = %s; FIN_HALF = %s; HW_SLOT = %s; HW_FIN = %s; LAB_R = %s;" % (v(WHEEL_R), v(B["R_HOLE"]), v(B["c"]), v(W), v(B["A_AX"]), v(HANDLE_A0), v(H_RHO), v(FH), v(HW_SLOT), v(HW_FIN), v(LAB_R)),
     "BL_SLIT = %s; WH_SLIT = %s; BL_T = %s; WH_T = %s; BL_BUMP = %s; WH_BUMP = %s; BL_CL = %s; WH_CL = %s; BL_DV = %s; WH_DV = %s; TIP_R = %s; SPR_WALL = %s; HUB_C = %s; WD_A0 = %s; WH_ARC = %s; DB_A = %s; BL_ARC = %s;" % (v(SLIT_B), v(SLIT_W), v(BL_T), v(WH_T), v(BUMP_B), v(BUMP_W), v(SCL_B), v(SCL_W), v(DV_B), v(DV_W), v(TIP_R), v(WALL), v(HUBC), v(WD_A0), v(WH_ARC), v(DB_A), v(BL_ARC)),
     "STOP_R = %s;" % v([q[1] for q in STOPS])]
open("scad/layout.scad", "w").write("\n".join(L) + "\n")
# ------------------------------------------------------------------ plot
fig, ax = plt.subplots(1, 2, figsize=(17, 7))
a = ax[0]; th = np.linspace(-A_L, A_R, 200)
a.plot(*np.array([arc(t) for t in th]).T, "k", lw=2)
a.add_patch(plt.Circle(gL * [-1, 1], R_G, fc="#9bb7d4")); a.add_patch(plt.Circle(CR, R_ROLL, fc="#e0a36a")); a.add_patch(plt.Circle(S, FLANGE_R, fill=False, color="#b8860b")); a.add_patch(plt.Circle(CL * [-1, 1], CASS_R, fill=False, color="#b8860b", lw=2))
a.axhline(Y_FRONT, color="g", ls="--"); a.axhline(Y_RIM, color="r", ls="--"); a.set_aspect("equal"); a.set_xlim(-66, 66); a.set_ylim(-8, 36); a.grid(alpha=.3); a.set_title("plan view: film path")
a = ax[1]
for phi, col in ((-THETA, "#2f6db5"), (0, "#999"), (THETA, "#c93a3a")):
    a.plot(*Pg([tuple(P_S)] + [tuple(pol(P_S, R_OUT, t + phi)) for t in np.linspace(A0 - SPAN, A0 + SPAN, 60)]).exterior.xy, color=col, lw=1)
    a.plot(*sector(P_S, R_OUT + SLIT, R_OUT + SLIT + BL_T, DB_A - BL_ARC - 5 + phi, DB_A + 1.5 + phi).exterior.xy, color=col, lw=1); a.plot(*pol(P_S, R_BL - 0.5, DB_A + phi), ".", color=col)
for g_, col in ((btrack, "#555"), (bstops, "#555"), (wwall, "#555"), (lands, "#bbb"), (latch, "#bbb")):
    for q in (g_.geoms if hasattr(g_, "geoms") else [g_]): a.fill(*q.exterior.xy, color=col, alpha=.5)
a.add_patch(plt.Circle(c, WHEEL_R, fill=False, color="k", lw=1.5)); a.add_patch(plt.Circle(c, COLLAR, fc="#ccc"))
a.plot(*sector(c, WHEEL_R + SLIT, WHEEL_R + SLIT + WH_T, WD_A0 - WH_ARC - 11, WD_A0 + 1.5).exterior.xy, "k", lw=1); a.plot(*pol(c, RWW + 0.4, WD_A0), "k.")
for kk, (lab, r) in enumerate(STOPS):
    h = pol(c, B["R_HOLE"], B["A_AX"] + W[kk]); a.add_patch(plt.Circle(h, max(r, 0.4), color="k")); a.annotate(lab, h + [0.8, 0.8], fontsize=8)
pts = np.array([pol(c, H_RHO, HANDLE_A0 - t) for t in np.linspace(-FH, W[-1] + FH, 60)]); a.plot(*pts.T, "g", lw=4, alpha=.5)
a.add_patch(plt.Circle((0, 0), 6.1, fill=False, color="b")); a.plot(*P_S, "ko"); a.add_patch(plt.Rectangle((FX0, FZ0), FX1 - FX0, FZ1 - FZ0, fill=False, ls="--"))
a.set_aspect("equal"); a.set_xlim(-34, 36); a.set_ylim(-31, 34); a.grid(alpha=.3); a.set_title("front plate seen from behind")
plt.tight_layout(); plt.savefig("build/layout.png", dpi=75)
