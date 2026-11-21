"""How each part prints.  One page per part: the part as it stands on the bed, before (v2.4) and now, with the numbers that decide whether it prints:
what it stands on, how tall it is, the thinnest place that has to carry what is printed above it, how far the top sways when the nozzle drags on it,
the thinnest wall or post, what is printed over air, and the shortest layer.
Writes build/printcards.json and build/CURVE-35_print_sheets.pdf.  (Needs the print files: run tools/printcheck.py and tools/pathaudit.py first.)"""
import os, sys, json, subprocess, numpy as np, trimesh
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon
E_PLA = 3000.0; NEW = "build/print/one135_%s.stl"; OLDDIR = "build/old24" if os.path.exists("build/old24") else "previous/v2.4"; OLD = OLDDIR + "/print/one135_%s.stl"; PIC = "build/printcards/"; os.makedirs(PIC, exist_ok=True)      # the version before: in build/old24 here, in previous/v2.4 inside the package

def inertia(g):
    """area, and the smaller principal second moment of area about the centroid, of a shapely (multi)polygon"""
    A = Ix = Iy = Ixy = 0.0; c = g.centroid
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        for ring, sgn in [(p.exterior, 1.0)] + [(r, -1.0) for r in p.interiors]:
            xy = np.asarray(ring.coords) - [c.x, c.y]; x, y = xy[:-1, 0], xy[:-1, 1]; x1, y1 = xy[1:, 0], xy[1:, 1]; cr = x * y1 - x1 * y; s = sgn * np.sign(cr.sum() or 1.0)
            A += s * cr.sum() / 2; Ix += s * (cr * (y * y + y * y1 + y1 * y1)).sum() / 12; Iy += s * (cr * (x * x + x * x1 + x1 * x1)).sum() / 12; Ixy += s * (cr * (x * y1 + 2 * x * y + 2 * x1 * y1 + x1 * y)).sum() / 24
    m = (Ix + Iy) / 2; d = np.hypot((Ix - Iy) / 2, Ixy); return abs(A), max(m - d, 1e-9)
def inscribed(p, hi=8.0):
    """diameter of the largest circle that fits in a polygon"""
    lo = 0.0
    for _ in range(9):
        mid = (lo + hi) / 2
        if p.buffer(-mid).is_empty: hi = mid
        else: lo = mid
    return 2 * lo
def measure(f):
    m = trimesh.load(f, process=True); H = float(m.bounds[1][2]); z = np.arange(0.1, H, 0.2); secs = m.section_multiplane([0, 0, 0], [0, 0, 1], z); A, I, thin = [], [], (99.0, 0.0)
    for k, (h, s) in enumerate(zip(z, secs)):
        if s is None: A.append(0.0); I.append(1e-9); continue
        g = unary_union([p.buffer(0) for p in s.polygons_full]); a, i = inertia(g); A.append(a); I.append(i)
        if k % 3 == 0:
            for p in (g.geoms if hasattr(g, "geoms") else [g]):
                d = inscribed(p)
                if 0.05 < d < thin[0]: thin = (d, float(h))
    A, I = np.array(A), np.array(I); deq = (64 * I / np.pi) ** 0.25                    # the round bar that would be as stiff as this layer
    above = H - z; carry = above > 3.0                                                 # only layers with at least 3 mm of part above them count as carrying something
    kneck = int(np.argmin(np.where(carry, deq, 1e9))) if carry.any() else 0
    sway = float(np.sum((H - z) ** 2 / (E_PLA * I)) * 0.2)                             # mm at the top per newton pushing sideways at the top: a cantilever of changing thickness
    n = np.asarray(m.face_normals); zc = m.triangles_center[:, 2]; over = (-n[:, 2] > 0.72) & (zc > 0.25)
    g0 = [q.buffer(0) for q in secs[0].polygons_full] if secs[0] is not None else []                           # the first layer: how many separate pieces lie on the bed, and how many openings they have
    return dict(first_layer_pieces=len(g0), first_layer_openings=sum(len(q.interiors) for q in g0), height_mm=H, stands_on_mm2=float(A[0]), stands_on_width_mm=float(deq[0]), neck_mm=float(deq[kneck]), neck_at_mm=float(z[kneck]), above_neck_mm=float(above[kneck]), sway_mm_per_N=sway,
                thinnest_mm=float(thin[0]), thinnest_at_mm=float(thin[1]), over_air_mm2=float(m.area_faces[over].sum()), size=[float(x) for x in m.extents])
