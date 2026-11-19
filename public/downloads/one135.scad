// ONE-135 v2.17 : one simple 35 mm film camera, printed parts only.  No spring, no pins, no screws, no supports,
// no glue, no tape, no tools.  The only things that are not printed: the film and (optional, but it makes this a
// hand-held camera) the lens from a used single-use camera.
//
// v2.17 (print-farm review): (1) every print file is a sealed solid: tools/scadr.py welds what OpenSCAD 2021 writes (its STL writer keeps six digits, so faces that the
// model puts 0.00001 to 0.001 mm apart came out as slivers and 10-nanometre edges, which a checker that welds vertices reads as non-manifold edges) through manifold3d,
// and tools/meshcheck.py proves 0 open / 0 non-manifold edges on every file.  (2) BED_CHAMFER: a 45-degree chamfer on each part's outer edge on the bed (elephant's foot);
// the table is by BED_CHAMFER, below.  (3) Stiffer shutter and aperture wheel: the shutter's thick root reaches 17 mm from the pivot (it was 14); the aperture wheel
// carries a web 1.2 mm tall over 130 degrees of its far side, merged with the handle's foot, in a matching room in the front plate.  Swing, overlap, clicks and holes unchanged.
//
// v2.10 (round 6): the guard round the rocker is gone again (it stood in the line of sight).  Sights: two rails in a V on the top whose outer sides are the left and right
// edges of the picture, and a wedge sunk into each end for the top and bottom edges.  The front plate takes two moves to come off, up and then sideways (it took one,
// and a fall could do it): each foot has a second lip, each pocket runs on sideways at its top.  The back's pads are 5.6 mm wide.
// v2.9 (round 5): the front plate's latch leaf points up from its root (it holds two to four times as hard and goes on with a third of the force); the back's fingers
// are plain again and its catch stands 1.4 mm proud, not 2.4 (putting the camera down on its back no longer strains them); wind knob fork 6.6 mm.  See END_CASES.md.
//
// World frame: origin = centre of the film at the gate.  +X right (seen from behind the camera),
// +Y toward the subject, +Z up.  Units mm.  Every part is modelled in its assembled position;
// PART = "p_<name>" lays one part on the print bed.
//
// How it works
//   * Film is curved on a 32 mm radius (the drum) around the lens, so a single-element lens is sharp to the corners.
//   * PRE-WIND: after loading you crank the whole roll onto the take-up spool; every shot winds the exposed frame
//     back into the cassette.  At the end the film is already sealed in its cassette.
//   * The body is ONE print, front face on the bed, open at the back: every cavity is open upward, so no supports.
//     Everything that sits behind the film rides on the back, as ONE solid block: film guide, pressure pad and film post in one piece.
//   * Light seal: the body's rim steps down twice; a low step and a band on the back fill the two steps.  No tongue, no groove, nothing narrower than 2 mm.
//   * Three things come through the top: two knobs and the frame wheel's neck.  Each slides in from the back, and a bar on the back closes its slot
//     behind it: a wide bar over a narrower one, so that no gap runs straight down.  What still gets past lands on plastic, not on film: on the
//     knob's ring, on the wheel's collar, and on a solid foot of the take-up block that lies over the film roll.  Checked with tools/aimleak.py
//     (straight lines) and tools/knobsim.py (light that bounces).
//   * Shutter: ONE moving part.  The blade hangs from a 5.5 mm boss near the top edge of the front plate; its tab reaches
//     over the top of the camera.  The tab is 7 mm from the pivot and the lens is 28.5 mm from it, so the blade's window
//     crosses the lens four times as fast as your finger moves.  The click spring is the blade's own rim: a 1.8 mm beam,
//     28 mm long, with a bump that drops into three notches: closed, open (time exposures, pinhole), closed.
//   * Aperture wheel: S (sun), C (cloud), T (a 1 mm hole for time exposures on a stand); the same kind of rim spring clicks it into place.
//     None of the holes is a pinhole.  The pinhole experiment (v2.16): the lens comes out, and a thin metal pinhole disc goes on the lens seat in its place,
//     clamped by the pinhole ring (PART = "pinring", "pindisc").
//   * The front plate slides on from above: four hooked feet, one click.  Press the tab, slide it up, and the whole shutter is in your hand.
//   * Every part that bends was sized with a finite-element model (tools/fea_cases.py); every part was sliced and the
//     tool paths compared with the model (tools/printsim.py).
//   * No finder: sights.  The wedge on the top shows how wide the picture is (sight along its edges, aim along its groove); the wedge on each end how tall.
//
// Layout numbers (film path, pivot, wheel) come from tools/layout.py -> layout.scad.
include <layout.scad>

/* [View] */
PART      = "asm";    // asm | body | back | front | blade | wheel | roller | knob | spool | p_<part> (print layout) | p_test | film | cassette | lens
EXPLODE   = 0;        // 0..1
PHI       = THETA_S;  // blade angle: -THETA_S (closed) .. 0 (open) .. +THETA_S (closed)
STOP      = 2;        // aperture wheel: 0 = small dot (f/16), 1 = middle dot (f/11), 2 = large dot (f/9.5; also the one for the pinhole experiment)
KNOB_LIFT = 0;        // (knobs no longer lift: each slides in from the back with its cassette or spool)
SLID      = 0;        // front plate: 0 = locked, SLIDE = raised to where it is put on / lifted off
P1_UP     = 0;        // the first plate's slide: 0 = shut, P1_T = lifted (open)
ROLL_UP   = 0;        // frame wheel: ROLL_LIFT = raised to where it goes into / comes out of its fork
SHOW_FILM = true;
SHOW_BACK = true;
SECTION   = false;    // cut the assembly at Z = 0
DARK      = true;     // false: draw the blade in a colour that shows in figures

/* [Bed chamfer, v2.17] */
// A 45-degree chamfer on the outer edges of each part's face on the bed: the first layers spread (elephant's foot), and a chamfer lets them spread into air instead of
// into a fit.  BED_CHAMFER where the edge meets nothing; BED_CH_FIT where it is a fit, a light seal, a sliding face or a click; none where even that is too much.  Per part, as it lies on the bed:
//   body   front face down.  Sides and bottom BED_CHAMFER (nothing there; the plate's edges stand 1.6 mm or more inside).  Top edge none: the plate's top edge lies flush on it
//          (a light seal), and the wall over the plate's upper foot pockets is 2.4 mm there (0.4 more of chamfer left 2.0 at the bed: tools/printrules.py flagged it).
//   back   outer face down.  Outline BED_CHAMFER (the camera's outside).  Latch fingers, their slits and the pads keep their 0.4 mm steps: springs and a catch.
//   front  front face down.  Outline BED_CHAMFER (the camera's front: nothing mates; the feet and the latch are on the other face).  The sight, slits and pocket keep their own steps.
//   plate1 as the front plate.
//   blade  front face down, 1 mm thick, and it slides under the plate's ceiling; its straight edges are the light overlap.  BED_CH_FIT (two layers: 0.4, then 0.2), the
//          same 0.4 as its old bed layer at the overlap.  The click spring and its tooth keep their own 0.3 mm relief: a spring is sized as it is.
//   wheel  back face down, 1 mm thick, slides on the body's face: BED_CH_FIT.  Its click spring keeps its own relief.
//   knob, spool  the knob's top on the bed: nothing touches it.  BED_CHAMFER.
//   pinring  its clamping face down; it is pressed into the crush ribs, so the chamfer is a lead-in.  BED_CH_FIT: the face still clamps the disc 1.9 mm past the port's corner.
//   roller (frame wheel)  none beyond its 0.15 mm step: its bed face is the eight teeth, 0.4 mm wide at the tip, and the teeth are what meets the film's holes.
//   nearring, slide1  none: 0.4 and 1.0 mm thick flat parts whose bed edges are their fits.  Gauges, test slab, tower: none (they show fits as the camera's parts print).
BED_CHAMFER = 1.0; BED_CH_FIT = 0.4;

/* [Film and body] */
RF = 32; CF = [0, 32];                      // drum radius and its centre (the lens stop sits on this axis)
GATE_A = 18 / RF * 180 / PI;                // half-angle of the 36 mm frame
GATE_Z = 12;
FILM_W = 35; FILM_T = 0.13;
RAIL_IN = 15.6;                             // rails carry only the 2 mm margin outside the perforations
ZS = 17.9;                                  // half height of the film slot (film 35 wide)
DOOR_T = 3.0;
RCH_C = 13.1; WALL_E = 5.6;                   // end walls: as thick as the top and bottom walls, so the same two steps go all the way round
BXL = -CASS[0] + RCH_C + WALL_E; BXR = SPOOL[0] + RCH_S + WALL_E;
ZC0 = -22.4; ZC1 = 22.6; HUB_Z = -26.2;      // cassette / spool chamber floor and ceiling, bottom of the hub slots
XLIP = LIP_TIP[0] + 1.5;                    // the tall cassette cavity ends here
YB_L = 10.0; YB_R = 13.4;                   // rear face of the block beside the drum (left / right)
R_G = 3.0;                                  // fixed film guide on the back
TOOTH = 1.2;
// Light seal: two steps that nest (no tongue, no groove).  Seen from outside inward, the body's rim is: a lip LIP_W wide at full height, a tread STEP_H lower,
// and inside that the rim is 2 x STEP_H lower.  The back carries the same stair the other way up: a low step and, inside it, a band BAND_W wide.
// Light has to turn four corners.  The steps are the SAME height on both parts, so with the back pressed home every tread is closed, not only the outer edge:
// that matters more than anything else here (tools/sealsim.py: 0.2 mm of slack on the treads lets through several hundred times more stray light; one step
// instead of two, a thousand times more).  Heights are whole layers on both parts, so a printer keeps them.
// Nothing here is thinner than 2 mm, each step is 1.3 mm or more wide, and no wall is left standing inside the band: the low part runs on LAP_IN further and opens into the chambers.
LIP_W = 1.8; TREAD_W = 1.4; BAND_W = 1.8; LAP_G = 0.6; FIT = 0.65; STEP_H = 1.2; LAP_IN = 1.9;
// v2.7: 0.6 mm of room beside each riser (it was 0.3: the back bound on a printer 0.2 fat); lip and band are four 0.45 mm lines.  FIT: room beside every block, bar, shaft and ring that goes into a slot (it was 0.4)
RING_IN = LIP_W + TREAD_W + LAP_G + BAND_W / 2; ZR_OUT = H - RING_IN; ZR_IN = ZS + BAND_W / 2; XJ_L = -25.8; XJ_R = 17.2;   // the band's centre line: 4.6 mm inside the edge; between the latches it dips to the edge of the film slot
TOL = 0.2;
BAND_H = 2 * STEP_H; ZB_TOP = ZR_OUT + BAND_W / 2 + LAP_G;      // how high the seat of the seal band reaches in the body's top wall (24.9)
SAD_Z = 17.4; SAD_BAND = 12.6;                // the film block on the back: half its height, and where its two proud bands begin (the picture is 12 mm either side of the middle)
// The frame wheel (it replaces the tall sprocket roller): a short drum with eight teeth that the film turns once per picture, a neck, a collar and a dial.
// It prints with its teeth flat on the bed.  It stands on the flat top of the film guide (the nose) and its neck turns in ONE solid fork on the back: lift it
// 2.5 mm, pass its neck through the mouth, lower it: its collar now sits in the round seat behind the fork's lips.  In the camera a ledge of the body (SLOT_Z)
// keeps it down.  The film pushes the wheel toward the back: the fork's floor carries that (0.4 mm of room round the neck), and the end of the slot in the
// body's top steadies the neck 9 mm higher up.  Nothing rests on a cone or an edge: every seat is a flat face or a round hole.
// Below it, a fixed nose on the back guides the film; the wheel carries the film's top band and counts.
WH_Z = [13.4, 15.9]; TOOTH_Z = 1.5;                                             // the wheel's drum.  Its teeth are the lowest 1.5 mm (13.4 to 14.9): the top row of perforations is 12.7 to 15.5, so 0.6 mm to spare each side
SHAFT_R = 3.0; SHAFT_CL = 0.65; COLLAR_R = 4.6; COLLAR_Z = [22.0, 22.8]; ROLL_LIFT = 2.7; SLOT_Z = COLLAR_Z[1] + 0.6;   // neck 6 mm, collar 9.2 mm (1.1 mm wider all round than the hole in the wall over it: what comes down that hole lands on the collar).  ROLL_LIFT = the room above the drum; 2.2 mm of lift frees the wheel (2.5 on the fattest printer)
RB_HW = 7.1; RB_HWL = 8.7; RB_SEAT = COLLAR_R + 0.5; RB_GAP = 2 * SHAFT_R + 1.0; RB_UP = 5.2; FW_LAP = 1.0; RB_Z = [WH_Z[1] + ROLL_LIFT + 0.1, COLLAR_Z[1]]; RB_FLOOR = COLLAR_Z[0] - (COLLAR_R - SHAFT_R) - 0.2;   // the fork: 15.8 mm wide.  Its prong on the latch side (RB_HWL) is 3.7 mm thick or more and stands alone; the one on the spool side (RB_HW) is joined to the spool block's foot; its floor is 0.2 below the wheel's cone.  The floor part is FW_LAP shorter in front than the part over it: it laps over a step in the body
NOSE_BAND = 0.4; NOSE_MID = 1.6; NOSE_TOP = WH_Z[0] - 0.26;                      // the nose: its bottom band carries the film 0.4 inside the drum's radius (where the loaded wheel settles on a typical printer); its middle is 1.6 inside and touches nothing; its top is the wheel's seat
DIAL_R = 6.0; RIDGE_R0 = SHAFT_R + SHAFT_CL; RIDGE_H = 1.7; DIAL_Z = [H + 0.2 + DIAL_R - SHAFT_R, H + 1.6 + DIAL_R - SHAFT_R];   // the dial stands on a 45-degree cone, so the wheel prints without support
CONE_Z0 = COLLAR_Z[0] - (COLLAR_R - SHAFT_R); FW_KSW = 2.8; FW_NK = 2.0; FW_LZ = COLLAR_Z[1] + ROLL_LIFT - 0.1;                // the slot for the wheel's neck in the body's top: from FW_LZ up (above where the lifted collar comes) it is wider behind the neck, like the knob slots, and a wide bar on the back closes it right up to the neck

/* [Front stack, back to front] */
// Every thickness in the front stack is a whole number of 0.2 mm layers, so a slicer cannot round a clearance away.
Y_WH0 = Y_FRONT + 0.05; Y_WH1 = Y_WH0 + 1.0;   // wheel, 5 layers; its front face is the stop plane
Y_SC0 = Y_WH1 + 0.2; Y_SC1 = Y_SC0 + 1.0;     // blade, 5 layers, one layer clear of the wheel
LENS_SEAT = 1.0;                            // how far the lens seat stands in front of the shutter pocket.  THE focus setting.  v2.14: 1.0, not 0.8 (tools/focus.py): at 0.8 the film stood only 0.08 mm behind
                                            // the lens's far-subject focus, so the camera was set for about 13 m, not the 3.8 m intended; one layer more sets it for 3.7 m.  One layer (0.2) is the step: see the focus check
