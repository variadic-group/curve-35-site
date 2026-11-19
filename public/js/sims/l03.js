/* Lesson 3: Catching light.  Sims: l03_grains (expose, develop, fix, print), l03_window (negative, print, and how wrong the light can be).
   Figures: fig_l03_cut, fig_l03_chain, fig_l03_colour.  Numbers: about 4 silver atoms make a speck; a crystal about 0.001 mm; the film forgives
   1 step too little and 3 too much (build/exposure.json); the camera's three cases +0.5, +0.6, 0.0 steps (build/log_dial_exposure.txt). */
(function () {
  "use strict";
  var C = window.CURVE, U = C.U, K = U.colours;
  var T = 'font-family="Inter, sans-serif"';

  function hexagon(x, y, r, fill, stroke) {
    var p = []; for (var i = 0; i < 6; i++) { var a = Math.PI / 6 + i * Math.PI / 3; p.push((x + r * Math.cos(a)).toFixed(1) + "," + (y + r * Math.sin(a)).toFixed(1)); }
    return '<polygon points="' + p.join(" ") + '" fill="' + fill + '"' + (stroke ? ' stroke="' + stroke + '" stroke-width="1.5"' : "") + "/>";
  }
  C.fig("fig_l03_cut", function () {
    var b = '<rect width="640" height="330" fill="#fff"/>', rnd = U.rng(7);
    b += '<rect x="40" y="70" width="400" height="110" fill="#E9B872" stroke="#2D2A26" stroke-width="2.5"/><rect x="40" y="180" width="400" height="90" fill="#DCEBF2" stroke="#2D2A26" stroke-width="2.5"/>';
    for (var i = 0; i < 46; i++) { var x = 56 + rnd() * 370, y = 84 + rnd() * 84; b += i % 3 ? hexagon(x, y, 6 + rnd() * 4, "#f6f2ea", "#8a7a64") : '<polygon points="' + x + "," + (y - 8) + " " + (x + 8) + "," + (y + 6) + " " + (x - 8) + "," + (y + 6) + '" fill="#f6f2ea" stroke="#8a7a64" stroke-width="1.5"/>'; }
    b += '<line x1="450" y1="125" x2="480" y2="125" stroke="#2D2A26" stroke-width="1.5"/><text x="488" y="120" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">gelatin</text><text x="488" y="138" ' + T + ' font-size="12" fill="#625C53">holding crystals</text>' +
      '<line x1="450" y1="225" x2="480" y2="225" stroke="#2D2A26" stroke-width="1.5"/><text x="488" y="222" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">plastic</text><text x="488" y="240" ' + T + ' font-size="12" fill="#625C53">the clear base</text>' +
      '<line x1="60" y1="300" x2="80" y2="300" stroke="#2D2A26" stroke-width="3"/><text x="88" y="305" ' + T + ' font-size="13" fill="#2D2A26">a crystal: about 0.001 mm across (drawn far bigger)</text>' +
      '<text x="40" y="28" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">The film, cut through and hugely magnified</text>' +
      '<path d="M290 36 L314 66" stroke="' + K.sun + '" stroke-width="4"/><path d="M302 62 L314 66 L316 53" fill="none" stroke="' + K.sun + '" stroke-width="4"/>' +
      '<text x="324" y="58" ' + T + ' font-size="12" font-weight="600" fill="#9a6a00">light comes in here</text>';
    return U.svg(640, 330, b, "A cut through film: a thick clear plastic base, and on it a layer of gelatin holding tiny crystals of silver salt.");
  });
  C.fig("fig_l03_chain", function () {
    var b = '<rect width="660" height="250" fill="#fff"/>', rnd = U.rng(3), names = ["1. light marks", "2. developer", "3. fixer", "4. the negative", "5. the print"], w = 112, gap = 18;
    var cells = []; for (var i = 0; i < 20; i++) cells.push({ x: rnd(), y: rnd(), m: rnd() < (i % 2 ? 0.75 : 0.25) });
    names.forEach(function (n, k) {
      var x0 = 14 + k * (w + gap), y0 = 50;
      b += '<rect x="' + x0 + '" y="' + y0 + '" width="' + w + '" height="' + w + '" rx="10" fill="' + (k >= 2 ? (k === 4 ? "#fbfaf6" : "#e6eef2") : "#efe2c7") + '" stroke="#2D2A26" stroke-width="2"/>';
      if (k < 4) cells.forEach(function (c) {
        var cx = x0 + 12 + c.x * (w - 24), cy = y0 + 12 + c.y * (w - 24);
        if (k === 0) { b += hexagon(cx, cy, 7, "#f6f2ea", "#8a7a64"); if (c.m) b += '<circle cx="' + (cx + 2) + '" cy="' + (cy - 2) + '" r="2.2" fill="#2D2A26"/>'; }
        else if (k === 1) b += hexagon(cx, cy, 7, c.m ? "#1b1a18" : "#f6f2ea", "#8a7a64");
        else if (c.m) b += hexagon(cx, cy, 7, "#1b1a18");
      });
      if (k === 3) b += '<rect x="' + (x0 + 8) + '" y="' + (y0 + 8) + '" width="' + (w - 16) + '" height="' + (w - 16) + '" fill="none"/>';
      if (k === 4) cells.forEach(function (c) { if (!c.m) b += hexagon(x0 + 12 + c.x * (w - 24), y0 + 12 + c.y * (w - 24), 7, "#1b1a18"); });
      b += '<text x="' + (x0 + w / 2) + '" y="' + (y0 + w + 24) + '" text-anchor="middle" ' + T + ' font-size="13" font-weight="700" fill="#2D2A26">' + n + "</text>";
      if (k < 4) b += '<text x="' + (x0 + w + gap / 2) + '" y="' + (y0 + w / 2 + 6) + '" text-anchor="middle" ' + T + ' font-size="18" font-weight="700" fill="' + K.plate + '">›</text>';
    });
    b += '<text x="14" y="28" ' + T + ' font-size="13" fill="#625C53">a speck of ~4 atoms → the whole crystal black → the untouched crystals washed away → print through it: backwards twice</text>';
    return U.svg(660, 250, b, "Five steps: light marks some crystals with specks; developer turns marked crystals black; fixer dissolves the rest; that is the negative; printing through it reverses it again.");
  });
  C.fig("fig_l03_colour", function () {
    var b = '<rect width="640" height="300" fill="#fff"/>', L = [["catches blue", "#3B6FE0", "yellow dye", "#F2C81F"], ["catches green", "#2E9E52", "magenta dye", "#D6338A"], ["catches red", "#D9402B", "cyan dye", "#1FB5C9"]];
    L.forEach(function (l, i) {
      var y = 60 + i * 56;
      b += '<rect x="60" y="' + y + '" width="330" height="48" fill="' + l[1] + '22" stroke="#2D2A26" stroke-width="2"/>' +
        '<text x="74" y="' + (y + 30) + '" ' + T + ' font-size="15" font-weight="700" fill="#2D2A26">' + l[0] + "</text>" +
        '<line x1="' + (250 + i * 40) + '" y1="20" x2="' + (250 + i * 40) + '" y2="' + (y + 24) + '" stroke="' + l[1] + '" stroke-width="4"/><circle cx="' + (250 + i * 40) + '" cy="' + (y + 24) + '" r="8" fill="' + l[3] + '" stroke="#2D2A26" stroke-width="1.5"/>' +
        '<text x="410" y="' + (y + 30) + '" ' + T + ' font-size="15" fill="#2D2A26">→ makes <tspan font-weight="700" fill="' + (i === 0 ? "#9a7a00" : l[3]) + '">' + l[2] + "</tspan></text>";
    });
    b += '<rect x="60" y="228" width="330" height="40" fill="#DCEBF2" stroke="#2D2A26" stroke-width="2"/><text x="74" y="253" ' + T + ' font-size="14" fill="#2D2A26">plastic base</text>' +
      '<text x="60" y="290" ' + T + ' font-size="13" fill="#625C53">Each colour of light stops in its own layer. Developing leaves a dye of the opposite colour.</text>';
    return U.svg(640, 300, b, "Colour film has three layers: one catches blue light and makes yellow dye, one green and makes magenta, one red and makes cyan.");
  });

  // ------------------------------------------------------------------ expose, develop, fix, print
  C.sim("l03_grains", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 2 / 3, maxH: 520 });
    var cap = U.h("p", { class: "sim-cap" }); left.appendChild(cap);
    var S = { steps: 0, phase: 0, specks: true, upright: false, sweep: 1, pick: null };
    var sx = U.slider({ label: "How much light", min: -3, max: 4, step: 0.5, value: 0, fmt: function (v) { return v === 0 ? "just right" : (v > 0 ? "+" : "") + v + " steps (× " + U.fmt(Math.pow(2, v), 2) + ")"; }, onInput: function (v) { S.steps = v; reset(); } });
    right.appendChild(sx.el);
    var bts = U.h("div", { class: "sim-ctl" }); bts.appendChild(U.h("span", { class: "sim-lab" }, "In order"));
    var row = U.h("div", { class: "sim-row" }); bts.appendChild(row); right.appendChild(bts);
    var bE = U.button("1. Click: let light in", function () { go(1); }, "sim-go"), bD = U.button("2. Developer", function () { go(2); }), bF = U.button("3. Fixer", function () { go(3); }), bP = U.button("4. Print it", function () { go(4); }), bR = U.button("Start again", function () { reset(); });
    [bE, bD, bF, bP, bR].forEach(function (b) { row.appendChild(b); });
    var spk = U.choice({ label: "The specks of silver", options: [{ v: true, label: "show them (drawn far too big)" }, { v: false, label: "as your eye sees" }], value: true, onChange: function (v) { S.specks = v; st.redraw(); } });
    right.appendChild(spk.el);
    var up = U.choice({ label: "Which way up", options: [{ v: false, label: "as on the film" }, { v: true, label: "turned right way up" }], value: false, onChange: function (v) { S.upright = v; st.redraw(); } });
    right.appendChild(up.el);
    var set = U.readouts(right, [{ k: "m", label: "crystals marked" }, { k: "stage", label: "the film now", cls: "sim-hi" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var sc = U.scene(96, 64), grains = [], NX = 78, NY = 52, raf = 0;
    (function make() {
      var rnd = U.rng(11);
      for (var j = 0; j < NY; j++) for (var i = 0; i < NX; i++) grains.push({ x: (i + 0.5 + (rnd() - 0.5) * 0.5) / NX, y: (j + 0.5 + (rnd() - 0.5) * 0.5) / NY, r: 0.36 + rnd() * 0.18, a: rnd() * 1, tri: rnd() < 0.3, u: rnd(), hits: 0, mark: false });
    })();
    function lumAt(x, y) { // the light landing here: the scene upside down, as the lens puts it
      var sx2 = Math.floor((1 - x) * sc.w), sy2 = Math.floor((1 - y) * sc.h), p = (Math.min(sc.h - 1, sy2) * sc.w + Math.min(sc.w - 1, sx2)) * 3;
      return 0.2126 * sc.d[p] + 0.7152 * sc.d[p + 1] + 0.0722 * sc.d[p + 2];
    }
    function expose() {
      var rnd = U.rng(5 + Math.round(S.steps * 4));
      grains.forEach(function (g) { g.hits = U.poisson(lumAt(g.x, g.y) * 12 * Math.pow(2, S.steps), rnd); g.mark = g.hits >= 4; });
    }
    function reset() { cancelAnimationFrame(raf); S.phase = 0; S.sweep = 1; grains.forEach(function (g) { g.hits = 0; g.mark = false; }); upd(); }
    function go(ph) {
      if (ph !== S.phase + 1) return;
      if (ph === 1) expose();
      S.phase = ph; S.sweep = api.reducedMotion ? 1 : 0;
      var t0 = performance.now();
      cancelAnimationFrame(raf);
      (function tick(t) { S.sweep = Math.min(1, (t - t0) / 1200); st.now(); if (S.sweep < 1) raf = requestAnimationFrame(tick); else upd(); })(t0);
      upd();
    }
    var NAMES = ["fresh film", "a hidden picture", "developed", "fixed: a negative", "printed: a positive"];
    function upd() {
      var m = grains.filter(function (g) { return g.mark; }).length;
      set({ m: S.phase ? Math.round(100 * m / grains.length) + " %" : "–", stage: NAMES[S.phase] });
      bE.disabled = S.phase !== 0; bD.disabled = S.phase !== 1; bF.disabled = S.phase !== 2; bP.disabled = S.phase !== 3;
      var tx = ["Fresh film: every crystal pale and untouched. Press 1 to let the scene's light fall on it for a moment.",
        "Light has left specks of a few silver atoms on " + Math.round(100 * m / grains.length) + " % of the crystals. Switch to 'as your eye sees': nothing at all. This is the hidden picture.",
        "Developer has turned every marked crystal, all of it, into black silver. A few atoms became billions: now you can see it.",
        "Fixer has washed away the crystals light never touched. The film is clear there, and light can't change it any more. Dark where the scene was bright: a negative.",
        "Light shone through the negative onto fresh paper. Clear film let light through, so the paper went dark there: backwards twice, the right way round."][S.phase];
      if (S.phase >= 3 && S.steps <= -2) tx += " Too little light: only the brightest parts marked any crystals. A thin negative, and shadows with nothing in them.";
      if (S.phase >= 3 && S.steps >= 3.5) tx += " Lots of light: nearly every crystal is marked, a dense negative. Film forgives up to about 3 steps too much.";
      verdict.textContent = tx; cap.textContent = S.phase === 4 ? "Paper, printed through the negative (simulated)." : "The film's crystals, seen from the front, hugely magnified (simulated). Click a crystal to look closer.";
      say(NAMES[S.phase] + ". " + tx); st.redraw();
    }
    st.draw = function (g, W, H) {
      var flip = S.upright, cw = W / NX, ch = H / NY, ph = S.phase, sw = S.sweep;
      g.fillStyle = ph >= 3 ? (ph === 4 ? "#f4f1ea" : "#c9d6dc") : "#d9b779"; g.fillRect(0, 0, W, H);
      if (ph === 4) { g.fillStyle = "rgba(0,0,0,.04)"; g.fillRect(0, 0, W, H); }
      grains.forEach(function (gr, i) {
        var x = (flip ? 1 - gr.x : gr.x) * W, y = (flip ? 1 - gr.y : gr.y) * H, r = gr.r * Math.min(cw, ch) * 1.25, done = gr.x < sw;
        var fill = "#f6f2ea", show = true;
        if (ph === 2 && gr.mark && done) fill = "#15130f";
        if (ph === 2 && gr.mark && !done) fill = "#f6f2ea";
        if (ph === 3) { if (gr.mark) fill = "#15130f"; else { show = !done; } }
        if (ph === 4) { if (!gr.mark) fill = done ? "#22201b" : "#f4f1ea"; else show = false; }
        if (ph === 1 && !done && gr.u < sw * 3) { /* photons arriving */ }
        if (show) {
          g.fillStyle = fill; g.beginPath();
          if (gr.tri) { for (var k = 0; k < 3; k++) { var a = gr.a * 6 + k * 2.094; g.lineTo(x + r * Math.cos(a), y + r * Math.sin(a)); } }
          else for (var k2 = 0; k2 < 6; k2++) { var a2 = gr.a + k2 * 1.047; g.lineTo(x + r * Math.cos(a2), y + r * Math.sin(a2)); }
          g.closePath(); g.fill();
          if (ph < 2 || (ph === 2 && !done)) { g.strokeStyle = "rgba(120,100,70,.5)"; g.lineWidth = 0.6; g.stroke(); }
        }
        if (ph === 1 && gr.mark && S.specks && done) { g.fillStyle = "#15130f"; g.beginPath(); g.arc(x + r * 0.2, y - r * 0.2, Math.max(1.1, r * 0.28), 0, 7); g.fill(); }
        if (ph === 1 && !done) { /* the flash */ }
      });
      if (ph === 1 && sw < 1) { g.fillStyle = "rgba(255,240,170," + (0.55 * (1 - sw)).toFixed(3) + ")"; g.fillRect(0, 0, W, H); }
      if ((ph === 2 || ph === 3) && sw < 1) { g.fillStyle = ph === 2 ? "rgba(120,170,230,.28)" : "rgba(140,220,170,.28)"; g.fillRect(0, 0, W * sw, H); U.label(g, ph === 2 ? "developer" : "fixer", Math.max(40, W * sw - 8), 22, { align: "right", color: "#fff", size: 13 }); }
      // the close-up of one crystal
      var p = S.pick;
      if (p != null) {
        var gr2 = grains[p], bx = W - 128, by = 10, bw = 118;
        g.fillStyle = "rgba(20,18,15,.92)"; g.fillRect(bx, by, bw, bw + 34); g.strokeStyle = "#fff"; g.strokeRect(bx + 0.5, by + 0.5, bw - 1, bw + 33);
        var cx = bx + bw / 2, cy = by + bw / 2, R = 40;
        g.fillStyle = ph >= 2 && gr2.mark ? "#15130f" : (ph >= 3 && !gr2.mark ? "transparent" : "#f6f2ea"); g.beginPath(); for (var k3 = 0; k3 < 6; k3++) { var a3 = k3 * 1.047 + 0.5; g.lineTo(cx + R * Math.cos(a3), cy + R * Math.sin(a3)); } g.closePath(); g.fill(); g.strokeStyle = "#8a7a64"; g.stroke();
        if (ph === 1) { for (var q = 0; q < Math.min(gr2.hits, 12); q++) { g.fillStyle = "#15130f"; g.beginPath(); g.arc(cx + 14 + (q % 4) * 6, cy - 16 + Math.floor(q / 4) * 6, 2.6, 0, 7); g.fill(); } }
        var txt = ph === 0 ? "untouched" : ph === 1 ? gr2.hits + " atom" + (gr2.hits === 1 ? "" : "s") + (gr2.mark ? ": marked" : ": not enough") : ph === 2 ? (gr2.mark ? "all black silver" : "still pale") : ph === 3 ? (gr2.mark ? "silver: stays" : "washed away") : "";
        U.label(g, "one crystal", cx, by + bw + 12, { align: "center", color: "#b9b0a2", size: 10 });
        U.label(g, txt, cx, by + bw + 27, { align: "center", color: "#fff", size: 11 });
      }
    };
    U.drag(st.cv, function (x, y, ph) {
      if (ph !== "down") return;
      var W = st.w, H = st.h, fx = x / W, fy = y / H; if (S.upright) { fx = 1 - fx; fy = 1 - fy; }
      var best = 0, bd = 1e9; grains.forEach(function (gr, i) { var d = Math.hypot(gr.x - fx, (gr.y - fy) * H / W); if (d < bd) { bd = d; best = i; } });
      S.pick = best; st.redraw();
    });
    S.pick = Math.floor(NX * NY * 0.18) + 10;
    upd();
    return { destroy: function () { cancelAnimationFrame(raf); st.destroy(); } };
  });

  // ------------------------------------------------------------------ the negative, the print, and how wrong the light can be
  C.sim("l03_window", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var narrow = function (w) { return w < 560; };
    var st = U.stage(wrap, { aspect: function (w) { return narrow(w) ? 2.15 : 0.25; }, maxH: 760 });
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div", { class: "sim-ctls" }), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var S = { steps: 0, colour: true, invert: false };
    var sx = U.slider({ label: "Light on the film", min: -3, max: 5, step: 0.1, value: 0, fmt: function (v) { return Math.abs(v) < 0.05 ? "just right" : (v > 0 ? "+" : "−") + Math.abs(v).toFixed(1) + " steps"; }, onInput: function (v) { S.steps = v; upd(); } });
    left.appendChild(sx.el);
    var meter = U.stage(left, { aspect: 0.16, maxH: 70, min: 200 });
    var q = U.h("div", { class: "sim-ctl" }); q.appendChild(U.h("span", { class: "sim-lab" }, "Your camera, ISO 400 film, by the model"));
    var qr = U.h("div", { class: "sim-seg" }); q.appendChild(qr); left.appendChild(q);
    [["full sun, small dot", 0.5], ["hazy sun, middle dot", 0.6], ["bright cloud, large dot", 0]].forEach(function (c) { qr.appendChild(U.button(c[0] + " (" + (c[1] ? "+" + c[1] : "0") + ")", function () { sx.set(c[1]); })); });
    right.appendChild(U.choice({ label: "Film", options: [{ v: true, label: "colour negative" }, { v: false, label: "black and white" }], value: true, onChange: function (v) { S.colour = v; upd(); } }).el);
    right.appendChild(U.choice({ label: "The negative", options: [{ v: false, label: "as it is" }, { v: true, label: "through a phone's 'invert colours'" }], value: false, onChange: function (v) { S.invert = v; upd(); } }).el);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var sc = U.scene(270, 180), res = null;
    function upd() {
      res = U.develop(sc, S.steps, S.colour);
      var s = S.steps, ok = s >= -1 && s <= 3, t;
      if (s < -1) t = "Too little light: the darks never marked the film. The print's shadows are a flat, muddy grey.";
      else if (s > 3) t = "Too much light: the brights all marked the film the same. The print's sky and cloud go flat.";
      else t = "Inside the film's window (1 step under to 3 over): the lab prints it back to a good picture.";
      verdict.textContent = t;
      say("Light " + (s >= 0 ? "+" : "") + s.toFixed(1) + " steps. " + t + " The negative is dark where the scene was bright" + (S.colour ? ", in opposite colours under an orange tint." : "."));
      st.redraw(); meter.redraw();
    }
    st.draw = function (g, W, H) {
      g.fillStyle = "#0d0b09"; g.fillRect(0, 0, W, H);
      var nar = narrow(W), pw, ph, boxes = [];
      if (nar) { pw = W; ph = (H - 60) / 3; for (var i = 0; i < 3; i++) boxes.push([0, i * (ph + 20) + 18, pw, ph]); }
      else { pw = (W - 40) / 3; ph = H - 24; for (var j = 0; j < 3; j++) boxes.push([j * (pw + 20), 22, pw, ph]); }
      var labels = ["the scene (simulated)", "the negative", "the print"];
      var neg = res.neg;
      if (S.invert) { var inv = new U.Img(neg.w, neg.h); for (var k = 0; k < neg.d.length; k++) inv.d[k] = Math.max(0, 1 - neg.d[k] / (S.colour ? [1, 0.62, 0.36][k % 3] : 1)); neg = inv; }
      U.paint(g, sc, boxes[0][0], boxes[0][1], boxes[0][2], boxes[0][3], 1, {});
      U.paint(g, neg, boxes[1][0], boxes[1][1], boxes[1][2], boxes[1][3], 1, { film: false });
      U.paint(g, res.print, boxes[2][0], boxes[2][1], boxes[2][2], boxes[2][3], 1, {});
      boxes.forEach(function (b, i) { U.label(g, labels[i] + (i === 1 && S.invert ? ", inverted" : ""), b[0] + 4, b[1] - 6, { color: "#d8d0c2", size: 11 }); });
      U.simTag(g, boxes[2][0] + 6, boxes[2][1] + boxes[2][3] - 6);
    };
    meter.draw = function (g, W, H) {
      var x0 = 14, x1 = W - 14, y = H * 0.42;
      function X(s) { return x0 + (x1 - x0) * (s + 3) / 8; }
      g.fillStyle = "#2a251e"; g.fillRect(x0, y - 8, x1 - x0, 16);
      g.fillStyle = "#1d7a46"; g.fillRect(X(-1), y - 8, X(3) - X(-1), 16);
      for (var s = -3; s <= 5; s++) { g.fillStyle = "#b9b0a2"; g.fillRect(X(s) - 0.5, y + 9, 1, 5); U.label(g, (s > 0 ? "+" : "") + s, X(s), H - 4, { align: "center", color: "#b9b0a2", size: 10, weight: 400 }); }
      U.label(g, "the film's window", (X(-1) + X(3)) / 2, y + 4, { align: "center", color: "#fff", size: 10 });
      g.fillStyle = "#fff"; g.beginPath(); g.moveTo(X(S.steps), y - 10); g.lineTo(X(S.steps) - 7, y - 20); g.lineTo(X(S.steps) + 7, y - 20); g.fill();
    };
    upd();
    return { destroy: function () { st.destroy(); meter.destroy(); } };
  });
})();

