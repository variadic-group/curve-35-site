/* CURVE 35, maker lesson M3 "How we know it works": interactive pieces and figures.
   Numbers: build/focus.json "check" (blur at 1, 1.5, 2, 4 m and far, large dot, middle of the picture, with the lens 0.6 mm in to 0.8 mm out;
   sharp on a postcard 0.05 mm; one layer of the seat 0.2 mm; LENS_SEAT in scad/one135.scad), build/exposure.json (ISO 400). */
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

  var C12 = "#e0402a";
  var CHECK = [
    [-0.6, "far", [0.151, 0.112, 0.093, 0.065, 0.04], 3], [-0.4, "far", [0.13, 0.091, 0.072, 0.045, 0.025], 2], [-0.2, "far", [0.108, 0.069, 0.051, 0.028, 0.025], 1],
    [0.0, "4 m", [0.086, 0.049, 0.033, 0.023, 0.04], 0], [0.2, "2 m", [0.065, 0.031, 0.023, 0.035, 0.06], -1], [0.4, "1.5 m", [0.045, 0.023, 0.03, 0.054, 0.081], -2],
    [0.6, "1 m", [0.028, 0.032, 0.048, 0.074, 0.102], -3], [0.8, "1 m", [0.023, 0.05, 0.068, 0.096, 0.124], -4]];
  var NAMES = ["1 m", "1.5 m", "2 m", "4 m", "far"];
  var uid = 0;

  // ------------------------------------------------------------------ sim: the five-thing focus check
  CURVE.sim("m03_five", function (host, api) {
    var r = H.root(host, api, "The five-thing focus check: predict which of five things is sharpest, then diagnose a mystery camera");
    var id = "m03f" + (++uid);
    var st = { row: 3, mode: "predict", guess: null, mystery: null, solved: false };
    var top = H.el("div", { "class": "mk-ctl" }, r);
    var sMode = H.seg(top, "Mode", [["predict", "1. predict"], ["explore", "2. move the lens"], ["mystery", "3. mystery camera"]], "predict", function (v) { st.mode = v; if (v === "mystery") newMystery(); if (v === "predict") { st.row = 3; st.guess = null; } draw(); });
    var stage = H.el("div", { "class": "mk-stage" }, r);
    var W = 720, HH = 300, svg = H.sv("svg", { viewBox: "0 0 " + W + " " + HH, role: "img", "aria-label": "Five boxes with letters on them at 1, 1.5, 2 and 4 metres and far away, each blurred as the camera would see it, and a bar chart of their blur" }, stage);
    var tag = H.el("div", { "class": "mk-tag" }, stage, "simulated from the model's blur");
    var ctl = H.el("div", { "class": "mk-ctl" }, r);
    var sl = H.slider(ctl, { label: "Lens: how far it sits from where it should", min: 0, max: 7, step: 1, value: 3, fmt: function (v) { var o = CHECK[v][0]; return (o > 0 ? "+" : "") + H.fmt(o, 1) + " mm" + (o === 0 ? " (as designed)" : o > 0 ? " (too far from the film)" : " (too close to the film)"); }, on: function (v) { st.row = v; draw(); } });
    var ans = H.el("div", { "class": "mk-f" }, ctl); H.el("span", null, ans, "Your diagnosis");
    var ansSeg = H.el("div", { "class": "mk-seg" }, ans), ansBtns = [];
    [[2, "LENS_SEAT +0.4"], [1, "+0.2"], [0, "leave it"], [-1, "−0.2"], [-2, "−0.4"], [-3, "−0.6"]].forEach(function (o) { var b = H.el("button", { type: "button" }, ansSeg, o[1]); b.addEventListener("click", function () { diagnose(o[0]); }); ansBtns.push(b); });
    var say = H.el("p", { "class": "mk-say", "aria-live": "polite" }, r);
    function newMystery() { var choices = [1, 2, 4, 5, 6, 3]; st.mystery = choices[Math.floor(Math.random() * choices.length)]; st.solved = false; }
    function diagnose(layers) {
      if (st.mode !== "mystery") return;
      var right = CHECK[st.mystery][3];
      if (layers === right) { st.solved = true; say.textContent = "Right. This camera's lens sat " + H.fmt(CHECK[st.mystery][0], 1) + " mm out, so the " + CHECK[st.mystery][1] + " thing came out sharpest. " + (right === 0 ? "Nothing to change." : "Change LENS_SEAT by " + (right > 0 ? "+" : "−") + H.fmt(Math.abs(right) * 0.2, 1) + " mm (" + Math.abs(right) + " layer" + (Math.abs(right) > 1 ? "s" : "") + "), reprint the front plate and shoot the card again.") + " Press 'mystery camera' for another."; draw(); }
      else say.textContent = "Not quite. Look again: which thing is sharpest, and how soft are the others? Nearer than 4 m: the lens sits too far from the film, so lower LENS_SEAT. The far one: too close, so raise it. Each layer is 0.2 mm.";
    }
    function draw() {
      svg.innerHTML = "";
      var row = st.mode === "mystery" ? st.mystery : st.mode === "predict" && st.guess == null ? 3 : st.row, R = CHECK[row];
      var defs = H.sv("defs", null, svg);
      var showNums = !(st.mode === "predict" && st.guess == null) && !(st.mode === "mystery" && !st.solved);
      H.sv("rect", { x: 0, y: 0, width: W, height: 150, fill: "#dbe9f3" }, svg);
      H.sv("rect", { x: 0, y: 150, width: W, height: 40, fill: "#b8c8a6" }, svg);
      // the camera
      H.sv("rect", { x: 14, y: 128, width: 34, height: 26, rx: 4, fill: "#3b3936" }, svg); H.sv("circle", { cx: 48, cy: 141, r: 5, fill: "#9fd3e6" }, svg);
      var xs = [130, 245, 360, 480, 620], sizes = [62, 54, 48, 42, 0];
      R[2].forEach(function (b, i) {
        var f = H.sv("filter", { id: id + "b" + i, x: "-30%", y: "-30%", width: "160%", height: "160%" }, defs);
        H.sv("feGaussianBlur", { stdDeviation: (b * 38).toFixed(2) }, f);
        var g = H.sv("g", { filter: "url(#" + id + "b" + i + ")" }, svg), x = xs[i];
        if (i < 4) {
          var s = sizes[i];
          H.sv("rect", { x: x - s / 2, y: 160 - s, width: s, height: s, fill: "#fff", stroke: "#2D2A26", "stroke-width": 1.5 }, g);
          for (var k = 0; k < 5; k++) H.sv("rect", { x: x - s / 2 + 5 + k * (s - 10) / 5, y: 160 - s + 6, width: (s - 10) / 10, height: s - 12, fill: "#1d1a17" }, g);
        } else {   // far: a roof with tiles
          H.sv("path", { d: "M" + (x - 70) + " 110 L" + x + " 70 L" + (x + 70) + " 110Z", fill: "#b8452c" }, g);
          for (var t = 0; t < 7; t++) H.sv("line", { x1: x - 60 + t * 20, y1: 106, x2: x - 6 + t * 6, y2: 76, stroke: "#6e2a1b", "stroke-width": 2 }, g);
          H.sv("rect", { x: x - 60, y: 110, width: 120, height: 50, fill: "#a9a39a" }, g);
        }
        var lt = H.sv("text", { x: x, y: 182, "text-anchor": "middle", style: "font:600 13px var(--sans,system-ui,sans-serif)", fill: "#2D2A26" }, svg); lt.textContent = NAMES[i];
        // bar chart
        var by = 290, bh = Math.min(1, b / 0.16) * 80, bx = x - 18;
        if (showNums) {
          H.sv("rect", { x: bx, y: by - bh, width: 36, height: bh, rx: 4, fill: b <= 0.05 ? "#1f8a70" : C12 }, svg);
          var vt = H.sv("text", { x: x, y: by - bh - 6, "text-anchor": "middle", style: "font:600 12px var(--sans,system-ui,sans-serif)", fill: "#2D2A26" }, svg); vt.textContent = H.fmt(b, 3);
        }
        if (st.mode === "predict" && st.guess == null) {
          var btn = H.sv("rect", { x: x - 40, y: 196, width: 80, height: 30, rx: 15, fill: "#fff", stroke: "#2D2A26", "stroke-width": 2, tabindex: 0, role: "button", "aria-label": "Predict: " + NAMES[i] + " is sharpest", style: "cursor:pointer" }, svg);
          var bt = H.sv("text", { x: x, y: 216, "text-anchor": "middle", style: "font:600 12px var(--sans,system-ui,sans-serif);pointer-events:none", fill: "#2D2A26" }, svg); bt.textContent = "sharpest?";
          (function (ii) { btn.addEventListener("click", function () { guess(ii); }); btn.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); guess(ii); } }); })(i);
        }
      });
      if (showNums) { var ly = 290 - 0.05 / 0.16 * 80; H.sv("line", { x1: 90, y1: ly, x2: 690, y2: ly, stroke: "#2D2A26", "stroke-dasharray": "5 4" }, svg); var pt = H.sv("text", { x: 92, y: ly - 4, style: "font:600 11px var(--sans,system-ui,sans-serif)", fill: "#2D2A26" }, svg); pt.textContent = "0.05 mm: sharp on a postcard"; }
      sl.input.disabled = st.mode !== "explore";
      ans.style.display = st.mode === "mystery" ? "" : "none";
      tag.textContent = st.mode === "mystery" ? "simulated: a mystery camera's test frame" : "simulated from the model's blur";
      if (st.mode === "explore") {
        var sharp = R[2].filter(function (b) { return b <= 0.05; }).length;
        say.textContent = "Lens " + (R[0] > 0 ? "+" : "") + H.fmt(R[0], 1) + " mm. Sharpest: the " + R[1] + " thing. " + sharp + " of 5 pass the 0.05 mm postcard test. " + (R[3] === 0 ? "This is the camera as designed." : "Fix: LENS_SEAT " + (R[3] > 0 ? "+" : "−") + H.fmt(Math.abs(R[3]) * 0.2, 1) + " mm.");
      }
      if (st.mode === "mystery" && !st.solved) say.textContent = "A camera came off a friend's printer. This is its test frame. Which thing is sharpest, and what would you change in one135.scad? Pick your fix.";
    }
    function guess(i) {
      st.guess = i; draw();
      var R = CHECK[3][2];
      say.textContent = (i === 3 ? "Yes: the 4 m thing. " : "The model says the 4 m thing, not the " + NAMES[i] + " one. ") + "The lens is set for 3.7 m, so 4 m has the least blur (0.023 mm). The 1 m thing has " + H.fmt(R[0], 3) + " mm, about 3.7 times as much, and fails the postcard test. Far away (" + R[4] + " mm) is softer than 4 m too. Now try mode 2.";
    }
    draw();
    say.textContent = "Five things stand in a line at 1, 1.5, 2 and 4 metres and far away. Large dot, middle of the picture. Before any numbers: which one will come out sharpest? Tap it.";
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ sim: the proof roll, planned and ticked
  var FRAMES = [
    { what: "The reference card in the middle, 4 m, camera resting", dot: null, light: null, model: "The sharpest frame of the roll, in its middle. It becomes the first row of the record: every later camera is judged against it." },
    { what: "One scene at the small dot", dot: "small", light: null, model: "Same light as frames 3 and 4. The darkest of the three, and the sharpest toward the ends." },
    { what: "The same scene at the middle dot", dot: "middle", light: null, model: "About twice the light of frame 2." },
    { what: "The same scene at the large dot", dot: "large", light: null, model: "About a third more light again; the softest toward the ends." },
    { what: "Full sun", dot: "small", light: "sun", model: "About half a step more light than needed: inside what the film forgives." },
    { what: "Deep shade (or indoors by a window)", dot: "large", light: "shade", model: "Too dark: about two steps under, outside what the film forgives. Predicted to fail. If it doesn't, that's news." },
    { what: "Something moving, camera panned with it", dot: null, light: null, model: "The moving thing sharper than the background." },
    { what: "A time picture: camera on a table, rocker held level, count as the chart says", dot: "small", light: null, model: "Correctly lit, if the camera did not move." },
    { what: "Two pictures on one: press, don't wind, press again", dot: null, light: null, model: "Both pictures, each fainter where the other is bright." },
    { what: "A portrait at 1.5 m", dot: null, light: null, model: "Sharp in the middle at every dot; the picture about 1.1 m tall, so the face is small and the body cut." },
    { what: "The same portrait at 4 m", dot: null, light: null, model: "Sharp; the whole person small; the picture 3 m tall." },
    { what: "Into the light, one dot bigger than the chart", dot: null, light: "sun", model: "Bright edges; the face lit enough to see." }];
  var LIGHT = { sun: ["full sun", 2.0], hazy: ["hazy sun", 1.0], cloud: ["bright cloud", 0.0], overcast: ["overcast", -1.0], shade: ["deep shade", -2.0] };
  var DOTOFF = { small: -1.54, middle: -0.43, large: 0 };
  var VAGUE = /\b(nice|good|ok|okay|cool|fine|great|normal|decent|pretty|alright|bad|interesting)\b/i;
  var CONCRETE = /(\d|sharp|soft|blur|dark|light|bright|middle|edge|end|corner|tall|cut|whole|face|streak|faint|dense|thin|half|third|quarter|fill)/i;
  CURVE.sim("m03_roll", function (host, api) {
    var r = H.root(host, api, "The test roll: twelve frames, each with a prediction written before the film goes in, ticked off as you shoot and checked when the scans come back");
    var KEY = "curve-m3-test-roll", data;
    try { data = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { data = null; }
    if (!data || !data.rows || data.rows.length !== 12) data = { rows: FRAMES.map(function (f) { return { dot: f.dot || "", light: f.light || "", expect: "", shot: false, right: "" }; }), sealed: false };
    function save() { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) { } }
    var head = H.el("div", { "class": "mk-read" }, r);
    var nW = H.num(head, "predictions written"), nC = H.num(head, "checkable"), nS = H.num(head, "frames shot"), nR = H.num(head, "came out as said");
    var list = H.el("ol", { style: "list-style:none;margin:14px 0 0;padding:0;display:grid;gap:10px" }, r);
    var rows = [];
    FRAMES.forEach(function (f, i) {
      var d = data.rows[i];
      var li = H.el("li", { "class": "mk-card" }, list);
      var top = H.el("div", { style: "display:flex;gap:10px;align-items:baseline;flex-wrap:wrap" }, li);
      H.el("b", { style: "font-size:22px;min-width:2.2em;color:#c0392b" }, top, String(i + 1));
      H.el("span", { style: "font-weight:600;flex:1 1 260px" }, top, f.what);
      var sel = H.el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;margin:8px 0" }, li);
      var dotS = H.el("select", { "aria-label": "Frame " + (i + 1) + ": dot" }, sel);
      [["", "dot?"], ["small", "small dot"], ["middle", "middle dot"], ["large", "large dot"]].forEach(function (o) { var op = H.el("option", { value: o[0] }, dotS, o[1]); if (d.dot === o[0]) op.selected = true; });
      var litS = H.el("select", { "aria-label": "Frame " + (i + 1) + ": light" }, sel);
      [["", "light?"]].concat(Object.keys(LIGHT).map(function (k) { return [k, LIGHT[k][0]]; })).forEach(function (o) { var op = H.el("option", { value: o[0] }, litS, o[1]); if (d.light === o[0]) op.selected = true; });
      [dotS, litS].forEach(function (s) { s.style.cssText = "font:600 14px var(--sans,system-ui,sans-serif);padding:6px 8px;border-radius:8px;border:2px solid var(--ink,#2D2A26);background:#fff"; });
      var hint = H.el("span", { style: "font-size:13px;color:#625C53;align-self:center" }, sel);
      var ta = H.el("textarea", { rows: 2, placeholder: "I expect… (sharp or soft, where? light or dark? what fills the picture?)", "aria-label": "Frame " + (i + 1) + ": I expect", style: "width:100%;font:15px var(--sans,system-ui,sans-serif);padding:8px;border-radius:8px;border:1px solid var(--rule,#DDD6CA);resize:vertical" }, li);
      ta.value = d.expect;
      var flag = H.el("div", { style: "font-size:13px;min-height:1.2em;margin:4px 0" }, li);
      var bot = H.el("div", { style: "display:flex;gap:12px;flex-wrap:wrap;align-items:center" }, li);
      var mb = H.el("button", { type: "button", "class": "mk-btn" }, bot, "What the model says");
      var shot = H.el("label", { style: "display:flex;gap:6px;align-items:center;font-weight:600" }, bot); var shC = H.el("input", { type: "checkbox" }, shot); H.el("span", null, shot, "shot"); shC.checked = d.shot;
      var rr = H.el("div", { "class": "mk-seg", role: "group", "aria-label": "Frame " + (i + 1) + ": came out as predicted?" }, bot), rb = [];
      [["yes", "came out as said"], ["no", "it didn't"]].forEach(function (o) { var b = H.el("button", { type: "button", "aria-pressed": String(d.right === o[0]) }, rr, o[1]); b.addEventListener("click", function () { d.right = d.right === o[0] ? "" : o[0]; rb.forEach(function (x, j) { x.setAttribute("aria-pressed", String(d.right === ["yes", "no"][j])); }); upd(); }); rb.push(b); });
      var mp = H.el("p", { hidden: "", style: "margin:8px 0 0;padding:8px 10px;background:#EFEBE3;border-radius:8px;font-size:14px" }, li, "The model: " + f.model);
      mb.addEventListener("click", function () { mp.hidden = !mp.hidden; mb.textContent = mp.hidden ? "What the model says" : "Hide the model"; });
      function light() {
        if (!d.dot || !d.light) { hint.textContent = ""; return; }
        var s = LIGHT[d.light][1] + DOTOFF[d.dot] + (i === 11 ? -2 : 0);
        hint.textContent = "by the model: " + (s >= 0 ? "+" : "") + H.fmt(s, 1) + " steps " + (i === 11 ? "on the face " : "") + (s < -1 ? "(too dark: outside what the film forgives)" : s > 3 ? "(far too much light)" : "(inside what the film forgives)");
        hint.style.color = s < -1 || s > 3 ? "#c0392b" : "#625C53";
      }
      function check() {
        var t = ta.value.trim();
        if (!t) { flag.textContent = ""; return 0; }
        if (VAGUE.test(t) && !CONCRETE.test(t)) { flag.textContent = "Can this be wrong? 'It will be nice' can't be checked. Say what will be sharp, light or dark, or how much fills the picture."; flag.style.color = "#c0392b"; return 0; }
        if (!CONCRETE.test(t)) { flag.textContent = "Make it checkable: name a place (middle, ends), a size or a brightness."; flag.style.color = "#b26a00"; return 0; }
        flag.textContent = "Checkable: a scan can prove this right or wrong."; flag.style.color = "#1f8a70"; return 1;
      }
      dotS.addEventListener("change", function () { d.dot = dotS.value; light(); upd(); });
      litS.addEventListener("change", function () { d.light = litS.value; light(); upd(); });
      ta.addEventListener("input", function () { d.expect = ta.value; upd(); });
      shC.addEventListener("change", function () { d.shot = shC.checked; upd(); });
      light();
      rows.push({ check: check, ta: ta });
    });
    var bar = H.el("div", { "class": "mk-ctl" }, r);
    var cp = H.el("button", { type: "button", "class": "mk-btn go" }, bar, "Copy my sheet");
    var rs = H.el("button", { type: "button", "class": "mk-btn" }, bar, "Start a new roll");
    var say = H.el("p", { "class": "mk-say", "aria-live": "polite" }, r);
    function upd() {
      var w = 0, c = 0, s = 0, y = 0, judged = 0;
      data.rows.forEach(function (d, i) { if (d.expect.trim()) w++; c += rows[i] ? rows[i].check() : 0; if (d.shot) s++; if (d.right === "yes") y++; if (d.right) judged++; });
      nW.set(w + " / 12", w === 12 ? "ok" : ""); nC.set(c + " / 12", c === 12 ? "ok" : ""); nS.set(s + " / 12", s === 12 ? "ok" : ""); nR.set(judged ? y + " / " + judged : "–");
      say.textContent = w < 12 ? "Write all twelve predictions before the film goes in. Your sheet is saved in this browser as you type." : s < 12 ? "All twelve said first. Now load the film, shoot, and tick each frame. Don't change a prediction after the film is posted." : judged < 12 ? "Roll shot. When the scans come back, mark each frame: did it come out as you said? Right or wrong, write why." : "Done: " + y + " of 12 came out as said. Every 'no' is a clue: which one thing would you change, and which frame would tell you if it worked?";
      save();
    }
    cp.addEventListener("click", function () {
      var txt = "CURVE 35 test roll\n" + FRAMES.map(function (f, i) { var d = data.rows[i]; return (i + 1) + ". " + f.what + " | dot: " + (d.dot || "-") + " | light: " + (d.light ? LIGHT[d.light][0] : "-") + " | I expect: " + (d.expect || "-") + " | shot: " + (d.shot ? "yes" : "no") + " | as said: " + (d.right || "-"); }).join("\n");
      try { navigator.clipboard.writeText(txt).then(function () { say.textContent = "Copied. Paste it somewhere safe and keep it with the roll."; }, function () { say.textContent = txt; }); } catch (e) { say.textContent = txt; }
    });
    rs.addEventListener("click", function () { if (!window.confirm || window.confirm("Clear all twelve rows?")) { try { localStorage.removeItem(KEY); } catch (e) { } host.innerHTML = ""; CURVE.sims.m03_roll(host, api); } });
    upd();
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ figures
  function S(w, h, label, body) { return '<svg viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;font-family:var(--sans,system-ui,sans-serif)">' + body + "</svg>"; }
  function T(x, y, s, o) { o = o || {}; return '<text x="' + x + '" y="' + y + '" font-size="' + (o.size || 15) + '" font-weight="' + (o.w || 600) + '" fill="' + (o.fill || "#2D2A26") + '"' + (o.anchor ? ' text-anchor="' + o.anchor + '"' : "") + ">" + s + "</text>"; }

  CURVE.fig("fig_m03_ledger", function () {
    var b = "", L = [["light: 69 million rays, none on the film", "no fog on a roll left in the sun"], ["fit: five printers, nothing binds", "every part prints clean, first try"], ["motion: 1865 positions, no collision", "the clicks feel like clicks"], ["focus: the 4 m thing sharpest", "the check picture: is it?"], ["shutter about 1/322 s", "slow-motion video of the blade"], ["", "a 13-year-old builds it from the guide alone"]];
    b += '<rect x="10" y="10" width="345" height="300" rx="14" fill="#e3ecfd" stroke="#2b6cd8" stroke-width="3"/><rect x="365" y="10" width="345" height="300" rx="14" fill="#fff1e8" stroke="' + C12 + '" stroke-width="3"/>';
    b += T(26, 42, "The model says it should", { fill: "#1e4fa8", size: 18 }) + T(381, 42, "A print and a roll show it did", { fill: "#a3301f", size: 18 });
    L.forEach(function (row, i) {
      var y = 76 + i * 38;
      if (row[0]) b += '<circle cx="34" cy="' + (y - 5) + '" r="9" fill="#2b6cd8"/><path d="M29 ' + (y - 5) + " l4 4 l7 -8" + '" stroke="#fff" stroke-width="2.5" fill="none"/>' + T(52, y, row[0], { size: 13, w: 400 });
      b += '<rect x="380" y="' + (y - 14) + '" width="18" height="18" rx="4" fill="#fff" stroke="' + C12 + '" stroke-width="2"/>' + T(408, y, row[1], { size: 13, w: 400 });
    });
    b += T(381, 300, "Empty boxes: your roll fills them.", { size: 13, fill: "#a3301f" });
    return S(720, 320, "Two columns. Left, checked in the model: light, fit, motion, focus, shutter time. Right, still empty boxes that only a printed camera and a roll can tick: no fog, clean prints, clicks that feel right, a sharp check picture, the real shutter time, a first-time builder.", b);
  });

  CURVE.fig("fig_m03_card", function () {
    var b = '<rect x="160" y="10" width="400" height="280" rx="6" fill="#fff" stroke="#2D2A26" stroke-width="3"/>';
    // bars in groups, getting finer
    var x = 190; [14, 10, 7, 5, 3.5].forEach(function (w) { for (var k = 0; k < 3; k++) b += '<rect x="' + (x + k * w * 2) + '" y="40" width="' + w + '" height="70" fill="#1d1a17"/>'; x += w * 6 + 14; });
    b += T(190, 130, "bars: the finest you can count = how sharp", { size: 12, w: 400 });
    // star
    var cx = 460, cy = 90, R = 60; for (var s = 0; s < 18; s++) { var a0 = s * Math.PI / 9, a1 = a0 + Math.PI / 18; b += '<path d="M' + cx + " " + cy + " L" + (cx + R * Math.cos(a0)).toFixed(1) + " " + (cy + R * Math.sin(a0)).toFixed(1) + " L" + (cx + R * Math.cos(a1)).toFixed(1) + " " + (cy + R * Math.sin(a1)).toFixed(1) + 'Z" fill="#1d1a17"/>'; }
    b += T(cx, 168, "a star: blur shows as a grey middle", { size: 12, w: 400, anchor: "middle" });
    // grey steps
    for (var g = 0; g < 5; g++) { var v = Math.round(240 - g * 50); b += '<rect x="' + (210 + g * 60) + '" y="200" width="60" height="50" fill="rgb(' + v + "," + v + "," + v + ')" stroke="#2D2A26"/>'; }
    b += T(360, 274, "five grey steps: was the light right?", { size: 12, w: 400, anchor: "middle" });
    b += T(16, 40, "The", { size: 16 }) + T(16, 60, "reference", { size: 16 }) + T(16, 80, "card", { size: 16 }) + T(16, 110, "taped to a wall,", { size: 12, w: 400 }) + T(16, 126, "the camera 4 m", { size: 12, w: 400 }) + T(16, 142, "away, the card in", { size: 12, w: 400 }) + T(16, 158, "the middle", { size: 12, w: 400 });
    return S(720, 300, "The reference card: groups of black bars getting finer, a star of black spokes, and five grey steps. Photographed from 4 m, the finest bars you can count say how sharp the camera is.", b);
  });
})();
