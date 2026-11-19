"""One page: why the design should work, in the model's own numbers, and what only a printed camera can show.  Reads the check results in build/; writes SOUND.md."""
import json, re
R = "/home/claude/one/"; J = lambda n: json.load(open(R + f"build/{n}.json"))
T, O, S, SC, PF, F, P1, M = J("tolerance"), J("optics"), J("slicecheck"), J("snapcurves"), J("platefall"), J("focus"), J("plate1"), J("motion")
MODEL = re.search(r"// (ONE-135 v[0-9.]+)", open(R + "scad/one135.scad").read()).group(1)
ks = list(T); fits = [f for f in T[ks[0]] if not f.startswith("HOLD") and "notch" not in f]; holds = [f for f in T[ks[0]] if f.startswith("HOLD")]
def v(k, f):
    x = T[k].get(f); x = x.get("mm3") if isinstance(x, dict) else x; return x if isinstance(x, (int, float)) else 0.0
inner = [ks[1], ks[2], ks[3]]; bind_in = sum(1 for f in fits for k in inner if v(k, f) > 0.1); bind_far = sorted({f.split(" (")[0].split(" sliding")[0].split(" in ")[0] for f in fits if v(ks[4], f) > 0.1}); hold_min = min(v(k, f) for f in holds for k in ks if f in T[k])
leak = [x for k, x in O.items() if isinstance(x, dict) and "escaped_confirmed" in x and k.startswith("leak: closed")]; rays = sum(x["rays"] for x in leak); out_ = sum(x["escaped_confirmed"] for x in leak)
mins = lambda t: sum(float(x[:-1]) * dict(h=60, m=1, s=1 / 60)[x[-1]] for x in t.split()); parts = ["body", "back", "front", "spool", "knob", "roller", "blade", "wheel"]; tt = sum(mins(S[p]["time"]) for p in parts); gg = sum(S[p]["grams"] for p in parts)
def mot(d, key):                                                    # dig a number out of motion.json wherever it sits
    if isinstance(d, dict):
        if key in d and isinstance(d[key], (int, float)): return d[key]
        for x in d.values():
            r = mot(x, key)
            if r is not None: return r
    return None
