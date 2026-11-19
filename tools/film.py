"""Lesson films for CURVE 35.  Every frame is drawn here (skia) or rendered from the model (OpenSCAD guide mode): no photographs.
One encoded file per scene, joined without re-encoding.  python3 tools/film.py 1 [frames | scene-name ...]"""
import os, sys, math, json, subprocess, numpy as np, skia
from PIL import Image
sys.path.insert(0, "tools")
import booklet_render as BR
W, H, FPS = 1920, 1080, 30
OUT = "build/film"; SRC = OUT + "/src"; os.makedirs(SRC, exist_ok=True)
MODEL = "ONE-135 v2.14"

def col(h, a=255): h = h.lstrip("#"); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
BG = col("0f1317"); PANEL = col("182028"); LINE = col("2b3642"); INK = col("f1ece2"); MUTE = col("8e99a6"); ORANGE = col("e8651a"); YEL = col("f4c430"); CYAN = col("4fb7e6"); RED = col("ef5b4c"); GREEN = col("3fae6b"); WHITE = col("ffffff")
def alpha(c, a): return skia.Color(skia.ColorGetR(c), skia.ColorGetG(c), skia.ColorGetB(c), int(max(0, min(1, a)) * skia.ColorGetA(c)))
TF = {w: skia.Typeface("Inter", skia.FontStyle(w, 5, skia.FontStyle.kUpright_Slant)) for w in (400, 500, 600, 700, 800)}
def font(size, weight=500): f = skia.Font(TF[weight], size); f.setSubpixel(True); return f
def clamp(x): return max(0.0, min(1.0, x))
def ramp(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= a)
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def window(t, a, b, f=0.35): return ease(ramp(t, a, a + f)) * (1 - ease(ramp(t, b - f, b)))
def text(c, s, x, y, size=44, color=INK, weight=500, align="l", a=1.0):
    f = font(size, weight); w = f.measureText(s); x = x - w / 2 if align == "c" else x - w if align == "r" else x
    c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=alpha(color, a))); return w
def wrap(s, size, weight, maxw):
    f = font(size, weight); out = []; cur = ""
    for wd in s.split():
        t = (cur + " " + wd).strip()
        if f.measureText(t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = wd
    return out + [cur] if cur else out
def para(c, s, x, y, size=40, maxw=800, color=INK, weight=500, align="l", a=1.0, lh=1.32):
    ls = wrap(s, size, weight, maxw)
    for i, l in enumerate(ls): text(c, l, x, y + i * size * lh, size, color, weight, align, a)
    return len(ls) * size * lh
def stroke(color, w=3, a=1.0, dash=None, cap=True):
    p = skia.Paint(AntiAlias=True, Color=alpha(color, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    if cap: p.setStrokeCap(skia.Paint.kRound_Cap)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p
def fill(color, a=1.0): return skia.Paint(AntiAlias=True, Color=alpha(color, a))
def line(c, x0, y0, x1, y1, color, w=3, a=1.0, dash=None): c.drawLine(x0, y0, x1, y1, stroke(color, w, a, dash))
def dot(c, x, y, r, color, a=1.0, glow=0):
    if glow: p = fill(color, a * 0.45); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow)); c.drawCircle(x, y, r * 2.2, p)
    c.drawCircle(x, y, r, fill(color, a))
def rrect(c, x, y, w, h, r, color, a=1.0, outline=None, ow=2):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, fill(color, a))
    if outline is not None: c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, stroke(outline, ow, a))
def poly(c, pts, color, a=1.0, w=None):
    p = skia.Path(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close(); c.drawPath(p, fill(color, a) if w is None else stroke(color, w, a))
class layer:
    def __init__(s, c, a): s.c = c; s.a = a
    def __enter__(s): s.c.saveLayerAlpha(None, int(clamp(s.a) * 255))
    def __exit__(s, *e): s.c.restore()
_img = {}
def image(path, w, h=None):
    k = (path, w, h)
    if k not in _img:
        im = Image.open(path).convert("RGBA"); h2 = h or round(im.height * w / im.width); _img[k] = skia.Image.fromarray(np.ascontiguousarray(np.asarray(im.resize((w, h2), Image.LANCZOS))))
    return _img[k]
def card(c, path, x, y, w, a=1.0, pad=18, label=None):
    im = image(path, w); h = im.height()
    with layer(c, a):
        sh = fill(col("000000"), 0.5); sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)); c.drawRoundRect(skia.Rect.MakeXYWH(x - pad, y - pad + 10, w + 2 * pad, h + 2 * pad), 22, 22, sh)
        rrect(c, x - pad, y - pad, w + 2 * pad, h + 2 * pad, 22, WHITE); c.drawImage(im, x, y, skia.SamplingOptions(), skia.Paint())
        if label: text(c, label, x + 6, y + h + 4, 22, col("6b7480"), 500)
    return h
def captions(c, t, caps, y=962, size=42):
    for a, b, s in caps:
        v = window(t, a, b)
        if v > 0:
            ls = wrap(s, size, 500, 1620); y0 = y if len(ls) > 1 else y + 26
            for i, l in enumerate(ls): text(c, l, W / 2, y0 + i * size * 1.3, size, INK, 500, "c", v)
def model(name, d, cam, size=(1600, 1200)):
    BR.OUT = SRC; return BR.render(name, dict(PART="guide", G_MESH=True, G_AUTO=False, **d), cam, size=size)
ALL = ["body", "back", "roller", "spool", "knob", "front", "wheel", "blade"]
R1 = ["body", "back", "roller", "spool", "knob", "plate1", "slide1", "pinring"]      # rung 1: the dark box, the first plate, its slide, the ring that holds the foil

