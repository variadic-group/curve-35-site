"""quick looks: python3 tools/shot.py out.png cam key=value ...   (guide-mode parts lists as JSON)"""
import subprocess, sys
def shot(out, defs, cam, size=(1100, 1000), proj="o", edges=True, scad="/home/claude/one/scad/one135.scad"):
    cmd = ["xvfb-run", "-a", "openscad", "-o", out, f"--imgsize={size[0]},{size[1]}", f"--camera={cam}", "--colorscheme=Tomorrow", f"--projection={proj}"]
    if edges: cmd += ["--view=edges"]
    for k, v in defs.items(): cmd += ["-D", f"{k}={v}"]
    r = subprocess.run(cmd + [scad], capture_output=True, text=True, timeout=900)
    if r.returncode: print(r.stderr[-800:])
    return out
