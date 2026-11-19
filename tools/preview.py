"""Preview sheets for marking up: every print file as it lies on the bed, drawn shaded with its edges outlined, from four corners, from above and from below.
The two plan views carry a lettered millimetre grid, so a spot can be named ("TOP D3"); the main features carry numbers.
    python3 tools/preview.py [--round N] [part ...]   ->  build/preview/<n>_<part>.png and .json, and named copies in build/preview/round<N>/

The loop: the sheets go out, marks come back, the model changes, the changed parts are drawn again as the next round.
Nothing here keeps a number of its own: before drawing, the tool reads the model's values afresh and exports again any print file that is older than the model.
Each sheet's .json says what every grid square means in the print file's own millimetres, and which model it was drawn from."""
import sys, os, re, json, shutil, hashlib, numpy as np, trimesh
sys.path.insert(0, "tools"); from scadr import values, export
from PIL import Image, ImageDraw, ImageFont
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
OUT = "build/preview"; os.makedirs(OUT, exist_ok=True); SS = 2
F = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"; font = lambda size, bold=False: ImageFont.truetype(F % ("Bold" if bold else "Regular"), size)
COL = dict(body=(176, 182, 194), back=(150, 170, 206), front=(232, 132, 62), blade=(52, 168, 152), wheel=(232, 190, 60), roller=(74, 138, 222), knob=(214, 84, 76), spool=(214, 84, 76))

def frame(az, el):
    """camera looking at the part from azimuth az (degrees round the bed's upright axis, 0 = from the front, -y) and elevation el (90 = straight down)"""
    a, e = np.radians(az), np.radians(el); f = -np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)])          # the way the camera looks
    up = np.array([0, 0, 1.0]) if abs(el) < 89.9 else np.array([np.sin(a), np.cos(a) if abs(a) > 1e-9 else 1.0, 0.0]) * (1 if el > 0 else 1)
    if abs(el) >= 89.9: up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f); return r, u, f

