"""Two films of ONE-135 moving, drawn from the meshes tools/motion.py measures (scad/motion.scad shows each mesh where a matrix puts it).
  guide : every step of the build and of use as a moving instruction book (the words are the guide's own: tools/steps.py)
  proof : every moving part through its travel, with what tools/motion.py measured beside it
One encoded file per step, joined without re-encoding; each step's file is a clip of its own.
    python3 tools/motionfilm.py guide|proof [stills | clip-key ...]"""
import os, sys, json, math, hashlib, subprocess, time, numpy as np, skia, concurrent.futures as cf
from PIL import Image
sys.path.insert(0, "tools"); import kin; from kin import V, TH, XE, LIFT, PITCH, RP, Tr, RZ
import film as FL; from film import text, para, wrap, rrect, col, layer, ease, ramp, clamp, line, dot, stroke, fill, W, H, FPS, BG, INK, MUTE, PANEL, LINE, ORANGE, YEL, CYAN, RED, GREEN, WHITE
import steps as ST
ROOT = os.getcwd(); OUT = "build/motion"; FRD = OUT + "/fr"; MS = OUT + "/mesh"; [os.makedirs(d, exist_ok=True) for d in (FRD, MS)]
MODEL = FL.MODEL; I = np.eye(4); W1, W2 = V["WPOS"][1], V["WPOS"][2]; SL = V["SLIDE"]; RO, SP, CA = V["ROLLER"], V["SPOOL"], V["CASS"]; CW, CH, SS = 1240, 930, 1.5; CX, CY = 40, 104
COL = dict(body=[0.22, 0.23, 0.26], back=[0.80, 0.81, 0.83], plate1=[0.58, 0.30, 0.78], slide1=[0.13, 0.13, 0.15], pinring=[0.20, 0.21, 0.24], front=[0.93, 0.46, 0.13], blade=[0.15, 0.62, 0.60], wheel=[0.95, 0.78, 0.20], spool=[0.85, 0.20, 0.18], knob=[0.35, 0.72, 0.25], roller=[0.22, 0.52, 0.86],
           lens=[0.55, 0.80, 0.95], cassette=[0.90, 0.68, 0.10], film=[0.50, 0.32, 0.20], arrow=[0.98, 0.98, 0.96])
PLATE_IN = (2, 8, 0, 58, 0, 28, 300); FRONT = (0, 20, 6, 66, 0, 200, 250); FRONT_NEAR = (12, 40, 0, 62, 0, 232, 280); REAR_FAR = (4, -26, 0, 46, 0, 24, 450); REAR_TOP = (4, -22, 0, 46, 0, 24, 410); FACE = (0, 12, 2, 70, 0, 205, 300)
TOP = (0, 0, 8, 52, 0, 28, 320); B3 = (0, 0, 2, 64, 0, 28, 400); B8 = (20, 4, 6, 58, 0, 208, 250); L2 = (-45, 10, 12, 70, 0, 28, 230); S2 = (0, 8, 20, 30, 0, 0, 300); S3 = (6, 20, 10, 62, 0, 205, 285)
def mesh(n): return f"{ROOT}/{kin.path(n)}"
# the frame wheel in two meshes, so that the arrowhead on its dial can be drawn white as it is printed
RB, RA = f"{ROOT}/{MS}/roller_body.stl", f"{ROOT}/{MS}/roller_arrow.stl"
if not os.path.exists(RB) or os.path.getmtime(RB) < os.path.getmtime(kin.path("roller")):
    kin.save(kin.man("roller").trim_by_plane([0, 0, -1], -V["DIAL_Z"][1]), RB); kin.save(kin.man("roller").trim_by_plane([0, 0, 1], V["DIAL_Z"][1]), RA)
# ---------------------------------------------------------------- the film, as a mesh for each moment
ROLL0 = kin.roll_radius(0); _, _i0 = kin.film(ROLL0, adv=0.0, path=kin.film_pts_closing(0.0, ROLL0, step=2.0)); U0 = _i0["u_mid"]; OPEN_D = 48.0
def filmmesh(roll=ROLL0, adv=0.0, d=0.0, upto=None):
    """film with its perforations: take-up roll of radius roll, moved adv mm toward the take-up, the back d mm from home, drawn only as far as upto mm from the cassette's lip"""
    k = hashlib.sha1(json.dumps([round(roll, 3), round(adv, 3), round(d, 3), None if upto is None else round(upto, 2), os.path.getmtime("tools/kin.py")]).encode()).hexdigest()[:14]; f = f"{ROOT}/{MS}/film_{k}.stl"; j = f[:-4] + ".json"
    if not os.path.exists(j):
        P, S, info = kin.film_pts_closing(d, roll, step=2.0)
        if upto is not None:
            u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; n = max(2, int(np.searchsorted(u, upto))); q = P[:n].copy()
            if n < len(P): q = np.vstack([q, P[n - 1] + (P[n] - P[n - 1]) * clamp((upto - u[n - 1]) / (u[n] - u[n - 1]))])
            P, S = q, (S[:n] + [S[min(n, len(S) - 1)]])[:len(q)]
        m, info = kin.film(roll, adv=adv, path=(P, S, info), u0=U0, with_roll=upto is None); kin.save(m, f)
        json.dump(dict(phase=float(kin.wheel_phase(info)) if info["wrap_deg"] > 0.5 and upto is None else 0.0, wrap=float(info["wrap_deg"])), open(j, "w"))
    return f, json.load(open(j))