assert(LENS_SEAT >= 0.6 && LENS_SEAT <= 1.4, "LENS_SEAT: 0.6 to 1.4.  Below, the seat's floor is too thin to bridge; above, the crush ribs no longer hold the lens.  This body takes a 32 mm lens.");
Y_CV0 = Y_FRONT + 2.4; Y_SEAT = Y_CV0 + LENS_SEAT; Y_CVF = Y_CV0 + 2.6;   // front plate: pocket 12 layers deep, lens seat, front face
HOLE_COMP = 0.15;                           // small holes print small (tools/printsim.py): they are drawn this much larger, on radius.  Nothing is reamed.
PORT_CV = 3.15; WIN_R = 2.8; PORT_H = 3.4;  // PORT_H: half width of the lens port (a slot, a square, an octagon: it bridges with nothing to poke out)
R_IN = R_PORT - PORT_CV - OVERLAP;
// pivots are stout bosses on the front plate: nothing thinner than 4.7 mm turns anything
BOSS_R = 2.75; HUB_HOLE = BOSS_R + HUB_C; HUB_R = 5.4;   // blade: 0.5 mm of room on the boss (HUB_C): it cannot seize even with every wall 0.25 mm fat.  The play does no harm: see the click, below
WBOSS_R = 2.35; WHOLE = WBOSS_R + HUB_C;                  // wheel: a plain 4.7 mm post (no shoulder: the slab over the wheel and the blade keep it flat)
// finger tab: rises past the top edge of the plate and reaches back over the top of the body
AIM_R = 0.7;      // the engraved lines on the top are 1.4 mm wide
RK_LX = 1.14 - AIM_R;      // the rocker's left side is this much longer: lying down, its end is on the lens's line and serves as the sight
FIN_W = 11.0; FIN_L = 6.0; RK_L = 13.0; RK_T = 3.15;     // shutter rocker: a shallow V on top of the hub.  Press the raised side flat.  The arm is 8 mm wide where it comes up through the plate; each side is 10.5 x 5 mm
FIN_CLR = 1.8; RK_V = (H + FIN_CLR - P_S[1] + RK_L * sin(1.2)) / cos(THETA_S + 1.2);   // the side that is down lies FIN_CLR above the body, even against a stop
RK_REACH = RK_L + RK_V * sin(THETA_S);                           // how far the flat side reaches from the pivot (14.9)
// v2.10 sights.  The film's edges are GATE_A either side of the lens's axis and atan(GATE_Z / RF) above and below it.  A straight edge that runs in one of those directions points at the
// same place in the picture wherever the eye is (its vanishing point), so the sights are edges, as long as the camera allows:
//   on the top, two rails in a V, SG_H high and SG_RW wide, from the rear rim to SG_Y1, 4.5 mm short of the front face (where the rocker reaches back over the top); each ends in a
//   45-degree ramp.  Their outer sides are the left and right edges of the picture; the notch where they come together at the rear is the aiming point.  The V lies left of the
//   rocker (the rocker's raised side stood in the way of the old lines) and 3 mm clear of the wind knob.  Each rail leans 32 degrees as it is printed, and its ramp is where it starts: no support.
//   on each end, a wedge sunk SE_D into the wall: its two sides are the top and bottom edges of the picture.
SB_L = 3.0; SB_TOP = 1.0; SB_Y1 = 23.0; SB_ZERO = 2800;   // SB_ZERO: the distance at which the line of sight crosses the lens's own line (the blade's top is lower than the rails' by SB_DROP)
//      // front sight: a blade on the V's middle line, this long, this wide at its top (2.4 at its foot)
SG_X = -2.0; SG_H = 2.4; SG_RW = 2.4; SG_W0 = 6.4; SG_Y0 = Y_RIM + 5.0; SG_Y1 = 18.0;    // top rails: where the V's middle is, their height and width, the V's width at the rear end, where it starts, where its full height ends
SB_DROP = (SB_Y1 - SB_L - SG_Y0) * (H + SG_H) / SB_ZERO;
SE_D = 0.6; SE_W0 = 4.0; SE_Y0 = Y_RIM + 2.0; SE_Y1 = Y_FRONT - 2.5;        // end wedges: depth, width at the rear end, from .. to
GATE_V = atan(GATE_Z / RF);                                                  // half the picture's height, seen from the lens (20.6 degrees)
HND_UP = 3.5;                               // aperture handle: stands this far proud of the plate
// knobs: the shaft and its collar slide into a T-slot from the back; a block on the back closes the slot.  A knob cannot be pulled out or fall out.
KN_R = 4.5; KN_CR = KN_R + 1.2; KN_CZ = [ZC1 + 0.3, ZC1 + 1.3]; KN_PZ = [ZC1 - 0.01, ZC1 + 3.1];   /* v2.14: 3.1, not 2.8.  On the fattest printer the top wall is 0.5 mm thicker; the knob rides up 0.3 on it and the cone over its ring met the pocket's ceiling.  Now it has 0.3 to spare */ SP_KR = CORE_R; SP_KCR = SP_KR + 1.2; KSW = 2.8; KN_SC = 0.65; KN_NK = 1.6; KN_LZ = ZB_TOP; KEEL = [SPOOL[0] - ROLLER[0] - RB_HW - 0.85, RCH_S - FIT];   // knob shaft, its ring (1.2 mm proud), where the ring's flat part sits, and the lower half of the 5.6 mm top wall, which is the ring's channel: no thin fin above or below it.  KSW: how much wider than the shaft the slot is higher up, each side; KN_NK: how far behind the shaft's centre it widens; KN_LZ: from what height; KN_SC: how close the block comes to the shaft
// click springs (v2.7): the outer rim of the blade (and of the wheel) is a beam with a round-tipped tooth at its free end that sits in a
// 45-degree V.  All the sizes come from tools/layout.py, where the reasoning is.  In short: between two printed parts a click is a tab in a
// slot, so how far the tooth is pushed in moves with FOUR times the printer's wall error while the spring's own push seats the hub (at rest).
// While the rocker is pressed the finger seats the hub the other way: the blade hangs on its boss and the error cancels.  So:
//   at rest the blade's tooth is pushed in 0.8 mm + 4 x the error (0.2 on a printer 0.15 thin, 1.8 on one 0.25 fat): it only holds the blade shut;
//   pressed, it is pushed in 1.8 mm on every printer: that sets how hard the click is, and so the shutter's time.
// The hub holes are drawn HUB_C off-centre, away from the tooth: as drawn each part is at rest and its tooth just touches both ramps.
// A fat printer's spring is bent a little at rest (it relaxes with time, toward 'just touching'); a thin printer's tooth has up to 0.6 mm of slack.
SPR_RAMP = 45;
RWB = R_OUT + BL_SLIT + BL_T + BL_CL;       // click wall for the blade: only as tall as the blade, so the wheel passes under it
RWW = WHEEL_R + WH_SLIT + WH_T + WH_CL;     // click wall for the wheel
WH_HC = pol(WHEEL_C, -(HUB_C - 0.02), WD_A0);   // centre of the wheel's hub hole
WIN_IN = 0.85 * (2 * HUB_C - 0.1);              // (0.85: the share of the drop that is across the window's path; - 0.1: a printer 0.05 fat, the middle of the range, leaves that much less play.  tools/exposure.py)
BL_HC = pol(P_S, -(HUB_C - 0.02), DB_A);        // centre of the blade's hub hole (in the blade's own frame, at mid-swing)
PORT_FW = [4.3, 2.6];                       // body port radius at its back / front
// STOP_R (tools/layout.py): what the three holes should come out as: 2.0, 2.9 and 3.4 mm, f/16, f/11 and f/9.5 (v2.14; the large one was 4.0, f/8).  One stop apart: the full-sun opening for ISO 400, 200 and 100 film
// at about 1/300 s.  Duller light: one or two holes larger.
DOT_R = STOP_R;                             // three dots beside the aperture handle, small to large: each is the size of the hole behind it.  There is no lettering on any part
LENS_D = 12.0; LENS_FL = 0.88;              // flange of the salvaged lens: use the lens gauge
// slide-and-click mount.  The plate is set on SLIDE higher and slid DOWN until it clicks: four hooked feet, one latch.  Down is the way every press on the
// shutter pushes the plate and the way it hangs, so in use it sits hard on its stops whatever the latch's play.  (Up to v2.5 it slid sideways: it could rest
// anywhere within the latch's play, and half a millimetre of play there let the plate, and the lens on it, stand 0.6 mm off the body.)
SLIDE = 4.4; FOOT_L = 3.6; FOOT_W = 6.4; FOOT_D = 4.4; FOOT_TIP = 2.4; LIP = 1.6; FOOT_EDGE = 2.0; PL_GY = 0.25; PK_X = 0.7;     // feet 6.4 mm wide and 4.4 tall; the hook's tip is 2.4 mm thick (the hook's slope is as it was).  PL_GY: how far the plate could be pulled off its seat; PK_X: room beside each foot in its pocket
// v2.10: TWO moves to take the plate off, up and then sideways, so that one knock cannot do it (tools/platefall.py).  Up to v2.9 the hooks let go after 1.7 mm of sliding up, and a fall onto
// the knobs or the top's rear edge threw the plate off: the body stops, the plate keeps going, and its latch only has a few newton millimetres to stop it with.  Now each foot also has a lip on
// its right side (SIDE_L long, the hook's own slope), under a second strip of the body's skin that runs the whole height of its pocket: slid up, the plate still cannot come off.  Only where it
// has gone up XUP (the feet stand above a wall ZW high) can it be slid XA sideways, out from under those strips, and lifted off.  At home nothing has changed: the four hooks, their stops, the
// wedge that seats the plate and the latch are as they were; the side lips touch nothing (SIDE_G of room).  It goes on the same way back: on high and to the side, across, down until it clicks.
SIDE_L = 3.2; SIDE_G = 0.8; XA = 3.6; ZW = 2.2; PK_TOP = 1.0; FOOT_CH = 1.0; PK_D = FOOT_D + 0.8; XUP = ZW + LIP;      // side lip; its room; how far the pocket runs on sideways at its top; the wall under that part; room over the foot at the top of its travel; how deep the pockets are (0.8 mm more than the feet: their roofs are bridges 10.6 mm long); the plate has to go up XUP = 3.8
FEET = [[FX0 + FOOT_EDGE + 2.4, FZ0 + 2.3], [FX1 - FOOT_EDGE - FOOT_W, FZ0 + 2.3], [FX0 + FOOT_EDGE + 2.4, FZ1 - 11.5], [FX1 - FOOT_EDGE - FOOT_W, FZ1 - 11.5]];   // [x of the foot's left side, z of its hooked face].  All four hooks point down.  The top two leave 2.5 mm of wall above their pockets (they stand 0.3 mm lower than in v2.9: their pockets are 0.3 mm taller).  (The two left feet stand 2.4 mm further in than in v2.9: their pockets now run on 3.6 mm to the left)
// v2.8 latch of the front plate.  tools/endcases.py: v2.7's upright tongue engaged SIDEWAYS, and the plate floats sideways on its feet (0.7 mm less twice the wall error), so a printer
// 0.15 thin left it nothing to hold with, and on one 0.25 fat the tooth could not get past its bump.  Now a LEAF lying in the plate's front face: 7 layers thick, free on three sides,
// with a post on its free end that reaches TOOTH_H = 10 layers behind the plate into a channel in the body.  As the plate slides down, the post's round end rides up a ramp and drops
// behind it.  Leaf thickness, reach and the height of the bump are all counted in LAYERS, which every printer gets right; wall error only makes the leaf a little wider or narrower.
LF_X0 = 27.0; LF_X1 = 31.6; LF_T = 1.6; LF_G = 1.0;         // the leaf: 4.6 mm wide, 1.6 thick (8 layers); the slit round it
LF_ZR = -19.1; LF_ZH = 5.6; LF_PL = 3.0; LF_FG = 1.4;        // its root; the middle of its post (plate at home); the post's length along the leaf; the gap beyond its free end (the post tips as the leaf bends).  (v2.10: the whole leaf sits 2 mm lower, so that its channel, now 1.6 mm longer, keeps 1.8 mm of wall under the pocket above it)
// v2.9: the leaf points UP from its root (it pointed down).  The bump pushes on the post 5 mm behind the leaf, and that push turns the leaf's end as well as lifting it (tools/fea_cases.py:
// 1 N along the slide counts as 0.38 N of lift, with or against).  Pointing down, the push that takes the plate off helped the post out, and the push that puts it on held the post in:
// the plate came off at half the force worked out in round 4 and took five times the force to put on.  Pointing up it is the other way round.
LF_R = 0.8; TOOTH_H = 2.0;                                  // the post's round end; how far it reaches behind the plate
LF_DB = 0.4; LF_DE = 2.4;                                   // the channel in the body: 2 layers deep over the bump, 12 elsewhere: the post has to rise 1.6 mm (the leaf is 25 mm long so that this strains it 0.85 % at most)
LF_RAKE = 38; LF_RAMP = 54; LF_TOP = 0.4; LF_SL = -0.1;   /* v2.14: the bump's top is 0.4 wide, not 0.8, and the side the post climbs lies back at 54 degrees, not 62: the same bump in the same place, but the push to click the plate on is about half (tools/snapcurves.py).  The side that holds is untouched */                    // the bump: the side that holds (measured from the direction of sliding), the side the post climbs on the way in; play at home
LF_ZB = LF_ZH + LF_PL / 2 + LF_FG;                          // far side of the gap beyond the leaf's free end
LF_ZC0 = LF_ZH - LF_R - 0.9; LF_ZC1 = LF_ZH + SLIDE + 1.6 + LF_R + 0.9;       // the channel's two ends (v2.10: 1.6 mm longer at the top: the plate can go up further before its feet meet the tops of their pockets, on a thin printer 6 mm)
function leaf_cut_yz() = let(zr0 = LF_ZH + LF_SL + 0.04, zr1 = zr0 + (LF_DE - LF_DB) / tan(LF_RAKE), zt1 = zr1 + LF_TOP, ze1 = zt1 + (LF_DE - LF_DB) / tan(LF_RAMP), zc0 = LF_ZC0, zc1 = LF_ZC1)
    [[Y_FRONT + 0.01, zc0], [Y_FRONT - LF_DE, zc0], [Y_FRONT - LF_DE, zr0], [Y_FRONT - LF_DB, zr1], [Y_FRONT - LF_DB, zt1], [Y_FRONT - LF_DE, ze1], [Y_FRONT - LF_DE, zc1], [Y_FRONT + 0.01, zc1]];   // the channel's side view (y, z)
// legend engraved on the back: [text, x, z, align].  Few words, 5.5 mm tall, three layers deep: small text does not survive a first layer.
// (no legend on the back: engraved letters on the bed face are the feature most likely to print badly)
FORK_GAP = 2.3; FORK_R = 3.3; FORK_Z0 = 19.4;          // wind knob: a 6.6 mm round end (v2.9; it was 6.2) with a 2.3 mm slot across it, for the bar inside the cassette's spool.  7.1 mm on the fattest printer.  The key gauge is still the check: 3.1 fits a tighter hole
WIND_HEAD = 9.5;                                        // the wind knob is the smaller of the two: it needs little force.  19 mm across: even between two teeth, and with the back standing 1 mm off, it covers the gap in front of the block that closes its slot
TAKE_HEAD = 10.5; WIND_CW = true; TAKE_CW = false;                        // 21 mm across, for the same reason.  Which way each knob turns, seen from above: the saw teeth show it
JRN_R = 4.3;                                // take-up spool: no flange at all; a plain journal at the bottom.  One piece: no cap, no thread
LEDGE_Z = [ZS, ZC1 + 0.01]; LEDGE2_Z = [ZC0 - 0.01, -ZS];   // two solid steps in the take-up chamber (its ceiling and floor come in to the film slot's level over the front half): the roll rests on the lower one and cannot climb past the upper one.  They were 1.6 mm ledges
SP_T = ZC0 + 44.1; SP_B = HUB_Z + 0.3; SP_F = 17.75;      // printed take-up spool: top end, hub end, inner faces of its flanges
// latch of the back (top; the bottom one is its mirror).  A finger cut in the edge of the back, pressed at its tip; its nub comes up behind a bar on the body.
HORN_T = 2.2; F_X0 = -18.2; F_X1 = 16.5; F_Z1 = H - HORN_T - 0.02; F_T = 1.3; F_Z0 = F_Z1 - F_T; DOOR_TOP = 21.58; F_SLIT = F_Z0 - DOOR_TOP; NUB_X0 = -17.8; NUB_X1 = -15.8; NUB_H = 1.6; F_DROP = 0.8;
// v2.8 (tools/endcases.py): v2.7's finger lay against the catch along its whole length.  Near its root a finger cannot give way, so any printer more than 0.01 mm fat jammed the back,
// and the pad at the tip moved 1.7 times as far as the nub, so the slit closed before the nub was clear.  Now: the nub is AT the tip and the pad 8 mm inboard of it (the tip moves no further
// than the nub); the finger is 35 mm long, 1.3 thick, and slopes F_DROP down toward its root, so it meets the catch only beside the nub, where it can bend; the slit is 3.1 mm.
// The slit cannot reach further left than x = -23: there the door's top edge covers the cassette chamber's opening.
// DOOR_TOP: the edge under the slit covers the entrance of the light trap and stays where it was.
// A finger cut from a 3 mm plate is soft SIDEWAYS: pulled off without the pads, the back bends its fingers front to back.  So the 15 mm next to each finger's root carry a rib
// RIB_H high on the inside, which runs in a groove in the body's rim (RIB_Z: the groove, above the light trap's entrance).  That part hardly moves when the pad is pressed.
RIB_X0 = 1.0; RIB_H = 0; RIB_Z = [23.0, 26.3];
// v2.9 (tools/abuse.py, the covers in a fall): the rib is gone (RIB_H = 0) and the catch stands 1.4 mm proud of the back, not 2.4.  When the camera is put down on its back the catch lands first
// and the back travels on until the table meets it; the nubs are held, so the fingers are bent front to back by that travel less the 0.4 mm of slack.  With the rib that was 2.0 mm and 1.7 % strain,
// from any fall of 34 mm.  A plain finger takes twice the travel for the same strain, and the travel is now 1.0 mm: 0.4 %.  The price: pulled without its pads the back gives at 3.6 N, not 5.5.
// The two fingers, top and bottom, so centre the back between the catches, and each nub stands NUB_H above its finger's top: how far it reaches up behind the bar is then the same on every printer
// (a step on one part against a step on the other), instead of moving with four times the wall error.  A fat printer's fingers stay bent a little (they relax); a thin printer's leave up to 0.3 mm of play.
//     // finger 1.8 mm thick, 36 mm long: the nub is 25 mm from its root, so it bends half as hard as the 1.4 x 25 mm finger of v2.4
PAD_X0 = -10.8; PAD_X1 = -0.7; PAD_UP = 1.8;               // both pads stand 1.8 mm proud, between the tab and the inner post of the catch: pinch them.  (v2.10: 5.6 mm wide, they were 3.4: the width of a child's fingertip.  The catch's tab is 2.2 mm shorter for it.)  Pressed level with the catch they have moved far enough on every printer.  (The camera stands on two skids, so the table cannot press the bottom one.)
// the catch on the body: a 4 mm post, a 23 mm wide tab, and a bar bridging them.  2.6 mm thick, rounded where it joins the rim (finite-element checked).
SIGHT_DROP = (Y_CVF + 4.5) * (H + PAD_UP) / 2800;     // the front point is this much lower than the top pad's top, so that the line over both meets the lens's line 2.8 m away
OP_X0 = -22.4; OP_X1 = -18.4; ARM_X0 = -15.2; ARM_X1 = -11.6; HORN_X0 = 0.1; HORN_X1 = 14.0; HORN_GAP = 0.4; HORN_L = DOOR_T + HORN_GAP + 1.0; HORN_LEAD = 0.7; HORN_RF = 0.8;   // two posts (4 and 3.6 mm) with the bar between them, and an 18 mm tab that takes the knocks.  None is rounded where it joins the rim any more: the finger passes right under them, and a rounded root left it no room on a fat printer (v2.7 cut the finger's edge away to make room).  Instead their rear lower edge is bevelled HORN_LEAD, so the finger finds its way under them.  Only the outer post, which stands over the door's fixed edge, keeps a rounded root.  HORN_GAP: two whole layers (0.25 was a quarter layer: what printed depended on rounding)
SKID = 2.2; CORNER_R = 5;                                    // v2.7: the four long edges of the box are rounded 5 mm (they were 3): friendlier in the hand.  The seal's lip is still 2.1 mm thick at the corners                                                  // height of the two skids under the body

$fa = 4; $fs = 0.4;

