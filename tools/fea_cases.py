import shapely
"""Finite-element cases for ONE-135: every part that bends, catches or could be knocked, cut from the exported meshes
(run tools/check.py first).  Writes build/fea.json and build/fea.png."""
import sys, json, pickle, numpy as np, shapely
sys.path.insert(0, "tools"); import fea
W = fea.WALL                                                        # this printer's wall error (0 unless WALL is set)
from scadr import values
MV = values(["LF_X0", "LF_X1", "LF_T", "LF_ZR", "LF_ZH", "LF_ZB", "LF_DB", "TOOTH_H", "Y_CVF", "F_X0", "F_X1", "F_Z1", "F_T", "F_DROP", "DOOR_TOP", "NUB_X0", "NUB_X1", "NUB_H", "PAD_X0", "PAD_X1", "PAD_UP", "OP_X0", "OP_X1", "ARM_X0", "ARM_X1", "HORN_X0", "HORN_X1", "HORN_GAP", "FEET", "FOOT_W", "FOOT_L", "KN_R", "KN_CR", "SP_KR", "SP_KCR", "KSW", "ZC1", "CASS", "SPOOL", "RB_HW", "RB_HWL", "RB_SEAT", "RB_GAP", "RB_FLOOR", "RB_Z", "ROLLER", "RB_UP", "KN_PZ", "KN_LZ", "KN_CZ", "KN_NK", "KN_SC", "H", "Y_RIM", "FW_KSW", "FW_NK", "FW_LZ", "SHAFT_R", "SHAFT_CL", "COLLAR_R"])     # the model's own numbers
from shapely.geometry import box
A = "build/asm/"; LY = json.load(open("build/layout.json")); B = LY["B"]; P = np.array(B["P_S"]); TH = B["THETA"]; C = np.array(B["c"]); H = B["H"]
YF = 25.47; YRIM = LY["A"]["Y_RIM"]; out = {}; pics = {}
# v2.7: the blade's tooth is pushed in PRESSED_B while the rocker is pressed (the same on every printer) and REST_B + 4 e at rest; the wheel's REST_W + 4 e
BENDS_B = ((B["PRESSED_B"], "pressed: the same on every printer"), (B["REST_B"], "at rest, as drawn"), (round(B["REST_B"] + 0.4, 2), "at rest, walls +0.10"), (round(B["REST_B"] + 1.0, 2), "at rest, walls +0.25: it relaxes with time"))
BENDS_W = ((B["REST_W"], "as drawn"), (round(B["REST_W"] + 0.4, 2), "walls +0.10"), (round(B["REST_W"] + 1.0, 2), "walls +0.25"), (round(B["REST_W"] - 0.6, 2), "walls -0.15"))
BENDS = BENDS_B
def scaled(r, k, name, limit=None):
    lim = fea.LIMIT[limit] if limit else r["limit_pct"]; e = r["peak_strain_pct"] * k
    return dict(r, name=name, force_N=round(r["force_N"] * k, 3), peak_strain_pct=round(e, 3), peak_stress_MPa=round(r["peak_stress_MPa"] * k, 1), limit_pct=lim, criterion=limit or r["criterion"], margin=round(lim / max(e, 1e-9), 2))
def keep(r):
    out[r["name"]] = r; print(f"   {r['name']:74s} {r['force_N']:6.2f} N  {r['peak_strain_pct']:5.2f} %  ({r['peak_stress_MPa']:5.1f} MPa)  limit {r['limit_pct']} %  x{r['margin']:.1f} {'OK' if r['margin'] >= 1 else '** OVER **'}")
def uy_at(f, x, y):
    m, _, (ux, uy) = f; i = np.argmin(np.hypot(m.p[0] - x, m.p[1] - y)); return float(uy[i])
def arcballs(c, r, a0, a1, step=3.0, rad=2.2, size=0.3):
    n = max(2, int(abs(a1 - a0) * np.pi / 180 * r / step)); return [(c[0] + r * np.cos(np.radians(t)), c[1] + r * np.sin(np.radians(t)), rad, size) for t in np.linspace(a0, a1, n)]
# ---- 1. blade click spring: the rim itself
T_ = B["BL_T"]; R = B["R_OUT"]; bl = fea.section(A + f"blade_PHI{TH}.stl", [0, YF + 1.5, 0], [0, 1, 0], [0, 2]); bl = shapely.affinity.rotate(bl, 90 - (B["DB_A"] + TH), origin=tuple(P))
tip = (P[0], P[1] + R + B["SLIT"] + T_ + B["BUMP"] - 0.02); ra = np.radians(90 - B["BL_ARC"]); root = P + (R + B["SLIT"]) * np.array([np.cos(ra), np.sin(ra)])
r, f = fea.run("blade click spring, per mm", bl, lambda x, y: np.where(np.hypot(x - P[0], y - P[1]) < 5.4, 2.0, 1.0), lambda x, y: np.hypot(x - P[0], y - P[1]) < 4.8, [(tip, (None, -1.0))], h=2.5,
               fine=[(root[0], root[1], 3.5, 0.07)] + arcballs(P, R + B["SLIT"] + T_ / 2, 90 - B["BL_ARC"], 90, step=2.0, rad=2.4, size=0.18))   # v2.18: finer all along the beam: a constant-strain beam peaks anywhere along it
