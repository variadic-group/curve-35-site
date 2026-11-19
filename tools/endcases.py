"""End cases: every click, latch and spring followed through its motion on printers 0.15 mm thin, exact, 0.10 and 0.25 mm fat.
Sections of the two parts are cut from the meshes, grown by the wall error, and moved through the real motion.  At each step the spring's end is
pushed back just far enough to be free of the other part: that is how far the spring bends there, and whether it has the room.  The slope of that
curve is the ramp the spring climbs, so with the spring's stiffness and strain (tools/fea_cases.py run at the same wall error: WALL=...) and
friction 0.2 / 0.35 / 0.45 it also gives the force at the hand and the force that holds.  Writes build/endcases.json."""
import sys, json, numpy as np, shapely
from shapely.geometry import box, Point
from shapely.affinity import rotate, translate
sys.path.insert(0, "tools"); import fea, geom
from scadr import values
A = "build/asm/"; LY = json.load(open("build/layout.json")); B = LY["B"]; P = np.array(B["P_S"]); C = np.array(B["c"]); TH = B["THETA"]; YF = 25.47
MV = values(["SLIDE", "F_Z0", "F_Z1", "F_SLIT", "NUB_X0", "NUB_X1", "NUB_H", "H", "Y_RIM", "H_RHO", "PAD_X0", "PAD_X1"])
PRINTERS = [(-0.15, "0.15 thin"), (0.0, "exact"), (0.10, "0.10 fat"), (0.25, "0.25 fat")]; MUS = (0.2, 0.35, 0.45); TOL = 0.003
FE = {e: json.load(open("build/fea.json" if e == 0 else "build/fea_wall%+.2f.json" % e)) for e, _ in PRINTERS}
def per_mm(e, key, bend):
    r = [v for k, v in FE[e].items() if key in k][0]; return r["force_N"] / bend, r["peak_strain_pct"] / bend
def sec(name, origin, normal, ax, e): return fea.section(A + name + ".stl", origin, normal, ax).buffer(e, 8)
def grow1(p, e, axis):
    """grow a section along one of its axes only: the other is the print's layer direction, where wall error does not apply"""
    if not e: return p
    sh = [translate(p, t if axis == 0 else 0.0, t if axis == 1 else 0.0) for t in np.linspace(-abs(e), abs(e), 7)]
    if e > 0: return shapely.unary_union(sh)
    q = sh[0]
    for g in sh[1:]: q = q.intersection(g)
    return q
def free_at(piece, dirv, blockers, dmax=3.6):
    """smallest shift of piece along dirv that takes it out of blockers; None if it cannot get free"""
    over = lambda d: translate(piece, d * dirv[0], d * dirv[1]).intersection(blockers).area > TOL
    if not over(0.0): return 0.0
    lo = 0.0
    for hi in np.arange(0.1, dmax + 0.05, 0.1):
        if not over(hi): break
        lo = hi
    else: return None
    for _ in range(6):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if over(mid) else (lo, mid)
    return hi
def cam(s, d, K, mu, kap=0.0):
    """force along the motion that drives a follower whose spring (K N/mm) is bent d(s): N (tan a + mu) / (1 - mu tan a); it locks where mu tan a reaches 1.
    kap: the driving force itself helps to lift the follower (kap > 0) or holds it down (kap < 0), kap N of lift for each newton: F = N g / (1 + kap g); it locks where kap g reaches -1"""
    d = np.array([np.nan if v is None else v for v in d], float); slope = np.gradient(d, s); den = 1 - mu * slope; g = (slope + mu) / np.maximum(den, 0.08); den2 = 1 + kap * g
    return np.where((den > 0.08) & (den2 > 0.08), K * d * g / np.maximum(den2, 0.08), np.where(d > 1e-6, np.inf, 0.0))
def peak(F): F = F[~np.isnan(F)]; return float(F.max()) if len(F) else float("nan")
def room_to(piece, dirv, own):
    for d in np.arange(0.0, 4.0, 0.05):
        if translate(piece, d * dirv[0], d * dirv[1]).intersection(own).area > TOL: return float(d - 0.05)
    return 4.0