def shot(scad, part, out, size, stl, under=False):
    c = trimesh.load(stl, process=False).bounds.mean(axis=0)                           # look at the middle of the part, at the same scale for the before and the after picture
    d = max(size) * 3.3; cmd = ["xvfb-run", "-a", "openscad", "-o", out, "--imgsize=700,700", f"--camera={c[0]:.2f},{c[1]:.2f},{c[2]:.2f},{145 if under else 62},0,{200 if under else 28},{d:.0f}", "--projection=o", "-D", 'PART="g_print"', "-D", f'G_P="p_{part}"', scad]
    subprocess.run(cmd, capture_output=True)
    from PIL import Image; im = Image.open(out).convert("RGB"); a = np.asarray(im).copy(); bg = a[0, 0].astype(int); blank = abs(a.astype(int) - bg).sum(2) < 6; a[blank] = 255
    ys, xs = np.where(~blank); Image.fromarray(a[max(ys.min() - 6, 0):ys.max() + 7, max(xs.min() - 6, 0):xs.max() + 7]).save(out)       # cropped to the part: every picture of a pair keeps the same pixels per millimetre

PARTS = [("roller", "Frame wheel (it replaces the sprocket roller)", ["roller"]), ("back", "Back", ["back"]), ("front", "Front plate", ["front"]), ("body", "Body", ["body"]), ("spool", "Take-up spool", ["spool"]), ("knob", "Green winder", ["knob"]),
         ("wheel", "Aperture wheel", ["wheel"]), ("blade", "Shutter", ["blade"])]
SHORT = dict(roller="A wheel 19 mm tall, standing on its teeth, instead of a roller 51 mm tall. No pin, no bracket.", back="No bracket. One solid fork. A solid post for the film. Thicker tongue, fingers and blocks.",
             front="A solid slab with three pockets instead of raised walls and posts. Wider feet.", body="No thin skins, no 1 mm lips. Foot pockets closed all round. One plain pocket for the fork.",
             spool="Stem as thick as the core: 11.2 mm instead of 9.", knob="Blunter fork tips: nothing under 1.2 mm.", wheel="Click spring 1.8 mm instead of 1.6. Finger dish with a flat rim.", blade="Unchanged. Its stops are now steps in the edge of a pocket.")
