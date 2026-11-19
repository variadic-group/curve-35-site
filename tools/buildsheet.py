"""ONE-135 build sheet: one sheet, two sides (US Letter)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepInFrame
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PI
F = "/usr/share/fonts/truetype/liberation/LiberationSans-"
for n, f in (("LS", "Regular"), ("LSB", "Bold"), ("LSI", "Italic")): pdfmetrics.registerFont(TTFont(n, F + f + ".ttf"))
pdfmetrics.registerFontFamily("LS", normal="LS", bold="LSB", italic="LSI")
INK = colors.HexColor("#1c1e22"); ACC = colors.HexColor("#c8551a"); GREY = colors.HexColor("#5b6068"); RULE = colors.HexColor("#c9ccd1"); TINT = colors.HexColor("#f4f1ec")
B = ParagraphStyle("b", fontName="LS", fontSize=9.2, leading=12.1, textColor=INK, spaceAfter=1.2)
S = ParagraphStyle("s", parent=B, fontSize=8.7, leading=11.4, textColor=GREY)
H = ParagraphStyle("h", fontName="LSB", fontSize=11.5, leading=14, textColor=ACC, spaceBefore=5, spaceAfter=3)
T = ParagraphStyle("t", fontName="LSB", fontSize=24, leading=27, textColor=INK)
ST = ParagraphStyle("st", parent=B, fontSize=10, leading=13.5, textColor=GREY)
W = letter[0] - 28 * mm
def img(path, w):
    iw, ih = PI.open(path).size; return Image(path, width=w, height=w * ih / iw)
def P(t, st=B): return Paragraph(t, st)
def steps(items, start=1): return [P(f"<b>{i}.</b> {t}") for i, t in enumerate(items, start)]
def tbl(rows, widths, head=True, size=9.0):
    t = Table([[P(str(c), ParagraphStyle("c", parent=B, fontSize=size, leading=size + 2.2, fontName="LSB" if (head and r == 0) else "LS")) for c in row] for r, row in enumerate(rows)], colWidths=widths)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE), ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if head: st += [("BACKGROUND", (0, 0), (-1, 0), TINT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, GREY)]
    t.setStyle(TableStyle(st)); return t
def cols(left, right, wl=0.5, gap=6 * mm):
    t = Table([[left, right]], colWidths=[W * wl - gap / 2, W * (1 - wl) - gap / 2])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, 0), gap), ("RIGHTPADDING", (1, 0), (1, 0), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t
def box(flow, w=W):
    t = Table([[flow]], colWidths=[w]); t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("BOX", (0, 0), (-1, -1), 0.6, ACC), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])); return t
st = []
# ------------------------------------------------------------------ side 1
st += [P("ONE-135", T), P("One simple 35 mm film camera: 9 printed parts, 1 spring, 2 screws, a lens from a used disposable. No supports, no glue, no printed threads. "
                           "It pre-winds the roll, so every shot goes straight back into the cassette and the finished film is already sealed.", ST), Spacer(1, 4)]
st += [cols(img("build/fig/hero_front.png", W * 0.43), img("build/fig/exploded_labelled.png", W * 0.53), wl=0.45, gap=4 * mm), Spacer(1, 3)]
st += [tbl([["Film", "Lens", "Focus", "Apertures", "Shutter", "Size"],
            ["135 full frame, curved on a 32 mm radius", "salvaged, about 32 mm; view 64° × 41°", "fixed: 1.5 m to the horizon at f/11", "f/8, 11, 16, 22 and P (pinhole stop, time)",
             "about 1/300 s (simulated; 1/200 to 1/400)", "120 × 59 × 39 mm; about 140 g of filament"]], [W / 6] * 6, size=8.6), Spacer(1, 5)]
left = [P("Print: 9 parts, no supports, each flat on the face named", H),
        tbl([["#", "Part", "Bed face", "Notes"], ["1", "lever", "front", "pins point up"], ["2", "front plate + finder", "front", "one-layer skins bridge the lens port and screw holes"],
             ["3", "shutter blade", "front", "0.6 mm thick; its pivot pin points up"], ["4", "aperture wheel", "back", ""], ["5", "body", "front", "about 6 h; every cavity opens upward"],
             ["6", "take-up spool", "knob", "brim"], ["7", "sprocket roller + dial", "dial", "brim"], ["8", "wind knob", "head", ""], ["9", "back", "outside", "exposure guide engraved"]],
            [6 * mm, 35 * mm, 15 * mm, None]),
        Spacer(1, 3), P("Black PLA or PETG, 0.2 mm layers, 0.4 mm nozzle, 4 walls, 20 % infill. About 10 to 12 hours in total (estimate, not sliced). "
                        "Body, back, front plate, blade and wheel must be opaque: hold a 0.6 mm chip of your filament against a bright lamp first.", S)]
right = [P("Buy or salvage: 5 pieces", H),
         P("<b>Lens</b> from a used disposable camera. Measure its flange; if it is not 12.0 mm, set LENS_D in the model and re-export the front plate."),
         P("<b>Spring.</b> Small extension spring, about 2.4 mm across and 9.7 mm between hooks when relaxed, pulling about 0.15 N at 10.7 mm and 0.45 N at 14.6 mm. "
           "To make one: 30 close turns of a plain 0.010 in (0.25 mm) steel guitar string on a 2 mm rod, last half-turn at each end bent out as a hook."),
         P("<b>2 screws.</b> M3 × 10 self-tapping, pan head (or No. 4 × 3/8 in)."),
         P("<b>Pinhole shim</b> (only for P). A 6 mm disc of drinks-can aluminium with a 0.23 mm needle hole."),
         P("<b>Optional:</b> a 1/4 in-20 nut pressed into the base for a tripod."),
         Spacer(1, 4),
         box([P("Print the shutter test first", ParagraphStyle("hb", parent=H, spaceBefore=0)),
              P("The shutter is the only mechanism. Print <b>one135_test_slab.stl</b> (15 minutes: the front 4 mm of the body) with the front plate, blade, wheel and lever, "
                "and do assembly steps 1 to 5 on it. The screws poke out of the slab, so rest it over a gap. The lever should snap the blade across both ways and the wheel should click. Then print the rest.")],
             w=W * 0.5 - 3 * mm)]
st += [cols(left, right)]
st += [PageBreak()]
# ------------------------------------------------------------------ side 2
st += [img("build/fig/section.png", W * 0.86), Spacer(1, 1)]
asm = [P("Assembly", H)] + steps([
    "<b>Front plate.</b> Push the skin out of the lens port from behind with a pencil and trim the edge.",
    "<b>Wheel.</b> For P, glue the pinhole shim into the wheel's shallow seat. Lay the body on its back. Seen from the front, put the wheel on the body with its centre hole over the small hole just below and to the right of the port.",
    "<b>Blade.</b> Drop the blade's pin into the hole 19 mm to the left of the port. The blade lies on top of the wheel.",
    "<b>Front plate on.</b> Lower it so the wheel's handle comes through the curved slot and the three pins find their holes. Drive the two screws; they pierce their skins.",
    "<b>Spring and lever.</b> Hook one end of the spring onto the neck of the lever's small pin. Through the window, hook the other end into the hole in the blade's tail. "
    "Hold the lever pointing straight up, press its pivot into the keyed hole, and swing it to one side. Now it cannot come off.",
    "<b>Lens.</b> Press it into its pocket, bulge outward, until the flange sits on the seat.",
    "<b>Back parts.</b> Camera face down. Drop in the sprocket roller (teeth at the bottom) and the take-up spool, press the wind knob into the hole above the cassette chamber, and snap the back on. Pinch the two pads to open it."])
asm += [Spacer(1, 4), P("Checked in software", H),
        P("Fit: every pair of parts in 11 shutter, lever and aperture states, plus full sweeps, with film and cassette in place: no interference. "
          "Light path: clear to the whole frame, with 10 % to spare at f/8. Leaks: 18 million rays from the film with the shutter closed; none leaves in a straight line. "
          "Shutter: simulated with friction; completes its swing up to a friction coefficient of 0.8. Printing: every part is one watertight body, no overhang past 45°, no bridge over 12 mm.", S),
        P("Check on your first print", H),
        P("The back's two latches, the lens fit and the wind knob's grip are untested snap and press fits. Shoot one cheap roll to prove the light seals. "
          "If a negative shows a faint second image the blade is bouncing: stick a scrap of felt on each of the two stop posts.", S)]
use = [P("Loading (subdued light)", H)] + steps([
    "Camera face down, back off. Lift out the sprocket roller. Lift the wind knob, drop the cassette into the left chamber with its long hub down, and press the knob back, turning it until its fork drops in.",
    "Pull the leader across to the take-up spool and tuck its tip into the slot. Turn the spool one turn anticlockwise so it grips.",
    "Drop the sprocket roller back in behind the film, teeth in the lower row of perforations.",
    "Snap the back on. Its guide presses the film into place.",
    "<b>Pre-wind:</b> turn the take-up spool knob anticlockwise until it stops. The turns of the frame dial are your number of frames."])
use += [P("Shooting", H)] + steps([
    "Set the aperture from the guide on the back.", "Frame through the peep hole and the wire frame.", "Flick the lever across. Either direction takes one picture.",
    "Turn the wind knob clockwise until the frame dial has made one full turn."])
use += [P("When the dial stops turning as you wind, the film is home: open the back in any light."), Spacer(1, 3),
        tbl([["", "Sun", "Haze", "Cloud", "Dull"], ["ISO 400", "f/22", "f/16", "f/11", "f/8"], ["ISO 200", "f/16", "f/11", "f/8", ""]], [16 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm]), Spacer(1, 3),
        P("<b>P, time exposures.</b> P can be selected only while the lever rests toward the lens. Put the camera on something solid. Flick the lever away from the lens: the blade stops open. "
          "Flick it back to close. ISO 400: sun, a quick open-and-shut; cloud 1 s; shade 4 s. With the lens left out the same hole makes a true pinhole camera with a wider view.")]
st += [cols(asm, use)]
doc = SimpleDocTemplate("build/ONE-135_build_sheet.pdf", pagesize=letter, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                        title="ONE-135 build sheet", author="Camera Ladder")
def foot(c, d):
    c.setFont("LS", 7); c.setFillColor(GREY); c.drawString(14 * mm, 6 * mm, "ONE-135 build sheet  ·  designed and checked in software, not yet printed  ·  side %d of 2" % d.page)
doc.build(st, onFirstPage=foot, onLaterPages=foot)
from pypdf import PdfReader
print("pages:", len(PdfReader("build/ONE-135_build_sheet.pdf").pages))
