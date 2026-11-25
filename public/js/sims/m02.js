/* CURVE 35, maker lesson M2 "Click": interactive pieces and figures.
   Numbers: course/FACTS.md, build/snapcurves.json (back: 1.6 mm nub, 0.61 N; fattest 2.1 mm, 1.44 N),
   END_CASES.md section 3 (PLA yields at about 1.7 %; 0.5 % / 1.0 % limits), build/platefall.json (simple fall model). */
(function () {
  "use strict";
  if (!window.CURVE || !CURVE.sim) return;
  // ---- shared little helpers for the maker lessons (same block in m02.js and m03.js; whichever loads first defines it)
  var H = window.CURVE_MK || (window.CURVE_MK = (function () {
    var NS = "http://www.w3.org/2000/svg", styled = false, actx = null;
    function css() {
      if (styled) return; styled = true;
      var s = document.createElement("style"); s.id = "curve-mk-sims";
      s.textContent = [
        ".mk{--c:var(--lc,var(--mkc,#14a08c));--m:var(--stage-mute,#625C53);--p2:var(--stage-2,#EFEBE3);font-family:var(--sans,system-ui,sans-serif);color:inherit;font-size:15px;line-height:1.45;font-variant-numeric:tabular-nums}",
        ".mk *{box-sizing:border-box}",
        ".mk-stage{position:relative;background:#fff;color:#2D2A26;border:2px solid var(--ink,#2D2A26);border-radius:14px;overflow:hidden}",
        ".mk-stage svg,.mk-stage canvas{display:block;width:100%;height:auto}",
        ".mk-ctl{display:flex;flex-wrap:wrap;gap:12px 22px;align-items:flex-end;margin:14px 0 6px}",
        ".mk-f{display:flex;flex-direction:column;gap:6px;min-width:150px;flex:1 1 170px}",
        ".mk-f>span{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--m)}",
        ".mk-f output{font-weight:700;font-size:14px;color:inherit;text-transform:none;letter-spacing:0;filter:brightness(1.6)}",
        ".mk input[type=range]{width:100%;accent-color:var(--c);height:28px;margin:0}",
        ".mk-seg{display:flex;flex-wrap:wrap;gap:6px}",
        ".mk-seg button,.mk-btn{font:600 14px/1 var(--sans,system-ui,sans-serif);padding:9px 12px;border-radius:10px;border:1.5px solid #6b6357;background:var(--p2);color:inherit;cursor:pointer;min-height:38px}",
        ".mk-seg button:hover,.mk-btn:hover{border-color:var(--c)}",
        ".mk-seg button[aria-pressed=true]{background:var(--c);border-color:var(--c);color:var(--lc-on,#fff)}",
        ".mk-btn.go{background:var(--c);border-color:var(--c);color:var(--lc-on,#fff);font-size:15px;padding:11px 16px}",
        ".mk-btn:disabled{opacity:.45;cursor:default}",
        ".mk-seg button:focus-visible,.mk-btn:focus-visible,.mk input:focus-visible,.mk textarea:focus-visible,.mk select:focus-visible,.mk-stage:focus-visible{outline:3px solid var(--c);outline-offset:2px}",
        ".mk-read{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:8px;margin:12px 0 0}",
        ".mk-num{background:var(--p2);border-radius:12px;padding:9px 12px;border-left:4px solid transparent}",
        ".mk-num b{display:block;font-size:22px;line-height:1.15;font-weight:700}",
        ".mk-num small{font-size:12px;color:var(--m)}",
        ".mk-num.hot{border-left-color:#e0402a}.mk-num.ok{border-left-color:#2fbf71}",
        ".mk-tag{position:absolute;top:8px;right:10px;font:600 11px/1 var(--sans,system-ui,sans-serif);letter-spacing:.06em;text-transform:uppercase;background:#2D2A26;color:#fff;padding:5px 8px;border-radius:6px;pointer-events:none}",
        ".mk-say{margin:12px 0 0;padding:10px 14px;border-left:5px solid var(--c);background:var(--p2);border-radius:0 10px 10px 0;font-size:15px}",
        ".mk-card{background:#fff;color:#2D2A26;border:2px solid var(--ink,#2D2A26);border-radius:12px;padding:10px 12px}",
        ".mk-card .mk-seg button,.mk-card .mk-btn{background:#fff;border-color:#2D2A26}",
        ".mk-card .mk-seg button[aria-pressed=true]{background:#2D2A26;color:#fff}",
        ".mk-card select,.mk-card textarea{color:#2D2A26;background:#fff}",
        ".mk .big{font:700 30px var(--sans,system-ui,sans-serif);fill:#e0402a}",
        "@media (max-width:560px){.mk-f{min-width:100%}.mk-num b{font-size:19px}}"
      ].join("\n");
      document.head.appendChild(s);
    }
    function el(tag, attrs, parent, text) {
      var e = document.createElement(tag);
      if (attrs) for (var k in attrs) { if (k === "style") e.style.cssText = attrs[k]; else if (k === "class") e.className = attrs[k]; else e.setAttribute(k, attrs[k]); }
      if (text != null) e.textContent = text;
      if (parent) parent.appendChild(e);
      return e;
    }
    function sv(tag, attrs, parent) {
      var e = document.createElementNS(NS, tag);
      if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
      if (parent) parent.appendChild(e);
      return e;
    }
    function root(host, api, label) {
      css();
      var r = el("div", { "class": "mk", role: "group", "aria-label": label }, host);
      r.style.setProperty("--mkc", (api && api.colour) || "#14a08c");
      return r;
    }
    function slider(parent, o) {
      var f = el("label", { "class": "mk-f" }, parent), sp = el("span", null, f, o.label + " ");
      var out = el("output", null, sp), inp = el("input", { type: "range", min: o.min, max: o.max, step: o.step, value: o.value }, f);
      function show() { out.textContent = o.fmt ? o.fmt(+inp.value) : inp.value; inp.setAttribute("aria-valuetext", out.textContent); }
      inp.addEventListener("input", function () { show(); o.on && o.on(+inp.value); });
      show();
      return { input: inp, get: function () { return +inp.value; }, set: function (v, quiet) { inp.value = v; show(); if (!quiet && o.on) o.on(+inp.value); } };
    }
    function seg(parent, label, opts, val, on) {
      var f = el("div", { "class": "mk-f" }, parent); el("span", { id: "" }, f, label);
      var g = el("div", { "class": "mk-seg", role: "group", "aria-label": label }, f), bs = [];
      opts.forEach(function (o) {
        var b = el("button", { type: "button", "aria-pressed": String(o[0] === val) }, g, o[1]); bs.push(b);
        b.addEventListener("click", function () { set(o[0]); on && on(o[0]); });
      });
      function set(v) { val = v; bs.forEach(function (b, i) { b.setAttribute("aria-pressed", String(opts[i][0] === v)); }); }
      return { get: function () { return val; }, set: set };
    }
    function num(parent, label) {
      var d = el("div", { "class": "mk-num" }, parent), b = el("b", null, d, "–"); el("small", null, d, label);
      return { set: function (v, cls) { b.textContent = v; d.className = "mk-num" + (cls ? " " + cls : ""); } };
    }
    function click(vol) {   // a short, dry click from filtered noise
      try {
        var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
        actx = actx || new AC(); if (actx.state === "suspended") actx.resume();
        var n = Math.floor(actx.sampleRate * 0.03), b = actx.createBuffer(1, n, actx.sampleRate), d = b.getChannelData(0);
        for (var i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 6);
        var s = actx.createBufferSource(), f = actx.createBiquadFilter(), g = actx.createGain();
        s.buffer = b; f.type = "bandpass"; f.frequency.value = 2600; f.Q.value = 1.2; g.gain.value = vol == null ? 0.6 : vol;
        s.connect(f); f.connect(g); g.connect(actx.destination); s.start();
      } catch (e) { /* no sound: fine */ }
    }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function fmt(v, d) { return (Math.round(v * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d); }
    return { css: css, el: el, sv: sv, root: root, slider: slider, seg: seg, num: num, click: click, lerp: lerp, clamp: clamp, fmt: fmt };
  })());

  var C9 = "#14a08c";

  // ------------------------------------------------------------------ sim: bend a snap
  CURVE.sim("m02_snap", function (host, api) {
    var r = H.root(host, api, "Snap fit simulator: push a springy finger over a bar and watch strain and force");
    var stage = H.el("div", { "class": "mk-stage" }, r);
    var W = 720, HH = 330;
    var svg = H.sv("svg", { viewBox: "0 0 " + W + " " + HH, role: "img", "aria-label": "Side view of a plastic finger with a nub, sliding past a bar on the camera body, and a graph of push force against travel" }, stage);
    H.el("div", { "class": "mk-tag" }, stage, "beam estimate · bend drawn 3× larger");
    var ctl = H.el("div", { "class": "mk-ctl" }, r);
    var state = { s: 0, L: 35, t: 1.3, h: 1.6, clicked: false, set: 0, locked: false, broke: false, trace: [] };
    var EXAG = 3, PX = 6;   // px per mm, and bend exaggeration
    var push = H.slider(ctl, { label: "Push the back on", min: 0, max: 5, step: 0.02, value: 0, fmt: function (v) { return H.fmt(v, 1) + " mm"; }, on: function (v) { move(v); } });
    var len = H.slider(ctl, { label: "Finger length", min: 10, max: 40, step: 0.5, value: 35, fmt: function (v) { return H.fmt(v, 1) + " mm"; }, on: function (v) { state.L = v; reset(); } });
    var thk = H.slider(ctl, { label: "Finger thickness", min: 0.6, max: 2.4, step: 0.05, value: 1.3, fmt: function (v) { return H.fmt(v, 2) + " mm"; }, on: function (v) { state.t = v; reset(); } });
    var ctl2 = H.el("div", { "class": "mk-ctl" }, r);
    var pr = H.seg(ctl2, "Printer", [[1.6, "as drawn"], [2.1, "fattest printer"]], 1.6, function (v) { state.h = v; reset(); });
    var bf = H.el("div", { "class": "mk-f" }, ctl2); H.el("span", null, bf, "Now try");
    var bs = H.el("div", { "class": "mk-seg" }, bf);
    var pullB = H.el("button", { type: "button", "class": "mk-btn" }, bs, "Pull it straight off");
    var pinchB = H.el("button", { type: "button", "class": "mk-btn" }, bs, "Pinch the pad");
    var resetB = H.el("button", { type: "button", "class": "mk-btn" }, bs, "Reset");
    var snd = H.seg(ctl2, "Sound", [[1, "click on"], [0, "off"]], 1);
    var read = H.el("div", { "class": "mk-read" }, r);
    var nTip = H.num(read, "tip bent sideways"), nStr = H.num(read, "stretch at the root (strain)"), nF = H.num(read, "push needed now"), nPk = H.num(read, "most force on the way");
    var say = H.el("p", { "class": "mk-say", "aria-live": "polite" }, r);

    // geometry of the ramp along the travel s (mm)
    var A0 = 0.8, TAN = Math.tan(30 * Math.PI / 180), FLAT = 0.5, MU = 0.3;
    function rampEnd() { return A0 + state.h / TAN; }
    function dropAt() { return rampEnd() + FLAT; }
    function defl(s) { if (s < A0) return 0; if (s < rampEnd()) return (s - A0) * TAN; if (s < dropAt()) return state.h; return 0; }
    var R = (MU + TAN) / (1 - MU * TAN), K0 = 0.61 / (1.6 * R);   // calibrated: the back's own finger, 35 x 1.3 mm with a 1.6 mm nub -> 0.61 N peak (snapcurves "back", as drawn)
    function tEff() { return state.t + (state.h > 2 ? 0.25 : 0); }   // the fattest printer also prints the finger 0.25 mm thicker
    function k() { return K0 * Math.pow(tEff() / 1.3, 3) * Math.pow(35 / state.L, 3); }
    function force(s) { var d = defl(s); if (s >= A0 && s < rampEnd()) return k() * d * R; if (s >= rampEnd() && s < dropAt()) return k() * state.h * R * (0.18 / 0.61); return 0.02; }
    function strain(d) { return 1.5 * tEff() * d / (state.L * state.L) * 100; }
    function peak() { var m = 0; for (var s = 0; s <= 5; s += 0.02) m = Math.max(m, force(s)); return m; }

    // layout: the finger stays put on screen; the body's bar moves up past it (that is the same as pushing the back down)
    var g = H.sv("g", null, svg), gp = H.sv("g", null, svg);
    var cp = H.sv("clipPath", { id: "m02clip" }, H.sv("defs", null, svg)); H.sv("rect", { x: 0, y: 0, width: 445, height: HH }, cp);
    g.setAttribute("clip-path", "url(#m02clip)");
    var X0 = 150, Y0 = 70, SC = 30;
    function draw() {
      g.innerHTML = "";
      var s = state.s, d = Math.max(defl(s), state.set), Lp = state.L * PX, tp = Math.max(4, tEff() * PX * 1.6);
      var xf = X0 + tp, tipY = Y0 + Lp, hx = state.h * PX * EXAG, nubH = 26;
      // the body's bar: slope on top (way in), square face underneath (way out)
      var yc = tipY - 10, ytop = yc - FLAT * SC;   // the nub's outer corner, and its square top
      var yb0 = yc + (A0 - s) * SC, ys = yb0 + (rampEnd() - A0) * SC, yb1 = ys, xr = xf + hx;
      H.sv("path", { d: "M" + xr + " " + yb0 + " L440 " + yb0 + " L440 " + yb1 + " L" + xf + " " + yb1 + " L" + xf + " " + ys + "Z", fill: "#3b3936" }, g);
      H.sv("line", { x1: xr, y1: yb0, x2: xf, y2: ys, stroke: "#2fbf71", "stroke-width": 5, "stroke-linecap": "round" }, g);
      H.sv("line", { x1: xf, y1: yb1, x2: xr + 40, y2: yb1, stroke: "#e0402a", "stroke-width": 5, "stroke-linecap": "round" }, g);
      lab(g, xr + 40, yb0 + 22, "slope: way in", "#7fe0a8");
      lab(g, xr + 50, yb1 - 8, "square face: way out", "#ff9a8a");
      lab(g, 300, yb0 + 50, "the camera body", "#cfc8bb", 12);
      // the finger: cantilever bend, coloured by strain (largest at the root)
      var segs = 24, eps = strain(d), off = function (a) { return -d * EXAG * PX * (3 * a * a - a * a * a) / 2; };
      for (var i = 0; i < segs; i++) {
        var a = i / segs, b = (i + 1) / segs, ya = Y0 + a * Lp, yb = Y0 + b * Lp + 0.7;
        H.sv("path", { d: "M" + (X0 + off(a)) + " " + ya + " L" + (xf + off(a)) + " " + ya + " L" + (xf + off(b)) + " " + yb + " L" + (X0 + off(b)) + " " + yb + "Z", fill: heat(eps * (1 - a)), stroke: heat(eps * (1 - a)), "stroke-width": 0.5 }, g);
      }
      var dx = off(1), nx = xf + dx;
      H.sv("path", { d: "M" + nx + " " + ytop + " L" + (nx + hx) + " " + ytop + " L" + (nx + hx) + " " + yc + " L" + nx + " " + (tipY + 4) + " L" + (X0 + dx) + " " + (tipY + 4) + " L" + (X0 + dx) + " " + ytop + "Z", fill: "#14a08c" }, g);
      lab(g, X0 + dx - 40, tipY - 6, "nub", "#2D2A26", 12);
      // the back the finger is part of
      H.sv("rect", { x: X0 - 110, y: Y0 - 34, width: 230, height: 34, rx: 6, fill: "#c9cdcf" }, g);
      lab(g, X0 - 100, Y0 - 12, "the back", "#2D2A26");
      H.sv("circle", { cx: X0 + tp / 2, cy: Y0 + 4, r: 11, fill: "none", stroke: heat(Math.max(eps, 0.6)), "stroke-width": 3 }, g);
      lab(g, X0 - 44, Y0 + 22, "root", "#2D2A26", 12);
      var at = H.sv("path", { d: "M" + (X0 - 70) + " " + (Y0 + 50) + " l0 50 l-7 -10 m7 10 l7 -10", stroke: "#625C53", "stroke-width": 2, fill: "none" }, g);
      lab(g, X0 - 130, Y0 + 120, "pushed on: " + H.fmt(s, 1) + " mm", "#625C53", 12);
      if (state.clicked && !state.broke && s >= dropAt() && s - dropAt() < 0.5) { var c = H.sv("text", { x: X0 + 60, y: tipY + 40, "class": "big" }, g); c.textContent = "CLICK"; }
      if (state.locked) { var t2 = H.sv("text", { x: 20, y: HH - 16, fill: "#c0392b", style: "font:700 15px var(--sans,system-ui,sans-serif)" }, g); t2.textContent = "square on square: locked"; }
      if (state.broke) { var t3 = H.sv("text", { x: 14, y: HH - 16, fill: "#c0392b", style: "font:700 13px var(--sans,system-ui,sans-serif)" }, g); t3.textContent = "Past 1.7 %: it stays bent. Ruined. Reset."; }
      // strain bar
      var sbx = 200, sby = 16, sbw = 220;
      lab(g, sbx, sby - 2, "stretch at the root", "#2D2A26", 12);
      H.sv("rect", { x: sbx, y: sby + 4, width: sbw, height: 12, rx: 6, fill: "#fff", stroke: "#DDD6CA" }, g);
      H.sv("rect", { x: sbx, y: sby + 4, width: Math.min(sbw, sbw * eps / 2), height: 12, rx: 6, fill: heat(Math.max(eps, 0.3)) }, g);
      [[0.5, "0.5"], [1.0, "1.0"], [1.7, "1.7 %"]].forEach(function (m) { var mx = sbx + sbw * m[0] / 2; H.sv("line", { x1: mx, y1: sby + 1, x2: mx, y2: sby + 19, stroke: "#625C53" }, g); lab(g, mx - 8, sby + 32, m[1], "#625C53", 11); });
      drawPlot();
    }
    function lab(p, x, y, s, col, size) { var t = H.sv("text", { x: x, y: y, fill: col || "#2D2A26", style: "font:600 " + (size || 13) + "px var(--sans,system-ui,sans-serif)" }, p); t.textContent = s; return t; }
    function heat(e) {   // 0 % pale, 0.5 % yellow, 1.0 % orange, 1.7 % red
      var stops = [[0, [236, 233, 226]], [0.5, [246, 211, 92]], [1.0, [240, 140, 40]], [1.7, [214, 48, 39]], [3, [140, 20, 20]]];
      for (var i = 1; i < stops.length; i++) if (e <= stops[i][0]) { var a = stops[i - 1], b = stops[i], t = (e - a[0]) / (b[0] - a[0]); return "rgb(" + a[1].map(function (c, j) { return Math.round(H.lerp(c, b[1][j], t)); }).join(",") + ")"; }
      return "rgb(140,20,20)";
    }
    // the force graph
    var PX0 = 470, PY0 = 60, PW = 230, PH = 200;
    function drawPlot() {
      gp.innerHTML = "";
      var fmax = Math.max(1, Math.ceil(peak() * 1.25 * 2) / 2);
      H.sv("rect", { x: PX0, y: PY0, width: PW, height: PH, fill: "#fff", stroke: "#DDD6CA", rx: 6 }, gp);
      lab(gp, PX0, PY0 - 10, "push force against travel", "#2D2A26", 12);
      lab(gp, PX0 + PW - 60, PY0 + PH + 18, "travel, mm", "#625C53", 11);
      lab(gp, PX0 + 4, PY0 + 14, H.fmt(fmax, 1) + " N", "#625C53", 11);
      function px(s) { return PX0 + s / 5 * PW; } function py(f) { return PY0 + PH - Math.min(f, fmax) / fmax * (PH - 8); }
      var d = "";
      for (var s = 0; s <= 5.0001; s += 0.02) d += (d ? " L" : "M") + px(s).toFixed(1) + " " + py(force(s)).toFixed(1);
      H.sv("path", { d: d, fill: "none", stroke: "#cfc8bb", "stroke-width": 2, "stroke-dasharray": "4 4" }, gp);
      if (state.trace.length > 1) H.sv("path", { d: "M" + state.trace.map(function (p) { return px(p[0]).toFixed(1) + " " + py(p[1]).toFixed(1); }).join(" L"), fill: "none", stroke: C9, "stroke-width": 3.5, "stroke-linejoin": "round" }, gp);
      H.sv("circle", { cx: px(state.s), cy: py(force(state.s)), r: 6, fill: C9, stroke: "#fff", "stroke-width": 2 }, gp);
      var dx = px(dropAt()); H.sv("line", { x1: dx, y1: PY0 + 6, x2: dx, y2: PY0 + PH, stroke: "#e0402a", "stroke-dasharray": "3 3" }, gp);
      lab(gp, dx + 4, PY0 + 30, "click", "#c0392b", 12);
    }
    function move(v) {
      if (state.broke) { push.set(state.s, true); return; }
      var prev = state.s; state.s = v; state.locked = false;
      if (v < prev && prev >= dropAt() && v < dropAt()) { state.s = prev; push.set(prev, true); state.locked = true; }   // can't come back past the square face
      if (prev < dropAt() && state.s >= dropAt()) { state.clicked = true; if (snd.get()) H.click(Math.min(1, 0.25 + k() * state.h / 2)); }
      var e = strain(defl(state.s));
      if (e > 1.7) { state.broke = true; state.set = defl(state.s) * (1 - 1.7 / e); }
      state.trace.push([state.s, force(state.s)]); if (state.trace.length > 600) state.trace.shift();
      draw(); text();
    }
    function text() {
      var d = defl(state.s), e = strain(d), pk = peak(), em = strain(state.h);
      nTip.set(H.fmt(d, 2) + " mm");
      nStr.set(H.fmt(e, 2) + " %", e > 1.7 ? "hot" : e > 1.0 ? "hot" : "ok");
      nF.set(state.locked ? "locked" : H.fmt(force(state.s), 2) + " N");
      nPk.set(H.fmt(pk, 2) + " N");
      var verdict = em > 1.7 ? "This finger will yield on the way in: at full bend its root stretches " + H.fmt(em, 2) + " %, past 1.7 %. Make it longer or thinner."
        : em > 1.0 ? "Full bend stretches the root " + H.fmt(em, 2) + " %: past the 1.0 % limit for a spring bent now and then. It might survive, but it is living dangerously."
        : em > 0.5 ? "Full bend stretches the root " + H.fmt(em, 2) + " %: fine for a back you open now and then (under 1.0 %), too much for a spring bent at every picture (0.5 %)."
        : "Full bend stretches the root only " + H.fmt(em, 2) + " %: gentle enough for a spring bent at every picture.";
      if (pk < 0.2) verdict += " But the push is so soft (" + H.fmt(pk, 2) + " N) that the click would hardly be felt.";
      if (pk > 3) verdict += " And at " + H.fmt(pk, 1) + " N it is a hard push for one thumb.";
      if (state.locked) verdict = "Pulled straight off, the nub's square face meets the bar's square face. Nothing slopes, so nothing slides. Pinch the pad to let it go.";
      if (state.broke) verdict = "The root stretched past about 1.7 %: the plastic yielded and stays bent. In real life you would see a pale stress mark. Reset, then make the finger longer or thinner.";
      say.textContent = verdict + (state.clicked && !state.locked && !state.broke && state.s >= dropAt() ? " Click: the finger sprang back behind the bar." : "");
    }
    function reset() { state.s = 0; state.clicked = false; state.set = 0; state.locked = false; state.broke = false; state.trace = []; push.set(0, true); draw(); text(); }
    pullB.addEventListener("click", function () {
      if (state.s < dropAt()) { push.set(0, true); state.s = 0; state.trace = []; state.clicked = false; draw(); say.textContent = "Not clicked yet, so it just slides back out. Push it on past the click first."; return; }
      state.locked = true; draw(); text();
    });
    pinchB.addEventListener("click", function () {
      if (state.s < dropAt()) { say.textContent = "Nothing to let go yet: push the back on until it clicks."; return; }
      // pinching bends the finger clear (about 0.5 N a pad on the real back), then the back lifts off
      var steps = api.reducedMotion ? 1 : 24, i = 0;
      (function anim() {
        i++; var t = i / steps; state.set = state.h * Math.sin(Math.PI * Math.min(1, t)) ; state.s = dropAt() * (1 - t) + 0.0; state.locked = false;
        draw();
        if (i < steps) requestAnimationFrame(anim); else { state.set = 0; reset(); say.textContent = "Pinching the pad bent the finger out of the way from the other side, and the back lifted off. On the real back that takes about 0.5 N a pad (model estimate)."; }
      })();
    });
    resetB.addEventListener("click", reset);
    reset();
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ sim: drop a hundred cameras
  // build/platefall.json: percent of drops; off, thrown_clear (part of off), left_up, went_over_and_came_back
  var FALL = {
    one: {
      "0.1": { thin: [54.57, 54.57, 10.81, 9.42], typical: [27.17, 27.17, 2.66, 3.63], fat: [11.8, 11.8, 1.15, 2.83] },
      "0.3": { thin: [66.52, 66.52, 6.65, 15.78], typical: [46.64, 46.64, 0.96, 8.44], fat: [33.66, 33.66, 0.66, 9.52] },
      "0.5": { thin: [70.98, 70.98, 3.74, 15.57], typical: [59.32, 59.32, 8.91, 9.46], fat: [40.29, 40.29, 0.36, 12.19] },
      "1.0": { thin: [74.55, 74.55, 3.08, 13.61], typical: [67.41, 67.41, 2.03, 16.88], fat: [57.78, 57.78, 4.67, 16.74] } },
    three: {
      "0.1": { thin: [10.11, 3.58, 36.44, 10.99], typical: [2.44, 0.27, 14.64, 2.62], fat: [0.58, 0.13, 7.11, 1.03] },
      "0.3": { thin: [19.76, 3.38, 36.68, 20.48], typical: [5.09, 0.26, 19.08, 14.5], fat: [1.49, 0.02, 11.86, 11.6] },
      "0.5": { thin: [22.71, 3.66, 33.59, 25.4], typical: [6.08, 0.1, 30.43, 20.58], fat: [1.43, 0.02, 12.0, 17.08] },
      "1.0": { thin: [22.16, 4.07, 36.96, 26.66], typical: [6.92, 0.14, 31.04, 32.42], fat: [2.54, 0.04, 23.45, 24.01] } }
  };
  CURVE.sim("m02_fall", function (host, api) {
    var r = H.root(host, api, "Drop one hundred cameras in the fall model and count the plates that come off");
    var data = FALL;
    var ctl = H.el("div", { "class": "mk-ctl" }, r);
    var st = { plate: "three", h: "1.0", p: "typical", busy: false };
    var sPlate = H.seg(ctl, "Front plate", [["one", "old: straight up and off"], ["three", "now: up, then sideways"]], "three", function (v) { st.plate = v; show(false); });
    var sH = H.seg(ctl, "Drop height", [["0.1", "10 cm"], ["0.3", "30 cm"], ["0.5", "50 cm"], ["1.0", "1 m"]], "1.0", function (v) { st.h = v; show(false); });
    var sP = H.seg(ctl, "Printer", [["thin", "thin, slippery"], ["typical", "typical"], ["fat", "fat, rough"]], "typical", function (v) { st.p = v; show(false); });
    var stage = H.el("div", { "class": "mk-stage" }, r);
    H.el("div", { "class": "mk-tag" }, stage, "simple fall model");
    var W = 720, HH = 380, svg = H.sv("svg", { viewBox: "0 0 " + W + " " + HH, role: "img", "aria-label": "A grid of one hundred small cameras; each turns red if its front plate came off, amber if the plate was knocked up but held" }, stage);
    var go = H.el("button", { type: "button", "class": "mk-btn go" }, H.el("div", { "class": "mk-ctl" }, r), "Drop all 100");
    var read = H.el("div", { "class": "mk-read" }, r);
    var nOff = H.num(read, "plates off"), nClear = H.num(read, "thrown clear across the floor"), nUp = H.num(read, "knocked up, still held"), nClass = H.num(read, "a class of 30: plates off");
    var say = H.el("p", { "class": "mk-say", "aria-live": "polite" }, r);
    var icons = [], order = [];
    for (var i = 0; i < 100; i++) order.push(i);
    var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    for (i = 99; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)), t = order[i]; order[i] = order[j]; order[j] = t; }
    var G = H.sv("g", { transform: "translate(40,30)" }, svg);
    var floor = H.sv("line", { x1: 20, y1: HH - 14, x2: W - 20, y2: HH - 14, stroke: "#625C53", "stroke-width": 2 }, svg);
    for (i = 0; i < 100; i++) {
      var cx = (i % 10) * 64, cy = Math.floor(i / 10) * 32;
      var g = H.sv("g", { transform: "translate(" + cx + "," + cy + ")" }, G);
      var body = H.sv("rect", { x: 0, y: 6, width: 44, height: 20, rx: 4, fill: "#3b3936" }, g);
      var plate = H.sv("rect", { x: 9, y: 6, width: 26, height: 20, rx: 3, fill: "#D9601A" }, g);
      var lens = H.sv("circle", { cx: 22, cy: 16, r: 4.5, fill: "#9fd3e6", stroke: "#2D2A26" }, g);
      icons.push({ g: g, plate: plate, lens: lens, body: body, x: cx, y: cy });
    }
    function rates() { return data[st.plate][st.h][st.p]; }
    function counts() {
      var q = rates(), off = Math.round(q[0]), clear = Math.round(q[1]), up = Math.round(q[2]), back = Math.round(q[3]);
      return { off: off, clear: Math.min(off, clear), up: up, back: back, raw: q };
    }
    function paint(c, n) {   // n: how many icons revealed so far (in shuffled order)
      for (var k = 0; k < 100; k++) {
        var idx = order[k], ic = icons[idx], kind = k < c.off ? "off" : k < c.off + c.up ? "up" : k < c.off + c.up + c.back ? "back" : "ok";
        var shown = k < n;
        ic.g.setAttribute("opacity", shown ? 1 : 0.7);
        ic.plate.setAttribute("transform", !shown ? "" : kind === "off" ? (k < c.clear ? "translate(14,-14) rotate(25 22 16)" : "translate(6,-8) rotate(12 22 16)") : kind === "up" ? "translate(0,-6)" : "");
        ic.plate.setAttribute("fill", !shown ? "#D9601A" : kind === "off" ? "#d6301f" : kind === "up" ? "#f0a400" : "#D9601A");
        ic.plate.setAttribute("opacity", shown && kind === "off" ? 0.85 : 1);
        ic.lens.setAttribute("transform", ic.plate.getAttribute("transform"));
        ic.body.setAttribute("fill", shown && kind === "back" ? "#566e6b" : "#3b3936");
      }
    }
    function show(anim) {
      var c = counts();
      if (!anim) { paint(c, 0); nOff.set("?"); nClear.set("?"); nUp.set("?"); nClass.set("?"); say.textContent = "Ready: " + (st.plate === "one" ? "the old plate (straight up and off)" : "today's plate (up, then sideways)") + ", " + (st.h === "1.0" ? "1 m" : (+st.h * 100) + " cm") + ", a " + (st.p === "typical" ? "typical" : st.p === "thin" ? "thin, slippery" : "fat, rough") + " printer. Guess how many plates come off, then drop."; return; }
      if (st.busy) return; st.busy = true; go.disabled = true;
      var n = 0, step = api.reducedMotion ? 100 : 4;
      (function tick() {
        n = Math.min(100, n + step); paint(c, n);
        if (n < 100) setTimeout(tick, 22); else done(c);
      })();
    }
    function done(c) {
      st.busy = false; go.disabled = false;
      nOff.set(c.off + " in 100", c.off > 20 ? "hot" : "ok"); nClear.set(c.clear < 1 ? "under 1 in 100" : c.clear + " in 100"); nUp.set(c.up + " in 100");
      var cls = 30 * c.raw[0] / 100; nClass.set("about " + Math.round(cls), cls > 6 ? "hot" : "ok");
      var other = data[st.plate === "one" ? "three" : "one"][st.h][st.p][0];
      say.textContent = "Red: plate off (" + c.off + "). Amber: knocked up but still held, slide it back down (" + c.up + "). Dark: it moved and came back by itself (" + c.back + "). A class of 30 dropping once each: 30 × " + H.fmt(c.raw[0] / 100, 2) + " = " + H.fmt(cls, 1) + ". " +
        (st.plate === "one" ? "Today's plate, same drop: " + Math.round(other) + " in 100." : "The old plate, same drop: " + Math.round(other) + " in 100.");
    }
    go.addEventListener("click", function () { show(true); });
    show(false);
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ figures
  function S(w, h, label, body) { return '<svg viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;font-family:var(--sans,system-ui,sans-serif)">' + body + "</svg>"; }
  function T(x, y, s, o) { o = o || {}; return '<text x="' + x + '" y="' + y + '" font-size="' + (o.size || 15) + '" font-weight="' + (o.w || 600) + '" fill="' + (o.fill || "#2D2A26") + '"' + (o.anchor ? ' text-anchor="' + o.anchor + '"' : "") + ">" + s + "</text>"; }

  CURVE.fig("fig_m02_nine", function () {
    var parts = [["body", "#3b3936", "r"], ["back", "#c9cdcf", "r"], ["front plate", "#D9601A", "r"], ["shutter", "#8145C0", "s"], ["dot wheel", "#f2c230", "c"], ["spool", "#d6301f", "c"], ["green winder", "#2fa84f", "c"], ["frame wheel", "#2f6fe0", "c"], ["lens", "#9fd3e6", "l"]];
    var b = "";
    parts.forEach(function (p, i) {
      var x = 40 + (i % 5) * 136, y = i < 5 ? 40 : 170;
      if (p[2] === "r") b += '<rect x="' + (x - 34) + '" y="' + (y) + '" width="68" height="62" rx="9" fill="' + p[1] + '"/>';
      if (p[2] === "s") b += '<path d="M' + (x - 30) + " " + (y + 10) + " L" + (x + 30) + " " + (y + 2) + " L" + (x + 26) + " " + (y + 60) + " L" + (x - 20) + " " + (y + 52) + 'Z" fill="' + p[1] + '"/>';
      if (p[2] === "c") b += '<circle cx="' + x + '" cy="' + (y + 31) + '" r="31" fill="' + p[1] + '"/>';
      if (p[2] === "l") b += '<ellipse cx="' + x + '" cy="' + (y + 31) + '" rx="13" ry="31" fill="' + p[1] + '" stroke="#2D2A26" stroke-width="2"/>';
      b += T(x, y + 86, p[0], { anchor: "middle", size: 14 });
    });
    b += '<g transform="translate(560,190)"><circle r="40" fill="none" stroke="#c0392b" stroke-width="5"/><line x1="-28" y1="28" x2="28" y2="-28" stroke="#c0392b" stroke-width="5"/>' + T(0, 5, "screws", { anchor: "middle", size: 13 }) + "</g>";
    return S(680, 290, "The nine pieces of the camera: body, back, front plate, shutter, dot wheel, spool, green winder, frame wheel and lens. No screws.", b);
  });

  CURVE.fig("fig_m02_catch", function () {
    var b = "";
    // first: a stiff hook jamming
    b += T(20, 28, "First guess: stiff", { size: 16 });
    b += '<rect x="60" y="44" width="34" height="120" rx="4" fill="#5d5a55"/><path d="M94 140 L120 164 L94 164Z" fill="#5d5a55"/>';
    b += '<path d="M104 176 L150 176 L150 230 L104 230Z" fill="#3b3936"/><path d="M104 176 L130 150 L150 150 L150 176Z" fill="#3b3936"/>';
    b += '<g stroke="#c0392b" stroke-width="7" stroke-linecap="round"><line x1="30" y1="190" x2="80" y2="240"/><line x1="80" y1="190" x2="30" y2="240"/></g>' + T(20, 266, "jams, or cracks", { fill: "#c0392b", size: 14 });
    // second: the soft finger
    var x = 330;
    b += T(x - 60, 28, "What it really is: soft, and shaped", { size: 16 });
    b += '<rect x="' + (x - 70) + '" y="40" width="120" height="22" rx="5" fill="#c9cdcf"/>' + T(x - 64, 56, "the back", { size: 12 });
    b += '<path d="M' + (x - 30) + " 62 Q" + (x - 28) + " 140 " + (x - 6) + " 196 L" + (x + 4) + " 196 Q" + (x - 18) + " 140 " + (x - 20) + ' 62Z" fill="#14a08c"/>';
    b += '<path d="M' + (x + 4) + " 172 L" + (x + 24) + " 192 L" + (x + 24) + " 200 L" + (x - 4) + ' 200Z" fill="#14a08c"/>' + T(x + 30, 186, "nub", { size: 12 });
    b += '<path d="M' + (x - 30) + " 62 L" + (x - 30) + " 196 L" + (x - 20) + " 196 L" + (x - 20) + ' 62Z" fill="none" stroke="#14a08c" stroke-dasharray="4 4" opacity=".7"/>';
    // bar on the body
    var bx = x - 4, by = 210;
    b += '<path d="M' + (bx + 30) + " " + (by - 8) + " L" + (bx + 2) + " " + (by + 20) + " L" + (bx + 2) + " " + (by + 44) + " L" + (bx + 180) + " " + (by + 44) + " L" + (bx + 180) + " " + (by - 8) + 'Z" fill="#3b3936"/>';
    b += '<line x1="' + (bx + 30) + '" y1="' + (by - 8) + '" x2="' + (bx + 2) + '" y2="' + (by + 20) + '" stroke="#2fbf71" stroke-width="6" stroke-linecap="round"/>';
    b += T(bx + 200, by + 4, "slope: the way in", { fill: "#1d8a52", size: 14 });
    b += '<path d="M' + (bx + 2) + " " + (by + 44) + " L" + (bx + 2) + " " + (by + 20) + '" stroke="#e0402a" stroke-width="0"/>';
    b += '<line x1="' + (bx + 2) + '" y1="' + (by + 44) + '" x2="' + (bx + 70) + '" y2="' + (by + 44) + '" stroke="#e0402a" stroke-width="6" stroke-linecap="round"/>';
    b += T(bx + 200, by + 40, "square face: the way out", { fill: "#c0392b", size: 14 });
    b += '<path d="M' + (x + 70) + " 120 q30 0 30 30" + '" fill="none" stroke="#2D2A26" stroke-width="2" marker-end="url(#a9)"/>' + T(x + 80, 108, "bends, then springs back", { size: 13, w: 400 });
    b += '<defs><marker id="a9" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#2D2A26"/></marker></defs>';
    return S(720, 280, "Left: a stiff hook jams against the bar. Right: the back's long soft finger bends as its nub rides up the bar's green slope, then springs back behind the red square face, which stops it coming out.", b);
  });

  CURVE.fig("fig_m02_finger", function () {
    var b = "";
    function finger(x, L, t, col, label, eps) {
      var bend = 26, s = "";
      s += '<rect x="' + (x - 20) + '" y="30" width="' + (t + 40) + '" height="16" fill="#c9cdcf"/>';
      s += '<path d="M' + x + " 46 Q" + x + " " + (46 + L * 0.6) + " " + (x + bend) + " " + (46 + L) + " L" + (x + bend + t) + " " + (46 + L) + " Q" + (x + t) + " " + (46 + L * 0.6) + " " + (x + t) + ' 46Z" fill="' + col + '"/>';
      s += '<ellipse cx="' + (x + t / 2) + '" cy="50" rx="' + (t / 2 + 9) + '" ry="9" fill="none" stroke="' + (eps > 1 ? "#d6301f" : "#e6b800") + '" stroke-width="4"/>';
      s += T(x - 10, 46 + L + 34, label, { size: 14 });
      s += T(x - 10, 46 + L + 54, "root stretch about " + eps + " %", { size: 13, w: 400, fill: eps > 1 ? "#c0392b" : "#625C53" });
      s += '<line x1="' + (x + t) + '" y1="' + (46 + L + 10) + '" x2="' + (x + bend + t) + '" y2="' + (46 + L + 10) + '" stroke="#2D2A26" stroke-width="2"/>';
      return s;
    }
    // long thin: L=18 mm, t=1.0 mm, bend 1.6 mm: 1.5*1*1.6/324 = 0.74 %;  short thick: L=9, t=2: 1.5*2*1.6/81 = 5.9 %
    b += finger(80, 200, 9, "#f6dc7a", "long and thin: 18 mm by 1 mm", "0.7");
    b += finger(420, 100, 18, "#e4572e", "short and thick: 9 mm by 2 mm", "5.9");
    b += T(420, 220, "same 1.6 mm bend at the tip", { size: 13, w: 400, fill: "#625C53" });
    b += T(420, 240, "strain = 1.5 × thickness × bend ÷ length²", { size: 13, w: 600 });
    return S(720, 320, "Two fingers bent the same 1.6 mm at the tip. The long thin one, 18 by 1 mm, stretches about 0.7 % at its root; the short thick one, 9 by 2 mm, about 5.9 %, far past the 1.7 % where the plastic stays bent.", b);
  });

  CURVE.fig("fig_m02_path", function () {
    var b = '<defs><marker id="p9" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#14a08c"/></marker></defs>';
    b += '<rect x="170" y="60" width="380" height="190" rx="18" fill="#3b3936"/>';
    b += '<rect x="250" y="70" width="210" height="170" rx="12" fill="#D9601A"/><circle cx="355" cy="160" r="34" fill="#9fd3e6" stroke="#2D2A26" stroke-width="3"/>';
    [[262, 230], [448, 230], [262, 80], [448, 80]].forEach(function (p) { b += '<rect x="' + (p[0] - 8) + '" y="' + (p[1] - 6) + '" width="16" height="12" fill="#ffb27a" stroke="#2D2A26"/>'; });
    var A = 'stroke="#14a08c" stroke-width="7" fill="none" marker-end="url(#p9)" stroke-linecap="round"';
    b += '<path d="M355 54 L355 16" ' + A + "/>" + T(370, 30, "1. up, past the click", { size: 15 });
    b += '<path d="M470 110 L560 110" ' + A + "/>" + T(568, 100, "2. sideways,", { size: 15 }) + T(568, 120, "lips out from", { size: 13, w: 400 }) + T(568, 136, "under the skin", { size: 13, w: 400 });
    b += '<g transform="translate(600,220)"><circle r="20" fill="none" stroke="#14a08c" stroke-width="5"/><circle r="5" fill="#14a08c"/></g>' + T(568, 268, "3. away from the body", { size: 15 });
    b += '<g transform="translate(70,150)"><path d="M-40 0 L20 0" stroke="#c0392b" stroke-width="7" marker-end="url(#k9)"/></g><defs><marker id="k9" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#c0392b"/></marker></defs>';
    b += T(14, 190, "a knock:", { size: 14, fill: "#c0392b" }) + T(14, 208, "one direction", { size: 13, w: 400, fill: "#c0392b" }) + T(14, 224, "at a time", { size: 13, w: 400, fill: "#c0392b" });
    return S(720, 290, "The front plate from the front. To come off it must move up past its click, then sideways so the lips on its four feet leave the body's skin, then away from the body. A knock pushes in only one direction at a time.", b);
  });
})();