for d, lab in BENDS_B: keep(scaled(r, d, f"blade click spring, tooth pushed in {d} mm ({lab})", "inplane_repeated"))
STOP_B = round(B["SLIT"] + T_ - B["BL_T1"], 2) if B.get("BL_T0", 0) > 0 else B["SLIT"]   # v2.18: the tapered beam keeps its outer face, so its thin tip stands further off the rim
keep(scaled(r, STOP_B, f"blade click spring, squeezed until the rim stops it ({STOP_B} mm)", "inplane_rare"))
pics["blade"] = (f, (root[0] - 3, tip[0] + 3, P[1] + R - 12, P[1] + R + 8), BENDS_B[0][0])
# ---- 2. wheel click spring
T_ = B["WH_T"]; RW = B["WHEEL_R"]; wh = fea.section(A + "wheel_STOP0.stl", [0, YF + 0.75, 0], [0, 1, 0], [0, 2]); wh = shapely.affinity.rotate(wh, 90 - B["WD_A0"], origin=tuple(C))
tipw = (C[0], C[1] + RW + B["SLIT_W"] + T_ + B["BUMP_W"] - 0.05); ra = np.radians(90 - B["WH_ARC"]); rootw = C + (RW + B["SLIT_W"]) * np.array([np.cos(ra), np.sin(ra)])
r, f = fea.run("wheel click spring, per mm", wh, lambda x, y: np.full_like(x, 1.0), lambda x, y: np.hypot(x - C[0], y - C[1]) < 4.2, [(tipw, (None, -1.0))], h=2.0,
               fine=[(rootw[0], rootw[1], 3.5, 0.07)] + arcballs(C, RW + B["SLIT_W"] + T_ / 2, 90 - B["WH_ARC"], 90))
for d, lab in BENDS_W: keep(scaled(r, d, f"wheel click spring, tooth pushed in {d} mm at the top of the ramp ({lab})", "inplane_rare"))
keep(scaled(r, B["SLIT_W"], f"wheel click spring, squeezed until the rim stops it ({B['SLIT_W']} mm)", "inplane_rare"))
pics["wheel"] = (f, (C[0] - 3, C[0] + RW + 5, C[1] + 1, C[1] + RW + 6), BENDS[2][0])
# ---- 3. front plate latch: a leaf in the plate's front face (v2.8), bent outward by the post on its free end.  Side view (z, y): y is the layer direction, so the wall error
#         does not change the leaf's thickness: the section is cut as drawn and only its width (4.6 mm, in the print plane) takes the error
LW = MV["LF_X1"] - MV["LF_X0"] + 2 * W; ZR, ZH, YCF = MV["LF_ZR"], MV["LF_ZH"], MV["Y_CVF"]; LIFT = MV["TOOTH_H"] - MV["LF_DB"]
LS = 1.0 if ZH > ZR else -1.0                                                                      # which way the leaf points from its root: -1 down (v2.8), +1 up (v2.9)
fea.WALL = 0.0; fr = fea.section(A + "front.stl", [(MV["LF_X0"] + MV["LF_X1"]) / 2, 0, 0], [1, 0, 0], [2, 1]); fea.WALL = W; fr = fr.intersection(box(min(MV["LF_ZB"] - 2.5, ZR - 7), YF - 2.6, max(MV["LF_ZB"] + 2.5, ZR + 7), YCF + 0.1))
lth = lambda x, y: np.where((ZR - x) * LS > 0.5, 3 * LW, LW); lfx = lambda x, y: (ZR - x) * LS > 5.5; lfine = [(ZR, YCF - MV["LF_T"], 3.0, 0.07), ((ZR + ZH) / 2, YCF - MV["LF_T"] / 2, 12, 0.25)]; LPT = (ZH, YF - MV["TOOTH_H"] + 0.05)
r, f = fea.run("plate latch leaf, per mm", fr, lth, lfx, [(LPT, (None, 1.0))], h=0.9, fine=lfine, limit="inplane_rare")
# the bump pushes the post along the slide as well, 5 mm behind the leaf: that turns the leaf's end.  How far the post lifts for a push along z, against how far for a push along y:
r2, f2 = fea.run("plate latch leaf, post pushed along the slide, per mm", fr, lth, lfx, [(LPT, (1.0, None))], h=0.9, fine=lfine, limit="inplane_rare")
i2 = np.argmin(np.hypot(f2[0].p[0] - LPT[0], f2[0].p[1] - LPT[1])); KAP = float(f2[2][1][i2]) / r2["force_N"] * r["force_N"]              # lift (mm) per newton along +z, times the leaf's stiffness: a pure number
json.dump(dict(K_y=r["force_N"], kappa_plus_z=KAP, leaf_points=LS), open("build/fea_leaf%s.json" % ("" if not W else "_wall%+.2f" % W), "w")); print("   (a push of 1 N on the post toward +z lifts it as much as %.2f N straight out would)" % KAP)
for d, lab in ((round(LIFT - 0.55, 2), "riding over the bump on a printer 0.15 thin: the plate's feet have 0.55 mm of slack and take it up first"), (round(LIFT - 0.25, 2), "riding over the bump, as drawn"), (LIFT, "riding over the bump with no slack in the feet: as far as it goes")):
    keep(scaled(r, d, f"plate latch leaf, post lifted {d} mm ({lab})", "inplane_rare"))