# ---------------------------------------------------------------- 1. the shutter's click
def rim_click(e, part, ctr, R, slit, ang0, sweep, hub, seats, step=0.25, level=1.5):
    """a tooth on a rim spring, followed along its click wall.  ang0: where the tooth points in the world; sweep: how far the part turns (degrees, sign = sense)"""
    rot = 90 - ang0; p = rotate(sec(part, [0, YF + level, 0], [0, 1, 0], [0, 2], e), rot, origin=tuple(ctr))
    ring = Point(ctr).buffer(R + 14, 64).difference(Point(ctr).buffer(R - 3, 64)); fr = sec("front", [0, YF + level, 0], [0, 1, 0], [0, 2], e).intersection(ring)
    tb = box(ctr[0] - 6, ctr[1] + R + slit / 2, ctr[0] + 6, ctr[1] + R + 12); tip = p.intersection(tb); body = p.difference(tb); local = box(ctr[0] - 9, ctr[1] + R - 3, ctr[0] + 9, ctr[1] + R + 14)
    rho = max(hub - 2 * e, 0.0); ph = np.arange(0, abs(sweep) + 0.01, step); sg = np.sign(sweep); res = dict(angles=ph, room=room_to(tip, (0, -1), body), play=2 * rho)
    for seat in seats:
        d = []
        for a in ph:
            wall = rotate(fr, rot - sg * a, origin=tuple(ctr)).intersection(local); dn = np.radians(270 + rot - sg * a)        # the world's "down" in the part's own frame
            t = (rho * np.cos(dn), rho * np.sin(dn) + hub - 0.02) if seat == "pressed" else (0.0, hub - 0.02 - rho)   # pressed: it hangs on its post under the finger.  rest: its own spring pushes it off the wall
            d.append(free_at(translate(tip, *t), (0, -1), wall))
        res[seat] = np.array([np.nan if v is None else v for v in d], float)
    return res
out = {}
print("1. SHUTTER: the blade's tooth along its click wall (closed - open - closed), pressed and at rest")
RW = B["R_OUT"] + B["SLIT"] + B["BL_T"] + B["SCL"]
for e, name in PRINTERS:
    r = rim_click(e, f"blade_PHI{TH}", P, B["R_OUT"], B["SLIT"], B["DB_A"] + TH, -2 * TH, B["HUBC"], ("pressed", "rest")); K, eps = per_mm(e, "blade click spring, tooth pushed in %s mm (pressed" % B["PRESSED_B"], B["PRESSED_B"])
    s = np.radians(r["angles"]) * RW; lev = np.array([geom.lever(B, TH - a) for a in r["angles"]]); first = r["angles"] < TH * 0.6; dp, dr = r["pressed"], r["rest"]
    press = [peak((cam(s, dp, K, mu) * RW / lev)[first]) for mu in MUS]; hold = [peak((cam(s, dr, K, mu) * RW)[first]) for mu in MUS]         # N at the finger; N mm of holding torque at rest
    mid = np.abs(r["angles"] - TH) < 2.0; o = dict(wall_error=e, bend_on_wall_pressed=float(np.nanmax(dp)), bend_in_notch_pressed=float(dp[0]), bend_at_rest=float(dr[0]), engagement_at_rest=float(np.nanmax(dr[first])),
             dip_at_middle_click=float(np.nanmax(dp) - np.nanmin(dp[mid])), room=r["room"], hub_play=r["play"], spring_N_per_mm=K, strain_pressed_pct=eps * float(np.nanmax(dp)), strain_at_rest_pct=eps * float(dr[0]),
             press_N=press, hold_at_rest_Nmm=hold, blocked=bool(np.isnan(dp).any()))
    out.setdefault("shutter", {})[name] = o
    print("  %-9s bend pressed %.2f mm (room %.2f) strain %.2f %%; press %.1f / %.1f / %.1f N; at rest: tooth %.2f mm deep, spring bent %.2f mm (%.2f %%), holds %.1f to %.1f N mm; middle click %.2f mm deep; hub play %.2f%s"
          % (name, o["bend_on_wall_pressed"], o["room"], o["strain_pressed_pct"], *press, o["engagement_at_rest"], o["bend_at_rest"], o["strain_at_rest_pct"], hold[0], hold[2], o["dip_at_middle_click"], o["hub_play"], "  ** BLOCKED **" if o["blocked"] else ""))
