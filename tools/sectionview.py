"""Cut the assembled camera with a plane and draw what is there.  python3 tools/sectionview.py out.png axis value xmin xmax ymin ymax [parts...]
axis x: picture is y (across) by z (up) at that x;  axis z: picture is x by y at that z."""
import sys, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon
COL = dict(body="#9aa3ad", back="#4f6d8f", roller="#d98a2b", film="#7a4a2a", front="#c9b458", knob="#5a9a6a", spool="#5a9a6a", cassette="#b8b8b8")
def cut(out, axis, val, box, parts, asm="build/asm"):
    fig, ax = plt.subplots(figsize=(11, 11 * (box[3] - box[2]) / (box[1] - box[0])))
    n = np.eye(3)[dict(x=0, y=1, z=2)[axis]]; keep = [i for i in range(3) if n[i] == 0]
    for p in parts:
        t = trimesh.load(f"{asm}/{p}.stl", process=True); s = t.section(plane_origin=n * val, plane_normal=n)
        if s is None: continue
        for e in s.entities:
            q = s.vertices[e.points][:, keep]; ax.fill(q[:, 0], q[:, 1], color=COL.get(p.split("_")[0], "#888"), alpha=0.55, lw=0); ax.plot(q[:, 0], q[:, 1], color="k", lw=0.5)
    ax.set_xlim(box[0], box[1]); ax.set_ylim(box[2], box[3]); ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.set_title(f"{axis} = {val}   " + ", ".join(parts))
    ax.set_xticks(np.arange(np.ceil(box[0]), box[1] + 0.01, 1 if box[1] - box[0] < 30 else 5)); ax.set_yticks(np.arange(np.ceil(box[2]), box[3] + 0.01, 1 if box[3] - box[2] < 30 else 5)); ax.tick_params(labelsize=6)
    fig.savefig(out, dpi=95, bbox_inches="tight"); plt.close(fig)
if __name__ == "__main__":
    a = sys.argv; cut(a[1], a[2], float(a[3]), [float(x) for x in a[4:8]], a[8:] or ["body", "back", "roller", "film"])