pics["latch"] = (f, (min(MV["LF_ZB"], ZR) - 4, max(MV["LF_ZB"], ZR) + 4, YF - 3, YCF + 2.5), LIFT)
# ---- 4. back latch finger (3 mm deep; v2.8: nub at its tip, pad 8 mm inboard, sloping down toward its root)
FX0_, FZ1, FT, NUBC, NUBI, PADC, NH, FROOT = MV["F_X0"], MV["F_Z1"], MV["F_T"], (MV["NUB_X0"] + MV["NUB_X1"]) / 2, MV["NUB_X1"], (MV["PAD_X0"] + MV["PAD_X1"]) / 2, MV["NUB_H"], MV["F_X1"] - 1.5
SL = FZ1 - FT - MV["DOOR_TOP"]                                                                    # the slit under the tip
bk = fea.section(A + "back.stl", [0, YRIM - 2.0, 0], [0, 1, 0], [0, 2]); bk = bk.intersection(box(-45, 8, 30, 31)); fix = lambda x, y: (y < 8.5) | (x > 29.5) | (x < -44.5); fine = [(FROOT, FZ1 - MV["F_DROP"] - FT / 2, 4.5, 0.07), (-2, FZ1 - 0.9, 19, 0.3)]
RIBH = values(["RIB_H"])["RIB_H"]; deep = lambda x, y: np.where((x > 1.0) & (y > FZ1 - 2.8), 3.0 + RIBH, 3.0)        # the finger is 3 mm deep (v2.8 had a 2 mm rib near its root; v2.9 has none)
r, f = fea.run("back latch finger, nub pushed down, per mm", bk, deep, fix, [((NUBC, FZ1 + NH), (None, -1.0))], h=1.5, fine=fine)
tip_n = uy_at(f, FX0_ + 0.1, FZ1 - FT) / uy_at(f, NUBC, FZ1 + NH)
for d, lab in ((0.5, "at rest on a printer 0.25 fat: held down by the catch beside the nub; it relaxes"), (NH, "closing the back: as drawn"), (round(NH + 0.5, 2), "closing the back: printer 0.25 fat")): keep(scaled(r, d, f"back latch finger, nub pushed down {d} mm ({lab})", "inplane_rare"))
r, f = fea.run("back latch finger, pad pressed, per mm", bk, deep, fix, [((PADC, H + MV["PAD_UP"]), (None, -1.0))], h=1.5, fine=fine)
nub = -uy_at(f, NUBI, FZ1 + NH); tipd = -uy_at(f, FX0_ + 0.1, FZ1 - FT)
print(f"   (pad pressed 1 mm: the inner end of the nub drops {nub:.2f} mm, the tip {tipd:.2f} mm; nub pushed 1 mm: the tip drops {tip_n:.2f} mm)")
json.dump(dict(nub_per_pad=nub, tip_per_pad=tipd, tip_per_nub_pushed=tip_n, slit=SL - 2 * W, pad_up=MV["PAD_UP"]), open("build/fea_finger%s.json" % ("" if not W else "_wall%+.2f" % W), "w"))
for need, lab in ((NH + 0.1, "as drawn"), (NH + 0.6, "printer 0.25 fat, or the back pushed toward this latch")): keep(scaled(r, need / nub, f"back latch finger, pad pressed until the nub is clear by 0.1 mm ({lab}: pad {need / nub:.2f} mm)", "inplane_rare"))
keep(scaled(r, MV["PAD_UP"], f"back latch finger, pad pressed level with the catch ({MV['PAD_UP']} mm: as far as a flat finger can push it)", "inplane_rare"))
keep(scaled(r, SL / tipd, f"back latch finger, pad pressed until the slit closes (pad {SL / tipd:.2f} mm)", "inplane_rare"))
pics["finger"] = (f, (-25, 20, 19, 31), SL / tipd)
# ---- 5. the catch on the body (v2.8: two posts with a bar between them, rounded where they join the rim, and a 20.6 mm tab that is not).  The section is cut through a post; a knock is shared by all three (28 mm in all).  The body is printed with this tab standing up: weak direction.
bd = fea.section(A + "body.stl", [(MV["ARM_X0"] + MV["ARM_X1"]) / 2, 0, 0], [1, 0, 0], [1, 2]); bd = bd.intersection(box(YRIM - 7, H - 10, YRIM + 5, H + 1))
r, f = fea.run("body catch, knocked sideways, per 0.05 mm", bd, lambda x, y: np.full_like(x, MV["ARM_X1"] - MV["ARM_X0"] + MV["OP_X1"] - MV["OP_X0"] + MV["HORN_X1"] - MV["HORN_X0"]), lambda x, y: x > YRIM + 4.5, [((YRIM - 5.1, H - 1.1), (None, 0.05))], h=0.6, fine=[(YRIM, H - 2.6, 3.0, 0.06)], limit="across_rare", ignore=0.8)
for F in (20.0, 40.0): keep(scaled(r, F / r["force_N"], f"body catch, knocked sideways at its end with {F:.0f} N (back off)", "across_rare"))
pics["tab"] = (f, (YRIM - 7.5, YRIM + 4.5, H - 7.5, H + 0.5), 40.0 / r["force_N"])
bd2 = fea.section(A + "body.stl", [0, 0, H - 1.1], [0, 0, 1], [0, 1]); bd2 = bd2.intersection(box(-24, YRIM - 7, MV["ARM_X1"] + 0.3, YRIM + 6))
r, f = fea.run("body catch, pulled by the latch, per 0.02 mm", bd2, lambda x, y: np.full_like(x, 2.2), lambda x, y: (y > YRIM + 5.5), [((NUBC, YRIM - 3.0 - MV["HORN_GAP"] - 0.05), (None, -0.02))], h=0.6, fine=[(NUBC, YRIM - 3.5, 3.2, 0.06), (MV["OP_X1"], YRIM, 2.0, 0.08), (MV["ARM_X0"], YRIM, 2.0, 0.08)], limit="across_rare", ignore=0.6)
_rv = values(["RIB_X0", "RIB_H"]); _tF = FT + 2 * W; _a1 = _rv["RIB_X0"] - NUBC; _a2 = FROOT - _rv["RIB_X0"]; _I1 = _tF * 27 / 12; _I2 = _tF * (3.0 + _rv["RIB_H"]) ** 3 / 12
FBRK = 2 * 1.7 / (max(_a1 * 1.5 / _I1, (_a1 + _a2) * (3.0 + _rv["RIB_H"]) / 2 / _I2) * 1.2 / fea.E_PLA * 100)          # what a finger passes on when it is bent to twice its yield strain: more than that it cannot pull
keep(scaled(r, FBRK / r["force_N"], "body catch, back pulled off without the pads until its fingers are about to break (%.1f N a latch)" % FBRK, "across_rare"))
# ---- 6. hooked foot of the front plate, and the ledge in the body over it: plate pulled off with 20 and 40 N
xf, x0 = MV["FEET"][0]; FW = MV["FOOT_W"]                                                  # a foot (bottom left: the body is thinnest outside its pocket): its side, its hooked face, its width.  The hooks point down: the section is cut along z
ft = fea.section(A + "front.stl", [xf + FW / 2, 0, 0], [1, 0, 0], [2, 1]); ft = ft.intersection(box(x0 - 2.6, YF - 5.0, x0 + 7, YF + 2.2))
r, f = fea.run("hooked foot, per 0.02 mm", ft, lambda x, y: np.full_like(x, FW), lambda x, y: y > YF + 1.9, [((x0 - 0.85, YF - 1.2), (None, -0.02))], h=0.5, fine=[(x0, YF - 0.6, 2.0, 0.06)], limit="across_rare", ignore=0.45)
for F in (20, 40): keep(scaled(r, F / 4 / r["force_N"], f"hooked foot, plate pulled off with {F} N ({F // 4} N a foot)", "across_rare"))
lg = fea.section(A + "body.stl", [xf + FW / 2, 0, 0], [1, 0, 0], [2, 1]); lg = lg.intersection(box(x0 - 7, YF - 7.2, x0 + 9.95, YF + 0.1))
r, f = fea.run("body ledge, per 0.02 mm", lg, lambda x, y: np.full_like(x, FW + 0.7), lambda x, y: (y < YF - 6.7) | (x < x0 - 6.5) | (x > x0 + 9.5), [((x0 - 1.0, YF - 1.0), (None, 0.02))], h=0.6, fine=[(x0 - 1.0, YF - 0.8, 2.5, 0.06)], limit="across_rare", ignore=0.45)
keep(scaled(r, 10 / r["force_N"], "ledge in the body over a foot, plate pulled off with 40 N", "across_rare"))
# ---- 7. what a child's hands can do to the small parts: beam and shaft formulas (stress concentration 1.5 unless noted)
def formula(name, stress, crit, force=None, note="formula", d=None, p=2):
    """d: the dimension in the print plane that the stress goes with (to the power p); a printer with wall error W makes it d + 2 W"""
    stress = stress * (d / (d + 2 * W)) ** p if (W and d) else stress
    force = 0.0 if force is None else force; e = stress / fea.E_PLA * 100; keep(dict(name=name, force_N=force, peak_strain_pct=round(e, 3), peak_stress_MPa=round(stress, 1), limit_pct=fea.LIMIT[crit], criterion=crit, margin=round(fea.LIMIT[crit] / e, 2), note=note))
