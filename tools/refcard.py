"""The reference card and the record sheet: one fixed thing to photograph, so that every design change is judged against the same picture.
Writes build/CURVE-35_reference_card.pdf (page 1: the card, page 2: how to use it and the record), reference/record_template.json, reference/index.csv (header only)."""
import os, json, math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

NAME, CARD = "CURVE 35", "R1"
F_LENS, DIST = 32.0, 4000.0                                   # focal length and the camera-to-card distance, mm.  4 m is where the lens is focused (LENS_SEAT)
MAG = F_LENS / (DIST - F_LENS)                                # size on film / size on the card
GROUPS = [5, 7, 10, 14, 20, 28, 40]                           # line pairs per mm ON THE FILM when the card is photographed from DIST
period = lambda f: 1.0 / (f * MAG)                            # mm on the card for one black bar plus one white gap
N_STAR, R_STAR = 18, 40.0                                     # star: 18 black spokes, 40 mm radius
star_lpmm = lambda r: N_STAR / (2 * math.pi * r * MAG)        # what the star shows at radius r

def bars(c, x, y, f, vertical):
    """three black bars with two white gaps, in a square 2.5 periods on a side, bottom left corner at (x, y) in mm"""
    P = period(f); w = 2.5 * P
    for i in range(3):
        if vertical: c.rect((x + i * P) * mm, y * mm, P / 2 * mm, w * mm, stroke=0, fill=1)
        else: c.rect(x * mm, (y + i * P) * mm, w * mm, P / 2 * mm, stroke=0, fill=1)
    return w

def pair(c, x, y, f, gap, label_h=None):
    """a vertical-bar group and a horizontal-bar group side by side, with the number under them; returns (width, height)"""
    w = bars(c, x, y, f, True); bars(c, x + w + gap, y, f, False)
    h = label_h or max(3.2, min(9.0, w * 0.22)); c.setFont("Helvetica-Bold", h * mm / 0.72); c.drawCentredString((x + w + gap / 2) * mm, (y - h - 1.2) * mm, str(f))
    return 2 * w + gap, w

def finder(c, x, y, s=12.0):
    c.setFillGray(0); c.rect(x * mm, y * mm, s * mm, s * mm, stroke=0, fill=1); c.setFillGray(1); c.rect((x + s / 6) * mm, (y + s / 6) * mm, s * 2 / 3 * mm, s * 2 / 3 * mm, stroke=0, fill=1)
    c.setFillGray(0); c.rect((x + s / 3) * mm, (y + s / 3) * mm, s / 3 * mm, s / 3 * mm, stroke=0, fill=1)

