/* CURVE 35, maker lesson M4 "Made for hands": interactive pieces and figures (from old lesson 10).
   Numbers: course/FACTS.md (lens 32 mm, shutter about 1/300 s (1/322 by the model), picture 36 x 24 mm), SOUND.md (rocker about 2.3 N,
   5 mm of travel), scad/one135.scad (pad top H + PAD_UP = 30.0 mm above the lens's line; front point 35 mm forward and
   SIGHT_DROP = 0.375 mm lower; crossing 2800 mm), build/sightcheck.json (aim 4.3 % high at 0.7 m, 1.4 % at 1.4 m). */
(function () {
  "use strict";
  if (!window.CURVE || !CURVE.sim) return;
  // ---- shared little helpers (same block in l08.js and l12.js (same block in each file; whichever loads first defines it)
  var H = window.CURVE_L3 || (window.CURVE_L3 = (function () {
    var NS = "http://www.w3.org/2000/svg", styled = false, actx = null;
    function css() {
      if (styled) return; styled = true;
      var s = document.createElement("style"); s.id = "curve-l3-sims";
      s.textContent = [
        ".l3{--c:var(--lc,var(--l3c,#14a08c));--m:var(--stage-mute,#625C53);--p2:var(--stage-2,#EFEBE3);font-family:var(--sans,system-ui,sans-serif);color:inherit;font-size:15px;line-height:1.45;font-variant-numeric:tabular-nums}",
        ".l3 *{box-sizing:border-box}",
        ".l3-stage{position:relative;background:#fff;color:#2D2A26;border:2px solid var(--ink,#2D2A26);border-radius:14px;overflow:hidden}",
        ".l3-stage svg,.l3-stage canvas{display:block;width:100%;height:auto}",
        ".l3-ctl{display:flex;flex-wrap:wrap;gap:12px 22px;align-items:flex-end;margin:14px 0 6px}",
        ".l3-f{display:flex;flex-direction:column;gap:6px;min-width:150px;flex:1 1 170px}",
        ".l3-f>span{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--m)}",
        ".l3-f output{font-weight:700;font-size:14px;color:inherit;text-transform:none;letter-spacing:0;filter:brightness(1.6)}",
        ".l3 input[type=range]{width:100%;accent-color:var(--c);height:28px;margin:0}",
        ".l3-seg{display:flex;flex-wrap:wrap;gap:6px}",
        ".l3-seg button,.l3-btn{font:600 14px/1 var(--sans,system-ui,sans-serif);padding:9px 12px;border-radius:10px;border:1.5px solid #6b6357;background:var(--p2);color:inherit;cursor:pointer;min-height:38px}",
        ".l3-seg button:hover,.l3-btn:hover{border-color:var(--c)}",
        ".l3-seg button[aria-pressed=true]{background:var(--c);border-color:var(--c);color:var(--lc-on,#fff)}",
        ".l3-btn.go{background:var(--c);border-color:var(--c);color:var(--lc-on,#fff);font-size:15px;padding:11px 16px}",
        ".l3-btn:disabled{opacity:.45;cursor:default}",
        ".l3-seg button:focus-visible,.l3-btn:focus-visible,.l3 input:focus-visible,.l3 textarea:focus-visible,.l3 select:focus-visible,.l3-stage:focus-visible{outline:3px solid var(--c);outline-offset:2px}",
        ".l3-read{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:8px;margin:12px 0 0}",
        ".l3-num{background:var(--p2);border-radius:12px;padding:9px 12px;border-left:4px solid transparent}",
        ".l3-num b{display:block;font-size:22px;line-height:1.15;font-weight:700}",
        ".l3-num small{font-size:12px;color:var(--m)}",
        ".l3-num.hot{border-left-color:#e0402a}.l3-num.ok{border-left-color:#2fbf71}",
        ".l3-tag{position:absolute;top:8px;right:10px;font:600 11px/1 var(--sans,system-ui,sans-serif);letter-spacing:.06em;text-transform:uppercase;background:#2D2A26;color:#fff;padding:5px 8px;border-radius:6px;pointer-events:none}",
        ".l3-say{margin:12px 0 0;padding:10px 14px;border-left:5px solid var(--c);background:var(--p2);border-radius:0 10px 10px 0;font-size:15px}",
        ".l3-card{background:#fff;color:#2D2A26;border:2px solid var(--ink,#2D2A26);border-radius:12px;padding:10px 12px}",
        ".l3-card .l3-seg button,.l3-card .l3-btn{background:#fff;border-color:#2D2A26}",
        ".l3-card .l3-seg button[aria-pressed=true]{background:#2D2A26;color:#fff}",
        ".l3-card select,.l3-card textarea{color:#2D2A26;background:#fff}",
        ".l3 .big{font:700 30px var(--sans,system-ui,sans-serif);fill:#e0402a}",
        "@media (max-width:560px){.l3-f{min-width:100%}.l3-num b{font-size:19px}}"
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
      var r = el("div", { "class": "l3", role: "group", "aria-label": label }, host);
      r.style.setProperty("--l3c", (api && api.colour) || "#14a08c");
      return r;
    }
    function slider(parent, o) {
      var f = el("label", { "class": "l3-f" }, parent), sp = el("span", null, f, o.label + " ");
      var out = el("output", null, sp), inp = el("input", { type: "range", min: o.min, max: o.max, step: o.step, value: o.value }, f);
      function show() { out.textContent = o.fmt ? o.fmt(+inp.value) : inp.value; inp.setAttribute("aria-valuetext", out.textContent); }
      inp.addEventListener("input", function () { show(); o.on && o.on(+inp.value); });
      show();
      return { input: inp, get: function () { return +inp.value; }, set: function (v, quiet) { inp.value = v; show(); if (!quiet && o.on) o.on(+inp.value); } };
    }
    function seg(parent, label, opts, val, on) {
      var f = el("div", { "class": "l3-f" }, parent); el("span", { id: "" }, f, label);
      var g = el("div", { "class": "l3-seg", role: "group", "aria-label": label }, f), bs = [];
      opts.forEach(function (o) {
        var b = el("button", { type: "button", "aria-pressed": String(o[0] === val) }, g, o[1]); bs.push(b);
        b.addEventListener("click", function () { set(o[0]); on && on(o[0]); });
      });
      function set(v) { val = v; bs.forEach(function (b, i) { b.setAttribute("aria-pressed", String(opts[i][0] === v)); }); }
      return { get: function () { return val; }, set: set };
    }
    function num(parent, label) {
      var d = el("div", { "class": "l3-num" }, parent), b = el("b", null, d, "–"); el("small", null, d, label);
      return { set: function (v, cls) { b.textContent = v; d.className = "l3-num" + (cls ? " " + cls : ""); } };
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

  var C10 = "#2f6fe0", U = CURVE.U;

  // ------------------------------------------------------------------ sim: hold still
  CURVE.sim("m04_shake", function (host, api) {
    var r = H.root(host, api, "Camera shake simulator: how far the picture smears during the exposure");
    var ctl = H.el("div", { "class": "l3-ctl" }, r);
    var st = { T: 1 / 322, hold: "two", press: "quick", path: null, seed: 3 };
    var sT = H.seg(ctl, "Shutter", [["snap", "one press: about 1/300 s"], ["c1", "time picture: count 1"], ["c5", "count 5"]], "snap", function (v) { st.T = v === "snap" ? 1 / 322 : v === "c1" ? 1 : 5; shoot(); });
    var sHold = H.seg(ctl, "Holding it", [["table", "on a table"], ["two", "two hands, elbows in"], ["one", "one hand, arm out"]], "two", function (v) { st.hold = v; shoot(); });
    var sPress = H.seg(ctl, "Pressing", [["quick", "one quick press"], ["stab", "a stab"]], "quick", function (v) { st.press = v; shoot(); });
    var ctl2 = H.el("div", { "class": "l3-ctl" }, r);
    var wob = H.slider(ctl2, { label: "How much your hands wander (your guess)", min: 0, max: 4, step: 0.1, value: 1, fmt: function (v) { return H.fmt(v, 1) + "° a second"; }, on: function () { shoot(); } });
    var again = H.el("button", { type: "button", "class": "l3-btn go" }, ctl2, "Take it again");
    var stage = H.el("div", { "class": "l3-stage" }, r);
    var cv = H.el("canvas", { width: 720, height: 480, "aria-hidden": "true" }, stage), ctx = cv.getContext("2d");
    H.el("div", { "class": "l3-tag" }, stage, "simulated");
    var read = H.el("div", { "class": "l3-read" }, r);
    var nBl = H.num(read, "smear on the film"), nX = H.num(read, "against the postcard limit (0.05 mm)"), nAng = H.num(read, "how far the camera turned");
    var say = H.el("p", { "class": "l3-say", "aria-live": "polite" }, r);
    // the scene, sharp, painted once
    var W = 720, HH = 480, base = document.createElement("canvas"); base.width = W; base.height = HH;
    var im = U.scene(W, HH); U.paint(base.getContext("2d"), im, 0, 0, W, HH, 1.0);
    var PXMM = W / 36;   // pixels per mm of film
    var seed = 11; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647 - 0.5; }
    function rate() { return st.hold === "table" ? 0 : st.hold === "one" ? Math.max(wob.get(), 0.1) * 2 : wob.get(); }   // degrees a second; one hand: twice your two-hand wander (an assumption)
    function shoot() {
      // a smooth wandering path of the aim (x, y in radians) over the exposure, plus a jolt if stabbed
      var n = 64, T = st.T, w = rate() * Math.PI / 180, dir = Math.random() * 6.283, path = [[0, 0]], x = 0, y = 0, vx = Math.cos(dir), vy = Math.sin(dir);
      var turnRate = Math.min(1, T * 2);   // over longer times the wander turns about
      for (var i = 1; i <= n; i++) {
        var dt = T / n, t = i * dt;
        vx += rnd() * turnRate * 1.5; vy += rnd() * turnRate * 1.5; var m = Math.hypot(vx, vy) || 1; vx /= m; vy /= m;
        var sp = w;
        if (st.press === "stab") sp += (40 * Math.PI / 180) * Math.exp(-t / 0.02);   // a stab tips the camera: about 40° a second, dying away in a fiftieth of a second (an assumption)
        x += vx * sp * dt; y += (vy * sp + (st.press === "stab" ? 40 * Math.PI / 180 * Math.exp(-t / 0.02) * 0.8 : 0)) * dt;
        path.push([x, y]);
      }
      st.path = path; draw();
    }
    function draw() {
      var p = st.path, n = p.length;
      ctx.clearRect(0, 0, W, HH);
      var len = 0; for (var i = 1; i < n; i++) len += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
      var smearMM = 32 * len;   // film 32 mm behind the lens: an angle of a radians moves the picture 32 a mm
      var spread = 32 * Math.max.apply(null, p.map(function (q) { return Math.hypot(q[0], q[1]); }));
      var copies = Math.min(n, Math.max(1, Math.ceil(smearMM * PXMM * 1.5)));
      ctx.globalAlpha = 1;
      if (copies <= 1) ctx.drawImage(base, 0, 0);
      else {
        for (var k = 0; k < copies; k++) {
          var q = p[Math.round(k / (copies - 1) * (n - 1))];
          ctx.globalAlpha = 1 / (k + 1);
          ctx.drawImage(base, q[0] * 32 * PXMM, q[1] * 32 * PXMM);
        }
        ctx.globalAlpha = 1;
      }
      // the trail, drawn 1:1 at the scale of the picture, in the corner box
      var bx = 18, by = HH - 128, bw = 150, bh = 110;
      ctx.fillStyle = "rgba(255,255,255,.88)"; ctx.fillRect(bx, by, bw, bh);
      ctx.strokeStyle = "#2D2A26"; ctx.lineWidth = 1; ctx.strokeRect(bx, by, bw, bh);
      var zoom = 10, cx = bx + bw / 2, cy = by + bh / 2 + 6;
      ctx.strokeStyle = "rgba(0,0,0,.2)"; ctx.beginPath(); ctx.arc(cx, cy, 0.05 / 2 * PXMM * zoom, 0, 7); ctx.stroke();   // the 0.05 mm circle
      ctx.strokeStyle = "#d6301f"; ctx.lineWidth = 2.5; ctx.beginPath();
      p.forEach(function (q, i) { var X = cx + q[0] * 32 * PXMM * zoom, Y = cy + q[1] * 32 * PXMM * zoom; if (i) ctx.lineTo(X, Y); else ctx.moveTo(X, Y); }); ctx.stroke();
      ctx.save(); ctx.beginPath(); ctx.rect(bx, by, bw, bh); ctx.restore();
      U.label(ctx, "the aim's path, 10× larger", bx + 6, by + 14, { size: 11, color: "#2D2A26" });
      U.label(ctx, "grey ring: 0.05 mm", bx + 6, by + bh - 6, { size: 10, color: "#625C53", weight: 400 });
      var x = smearMM / 0.05;
      nBl.set(smearMM < 0.001 ? "under 0.001 mm" : H.fmt(smearMM, smearMM < 0.1 ? 3 : 2) + " mm", x > 1 ? "hot" : "ok");
      nX.set(x < 0.1 ? "far under" : H.fmt(x, x < 10 ? 1 : 0) + "×", x > 1 ? "hot" : "ok");
      nAng.set(H.fmt(len * 180 / Math.PI, 3) + "°");
      var tw = st.T < 0.01 ? "about a three-hundredth of a second" : st.T === 1 ? "about a second (count 1)" : "about five seconds (count 5)";
      var s = "Open for " + tw + ". The camera turned " + H.fmt(len * 180 / Math.PI, 3) + "°, so the picture slid " + H.fmt(smearMM, 3) + " mm across the film. ";
      if (x <= 1) s += st.T < 0.01 ? "Sharp: a three-hundredth of a second is so short that ordinary hands hardly move in it." : "Sharp: nothing moved the camera.";
      else if (st.T < 0.01) s += "Smeared: the stab swung the camera while the shutter was open. Move the rocker, not the camera.";
      else s += "Smeared " + H.fmt(x, 0) + " times past what a postcard forgives. Nobody holds still for a whole count: stand the camera on something.";
      say.textContent = s;
    }
    again.addEventListener("click", shoot);
    shoot();
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ sim: where the sight crosses the lens's line
  CURVE.sim("m04_sight", function (host, api) {
    var r = H.root(host, api, "Sight line simulator: the sight sits above the lens and is tilted to cross the lens's line at a distance");
    var ctl = H.el("div", { "class": "l3-ctl" }, r);
    var st = { d: 1.4, drop: 0.375 };
    var sd = H.slider(ctl, { label: "How far away your friend stands", min: 0.7, max: 10, step: 0.05, value: 1.4, fmt: function (v) { return H.fmt(v, 1) + " m"; }, on: function (v) { st.d = v; draw(); } });
    var sp = H.slider(ctl, { label: "SIGHT_DROP: how much lower the front point is", min: 0, max: 1.0, step: 0.005, value: 0.375, fmt: function (v) { return H.fmt(v, 3) + " mm" + (Math.abs(v - 0.375) < 0.003 ? " (as drawn)" : ""); }, on: function (v) { st.drop = v; draw(); } });
    var ctl2 = H.el("div", { "class": "l3-ctl" }, r);
    H.seg(ctl2, "Jump to", [[0.7, "0.7 m"], [1, "1 m"], [1.4, "1.4 m"], [2, "2 m"], [2.8, "2.8 m"], [4, "4 m"], [10, "10 m"]], 1.4, function (v) { sd.set(v); });
    var bR = H.el("button", { type: "button", "class": "l3-btn" }, H.el("div", { "class": "l3-f" }, ctl2), "Back to the real sight");
    bR.addEventListener("click", function () { sp.set(0.375); });
    var stage = H.el("div", { "class": "l3-stage" }, r);
    H.el("div", { "class": "l3-tag" }, stage, "drawn from the model's numbers");
    var W = 720, HH = 300, svg = H.sv("svg", { viewBox: "0 0 " + W + " " + HH, role: "img", "aria-label": "Left: side view of the sight line and the lens's line, heights stretched. Right: the picture at that distance, with where your aim lands." }, stage);
    var read = H.el("div", { "class": "l3-read" }, r);
    var nC = H.num(read, "the lines cross at"), nU = H.num(read, "your aim lands above the middle by"), nP = H.num(read, "of the picture's height"), nH = H.num(read, "picture height there");
    var say = H.el("p", { "class": "l3-say", "aria-live": "polite" }, r);
    function up(d) { return 30 - d * 1000 * st.drop / 35; }   // mm the aimed point sits above the lens's line, at d metres
    function draw() {
      svg.innerHTML = "";
      var g = H.sv("g", null, svg), X0 = 80, X1 = 400, Y = 170, dmax = 10;
      function xx(d) { return X0 + d / dmax * (X1 - X0); }
      function yy(mm) { return Y - mm * 1.3; }                          // heights stretched hugely
      // distance ticks
      [1, 2.8, 4, 6, 8, 10].forEach(function (d) { H.sv("line", { x1: xx(d), y1: Y + 70, x2: xx(d), y2: Y + 78, stroke: "#625C53" }, g); txt(g, xx(d), Y + 94, d + " m", 11, "#625C53", "middle"); });
      H.sv("line", { x1: X0, y1: Y + 74, x2: X1, y2: Y + 74, stroke: "#625C53" }, g);
      // camera
      H.sv("rect", { x: X0 - 50, y: Y - 30, width: 46, height: 52, rx: 6, fill: "#3b3936" }, g);
      H.sv("rect", { x: X0 - 8, y: Y - 22, width: 6, height: 40, fill: "#D9601A" }, g);
      H.sv("circle", { cx: X0 - 2, cy: Y, r: 5, fill: "#9fd3e6", stroke: "#2D2A26" }, g);
      // lens line
      H.sv("line", { x1: X0, y1: Y, x2: X1 + 10, y2: Y, stroke: C10, "stroke-width": 3 }, g); txt(g, X1 - 90, Y + 18, "the lens's line", 12, C10);
      // sight line
      var pts = []; for (var d = 0; d <= dmax + 0.001; d += 0.05) pts.push(xx(d).toFixed(1) + " " + yy(up(d)).toFixed(1));
      H.sv("path", { d: "M" + pts.join(" L"), stroke: "#d6301f", "stroke-width": 3, fill: "none" }, g); txt(g, X0 + 4, yy(30) - 12, "the sight line", 12, "#d6301f");
      H.sv("circle", { cx: X0, cy: yy(30), r: 4, fill: "#d6301f" }, g); txt(g, X0 - 70, yy(30) - 30, "pad: 30 mm up", 11, "#2D2A26");
      var cross = st.drop > 0 ? 30 * 35 / st.drop / 1000 : Infinity;
      if (cross <= dmax) { H.sv("circle", { cx: xx(cross), cy: Y, r: 7, fill: "none", stroke: "#2D2A26", "stroke-width": 2 }, g); txt(g, xx(cross), Y - 14 + (cross < 2 ? 40 : 0), "cross: " + H.fmt(cross, 1) + " m", 12, "#2D2A26", "middle"); }
      // the friend
      var fx = xx(st.d);
      H.sv("line", { x1: fx, y1: yy(up(st.d)), x2: fx, y2: Y, stroke: "#2D2A26", "stroke-dasharray": "3 3" }, g);
      H.sv("circle", { cx: fx, cy: yy(up(st.d)), r: 6, fill: "#d6301f", stroke: "#fff", "stroke-width": 2 }, g); txt(g, fx + 8, yy(up(st.d)) - 8, "you aim here", 11, "#d6301f");
      txt(g, X0 - 50, 24, "Side view: heights stretched about 40 times", 12, "#625C53");
      // the picture at that distance
      var px = 480, pw = 216, ph = 144, py = 70;
      var hgt = 0.75 * st.d * 1000, wid = 36 / 32 * st.d * 1000, u = up(st.d), pct = u / hgt * 100;
      txt(g, px, py - 14, "The picture at " + H.fmt(st.d, 1) + " m", 13, "#2D2A26");
      H.sv("rect", { x: px, y: py, width: pw, height: ph, fill: "#eef3f8", stroke: "#2D2A26", "stroke-width": 2 }, g);
      var ay = py + ph / 2 - u / hgt * ph;
      var face = Math.max(5, 230 / hgt * ph / 2);   // a face about 23 cm tall
      if (ay > py - face && ay < py + ph + face) {
        var cl = H.sv("clipPath", { id: "m04c" }, H.sv("defs", null, g)); H.sv("rect", { x: px, y: py, width: pw, height: ph }, cl);
        var gg = H.sv("g", { "clip-path": "url(#m04c)" }, g);
        H.sv("circle", { cx: px + pw / 2, cy: ay, r: face, fill: "#e8b892", stroke: "#2D2A26" }, gg);
        H.sv("rect", { x: px + pw / 2 - face * 1.6, y: ay + face * 1.05, width: face * 3.2, height: face * 6, rx: face, fill: "#2f6fe0", opacity: 0.8 }, gg);
      }
      H.sv("line", { x1: px + pw / 2 - 10, y1: py + ph / 2, x2: px + pw / 2 + 10, y2: py + ph / 2, stroke: C10, "stroke-width": 2 }, g);
      H.sv("line", { x1: px + pw / 2, y1: py + ph / 2 - 10, x2: px + pw / 2, y2: py + ph / 2 + 10, stroke: C10, "stroke-width": 2 }, g);
      H.sv("circle", { cx: px + pw / 2, cy: Math.max(py - 6, Math.min(py + ph + 6, ay)), r: 5, fill: "#d6301f" }, g);
      txt(g, px, py + ph + 20, "blue cross: the middle of the picture", 11, "#625C53");
      txt(g, px, py + ph + 36, "red dot: the nose you aimed at", 11, "#625C53");
      nC.set(isFinite(cross) ? H.fmt(cross, 1) + " m" : "never");
      nU.set(H.fmt(u, 0) + " mm");
      nP.set(H.fmt(Math.abs(pct), 1) + " %" + (pct < 0 ? " low" : ""), Math.abs(pct) > 3 ? "hot" : "ok");
      nH.set(H.fmt(hgt / 1000, 2) + " m");
      say.textContent = "At " + H.fmt(st.d, 1) + " m the picture is " + H.fmt(hgt / 1000, 2) + " m tall (0.75 × the distance). The sight line is " + H.fmt(Math.abs(u), 0) + " mm " + (u >= 0 ? "above" : "below") + " the lens's line there, so what you aimed at lands " + H.fmt(Math.abs(pct), 1) + " % of the picture " + (u >= 0 ? "above" : "below") + " the middle. " +
        (st.drop === 0 ? "With the point not lowered at all, the two lines never meet: always 30 mm apart, which matters most up close." : isFinite(cross) ? "The lines cross at " + H.fmt(cross, 1) + " m: 30 ÷ " + H.fmt(st.drop, 3) + " = " + H.fmt(30 / st.drop, 0) + " steps of 35 mm." : "");
    }
    function txt(p, x, y, s, size, fill, anchor) { var t = H.sv("text", { x: x, y: y, fill: fill || "#2D2A26", "text-anchor": anchor || "start", style: "font:600 " + (size || 12) + "px var(--sans,system-ui,sans-serif)" }, p); t.textContent = s; return t; }
    function person(p, x, foot, k) {
      var h = 150 * k;
      H.sv("circle", { cx: x, cy: foot - h + 10 * k * 1.4, r: 12 * k * 1.4, fill: "#e8b892", stroke: "#2D2A26" }, p);
      H.sv("rect", { x: x - 12 * k * 1.4, y: foot - h + 26 * k * 1.4, width: 24 * k * 1.4, height: h - 30 * k * 1.4, rx: 8 * k, fill: "#2f6fe0" }, p);
    }
    draw();
    return { destroy: function () { host.innerHTML = ""; } };
  });

  // ------------------------------------------------------------------ figures
  function S(w, h, label, body) { return '<svg viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + label + '" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;font-family:var(--sans,system-ui,sans-serif)">' + body + "</svg>"; }
  function T(x, y, s, o) { o = o || {}; return '<text x="' + x + '" y="' + y + '" font-size="' + (o.size || 15) + '" font-weight="' + (o.w || 600) + '" fill="' + (o.fill || "#2D2A26") + '"' + (o.anchor ? ' text-anchor="' + o.anchor + '"' : "") + ">" + s + "</text>"; }

  CURVE.fig("fig_m04_tries", function () {
    var b = "", items = [
      ["1", "two rails beside the lens", "pointed true by the sums; looked wrong to the eye", "x"],
      ["2", "rails over the lens", "better, still not where the eye wanted it", "x"],
      ["3", "the rocker's end alone", "too little to line up", "x"],
      ["4", "groove, edges, point", "the eye and the sums agree", "ok"]];
    items.forEach(function (it, i) {
      var x = 18 + i * 176;
      b += '<rect x="' + x + '" y="20" width="160" height="220" rx="14" fill="' + (it[3] === "ok" ? "#e3ecfd" : "#f3efe8") + '" stroke="' + (it[3] === "ok" ? C10 : "#cfc8bb") + '" stroke-width="3"/>';
      b += T(x + 14, 52, "try " + it[0], { size: 18, fill: it[3] === "ok" ? C10 : "#625C53" });
      // a tiny top view of the camera with the sight marks
      b += '<rect x="' + (x + 20) + '" y="70" width="120" height="44" rx="6" fill="#3b3936"/><circle cx="' + (x + 80) + '" cy="118" r="8" fill="#9fd3e6" stroke="#2D2A26"/>';
      if (i === 0) b += '<rect x="' + (x + 60) + '" y="104" width="6" height="22" fill="#f2c230"/><rect x="' + (x + 94) + '" y="104" width="6" height="22" fill="#f2c230"/>';
      if (i === 1) b += '<rect x="' + (x + 77) + '" y="72" width="6" height="40" fill="#f2c230"/>';
      if (i === 2) b += '<rect x="' + (x + 100) + '" y="76" width="22" height="10" rx="3" fill="#8145C0"/>';
      if (i === 3) b += '<line x1="' + (x + 80) + '" y1="72" x2="' + (x + 80) + '" y2="112" stroke="#f2c230" stroke-width="3"/><line x1="' + (x + 52) + '" y1="72" x2="' + (x + 40) + '" y2="112" stroke="#f2c230" stroke-width="2"/><line x1="' + (x + 108) + '" y1="72" x2="' + (x + 120) + '" y2="112" stroke="#f2c230" stroke-width="2"/><path d="M' + (x + 75) + " 112 L" + (x + 80) + " 104 L" + (x + 85) + ' 112Z" fill="#D9601A"/>';
      b += T(x + 14, 156, it[1], { size: 13 });
      var words = it[2].split(" "), line = "", ly = 178;
      words.forEach(function (w) { if ((line + " " + w).length > 22) { b += T(x + 14, ly, line, { size: 12, w: 400, fill: "#625C53" }); ly += 16; line = w; } else line = line ? line + " " + w : w; });
      b += T(x + 14, ly, line, { size: 12, w: 400, fill: "#625C53" });
      b += it[3] === "ok" ? '<circle cx="' + (x + 136) + '" cy="44" r="13" fill="' + C10 + '"/><path d="M' + (x + 130) + " 44 l4 5 l8 -10" + '" stroke="#fff" stroke-width="3" fill="none"/>' : '<g stroke="#c0392b" stroke-width="3"><line x1="' + (x + 128) + '" y1="36" x2="' + (x + 144) + '" y2="52"/><line x1="' + (x + 144) + '" y1="36" x2="' + (x + 128) + '" y2="52"/></g>';
    });
    return S(720, 260, "The four sights tried on the camera, seen from above: two rails beside the lens, rails over the lens, the rocker's end alone, and the one kept: a middle groove, two outer lines and a point.", b);
  });

  CURVE.fig("fig_m04_rocker", function () {
    var b = "";
    function rocker(x, tilt, label, sub) {
      var s = "";
      s += '<rect x="' + (x - 90) + '" y="150" width="180" height="60" rx="10" fill="#3b3936"/>';
      s += '<g transform="rotate(' + tilt + " " + x + ' 140)"><path d="M' + (x - 80) + " 128 L" + x + " 142 L" + (x + 80) + " 128 L" + (x + 80) + " 140 L" + x + " 152 L" + (x - 80) + ' 140Z" fill="#8145C0"/></g>';
      s += '<circle cx="' + x + '" cy="146" r="5" fill="#fff"/>';
      s += T(x, 248, label, { anchor: "middle", size: 15 }) + T(x, 268, sub, { anchor: "middle", size: 13, w: 400, fill: "#625C53" });
      return s;
    }
    b += rocker(170, -7, "before the picture", "the right side is up: press it");
    b += '<path d="M' + 240 + " 90 q0 -26 0 -1" + '"/><g transform="translate(232,74)"><path d="M0 0 l0 34 l-8 -10 m8 10 l8 -10" stroke="#2f6fe0" stroke-width="4" fill="none"/></g>' + T(250, 76, "one quick press, about 2 N", { size: 13 });
    b += rocker(530, 7, "after the click", "now the left side is up");
    b += '<path d="M330 180 L380 180" stroke="#2D2A26" stroke-width="3" marker-end="url(#m04r)"/><defs><marker id="m04r" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#2D2A26"/></marker></defs>';
    b += T(360, 30, "The part tells you what to do next", { anchor: "middle", size: 17 });
    return S(720, 290, "The rocker is a shallow V on top of the camera. One side is always raised; press it and, after the click, the other side is raised.", b);
  });

  CURVE.fig("fig_m04_eyeline", function () {
    var b = "";
    b += '<line x1="60" y1="200" x2="690" y2="200" stroke="' + C10 + '" stroke-width="4"/>' + T(560, 222, "the lens's line", { fill: C10, size: 14 });
    b += '<line x1="60" y1="80" x2="660" y2="200" stroke="#d6301f" stroke-width="4"/>' + T(300, 112, "the sight line", { fill: "#d6301f", size: 14 });
    b += '<rect x="20" y="70" width="44" height="150" rx="8" fill="#3b3936"/><circle cx="60" cy="200" r="7" fill="#9fd3e6" stroke="#2D2A26"/>';
    b += '<line x1="80" y1="80" x2="80" y2="200" stroke="#2D2A26" stroke-dasharray="4 4"/>' + T(88, 146, "30 mm", { size: 14 });
    b += '<path d="M60 64 L150 64" stroke="#2D2A26" stroke-width="2"/>' + T(70, 56, "35 mm forward: 0.375 mm lower (SIGHT_DROP)", { size: 13, w: 400 });
    b += '<circle cx="660" cy="200" r="10" fill="none" stroke="#2D2A26" stroke-width="3"/>' + T(660, 250, "they cross about 2.8 m away", { anchor: "middle", size: 14 });
    b += T(360, 290, "30 ÷ 0.375 = 80 steps;  80 × 35 mm = 2800 mm = 2.8 m", { anchor: "middle", size: 15 });
    b += T(20, 24, "Heights stretched: the real slope is far too gentle to see", { size: 12, w: 400, fill: "#625C53" });
    return S(720, 310, "The sight line starts 30 mm above the lens's line and falls 0.375 mm every 35 mm, so the two lines cross about 2.8 metres in front of the camera.", b);
  });

})();