def post(name, F, L, b, h, kt=1.5, crit="across_rare", hw=True):                 # hw: h lies in the print plane (wall error applies); False: h is a number of layers
    b_, h_ = b + 2 * W, h + (2 * W if hw else 0.0); formula(name, 6 * F * L / (b_ * h_ * h_) * kt, crit, F, "beam formula")
def torsion(poly, h=0.1):
    """Prandtl stress function on a cross-section: torsion constant J (mm4) and the peak shear stress per unit torque (1/mm3)"""
    from skfem import Basis, ElementTriP1, BilinearForm, LinearForm, condense, solve
    from skfem.helpers import dot, grad
    m = fea.mesh(poly, h=h); b = Basis(m, ElementTriP1()); K = BilinearForm(lambda u, v, w: dot(grad(u), grad(v))).assemble(b); f = LinearForm(lambda v, w: 2.0 * v).assemble(b)
    phi = solve(*condense(K, f, D=m.boundary_nodes())); J = 2 * float(LinearForm(lambda v, w: 1.0 * v).assemble(b) @ phi); g = b.interpolate(phi).grad; return J, float(np.sqrt(g[0] ** 2 + g[1] ** 2).max()) / J
from shapely.geometry import Point as _P
# aperture handle: 6.2 x 11 mm where it leaves the wheel's foot, loaded 4.4 mm higher (the middle of the part that shows); the slot in the plate would catch it sooner
post("aperture handle, knocked across with 30 N", 30, 4.4, 11.0, 6.2)
post("aperture handle, pushed 30 N past the end of its slot", 30, 4.4, 6.2, 11.0)
# shutter rocker.  A press that goes on past the click drives the blade against its stops: the whole torque passes through the arm (8 x 2 mm, lying in the print layers) and through the blade's root
import geom; ARMW, ARMT, FINL = geom.FIN_W, 2.0, geom.FIN_L; RS, HUBR = 23.5, 4.6
flat = lambda frac: geom.lever(B, -B["THETA"] - 1.2, frac)                                   # lever arm of a press when the pressed side is flat, the blade on its stop
chord = lambda r: 2 * r * np.sin(np.radians(B["SPAN"])); sec = lambda T, r, w, t: 6 * (T / RS) * (RS - r) / (t * w * w) * 1.3
root = lambda T: max(sec(T, HUBR, 2 * HUBR, 2.0), sec(T, 10, chord(10), 2.0), sec(T, 14, chord(14), 1.0))
T30, T10 = 30 * flat(1.0), 10 * flat(geom.PRESS); Tk = 40 * (geom.press_point(B, 1.0)[1])
formula("shutter rocker, 30 N on the very tip of the raised side, blade on its stop: the arm", 6 * T30 / (ARMT * ARMW ** 2) * 1.3, "inplane_rare", 30, "torque %.0f N mm through the 8 x 2 mm arm" % T30, d=ARMW)
formula("shutter rocker, the same 30 N: the blade where it meets its hub", root(T30), "inplane_rare", 30, "stop %.1f mm from the pivot; worst of three sections (at the hub, at 10 mm, at 14 mm where the blade thins to 1 mm)" % RS, d=8.5)
formula("shutter rocker, 10 N where the finger falls, every picture: the blade where it meets its hub", root(T10), "inplane_repeated", 10, "a firm press that goes on to the stop, torque %.0f N mm" % T10, d=8.5)
formula("shutter rocker, the raised side knocked sideways with 40 N: the blade where it meets its hub", root(Tk), "inplane_rare", 40, "torque %.0f N mm" % Tk, d=8.5)
T23 = 30 * 8.94                                                                               # v2.3 had no rocker: its tab was pushed sideways 8.94 mm above the pivot (geom.tab of that version)
out["shutter rocker, the same 30 N: the blade where it meets its hub"]["note"] += "; the v2.3 blade (3.9 x 1 mm at its hub) would have reached %.1f %% under the same 30 N on its own tab" % (sec(T23, HUBR, chord(HUBR), 1.0) / fea.E_PLA * 100)
post("shutter rocker, 30 N on the rear edge of one side (the finger is %.1f mm behind the arm)" % (FINL - ARMT / 2), 30, FINL - ARMT / 2, ARMW, ARMT, kt=1.3, crit="inplane_rare", hw=False)
post("shutter rocker, 40 N in the middle of one side", 40, FINL / 2 - ARMT / 2, ARMW, ARMT, kt=1.3, crit="inplane_rare", hw=False)
KH = geom.press_point(B, 1.0)[1] - (B["H"] - B["P_S"][1])                                    # height of the raised tip above the top of the plate
post("shutter rocker, the raised side knocked from the front or the back with 15 N", 15, KH, ARMW, ARMT, kt=1.3, crit="inplane_rare", hw=False)
out["shutter rocker, the raised side knocked from the front or the back with 15 N"]["note"] = "the arm is the weak place for this: 8 x 2 mm, %.1f mm below the knock.  It can be expected to break near 30 N: put a spare shutter in the bag" % KH
# wind knob: two prongs (segments of a 5.8 mm circle) straddle the bar in the cassette's spool; the bar bears on the ends of the slot faces
def fork_case(FR, FG, tag):
    seg = _P(0, 0).buffer(FR, 64).intersection(box(-5, FG / 2, 5, 5)); aa = np.sqrt(FR ** 2 - (FG / 2) ** 2) - 0.3; Js, ts = torsion(seg)
    gx, gy = np.meshgrid(np.arange(-4, 4, 0.02), np.arange(FG / 2, 4, 0.02)); ins = shapely.contains_xy(seg, gx, gy); yc = gy[ins].mean(); Ix = ((gy[ins] - yc) ** 2).sum() * 0.0004
    def fork(name, T, crit):
        Fp = T / (2 * aa); sb = Fp * 1.85 * (yc - FG / 2) / Ix * 1.3; tq = Fp * aa * ts; formula(name, np.sqrt(sb ** 2 + 3 * tq ** 2), crit, round(T / 7.5, 1), "prong as a beam (bending + twist), layers across it; knob torque %.0f N mm, force at the knob's rim" % T); return out[name]
    fork(f"wind knob{tag}, winding a frame back into the cassette, typical (1.5 N of film pull: 15 N mm)", 15, "across_repeated")
    fork(f"wind knob{tag}, winding a frame back, stiffest cassette on a full roll (30 N mm)", 30, "across_repeated")
    r = fork(f"wind knob{tag}, forced with 60 N mm (the other knob held, or the film jammed)", 60, "across_rare"); lim = 60 * fea.LIMIT["across_rare"] / r["peak_strain_pct"]
    r["note"] += "; reaches the limit at %.0f N mm and can be expected to break near %.0f" % (lim, 2 * lim); return lim
