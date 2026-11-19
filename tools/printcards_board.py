"""One picture for a quick look: every reworked part before and now, each pair at one scale, as it stands on the bed.
Uses the pictures tools/printcards.py made.  Writes build/CURVE-35_before_now.png."""
import sys, json
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "tools"); from booklet import NAME, MODEL, PREV
PIC = "build/printcards/"; F = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"
font = lambda size, bold=False: ImageFont.truetype(F % ("Bold" if bold else "Regular"), size)
D = json.load(open("build/printcards.json")); INK, GREY, RULE, ACC = (26, 28, 32), (95, 100, 108), (214, 218, 224), (200, 85, 26)
n = lambda k: D[k]["now"]; b = lambda k, i=0: D[k]["before"][i]
r = lambda k: D[k]["rules"]; c = lambda k, i: r(k)["carries"][i]
TILES = [("Frame wheel (was the roller)", ["roller_old"], "roller_new", f"{b('roller')['height_mm']:.0f} mm tall to {n('roller')['height_mm']:.0f}; stands on its teeth; carries {c('roller', 0)['ratio']:.1f} to {c('roller', 1)['ratio']:.1f} times its width"),
         ("Back", ["back_old"], "back_new", f"{r('back')['thin'][0]} thin places and {r('back')['tall'][0]} tall free-standing pieces to none"),
         ("Front plate", ["front_old"], "front_new", "raised walls and posts to a solid slab with three pockets"),
         ("Body", ["body_old"], "body_new", f"{r('body')['thin'][0]} thin places to {r('body')['thin'][1]} (kept on purpose: the picture's edges)"),
         ("Take-up spool", ["spool_old"], "spool_new", f"stem as thick as the core; carries {c('spool', 0)['ratio']:.1f} to {c('spool', 1)['ratio']:.1f} times its width"),
         ("Wind knob", ["knob_old"], "knob_new", "blunter fork tips: nothing under 1.2 mm"),
         ("Aperture wheel", ["wheel_old"], "wheel_new", "click spring 1.6 to 1.8 mm; dish with a flat rim"),
         ("Shutter", ["blade_old"], "blade_new", "unchanged")]
COLS, TW, AH, PAD, HEAD, GAP = 4, 470, 290, 22, 84, 16
def fit(olds, new):
    pics = [Image.open(PIC + o + ".png") for o in olds] + [Image.open(PIC + new + ".png")]; aw = TW - 18 - GAP * (len(pics) - 1) - 10
    k = min(aw / sum(p.width for p in pics), AH / max(p.height for p in pics), 1.0); return [p.resize((max(1, round(p.width * k)), max(1, round(p.height * k))), Image.LANCZOS) for p in pics], aw
FIT = [fit(olds, new) for _, olds, new, _ in TILES]; rows = (len(TILES) + COLS - 1) // COLS
RH = [max(max(q.height for q in FIT[i][0]) for i in range(r * COLS, min(len(TILES), (r + 1) * COLS))) + 108 for r in range(rows)]; W, H = COLS * TW + PAD * 2, HEAD + sum(RH) + 46
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
d.text((PAD, 20), f"{NAME}: every part before and now", font=font(30, True), fill=INK); d.text((PAD, 58), f"{MODEL}.  Each pair is drawn at one scale, standing on the bed the way it prints.  Left: " + PREV + ".  Right: now.", font=font(15), fill=GREY)
for i, (title, olds, new, note) in enumerate(TILES):
    r = i // COLS; x0 = PAD + (i % COLS) * TW; y0 = HEAD + sum(RH[:r]); ah = RH[r] - 108; pics, aw = FIT[i]; d.line([(x0, y0 + 6), (x0 + TW - 18, y0 + 6)], fill=RULE, width=1)
    d.text((x0, y0 + 14), title, font=font(19, True), fill=INK); d.text((x0, y0 + 40), note, font=font(13), fill=ACC)
    x = x0 + (aw - sum(q.width for q in pics)) / 2
    for j, q in enumerate(pics):
        im.paste(q, (round(x), round(y0 + 66 + (ah - q.height))))
        lab = "now" if j == len(pics) - 1 else "before"; d.text((round(x + q.width / 2 - d.textlength(lab, font=font(12)) / 2), y0 + 70 + ah), lab, font=font(12), fill=GREY)
        if j == len(pics) - 2: d.line([(round(x + q.width + GAP / 2), y0 + 70), (round(x + q.width + GAP / 2), y0 + 64 + ah)], fill=RULE, width=1)
        x += q.width + GAP
d.text((PAD, H - 30), "Drawn from the print files; nothing has been printed.  Numbers and reasons, part by part: " + NAME.replace(" ", "-") + "_print_sheets.pdf", font=font(13), fill=GREY)
im.save("build/CURVE-35_before_now.png"); print("board", im.size)