# ------------------------------------------------------------------ lesson 1: a picture from a hole
PH = json.load(open("build/pinhole.json")); F_MM = PH["pinhole_to_film_mm"]; D_BEST = PH["best_hole_mm"]; N_BEST = PH["f_number"]; LAMBDA = 0.00055
TX, YT, YM, YB = 360, 290, 515, 740; FX, F0, F1 = 1400, 270, 770; WX = 1052; HY = 520
SRCS = [(YT, YEL), (YM, CYAN), (YB, RED)]
def tree(c, x, base, s=1.0, a=1.0):
    rrect(c, x - 14 * s, base - 240 * s, 28 * s, 240 * s, 6 * s, col("7a5234"), a)
    for dx, dy, r, k in ((-70, -300, 92, "2f8a4e"), (62, -310, 98, "369a57"), (0, -372, 104, "3fae6b"), (-6, -285, 80, "2b7d47")): c.drawCircle(x + dx * s, base + dy * s, r * s, fill(col(k), a))
def through(ys): return HY + (HY - ys) * (FX - WX) / (WX - TX)
def l1_setup(c, a=1.0, film_a=1.0):
    tree(c, TX, YB, 1.0, a); text(c, "tree", TX, YB + 52, 30, MUTE, 500, "c", a)
    rrect(c, FX, F0, 20, F1 - F0, 6, col("d9d2c4"), film_a); text(c, "film", FX + 10, F0 - 24, 30, MUTE, 500, "c", a)
def fans(c, g, a_left=0.55, a_right=0.55, stop=None):
    for i, (ys, k) in enumerate(SRCS):
        gi = clamp(g[i])
        if gi <= 0: continue
        for j in range(13):
            yf = F0 + 10 + j * (F1 - F0 - 20) / 12; xe = TX + gi * (FX - TX); ye = ys + gi * (yf - ys)
            if stop is None: line(c, TX, ys, xe, ye, k, 2.5, a_left)
            else:
                yw = ys + (yf - ys) * (WX - TX) / (FX - TX); line(c, TX, ys, WX, yw, k, 2.5, a_left)
                if a_right > 0: line(c, WX, yw, FX, yf, k, 2.5, a_right)
        dot(c, TX, ys, 11, k, 1.0, glow=10)
def inset(c, x, y, a, kind, title, sub):
    w, h = 330, 220
    with layer(c, a):
        text(c, title, x, y - 18, 26, MUTE, 500); rrect(c, x, y, w, h, 10, col("f3efe6"))
        if kind == "mud": rrect(c, x + 8, y + 8, w - 16, h - 16, 6, col("b9a58f"))
        else:
            c.save(); c.clipRect(skia.Rect.MakeXYWH(x + 8, y + 8, w - 16, h - 16)); rrect(c, x + 8, y + 8, w - 16, h - 16, 6, col("cfe4f2")); c.drawRect(skia.Rect.MakeXYWH(x + 8, y + 8, w - 16, 46), fill(col("8fb58a")))
            c.translate(x + w / 2, y + 30); c.scale(-0.40, -0.40); tree(c, 0, 0); c.restore()
        text(c, sub, x, y + h + 34, 26, INK, 500)

def s_hook(c, t):
    text(c, "This camera has no lens.", W / 2, 250 - 40 * ease(ramp(t, 2.6, 3.6)), 92, INK, 800, "c", ease(ramp(t, 0.2, 1.0)))
    card(c, model("l1_hero1", dict(G_OLD=[], G_NEW=R1, G_VECS=[[0, 0, 0]] * 8), BR.FACE), 170, 300 + 30 * (1 - ease(ramp(t, 2.6, 3.8))), 800, ease(ramp(t, 2.6, 3.8)))
    for i, s in enumerate(("No glass.", "No battery.", "No sensor.")): text(c, s, 1110, 450 + i * 100, 68, INK, 700, "l", window(t, 4.4 + i * 1.0, 9.4, 0.4))
    a = ease(ramp(t, 9.6, 10.4)); text(c, "Just a hole", 1110, 470, 68, INK, 700, "l", a); text(c, "a quarter of a", 1110, 560, 68, INK, 700, "l", a); text(c, "millimetre wide.", 1110, 650, 68, INK, 700, "l", a)
    text(c, "So how does a hole make a picture?", 1110, 790, 44, ORANGE, 700, "l", ease(ramp(t, 13.0, 13.8)))
def s_nohole(c, t):
    l1_setup(c); g = [ramp(t, 2 + 3 * i, 4.6 + 3 * i) for i in range(3)]; fans(c, [ease(x) for x in g])
    for i, (ys, k) in enumerate(SRCS): rrect(c, FX, F0, 20, F1 - F0, 6, k, 0.33 * ease(ramp(t, 4.2 + 3 * i, 5.0 + 3 * i)))
    inset(c, 1500, 400, ease(ramp(t, 11.5, 12.5)), "mud", "what the film records", "an even glow: no picture")
    captions(c, t, [(0.4, 10.8, "Hold a piece of film up to a tree. Light from each point of the tree lands on every part of the film."), (11.2, 20, "So every part of the film sees the whole tree at once. All the light is there. The picture is not.")])
def wall(c, dy=0, a=1.0):
    for y0, y1 in ((150, HY - 13), (HY + 13, 880)): rrect(c, WX - 14, y0 + dy, 28, y1 - y0, 4, col("596675"), a, outline=col("8e99a6"), ow=2)
