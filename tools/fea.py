"""2-D finite-element models (linear elastic, plane stress with per-region thickness) of the parts that bend or snap.
Geometry is cut straight from the exported part meshes.  A displacement is imposed where the part is pushed in use; the model
returns the force that takes and the peak strain, which is compared with what printed PLA tolerates in that print direction."""
import sys, json, numpy as np, trimesh, shapely, gmsh
from shapely.geometry import Polygon, Point
from skfem import MeshTri, Basis, ElementTriP1, ElementVector, BilinearForm, condense, solve
from skfem.helpers import ddot, sym_grad, trace, eye
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
E_PLA = 3000.0; NU = 0.36
import os
WALL = float(os.environ.get("WALL", "0"))                             # printer's wall error: every section is cut from the model and then grown by this much (tools/endcases.py)
LIMIT = dict(inplane_repeated=0.5, inplane_rare=1.0, across_repeated=0.33, across_rare=0.5)      # peak strain, %  (about 15 / 30 / 10 / 15 MPa)
def section(stl, origin, normal, ax):
    """cut a mesh with a plane; return the cross-section as one shapely polygon (even-odd) in the two world axes `ax`"""
    m = trimesh.load(stl, process=True); sec = m.section(plane_origin=origin, plane_normal=normal); out = None
    for loop in sorted([Polygon(np.asarray(l)[:, ax]) for l in sec.discrete if len(l) > 3], key=lambda p: -p.area):
        loop = loop.buffer(0); out = loop if out is None else out.symmetric_difference(loop)
    return out.buffer(WALL, 8) if WALL else out
