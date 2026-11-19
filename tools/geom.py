"""Numbers that the model (scad/one135.scad) and several tools share.  Keep in step with the model."""
import numpy as np
FIN_W, FIN_L, RK_L, RK_T, FIN_CLR = 11.0, 6.0, 13.0, 3.15, 1.8     # shutter rocker: arm width through the plate, depth front to back, length of each side, thickness, clearance over the body
PRESS = 0.8                                                       # where the finger presses: this fraction of the way out along the raised side
def rocker_v(B):
    """height of the rocker's lowest point (the bottom of the V) above the pivot"""
    return (B["H"] + FIN_CLR - B["P_S"][1] + RK_L * np.sin(np.radians(1.2))) / np.cos(np.radians(B["THETA"] + 1.2))
def press_point(B, frac=PRESS):
    """the finger's point on top of one side, in the blade's own frame (x across, z up from the pivot)"""
    th = np.radians(B["THETA"]); p = frac * RK_L
    return np.array([p * np.cos(th) - RK_T * np.sin(th), rocker_v(B) + p * np.sin(th) + RK_T * np.cos(th)])
def lever(B, psi_deg, frac=PRESS):
    """lever arm (mm) of a downward press while the pressed side stands psi degrees above its middle position: +THETA when the press starts, -THETA when it ends"""
    x, z = press_point(B, frac); a = np.radians(psi_deg); return float(x * np.cos(a) - z * np.sin(a))
def tab(B):
    """(height of the rocker's underside above the pivot, the finger's lever arm at mid-swing).  The old name is kept for the tools that need one number"""
    return float(rocker_v(B)), lever(B, 0.0)
