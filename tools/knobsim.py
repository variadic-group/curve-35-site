"""ONE-135: scattered light past a knob.  tools/optics.py and tools/aimleak.py look for STRAIGHT lines out of the camera.  This tool
follows light that bounces: every surface is taken as matt, sending back a share R of what falls on it, evenly to all sides.
Light starts all round the slit between a knob's head and the top of the body (as if the sky were equally bright in every direction
it can be seen from there), and is followed until it reaches the film, leaves the camera, or has faded.
The result is  T = light reaching the film / light entering the slit.  It is a number for COMPARING designs, not a forecast of fog.
    python3 tools/knobsim.py [spool|knob|wheel] [mesh folder] [back stands off, mm] [rays] [R]
    python3 tools/knobsim.py table [rays] [R]      all three openings, now and in round 1 -> build/knobsim.json"""
import sys, os, json, time, numpy as np, trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector as Fast
sys.path.insert(0, "tools"); from scadr import values
def load(d, off, with_film=True, lift=0.0, push=0.0):
    V = values(["H", "Y_RIM", "SPOOL", "CASS", "ROLLER", "ZC1", "TAKE_HEAD", "WIND_HEAD", "DIAL_R", "SHAFT_R", "HEAD_GAP"]); TH = json.load(open("build/layout.json"))["B"]["THETA"]
    L = lambda n: trimesh.load((d if os.path.exists(d + n + ".stl") else "build/asm/") + n + ".stl", process=True)
    names = ["body", "back", "front", "roller", "knob", "cassette", "spool", f"blade_PHI{TH}", "wheel_STOP2"] + (["film"] if with_film else []); ms = []; ids = []
    for k, x in enumerate(names):
        m = L(x)
        if x in ("back", "roller"): m.apply_translation([0, -off, 0])
        if x == "roller" and push: m.apply_translation([0, -push, 0])                          # the film pulls the frame wheel back against its cradle
        if x in ("knob", "spool") and lift: m.apply_translation([0, 0, lift])              # a knob lifted off the top of the body (camera upside down, or pulled)
        ms.append(m); ids.append(np.full(len(m.faces), k))
    return V, trimesh.util.concatenate(ms), np.concatenate(ids), names
def lambert(nrm, rng):                                               # a direction about each normal, cosine weighted
    k = len(nrm); u = rng.uniform(size=k); ph = rng.uniform(0, 2 * np.pi, k); st = np.sqrt(u); ct = np.sqrt(1 - u)
    a = np.where(np.abs(nrm[:, [0]]) > 0.9, [[0, 1.0, 0]], [[1.0, 0, 0]]); t1 = np.cross(nrm, a); t1 /= np.linalg.norm(t1, axis=1)[:, None]; t2 = np.cross(nrm, t1)
    return t1 * (st * np.cos(ph))[:, None] + t2 * (st * np.sin(ph))[:, None] + nrm * ct[:, None]
