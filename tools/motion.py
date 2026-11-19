"""ONE-135 motion proof.  tools/check.py asks whether the parts overlap where they rest and along the straight ways in and out.  This tool moves every part
that moves through the whole of its travel, in small steps, and at every step measures against every neighbour: the volume the two share (it must be nothing)
and the nearest the two come to each other.  Then the film: a strip with both rows of perforations is drawn along the model's film path and pulled through one
picture's length while it turns the frame wheel; the teeth must pass through the holes without touching the film between them.  Three film thicknesses,
an empty and a full take-up roll.  Rigid parts at their drawn size: springs and clicks are left out here (their bumps are removed) and are covered by tools/fea.py.
Writes build/motion.json.     python3 tools/motion.py"""
import sys, os, json, time, numpy as np, manifold3d as m3
sys.path.insert(0, "tools"); import kin; from kin import V, TH, XE, LIFT, PITCH, RP, man, put, Tr, RZ, blade, wheel
t00 = time.time(); SEARCH = 4.0; EPS = 0.002
PHIS = [float(round(x, 3)) for x in np.linspace(-TH, TH, 23)]
def comp(*ms): return m3.Manifold.compose(list(ms))
def measure(mover, others):
    out = {}
    for n, o in others.items(): out[n] = (float((mover ^ o).volume()), float(mover.min_gap(o, SEARCH)))
    return out
import re as _re; R = {"model": _re.search(r"// (ONE-135 v[0-9.]+)", open("scad/one135.scad").read()).group(1), "motions": {}, "film": {}}
def run(key, label, unit, xs, mover, others, expected=(), note=""):
    t0 = time.time(); rows = [measure(mover(x), others) for x in xs]; pairs = {n: dict(overlap=[round(r[n][0], 4) for r in rows], gap=[round(r[n][1], 3) for r in rows]) for n in others}
    worst = max(((max(p["overlap"]), n) for n, p in pairs.items() if n not in expected), default=(0, "")); near = min((min(p["gap"]), n, xs[int(np.argmin(p["gap"]))]) for n, p in pairs.items() if n not in expected)
    R["motions"][key] = dict(label=label, unit=unit, x=[round(float(x), 3) for x in xs], pairs=pairs, expected=list(expected), note=note, steps=len(xs), max_overlap_mm3=round(worst[0], 4), max_overlap_with=worst[1],
                             min_gap_mm=round(near[0], 3), min_gap_with=near[1], min_gap_at=round(float(near[2]), 2), free=bool(worst[0] <= EPS))
    print("%-34s %3d steps  shared volume %.4f mm3%s  nearest %.2f mm (%s, at %s %s)  %s   %.0f s" % (label, len(xs), worst[0], " (" + worst[1] + ")" if worst[0] > EPS else "", near[0], near[1], round(float(near[2]), 1), unit, "FREE" if worst[0] <= EPS else "MEETS", time.time() - t0), flush=True)
    for n in expected: print("      expected contact with %s: up to %.3f mm3" % (n, max(pairs[n]["overlap"])))
S = lambda *n: {k: man(k) for k in n}
# ---------------------------------------------------------------- 1. the shutter swings from one closed position to the other
run("shutter", "shutter, closed to closed", "deg", PHIS, lambda p: man(f"bladeN_BL_BUMP0.0_PHI{p}"), {**S("front", "body", "lens", "back", "roller", "spool", "knob"), **{f"aperture wheel at stop {k}": man(f"wheel_STOP{k}") for k in range(3)}},
    note="click bump removed: the bump is meant to press on its wall")
# ---------------------------------------------------------------- 2. the aperture wheel slides from the smallest hole to the largest
AW = np.linspace(0, V["WPOS"][2], 31)
run("aperture", "aperture wheel, small to large", "deg", AW, lambda a: put("wheel0", wheel(a)), {**S("front", "body", "lens"), "shutter closed one way": man(f"blade_PHI{TH}"), "shutter closed the other way": man(f"blade_PHI{-TH}"), "shutter open": man("blade_PHI0.0")},
    note="click tooth removed")
