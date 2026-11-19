"""ONE-135 picture build guide: parts laid flat, then one picture per step.  Landscape US Letter."""
import os, json
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader, simpleSplit
from PIL import Image, ImageDraw, ImageFont, ImageChops
F = "/usr/share/fonts/truetype/liberation/LiberationSans-"
for n, f in (("LS", "Regular"), ("LSB", "Bold")): pdfmetrics.registerFont(TTFont(n, F + f + ".ttf"))
W, H = landscape(letter); M = 30
INK = colors.HexColor("#1c1e22"); ACC = colors.HexColor("#c8551a"); GREY = colors.HexColor("#5b6068"); RULE = colors.HexColor("#d5d8dd"); TINT = colors.HexColor("#eef3fb"); PALE = colors.HexColor("#f6f4f0")
G = "build/guide/"; T = G + "trim/"; os.makedirs(T, exist_ok=True)
def trim(name, pad=16, src=None):
    im = Image.open(src or (G + name + ".png")).convert("RGB"); bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox(); box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))
    out = T + name + ".png"; im.crop(box).save(out); return out
def annotate(name, labels):
    im = Image.open(G + name + ".png").convert("RGB"); d = ImageDraw.Draw(im); f = ImageFont.truetype(F + "Regular.ttf", 46)
    for text, tip, at in labels:
        w = d.textlength(text, font=f); cx = at[0] + w / 2
        d.line([tip, (cx if abs(cx - tip[0]) < w / 2 else (at[0] if tip[0] < at[0] else at[0] + w), at[1] + (58 if tip[1] > at[1] else -4))], fill=(40, 40, 40), width=4)
        d.ellipse([tip[0] - 6, tip[1] - 6, tip[0] + 6, tip[1] + 6], fill=(40, 40, 40)); d.text(at, text, fill=(20, 20, 20), font=f)
    out = G + name + "_lab.png"; im.save(out); return out
def fit(c, path, x, y, w, h, align="c"):
    iw, ih = Image.open(path).size; s = min(w / iw, h / ih); dw, dh = iw * s, ih * s
    c.drawImage(ImageReader(path), x + (w - dw) / 2, y + (h - dh) / 2 if align == "c" else y + h - dh, dw, dh)
def text(c, s, x, y, w, font="LS", size=11, lead=None, color=INK):
    c.setFont(font, size); c.setFillColor(color); lead = lead or size * 1.3
    for ln in simpleSplit(s, font, size, w): c.drawString(x, y, ln); y -= lead
    return y
def header(c, section, page):
    c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(M, H - 26, "ONE-135"); c.setFont("LS", 11); c.setFillColor(GREY); c.drawString(M + 62, H - 26, "build guide")
    c.setFillColor(ACC); c.setFont("LSB", 13); c.drawRightString(W - M, H - 26, section)
    c.setStrokeColor(RULE); c.setLineWidth(0.6); c.line(M, H - 34, W - M, H - 34)
    c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(M, 16, "Model v2.1: checked in software (fit, light, finite-element strength, print simulation), not yet printed. Generated from the OpenSCAD model."); c.drawRightString(W - M, 16, str(page))
PARTS = [("front", "Front plate", "front face", "61 x 55 x 7"), ("wheel", "Aperture wheel", "back face", "35 x 34 x 7"), ("blade", "Shutter blade", "front face", "36 x 45 x 8"),
         ("body", "Body", "front face", "121 x 58 x 34"), ("back", "Back", "outside face", "121 x 59 x 16"), ("roller", "Sprocket roller", "dial", "16 x 16 x 50"),
         ("knob", "Knob: print two", "head", "18 x 18 x 16"), ("spool", "Take-up spool", "top end", "22 x 22 x 46"), ("spoolcap", "Spool cap", "flange", "22 x 22 x 8")]
