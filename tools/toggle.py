"""Over-centre geometry study.  Blade pivot at the origin; blade pin S at radius R_S, pointing down (-z) +/- THETA.
Lever pivot P_L = (0, zp) below; lever pin L at radius R_L from it, +/- BETA.  All lengths mm.
d = distance from the blade pivot to the spring line = torque arm per unit spring force.
What matters: d_start (lever fully thrown, blade not yet moved) against the friction arm mu * (r_pin + h)."""
import numpy as np, itertools
TH = np.radians(24.5)
def S(phi, RS): return np.array([RS * np.sin(phi), -RS * np.cos(phi)])
def L(beta, zp, RL): return np.array([RL * np.sin(beta), zp + RL * np.cos(beta)])
def arm(P, A, B):                       # signed distance of P from line A->B
    v = B - A; return float((v[0] * (P[1] - A[1]) - v[1] * (P[0] - A[0])) / np.linalg.norm(v))
rows = []
for RS, xl, zc in itertools.product([6, 7, 8, 9, 10], [5.5, 6.5, 7.5, 9.0], [2.5, 3.3, 4.5, 6.0]):
    zp = -(RS + 4.3); RL = zc - zp; be = np.arcsin(xl / RL)
    Sl = S(-TH, RS); Ll, Lr = L(-be, zp, RL), L(be, zp, RL); PL = np.array([0, zp])
    d_start = abs(arm(np.zeros(2), Sl, Lr)); d_mid = abs(arm(np.zeros(2), S(0, RS), Lr)); d_rest = abs(arm(np.zeros(2), Sl, Ll))
    hold = arm(PL, Sl, Ll)              # > 0: the spring pushes the lever outward onto its stop
    len_rest = np.linalg.norm(Ll - Sl); len_max = np.linalg.norm(Lr - Sl)
    bs = np.linspace(-be, be, 400); ln = [np.linalg.norm(L(b, zp, RL) - Sl) for b in bs]
    tq = [arm(np.zeros(2), Sl, L(b, zp, RL)) for b in bs]; i_dead = int(np.argmin(np.abs(tq)))
    rows.append((RS, xl, zc, zp, RL, np.degrees(be), d_start, d_mid, d_rest, hold, len_rest, ln[i_dead], len_max, np.degrees(bs[i_dead])))
print(" RS   xL   zc     zp    RL  beta | d_start d_mid d_rest  hold | len rest  dead   max | dead at")
for r in sorted(rows, key=lambda r: -r[6])[:16] + [r for r in rows if r[0] == 8 and r[1] == 6.5]:
    print("%3d %4.1f %4.1f %6.1f %5.1f %5.1f | %6.2f %6.2f %6.2f %5.2f | %7.2f %6.2f %6.2f | %5.1f" % r)
