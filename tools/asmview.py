"""Pictures of the assembled camera, each part in its own colour (same shading as the preview sheets).
usage: python3 tools/asmview.py out.png [az el px_per_mm [blade_phi]]  ...  or import asm_image()"""
import sys, json, numpy as np, trimesh
from PIL import Image
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
COL = dict(body=(176, 182, 194), back=(150, 170, 206), front=(232, 132, 62), blade=(129, 69, 192), wheel=(232, 190, 60), roller=(74, 138, 222), knob=(214, 84, 76), spool=(214, 84, 76), lens=(120, 200, 235))
THETA = json.load(open("build/layout.json"))["B"]["THETA"]
def load_parts(phi=None, parts=("body", "back", "front", "blade", "wheel", "roller", "knob", "spool", "lens"), A="build/asm/"):
    phi = THETA if phi is None else phi; out = {}
    for n in parts:
        f = {"blade": "blade_PHI%s" % phi, "wheel": "wheel_STOP2"}.get(n, n)
        out[n] = trimesh.load(A + f + ".stl", process=True)
    return out
def asm_image(P, az, el, ppm, SS=2, pad=10, box=None):
    """P: dict name -> mesh (world frame: +y toward the subject, +z up).  az: 0 = seen from the front, 180 = from behind; el: elevation."""
    V = np.vstack([m.vertices for m in P.values()]); F = []; C = []; o = 0
    for n, m in P.items(): F.append(m.faces + o); C += [COL[n]] * len(m.faces); o += len(m.vertices)
    m = trimesh.Trimesh(V, np.vstack(F), process=False); C = np.array(C, float)
    a, e = np.radians(az), np.radians(el); f = -np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])          # az 0: the eye is in front (+y), looking toward -y
    up = np.array([0, 0, 1.0]) if abs(el) < 89.9 else np.array([0, -1.0, 0]); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    c = (V.min(0) + V.max(0)) / 2; Q = V - c; xs, ys = Q @ r, Q @ u; s = ppm * SS
    if box is not None:                                                                                   # box: world-space box to frame (lo, hi)
        B = np.array([[x, y, z] for x in (box[0][0], box[1][0]) for y in (box[0][1], box[1][1]) for z in (box[0][2], box[1][2])]) - c; xs, ys = B @ r, B @ u
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); W = int(np.ceil((x1 - x0) * s)) + 2 * pad * SS; Hh = int(np.ceil((y1 - y0) * s)) + 2 * pad * SS
    jx, jy = np.meshgrid(np.arange(W), np.arange(Hh)); X = x0 + (jx - pad * SS + 0.5) / s; Y = y1 - (jy - pad * SS + 0.5) / s; far = np.abs(Q @ f).max() + 10
    O = (c + X[..., None] * r + Y[..., None] * u - far * f).reshape(-1, 3); D = np.broadcast_to(f, O.shape); rt = Fast(m)
    depth = np.full(len(O), np.inf); tri = np.full(len(O), -1)
    for k in range(0, len(O), 1500000):
        loc, ir, it = rt.intersects_location(O[k:k + 1500000], D[k:k + 1500000], multiple_hits=False); depth[k + ir] = (loc - O[k + ir]) @ f; tri[k + ir] = it
    depth = depth.reshape(Hh, W); tri = tri.reshape(Hh, W); hit = tri >= 0; n = np.zeros((Hh, W, 3)); n[hit] = m.face_normals[tri[hit]]
    light = -f * 0.55 + u * 0.62 - r * 0.42; light /= np.linalg.norm(light); lam = np.clip(n @ light, 0, 1); facing = np.clip(-(n @ f), 0, 1)
    shade = 0.46 + 0.42 * lam + 0.14 * facing; img = np.ones((Hh, W, 3)) * 255.0; img[hit] = np.clip(shade[hit, None] * C[tri[hit]], 0, 255)
    dn = np.where(hit, depth, 1e6); ed = np.zeros((Hh, W), bool); thr = 0.12 + 0.9 / s; part = np.where(hit, C[np.clip(tri, 0, None)].sum(-1), -1)
    for ax in (0, 1):
        a_, b_ = (dn[1:], dn[:-1]) if ax == 0 else (dn[:, 1:], dn[:, :-1]); na, nb = (n[1:], n[:-1]) if ax == 0 else (n[:, 1:], n[:, :-1]); pa, pb = (part[1:], part[:-1]) if ax == 0 else (part[:, 1:], part[:, :-1])
        k = (np.abs(a_ - b_) > thr) | ((na * nb).sum(-1) < 0.90) | (pa != pb)
        if ax == 0: ed[1:] |= k; ed[:-1] |= k
        else: ed[:, 1:] |= k; ed[:, :-1] |= k
    img[ed & hit] = img[ed & hit] * 0.30
    im = Image.fromarray(img.astype(np.uint8)).resize((W // SS, Hh // SS), Image.LANCZOS)
    def to_px(p):
        q = np.asarray(p, float) - c; return ((q @ r) - x0) * ppm + pad, (y1 - (q @ u)) * ppm + pad
    return im, to_px
if __name__ == "__main__":
    out = sys.argv[1]; az, el, ppm = (float(x) for x in (sys.argv[2:5] + ["35", "28", "7"][len(sys.argv) - 2:])[:3]) if len(sys.argv) > 2 else (35.0, 28.0, 7.0)
    im, _ = asm_image(load_parts(), az, el, ppm); im.save(out); print(out, im.size)

def resting_plane(P, up=(0, 0, 1.0)):
    """the plane a table makes when the camera is laid on the side that faces 'up': the face of its hull under its centre of gravity.  Returns (unit normal, offset, clearance of the shutter)"""
    V = np.vstack([m.vertices for m in P.values()]); hull = trimesh.convex.convex_hull(V); N = hull.face_normals; up = np.asarray(up, float)
    cg = np.average([P[n].center_mass for n in ("body", "back", "front")], axis=0, weights=[P[n].volume for n in ("body", "back", "front")]); best = None
    for fi in np.where(N @ up > 0.6)[0]:
        t = hull.triangles[fi]; n = N[fi]; q = cg + n * ((t[0] - cg) @ n)
        if min(np.cross(t[1] - t[0], q - t[0]) @ n, np.cross(t[2] - t[1], q - t[1]) @ n, np.cross(t[0] - t[2], q - t[2]) @ n) >= -1e-6 and (best is None or n @ up > N[best] @ up): best = fi
    n = N[best]; off = hull.triangles[best][0] @ n; return n, off, off - (P["blade"].vertices @ n).max()
def guard_sheet(out, title="9. The camera with its guard", sub="", ppm=7.0):
    from PIL import ImageDraw, ImageFont
    F = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"; font = lambda s, b=False: ImageFont.truetype(F % ("Bold" if b else "Regular"), s); INK, GREY, ACC = (26, 28, 32), (95, 100, 108), (200, 85, 26)
    P = load_parts(); a, _ = asm_image(P, 32, 28, ppm); b, _ = asm_image(P, 152, 40, ppm)
    box = ([-13, 12, 24], [45, 31, 42]); c, _ = asm_image(P, 180, 48, ppm * 2.2, box=box)
    n, off, clear = resting_plane(P); clear = min(clear, resting_plane(load_parts(phi=-THETA))[2]); z = np.array([0, 0, -1.0]); v = np.cross(n, z); s_, c_ = np.linalg.norm(v), n @ z; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); R = np.eye(3) + K + K @ K * ((1 - c_) / s_ ** 2)                    # clear: the rocker at rest on either side
    Q = {}
    for k, m in P.items(): t = m.copy(); t.vertices = t.vertices @ R.T; Q[k] = t
    d, to_px = asm_image(Q, 90, 0, ppm * 1.25, pad=26); zt = min(q.vertices[:, 2].min() for q in Q.values()); dd = ImageDraw.Draw(d); y_t = to_px([0, 0, zt])[1]
    dd.line([(0, y_t + 1), (d.width, y_t + 1)], fill=INK, width=3)
    for x in range(-20, d.width, 16): dd.line([(x, y_t + 14), (x + 12, y_t + 2)], fill=GREY, width=1)
    M, G = 40, 28; caps = ["From the front: an ear at each end of the rocker, a low wall between them.", "From behind: the rocker lies between the ears.  It is open to the back and above: the finger comes in from there.",
                           "Close up, from behind and above.  The raised side is 1.8 mm lower than the ears.", "Laid on its top, seen from the end: it rests on the guard and on both knobs.  The rocker is %.1f mm clear of the table." % clear]
    w1 = a.width + G + b.width; w2 = c.width + G + d.width; W = max(w1, w2) + 2 * M; h1 = max(a.height, b.height); h2 = max(c.height, d.height); Hh = 120 + h1 + 62 + h2 + 62 + 46
    S = Image.new("RGB", (W, Hh), "white"); dr = ImageDraw.Draw(S); dr.text((M, 26), title, font=font(34, True), fill=INK); dr.text((M, 72), sub, font=font(17), fill=GREY)
    def put(im, x, y, cap, wmax):
        S.paste(im, (x, y)); words = cap.split(" "); line = ""; yy = y + im.height + 4
        for w_ in words:
            t = (line + " " + w_).strip()
            if dr.textlength(t, font=font(18)) > wmax and line: dr.text((x, yy), line, font=font(18), fill=INK); yy += 24; line = w_
            else: line = t
        dr.text((x, yy), line, font=font(18), fill=INK)
    put(a, M, 112, caps[0], a.width); put(b, M + a.width + G, 112, caps[1], b.width); y2 = 112 + h1 + 66; put(c, M, y2, caps[2], c.width); put(d, M + c.width + G, y2, caps[3], d.width)
    S.save(out, optimize=True); return S.size, clear

def eye_image(P, eye, fwd, fov=90.0, W=900, Hh=600, SS=2, sky=(214, 226, 240), ground=(196, 190, 176)):
    """what an eye at `eye` sees, looking along `fwd` (perspective, rectilinear).  Returns the picture and a function that puts a DIRECTION (a far-away point) on it"""
    V = np.vstack([m.vertices for m in P.values()]); F = []; C = []; o = 0
    for n, m in P.items(): F.append(m.faces + o); C += [COL[n]] * len(m.faces); o += len(m.vertices)
    m = trimesh.Trimesh(V, np.vstack(F), process=False); C = np.array(C, float); rt = Fast(m)
    eye = np.asarray(eye, float); f = np.asarray(fwd, float); f /= np.linalg.norm(f); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f); t = np.tan(np.radians(fov) / 2); w, h = W * SS, Hh * SS
    jx, jy = np.meshgrid(np.arange(w), np.arange(h)); X = ((jx + 0.5) / w * 2 - 1) * t; Y = (1 - (jy + 0.5) / h * 2) * t * h / w
    D = f + X[..., None] * r + Y[..., None] * u; D /= np.linalg.norm(D, axis=-1)[..., None]; D = D.reshape(-1, 3); O = np.broadcast_to(eye, D.shape)
    tri = np.full(len(D), -1); depth = np.full(len(D), np.inf)
    for k in range(0, len(D), 1500000):
        loc, ir, it = rt.intersects_location(O[k:k + 1500000], D[k:k + 1500000], multiple_hits=False); tri[k + ir] = it; depth[k + ir] = np.linalg.norm(loc - eye, axis=1)
    tri = tri.reshape(h, w); depth = depth.reshape(h, w); hit = tri >= 0; n = np.zeros((h, w, 3)); n[hit] = m.face_normals[tri[hit]]; Dv = D.reshape(h, w, 3)
    light = np.array([0.35, -0.45, 0.82]); light /= np.linalg.norm(light); lam = np.clip(n @ light, 0, 1); facing = np.clip(-(n * Dv).sum(-1), 0, 1); shade = 0.42 + 0.44 * lam + 0.16 * facing
    img = np.where((Dv[..., 2] > 0)[..., None], np.array(sky, float), np.array(ground, float)) * np.ones((h, w, 3)); img[hit] = np.clip(shade[hit, None] * C[tri[hit]], 0, 255)
    dn = np.where(hit, depth, 1e6); ed = np.zeros((h, w), bool); part = np.where(hit, C[np.clip(tri, 0, None)].sum(-1), -1)
    for ax in (0, 1):
        a_, b_ = (dn[1:], dn[:-1]) if ax == 0 else (dn[:, 1:], dn[:, :-1]); na, nb = (n[1:], n[:-1]) if ax == 0 else (n[:, 1:], n[:, :-1]); pa, pb = (part[1:], part[:-1]) if ax == 0 else (part[:, 1:], part[:, :-1])
        k = (np.abs(a_ - b_) > 0.02 * np.minimum(a_, b_) + 0.15) | ((na * nb).sum(-1) < 0.90) | (pa != pb)
        if ax == 0: ed[1:] |= k; ed[:-1] |= k
        else: ed[:, 1:] |= k; ed[:, :-1] |= k
    img[ed & hit] = img[ed & hit] * 0.30
    im = Image.fromarray(img.astype(np.uint8)).resize((W, Hh), Image.LANCZOS)
    def to_px(v, point=False):
        v = np.asarray(v, float) - (eye if point else 0); z = v @ f
        if z <= 1e-6: return None
        return ((v @ r) / z / t + 1) / 2 * W, (1 - (v @ u) / z / (t * Hh / W)) / 2 * Hh
    return im, to_px
