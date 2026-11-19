"""The kit booklet: what is in the bag, build, film in, take pictures, film out.  Pictures first, very few words.
Half-letter landscape pages (8.5 x 5.5 in), 20 of them: print as a booklet, fold, staple.  NAME is the only place the product name lives."""
import os, json, math
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader, simpleSplit
from PIL import Image, ImageChops
NAME = "CURVE 35"; MODEL = "ONE-135 v2.16"; PREV = "v2.15"; TAG = "Build your own film camera"
F = "/usr/share/fonts/truetype/liberation/LiberationSans-"
for n, f in (("LS", "Regular"), ("LSB", "Bold")): pdfmetrics.registerFont(TTFont(n, F + f + ".ttf"))
W, H = 612, 396; M = 22
INK = colors.HexColor("#17191d"); GREY = colors.HexColor("#6a6f78"); BOX = colors.HexColor("#e8f1fb"); BOXL = colors.HexColor("#9fbbe0"); YEL = colors.HexColor("#ffd23f")
SEC = {"THE HOLE": colors.HexColor("#8e44ad"), "BUILD": colors.HexColor("#e8641b"), "FILM IN": colors.HexColor("#2a78d6"), "PHOTOS": colors.HexColor("#1b9e62"), "FILM OUT": colors.HexColor("#7a4fd0"), "CARE": colors.HexColor("#6a6f78"), "KNOW": colors.HexColor("#3b4a5a")}
G = "build/booklet/"; T = G + "trim/"; os.makedirs(T, exist_ok=True)
def trim(name, pad=14):
    out = T + name + ".png"; src = G + name + ".png"
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(src): return out
    im = Image.open(src).convert("RGB"); box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))).save(out); return out
def fit(c, path, x, y, w, h):
    iw, ih = Image.open(path).size; s = min(w / iw, h / ih); c.drawImage(ImageReader(path), x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s); return (x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s)
PARTS = [('body', 'body'), ('spool', 'spool'), ('knob', 'wind knob'), ('roller', 'frame wheel'), ('back', 'back'), ('front', 'front plate'), ('blade', 'shutter'), ('wheel', 'aperture wheel')]
NUM = {p[0]: i + 1 for i, p in enumerate(PARTS)}; THUMB = {**{p[0]: "p_" + p[0] for p in PARTS}, "lens": "lens", "cassette": "cassette", "plate1": "p_plate1", "slide1": "p_slide1", "pinring": "p_pinring", "pindisc": "p_pindisc"}
# QR codes: short links on curve35.com (site/build.py SHORT writes them to dist/_redirects as 302s to the page's routes).
# segno, error level M, a quiet zone of 2 modules on a white ground, the code itself at least 15 mm.  Every path used is listed in build/booklet/qr_paths.json for the check.
SITE = "curve35.com"; QR_USED = []
def qr(c, path, x, y, size, label=True, fs=6.6):
    """The code with its quiet zone, bottom-left corner at (x, y); size: the code alone, in points (15 mm = 42.5 pt).  The short address under it.  Returns the outer width."""
    import segno
    q = segno.make(f"https://{SITE}/{path}", error="m", micro=False, boost_error=False); n = q.symbol_size(border=0)[0]; mod = size / n; qz = 2 * mod; o = size + 2 * qz
    assert size >= 42.5, f"QR {path}: {size / 72 * 25.4:.1f} mm is under 15 mm"
    c.saveState(); c.setFillColor(colors.white); c.rect(x, y, o, o, fill=1, stroke=0); c.setFillColor(colors.black)
    for r, row in enumerate(q.matrix):
        for k, v in enumerate(row):
            if v: c.rect(x + qz + k * mod, y + o - qz - (r + 1) * mod, mod + 0.02, mod + 0.02, fill=1, stroke=0)
    if label: c.setFillColor(INK); c.setFont("LSB", fs); c.drawCentredString(x + o / 2, y - fs - 0.5, f"{SITE}/{path}")
    c.restoreState(); QR_USED.append({"path": path, "data": f"https://{SITE}/{path}", "mm": round(size / 72 * 25.4, 1), "version": q.version, "error": q.error}); return o
def tag(c, sec, page):
    c.setFillColor(SEC[sec]); c.roundRect(M, H - M - 15, 8 + pdfmetrics.stringWidth(sec, "LSB", 9.5) + 8, 15, 7.5, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 9.5); c.drawString(M + 8, H - M - 11.3, sec)
    c.setFillColor(GREY); c.setFont("LS", 8); c.drawRightString(W - M, 10, str(page)); c.drawString(M, 10, NAME)
def callout(c, items, xr, ytop):
    cw = 46; bw = len(items) * cw + 8; bh = 54; x0 = xr - bw
    c.setFillColor(BOX); c.setStrokeColor(BOXL); c.setLineWidth(0.8); c.roundRect(x0, ytop - bh, bw, bh, 7, fill=1, stroke=1)
    for i, (k, q) in enumerate(items):
        cx = x0 + 5 + i * cw; fit(c, trim(THUMB[k], 6), cx, ytop - bh + 15, cw - 6, bh - 19); c.setFillColor(INK); c.setFont("LSB", 9.5); c.drawString(cx + 1, ytop - bh + 5, f"{q}x")
        if k in NUM: badge(c, cx + cw - 15, ytop - bh + 8.5, NUM[k], 5.6, 7)
