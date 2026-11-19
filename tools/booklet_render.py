"""Render every picture of the kit booklet from the OpenSCAD model (colours and arrows come from the model's guide mode)."""
import subprocess, os, json, sys, concurrent.futures as cf, numpy as np
from PIL import Image
SCAD = "scad/one135.scad"; OUT = "build/booklet"; os.makedirs(OUT, exist_ok=True)
def dval(v): return json.dumps(v) if not isinstance(v, bool) else ("true" if v else "false")
def render(name, d, cam=None, size=(1200, 900), ss=2, viewall=False):
    out = f"{OUT}/{name}.png"; raw = out + ".raw.png"
    if os.path.exists(out) and os.path.getmtime(out) > max(os.path.getmtime(SCAD), os.path.getmtime("scad/layout.scad"), os.path.getmtime(__file__)): return out
    cmd = ["xvfb-run", "-a", "openscad", "-o", raw, f"--imgsize={size[0] * ss},{size[1] * ss}", "--colorscheme=Tomorrow", "--projection=p"]
    cmd += ["--viewall", "--autocenter", f"--camera=0,0,0,{cam[0]},{cam[1]},{cam[2]},300"] if viewall else [f"--camera={','.join(str(c) for c in cam)}"]
    for k, v in d.items(): cmd += ["-D", f"{k}={dval(v)}"]
    r = subprocess.run(cmd + [SCAD], capture_output=True, text=True, timeout=1800)
    if not os.path.exists(raw): print(r.stderr[-1500:]); raise RuntimeError(name)
    im = Image.open(raw).convert("RGB"); bg = im.getpixel((0, 0)); a = np.asarray(im).copy(); a[(abs(a.astype(int) - np.array(bg)).sum(2) < 6)] = 255
    Image.fromarray(a).resize(size, Image.LANCZOS).save(out); os.remove(raw); return out
