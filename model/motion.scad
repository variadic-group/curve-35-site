// ONE-135 moving pictures.  tools/motionfilm.py writes one small file per frame that sets P (and the arrows) and includes this one.
// Every part is drawn from its exported mesh (build/asm/*.stl), moved by the same matrix tools/motion.py measured it with: what is seen is what was tested.
P = [];        // [mesh file, [r, g, b, a], [12 numbers: the top three rows of its matrix]]
ARROWS = [];   // straight arrows [[from], [to]]
TURNS = [];    // curved arrows [[x, y, z], radius, clockwise seen from above (1) or not (0)]
ROT = [0, 0, 0];
module arrow3(p0, p1, r = 0.7) { v = p1 - p0; L = norm(v);
    color([0.08, 0.08, 0.10]) translate(p0) rotate([0, acos(v[2] / L), atan2(v[1], v[0])]) { cylinder(r = r, h = max(L - 5, 0.1), $fn = 16); translate([0, 0, max(L - 5, 0)]) cylinder(r1 = 2.3, r2 = 0, h = 5, $fn = 20); } }
module turn3(c, r, cw) color([0.08, 0.08, 0.10]) translate(c) mirror([0, cw ? 1 : 0, 0]) {
    rotate([0, 0, 30]) rotate_extrude(angle = 255, $fn = 60) translate([r, 0]) circle(0.75, $fn = 12);
    rotate([0, 0, 285]) translate([r, 0, 0]) rotate([-90, 0, 0]) cylinder(r1 = 2.4, r2 = 0, h = 5.5, $fn = 20); }
rotate(ROT) {
    for (p = P) color(p[1]) multmatrix([[p[2][0], p[2][1], p[2][2], p[2][3]], [p[2][4], p[2][5], p[2][6], p[2][7]], [p[2][8], p[2][9], p[2][10], p[2][11]], [0, 0, 0, 1]]) import(p[0], convexity = 6);
    for (q = ARROWS) arrow3(q[0], q[1]);
    for (q = TURNS) turn3(q[0], q[1], q[2]);
}