# ---------------------------------------------------------------- 2. the aperture wheel's click
print("2. APERTURE WHEEL: its tooth along its click wall (small - middle - large hole); its own spring seats it")
RWW = B["WHEEL_R"] + B["SLIT_W"] + B["WH_T"] + B["SCL_W"]
for e, name in PRINTERS:
    r = rim_click(e, "wheel_STOP0", C, B["WHEEL_R"], B["SLIT_W"], B["WD_A0"], -B["WPOS"][2], B["HUBC"], ("rest",), step=0.5, level=0.75); K, eps = per_mm(e, "wheel click spring, tooth pushed in %s mm at the top of the ramp (as drawn" % B["REST_W"], B["REST_W"])
    s = np.radians(r["angles"]) * RWW; d = r["rest"]; turn = [peak(cam(s, d, K, mu) * RWW / MV["H_RHO"]) for mu in MUS]; back = [peak(cam(s[::-1] * -1, d[::-1], K, mu) * RWW / MV["H_RHO"]) for mu in MUS]
    notch = [float(d[np.argmin(np.abs(r["angles"] - w))]) for w in B["WPOS"]]
    o = dict(wall_error=e, bend_on_wall=float(np.nanmax(d)), bend_in_notches=notch, room=r["room"], hub_play=r["play"], spring_N_per_mm=K, strain_pct=eps * float(np.nanmax(d)), strain_at_rest_pct=eps * max(notch), turn_N=turn, turn_back_N=back, blocked=bool(np.isnan(d).any()))
    out.setdefault("wheel", {})[name] = o
    print("  %-9s bend on the wall %.2f mm (room %.2f) strain %.2f %%; in the notches %.2f / %.2f / %.2f mm (%.2f %% at rest); turning takes %.1f / %.1f / %.1f N at the handle (back: %.1f / %.1f / %.1f); hub play %.2f%s"
          % (name, o["bend_on_wall"], o["room"], o["strain_pct"], *notch, o["strain_at_rest_pct"], *turn, *back, o["hub_play"], "  ** BLOCKED **" if o["blocked"] else ""))
# ---------------------------------------------------------------- 3. the front plate's latch (v2.8: a leaf that bends in the layer direction)
print("3. FRONT PLATE: slid on (4.4 mm down) and pushed back up against its latch.  Side view: only the sliding direction takes the wall error; heights are layers")
LV = values(["LF_X0", "LF_X1", "LF_ZH", "TOOTH_H", "LF_DB", "FEET", "FOOT_W", "SLIDE", "PK_X"]); XM = (LV["LF_X0"] + LV["LF_X1"]) / 2; SL = LV["SLIDE"]; ZHm = LV["LF_ZH"]; arr = lambda v: np.array([np.nan if q is None else q for q in v], float)
side = lambda part, x, e: grow1(sec(part, [x, 0, 0], [1, 0, 0], [2, 1], 0), e, 0)
for e, name in PRINTERS:
    post = side("front", XM, e).intersection(box(ZHm - 1.7, YF - 2.6, ZHm + 1.7, YF + 3.5)); near = side("body", XM, e).intersection(box(ZHm - 4, YF - 3.2, ZHm + SL + 4, YF + 0.5))
    xf = LV["FEET"][0][0] + LV["FOOT_W"] / 2; feet = side("front", xf, e).intersection(box(-40, YF - 5, 40, YF + 0.02)); pock = side("body", xf, e)
    up = [q for q in np.arange(0, 1.01, 0.01) if translate(feet, 0, q).intersection(pock).area < TOL]; slack = max(up) if up else 0.0                  # how far the plate lifts off the body before its hooks stop it
    LIFT = round(LV["TOOTH_H"] - LV["LF_DB"], 2); K, eps = per_mm(e, "plate latch leaf, post lifted %s mm (riding over the bump with no slack" % LIFT, LIFT); z = np.arange(SL, -0.001, -0.05); lift = arr([free_at(translate(post, zz, 0), (0, 1), near) for zz in z]); d = np.maximum(lift - slack, 0.0); upw = d[::-1]
    LJ = json.load(open("build/fea_leaf.json" if e == 0 else "build/fea_leaf_wall%+.2f.json" % e)); KAP = LJ["kappa_plus_z"]          # sliding on, the bump pushes the post toward +z; pushed back up, toward -z
    on = [peak(cam(SL - z, d, K, mu, KAP)) for mu in MUS]; off = [peak(cam(z[::-1], upw, K, mu, -KAP)) for mu in MUS]
    def work(F): F = np.where(np.isfinite(F), F, 0.0); k = int(np.argmax(F)); return float(np.trapezoid(np.maximum(F[:k + 1], 0), z[::-1][:k + 1]))     # work to push the plate up as far as the top of the bump (N mm): what a fall has to supply
    woff = [work(cam(z[::-1], upw, K, mu, -KAP)) for mu in MUS]; play = float(z[::-1][np.argmax(lift[::-1] > 0.03)]) if (lift > 0.03).any() else float(SL)
    o = dict(wall_error=e, kappa=KAP, lift_when_set_on=float(lift[0]) if np.isfinite(lift[0]) else None, slack_of_feet=slack, sideways_float=LV["PK_X"] - 2 * e, post_lift=float(np.nanmax(lift)), leaf_bend=float(np.nanmax(d)), at_rest=float(d[-1]), strain_pct=eps * float(np.nanmax(d)), spring_N_per_mm=K, slide_on_N=on, hold_N=off, work_off_Nmm=woff, play_at_home=play, blocked=bool(np.isnan(lift).any()))
    out.setdefault("plate", {})[name] = o
    print("  %-9s the post rises %.2f mm, the feet take up %.2f, the leaf bends %.2f mm (%.2f %%); slides on with %.1f / %.1f / %.1f N; at home: %.2f mm of play, leaf bent %.2f; pushed back up it holds %.1f / %.1f / %.1f N; sideways float +/- %.2f%s"
          % (name, o["post_lift"], slack, o["leaf_bend"], o["strain_pct"], *on, play, o["at_rest"], *off, o["sideways_float"], " ** BLOCKED **" if o["blocked"] else ""))