def card(c):
    W, H = 279.4, 215.9; c.setFillGray(0); c.setStrokeGray(0)
    for fx, fy in ((8, 8), (W - 20, 8), (8, H - 20), (W - 20, H - 20)): finder(c, fx, fy)
    c.setFont("Helvetica-Bold", 15); c.drawString(26 * mm, (H - 15.5) * mm, f"{NAME}  REFERENCE CARD {CARD}")
    c.setFont("Helvetica", 9.5); c.drawString(26 * mm, (H - 20.5) * mm, "Tape flat to a wall. Camera 4 m away (cut a string 4 m long), square to the wall. Print at 100 %: no scaling.")
    # the star
    cx, cy = 54.0, H - 72.0
    for i in range(N_STAR): c.wedge((cx - R_STAR) * mm, (cy - R_STAR) * mm, (cx + R_STAR) * mm, (cy + R_STAR) * mm, i * 360.0 / N_STAR, 180.0 / N_STAR, stroke=0, fill=1)
    c.setLineWidth(0.6); c.circle(cx * mm, cy * mm, R_STAR * mm, stroke=1, fill=0)
    c.setFont("Helvetica", 7.5); c.drawCentredString(cx * mm, (cy - R_STAR - 4.2) * mm, f"star: {star_lpmm(R_STAR):.0f} at the rim, {star_lpmm(R_STAR / 2):.0f} half way in, {star_lpmm(R_STAR / 4):.0f} a quarter of the way out")
    # grey steps
    gx, gy, gs = 14.0, H - 142.0, 16.0
    for i, g in enumerate((1.0, 0.75, 0.5, 0.25, 0.0)):
        c.setFillGray(g); c.rect((gx + i * gs) * mm, gy * mm, gs * mm, gs * mm, stroke=1, fill=1)
    c.setFillGray(0); c.setFont("Helvetica", 7.5); c.drawString(gx * mm, (gy - 4) * mm, "five steps, white to black: how many can you tell apart?")
    # which way up
    ux, uy = 34.0, 38.0; pth = c.beginPath(); pth.moveTo(ux * mm, (uy + 26) * mm); pth.lineTo((ux - 13) * mm, (uy + 8) * mm); pth.lineTo((ux - 5) * mm, (uy + 8) * mm); pth.lineTo((ux - 5) * mm, uy * mm); pth.lineTo((ux + 5) * mm, uy * mm); pth.lineTo((ux + 5) * mm, (uy + 8) * mm); pth.lineTo((ux + 13) * mm, (uy + 8) * mm); pth.close(); c.drawPath(pth, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 30); c.drawString((ux + 16) * mm, (uy + 3) * mm, "R")
    c.setFont("Helvetica", 7.5); c.drawString(14 * mm, (uy - 5) * mm, "arrow up, R the right way round: the scan is not flipped")
    # bar groups: lines per mm on the film at 4 m
    x0 = 104.0; ya = H - 30.0 - 2.5 * period(5); wa, ha = pair(c, x0, ya, 5, 5.0)
    xs = x0 + wa + 7.0; ys = H - 30.0
    for f in (20, 28, 40):
        w = 2.5 * period(f); ys -= w; pair(c, xs, ys, f, 2.0, 3.4); ys -= 7.5
    yb = ya - 14.0 - 2.5 * period(7); wb, hb = pair(c, x0, yb, 7, 4.5); pair(c, x0 + wb + 8.0, yb + (hb - 2.5 * period(10)), 10, 4.0)
    yc = yb - 13.0 - 2.5 * period(14); wc, hc = pair(c, x0, yc, 14, 3.0)
    # a box for the frame's code, written thick so that it can be read in the photograph itself
    bx, by, bw, bh = x0 + wc + 12.0, yc - 9.0, 78.0, 2.5 * period(14) + 9.0; c.setLineWidth(1.2); c.rect(bx * mm, by * mm, bw * mm, bh * mm, stroke=1, fill=0)
    c.setFont("Helvetica", 7.5); c.drawString(bx * mm, (by - 4) * mm, "write this roll's code here with a thick marker (two or three big characters)")
    c.setFont("Helvetica", 9.5); c.drawString(26 * mm, (H - 25.2) * mm, "Bars: the number is lines per mm on the film from 4 m (from 2 m, halve it). Find the smallest group where you can still count three bars.")
    # the scale
    sx, sy = 40.0, 13.0; c.setLineWidth(0.8); c.line(sx * mm, sy * mm, (sx + 200) * mm, sy * mm)
    for i in range(0, 201, 10): c.line((sx + i) * mm, sy * mm, (sx + i) * mm, (sy + (4 if i % 50 == 0 else 2)) * mm)
    c.setFont("Helvetica", 7.5); c.drawString((sx + 2) * mm, (sy - 4) * mm, "this line is 200 mm long. Check it with a ruler: if it is not, the numbers on this card are wrong.")

FIELDS = [("Record number", "given when it is accepted, like R1-0007"), ("Date, and who", ""), ("Camera", "model and version; what was changed, one change at a time"), ("Printer, filament, fit-gauge slot", ""), ("Build", "lens (which one) or pinhole ring"),
          ("Film, lab, scan size", "same film and same lab within one comparison"), ("Frame 1: C, open shade, card in the middle, 4 m", "smallest group you can count: upright bars ___  lying bars ___   star grey out to ___ of its width   grey steps seen ___ of 5"),
          ("Frame 2 and 3: card in a corner", "smallest group: ___ and ___"), ("Frame 4: S, full sun", "smallest group: ___   too dark / right / too bright"), ("Frame 5: T, indoors, 1 second, on a table", "smallest group: ___   distance ___ m"),
          ("Frame 6: leak frame (no picture taken, 2 minutes in sun, every side)", "clear / marks: where?"), ("Frame 7: plain sky or a white wall", "dark corners?  lines along the film?  spots?"), ("Spacing of the frames on the film", "even / overlapping / gaps"),
          ("Shutter, if filmed in slow motion", "fast press ___ s   slow press ___ s   blade seen to bounce back into the light: yes / no"), ("Against the record before", "better / the same / worse, and why you think so")]