def badge(c, x, y, n, r=7, fs=8.5, col=None):
    c.setFillColor(col or INK); c.circle(x, y, r, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", fs); c.drawCentredString(x, y - fs * 0.35, str(n))
def burst(c, x, y, word="CLICK", r=17):
    pts = [(x + (r if i % 2 == 0 else r * 0.72) * math.cos(i * math.pi / 9), y + (r if i % 2 == 0 else r * 0.72) * math.sin(i * math.pi / 9)) for i in range(18)]
    p = c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close(); c.setFillColor(YEL); c.setStrokeColor(INK); c.setLineWidth(0.8); c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(INK); c.setFont("LSB", 6.6 if len(word) > 4 else 8); c.drawCentredString(x, y - 2.5, word)
def pill(c, x, y, s, col=INK, fs=11):
    w = pdfmetrics.stringWidth(s, "LSB", fs) + 14; c.setFillColor(col); c.roundRect(x, y, w, fs + 7, (fs + 7) / 2, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", fs); c.drawString(x + 7, y + 4.4, s); return w
def sun(c, x, y, r=7):
    c.setFillColor(YEL); c.setStrokeColor(INK); c.setLineWidth(0.9); c.circle(x, y, r, fill=1, stroke=1)
    for i in range(8): a = i * math.pi / 4; c.line(x + (r + 2.5) * math.cos(a), y + (r + 2.5) * math.sin(a), x + (r + 6) * math.cos(a), y + (r + 6) * math.sin(a))
def cloud(c, x, y, s=1.0):
    c.setFillColor(colors.HexColor("#dfe5ee")); c.setStrokeColor(INK); c.setLineWidth(0.9)
    for dx, dy, r in ((-7, 0, 6), (0, 4, 8), (8, 0, 6.5), (1, -2, 7)): c.circle(x + dx * s, y + dy * s, r * s, fill=1, stroke=0)
    p = c.beginPath(); p.arc(x - 13 * s, y - 6 * s, x - 1 * s, y + 6 * s, 90, 180); p.arc(x - 8 * s, y - 4 * s, x + 8 * s, y + 12 * s, 20, 140); p.arc(x + 1.5 * s, y - 6.5 * s, x + 14.5 * s, y + 6.5 * s, -90, 180); c.drawPath(p, fill=0, stroke=1); c.line(x - 7 * s, y - 6 * s, x + 8 * s, y - 6.5 * s)
def pin(c, x, y):
    c.setFillColor(INK); c.circle(x, y, 9, fill=1, stroke=0); c.setFillColor(colors.white); c.circle(x, y, 1.6, fill=1, stroke=0)
def haze(c, x, y): sun(c, x, y, 6); c.setStrokeColor(colors.HexColor("#b9c0cb")); c.setLineWidth(2.2); [c.line(x - 12, y - 3 + 4 * k, x + 12, y - 3 + 4 * k) for k in range(3)]
def dull(c, x, y):
    for col, dx, dy in (("#aab2be", 3, 2), ("#7f8896", -2, -2)):
        c.setFillColor(colors.HexColor(col))
        for ex, ey, r in ((-7, 0, 6), (0, 4, 8), (8, 0, 6.5), (1, -2, 7)): c.circle(x + dx + ex, y + dy + ey, r, fill=1, stroke=0)
def shade(c, x, y):
    sun(c, x + 8, y + 6, 4); c.setFillColor(colors.HexColor("#5b3a26")); c.rect(x - 4.5, y - 11, 3, 10, fill=1, stroke=0); c.setFillColor(colors.HexColor("#2f6b45")); [c.circle(x + dx, y + dy, r, fill=1, stroke=0) for dx, dy, r in ((-7, 0, 6), (1, 1, 7), (-3, 6, 6))]
def clock(c, x, y, r=7.5):
    c.setFillColor(colors.white); c.setStrokeColor(SEC["PHOTOS"]); c.setLineWidth(1.6); c.circle(x, y, r, fill=1, stroke=1); c.line(x, y, x, y + r * 0.62); c.line(x, y, x + r * 0.45, y - r * 0.2); c.setFillColor(SEC["PHOTOS"]); c.rect(x - 1.5, y + r, 3, 2.6, fill=1, stroke=0)
EXPO = json.load(open("build/exposure.json"))["coverage"]; LIGHTS = [("full sun", sun, "full sun"), ("hazy sun", haze, "hazy sun"), ("bright cloud", cloud, "cloud"), ("overcast", dull, "dull"), ("open shade", shade, "shade")]; ISOS = ["100", "200", "400"]
DOT = {"small": 2.6, "middle": 4.4, "large": 6.4}
def which(iso, light):
    d = EXPO[iso][light]; t = d["typical"]; return ("T", 0.0) if t < -1.0 else (d["hole"], t)          # the model's stops over or under on a typical printer; more than one stop under is too dark for a snap
TIMES = {"100": (4, 20, 80), "200": (2, 10, 40), "400": (1, 5, 20)}; ROOMS = ("by a window", "room lights on", "dim room")      # small dot; they lean long on purpose
PINS = {"100": ("1", "3", "15", "4 min"), "200": ("open, shut", "2", "8", "90"), "400": ("open, shut", "1", "3", "40")}; PINL = ("full sun", "cloud", "shade", "indoors")   # v2.16: tools/pinhole.py, the 0.25 mm disc at 28.9 mm (f/116), with the film's slowing on long exposures; rounded long
def chart(c, x0, ytop, cw=42, rh=44, lab=44, fs=8, k=1.0, isos=None):
    IS = isos or ISOS
    for j, (L, ic, nm) in enumerate(LIGHTS):
        cx = x0 + lab + j * cw + cw / 2; ic(c, cx, ytop - 16); c.setFillColor(GREY); c.setFont("LS", fs); c.drawCentredString(cx, ytop - 40, nm)
    for i, iso in enumerate(IS):
        y = ytop - 48 - (i + 1) * rh; c.setFillColor(INK); c.setFont("LSB", 10.5 * k); c.drawString(x0, y + rh / 2 + 1, "ISO"); c.drawString(x0, y + rh / 2 - 11 * k, iso)
        for j, (L, ic, nm) in enumerate(LIGHTS):
            hole, t = which(iso, L); bx = x0 + lab + j * cw
            c.setFillColor(colors.white if hole == "T" else colors.HexColor("#fff3c4") if t < 0 else BOX); c.setStrokeColor(BOXL); c.setLineWidth(0.6); c.roundRect(bx + 2, y + 2, cw - 4, rh - 4, 5, fill=1, stroke=1)
            if hole == "T": clock(c, bx + cw / 2, y + rh / 2 - 1, 7.5 * k)
            else: c.setFillColor(INK); c.circle(bx + cw / 2, y + rh / 2, DOT[hole] * k, fill=1, stroke=0)
    return ytop - 48 - len(IS) * rh
def legend(c, x0, y, fs=9):
    c.setFillColor(INK); [c.circle(x0 + 5 + dx, y + 3, r, fill=1, stroke=0) for dx, r in ((0, 2.6), (12, 4.4), (28, 6.4))]; c.setFont("LS", fs); c.drawString(x0 + 44, y, "slide the handle to this dot")
    clock(c, x0 + 16, y - 15, 6); c.setFillColor(INK); c.setFont("LS", fs); c.drawString(x0 + 44, y - 18, "too dark for a snap: a time picture")
    c.setFillColor(colors.HexColor("#fff3c4")); c.setStrokeColor(BOXL); c.roundRect(x0 + 4, y - 40, 26, 13, 3, fill=1, stroke=1); c.setFillColor(INK); c.drawString(x0 + 44, y - 37, "works; the picture comes out a little dark")
def table3(c, x0, y, rows, heads, colw, lab=50, fs=9, rh=14, title=None):
    if title: c.setFillColor(INK); c.setFont("LSB", fs + 0.5); c.drawString(x0, y + rh + 4, title)
    c.setFillColor(GREY); c.setFont("LS", fs - 1)
    for j, hd in enumerate(heads): c.drawCentredString(x0 + lab + j * colw + colw / 2, y, hd)
    for i, (k, vals) in enumerate(rows):
        yy = y - (i + 1) * rh; c.setFillColor(BOX if i % 2 == 0 else colors.white); c.rect(x0 - 3, yy - 3.5, lab + colw * len(heads) + 6, rh, fill=1, stroke=0); c.setFillColor(INK); c.setFont("LSB", fs); c.drawString(x0, yy, "ISO " + k)
        for j, v in enumerate(vals): c.drawCentredString(x0 + lab + j * colw + colw / 2, yy, str(v))
    return y - (len(rows) + 1) * rh
def step(c, num, img, x, y, w, h, items=None, cap=None, bursts=(), extra=None, col=INK, top=58, check=None, code=None):
    c.setFillColor(col); c.setFont("LSB", 40); c.drawString(x, y + h - 36, str(num)); qw = 0
    if code: S = 43.5; o = S * 29 / 25; qw = qr(c, code, x + w - o, y + h - o, S, fs=6.2) + 6      # 15.3 mm; the outer box is S plus 2 modules a side (25 modules for bN)
    if items: callout(c, items, x + w - qw, y + h)
    ch = 0
    if cap:
        lines = simpleSplit(cap, "LS", 10.5, w); cl = simpleSplit(check, "LS", 9.5, w - 16) if check else []; ch = 13 * len(lines) + 3 + (12 * len(cl) + 4 if cl else 0); c.setFillColor(INK); c.setFont("LS", 10.5)
        for i, ln in enumerate(lines): c.drawString(x, y + ch - 12 - 13 * i, ln)
        if cl:
            y1 = y + 12 * len(cl) - 6; c.setStrokeColor(SEC["PHOTOS"]); c.setLineWidth(1.8); c.line(x + 1, y1 + 3, x + 4, y1); c.line(x + 4, y1, x + 10, y1 + 7); c.setFillColor(colors.HexColor("#14774a")); c.setFont("LS", 9.5)
            for i, ln in enumerate(cl): c.drawString(x + 16, y + 12 * (len(cl) - 1 - i) + 2, ln)
    bx = fit(c, trim(img), x, y + ch, w, h - top - ch)
    for (fx, fy, word) in bursts: burst(c, bx[0] + fx * bx[2], bx[1] + fy * bx[3], word)
    if extra: extra(c, bx)
    return bx
def two(c, sec, page, a, b):
    tag(c, sec, page); w = (W - 2 * M - 18) / 2; h = H - 2 * M - 26
    for i, s in enumerate((a, b)):
        if s: step(c, x=M + i * (w + 18), y=M + 4, w=w, h=h, col=SEC[sec], **s)
    c.showPage()
def build():
    c = canvas.Canvas("build/booklet/_master.pdf", pagesize=(W, H)); c.setTitle(f"{NAME} kit booklet"); c.setAuthor("Variadic Group LLC")
    # 1 cover
    c.setFillColor(colors.HexColor("#fff4e6")); c.rect(0, 0, W, H, fill=1, stroke=0); c.setFillColor(SEC["BUILD"]); c.rect(0, H - 86, W, 86, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("LSB", 46); c.drawString(M + 6, H - 60, NAME); c.setFont("LS", 15); c.drawString(M + 8, H - 79, TAG)
    fit(c, trim("hero"), 150, 6, W - 170, H - 100); x = M + 6
    c.setFillColor(INK); c.setFont("LSB", 11); c.drawString(M + 6, 238, "Start here"); c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(M + 6, 227, "every step as a film")
    qr(c, "start", M + 6, 148, 62, fs=7.5)
    for s in ("9 pieces", "no tools", "no glue"): c.setFillColor(INK); pill(c, x, 104 - 0, s, INK, 11); x += 0; c.translate(0, -24)
    c.translate(0, 72); c.setFillColor(GREY); c.setFont("LS", 8.5); c.drawString(M + 6, 28, "takes 35 mm film"); c.drawString(M + 6, 16, "ages 14 and up"); c.showPage()
    # 2 in the bag
    tag(c, "BUILD", 2); c.setFillColor(INK); c.setFont("LSB", 20); c.drawString(M + 78, H - M - 14, "In the bag")
    cw = (W - 2 * M) / 5; chh = 132
    for i, (k, nm) in enumerate(PARTS + [("lens", "lens")]):
        x0 = M + (i % 5) * cw; y0 = H - M - 40 - (i // 5 + 1) * chh; fit(c, trim(THUMB[k], 8), x0 + 6, y0 + 24, cw - 12, chh - 34)
        if k in NUM: badge(c, x0 + 15, y0 + 13, NUM[k])
        c.setFillColor(INK); c.setFont("LSB", 10); c.drawString(x0 + 27, y0 + 9.5, "1x"); c.setFillColor(GREY); c.setFont("LS", 9); c.drawString(x0 + 44, y0 + 9.5, nm)
    x0 = M + 4 * cw; y0 = H - M - 40 - 2 * chh; c.setFillColor(INK); c.setFont("LSB", 10); c.drawString(x0 + 12, y0 + 66, "Spares"); c.setFillColor(GREY); c.setFont("LS", 9)      # the empty fifth cell of the second row
    for i, tx in enumerate(("1x wind knob", "1x shutter")): c.drawString(x0 + 12, y0 + 50 - 13 * i, tx)
    fit(c, trim("p_pinring", 6), x0 + 4, y0 + 4, 20, 22); fit(c, trim("p_pindisc", 6), x0 + 22, y0 + 4, 16, 22); c.setFillColor(INK); c.setFont("LSB", 8.6); c.drawString(x0 + 40, y0 + 18, "pinhole ring + disc"); c.setFillColor(GREY); c.setFont("LS", 7.6); c.drawString(x0 + 40, y0 + 8, "for the pinhole"); c.drawString(x0 + 40, y0 - 1, "experiment: page 15")
    c.setStrokeColor(BOXL); c.setLineWidth(0.8); c.setFillColor(BOX); c.roundRect(M, M + 2, W - 2 * M, 44, 8, fill=1, stroke=1); fit(c, trim("cassette", 6), M + 8, M + 5, 40, 38)
    c.setFillColor(INK); c.setFont("LSB", 11); c.drawString(M + 56, M + 27, "Film: any 35 mm film.  A roll is in the starter kit."); c.setFillColor(GREY); c.setFont("LS", 9.5); c.drawString(M + 56, M + 13, "The dot chart in this guide is for ISO 400 film.")
    c.setFont("LS", 7.6); c.drawRightString(W - M - 8, M + 27, "In your bag the shutter and the aperture wheel are black:"); c.drawRightString(W - M - 8, M + 18, "they keep light off the film. They are drawn in colour"); c.drawRightString(W - M - 8, M + 9, "here so you can follow them."); c.showPage()
    # build, film in, pictures, film out: from the master list in tools/steps.py
    from steps import STEPS, WEB
    w = (W - 2 * M - 18) / 2; h = H - 2 * M - 26; page = [3]
    def panel(st, i):
        extra = None
        def inset(c, bx, col, word):
            path = trim("dial", 2); wI = 96; hI = wI * 0.72; x = bx[0] + bx[2] - wI - 2; y = bx[1] + 2; c.saveState(); pth = c.beginPath(); pth.roundRect(x, y, wI, hI, 7); c.clipPath(pth, stroke=0, fill=0); iw, ih = Image.open(path).size; sc = wI / (iw * 0.62)
            c.drawImage(ImageReader(path), x - iw * 0.20 * sc, y - ih * 0.12 * sc, iw * sc, ih * sc); c.restoreState(); c.setStrokeColor(col); c.setLineWidth(1.6); c.roundRect(x, y, wI, hI, 7, fill=0, stroke=1); pill(c, x + 4, y + hI - 14, word, col, 8)
        def focusbar(c, bx, col):
            """How far away: a strip under the aiming picture.  Soft up to the small dot's near limit, sharp with the small dot from there, sharp with any dot from the large dot's near limit on."""
            FO = json.load(open("build/exposure.json"))["focus"]; n0, n1 = round(FO["small"]["sharp_from_m"], 1), round(FO["large"]["sharp_from_m"], 1); x0 = M + i * (w + 18) + 16; x1 = x0 + w - 34; yb = bx[1] + bx[3] + 13; k = (x1 - x0) / 5.0; X = lambda m: x0 + k * m
            c.setFillColor(INK); c.setFont("LSB", 8.5); c.drawString(x0 - 16, yb + 26, "How far away?"); c.setFont("LS", 8.5); c.drawString(x0 + 52, yb + 26, f"Two big steps ({n1:.0f} m) or more.")
            c.setFillColor(GREY); c.setFont("LS", 7.6); c.drawString(x0 - 16, yb + 15, f"With the small dot, in sun, from {n0} m. Nearer than that, the picture is soft.")
            c.setFillColor(colors.HexColor("#d9dce1")); c.rect(X(0), yb, X(n0) - X(0), 9, fill=1, stroke=0); c.setFillColor(colors.HexColor("#a9dcc0")); c.rect(X(n0), yb, X(n1) - X(n0), 9, fill=1, stroke=0); c.setFillColor(col); c.rect(X(n1), yb, x1 - X(n1), 9, fill=1, stroke=0)
            pth = c.beginPath(); pth.moveTo(x1, yb - 2.5); pth.lineTo(x1 + 9, yb + 4.5); pth.lineTo(x1, yb + 11.5); pth.close(); c.drawPath(pth, fill=1, stroke=0)
            c.setFillColor(INK); c.roundRect(X(0) - 13, yb - 1, 11, 11, 2, fill=1, stroke=0); c.setFillColor(colors.white); c.circle(X(0) - 7.5, yb + 4.5, 2.6, fill=1, stroke=0)
            c.setFillColor(GREY); c.setFont("LS", 7.2); c.drawCentredString((X(0) + X(n0)) / 2, yb + 2.2, "soft"); c.setFillColor(colors.white); c.setFont("LSB", 7.2); c.drawCentredString((X(n1) + x1) / 2, yb + 2.2, "sharp, as far as you can see")
            c.setFillColor(GREY); c.setFont("LS", 7)
            for m in (1, 2, 3, 4): c.setStrokeColor(GREY); c.setLineWidth(0.6); c.line(X(m), yb - 1, X(m), yb - 4); c.drawCentredString(X(m), yb - 11, f"{m} m")
        if st["sec"] == "FILM IN" and st["n"] == 1: extra = lambda c, bx: pill(c, bx[0] + 4, bx[1] + bx[3] - 22, "in the shade, never in the sun", SEC["FILM IN"], 10)
        if st["sec"] == "FILM IN" and st["n"] == 6: extra = lambda c, bx: (pill(c, bx[0] + bx[2] * 0.56, bx[1] + bx[3] * 0.93, "until it stops", SEC["FILM IN"], 10), inset(c, bx, SEC["FILM IN"], "the arrow goes round"))
        if st["sec"] == "PHOTOS" and st["n"] == 1: extra = lambda c, bx: minidots(c, bx)
        if st["sec"] in ("PHOTOS", "FILM OUT") and st["img"] == "s4": extra = lambda c, bx, sec=st["sec"]: inset(c, bx, SEC[sec], "arrow: once round" if sec == "PHOTOS" else "until the arrow stops")
        step(c, st["n"], st["img"], M + i * (w + 18), M + 4, w, h, items=st["parts"] or None, cap=st["do"], check=st["check"], bursts=st["bursts"], extra=extra, col=SEC[st["sec"]],
             code=f"b{st['n']}" if st["sec"] == "BUILD" else None)
    def minidots(c, bx):                                             # which dot, as small as it can be: three kinds of sky and one line for darker
        ww, hh = 150, 82; x, y = bx[0] + 4, bx[1] + 4; c.setFillColor(colors.white); c.setStrokeColor(BOXL); c.setLineWidth(0.8); c.roundRect(x, y, ww, hh, 6, fill=1, stroke=1)
        for k, ((L, ic, nm), hole) in enumerate(zip(LIGHTS[:3], ("small", "middle", "large"))):
            yy = y + hh - 16 - 17 * k; c.setFillColor(INK); c.circle(x + 12, yy + 3, DOT[hole] * 0.8, fill=1, stroke=0); c.setFont("LS", 8.5); c.drawString(x + 24, yy, nm)
        c.setFillColor(GREY); c.setFont("LS", 7.4); c.drawString(x + 8, y + 15, "Darker: hold the rocker level, count."); c.drawString(x + 8, y + 6, "For ISO 400 film.")
    def spread(sec, sts, right=None):
        for k in range(0, len(sts), 2):
            tag(c, sec, page[0]); panel(sts[k], 0)
            if k + 1 < len(sts): panel(sts[k + 1], 1)
            elif right: right()
            c.showPage(); page[0] += 1
    by = lambda sec: [x for x in STEPS if x["sec"] == sec]
    def done():
        fit(c, trim("hero_back"), M + w + 18, M + 44, w, h - 80); c.setFillColor(SEC["BUILD"]); c.setFont("LSB", 24); c.drawCentredString(M + w + 18 + w / 2, M + 22, "Done!"); c.setFillColor(INK); c.setFont("LS", 10); c.drawCentredString(M + w + 18 + w / 2, M + 8, "Press the rocker: click.  Slide the handle: three clicks.")
    spread("BUILD", by("BUILD"))
    # done, and how it works: one page.  The one explainer in the box
    import manual; manual.how_picture(); FO = json.load(open("build/exposure.json")); ST3 = FO["printers"]["typical"]["stops"]; FN = ["%g" % min((8, 9.5, 11, 13, 16, 19, 22), key=lambda n: abs(n - 32.0 / q["hole_mm"])) for q in ST3]
    tag(c, "BUILD", page[0]); fit(c, trim("hero_back"), M, M + 74, w, h - 124); c.setFillColor(SEC["BUILD"]); c.setFont("LSB", 30); c.drawCentredString(M + w / 2, M + 46, "Done!"); c.setFillColor(INK); c.setFont("LS", 10); c.drawCentredString(M + w / 2, M + 28, "Press the rocker: click.  Slide the handle: three clicks.")
    xr = M + w + 18; c.setFillColor(SEC["KNOW"]); c.setFont("LSB", 15); c.drawString(xr, H - M - 14, "How it works"); c.setFillColor(GREY); c.setFont("LS", 8.5); c.drawString(xr + 100, H - M - 14, "from above, cut through the middle")
    fit(c, "build/booklet/how.png", xr - 4, M + 148, w + 8, h - 166); y = M + 136
    for n, tx in enumerate(("Light comes in through the lens.", "A hole in the wheel sets how much: the dot you choose.", "Press the rocker: the shutter opens for an instant.", "The film lies on a curve round the lens, so the whole picture is sharp.",
                            "The green knob winds each picture back into the film's shell.", "The film turns the blue wheel: once round for each picture.")):
        badge(c, xr + 6, y + 3, n + 1, 5.6, 7, SEC["KNOW"]); c.setFillColor(INK); c.setFont("LS", 8.8)
        for ln in simpleSplit(tx, "LS", 8.8, w - 20): c.drawString(xr + 17, y, ln); y -= 10.6
        y -= 3.4
    c.showPage(); page[0] += 1
    spread("FILM IN", by("FILM IN"))
    ph = by("PHOTOS"); fo = by("FILM OUT")
    def sct():                                                        # three dots, three kinds of light; and what to do when it is darker
        x0 = M + w + 26; ww = w - 16; c.setFillColor(INK); c.setFont("LSB", 15); c.drawString(x0, H - M - 22, "Which dot?"); c.setFillColor(GREY); c.setFont("LS", 9.5); c.drawString(x0 + 92, H - M - 22, "Look at the sky."); y = H - M - 34; rh = 50
        for i, ((L, ic, nm), sub) in enumerate(zip(LIGHTS[:3], ("hard, dark shadows", "soft shadows", "bright, no shadows"))):
            hole, t = which("400", L); assert hole == ("small", "middle", "large")[i], (L, hole); yy = y - (i + 1) * rh; c.setFillColor(BOX); c.setStrokeColor(BOXL); c.setLineWidth(0.8); c.roundRect(x0, yy + 4, ww, rh - 8, 8, fill=1, stroke=1)
            c.setFillColor(INK); c.circle(x0 + 26, yy + rh / 2, DOT[hole] * 1.5, fill=1, stroke=0); ic(c, x0 + 72, yy + rh / 2 + 1); c.setFillColor(INK); c.setFont("LSB", 12); c.drawString(x0 + 100, yy + rh / 2 + 2, nm); c.setFillColor(GREY); c.setFont("LS", 9); c.drawString(x0 + 100, yy + rh / 2 - 10, sub); c.drawRightString(x0 + ww - 10, yy + rh / 2 - 3, hole + " dot")
        yy = y - 3 * rh - 6; c.setFillColor(colors.white); c.setStrokeColor(BOXL); c.roundRect(x0, yy - 74, ww, 74, 8, fill=1, stroke=1); clock(c, x0 + 26, yy - 20, 8); c.setFillColor(INK); c.setFont("LSB", 11); c.drawString(x0 + 46, yy - 18, "Darker than that: a time picture"); c.setFont("LS", 9)
        c.drawString(x0 + 46, yy - 31, "Camera on something steady. Small dot."); c.drawString(x0 + 46, yy - 42, "Hold the rocker level: open. Count. Press it down."); x = x0 + 46
        for lab, n in zip(("by a window", "lamps on", "dim room"), TIMES["400"]): x += pill(c, x, yy - 66, f"{lab}  {n}", INK, 8.5) + 5
        c.setFillColor(GREY); c.setFont("LS", 8.5); c.drawString(x0, M + 10, "For ISO 400 film. A bigger dot lets in more light.")
    spread("PHOTOS", ph[:2]); spread("PHOTOS", ph[2:4])
    def tag2(sec): xx = M + w + 18; c.setFillColor(SEC[sec]); c.roundRect(xx, H - M - 15, 16 + pdfmetrics.stringWidth(sec, "LSB", 9.5), 15, 7.5, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 9.5); c.drawString(xx + 8, H - M - 11.3, sec)
    spread("FILM OUT", fo[:2])
    tag(c, "FILM OUT", page[0]); xl = M + 10; c.setFillColor(SEC["FILM OUT"]); c.setFont("LSB", 17); c.drawString(xl, H - M - 50, "Get it developed"); fit(c, trim("cassette", 6), xl + w - 110, H - M - 170, 80, 120); y = H - M - 80
    for n, tx in enumerate(("Keep the finished film out of the light: in its tub, or in a pocket.", "Starter kit: post it in the envelope, with the code from your card.", "Any photo lab can develop 35 mm colour film.", "Ask for scans. Keep the negatives: they are the originals.")):
        badge(c, xl + 7, y + 3, n + 1, 6.5, 8, SEC["FILM OUT"]); c.setFillColor(INK); c.setFont("LS", 10.5)
        for ln in simpleSplit(tx, "LS", 10.5, w - 130 if n < 3 else w - 30): c.drawString(xl + 20, y, ln); y -= 13
        y -= 9
    xr = M + w + 26; c.setFillColor(SEC["THE HOLE"]); c.setFont("LSB", 17); c.drawString(xr, H - M - 50, "The pinhole experiment"); c.setFillColor(GREY); c.setFont("LS", 9.5); c.drawString(xr, H - M - 66, "A picture without the lens: the oldest kind of camera.")
    fit(c, trim("h2"), xr, M + 160, w - 20, h - 240); y = M + 142
    for n, st in enumerate(WEB):
        badge(c, xr + 7, y + 3, n + 1, 6.5, 8, SEC["THE HOLE"]); c.setFillColor(INK); c.setFont("LS", 9.5)
        for ln in simpleSplit(st.get("short", st["do"]), "LS", 9.5, w - 46): c.drawString(xr + 20, y, ln); y -= 11.5
        y -= 6
    c.showPage(); page[0] += 1
    # back cover: the numbers, six things to remember, who made it, and two codes: help and the lessons
    c.setFillColor(colors.HexColor("#fff4e6")); c.rect(0, 0, W, H, fill=1, stroke=0); xl = M + 6; c.setFillColor(SEC["BUILD"]); c.setFont("LSB", 22); c.drawString(xl, H - M - 20, NAME)
    c.setFillColor(INK); c.setFont("LSB", 12); c.drawString(xl, H - M - 54, "The numbers"); y = H - M - 72
    for k, v in (("Lens", "32 mm, one piece of plastic"), ("Focus", "fixed: sharp from 2 m"), ("Holes", "about f/%s, f/%s, f/%s" % tuple(FN)), ("Shutter", "about 1/300 s, or held open"), ("Film", "any 35 mm; the dots are for ISO 400"), ("Picture", "36 x 24 mm")):
        c.setFillColor(GREY); c.setFont("LS", 9.5); c.drawString(xl, y, k); c.setFillColor(INK); c.drawString(xl + 50, y, v); y -= 14
    xr = M + w + 26; c.setFillColor(INK); c.setFont("LSB", 12); c.drawString(xr, H - M - 54, "Good to know"); y = H - M - 72
    for tx in ("Load and unload in the shade, never in the sun.", "Press the rocker, then wind. Every time.", "Put what matters in the middle: it is sharpest there.", "Never force a knob. If one is stiff, stop and look.", "If the back comes open, the pictures already taken are safe in the film's shell.", "Keep the camera out of hot cars: the plastic softens."):
        c.setFillColor(SEC["BUILD"]); c.circle(xr + 3, y + 3.5, 2.2, fill=1, stroke=0); c.setFillColor(INK); c.setFont("LS", 9.5)
        for ln in simpleSplit(tx, "LS", 9.5, w - 30): c.drawString(xr + 12, y, ln); y -= 12
        y -= 4
    c.setFillColor(GREY); c.setFont("LS", 8); lines = []                     # who made it, bottom up, kept inside the left column
    for tx in ("Made by Variadic Group LLC, 2108 N St #18255, Sacramento, CA 95816.", "curve35.com  \u00b7  support@curve35.com  \u00b7  (209) 528-9554",
               "This guide: CC BY-NC-SA 4.0. Credit: CURVE 35 by Variadic Group LLC, curve35.com. CURVE 35 and its logos are trademarks. Want to sell kits? hello@curve35.com",
               f"{MODEL}   batch: ________"): lines += simpleSplit(tx, "LS", 8, w - 4)
    for k, ln in enumerate(reversed(lines)): c.drawString(xl, M + 4 + 10 * k, ln)
    c.setFillColor(INK); c.setFont("LSB", 9)
    for k, ln in enumerate(reversed(simpleSplit("Ages 14 and up.  Contains small parts: keep away from children under 3.", "LSB", 9, w - 4))): c.drawString(xl, M + 10 + 10 * len(lines) + 11 * k, ln)
    xq = M + w + 26
    for k, (path, hd, sub) in enumerate((("help", "Stuck?", "fixes for every step"), ("lessons", "How it works", "nine free lessons"))):
        xx = xq + k * 140; c.setFillColor(INK); c.setFont("LSB", 10); c.drawString(xx, M + 92, hd); c.setFillColor(GREY); c.setFont("LS", 7.6); c.drawString(xx, M + 82, sub); qr(c, path, xx, M + 12, 56, fs=7)
    c.showPage(); NKIT = c.getPageNumber() - 1
    # ---- the first picture: rung 1, a hole and a slide.  Four pages for the website (lesson 1), in the guide's own layout
    page[0] = 1; spread("THE HOLE", WEB[:4])
    tag(c, "THE HOLE", page[0]); c.setFillColor(INK); c.setFont("LSB", 20); c.drawString(M + 86, H - M - 14, "Your first picture"); fit(c, trim("r5"), M, M + 96, w + 6, h - 110); y = M + 84
    for n, tx in enumerate(("Stand the camera on something steady, outdoors.", "Aim along the middle line on top.", "Lift the slide by its grip. Count. Push it down.", "Wind on: turn the green knob until the arrow has gone once round.")):
        badge(c, M + 7, y + 3, n + 1, 6.5, 8, SEC["THE HOLE"]); c.setFillColor(INK); c.setFont("LS", 10); c.drawString(M + 20, y, tx); y -= 16
    xr = M + w + 34; c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(xr, H - M - 56, "How long to count"); table3(c, xr + 4, H - M - 92, [(k, PINS[k]) for k in ISOS], PINL, 49, lab=44, fs=8.5, title="Seconds, by film and light"); c.setFillColor(INK); c.setFont("LS", 9.5); y = H - M - 196
    for tx in ("A hole this small lets in very little light, so every picture is counted, not snapped.", "A camera is a dark box with a hole. Everything you add from here makes the picture brighter, sharper or quicker to take: a lens, three sizes of hole, a shutter.", "Then take the same picture again with the lens, and compare."):
        for ln in simpleSplit(tx, "LS", 9.5, W - M - xr - 6): c.drawString(xr, y, ln); y -= 12.5
        y -= 6
    c.showPage(); page[0] += 1; spread("THE HOLE", WEB[4:])
    c.save()
    from pypdf import PdfReader, PdfWriter
    rd = PdfReader("build/booklet/_master.pdf")
    for name, pages in (("build/CURVE-35_kit_booklet.pdf", range(0, NKIT)), ("build/old/CURVE-35_first_picture_retired.pdf", range(NKIT, len(rd.pages)))):
        wr = PdfWriter(); [wr.add_page(rd.pages[k]) for k in pages]; wr.add_metadata({"/Title": f"{NAME} " + ("kit booklet" if "kit" in name else "first picture"), "/Author": "Variadic Group LLC"}); wr.write(name)
    json.dump(QR_USED, open("build/booklet/qr_paths.json", "w"), indent=1)
    print("kit booklet:", NKIT, "pages; first picture:", len(rd.pages) - NKIT, "pages")
def light_chart():
    """One letter page for the wall or the camera bag: which dot, and how long."""
    from reportlab.lib.pagesizes import letter
    PW, PH = letter; c = canvas.Canvas("build/CURVE-35_light_chart.pdf", pagesize=letter); c.setTitle(f"{NAME} light chart"); c.setAuthor("Variadic Group LLC"); x0 = 54; TW = PW - 2 * x0
    c.setFillColor(SEC["BUILD"]); c.rect(0, PH - 74, PW, 74, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 30); c.drawString(x0, PH - 48, f"{NAME} light chart"); c.setFont("LS", 12); c.drawString(x0, PH - 65, "which dot, and how long")
    c.setFillColor(INK); c.setFont("LSB", 15); c.drawString(x0, 694, "1. A snap: press the rocker"); c.setFillColor(GREY); c.setFont("LS", 10); c.drawString(x0 + 214, 694, "Find your film's ISO on its box. Look at the sky. Stand 2 m or more away.")
    yb = chart(c, x0, 684, cw=74, rh=46, lab=60, fs=9.5, k=1.2); legend(c, x0 + 60, yb - 18, 10); c.setFillColor(GREY); c.setFont("LS", 9.5)
    for i, tx in enumerate(("full sun: hard, dark shadows", "hazy sun: soft shadows", "cloud: bright, no shadows", "dull: heavy cloud, rain", "shade: out of the sun on a sunny day")): c.drawString(x0 + 330, yb - 14 - 12.5 * i, tx)
    c.setFillColor(INK); c.setFont("LSB", 15); c.drawString(x0, 410, "2. A time picture: hold the shutter open and count"); c.setFont("LS", 10)
    for i, ln in enumerate(simpleSplit("Stand the camera on something steady. Small dot. Put a fingertip on each side of the rocker, lower the raised side until it is level (open), count, then press it on down (closed). With the large dot, count a third as long.", "LS", 10, TW)): c.drawString(x0, 394 - 13 * i, ln)
    table3(c, x0 + 4, 330, [(k, [f"{v} s" for v in TIMES[k]]) for k in ISOS], ROOMS, 120, lab=70, fs=11, rh=16, title="With the lens: seconds to count")
    c.setFillColor(GREY); c.setFont("LS", 9.5); c.drawString(x0, 262, "Outdoors but too dark for a snap (the clock in chart 1): small dot, open and shut as fast as you can.")
    c.setFillColor(INK); c.setFont("LSB", 15); c.drawString(x0, 234, "3. The pinhole experiment"); c.setFillColor(GREY); c.setFont("LS", 10); c.drawString(x0 + 210, 234, "Disc and ring in place of the lens, large dot. Hold the rocker level, count."); c.setFillColor(INK); table3(c, x0 + 4, 198, [(k, [v if not v[0].isdigit() else v + " s" for v in PINS[k]]) for k in ISOS], PINL, 96, lab=70, fs=11, rh=16, title="With the hole: seconds to count")
    c.setFillColor(BOX); c.setStrokeColor(BOXL); c.roundRect(x0 - 8, 30, TW + 16, 104, 10, fill=1, stroke=1); c.setFillColor(INK); c.setFont("LSB", 10.5); c.drawString(x0 + 2, 120, "Why it works, and how sure this is"); c.setFont("LS", 9); yy = 106
    for tx in ("The shutter always gives about 1/300 s. The middle dot lets in twice the light of the small one, the large dot about a third more again (about f/16, f/11, f/9.5), and each step of film speed needs half the light. One step dimmer outside: one dot bigger.",
               "Colour negative film forgives about one step too little light and three too much, so the counts lean long on purpose. If in doubt, give more light.",
               f"Every number comes from the camera's own model ({MODEL}), typical printer. Start here, and write down what you used: curve35.com/help."):
        for ln in simpleSplit(tx, "LS", 9, TW - 4): c.drawString(x0 + 2, yy, ln); yy -= 11.2
        yy -= 3
    c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(x0, 16, f"{NAME}  {MODEL}  Variadic Group LLC"); c.showPage(); c.save()
def card():
    """The card in the bag, the size of a business card (3.5 x 2 in), two sides: what it is, and where the rest lives.  Cheap to print; it is also what gets handed to a friend."""
    CWd, CHt = 252, 144; c = canvas.Canvas("build/CURVE-35_card.pdf", pagesize=(CWd, CHt)); c.setTitle(f"{NAME} card"); c.setAuthor("Variadic Group LLC")
    c.setFillColor(colors.HexColor("#fff4e6")); c.rect(0, 0, CWd, CHt, fill=1, stroke=0); c.setFillColor(SEC["BUILD"]); c.rect(0, CHt - 44, CWd, 44, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 24); c.drawString(12, CHt - 28, NAME); c.setFont("LS", 8.5); c.drawString(13, CHt - 39, TAG)
    fit(c, trim("hero"), 96, 4, 150, 96); c.setFillColor(INK); x = 12
    for i, tx in enumerate(("a real 35 mm camera", "you build it yourself", "no tools, no glue")): c.setFont("LS", 8.5); c.drawString(12, 78 - 12 * i, tx)
    c.setFillColor(GREY); c.setFont("LS", 7); c.drawString(12, 12, "ages 14 and up"); c.showPage()
    c.setFillColor(colors.white); c.rect(0, 0, CWd, CHt, fill=1, stroke=0); c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(12, CHt - 22, "Start here"); qr(c, "start", CWd - 78, CHt - 76, 56, fs=6.4); c.setFillColor(INK); c.setFont("LS", 8.5)
    for i, tx in enumerate(("every step as a short film", "the full light chart", "your first picture, with a hole", "how and why it works")): c.setFillColor(SEC["PHOTOS"]); c.circle(15, CHt - 37 - 12 * i, 2, fill=1, stroke=0); c.setFillColor(INK); c.drawString(22, CHt - 40 - 12 * i, tx)
    c.setFillColor(BOX); c.setStrokeColor(BOXL); c.setLineWidth(0.7); c.roundRect(10, 8, CWd - 20, 44, 6, fill=1, stroke=1); c.setStrokeColor(INK); c.setLineWidth(0.8)
    for k, (hd, sub) in enumerate((("Starter kit", "film inside; developing code:"), ("Camera kit", "add any 35 mm film"))): yy = 36 - 20 * k; c.setFillColor(colors.white); c.rect(17, yy - 1, 8, 8, fill=1, stroke=1); c.setFillColor(INK); c.setFont("LSB", 8); c.drawString(30, yy, hd); c.setFont("LS", 7.5); c.setFillColor(GREY); c.drawString(30 + pdfmetrics.stringWidth(hd, "LSB", 8) + 5, yy, sub)
    c.setStrokeColor(BOXL); c.setFillColor(colors.white); c.roundRect(170, 30, CWd - 188, 17, 4, fill=1, stroke=1); c.showPage(); c.save()
if __name__ == "__main__":
    build(); light_chart(); card(); print("booklet written")