# ---------------------------------------------------------------- 3. the front plate goes on: onto the body, across, down
sub = comp(man("frontN"), man(f"blade_PHI{TH}"), man("wheel_STOP2"), man("lens")); SL = V["SLIDE"]
legA = [(-XE, d, SL) for d in np.linspace(14, 0, 15)]; legB = [(-s, 0, SL) for s in np.linspace(XE, 0, 12)[1:]]; legC = [(0, 0, s) for s in np.linspace(SL, 0, 14)[1:]]; PL = legA + legB + legC
plen = np.r_[0, np.cumsum([np.linalg.norm(np.subtract(PL[i + 1], PL[i])) for i in range(len(PL) - 1)])]; PLmap = {round(float(u), 3): p for u, p in zip(plen, PL)}
run("plate", "front plate: on, across, down", "mm of travel", [round(float(u), 3) for u in plen], lambda u: sub.translate(list(PLmap[round(float(u), 3)])), S("body"), note="latch tooth removed (the tongue gives); carried with it: shutter, aperture wheel, lens")
R["motions"]["plate"]["legs"] = dict(onto=float(plen[len(legA) - 1]), across=float(plen[len(legA) + len(legB) - 1]), down=float(plen[-1]))
# ---------------------------------------------------------------- 4. the lens is pressed in
run("lens", "lens pressed into its pocket", "mm from home", np.linspace(8, 0, 17), lambda d: man("lens").translate([0, float(d), 0]), {**S("front"), "shutter open": man("blade_PHI0.0"), "aperture wheel": man("wheel_STOP2")}, expected=("front",), note="the three ribs in the pocket are meant to be squeezed")
# ---------------------------------------------------------------- 5. the spool and its knob
run("spool_in", "spool slides in from the back", "mm from home", np.linspace(26, 0, 27), lambda d: man("spool").translate([0, -float(d), 0]), S("body"))
ANG = np.arange(0, 360, 5.0)
run("spool_turn", "spool, one whole turn", "deg", ANG, lambda a: put("spool", RZ(V["SPOOL"], a)), S("body", "back", "roller"))
# ---------------------------------------------------------------- 6. the wind knob
run("knob_in", "wind knob slides in (alone)", "mm from home", np.linspace(26, 0, 27), lambda d: man("knob").translate([0, -float(d), 0]), S("body"))
run("knobfilm_in", "wind knob and film slide in", "mm from home", np.linspace(26, 0, 27), lambda d: comp(man("knob"), man("cassette")).translate([0, -float(d), 0]), S("body"))
run("knob_turn", "wind knob, one whole turn", "deg", ANG, lambda a: put("knob", RZ(V["CASS"], a)), S("body", "back"))
# ---------------------------------------------------------------- 7. the frame wheel: into its fork, down, and round
FW = [(0, d, LIFT) for d in np.linspace(12, 0, 13)] + [(0, 0, z) for z in np.linspace(LIFT, 0, 11)[1:]]; flen = np.r_[0, np.cumsum([np.linalg.norm(np.subtract(FW[i + 1], FW[i])) for i in range(len(FW) - 1)])]; FWmap = {round(float(u), 3): p for u, p in zip(flen, FW)}
run("wheel_in", "frame wheel: into the fork, down", "mm of travel", [round(float(u), 3) for u in flen], lambda u: man("roller").translate(list(FWmap[round(float(u), 3)])), S("back"))
run("wheel_turn", "frame wheel, one whole turn", "deg", np.arange(0, 360, 2.5), lambda a: put("roller", RZ(V["ROLLER"], a)), S("back", "body", "spool"))
t0 = time.time(); top = lambda n: man(n).trim_by_plane([0, 0, 1], V["H"] - 0.5)                                  # only what stands above the top of the body
sw = lambda m, c, st: m3.Manifold.batch_boolean([m.transform(RZ(c, a)[:3, :]) for a in np.arange(0, 360, st)], m3.OpType.Add)
dial = sw(top("roller"), V["ROLLER"], 4.0); head = sw(top("spool"), V["SPOOL"], 3.0)
R["dial_and_knob"] = dict(shared_mm3=round(float((dial ^ head).volume()), 4), nearest_mm=round(float(dial.min_gap(head, SEARCH)), 3)); print("frame wheel's dial and the spool's knob, both turning: shared %.4f mm3, nearest %.2f mm   %.0f s" % (R["dial_and_knob"]["shared_mm3"], R["dial_and_knob"]["nearest_mm"], time.time() - t0), flush=True)
# ---------------------------------------------------------------- 8. the back goes on, carrying the frame wheel
run("back", "back and frame wheel go on", "mm from home", np.linspace(14, 0, 29), lambda d: comp(man("backN"), man("roller")).translate([0, -float(d), 0]), S("body", "spool", "knob", "cassette"), note="latch nubs pressed in (the fingers give)")
run("back_film", "back closes over the film", "mm from home", np.linspace(14, 0, 29), lambda d: man("backN").translate([0, -float(d), 0]), {"film, empty take-up": man("film_empty"), "film, full take-up": man("film")}, note="the back alone against the threaded film")
# the cassette stands on the chamber's floor (that is a rest, not a rub): its side clearance on the way in
cas = man("cassette").trim_by_plane([0, 0, 1], V["ZC0"] + 0.5).trim_by_plane([0, 0, -1], -(V["ZC0"] + 42.9))
run("cassette_side", "film's shell, side clearance going in", "mm from home", np.linspace(26, 0, 27), lambda d: cas.translate([0, -float(d), 0]), S("body"), note="bought part, drawn 25 mm across; its two ends left out (it stands on the floor)")
# ---------------------------------------------------------------- 9. the film and the frame wheel's teeth
ring = (m3.Manifold.cylinder(V["TOOTH_Z"] + 1.0, V["R_ROLL"] + V["TOOTH"] + 1.0, circular_segments=96) - m3.Manifold.cylinder(V["TOOTH_Z"] + 3.0, V["R_ROLL"] + 0.03, circular_segments=96).translate([0, 0, -1])).translate([V["ROLLER"][0], V["ROLLER"][1], V["WH_Z"][0] - 0.5])
teeth = man("roller") ^ ring; print("teeth alone: %.2f mm3" % teeth.volume())
ADV = np.linspace(0, PITCH, 39); F = R["film"]; F["cases"] = {}
# the back closes with the film in: the frame wheel rides in on the back and the film wraps round it as it comes.  The film does not move; the wheel is free to turn.
# At each position: over how many degrees of the wheel's turn (of the 45 between two teeth) do all teeth stand clear of the film?  If there is always such a place, the teeth can come down into the holes.
roll0 = kin.roll_radius(0); _, i0 = kin.film(roll0, adv=0.0, path=kin.film_pts_closing(0.0, roll0), near=(V["ROLLER"], 17.0)); u0 = i0["u_mid"]; F["closing"] = []
for d in np.linspace(6, 0, 25):
    d = float(d); f, info = kin.film(roll0, adv=0.0, path=kin.film_pts_closing(d, roll0), u0=u0, near=([V["ROLLER"][0], V["ROLLER"][1] - d], 17.0))
    ov = [float((teeth.transform((Tr([0, -d, 0]) @ RZ(V["ROLLER"], ph))[:3, :]) ^ f).volume()) for ph in np.arange(0, 45, 1.0)]
    F["closing"].append(dict(back_mm_from_home=round(d, 2), wrap_deg=round(float(info["wrap_deg"]), 1), free_deg=int(sum(o <= 1e-4 for o in ov)), least_shared_mm3=round(min(ov), 5), most_shared_mm3=round(max(ov), 4)))