NUM = {p[0]: i + 1 for i, p in enumerate(PARTS)}
THUMB = {**{p[0]: "p_" + p[0] for p in PARTS}, "lens": "b_lens", "shims": "b_shims", "spool_std": "b_spool_std"}
LABEL = {**{p[0]: p[1] for p in PARTS}, "lens": "Lens", "shims": "Shim"}
def callout(c, items, x, ytop, w):
    """Lego-style box of the parts this step uses: [(key, qty)]"""
    n = len(items); cw = 58; bw = n * cw + 8; bh = 64; x0 = x + w - bw
    c.setFillColor(TINT); c.setStrokeColor(colors.HexColor("#b9c8e0")); c.setLineWidth(0.7); c.roundRect(x0, ytop - bh, bw, bh, 6, fill=1, stroke=1)
    for i, (k, q) in enumerate(items):
        cx = x0 + 6 + i * cw; fit(c, trim(THUMB[k], 6), cx, ytop - bh + 18, cw - 8, bh - 24)
        c.setFillColor(INK); c.setFont("LSB", 10); c.drawString(cx, ytop - bh + 6, f"{q}x")
        if k in NUM:
            c.setFillColor(ACC); c.circle(cx + 26, ytop - bh + 9.5, 6.5, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 8); c.drawCentredString(cx + 26, ytop - bh + 6.7, str(NUM[k]))
        else: c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(cx + 17, ytop - bh + 6.5, {"lens": "lens", "shims": "shim"}[k])
def step(c, num, img, cap, x, y, w, h, items=None, note=None, cap_h=None, numsize=40):
    c.setFillColor(INK); c.setFont("LSB", numsize); c.drawString(x, y + h - numsize + 2, str(num))
    if items: callout(c, items, x, y + h - 2, w)
    need = 14 * len(simpleSplit(cap, "LS", 11, w)) + (12 * len(simpleSplit(note, "LS", 9, w)) + 4 if note else 0) + 6
    cap_h = max(cap_h or 0, need); top = 70 if items else numsize + 8
    fit(c, trim(img, src=G + img + ".png"), x, y + cap_h + 4, w, h - top - cap_h - 4)
    yy = text(c, cap, x, y + cap_h - 12, w, size=11, lead=14)
    if note: text(c, note, x, yy - 2, w, size=9, lead=12, color=GREY)