// ------------------------------------------------------------------ helpers
function pol(c, r, a) = [c[0] + r * cos(a), c[1] + r * sin(a)];
function arcp(a, r = RF) = [r * sin(a), CF[1] - r * cos(a)];       // point on the drum at film angle a (0 = frame centre)
module ey(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();    // 2-D (x,z) -> y0..y1
module ez(z0, z1) translate([0, 0, z0]) linear_extrude(z1 - z0) children();                        // 2-D (x,y) -> z0..z1
module rot_xz(c, deg) translate([c[0], 0, c[1]]) rotate([0, -deg, 0]) translate([-c[0], 0, -c[1]]) children();
module cyl_y(p, r, y0, y1, r1 = undef) translate([p[0], y1, p[1]]) rotate([90, 0, 0]) cylinder(r1 = is_undef(r1) ? r : r1, r2 = r, h = y1 - y0);
module rrect2(p0, p1, r) hull() for (x = [p0[0] + r, p1[0] - r], y = [p0[1] + r, p1[1] - r]) translate([x, y]) circle(r);
module arc_slot(c, r, a0, a1, hw, n = 24) for (i = [0 : n - 1]) hull() {
    translate(pol(c, r, a0 + (a1 - a0) * i / n)) circle(hw); translate(pol(c, r, a0 + (a1 - a0) * (i + 1) / n)) circle(hw); }
module slot_plan(c, hw) { translate(c) circle(hw); translate([c[0] - hw, Y_RIM - 1]) square([2 * hw, c[1] - Y_RIM + 1]); }
RING = [[-BXL + RING_IN, ZR_OUT], [XJ_L, ZR_OUT], [XJ_L, ZR_IN], [XJ_R, ZR_IN], [XJ_R, ZR_OUT], [BXR - RING_IN, ZR_OUT],
        [BXR - RING_IN, -ZR_OUT], [XJ_R, -ZR_OUT], [XJ_R, -ZR_IN], [XJ_L, -ZR_IN], [XJ_L, -ZR_OUT], [-BXL + RING_IN, -ZR_OUT]];
module ringpoly() offset(r = -1.2) offset(delta = 1.2) offset(r = 1.2) offset(delta = -1.2) polygon(RING);     // every corner of the seal's path is rounded: the lip outside it keeps its thickness round the body's corners
module ring2d(w) difference() { offset(delta = w / 2) ringpoly(); offset(delta = -w / 2) ringpoly(); }
module lap_step2d(out) {                                         // what is cut from the body's rim: everything from `out` outside the band's centre line inward
    difference() { offset(delta = out) ringpoly(); offset(delta = -BAND_W / 2 - LAP_IN) ringpoly(); }
    for (s = [0, 1]) mirror([0, s]) for (x = [XJ_L - BAND_W / 2 - LAP_IN, XJ_R - 1.2]) translate([x, ZS - 0.01]) square([BAND_W / 2 + LAP_IN + 1.2, ZR_IN + 1.2 - ZS]);   // the four inside corners where the band steps down: cut square, so no sliver is left beside the chambers
}

// ================================================================== BODY (one print, front face down)
A_DL = asin(sqrt(RF * RF - pow(CF[1] - YB_L, 2)) / RF);        // where the drum meets the side shelves
A_DR = asin(sqrt(RF * RF - pow(CF[1] - YB_R, 2)) / RF);
module film_slot_plan() {
    te = 180 - asin((YB_R - SPOOL[1]) / RCH_S);
    polygon(concat([[XLIP, Y_RIM - 1], [SPOOL[0] + RCH_S, Y_RIM - 1]],
                   [for (t = [0 : 4 : te]) pol(SPOOL, RCH_S, t)], [pol(SPOOL, RCH_S, te)],
                   [for (a = [A_DR : -1.5 : -A_DL]) arcp(a)], [arcp(-A_DL), [XLIP, YB_L]]));
}
module cass_plan() {
    translate(CASS) circle(RCH_C);
    translate([CASS[0] - RCH_C, Y_RIM - 1]) square([2 * RCH_C, CASS[1] - Y_RIM + 1]);
    translate([CASS[0], Y_RIM - 1]) square([XLIP - CASS[0] + 0.01, YB_L - Y_RIM + 1]);
}
module funnel() hull() {                                        // taking-light cavity: gate -> port
    for (a = [-GATE_A - 0.6, -(GATE_A + 0.6) / 2, 0, (GATE_A + 0.6) / 2, GATE_A + 0.6], r = [29, 32.3], z = [-GATE_Z - 0.3, GATE_Z + 0.3])
        translate([r * sin(a), CF[1] - r * cos(a), z]) cube(0.02, center = true);
    cyl_y([0, 0], PORT_FW[0], Y_FRONT - 2.4, Y_FRONT + 0.1, PORT_FW[1] - 0.06);
    translate([-13, 12, -9.5]) cube([26, 0.5, 19]);
}
module horn(s) scale([1, 1, s]) difference() {                   // catch for the back's latch (s = 1 top, -1 bottom)
    yc = Y_RIM - DOOR_T - HORN_GAP;
    union() {
        for (x = [[OP_X0, OP_X1], [ARM_X0, ARM_X1], [HORN_X0, HORN_X1]]) translate([x[0], Y_RIM - HORN_L, H - HORN_T]) cube([x[1] - x[0], HORN_L + 0.01, HORN_T]);   // two posts and the tab
        translate([OP_X1 - 0.01, Y_RIM - HORN_L, H - HORN_T]) cube([ARM_X0 - OP_X1 + 0.02, yc - Y_RIM + HORN_L, HORN_T]);    // bar: a 3 mm bridge between the posts; the nub comes up behind it
        translate([OP_X0, 0, 0]) rotate([90, 0, 90]) linear_extrude(OP_X1 - OP_X0) translate([Y_RIM, H - HORN_T])              // the outer post is rounded where it joins the rim
            difference() { translate([-HORN_RF, -HORN_RF]) square([HORN_RF, HORN_RF + 0.01]); translate([-HORN_RF, -HORN_RF]) circle(HORN_RF, $fn = 32); }
        translate([0, 0, H - HORN_T]) linear_extrude(HORN_T) {                                                              // its two inside corners are rounded
            translate([OP_X1, yc]) difference() { translate([-0.01, -0.01]) square(0.61); translate([0.6, 0.6]) circle(0.6, $fn = 24); }
            translate([ARM_X0, yc]) difference() { translate([-0.6, -0.01]) square(0.61); translate([-0.6, 0.6]) circle(0.6, $fn = 24); }
        }
    }
    exx(OP_X0 - 1, HORN_X1 + 1) polygon([[Y_RIM - HORN_L - 0.01, H - HORN_T - 0.01], [Y_RIM - HORN_L + HORN_LEAD, H - HORN_T - 0.01], [Y_RIM - HORN_L - 0.01, H - HORN_T + HORN_LEAD]]);   // lead-in for the finger and its nub
}
// v2.7: a low ridge round the hole for the frame wheel, sloped like the underside of the wheel's dial and 0.6 mm from it.  Light that used to fall straight into the
// gap round the neck now has to pass that thin slanted slot first.  The front and sides of the ridge are on the body, the rear on the back's bar.  45-degree faces: no support.
module fw_ridge() translate([ROLLER[0], ROLLER[1], H - 0.01]) rotate_extrude($fn = 72) polygon([[RIDGE_R0, 0], [RIDGE_R0 + RIDGE_H, RIDGE_H], [RIDGE_R0 + 2 * RIDGE_H, 0]]);
module fork_slot_plan() translate([ROLLER[0] - RB_HWL - FIT, Y_RIM - 1]) square([RB_HWL + RB_HW + 2 * FIT, ROLLER[1] + RB_UP + FIT - Y_RIM + 1]);
module shaft_slot_plan() { translate(ROLLER) circle(SHAFT_R + SHAFT_CL); translate([ROLLER[0] - SHAFT_R - SHAFT_CL, Y_RIM - 1]) square([2 * (SHAFT_R + SHAFT_CL), ROLLER[1] - Y_RIM + 1]); }
module tslot_plan(c, r, hw, nk = 0) { hull() { translate(c) circle(r); translate([c[0], c[1] - nk]) circle(r); } translate([c[0] - hw, Y_RIM - 1]) square([2 * hw, c[1] - nk - Y_RIM + 1]); }   // a round seat where the shaft turns, and behind it a straight neck at least as wide as the seat (up to v2.5 the neck was narrower than the shaft: the knobs could not be pushed in)
module spool_plan() { translate(SPOOL) circle(RCH_S); translate([SPOOL[0] - RCH_S, Y_RIM - 1]) square([2 * RCH_S, SPOOL[1] - Y_RIM + 1]); }
function foot_pts(x0, c, s) = [[x0 + FOOT_L + s, Y_FRONT + 0.01], [x0 + FOOT_L + s, Y_FRONT - FOOT_D + FOOT_CH], [x0 + FOOT_L + s - FOOT_CH, Y_FRONT - FOOT_D], [x0 - LIP + FOOT_CH, Y_FRONT - FOOT_D], [x0 - LIP, Y_FRONT - FOOT_D + FOOT_CH],
                               [x0 - LIP, Y_FRONT - FOOT_D + FOOT_TIP], [x0, Y_FRONT - 0.3], [x0, Y_FRONT + 0.01]];     // a foot, side view (z, y): the hook is LIP long, its tip FOOT_TIP thick, a 47-degree slope over it.  v2.10: its far end is chamfered FOOT_CH above and below, so a plate set on too high or too low is led into its pockets
PK_SL = LIP / (FOOT_D - FOOT_TIP - 0.3);                                                             // the slope: how far down per millimetre of depth
function pocket_pts(x0, s) = [[x0 + FOOT_L + s + PK_TOP, Y_FRONT + 0.01], [x0 + FOOT_L + s + PK_TOP, Y_FRONT - PK_D], [x0 - LIP - 0.02, Y_FRONT - PK_D],
                              [x0 - LIP - 0.02, Y_FRONT - FOOT_D + FOOT_TIP + PL_GY - 0.02 / PK_SL], [x0 + (0.31 - PL_GY) * PK_SL, Y_FRONT + 0.01]];
// its pocket: the hook's tip stands on the pocket's floor (that is the plate's stop: both parts print fat or thin the same way there, so only 2 x the error moves the plate);
// the slope over it is the hook's own slope, PL_GY nearer the front: pressing the plate down wedges it against the body.  Everywhere else there is 0.7 mm of room.
function pocket_yz(z0, s) = [for (q = pocket_pts(z0, s)) [q[1], q[0]]];
module exx(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();    // 2-D (y, z) -> x0..x1
function foot_yz(z0, c, s) = [for (q = foot_pts(z0, c, s)) [q[1], q[0]]];                             // a foot's side view: foot_pts gives (z, y)
module rail2d(sd, ya, yb) { xa = sd * (SG_W0 / 2 + tan(GATE_A) * (ya - SG_Y0)); xb = sd * (SG_W0 / 2 + tan(GATE_A) * (yb - SG_Y0)); polygon([[xa, ya], [xb, yb], [xb - sd * SG_RW, yb], [xa - sd * SG_RW, ya]]); }   // one rail of the V on the top, between ya and yb
module sight2d(w0, y0, y1, a) polygon([[-w0 / 2, y0], [w0 / 2, y0], [w0 / 2 + tan(a) * (y1 - y0), y1], [-w0 / 2 - tan(a) * (y1 - y0), y1]]);   // a wedge that opens toward the subject by the angle a either side of its middle
module body() {
    difference() {
        ey(Y_RIM, Y_FRONT) rrect2([-BXL, -H], [BXR, H], CORNER_R);
        ez(-ZS, ZS) film_slot_plan();
        ez(ZC0, ZC1) cass_plan();
        ez(ZC0, ZC1) spool_plan();                                                           // take-up: a bare cassette spool, salvaged or printed
        for (q = [[CASS, KN_R, KN_CR], [SPOOL, SP_KR, SP_KCR]]) {
            ez(HUB_Z, ZC0 + 0.01) slot_plan(q[0], JRN_R + FIT);                                      // the long hub of the cassette / spool slides in here
            ez(KN_PZ[0], KN_PZ[1]) tslot_plan(q[0], q[2] + FIT, q[2] + FIT);                 // knob: it slides in from the back.  Lower half of the wall: a plain straight channel, as wide as the knob's ring ...
            ez(KN_PZ[1] - 0.01, H + 1) tslot_plan(q[0], q[1] + FIT, q[1] + FIT);             // ... upper half: a round seat for the shaft ...
            ez(KN_LZ, H + 1) translate([q[0][0] - q[1] - KSW, Y_RIM - 1]) square([2 * (q[1] + KSW), q[0][1] - KN_NK - Y_RIM + 1]);   // ... and from 2 mm behind the shaft's centre a slot WIDER than the channel under it.
            // So the block that closes the slot is a T: a wide bar over a narrower one.  Every gap beside the narrow bar has the wide bar over it, every gap beside the wide bar has the body under it,
            // and the one gap that opens when the back stands a little off (in front of the wide bar) lies under the knob's head.
        }
        funnel();
        cyl_y([0, 0], 2.9, Y_FRONT - 0.4, Y_FRONT + 0.1);                                    // the port's mouth is on the bed: 0.35 mm wider for two layers, so elephant's foot cannot shade the picture's corners
        ez(-RAIL_IN, RAIL_IN) polygon(concat([for (a = [-A_DL : 1.5 : A_DR]) arcp(a, RF + 0.05)], [arcp(A_DR, RF + 0.05)],
                                             [for (a = [A_DR : -1.5 : -A_DL]) arcp(a, RF - 0.25)], [arcp(-A_DL, RF - 0.25)]));   // only the rails touch the film
        translate([ROLLER[0], ROLLER[1], WH_Z[0] - 0.6]) cylinder(r = R_ROLL + TOOTH + 0.9, h = 3.2);    // room for the frame wheel's teeth (the wheel sits on the back, which can lie 0.4 mm to either side)
        // pocket for the fork that carries the frame wheel (the wheel rides on the back)
        ez(RB_FLOOR - FIT, SLOT_Z) difference() { fork_slot_plan();                          // room for the fork ...
            difference() { translate([ROLLER[0] - RB_GAP / 2 + FIT, ROLLER[1] + COLLAR_R + 0.5]) square([RB_GAP - 2 * FIT, RB_UP + 1]); translate(ROLLER) circle(COLLAR_R + 0.8); } }   // ... but not in the fork's mouth in front of the collar: the body fills that
        ez(ZS - 0.01, RB_FLOOR - FIT + 0.01) difference() {                                        // ... its lowest 2 mm are 1 mm shorter in front: a solid step of the body under the fork's front edge, so that the gap there does not run straight down to the film,
            translate([ROLLER[0] - RB_HWL - FIT, Y_RIM - 1]) square([RB_HWL + RB_HW + 2 * FIT, ROLLER[1] + RB_UP - FW_LAP + FIT - Y_RIM + 1]);
            difference() { translate([ROLLER[0] - RB_GAP / 2 + FIT, ROLLER[1] + SHAFT_R]) square([RB_GAP - 2 * FIT, RB_UP]); translate(ROLLER) circle(SHAFT_R + SHAFT_CL); }   // and lower down the same tongue comes right up to the neck
        }
        ez(SLOT_Z - 0.01, H + 1) shaft_slot_plan();                                          // ... and above it only the neck passes: this ledge keeps the wheel's collar in the fork
        ez(FW_LZ, H + 1) translate([ROLLER[0] - SHAFT_R - FW_KSW, Y_RIM - 1]) square([2 * (SHAFT_R + FW_KSW), ROLLER[1] - FW_NK - Y_RIM + 1]);          // higher up the slot is wider behind the neck: room for a wide bar that wraps the neck
        ez(ZB_TOP - 0.01, FW_LZ + 0.01) translate([ROLLER[0] - SHAFT_R - FW_KSW, Y_RIM - 1]) square([2 * (SHAFT_R + FW_KSW), BAND_H + 1]);              // (at the rim, down to the seal band's seat: no thin skin is left over it)
        ey(Y_RIM - 0.01, Y_RIM + STEP_H) lap_step2d(BAND_W / 2 + TREAD_W + LAP_G);            // first step down, inside the rim's lip
        ey(Y_RIM - 0.01, Y_RIM + 2 * STEP_H) lap_step2d(BAND_W / 2 + LAP_G);                  // second step down: the back's band stands in it
        // front face (recesses only): four pockets for the plate's hooked feet, one for its latch
        for (f = FEET) { xr = f[0] + FOOT_W + PK_X; zt = f[1] + FOOT_L + SLIDE + PK_TOP;
                         exx(f[0] - PK_X, xr) polygon(pocket_yz(f[1], SLIDE));                                                 // the pocket: the foot slides up and down in it; its hook goes in under the skin at the bottom
                         ez(f[1] - 0.01, zt) polygon([[xr - 0.01, Y_FRONT - 0.05], [xr + SIDE_L + 0.3, Y_FRONT - 0.05 - (SIDE_L + 0.3) / PK_SL], [xr + SIDE_L + 0.3, Y_FRONT - PK_D], [xr - 0.01, Y_FRONT - PK_D]]);   // v2.10: room under the skin on its right, the whole height, for the foot's side lip
                         translate([f[0] - PK_X - XA, Y_FRONT - PK_D, f[1] + ZW]) cube([XA + 0.01, PK_D + 0.01, zt - f[1] - ZW]);                                                                    // v2.10: at the top the pocket runs on XA to the left, over a wall ZW high: the way in and out
                         for (k = [0 : 2]) { translate([f[0] - PK_X - 0.1 * (3 - k), Y_FRONT - 0.2 * (k + 1), f[1] - 0.3 - 0.2 * (3 - k)]) cube([FOOT_W + 2 * PK_X + 0.2 * (3 - k), 0.21 + 0.2 * k, zt - f[1] + 0.3 + 0.4 * (3 - k)]);     // the mouths widen in three steps over the first three layers (a chamfer): room for elephant's foot
                                             translate([f[0] - PK_X - XA - 0.1 * (3 - k), Y_FRONT - 0.2 * (k + 1), f[1] + ZW - 0.1 * (3 - k)]) cube([XA + 0.1 * (3 - k) + 0.01, 0.21 + 0.2 * k, zt - f[1] - ZW + 0.2 * (3 - k)]); } }
        if (RIB_H > 0) for (s = [1, -1]) scale([1, 1, s]) translate([RIB_X0 - 0.7, Y_RIM - 0.01, RIB_Z[0]]) cube([F_X1 + 2.6 + 0.7 - RIB_X0 + 0.7, RIB_H + 0.66, RIB_Z[1] - RIB_Z[0]]);   // grooves in the rim for the ribs on the back's latch fingers
        exx(LF_X0 - 0.7, LF_X1 + 0.7) polygon(leaf_cut_yz());                                 // channel for the plate's latch post, with its bump
        intersection() { exx(LF_X0 - 0.7 - XA, LF_X0 - 0.69) polygon(leaf_cut_yz()); translate([LF_X0 - 0.7 - XA - 1, Y_FRONT - 4, LF_ZH + XUP - LF_R - 1.1]) cube([XA + 2, 5, 20]); }   // v2.10: at the top it runs on XA to the left, like the pockets: the post goes sideways with the plate
        for (k = [0 : 1]) { translate([LF_X0 - 0.7 - 0.2 * (2 - k), Y_FRONT - 0.2 * (k + 1), LF_ZC0 - 0.2 * (2 - k)]) cube([LF_X1 - LF_X0 + 1.4 + 0.4 * (2 - k), 0.21 + 0.2 * k, LF_ZC1 - LF_ZC0 + 0.4 * (2 - k)]);   // its mouth is wider on the two bed layers: elephant's foot
                            translate([LF_X0 - 0.7 - XA - 0.2 * (2 - k), Y_FRONT - 0.2 * (k + 1), LF_ZH + XUP - LF_R - 1.1 - 0.2 * (2 - k)]) cube([XA + 0.2 * (2 - k) + 0.01, 0.21 + 0.2 * k, LF_ZC1 - LF_ZH - XUP + LF_R + 1.1 + 0.4 * (2 - k)]); }
        cyl_y([0, 0], PORT_FW[1] + 0.5, Y_FRONT - 0.4, Y_FRONT + 0.1);                       // the port's first two layers are wider: elephant's foot cannot make the port smaller than the largest stop
        // tripod: 1/4"-20 nut pocket (flats face front and back so its roof is a short bridge)
        translate([0, 13, -H - 0.01]) { cylinder(d = 11.4 / cos(30), h = 6, $fn = 6); cylinder(d = 7, h = 8); }
        for (sx = [-1, 0, 1]) hull() for (q = [[sx * 2.4, Y_RIM + 6], [sx * (2.4 + tan(GATE_A) * (Y_FRONT - 4.5 - Y_RIM - 6)), sx == 0 ? Y_FRONT + 1 : Y_FRONT - 4.5]]) translate([q[0], q[1], H - 0.6]) cylinder(r = AIM_R, h = 1, $fn = 8);   // aim lines, as in v2.9: the outer two are the picture's edges; the middle one lies on the lens's line and (v2.10) runs to the front face
        translate([ROLLER[0], ROLLER[1] + RIDGE_R0 + 2 * RIDGE_H + 0.6, H - 0.6]) linear_extrude(1) polygon([[-0.5, 0], [0.5, 0], [1.9, 4.4], [-1.9, 4.4]]);      // index mark for the frame dial (v2.11: an arrowhead pointing at the dial; it was a 1.4 mm line)
        difference() { ey(Y_FRONT - BED_CHAMFER, Y_FRONT + 1) translate([-BXL - 5, -H - 5]) square([BXL + BXR + 10, 2 * H + 10]);       // v2.17: the bed chamfer (front face down): BED_CHAMFER on the sides and the bottom;
            hull() { ey(Y_FRONT - BED_CHAMFER - 0.02, Y_FRONT - BED_CHAMFER) rrect2([-BXL, -H], [BXR, H], CORNER_R);                       // none on the top edge, where the front plate's top edge lies flush on the face (a light seal) and only 2.4 mm stands over the feet's pockets
                     ey(Y_FRONT - 0.01, Y_FRONT + 0.01) rrect2([-BXL + BED_CHAMFER, -H + BED_CHAMFER], [BXR - BED_CHAMFER, H], CORNER_R - BED_CHAMFER); } }
    }
    horn(1); horn(-1);
    difference() { fw_ridge(); translate([ROLLER[0] - RIDGE_R0 - 2 * RIDGE_H - 0.2, Y_RIM - 1, H - 1]) cube([2 * (RIDGE_R0 + 2 * RIDGE_H + 0.2), ROLLER[1] - FW_NK - Y_RIM + 1, 6]); ez(H - 1, H + 5) shaft_slot_plan(); }   // the ridge round the frame wheel's hole (front and sides)
    translate([ROLLER[0], ROLLER[1], 0]) difference() {                                      // v2.7: the tongue in the fork's mouth also follows the collar's cone, in front of the neck
        translate([-RB_GAP / 2 + FIT, SHAFT_R + 0.3, RB_FLOOR - FIT]) cube([RB_GAP - 2 * FIT, RB_UP - FW_LAP - SHAFT_R, COLLAR_Z[0] - RB_FLOOR + FIT]);
        translate([0, 0, RB_FLOOR - FIT - 1]) cylinder(r = SHAFT_R + SHAFT_CL, h = CONE_Z0 - RB_FLOOR + FIT + 1.01);
        translate([0, 0, CONE_Z0]) cylinder(r1 = SHAFT_R + SHAFT_CL, r2 = COLLAR_R + 0.8, h = COLLAR_Z[0] - CONE_Z0 + 0.02);
    }
    for (q = [[LEDGE_Z, CORE_R + 0.7], [LEDGE2_Z, CORE_R + 0.7]])                                                               // solid steps above and under the take-up roll: front half only, so each grows up from the chamber wall as it prints.  (The rear half of the upper one is on the back: the foot of the spool's block)
        ez(q[0][0], q[0][1]) intersection() { difference() { translate(SPOOL) circle(RCH_S + 0.6); translate(SPOOL) circle(q[1]); fork_slot_plan(); }     // (the upper one keeps clear of the pocket for the frame wheel's fork)
                                              translate([SPOOL[0] - RCH_S - 1, SPOOL[1] + 1.0]) square([2 * RCH_S + 2, RCH_S + 2]); }
    for (x = [-BXL + 6.5, BXR - 11.5]) hull() { translate([x, Y_RIM + 2, -H - SKID]) cube([5, Y_FRONT - Y_RIM - 2 - BED_CHAMFER, SKID + 0.01]);   // two skids: they run in the print direction, so they need no support
        translate([x + BED_CHAMFER, Y_FRONT - 0.01, -H - SKID + BED_CHAMFER]) cube([5 - 2 * BED_CHAMFER, 0.01, SKID]); }                     // (v2.17: chamfered at the bed like the body, and up into the body's own chamfer)          // two skids: they run in the print direction, so they need no support
}

// ================================================================== BACK (carries everything behind the film)
function f_top(x) = F_Z1 - F_DROP * (x - F_X0) / (F_X1 + 0.6 - F_X0);      // the finger's top: level with the catch at its tip, F_DROP lower at its root
module latch_cuts2d() {                                         // top latch; mirrored for the bottom
    xr = F_X1 - 1.5; rr = (f_top(xr) - F_T - DOOR_TOP) / 2;
    polygon([[F_X0 - 0.8, DOOR_TOP], [xr, DOOR_TOP], [xr, f_top(xr) - F_T], [F_X0 - 0.8, f_top(F_X0) - F_T]]);   // slit under the finger: it is also the stop
    translate([xr, DOOR_TOP + rr]) circle(rr, $fn = 48);                                         // a full round end, tangent to the finger: no sharp corner at its root
    translate([F_X0 - 0.8, DOOR_TOP]) square([0.8, H + 5]);                                      // gap at its free end
    difference() {                                                                               // notch above it
        polygon([[F_X0 - 0.01, f_top(F_X0)], [F_X1 + 0.6, f_top(F_X1 + 0.6)], [F_X1 + 0.6, H + 5], [F_X0 - 0.01, H + 5]]);
        translate([F_X1 + 0.6 - 1.2, f_top(F_X1 + 0.6) - 0.02]) difference() { square([1.21, 1.2]); translate([0, 1.2]) circle(1.2, $fn = 32); }
    }
    translate([OP_X0 - 0.6, F_Z1 - 1.4]) square([F_X0 - 0.79 - OP_X0 + 0.6, H + 5]);             // the edge beyond the tip stands clear of the outer post and of its rounded root
}
module back2d() difference() {
    union() {
        difference() { rrect2([-BXL, -H], [BXR, H], CORNER_R); latch_cuts2d(); mirror([0, 1]) latch_cuts2d(); }
        for (s = [0, 1]) mirror([0, s]) translate([PAD_X0, F_Z1 - 0.4]) square([PAD_X1 - PAD_X0, H + PAD_UP - F_Z1 + 0.4]);   // the pads
    }
}
module nub(s) {                                                 // ramp on the way in, square catch on the way out
    hull() {
        translate([NUB_X0, Y_RIM - DOOR_T + 0.2, s > 0 ? F_Z1 - 0.01 : -F_Z1 - NUB_H]) cube([NUB_X1 - NUB_X0, 0.7, NUB_H + 0.01]);
        translate([NUB_X0, Y_RIM - 0.02, s > 0 ? F_Z1 - 0.6 : -F_Z1 + 0.58]) cube([NUB_X1 - NUB_X0, 0.02, 0.02]);       // the ramp starts 0.6 mm below the finger's top: on a fat printer it still goes in under the bar
    }
    translate([NUB_X0 + 0.2, Y_RIM - DOOR_T, s > 0 ? F_Z1 - 0.8 : -F_Z1 - NUB_H]) cube([NUB_X1 - NUB_X0 - 0.4, 0.21, NUB_H + 0.8]);     // its layer on the bed is 0.2 mm narrower (and reaches down into the finger, so it is not a loose island)
}
// The film block: guide, pressure pad and film post as ONE solid shape, from the cassette side to the take-up side.  Its top follows the back of the film;
// both ends are straight-sided (nothing narrows toward its foot).  rg: radius of the guide's round top; dd: how far behind the film the pad lies; rp: radius of the post's round top.
SAD_A = [-40, 45];                                              // the pad follows the drum between these film angles; the film lies on the drum from -41 to 46 degrees
module saddle2d(rg, dd, rp) {
    pl = arcp(SAD_A[0], RF + dd); pr = arcp(SAD_A[1], RF + dd);
    hull() { translate(GUIDE) circle(rg); translate([GUIDE[0] - rg, Y_RIM - 0.01]) square([2 * rg, 0.02]); }                                   // guide
    hull() { translate(ROLLER) circle(rp); translate([ROLLER[0] - rp, Y_RIM - 0.01]) square([2 * rp, 0.02]); }                                 // post
    polygon(concat([for (a = [SAD_A[0] : 1.5 : SAD_A[1]]) arcp(a, RF + dd)], [pr, [pr[0], Y_RIM - 0.01], [pl[0], Y_RIM - 0.01]]));             // pad behind the drum
    hull() { translate(GUIDE) circle(rg); translate(pl) circle(0.01); translate([GUIDE[0], Y_RIM - 0.01]) square([pl[0] - GUIDE[0], 0.02]); }   // filled between them: a straight line from round top to pad,
    hull() { translate(ROLLER) circle(rp); translate(pr) circle(0.01); translate([pr[0], Y_RIM - 0.01]) square([ROLLER[0] - pr[0], 0.02]); }    // which stays behind the film (the film is straight there too)
}
module film_block() {
    ez(-SAD_Z, -SAD_BAND + 0.01) saddle2d(R_G, 0.45, R_ROLL - NOSE_BAND);                        // lower band: guide and post carry the film here, outside the picture; the pad stands 0.45 behind it
    ez(-SAD_BAND, NOSE_TOP) saddle2d(R_G - 0.3, 0.85, R_ROLL - NOSE_MID);                        // behind the picture: 0.3 to 1.2 mm lower, it touches nothing.  Its flat end, NOSE_TOP, is the frame wheel's seat
    pe = arcp(33, RF + 0.45); pf = arcp(29, RF + 0.45);
    ez(SAD_BAND - 0.01, SAD_Z) intersection() {                                                  // upper band: guide and pad only.  It stops 2 mm short of the frame wheel's room, and its end is cut flat: no thin tip
        saddle2d(R_G, 0.45, R_ROLL - NOSE_MID);
        union() { translate([-40, Y_RIM - 1]) square([40 + pf[0], 30]); translate([-40, Y_RIM - 1]) square([40 + pe[0], pf[1] - Y_RIM + 1]); }
    }
}
module cradle2d(c, hw, seat) difference() { translate([c[0] - hw, Y_RIM - 0.01]) square([2 * hw, c[1] - Y_RIM]); translate(c) circle(seat); }
module fork2d(c) difference() {                                // seat zone of the fork: the collar sits in the round seat; the mouth is narrower than the collar, so the wheel leaves only when lifted
    translate([c[0] - RB_HWL, Y_RIM - 0.01]) square([RB_HWL + RB_HW, c[1] - Y_RIM + RB_UP]);
    translate(c) circle(RB_SEAT);
    translate([c[0] - RB_GAP / 2, c[1]]) square([RB_GAP, RB_UP + 1]);
    polygon([[c[0] - RB_GAP / 2, c[1] + RB_UP - 0.6], [c[0] - RB_GAP / 2 - 0.6, c[1] + RB_UP + 0.01], [c[0] + RB_GAP / 2 + 0.6, c[1] + RB_UP + 0.01], [c[0] + RB_GAP / 2, c[1] + RB_UP - 0.6]]);
}
module forkfloor2d(c) difference() {                           // floor zone: only the neck passes, with 0.4 mm of room.  This half-round is the wheel's bearing: the film pushes the neck into it
    translate([c[0] - RB_HWL, Y_RIM - 0.01]) square([RB_HWL + RB_HW, c[1] - Y_RIM + RB_UP - FW_LAP]);   // FW_LAP shorter in front than the part over it
    translate(c) circle(RB_GAP / 2);
    translate([c[0] - RB_GAP / 2, c[1]]) square([RB_GAP, RB_UP + 1]);
}
module back() {
    difference() {
        intersection() {
            union() { ey(Y_RIM - DOOR_T + 0.39, Y_RIM) back2d(); ey(Y_RIM - DOOR_T + 0.19, Y_RIM - DOOR_T + 0.4) offset(delta = -0.2) back2d(); ey(Y_RIM - DOOR_T, Y_RIM - DOOR_T + 0.2) offset(delta = -0.4) back2d(); }     // the layer on the bed is 0.2 mm smaller all round
            union() { yb = Y_RIM - DOOR_T;                                                    // v2.17: the bed chamfer on the outline (BED_CHAMFER); the latch fingers, slits and pads keep the 0.4 mm steps above
                      ey(yb + BED_CHAMFER - 0.01, Y_RIM + 1) translate([-BXL - 5, -H - 5]) square([BXL + BXR + 10, 2 * H + 10]);
                      hull() { ey(yb + BED_CHAMFER - 0.02, yb + BED_CHAMFER) rrect2([-BXL, -H], [BXR, H], CORNER_R); ey(yb - 0.01, yb + 0.01) rrect2([-BXL + BED_CHAMFER, -H + BED_CHAMFER], [BXR - BED_CHAMFER, H - BED_CHAMFER], CORNER_R - BED_CHAMFER); }
                      for (s = [0, 1]) mirror([0, 0, s]) ey(yb - 1, Y_RIM + 1) translate([PAD_X0 - 1, F_Z1 - 1]) square([PAD_X1 - PAD_X0 + 2, H + PAD_UP - F_Z1 + 2]); }
        }
    }
    nub(1); nub(-1);
    if (RIB_H > 0) for (s = [1, -1]) scale([1, 1, s]) ey(Y_RIM - 0.01, Y_RIM + RIB_H) polygon([[RIB_X0, f_top(RIB_X0) - F_T], [RIB_X0, f_top(RIB_X0)], [F_X1 + 0.6, f_top(F_X1 + 0.6)], [F_X1 + 2.6, f_top(F_X1 + 0.6)],
        [F_X1 + 2.6, f_top(F_X1 + 0.6) - F_T - 0.5], [F_X1 - 1.5, f_top(F_X1 - 1.5) - F_T]]);     // rib on the finger's inner face, next to its root: stiff front to back
    ey(Y_RIM - 0.01, Y_RIM + STEP_H) difference() { offset(delta = BAND_W / 2 + TREAD_W) ringpoly(); offset(delta = BAND_W / 2 - 0.01) ringpoly(); }   // light seal: a low step ...
    ey(Y_RIM - 0.01, Y_RIM + BAND_H) ring2d(BAND_W);                                         // ... and inside it the band.  Together they fill the two steps of the body's rim exactly
    for (s = [-1, 1]) scale([1, 1, s]) ey(Y_RIM - 0.01, Y_RIM + BAND_H) translate([XJ_L + BAND_W / 2 - 0.01, SAD_Z - 0.01]) square([XJ_R - XJ_L - BAND_W + 0.02, ZR_IN - BAND_W / 2 - SAD_Z + 0.02]);   // between the latches the band and the film block are one
    film_block();
    for (q = [[CASS, KN_R, KN_CR, false], [SPOOL, SP_KR, SP_KCR, true]]) difference() {       // these two blocks close the knob slots in the body's top: light traps, and they keep the knobs in
        union() { ey(Y_RIM - 0.01, q[0][1] - KN_NK - FIT) translate([q[0][0] - q[1] - KSW + FIT, KN_LZ + FIT]) square([2 * (q[1] + KSW - FIT), H - 0.2 - KN_LZ - FIT]);                 // the wide bar, in the upper half of the wall: 2.6 mm thick, its two tips 2.2 mm wide
                  ey(Y_RIM - 0.01, q[0][1] - sqrt(pow(q[2] + KN_SC, 2) - pow(q[2] - 1.2, 2))) translate([q[0][0] - q[2], ZC1 + (q[3] ? -FIT - 0.01 : 0.3)]) square([2 * q[2], KN_LZ + FIT + 0.01 - ZC1 - (q[3] ? -FIT - 0.01 : 0.3)]);   // the narrower bar under it, in the ring's channel: it stops where its tips would get thinner than 1.2 mm
                  if (q[3]) ez(ZS + 0.4, ZC1 - FIT) difference() {                               // take-up side only: a foot under that, inside the chamber.  It is the rear half of the solid step over the film roll
                      translate([q[0][0] - KEEL[0], Y_RIM - 0.01]) square([KEEL[0] + KEEL[1], q[0][1] + 0.6 - Y_RIM]);                        // (the front half is on the body); its two prongs pass either side of the spool's core
                      translate([q[0][0] - q[1] - KN_SC, q[0][1]]) square([2 * (q[1] + KN_SC), 2]); } }
        translate([q[0][0], q[0][1], ZS]) cylinder(r = q[1] + KN_SC, h = H - ZS + 1);           // hollowed to fit round the back of the shaft ...
        translate([q[0][0], q[0][1], ZC1]) cylinder(r = q[2] + KN_SC, h = KN_LZ + 0.4 - ZC1);     // ... and, in the narrow bar, of its ring.  The wide bar reaches in over the ring, the foot in under it
    }
    // the frame wheel hangs in this one fork and stays with the back
    ez(RB_Z[0], ZC1 - FIT) translate([ROLLER[0] + RB_HW - 0.01, Y_RIM - 0.01]) square([SPOOL[0] - KEEL[0] - ROLLER[0] - RB_HW + 0.02, SPOOL[1] + 0.6 - Y_RIM]);   // the fork and the foot of the spool's block are joined: one solid over the film that runs from the wheel to the spool
    ez(RB_FLOOR - 0.01, RB_Z[1]) fork2d(ROLLER);
    translate([ROLLER[0], ROLLER[1], 0]) difference() {                                      // v2.7: under the collar the seat is a cone, like the collar's own underside, 0.35 mm from it: light that comes down
        translate([0, 0, RB_FLOOR - 0.01]) cylinder(r = RB_SEAT + 0.02, h = COLLAR_Z[0] - RB_FLOOR + 0.01);   // behind the neck no longer finds an open space under the collar, only a thin slanted gap
        translate([0, 0, CONE_Z0 - 0.15]) cylinder(r1 = RB_GAP / 2, r2 = RB_SEAT + 0.17, h = COLLAR_Z[0] - CONE_Z0 + 0.17);   // (0.65 below the collar's cone, so a fat collar still comes to rest on the film post, not here)
        translate([0, 0, RB_FLOOR - 1]) cylinder(r = RB_GAP / 2, h = CONE_Z0 - RB_FLOOR + 1.01);
        translate([-RB_GAP / 2, 0, RB_FLOOR - 1]) cube([RB_GAP, RB_UP + 3, 5]);              // (the mouth stays open: the neck comes in through it)
        translate([0, 0, RB_FLOOR - 1]) linear_extrude(5) polygon([[-RB_GAP / 2 - 0.01, 0], [-RB_GAP / 2 - 1.6, RB_UP + 3], [RB_GAP / 2 + 1.6, RB_UP + 3], [RB_GAP / 2 + 0.01, 0]]);
    }
    ez(RB_Z[0], RB_FLOOR) forkfloor2d(ROLLER);
    ez(RB_Z[1] - 0.01, H - 0.2) translate([ROLLER[0] - SHAFT_R, Y_RIM - 0.01]) square([2 * SHAFT_R, ROLLER[1] - COLLAR_R - 0.7 - Y_RIM]);   // fills the slot in the body's top behind the neck: light trap
    difference() {                                                                           // ... and over that a wide bar that comes right up to the neck: its two tips pass either side of it.  The lifted collar goes under it
        union() { intersection() { translate([0, 0, -0.19]) fw_ridge(); translate([ROLLER[0] - SHAFT_R - FW_KSW + FIT, Y_RIM, H - 1]) cube([2 * (SHAFT_R + FW_KSW - FIT), ROLLER[1] - FW_NK - FIT - Y_RIM, 6]); }   // the rear part of the ridge round the frame wheel's hole
                  ez(FW_LZ + FIT, H - 0.2) translate([ROLLER[0] - SHAFT_R - FW_KSW + FIT, Y_RIM - 0.01]) square([2 * (SHAFT_R + FW_KSW - FIT), ROLLER[1] - FW_NK - FIT - Y_RIM]);
                  ez(ZR_OUT, FW_LZ + 0.41) translate([ROLLER[0] - SHAFT_R - FW_KSW + FIT, Y_RIM - 0.01]) square([2 * (SHAFT_R + FW_KSW - FIT), BAND_H - 0.3]); }   // at the rim it stands on the seal band
        translate([ROLLER[0], ROLLER[1], RB_Z[1]]) cylinder(r = SHAFT_R + 0.5, h = H);     // 0.5, not SHAFT_CL: the film pulls the neck back against this cradle and against the fork's floor: two bearings in line, and the gap behind the neck is closed
    }
    ey(Y_RIM - 0.01, Y_RIM + BAND_H) translate([XJ_R - 0.01, ZR_IN - BAND_W / 2]) square([ROLLER[0] - RB_HWL - XJ_R + 0.02, ZR_OUT - ZR_IN + 0.01]);   // the fork's foot runs into the band: it does not stand alone, and there is no pit beside it
}

// ================================================================== click springs (the same shape on the blade and on the wheel)
module sector2d(c, r0, r1, a0, a1, n = 12) polygon(concat([for (i = [0 : n]) pol(c, r0, a0 + (a1 - a0) * i / n)], [for (i = [n : -1 : 0]) pol(c, r1, a0 + (a1 - a0) * i / n)]));
module rimspring2d(c, R, slit, t, a_tip, arc) {                 // on a part whose rim is at radius R: a beam t thick, slit clear of the rim, rooted at a_tip - arc, free end at a_tip
    dr = 3.0 / R * 180 / PI; a0 = a_tip - arc - dr; a1 = a_tip + 1.5 / R * 180 / PI;
    sector2d(c, R + slit, R + slit + t, a0, a1, 60);
    sector2d(c, R - 1.4, R + slit + t, a0, a_tip - arc, 6);                                      // root: 3 mm of solid (it reaches 1.4 mm into the part: the layer on the bed stays in one piece)
}
module rimbump2d(c, R, slit, t, a_tip, bump) if (bump > 0.05) translate(pol(c, R + slit + t, a_tip)) rotate(a_tip - 90) hull() {     // the tooth: a round tip (TIP_R) on a 2.6 mm base
    translate([0, bump - TIP_R]) circle(TIP_R, $fn = 48);
    translate([-1.3, -0.9]) square([2.6, 0.9]);
}
module rimspring_cut2d(c, R, slit, a_tip, arc) intersection() { // the closed end of the slit is a full round, tangent to the spring: no sharp corner where the spring starts
    rk = slit / 2; da = 2 * rk / R * 180 / PI;
    translate(pol(c, R + slit - rk, a_tip - arc)) circle(rk, $fn = 32);
    sector2d(c, R - 3, R + slit + 0.001, a_tip - arc - da, a_tip - arc + da, 6);
}
module notch2d(c, rw, a, dv) {                                  // a V with 45-degree ramps in a wall whose face is at radius rw; its apex is dv deep.  The round tip seats on both ramps, 0.33 above the apex
    polygon([for (v = [[-dv - 0.3, -0.1], [-0.3, dv - 0.12], [0.3, dv - 0.12], [dv + 0.3, -0.1]]) pol(c, rw + v[1], a + v[0] / rw * 180 / PI)]);
}

// ================================================================== FRONT PLATE (prints front face down; everything rises inside it)
module plate_out2d() rrect2([FX0, FZ0], [FX1, FZ1], 2.5);    // outline
module plate_bed2d() rrect2([FX0 + BED_CHAMFER, FZ0 + BED_CHAMFER], [FX1 - BED_CH_FIT, FZ1 - BED_CHAMFER], 2.5 - BED_CHAMFER);   // v2.17: the bed face, chamfered; BED_CH_FIT on the right, where only 1.4 mm of plate stands beside the latch leaf's slit
module leaf_slit2d() {                                        // the slit round the latch leaf: two sides with round ends, and the gap below its free end
    for (x = [LF_X0 - LF_G / 2, LF_X1 + LF_G / 2]) hull() { translate([x, LF_ZR + LF_G / 2]) circle(LF_G / 2, $fn = 32); translate([x, LF_ZB - LF_G / 2]) circle(LF_G / 2, $fn = 32); }
    translate([LF_X0 - LF_G, LF_ZB - LF_FG]) square([LF_X1 - LF_X0 + 2 * LF_G, LF_FG]);
}
module top_open2d() {                                          // the hub and the tab's arm come out through the top edge here
    translate(P_S) circle(HUB_R + 1.2);
    for (i = [0 : 16]) translate(P_S) rotate(-THETA_S - 2.2 + i * (2 * THETA_S + 4.4) / 16) translate([-FIN_W / 2 - 1.2, 0]) square([FIN_W + 2.4, 9]);   // the arm's whole swing, plus 1.2 mm: the hub has 0.6 mm of play
}
// The inside of the plate is a solid slab with three pockets in it: nothing stands alone on a floor.  The pockets' own edges are the click walls and the stops.
A_LO = A0 - SPAN - THETA_S - 1.4; A_HI = A0 + SPAN + THETA_S + 1.4;      // where the blade's straight edges stop: 1.2 degrees past each notch (the click parks the blade; the stops only catch overshoot)
module blade_room2d() {                                         // what the shutter sweeps, at the blade's level
    difference() {
        union() { sector2d(P_S, 0.01, RWB, A_LO - 0.8, A_HI + 0.8, 40); sector2d(P_S, R_OUT - 1.0, RWB, A_HI, DB_A + THETA_S + 4.6, 12); }
        sector2d(P_S, 20, 27, A_LO - 0.9, A_LO, 3); sector2d(P_S, 20, 27, A_HI, A_HI + 0.9, 3);              // the two stops: 7 mm pads on the pocket's edge.  Elsewhere the edge stands 0.3 to 0.4 mm back
    }
    for (s = [-1, 1]) notch2d(P_S, RWB, DB_A + s * THETA_S, BL_DV);                                        // click notches: closed, open (shallow), closed
    notch2d(P_S, RWB, DB_A, 0.7);
    top_open2d();
}
module root_room2d() for (i = [0 : 12]) translate(P_S) rotate(-THETA_S - 1.2 + i * (2 * THETA_S + 2.4) / 12) translate(-P_S) offset(delta = 1.8) root2d();   // the blade's thick root, swept, at the wheel's level
module wheel_room2d() {                                         // the wheel's disc and the part of its rim that carries the click spring, at the wheel's level
    translate(WHEEL_C) circle(WHEEL_R + 0.7);
    sector2d(WHEEL_C, WHEEL_R - 1, RWW, WD_A0 - WH_ARC - 10.7 - WPOS[2] - 3.0, WD_A0 + 8.5, 40);
    for (k = [0 : 2]) notch2d(WHEEL_C, RWW, WD_A0 - WPOS[k], WH_DV);                                        // one notch per position
}
module foot_room2d() arc_slot(WHEEL_C, H_RHO, HANDLE_A0 + FIN_HALF + 2.5, HANDLE_A0 - WPOS[2] - FIN_HALF - 2.5, HW_FIN + 1.0, 40);   // the handle's foot, at the blade's level
FIN_SLOT = HW_SLOT;
module fin_slot2d() arc_slot(WHEEL_C, H_RHO, HANDLE_A0 + FIN_HALF + 1, HANDLE_A0 - WPOS[2] - FIN_HALF - 1, FIN_SLOT, 40);
module front(slid = SLID) translate([0, 0, slid]) {
    difference() {
        union() {
            ey(Y_CV0, Y_CVF - BED_CHAMFER + 0.01) plate_out2d();
            hull() { ey(Y_CVF - BED_CHAMFER, Y_CVF - BED_CHAMFER + 0.02) plate_out2d(); ey(Y_CVF - 0.02, Y_CVF) plate_bed2d(); }   // v2.17: the bed chamfer (it was one layer 0.2 mm smaller)
            ey(Y_FRONT, Y_CV0 + 0.01) difference() { plate_out2d(); offset(r = -0.6) offset(delta = 0.6) { blade_room2d(); root_room2d(); wheel_room2d(); foot_room2d(); wheel_web_room2d(); } }   // the slab: solid up to the body's face wherever nothing moves
            ey(Y_SC0 - 0.05, Y_CV0 + 0.01) difference() { plate_out2d(); offset(r = -0.6) offset(delta = 0.6) { blade_room2d(); root_room2d(); foot_room2d(); wheel_web_room2d(); } }        // over the wheel, outside the blade's sweep: solid down to the wheel's face, so the wheel cannot tip (v2.17: except over its web, which rides under the plate's ceiling instead)
            cyl_y(P_S, BOSS_R, Y_FRONT + 0.2, Y_CV0 + 0.01);                                         // the blade turns on this
            difference() { cyl_y(WHEEL_C, WBOSS_R, Y_FRONT + 0.15, Y_CV0 + 0.01); cyl_y(P_S, RWB, Y_FRONT, Y_CV0 + 0.02); }   // the wheel turns on this plain post; it is flat where the blade's spring passes
            ey(Y_SC1 + 0.6, Y_CVF) polygon([[-1.6, FZ1 - 1], [1.6, FZ1 - 1], [0.4, H + PAD_UP - SIGHT_DROP], [-0.4, H + PAD_UP - SIGHT_DROP]]);   // v2.10: front sight, a point on the plate's top edge on the lens's line, in front of the rocker
            for (f = FEET) intersection() { exx(f[0], f[0] + FOOT_W) polygon(foot_yz(f[1], 0, 0));         // hooked feet (the hooks point down), corners rounded so that a bulging corner or a seam cannot bind
                ey(Y_FRONT - FOOT_D - 1, Y_FRONT + 0.1) rrect2([f[0], f[1] - LIP - 0.01], [f[0] + FOOT_W, f[1] + FOOT_L + 0.01], 0.8);
                hull() { translate([f[0], Y_FRONT - FOOT_D + 0.8, f[1] - LIP - 1]) cube([FOOT_W, FOOT_D, FOOT_L + LIP + 2]); translate([f[0] + 0.8, Y_FRONT - FOOT_D, f[1] - LIP - 1]) cube([FOOT_W - 1.6, 0.01, FOOT_L + LIP + 2]); } }   // its far end tapers 0.8 mm each side: it finds its pocket
            for (f = FEET) { xf = f[0] + FOOT_W; d0 = 0.05 + SIDE_G - PK_X;                              // v2.10: a lip on each foot's right side, with the hook's own slope (43 degrees off upright as it prints), as long as the foot is tall.  It prints as the hook does: growing outward from the foot
                intersection() { ez(f[1] + 0.3, f[1] + FOOT_L - 0.3) polygon([[xf - 1.0, Y_FRONT - d0], [xf, Y_FRONT - d0], [xf + SIDE_L, Y_FRONT - d0 - SIDE_L / PK_SL], [xf + SIDE_L, Y_FRONT - FOOT_D + 0.3], [xf + SIDE_L - 0.3, Y_FRONT - FOOT_D], [xf - 1.0, Y_FRONT - FOOT_D]]);
                                 exx(xf - 1.1, xf + SIDE_L + 0.1) polygon(foot_yz(f[1], 0, 0)); } }                 // the lip's far end carries the foot's own chamfer
            exx(LF_X0, LF_X1) polygon([[Y_CVF - LF_T + 0.01, LF_ZR - 0.01], [Y_CVF - LF_T - 0.8, LF_ZR - 0.01], [Y_CVF - LF_T + 0.01, LF_ZR + 2.4]]);   // the leaf's root is filled in behind with a long wedge: no sharp corner where it bends most
        }
        ey(Y_FRONT - 3, Y_CVF + 1) leaf_slit2d();                                                    // the latch leaf: a slit round three sides, through the plate
        for (k = [0 : 1]) ey(Y_CVF - 0.21 - 0.2 * k, Y_CVF + 1) offset(delta = 0.2 * (2 - k)) leaf_slit2d();   // (wider on the two bed layers, in steps: elephant's foot)
        difference() { translate([LF_X0 - 0.01, Y_FRONT - 3, LF_ZR]) cube([LF_X1 - LF_X0 + 0.02, Y_CVF - LF_T - Y_FRONT + 3, LF_ZB - LF_ZR]);        // and everything behind the leaf
                       exx(LF_X0 - 1, LF_X1 + 1) polygon([[Y_CVF - LF_T + 0.01, LF_ZR - 0.01], [Y_CVF - LF_T - 0.8, LF_ZR - 0.01], [Y_CVF - LF_T + 0.01, LF_ZR + 2.4]]); }
        ey(Y_CV0 - 1, Y_CVF + 1) fin_slot2d();                                                       // aperture handle
        for (k = [0 : 1]) ey(Y_CVF - 0.21 - 0.2 * k, Y_CVF + 1) offset(delta = 0.2) fin_slot2d();    // (wider on the two bed layers, in steps)
        // lens port through the pocket floor.  Three layers, each a bridge the printer can make: a slot, a square, an octagon.  Nothing to poke out.
        translate([-PORT_H, Y_SEAT - 0.2, -(LENS_D / 2 + 0.3)]) cube([2 * PORT_H, 0.21, LENS_D + 0.6]);
        translate([-PORT_H, Y_SEAT - 0.4, -PORT_H]) cube([2 * PORT_H, 0.21, 2 * PORT_H]);
        ey(Y_CV0 - 0.01, Y_SEAT - 0.39) rotate(22.5) circle(r = PORT_H / cos(22.5), $fn = 8);
        difference() {                                                                               // lens pocket with three crush ribs
            cyl_y([0, 0], LENS_D / 2 + 0.1, Y_SEAT, Y_CVF + 0.01);
            for (a = [90, 210, 330]) cyl_y(pol([0, 0], LENS_D / 2 + 0.55, a), 0.8, Y_SEAT - 0.01, Y_CVF - 0.6);
        }
        cyl_y([0, 0], LENS_D / 2 + 0.1, Y_CVF - 0.6, Y_CVF + 0.01, LENS_D / 2 + 0.7);
        for (k = [0 : 2], l = [[0.6, 0], [0.2, 0.25]]) ey(Y_CVF - l[0], Y_CVF + 0.01)                   // three dots by the handle, small to large: 3 layers deep, a little wider on the bed layer
            translate(pol(WHEEL_C, H_RHO + LAB_R, HANDLE_A0 - WPOS[k])) circle(r = DOT_R[k] + l[1], $fn = 32);
    }
    translate([LF_X0, Y_FRONT - 0.01, LF_ZH - LF_PL / 2]) cube([LF_X1 - LF_X0, Y_CVF - LF_T - Y_FRONT + 0.02, LF_PL]);                        // the latch post, standing on the leaf's free end
    exx(LF_X0, LF_X1) hull() { translate([Y_FRONT - TOOTH_H + LF_R, LF_ZH]) circle(LF_R, $fn = 32); translate([Y_FRONT - 0.01, LF_ZH - LF_R]) square([0.02, 2 * LF_R]); }   // its round end, behind the plate
}


// ================================================================== v2.13 THE FIRST PLATE: rung 1 of the ladder.  A pinhole and a slide: no lens, no wheel, no shutter.
// It goes on the body exactly as the front plate does (the same four feet, the same latch leaf: those lines are the front plate's own).  Behind its skin, against the body's face,
// lies one flat strip, the slide: down, it covers the port; lifted P1_T, its hole stands in line with the pinhole.  Its own weight keeps it shut.  It cannot come out while the plate is on:
// its body is wider than the slot its tab comes up through.  The pinhole is a needle prick in kitchen foil, held on the lens seat by the pinhole ring, as before.
P1_T = 10.0;                                   // how far the slide is lifted
P1_HW = 10.0; P1_ZB = -16.8; P1_ZS = 15.8;     // the slide's body: half width, bottom and shoulder (both when shut)
P1_HOLE = 2.8;   /* v2.14: 2.8, not 3.3: half a millimetre more of the slide covers the port when a fat print seats it high on its wedge (0.8 mm left on the fattest printer, not 0.3) */                                 // its hole: the cone from the pinhole to the corners of the picture is 2.0 mm in radius where it passes
P1_TAB = [-10.0, -4.0]; P1_GRIP = [FZ1 + 2.4, FZ1 + 8.4];   // the tab comes up beside the sight, not in its line; its grip stands clear of the plate's top edge
P1_D = 1.25; P1_CL = 0.15;                     // the pocket is this deep (the slide is 1.0 thick: five layers) and this much longer than the slide's travel
// v2.14 THE FIRST WEDGE.  The slide's lower end is a wedge (P1_TA a side over its last P1_NOSE mm) and the pocket's lower end is the same wedge.  Pushed down, the slide stops where the two meet:
// no gap at the sides, and it stays down by friction whichever way up the camera is (before, only its weight held it shut).  A fat print seats about 1.1 mm higher, a thin one 0.9 mm lower (P1_UNDER is room
// for that); a slide that seats too high is sanded on its two slanted edges.  Lifted 2 mm it is as free as before.  Its open end is still a square stop: that end sets where the hole stands.
P1_TA = 10; P1_NOSE = 12.0; P1_UNDER = 2.0;
P1_SEAT = Y_CV0 + 0.8;                         // the foil's seat in the first plate.  Its own number: the lens seat moved in v2.14 (focus), and a pinhole has no focus; here the body's port cuts least of the corners
function p1_hw(z) = P1_HW - max(0, P1_ZB + P1_NOSE - z) * tan(P1_TA);                 // the slide's half width at height z (slide shut)
module p1_slide2d() polygon([[-p1_hw(P1_ZB), P1_ZB], [p1_hw(P1_ZB), P1_ZB], [P1_HW, P1_ZB + P1_NOSE], [P1_HW, P1_ZS], [-P1_HW, P1_ZS], [-P1_HW, P1_ZB + P1_NOSE]]);
module p1_pocket2d() { zl = P1_ZB - P1_UNDER; zk = P1_ZB + P1_NOSE + 0.28 / tan(P1_TA);   // the socket's walls are the nose's own lines, 0.02 clear; above the knee the pocket is 0.3 wider a side, as before
                       polygon([[-p1_hw(zl) - 0.02, zl], [p1_hw(zl) + 0.02, zl], [P1_HW + 0.3, zk], [P1_HW + 0.3, P1_ZS + P1_T + P1_CL], [-P1_HW - 0.3, P1_ZS + P1_T + P1_CL], [-P1_HW - 0.3, zk]]);
                       translate([P1_TAB[0] - 0.3, P1_ZS]) square([P1_TAB[1] - P1_TAB[0] + 0.6, FZ1 + 2 - P1_ZS]); }
module plate1(slid = SLID) translate([0, 0, slid]) {
    difference() {
        union() {
            ey(Y_FRONT, Y_CVF - BED_CHAMFER + 0.01) plate_out2d();
            hull() { ey(Y_CVF - BED_CHAMFER, Y_CVF - BED_CHAMFER + 0.02) plate_out2d(); ey(Y_CVF - 0.02, Y_CVF) plate_bed2d(); }   // v2.17: the bed chamfer, as on the front plate
            ey(Y_SC1 + 0.6, Y_CVF) polygon([[-1.6, FZ1 - 1], [1.6, FZ1 - 1], [0.4, H + PAD_UP - SIGHT_DROP], [-0.4, H + PAD_UP - SIGHT_DROP]]);   // v2.10: front sight, a point on the plate's top edge on the lens's line, in front of the rocker
            for (f = FEET) intersection() { exx(f[0], f[0] + FOOT_W) polygon(foot_yz(f[1], 0, 0));         // hooked feet (the hooks point down), corners rounded so that a bulging corner or a seam cannot bind
ey(Y_FRONT - FOOT_D - 1, Y_FRONT + 0.1) rrect2([f[0], f[1] - LIP - 0.01], [f[0] + FOOT_W, f[1] + FOOT_L + 0.01], 0.8);
hull() { translate([f[0], Y_FRONT - FOOT_D + 0.8, f[1] - LIP - 1]) cube([FOOT_W, FOOT_D, FOOT_L + LIP + 2]); translate([f[0] + 0.8, Y_FRONT - FOOT_D, f[1] - LIP - 1]) cube([FOOT_W - 1.6, 0.01, FOOT_L + LIP + 2]); } }   // its far end tapers 0.8 mm each side: it finds its pocket
            for (f = FEET) { xf = f[0] + FOOT_W; d0 = 0.05 + SIDE_G - PK_X;                              // v2.10: a lip on each foot's right side, with the hook's own slope (43 degrees off upright as it prints), as long as the foot is tall.  It prints as the hook does: growing outward from the foot
intersection() { ez(f[1] + 0.3, f[1] + FOOT_L - 0.3) polygon([[xf - 1.0, Y_FRONT - d0], [xf, Y_FRONT - d0], [xf + SIDE_L, Y_FRONT - d0 - SIDE_L / PK_SL], [xf + SIDE_L, Y_FRONT - FOOT_D + 0.3], [xf + SIDE_L - 0.3, Y_FRONT - FOOT_D], [xf - 1.0, Y_FRONT - FOOT_D]]);
exx(xf - 1.1, xf + SIDE_L + 0.1) polygon(foot_yz(f[1], 0, 0)); } }                 // the lip's far end carries the foot's own chamfer
            exx(LF_X0, LF_X1) polygon([[Y_CVF - LF_T + 0.01, LF_ZR - 0.01], [Y_CVF - LF_T - 0.8, LF_ZR - 0.01], [Y_CVF - LF_T + 0.01, LF_ZR + 2.4]]);   // the leaf's root is filled in behind with a long wedge: no sharp corner where it bends most
        }
        ey(Y_FRONT - 0.01, Y_FRONT + P1_D) p1_pocket2d();                                           // the slide's pocket, open toward the body; the tab's slot runs out through the top edge
        ey(Y_FRONT - 3, Y_CVF + 1) leaf_slit2d();                                                    // the latch leaf: a slit round three sides, through the plate
        for (k = [0 : 1]) ey(Y_CVF - 0.21 - 0.2 * k, Y_CVF + 1) offset(delta = 0.2 * (2 - k)) leaf_slit2d();   // (wider on the two bed layers, in steps: elephant's foot)
        difference() { translate([LF_X0 - 0.01, Y_FRONT - 3, LF_ZR]) cube([LF_X1 - LF_X0 + 0.02, Y_CVF - LF_T - Y_FRONT + 3, LF_ZB - LF_ZR]);        // and everything behind the leaf
exx(LF_X0 - 1, LF_X1 + 1) polygon([[Y_CVF - LF_T + 0.01, LF_ZR - 0.01], [Y_CVF - LF_T - 0.8, LF_ZR - 0.01], [Y_CVF - LF_T + 0.01, LF_ZR + 2.4]]); }
        translate([-PORT_H, P1_SEAT - 0.2, -(LENS_D / 2 + 0.3)]) cube([2 * PORT_H, 0.21, LENS_D + 0.6]);
        translate([-PORT_H, P1_SEAT - 0.4, -PORT_H]) cube([2 * PORT_H, 0.21, 2 * PORT_H]);
        ey(Y_FRONT + P1_D - 0.01, P1_SEAT - 0.39) rotate(22.5) circle(r = PORT_H / cos(22.5), $fn = 8);   // the port, from the lens seat back to the slide
        difference() {                                                                               // lens pocket with three crush ribs
cyl_y([0, 0], LENS_D / 2 + 0.1, P1_SEAT, Y_CVF + 0.01);
for (a = [90, 210, 330]) cyl_y(pol([0, 0], LENS_D / 2 + 0.55, a), 0.8, P1_SEAT - 0.01, Y_CVF - 0.6);
}
        cyl_y([0, 0], LENS_D / 2 + 0.1, Y_CVF - 0.6, Y_CVF + 0.01, LENS_D / 2 + 0.7);
    }
    translate([LF_X0, Y_FRONT - 0.01, LF_ZH - LF_PL / 2]) cube([LF_X1 - LF_X0, Y_CVF - LF_T - Y_FRONT + 0.02, LF_PL]);                        // the latch post, standing on the leaf's free end
    exx(LF_X0, LF_X1) hull() { translate([Y_FRONT - TOOTH_H + LF_R, LF_ZH]) circle(LF_R, $fn = 32); translate([Y_FRONT - 0.01, LF_ZH - LF_R]) square([0.02, 2 * LF_R]); }   // its round end, behind the plate
}
module slide1(up = 0) translate([0, 0, up]) difference() {        // prints flat, grip up
    union() {
        ey(Y_FRONT + 0.1, Y_FRONT + 1.1) { offset(r = 0.8) offset(delta = -0.8) p1_slide2d(); translate([P1_TAB[0], P1_ZS - 1]) square([P1_TAB[1] - P1_TAB[0], P1_GRIP[1] - P1_ZS + 1]); }
        ey(Y_FRONT + 0.1, Y_FRONT + 3.1) translate([P1_TAB[0], P1_GRIP[0]]) square([P1_TAB[1] - P1_TAB[0], P1_GRIP[1] - P1_GRIP[0]]);      // the grip: three times as thick, above the plate's top edge
    }
    cyl_y([0, -P1_T], P1_HOLE, Y_FRONT, Y_FRONT + 1.2);
}

// ================================================================== BLADE (the whole shutter: one part)
module rocker2d() offset(r = 0.8) offset(delta = -0.8) polygon([     // a shallow V.  In each closed position one side lies flat, just above the camera, and the other stands up 31 degrees
    [-(RK_L + RK_LX) * cos(THETA_S), RK_V + (RK_L + RK_LX) * sin(THETA_S)], [0, RK_V], [RK_L * cos(THETA_S), RK_V + RK_L * sin(THETA_S)],
    [RK_L * cos(THETA_S) - RK_T * sin(THETA_S), RK_V + RK_L * sin(THETA_S) + RK_T * cos(THETA_S)], [0, RK_V + RK_T / cos(THETA_S)],
    [-(RK_L + RK_LX) * cos(THETA_S) + RK_T * sin(THETA_S), RK_V + (RK_L + RK_LX) * sin(THETA_S) + RK_T * cos(THETA_S)]]);
module root2d() {                                               // where the blade meets its hub: as wide as the hub, twice as thick as the blade, out to 14 mm.
    hull() { translate(P_S) circle(HUB_R); intersection() { pie2d(); translate(P_S) circle(10); } }   // A press on the rocker that goes on past the click is carried from here to the stops
    intersection() { pie2d(); translate(P_S) circle(14); }
}
// v2.17: the root's web.  Behind the blade (at the wheel's level) the pocket is open wherever the wheel never comes, and out to 17 mm from the pivot the blade's whole swing stays
// 1.3 mm or more clear of the wheel's and of the plate's walls: so the root, 2 mm deep, reaches 17 mm (it reached 14), between BW_A of the pie's edges.  Farther out the blade passes
// over the wheel and stays 1 mm thick.  The plate is not changed for it.
BW_R = 17.0; BW_A = [4.0, 3.6];
module blade_web2d() sector2d(P_S, 0.01, BW_R, A0 - SPAN + BW_A[0], A0 + SPAN - BW_A[1], 24);
module arm2d() offset(r = -0.6) offset(delta = 0.6) { translate([P_S[0] - FIN_W / 2, P_S[1]]) square([FIN_W, RK_V + RK_T]); translate(P_S) rocker2d(); translate(P_S) circle(HUB_R); }
module blade_out2d() { pie2d(); root2d(); blade_web2d(); arm2d(); translate(P_S) rocker2d(); }     // the blade's outline on the bed, less its click spring
module pie2d() polygon(concat([P_S], [for (a = [A0 - SPAN : 2 : A0 + SPAN]) pol(P_S, R_OUT, a)], [pol(P_S, R_OUT, A0 + SPAN)]));
module blade(phi = PHI) rot_xz(P_S, phi) {                      // prints front face down; hub, arm and tab rise from it
    difference() {
        union() {
            intersection() {
                union() {
                    ey(Y_SC0 + 0.19, Y_SC1 - 0.2) pie2d();
                    ey(Y_SC0, Y_SC0 + 0.2) offset(delta = -0.3) pie2d();                                     // the layer that faces the wheel is 0.3 smaller: a lead-in
                    ey(Y_SC1 - 0.21, Y_SC1) offset(delta = -0.4) pie2d();                                    // the layer on the bed is 0.4 smaller: elephant's foot lands on size
                    ey(Y_FRONT + 0.25, Y_SC1) root2d();                                                      // hub and root: nearly the full depth of the pocket, so the blade cannot tip, and a hard press cannot snap the blade off its hub
                    ey(Y_FRONT + 0.25, Y_SC1) blade_web2d();                                                 // v2.17: the root's web, as deep, out to BW_R
                    ey(Y_FRONT + 0.25, Y_SC1) arm2d();                                                       // arm: comes up through the top of the plate; its corners under the rocker are rounded
                    ey(Y_SC1 - FIN_L, Y_SC1) translate(P_S) rocker2d();                                       // rocker: lies over the top of the camera.  Press the raised side flat
                }
                union() {                                                                                    // v2.17: the bed chamfer (BED_CH_FIT), in two layers
                    ey(Y_SC1 - FIN_L - 1, Y_SC1 - BED_CH_FIT + 0.01) translate(P_S) square(120, center = true);
                    ey(Y_SC1 - BED_CH_FIT, Y_SC1 - BED_CH_FIT / 2 + 0.01) offset(delta = -BED_CH_FIT / 2) blade_out2d();
                    ey(Y_SC1 - BED_CH_FIT / 2, Y_SC1 + 0.01) offset(delta = -BED_CH_FIT) blade_out2d();
                }
            }
            ey(Y_SC0, Y_SC1 - 0.2) rimspring2d(P_S, R_OUT, BL_SLIT, BL_T, DB_A, BL_ARC);             // click spring: the rim itself.  It is a spring: it stays 1.35 mm wide and keeps its own bed relief
            ey(Y_SC1 - 0.21, Y_SC1) offset(delta = -0.3) rimspring2d(P_S, R_OUT, BL_SLIT, BL_T, DB_A, BL_ARC);
            ey(Y_SC0, Y_SC1 - 0.4) rimbump2d(P_S, R_OUT, BL_SLIT, BL_T, DB_A, BL_BUMP - 0.02);
            ey(Y_SC1 - 0.41, Y_SC1) rimbump2d(P_S, R_OUT, BL_SLIT, BL_T, DB_A, BL_BUMP - 0.3);       // the two layers on the bed: 0.3 lower
        }
        ey(Y_SC0 - 1, Y_SC1 + 1) rimspring_cut2d(P_S, R_OUT, BL_SLIT, DB_A, BL_ARC);
        cyl_y(pol(P_S, R_PORT - WIN_IN, A0), WIN_R, Y_SC0 - 1, Y_SC1 + 1);                           // the window.  While the rocker is pressed the blade hangs 2 x HUB_C lower on its boss: the window is drawn WIN_IN nearer the pivot, so that it crosses the lens's axis then
        cyl_y(BL_HC, HUB_HOLE, Y_FRONT, Y_SC1 + 1);                                                // off-centre by the hub's play, away from the tooth: at rest the spring holds this side on the boss
        cyl_y(BL_HC, HUB_HOLE, Y_SC1 - 0.4, Y_SC1 + 0.01, HUB_HOLE + 0.4);                              // the hole flares on the bed side: room for elephant's foot
    }
}

// v2.17: the aperture wheel was a 1 mm disc (the print farm: "thin on average, it may flex or warp").  Over its far side, which the shutter never crosses, it now carries a web
// 1.2 mm tall (up to the shutter's own front face): WW_A from the handle's foot round to the plate's solid corner, WW_R from the hub to 0.5 inside the rim.  The front plate has a
// room for its swing (wheel_web_room2d), 1.1 mm all round (the wheel has 0.5 of play on its post, and a fat printer adds 0.25 to each wall), and the web's top rides 0.15 under the room's ceiling as the disc rode under the slab it replaces: the wheel still cannot tip.
// It stays 1.5 mm or more from everything the shutter sweeps in every position of both (tools/meshcheck.py does not check this; tools/check.py and tools/motion.py do).
WW_R = [4.6, WHEEL_R - 0.5]; WW_A = [190, 320];
module wheel_web2d() sector2d(WHEEL_C, WW_R[0], WW_R[1], WW_A[0], WW_A[1], 40);
module wheel_web_room2d() offset(delta = 1.1) sector2d(WHEEL_C, WW_R[0], WW_R[1], WW_A[0] - WPOS[2], WW_A[1], 60);
// ================================================================== APERTURE WHEEL (three positions: Pinhole, Sun, Cloud)
module wheel(pos = STOP) rot_xz(WHEEL_C, -WPOS[pos]) {
    difference() {
        union() {
            ey(Y_WH0 + 0.39, Y_WH1 - 0.2) translate(WHEEL_C) circle(WHEEL_R);
            ey(Y_WH0 + 0.19, Y_WH0 + 0.4) translate(WHEEL_C) circle(WHEEL_R - BED_CH_FIT / 2);       // v2.17: the bed chamfer, two layers (0.4, then 0.2)
            ey(Y_WH0, Y_WH0 + 0.2) translate(WHEEL_C) circle(WHEEL_R - BED_CH_FIT);                  // the layer on the bed is 0.4 smaller: elephant's foot lands on size
            ey(Y_WH1 - 0.01, Y_SC1) wheel_web2d();                                                   // v2.17: the web (see WW_R), up to the blade's front face
            ey(Y_WH1 - 0.21, Y_WH1) translate(WHEEL_C) circle(WHEEL_R - 0.3);                        // top layer 0.3 smaller: a lead-in for the blade's edge
            ey(Y_WH0 + 0.19, Y_WH1) rimspring2d(WHEEL_C, WHEEL_R, WH_SLIT, WH_T, WD_A0, WH_ARC);     // click spring: the rim itself
            ey(Y_WH0, Y_WH0 + 0.2) offset(delta = -0.3) rimspring2d(WHEEL_C, WHEEL_R, WH_SLIT, WH_T, WD_A0, WH_ARC);
            ey(Y_WH0 + 0.4, Y_WH1) rimbump2d(WHEEL_C, WHEEL_R, WH_SLIT, WH_T, WD_A0, WH_BUMP - 0.02);
            ey(Y_WH0, Y_WH0 + 0.41) rimbump2d(WHEEL_C, WHEEL_R, WH_SLIT, WH_T, WD_A0, WH_BUMP - 0.3);
        }
        ey(Y_WH0 - 1, Y_WH1 + 1) rimspring_cut2d(WHEEL_C, WHEEL_R, WH_SLIT, WD_A0, WH_ARC);
        cyl_y(WH_HC, WHOLE, Y_WH0 - 1, Y_WH1 + 1);                                                 // off-centre by the hub's play, away from the tooth: the spring holds this side on the post
        cyl_y(WH_HC, WHOLE + 0.4, Y_WH0 - 0.01, Y_WH0 + 0.4, WHOLE);                                  // the hole flares on the bed side
        for (k = [0 : 2]) { h = pol(WHEEL_C, R_HOLE, A_AX + WPOS[k]); r = STOP_R[k] + HOLE_COMP;
            top = Y_WH1;
            e = 0.4;                                                                                  // the edge of the hole: two layers
            cyl_y(h, r + 0.75, Y_WH0 - 0.01, top - e + 0.01, r, $fn = 32);                                      // cone behind a thin edge, so the hole does not shade the corners
            cyl_y(h, r, top - e, top + 0.01, $fn = 32); }
    }
    difference() {                                                                                    // handle: 6.2 mm thick, 11 mm long, HND_UP proud of the plate, dished for a fingertip
        union() { ey(Y_WH1 - 0.01, Y_CVF + HND_UP - 0.6) arc_slot(WHEEL_C, H_RHO, HANDLE_A0 - FIN_HALF, HANDLE_A0 + FIN_HALF, HW_SLOT - 1.0, 12);
                  ey(Y_CVF + HND_UP - 0.61, Y_CVF + HND_UP) offset(delta = -0.4) arc_slot(WHEEL_C, H_RHO, HANDLE_A0 - FIN_HALF, HANDLE_A0 + FIN_HALF, HW_SLOT - 1.0, 12); }
        intersection() { translate([pol(WHEEL_C, H_RHO, HANDLE_A0)[0], Y_CVF + HND_UP + 13.3, pol(WHEEL_C, H_RHO, HANDLE_A0)[1]]) sphere(r = 14, $fn = 96);
                         ey(Y_CVF, Y_CVF + HND_UP + 1) arc_slot(WHEEL_C, H_RHO, HANDLE_A0 - FIN_HALF, HANDLE_A0 + FIN_HALF, HW_SLOT - 1.0 - 1.9, 12); }     // the dish stops short of the edge all round: a flat rim 1.3 mm wide, no thin lip
    }
    ey(Y_WH1 - 0.01, Y_CV0 - 0.1) arc_slot(WHEEL_C, H_RHO, HANDLE_A0 - FIN_HALF, HANDLE_A0 + FIN_HALF, HW_FIN, 12);
}

// ================================================================== FRAME WHEEL (short sprocket + dial; prints with its teeth flat on the bed)
DIAL_PT = 1.0;                                                 // v2.11: a raised arrowhead on the dial, five layers tall, in place of the notch in its rim: the notch could not be seen in a part of one colour.
                                                               // The dial stays round: a nose on it would pass 0.1 mm from the big knob.  Printed with a change of filament at the arrowhead's first layer, the arrowhead is white
module dial_arrow2d() offset(r = 0.4, $fn = 24) polygon([[5.4, 0], [-2.6, 3.4], [-2.6, -3.4]]);                       // its tip is 0.2 mm inside the rim; it comes back to the arrowhead on the body once per picture.  Nothing engraved
module dial_arrow() translate([0, 0, DIAL_Z[1] - 0.01]) linear_extrude(DIAL_PT + 0.01) rotate(90) dial_arrow2d();
module roller_arrow(lift = 0) translate([ROLLER[0], ROLLER[1], lift]) dial_arrow();
// v2.12 (tools/motion.py): each tooth tapers STRAIGHT from 1.5 mm at its root to 0.4 at its tip.  Up to v2.11 it kept 1.0 mm of width to within 0.3 mm of the tip, and on the way into a perforation
// (where the film comes off the gate, before it lies on the drum) that shoulder came to 0.06 to 0.09 mm from the hole's edge: less than a printer's error.  The straight taper leaves 0.18 to 0.22 mm.
module tooth2d() polygon([[R_ROLL - 0.3, -0.75], [R_ROLL + TOOTH, -0.2], [R_ROLL + TOOTH, 0.2], [R_ROLL - 0.3, 0.75]]);   // 1.5 mm wide at its root, 1.2 high: the perforation is 2.0 x 2.8
module star2d() { circle(R_ROLL); for (k = [0 : 7]) rotate(45 * k) tooth2d(); }
module roller(lift = 0, arrow = true) translate([ROLLER[0], ROLLER[1], lift]) {     // 20 mm tall on a 12 mm base.  Printed as it stands in the camera: teeth down
    translate([0, 0, WH_Z[0] + 0.39]) cylinder(r = R_ROLL, h = WH_Z[1] - WH_Z[0] - 0.39);                               // short drum: the film's top band rides on it
    translate([0, 0, WH_Z[0] + 0.39]) linear_extrude(TOOTH_Z - 0.39) star2d(); translate([0, 0, WH_Z[0]]) linear_extrude(0.4) offset(delta = -0.15) star2d();   // 8 teeth = 8 perforations = one picture per turn.  Each tooth is a plain 1.5 mm high block standing on the bed.  (The two layers on the bed are drawn 0.15 smaller: elephant's foot lands on size)
    translate([0, 0, WH_Z[1] - 0.01]) cylinder(r = SHAFT_R, h = H + 0.22 - WH_Z[1]);                                   // neck
    translate([0, 0, COLLAR_Z[0] - COLLAR_R + SHAFT_R]) cylinder(r1 = SHAFT_R, r2 = COLLAR_R, h = COLLAR_R - SHAFT_R);  // 45 degrees under the collar: prints without support.  It touches nothing: the wheel stands on the nose
    translate([0, 0, COLLAR_Z[0] - 0.01]) cylinder(r = COLLAR_R, h = COLLAR_Z[1] - COLLAR_Z[0] + 0.01);                // collar: the fork's lips hold it
    translate([0, 0, H + 0.2]) cylinder(r1 = SHAFT_R, r2 = DIAL_R, h = DIAL_R - SHAFT_R + 0.01);                       // 45 degrees under the dial
    translate([0, 0, DIAL_Z[0]]) cylinder(r = DIAL_R, h = DIAL_Z[1] - DIAL_Z[0]);
    if (arrow) dial_arrow();
}

// ================================================================== WIND KNOB, and the TAKE-UP SPOOL (which has its own knob)
GRIP_D = 0.8;                                                    // how deep the saw teeth are: 0.8 mm (the head has no skirt: what counts for light is its radius between two teeth)
module grip2d(r, n) offset(r = 0.4) offset(delta = -0.4) polygon([for (k = [0 : n - 1], t = [0, 0.31, 0.63, 0.94]) pol([0, 0], r - GRIP_D + GRIP_D * t / 0.94, 360 * (k + t) / n)]);
// Saw teeth round the knob instead of fine knurling or an engraved arrow: the fingers catch when the knob is turned the right way and slip the other way.  It is one outline, so it prints as plain walls.
HEAD_GAP = 0.05; HEAD_H = 7.0;                                                  // v2.7: the heads REST on the top of the body (they stood 0.4 mm clear): their own weight closes the gap that light came in by
module knob_grip2d(cw, r) if (cw) grip2d(r, round(r * 1.1)); else mirror([1, 0]) grip2d(r, round(r * 1.1));
module knob_head(cw, r = 9) translate([0, 0, H + HEAD_GAP]) {    // one plain outline from the bed up: no skirt, nothing that grows outward
    linear_extrude(HEAD_H - HEAD_GAP - BED_CHAMFER + 0.01) knob_grip2d(cw, r);
    translate([0, 0, HEAD_H - HEAD_GAP - BED_CHAMFER]) linear_extrude(BED_CHAMFER, scale = (r - BED_CHAMFER) / r) knob_grip2d(cw, r);   // v2.17: the bed chamfer on the knob's top (it prints head down)
}
module knob_stem(r = KN_R, cr = KN_CR) {
    translate([0, 0, ZC1 - 0.3]) cylinder(r = r, h = H + 0.41 - ZC1 + 0.3);                             // solid shaft
    translate([0, 0, KN_CZ[0]]) cylinder(r = cr, h = KN_CZ[1] - KN_CZ[0]);                              // the ring: 1 mm flat, rides in the pocket in the lower half of the top wall
    translate([0, 0, KN_CZ[1] - 0.01]) cylinder(r1 = cr, r2 = r, h = cr - r);                           // 45 degrees, 1.2 mm: the only place on a knob where the print grows outward
}
module knob(c = CASS, lift = 0) translate([c[0], c[1], lift]) {      // wind knob: turns the spool inside the cassette.  Prints head down
    knob_head(WIND_CW, WIND_HEAD); knob_stem();
    difference() {
        translate([0, 0, FORK_Z0]) cylinder(r = FORK_R, h = ZC1 - 0.29 - FORK_Z0);
        translate([-5, -FORK_GAP / 2, FORK_Z0 - 1]) cube([10, FORK_GAP, ZC1 - 0.3 - FORK_Z0 + 1]);         // the slot
        hull() { translate([-5, -FORK_GAP / 2 - 0.3, FORK_Z0 - 0.01]) cube([10, FORK_GAP + 0.6, 0.01]); translate([-5, -FORK_GAP / 2, FORK_Z0 + 0.5]) cube([10, FORK_GAP, 0.01]); }   // its mouth is flared: the bar finds it
        translate([0, 0, FORK_Z0 - 0.01]) difference() { cylinder(r = FORK_R + 1, h = 0.4); cylinder(r1 = FORK_R - 0.4, r2 = FORK_R, h = 0.41); }                               // and the end is chamfered
    }
    for (s = [-1, 1]) intersection() {                                                                 // each prong is thicker at its root: no sharp corner to start a crack
        translate([0, 0, FORK_Z0]) cylinder(r = FORK_R, h = ZC1 - 0.29 - FORK_Z0);
        rotate([90, 0, 90]) linear_extrude(10, center = true) polygon([[s * (FORK_GAP / 2 + 0.01), ZC1 - 0.29], [s * (FORK_GAP / 2 + 0.01), ZC1 - 0.9], [s * (FORK_GAP / 2 - 0.6), ZC1 - 0.29]]);
    }
}
// Take-up spool.  ONE plain column 11.2 mm thick from its knob to its journal, with one small ring.  No flange, no cap, no thread:
// the film roll sits between two solid steps in the body (LEDGE_Z, LEDGE2_Z).
module spool() translate([SPOOL[0], SPOOL[1], 0]) difference() {          // prints knob down
    union() {
        knob_head(TAKE_CW, TAKE_HEAD); knob_stem(SP_KR, SP_KCR);                                        // the stem is as thick as the core
        translate([0, 0, -SP_F]) cylinder(r = CORE_R, h = ZC1 - 0.29 + SP_F);                               // core and stem: one column
        translate([0, 0, SP_B]) cylinder(r = JRN_R, h = -SP_F - SP_B + 0.01);                               // journal: turns in the slot under the chamber floor
    }
    translate([0.8, -0.5, -SP_F - 0.01]) cube([CORE_R, 1.0, 2 * SP_F + 0.01]);                        // the film's tip tucks in here: the slot runs the whole width of the film, so any end fits, trimmed or not
}
// The pinhole experiment (v2.16).  Leave the lens out.  A thin metal pinhole disc lies on the lens seat, over the port, and the pinhole ring is pressed in on top of it:
// the lens pocket's own three crush ribs hold the ring, and the ring clamps the disc flat on the seat.  No glue.  Set the wheel to the large dot; hold the rocker level and count.
//   The disc is a bought part in the kit: PD_D across, about 0.05 mm brass or steel shim, laser-drilled 0.25 mm (tools/pinhole.py: the best hole at this distance is 0.24).
//   Made at home: a piece of drinks-can aluminium (about 0.1 mm), pricked with a pin.  Any thickness from 0.05 to 0.12 mm works: the ring's underside is flat and it is pushed
//   down until it stops ON THE DISC (the ribs hold it at any depth), so the disc is always clamped, never loose under a ring that has bottomed on the seat.
//   Light: the disc covers the port's octagon (3.68 mm to a corner) with at least 0.9 mm to spare, even pushed to one side of the pocket on the thinnest printer; clamped flat, no gap.
//   The ring stands PR_UP proud of the plate's face, in the pocket's chamfered mouth: a fingernail lifts it out.  Then tip the camera and the disc drops out.
PD_D = 10.5; PD_T = 0.10; PD_HOLE = 0.25;   // the pinhole disc: across, thick (drawn; 0.05 to 0.12 works), hole
PR_H = 2.3; PR_BORE = 2.0;                  // the ring: tall, and the radius of its bore at the disc.  The bore opens at 45 degrees: wider than the 41 degrees the picture's corners need
PR_UP = Y_SEAT + PD_T + PR_H - Y_CVF;       // how far it stands proud of the front plate (0.8 mm with a 0.1 mm disc)
module pinring(ys = Y_SEAT + PD_T) difference() { union() { cyl_y([0, 0], LENS_D / 2 - 0.05 - BED_CH_FIT, ys, ys + BED_CH_FIT, LENS_D / 2 - 0.05); cyl_y([0, 0], LENS_D / 2 - 0.05, ys + BED_CH_FIT - 0.01, ys + PR_H); }   /* v2.17: chamfered at the clamping face (on the bed): a lead-in for the ribs */ cyl_y([0, 0], PR_BORE, ys - 0.01, ys + PR_H + 0.01, PR_BORE + PR_H + 0.02); }
module pindisc() difference() { cyl_y([0, 0], PD_D / 2, Y_SEAT, Y_SEAT + PD_T); cyl_y([0, 0], PD_HOLE / 2, Y_SEAT - 1, Y_SEAT + 1); }     // a bought part (display and checks only)
module pinring_v215(ys = Y_SEAT) difference() { cyl_y([0, 0], LENS_D / 2 - 0.05, ys + 0.05, ys + 1.45); cyl_y([0, 0], 2.0, ys, ys + 1.5, 3.5); }     // v2.15: clamped kitchen foil.  Retired, unused
// v2.14 the near ring (optional; for the lesson on focus): 0.4 mm, two layers, under the lens.  The camera is then set for 1.5 m, not 3.7 m.  Same crush ribs; the lens still sits below the plate's face.
module nearring() difference() { cyl_y([0, 0], LENS_D / 2 - 0.05, Y_SEAT, Y_SEAT + 0.4); cyl_y([0, 0], 4.3, Y_SEAT - 1, Y_SEAT + 2); }

// ================================================================== things you salvage (display and checks only)
module shim_ring(i = 0) difference() { cyl_y([0, 0], 5.7, Y_SEAT + 0.2 * i, Y_SEAT + 0.2 * (i + 1)); cyl_y([0, 0], 4.3, Y_SEAT - 1, Y_SEAT + 2); }
module lens() translate([0, Y_SEAT - 28.40, 0]) {                // salvaged 32 mm meniscus, flange on the seat
    difference() {
        union() { intersection() { translate([0, 31.47 - 9.08, 0]) sphere(9.08, $fn = 64); cyl_y([0, 0], 5.35, 25.4, 31.6); }
                  cyl_y([0, 0], LENS_D / 2 - 0.05, 28.40, 28.40 + LENS_FL); }
        translate([0, 31.47 - 2.2 - 19.82, 0]) sphere(19.82, $fn = 96);
    }
}
D_C = [-cos(DELTA_L), -sin(DELTA_L)]; N_C = [-sin(DELTA_L), cos(DELTA_L)];      // lip direction (toward the cassette) and its emulsion-side normal
module cassette() {
    translate([CASS[0], CASS[1], 0]) { translate([0, 0, ZC0 - 3.5]) cylinder(r = 4.3, h = 3.51); translate([0, 0, ZC0]) cylinder(r = 12.5, h = 43.4);
                                       translate([0, 0, ZC0 + 43.4]) cylinder(r = 3.75, h = 1.0); }
    ez(ZC0 + 0.6, ZC0 + 42.8) polygon([LIP_TIP + 1.5 * N_C, LIP_TIP - 1.5 * N_C, LIP_TIP + 13 * D_C - 1.5 * N_C, LIP_TIP + 16 * D_C + 1.5 * N_C]);   // felt-lined lip
}
function ctan(c1, r1, c2, r2) = let(d = c2 - c1, D = norm(d), th = atan2(d[1], d[0]), b = acos((r1 + r2) / D)) [c1 + r1 * [cos(th + b), sin(th + b)], c2 - r2 * [cos(th + b), sin(th + b)], th + b];
module film_geom(roll = ROLL_FULL, loose = false) {         // the film path, lip -> guide -> drum -> roller -> take-up roll
    t = FILM_T; ct = ctan(ROLLER, R_ROLL + t / 2, SPOOL, roll);
    a0 = atan2(CF[1] - GUIDE[1], CF[0] - GUIDE[0]); a1 = atan2(CF[1] - ROLLER[1], CF[0] - ROLLER[0]);
    sp = SPOOL + roll * [cos(250), sin(250)];
    pts = loose ? concat([LIP_TIP + 13 * D_C, LIP_TIP], [for (a = [-A_L + 4 : 2 : A_R - 6]) arcp(a, RF + 0.02 + t / 2)], [sp])
                : concat([LIP_TIP + 13 * D_C, LIP_TIP],
                         [for (a = [90 + DELTA_L : -6 : a0]) pol(GUIDE, R_G + 0.22 + t / 2, a)],
                         [for (a = [-A_L : 2 : A_R]) arcp(a, RF + 0.02 + t / 2)],
                         [for (a = [a1 : -6 : ct[2]]) pol(ROLLER, R_ROLL + t / 2, a)], [ct[0], ct[1]]);
    ez(-FILM_W / 2, FILM_W / 2) {
        for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) circle(d = t, $fn = 6); translate(pts[i + 1]) circle(d = t, $fn = 6); }
        translate(SPOOL) difference() { circle(roll); circle(CORE_R + 0.05); }
    }
}
module film(roll = ROLL_FULL) color([0.45, 0.3, 0.2, 0.9]) film_geom(roll);

