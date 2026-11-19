"""Render every picture for the ONE-135 build guide from the OpenSCAD model."""
import subprocess, os, json, sys, concurrent.futures as cf
from PIL import Image
SCAD = "scad/one135.scad"; OUT = "build/guide"; os.makedirs(OUT, exist_ok=True)
def dval(v): return json.dumps(v) if not isinstance(v, bool) else ("true" if v else "false")
def render(name, d, cam=None, size=(1200, 900), ss=2, viewall=False):
    out = f"{OUT}/{name}.png"; raw = out + ".raw.png"
    cmd = ["xvfb-run", "-a", "openscad", "-o", raw, f"--imgsize={size[0] * ss},{size[1] * ss}", "--colorscheme=Tomorrow", "--projection=p"]
    cmd += ["--viewall", "--autocenter", f"--camera=0,0,0,{cam[0]},{cam[1]},{cam[2]},300"] if viewall else [f"--camera={','.join(str(c) for c in cam)}"]
    for k, v in d.items(): cmd += ["-D", f"{k}={dval(v)}"]
    r = subprocess.run(cmd + [SCAD], capture_output=True, text=True, timeout=900)
    if not os.path.exists(raw): print(r.stderr[-1500:]); raise RuntimeError(name)
    im = Image.open(raw).convert("RGB"); px = im.load(); bg = px[0, 0]
    import numpy as np
    a = np.asarray(im).copy(); m = (abs(a.astype(int) - np.array(bg)).sum(2) < 6); a[m] = 255
    Image.fromarray(a).resize(size, Image.LANCZOS).save(out); os.remove(raw); return out