c = canvas.Canvas("build/ONE-135_build_guide.pdf", pagesize=(W, H)); c.setTitle("ONE-135 build guide"); c.setAuthor("Camera Ladder")
# ------------------------------------------------------------------ 1. cover: the parts laid flat
c.setFillColor(INK); c.setFont("LSB", 34); c.drawString(M, H - 62, "ONE-135"); c.setFont("LS", 15); c.setFillColor(GREY); c.drawString(M + 158, H - 62, "build guide")
text(c, "One simple 35 mm film camera, printed parts only. No spring, no pins, no screws, no supports, no glue, no tape, no tools.", M, H - 84, 300, size=11, lead=14, color=GREY)
fit(c, trim("hero"), M, 250, 300, 240)
c.setFillColor(PALE); c.setStrokeColor(RULE); c.roundRect(M, 44, 300, 192, 6, fill=1, stroke=1)
c.setFillColor(ACC); c.setFont("LSB", 12); c.drawString(M + 10, 218, "Nothing to buy")
for i, (k, name, sub, sub2) in enumerate([("shims", "Pinhole", "printed into the aperture wheel: works with no lens", "at all, with the camera resting on something"),
                                          ("lens", "Lens (optional)", "from a used Fujifilm QuickSnap: turns it into a", "hand-held camera (measure it first: last page)"),
                                          ("spool_std", "Spool (optional)", "the spool out of any 35 mm cassette can stand in", "for printed parts 8 and 9")]):
    yy = 164 - i * 44
    if k != "shims": fit(c, trim(THUMB[k], 6), M + 10, yy, 40, 38)
    else: c.setFillColor(colors.HexColor("#b9bcc2")); c.circle(M + 30, yy + 19, 13, fill=1, stroke=0); c.setFillColor(INK); c.circle(M + 30, yy + 19, 1.1, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont("LSB", 10.5); c.drawString(M + 58, yy + 24, name)
    c.setFont("LS", 8.8); c.setFillColor(GREY); c.drawString(M + 58, yy + 12, sub); c.drawString(M + 58, yy + 1, sub2)
c.setFont("LS", 8.5); c.setFillColor(GREY); c.drawString(M + 10, 52, "With the lens, also print one135_shims.stl. Optional: a 1/4-20 tripod nut.")
X0 = M + 322; c.setFillColor(ACC); c.setFont("LSB", 14); c.drawString(X0, H - 58, "Print these 9 parts"); c.setFillColor(GREY); c.setFont("LS", 10)
c.drawString(X0 + 142, H - 58, "each one lies on the bed exactly as drawn; no supports")
cw, ch = (W - M - X0) / 3, 162
for i, (k, name, face, size) in enumerate(PARTS):
    x, y = X0 + (i % 3) * cw, H - 76 - (i // 3 + 1) * ch
    c.setStrokeColor(RULE); c.setLineWidth(0.6); c.roundRect(x + 3, y + 4, cw - 8, ch - 8, 6, fill=0, stroke=1)
    fit(c, trim("p_" + k, 6), x + 34, y + 44, cw - 48, ch - 58)
    c.setFillColor(ACC); c.circle(x + 20, y + ch - 22, 10, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 11); c.drawCentredString(x + 20, y + ch - 26, str(i + 1))
    c.setFillColor(INK); c.setFont("LSB", 10.5); c.drawString(x + 12, y + 30, name); c.setFont("LS", 8.5); c.setFillColor(GREY); c.drawString(x + 12, y + 19, f"prints on its {face}"); c.drawString(x + 12, y + 9, f"{size} mm")
header_done = c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(M, 16, "Model v2.1: checked in software (fit, light, finite-element strength, print simulation), not yet printed. This guide is generated from the OpenSCAD model."); c.showPage()
# ------------------------------------------------------------------ numbers that the checks produced
J = lambda n: json.load(open("build/" + n + ".json"))
SL = J("slicecheck"); FE = J("fea"); PSIM = J("printsim"); SH = J("shutter"); OP = J("optics"); SW = J("slicesweep")
def mins(t): return sum(float(x[:-1]) * dict(d=1440, h=60, m=1, s=1 / 60)[x[-1]] for x in t.split())
QTY = dict(knob=2); KIT = ["body", "back", "front", "blade", "wheel", "roller", "knob", "spool", "spoolcap"]
GRAMS = sum(SL[n]["grams"] * QTY.get(n, 1) for n in KIT); MIN = sum(mins(SL[n]["time"]) * QTY.get(n, 1) for n in KIT); hm = lambda m: ("%d h %02d min" % (round(m) // 60, round(m) % 60)) if round(m) >= 60 else "%d min" % round(m)
fe = lambda key, *has: [v for k, v in FE.items() if k.startswith(key) and all(h in k for h in has)][0]
clk = [v["blade"]["click_at_finger_N"] for v in PSIM.values()]; rays = sum(v["rays"] for k, v in OP.items() if k.startswith("leak") and "sanity" not in k)
leaks = sum(v["escaped_confirmed"] for k, v in OP.items() if k.startswith("leak") and "sanity" not in k)
sw = lambda w, i, lh=0.2: [r for r in SW if r["part"] == "body" and r["walls"] == w and r["infill"] == i and r["layer"] == lh][0]
# ------------------------------------------------------------------ build steps, two per page
BUILD = [("a3", "Hold the front plate face down in your palm. Drop the wheel over the wide boss, with its handle through the curved slot and its sprung rim toward the notched wall.", [("front", 1), ("wheel", 1)], "Turn it by the handle: it clicks at P, S and C."),
         ("a4", "Drop the blade over the boss near the top edge. Its tab stands up past the edge; the tooth on its sprung rim sits in a notch of the curved wall.", [("blade", 1)], "Swing it: it clicks at each end and, softly, in the middle."),
         ("a5", "Lower the body onto the plate about 3 mm to one side, so the four feet drop into their pockets. Then slide the plate toward the wind-knob end until it clicks.", [("body", 1)], "To take it off again: press the pad in its top edge and slide it back."),
         ("a6", "For the lens: drop one shim ring into the pocket, then press the lens in, bulge outward. For a pinhole camera, leave the pocket empty.", [("shims", 1), ("lens", 1)], None),
         ("a7", "Check focus, once. Slide the tab to its middle click (open) and set the wheel to C. Hold a piece of baking paper flat across the film opening and aim at something bright and far away.", None, "Blurred? Take the lens out and add or remove a shim. Each shim moves the focus by 0.2 mm."),
         ("a8", "Hold the sprocket roller with its dial 2 mm above the top edge of the back. Lay its shaft in the fork, then slide it down: its bottom pin goes into the hole. It stays with the back from now on.", [("back", 1), ("roller", 1)], "Nothing snaps: to take it out, slide it up 2 mm and lift."),
         ("a9", "Push the cap onto the take-up spool and drop the spool into the right-hand chamber, cap down. Press a knob into each hole in the top, turning it until it drops in.", [("spool", 1), ("spoolcap", 1), ("knob", 2)], "A spool from a used 35 mm cassette fits here instead, long end down."),
         ("a10", "Press the back on until both latches click. To open it, pinch the two pads, top and bottom, and pull.", None, None)]
pw = (W - 2 * M - 28) / 2; ph = H - 34 - 40 - 30
for i in range(0, 8, 2):
    header(c, "Build", i // 2 + 2)
    for j in (0, 1):
        img, cap, items, note = BUILD[i + j]; step(c, i + j + 1, img, cap, M + j * (pw + 28), 34, pw, ph, items, note, cap_h=70)
    c.setStrokeColor(RULE); c.line(W / 2, 40, W / 2, H - 44); c.showPage()
# ------------------------------------------------------------------ loading, three per page
LOAD = [("l1", "In dim light, pinch the two pads and take the back off. The roller comes away with it.", None), ("l2", "Lift the wind knob. Drop in the cassette, long hub down. Press the knob back, turning it until it drops in.", None),
        ("l3", "Pull the film across and tuck its tip into the slot in the spool. Turn the take-up knob one turn anticlockwise.", "Salvaged spool: hook the film's tip into the slot in its core."),
        ("l4", "Press the back on until it clicks. The roller's teeth find the lower row of holes.", None),
        ("l5", "Pre-wind: turn the take-up knob anticlockwise until it stops, about 36 turns for 36 exposures.", "Count the turns of the frame dial beside it: that is your number of pictures."),
        ("s3", "After each picture, turn the wind knob clockwise until the frame dial has made one full turn.", "When the dial stops turning as you wind, the film is home. Open the back in any light.")]
tw = (W - 2 * M - 2 * 22) / 3; rh = (H - 34 - 40 - 44) / 2
header(c, "Load film", 6)
for i in range(6):
    img, cap, note = LOAD[i]; step(c, i + 1, img, cap, M + (i % 3) * (tw + 22), 52 + (1 - i // 3) * (rh + 10), tw, rh, None, note, cap_h=58, numsize=30)
for j in (1, 2): c.setStrokeColor(RULE); c.line(M + j * (tw + 22) - 11, 52, M + j * (tw + 22) - 11, H - 44)
c.line(M, 52 + rh + 5, W - M, 52 + rh + 5)
text(c, "Every shot winds one frame back into the cassette, so the finished roll is already sealed. That is why the whole roll is wound out first.", M, 36, W - 2 * M, size=9.5, lead=13, color=GREY)
c.showPage()
# ------------------------------------------------------------------ shooting: 2 x 2 and a strip
header(c, "Shoot", 7)
s1 = annotate("s1", [("Shutter tab", (450, 252), (120, 60)), ("Aperture handle", (688, 585), (770, 800))])
SHOOT = [("s1_lab", "Set the aperture with the yellow handle: S for sun, C for cloud. P is the pinhole.", None),
         ("s0", "Aim by sighting along the top: the middle line points at the centre, the outer two at the edges.", "Rule of thumb: the picture is about as wide as you are far from your subject, and three quarters as tall. At 2 m it is about 2.2 m wide and 1.5 m tall."),
         ("s2", "Flick the tab across, past its click. Either direction takes one picture; then wind on.", "Flick it, do not push it: a slow push gives a long exposure."),
         ("s4", "Time exposures and the pinhole: rest the camera on something, slide the tab slowly to its middle click, count, and slide it on.", None)]
strip = 78; rh = (H - 34 - 40 - 30 - strip) / 2
for j in range(4):
    img, cap, note = SHOOT[j]; step(c, j + 1, img, cap, M + (j % 2) * (pw + 28), 40 + strip + (1 - j // 2) * (rh + 10), pw, rh, None, note, cap_h=42, numsize=28)
c.setStrokeColor(RULE); c.line(W / 2, 40 + strip + 4, W / 2, H - 44); c.line(M, 40 + strip + rh + 5, W - M, 40 + strip + rh + 5)
c.setFillColor(PALE); c.setStrokeColor(RULE); c.roundRect(M, 34, W - 2 * M, strip - 6, 6, fill=1, stroke=1)
c.setFillColor(ACC); c.setFont("LSB", 11); c.drawString(M + 12, 34 + strip - 22, "Which letter"); c.drawString(M + 372, 34 + strip - 22, "Middle click: time exposures")
cols = ["", "Sun", "Haze", "Cloud", "Shade"]; rows = [["ISO 400", "S", "S", "C", "C"], ["ISO 200", "S", "C", "C", "C"]]
for k, t_ in enumerate(cols): c.setFont("LSB", 9.5); c.setFillColor(INK); c.drawString(M + 110 + k * 50, 34 + strip - 22, t_)
for r, row in enumerate(rows):
    for k, t_ in enumerate(row): c.setFont("LSB" if k == 0 else "LS", 9.5); c.setFillColor(INK); c.drawString(M + 110 + k * 50, 34 + strip - 38 - r * 14, t_)
text(c, "Lens at S, ISO 400: by a window 1 s, lamplit room 4 s, night street 15 s. Pinhole (wheel at P, lens out), ISO 400: sun, one slow sweep of the tab; cloud 1/4 s; shade 1 s; by a window 30 s.", M + 372, 34 + strip - 37, W - 2 * M - 386, size=9.3, lead=12.2)
c.showPage()
# ------------------------------------------------------------------ reference
header(c, "Reference", 8)
colw = (W - 2 * M - 30) / 2
def block(title, body, x, y, w=None, size=10):
    c.setFillColor(ACC); c.setFont("LSB", 12); c.drawString(x, y, title); yy = y - 16
    for para in body: yy = text(c, para, x, yy, w or colw, size=size, lead=size * 1.35) - 5
    return yy - 8
y = block("Printing", ["Black PETG (best: PLA softens in a hot car) or PLA, 0.2 mm layers, 0.4 mm nozzle, 3 walls, 15 % gyroid infill, no supports. Brim on the roller and the spool. Every shutter part is a whole number of 0.2 mm layers thick, so keep that layer height.",
                       "Sliced in PrusaSlicer 2.7 at those settings: %.0f g of filament (about $%.2f at $22 a kilo) and %s in total. The body alone is %s." % (GRAMS, GRAMS * 0.022, hm(MIN), hm(mins(SL["body"]["time"]))),
                       "Hollowing the body would save nothing: %.0f of its %.0f g is skin. Two walls and 10 %% infill save %.0f g and %d minutes, but leave a 0.9 mm skin that may let light through." % (sw(3, 0)["grams"], sw(3, 15)["grams"], sw(3, 15)["grams"] - sw(2, 10)["grams"], sw(3, 15)["minutes"] - sw(2, 10)["minutes"]),
                       "Body, back, front plate, blade and wheel must be opaque. Hold a 0.6 mm chip of your filament against a bright lamp first."], M, H - 62)
y = block("Test the front first (an hour)", ["Print one135_test_slab.stl (the front 4 mm of the body) with the front plate, blade and wheel, and do build steps 1 to 3 on it. It tells you what your printer decides: whether the plate slides on and clicks, and how the two clicks feel."], M, y)
y = block("The lens: one used Fujifilm QuickSnap", ["Its lens is 32 mm, which is what this camera is spaced for. A Kodak FunSaver lens is 30 mm and will not reach focus. Photo labs often discard the empty shells; ask for one.",
                          "The lens pocket is drawn 12 mm across, a placeholder. Print one135_lens_gauge.stl (10 minutes): the hole your lens presses into snugly is its size. Set LENS_D to it before printing the front plate.",
                          "Shims adjust focus for lenses from about 31.8 to 32.8 mm. A 30 or 31 mm lens (Kodak, Ilford, Lomography) needs the film moved closer: a different body, which the model can generate.",
                          "Careful: a flash camera's capacitor can give a nasty shock even with the battery out. Keep your fingers off the circuit board."], M, y)
X2 = M + colw + 30
fit(c, trim("f1"), X2, H - 62 - 150, 190, 160)
c.setFillColor(ACC); c.setFont("LSB", 12); c.drawString(X2 + 200, H - 62, "Taking the shutter out")
text(c, "No tools. Press the pad in the plate's top edge, slide the plate 3 mm toward the shutter tab, and lift it off. The wheel and blade lift off their bosses.", X2 + 200, H - 78, colw - 200, size=10, lead=13.5)
y2 = block("Shutter speed", ["There is no separate spring. The tab is 7 mm from the pivot and the lens 28.5 mm, so the blade crosses the lens four times as fast as your finger; the click makes you build up %.1f to %.1f N (depending on the printer) before it lets go." % (min(clk), max(clk)),
                             "Estimate: about %s s on a typical printer, from %s on one that prints thin to %s on one that prints fat, and half a stop either way with the hand. Negative film forgives that. To measure yours, film the lens with a phone in slow motion and count frames." % (SH["exposure_range"]["typical_printer"], SH["exposure_range"]["slowest_printer"], SH["exposure_range"]["fastest_printer"])], X2, H - 62 - 168)
y2 = block("The printed pinhole", ["P is a hole printed straight into the wheel. It comes out about %.1f mm across on a typical printer (%.1f to %.1f mm over the range of printers): soft, but it needs no lens. For a sharper one, lay a 6 mm disc of drinks-can foil with a needle hole in the seat around it; that is the one optional step that needs a dab of glue." % (PSIM["typical printer"]["aperture_holes_mm"]["P"], PSIM["fattest printer"]["aperture_holes_mm"]["P"], PSIM["thin printer"]["aperture_holes_mm"]["P"])], X2, y2)
y2 = block("Not yet checked on a print", ["Everything on the next page is software. A real print has still to confirm the feel of the plate's slide and click, the back's latches, the knobs' grip, the lens fit, and above all the shutter's real speed."], X2, y2)
c.showPage()
# ------------------------------------------------------------------ how it was checked
header(c, "How it was checked", 9)
fit(c, "build/fea.png", M, 196, 300, H - 44 - 196, align="t"); fit(c, "build/printsim.png", M + 316, H - 44 - 214, W - 2 * M - 316, 208, align="t")
c.setFillColor(GREY); c.setFont("LS", 8); c.drawString(M, 186, "Finite-element strain maps of the parts that bend (red = 1 %)."); c.drawString(M + 316, H - 44 - 222, "Print simulation: plastic rebuilt from the sliced tool paths of a printer whose walls come out 0.10 mm fat.")
yL = block("Strength (finite elements)", ["Every part that bends, catches or could be knocked was cut out of the model and solved: peak strain against what printed plastic takes in that print direction (0.5 % if it happens every shot, 1 % if it happens now and then; half that across the layers).",
     "Shutter click spring: %.2f to %.2f %% over the whole range of printers. Aperture click: %.2f to %.2f %%. Plate latch: %.2f %% to release, %.2f %% at its stop. Back latches: %.2f %% to open, %.2f %% at their stop. Catch on the body, knocked with 40 N: %.2f %%. Feet of the plate, pulled with 40 N: %.2f %%."
     % (fe("blade click spring", "thin")["peak_strain_pct"], fe("blade click spring", "fattest")["peak_strain_pct"], fe("wheel click spring", "thin")["peak_strain_pct"], fe("wheel click spring", "fattest")["peak_strain_pct"],
        fe("plate latch tongue", "release")["peak_strain_pct"], fe("plate latch tongue", "as far")["peak_strain_pct"], fe("back latch finger, pad", "as drawn")["peak_strain_pct"], fe("back latch finger, pad", "slit closes")["peak_strain_pct"],
        fe("body catch, knocked", "40 N")["peak_strain_pct"], fe("hooked foot", "40 N")["peak_strain_pct"]),
     "Each spring has a stop: the part behind it catches it before it can be over-bent."], M, 168, 300, 8.6)
xr = M + 316; wr = (W - 2 * M - 316 - 20) / 2
y1 = block("Printing (slicing and simulation)", ["Every part was sliced and the tool paths compared with the model layer by layer: nothing that matters is dropped. Then the plastic was rebuilt from the tool paths with printer error added (walls from 0.08 mm thin to 0.15 mm fat, a fatter first layer) and measured.",
     "On every one of those printers both clicks work (%.1f to %.1f N at the shutter tab), no spring runs out of room, the slits stay open, and the letters stay readable. The first layer of every flat part is drawn 0.2 mm smaller, so elephant's foot lands on size." % (min(clk), max(clk))], xr, H - 44 - 240, wr, 8.6)
y1 = block("Fit", ["All parts in every shutter and aperture position, the plate sliding on and off, the roller going into its bearings, the back coming off: no collisions; every catch holds. Repeated with every part grown and shrunk as above."], xr, y1, wr, 8.6)
y3 = block("Light", ["%d million rays traced from the film in all directions with the shutter closed, in %d set-ups (both sides, each aperture, blade at the ends of its play, roller at the top of its float): %d leave the camera." % (round(rays / 1e6), len([k for k in OP if k.startswith("leak") and "sanity" not in k]), leaks),
     "Corners of the picture get %.0f %% of the light at C and %.0f %% at S." % (100 * OP["C f/8"]["light_kept_worst_corner"], 100 * OP["S f/16"]["light_kept_worst_corner"])], xr + wr + 20, H - 44 - 240, wr, 8.6)
y3 = block("What software cannot tell", ["How your filament and printer really behave: warping, stringing in the slits, a rough first layer, layer bonding. Print the test slab first."], xr + wr + 20, y3, wr, 8.6)
c.showPage()
# ------------------------------------------------------------------ fit and wear
header(c, "Fit, tuning and wear", 10)
y = block("Nothing to finish", ["No hole is drilled, no skin is cut away, nothing is glued or taped. The lens port is bridged in three layers, the aperture holes are printed to size, and every part goes together by hand."], M, H - 62)
y = block("If a fit is tight", ["The design leaves room for walls up to 0.15 mm fat. If the test slab shows the plate will not slide on, or the wheel or blade will not turn freely, your printer is laying down more than that: lower its flow (extrusion multiplier) by 5 % and reprint the small part. That is a setting, not a tool."], M, y)
y = block("If a fit is loose", ["On a printer that prints thin, the front plate can move half a millimetre along its slide before the latch catches (it cannot come off), and the clicks are light: about %.1f N at the tab instead of %.1f. Raise the flow by 5 %% and reprint the blade and wheel: 12 minutes." % (min(clk), PSIM["typical printer"]["blade"]["click_at_finger_N"])], M, y)
y = block("Click too stiff or too soft", ["How far the tooth is pushed in is BUMP - SCL - HUBC in tools/layout.py, plus four times however fat your walls print. Change BUMP by 0.2 mm, run layout.py, and reprint the blade and the front plate."], M, y)
X2 = M + colw + 30
y2 = block("What can break, and how hard you have to try", ["The click springs cannot be over-bent inward: the part behind them stops them. Pried outward on purpose, with a fingernail, they give at about 5 mm. A blade is a 5 minute print and a wheel 7.",
                                           "The two catches for the back stand 5 mm proud of the body when the back is off. Each takes a 40 N (4 kg) knock; the body is the one part you would not want to reprint, so do not stand it on them on a hard floor.",
                                           "The roller's bearings, the knobs, the spool and the feet of the front plate do not bend at all."], X2, H - 62)
y2 = block("What wears, and what does not", ["Each spring only bends while its part moves, and rests straight in a notch, so it does not creep or go slack. The blade turns on a 5.5 mm boss with 0.4 mm of room: it cannot seize, and wear only adds play, which the click takes up.",
                                           "Knobs and spool turn plastic on plastic and loosen slightly over years; that is harmless. The back's latches flex once per roll.",
                                           "Keep PLA cameras out of hot cars: PLA softens near 55 C. Grit in the shutter: lift the plate off and blow it out."], X2, y2)
c.showPage(); c.save()

from pypdf import PdfReader; print("pages:", len(PdfReader("build/ONE-135_build_guide.pdf").pages))