F["closing_free"] = all(c["free_deg"] > 0 for c in F["closing"]); cmin = min(F["closing"], key=lambda c: c["free_deg"])
print("back closing with film in: at every one of %d positions the wheel has a place to stand with all teeth clear: %s (least room: %d of 45 degrees, %.1f mm from home; wrap grows %.0f -> %.0f deg)" % (len(F["closing"]), F["closing_free"], cmin["free_deg"], cmin["back_mm_from_home"], F["closing"][0]["wrap_deg"], F["closing"][-1]["wrap_deg"]))
print("   out of step (teeth on the film between two holes): up to %.2f mm3 of tooth where film is: the film's top edge is held 1.2 mm off the drum until the first 5 mm of winding lets the teeth drop in" % max(c["most_shared_mm3"] for c in F["closing"]))
FILMS = [("thin film, 0.10 mm", 0.10), ("ordinary film, 0.13 mm", 0.13), ("thick film, 0.15 mm", 0.15)]
for flab, t in FILMS:
    for rlab, L in (("take-up roll empty", 0.0), ("36 pictures on the take-up roll", 1640.0)):
        t0 = time.time(); roll = kin.roll_radius(L, t); ov = []; gp = []; drum = []
        for a in ADV:
            f, info = kin.film(roll, adv=float(a), t=t, near=(V["ROLLER"], 17.0)); ph = kin.wheel_phase(info) + kin.wheel_turn(float(a)) * (V["R_ROLL"] + 0.13 / 2) / (V["R_ROLL"] + t / 2)      # a thinner film rides nearer the drum: the wheel turns a little more per millimetre
            Mz = RZ(V["ROLLER"], ph); tt = teeth.transform(Mz[:3, :]); ov.append(float((tt ^ f).volume())); gp.append(float(tt.min_gap(f, SEARCH)))
        room = 0.0
        for sh in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):               # how much smaller could every hole be before a tooth touched?
            worst = 0.0
            for a in ADV[::3]:
                f, info = kin.film(roll, adv=float(a), t=t, near=(V["ROLLER"], 17.0), shrink=sh); ph = kin.wheel_phase(info) + kin.wheel_turn(float(a)) * (V["R_ROLL"] + 0.13 / 2) / (V["R_ROLL"] + t / 2)
                worst = max(worst, float((teeth.transform(RZ(V["ROLLER"], ph)[:3, :]) ^ f).volume()))
            if worst > EPS: break
            room = sh
        F["cases"][f"{flab}; {rlab}"] = dict(thickness=t, roll_radius=round(roll, 2), wrap_deg=round(float(info["wrap_deg"]), 1), teeth_in_holes=round(float(info["wrap_deg"]) / 45, 2), adv=[round(float(a), 3) for a in ADV], overlap=[round(x, 5) for x in ov], gap=[round(x, 3) for x in gp],
                                             max_overlap_mm3=round(max(ov), 5), min_gap_mm=round(min(gp), 3), holes_could_shrink_by_mm=room)
        print("%-24s %-34s wrap %5.1f deg (%.1f teeth)  teeth x film %.5f mm3  nearest tooth to hole edge %.2f mm  holes could be %.2f mm smaller all round   %.0f s" % (flab, rlab, info["wrap_deg"], info["wrap_deg"] / 45, max(ov), min(gp), room, time.time() - t0), flush=True)