# what was said, what changed, why it prints.  {names} are filled in from the print files (see FACTS below): no number here is typed twice
SAID = {"roller": ("I just dont see any way the sprocket roller prints successfully... and even the little teeth on it seems impossible",
                   "The roller is gone. In its place is a wheel {h1:.0f} mm tall instead of {h0:.0f}: a short drum with the eight teeth, a 6 mm neck, a collar and the dial. It stands on its teeth. They are the first thing printed, flat on the bed: each is a plain block 1.5 mm wide, 1.5 mm tall and 1.2 mm high. The pin at the roller's foot, and the bracket on the back that held it, are gone too. The wheel stands on a solid post on the back, and its neck turns in one fork.",
                   "It is a 14 mm star on the bed with a 6 mm post on it. Its thinnest level carries {carry1}; the roller's carried {carry0}. The first layer is one piece. The two overhangs, under the collar and under the dial, are 45-degree cones. <b>What it costs:</b> the wheel is only as tall as the film's top row of holes, so the lower half of the film now slides round the post on the back instead of rolling. By the friction model, winding is about one and a half times as heavy."),
        "back": ("The back plate also seems to have an over complication of tabs that look like they could be victim to snapping off or just not printing well",
                 "Read layer by layer, the old back had {thin0} places thinner than three lines of plastic and {tall0} free-standing pieces too tall for their width: the bracket for the roller's pin (3 mm wide, 13 mm tall), the two prongs of the fork, the tips of the winder blocks and of the film ribs, and a light-seal tongue 1 mm wide. Now it has none of either. The bracket is gone. The fork is one solid block, 14 mm wide and 4 mm thick, with a round seat. Beside it stands the film post: a solid rib 30 mm long and 7 to 11 mm thick. The tongue is 1.4 mm. The winder blocks are wider and end square; so do the ribs. The two latch fingers are 1.8 mm thick instead of 1.4 and 36 mm long instead of 25: for the same travel they strain 0.46 % instead of 0.68 % (the limit is 1 %).",
                 "It lies outside face down, and everything on it stands straight up from the plate. The narrow things that are left are named in the audit: the two latch fingers, which are meant to bend, and the light-seal tongue, 1.4 mm wide and 1.8 mm tall, joined to the plate along its whole length. The last millimetre of the film post is its rounded top, where the film slides. Printed alone, those layers take {layer1:.0f} seconds each: print the back on the plate with the body, and smooth the top of the post with a fingernail if it is rough."),
        "front": ("The front plate has all these fine details and raised parts... can I even get that resolution?",
                  "The inner face used to carry raised pieces on a thin floor: two curved click walls, a stop post and thin rims. Now it is a solid slab with three pockets cut into it: one for the shutter, one for the aperture wheel, one for the foot of the handle. The edges of the pockets do what the raised pieces did: the click notches are cut into an edge, and each stop is a step in an edge. Only the two round pegs that the shutter and the wheel turn on, and the four feet, stand up from the slab. The feet are 5.6 mm wide instead of 3.6 and sit 2 mm in from the plate's edge. The latch tongue is 1.6 mm instead of 1.3.",
                  "<b>Can a printer make it?</b> Yes, with an ordinary 0.4 mm nozzle. Across the bed a printer puts an edge within about 0.1 mm of where it is drawn. What it cannot do is lay a wall thinner than its nozzle or a step lower than its layer, so the plate asks for neither: nothing on it is thinner than 1.2 mm (three lines of plastic; the old plate had {thin0} such places), and every level is a whole number of 0.2 mm layers. The finest shapes are the click notches, and they are dents in a solid edge, not pieces of plastic. The print simulation rebuilds them from the slicer's tool paths on five printers, thin to fat: the clicks work on all five, weakly on the thinnest. Print the fit gauge first, then the test slab (the front 4 mm of the body) with this plate, the shutter and the wheel: under two hours, and it tries every fit and every click."),
        "body": ("free standing pieces with suspicious supporting or too fine of detail",
                 "Read layer by layer, the old body had {thin0} places thinner than three lines of plastic. The worst were two skins a quarter of a millimetre thick and 10 mm long, over the pockets for the front plate's upper feet. They had been there since the first version; no earlier check looked for them. The feet now sit 2 mm in from the plate's edge, so each pocket is closed all round by solid wall. The lip outside the light-seal groove is 1.4 mm instead of 1.0. The two ledges for the film roll are 1.6 mm instead of 1.0. The 0.5 mm slivers beside the roller's slots went with the slots: the frame wheel's fork has one plain pocket.",
                 "It prints front face down, as before. Its first layer is one piece with {open1} closed openings: the lens port, the four foot pockets and the latch pocket. {kept1} thin places are kept on purpose: the two side edges of the picture frame, each a ridge 0.9 mm wide and 0.6 mm high on solid plastic. They set the edge of the picture and carry nothing."),
        "spool": ("overall simplify everything where possible",
                  "The stem between the winder and the film is as thick as the core: one plain 11.2 mm column from the winder to the tip, where it was 9 mm. Nothing else changed.",
                  "It stands on its winder. Its thinnest level now carries {carry1}; it was {carry0}. The rule is five times, and this is still the tallest and most slender part in the kit: print it beside the cooling tower, as the plate does."),
        "knob": ("",
                 "The two prongs of the fork ended in tips 1.05 mm thick. The flare at the mouth of the slot and the chamfer round the end are smaller, and nothing on the winder is under 1.2 mm now. The fork's size is unchanged: the film cassette sets it, and it is still the part that breaks first if the winder is forced.",
                 "It stands on its head. Printed alone, the last layers of the prongs take {layer1:.0f} seconds: print the two winders with the spool and the tower, as the plates do."),
        "wheel": ("",
                  "The click spring round the rim is 1.8 mm thick instead of 1.6, the same as the shutter's. The dish on top of the handle has a flat rim instead of a sharp one. A thicker spring is stiffer: on the fattest printer it now strains 0.60 % instead of 0.53 % (the limit is 1 %).",
                  "It lies flat on the bed. The handle is a plain post rising from it."),
        "blade": ("",
                  "Unchanged. Its two stops used to be posts on the front plate; they are now steps in the edge of the pocket it swings in.",
                  "It lies flat on the bed, front face down. The rocker, the hub and the root rise from it; nothing overhangs.")}

