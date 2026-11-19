"""One page: the focus check.  For whoever fits a lens (us, once per batch; a maker printing their own).  Reads build/focus.json."""
import json
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R = "/home/claude/one/"; FJ = json.load(open(R + "build/focus.json")); FD = "/usr/share/fonts/truetype/liberation/LiberationSans-"
for n, f in (("LS", "Regular"), ("LSB", "Bold")): pdfmetrics.registerFont(TTFont(n, FD + f + ".ttf"))
W, H = letter; M = 48; INK = colors.HexColor("#1f2328"); GREY = colors.HexColor("#6b7280"); OR = colors.HexColor("#e8641b"); BOX = colors.HexColor("#f4f6f8"); LINE = colors.HexColor("#c9d1d9"); GOOD = colors.HexColor("#1a7f4b")
c = canvas.Canvas(R + "build/CURVE-35_focus_check.pdf", pagesize=letter); c.setTitle("CURVE 35: focus check")
def para(x, y, w, t, f="LS", s=10.5, col=INK, lead=None):
    c.setFillColor(col); c.setFont(f, s)
    for ln in simpleSplit(t, f, s, w): c.drawString(x, y, ln); y -= lead or s * 1.38
    return y
c.setFillColor(OR); c.rect(0, H - 74, W, 74, fill=1, stroke=0); c.setFillColor(colors.white); c.setFont("LSB", 26); c.drawString(M, H - 46, "Focus check"); c.setFont("LS", 11); c.drawString(M, H - 63, "CURVE 35  ·  for whoever fits the lens.  A kit's lens is already set: a kit buyer never does this.")
y = H - 104; c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(M, y, "1  The lens: 32 mm"); y = para(M, y - 18, W - 2 * M, "This camera is built round a 32 mm lens. A 31 mm lens gives soft pictures, a 30 mm lens blurred ones, and the seat cannot be moved far enough to reach them. The lens of a Fujifilm single-use camera is 32 mm; Kodak's is 30 mm.") - 12
c.setFont("LSB", 13); c.setFillColor(INK); c.drawString(M, y, "2  Five things, large dot"); y -= 16
y = para(M, y, W - 2 * M, "Stand five things with print or sharp edges on them (boxes, books) at these distances from the camera, a little apart so each can be seen. Use something far away as the fifth: a roof, a tree. Bright day, large dot.") - 6
x0, x1 = M + 26, W - M - 30; yy = y - 34; c.setStrokeColor(LINE); c.setLineWidth(1.2); c.line(x0, yy, x1, yy); c.setFillColor(INK); c.roundRect(x0 - 26, yy - 9, 26, 18, 3, fill=1, stroke=0); c.circle(x0 + 2, yy, 4.5, fill=1, stroke=0)
POS = (("1 m", .13), ("1.5 m", .26), ("2 m", .40), ("4 m", .62), ("far", 1.0))
for lab, f in POS:
    x = x0 + f * (x1 - x0); c.setFillColor(GOOD if lab == "4 m" else colors.white); c.setStrokeColor(GOOD if lab == "4 m" else INK); c.setLineWidth(1.2); c.rect(x - 7, yy + 4, 14, 20, fill=1, stroke=1); c.setFillColor(INK); c.setFont("LSB", 10); c.drawCentredString(x, yy - 16, lab)
c.setFillColor(GREY); c.setFont("LS", 8.5); c.drawString(x0 - 26, yy - 22, "camera"); c.drawRightString(x1 + 30, yy + 30, "not to scale"); y = yy - 40
c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(M, y, "3  Look"); y -= 17; cw = (W - 2 * M - 16) / 2
for k, (hd, tx) in enumerate((("Without film", "Back off. A strip of frosted tape across the film rails, frosted side to the lens. Hold the rocker level: the shutter stays open. Look at the tape from behind with a magnifier, a coat over your head."), ("With film", "One picture of all five. Look at the scan at full size, in the middle of the picture."))):
    x = M + k * (cw + 16); c.setFillColor(BOX); c.setStrokeColor(LINE); c.setLineWidth(0.8); c.roundRect(x, y - 74, cw, 82, 7, fill=1, stroke=1); c.setFillColor(INK); c.setFont("LSB", 10.5); c.drawString(x + 10, y - 8, hd); para(x + 10, y - 22, cw - 20, tx, s=9.5)
y -= 98; c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(M, y, "4  Which one is sharpest?"); y -= 12
ROWS = (("4 m", "right", "leave it", GOOD), ("2 m", "lens 0.2 mm too far from the film", "seat down 1 layer", INK), ("1.5 m", "0.4 mm too far", "seat down 2 layers", INK), ("1 m", "0.6 to 0.8 mm too far", "seat down 3 layers, look again", INK), ("far", "too near the film", "seat up 1 layer, look again", INK))
for i, (a, b, d, col) in enumerate(ROWS):
    yy = y - 22 * (i + 1); c.setFillColor(BOX if i % 2 == 0 else colors.white); c.rect(M, yy - 6, W - 2 * M, 22, fill=1, stroke=0); c.setFillColor(col); c.setFont("LSB", 11); c.drawString(M + 10, yy, a); c.setFont("LS", 10.5); c.setFillColor(INK); c.drawString(M + 80, yy, b); c.setFont("LSB", 10.5); c.setFillColor(col); c.drawString(M + 300, yy, d)
y -= 22 * len(ROWS) + 16
y = para(M, y, W - 2 * M, "One layer is 0.2 mm. The seat is one number, LENS_SEAT in scad/one135.scad (0.6 to 1.4; drawn at %.1f). Change it, export the front plate, print it again. Only the plate changes." % FJ["lens_seat"], s=10) - 10
c.setFillColor(INK); c.setFont("LSB", 13); c.drawString(M, y, "How much it matters"); y -= 17; sf = FJ["sharp_from_m"]
y = para(M, y, W - 2 * M, "In its place the lens gives a picture that is sharp in the middle and softer toward the ends. In the middle, sharp on a postcard from %.1f m (small dot), %.1f m (middle dot), %.1f m (large dot). A lens 0.2 mm out of place shows only at the large dot, and only on a print; on a phone nothing shows until it is about 0.5 mm out." % (sf["small"]["a postcard"], sf["middle"]["a postcard"], sf["large"]["a postcard"]), s=10) - 8
rg = FJ["rings"]["0.4"]; y = para(M, y, W - 2 * M, "Near ring (optional part): 0.4 mm under the lens sets the camera for %.1f m. Small dot: sharp from %.1f m to far away. Large dot: %.1f to %.0f m." % (rg["set_for_m"], rg["sharp_on_a_postcard_m"]["small"][0], rg["sharp_on_a_postcard_m"]["large"][0], rg["sharp_on_a_postcard_m"]["large"][1]), s=10)
c.setFillColor(GREY); c.setFont("LS", 8.5); c.drawString(M, 30, "From the model (%s, tools/focus.py). Nothing has been printed or photographed yet: the first roll checks this sheet too." % FJ["model"]); c.showPage(); c.save(); print("focus check written")