FORK_LIMITS = {d: fork_case(d / 2 + W, 2.3 - 2 * W, f" ({d} mm fork{tag})") for d, tag in ((6.6, ""), (6.2, ", a variant for a cassette or a printer where 6.6 will not go in"), (5.8, ", for a tight cassette"))}
# take-up spool: knob, shaft and spool are one piece.  Shaft 11.2 mm, as thick as the core; forcing it at the end of the roll (the film is fixed to the cassette's spool to hold 40 N)
tor = lambda T, d, kt=1.3: np.sqrt(3) * 16 * T / (np.pi * (d + 2 * W) ** 3) * kt
formula("take-up spool, winding the roll on, stiffest cassette (8 N of film pull on a full roll: 80 N mm)", tor(80, 11.2), "across_repeated", 80 / 9, note="solid shaft in torsion, shear between layers; force at the knob's rim")
formula("take-up spool, forced with 300 N mm at the end of the roll (33 N at the knob's rim)", tor(300, 11.2), "across_rare", 300 / 9, note="solid shaft in torsion, shear between layers")
formula("take-up spool, film pulled with 40 N at the end of the roll: the core as a beam between its two bearings", 32 * (40 * 44 / 4) / (np.pi * 11.2 ** 3) * 1.3, "across_rare", 40, "11.2 mm core, 44 mm between the top wall and the floor slot, load in the middle; the 1 mm film slot is ignored", d=11.2, p=3)
RINGH = MV["KN_CZ"][1] - MV["KN_CZ"][0] + MV["KN_CR"] - MV["KN_R"] - 0.4                         # the ring and the part of its cone outside the hole in the wall above it
formula("knob pulled up with 40 N (its ring caught under the top wall, sheared between layers)", np.sqrt(3) * 40 / (2 * np.pi * (MV["KN_R"] + 0.4) * RINGH), "across_rare", 40, "shear through the ring and its cone, %.1f mm high, at the edge of the hole" % RINGH)
# the two blocks on the back that close the knob slots: a wide bar (2.6 mm thick) over a narrower one (2.5 mm), standing up from the back.  Loads with the back off the camera
def block_case(c, r, cr, tag):
    zb = MV["KN_LZ"] + 0.4; tB = MV["H"] - 0.2 - zb; tA = zb - (MV["ZC1"] + 0.3); wB = 2 * (r + MV["KSW"] - 0.4); wA = 2 * cr; L = c[1] - MV["KN_NK"] - 0.4 - MV["Y_RIM"]
    yt = np.sqrt((cr + 0.5) ** 2 - (cr - 1.2) ** 2); Lh = yt - MV["KN_NK"] - 0.4; wh = (r + MV["KSW"] - 0.4) - np.sqrt((r + MV["KN_SC"]) ** 2 - yt ** 2)   # the tip that stands in front of the narrow bar: its length and its width where it leaves that bar
    aA, aB = wA * tA, wB * tB; zc = (aA * tA / 2 + aB * (tA + tB / 2)) / (aA + aB); Ix = wA * tA ** 3 / 12 + aA * (zc - tA / 2) ** 2 + wB * tB ** 3 / 12 + aB * (tA + tB / 2 - zc) ** 2
    Iz = (tB * wB ** 3 + tA * wA ** 3) / 12
    formula(f"block that closes the {tag} slot, knocked sideways at its end with 30 N (back off)", 30 * L / (Iz / (wB / 2)) * 1.5, "across_rare", 30, "the whole block as a beam %.1f mm long, %.1f mm wide; layers across it" % (L, wB), d=wB)
    formula(f"block that closes the {tag} slot, pushed up or down at its end with 30 N (back off)", 30 * L / (Ix / max(zc, tA + tB - zc)) * 1.5, "across_rare", 30, "the whole block as a beam %.1f mm long, %.1f mm thick; layers across it" % (L, tA + tB), d=tA + tB)
    n = f"one tip of the {tag} block, struck up or down with 15 N (back off)"
    formula(n, 6 * 15 * Lh / (wh * tB ** 2) * 1.5, "across_rare", 15, "the tip stands %.1f mm in front of the lower bar, %.1f mm wide and %.1f mm thick there; layers across it" % (Lh, wh, tB), d=tB)
    out[n]["note"] += "; it can be expected to break near %.0f N" % (2 * 15 * fea.LIMIT["across_rare"] / out[n]["peak_strain_pct"])