# ---------------------------------------------------------------- 4. the back's two latch fingers
print("4. BACK: pressed on, and opened by its pads (one finger; there are two, top and bottom).  The back itself has (0.6 - 2e) mm of play up and down in the rim")
NUBC = (MV["NUB_X0"] + MV["NUB_X1"]) / 2; YR = MV["Y_RIM"]; H = MV["H"]
for e, name in PRINTERS:
    bk = grow1(sec("back", [NUBC, 0, 0], [1, 0, 0], [1, 2], 0), e, 1); bd = grow1(sec("body", [NUBC, 0, 0], [1, 0, 0], [1, 2], 0), e, 1)      # y is the layer direction of both parts
    fb = box(YR - 12, MV["F_Z1"] - 2.2, YR + 3, H + 4); fin = bk.intersection(fb); near = bd.intersection(box(YR - 14, 20, YR + 6, H + 4))
    K, eps = per_mm(e, "back latch finger, nub pushed down 1.6", 1.6); y = np.arange(-7.0, 0.001, 0.05); d = arr([free_at(translate(fin, yy, 0), (0, -1), near) for yy in y])
    R = json.load(open("build/fea_finger%s.json" % ("" if e == 0 else "_wall%+.2f" % e))); eps_pad = [v for k, v in FE[e].items() if "pad pressed level with the catch" in k][0]["peak_strain_pct"] / R["pad_up"]
    rest = max(0.0, 2 * e - 0.07); play = max(0.0, 0.6 - 2 * e); ride = float(np.nanmax(d)); eng = ride - max(0.0, 0.07 - 2 * e) * 0 ; worst_eng = ride - max(0.0, play - rest)       # engagement: centred, and with the back pushed away from this latch as far as the rim lets it go
    need = ride + 0.1; need_w = ride + min(play, 0.6) + 0.1; on = [peak(cam(y - y[0], d, K, mu)) for mu in MUS]
    o = dict(wall_error=e, nub_engagement=ride, nub_engagement_back_pushed_away=worst_eng, bent_at_rest=rest, spring_N_per_mm=K, strain_closing_pct=eps * ride, close_N_one_finger=on, pad_travel_to_open=need / R["nub_per_pad"], pad_travel_worst=need_w / R["nub_per_pad"],
             pad_can_go=R["pad_up"], strain_opening_pct=eps_pad * need_w / R["nub_per_pad"], tip_closing=R["tip_per_nub_pushed"] * (ride + play), tip_opening=R["tip_per_pad"] * need_w / R["nub_per_pad"], slit=R["slit"], blocked=bool(np.isnan(d).any()))
    out.setdefault("back", {})[name] = o; bad = max(o["tip_closing"], o["tip_opening"]) > o["slit"] or o["pad_travel_worst"] > o["pad_can_go"]
    print("  %-9s nub catches %.2f mm (%.2f with the back pushed away from it); closing bends the finger %.2f mm (%.2f %%), %.1f / %.1f / %.1f N; at rest bent %.2f; to open press the pad %.2f mm (%.2f at worst; it stands %.1f proud): %.2f %%; the tip moves %.2f closing, %.2f opening, slit %.2f%s%s"
          % (name, ride, worst_eng, ride, o["strain_closing_pct"], *on, rest, o["pad_travel_to_open"], o["pad_travel_worst"], o["pad_can_go"], o["strain_opening_pct"], o["tip_closing"], o["tip_opening"], o["slit"], "  ** NOT ENOUGH TRAVEL **" if bad else "", " ** BLOCKED **" if o["blocked"] else ""))
json.dump(out, open("build/endcases.json", "w"), indent=1, default=lambda v: v.tolist() if hasattr(v, "tolist") else float(v))