def s_hole(c, t):
    l1_setup(c); k = ease(ramp(t, 2.0, 3.4)); dim = 1 - 0.6 * ease(ramp(t, 18.6, 19.6))
    fans(c, [1, 1, 1], 0.55 * dim, 0.55 * (1 - k), stop=True); dy = -(1 - ease(ramp(t, 0.3, 2.4))) * 900; wall(c, dy)
    if t > 0.6: text(c, "a wall with a small hole", WX, 132 + dy, 30, MUTE, 500, "c")
    for i, (ys, kc) in enumerate(SRCS):
        rrect(c, FX, F0, 20, F1 - F0, 6, kc, 0.33 * (1 - k)); a = ease(ramp(t, 2.8, 3.8)); yf = through(ys)
        if a > 0: line(c, TX, ys, FX, yf, kc, 4.5, a * dim); dot(c, FX + 10, yf, 10, kc, a, glow=8)
    if 20.2 < t < 33.4:   # one point walked up the tree: its picture walks down the film
        a = window(t, 20.2, 33.4, 0.5); u = 0.5 - 0.5 * math.cos((t - 20.4) * math.pi / 6.0); ys = YB + (YT - YB) * u; yf = through(ys)
        line(c, TX, ys, FX, yf, WHITE, 4, a); dot(c, TX, ys, 12, WHITE, a, glow=12); dot(c, FX + 10, yf, 11, WHITE, a, glow=12)
    m = ease(ramp(t, 8.6, 9.8)); inset(c, 1500, 400, 1 - m, "mud", "what the film records", "an even glow: no picture"); inset(c, 1500, 400, m, "tree", "what the film records", "a picture, upside down")
    captions(c, t, [(0.4, 7.6, "Now put a wall with a small hole between them. Most of the light is stopped."), (8.0, 19.0, "Each part of the film can see only one point of the tree: the one in line with the hole. That is all a picture is."),
                    (19.6, 34, "It is upside down, and left and right are swapped, because the rays cross in the hole. Move a point up the tree and its picture moves down.")])

EV_T = 9.0; EV_0 = 4.2
EVENTS = [("c. 400 BC", "Mozi and his school, China", "The oldest account that survives: light through a small hole makes an upside-down picture, because light travels in straight lines."),
          ("c. 350 BC", "Aristotle, or a follower, Greece", "The book Problems asks why the spots of sunlight under a tree turn into crescents during an eclipse. Every gap between the leaves is a pinhole."),
          ("c. 1021", "Ibn al-Haytham", "In his Book of Optics he tests it. Several lamps, one hole, a spot of light for each. Screen one lamp and only its spot goes out."),
          ("1544", "Gemma Frisius, Leuven", "He watches an eclipse of the sun safely inside a dark room, and prints a picture of the room the year after."),
          ("1550 to 1568", "Cardano, then Barbaro, Italy", "Glass goes in the hole: first a glass disc, then a lens with a stop in front. The picture gets far brighter. That is lesson 2."),
          ("1604", "Johannes Kepler", "He is the first to use the name camera obscura: Latin for dark room. Our word camera simply means room."),
          ("1826 or 1827", "Nicéphore Niépce, France", "He puts a light-sensitive plate where the picture falls and waits: eight hours by tradition, perhaps days. It is the oldest camera photograph that survives.")]
def crescent(c, x, y, r, color, a=1.0, flip=1):
    p = skia.Path(); p.addCircle(x, y, r); q = skia.Path(); q.addCircle(x + flip * r * 0.55, y - flip * r * 0.1, r * 0.92); c.drawPath(skia.Op(p, q, skia.PathOp.kDifference_PathOp), fill(color, a))
def person(c, x, y, s, color, a=1.0, inv=1):
    c.drawCircle(x, y - inv * 78 * s, 13 * s, fill(color, a)); p = stroke(color, 7 * s, a)
    for q in ((0, -62, 0, -22), (0, -22, -16, 0), (0, -22, 16, 0), (-20, -50, 20, -50)): c.drawLine(x + q[0] * s, y + inv * q[1] * s, x + q[2] * s, y + inv * q[3] * s, p)
