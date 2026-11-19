"""The front plate in a fall, followed in time, in three directions.  The body is taken to stop dead; the plate, with shutter, wheel and lens, keeps its speed.  It can move on the
body's face (x toward the way out, z up) inside what its feet and pockets allow, and away from the face (D) as far as its hooks and side lips allow; hooks and lips are sloped,
so a plate pulled off the face is pushed up by its hooks and sideways by its lips, and the model follows that.  It bounces off whatever it meets and rubs on the face.
Where the plate can go is not assumed: it is read from build/platewindow.json, measured on the meshes printed fat and thin (run platewindow.py first).
Compares the mount as it is (up, then sideways) with round 5's (up and it is off its hooks).  A rough model: restitution and friction are guesses, the body is taken as rigid and
still, the camera's own bounce is left out.  Writes build/platefall.json.
    python3 tools/platefall.py"""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "tools"); from scadr import values
A = "build/asm/"; LY = json.load(open("build/layout.json")); B = LY["B"]; TH = B["THETA"]; G = 9.81; KS = 1.06; DOFF = 3.07      # KS: hooks and lips let the plate 1.06 mm further off per millimetre moved along them; DOFF: off the face by this much, nothing holds
L = lambda n: trimesh.load(A + n + ".stl", process=True)
def directions(n=20000, seed=3):
    rng = np.random.default_rng(seed); d = rng.normal(size=(n, 3)); return d / np.linalg.norm(d, axis=1)[:, None]
def geometry(d):
    """for every direction of fall: does the body land before the plate, and how far the plate can then travel along that direction before the floor meets it"""
    parts = {n: L(n) for n in ("body", "back", "front", "roller", "knob", "spool", "wheel_STOP1")}; blades = [L(f"blade_PHI{s * TH}") for s in (1, -1)]
    h_all = np.max([(d @ m.vertices.T).max(1) for m in parts.values()] + [(d @ b.vertices.T).max(1) for b in blades], 0)
    h_pl = np.max([(d @ parts["front"].vertices.T).max(1), (d @ parts["wheel_STOP1"].vertices.T).max(1)] + [(d @ b.vertices.T).max(1) for b in blades], 0)
    return h_all - h_pl
def ramp(p, q, vp, vq, g0, on, MU, R):
    """a sloped hold: q (off the face) may not exceed g0 + KS * p; where it does, put the plate back on the slope and turn its speed round (it slides along the slope, rubbing)"""
    phi = q - g0 - KS * p; k = on & (phi > 0)
    if not k.any(): return
    n2 = 1 + KS * KS; p[k] += phi[k] * KS / n2; q[k] -= phi[k] / n2; rt = np.sqrt(n2); vn = (-KS * vp[k] + vq[k]) / rt; hit = np.maximum(vn, 0); vt = (vp[k] + KS * vq[k]) / rt
    vt = np.sign(vt) * np.maximum(np.abs(vt) - MU * (1 + R) * hit, 0); vn = np.where(vn > 0, -R * vn, vn); vp[k] = (-KS * vn + vt) / rt; vq[k] = (vn + KS * vt) / rt