FR = ["body", "wheel", "blade", "front", "lens"]; PRE = ["body", "wheel", "blade", "front"]; INS = ["spool", "knob"]; TAKE = ["spool"]
BOX = ["body", "spool", "knob", "roller", "back"]; P1 = ["plate1", "slide1"]       # the dark box (BUILD 1 to 4); the first plate and its slide (rung 1, on the web)
FRONT_NEAR = (12, 40, 0, 62, 0, 232, 280); REAR_FAR = (4, -26, 0, 46, 0, 24, 450); REAR_TOP = (4, -22, 0, 46, 0, 24, 410); PLATE_IN = (2, 8, 0, 58, 0, 28, 300); FACE = (0, 12, 2, 70, 0, 205, 300); TOP = (0, 0, 8, 52, 0, 28, 320)
G = lambda **k: dict(PART="guide", G_MESH=True, **k)
STEPS = {
 # ---- build
 "b1": (G(G_OLD=["front"], G_NEW=["blade"], G_VECS=[[0, -38, 0]]), PLATE_IN),
 "b2": (G(G_OLD=["front", "blade"], G_NEW=["wheel"], G_VECS=[[0, -38, 0]]), PLATE_IN),
 "b3": (G(G_ROT=[-90, 0, 0], G_SLID=4.6, G_SIDE=3.2, G_OLD=["front", "blade", "wheel"], G_NEW=BOX, G_VECS=[[0, -40, 0]] * 5, G_AUTO=False, G_ARROWS=[[[46, -13, -12], [46, 21, -12]], [[-46, -13, -12], [-46, 21, -12]]]), (0, 0, 2, 64, 0, 28, 400)),
 "b3b": (G(G_SLID=4.6, G_SIDE=3.2, G_OLD=BOX, G_NEW=["front", "blade", "wheel"], G_VECS=[[0, 0, 0]] * 3, G_ARROWS=[[[-24, 36, 18], [0, 36, 18]]]), (0, 20, 6, 66, 0, 200, 250)),
 "b3c": (G(G_SLID=4.6, G_SIDE=0, G_OLD=BOX, G_NEW=["front", "blade", "wheel"], G_VECS=[[0, 0, 0]] * 3, G_ARROWS=[[[-42, 34, 24], [-42, 34, 2]]]), (0, 20, 6, 66, 0, 200, 250)),
 "b3d": (G(G_SLID=0, G_SIDE=0, G_OLD=BOX, G_NEW=["front", "blade", "wheel"], G_VECS=[[0, 0, 0]] * 3), (0, 20, 6, 66, 0, 200, 250)),
 "b4": (G(G_OLD=PRE + BOX[1:], G_NEW=["lens"], G_VECS=[[0, 34, 0]]), FRONT_NEAR),
 "b6": (G(G_OLD=["body"], G_NEW=TAKE, G_VECS=[[0, -44, 0]] * 2, G_ARROWS=[[[45.5, -30, 42], [45.5, -2, 42]]]), REAR_FAR),
 "b7": (G(G_OLD=["body"] + TAKE, G_NEW=["knob"], G_VECS=[[0, -40, 0]]), REAR_FAR),
 "b8": (G(ROLL_UP=2.5, G_OLD=["back"], G_NEW=["roller"], G_VECS=[[0, 26, 0]], G_ARROWS=[[[27.57, 5.4, 46], [27.57, 5.4, 39]]]), (20, 4, 6, 58, 0, 208, 250)),
 "b9": (G(G_OLD=["body"] + INS, G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2, G_ARROWS=[[[-10, -46, 36], [-10, -12, 36]]]), REAR_FAR),
 # ---- film in
 "l1": (G(G_OLD=FR + INS, G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2, G_ARROWS=[[[-10, -12, 36], [-10, -46, 36]]]), REAR_FAR),
 "l2": (G(G_OLD=["cassette"], G_NEW=["knob"], G_VECS=[[0, 0, 26]]), (-45, 10, 12, 70, 0, 28, 230)),
 "l3": (G(G_OLD=FR + TAKE, G_NEW=["cassette", "knob"], G_VECS=[[0, -46, 0]] * 2, G_ARROWS=[[[-44.9, -34, 42], [-44.9, -4, 42]]]), REAR_TOP),
 "l4": (G(G_OLD=FR + INS + ["cassette"], G_NEW=["film_loose"], G_VECS=[[0, 0, 0]]), REAR_TOP),
 "l5": (G(G_OLD=FR + INS + ["cassette", "film"], G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2, G_ARROWS=[[[-10, -46, 36], [-10, -12, 36]]]), REAR_FAR),
 "l6": (G(G_OLD=FR + ["knob", "back"], G_NEW=TAKE + ["roller"], G_VECS=[[0, 0, 0]] * 2, G_TURNS=[[[45.5, 8.7, 38.5], 12, 0]]), TOP),
 # ---- pictures
 "s1": (G(G_OLD=["body", "back", "roller"] + INS + ["lens"], G_NEW=["front", "wheel", "blade"], G_VECS=[[0, 0, 0]] * 3), FACE),
 "s2": (G(G_OLD=FR + INS + ["roller", "back"]), (0, 8, 20, 30, 0, 0, 300)),
 "s3": (G(G_OLD=["body", "back", "roller"] + INS + ["lens", "front", "wheel"], G_NEW=["blade"], G_VECS=[[0, 0, 0]], G_ARROWS=[[[24.5, 24.5, 56], [24.5, 24.5, 40]]]), (6, 20, 10, 62, 0, 205, 285)),
 "s4": (G(G_OLD=FR + TAKE + ["back"], G_NEW=["knob", "roller"], G_VECS=[[0, 0, 0]] * 2, G_TURNS=[[[-44.9, 10.0, 38.5], 11, 1]]), TOP),
 "s5": (G(G_PHI=0, G_STOP=0, G_OLD=["body", "back", "roller"] + INS + ["lens", "front"], G_NEW=["blade", "wheel"], G_VECS=[[0, 0, 0]] * 2), (6, 20, 10, 62, 0, 205, 285)),
 # ---- film out
 "u1": (G(G_OLD=FR + TAKE, G_NEW=["cassette", "knob"], G_VECS=[[0, -46, 0]] * 2, G_ARROWS=[[[-44.9, -4, 42], [-44.9, -34, 42]]]), REAR_TOP),
 "f1": (G(G_OLD=["body", "back", "roller"] + INS, G_NEW=["front", "wheel", "blade", "lens"], G_VECS=[[0, 0, 0]] * 4, G_ARROWS=[[[-44, 34, 2], [-44, 34, 24]], [[-24, 36, 34], [0, 36, 34]]]), (0, 20, 6, 66, 0, 200, 250)),
 "cassette": (G(G_NEW=["cassette"], G_VECS=[[0, 0, 0]]), (-45, 10, 0, 68, 0, 28, 150)),
 "dial": (G(G_OLD=["body", "back", "front", "wheel", "blade", "lens"], G_NEW=["roller", "spool", "knob"], G_VECS=[[0, 0, 0]] * 3), (27.57, 9, 30, 36, 0, 12, 118)),
 "hero": (G(G_OLD=[], G_NEW=["body", "back", "roller", "spool", "knob", "front", "wheel", "blade", "lens"], G_VECS=[[0, 0, 0]] * 9), FACE),
 "pr": (G(G_OLD=["body"], G_NEW=["front", "wheel", "blade", "pinring"], G_VECS=[[0, 0, 0]] * 3 + [[0, 34, 0]], G_AUTO=True), FRONT_NEAR),
 "k_inside": (G(G_OLD=["front"], G_NEW=["wheel", "blade"], G_VECS=[[0, 0, 0]] * 2), PLATE_IN),
 "section": (dict(PART="asm", SECTION=True, DARK=False, SHOW_BACK=True), (0, 12, 0, 0, 0, 0, 330)),
 "hero_back": (G(G_OLD=[], G_NEW=["body", "back", "roller"] + INS + ["front", "wheel", "blade", "lens"], G_VECS=[[0, 0, 0]] * 9), (0, -10, 6, 58, 0, 32, 340)),     # the finished camera from behind: the rocker and the plate's top edge show over the top
 # ---- rung 1, the first picture: a hole and a slide (on the web with lesson 1)
 "r1": (G(G_OLD=["plate1"], G_NEW=["slide1"], G_VECS=[[0, -38, 0]]), PLATE_IN),
 "r2": (G(G_ROT=[-90, 0, 0], G_SLID=4.6, G_SIDE=3.2, G_OLD=P1, G_NEW=BOX, G_VECS=[[0, -40, 0]] * 5, G_AUTO=False, G_ARROWS=[[[46, -13, -12], [46, 21, -12]], [[-46, -13, -12], [-46, 21, -12]]]), (0, 0, 2, 64, 0, 28, 400)),
 "r3": (G(G_SLID=4.6, G_SIDE=3.2, G_OLD=BOX, G_NEW=P1, G_VECS=[[0, 0, 0]] * 2, G_ARROWS=[[[-24, 36, 18], [0, 36, 18]], [[-42, 34, 24], [-42, 34, 2]]]), (0, 20, 6, 66, 0, 200, 250)),
 "r4": (G(G_OLD=BOX + P1, G_NEW=["pinring"], G_VECS=[[0, 34, 0]]), FRONT_NEAR),
 "r5": (G(G_UP=10, G_OLD=BOX + ["plate1", "pinring"], G_NEW=["slide1"], G_VECS=[[0, 0, 0]], G_ARROWS=[[[-7, 27, 44], [-7, 27, 62]]]), (0, 20, 10, 64, 0, 205, 270)),
 "x1": (G(G_OLD=BOX, G_NEW=P1 + ["pinring"], G_VECS=[[0, 0, 0]] * 3, G_ARROWS=[[[-44, 34, 2], [-44, 34, 24]], [[-24, 36, 34], [0, 36, 34]]]), (0, 20, 6, 66, 0, 200, 250)),
 "r_hero": (G(G_OLD=[], G_NEW=BOX + P1 + ["pinring"], G_VECS=[[0, 0, 0]] * 8), FACE),
 "h2": (G(G_OLD=PRE + BOX[1:], G_NEW=["pindisc", "pinring"], G_VECS=[[0, 18, 0], [0, 38, 0]]), (0, 30, 0, 66, 0, 215, 215)),            # v2.16: the pinhole disc, then the ring over it, in the lens pocket in place of the lens
 "h_hero": (G(G_OLD=[], G_NEW=["body", "back", "roller", "spool", "knob", "front", "wheel", "blade", "pindisc", "pinring"], G_VECS=[[0, 0, 0]] * 10), FACE),
 "lens": (G(G_NEW=["lens"], G_VECS=[[0, 0, 0]]), (0, 30, 0, 70, 0, 200, 60)),
 "pinset": (G(G_NEW=["pindisc", "pinring"], G_VECS=[[-7, 0, 0], [7, 0, 0]]), (0, 30, 0, 62, 0, 200, 70)),     # v2.16: the pinhole disc and its ring side by side (the website's part card)
}
PARTS = ["front", "blade", "wheel", "body", "spool", "roller", "knob", "back"]
if __name__ == "__main__":
    only = sys.argv[1:]
    jobs = [(k, v[0], v[1], (1200, 900), False) for k, v in STEPS.items()] + [("p_" + n, dict(PART="g_print", G_P="p_" + n), (55, 0, 25), (800, 600), True) for n in PARTS + ["plate1", "slide1", "pinring", "pindisc"]]
    if only: jobs = [j for j in jobs if j[0] in only]
    with cf.ThreadPoolExecutor(2) as ex: list(ex.map(lambda j: render(j[0], j[1], j[2], size=j[3], viewall=j[4]), jobs))
    print("rendered", len(jobs))