FR = ["body", "wheel", "blade", "front", "lens"]; PRE = ["body", "wheel", "blade", "front"]; INS = ["spool", "spoolcap", "knob", "knob2"]
FRONT_CAM = (0, 30, 0, 62, 0, 232, 470); FRONT_NEAR = (12, 40, 0, 62, 0, 232, 280); REAR_FAR = (4, -26, 0, 46, 0, 24, 450); REAR_TOP = (4, -22, 0, 46, 0, 24, 410)
PLATE_IN = (2, 8, 0, 58, 0, 28, 300); FACE = (0, 12, 2, 70, 0, 205, 300)
STEPS = {
 # ---- build
 "a3": dict(d=dict(PART="guide", G_OLD=["front"], G_NEW=["wheel"], G_VECS=[[0, -38, 0]]), cam=PLATE_IN),
 "a4": dict(d=dict(PART="guide", G_OLD=["front", "wheel"], G_NEW=["blade"], G_VECS=[[0, -38, 0]]), cam=PLATE_IN),
 "a5": dict(d=dict(PART="guide", G_SLID=3.4, G_OLD=["body"], G_NEW=["front", "blade", "wheel"], G_VECS=[[0, 36, 0]] * 3, G_ARROWS=[[[40, 66, 36], [22, 66, 36]]]), cam=(6, 46, 0, 62, 0, 232, 400)),
 "a6": dict(d=dict(PART="guide", G_OLD=PRE, G_NEW=["lens"], G_VECS=[[0, 34, 0]]), cam=FRONT_NEAR),
 "a7": dict(d=dict(PART="guide", G_PHI=0, G_OLD=FR, G_NEW=["tape"], G_VECS=[[0, -34, 0]]), cam=REAR_TOP),
 "a8": dict(d=dict(PART="guide", ROLL_UP=2.4, G_OLD=["back"], G_NEW=["roller"], G_VECS=[[0, 30, 0]], G_ARROWS=[[[40.5, 5.4, 38], [40.5, 5.4, 31]]]), cam=(14, 4, 0, 58, 0, 208, 330)),
 "a9": dict(d=dict(PART="guide", G_OLD=FR, G_NEW=INS, G_VECS=[[0, -44, 0], [0, -44, -16], [0, 0, 30], [0, 0, 30]]), cam=(4, -20, 12, 46, 0, 24, 480)),
 "a10": dict(d=dict(PART="guide", G_OLD=FR + INS, G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2), cam=REAR_FAR),
 # ---- loading
 "l1": dict(d=dict(PART="guide", G_OLD=FR + INS, G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2, G_REV=["back"]), cam=REAR_FAR),
 "l2": dict(d=dict(PART="guide", KNOB_LIFT=3, G_OLD=FR + INS, G_NEW=["cassette"], G_VECS=[[0, -46, 0]], G_ARROWS=[[[-44.7, 11, 39], [-44.7, 11, 51]]]), cam=REAR_TOP),
 "l3": dict(d=dict(PART="guide", G_OLD=FR + INS + ["cassette"], G_NEW=["film_loose"], G_VECS=[[0, 0, 0]], G_TURNS=[[[45.4, 9.2, 38], 11, 0]]), cam=REAR_TOP),
 "l4": dict(d=dict(PART="guide", G_OLD=FR + INS + ["cassette", "film"], G_NEW=["back", "roller"], G_VECS=[[0, -48, 0]] * 2), cam=REAR_FAR),
 "l5": dict(d=dict(PART="guide", G_OLD=FR + INS + ["roller", "back"], G_TURNS=[[[45.4, 9.2, 38], 12, 0]]), cam=(0, 0, 8, 52, 0, 28, 320)),
 # ---- shooting
 "s1": dict(d=dict(PART="guide", G_OLD=["body", "back", "roller"] + INS + ["lens"], G_NEW=["front", "wheel", "blade"], G_VECS=[[0, 0, 0]] * 3), cam=FACE),
 "s0": dict(d=dict(PART="guide", G_OLD=FR + INS + ["roller", "back"]), cam=(0, 8, 20, 30, 0, 0, 300)),
 "s2": dict(d=dict(PART="guide", G_OLD=["body", "back", "roller"] + INS + ["lens", "front", "wheel"], G_NEW=["blade"], G_VECS=[[0, 0, 0]], G_ARROWS=[[[31, 24, 35.5], [8, 24, 35.5]]]), cam=(6, 20, 10, 62, 0, 205, 285)),
 "s4": dict(d=dict(PART="guide", G_PHI=0, G_OLD=["body", "back", "roller"] + INS + ["lens", "front", "wheel"], G_NEW=["blade"], G_VECS=[[0, 0, 0]]), cam=(6, 20, 10, 62, 0, 205, 285)),
 "s3": dict(d=dict(PART="guide", G_OLD=FR + ["spool", "spoolcap", "knob2", "roller", "back"], G_NEW=["knob"], G_VECS=[[0, 0, 0]], G_TURNS=[[[-44.7, 11, 38], 12, 1]]), cam=(0, 0, 8, 52, 0, 28, 320)),
 # ---- taking the shutter out
 "f1": dict(d=dict(PART="guide", G_OLD=["body", "back", "roller"] + INS, G_NEW=["front", "wheel", "blade", "lens"], G_VECS=[[0, 0, 0]] * 4, G_ARROWS=[[[-12, 29, 41], [-12, 29, 28]], [[-4, 36, -33], [14, 36, -33]]]), cam=FACE),
}
PARTS = ["front", "blade", "wheel", "body", "spool", "spoolcap", "roller", "knob", "back"]
BOUGHT = {"hero": dict(d=dict(PART="asm", SHOW_FILM=False, DARK=False), cam=FACE),
          "b_lens": dict(d=dict(PART="guide", G_NEW=["lens"], G_VECS=[[0, 0, 0]]), cam=(0, 30, 0, 70, 0, 200, 60)),
          "b_spool_std": dict(d=dict(PART="guide", G_NEW=["spool_std"], G_VECS=[[0, 0, 0]]), cam=(45.4, 9.2, -2, 72, 0, 200, 190))}
if __name__ == "__main__":
    only = sys.argv[1:]
    jobs = [(k, v["d"], v["cam"], (1200, 900), v.get("viewall", False)) for k, v in {**STEPS, **BOUGHT}.items()]
    jobs += [("p_" + n, dict(PART="g_print", G_P="p_" + n), (55, 0, 25), (800, 600), True) for n in PARTS]
    if only: jobs = [j for j in jobs if j[0] in only]
    with cf.ThreadPoolExecutor(2) as ex: list(ex.map(lambda j: render(j[0], j[1], j[2], size=j[3], viewall=j[4]), jobs))
    print("rendered", len(jobs))