# ---------------------------------------------------------------- one picture
def sc(cam, body=None, front=None, blade=None, wheel=None, lens=None, spool=None, knob=None, roller=None, back=None, cass=None, film=None, phi=TH, wa=W2, alpha=None, rot=(0, 0, 0), arrows=(), turns=()):
    alpha = alpha or {}; P = []
    def add(f, c, M, n): P.append([f, [*COL[c], alpha.get(n, 1.0)], [round(float(x), 5) for x in np.asarray(M)[:3, :].ravel()]])
    if body is not None: add(mesh("body"), "body", body, "body")
    if front is not None: add(mesh("front"), "front", front, "front")
    if blade is not None: add(mesh("bladeB"), "blade", blade @ kin.blade(phi), "blade")
    if wheel is not None: add(mesh("wheelB"), "wheel", wheel @ kin.wheel(wa), "wheel")
    if lens is not None: add(mesh("lens"), "lens", lens, "lens")
    if spool is not None: add(mesh("spool"), "spool", spool, "spool")
    if knob is not None: add(mesh("knob"), "knob", knob, "knob")
    if cass is not None: add(mesh("cassette"), "cassette", cass, "cass")
    if film is not None: add(film, "film", I, "film")
    if roller is not None: add(RB, "roller", roller, "roller"); add(RA, "arrow", roller, "roller")
    if back is not None: add(mesh("back"), "back", back, "back")
    P.sort(key=lambda p: -p[1][3])                                    # see-through parts are drawn last
    return dict(P=P, cam=[round(float(x), 3) for x in cam], rot=list(rot), arrows=[list(map(list, a)) for a in arrows], turns=[list(t) for t in turns])
def plate(M=I, lens=True): return dict(front=M, blade=M, wheel=M, **(dict(lens=M) if lens else {}))
def lerp(a, b, e): return tuple(x + (y - x) * e for x, y in zip(a, b))
def seg(u, a, b): return ease(ramp(u, a, b))
def fkey(s): return hashlib.sha1(json.dumps(s, sort_keys=True).encode()).hexdigest()[:16]
def render(s):
    k = fkey(s); png = f"{FRD}/{k}.png"
    if os.path.exists(png): return png
    scad = f"{FRD}/{k}.scad"; raw = f"{FRD}/{k}.raw.png"
    open(scad, "w").write("include <%s/scad/motion.scad>\nP = %s;\nROT = %s;\nARROWS = %s;\nTURNS = %s;\n" % (ROOT, json.dumps(s["P"]), json.dumps(s["rot"]), json.dumps(s["arrows"]), json.dumps(s["turns"])))
    for attempt in range(4):                                           # now and then the picture comes back unfinished: ask again
        if os.path.exists(raw): os.remove(raw)
        r = subprocess.run(["openscad", "-o", raw, f"--imgsize={int(CW * SS)},{int(CH * SS)}", "--colorscheme=Tomorrow", "--projection=p", "--camera=" + ",".join(str(c) for c in s["cam"]), scad], capture_output=True, text=True, env=dict(os.environ, DISPLAY=DISP), timeout=600)
        try: im = Image.open(raw).convert("RGB"); break
        except Exception: im = None; time.sleep(0.5)
    if im is None: print(r.stderr[-800:]); raise RuntimeError("render failed")
    a = np.asarray(im).copy(); bg = a[0, 0].astype(int); a[np.abs(a.astype(int) - bg).sum(2) < 6] = 255
    Image.fromarray(a).resize((CW, CH), Image.LANCZOS).save(png + ".tmp.png"); os.replace(png + ".tmp.png", png); os.remove(raw); os.remove(scad); return png
