"""The build manual: every step with what to do, what you should see, what to do if you don't, and why it is made that way.
Same master list as the kit booklet (tools/steps.py); this is the exhaustive version, for parents, teachers and makers."""
import os, sys, json
sys.path.insert(0, "tools")
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from PIL import Image as PImage
from docs import P_, H1, H2, SM, TC, TB, p, table, footer, INK, GREY, RULE, TINT
from booklet import NAME, MODEL, trim
from steps import STEPS, PARTS, TROUBLE, WEB
W = letter[0] - 36 * mm
def pic(name, w, hmax):
    path = trim(name); iw, ih = PImage.open(path).size; s = min(w / iw, hmax / ih); return Image(path, width=iw * s, height=ih * s)
def how_picture():
    import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    L = json.load(open("build/layout.json")); A = L["A"]; B = L["B"]; cass = (-A["cass"][0], A["cass"][1]); sp = A["spool"]; ro = A["roller"]; fig, ax = plt.subplots(figsize=(7.4, 4.6)); P = plt.Polygon; C = plt.Circle
    ax.add_patch(plt.Rectangle((-61, -3), 121.5, 28.5, fc="#3f434b", ec="none")); ax.add_patch(plt.Rectangle((-61, -6), 121.5, 3, fc="#5a6070", ec="none")); ax.add_patch(plt.Rectangle((B["plate"][0], 25.5), B["plate"][1] - B["plate"][0], 5, fc="#e8641b", ec="none"))
    ax.add_patch(P([(-17.5, 1), (17.5, 1), (4, 25.5), (-4, 25.5)], fc="#17191d", ec="none"))                                             # the dark funnel between lens and film
    for a in (-26, 0, 26):
        fx, fy = 32 * np.sin(np.radians(a)), 32 - 32 * np.cos(np.radians(a)); dx, dy = -fx, 29.3 - fy; ax.plot([fx, fx + dx * 2.6], [fy, fy + dy * 2.6], color="#ffd23f", lw=2.2, zorder=3)
    ax.add_patch(matplotlib.patches.Ellipse((0, 29.6), 9, 3.2, fc="#9fd0ee", ec="#2a78d6", lw=1.2, zorder=5)); ax.plot([-9, -1.2], [26.2, 26.2], color="#e7b416", lw=3, zorder=5); ax.plot([1.2, 9], [26.2, 26.2], color="#e7b416", lw=3, zorder=5); ax.plot([-12, 12], [27.4, 27.4], color="#1b9e8f", lw=3, zorder=4)
    ax.add_patch(C(cass, 12.5, fc="#d9a514", ec="none")); ax.add_patch(C(cass, 3.3, fc="#59b840", ec="none")); ax.add_patch(C(sp, A["ROLL_FULL"], fc="#8a5a3a", ec="none")); ax.add_patch(C(sp, A["CORE_R"], fc="#d0342c", ec="none")); ax.add_patch(C(ro, A["R_ROLL"], fc="#2a78d6", ec="none"))
    aa = np.radians(np.arange(-A["A_L"], A["A_R"] + 1, 2)); film = [(cass[0] + 12.3, cass[1] - 3.5)] + [(32.4 * np.sin(t), 32 - 32.4 * np.cos(t)) for t in aa] + [(ro[0] - 2.5, ro[1] - 5.6), (ro[0] + 4.5, ro[1] - 4.2), (sp[0] - 7.5, sp[1] - 6.8)]
    ax.plot(*zip(*film), color="#8a5a3a", lw=2.6, zorder=6, solid_capstyle="round")
    for n, (x, y), (tx, ty) in ((1, (0, 31.4), (-16, 43)), (2, (-7, 26.2), (-36, 37)), (3, (10, 27.4), (30, 37)), (4, (0, 0.4), (0, 9)), (5, (sp[0], sp[1]), (72, 12)), (5, cass, (-72, 12)), (6, (ro[0], ro[1]), (27, -12))):
        ax.annotate(str(n), (x, y), xytext=(tx, ty), fontsize=13, fontweight="bold", color="white", ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.25", fc="#17191d", ec="none"), arrowprops=dict(arrowstyle="-", color="#17191d", lw=1.2), zorder=9)
    ax.text(0, 66, "light from what you photograph", ha="center", fontsize=10, color="#5b6068"); ax.set_xlim(-80, 80); ax.set_ylim(-17, 70); ax.set_aspect("equal"); ax.axis("off"); plt.tight_layout(pad=0.1); plt.savefig("build/booklet/how.png", dpi=130); plt.close()
def step_block(st):
    rows = [("Do", st["do"]), ("You should see", st["check"])] + ([("If not", st["ifnot"])] if st["ifnot"] else []) + ([("Why", st["why"])] if st["why"] else [])
    txt = [Paragraph(f"<font face='LSB' size=15 color='#c8551a'>{st['n']}</font>", P_)] + [Paragraph(f"<font face='LSB'>{k}.</font> {v}", P_) for k, v in rows]
    t = Table([[pic(st["img"], W * 0.40, 44 * mm), txt]], colWidths=[W * 0.42, W * 0.58]); t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5)])); return KeepTogether([t])