def frame_dirs(ga, gz_over_rf, n=40):
    """the edge of the picture as directions in the world (film curved about the lens: left and right edges ga degrees off the axis, top and bottom at tan = gz / rf at every angle)"""
    a = np.radians(np.linspace(-ga, ga, n)); top = [(np.sin(q), np.cos(q), gz_over_rf) for q in a]; bot = [(np.sin(q), np.cos(q), -gz_over_rf) for q in a[::-1]]
    return top + bot + [top[0]]

def _fonts():
    from PIL import ImageFont
    F = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"; return lambda s, b=False: ImageFont.truetype(F % ("Bold" if b else "Regular"), s)
def _dash(d, a, b, fill, width=3, on=12, off=8):
    a = np.asarray(a, float); b = np.asarray(b, float); L = np.linalg.norm(b - a); n = max(int(L // (on + off)), 1); u = (b - a) / max(L, 1e-9)
    for k in range(n + 1):
        p = a + u * k * (on + off); q = a + u * min(k * (on + off) + on, L)
        if k * (on + off) < L: d.line([tuple(p), tuple(q)], fill=fill, width=width)
def _put(S, dr, font, im, x, y, cap, wmax, INK):
    S.paste(im, (x, y)); line = ""; yy = y + im.height + 6
    for w_ in cap.split(" "):
        t = (line + " " + w_).strip()
        if dr.textlength(t, font=font(18)) > wmax and line: dr.text((x, yy), line, font=font(18), fill=INK); yy += 24; line = w_
        else: line = t
    dr.text((x, yy), line, font=font(18), fill=INK); return yy + 24
def sights_sheet(out, title="9. The camera and its sights", sub="", ppm=6.4):
    from PIL import ImageDraw
    sys.path.insert(0, "tools"); from scadr import values
    V = values(["GATE_A", "GATE_Z", "RF", "SG_X", "SG_W0", "SG_Y0", "SG_Y1", "SG_H", "H", "Y_RIM", "Y_FRONT", "BXL", "BXR", "SE_W0", "SE_Y0", "SE_Y1", "GATE_V"]); font = _fonts(); INK, GREY, ACC, RED = (26, 28, 32), (95, 100, 108), (200, 85, 26), (200, 40, 40)
    P = load_parts(); ta = np.tan(np.radians(V["GATE_A"])); tv = np.tan(np.radians(V["GATE_V"])); zt = V["H"] + V["SG_H"]
    # A: from above, the rear toward the viewer
    a, pa = asm_image(P, 180, 88, ppm, pad=14, box=([-V["BXL"] - 20, V["Y_RIM"] - 6, 0], [V["BXR"] + 2, V["SG_Y1"] + 40, zt])); d = ImageDraw.Draw(a)
    for sd, lab in ((-1, "left edge of the picture"), (1, "right edge of the picture")):
        p0 = [V["SG_X"] + sd * (V["SG_W0"] / 2 + ta * (V["SG_Y1"] - V["SG_Y0"])), V["SG_Y1"], zt]; p1 = [p0[0] + sd * ta * 26, p0[1] + 26, zt]; q0, q1 = pa(p0), pa(p1); _dash(d, q0, q1, RED)
        d.text((q1[0] - (d.textlength(lab, font=font(17)) if sd < 0 else 0) + sd * 8, q1[1] - 12), lab, font=font(17), fill=RED)
    q0, q1 = pa([V["SG_X"], V["SG_Y0"] + 4, zt]), pa([V["SG_X"], V["SG_Y1"] + 26, zt]); _dash(d, q0, q1, ACC, 2, 6, 6); d.text((q1[0] - d.textlength("aim", font=font(17)) / 2, q1[1] - 26), "aim", font=font(17), fill=ACC)
    # B: from behind, the eye a little above the top
    eye = [V["SG_X"], -75, V["H"] + 22]; b, pb = eye_image(P, eye, [0, 1, -0.12], 84, 860, 560); d = ImageDraw.Draw(b)
    fr = [pb(v) for v in frame_dirs(V["GATE_A"], V["GATE_Z"] / V["RF"])]; d.line([q for q in fr if q is not None], fill=RED, width=3)
    for sd in (-1, 1):
        p0 = np.array([V["SG_X"] + sd * (V["SG_W0"] / 2 + ta * (V["SG_Y1"] - V["SG_Y0"])), V["SG_Y1"], zt]); _dash(d, pb(p0, True), pb([sd * np.sin(np.radians(V["GATE_A"])), np.cos(np.radians(V["GATE_A"])), 0.0]), RED, 2, 8, 7)
    t_ = "red frame: what the film sees"; d.text(((b.width - d.textlength(t_, font=font(17))) / 2, 92), t_, font=font(17), fill=RED)
    # C: from the end
    c, pc = asm_image(P, 270, 0, ppm * 1.25, pad=60); d = ImageDraw.Draw(c); xe = -V["BXL"]
    for sd, lab in ((1, "top edge of the picture"), (-1, "bottom edge")):
        p0 = [xe, V["SE_Y1"], sd * (V["SE_W0"] / 2 + tv * (V["SE_Y1"] - V["SE_Y0"]))]; p1 = [xe, p0[1] + 22, p0[2] + sd * tv * 22]; q0, q1 = pc(p0), pc(p1); _dash(d, q0, q1, RED)
        d.text((max(q1[0] - 20, 4), q1[1] + (-26 if sd > 0 else 6)), lab, font=font(17), fill=RED)
    # D: three-quarter view from behind
    e, _ = asm_image(P, 152, 40, ppm)
    M, G = 40, 30; caps = ["From above.  The two rails on the top form a V.  Their outer sides run the way the left and right edges of the picture run: what lies between them, carried on, is in the picture.  The blade at the front, seen in the notch at the rear, is the middle of the picture, like the sights on a gun.",
                           "From behind, the eye 2 cm above the top and 7 cm behind the camera.  Each rail points at its edge of the picture, wherever the eye is.  The lower part of the picture lies behind the camera from here: the rails are edges to sight along, not a frame to look through.",
                           "From the end.  The wedge sunk into each end shows the top and bottom edges the same way: for a camera on a table or a stand.",
                           "The whole camera from behind.  The line of sight starts 31 mm above the lens and 2 mm to its left: the rocker's end, when it is down, comes to 1 mm from the lens's line.  The blade is 0.2 mm lower than the rails, so the line dips and meets the lens's own line at 2.8 m: the point aimed at is within 1.5 % of the picture's height of its middle from 1.4 m to any distance."]
    wl = max(a.width, c.width + 0); W = M + max(a.width, e.width) + G + max(b.width, c.width) + M; col2 = M + max(a.width, e.width) + G
    h1 = max(a.height, b.height); h2 = max(e.height, c.height); Hh = 120 + h1 + 110 + h2 + 100
    S = Image.new("RGB", (W, Hh), "white"); dr = ImageDraw.Draw(S); dr.text((M, 26), title, font=font(34, True), fill=INK); dr.text((M, 72), sub, font=font(17), fill=GREY)
    _put(S, dr, font, a, M, 112, caps[0], a.width, INK); _put(S, dr, font, b, col2, 112, caps[1], b.width, INK); y2 = 112 + h1 + 110
    _put(S, dr, font, e, M, y2, caps[3], e.width, INK); _put(S, dr, font, c, col2, y2, caps[2], max(c.width, 520), INK)
    S.save(out, optimize=True); return S.size
def plate_sheet(out, title="11. Front plate: on and off in two moves", sub="", ppm=7.0):
    from PIL import ImageDraw
    sys.path.insert(0, "tools"); from scadr import values
    V = values(["SLIDE", "XA", "XUP", "FX0", "FX1", "FZ0", "FZ1", "Y_FRONT", "Y_CVF", "FOOT_W", "FOOT_L", "FOOT_D", "FOOT_EDGE"]); font = _fonts(); INK, GREY, ACC = (26, 28, 32), (95, 100, 108), (200, 85, 26)
    try: W_ = json.load(open("build/platewindow.json"))["now"]; wt, wd = W_["typical: walls +0.10"], W_["as drawn"]
    except Exception: wt = wd = None
    P0 = load_parts(parts=("body", "back", "front", "blade", "wheel", "roller", "knob", "spool", "lens")); ims = []
    zu = (wd["band"][0] + wd["band"][1]) / 2 if wd else V["SLIDE"]; XE = (wd["set_on"]["side"][0] + wd["set_on"]["side"][1]) / 2 if wd else V["XA"] - 0.6
    box = ([V["FX0"] - 16, 0, V["FZ0"] - 6], [V["FX1"] + 16, V["Y_CVF"] + 2, V["FZ1"] + 16])
    def moved(dx, dy, dz):
        Q = {}
        for k, m in P0.items():
            t = m.copy()
            if k in ("front", "blade", "wheel", "lens"): t.apply_translation([dx, dy, dz])
            Q[k] = t
        return Q
    catch = "On a typical printer the feet catch anywhere within %.1f mm sideways and %.1f mm up and down of the right place." % (wt["catches"]["wide"], wt["catches"]["tall"]) if wt else ""
    steps = [((-XE, 7.0, zu), "1  Lay the plate on the front about %.0f mm above its place and %.0f mm to the right of it (seen from the front), press lightly and move it about: its four feet drop into the tops of their pockets.  %s" % (zu, XE, catch), [], True),
             ((-XE, 0, zu), "2  Slide it to the left until it stops.", [((1, 0, 0), 16)], False),
             ((0, 0, zu), "3  Slide it down until it clicks.", [((0, 0, -1), 18)], False),
             ((0, 0, 0), "Home: its top edge is level with the camera's top.  To take it off: push it up, past the click, until it stops; slide it to the right until it stops; lift it away.", [], False)]
    for (dx, dy, dz), cap, arrows, labels in steps:
        im, px = asm_image(moved(dx, dy, dz), 24, 16, ppm, pad=14, box=box); d = ImageDraw.Draw(im); c0 = np.array([dx + (V["FX0"] + V["FX1"]) / 2 - 22, V["Y_CVF"] + dy + 0.5, dz + (V["FZ0"] + V["FZ1"]) / 2 + 14])
        for v, L in arrows:
            v = np.array(v, float); a0 = px(c0 - v * L * 0.5); a1 = px(c0 + v * L * 0.5); d.line([a0, a1], fill=INK, width=7)
            u = np.array(a1) - np.array(a0); u /= np.linalg.norm(u); n = np.array([-u[1], u[0]]); tip = np.array(a1) + u * 6; d.polygon([tuple(tip), tuple(tip - u * 26 + n * 13), tuple(tip - u * 26 - n * 13)], fill=INK)
        if labels:
            fx = V["FX1"] - V["FOOT_EDGE"] - V["FOOT_W"]; fz = V["FZ1"] - 11.5
            for text, pt, off in (("foot", [fx + V["FOOT_W"] + 1.0 + dx, V["Y_FRONT"] + dy - 2.0, fz + 1.8 + dz], (-96, -34)), ("its pocket", [fx + V["FOOT_W"] + 2.2, V["Y_FRONT"], fz + 6.2], (-150, 26))):
                q = px(pt); t0 = (q[0] + off[0], q[1] + off[1]); d.line([q, (t0[0] + d.textlength(text, font=font(18, True)) + 4, t0[1] + 12)], fill=INK, width=2); d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=INK)
                d.rectangle([t0[0] - 4, t0[1] - 2, t0[0] + d.textlength(text, font=font(18, True)) + 4, t0[1] + 24], fill="white"); d.text(t0, text, font=font(18, True), fill=INK)
        ims.append((im, cap))
    M, G = 40, 26; w = ims[0][0].width; W = 2 * M + 2 * w + G; h = ims[0][0].height; Hh = 120 + 2 * (h + 112) + 20
    S = Image.new("RGB", (W, Hh), "white"); dr = ImageDraw.Draw(S); dr.text((M, 26), title, font=font(34, True), fill=INK); dr.text((M, 72), sub, font=font(17), fill=GREY)
    for k, (im, cap) in enumerate(ims): _put(S, dr, font, im, M + (k % 2) * (w + G), 112 + (k // 2) * (h + 112), cap, w, INK)
    S.save(out, optimize=True); return S.size

def viewport_sheet(out, title="9. The sight: a groove, two edges and a point", sub="", ppm=6.4):
    from PIL import ImageDraw
    sys.path.insert(0, "tools"); from scadr import values
    V = values(["H", "BXL", "BXR", "Y_RIM", "Y_CVF", "PAD_UP", "PAD_X1", "AIM_R", "SIGHT_DROP"]); font = _fonts(); INK, GREY, RED = (26, 28, 32), (95, 100, 108), (200, 40, 40)
    TH = json.load(open("build/layout.json"))["B"]["THETA"]; P = load_parts(phi=TH); zt = V["H"] + V["PAD_UP"]
    a, pa = asm_image(P, 180, 88, ppm * 1.6, pad=14, box=([-34, V["Y_RIM"] - 8, 0], [40, V["Y_CVF"] + 22, zt])); d = ImageDraw.Draw(a)
    _dash(d, pa([0, V["Y_RIM"] - 6, zt]), pa([0, V["Y_CVF"] + 18, zt]), RED, 2, 8, 6); q = pa([0, V["Y_CVF"] + 18, zt]); d.text((q[0] + 8, q[1]), "the lens's line", font=font(17), fill=RED)
    for text, pt, off in (("top pad of the back: its right edge", [V["PAD_X1"], -4.5, zt], (-330, -6)), ("rocker's end, when this side is down", [V["AIM_R"], 24.7, zt], (40, -40)), ("point on the front plate", [0, V["Y_CVF"] - 1, zt], (-250, -30)), ("engraved line", [0, 10, zt], (60, 10))):
        q = pa(pt); t0 = (q[0] + off[0], q[1] + off[1]); d.line([q, (t0[0] + (d.textlength(text, font=font(17)) if off[0] < 0 else 0), t0[1] + 11)], fill=INK, width=2); d.rectangle([t0[0] - 3, t0[1] - 1, t0[0] + d.textlength(text, font=font(17)) + 3, t0[1] + 22], fill='white'); d.text(t0, text, font=font(17), fill=INK)
    eye = [0, -260, zt + 4]; b, pb = eye_image(P, eye, [0, 1, -0.012], 16, 900, 520); e, _ = asm_image(P, 152, 40, ppm)
    caps = ["From above.  The middle engraved line lies on the lens's line.  The right edge of the back's top pad stands at its left edge, the end of the rocker (when that side is down) at its right edge, and the point on the front plate in the middle at the front.",
            "From the eye, 26 cm behind the camera and just above the top: the point at the front, seen between the pad's edge and the rocker's end.  The point is %.2f mm lower than the pad's top, so the line over both meets the lens's line 2.8 m away." % V["SIGHT_DROP"],
            "The whole camera from behind.  The two outer engraved lines run the way the picture's left and right edges run."]
    M, G = 40, 30; W = M + max(a.width, e.width) + G + b.width + M; Hh = 120 + max(a.height, b.height) + 120 + e.height + 90
    S = Image.new("RGB", (W, Hh), "white"); dr = ImageDraw.Draw(S); dr.text((M, 26), title, font=font(34, True), fill=INK); dr.text((M, 72), sub, font=font(17), fill=GREY)
    _put(S, dr, font, a, M, 112, caps[0], a.width, INK); _put(S, dr, font, b, M + max(a.width, e.width) + G, 112, caps[1], b.width, INK); _put(S, dr, font, e, M, 112 + max(a.height, b.height) + 120, caps[2], e.width, INK)
    S.save(out, optimize=True); return S.size