def icon(c, k, x, y, p, a):
    with layer(c, a):
        if k == 0:
            hx, hy, wx = x + 330, y + 180, x + 600; c.drawRect(skia.Rect.MakeXYWH(hx, y + 30, wx - hx, 300), stroke(MUTE, 4)); c.drawLine(hx, hy - 12, hx, hy + 12, stroke(BG, 8, cap=False)); person(c, x + 50, y + 300, 1.9, INK)
            g = ease(ramp(p, 0.1, 0.5))
            for ys, kc in ((y + 152, YEL), (y + 300, RED)): ye = hy + (hy - ys) * (wx - hx) / (hx - x - 50); line(c, x + 50, ys, x + 50 + g * (wx - x - 50), ys + g * (ye - ys), kc, 3, 0.9)
            person(c, x + 556, y + 64, 1.83, ORANGE, ease(ramp(p, 0.5, 0.7)), inv=-1)
        if k == 1:
            crescent(c, x + 130, y + 70, 44, YEL);
            for dx, dy, r in ((330, 90, 80), (430, 70, 90), (540, 95, 78), (385, 130, 70), (490, 135, 72)): c.drawCircle(x + dx, y + dy, r, fill(col("2f8a4e")))
            rrect(c, x + 425, y + 180, 24, 130, 4, col("7a5234")); c.drawLine(x + 180, y + 312, x + 720, y + 312, stroke(MUTE, 4))
            for i, (dx, r) in enumerate(((250, 15), (330, 19), (540, 21), (620, 16), (690, 13))): crescent(c, x + dx, y + 336, r, YEL, ease(ramp(p, 0.15 + 0.08 * i, 0.3 + 0.08 * i)), flip=-1)
        if k == 2:
            off = 0.55 < p < 0.85; ks = (YEL, ORANGE, RED)
            c.drawLine(x + 400, y + 20, x + 400, y + 168, stroke(MUTE, 8, cap=False)); c.drawLine(x + 400, y + 192, x + 400, y + 340, stroke(MUTE, 8, cap=False)); c.drawLine(x + 700, y + 40, x + 700, y + 320, stroke(col("d9d2c4"), 8, cap=False))
            for i, ys in enumerate((80, 180, 280)):
                on = not (off and i == 1); g = ease(ramp(p, 0.1 + 0.08 * i, 0.3 + 0.08 * i)); yf = 180 + (180 - ys) * 1.0
                rrect(c, x + 88, y + ys + 6, 24, 40, 4, col("596675")); dot(c, x + 100, y + ys, 15, ks[i], 1.0 if on else 0.15, glow=12 if on else 0)
                if on: line(c, x + 100, y + ys, x + 100 + g * 600, y + ys + g * (yf - ys), ks[i], 3, 0.9); dot(c, x + 700, y + yf, 12, ks[i], ease(ramp(p, 0.3 + 0.08 * i, 0.4 + 0.08 * i)), glow=8)
        if k == 3:
            crescent(c, x + 110, y + 60, 40, YEL); poly(c, [(x + 330, y + 340), (x + 330, y + 120), (x + 520, y + 30), (x + 710, y + 120), (x + 710, y + 340)], MUTE, 1, w=4); c.drawLine(x + 330, y + 132, x + 330, y + 156, stroke(BG, 8, cap=False))
            g = ease(ramp(p, 0.1, 0.5)); line(c, x + 110, y + 60, x + 110 + g * 590, y + 60 + g * 226, YEL, 3, 0.9); crescent(c, x + 688, y + 286, 22, YEL, ease(ramp(p, 0.5, 0.7)), flip=-1)
        if k == 4:
            c.drawLine(x + 380, y + 20, x + 380, y + 130, stroke(MUTE, 8, cap=False)); c.drawLine(x + 380, y + 230, x + 380, y + 340, stroke(MUTE, 8, cap=False)); c.drawLine(x + 700, y + 40, x + 700, y + 320, stroke(col("d9d2c4"), 8, cap=False))
            lp = skia.Path(); lp.moveTo(x + 380, y + 128); lp.quadTo(x + 412, y + 180, x + 380, y + 232); lp.quadTo(x + 348, y + 180, x + 380, y + 128); c.drawPath(lp, fill(CYAN, 0.85)); dot(c, x + 100, y + 180, 15, YEL, glow=12)
            g = ease(ramp(p, 0.1, 0.5))
            for dy in (-44, -22, 0, 22, 44):
                xa = x + 100 + min(g * 2, 1) * 280; line(c, x + 100, y + 180, xa, y + 180 + min(g * 2, 1) * dy, YEL, 3, 0.85)
                if g > 0.5: line(c, x + 380, y + 180 + dy, x + 380 + (g * 2 - 1) * 320, y + 180 + dy * (1 - (g * 2 - 1)), YEL, 3, 0.85)
            dot(c, x + 700, y + 180, 10 + 6 * ease(ramp(p, 0.5, 0.6)), WHITE, ease(ramp(p, 0.5, 0.6)), glow=16)
        if k == 5:
            f = skia.Font(skia.Typeface("DejaVu Serif", skia.FontStyle(400, 5, skia.FontStyle.kItalic_Slant)), 92); f.setSubpixel(True)
            w1 = f.measureText("camera"); w0 = f.measureText("camera "); w2 = f.measureText("obscura"); c.drawString("camera obscura", x + 30, y + 150, f, fill(INK)); g = ease(ramp(p, 0.2, 0.45))
            line(c, x + 30, y + 176, x + 30 + g * w1, y + 176, ORANGE, 6); line(c, x + 30 + w0, y + 176, x + 30 + w0 + g * w2, y + 176, MUTE, 6); text(c, "room", x + 30 + w1 / 2, y + 244, 50, ORANGE, 700, "c", g); text(c, "dark", x + 30 + w0 + w2 / 2, y + 244, 50, MUTE, 700, "c", g)
        if k == 6:
            rrect(c, x + 150, y + 40, 400, 290, 10, col("7d8690")); g = ease(ramp(p, 0.05, 0.95))
            for q in ([(170, 310), (170, 150), (250, 110), (250, 310)], [(270, 310), (270, 200), (400, 160), (400, 310)], [(420, 310), (420, 120), (530, 150), (530, 310)]): poly(c, [(x + u, y + v) for u, v in q], col("d5dae0"), 0.75 * g)
            c.drawCircle(x + 660, y + 180, 70, stroke(INK, 5)); ang = p * 2 * math.pi * 3 - math.pi / 2; line(c, x + 660, y + 180, x + 660 + 52 * math.cos(ang), y + 180 + 52 * math.sin(ang), ORANGE, 6); line(c, x + 660, y + 180, x + 660 + 34 * math.cos(ang / 12), y + 180 + 34 * math.sin(ang / 12), INK, 6)
def hist(idx, intro=None, lead=1.0):
    """The timeline, told where each step belongs: this scene shows the events in idx; the strip of seven dates stays on screen and fills as the film goes."""
    t0 = EV_0 if intro else lead; n = len(EVENTS)
    def f(c, t):
        if intro: text(c, intro[0], W / 2, 520, 60, INK, 700, "c", window(t, 0.1, t0 - 0.1, 0.3)); text(c, intro[1], W / 2, 600, 40, ORANGE, 600, "c", window(t, 1.4, t0 - 0.1, 0.3))
        j = int(clamp((t - t0) / (len(idx) * EV_T) - 1e-9) * len(idx)) if t >= t0 else -1; k = idx[j] if j >= 0 else -1; upto = k if k >= 0 else idx[0]
        a0 = ease(ramp(t, t0 - 0.4, t0 + 0.2)) if intro else 1.0; xs = [230 + i * (1460 / (n - 1)) for i in range(n)]; line(c, 190, 860, 1730, 860, LINE, 4, a0)
        for i in range(n):
            on = i == k; done = i < upto; dot(c, xs[i], 860, 13 if on else 9, ORANGE if on else INK if done else MUTE, a0, glow=10 if on else 0); text(c, EVENTS[i][0], xs[i], 910, 24, ORANGE if on else INK if done else MUTE, 700 if on else 500, "c", a0)
        if k >= 0:
            lt = t - t0 - j * EV_T; a = window(lt, 0, EV_T, 0.3); yr, who, txt = EVENTS[k]
            text(c, yr, 190, 380, 104 if len(yr) < 11 else 88, ORANGE, 800, "l", a); text(c, who, 194, 460, 40, INK, 600, "l", a); para(c, txt, 194, 550, 36, 760, INK, 500, "l", a, 1.36); icon(c, k, 1010, 250, min(1.0, lt / 5.0), a)
    return f, t0 + len(idx) * EV_T