def build():
    how_picture()
    S = [Paragraph(f"{NAME}: build manual", H1), Paragraph(f"{MODEL}.  The complete version of the booklet in the bag: every step, what you should see, what to do if you don't, and why the part is made that way.", SM)]
    S += [Paragraph("What is in the bag", H2), table([["Part", "What it does"]] + [[nm, what] for _, nm, what in PARTS] + [["lens", "bends the light into a sharp picture"], ["spare green winder", "the green winder is the part meant to give way first if a winder is forced"], ["spare shutter", "its rocker stands above the camera: a hard knock from the front or the back can snap it off"]], [W * 0.25, W * 0.75])]
    S += [Paragraph("How it works", H2), Table([[pic("how", W * 0.52, 66 * mm), [p("Seen from above, cut through the middle:"), p("<b>1.</b> Light comes in through the lens at the front."), p("<b>2.</b> A hole in the wheel behind it sets how much light: small, middle or large."),
           p("<b>3.</b> The shutter covers the hole. When you press its rocker, a window in it passes the hole: for that instant light reaches the film."), p("<b>4.</b> The film lies on a curve around the lens, so the whole picture is sharp."),
           p("<b>5.</b> The film starts wound on the red winder. After each picture the green winder winds that piece back into the film's own shell."), p("<b>6.</b> The film turns the blue frame wheel; the arrow on its dial goes round once per picture.")]]], colWidths=[W * 0.54, W * 0.46])]
    for sec, title in (("BUILD", "Build"), ("FILM IN", "Put the film in"), ("PHOTOS", "Take pictures"), ("FILM OUT", "Take the film out")):
        S.append(Paragraph(title, H2)); S += [step_block(st) for st in STEPS if st["sec"] == sec]
        if sec == "PHOTOS": S += [Spacer(1, 4), p("<b>Time pictures, for dim light.</b> Indoors or in shade, with the camera standing on something steady. Set the small dot. Put a fingertip on each side of the rocker and lower the raised side until both sides are level: the shutter is open and stays open. Count. Press the same side on down: closed. (Two fingers, because on most prints the click would otherwise throw the shutter right across.) Seconds to count, as a place to start: by a window 1, lamps on 5, dim room 20. In daylight outdoors, use the dots as in step 1."),
                                 p("<b>Which dot?</b> With ISO 400 film: small dot in full sun, middle dot in hazy sun, large dot under cloud. Film forgives too much light far better than too little: if in doubt between two dots, choose the larger one. With ISO 200 film go one dot larger.")]
    S += [Paragraph("If something is wrong", H2), table([["What you see", "Likely cause", "What to do"]] + [list(r) for r in TROUBLE], [W * 0.30, W * 0.40, W * 0.30])]
    S += [Paragraph("Care", H2), Table([[pic("f1", W * 0.40, 40 * mm), [p("<b>To clean or change the shutter</b> push the front plate up past its click, slide it sideways until it stops, and lift it off. The shutter and the wheel lift off their pegs. To put it back: build steps 7 to 9."), p("<b>After a knock</b> look at the front plate. Its top edge should be level with the top of the camera. If it stands higher, slide it sideways until it stops, then down until it clicks."),
           p("Keep the lens dry and clean. Load and unload in the shade. Do not leave the camera in a hot car: the plastic softens at about 55 C."), p("If the back comes open with film inside, only the pictures you have not taken yet are lost: the ones you took are already in the film's shell."),
           p("<b>Keeping the film in the dark.</b> Leave the film in its tub until the moment you load it. Load in the shade: your own shadow is enough, direct sun is not. Pull out only as much film as reaches the red winder. Close the back before the long wind. From then until the arrow on the dial stops for good, the back stays shut. A finished film goes straight back into its tub. The piece of film that saw daylight while you loaded comes last, so the last picture or two of a roll may be fogged at one end.")]]], colWidths=[W * 0.42, W * 0.58])]
    S += [Paragraph("Your first roll: the reference photograph", H2), p("Print the reference card (CURVE-35_reference_card.pdf) and tape it to a wall in the shade. Stand 4 m away: cut a string that long. Set the large dot, rest the camera on something, and photograph the card in the middle of the picture. "
               "Then, without taking a picture, leave the camera in the sun for two minutes, turning each side to the sun, and wind on: that blank frame shows any light leak."),
          p("When the film comes back, find the smallest group of bars in which you can still count three. Write the number down with the date. Every change anyone makes to this camera is judged against that photograph. The full method, five more frames and how to send in a record are in REFERENCE_PHOTO.md.")]
    S += [KeepTogether([Paragraph("The pinhole experiment: a picture without the lens", H2), Table([[pic("h2", W * 0.40, 44 * mm), [p("The lens pocket takes either the lens or a pinhole disc: a thin metal disc with a hole a quarter of a millimetre across, held flat by the printed pinhole ring. The kit has a disc, laser-drilled. Lesson 1 is built round it."),
           p("<b>1.</b> " + WEB[0]["do"] + " " + WEB[0]["check"]), p("<b>2.</b> " + WEB[1]["do"] + " " + WEB[1]["check"]),
           p("<b>3.</b> " + WEB[2]["do"] + " Seconds, as a place to start with ISO 400 film: sun, open and shut at once; cloud 1; shade 3; indoors by a window 40. " + PINTXT),
           p("To go back to the lens: lift the ring out with a fingernail (it stands a little proud of the plate), tip the disc out, press the lens in."),
           p("Why not print the hole? The smallest round hole a printer makes well is about 1 mm. That is four times too big for a pinhole, and the picture would be that much softer.")]]], colWidths=[W * 0.42, W * 0.58])])]
    SimpleDocTemplate(f"build/{NAME.replace(' ', '-')}_build_manual.pdf", pagesize=letter, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=17 * mm, title=f"{NAME} build manual", author="Variadic Group LLC").build(S, onFirstPage=footer, onLaterPages=footer)
PH = json.load(open("build/pinhole.json")) if os.path.exists("build/pinhole.json") else None
P1J = json.load(open("build/plate1.json")) if os.path.exists("build/plate1.json") else None
P1TXT = (f"By the model the hole lights {P1J['open']['picture_lit_pct']:.1f} % of the picture. " if P1J else "")
PINTXT = (f"At the large dot the hole reaches {PH['wheel']['large dot, hole 0.0 mm off centre']['frame_lit_pct']:.0f} % of the picture; the far corners stay dark." if PH else "")
if __name__ == "__main__":
    build(); print("build manual written")
