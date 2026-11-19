"""Every joint in the camera against a fatter or a thinner printer: which is the first to bind, which hold is the first to go, and what a wedge would do there.
Reads build/tolerance.json (five printers), build/focus.json and build/plate1.json; writes build/joints.json and WEDGE.md.  Model only: nothing has been printed."""
import json, math
R = "/home/claude/one/"; T = json.load(open(R + "build/tolerance.json")); F = json.load(open(R + "build/focus.json")); ks = list(T.keys()); WALL = [0.0, 0.10, 0.15, -0.08, 0.25, -0.15]
val = lambda k, fit: (T[k].get(fit) or {}).get("mm3") if isinstance(T[k].get(fit), dict) else T[k].get(fit)
JOINT = (("shutter", ("blade",)), ("aperture wheel", ("wheel (all", "wheel against", "wheel click")), ("front plate on the body", ("front plate",)), ("frame wheel", ("frame wheel",)), ("back on the body", ("back ", "back +")),
         ("wind knob", ("wind knob",)), ("spool", ("spool",)), ("film shell in its chamber", ("cassette",)))
def joint_of(fit):
    f = fit.replace("HOLD ", "")
    return next((j for j, keys in JOINT if any(f.startswith(k) for k in keys)), None)
out = {}
for j, _ in JOINT: out[j] = dict(binds_from_mm=None, binds_mm3_far_fat=0.0, hold_drawn=None, hold_far_thin=None)
for fit in T[ks[0]]:
    j = joint_of(fit); v = [val(k, fit) for k in ks]
    if j is None or not all(isinstance(x, (int, float)) for x in v): continue
    if fit.startswith("HOLD"):
        if out[j]["hold_drawn"] is None or v[5] / max(v[0], 1e-9) < out[j]["hold_far_thin"] / max(out[j]["hold_drawn"], 1e-9): out[j]["hold_drawn"], out[j]["hold_far_thin"] = v[0], v[5]
    elif "notch" not in fit:                                           # the shutter's notch is a spring: it is meant to give
        fat = sorted((w, x) for w, x in zip(WALL, v) if w > 0); first = next((w for w, x in fat if x > 0.1), None)           # under 0.1 mm3 is two faces that are meant to touch (a knob's head resting on the body), not a bind
        if first is not None and (out[j]["binds_from_mm"] is None or first < out[j]["binds_from_mm"]): out[j]["binds_from_mm"] = first
        out[j]["binds_mm3_far_fat"] = max(out[j]["binds_mm3_far_fat"], v[4])
P1 = json.load(open(R + "build/plate1.json")); t10 = math.tan(math.radians(10))
out["slide in the first plate"] = dict(wedge_since="v2.14", seats_mm={"typical": round((0.4 - 0.04) / (2 * t10), 2), "fat": round((0.6 - 0.04) / (2 * t10), 2), "thin": round((-0.32 - 0.04) / (2 * t10), 2)}, shut_straight_ways_out=P1["shut"]["straight_ways_out"])
out["lens on its seat"] = dict(flat_datum=True, step_mm=0.2, room_postcard_mm=F["room"])
NOW = {"shutter": "pivot on a peg; a spring tooth in a notch", "aperture wheel": "turns in a round pocket; a spring tooth clicks in three notches", "front plate on the body": "four hooked feet into pockets: down, across, down; a leaf latch",
       "frame wheel": "snaps into a fork in the back", "back on the body": "pressed straight on; stepped rim (the light trap); two fingers with catches", "wind knob": "round journal in a round bore, slid in from behind",
       "spool": "round journal in a round bore, slid in from behind", "film shell in its chamber": "loose, on purpose", "slide in the first plate": "wedge at its shut end, square stop at its open end", "lens on its seat": "flat seat (whole layers), three crush ribs"}
WEDGE = {"spool": "not yet.  It has 0.65 mm of room all round: loose on purpose.  A cone under its head would take the rattle out, but the head lying flat on the body is the light seal there, so that waits for a printed camera", "wind knob": "the same",
         "back on the body": "leave.  It passes on all five printers and its stepped rim is the most-tested light trap in the camera",
         "frame wheel": "leave.  It has to come away with the back when film goes in, so it keeps its fork; pinched between cones it would drop out",
         "front plate on the body": "already one: its hooks are 43-degree wedges that pull it onto the body's flat face, and that face sets the focus.  The sideways move seats the side lips, its second hold if it is knocked upward; that move stays until a fall test on a real print says the lips can go",
         "aperture wheel": "leave: its tooth is already a spring", "shutter": "leave: its tooth is already a spring", "lens on its seat": "leave: this is the one distance that must be exact, so it stays a flat stop; the ribs are the give",
         "slide in the first plate": "done (v2.14)", "film shell in its chamber": "leave"}