def blur_mm(d): return d, 1.9 ** 2 * LAMBDA * F_MM / d      # geometric disc; spreading by diffraction (the constant that gives Rayleigh's best hole)
def sun_seconds(d): return (F_MM / d / 16) ** 2 / 400
_sim = {}
def sim_scene():
    s = skia.Surface(900, 600); c = s.getCanvas(); p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear(points=[(0, 0), (0, 380)], colors=[col("6fa8dc"), col("e4f0f8")])); c.drawRect(skia.Rect.MakeXYWH(0, 0, 900, 380), p)
    c.drawCircle(730, 90, 38, fill(col("fff6c8"))); poly(c, [(0, 380), (0, 300), (160, 250), (330, 310), (520, 240), (700, 300), (900, 260), (900, 380)], col("8aa7b8")); c.drawRect(skia.Rect.MakeXYWH(0, 370, 900, 230), fill(col("7fa35a")))
    poly(c, [(0, 600), (0, 520), (900, 470), (900, 600)], col("6c8f4b")); rrect(c, 470, 250, 250, 180, 2, col("efe6d2")); poly(c, [(450, 252), (595, 160), (740, 252)], col("a2452f")); rrect(c, 570, 340, 50, 90, 2, col("5b3a26"))
    for wx in (495, 650):
        rrect(c, wx, 285, 46, 46, 2, col("31475c")); c.drawLine(wx + 23, 285, wx + 23, 331, stroke(col("efe6d2"), 3, cap=False)); c.drawLine(wx, 308, wx + 46, 308, stroke(col("efe6d2"), 3, cap=False))
    tree(c, 220, 470, 0.72)
    for i in range(52): c.drawRect(skia.Rect.MakeXYWH(30 + i * 16.5, 452 + i * -0.5, 5, 70), fill(col("f7f3ea")))
    c.drawRect(skia.Rect.MakeXYWH(30, 470, 850, 6), fill(col("f7f3ea")));
    for i, (bx, by) in enumerate(((330, 120), (372, 100), (410, 128))): c.drawLine(bx - 12, by - 6, bx, by, stroke(col("2b3642"), 3)); c.drawLine(bx, by, bx + 12, by - 6, stroke(col("2b3642"), 3))
    a = s.toarray()[:, :, [2, 1, 0]].astype(np.float32) / 255; return a ** 2.2
def sim(d):
    from scipy.signal import fftconvolve
    from scipy.ndimage import gaussian_filter
    k = round(math.log(d) * 25)
    if k not in _sim:
        if "base" not in _sim: _sim["base"] = sim_scene()
        dd = math.exp(k / 25); g, f = blur_mm(dd); R = g * 25 / 2; a = np.pad(_sim["base"], ((80, 80), (80, 80), (0, 0)), mode="edge")
        if R > 0.6:
            n = int(math.ceil(R)) + 1; yy, xx = np.mgrid[-n:n + 1, -n:n + 1]; ker = np.clip(R + 0.5 - np.hypot(xx, yy), 0, 1); ker /= ker.sum(); a = np.stack([fftconvolve(a[:, :, i], ker, mode="same") for i in range(3)], 2)
        a = gaussian_filter(a, (f * 25 / 2.355, f * 25 / 2.355, 0))[80:-80, 80:-80]; rgba = np.dstack([np.clip(a, 0, 1) ** (1 / 2.2) * 255, np.full(a.shape[:2], 255)]).astype(np.uint8); _sim[k] = skia.Image.fromarray(np.ascontiguousarray(rgba))
    return _sim[k]
D_HI, D_LO = 2.0, 0.06
def d_of(t):
    L = lambda a, b, u: math.exp(math.log(a) + (math.log(b) - math.log(a)) * ease(u))
    if t < 7: return D_HI
    if t < 22: return L(D_HI, D_BEST, (t - 7) / 15)
    if t < 29: return D_BEST
    if t < 34: return L(D_BEST, D_LO, (t - 29) / 5)
    if t < 38: return D_LO
    if t < 41: return L(D_LO, D_BEST, (t - 38) / 3)
    return D_BEST