// lens gauge: try the lens in each hole; the one it presses into snugly is your LENS_D.  No calipers needed.
GAUGE = [11.0, 11.25, 11.5, 11.75, 12.0, 12.25, 12.5, 12.75, 13.0];
module lensgauge() difference() {
    translate([0, -4, 0]) cube([len(GAUGE) * 14.5 + 1, 22, 1.2]);
    for (i = [0 : len(GAUGE) - 1]) {
        translate([8 + 14.5 * i, 7, -1]) cylinder(d = GAUGE[i], h = 3, $fn = 90);
        translate([8 + 14.5 * i, -1.6, 0.8]) linear_extrude(1) text(str(GAUGE[i] * 100), size = 2.6, halign = "center", font = "Liberation Sans:style=Bold");
    }
}
// key gauge: push each end into the hole in the top of a film cassette, over the bar.  The largest one that goes in is your FORK_R.
KEYS = [2.9, 3.1, 3.3];
module keygauge() { translate([-6, -5, 0]) cube([len(KEYS) * 12, 10, 1.6]);
    for (i = [0 : len(KEYS) - 1]) translate([12 * i, 0, 0]) { difference() { cylinder(r = KEYS[i], h = 1.6 + 6); translate([-5, -FORK_GAP / 2, 1.6 + 3]) cube([10, FORK_GAP, 4]); }
        translate([-4.5, -4.6, 1.2]) linear_extrude(0.8) text(str(KEYS[i] * 20), size = 2.4, font = "Liberation Sans:style=Bold"); } }
