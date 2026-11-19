/* Lesson 4: How much light.  Sims: l04_dots (slide the dot), l04_ladder (why 8, 11, 16), l04_sunny (which dot for this sky).
   Figures: fig_l04_guess, fig_l04_area, fig_l04_fnumber, fig_l04_time.
   Numbers: course/FACTS.md (lens 32 mm; dots 1.96, 2.88, 3.34 mm = f/16.4, f/11.1, f/9.6; shutter about 1/322 s; sharp share 99 % and 62 %);
   build/log_dial_exposure.txt part 2 (exposure for each film and sky; the dots are 0, +1.08 and +1.49 steps apart by the model's light figures). */
(function () {
  "use strict";
  var C = window.CURVE, U = C.U, K = U.colours, O = C.OPTICS;
  var T = 'font-family="Inter, sans-serif"';
  var DOT_STEPS = { small: 0, middle: Math.log(0.020199504713705647 / 0.009563471319842108) / Math.LN2, large: Math.log(0.026866487728749458 / 0.009563471319842108) / Math.LN2 };

  C.fig("fig_l04_guess", function () {
    var b = '<rect width="640" height="300" fill="#fff"/>', s = 34;
    b += '<circle cx="170" cy="150" r="' + (2 * s) + '" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/>';
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (p, i) { b += '<circle cx="' + (170 + p[0] * s * 0.98) + '" cy="' + (150 + p[1] * s * 0.98) + '" r="' + (s * 0.94) + '" fill="none" stroke="' + K.plate + '" stroke-width="2.5" stroke-dasharray="' + (i ? "6 4" : "0") + '"/>'; });
    b += '<circle cx="460" cy="150" r="' + s + '" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/>';
    b += '<text x="170" y="40" text-anchor="middle" ' + T + ' font-size="18" font-weight="700" fill="#2D2A26">f/8: a 4 mm hole</text><text x="460" y="40" text-anchor="middle" ' + T + ' font-size="18" font-weight="700" fill="#2D2A26">f/16: a 2 mm hole</text>' +
      '<text x="170" y="270" text-anchor="middle" ' + T + ' font-size="14" fill="#625C53">four f/16 holes fit inside</text><text x="460" y="270" text-anchor="middle" ' + T + ' font-size="14" fill="#625C53">half as wide: a quarter of the light</text>' +
      '<line x1="420" y1="150" x2="500" y2="150" stroke="#2D2A26" stroke-width="1.5"/>';
    return U.svg(640, 300, b, "An f/8 hole is twice as wide as an f/16 hole, and four f/16 holes fit inside it: four times the light.");
  });
  C.fig("fig_l04_area", function () {
    var b = '<rect width="640" height="280" fill="#fff"/>', q = 60;
    b += '<rect x="110" y="110" width="' + q + '" height="' + q + '" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/>';
    for (var i = 0; i < 2; i++) for (var j = 0; j < 2; j++) b += '<rect x="' + (360 + i * q) + '" y="' + (50 + j * q) + '" width="' + q + '" height="' + q + '" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/><text x="' + (360 + i * q + q / 2) + '" y="' + (50 + j * q + q / 2 + 8) + '" text-anchor="middle" ' + T + ' font-size="22" font-weight="700" fill="#9a6a00">' + (1 + i + 2 * j) + "</text>";
    b += '<text x="140" y="200" text-anchor="middle" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">1 wide: 1 square</text><text x="420" y="200" text-anchor="middle" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">2 wide, 2 tall: 4 squares</text>' +
      '<text x="320" y="250" text-anchor="middle" ' + T + ' font-size="15" fill="#625C53">Light comes through the whole area. Twice the width is four times the light.</text>';
    return U.svg(640, 280, b, "A square one unit wide holds one square; a square two units wide holds four. Twice the width, four times the area.");
  });
  C.fig("fig_l04_fnumber", function () {
    var b = '<rect width="640" height="260" fill="#fff"/>', lx = 140, fx = 540, cy = 120;
    b += '<path d="M' + lx + ' 40 Q' + (lx + 22) + " " + cy + " " + lx + ' 200 Q' + (lx - 22) + " " + cy + " " + lx + ' 40Z" fill="' + K.glass + '" stroke="#2D2A26" stroke-width="2.5"/>';
    b += '<rect x="' + (lx + 26) + '" y="30" width="8" height="' + (cy - 20 - 30) + '" fill="#2D2A26"/><rect x="' + (lx + 26) + '" y="' + (cy + 20) + '" width="8" height="' + (210 - cy - 20) + '" fill="#2D2A26"/>';
    b += '<rect x="' + fx + '" y="30" width="10" height="180" fill="#6d4f35"/><line x1="' + lx + '" y1="' + cy + '" x2="' + fx + '" y2="' + cy + '" stroke="#2D2A26" stroke-width="2" stroke-dasharray="6 5"/>';
    b += '<text x="' + ((lx + fx) / 2) + '" y="' + (cy - 10) + '" text-anchor="middle" ' + T + ' font-size="16" font-weight="700" fill="#2D2A26">lens length: 32 mm</text>' +
      '<line x1="' + (lx + 46) + '" y1="' + (cy - 20) + '" x2="' + (lx + 46) + '" y2="' + (cy + 20) + '" stroke="' + K.plate + '" stroke-width="3"/><text x="' + (lx + 54) + '" y="' + (cy + 40) + '" ' + T + ' font-size="15" font-weight="700" fill="' + K.plate + '">hole: 2 mm</text>' +
      '<text x="320" y="245" text-anchor="middle" ' + T + ' font-size="20" font-weight="700" fill="#2D2A26">f-number = 32 ÷ 2 = 16   →   f/16</text>';
    return U.svg(640, 260, b, "The f-number is the lens's length divided by the hole's width: 32 mm divided by 2 mm is 16, f/16.");
  });
  C.fig("fig_l04_time", function () {
    var b = '<rect width="640" height="260" fill="#fff"/>';
    b += '<rect x="80" y="110" width="200" height="80" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/><rect x="380" y="30" width="100" height="160" fill="#FFE9A8" stroke="#2D2A26" stroke-width="3"/>';
    b += '<text x="180" y="215" text-anchor="middle" ' + T + ' font-size="14" fill="#2D2A26">how long →</text><text x="66" y="150" text-anchor="end" ' + T + ' font-size="14" fill="#2D2A26">how bright</text>' +
      '<text x="430" y="215" text-anchor="middle" ' + T + ' font-size="14" fill="#2D2A26">half as long</text><text x="494" y="110" ' + T + ' font-size="14" fill="#2D2A26">twice as bright</text>' +
      '<text x="320" y="248" text-anchor="middle" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">same area, same light, same picture</text>';
    return U.svg(640, 260, b, "Two rectangles with the same area: one wide and low, one narrow and twice as tall. Bright times long is the light the film gets.");
  });

  // ------------------------------------------------------------------ slide the dot
  C.sim("l04_dots", function (el, api) {
    var F = api.facts, wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 0.6, maxH: 440, cls: "sim-light" });
    left.appendChild(U.h("p", { class: "sim-cap" }, "The hole on squared paper: each square is 0.25 mm. Squares inside are counted. Drag across the paper to size the hole."));
    var S = { d: 1.96 };
    var sd = U.slider({ label: "Hole width", min: 1, max: 5, step: 0.01, value: S.d, fmt: function (v) { return v.toFixed(2) + " mm"; }, onInput: function (v) { S.d = v; upd(); } });
    right.appendChild(sd.el);
    var dots = U.h("div", { class: "sim-ctl" }); dots.appendChild(U.h("span", { class: "sim-lab" }, "Your wheel"));
    var dr = U.h("div", { class: "sim-seg" }); dots.appendChild(dr); right.appendChild(dots);
    [["small", 1.96], ["middle", 2.88], ["large", 3.34], ["f/8 (not built)", 4.0]].forEach(function (x, i) { dr.appendChild(U.button(x[0], function () { sd.set(x[1]); }, i === 3 ? "sim-dashed" : "")); });
    var pv = U.stage(right, { aspect: 2 / 3, maxH: 220 });
    right.appendChild(U.h("p", { class: "sim-cap" }, "Light on the film, bright cloud, ISO 400, 1/322 s (simulated)"));
    var set = U.readouts(right, [{ k: "f", label: "f-number", cls: "sim-hi" }, { k: "a", label: "area" }, { k: "x", label: "light vs small" }, { k: "s", label: "sharp, far scene" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap), sc = U.scene(240, 160), count = 0;
    function upd() {
      var d = S.d, N = Math.abs(d - 1.96) < 0.005 ? 16.4 : Math.abs(d - 2.88) < 0.005 ? 11.1 : Math.abs(d - 3.34) < 0.005 ? 9.6 : 32 / d, A = Math.PI * d * d / 4, x = (d / 1.96) * (d / 1.96), steps = Math.log(x) / Math.LN2, sh = O.share(d, false);
      count = 0; var q = 0.25, r = d / 2; for (var i = -Math.ceil(r / q); i < Math.ceil(r / q); i++) for (var j = -Math.ceil(r / q); j < Math.ceil(r / q); j++) if (Math.hypot((i + 0.5) * q, (j + 0.5) * q) < r) count++;
      set({ f: "f/" + N.toFixed(1), a: A.toFixed(1) + " <small>mm²</small>", x: "× " + x.toFixed(2) + " <small>" + (steps >= 0 ? "+" : "") + steps.toFixed(1) + " steps</small>", s: Math.round(sh * 100) + " %" });
      var t = Math.abs(d - 1.96) < 0.02 ? "The small dot: f/16. The sharpest, and the least light." : Math.abs(d - 2.88) < 0.02 ? "The middle dot: about twice the small dot's light (× 2.16), f/11." :
        Math.abs(d - 3.34) < 0.02 ? "The large dot: a third more than the middle (× 1.35), f/9.5. Sharp over about 62 % of a far picture." :
        Math.abs(d - 4) < 0.02 ? "f/8 would need 4.0 mm: half a step more light than the large dot, and softer still away from the middle. Not built." :
        "Width × " + (d / 1.96).toFixed(2) + " of the small dot, light × " + x.toFixed(2) + ".";
      verdict.textContent = t;
      say("Hole " + d.toFixed(2) + " mm: f/" + N.toFixed(1) + ", area " + A.toFixed(1) + " square mm, " + count + " squares of 0.25 mm. " + x.toFixed(2) + " times the small dot's light. " + t);
      st.redraw(); pv.redraw();
    }
    st.draw = function (g, W, H) {
      var cx = W * 0.58, cy = H / 2, px = Math.min(H * 0.86 / 5, W * 0.7 / 5), q = 0.25 * px, r = S.d / 2 * px;
      g.fillStyle = "#fff"; g.fillRect(0, 0, W, H);
      g.strokeStyle = "#e3eef6"; g.lineWidth = 1;
      for (var x = cx % q; x < W; x += q) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }
      for (var y = cy % q; y < H; y += q) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
      g.strokeStyle = "#c3d7e6"; for (var x2 = cx % (q * 4); x2 < W; x2 += q * 4) { g.beginPath(); g.moveTo(x2, 0); g.lineTo(x2, H); g.stroke(); } for (var y2 = cy % (q * 4); y2 < H; y2 += q * 4) { g.beginPath(); g.moveTo(0, y2); g.lineTo(W, y2); g.stroke(); }
      var n = Math.ceil(S.d / 2 / 0.25);
      for (var i = -n; i < n; i++) for (var j = -n; j < n; j++) if (Math.hypot((i + 0.5) * 0.25, (j + 0.5) * 0.25) < S.d / 2) { g.fillStyle = "rgba(242,184,7,.55)"; g.fillRect(cx + i * q + 1, cy + j * q + 1, q - 2, q - 2); }
      // other dots, faint, for comparison
      [1.96, 2.88, 3.34].forEach(function (d) { g.strokeStyle = "rgba(45,42,38,.25)"; g.setLineDash([4, 4]); g.beginPath(); g.arc(cx, cy, d / 2 * px, 0, 7); g.stroke(); });
      g.setLineDash([]); g.strokeStyle = "#2D2A26"; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.stroke();
      g.strokeStyle = api.colour; g.lineWidth = 2; g.beginPath(); g.moveTo(cx - r, cy + r + 14); g.lineTo(cx + r, cy + r + 14); g.stroke();
      U.label(g, S.d.toFixed(2) + " mm", cx, cy + r + 30, { align: "center", color: "#2D2A26", size: 13 });
      // the wheel, small, at the left
      var wx = W * 0.15, wy = H * 0.5, wr = Math.min(W * 0.12, H * 0.36);
      g.fillStyle = "#F2C230"; g.beginPath(); g.arc(wx, wy, wr, 0, 7); g.fill(); g.strokeStyle = "#2D2A26"; g.lineWidth = 2; g.stroke();
      [[1.96, -2.2], [2.88, -0.5], [3.34, 1.2]].forEach(function (h) { var hx = wx + wr * 0.6 * Math.cos(h[1]), hy = wy + wr * 0.6 * Math.sin(h[1]), hr = h[0] / 2 * wr / 7; g.fillStyle = Math.abs(h[0] - S.d) < 0.02 ? "#fff" : "#2D2A26"; g.beginPath(); g.arc(hx, hy, hr, 0, 7); g.fill(); g.strokeStyle = "#2D2A26"; g.stroke(); });
      U.label(g, "the wheel", wx, wy + wr + 18, { align: "center", color: "#625C53", size: 11 });
      U.label(g, count + " squares", W - 10, 22, { align: "right", color: "#2D2A26", size: 15, weight: 700 });
      U.label(g, "× " + ((S.d / 1.96) * (S.d / 1.96)).toFixed(2) + " the small dot", W - 10, 42, { align: "right", color: "#625C53", size: 12 });
    };
    pv.draw = function (g, W, H) { var x = (S.d / 3.34) * (S.d / 3.34); U.paint(g, sc, 0, 0, W, H, 1.0 * x, { vignette: 0.3 }); U.simTag(g, 6, H - 6); };
    U.drag(st.cv, function (x, y, ph) {
      if (ph !== "down" && ph !== "move") return;
      var W = st.w, H = st.h, cx = W * 0.58, cy = H / 2, px = Math.min(H * 0.86 / 5, W * 0.7 / 5);
      if (x < W * 0.3) return;
      sd.set(U.clamp(2 * Math.hypot(x - cx, y - cy) / px, 1, 5));
    });
    upd();
    return { destroy: function () { st.destroy(); pv.destroy(); } };
  });

  // ------------------------------------------------------------------ why 8, 11, 16: build the row yourself
  C.sim("l04_ladder", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var st = U.stage(wrap, { aspect: function (w) { return w < 560 ? 0.95 : 0.42; }, maxH: 460 });
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div", { class: "sim-ctls" }), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var S = { m: 2 };
    var sm = U.slider({ label: "Each step: divide the f-number by", min: 1.2, max: 2, step: 0.01, value: 2, fmt: function (v) { return "÷ " + v.toFixed(2); }, onInput: function (v) { S.m = v; upd(); } });
    left.appendChild(sm.el);
    var row = U.h("div", { class: "sim-row" }); left.appendChild(row);
    row.appendChild(U.button("÷ 2 (the guess)", function () { sm.set(2); })); row.appendChild(U.button("÷ 1.5", function () { sm.set(1.5); })); row.appendChild(U.button("÷ √2 = 1.41", function () { sm.set(Math.SQRT2); }));
    var set = U.readouts(right, [{ k: "w", label: "width each step" }, { k: "l", label: "light each step", cls: "sim-hi" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    function rungs() { var out = []; for (var k = 0; k < 5; k++) out.push(16 / Math.pow(S.m, k)); return out; }
    function nice(N) { var row = [22, 16, 11, 8, 5.6, 4, 2.8, 2]; for (var i = 0; i < row.length; i++) if (Math.abs(N - row[i]) / row[i] < 0.04) return row[i]; return null; }
    function upd() {
      var m = S.m, L = m * m, r = rungs();
      set({ w: "× " + m.toFixed(2), l: "× " + L.toFixed(2) });
      var t = Math.abs(L - 2) < 0.04 ? "That's it. Each step is 1.41 times the width and twice the light, because 1.41 × 1.41 ≈ 2. Rounded: 16, 11, 8, 5.6, 4." :
        L > 2 ? "Each step gives × " + L.toFixed(2) + " the light: more than double. The steps are too big." : "Each step gives × " + L.toFixed(2) + " the light: less than double. Too small.";
      verdict.textContent = t;
      say("Dividing by " + m.toFixed(2) + " each step gives the row " + r.map(function (n) { return "f/" + n.toFixed(1); }).join(", ") + ". " + t);
      st.redraw();
    }
    st.draw = function (g, W, H) {
      var r = rungs(), narrow = W < 560, n = r.length, colW = W / n, maxD = 32 / r[n - 1], scale = Math.min(colW * 0.44, (narrow ? H * 0.12 : H * 0.17)) / (maxD / 2);
      g.fillStyle = "#0d0b09"; g.fillRect(0, 0, W, H);
      var holeY = narrow ? H * 0.17 : H * 0.27, barBase = H - 34, barTop = narrow ? H * 0.42 : H * 0.56, maxSteps = Math.log(Math.pow(S.m, 2 * (n - 1))) / Math.LN2;
      for (var k = 0; k < n; k++) {
        var N = r[k], d = 32 / N, cx = colW * (k + 0.5), rr = Math.min(colW * 0.45, d / 2 * scale), nv = nice(N);
        g.fillStyle = "#FFE58A"; g.beginPath(); g.arc(cx, holeY, rr, 0, 7); g.fill();
        U.label(g, "f/" + (N >= 10 ? N.toFixed(1) : N.toFixed(2)), cx, 22, { align: "center", color: nv ? "#fff" : "#b9b0a2", size: narrow ? 12 : 15, weight: 700 });
        if (nv && Math.abs(S.m * S.m - 2) < 0.04) U.label(g, "→ " + nv, cx, 40, { align: "center", color: api.colour, size: 12 });
        var light = Math.pow(S.m, 2 * k), steps = Math.log(light) / Math.LN2, bh = (barBase - barTop) * (k === 0 ? 0.06 : Math.max(0.06, steps / Math.max(4.2, maxSteps)));
        g.fillStyle = api.colour; g.fillRect(cx - colW * 0.28, barBase - bh, colW * 0.56, bh);
        U.label(g, "× " + (light < 10 ? light.toFixed(1) : Math.round(light)), cx, barBase + 18, { align: "center", color: "#fff", size: narrow ? 11 : 13 });
        if (k) U.label(g, "× " + (S.m * S.m).toFixed(2), colW * k, holeY + (narrow ? H * 0.11 : H * 0.17), { align: "center", color: Math.abs(S.m * S.m - 2) < 0.04 ? "#9BE564" : "#FF8A6B", size: 11 });
      }
      U.label(g, "light, against f/16 (bar height in steps)", 8, barTop - 8, { color: "#b9b0a2", size: 11, weight: 400 });
    };
    upd();
    return { destroy: st.destroy };
  });

  // ------------------------------------------------------------------ which dot for this sky
  C.sim("l04_sunny", function (el, api) {
    var F = api.facts, wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var pv = U.stage(left, { aspect: 2 / 3, maxH: 380 });
    left.appendChild(U.h("p", { class: "sim-cap" }, "The print you would get back (simulated)"));
    var meter = U.stage(left, { aspect: 0.14, maxH: 70, min: 220 });
    var SK = [["full sun", 0], ["hazy sun", 1], ["bright cloud", 2], ["dull, overcast", 3], ["open shade", 4], ["indoors by a window", 8.8], ["indoors, lamps on", 11.1], ["a dim room", 13.1]];
    var S = { sky: 0, iso: 400, dot: "small" };
    right.appendChild(U.choice({ label: "The light", options: SK.map(function (s, i) { return { v: i, label: s[0] }; }), value: 0, onChange: function (v) { S.sky = v; upd(); } }).el);
    right.appendChild(U.choice({ label: "Film speed", options: [100, 200, 400, 800].map(function (x) { return { v: x, label: "ISO " + x }; }), value: 400, onChange: function (v) { S.iso = v; upd(); } }).el);
    var dc = U.choice({ label: "Dot", options: [{ v: "small", label: "small f/16" }, { v: "middle", label: "middle f/11" }, { v: "large", label: "large f/9.5" }], value: "small", onChange: function (v) { S.dot = v; upd(); } });
    right.appendChild(dc.el);
    var best = U.button("Pick the best dot for me", function () { var b = bestDot(); if (b) dc.set(b); }); right.appendChild(best);
    var set = U.readouts(right, [{ k: "o", label: "off by", cls: "sim-hi" }, { k: "r", label: "sunny 16 says" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap), sc = U.scene(270, 180), res = null;
    function off(dot) { return 0.5 - SK[S.sky][1] + DOT_STEPS[dot] + Math.log(S.iso / 400) / Math.LN2; }
    function bestDot() { var c = ["small", "middle", "large"].filter(function (d) { var o = off(d); return o >= -1 && o <= 3; }); if (!c.length) return null; c.sort(function (a, b) { return Math.abs(off(a) - 0.5) - Math.abs(off(b) - 0.5); }); return c[0]; }
    function upd() {
      var o = off(S.dot), b = bestDot(), t;
      res = U.develop(sc, Math.max(-6, o), true);
      if (o >= -1 && o <= 3) t = "Inside the film's window: a good picture." + (b && b !== S.dot ? " The " + b + " dot would be closer still." : "");
      else if (o > 3) t = "Far too much light, even for forgiving film. Try a smaller dot or slower film.";
      else if (b) t = "Too little light. Try the " + b + " dot.";
      else {
        var cnt = S.sky >= 5 ? { 5: 1, 6: 5, 7: 20 }[S.sky] * 400 / S.iso / Math.pow(2, DOT_STEPS[S.dot]) : null;
        t = "Too dark for a snap with any dot. Hold the rocker at its middle click and count" + (cnt ? ": about " + (cnt < 1.5 ? 1 : Math.round(cnt)) + " at the " + S.dot + " dot." : ": a time picture (lesson 5).");
      }
      var rule = S.sky === 0 ? "f/16, 1/" + S.iso + " s" : "<small>for full sun only</small>";
      set({ o: (o >= 0 ? "+" : "−") + Math.abs(o).toFixed(1) + " <small>steps</small>", r: rule });
      verdict.textContent = t;
      say(SK[S.sky][0] + ", ISO " + S.iso + ", " + S.dot + " dot: " + (o >= 0 ? "+" : "") + o.toFixed(1) + " steps from just right. " + t);
      pv.redraw(); meter.redraw();
    }
    pv.draw = function (g, W, H) { U.paint(g, res.print, 0, 0, W, H, 1, { vignette: 0.25 }); U.simTag(g, 8, H - 8); };
    meter.draw = function (g, W, H) {
      var x0 = 14, x1 = W - 14, y = H * 0.42, lo = -5, hi = 5, o = off(S.dot);
      function X(s) { return x0 + (x1 - x0) * (U.clamp(s, lo, hi) - lo) / (hi - lo); }
      g.fillStyle = "#2a251e"; g.fillRect(x0, y - 8, x1 - x0, 16);
      g.fillStyle = "#1d7a46"; g.fillRect(X(-1), y - 8, X(3) - X(-1), 16);
      for (var s = lo; s <= hi; s++) U.label(g, (s > 0 ? "+" : "") + s, X(s), H - 4, { align: "center", color: "#b9b0a2", size: 10, weight: 400 });
      U.label(g, "the film's window", (X(-1) + X(3)) / 2, y + 4, { align: "center", color: "#fff", size: 10 });
      g.fillStyle = o < lo || o > hi ? "#FF6B4A" : "#fff"; g.beginPath(); g.moveTo(X(o), y - 10); g.lineTo(X(o) - 7, y - 20); g.lineTo(X(o) + 7, y - 20); g.fill();
    };
    upd();
    return { destroy: function () { pv.destroy(); meter.destroy(); } };
  });
})();

/* Lesson 4's picture (hero_fig, and its card): the f-number steps.  Each hole has twice the area of the one before, so each step lets in twice the light. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#E8641B", COLINK = "#9A3E0B";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  C.fig("fig_l04_stops", function () {
    var xs = [86, 226, 384, 556], rs = [22, 31.1, 44, 62.2], fs = ["f/16", "f/11", "f/8", "f/5.6"], cy = 170, b = '<rect width="640" height="360" fill="#fff"/>';
    xs.forEach(function (x, i) { b += '<circle cx="' + x + '" cy="' + cy + '" r="' + rs[i] + '" fill="' + COL + '" stroke="' + INK + '" stroke-width="3"/>' + T(x, 278, fs[i], 32, 800, INK, "middle"); });
    for (var i = 0; i < 3; i++) {
      var a = xs[i] + rs[i] + 10, z = xs[i + 1] - rs[i + 1] - 10, m = (a + z) / 2;
      b += '<path d="M' + a + " " + (cy - 10) + " Q" + m + " " + (cy - 70) + " " + z + " " + (cy - 10) + '" fill="none" stroke="' + COLINK + '" stroke-width="3"/>' +
        '<path d="M' + z + " " + (cy - 10) + " l-13 -5 l5 13 z" + '" fill="' + COLINK + '"/>' + T(m, cy - 62, "×2", 28, 800, COLINK, "middle");
    }
    b += T(320, 334, "each step: twice the area, twice the light", 21, 600, "#625C53", "middle");
    return C.U.svg(640, 360, b, "Four holes: f/16, f/11, f/8 and f/5.6. Each hole has twice the area of the one before it, so each step lets in twice the light.");
  });
})();