def fmt_s(s): return f"1/{round(1 / s, -1 if s < 0.02 else 0):.0f} s" if s < 0.1 else f"{s:.2f} s" if s < 1 else f"{s:.1f} s"
def s_size(c, t):
    d = d_of(t); x0, y0 = 110, 180; text(c, "what the film records  (a simulation, not a photograph)", x0, y0 - 18, 26, MUTE, 500); c.drawImage(sim(d), x0, y0, skia.SamplingOptions(), skia.Paint()); c.drawRect(skia.Rect.MakeXYWH(x0, y0, 900, 600), stroke(LINE, 2, cap=False))
    lx = lambda v: x0 + 900 * (math.log(D_HI) - math.log(v)) / (math.log(D_HI) - math.log(D_LO)); ys = y0 + 648
    line(c, x0, ys, x0 + 900, ys, LINE, 6); line(c, x0, ys, lx(d), ys, ORANGE, 6); dot(c, lx(d), ys, 14, ORANGE, glow=8)
    for v, s in ((2.0, "2 mm"), (1.0, "1"), (0.5, "0.5"), (D_BEST, "0.24"), (0.12, "0.12"), (0.06, "0.06")): line(c, lx(v), ys + 14, lx(v), ys + 24, MUTE, 2); text(c, s, lx(v), ys + 50, 24, ORANGE if abs(v - D_BEST) < 1e-6 else MUTE, 600, "c")
    rx = 1100; text(c, "hole", rx, 222, 30, MUTE, 500); text(c, f"{d:.2f} mm", rx, 300, 84, INK, 800); text(c, f"f/{F_MM / d:.0f}", rx + 430, 300, 56, ORANGE, 700)
    text(c, "exposure in full sun, ISO 400 film", rx, 356, 28, MUTE, 500); text(c, fmt_s(sun_seconds(d)), rx + 475, 358, 36, INK, 700)
    px0, px1, py0, py1 = rx + 20, rx + 690, 430, 770; X = lambda v: px0 + (px1 - px0) * (math.log(D_HI * 1.15) - math.log(v)) / (math.log(D_HI * 1.15) - math.log(D_LO / 1.15)); Y = lambda b: py1 - (py1 - py0) * min(b, 2.3) / 2.3
    line(c, px0, py1, px1, py1, MUTE, 2); line(c, px0, py0, px0, py1, MUTE, 2); text(c, "blur on the film, mm", px0 + 10, py0 - 6, 24, MUTE, 500); text(c, "bigger hole", px0, py1 + 34, 22, MUTE, 500); text(c, "smaller hole", px1, py1 + 34, 22, MUTE, 500, "r")
    for b in (1, 2): line(c, px0, Y(b), px1, Y(b), LINE, 1); text(c, str(b), px0 - 12, Y(b) + 8, 22, MUTE, 500, "r")
    vs = [math.exp(math.log(D_HI) + (math.log(D_LO) - math.log(D_HI)) * i / 120) for i in range(121)]
    for fn, k2, dash, w in ((lambda v: blur_mm(v)[0], YEL, [10, 8], 3), (lambda v: blur_mm(v)[1], CYAN, [10, 8], 3), (lambda v: math.hypot(*blur_mm(v)), INK, None, 4.5)):
        p = skia.Path(); p.moveTo(X(vs[0]), Y(fn(vs[0]))); [p.lineTo(X(v), Y(fn(v))) for v in vs[1:]]; c.drawPath(p, stroke(k2, w, 1, dash))
    text(c, "the hole's own size", X(1.25), Y(1.25) - 34, 24, YEL, 600, "l"); text(c, "light spreading", X(0.085), Y(1.15), 24, CYAN, 600, "r"); text(c, "(diffraction)", X(0.085), Y(1.15) + 28, 24, CYAN, 600, "r")
    line(c, X(D_BEST), py1, X(D_BEST), Y(math.hypot(*blur_mm(D_BEST))) + 10, ORANGE, 2, 1, [6, 6]); text(c, "sharpest", X(D_BEST), py1 + 34, 24, ORANGE, 700, "c"); dot(c, X(d), Y(math.hypot(*blur_mm(d))), 11, ORANGE, glow=10)
    a = ease(ramp(t, 41.2, 42.2)); text(c, f"best hole = 1.9 × √(distance × wavelength) = 1.9 × √({F_MM:.1f} mm × 0.00055 mm) = {D_BEST:.2f} mm", W / 2, 922, 27, YEL, 600, "c", a)
    captions(c, t, [(0.3, 7.6, "How big should the hole be? A big hole is bright, but each point of the scene lands as a disc the size of the hole."), (8.0, 21.6, "Make it smaller and the picture gets sharper, and dimmer: the exposure gets longer."),
                    (22.0, 28.8, "For this camera, 28.7 mm from hole to film, the sharpest hole is about a quarter of a millimetre."), (29.2, 38.0, "Smaller still and it gets worse again. Light spreads out as it squeezes through a tiny hole."), (38.4, 47, "So a pinhole has a best size. The picture can never be sharper than that, which is why a lens was worth inventing.")], y=972, size=38)