def run(which="spool", d="build/asm/", off=0.3, n=20_000_000, R=0.3, seed=3, maxb=40, head=None, quiet=False, gap=None, lift=0.0, push=0.0):
    V, scene, fid, names = load(d, off, lift=lift, push=push); gap = (V["HEAD_GAP"] if d == "build/asm/" else 0.4) if gap is None else gap; fast = Fast(scene); FN = scene.face_normals; film_id = names.index("film"); rng = np.random.default_rng(seed)
    H = V["H"]; c = dict(spool=V["SPOOL"], knob=V["CASS"], wheel=V["ROLLER"])[which]; z0, z1 = H + 0.01, H + gap + lift - 0.01
    r0 = (head or dict(spool=V["TAKE_HEAD"], knob=V["WIND_HEAD"], wheel=V["DIAL_R"])[which]) + 0.3
    if which == "wheel": z1 = H + 0.2 + V["DIAL_R"] - V["SHAFT_R"]; c = [c[0], c[1] - off - push]; r0 += 0.2   # the frame wheel's dial stands on a cone: the opening under its rim is 3.2 mm high.  The wheel rides on the back and moves with it
    got = 0.0; got2 = 0.0; nhit = 0; depth = np.zeros(maxb + 1); t0 = time.time(); done = 0
    while done < n:
        k = min(2_000_000, n - done); done += k; ph = rng.uniform(0, 2 * np.pi, k); z = rng.uniform(z0, z1, k)
        O = np.c_[c[0] + r0 * np.cos(ph), c[1] + r0 * np.sin(ph), z]; D = lambert(-np.c_[np.cos(ph), np.sin(ph), np.zeros(k)], rng); w = np.ones(k)
        for b in range(maxb):
            if len(O) == 0: break
            tri = fast.intersects_first(O, D); hit = tri >= 0
            O, D, w, tri = O[hit], D[hit], w[hit], tri[hit]
            if len(O) == 0: break
            isf = fid[tri] == film_id
            if isf.any(): got += w[isf].sum(); got2 += (w[isf] ** 2).sum(); nhit += int(isf.sum()); depth[b] += w[isf].sum()
            O, D, w, tri = O[~isf], D[~isf], w[~isf], tri[~isf]
            if len(O) == 0: break
            nrm = FN[tri]; nrm = np.where(((nrm * D).sum(1) > 0)[:, None], -nrm, nrm)
            v0 = scene.vertices[scene.faces[tri, 0]]; t = ((v0 - O) * nrm).sum(1) / (D * nrm).sum(1); P = O + D * t[:, None]            # where the ray meets the triangle's plane
            w = w * R; keep = w > 1e-7; O = (P + nrm * 2e-3)[keep]; D = lambert(nrm[keep], rng); w = w[keep]
    T = got / n; err = np.sqrt(max(got2, 1e-30)) / n
    out = dict(which=which, off=off, R=R, rays=n, film_hits=nhit, T=T, T_err=err, by_bounces={int(i): float(v / n) for i, v in enumerate(depth) if v > 0}, band_mm2=float(2 * np.pi * r0 * (z1 - z0)), seconds=round(time.time() - t0))
    if not quiet: print("%-5s back %.2f mm off, R %.2f: T = %.2e +- %.1e  (%d rays reached the film of %d; fewest bounces %s; %d s)" % (which, off, R, T, err, nhit, n, min(out["by_bounces"]) if out["by_bounces"] else "-", out["seconds"]), flush=True)
    return out
NAMES = dict(spool="take-up knob", knob="wind knob", wheel="frame wheel")
def table(n=24_000_000, R=0.3, most=99):
    """all three openings in the top, now and in round 1 (v2.5), with the back home and standing 0.3 and 0.6 mm off -> build/knobsim.json.
    Rows already in the file (same rays, same R) are kept, so a run that was cut short goes on where it stopped."""
    note = "T = light reaching the film / light entering under the knob's head or the wheel's dial; every surface sends back the share R.  For comparing designs only"
    try: out = json.load(open("build/knobsim.json")); assert out["R"] == R and out["rays"] == n
    except Exception: out = dict(R=R, rays=n, note=note, rows=[])
    have = {(r["version"], r["opening"], r["off"]) for r in out["rows"]}; done = 0
    for tag, d, heads in (("now", "build/asm/", dict()), ("round 1 (v2.5)", "build/old25/asm/", dict(spool=9.0, knob=9.0))):
        for which in ("spool", "knob", "wheel"):
            for off in (0.0, 0.3, 0.6):
                if (tag, NAMES[which], off) in have or done >= most: continue
                r = run(which, d, off, n, R, head=heads.get(which), quiet=True); r["version"] = tag; r["opening"] = NAMES[which]; r["fewest_bounces"] = min(r["by_bounces"]) if r["by_bounces"] else None; out["rows"].append(r); done += 1
                print("%-15s %-13s back %.1f mm off: T = %.1e +- %.0e, area x T = %.1e mm2, fewest bounces %s" % (tag, NAMES[which], off, r["T"], r["T_err"], r["T"] * r["band_mm2"], r["fewest_bounces"]), flush=True)
                json.dump(out, open("build/knobsim.json", "w"), indent=1)
    print("rows in build/knobsim.json: %d of 18" % len(out["rows"]))
if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "table": table(int(a[1]) if len(a) > 1 else 24_000_000, float(a[2]) if len(a) > 2 else 0.3, int(a[3]) if len(a) > 3 else 99)
    else:
        which = a[0] if a else "spool"; d = a[1] if len(a) > 1 else "build/asm/"; off = float(a[2]) if len(a) > 2 else 0.3; n = int(a[3]) if len(a) > 3 else 20_000_000; R = float(a[4]) if len(a) > 4 else 0.3
        r = run(which, d, off, n, R); print(json.dumps(r["by_bounces"]))