ORDER = ["spool", "wind knob", "back on the body", "frame wheel", "front plate on the body"]
json.dump(out, open(R + "build/joints.json", "w"), indent=1)
def trouble(j):
    o = out[j]
    if j == "slide in the first plate": return "none: seats %+.1f mm (typical printer), %+.1f (fat), %+.1f (thin); no straight way for light" % (o["seats_mm"]["typical"], o["seats_mm"]["fat"], o["seats_mm"]["thin"])
    if j == "lens on its seat": return "a lens 0.2 mm out of place shows on a postcard at the large dot only"
    a = ("binds only on the fattest printer (walls +%.2f mm)" % o["binds_from_mm"] if o["binds_from_mm"] >= 0.25 else "binds when walls print %.2f mm fat" % o["binds_from_mm"]) if o["binds_from_mm"] else "never binds"
    b = "; %d %% of its hold is left on the thinnest" % round(100 * o["hold_far_thin"] / o["hold_drawn"]) if o["hold_drawn"] else ""
    return a + b
L = ["# Wedges: joints that find their own fit", "",
     "Model ONE-135 v2.14. From the model; nothing has been printed. Written by `tools/joints.py` from the five-printer fit check, the focus study and the first plate's check.", "",
     "## The rule", "",
     "**A flat face where the position must be exact. A wedge everywhere else.** A stepped fit needs the printer to hit a gap. A wedge needs nothing: the part goes in until it meets, a fat print stops a little sooner, a thin one a little later, and a tight one is eased on one slanted face by whoever printed it. (Kits are checked on a fit gauge before they are bagged; there is no sandpaper in the box.) That only works where \\\"a little sooner or later\\\" does no harm. The lens-to-film distance is the one place it does, so that stays a flat stop and the wedge's job there is to push the part against it.", "",
     "## What the five-printer check says", "",
     "Each joint is checked on five printers, from walls 0.15 mm thin to 0.25 mm fat (the fattest also spreads its first layers 0.4 mm). Two numbers per joint: the wall error at which it first binds, and how much of its hold is left on the thinnest printer.", "",
     "**No joint in the camera fails inside that range.** Nothing binds until the fattest printer, and every hold is still there on the thinnest. The fits are loose on purpose (0.65 mm round the knobs, 0.6 mm in the light trap) and the clicks are springs.", "",
     "**Corrected.** The first version of this page said the spool and wind knob bind first, at walls 0.15 mm fat. That was wrong: what the check saw there was each knob's head resting on the body, which it is meant to do. They bind only on the fattest printer.", "",
     "| Joint | How it fits now | On the five printers | As a wedge |", "|---|---|---|---|"]
rank = sorted(out, key=lambda j: (0 if j == "slide in the first plate" else 1, ORDER.index(j) if j in ORDER else 99))
for j in rank: L.append("| %s | %s | %s | %s |" % (j, NOW[j], trouble(j), WEDGE[j]))
L += ["", "## Done in v2.14: the first wedge", "",
      "The slide in the first plate. Its lower end and the pocket's lower end are the same wedge, 10 degrees a side. Pushed down it stops where the two meet: no gap at the sides, and friction keeps it shut whichever way up the camera is (before, only its own weight did). Lifted 2 mm it runs as freely as before. Its open end is still a square stop, because that end sets where the hole stands.", "",
      "## Wedges the camera already had", "",
      "- The front plate's four hooks and side lips: 43 degrees, pulling the plate against the body.",
      "- Each foot's far end tapers 0.8 mm a side, so it finds its pocket.",
      "- The wind knob's fork has a flared mouth, so it finds the bar in the film's shell.",
      "- The lens pocket has a lead-in, and three crush ribs that give.", "",
      "## Not cut into the body, and why", "",
      "The four changes proposed first (cones for the knobs, a V rim on the back, cone tips for the frame wheel, the front plate straight down) were looked at joint by joint before any plastic was moved. None is needed for fit, two would make the camera worse (the frame wheel would fall out with the back off; the front plate would lose its second hold), and the other two touch light seals that only a printed camera can judge. The table gives each one's reason.", "",
      "**What would reopen them:** the first printed camera. If the knobs rattle, the cone under the head is the fix. If the plate's three moves are too fiddly for a 13-year-old, the lips are the thing to redesign, with a fall test.", ""]
open(R + "WEDGE.md", "w").write("\n".join(L).replace('\\"', '"')); print("\n".join(L[12:24]).replace('\\"', '"')[:3800])