/* Lesson 3's picture (hero_fig, and its card): light marks some silver crystals; the developer turns those to black silver; the rest wash away: a negative. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#D23F31";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  // crystals in a 4 x 3 grid; the lit ones are the left half (where the light fell)
  var P = [[22, 22], [58, 30], [96, 20], [134, 28], [30, 62], [70, 70], [108, 58], [142, 72], [20, 104], [60, 110], [100, 100], [138, 108]];
  function panel(x, mode) {
    var b = '<rect x="' + x + '" y="120" width="164" height="132" rx="10" fill="' + (mode === "neg" ? "#EEF3F6" : "#F4E7C8") + '" stroke="' + INK + '" stroke-width="3"/>';
    P.forEach(function (p) {
      var lit = p[0] < 82, cx = x + p[0] + 4, cy = 120 + p[1] + 8;
      if (mode === "raw") b += '<rect x="' + (cx - 9) + '" y="' + (cy - 9) + '" width="18" height="18" transform="rotate(20 ' + cx + " " + cy + ')" fill="#fff" stroke="' + INK + '" stroke-width="2"/>' + (lit ? '<circle cx="' + cx + '" cy="' + cy + '" r="3.5" fill="' + COL + '"/>' : "");
      else if (mode === "dev") b += lit ? '<circle cx="' + cx + '" cy="' + cy + '" r="11" fill="' + INK + '"/>' : '<rect x="' + (cx - 9) + '" y="' + (cy - 9) + '" width="18" height="18" transform="rotate(20 ' + cx + " " + cy + ')" fill="#fff" stroke="' + INK + '" stroke-width="2"/>';
      else if (lit) b += '<circle cx="' + cx + '" cy="' + cy + '" r="11" fill="' + INK + '"/>';
    });
    return b;
  }
  function arrow(x) { return '<path d="M' + x + ' 186 h26" stroke="' + COL + '" stroke-width="5"/><path d="M' + (x + 34) + ' 186 l-12 -9 v18 z" fill="' + COL + '"/>'; }
  C.fig("fig_l03_hero", function () {
    var b = '<rect width="640" height="360" fill="#fff"/>';
    for (var i = 0; i < 5; i++) b += '<line x1="' + (30 + i * 14) + '" y1="34" x2="' + (52 + i * 14) + '" y2="108" stroke="#F2B807" stroke-width="5" stroke-linecap="round"/>';
    b += T(110, 56, "light", 24, 800, INK) + panel(16, "raw") + arrow(186) + panel(238, "dev") + arrow(408) + panel(460, "neg") +
      T(98, 290, "light marks", 22, 800, INK, "middle") + T(98, 316, "silver crystals", 18, 600, "#625C53", "middle") +
      T(320, 290, "developer", 22, 800, INK, "middle") + T(320, 316, "marked ones turn black", 18, 600, "#625C53", "middle") +
      T(542, 290, "the negative", 22, 800, COL, "middle") + T(542, 316, "light became dark", 18, 600, "#625C53", "middle");
    return C.U.svg(640, 360, b, "Light lands on part of the film and marks the silver crystals it hits. The developer turns the marked crystals into black silver; the unmarked ones are washed away. Where the light was is now dark: a negative.");
  });
})();
