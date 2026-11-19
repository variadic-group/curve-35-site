/* CURVE 35, lesson 8 "Taking a good picture": aim with the sight, hold still, frame the shot.
   Numbers: course/FACTS.md (lens 32 mm, shutter about 1/322 s, picture 36 x 24 mm), build/sightcheck.json
   (pad 30 mm above the lens's line, point 35 mm forward and 0.37 mm lower, crossing about 2.8 m), build/focus.json (blur by distance and place). */
(function () {
  "use strict";
  if (!window.CURVE || !CURVE.sim) return;
  // ---- shared little helpers for lessons 9 to 12 (same block in each file; whichever loads first defines it)
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
  CURVE.sim("l08_shake", function (host, api) {
    var r = H.root(host, api, "Camera shake simulator: how far the picture smears during the exposure");
    var ctl = H.el("div", { "class": "l3-ctl" }, r);
    var st = { T: 1 / 322, hold: "two", press: "quick", path: null, seed: 3 };
    var sT = H.seg(ctl, "Shutter", [["snap", "one press: 1/322 s"], ["c1", "time picture: count 1"], ["c5", "count 5"]], "snap", function (v) { st.T = v === "snap" ? 1 / 322 : v === "c1" ? 1 : 5; shoot(); });
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
  CURVE.sim("l08_sight", function (host, api) {
    var r = H.root(host, api, "Sight line simulator: the sight sits above the lens and is tilted to cross the lens's line at a distance");
    var ctl = H.el("div", { "class": "l3-ctl" }, r);
    var st = { d: 1.4, drop: 0.37 };
    var sd = H.slider(ctl, { label: "How far away your friend stands", min: 0.7, max: 10, step: 0.05, value: 1.4, fmt: function (v) { return H.fmt(v, 1) + " m"; }, on: function (v) { st.d = v; draw(); } });
    var sp = H.slider(ctl, { label: "How much lower the front point is", min: 0, max: 1.0, step: 0.01, value: 0.37, fmt: function (v) { return H.fmt(v, 2) + " mm" + (Math.abs(v - 0.37) < 0.005 ? " (the real one)" : ""); }, on: function (v) { st.drop = v; draw(); } });
    var ctl2 = H.el("div", { "class": "l3-ctl" }, r);
    H.seg(ctl2, "Jump to", [[0.7, "0.7 m"], [1, "1 m"], [1.4, "1.4 m"], [2, "2 m"], [2.8, "2.8 m"], [4, "4 m"], [10, "10 m"]], 1.4, function (v) { sd.set(v); });
    var bR = H.el("button", { type: "button", "class": "l3-btn" }, H.el("div", { "class": "l3-f" }, ctl2), "Back to the real sight");
    bR.addEventListener("click", function () { sp.set(0.37); });
    var stage = H.el("div", { "class": "l3-stage" }, r);
    H.el("div", { "class": "l3-tag" }, stage, "to scale");
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
        var cl = H.sv("clipPath", { id: "l10c" }, H.sv("defs", null, g)); H.sv("rect", { x: px, y: py, width: pw, height: ph }, cl);
        var gg = H.sv("g", { "clip-path": "url(#l10c)" }, g);
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
        (st.drop === 0 ? "With the point not lowered at all, the two lines never meet: always 30 mm apart, which matters most up close." : isFinite(cross) ? "The lines cross at " + H.fmt(cross, 1) + " m: 30 ÷ " + H.fmt(st.drop, 2) + " = " + H.fmt(30 / st.drop, 0) + " steps of 35 mm." : "");
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

  var C11 = "#e8a400";
  // blur in mm: [dot][zone] by distance column far, 4 m, 2 m, 1.5 m, 1 m   (focus.json as_drawn)
  var BL = {
    small: { m: [0.025, 0.014, 0.018, 0.027, 0.049], h: [0.044, 0.046, 0.052, 0.058, 0.073], e: [0.132, 0.14, 0.149, 0.155, 0.168], c: [0.139, 0.145, 0.152, 0.157, 0.167] },
    middle: { m: [0.034, 0.02, 0.028, 0.042, 0.073], h: [0.077, 0.076, 0.081, 0.088, 0.107], e: [0.189, 0.201, 0.213, 0.222, 0.24], c: [0.193, 0.201, 0.211, 0.218, 0.234] },
    large: { m: [0.04, 0.023, 0.033, 0.049, 0.086], h: [0.097, 0.097, 0.103, 0.111, 0.133], e: [0.225, 0.238, 0.251, 0.261, 0.281], c: [0.234, 0.244, 0.255, 0.263, 0.28] }
  };
  var INV = [0, 0.25, 0.5, 2 / 3, 1];          // 1 / distance of each column
  var ZR = [0, 0.5, 1.0, 1.2], ZK = ["m", "h", "e", "c"];   // zone radius, in 18 mm (half the picture's width)
  function byDist(arr, d) {   // interpolate in 1/d; nearer than 1 m, carry on the last slope
    var u = d >= 1e4 ? 0 : 1 / d;
    for (var i = 1; i < INV.length; i++) if (u <= INV[i]) { var t = (u - INV[i - 1]) / (INV[i] - INV[i - 1]); return H.lerp(arr[i - 1], arr[i], t); }
    return arr[4] + (u - 1) * (arr[4] - arr[3]) / (1 - 2 / 3);
  }
  function blurAt(dot, r, d) {   // r: distance from the middle of the picture in units of 18 mm
    r = Math.min(r, 1.2);
    for (var i = 1; i < ZR.length; i++) if (r <= ZR[i]) { var t = (r - ZR[i - 1]) / (ZR[i] - ZR[i - 1]); return H.lerp(byDist(BL[dot][ZK[i - 1]], d), byDist(BL[dot][ZK[i]], d), t); }
    return byDist(BL[dot].c, d);
  }
  var DOTS = { small: { mm: 1.96, say: "small" }, middle: { mm: 2.88, say: "middle" }, large: { mm: 3.34, say: "large" } };
  // steps of light against what ISO 400 film needs, at the large dot (exposure.json coverage, ISO 400 = ISO 100 + 2)
  var SKY = { sun: 2.0, hazy: 1.0, cloud: 0.0 };
  function stopsFor(dot, sky) { return SKY[sky] - 2 * Math.log(DOTS.large.mm / DOTS[dot].mm) / Math.LN2; }

  // ------------------------------------------------------------------ sim: frame a picture
  CURVE.sim("l08_frame", function (host, api) {
    var r = H.root(host, api, "Framing game: choose where to stand, the dot, the light and where your friend goes in the picture; see a simulated result");
    var st = { d: 4, dot: "middle", sky: "hazy", light: "behind", tx: 0, ty: 0 };
    var ctl = H.el("div", { "class": "l3-ctl" }, r);
    var sD = H.slider(ctl, { label: "Where you stand", min: 0.5, max: 8, step: 0.05, value: 4, fmt: function (v) { return H.fmt(v, 1) + " m from your friend"; }, on: function (v) { st.d = v; later(); } });
    var sDot = H.seg(ctl, "Dot", [["small", "small"], ["middle", "middle"], ["large", "large"]], "middle", function (v) { st.dot = v; later(); });
    var ctl2 = H.el("div", { "class": "l3-ctl" }, r);
    H.seg(ctl2, "The sky", [["sun", "full sun"], ["hazy", "hazy sun"], ["cloud", "bright cloud"]], "hazy", function (v) { st.sky = v; later(); });
    H.seg(ctl2, "The sun is", [["behind", "behind you"], ["side", "to one side"], ["front", "behind them"]], "behind", function (v) { st.light = v; later(); });
    var ctl3 = H.el("div", { "class": "l3-ctl" }, r);
    H.seg(ctl3, "Put your friend's face", [["mid", "in the middle"], ["third", "a third across"], ["end", "at the end"]], "mid", function (v) { st.tx = v === "mid" ? 0 : v === "third" ? -6 : -14; st.ty = 0; later(); });
    var hint = H.el("div", { "class": "l3-f" }, ctl3); H.el("span", null, hint, "Or"); H.el("div", { style: "font-size:14px" }, hint, "drag your friend around the picture (arrow keys work too)");
    var stage = H.el("div", { "class": "l3-stage", tabindex: "0", "aria-label": "The simulated picture. Arrow keys move your friend in the frame." }, r);
    stage.style.cursor = "grab"; stage.style.touchAction = "none";
    var W = 720, HH = 480, PXMM = 20, F = 32;
    var cv = H.el("canvas", { width: W, height: HH, "aria-hidden": "true" }, stage), ctx = cv.getContext("2d");
    H.el("div", { "class": "l3-tag" }, stage, "simulated: blur and light only");
    var read = H.el("div", { "class": "l3-read" }, r);
    var nH = H.num(read, "picture height at your friend"), nFit = H.num(read, "your friend"), nS = H.num(read, "your friend's face, on a postcard"), nE = H.num(read, "light on the film");
    var say = H.el("div", { "class": "l3-say", "aria-live": "polite" }, r);
    var hasFilter = "filter" in ctx;
    function mk() { var c = document.createElement("canvas"); c.width = W; c.height = HH; return c; }
    var Lfar = mk(), Lmid = mk(), Lme = mk(), tmp = mk(), acc = mk();
    // camera aim: the friend's face (1.58 m up) lands at (tx, ty) mm on the film; the camera is held 1.3 m up
    function aim() { var phi = Math.atan((1.58 - 1.3) / st.d) - st.ty / F, psi = -st.tx / F; return { phi: phi, psi: psi }; }
    function P(X, Y, Z, a) { var hz = Math.sqrt(X * X + Z * Z); return [W / 2 + PXMM * F * (Math.atan2(X, Z) - a.psi), HH / 2 - PXMM * F * (Math.atan((Y - 1.3) / hz) - a.phi)]; }
    function drawFar(g, a) {
      g.clearRect(0, 0, W, HH);
      var hor = P(0, 1.3, 1e5, a)[1];
      var sky = g.createLinearGradient(0, hor - 400, 0, hor);
      var top = st.sky === "cloud" ? "#c9cfd6" : st.sky === "hazy" ? "#a9c6e0" : "#6fa8e0", bot = st.sky === "cloud" ? "#e4e6e8" : "#dbe9f3";
      sky.addColorStop(0, top); sky.addColorStop(1, bot); g.fillStyle = sky; g.fillRect(0, 0, W, Math.max(0, hor + 2));
      if (st.sky === "cloud" || st.sky === "hazy") { g.fillStyle = "rgba(255,255,255,.75)"; [[120, 70, 50], [180, 60, 60], [520, 90, 70], [600, 80, 46]].forEach(function (c) { g.beginPath(); g.ellipse(c[0], hor - 260 + c[1], c[2] * 1.6, c[2] * 0.6, 0, 0, 7); g.fill(); }); }
      if (st.light === "front" && st.sky !== "cloud") { var sp = P(1.5, 1.3 + 0.25 * 1e3, 1e3, a); g.fillStyle = "#fff8d8"; g.beginPath(); g.arc(sp[0], sp[1], 26, 0, 7); g.fill(); }
      // far hills
      g.fillStyle = "#8fae7a"; g.beginPath(); g.moveTo(0, hor);
      for (var x = 0; x <= W; x += 20) g.lineTo(x, hor - 18 - 14 * Math.sin(x / 90 + 1) - 8 * Math.sin(x / 37));
      g.lineTo(W, HH); g.lineTo(0, HH); g.fill();
      g.fillStyle = "#6f9a52"; g.fillRect(0, hor, W, HH);
      // a path running away
      var p1 = P(-0.5, 0, 1.2, a), p2 = P(0.5, 0, 1.2, a), p3 = P(0.15, 0, 60, a), p4 = P(-0.15, 0, 60, a);
      g.fillStyle = "#d8c9a8"; g.beginPath(); g.moveTo(p1[0], p1[1]); g.lineTo(p2[0], p2[1]); g.lineTo(p3[0], p3[1]); g.lineTo(p4[0], p4[1]); g.fill();
    }
    function drawMid(g, a) {
      g.clearRect(0, 0, W, HH);
      // a house 14 m away, a tree 20 m away on the right, a bush 9 m on the left
      var b0 = P(-6, 0, 14, a), b1 = P(-1, 4, 14, a), rf = P(-3.5, 6.2, 14, a);
      g.fillStyle = "#b9b1a5"; g.fillRect(b0[0], b1[1], b1[0] - b0[0], b0[1] - b1[1]);
      g.fillStyle = "#b8452c"; g.beginPath(); g.moveTo(b0[0] - 8, b1[1]); g.lineTo(rf[0], rf[1]); g.lineTo(b1[0] + 8, b1[1]); g.fill();
      var dr = P(-3.9, 2, 14, a), dr2 = P(-3.1, 0, 14, a); g.fillStyle = "#1a1714"; g.fillRect(dr[0], dr[1], dr2[0] - dr[0], dr2[1] - dr[1]);
      [-5.2, -2.2].forEach(function (wx) { var w0 = P(wx, 3.1, 14, a), w1 = P(wx + 0.9, 2.3, 14, a); g.fillStyle = "#e9eef0"; g.fillRect(w0[0], w0[1], w1[0] - w0[0], w1[1] - w0[1]); g.strokeStyle = "#4b4740"; g.lineWidth = 2; g.strokeRect(w0[0], w0[1], w1[0] - w0[0], w1[1] - w0[1]); });
      var t0 = P(5, 0, 20, a), t1 = P(5, 3, 20, a), tc = P(5, 5.5, 20, a), tr = P(5 + 2.6, 5.5, 20, a)[0] - tc[0];
      g.fillStyle = "#5b3b22"; g.fillRect(t0[0] - tr * 0.12, t1[1], tr * 0.24, t0[1] - t1[1]);
      g.fillStyle = "#2c5a30"; g.beginPath(); g.arc(tc[0], tc[1], tr, 0, 7); g.fill(); g.beginPath(); g.arc(tc[0] - tr * 0.6, tc[1] + tr * 0.5, tr * 0.7, 0, 7); g.fill(); g.beginPath(); g.arc(tc[0] + tr * 0.6, tc[1] + tr * 0.5, tr * 0.7, 0, 7); g.fill();
      var bc = P(-7, 0.7, 9, a), br = P(-7 + 1.2, 0.7, 9, a)[0] - bc[0];
      g.fillStyle = "#3d6d3a"; g.beginPath(); g.ellipse(bc[0], bc[1], br * 1.3, br * 0.8, 0, 0, 7); g.fill();
    }
    function drawMe(g, a) {   // your friend: 1.7 m tall, in a yellow top, standing at d
      g.clearRect(0, 0, W, HH);
      var d = st.d, k = PXMM * F / d;   // px per metre at d
      var c = P(0, 0.85, d, a), x = c[0], foot = P(0, 0, d, a)[1];
      function Y(m) { return foot - m * k; }
      var back = st.light === "front", side = st.light === "side";
      var skin = "#e3b48f", top = "#f2c94c", legs = "#2c3e66", hair = "#3a2a1e";
      g.fillStyle = legs; g.fillRect(x - 0.16 * k, Y(0.85), 0.13 * k, 0.85 * k); g.fillRect(x + 0.03 * k, Y(0.85), 0.13 * k, 0.85 * k);
      g.fillStyle = top; roundRect(g, x - 0.22 * k, Y(1.45), 0.44 * k, 0.62 * k, 0.08 * k); g.fill();
      g.fillRect(x - 0.3 * k, Y(1.42), 0.09 * k, 0.55 * k); g.fillRect(x + 0.21 * k, Y(1.42), 0.09 * k, 0.55 * k);
      g.fillStyle = skin; g.beginPath(); g.ellipse(x, Y(1.58), 0.1 * k, 0.125 * k, 0, 0, 7); g.fill();
      g.fillStyle = hair; g.beginPath(); g.ellipse(x, Y(1.66), 0.105 * k, 0.06 * k, 0, Math.PI, 0); g.fill();
      // eyes and a smile: the detail that shows sharpness
      g.fillStyle = "#1d1a17"; g.beginPath(); g.arc(x - 0.035 * k, Y(1.59), 0.012 * k, 0, 7); g.arc(x + 0.035 * k, Y(1.59), 0.012 * k, 0, 7); g.fill();
      g.strokeStyle = "#7a3b2e"; g.lineWidth = Math.max(1, 0.008 * k); g.beginPath(); g.arc(x, Y(1.55), 0.035 * k, 0.2, Math.PI - 0.2); g.stroke();
      // the light on them
      g.save(); g.globalCompositeOperation = "source-atop";
      if (back) { g.fillStyle = "rgba(10,12,25,0.72)"; g.fillRect(0, 0, W, HH); g.strokeStyle = "rgba(255,245,200,0.95)"; g.lineWidth = Math.max(2, 0.02 * k); g.beginPath(); g.ellipse(x, Y(1.6), 0.105 * k, 0.13 * k, 0, Math.PI * 1.05, Math.PI * 1.95); g.stroke(); }
      if (side) { var gr = g.createLinearGradient(x - 0.25 * k, 0, x + 0.25 * k, 0); gr.addColorStop(0, "rgba(255,240,210,0.15)"); gr.addColorStop(0.5, "rgba(0,0,0,0)"); gr.addColorStop(0.55, "rgba(10,12,25,0.45)"); gr.addColorStop(1, "rgba(10,12,25,0.55)"); g.fillStyle = gr; g.fillRect(0, 0, W, HH); }
      g.restore();
      // shadow on the ground
      g.fillStyle = "rgba(0,0,0,.22)"; g.beginPath(); g.ellipse(x + (side ? 0.5 * k : 0), foot + (back ? 0.15 * k : 0), (side ? 0.6 : 0.3) * k, 0.06 * k, 0, 0, 7); g.fill();
      return { x: x, face: Y(1.58), head: Y(1.72), foot: foot, k: k };
    }
    function roundRect(g, x, y, w, h, rr) { g.beginPath(); g.moveTo(x + rr, y); g.arcTo(x + w, y, x + w, y + h, rr); g.arcTo(x + w, y + h, x, y + h, rr); g.arcTo(x, y + h, x, y, rr); g.arcTo(x, y, x + w, y, rr); g.closePath(); }
    // blur a layer the way this lens does: sharper in the middle, softer toward the ends
    function lensBlur(src, d, out) {
      var o = out.getContext("2d");
      var levels = [0, 0.35, 0.6, 0.8, 1.0, 1.2], R = 18 * PXMM;
      levels.forEach(function (rr, i) {
        var dia = blurAt(st.dot, rr, d) * PXMM, t = tmp.getContext("2d");
        t.save(); t.clearRect(0, 0, W, HH); t.filter = hasFilter && dia > 0.6 ? "blur(" + (dia / 3).toFixed(2) + "px)" : "none"; t.drawImage(src, 0, 0); t.restore();
        if (i > 0) {
          t.save(); t.globalCompositeOperation = "destination-in";
          var gr = t.createRadialGradient(W / 2, HH / 2, 0, W / 2, HH / 2, R * 1.2);
          gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(Math.max(0, levels[i - 1] / 1.2), "rgba(0,0,0,0)"); gr.addColorStop(rr / 1.2, "rgba(0,0,0,1)"); gr.addColorStop(1, "rgba(0,0,0,1)");
          t.fillStyle = gr; t.fillRect(0, 0, W, HH); t.restore();
        }
        o.drawImage(tmp, 0, 0);
      });
    }
    var LIN = new Float32Array(256); for (var i = 0; i < 256; i++) LIN[i] = CURVE.U.lin(i);
    var OUT = new Uint8Array(4097); for (i = 0; i <= 4096; i++) OUT[i] = CURVE.U.srgb(i / 4096);
    function develop(stops) {   // what the film does with too much or too little light (simulated)
      var img = ctx.getImageData(0, 0, W, HH), p = img.data;
      var shown = stops >= 0 ? Math.min(stops, 3) * 0.1 + Math.max(0, stops - 3) * 0.7 : stops >= -1 ? stops * 0.45 : -0.45 + (stops + 1) * 1.0;
      var gain = Math.pow(2, shown), lift = stops < -1 ? Math.min(0.05, (-1 - stops) * 0.02) : 0, flat = stops > 1.5 ? Math.min(0.12, (stops - 1.5) * 0.04) : 0;
      for (var q = 0; q < p.length; q += 4) for (var c = 0; c < 3; c++) {
        var v = LIN[p[q + c]] * gain; v = v / (1 + v * 0.15) * 1.15; v = v * (1 - flat) + flat * 0.5 + lift;
        p[q + c] = OUT[(v <= 0 ? 0 : v >= 1 ? 1 : v) * 4096 | 0];
      }
      ctx.putImageData(img, 0, 0);
    }
    var tm = 0, me = null;
    function later() { if (tm) return; tm = requestAnimationFrame(function () { tm = 0; render(); }); }
    function render() {
      var a = aim();
      drawFar(Lfar.getContext("2d"), a); drawMid(Lmid.getContext("2d"), a); me = drawMe(Lme.getContext("2d"), a);
      var ac = acc.getContext("2d"); ac.clearRect(0, 0, W, HH);
      lensBlur(Lfar, 1e5, acc); lensBlur(Lmid, 14, acc); lensBlur(Lme, st.d, acc);
      ctx.clearRect(0, 0, W, HH); ctx.drawImage(acc, 0, 0);
      var stops = stopsFor(st.dot, st.sky), faceStops = stops + (st.light === "front" ? -2 : 0);
      develop(stops);
      text(stops, faceStops);
    }
    function text(stops, faceStops) {
      var d = st.d, hgt = 0.75 * d, rFace = Math.hypot((me.x - W / 2) / PXMM, (me.face - HH / 2) / PXMM) / 18, b = blurAt(st.dot, rFace, d);
      var headIn = me.head >= 0, feetIn = me.foot <= HH, faceIn = me.face > 0 && me.face < HH && me.x > 0 && me.x < W;
      nH.set(H.fmt(hgt, 2) + " m");
      nFit.set(!faceIn ? "face cut off" : headIn && feetIn ? "whole, head to toe" : !feetIn && headIn ? "cut off " + (hgt < 1.0 ? "at the waist" : hgt < 1.4 ? "at the knees" : "at the ankles") : "head cut off", faceIn && headIn ? "ok" : "hot");
      nS.set(faceIn ? (b <= 0.05 ? "sharp (" + H.fmt(b, 3) + " mm)" : "soft (" + H.fmt(b, 3) + " mm)") : "–", b <= 0.05 ? "ok" : "hot");
      nE.set((faceStops >= 0 ? "+" : "") + H.fmt(faceStops, 1) + " steps on the face", faceStops < -1 || faceStops > 3 ? "hot" : "ok");
      var notes = [];
      if (d < 1.0 || b > 0.05) notes.push(rFace > 0.4 ? "Your friend is near the end of the picture, where this lens is softest: " + H.fmt(b, 3) + " mm of blur against " + H.fmt(blurAt(st.dot, 0, d), 3) + " mm in the middle. Put what matters in the middle." : "At " + H.fmt(d, 1) + " m the middle is soft: " + H.fmt(b, 3) + " mm. The " + st.dot + " dot is sharp from " + { small: "1.0", middle: "1.3", large: "1.5" }[st.dot] + " m. Step back.");
      else notes.push("Sharp face: " + H.fmt(b, 3) + " mm of blur, under the 0.05 mm a postcard forgives.");
      if (headIn && feetIn) notes.push(hgt > 3.5 ? "Head to toe, but small: the picture is " + H.fmt(hgt, 1) + " m tall here. Is that what you wanted?" : "The whole person fits: the picture is " + H.fmt(hgt, 1) + " m tall here.");
      else if (!headIn) notes.push("The top of the head is cut off. Drag your friend lower in the picture.");
      else notes.push("The picture is " + H.fmt(hgt, 2) + " m tall here, so the bottom is cut. Head to toe needs 1.7 ÷ 0.75: about 2.3 m away, aimed at their middle, or further back with the face in the middle.");
      if (faceStops < -1) notes.push(st.light === "front" ? "Sun behind them: their face is about two steps darker than the sky, past what the film forgives. Give more light: one dot bigger, or turn them round." : "Too little light: " + H.fmt(-faceStops, 1) + " steps short. The film forgives 1 step too little, not more. Use a bigger dot.");
      else if (faceStops > 3) notes.push("Very much too much light, " + H.fmt(faceStops, 1) + " steps. Use a smaller dot.");
      else notes.push("Light on the face: " + (faceStops >= 0 ? H.fmt(faceStops, 1) + " steps more than needed" : H.fmt(-faceStops, 1) + " steps less than needed") + ", inside what the film forgives (1 too little, 3 too much).");
      if (st.light === "side") notes.push("Sun to one side: shadows show the shape of a face.");
      if (st.light === "behind" && faceStops >= -1) notes.push("Sun behind you: an evenly lit, rather flat face. Mind your own shadow.");
      say.innerHTML = "<strong>Your picture, simulated:</strong> " + notes.map(function (s) { return s.replace(/</g, "&lt;"); }).join(" ");
    }
    // drag your friend around
    var dragging = false, last = null;
    function pos(e) { var b = cv.getBoundingClientRect(); return [(e.clientX - b.left) * W / b.width, (e.clientY - b.top) * HH / b.height]; }
    cv.addEventListener("pointerdown", function (e) { dragging = true; last = pos(e); try { cv.setPointerCapture(e.pointerId); } catch (x) { } stage.style.cursor = "grabbing"; });
    cv.addEventListener("pointermove", function (e) { if (!dragging) return; var p = pos(e); st.tx = H.clamp(st.tx + (p[0] - last[0]) / PXMM, -22, 22); st.ty = H.clamp(st.ty - (p[1] - last[1]) / PXMM, -16, 16); last = p; later(); });
    cv.addEventListener("pointerup", function () { dragging = false; stage.style.cursor = "grab"; });
    stage.addEventListener("keydown", function (e) {
      var k = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] }[e.key]; if (!k) return;
      e.preventDefault(); st.tx = H.clamp(st.tx + k[0] * 1.5, -22, 22); st.ty = H.clamp(st.ty + k[1] * 1.5, -16, 16); later();
    });
    if (api.onVisible) api.onVisible(render); else render();
    render();
    return { destroy: function () { host.innerHTML = ""; } };
  });
})();

/* Lesson 8's picture (hero_fig, and its card): aiming.  The sight on top and the lens look along two lines that meet about 2.8 m away (build/sightcheck.json). */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#B7791F", COLINK = "#7A4E10";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  C.fig("fig_l08_sight", function () {
    var b = '<rect width="640" height="360" fill="#fff"/>' +
      '<rect x="36" y="172" width="100" height="84" rx="8" fill="#3A3632" stroke="' + INK + '" stroke-width="3"/><rect x="132" y="196" width="14" height="38" rx="3" fill="#E8641B" stroke="' + INK + '" stroke-width="2"/>' +
      '<rect x="40" y="152" width="14" height="20" fill="' + COL + '" stroke="' + INK + '" stroke-width="2"/><path d="M118 172 L126 156 L134 172 Z" fill="' + COL + '" stroke="' + INK + '" stroke-width="2"/>' +
      '<line x1="146" y1="215" x2="632" y2="215" stroke="#2B6CD8" stroke-width="4" stroke-dasharray="12 7"/>' +
      '<line x1="47" y1="152" x2="540" y2="215" stroke="' + COL + '" stroke-width="4"/>' +
      '<circle cx="540" cy="215" r="13" fill="#fff" stroke="' + INK + '" stroke-width="3"/><circle cx="540" cy="215" r="5" fill="' + INK + '"/>' +
      T(270, 150, "the sight", 24, 800, COLINK, "middle") + T(330, 252, "the lens", 24, 800, "#2B6CD8", "middle") +
      T(540, 290, "they meet", 24, 800, INK, "middle") + T(540, 320, "about 2.8 m away", 20, 600, "#625C53", "middle") + T(86, 290, "side view", 18, 600, "#625C53", "middle");
    return C.U.svg(640, 360, b, "Side view of the camera. You look along the sight on top; the lens looks along its own line lower down. The two lines meet about 2.8 m in front of the camera, where the aim is best.");
  });
})();