# a wheel that is half a tooth out of step: the test must notice
f, info = kin.film(kin.roll_radius(0), adv=0.0, near=(V["ROLLER"], 17.0)); F["out_of_step_check_mm3"] = round(float((teeth.transform(RZ(V["ROLLER"], kin.wheel_phase(info) + 22.5)[:3, :]) ^ f).volume()), 4)
print("control: wheel half a tooth out of step x film: %.3f mm3 (must be > 0: the test can see a tooth on the film)" % F["out_of_step_check_mm3"])
# the plain film against the printed parts, as the take-up roll grows; then a roll that has sprung loose
F["roll"] = []
for L in (0, 200, 400, 700, 1000, 1300, 1640):
    for t in (0.13, 0.15):
        r = kin.roll_radius(L, t); f, info = kin.film(r, t=t); row = dict(length_on_mm=L, thickness=t, roll_radius=round(r, 2))
        for n in ("body", "back"): row[n] = [round(float((f ^ man(n)).volume()), 4), round(float(f.min_gap(man(n), SEARCH)), 3)]
        row["chamber_wall_gap"] = round(V["RCH_S"] - r, 2); F["roll"].append(row)
        print("  %4d mm wound on, %.2f mm film: roll radius %5.2f; x body %.4f mm3 (nearest %.2f); x back %.4f mm3 (nearest %.2f); roll to chamber wall %.2f mm" % (L, t, r, row["body"][0], row["body"][1], row["back"][0], row["back"][1], row["chamber_wall_gap"]))
F["turns_to_wind_out"] = round(float(sum(38.0 / (2 * np.pi * kin.roll_radius(38.0 * k)) for k in range(int(1640 / 38)))), 1)
F["pictures"] = dict(one_turn_of_dial_mm=round(2 * np.pi * RP, 3), eight_pitches_mm=8 * PITCH)
print("  one turn of the dial moves %.3f mm of film; 8 perforations are %.2f mm.  Winding 1.64 m onto the spool takes about %.0f turns of the knob" % (F["pictures"]["one_turn_of_dial_mm"], 8 * PITCH, F["turns_to_wind_out"]))
# ---------------------------------------------------------------- summary
R["summary"] = [dict(move=m["label"], steps=m["steps"], free=m["free"], shared_mm3=m["max_overlap_mm3"], nearest_mm=m["min_gap_mm"], nearest_to=m["min_gap_with"]) for m in R["motions"].values()]
R["all_free"] = all(m["free"] for m in R["motions"].values()) and R["dial_and_knob"]["shared_mm3"] <= EPS and all(c["max_overlap_mm3"] <= EPS for c in F["cases"].values()) and F["closing_free"]
F["film_on_its_rails_note"] = "the film is drawn 0.01 to 0.02 mm off the rails and guide it lies on; a film 0.02 mm thicker is drawn that much into the corner where guide meets rail (%.4f mm3 over its 35 mm width)" % max(r["body"][0] for r in F["roll"])
R["positions_tested"] = sum(m["steps"] * len(m["pairs"]) for m in R["motions"].values()) + sum(len(c["adv"]) for c in F["cases"].values()) + len(F["roll"]) * 2
json.dump(R, open("build/motion.json", "w"), indent=1)
print("\n%d positions measured.  Everything that moves is free: %s.   %.0f s" % (R["positions_tested"], R["all_free"], time.time() - t00))