// fit gauge: a comb of slots and a 3 mm key.  The narrowest slot the key drops into tells how fat or thin YOUR printer prints its walls
// (tools/tune.py turns that number into one slicer setting).  The slots are 3.0 mm + 0.1 x their number.
GSLOT = [for (i = [-3 : 8]) 3.0 + 0.1 * i];
module fitgauge() {
    L = len(GSLOT) * 7.5 + 3;
    difference() {
        union() { translate([0, 0, 0.2]) cube([L, 13, 1.4]); translate([0.3, 0.3, 0]) cube([L - 0.6, 12.4, 0.21]); }
        for (i = [0 : len(GSLOT) - 1]) { translate([3.5 + 7.5 * i, 6, -1]) cube([GSLOT[i], 8, 4]); translate([3.2 + 7.5 * i, 6, -1]) cube([GSLOT[i] + 0.6, 8, 1.21]);     // slots (wider on the bed layer: elephant's foot is not what this measures)
            translate([3.5 + 7.5 * i + GSLOT[i] / 2, 1.2, 1.2]) linear_extrude(1) text(str(i - 3), size = 3.2, halign = "center", font = "Liberation Sans:style=Bold"); }
    }
    translate([0, -13, 0]) { translate([0, 0, 0.2]) cube([14, 9, 1.4]); translate([0.3, 0.3, 0]) cube([13.4, 8.4, 0.21]);                     // the key: a 3.0 mm tab on a handle
        translate([5.5, 8.99, 0.2]) cube([3.0, 9, 1.4]); translate([5.8, 8.99, 0]) cube([2.4, 8.7, 0.21]); }
}
module cooltower() cylinder(r = 4, h = H + HEAD_H - SP_B);          // printed beside the spool: the nozzle goes away each layer, so the spool's thin top can cool
// ================================================================== assembly, print layouts
EX = [["body", [0, 0, 0]], ["back", [0, -45, 0]], ["front", [0, 42, 0]], ["blade", [0, 27, 0]], ["wheel", [0, 13, 0]],
      ["roller", [0, -30, 0]], ["knob", [0, 0, 28]], ["spool", [0, -30, 0]], ["lens", [0, 54, 0]]];