def render(m, az, el, px_per_mm, col, pad=14, flip_x=False):
    """orthographic picture: returns the image, and a function that maps a point of the part to its pixel (or None when it is hidden)"""
    r, u, f = frame(az, el)
    if flip_x: r = -r                                                                                                   # a view from below, mirrored so that it reads like the top view turned over
    V = m.vertices; c = (V.min(0) + V.max(0)) / 2; P = (V - c); xs, ys = P @ r, P @ u; s = px_per_mm * SS
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); W = int(np.ceil((x1 - x0) * s)) + 2 * pad * SS; Hh = int(np.ceil((y1 - y0) * s)) + 2 * pad * SS
    jx, jy = np.meshgrid(np.arange(W), np.arange(Hh)); X = x0 + (jx - pad * SS + 0.5) / s; Y = y1 - (jy - pad * SS + 0.5) / s; far = np.abs(P @ f).max() + 10
    O = c + X[..., None] * r + Y[..., None] * u - far * f; O = O.reshape(-1, 3); D = np.broadcast_to(f, O.shape); rt = Fast(m)
    depth = np.full(len(O), np.inf); tri = np.full(len(O), -1)
    for k in range(0, len(O), 1500000):
        loc, ir, it = rt.intersects_location(O[k:k + 1500000], D[k:k + 1500000], multiple_hits=False)
        depth[k + ir] = (loc - O[k + ir]) @ f; tri[k + ir] = it
    depth = depth.reshape(Hh, W); tri = tri.reshape(Hh, W); hit = tri >= 0; n = np.zeros((Hh, W, 3)); n[hit] = m.face_normals[tri[hit]]
    light = -f * 0.55 + u * 0.62 - r * 0.42; light /= np.linalg.norm(light); lam = np.clip((n @ light), 0, 1); facing = np.clip(-(n @ f), 0, 1)
    zrel = np.zeros((Hh, W)); d = depth[hit]; zrel[hit] = 1 - (d - d.min()) / max(d.max() - d.min(), 1e-6)                    # nearer the eye = lighter: it tells levels apart where every face looks the same way
    shade = 0.42 + 0.40 * lam + 0.10 * facing + 0.20 * zrel; img = np.ones((Hh, W, 3)) * 255.0; img[hit] = np.clip(shade[hit, None] * np.array(col), 0, 255)
    # outlines: where the depth jumps, where the surface turns, and round the silhouette
    dn = np.where(hit, depth, 1e6); e = np.zeros((Hh, W), bool); thr = 0.12 + 0.9 / s
    for ax in (0, 1):
        a_, b_ = (dn[1:], dn[:-1]) if ax == 0 else (dn[:, 1:], dn[:, :-1]); na, nb = (n[1:], n[:-1]) if ax == 0 else (n[:, 1:], n[:, :-1])
        k = (np.abs(a_ - b_) > thr) | ((na * nb).sum(-1) < 0.90)
        if ax == 0: e[1:] |= k; e[:-1] |= k
        else: e[:, 1:] |= k; e[:, :-1] |= k
    sil = np.zeros((Hh, W), bool); sil[1:] |= hit[1:] != hit[:-1]; sil[:, 1:] |= hit[:, 1:] != hit[:, :-1]
    img[e & hit] = img[e & hit] * 0.28; img[sil] = (30, 32, 38)
    im = Image.fromarray(img.astype(np.uint8)).resize((W // SS, Hh // SS), Image.LANCZOS)
    def to_px(p, hidden_ok=False):
        q = np.asarray(p, float) - c; x, y, z = q @ r, q @ u, q @ f; i, j = int((x - x0) * s + pad * SS), int((y1 - y) * s + pad * SS)
        if not hidden_ok and 0 <= i < W and 0 <= j < Hh:
            w_ = dn[max(j - 2, 0):j + 3, max(i - 2, 0):i + 3]
            if w_.size and (z + far) > w_.max() + 0.6: return None                                                       # something lies in front of it
        return (x - x0) * px_per_mm + pad, (y1 - y) * px_per_mm + pad
    return im, to_px, dict(x0=x0, y1=y1, c=c, r=r, u=u)


# ------------------------------------------------------------------ the sheets
SCAD = "scad/one135.scad"; NAMES = ["FORK_R", "GD_Z", "GD_WZ", "GD_HW", "LF_X0", "LF_X1", "LF_ZH", "TAKE_HEAD", "WIND_HEAD", "COLLAR_R", "ZR_OUT", "A0", "A_AX", "A_HI", "A_LO", "CASS", "COLLAR_Z", "CORE_R", "DB_A", "DIAL_Z", "DOOR_T", "DOT_R", "FEET", "FIN_HALF", "FIN_L", "FIN_W", "FOOT_L", "FOOT_W", "LAT_XI", "LAT_XO", "LAT_ZF", "LAT_ZR", "Y_CVF", "NOSE_TOP", "SLIDE", "FORK_Z0", "FX0", "FX1", "FZ0", "FZ1", "F_T", "F_X0", "F_X1", "F_Z1", "GUIDE", "H", "HANDLE_A0", "HUB_R", "HUB_Z", "HW_FIN", "HW_SLOT", "H_RHO", "JRN_R", "KN_CZ", "KN_PZ", "LAB_R", "LAT_X0", "LAT_X1", "LAT_Z0", "LAT_Z1", "LEDGE_Z", "LENS_D", "NUB_X0", "NUB_X1", "PAD_X0", "PAD_X1", "P_S", "RAIL_IN", "RB_FLOOR", "RB_Z", "RCH_C", "RCH_S", "RK_L", "ROLLER", "RWB", "RWW", "R_G", "R_HOLE", "R_OUT", "R_PORT", "R_ROLL", "SPAN", "SPOOL", "SP_F", "THETA_S", "TOOTH", "WD_A0", "WHEEL_C", "WHEEL_R", "WH_Z", "WPOS", "XJ_L", "XJ_R", "Y_CVF", "Y_FRONT", "Y_RIM", "Y_SC1", "Y_WH0", "ZC0", "ZC1", "ZR_IN", "ZR_OUT", "ZS"]
def fresh(path, *than): return os.path.exists(path) and os.path.getmtime(path) >= max(os.path.getmtime(q) for q in than)
if not fresh(OUT + "/_values.json", SCAD): json.dump(values(NAMES), open(OUT + "/_values.json", "w"), indent=1)                 # the model has changed since the values were read
V = json.load(open(OUT + "/_values.json"))
from booklet import NAME, MODEL
ARGS = sys.argv[1:]; ROUND = int(open(OUT + "/_round.txt").read()) if os.path.exists(OUT + "/_round.txt") else 1
if "--round" in ARGS: k_ = ARGS.index("--round"); ROUND = int(ARGS[k_ + 1]); del ARGS[k_:k_ + 2]; open(OUT + "/_round.txt", "w").write(str(ROUND))
SHA = hashlib.sha1(open(SCAD, "rb").read()).hexdigest()[:10]; RDIR = f"{OUT}/round{ROUND}"; os.makedirs(RDIR, exist_ok=True)
pol = lambda c, r, a: (c[0] + r * np.cos(np.radians(a)), c[1] + r * np.sin(np.radians(a)))
INK, GREY, RULE, ACC = (26, 28, 32), (95, 100, 108), (214, 218, 224), (200, 85, 26)

def panel(m, title, az, el, ppm, col, flip=False, grid=0):
    im, to_px, meta = render(m, az, el, ppm, col, flip_x=flip); return dict(title=title, im=im, to_px=to_px, meta=meta, grid=grid, ppm=ppm, labels=[], az=az, el=el, flip=flip)

def draw_grid(P, m, gm=30):
    """a lettered grid over a plan or side view: letters across, numbers down; returns the picture with a margin for the names, and what each square means"""
    im = P["im"]; cell = P["grid"]; r, u, c = P["meta"]["r"], P["meta"]["u"], P["meta"]["c"]; Q = m.vertices - c; xs, ys = Q @ r, Q @ u
    i0, i1 = int(np.floor(xs.min() / cell)), int(np.ceil(xs.max() / cell)); j0, j1 = int(np.floor(ys.min() / cell)), int(np.ceil(ys.max() / cell))
    X = lambda x: (x - P["meta"]["x0"]) * P["ppm"] + 14; Y = lambda y: (P["meta"]["y1"] - y) * P["ppm"] + 14
    x_lo, x_hi, y_lo, y_hi = X(i0 * cell), X(i1 * cell), Y(j1 * cell), Y(j0 * cell); ox, oy = gm + max(0, -int(np.floor(x_lo))), gm + max(0, -int(np.floor(y_lo)))
    W = int(max(im.width, x_hi) + ox + 6); Hh = int(max(im.height, y_hi) + oy + 6); out = Image.new("RGB", (W, Hh), "white"); out.paste(im, (ox, oy)); d = ImageDraw.Draw(out, "RGBA"); f = font(15, True)
    for i in range(i0, i1 + 1): d.line([(ox + X(i * cell), oy + y_lo), (ox + X(i * cell), oy + y_hi)], fill=(20, 30, 60, 70), width=1)
    for j in range(j0, j1 + 1): d.line([(ox, oy + Y(j * cell)) if False else (ox + x_lo, oy + Y(j * cell)), (ox + x_hi, oy + Y(j * cell))], fill=(20, 30, 60, 70), width=1)
    letters = [chr(65 + k) if k < 26 else "A" + chr(65 + k - 26) for k in range(i1 - i0)]
    for k, L in enumerate(letters): xc = ox + (X((i0 + k) * cell) + X((i0 + k + 1) * cell)) / 2; d.text((xc - d.textlength(L, font=f) / 2, oy + y_lo - 20), L, font=f, fill=GREY + (255,))
    for k in range(j1 - j0): yc = oy + (Y((j1 - k) * cell) + Y((j1 - k - 1) * cell)) / 2; t = str(k + 1); d.text((ox + x_lo - 8 - d.textlength(t, font=f), yc - 9), t, font=f, fill=GREY + (255,))
    P["im"] = out; P["off"] = (ox, oy); P["cells"] = dict(cell_mm=cell, columns=letters, rows=j1 - j0, col0_at=i0 * cell, row1_top_at=j1 * cell, across=[float(x) for x in r], up=[float(x) for x in u], centre=[float(x) for x in c])

def place_labels(P, feats):
    """numbered circles beside the features that can be seen in this view, each with a short leader"""
    im = P["im"]; d = ImageDraw.Draw(im); f = font(17, True); ox, oy = P.get("off", (0, 0)); placed = []; cx, cy = im.width / 2, im.height / 2
    for tag, pt in feats:
        q = P["to_px"](pt[1], True) if isinstance(pt, tuple) and pt[0] == "void" else P["to_px"](pt)
        if q is None: continue
        x, y = q[0] + ox, q[1] + oy; v = np.array([x - cx, y - cy]); v = v / (np.linalg.norm(v) + 1e-6); best = None
        for L in (44, 62, 82, 104):
            for da in (0, 30, -30, 60, -60, 95, -95, 135, -135, 180):
                a = np.radians(da); w = np.array([v[0] * np.cos(a) - v[1] * np.sin(a), v[0] * np.sin(a) + v[1] * np.cos(a)]); lx, ly = x + w[0] * L, y + w[1] * L
                if not (ox + 20 < lx < im.width - 18 and oy + (34 if oy else 18) < ly < im.height - 18): continue
                if all(np.hypot(lx - px, ly - py) > 38 for px, py in placed): best = (lx, ly); break
            if best: break
        if not best: best = (min(max(x + 30, 18), im.width - 18), min(max(y - 30, 18), im.height - 18))
        lx, ly = best; placed.append(best); d.line([(x, y), (lx, ly)], fill=INK, width=2); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=INK)
        d.ellipse([lx - 16, ly - 16, lx + 16, ly + 16], fill="white", outline=INK, width=2); d.text((lx - d.textlength(tag, font=f) / 2, ly - 10), tag, font=f, fill=INK); P["labels"].append(tag)

def snapper(m):
    rt = Fast(m); zt, zb = m.bounds[1][2] + 5, m.bounds[0][2] - 5
    def snap(x, y, below=False):
        loc, _, _ = rt.intersects_location([[x, y, zb if below else zt]], [[0, 0, 1.0 if below else -1.0]], multiple_hits=False)
        return loc[0] if len(loc) else np.array([x, y, m.bounds[0][2] if below else m.bounds[1][2]])
    return snap

def sheet(key, spec):
    stl = f"build/print/one135_{key}.stl"
    if not fresh(stl, SCAD, "scad/layout.scad"): export(SCAD, stl, dict(PART="p_" + key)); print(f"        {key}: print file exported again, the model is newer")
    m = trimesh.load(stl, process=True); col = COL[key]; ext = m.extents; snap = snapper(m); tall = spec["kind"] == "tall"; el = spec.get("el", 26 if tall else 38)
    # one scale for every view of the part
    def span(az, el_):
        r, u, f = frame(az, el_); Q = m.vertices - (m.bounds[0] + m.bounds[1]) / 2; return np.ptp(Q @ r), np.ptp(Q @ u)
    w1, h1 = span(spec.get("az", -35), el); ppm = min(1180 / max(w1, ext[0]), (1120 if tall else 880) / max(h1, ext[1] if not tall else ext[2]), 42.0); ppm = float(np.floor(ppm * 2) / 2); az = spec.get("az", -35)
    P1 = panel(m, "View 1", az, el, ppm, col); P2 = panel(m, "View 2: a quarter turn round" if tall else "View 2: from the opposite corner", az + (90 if tall else 180), el, ppm, col)
    PT = panel(m, f"TOP: straight down. Squares are {spec['cell']} mm", 0, 90, ppm, col, grid=spec["cell"]); PU = panel(m, f"UNDER: the face on the bed, turned over. Squares are {spec['cell']} mm", 0, -90, ppm, col, grid=spec["cell"])
    feats = []
    for tag, name, kind, data in spec["features"]:
        if kind == "pt": feats.append((tag, snap(*data), "top"))
        elif kind == "pt3": feats.append((tag, np.array(data, float), "top"))
        elif kind == "void": feats.append((tag, ("void", np.array(data, float)), "top"))
        elif kind == "void1": feats.append((tag, ("void", np.array(data, float)), "top1"))                      # a hollow that only the first view looks into
        elif kind == "under": feats.append((tag, snap(*data, below=True), "under"))
        elif kind == "ring": feats.append((tag, data, "ring"))
    def pts(P, which):
        out = []
        for tag, d_, k in feats:
            if k == "ring":
                if which == "under": continue
                cx_, cy_, rad, z = d_[:4]; a = P["az"] - 90 + 38 * (1 if int(tag) % 2 else -1); ph = d_[5] if len(d_) > 5 else 0.0; a = np.radians(round((a - ph) / d_[4]) * d_[4] + ph if len(d_) > 4 else a); out.append((tag, np.array([cx_ + rad * np.cos(a), cy_ + rad * np.sin(a), z])))      # the point of the ring that faces this camera, a little to one side
            elif k == which or (which == "top" and k == "top") or (k == "top1" and which == "top" and P is P1): out.append((tag, d_))
        return out
    for P in (PT, PU): draw_grid(P, m)
    place_labels(P1, pts(P1, "top")); place_labels(P2, pts(P2, "top")); place_labels(PU, [(t, d_) for t, d_, k in feats if k == "under"])
    panels = [P1, P2, PT, PU]
    if tall:
        PS_ = panel(m, f"SIDE: from the front. Squares are {spec['cell']} mm", 0, 0, ppm, col, grid=spec["cell"]); draw_grid(PS_, m); panels = [P1, P2, PS_, PT, PU]
    # ---- lay the panels out
    M, CAP, GAP = 44, 30, 38; f_t, f_c, f_l = font(34, True), font(17), font(19)
    if tall: cols = [[P1], [P2], [panels[2]], [PT, PU]]
    else: cols = [[P1, P2], [PT, PU]]
    cw = [max(p_["im"].width for p_ in c_) for c_ in cols]; ch = [sum(p_["im"].height + CAP for p_ in c_) + GAP * (len(c_) - 1) for c_ in cols]
    legend = [(t, n) for t, n, k, d_ in spec["features"]]; ncol = 3 if len(legend) > 8 else 2; rows = (len(legend) + ncol - 1) // ncol; LH = 28; leg_h = rows * LH + 16
    capw = lambda p_: ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(p_["title"], font=font(17, True)); cw = [int(max(w_, max(capw(p_) for p_ in c_) + 8)) for c_, w_ in zip(cols, cw)]     # a column is at least as wide as its captions
    W = max(sum(cw) + GAP * (len(cols) - 1) + 2 * M, 1500); HEAD = 112; Hh = HEAD + max(ch) + 26 + leg_h + 58
    S = Image.new("RGB", (W, Hh), "white"); d = ImageDraw.Draw(S)
    d.text((M, 26), f"{spec['n']}. {spec['title']}", font=f_t, fill=INK)
    d.text((M, 72), f"As it lies on the print bed, {spec['down']}.  {ext[0]:.1f} x {ext[1]:.1f} mm, {ext[2]:.1f} mm tall.  Every view is at one scale ({ppm:g} pixels to the millimetre).", font=f_c, fill=GREY)
    x = M
    for c_, w_ in zip(cols, cw):
        y = HEAD
        for p_ in c_:
            d.text((x, y), p_["title"], font=font(17, True), fill=ACC); S.paste(p_["im"], (x + (w_ - p_["im"].width) // 2 if len(c_) == 1 and False else x, y + CAP)); p_["at"] = (x, y + CAP); y += p_["im"].height + CAP + GAP
        x += w_ + GAP
    y0 = HEAD + max(ch) + 20; d.line([(M, y0), (W - M, y0)], fill=RULE, width=1); colw = (W - 2 * M) / ncol
    for k, (t, n) in enumerate(legend):
        lx = M + (k // rows) * colw; ly = y0 + 14 + (k % rows) * LH; d.ellipse([lx, ly, lx + 24, ly + 24], outline=INK, width=2); d.text((lx + 12 - d.textlength(t, font=font(15, True)) / 2, ly + 3), t, font=font(15, True), fill=INK); d.text((lx + 34, ly + 1), n, font=f_l, fill=INK)
    d.text((M, Hh - 40), f"{NAME} ({MODEL}), preview round {ROUND}.  Draw on this picture, or name a spot: \"{spec['title'].split(' (')[0]}, TOP D3\" or \"{spec['title'].split(' (')[0]} 4\".", font=f_c, fill=GREY)
    S.save(f"{OUT}/{spec['n']}_{key}.png", optimize=True); named = f"{RDIR}/{NAME.replace(' ', '-')}_round{ROUND}_{spec['n']}_{spec['title'].lower().replace(' ', '_')}"
    json.dump(dict(part=key, title=spec["title"], round=ROUND, model=MODEL, model_sha1=SHA, pixels_per_mm=ppm, size=[S.width, S.height], legend=legend,
                   panels=[dict(title=p_["title"], at=list(p_["at"]), size=list(p_["im"].size), az=p_["az"], el=p_["el"], mirrored=p_["flip"], labels=p_["labels"], grid=p_.get("cells")) for p_ in panels]), open(f"{OUT}/{spec['n']}_{key}.json", "w"), indent=1)
    shutil.copy(f"{OUT}/{spec['n']}_{key}.png", named + ".png"); shutil.copy(f"{OUT}/{spec['n']}_{key}.json", named + ".json"); shutil.copy(SCAD, f"{RDIR}/one135_round{ROUND}.scad")
    return S.size

PS_, WC = V.get("P_S", [16, 23.6]), V.get("WHEEL_C", [-8.13, -8.13]); RO, CA, SP = V.get("ROLLER", [27.57, 5.37]), V.get("CASS", [-44.95, 10.02]), V.get("SPOOL", [45.5, 8.7]); FT = V.get("FEET", [[-27.8, -24.6]] * 4)
# features: (number, name, kind, where).  "pt": a spot seen from above, in the print file's own x and y (the tool finds the surface under it); "under": the same from below;
# "pt3": a point given outright; "ring": (axis x, axis y, radius, height) on a round part: the tool takes the point of the ring that faces each camera.
SPECS = {
 "front": dict(n=1, title="Front plate", down="front face down: you are looking at its inside", kind="flat", cell=5, features=[
    ("1", "peg the shutter turns on", "pt", tuple(PS_)), ("2", "pocket the shutter swings in", "pt", pol(PS_, 20, V.get("A0", 236))), ("3", "V notches for the shutter's click, cut into the pocket's edge", "pt", pol(PS_, V.get("RWB", 36.4) - 0.9, V.get("DB_A", 262) + 6)),
    ("4", "stop: a step in the pocket's edge (one each side)", "pt", pol(PS_, 23.5, V.get("A_HI", 277.6) + 0.45)), ("5", "peg the aperture wheel turns on", "pt", tuple(WC)), ("6", "pocket for the aperture wheel", "pt", pol(WC, 11, 300)),
    ("7", "slot the aperture handle comes through", "pt", pol(WC, 12 + 3.5 + 0.9, 186)), ("8", "light port", "pt", (3.9, 0.0)), ("9", "foot (four): a hook pointing down, a lip on one side", "pt", (FT[2][0] + 2.8, FT[2][1] + 1.6)), ("10", "latch leaf, eight layers thick: it points up from its root", "pt", ((V.get("LF_X0", 27.0) + V.get("LF_X1", 31.6)) / 2, -6.0)), ("11", "latch post with a round end: drops behind a bump in the body", "void", ((V.get("LF_X0", 27.0) + V.get("LF_X1", 31.6)) / 2, V.get("LF_ZH", -12.2), V.get("Y_CVF", 30.47) - V.get("Y_FRONT", 25.47) + 1.0)),
    ("12", "side lip of a foot: holds the plate on while it is slid up", "pt", (FT[1][0] + V.get("FOOT_W", 6.4) + 1.7, FT[1][1] + 1.8)),
    ("a", "pocket the lens presses into (three ribs)", "under", (5.2, 0.0)), ("b", "three dots: small, middle, large opening", "under", pol(WC, 19.2, V.get("HANDLE_A0", 214) - 25.44))]),
 "blade": dict(n=2, title="Shutter", down="front face down", kind="flat", cell=5, features=[
    ("1", "rocker: press the raised side flat to take a picture; the end of its left side, when down, stands at the edge of the middle aim line", "pt", (9.0, 33.4)), ("2", "arm: comes up through the top of the camera", "pt", (PS_[0], 29.3)), ("3", "hub: its hole is 1 mm wider than the peg, off-centre", "pt", (PS_[0] + 3.9, PS_[1])),
    ("4", "root: twice as thick as the blade", "pt", pol(PS_, 9, V.get("A0", 236))), ("5", "blade, 1 mm thick: it covers the light port", "pt", pol(PS_, 22, V.get("A0", 236) - 9)), ("6", "window: light passes while it crosses the port", "pt", (3.7, 0.0)),
    ("7", "click spring: the blade's own rim", "pt", pol(PS_, V.get("R_OUT", 33.26) + 1.9, 247)), ("8", "tooth: drops into the notches in the plate", "pt", pol(PS_, V.get("R_OUT", 33.26) + 3.3, V.get("DB_A", 261.7)))]),
 "wheel": dict(n=3, title="Aperture wheel", down="back face down", kind="flat", cell=2, features=[
    ("1", "hole for the front plate's peg", "pt", (WC[0] + 3.7, -WC[1])), ("2", "three openings: 2.0, 2.9, 4.0 mm = f/16, f/11, f/8 (sun with ISO 400, 200, 100)", "pt", (-4.28 + 1.9, -2.71 - 0.6)), ("3", "handle with a dished top: slides to three clicks", "pt", (-18.3, 14.1)),
    ("4", "foot of the handle", "pt", (-20.9, 9.6)), ("5", "click spring: the wheel's own rim", "pt", (-24.9, 4.1)), ("6", "tooth: drops into the notches in the plate", "pt", (-26.5, 14.5))]),
 "body": dict(n=4, title="Body", down="front face down: you are looking into it from the back", kind="flat", cell=5, el=52, features=[
    ("1", "chamber for the film cassette", "void", (CA[0], 0.0, 26.0)), ("2", "chamber for the take-up spool", "void", (SP[0], 0.0, 26.0)), ("3", "rails the film lies on (top and bottom)", "pt", (0.0, 16.7)), ("4", "picture frame; its side edges are the two thin ridges kept on purpose", "pt", (17.3, 0.0)),
    ("5", "rim: a lip outside, two steps down inside it (all round)", "pt", (-60.9, 6.0)), ("6", "slot for a knob (two): a straight channel for its ring, wider higher up", "pt", (CA[0], 25.4)), ("7", "pocket for the frame wheel's fork", "pt", (RO[0] + 5.6, 21.6)), ("8", "solid steps above and below the film roll", "pt", (52.0, 19.5)), ("9", "pocket for a tripod nut (optional)", "void1", (0.0, -V.get("H", 28.2), V.get("Y_FRONT", 25.47) - 13.0)),
    ("10", "solid step and tongue under the fork's front edge", "pt", (RO[0], 19.0)), ("11", "slot for the frame wheel's neck: wider higher up", "pt", (RO[0] + 4.6, 26.8)), ("12", "catch for the back (top and bottom): two posts, a bar, a tab", "pt", (-13.4, 27.2)),
    ("a", "pocket for a foot of the plate (four): runs on sideways at its top", "under", (FT[1][0] + 2.8, FT[1][1] + 4.0)), ("b", "channel for the front plate's latch post: a bump in it holds the post", "under", ((V.get("LF_X0", 27.0) + V.get("LF_X1", 31.6)) / 2, V.get("LF_ZH", -12.2) + 2.0)), ("c", "light port", "under", (4.2, 0.0))]),
 "spool": dict(n=5, title="Take-up spool", down="knob down", kind="tall", cell=2, features=[
    ("1", "knob with saw teeth, 21 mm: your fingers catch one way", "ring", (SP[0], -SP[1], V.get("TAKE_HEAD", 10.5) - 0.2, 3.0)), ("2", "stem, as thick as the core", "ring", (SP[0], -SP[1], 5.6, 8.2)), ("3", "ring, 1.2 mm proud: it keeps the spool in the camera", "ring", (SP[0], -SP[1], 6.8, 11.8)),
    ("4", "core: the film winds onto it", "ring", (SP[0], -SP[1], 5.6, 30.0)), ("5", "slot for the film's tip", "ring", (SP[0], -SP[1], 5.6, 40.0, 360)),
    ("6", "plain end: turns in a slot in the body's floor", "ring", (SP[0], -SP[1], 4.3, 57.5))]),
 "knob": dict(n=6, title="Wind knob", down="head down", kind="tall", cell=1, features=[
    ("1", "head with saw teeth, 19 mm: your fingers catch one way", "ring", (CA[0], -CA[1], V.get("WIND_HEAD", 9.5) - 0.2, 3.0)), ("2", "stem", "ring", (CA[0], -CA[1], 4.5, 8.2)),
    ("3", "ring, 1.2 mm proud: it keeps the knob in the camera", "ring", (CA[0], -CA[1], 5.7, 11.8)), ("4", "fork, 6.6 mm: two prongs over the bar inside the film cassette", "ring", (CA[0], -CA[1], V.get("FORK_R", 3.3), 14.6, 180, 90))]),
 "roller": dict(n=7, title="Frame wheel", down="teeth down", kind="tall", cell=1, features=[
    ("1", "eight teeth: they sit in the holes along the film's edge", "ring", (RO[0], RO[1], 6.7, 1.5, 45)), ("2", "drum: the film's top band rides on it", "ring", (RO[0], RO[1], 4.9, 2.5)), ("3", "neck: turns in the fork on the back", "ring", (RO[0], RO[1], 3.0, 5.2)),
    ("4", "collar, 9.2 mm: sits behind the fork's lips and covers the hole in the top from below", "ring", (RO[0], RO[1], V.get("COLLAR_R", 4.5), 9.0)), ("5", "dial: goes round once per picture; a low ridge on the body shades the hole under it", "ring", (RO[0], RO[1], 3.6, 19.4)), ("6", "notch: comes back to the mark on the body", "void", (RO[0], RO[1] + 5.0, 19.4))]),
 "back": dict(n=8, title="Back", down="outside face down: you are looking at its inside", kind="flat", cell=5, features=[
    ("1", "film block: guide, pad and post in one solid piece", "pt", (2.0, 3.0)), ("2", "fork that holds the frame wheel", "pt", (RO[0] - 5.4, -20.8)), ("3", "proud band along each edge: only the bands can touch the film", "pt", (-6.0, 15.2)), ("4", "flat end of the block: the frame wheel stands on it", "void", (RO[0], -V.get("NOSE_TOP", 13.2), RO[1] + 6.0 + 2.5)),
    ("5", "light seal: a low step and a band (all round)", "pt", (-40.0, V.get("ZR_OUT", 23.6))), ("6", "latch finger (two): nub at its tip; plain, no rib", "pt", (4.0, 24.6)), ("7", "pad to pinch: 10.1 mm wide, stands 1.8 mm proud; the top one's edge is the rear sight", "pt", (-6.0, 24.9)), ("8", "block that closes a knob's slot (two): a wide bar over a narrow one", "pt", (CA[0] + 6.0, -26.6)),
    ("9", "foot of the spool's block: lies over the film roll, joined to the fork", "pt", (SP[0] + 8.6, -20.3)), ("10", "wide bar that wraps the frame wheel's neck", "pt", (RO[0] + 4.4, -26.9))]),
}

OLD = "build/old29/print/one135_%s.stl"; WAS = "round 5"
CHANGED = [("front", "Front plate", 6.4, -35, 38, ["GUARD GONE: it stood in the line of sight.  The plate is a plain rectangle again, with one small point on its top edge, on the lens's line: the front sight.",
                                                     "TWO MOVES TO COME OFF: each foot has a second lip, on one side.  Slid up, the plate still cannot come off; only at the top can it be slid sideways and lifted away.",
                                                     "Feet 4.4 mm tall (3.2), their far ends chamfered so that they find their pockets.  The two feet on one side stand 2.4 mm further in.  The latch leaf sits 2 mm lower.  Hooks, stops and latch work as before."]),
           ("body", "Body", 4.5, 145, 52, ["AIM LINES as in round 5: three engraved lines on the top.  The middle one lies on the lens's line and now runs to the front face.",
                                             "Pockets for the plate's feet: room under the skin for the side lips, and at the top each runs on 3.6 mm sideways: the way in and out.  They are 5.2 mm deep (3.6).",
                                             "The channel for the latch post is 1.6 mm longer and runs on sideways at its top.  The catch's tab is 2.2 mm shorter, to make room for wider pads."]),
           ("blade", "Shutter", 6.4, -35, 38, ["ROCKER'S LEFT SIDE 0.4 mm LONGER.  When that side is down its end stands at the right edge of the middle engraved line."]),
           ("back", "Back", 4.5, -35, 38, ["Pads 10.1 mm wide (3.4).  The right edge of the top pad stands at the left edge of the middle engraved line: with the rocker's end it frames the lens's line."])]

def changes():
    """one sheet: every changed part as it was and as it is, from the same corner at the same scale"""
    M, GAP = 44, 30; f_t, f_h, f_c, f_l = font(34, True), font(22, True), font(17, True), font(19); rows = []
    for key, title, ppm, az, el, notes in CHANGED:
        a, b = trimesh.load(OLD % key, process=True), trimesh.load(f"build/print/one135_{key}.stl", process=True)
        ia, _, _ = render(a, az, el, ppm, COL[key]); ib, _, _ = render(b, az, el, ppm, COL[key]); rows.append((title, ia, ib, notes))
    def wrap(d, text, width):
        out = []; line = ""
        for w_ in text.split(" "):
            t = (line + " " + w_).strip()
            if d.textlength(t, font=f_l) > width and line: out.append(line); line = w_
            else: line = t
        return out + [line]
    def block(r, wide):
        title, ia, ib, notes = r; w = max(ia.width + ib.width + GAP, wide); probe = ImageDraw.Draw(Image.new("RGB", (8, 8))); lines = [wrap(probe, n, w - 30) for n in notes]
        h = 34 + 26 + max(ia.height, ib.height) + 12 + 27 * sum(len(l) for l in lines) + 8
        im = Image.new("RGB", (w, h), "white"); d = ImageDraw.Draw(im); d.text((0, 0), title, font=f_h, fill=INK)
        d.text((0, 36), "before (%s)" % WAS, font=f_c, fill=GREY); d.text((ia.width + GAP, 36), "now (round %d)" % ROUND, font=f_c, fill=ACC)
        im.paste(ia, (0, 60)); im.paste(ib, (ia.width + GAP, 60)); y = 60 + max(ia.height, ib.height) + 12
        for l in lines:
            d.ellipse([4, y + 8, 11, y + 15], fill=ACC)
            for t in l: d.text((22, y), t, font=f_l, fill=INK); y += 27
        return im
    W = max(r[1].width + r[2].width + GAP for r in rows); W = max(W, 1180); blocks = [block(r, W) for r in rows]
    Hh = 112 + sum(b_.height + GAP for b_ in blocks) + 50; S = Image.new("RGB", (W + 2 * M, Hh), "white"); d = ImageDraw.Draw(S)
    d.text((M, 26), "What changed in round %d" % ROUND, font=f_t, fill=INK); d.text((M, 72), "Each part from the same corner and at the same scale, as it lies on the print bed.  Wind knob, take-up spool, frame wheel and aperture wheel are unchanged.", font=font(17), fill=GREY)
    y = 112
    for b_ in blocks: S.paste(b_, (M, y)); y += b_.height + GAP
    d.text((M, Hh - 40), f"{NAME} ({MODEL}), preview round {ROUND}.", font=font(17), fill=GREY); f = f"{RDIR}/{NAME.replace(' ', '-')}_round{ROUND}_0_what_changed.png"; S.save(f, optimize=True); return f, S.size

if __name__ == "__main__":
    import time
    if ARGS == ["changes"]: print(changes()); sys.exit()
    for key in (ARGS or list(SPECS)):
        t = time.time(); size = sheet(key, SPECS[key]); print(f"{key:7s} {size[0]} x {size[1]}  {time.time() - t:.0f} s")