def run(d, room, Hd, m, W_off, W_on, play, mode, P, MU=0.3, R=0.5, T=0.03, dt=5e-6, RAKE=2.56, FLAT=0.8, RAMP=1.06):
    """P: c (side play in the home pocket), ztop (top stop), gh, zh (hooks: how far off at home, and the height above which they have let go); and for 'two': zw (height at which it
    can go across), xend (how far across), xfree (across by this much its lips are clear), gl (lips: how far off before they bear)"""
    v0 = np.sqrt(2 * G * Hd) * 1000; n = len(d); thrown = room > 0.02; sgn = -1.0                                # the way out is toward -x of the camera: the model's x runs toward the way out
    gx, gz, gD = sgn * d[:, 0], d[:, 2], d[:, 1]; x = np.zeros(n); z = np.zeros(n); D = np.zeros(n); vx = np.where(thrown, v0 * gx, 0.0); vz = np.where(thrown, v0 * gz, 0.0); vD = np.where(thrown, v0 * gD, 0.0)
    off = np.zeros(n, bool); zmax = np.zeros(n); c = P["c"]; two = mode == "two"
    zb0, zb1, zf1, zr1 = play, play + RAKE, play + RAKE + FLAT, play + RAKE + FLAT + RAMP
    for _ in range(int(T / dt)):
        live = ~off; up = vz > 0
        Fz = np.where((z >= zb0) & (z < zb1), np.where(up, -W_off / RAKE, -0.4 * W_off / RAKE), 0.0) + np.where((z >= zf1) & (z < zr1), np.where(up, 0.4 * W_on / RAMP, W_on / RAMP), 0.0)     # the latch, N (W in N mm, lengths in mm)
        vz += (Fz / m + G * gz) * 1000 * dt; vx += G * gx * 1000 * dt; vD += G * gD * 1000 * dt; x += vx * dt * live; z += vz * dt * live; D += vD * dt * live
        k = D < 0                                                                                                 # the body's face: it bounces off and rubs
        if k.any():
            jn = (1 + R) * np.maximum(-vD[k], 0); D[k] = 0; vD[k] = R * np.abs(vD[k]); sp = np.hypot(vx[k], vz[k]); f = np.maximum(sp - MU * jn, 0) / np.maximum(sp, 1e-9); vx[k] *= f; vz[k] *= f
        k = z < 0; z[k] = 0; vz[k] = np.abs(vz[k]) * 0.3                                                             # home: the feet stand on their pocket floors
        k = z > P["ztop"]; z[k] = P["ztop"]; vz[k] = -np.abs(vz[k]) * R
        if two:
            hi = z >= P["zw"]; xr = np.where(hi, P["xend"], c)
            k = (x > c) & ~hi & (vz <= 0) & (z > P["zw"] - 0.3); z[k] = P["zw"]; vz[k] = np.abs(vz[k]) * R              # coming down beside the pocket: it lands on the wall under the way out
            k = (x > c) & (z < P["zw"] - 0.3); x[k] = c; vx[k] = -np.abs(vx[k]) * R
            k = x > xr; x[k] = xr[k]; vx[k] = -np.abs(vx[k]) * R
        else:
            k = x > c; x[k] = c; vx[k] = -np.abs(vx[k]) * R
        k = x < -c; x[k] = -c; vx[k] = np.abs(vx[k]) * R
        ramp(z, D, vz, vD, P["gh"], live & (z < P["zh"]), MU, R)                                                    # hooks: pulled off, the plate is pushed up along them
        if two:
            ramp(x, D, vx, vD, P["gl"], live & (x < P["xfree"]), MU, R)                                             # side lips: pulled off, it is pushed toward the way out along them
            k = (x > c) & (z < P["zw"] - 0.3); x[k] = c; vx[k] = -np.abs(vx[k]) * R                                 # ... as far as the pocket's wall lets it
        s = x * gx + z * gz + D * gD; k = (s > room) & thrown & live                                                # the floor meets the plate
        if k.any():
            b = s[k] - room[k]; x[k] -= b * gx[k]; z[k] -= b * gz[k]; D[k] -= b * gD[k]; vn = np.maximum(vx[k] * gx[k] + vz[k] * gz[k] + vD[k] * gD[k], 0); vx[k] -= 1.3 * vn * gx[k]; vz[k] -= 1.3 * vn * gz[k]; vD[k] -= 1.3 * vn * gD[k]
        off |= D > DOFF; zmax = np.maximum(zmax, z)
    loose = ~off & (x >= P["xfree"]) if two else np.zeros(n, bool)                                                 # still on its feet, but across far enough that nothing holds it: it comes off when the camera is picked up
    gone = off | loose; parked = ~gone & (z > zf1 - 0.2); lifted = ~gone & ~parked & (zmax > zb1)
    return dict(off=100 * float(gone.mean()), thrown_clear=100 * float(off.mean()), left_up=100 * float(parked.mean()), went_over_and_came_back=100 * float(lifted.mean()), thrown=100 * float(thrown.mean()))
def measured(PW, key, mode):
    w = PW["now" if mode == "two" else "round5"][key]; h = w["home"]; pb = dict(w["pull_off_by_height"]); gh = pb[0.0]
    P = dict(c=max(w["side_play_at_home"][1], 0.05), ztop=round(w["top_stop"] - h, 2), gh=gh)
    if mode == "two":
        P.update(zw=round(w["band"][0] - h, 2), xend=w["across_to"], xfree=w["set_on"]["side"][0], gl=w["pull_off_by_side_in_band"][0][1]); P["zh"] = round((P["gl"] - gh) / KS + 0.6, 2)   # above this the lips, not the hooks, hold
    else: P["zh"] = min(z for z, v in pb.items() if v >= 3.39)
    return P
if __name__ == "__main__":
    EC = json.load(open("build/endcases.json"))["plate"]; SLC = json.load(open("build/slicecheck.json")); m = (SLC["front"]["grams"] + SLC["blade"]["grams"] + SLC["wheel"]["grams"] + 2.0) / 1000
    d = directions(); room = geometry(d); PW = json.load(open("build/platewindow.json"))
    out = dict(plate_g=m * 1000, note="rough model in three directions: the body stops dead and is rigid, restitution 0.5, friction 0.3; the camera's own bounce is left out", measured={})
    CASES = [("a thin printer, slippery plastic", "0.15 thin", 0, "far too thin: walls -0.15"), ("a typical printer", "0.10 fat", 1, "typical: walls +0.10"), ("a fat printer, rough plastic", "0.25 fat", 2, "far too fat: walls +0.25")]
    for mode, label in (("two", "two moves (now)"), ("straight", "one move (as it was)")):
        for Hd in (0.1, 0.3, 0.5, 1.0):
            for name, key, mu, pk in CASES:
                q = EC[key]; P = measured(PW, pk, mode); out["measured"].setdefault(label, {})[name] = P
                r = run(d, room, Hd, m, q["work_off_Nmm"][mu], q["slide_on_N"][mu] * 0.7, q["play_at_home"], mode, P); out.setdefault(label, {}).setdefault("%.1f m" % Hd, {})[name] = r
                print("%-22s %.1f m  %-34s off %5.1f %% (thrown clear %5.1f)   left pushed up %5.1f %%   over the latch and back %5.1f %%" % (label, Hd, name, r["off"], r["thrown_clear"], r["left_up"], r["went_over_and_came_back"]), flush=True)
    json.dump(out, open("build/platefall.json", "w"), indent=1)