def mesh(poly, h=0.8, fine=()):
    """fine: [(x, y, radius, size)] local refinement"""
    poly = max([g for g in poly.geoms if g.geom_type == "Polygon"], key=lambda g: g.area) if poly.geom_type in ("MultiPolygon", "GeometryCollection") else poly
    poly = poly.simplify(0.01); gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); g = gmsh.model.geo; loops = []
    for ring in [poly.exterior] + list(poly.interiors):
        pts = [g.addPoint(x, y, 0) for x, y in list(ring.coords)[:-1]]; lines = [g.addLine(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]; loops.append(g.addCurveLoop(lines))
    g.addPlaneSurface(loops); g.synchronize(); F = gmsh.model.mesh.field; ids = []
    for (x, y, r, s) in fine:
        b = F.add("Ball"); F.setNumber(b, "XCenter", x); F.setNumber(b, "YCenter", y); F.setNumber(b, "Radius", r); F.setNumber(b, "VIn", s); F.setNumber(b, "VOut", h); F.setNumber(b, "Thickness", r); ids.append(b)
    if ids:
        mn = F.add("Min"); F.setNumbers(mn, "FieldsList", ids); F.setAsBackgroundMesh(mn)
    for k in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints", "MeshSizeFromCurvature"): gmsh.option.setNumber("Mesh." + k, 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h); gmsh.model.mesh.generate(2)
    _, xyz, _ = gmsh.model.mesh.getNodes(); et, _, en = gmsh.model.mesh.getElements(2); gmsh.finalize()
    p = xyz.reshape(-1, 3)[:, :2].T; t = (en[0].reshape(-1, 3) - 1).T.astype(np.int64)
    used = np.unique(t); remap = -np.ones(p.shape[1], np.int64); remap[used] = np.arange(len(used)); return MeshTri(p[:, used], remap[t])
def run(name, poly, thick, fixed, pushes, E=E_PLA, h=0.8, fine=(), ignore=0.5, limit="inplane_repeated", note=""):
    """thick(x, y) -> mm; fixed(x, y) -> bool; pushes: [((x, y), (dx, dy))] imposed displacements at those points"""
    m = mesh(poly, h, fine); basis = Basis(m, ElementVector(ElementTriP1()), intorder=2); c = m.p[:, m.t].mean(1); tk = thick(c[0], c[1])
    lam = E * NU / ((1 + NU) * (1 - 2 * NU)); mu = E / (2 * (1 + NU)); lam = 2 * lam * mu / (lam + 2 * mu)          # plane stress
    tq = np.repeat(tk[:, None], basis.X.shape[1] if basis.X.ndim > 1 else 1, 1)
    @BilinearForm
    def a(u, v, w):
        e = sym_grad(u); return w["t"] * ddot(2 * mu * e + lam * eye(trace(e), 2), sym_grad(v))
    K = a.assemble(basis, t=np.broadcast_to(tk[:, None], basis.dx.shape))
    x, y = m.p; u = np.zeros(basis.N); D = []
    fx = np.nonzero(fixed(x, y))[0]; D += list(basis.nodal_dofs[0, fx]) + list(basis.nodal_dofs[1, fx])
    loaded = []
    for (px, py), (dx, dy) in pushes:
        n = np.array([np.argmin(np.hypot(x - px, y - py))])          # one node: a contact point that is free to rotate and to slide sideways
        for k, d in ((0, dx), (1, dy)):
            if d is not None: dof = basis.nodal_dofs[k, n]; u[dof] = d; D += list(dof); loaded.append((dof, k))
    D = np.unique(D); u = solve(*condense(K, x=u, D=D)); R = K @ u
    force = float(np.hypot(*[sum(R[d].sum() for d, k in loaded if k == kk) for kk in (0, 1)]))
    ux, uy = u[basis.nodal_dofs[0]], u[basis.nodal_dofs[1]]; T = m.t; X = m.p[:, T]
    b = np.array([X[1, 1] - X[1, 2], X[1, 2] - X[1, 0], X[1, 0] - X[1, 1]]); cc = np.array([X[0, 2] - X[0, 1], X[0, 0] - X[0, 2], X[0, 1] - X[0, 0]]); A2 = b[0] * cc[1] - b[1] * cc[0]
    exx = (b * ux[T]).sum(0) / A2; eyy = (cc * uy[T]).sum(0) / A2; exy = 0.5 * ((cc * ux[T]).sum(0) + (b * uy[T]).sum(0)) / A2
    e1 = (exx + eyy) / 2 + np.sqrt(((exx - eyy) / 2) ** 2 + exy ** 2); e2 = (exx + eyy) / 2 - np.sqrt(((exx - eyy) / 2) ** 2 + exy ** 2); peak = np.maximum(np.abs(e1), np.abs(e2)) * 100
    keep = np.ones(len(peak), bool)
    for (px, py), _ in pushes: keep &= np.hypot(c[0] - px, c[1] - py) > ignore            # not the contact point itself
    keep &= ~np.isin(np.arange(m.t.shape[1]), np.nonzero(fixed(c[0], c[1]))[0])
    i = np.argmax(np.where(keep, peak, 0)); lim = LIMIT[limit]
    res = dict(name=name, force_N=round(force, 3), peak_strain_pct=round(float(peak[i]), 3), peak_stress_MPa=round(float(peak[i]) / 100 * E, 1), at=[round(float(c[0, i]), 2), round(float(c[1, i]), 2)],
               limit_pct=lim, margin=round(lim / max(float(peak[i]), 1e-9), 2), criterion=limit, elements=int(m.t.shape[1]), note=note)
    print(f"{name:46s} force {force:6.2f} N  peak strain {peak[i]:5.2f} % ({peak[i] / 100 * E:5.1f} MPa) at ({c[0, i]:6.1f}, {c[1, i]:6.1f})  limit {lim} % [{limit}]  x{res['margin']:.1f} {'OK' if res['margin'] >= 1 else '** OVER **'}")
    return res, (m, np.where(keep, peak, 0), (ux, uy))
from matplotlib.colors import LinearSegmentedColormap
CMAP = LinearSegmentedColormap.from_list("strain", [(0, "#dfe3ea"), (0.25, "#9fc5e8"), (0.5, "#ffd34d"), (0.75, "#f28c28"), (1, "#c81e1e")])
def picture(out, panels, cols=2, aspect=1.45, fs=17):
    """panels: [(title, (mesh, peak, (ux, uy)), (x0, x1, y0, y1), vmax)]; every panel is drawn bent, in a box of the same shape"""
    rows = int(np.ceil(len(panels) / cols)); fig, ax = plt.subplots(rows, cols, figsize=(7.2 * cols, 7.2 / aspect * rows + 0.9 * rows), squeeze=False)
    for a_, (title, (m, pk, (ux, uy)), box, vmax) in zip(ax.ravel(), panels):
        tp = a_.tripcolor(m.p[0] + ux, m.p[1] + uy, m.t.T, facecolors=pk, cmap=CMAP, vmin=0, vmax=vmax); a_.set_aspect("equal"); a_.set_title(title, fontsize=fs, loc="left")
        cx, cy = (box[0] + box[1]) / 2, (box[2] + box[3]) / 2; w = max(box[1] - box[0], (box[3] - box[2]) * aspect); a_.set_xlim(cx - w / 2, cx + w / 2); a_.set_ylim(cy - w / aspect / 2, cy + w / aspect / 2); a_.axis("off")
    for a_ in ax.ravel()[len(panels):]: a_.axis("off")
    plt.tight_layout(rect=(0, 0.085, 1, 1)); cax = fig.add_axes([0.25, 0.052, 0.5, 0.014]); cb = fig.colorbar(tp, cax=cax, orientation="horizontal"); cb.set_label("peak strain, %   (limit 0.5 % for every shot, 1 % for now and then; half that across the print layers)", fontsize=fs - 3); cb.ax.tick_params(labelsize=fs - 3)
    plt.savefig(out, dpi=80); plt.close()
