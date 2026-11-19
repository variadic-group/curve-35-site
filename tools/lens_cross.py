"""How does a lens that was NOT designed for ONE-135's film curve behave on it?
Stand-ins for a real disposable lens: plastic menisci optimised (earlier work, design.py) for a flat gate and for a
gentle R = 100 mm gate (what single-use cameras use).  Each is then put into ONE-135: stop 2.4-2.7 mm behind the lens,
film on R = 32 mm, focus re-set (the best a shim can do).  RMS spot radius in micrometres at 7 field points."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/cam/optics"); sys.argv = ["x"]
from design import *
from scipy.optimize import minimize_scalar
def best_focus(surfs, Rf, z0):
    r = minimize_scalar(lambda z: merit(surfs, z, Rf, rings=4)[0], bounds=(z0 - 4, z0 + 4), method="bounded", options=dict(xatol=1e-3))
    m, rms, f = merit(surfs, r.x, Rf, rings=6); return r.x, m * 1000, [round(q * 1000) for q in rms], f
def lens(p, ds=None, N=10):
    q = list(p[:4]); 
    if ds is not None: q[2] = ds
    return plastic_meniscus(q, N=N)
out = {}
x32 = json.load(open("res_plastic_R32.json"))["x"]; xfl = json.load(open("res_plastic_flat.json"))["x"]
print("optimising a meniscus for an R = 100 gate ...", flush=True)
x100 = optimise(lambda p: plastic_meniscus(p), [8.9, 18.9, 3.1, -0.5], 100.0, 31.0)
print(" R100 lens:", np.round(x100, 2))
names = ["centre", "16 deg", "26 deg", "32 deg (end)", "top", "26/15", "corner"]
def show(label, s, Rf, z0):
    z, m, rms, f = best_focus(s, Rf, z0); out[label] = dict(z_img=z, merit_um=m, rms_um=rms, efl=f)
    print("%-66s merit %3.0f | %s" % (label, m, "  ".join("%s %d" % (n, r) for n, r in zip(names, rms)))); return z
print("\n-- each lens in the camera it was designed for (f/10)")
show("lens designed for ONE-135 (R32), on R32", lens(x32), 32.0, x32[4])
show("lens designed for R100, on R100 (a disposable camera)", lens(x100), 100.0, x100[4])
show("lens designed for flat film, on flat film", lens(xfl), None, xfl[4])
print("\n-- the 'foreign' lenses dropped into ONE-135: film R32, stop 2.4 mm behind the lens, focus re-set")
for N in (10, 16):
    show("R100-design lens in ONE-135 at f/%d" % N, lens(x100, 2.4, N), 32.0, 31.0)
    show("flat-design lens in ONE-135 at f/%d" % N, lens(xfl, 2.4, N), 32.0, 31.0)
print("\n-- the same lenses if ONE-135's gate were gentler or flat (stop 2.4 mm, focus re-set, f/10)")
for Rf in (45.0, 60.0, 100.0, None):
    show("R100-design lens, gate %s" % ("R%d" % Rf if Rf else "flat"), lens(x100, 2.4), Rf, 31.0)
print("\n-- and the lens ONE-135 was designed around, on gentler gates (f/10)")
for Rf in (60.0, 100.0, None): show("R32-design lens, gate %s" % ("R%d" % Rf if Rf else "flat"), lens(x32), Rf, 31.0)
json.dump(dict(x100=list(map(float, x100)), results=out), open("/home/claude/one/build/lens_cross.json", "w"), indent=1)