function exv(n) = EX[search([n], EX)[0]][1] * EXPLODE;
module part(n) {
    if (n == "body")   color([0.20, 0.21, 0.24]) body();
    if (n == "back")   color([0.26, 0.28, 0.32]) back();
    if (n == "front")  color([0.93, 0.46, 0.13]) front();
    if (n == "blade")  translate([0, 0, SLID]) color(DARK ? [0.10, 0.10, 0.11] : [0.20, 0.62, 0.60]) blade();
    if (n == "wheel")  translate([0, 0, SLID]) color([0.95, 0.80, 0.25]) wheel();
    if (n == "roller") color([0.25, 0.55, 0.85]) roller(ROLL_UP);
    if (n == "knob")   color([0.85, 0.20, 0.18]) knob(CASS);
    if (n == "spool")  color([0.85, 0.20, 0.18]) spool();
    if (n == "lens")   translate([0, 0, SLID]) color([0.7, 0.85, 0.95, 0.6]) lens();
    if (n == "pinring") translate([0, 0, SLID]) color([0.2, 0.2, 0.22]) pinring();
    if (n == "pindisc") translate([0, 0, SLID]) color([0.80, 0.70, 0.45]) pindisc();
    if (n == "nearring") translate([0, 0, SLID]) color([0.2, 0.2, 0.22]) nearring();
    if (n == "plate1") color([0.58, 0.30, 0.78]) plate1();
    if (n == "slide1") translate([0, 0, SLID]) color([0.2, 0.2, 0.22]) slide1(P1_UP);
    if (n == "shims")  translate([0, 0, SLID]) color([0.95, 0.55, 0.20]) shim_ring(0);
}
module p_layout(n) {
    if (n == "p_body")   translate([0, 0, Y_FRONT]) rotate([-90, 0, 0]) body();
    if (n == "p_back")   translate([0, 0, -(Y_RIM - DOOR_T)]) rotate([90, 0, 0]) back();
    if (n == "p_front")  translate([0, 0, Y_CVF]) rotate([-90, 0, 0]) front(0);
    if (n == "p_blade")  translate([0, 0, Y_SC1]) rotate([-90, 0, 0]) blade(0);
    if (n == "p_wheel")  translate([0, 0, -Y_WH0]) rotate([90, 0, 0]) wheel(0);
    if (n == "p_roller") translate([0, 0, -WH_Z[0]]) roller();
    if (n == "p_knob")   translate([0, 0, H + HEAD_H]) rotate([180, 0, 0]) knob(CASS, 0);
    if (n == "p_spool")  translate([0, 0, H + HEAD_H]) rotate([180, 0, 0]) spool();
    if (n == "p_lensgauge") lensgauge();
    if (n == "p_keygauge") keygauge();
    if (n == "p_fitgauge") fitgauge();
    if (n == "p_tower") cooltower();
    if (n == "p_pinring") translate([0, 0, -(Y_SEAT + PD_T)]) rotate([90, 0, 0]) pinring();     // prints with the face that clamps the disc on the bed: flat, the flattest face there is
    if (n == "p_pindisc") translate([0, 0, -Y_SEAT]) rotate([90, 0, 0]) pindisc();     // (a bought part: drawn for the guide only)
    if (n == "p_nearring") translate([0, 0, -Y_SEAT]) rotate([90, 0, 0]) nearring();
    if (n == "p_plate1") translate([0, 0, Y_CVF]) rotate([-90, 0, 0]) plate1(0);
    if (n == "p_slide1") translate([0, 0, -(Y_FRONT + 0.1)]) rotate([90, 0, 0]) slide1(0);
    if (n == "p_shims")  for (i = [0 : 2]) translate([13 * i, 0, -Y_SEAT]) rotate([90, 0, 0]) shim_ring(0);     // three 0.2 mm focus shims
}
// ================================================================== picture guide (tools/guide_render.py drives this)
G_OLD = [];        // parts already in place: drawn pale
G_NEW = [];        // parts being added: drawn in colour, pulled out along their vector, with an arrow
G_VECS = [];       // one vector per new part
G_REV = [];        // new parts that are being taken OUT (arrow reversed)
G_ARROWS = [];     // extra straight arrows [[from], [to]]
G_TURNS = [];      // curved arrows [[x, y, z], radius, clockwise seen from above (1) or not (0)]
G_P = "p_body";    // PART = "g_print": one part as printed, in its colour
G_AUTO = true;        // draw the arrow of each new part by itself (off for film frames)
G_ROT = [0, 0, 0];     // the whole guide picture turned (to show the plate lying on the table)
G_MESH = false;    // draw the front plate from its exported mesh (build/asm/front.stl): the preview draws its many cuts wrongly otherwise
G_PHI = PHI; G_STOP = STOP; G_SLID = 0; G_SIDE = 0;      // G_SLID, G_SIDE: the front plate and what it carries drawn this far up and this far toward the way out (the two moves of its mount)
G_UP = 0;             // the first plate's slide drawn this far up (0 = shut, P1_T = open)
G_TRUE = false;       // true: the four parts light must not pass drawn black, as they are printed.  false (the guide): shutter teal, aperture wheel yellow, back grey, so each can be followed in the pictures
G_RAINBOW = false;    // a colourway to look at, not adopted: red spool, orange plate, yellow wheel, green wind knob, blue frame wheel, indigo shutter, violet film can; body black, back white
function g_col(n) = n == "front" ? [0.93, 0.46, 0.13] : n == "wheel" ? (G_TRUE ? [0.20, 0.21, 0.24] : [0.95, 0.78, 0.20]) : n == "blade" ? (G_RAINBOW ? [0.27, 0.22, 0.62] : G_TRUE ? [0.20, 0.21, 0.24] : [0.15, 0.62, 0.60])
    : n == "spool" ? [0.85, 0.20, 0.18] : n == "knob" ? [0.35, 0.72, 0.25]           // v2.11: the wind knob has its own colour (green: print services stock it), so the guide can tell the two knobs apart by name
    : n == "roller" ? [0.22, 0.52, 0.86] : n == "lens" ? [0.55, 0.80, 0.95] : n == "pinring" ? [0.20, 0.21, 0.24] : n == "pindisc" ? [0.80, 0.70, 0.45] : n == "can" ? [0.58, 0.30, 0.78]
    : n == "cassette" ? [0.90, 0.68, 0.10] : n == "film" || n == "film_loose" || n == "film_full" ? [0.50, 0.32, 0.20] : n == "shims" ? [0.95, 0.55, 0.20] : n == "tape" ? [0.70, 0.85, 0.95]
    : n == "plate1" ? [0.58, 0.30, 0.78] : n == "slide1" ? [0.13, 0.13, 0.15]          // v2.13: the first plate is violet, so the two plates can be told apart by name; its slide is black (it is what keeps the light out)
    : n == "back" ? (G_RAINBOW ? [0.93, 0.93, 0.91] : G_TRUE ? [0.30, 0.32, 0.36] : [0.80, 0.81, 0.83]) : (G_RAINBOW ? [0.15, 0.16, 0.18] : G_TRUE ? [0.26, 0.28, 0.32] : [0.22, 0.23, 0.26]);   // v2.13: the back is drawn light grey and the body near black, so the two can be told apart in every picture