def sheet(c):
    W, H = 279.4, 215.9; c.setFillGray(0); c.setFont("Helvetica-Bold", 14); c.drawString(14 * mm, (H - 16) * mm, f"{NAME} reference photograph: the record")
    c.setFont("Helvetica", 9); y = H - 23
    for line in ("One card, one distance, the same seven frames at the start of a roll. Every change to the camera is judged against the record before it. Change one thing at a time.",
                 "Rest the camera on something solid. Press the raised side of the rocker flat in one quick press. Keep the scans as the lab gave them: no sharpening, no cropping."):
        c.drawString(14 * mm, y * mm, line); y -= 4.6
    y -= 3; rh = 10.4; c.setLineWidth(0.5)
    for k, hint in FIELDS:
        c.setFont("Helvetica-Bold", 8.5); c.drawString(14 * mm, (y - 4) * mm, k); c.setFont("Helvetica", 8); c.setFillGray(0.35); c.drawString(118 * mm, (y - 4) * mm, hint); c.setFillGray(0)
        c.line(14 * mm, (y - rh + 2.6) * mm, (W - 14) * mm, (y - rh + 2.6) * mm); y -= rh
    c.setFont("Helvetica", 8); c.drawString(14 * mm, 9 * mm, "Send: this record (or record.json), the scans, and what you changed. See REFERENCE_PHOTO.md.")

TEMPLATE = dict(id=None, card=CARD, date="YYYY-MM-DD", by="initials or class",
                camera=dict(model="ONE-135", version="2.4", change="none (baseline)", printer="", filament="", fit_gauge_slot=None, build="lens", lens=""),
                film=dict(stock="", iso=400, lab="", scan_long_side_px=None),
                frames=[dict(frame=1, setting="C", light="open shade", distance_m=4.0, card="centre", finest_group_upright=None, finest_group_lying=None, star_grey_fraction=None, grey_steps_seen=None, notes=""),
                        dict(frame=2, setting="C", light="open shade", distance_m=4.0, card="top left corner", finest_group_upright=None, finest_group_lying=None, notes=""),
                        dict(frame=3, setting="C", light="open shade", distance_m=4.0, card="bottom right corner", finest_group_upright=None, finest_group_lying=None, notes=""),
                        dict(frame=4, setting="S", light="full sun", distance_m=4.0, card="centre", finest_group_upright=None, finest_group_lying=None, exposure="right", notes=""),
                        dict(frame=5, setting="T", light="indoors by a window, 1 s, on a table", distance_m=4.0, card="centre", finest_group_upright=None, finest_group_lying=None, notes=""),
                        dict(frame=6, setting="S", light="no picture taken: 2 minutes in sun, every side", leak_frame_clear=None, notes=""),
                        dict(frame=7, setting="C", light="plain sky or white wall", dark_corners=None, lines_along_film=None, notes="")],
                frame_spacing="even", shutter_time_s=dict(fast_press=None, slow_press=None), shutter_bounce_seen=None, against_previous="", files=[])
INDEX_COLS = ["id", "date", "by", "version", "change", "build", "printer", "film", "centre_upright", "centre_lying", "corner_worst", "sun_centre", "time_centre", "leak_frame_clear", "lines_along_film", "frame_spacing", "shutter_fast_s", "shutter_slow_s", "shutter_bounce", "against_previous"]

if __name__ == "__main__":
    os.makedirs("build", exist_ok=True); os.makedirs("reference/records", exist_ok=True)
    c = canvas.Canvas("build/CURVE-35_reference_card.pdf", pagesize=landscape(letter)); c.setTitle(f"{NAME} reference card {CARD}"); c.setAuthor("ONE-135 tools")
    card(c); c.showPage(); sheet(c); c.showPage(); c.save()
    json.dump(TEMPLATE, open("reference/record_template.json", "w"), indent=1)
    if not os.path.exists("reference/index.csv") or len(open("reference/index.csv").read().strip().splitlines()) <= 1: open("reference/index.csv", "w").write(",".join(INDEX_COLS) + "\n")      # no record yet: the header may still change
    print("magnification %.5f" % MAG, {f: round(period(f), 2) for f in GROUPS}, "star lp/mm at rim, half, quarter:", [round(star_lpmm(R_STAR / k), 1) for k in (1, 2, 4)])