def s_time(c, t):
    card(c, model("l1_time1", dict(G_UP=10, G_OLD=[], G_NEW=R1, G_VECS=[[0, 0, 0]] * 8), (6, 20, 10, 62, 0, 205, 335)), 130, 230, 760, ease(ramp(t, 0.1, 0.9)))
    x = 1010; text(c, "A hole this small lets in very little light", x, 250, 38, INK, 700, "l", ease(ramp(t, 0.3, 1.0)))
    for i, (lab, v) in enumerate((("a hole of 2 mm: bright, and blurred", (2 / D_BEST) ** 2), ("a hole of 1 mm", (1 / D_BEST) ** 2), (f"this camera's hole, {D_BEST:.2f} mm", 1))):
        a = ease(ramp(t, 1.2 + i * 1.4, 2.0 + i * 1.4)); y = 330 + i * 100; g = ease(ramp(t, 1.4 + i * 1.4, 2.6 + i * 1.4)); w = max(4, 640 * v / (2 / D_BEST) ** 2 * g)
        text(c, lab, x, y, 28, MUTE, 500, "l", a); rrect(c, x, y + 14, w, 30, 4, ORANGE if i == 2 else CYAN, a); text(c, f"{v:.0f}×" if i < 2 else "1×", x + w + 16, y + 40, 30, INK, 700, "l", a)
    a = ease(ramp(t, 8.6, 9.4)); text(c, "So a picture is counted, not snapped.", x, 668, 32, INK, 600, "l", a)
    for i, (k, v) in enumerate((("full sun", "open and shut"), ("cloud", "count 1"), ("shade", "count 3"), ("by a window", "count 20"))):
        a = ease(ramp(t, 11.6 + i * 0.7, 12.2 + i * 0.7)); bx = x + (i % 2) * 400; by = 706 + (i // 2) * 84; rrect(c, bx, by, 380, 66, 12, PANEL, a, outline=LINE); text(c, k, bx + 20, by + 43, 26, MUTE, 500, "l", a); text(c, v, bx + 360, by + 43, 28, INK, 700, "r", a)
    text(c, "counts are seconds; ISO 400 film; camera standing on something steady", x, 902, 22, MUTE, 500, "l", ease(ramp(t, 14.6, 15.2)))
    captions(c, t, [(0.6, 11.0, "The price of sharpness is light. A hole a quarter of a millimetre wide passes about seventy times less light than a hole of two millimetres."), (11.4, 26, "So the camera stands on something steady. You lift the slide, count, and push it down. That count is the exposure.")], y=985, size=38)
RING = 14; P1J = json.load(open("build/plate1.json"))["open"]
def s_kit(c, t):
    k = min(RING - 1, int(ease(ramp(t, 1.2, 4.2)) * (RING - 1) + 0.5)); v = 34 * (1 - k / (RING - 1))
    card(c, model(f"l1_ring1_{k:02d}", dict(G_OLD=[], G_NEW=R1, G_VECS=[[0, 0, 0]] * 7 + [[0, v, 0]]), (12, 40, 0, 62, 0, 232, 300)), 130, 230, 760, ease(ramp(t, 0.1, 0.9)))
    x = 1010; text(c, "In your kit: the first plate", x, 270, 42, INK, 700, "l", ease(ramp(t, 0.3, 1.0)))
    for i, s in enumerate(("The purple plate goes on the dark box. A black slide lies behind it.", "Cut a square of kitchen foil, 15 mm across. Prick it once with the very tip of a needle.", "Lay it over the round pocket and press the ring in over it.", "Lift the slide: open. Push it down: shut.")):
        a = ease(ramp(t, 4.4 + i * 1.3, 5.1 + i * 1.3)); y = 350 + i * 104; c.drawCircle(x + 24, y + 6, 24, fill(ORANGE, a)); text(c, str(i + 1), x + 24, y + 17, 30, WHITE, 800, "c", a); para(c, s, x + 68, y + 4, 31, 760, INK, 500, "l", a)
    para(c, f"By the model, the hole lights {P1J['picture_lit_pct']:.1f} % of the picture.", x, 786, 26, 800, MUTE, 500, "l", ease(ramp(t, 10, 10.8)))
    captions(c, t, [(0.6, 9.6, "Your camera starts as a dark box with a purple plate on its front: a pocket for a pinhole in foil, and a slide to open and shut it."), (10.0, 22, "No lens, no shutter, no dial. Take a picture with nothing but a hole. The lens comes next, and you will know what it is for.")], y=985, size=38)
def s_try(c, t):
    text(c, "So how does a hole make a picture?", W / 2, 170, 34, ORANGE, 700, "c", window(t, 0.3, 30, 0.5)); text(c, "It lets each part of the film see only one point of the world.", W / 2, 228, 44, INK, 700, "c", window(t, 1.2, 30, 0.6))
    for i, (hd, k, s) in enumerate((("Look", GREEN, "On a sunny day, stand under a leafy tree. Every round spot of light on the ground is a picture of the sun."), ("Try", ORANGE, "A box, a pin, a piece of tracing paper. Point the hole at a window and look at the paper from behind."),
                                    ("Next", CYAN, "Lesson 2: why a lens? The same picture, fifty times brighter, and what it costs."))):
        a = ease(ramp(t, 4.0 + i * 5.0, 4.8 + i * 5.0)); x = 150 + i * 550; rrect(c, x, 300, 510, 400, 20, PANEL, a, outline=LINE); rrect(c, x + 36, 338, 118 if i != 1 else 96, 46, 23, k, a); text(c, hd, x + 60, 371, 28, WHITE, 800, "l", a); para(c, s, x + 36, 446, 33, 440, INK, 500, "l", a, 1.4)
    a = window(t, 19.5, 30, 0.6); para(c, f"Every picture in this film is drawn or simulated from the CURVE 35 model ({MODEL}). The camera has not been printed yet, and no photograph appears here.", W / 2, 800, 27, 1300, MUTE, 500, "c", a)
    text(c, "CURVE 35", W / 2, 940, 46, INK, 800, "c", a); text(c, "Variadic Group LLC", W / 2, 984, 24, MUTE, 500, "c", a)

H1 = hist([0, 1], intro=("People have known this for about 2,400 years.", "For most of them, nobody could make the picture stay.")); H2 = hist([2]); H3 = hist([3, 4, 5]); H4 = hist([6])
LESSON1 = dict(n=1, title="A picture from a hole", scenes=[("hook", "A camera with no lens", 19, s_hook), ("nohole", "Why film alone sees nothing", 20, s_nohole), ("hole", "The hole", 34, s_hole),
                                                             ("noticed", "Who noticed first", H1[1], H1[0]), ("proved", "Who proved it", H2[1], H2[0]), ("size", "How big a hole?", 47, s_size), ("used", "What people did with it", H3[1], H3[0]),
                                                             ("time", "How long?", 26, s_time), ("stay", "Making the picture stay", H4[1], H4[0]), ("kit", "In your kit", 22, s_kit), ("try", "The answer; look, try, next", 30, s_try)])
LESSONS = {1: LESSON1}

def chrome(c, L, i, t):
    text(c, "CURVE 35", 70, 78, 26, ORANGE, 800); w = font(26, 800).measureText("CURVE 35"); text(c, f"Lesson {L['n']}  ·  {L['title']}", 70 + w + 18, 78, 26, MUTE, 500); text(c, f"{i + 1}  ·  {L['scenes'][i][1]}", W - 70, 78, 26, INK, 600, "r")
    tot = sum(s[2] for s in L["scenes"]); x = 70.0
    for j, s in enumerate(L["scenes"]):
        w = (W - 140 - 6 * (len(L["scenes"]) - 1)) * s[2] / tot; rrect(c, x, 1056, w, 5, 2.5, LINE)
        if j < i: rrect(c, x, 1056, w, 5, 2.5, MUTE)
        if j == i: rrect(c, x, 1056, max(5, w * clamp(t / s[2])), 5, 2.5, ORANGE)
        x += w + 6
def frame(L, i, t, surf=None):
    surf = surf or skia.Surface(W, H); c = surf.getCanvas(); c.clear(BG); name, title, dur, fn = L["scenes"][i]; fn(c, L["warp"][i](t) if "warp" in L else t); chrome(c, L, i, t)
    if i == 0 and t < 0.5: c.drawRect(skia.Rect.MakeWH(W, H), fill(col("000000"), 1 - t / 0.5))
    if i == len(L["scenes"]) - 1 and t > dur - 0.8: c.drawRect(skia.Rect.MakeWH(W, H), fill(col("000000"), (t - dur + 0.8) / 0.8))
    return surf
def ev_say(k): yr, who, txt = EVENTS[k]; return f"{yr}. {who}. {txt}"
VO = {"hook": [(0.3, "This camera has no lens."), (4.4, "No glass. No battery. No sensor."), (9.6, "Just a hole, a quarter of a millimetre wide."), (13.0, "So how does a hole make a picture?")],
      "noticed": [(0.2, "People have known this for about 2,400 years. For most of them, nobody could make the picture stay."), (EV_0, ev_say(0)), (EV_0 + EV_T, ev_say(1))],
      "proved": [(1.0, ev_say(2))], "used": [(1.0 + j * EV_T, ev_say(k)) for j, k in enumerate((3, 4, 5))], "stay": [(1.0, ev_say(6))],
      "try": [(0.3, "So how does a hole make a picture? It lets each part of the film see only one point of the world."), (4.0, "Look. On a sunny day, stand under a leafy tree. Every round spot of light on the ground is a picture of the sun."),
              (9.0, "Try. A box, a pin, a piece of tracing paper. Point the hole at a window and look at the paper from behind."), (14.0, "Next, lesson two: why a lens? The same picture, far brighter, and what it costs."),
              (19.5, "Every picture in this film is drawn or simulated from the model. The camera has not been printed yet.")]}
def plan(L):
    """give every scene its spoken lines (its own captions, unless VO names others), make the sound of each, and stretch the scene wherever a line needs longer than the picture gave it"""
    import voice as VC; global captions
    L["warp"] = {}; L["audio"] = {}; real = captions
    for i, (name, title, D, fn) in enumerate(L["scenes"]):
        lines = VO.get(name)
        if lines is None:
            got = []; captions = lambda c, t, caps, **k: got.extend(caps); fn(skia.Surface(16, 16).getCanvas(), 0.0); captions = real; lines = [(a, s_) for a, b, s_ in got]
        starts = [a for a, _ in lines]; wav = [VC.say(tx) for _, tx in lines]; seg = [(a, (starts[k + 1] if k + 1 < len(starts) else D) - a) for k, a in enumerate(starts)]; new = [max(l, d + 0.55) for (a, l), (f, d) in zip(seg, wav)]
        A = [starts[0]]; [A.append(A[-1] + x) for x in new[:-1]]; Dn = math.ceil((A[-1] + new[-1]) * FPS) / FPS
        def w(t, starts=starts, seg=seg, new=new, A=A, D=D):
            if t <= starts[0]: return t
            for (a, l), n_, s0 in zip(seg, new, A):
                if t < s0 + n_: return a + (t - s0) * l / n_
            return D
        L["warp"][i] = w; L["audio"][i] = [(s0 + 0.15, f) for s0, (f, d) in zip(A, wav)]; L["scenes"][i] = (name, title, Dn, fn)
    return L
def encode(L, i):
    name, title, dur, fn = L["scenes"][i]; final = f"{OUT}/l{L['n']}_{i + 1}_{name}.mp4"; tmp = final[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for k in range(round(dur * FPS)): frame(L, i, k / FPS, surf); p.stdin.write(surf.toarray().tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, final)
    else: raise RuntimeError(final)
    return final
def build(n, only=None):
    import voice as VC
    L = plan(LESSONS[n]); files = []; wavs = []; os.makedirs(f"{OUT}/clips", exist_ok=True)
    for i, s in enumerate(L["scenes"]):
        f = f"{OUT}/l{n}_{i + 1}_{s[0]}.mp4"; wv = VC.track(L["audio"][i], round(s[2] * FPS) / FPS, f"{OUT}/l{n}_{i + 1}_{s[0]}.wav")
        if (only is None or s[0] in only or not os.path.exists(f)) and only != ["join"]: f = encode(L, i); print("scene", s[0], "written", flush=True)
        VC.mux(f, wv, f"{OUT}/clips/l{n}_{i + 1}_{s[0]}.mp4"); files.append(f); wavs.append(wv)                    # each chapter is also a clip of its own, with its sound
    lst = f"{OUT}/l{n}.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(f)}'\n" for f in files)); out = f"build/CURVE-35_lesson_{n:02d}_{L['title'].lower().replace(' ', '_')}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{OUT}/l{n}_silent.mp4"], check=True); VC.mux(f"{OUT}/l{n}_silent.mp4", VC.join(wavs, f"{OUT}/l{n}.wav"), out)
    t = 0; ch = []
    for s in L["scenes"]: ch.append((f"{int(t // 60)}:{int(t % 60):02d}", s[1])); t += s[2]
    json.dump(dict(file=out, seconds=t, chapters=ch), open(f"{OUT}/l{n}_chapters.json", "w"), indent=1); print(out, f"{t:.0f} s"); return out
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    if len(sys.argv) > 2 and sys.argv[2] == "frames":      # full-size test frames: scene:seconds ...
        for a in sys.argv[3:]:
            s, t = a.split(":"); i = [q[0] for q in LESSONS[n]["scenes"]].index(s); frame(LESSONS[n], i, float(t)).makeImageSnapshot().save(f"{OUT}/test_{s}_{float(t):05.1f}.png", skia.kPNG)
        print("frames written")
    else: build(n, sys.argv[2:] or None)