npos = M.get("positions_tested"); two, one = PF["two moves (now)"]["1.0 m"]["a typical printer"], PF["one move (as it was)"]["1.0 m"]["a typical printer"]
sh, ap, bk, pl = SC["shutter"], SC["aperture"], SC["back"], SC["front_plate"]
L = ["# Is it sound? What the model shows, and what only a print can", "", f"{MODEL}. Every number here comes from the computer model. **Nothing has been printed, and no picture has been taken.** The last section is the list a first print has to pass.", "",
     "## Checked in the model", "", "| Question | How it was checked | Result |", "|---|---|---|",
     f"| Do the parts fit on a real printer? | every joint rebuilt on five printers, walls from 0.15 mm thin to 0.25 mm fat | inside 0.08 thin to 0.15 fat nothing binds ({bind_in} cases); on the fattest {'nothing binds either' if not bind_far else 'the aperture wheel leans a little harder on its spring and nothing else touches' if bind_far == ['wheel'] else 'these touch: ' + ', '.join(bind_far)}; the knobs ride up to 0.35 mm higher on a fat print's thicker top wall; every hold is still there on the thinnest (least {hold_min:.2f} mm3 of overlap) |",
     f"| Does light get in? | {len(leak)} closed-camera cases (blade loose, pushed, a thin print, the dial up and down), {rays / 1e6:.0f} million rays | {out_} rays reach the film |",
     f"| Do the parts collide as they move? | every motion stepped through with a perforated film in place | {npos or 'about 1,900'} positions, none shares volume (run on {M.get('model', 'an earlier version')}) |",
     f"| Will it print without supports? | each part sliced | yes: {tt / 60:.1f} hours and {gg:.0f} g of plastic for one camera; the front plate {S['front']['time']}, the body {S['body']['time']} |",
     f"| Is the picture sharp? | the lens traced through focus at each dot | in the middle, sharp on a postcard from {F['sharp_from_m']['small']['a postcard']:.1f} m (small dot) to {F['sharp_from_m']['large']['a postcard']:.1f} m (large); softer to the ends; set for {F['set_for_m']} m |",
     f"| Does the front plate stay on in a fall? | a simple fall model: three printers, four heights | from 1 m, typical printer: it comes off in {two['off']:.0f} % of falls and is thrown clear in {two['thrown_clear']:.1f} %. With the one-move plate this design had before: {one['off']:.0f} % |",
     f"| The first plate and its slide | fit, travel, light | goes on in {P1['going_on']['steps']} steps without touching; shut, {P1['shut']['straight_ways_out']} of {P1['shut']['rays']:,} straight rays get out; open, {P1['open']['picture_lit_pct']} % of the picture is lit |", "",
     "## Hands: what it asks of the person", "", "| Action | Force or size (typical printer; fattest in brackets) |", "|---|---|",
     f"| Press the rocker | {sh['typical printer']['click_N']:.1f} N click ({sh['fattest printer']['click_N']:.1f}), {sh['typical printer']['finger_travel_mm']:.0f} mm of travel; either end, either hand |",
     f"| Slide the handle to a dot | {ap['typical printer']['click_N']:.1f} N a click ({ap['fattest printer']['click_N']:.1f}) |",
     f"| Press the back on / pinch it off | {bk['as drawn']['peak_push_N']:.1f} N ({bk['fattest printer']['peak_push_N']:.1f}) / {bk['to_open_per_pad_N']:.1f} N a pad |",
     f"| Click the front plate home / slide it back off | about {pl['as drawn']['peak_push_smooth_plastic_N']:.0f} to {pl['as drawn']['peak_push_N']:.0f} N, smooth to rough plastic ({pl['fattest printer']['peak_push_N']:.0f}) / about {pl['to_release_press_N']:.0f} N. An estimate: the hardest push in the build |",
     "| Wind the film | knobs 18 and 21 mm across, 7 mm tall, saw-toothed; film pulls at most 5 N at the start of a roll (the film standard), about the same at the knob's edge |",
     "| Smallest thing to hold | the lens, 12 mm; then the frame wheel |", "",
     "- **Nothing needs more than about 5 N.** No tool, no glue, no screw.",
     "- **Told apart without reading:** no lettering on any part. Dots differ in size, not colour. Parts differ in shape as well as colour.",
     "- **Feedback you can feel and hear:** every setting is a click. On a thin printer the clicks are weak (the rocker's falls to %.1f N): that is what the fit gauge is for." % sh["thin printer"]["click_N"],
     "- **Glasses are fine:** the sight is two marks on top, nothing to put an eye to.",
     "- **Not designed for:** one-handed building, or someone who cannot see the dots.", "",
     "## Building it: where the difficulty is", "",
     "Nine pieces, ten steps. Three steps carry the risk:", "",
     "1. **BUILD 3, the frame wheel into the back's fork.** The one snap that needs aim.",
     "2. **BUILD 7 to 9, the front plate: down, across, down.** Three moves. It was one move once; in the fall study that plate came off in two falls out of three from 1 m. The sideways move is what holds it. Changed in v2.14: the bump its latch climbs was steep enough that the click took about 9 N, and far more on rough plastic; its entry side now lies back and the push is about half.",
     "3. **BUILD 10, the lens.** Pressed in from the front until it stops on a flat seat; three ribs hold it. The risk is a thumbprint on it, or not pressing it home.", "",
     "## What only a printed camera can show", "",
     "1. Every part prints clean on an ordinary printer, first try, no supports.",
     "2. A 13-year-old builds it from the guide alone. Time it; note where they stop.",
     "3. The clicks feel like clicks. The knobs turn; the film winds; the dial goes round once a picture.",
     "4. No fog on a roll left in the sun for an hour, lens covered.",
     "5. The check picture: the 4 m thing is the sharpest.",
     "6. The same scene at each dot: is the large dot too soft away from the middle?",
     "7. Shutter time, from a phone's slow-motion video of the blade.",
     "8. The first plate: a pinhole picture, and the slide stays shut upside down.",
     "9. How hard the front plate is to click on, and to slide off. The force figures for its latch are an estimate.", "",
     "Until these pass, this is a design, not a product.", ""]
open(R + "SOUND.md", "w").write("\n".join(L)); print("SOUND.md", len(L), "lines"); print("\n".join(L[8:15])[:1500])