block_case(MV["SPOOL"], MV["SP_KR"], MV["SP_KCR"], "take-up spool's"); block_case(MV["CASS"], MV["KN_R"], MV["KN_CR"], "wind knob's")
# frame wheel and its fork.  The fork is one plate 15.8 mm wide and 4.1 mm thick standing 13 mm from the back; the wheel's axis is 8.4 mm from the back.
# Its prong on the spool side is joined to the foot of the spool's block; the one on the latch side stands alone from 3.4 mm behind the wheel's axis
FKW = MV["RB_HWL"] + MV["RB_HW"]; FKT = MV["RB_Z"][1] - MV["RB_Z"][0]; SEATT = MV["RB_Z"][1] - MV["RB_FLOOR"]; PR = MV["RB_HWL"] - MV["RB_SEAT"]
post("fork that holds the frame wheel, 10 N on the wheel across it", 10, 8.4, FKW, FKT)
post("fork that holds the frame wheel, wheel pulled out against its lips with 10 N (5 N a lip)", 5, 3.0, SEATT, PR)
def _prong():                                                      # the free prong at the wheel's axis, where it is thinnest: the seat part over the floor part
    w1, t1, w2, t2 = PR, SEATT, MV["RB_HWL"] - MV["RB_GAP"] / 2, MV["RB_FLOOR"] - MV["RB_Z"][0]; a1, a2 = w1 * t1, w2 * t2; x1, x2 = w1 / 2, w2 / 2; xc = (a1 * x1 + a2 * x2) / (a1 + a2)
    I = t1 * w1 ** 3 / 12 + a1 * (xc - x1) ** 2 + t2 * w2 ** 3 / 12 + a2 * (xc - x2) ** 2; return I / max(xc, w2 - xc), w1, w2