function g_anchor(n) = n == "wheel" ? [WHEEL_C[0], Y_WH1, WHEEL_C[1]] : n == "blade" ? [8, Y_SC1, 9] : n == "front" || n == "plate1" ? [-14, Y_CVF, 14] : n == "slide1" ? [0, Y_FRONT, 0]
    : n == "lens" || n == "pinring" || n == "pindisc" ? [0, 31.8, 0] : n == "roller" ? [ROLLER[0], ROLLER[1] - 6, 0]
    : n == "spool" ? [SPOOL[0], SPOOL[1] - 10, 0] : n == "knob" ? [CASS[0], CASS[1], H + HEAD_H] : n == "back" ? [22, Y_RIM - DOOR_T, 0] : n == "cassette" ? [CASS[0], CASS[1] - 12.5, 0]
    : n == "shims" ? [0, Y_SEAT, 0] : n == "tape" ? [0, -1, 0] : [0, 0, 0];
module arrow3(p0, p1, r = 0.7) { v = p1 - p0; L = norm(v);
    color([0.08, 0.08, 0.10]) translate(p0) rotate([0, acos(v[2] / L), atan2(v[1], v[0])]) { cylinder(r = r, h = max(L - 5, 0.1), $fn = 16); translate([0, 0, max(L - 5, 0)]) cylinder(r1 = 2.3, r2 = 0, h = 5, $fn = 20); } }