DISP = ":97"; _xv = None
def xstart():
    global _xv
    if _xv is None: _xv = subprocess.Popen(["Xvfb", DISP, "-screen", "0", "1280x1024x24", "-nolisten", "tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
def xstop():
    if _xv is not None: _xv.terminate()
# ---------------------------------------------------------------- the moves (u runs 0 -> 1 over each)
def tri(x): return 1 - abs(2 * clamp(x) - 1)                          # there and back
BASE = dict(body=I, **plate())                                          # body with its front plate, shutter, aperture wheel and lens
RK_R, RK_L = [[24.5, 24.5, 58], [24.5, 24.5, 41]], [[7.5, 24.5, 58], [7.5, 24.5, 41]]      # an arrow onto the raised side of the rocker: on the right when the shutter stands at +TH, on the left at -TH
def press(u, a, b, d=.035):
    """the shutter through two presses, at u = a and u = b: it stays where each press leaves it (nothing springs back).  Returns its angle and the arrow to draw just before each press."""
    phi = TH - 2 * TH * ramp(u, a, a + d) + 2 * TH * ramp(u, b, b + d); return phi, ([RK_R] if a - .16 <= u < a else [RK_L] if b - .16 <= u < b else [])
def c_b1(u): e = seg(u, 0, .36); phi, ar = press(u, .56, .82); return sc(PLATE_IN, front=I, blade=Tr([0, -38 * (1 - e), 0]), phi=phi, arrows=ar)
def stops(u, a, b):
    """the aperture wheel from the large hole to the small one and back, resting at each click"""
    q = ramp(u, a, b); return W2 + (W1 - W2) * seg(q, .04, .18) + (0 - W1) * seg(q, .30, .44) + (W1 - 0) * seg(q, .58, .72) + (W2 - W1) * seg(q, .84, .98)
def c_b2(u): e = seg(u, 0, .36); return sc(PLATE_IN, front=I, blade=I, wheel=Tr([0, -38 * (1 - e), 0]), wa=stops(u, .46, 1))
BOX = dict(body=I, spool=I, knob=I, roller=I, back=I)                # BUILD 1 to 4: the dark box
def boxm(M): return dict(body=M, spool=M, knob=M, roller=M, back=M)
def c_b3(u): e = seg(u, 0, 1); return sc(B3, **boxm(Tr([0, -40 * (1 - e), 0])), **plate(Tr([-XE, 0, SL]), lens=False), rot=(-90, 0, 0))
def c_b3b(u): e = seg(u, 0, 1); return sc(FRONT, **BOX, **plate(Tr([-XE * (1 - e), 0, SL]), lens=False))
def c_b3c(u): e = seg(u, 0, 1); return sc(FRONT, **BOX, **plate(Tr([0, 0, SL * (1 - e)]), lens=False))
def c_b4(u): e = seg(u, 0, 1); return sc(FRONT_NEAR, **BOX, **plate(lens=False), lens=Tr([0, 34 * (1 - e), 0]))
def c_b6(u): return sc(REAR_FAR, body=I, spool=Tr([0, -44 * (1 - seg(u, 0, .5)), 0]) @ RZ(SP, 360 * seg(u, .62, 1)))
def c_b7(u): return sc(REAR_FAR, body=I, spool=I, knob=Tr([0, -40 * (1 - seg(u, 0, .5)), 0]) @ RZ(CA, -360 * seg(u, .62, 1)))
def c_b8(u): return sc(B8, back=I, roller=Tr([0, 26 * (1 - seg(u, 0, .4)), LIFT * (1 - seg(u, .48, .7))]) @ RZ(RO, 360 * seg(u, .78, 1)))
def c_b9(u, out=False, full=False): e = seg(u, 0, 1); e = e if not out else 1 - e; M = Tr([0, -48 * (1 - e), 0]); return sc(REAR_FAR, **(BASE if full else dict(body=I)), spool=I, knob=I, back=M, roller=M)
def c_l1(u): return c_b9(u, True, True)
def c_l2(u): return sc(L2, cass=I, knob=Tr([0, 0, 26 * (1 - seg(u, 0, .55))]) @ RZ(CA, -200 * seg(u, .68, 1)))
def c_l3(u): M = Tr([0, -46 * (1 - seg(u, 0, 1)), 0]); return sc(REAR_TOP, **BASE, spool=I, cass=M, knob=M)
_open = None
def open_len():
    global _open
    if _open is None: P, _, _ = kin.film_pts_closing(OPEN_D, ROLL0, step=2.0); _open = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
    return _open
def c_l4(u):
    g = seg(u, 0, .58); t = seg(u, .68, 1); f, _ = filmmesh(ROLL0, adv=37.0 * t, d=OPEN_D, upto=None if g >= 1 else 16 + (open_len() - 16) * g)
    return sc(REAR_TOP, **BASE, spool=RZ(SP, 360 * t), cass=I, knob=RZ(CA, 80 * t), film=f)
def c_l5(u): d = OPEN_D * (1 - seg(u, 0, 1)); f, i = filmmesh(ROLL0, adv=37.0, d=d); M = Tr([0, -d, 0]); return sc(REAR_TOP, **BASE, spool=I, cass=I, knob=I, film=f, back=M, roller=M @ RZ(RO, i["phase"] + kin.wheel_turn(37.0)))
def wound(adv, back_alpha=0.22, cam=REAR_TOP, hide_back=False):
    """the camera with adv mm of film wound onto the take-up (from the 37 mm that the first turn took)"""
    n = 60; s = np.linspace(0, adv, n); y = 1 / np.array([kin.roll_radius(x) for x in s]); ang = float(np.degrees(np.sum((y[1:] + y[:-1]) / 2 * np.diff(s)))) if adv > 0 else 0.0
    roll = kin.roll_radius(adv); f, i = filmmesh(roll, adv=37.0 + adv, d=0.0)
    return sc(cam, **BASE, spool=RZ(SP, 360 + ang), cass=I, knob=RZ(CA, 80 + float(np.degrees(adv / 9.0))), film=f, roller=RZ(RO, i["phase"] + kin.wheel_turn(37.0 + adv)), back=None if hide_back else I, alpha=dict(back=back_alpha))
def c_l6(u): return wound(38.0 * seg(u, 0, .38) + (1500.0 - 38.0) * ramp(u, .42, 1) ** 1.6)
def c_s1(u): wa = W2 + (W1 - W2) * seg(u, .08, .26) + (0 - W1) * seg(u, .38, .56) + (W2 - 0) * seg(u, .72, .96); return sc(FACE, **BASE, spool=I, knob=I, roller=I, back=I, wa=wa)
def c_s2(u): return sc(lerp((0, 0, 14, 52, 0, 16, 380), S2, seg(u, 0, 1)), **BASE, spool=I, knob=I, roller=I, back=I)
def c_s3(u): phi, ar = press(u, .30, .72); return sc(S3, **BASE, spool=I, knob=I, roller=I, back=I, phi=phi, arrows=ar)
def c_s4(u): e = seg(u, 0, 1); return sc(TOP, **BASE, spool=I, knob=RZ(CA, -360 * 38.0 / (2 * math.pi * 9.0) * e), roller=RZ(RO, 360 * e), back=I)
def c_o1(u): return sc(TOP, **BASE, spool=I, knob=RZ(CA, -1500 * ramp(u, 0, 1)), roller=RZ(RO, 500 * seg(u, 0, .45)), back=I)
def c_o2(u):
    M = Tr([0, -48 * seg(u, 0, .32), 0]); K = Tr([0, -46 * seg(u, .38, .68), 0]); return sc(REAR_TOP, **BASE, spool=I, back=M, roller=M, cass=K, knob=K @ Tr([0, 0, 26 * seg(u, .76, 1)]))
CLICKS = dict(b1=(.595, .855), b2=(.56, .70, .86, .99), b3c=(1.0,), b9=(1.0,), l5=(1.0,), s1=(.26, .56, .96), s3=(.335, .755))      # where in each move something clicks (as a share of the move)
MOVE = dict(b1=(c_b1, 6.0), b2=(c_b2, 7.0), b3=(c_b3, 2.6), b3b=(c_b3b, 1.8), b3c=(c_b3c, 1.4), b4=(c_b4, 2.2), b6=(c_b6, 4.6), b7=(c_b7, 4.6), b8=(c_b8, 5.6), b9=(c_b9, 2.6), l1=(c_l1, 2.6), l2=(c_l2, 3.6), l3=(c_l3, 2.6), l4=(c_l4, 5.6), l5=(c_l5, 3.2),
            l6=(c_l6, 9.0), s1=(c_s1, 5.6), s2=(c_s2, 3.6), s3=(c_s3, 4.0), s4=(c_s4, 3.6), o1=(c_o1, 6.0), u1=(c_o2, 6.0))
SECCOL = {"BUILD": col("e8651a"), "FILM IN": col("2f9e5e"), "PHOTOS": col("3d8fd6"), "FILM OUT": col("9a62c7")}
def guide_clips(voice=True):
    """every step of the guide as a clip named by the step (b1 ... o2).  With the voice on, each step is as long as its three lines need: what to do, what to check, why."""
    import voice as VC
    out = []; cnt = {}
    for s in ST.STEPS: cnt[s["sec"]] = cnt.get(s["sec"], 0) + 1
    def lines(tx): f, d = VC.say(tx); return f, d
    for s in ST.STEPS:
        img = "o1" if (s["sec"], s["n"]) == ("FILM OUT", 1) else s["img"]; fn, md = MOVE[img]; t0 = 1.1; cl = dict(key=ST.code(s), img=img, kind="step", step=s, of=cnt[s["sec"]], fn=fn, md=md, t0=t0)
        if voice:
            f, d = lines(s["do"]); L = [(0.5, f)]; t = 0.5 + d + 0.45; tc = round(max(t, t0 + md * .55), 2); f, d = lines(s["check"]); L.append((tc, f)); t = tc + d + 0.6; tw = None
            if s["why"]: tw = round(t, 2); f, d = lines(s["why"]); L.append((tw, f)); t = tw + d
            cl.update(lines=L, t_check=tc, t_why=tw, dur=math.ceil(max(t + 1.0, t0 + md + 2.0) * 10) / 10)
        else: words = len((s["do"] + " " + s["check"]).split()); cl["dur"] = round(max(md + 4.0, 3.4 + words / 2.7 + len(s["why"].split()) / 3.4), 1)
        cl["loops"] = min(3, max(1, int((cl["dur"] - t0 - 0.8) // (md + HOLD)))); out.append(cl)
    ti = dict(key="title", kind="title", dur=5.0); en = dict(key="end", kind="end", dur=8.0)
    if voice:
        f, d = lines("Curve thirty-five. Build it, load it, take pictures, unload it. Twenty-two steps."); ti.update(lines=[(0.5, f)], dur=math.ceil((d + 1.6) * 10) / 10)
        f, d = lines("That is the whole camera. Eight printed parts, one lens, one film. No screws, no glue, no tools."); en.update(lines=[(0.6, f)], dur=math.ceil((d + 2.6) * 10) / 10)
    return [ti] + out + [en]
# ---------------------------------------------------------------- drawing a frame
def base(c, head, sub, i, n, t, dur):
    c.clear(BG); text(c, head, CX, 62, 30, INK, 700); text(c, sub, W - 40, 62, 22, MUTE, 500, "r")
    x0, x1 = CX, W - 40; line(c, x0, H - 26, x1, H - 26, LINE, 4); line(c, x0, H - 26, x0 + (x1 - x0) * (i + clamp(t / dur)) / n, H - 26, ORANGE, 4)
def card(c, png, a=1.0):
    with layer(c, a):
        sh = fill(col("000000"), 0.5); sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)); c.drawRoundRect(skia.Rect.MakeXYWH(CX, CY + 8, CW, CH), 20, 20, sh)
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(CX, CY, CW, CH), 20, 20), True); c.drawImage(skia.Image.open(png), CX, CY, skia.SamplingOptions(), skia.Paint()); c.restore()
HOLD = 2.4                                                             # a long step plays its move again after this long at rest
def cyc(cl, t): c_ = cl["md"] + HOLD; k = min(int(max(t - cl["t0"], 0) // c_), cl.get("loops", 1) - 1); return k, t - cl["t0"] - k * c_      # which playing of the move, and the time within it
def u_of(cl, t): return ramp(cyc(cl, t)[1], 0, cl["md"])
def draw_guide(c, cl, i, n, t):
    base(c, "CURVE 35  ·  build and use", MODEL + "  ·  nothing here has been printed yet: this is the model moving", i, n, t, cl["dur"])
    if cl["kind"] == "title":
        a = ease(ramp(t, 0, .5)); text(c, "CURVE 35", W / 2, 440, 120, INK, 800, "c", a); text(c, "Build it, load it, shoot it, unload it", W / 2, 530, 46, INK, 500, "c", a); text(c, "22 steps, drawn from the model", W / 2, 610, 30, MUTE, 500, "c", a); return
    if cl["kind"] == "end":
        a = ease(ramp(t, 0, .5)); text(c, "That is the whole camera.", W / 2, 440, 72, INK, 700, "c", a); text(c, "Eight printed parts, one lens, one film. No screws, no glue, no tools.", W / 2, 520, 36, INK, 500, "c", a)
        text(c, "Each step in this film is also its own clip, for a lesson or a build page.", W / 2, 600, 28, MUTE, 500, "c", a); return
    s = cl["step"]; k, tau = cyc(cl, t); X = CX + CW + 44; Wd = W - 40 - X; sc_ = SECCOL[s["sec"]]
    if k >= 1 and tau < .4: card(c, render(cl["fn"](1.0))); card(c, render(cl["fn"](u_of(cl, t))), ease(ramp(tau, 0, .4)))      # the move starts again: fade from its end to its start
    else: card(c, render(cl["fn"](u_of(cl, t))))
    if k >= 1 and tau < cl["md"]: rrect(c, CX + 24, CY + 24, 132, 44, 22, col("11161b"), .85); text(c, "once more", CX + 90, CY + 54, 22, WHITE, 600, "c")
    rrect(c, X, CY, 22 + FL.font(24, 700).measureText(s["sec"]) + 22, 44, 22, sc_); text(c, s["sec"], X + 22, CY + 31, 24, WHITE, 700); text(c, f"step {s['n']} of {cl['of']}", X + Wd, CY + 31, 24, MUTE, 500, "r")
    text(c, str(s["n"]), X, CY + 150, 96, sc_, 800); a = ease(ramp(t, .15, .7)); h = para(c, s["do"], X, CY + 214, 31, Wd, INK, 500, a=a, lh=1.36); y = CY + 214 + h + 18
    tc = cl.get("t_check", cl["t0"] + cl["md"] * .55); b = ease(ramp(t, tc, tc + .5)); ls = wrap(s["check"], 27, 500, Wd - 78); bh = len(ls) * 27 * 1.36 + 36
    with layer(c, b):
        rrect(c, X, y, Wd, bh, 16, PANEL, outline=col("2f9e5e"), ow=2); p = skia.Path(); p.moveTo(X + 22, y + 34); p.lineTo(X + 32, y + 45); p.lineTo(X + 50, y + 22); c.drawPath(p, stroke(col("3fbf73"), 5))
        for k, l in enumerate(ls): text(c, l, X + 66, y + 41 + k * 27 * 1.36, 27, INK, 500)
    if s["why"]:
        tw = cl.get("t_why") or cl["t0"] + cl["md"] + .2; w_ = ease(ramp(t, tw, tw + .6)); text(c, "WHY", X, y + bh + 48, 20, sc_, 800, a=w_); para(c, s["why"], X, y + bh + 82, 24, Wd, col("b9c2cc"), 500, a=w_, lh=1.38)
    for uc in CLICKS.get(cl["img"], ()):                                   # a click where it happens in the move
        v = FL.window(tau, uc * cl["md"] - .03, uc * cl["md"] + 1.0, .1)
        if v > 0: w = FL.font(40, 800).measureText("CLICK"); rrect(c, CX + CW / 2 - w / 2 - 18, CY + 30, w + 36, 58, 29, col("e8651a"), v); text(c, "CLICK", CX + CW / 2, CY + 72, 40, WHITE, 800, "c", v)
    for bx, by, word in ([] if cl["img"] in CLICKS else s["bursts"]):
        v = FL.window(tau, cl["md"] - .1, cl["md"] + 1.5, .12)
        if v > 0: px, py = CX + bx * CW, CY + by * CH; w = FL.font(40, 800).measureText(word); rrect(c, px - w / 2 - 18, py - 40, w + 36, 58, 29, col("e8651a"), v); text(c, word, px, py + 2, 40, WHITE, 800, "c", v)
# ---------------------------------------------------------------- the proof film
MJ = json.load(open("build/motion.json")) if os.path.exists("build/motion.json") else None; PAL = [CYAN, YEL, col("ff8a4c"), col("7bd88f"), col("c79bf2"), col("f28fb1"), MUTE]
def pl_pos(x):                                                      # the front plate along its three moves, by millimetres of travel (as tools/motion.py walks it)
    a, b = 14.0, 14.0 + XE
    return [-XE, 14.0 - x, SL] if x <= a else [-(XE - (x - a)), 0, SL] if x <= b else [0, 0, SL - (x - b)]
def fw_pos(x): return [0, 12.0 - x, LIFT] if x <= 12 else [0, 0, LIFT - (x - 12.0)]
def p_shutter(u): x = -TH + 2 * TH * seg(u, .04, .44) - 2 * TH * seg(u, .56, .96); return sc(PLATE_IN, front=I, wheel=I, blade=I, phi=x), [("shutter", x)]      # stepped slowly across for the measurement, a rest, then back: in use a press flips it in an instant and it stays
def p_aperture(u): x = W2 * (seg(u, .04, .44) - seg(u, .56, .96)); return sc(PLATE_IN, front=I, blade=I, wheel=I, wa=x), [("aperture", x)]
def p_plate(u): x = 21.8 * seg(u, 0, 1); return sc(lerp((0, 26, 6, 72, 0, 222, 300), FRONT, seg(u, .55, .75)), body=I, **plate(Tr(pl_pos(x)))), [("plate", x)]
def p_lens(u): x = 8 * (1 - seg(u, 0, 1)); return sc(FRONT_NEAR, body=I, **plate(lens=False), lens=Tr([0, x, 0])), [("lens", x)]
def p_spool(u): d = 26 * (1 - seg(u, 0, .4)); a = 360 * ramp(u, .5, 1); return sc(REAR_FAR, **BASE, spool=Tr([0, -d, 0]) @ RZ(SP, a)), [("spool_in", d)] if u < .45 else [("spool_turn", a % 360)]
def p_knob(u): d = 26 * (1 - seg(u, 0, .4)); a = 360 * ramp(u, .5, 1); M = Tr([0, -d, 0]); return sc(REAR_FAR, **BASE, spool=I, cass=M, knob=M @ RZ(CA, -a)), [("knobfilm_in", d)] if u < .45 else [("knob_turn", a % 360)]
def p_wheel(u): x = 14.5 * seg(u, 0, .45); a = 360 * ramp(u, .52, 1); return sc(B8, back=I, roller=Tr(fw_pos(x)) @ RZ(RO, a)), [("wheel_in", x)] if u < .5 else [("wheel_turn", a % 360)]
def p_back(u): d = 14 * (1 - seg(u, 0, 1)); f, i = filmmesh(ROLL0, adv=37.0, d=d); M = Tr([0, -d, 0]); return sc(REAR_TOP, **BASE, spool=I, cass=I, knob=I, film=f, back=M, roller=M @ RZ(RO, i["phase"] + kin.wheel_turn(37.0)), alpha=dict(back=0.35)), [("back", d), ("back_film", d)]
TEETH = (30.5, 12.5, 12.5, 62, 0, 196, 62)
def p_teeth(u): adv = 37.0 + 38.0 * ramp(u, 0, 1); f, i = filmmesh(ROLL0, adv=adv, d=0.0); return sc(TEETH, spool=I, film=f, roller=RZ(RO, i["phase"] + kin.wheel_turn(adv)), back=I, alpha=dict(back=0.5)), [("teeth", (adv - 37.0) % PITCH)]
def p_roll(u): L = 1640.0 * ramp(u, 0, 1) ** 1.3; return wound(L, hide_back=True), [("roll", L)]
def p_dial(u): return sc(TOP, **BASE, back=I, knob=I, spool=RZ(SP, 360 * ramp(u, 0, 1)), roller=RZ(RO, -720 * ramp(u, 0, 1))), [("dial", 0)]
PROOF = [("shutter", "The shutter, moved slowly from one side to the other", "in use a press flips it in an instant and it stays there: nothing springs it back. Here it is stepped across, rested, and stepped back, to measure every position", p_shutter, 8.0),
         ("aperture", "The aperture wheel, moved slowly through its travel", "from the smallest hole to the largest, a rest, and back; in use it clicks into three places", p_aperture, 8.0),
         ("plate", "The front plate goes on", "onto the body, across, down: with shutter, wheel and lens on board", p_plate, 6.5), ("lens", "The lens is pressed in", "three ribs in its pocket are meant to be squeezed", p_lens, 4.0),
         ("spool", "The spool slides in and turns", "its knob rests on the top of the body", p_spool, 7.0), ("knob", "The wind knob and the film slide in; the knob turns", "the film's shell stands on the chamber floor", p_knob, 7.0),
         ("wheel", "The frame wheel goes into its fork and turns", "into the fork, down, then one whole turn", p_wheel, 7.5), ("back", "The back closes over the film", "the film wraps round the frame wheel as the back comes home", p_back, 6.0),
         ("teeth", "The film turns the frame wheel", "one picture: 38 mm of film, eight holes, one turn", p_teeth, 9.0), ("roll", "The whole film is wound onto the spool", "1.64 m of film: the roll grows from 5.9 mm to 10.1 mm", p_roll, 8.0),
         ("dial", "The dial and the red knob, both turning", "the nearest two things on top of the camera", p_dial, 5.0)]
def proof_clips(): return [dict(key="title", kind="title", dur=6.0)] + [dict(key=k, kind="move", title=t, sub=s, fn=f, md=md, dur=md + 4.0, t0=1.2) for k, t, s, f, md in PROOF] + [dict(key="summary", kind="summary", dur=14.0), dict(key="limits", kind="limits", dur=11.0)]
NAME = {"front": "front plate", "roller": "frame wheel", "knob": "wind knob", "cassette": "film's shell", "shutter open": "shutter, open", "film, empty take-up": "film (take-up roll empty)", "film, full take-up": "film (take-up roll full)"}
def nm(n): return NAME.get(n, n)
def series(key):
    """what tools/motion.py measured for one move: x, {neighbour: clearance}, shared volume per step, the expected contacts"""
    if key == "teeth": c = MJ["film"]["cases"]["ordinary film, 0.13 mm; take-up roll empty"]; return c["adv"], {"tooth to the edge of its hole": c["gap"]}, c["overlap"], []
    if key == "roll": r = [q for q in MJ["film"]["roll"] if q["thickness"] == 0.13]; return [q["length_on_mm"] for q in r], {"roll to the chamber wall": [q["chamber_wall_gap"] for q in r]}, [max(q["body"][0], q["back"][0]) for q in r], []
    m = MJ["motions"][key]; g = {nm(n): p["gap"] for n, p in m["pairs"].items() if n not in m["expected"] and min(p["gap"]) < 3.9}; aw = [n for n in g if n.startswith("aperture wheel at stop")]
    if aw: g["aperture wheel (at each of its three stops)"] = [min(g[n][k] for n in aw) for k in range(len(m["x"]))]; [g.pop(n) for n in aw]
    return m["x"], g, [max(p["overlap"][k] for n, p in m["pairs"].items() if n not in m["expected"]) for k in range(len(m["x"]))], m["expected"]
UNIT = dict(shutter="degrees of swing", aperture="degrees of slide", plate="mm of travel", lens="mm from home", spool_in="mm from home", spool_turn="degrees of turn", knobfilm_in="mm from home", knob_turn="degrees of turn", wheel_in="mm of travel", wheel_turn="degrees of turn",
            back="mm from home", back_film="mm from home", teeth="mm of film, within one hole's pitch", roll="mm of film wound on")
def plot(c, X, Y, Wd, Hh, key, xc):
    xs, G, ov, exp = series(key); xs = np.array(xs, float); ymax = 1.0 if key != "roll" else 7.0; x0, x1 = xs.min(), xs.max(); px = lambda x: X + 56 + (Wd - 72) * (x - x0) / (x1 - x0 or 1); py = lambda y: Y + Hh - 40 - (Hh - 88) * min(y, ymax) / ymax
    rrect(c, X, Y, Wd, Hh, 16, PANEL)
    for yv in np.linspace(0, ymax, 5): line(c, px(x0), py(yv), px(x1), py(yv), LINE, 1.5); text(c, ("%.2f" if ymax <= 1 else "%.0f") % yv, X + 48, py(yv) + 7, 18, MUTE, 500, "r")
    text(c, "clearance, mm" + ("  (1.00 and more is drawn at the top)" if ymax <= 1 else ""), X + 16, Y + 28, 18, MUTE, 500); text(c, UNIT[key], X + Wd - 16, Y + Hh - 10, 17, MUTE, 500, "r")
    names = sorted(G, key=lambda n: min(G[n]))[:5]
    for k, n in enumerate(names):
        ys = G[n]; p = skia.Path(); p.moveTo(px(xs[0]), py(ys[0])); [p.lineTo(px(a), py(b)) for a, b in zip(xs[1:], ys[1:])]; c.drawPath(p, stroke(PAL[k], 3))
    line(c, px(xc), Y + 44, px(xc), Y + Hh - 40, INK, 2, .8); j = int(np.argmin(np.abs(xs - xc))); yl = Y + Hh + 30
    for k, n in enumerate(names):
        line(c, X + 6, yl - 8, X + 34, yl - 8, PAL[k], 4); v = G[n][j]; text(c, n, X + 44, yl, 22, INK, 500); text(c, ("%.2f mm" % v) if (v < 3.9 or key == "roll") else "over 4 mm", X + Wd, yl, 22, INK, 600, "r"); yl += 32
    return ov[j], yl, exp
def draw_proof(c, cl, i, n, t):
    base(c, "CURVE 35  ·  does it all move freely?", MODEL + "  ·  the model, not a print", i, n, t, cl["dur"]); S = MJ["summary"]
    if cl["kind"] == "title":
        a = ease(ramp(t, 0, .5)); text(c, "Every part, through all of its travel", W / 2, 400, 76, INK, 800, "c", a)
        for k, l in enumerate(["Each part that moves is stepped through its whole travel.", "At every step: how much space does it share with a neighbour (it must be none),", "and how near do they come?  %d positions measured." % MJ["positions_tested"]]): text(c, l, W / 2, 490 + k * 50, 34, INK if k < 2 else YEL, 500, "c", ease(ramp(t, .4 + .5 * k, 1.0 + .5 * k)))
        text(c, "Then the film: a strip with its holes, pulled through the frame wheel's teeth.", W / 2, 690, 30, MUTE, 500, "c", ease(ramp(t, 2.2, 2.8))); return
    if cl["kind"] == "summary":
        text(c, "What was measured", CX, 150, 52, INK, 700); cols = [CX, 780, 1010, 1230, 1500]; y = 214
        for x, hlab, al in zip(cols, ["the move", "positions", "space shared", "nearest", "to"], "lrrrl"): text(c, hlab, x if al == "l" else x + 150, y, 22, MUTE, 600, al)
        rows = [(s["move"], str(s["steps"]), "none" if s["shared_mm3"] <= 0.002 else "%.3f mm3" % s["shared_mm3"], "%.2f mm" % s["nearest_mm"], nm(s["nearest_to"])) for s in S]
        cs = MJ["film"]["cases"]; rows += [("film through the frame wheel's teeth (6 films)", str(sum(len(v["adv"]) for v in cs.values())), "none", "%.2f mm" % min(v["min_gap_mm"] for v in cs.values()), "edge of a hole"),
                                         ("dial and red knob, both turning", "all round", "none", "%.2f mm" % MJ["dial_and_knob"]["nearest_mm"], "each other")]
        for k, r in enumerate(rows):
            a = ease(ramp(t, .3 + .28 * k, .7 + .28 * k)); yy = y + 44 + k * 42
            for x, v, al in zip(cols, r, "lrrrl"): text(c, v, x if al == "l" else x + 150, yy, 25, GREEN if v == "none" else INK, 600 if v == "none" else 500, al, a)
        para(c, "Nearest 0.00 to 0.05 mm: two parts that rest on each other. A knob on the top of the body, the plate on the body's face, the film's shell on the chamber floor, the shutter and the aperture wheel lying in the plate.", CX, y + 44 + len(rows) * 42 + 26, 23, W - 2 * CX, MUTE, 500, a=ease(ramp(t, 5, 5.6))); return
    if cl["kind"] == "limits":
        text(c, "What this does and does not show", CX, 170, 52, INK, 700)
        L = [("It shows", "that no part, at its drawn size, has to pass through another to be put in, to move, or to come out; and that the film's holes meet the teeth all the way round.", GREEN),
             ("It found", "the frame wheel's teeth came within 0.06 mm of a hole's edge on the way in. Their shape was changed (v2.12): now 0.18 mm or more.", YEL),
             ("It leaves out", "friction, the bending of the springs and of the film, and a real printer's error. The clicks and latches are covered by a separate strength check.", ORANGE),
             ("Still true", "nothing has been printed. A print and a roll of film are the real test.", INK)]
        y = 270
        for k, (h, s, cc) in enumerate(L):
            a = ease(ramp(t, .3 + .9 * k, .9 + .9 * k)); text(c, h, CX, y, 34, cc, 700, a=a); y += para(c, s, CX + 300, y, 32, W - CX - 380, INK, 500, a=a, lh=1.36) + 34
        return
    s, data = cl["fn"](u_of(cl, t)); card(c, render(s)); X = CX + CW + 44; Wd = W - 40 - X; h = para(c, cl["title"], X, CY + 40, 38, Wd, INK, 700, lh=1.25); h += para(c, cl["sub"], X, CY + 40 + h + 4, 24, Wd, MUTE, 500, lh=1.35); y = CY + 40 + h + 30
    if data[0][0] == "dial":
        d = MJ["dial_and_knob"]; rrect(c, X, y, Wd, 190, 16, PANEL); text(c, "space shared", X + 24, y + 48, 24, MUTE, 500); text(c, "none", X + Wd - 24, y + 52, 40, GREEN, 700, "r"); text(c, "nearest", X + 24, y + 118, 24, MUTE, 500); text(c, "%.2f mm" % d["nearest_mm"], X + Wd - 24, y + 122, 40, INK, 700, "r")
        text(c, "measured with each swept all the way round", X + 24, y + 166, 20, MUTE, 500); return
    key, xc = data[0]; ov, yl, exp = plot(c, X, y, Wd, 330, key, xc); extra = max((series(k2)[2][int(np.argmin(np.abs(np.array(series(k2)[0], float) - x2)))] for k2, x2 in data[1:]), default=0.0); ov = max(ov, extra); yl += 14
    rrect(c, X, yl, Wd, 86, 16, PANEL); text(c, "space shared with a neighbour", X + 22, yl + 52, 23, MUTE, 500); text(c, "none" if ov <= 0.002 else "%.3f mm3" % ov, X + Wd - 22, yl + 56, 38, GREEN if ov <= 0.002 else RED, 700, "r")
    if key == "teeth": para(c, "Before the change (v2.11) the nearest was 0.06 to 0.09 mm, on the way into a hole. The teeth now taper straight.", X, yl + 124, 22, Wd, MUTE, 500)
    if exp: para(c, "Meant to touch: the three ribs in the lens's pocket are squeezed by 0.3 mm3 as the lens goes home. That is what holds it.", X, yl + 124, 22, Wd, MUTE, 500)
# ---------------------------------------------------------------- build
def clip_frames(cl): return int(round(cl["dur"] * FPS))
def specs(cl, film):
    if cl["kind"] not in ("step", "move"): return []
    out = [cl["fn"](1.0)] if film == "guide" else []
    for f in range(clip_frames(cl)):
        r = cl["fn"](u_of(cl, f / FPS)); out.append(r if film == "guide" else r[0])
    return out
def encode(film, clips, i, draw):
    cl = clips[i]; out = f"{OUT}/{film}_{i:02d}_{cl['key']}.mp4"; tmp = out[:-4] + ".part.mp4"; surf = skia.Surface(W, H)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for f in range(clip_frames(cl)):
        with surf as c: draw(c, cl, i, len(clips), f / FPS)
        p.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType).tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError("ffmpeg failed on " + out)
    os.replace(tmp, out)
    if cl.get("lines") is not None:                                    # the clip's own sound, and the clip with it, for a lesson or a web page
        import voice as VC; os.makedirs(f"{OUT}/clips", exist_ok=True); wv = VC.track(cl["lines"], clip_frames(cl) / FPS, out[:-4] + ".wav"); VC.mux(out, wv, f"{OUT}/clips/{film}_{cl['key']}.mp4")
    return out
def main():
    film = sys.argv[1]; args = sys.argv[2:]; clips = guide_clips() if film == "guide" else proof_clips(); draw = draw_guide if film == "guide" else draw_proof; xstart()
    try:
        if args and args[0] == "stills":                               # python3 tools/motionfilm.py guide stills key:seconds ...
            for a in args[1:]:
                k, tt = a.split(":"); i = next(j for j, cl in enumerate(clips) if cl["key"].endswith(k) or cl["key"] == k); surf = skia.Surface(W, H)
                with surf as c: draw(c, clips[i], i, len(clips), float(tt))
                surf.makeImageSnapshot().save(f"{OUT}/still_{film}_{k}_{tt}.png", skia.kPNG); print("still", k, tt)
            return
        if args == ["sound"]:                                          # the sound again (a new recording of a line, or a new level) without drawing a single picture
            import voice as VC
            for i, cl in enumerate(clips): out = f"{OUT}/{film}_{i:02d}_{cl['key']}.mp4"; VC.mux(out, VC.track(cl["lines"], clip_frames(cl) / FPS, out[:-4] + ".wav"), f"{OUT}/clips/{film}_{cl['key']}.mp4")
            args = ["__none__"]
        todo = [i for i, cl in enumerate(clips) if not args or any(cl["key"].endswith(a) or cl["key"] == a for a in args)]; t0 = time.time(); uniq = {}
        for i in todo:
            for s in specs(clips[i], film): uniq.setdefault(fkey(s), s)
        need = [s for k, s in uniq.items() if not os.path.exists(f"{FRD}/{k}.png")]; print(f"{film}: {len(todo)} clips, {len(uniq)} different pictures, {len(need)} to render", flush=True)
        with cf.ThreadPoolExecutor(2) as ex: list(ex.map(render, need))
        print("rendered in %.0f s" % (time.time() - t0), flush=True)
        for i in todo: encode(film, clips, i, draw)
        lst = f"{OUT}/{film}.txt"; open(lst, "w").write("".join(f"file '{film}_{i:02d}_{cl['key']}.mp4'\n" for i, cl in enumerate(clips)))
        if all(os.path.exists(f"{OUT}/{film}_{i:02d}_{cl['key']}.mp4") for i, cl in enumerate(clips)):
            name = "build/CURVE-35_assembly_guide.mp4" if film == "guide" else "build/CURVE-35_motion_proof.mp4"; sil = f"{OUT}/{film}_silent.mp4"; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", sil], check=True)
            if film == "guide":
                import voice as VC; VC.mux(sil, VC.join([f"{OUT}/{film}_{i:02d}_{cl['key']}.wav" for i, cl in enumerate(clips)], f"{OUT}/guide.wav"), name); os.remove(sil)
            else: os.replace(sil, name)
            tot = sum(cl["dur"] for cl in clips); json.dump([dict(key=cl["key"], start=round(sum(c2["dur"] for c2 in clips[:i]), 1), seconds=cl["dur"]) for i, cl in enumerate(clips)], open(f"{OUT}/{film}_chapters.json", "w"), indent=1)
            print("%s  %.1f s (%d:%02d)  %d clips   %.0f s" % (name, tot, tot // 60, tot % 60, len(clips), time.time() - t0))
    finally: xstop()
if __name__ == "__main__": main()