SP, W1, W2 = _prong()
n = "fork's free prong, knocked sideways at its tip with 15 N (back off)"
formula(n, 15 * MV["RB_UP"] / SP * 1.5, "across_rare", 15, "the prong at the wheel's axis: %.1f mm thick in its upper part, %.1f in its lower; the knock %.1f mm further out; layers across it" % (W1, W2, MV["RB_UP"]), d=W1)
# the wide bar over the frame wheel's slot: 2.2 mm thick, it stands 3 mm in front of the narrow bar under it (the lifted collar passes under it)
FBT = MV["H"] - 0.2 - MV["FW_LZ"] - 0.4; FBW = 2 * (MV["SHAFT_R"] + MV["FW_KSW"] - 0.4); FBL = MV["COLLAR_R"] + 0.5 - MV["FW_NK"] - 0.4
n = "wide bar that wraps the frame wheel's neck, pushed up or down at its end with 30 N (back off)"
post(n, 30, FBL, FBW, FBT); out[n]["note"] = "a plate %.1f mm wide and %.1f mm thick standing %.1f mm in front of the bar under it; layers across it; it can be expected to break near %.0f N" % (FBW, FBT, FBL, 2 * 30 * fea.LIMIT["across_rare"] / out[n]["peak_strain_pct"])
formula("frame wheel, 10 N of film pull on its drum: the neck", 32 * (10 * 5.5) / (np.pi * 6.0 ** 3) * 1.3, "across_rare", 10, "6 mm neck, the drum's middle 5.5 mm below the fork's floor; layers across it", d=6.0, p=3)
post("frame wheel, one tooth pulled by the film with 5 N", 5, 0.6, 1.5, 1.5, crit="inplane_repeated")
out["frame wheel, one tooth pulled by the film with 5 N"]["note"] = "a tooth is 1.5 mm wide at its root, 1.5 mm long and 1.2 mm high, and lies in the layers.  The film turns the wheel; the wheel drives nothing"
# ---- 7b. v2.10: the side lip on each foot and the strip of the body's skin over it.  They hold the plate on only while it is pushed up; then a pull on the plate lands on four lips.
SV = values(["SIDE_L", "SIDE_G", "FOOT_D", "FOOT_L", "PK_X"]); slz = SV["FOOT_L"] - 0.6; slr = SV["FOOT_D"] - 0.15                # the lip: how long it is (along the foot), how thick at its root
for Fk in (40, 250):
    f1 = Fk / 4; arm = SV["SIDE_L"] / 2 + 0.5                                                                                        # the load sits about half-way along the lip
    formula(f"side lip of a foot, the pushed-up plate pulled off with {Fk} N ({f1:.0f} N a lip)", 6 * f1 * arm / (slz * slr ** 2) * 1.5, "across_rare", Fk, "a wedge %.1f mm long, %.1f mm thick at its root and %.1f mm long along the foot; layers across it" % (SV["SIDE_L"], slr, slz))
    tk = 0.05 + SV["SIDE_L"] + 0.3                                                                                                    # the skin over it: a wedge too, this thick where it joins the body
    formula(f"strip of the body's skin over a side lip, the pushed-up plate pulled off with {Fk} N ({f1:.0f} N a strip)", 6 * f1 * arm / (slz * tk ** 2) * 1.5, "inplane_rare", Fk, "a wedge %.1f mm thick where it joins the body, in the body's first layers; the load lies in the layers" % tk)