module turn3(c, r, cw) color([0.08, 0.08, 0.10]) translate(c) mirror([0, cw ? 1 : 0, 0]) {
    rotate([0, 0, 30]) rotate_extrude(angle = 255, $fn = 60) translate([r, 0]) circle(0.75, $fn = 12);
    rotate([0, 0, 285]) translate([r, 0, 0]) rotate([-90, 0, 0]) cylinder(r1 = 2.4, r2 = 0, h = 5.5, $fn = 20); }
module g_geom(n) {
    if (n == "body") body(); if (n == "back") back(); if (n == "front") translate([-G_SIDE, 0, G_SLID]) { if (G_MESH) import("../build/asm/front.stl", convexity = 10); else front(0); } if (n == "blade") translate([-G_SIDE, 0, G_SLID]) blade(G_PHI); if (n == "wheel") translate([-G_SIDE, 0, G_SLID]) wheel(G_STOP);
    if (n == "plate1") translate([-G_SIDE, 0, G_SLID]) { if (G_MESH) import("../build/asm/plate1.stl", convexity = 10); else plate1(0); } if (n == "slide1") translate([-G_SIDE, 0, G_SLID]) slide1(G_UP);
    if (n == "roller") roller(ROLL_UP, false); if (n == "knob") knob(CASS); if (n == "spool") spool(); if (n == "lens") translate([-G_SIDE, 0, G_SLID]) lens(); if (n == "pinring") translate([-G_SIDE, 0, G_SLID]) pinring(); if (n == "pindisc") translate([-G_SIDE, 0, G_SLID]) pindisc();
    if (n == "can") translate([-84, 12, -H]) { cylinder(r = 15.5, h = 49, $fn = 64); translate([0, 0, 49]) cylinder(r = 16.6, h = 7, $fn = 64); }      // a sketch of a film can, for the colour picture only: not a designed part
    if (n == "cassette") cassette(); if (n == "film_loose") film_geom(CORE_R + 0.3, true); if (n == "film") film_geom(CORE_R + 0.3); if (n == "film_full") film_geom();
    if (n == "shims") translate([0, 0, G_SLID]) shim_ring(0);
    if (n == "tape") ez(-13.5, 13.5) polygon(concat([for (a = [-24 : 3 : 24]) arcp(a, RF + 0.05)], [for (a = [24 : -3 : -24]) arcp(a, RF + 0.35)]));   // frosted tape across the gate for the focus check
}
module guide() {
    for (n = G_OLD) { color(n == "front" ? g_col("front") : n == "body" ? [0.60, 0.62, 0.66] : n == "cassette" ? [0.86, 0.78, 0.50] : n == "film" || n == "film_full" || n == "film_loose" ? [0.62, 0.50, 0.42] : [0.83, 0.84, 0.86]) g_geom(n); if (n == "roller") color([0.98, 0.98, 0.96]) roller_arrow(ROLL_UP); }
    for (i = [0 : 1 : len(G_NEW) - 1]) { n = G_NEW[i]; v = len(G_VECS) > i ? G_VECS[i] : [0, 0, 0]; a = g_anchor(n);
        translate(v) { color(g_col(n)) g_geom(n); if (n == "roller") color([0.98, 0.98, 0.96]) roller_arrow(ROLL_UP); }    // the arrowhead on the dial, in its second colour
        if (G_AUTO && norm(v) > 12) { rev = len(search([n], G_REV)) > 0 && search([n], G_REV)[0] != [];
            if (rev) arrow3(a + 0.18 * v, a + 0.80 * v); else arrow3(a + 0.80 * v, a + 0.16 * v); } }
    for (q = G_ARROWS) arrow3(q[0], q[1]);
    for (q = G_TURNS) turn3(q[0], q[1], q[2]);
}
module assembly() {
    for (e = EX) if (e[0] != "back" || SHOW_BACK) translate(exv(e[0])) part(e[0]);
    if (SHOW_FILM && EXPLODE == 0) { film(); color([0.85, 0.65, 0.1]) cassette(); }
}
function g_of(p) = p == "p_body" ? "body" : p == "p_back" ? "back" : p == "p_front" ? "front" : p == "p_blade" ? "blade" : p == "p_wheel" ? "wheel" : p == "p_roller" ? "roller"
    : p == "p_knob" ? "knob" : p == "p_shims" ? "shims" : p == "p_plate1" ? "plate1" : p == "p_slide1" ? "slide1" : p == "p_pinring" ? "pinring" : p == "p_pindisc" ? "pindisc" : "spool";
if (PART == "guide") rotate(G_ROT) guide();
else if (PART == "g_print") color(g_col(g_of(G_P))) p_layout(G_P);
else if (PART == "asm") { if (SECTION) difference() { assembly(); translate([-100, -100, 0]) cube([200, 200, 100]); } else assembly(); }
else if (PART == "film") film();
else if (PART == "film_empty") film(CORE_R + 0.3);
else if (PART == "cassette") cassette();
// shutter test slab: the front 6 mm of the body under the front plate.  Print it first (15 minutes) with the front plate,
// blade and wheel, and try the shutter and the slide-on fit before spending hours on the body.
else if (PART == "p_test")   translate([0, 0, Y_FRONT]) rotate([-90, 0, 0]) intersection() { body(); translate([FX0 - 2.5, Y_FRONT - 6, -H - 1]) cube([FX1 - FX0 + 9, 6.1, 2 * H + 2]); }
// print layouts: the face that goes on the bed
else if (len(PART) > 2 && PART[0] == "p" && PART[1] == "_") p_layout(PART);
else part(PART);