if __name__ == "__main__":
    import pathaudit; pa_new = json.load(open("build/pathaudit.json")); pa_old = json.load(open(OLDDIR + "/pathaudit.json")) if os.path.exists(OLDDIR + "/pathaudit.json") else {}
    sl_new = json.load(open("build/slicecheck.json")); out = {}; R1 = json.load(open("build/printrules.json")); R0 = json.load(open("build/printrules_v24.json"))    # the print rules, now and before (tools/printrules.py, run first)
    carry = lambda r: "%.0f mm on a level %.1f mm wide (%.1f times)" % (r["carries"]["above_mm"], r["carries"]["width_mm"], r["carries"]["ratio"])
    for key, title, olds in PARTS:
        now = measure(NEW % key); now.update(longest_bridge_mm=pa_new[key]["longest_bridge_mm"], shortest_layer_s=pa_new[key]["shortest_layer_s"], print_time=sl_new[key]["time"], grams=sl_new[key]["grams"])
        before = []
        for o in olds:
            b = measure(OLD % o); b.update(longest_bridge_mm=pathaudit.bridges_of(OLD % o, f"build/slice/before_{o}.gcode")[0], shortest_layer_s=pa_old.get(o, {}).get("shortest_layer_s"), part=o); before.append(b)      # the version before, sliced and measured the same way
            shot(OLDDIR + "/one135.scad", o, f"{PIC}{o}_old.png", max(now["size"], b["size"], key=max), OLD % o)
        shot("scad/one135.scad", key, f"{PIC}{key}_new.png", max([now["size"]] + [b["size"] for b in before], key=max), NEW % key)
        r0, r1 = R0[key], R1[key]
        rules = dict(skins=[len(r0.get("skins", [])), len(r1.get("skins", []))], thin=[len(r0["thin"]), len(r1["thin"]) + len(r1.get("accepted", []))], kept=len(r1.get("accepted", [])), tall=[len(r0["slender"]), len(r1["slender"])], carries=[r0["carries"], r1["carries"]], strips=[dict(kind=q["kind"], what=q["what"], width=q["width"]) for q in r1["strips"]],
                     unexplained=sum(q["kind"] == "not explained" for q in r1["strips"]), kept_why=sorted({q["what"] + ": " + q["why"] for q in r1.get("accepted", [])}))
        facts = dict(h0=before[0]["height_mm"], h1=now["height_mm"], thin0=rules["thin"][0], thin1=rules["thin"][1], kept1={0: "No", 1: "One", 2: "Two", 3: "Three"}.get(rules["kept"], str(rules["kept"])), tall0=rules["tall"][0], tall1=rules["tall"][1], carry0=carry(r0), carry1=carry(r1),
                     open1={0: "no", 4: "four", 5: "five", 6: "six"}.get(now["first_layer_openings"], str(now["first_layer_openings"])), layer1=now["shortest_layer_s"], bridge1=now["longest_bridge_mm"])
        out[key] = dict(title=title, now=now, before=before, rules=rules, facts=facts); print(f"{key:7s} now: stands on {now['stands_on_mm2']:.0f} mm2, {now['height_mm']:.1f} tall, neck {now['neck_mm']:.1f} mm at {now['neck_at_mm']:.1f} carrying {now['above_neck_mm']:.1f}, sway {now['sway_mm_per_N']:.3f} mm/N, thinnest {now['thinnest_mm']:.2f}"
                                                              f" | before: neck {before[0]['neck_mm']:.1f}, sway {before[0]['sway_mm_per_N']:.3f}, thinnest {before[0]['thinnest_mm']:.2f}")
    json.dump(out, open("build/printcards.json", "w"), indent=1)