# ---- 4b. the same finger bent SIDEWAYS (front to back): what happens when the back is pulled off without pressing the pads.  The bar holds the nub; the back drags the finger's root away.
RV = values(["RIB_X0", "RIB_H"]); tF = FT + 2 * W; a1 = RV["RIB_X0"] - NUBC; a2 = FROOT - RV["RIB_X0"]; I1 = tF * 3.0 ** 3 / 12; I2 = tF * (3.0 + RV["RIB_H"]) ** 3 / 12
KY = 1 / (a1 ** 3 / (3 * fea.E_PLA * I1) + ((a1 + a2) ** 3 - a1 ** 3) / (3 * fea.E_PLA * I2))
print(f"   (sideways the finger gives {KY:.2f} N/mm at its nub; without its rib it would give {3 * fea.E_PLA * I1 / (a1 + a2) ** 3:.2f})")
for Ftot in (3.0, 5.0, 10.0):
    Ff = Ftot / 2; sg = max(Ff * a1 * 1.5 / I1, Ff * (a1 + a2) * (3.0 + RV["RIB_H"]) / 2 / I2) * 1.2
    formula(f"back pulled off with {Ftot:.0f} N without pressing the pads ({Ff:.1f} N a finger): the finger bent front to back", sg, "inplane_rare", Ftot, "beam formula: %s; the back comes away %.1f mm (the light trap overlaps 1.9)" % ("3 mm deep from the nub to the rib, %.0f mm deep from there to the root" % (3.0 + RV["RIB_H"]) if RV["RIB_H"] else "the finger is 3 mm deep all the way", 0.4 + Ff / KY))
FJ = "build/fea_finger%s.json" % ("" if not W else "_wall%+.2f" % W); fj = json.load(open(FJ)); fj.update(sideways_N_per_mm=KY, sideways_strain_pct_per_N=max(a1 * 1.5 / I1, (a1 + a2) * (3.0 + RV["RIB_H"]) / 2 / I2) * 1.2 / fea.E_PLA * 100); json.dump(fj, open(FJ, "w"))
json.dump(out, open("build/fea.json" if not W else "build/fea_wall%+.2f.json" % W, "w"), indent=1)
if W: sys.exit(0)                                                   # the picture and the summary are for the model as drawn
import os
old = pickle.load(open("build/fea_old.pkl", "rb")) if os.path.exists("build/fea_old.pkl") else None      # the v2 tongue, kept for the before-and-after picture
sc = lambda key: (pics[key][0][0], pics[key][0][1] * pics[key][2], (pics[key][0][2][0] * pics[key][2], pics[key][0][2][1] * pics[key][2]))
g = lambda *has: [v for k, v in out.items() if all(h in k for h in has)][0]["peak_strain_pct"]
panels = ([("BEFORE  curled tongue on the blade,\ntypical printer: 1.33 % where it starts", old["old"], (old["P"][0] - 6, old["P"][0] + 13, old["P"][1] - 1, old["P"][1] + 13), 1.0)] if old else []) + [
          ("Blade: the rim is the spring; pressed\n(1.8 mm, every printer): %.2f %%" % g("blade click", "pressed"), sc("blade"), pics["blade"][1], 1.0),
          ("Aperture wheel: rim spring,\nas drawn: %.2f %%" % g("wheel click", "as drawn"), sc("wheel"), pics["wheel"][1], 1.0),
          ("Front plate latch: the leaf lifted\nas far as it goes: %.2f %%" % g("plate latch", "as far"), sc("latch"), pics["latch"][1], 1.0),
          ("Back latch, pad pressed until its slit\ncloses: %.2f %%" % g("back latch finger, pad", "slit closes"), sc("finger"), pics["finger"][1], 1.0),
          ("Catch on the body, knocked sideways\nwith 40 N: %.2f %% (limit 0.5 across layers)" % g("body catch, knocked", "40 N"), sc("tab"), pics["tab"][1], 1.0)]
fea.picture("build/fea.png", panels, 2)
