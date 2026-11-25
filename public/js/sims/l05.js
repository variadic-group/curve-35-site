/* CURVE 35, lesson 05: interactive pieces and figures. Numbers from course/FACTS.md and build/*.json (model ONE-135 v2.14). */
(function () {
  "use strict";
  /* --- small helpers shared by lessons 5 to 8 (copied into each file so each stands alone) --- */
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === "text") e.textContent = attrs[k]; else if (k === "html") e.innerHTML = attrs[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]); else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function sv(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs || {}) e.setAttribute(k, attrs[k]); return e; }
  function css() {
    if (document.getElementById("lx-style")) return;
    var s = document.createElement("style"); s.id = "lx-style";
    s.textContent = [
      ".lx{font:400 15px/1.45 var(--sans,system-ui,sans-serif);color:var(--stage-ink,#2D2A26);--k:var(--lx-k,#0f8b8d)}",
      ".lx *{box-sizing:border-box}",
      ".lx-stage{background:#fff;border:2px solid #000;border-radius:14px;overflow:hidden;position:relative}",
      ".lx-stage svg,.lx-stage canvas{display:block;width:100%;height:auto;touch-action:none}",
      ".lx-row{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:flex-end;margin:14px 0 0}",
      ".lx-ctl{display:flex;flex-direction:column;gap:6px;min-width:220px;flex:1}",
      ".lx-ctl label{font-weight:600;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--stage-mute,#625C53)}",
      ".lx-ctl output{font-weight:600;color:var(--stage-ink,#2D2A26);text-transform:none;letter-spacing:0;font-size:14px}",
      ".lx input[type=range]{width:100%;accent-color:var(--lc,var(--k))}",
      ".lx input[type=range]:disabled{opacity:.35}",
      ".lx-btn{font:600 15px/1 var(--sans,system-ui,sans-serif);border:1.5px solid #6b6356;background:var(--stage-2,#fff);color:var(--stage-ink,#2D2A26);border-radius:12px;padding:12px 16px;cursor:pointer}",
      ".lx-btn:hover{border-color:var(--lc,var(--k))}",
      ".lx-btn.go{background:var(--lc,var(--k));border-color:var(--lc,var(--k));color:var(--lc-on,#fff)}",
      ".lx-btn:disabled{opacity:.45;cursor:default}",
      ".lx-seg{display:inline-flex;flex-wrap:wrap;gap:6px}",
      ".lx-seg button{font:600 13.5px/1 var(--sans,system-ui,sans-serif);border:1.5px solid #6b6356;border-radius:10px;background:var(--stage-2,#fff);color:var(--stage-ink,#2D2A26);padding:10px 12px;cursor:pointer}",
      ".lx-seg button:hover{border-color:var(--lc,var(--k))}",
      ".lx-seg button[aria-pressed=true]{background:var(--lc,var(--k));border-color:var(--lc,var(--k));color:var(--lc-on,#fff)}",
      ".lx-read{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:8px;margin:14px 0 0}",
      ".lx-chip{background:var(--stage-2,#EFEBE3);border:1.5px solid #3a352d;border-radius:12px;padding:9px 12px;color:var(--stage-ink,#2D2A26)}",
      ".lx-chip b{display:block;font-size:22px;line-height:1.15;font-variant-numeric:lining-nums tabular-nums}",
      ".lx-chip span{font-size:11.5px;color:var(--stage-mute,#625C53);text-transform:uppercase;letter-spacing:.05em}",
      ".lx-chip.bad{background:#5a1f17;border-color:#e2553f}.lx-chip.good{background:#173d26;border-color:#3fbf6a}",
      ".lx-chip.bad span,.lx-chip.good span{color:#e8e1d4}.lx-chip.bad b,.lx-chip.good b{color:#fff}",
      ".lx-say{margin:12px 0 0;font-size:15px;line-height:1.5;min-height:1.5em;color:var(--stage-ink,#2D2A26);border-top:1px solid #3a352d;padding-top:12px}",
      ".lx-tag{position:absolute;right:10px;top:8px;font:600 11px/1 var(--sans,system-ui,sans-serif);letter-spacing:.06em;text-transform:uppercase;background:#1b1a18;color:#fff;padding:5px 8px;border-radius:6px}",
      ".lx svg text{font-family:var(--sans,system-ui,sans-serif)}"
    ].join("\n");
    document.head.appendChild(s);
  }
  function root(host, colour) { css(); var r = el("div", { "class": "lx" }); r.style.setProperty("--lx-k", colour || "#0f8b8d"); host.appendChild(r); return r; }
  function slider(o) {   // {label, min, max, step, value, fmt, on}
    var out = el("output"), inp = el("input", { type: "range", min: o.min, max: o.max, step: o.step, value: o.value });
    var id = "lx" + Math.random().toString(36).slice(2, 8); inp.id = id;
    var lab = el("label", { "for": id }, [o.label + " ", out]);
    function upd() { var v = +inp.value; out.textContent = o.fmt ? o.fmt(v) : v; inp.setAttribute("aria-valuetext", out.textContent); o.on && o.on(v); }
    inp.addEventListener("input", upd);
    var box = el("div", { "class": "lx-ctl" }, [lab, inp]); box.input = inp; box.set = function (v) { inp.value = v; upd(); }; box.init = upd; return box;
  }
  function seg(label, items, value, on) {   // items: [{v, t}]
    var g = el("div", { "class": "lx-seg", role: "group", "aria-label": label }), bs = [];
    items.forEach(function (it) {
      var b = el("button", { type: "button", "aria-pressed": String(it.v === value), text: it.t, onclick: function () { pick(it.v); } });
      b._v = it.v; bs.push(b); g.appendChild(b);
    });
    function pick(v) { bs.forEach(function (b) { b.setAttribute("aria-pressed", String(b._v === v)); }); on(v); }
    g.pick = pick; return g;
  }
  function chip(label) { var b = el("b"), c = el("div", { "class": "lx-chip" }, [b, el("span", { text: label })]); c.val = function (t, cls) { b.textContent = t; c.className = "lx-chip" + (cls ? " " + cls : ""); }; return c; }
  function say(r) { var p = el("p", { "class": "lx-say", "aria-live": "polite" }); r.appendChild(p); return p; }
  function onVis(api, fn) { var done = false; function go(on) { if (on === false || done) return; done = true; fn(); } if (api && api.onVisible) { api.onVisible(go); setTimeout(function () { go(true); }, 1500); } else go(true); }
  function reg(kind, name, fn) {
    var C = window.CURVE = window.CURVE || {};
    if (typeof C[kind] === "function") C[kind](name, fn);
    else { (C["_" + kind + "Queue"] = C["_" + kind + "Queue"] || []).push([name, fn]); }
  }
  function svgFig(w, h, title, body) { return '<svg viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + title.replace(/"/g, "&quot;") + '" xmlns="http://www.w3.org/2000/svg" width="100%" style="font-family:var(--sans,system-ui,sans-serif)">' + body + "</svg>"; }
  function fmtFrac(s) { return "1/" + Math.round(1 / s); }
  /* --- end helpers --- */

  /* ================= lesson 5: the shutter ================= */
  var PRINTERS = [   // build/log_dial_exposure.txt (middle dot) and course/FACTS.md; click force from the same log
    { w: "−0.15", n: "far too thin", T: 1 / 176, F: 0.7 },
    { w: "−0.08", n: "thin", T: 1 / 216, F: 1.1 },
    { w: "±0", n: "exact", T: 1 / 258, F: 1.5 },
    { w: "+0.10", n: "typical", T: 1 / 322, F: 2.3 },
    { w: "+0.15", n: "fat", T: 1 / 349, F: 2.5 },
    { w: "+0.25", n: "far too fat", T: 1 / 423, F: 3.4 }
  ];
  var T_TYP = 1 / 322, TRAVEL = 15.4, GEAR = 3.1, OPEN_MM = 5.5, R_MM = 17, PX = 10;   // window travel at the lens 15.4 mm; finger 5 mm; gearing about 3.1 (build/shutter.json)
  var HALF = (TRAVEL / 2) / R_MM;   // radians each side of the lens
  function gauss() { var u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function lg2(x) { return Math.log(x) / Math.LN2; }

  reg("sim", "l05_swing", function (host, api) {
    var K = (api && api.colour) || "#0f8b8d", RM = !!(api && api.reducedMotion), BL = "#8145C0", BLK = "#3A1F5C";   // the shutter is purple, whatever the page's own colour is
    var r = root(host, K);
    var st = { mode: "click", p: 3, v: 10, side: 1, phase: "idle", t: 0, raf: 0, dots: [] };
    var W = 720, H = 430, px = 180, py = 300, R = R_MM * PX, lx = px, ly = py - R;
    var s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "The shutter blade seen from inside the camera. It swings on its peg; its one window passes the lens's hole once per press. Readings below give the time it is open." });
    // left: blade
    s.appendChild(sv("rect", { x: 0, y: 0, width: 360, height: 330, fill: "#1e2426" }));
    s.appendChild(sv("circle", { cx: lx, cy: ly, r: 60, fill: "none", stroke: "#D9601A", "stroke-width": 3, "stroke-dasharray": "7 5" }));
    var hole = sv("circle", { cx: lx, cy: ly, r: 14.4, fill: "#ffe680" }); s.appendChild(hole);
    var glow = sv("circle", { cx: lx, cy: ly, r: 40, fill: "#ffe680", opacity: 0 }); s.appendChild(glow);
    var blade = sv("g", {});
    function arc(rad, a) { return [px + rad * Math.sin(a), py - rad * Math.cos(a)]; }
    var A = 0.86, ri = 120, ro = 212, p1 = arc(ri, -A), p2 = arc(ro, -A), p3 = arc(ro, A), p4 = arc(ri, A), wr = (OPEN_MM - 2.88) / 2 * PX;
    var d = "M" + p1 + " L" + p2 + " A" + ro + " " + ro + " 0 0 1 " + p3 + " L" + p4 + " A" + ri + " " + ri + " 0 0 0 " + p1 + "Z " +
      "M" + (lx - wr) + "," + ly + " a" + wr + "," + wr + " 0 1,0 " + 2 * wr + ",0 a" + wr + "," + wr + " 0 1,0 " + -2 * wr + ",0Z";
    blade.appendChild(sv("path", { d: d, fill: BL, "fill-rule": "evenodd", stroke: BLK, "stroke-width": 2 }));
    blade.appendChild(sv("path", { d: "M" + (px - 16) + "," + py + " L" + arc(ri, -A) + " L" + arc(ri, A) + " L" + (px + 16) + "," + py + "Z", fill: BL, stroke: BLK, "stroke-width": 2 }));
    s.appendChild(blade);
    s.appendChild(sv("circle", { cx: px, cy: py, r: 11, fill: "#ddd", stroke: "#0b3d3e", "stroke-width": 2 }));
    function lab(x, y, t, a, c, sz, w) { var e = sv("text", { x: x, y: y, "text-anchor": a || "start", fill: c || "#fff", "font-size": sz || 13, "font-weight": w || 600 }); e.textContent = t; s.appendChild(e); return e; }
    lab(px + 16, py + 4, "peg");
    lab(lx + 66, ly - 48, "lens", "start", "#ffb27a");
    var wl = lab(12, 22, "window over the lens: no", "start", "#cfd8d8", 13);
    lab(348, 322, "seen from inside", "end", "#93a3a3", 11, 400);
    // right: force line
    var gx = 400, gy = 40, gw = 290, gh = 150;
    s.appendChild(sv("rect", { x: gx, y: gy, width: gw, height: gh, fill: "#fbfaf7", stroke: "#2D2A26", "stroke-width": 1.5 }));
    lab(gx, gy - 12, "push at the finger (N)", "start", "#2D2A26", 13);
    lab(gx + gw, gy + gh + 18, "how far the finger has pressed: 0 to 5 mm", "end", "#625C53", 12, 400);
    var fpath = sv("path", { fill: "none", stroke: K, "stroke-width": 3 }); s.appendChild(fpath);
    var fdot = sv("circle", { r: 7, fill: "#D9601A", stroke: "#fff", "stroke-width": 2 }); s.appendChild(fdot);
    var fpk = lab(gx + 10, gy + 18, "", "start", "#2D2A26", 13);
    function gxp(x) { return gx + x / 5 * gw; } function gyp(f) { return gy + gh - f / 4 * gh; }
    function forceAt(x) {   // click mode: the tooth climbs its notch over the first mm, then lets go; push mode: only the blade's drag
      var F = PRINTERS[st.p].F;
      if (st.mode === "push") return 0.25;
      return x <= 1 ? F * Math.pow(x, 1.4) : Math.max(0.12 * F, F * Math.exp(-(x - 1) * 25));
    }
    function drawForce() { var dd = ""; for (var i = 0; i <= 100; i++) { var x = i / 20; dd += (i ? "L" : "M") + gxp(x).toFixed(1) + "," + gyp(forceAt(x)).toFixed(1); } fpath.setAttribute("d", dd); fpk.textContent = st.mode === "push" ? "no click: only the blade's drag" : "peak: the click, about " + PRINTERS[st.p].F + " N"; }
    // clock
    var clk = lab(545, 250, "0.0 ms", "middle", "#2D2A26", 44, 600);
    var clk2 = lab(545, 276, "time the window is over the lens", "middle", "#625C53", 13, 400);
    var slow = lab(545, 300, "", "middle", K, 13, 600);
    // ruler of steps
    var ry = 380, rx0 = 40, rx1 = 690, smin = -2, smax = 6;
    function rxp(v) { return rx0 + (v - smin) / (smax - smin) * (rx1 - rx0); }
    s.appendChild(sv("rect", { x: rxp(-1), y: ry - 18, width: rxp(3) - rxp(-1), height: 36, fill: "#dff3e4" }));
    s.appendChild(sv("line", { x1: rx0, y1: ry, x2: rx1, y2: ry, stroke: "#2D2A26", "stroke-width": 2 }));
    for (var k = smin; k <= smax; k++) { s.appendChild(sv("line", { x1: rxp(k), y1: ry - 6, x2: rxp(k), y2: ry + 6, stroke: "#2D2A26", "stroke-width": 2 })); lab(rxp(k), ry + 24, (k > 0 ? "+" : "") + k, "middle", "#2D2A26", 12, 400); }
    lab(rxp(1), ry - 24, "the film still makes a picture", "middle", "#1d6b35", 12, 600);
    lab(rx0, 342, "steps too much light, full sun, small dot, ISO 400: each press is a dot", "start", "#625C53", 12, 400);
    var dotsG = sv("g", {}); s.appendChild(dotsG);
    var stage = el("div", { "class": "lx-stage" }, [s]); r.appendChild(stage);
    // controls
    var go = el("button", { type: "button", "class": "lx-btn go", text: "Press the rocker" });
    var skip = el("button", { type: "button", "class": "lx-btn", text: "Skip to the end" }); skip.hidden = true;
    var clear = el("button", { type: "button", "class": "lx-btn", text: "Clear the dots" });
    var modeSeg = seg("Shutter", [{ v: "click", t: "With the click" }, { v: "push", t: "No click: blade follows the finger" }], "click", function (v) { st.mode = v; drawForce(); speak(); });
    var pSeg = seg("Printer", PRINTERS.map(function (p, i) { return { v: i, t: p.w }; }), 3, function (v) { st.p = v; drawForce(); speak(); });
    var vS = slider({ label: "Your finger:", min: 2, max: 20, step: 1, value: 10, fmt: function (v) { return v + " cm a second" + (v <= 4 ? " (slow)" : v >= 15 ? " (quick)" : ""); }, on: function (v) { st.v = v; } });
    r.appendChild(el("div", { "class": "lx-row" }, [go, skip, clear]));
    r.appendChild(el("div", { "class": "lx-row" }, [modeSeg]));
    r.appendChild(el("div", { "class": "lx-row" }, [el("div", { "class": "lx-ctl" }, [el("label", { text: "Printer: wall error in mm" }), pSeg]), vS]));
    var cT = chip("open for"), cF = chip("as a fraction"), cL = chip("light vs a typical click"), cS = chip("full sun, small dot");
    r.appendChild(el("div", { "class": "lx-read" }, [cT, cF, cL, cS]));
    var out = say(r);
    [cT, cF, cL, cS].forEach(function (c) { c.val("–"); });
    vS.init(); drawForce();
    function speak() {
      out.textContent = st.mode === "click" ? "With the click on the " + PRINTERS[st.p].n + " printer, the model gives about " + fmtFrac(PRINTERS[st.p].T) + " s whatever your finger does. Press and compare a slow finger with a quick one." :
        "No click: the blade moves only as fast as your finger, about three times faster at the window than at your fingertip. Try a slow finger.";
    }
    speak();
    function setBlade(sMM) {   // sMM: distance the window has moved, 0..TRAVEL
      var a = (-HALF + sMM / TRAVEL * 2 * HALF) * st.side;
      blade.setAttribute("transform", "rotate(" + (a * 180 / Math.PI).toFixed(2) + " " + px + " " + py + ")");
      var off = Math.abs(sMM - TRAVEL / 2), open = off < OPEN_MM / 2;
      glow.setAttribute("opacity", open ? (0.55 * (1 - off / (OPEN_MM / 2))).toFixed(2) : 0);
      wl.textContent = "window over the lens: " + (open ? "YES, light reaches the film" : "no");
      wl.setAttribute("fill", open ? "#ffe680" : "#cfd8d8");
    }
    setBlade(0);
    function fingerDot(x) { fdot.setAttribute("cx", gxp(x)); fdot.setAttribute("cy", gyp(forceAt(x))); }
    fingerDot(0);
    function result(T) {
      var light = T / T_TYP, steps = lg2(light), sun = 0.5 + steps;
      cT.val((T * 1000).toFixed(1) + " ms"); cF.val(fmtFrac(T) + " s");
      cL.val(light.toFixed(1) + "×", light > 2 ? "bad" : "");
      cS.val((sun >= 0 ? "+" : "") + sun.toFixed(1) + " steps", sun > 3 || sun < -1 ? "bad" : "good");
      st.dots.push({ v: sun, m: st.mode });
      var c = sv("circle", { cx: rxp(Math.max(smin, Math.min(smax, sun))), cy: ry - 8 + (st.dots.length % 5) * 4 - 8, r: 5, fill: st.mode === "click" ? K : "#c0392b", opacity: 0.8 }); dotsG.appendChild(c);
      out.textContent = "Open for " + (T * 1000).toFixed(1) + " thousandths of a second, about " + fmtFrac(T) + " s: " + light.toFixed(1) + " times the light of a typical click, so " + (sun >= 0 ? "+" : "") + sun.toFixed(1) + " steps in full sun at the small dot. " +
        (sun > 3 ? "Outside the film's window: too dense. The click would have saved it." : "Inside the film's window: a picture.");
    }
    function run() {
      if (st.phase === "load" || st.phase === "swing") return;
      cancelAnimationFrame(st.raf);
      var P = PRINTERS[st.p], vmm = st.v * 10, T, vw, tLoad, tSwing, fLoad = 10, fSwing = 100;
      if (st.mode === "click") { T = P.T * Math.pow(2, gauss() * 0.27); vw = OPEN_MM / T; tLoad = 1 / vmm; }
      else { vw = GEAR * vmm; T = OPEN_MM / vw; tLoad = 0; }
      tSwing = TRAVEL / vw;
      go.disabled = true; skip.hidden = false;
      slow.textContent = st.mode === "click" ? "pressing: shown 10× slower; swing: 100× slower" : "the whole swing: shown 100× slower";
      var t0 = performance.now(), openT = 0;
      function end() { cancelAnimationFrame(st.raf); setBlade(TRAVEL); fingerDot(5); clk.textContent = (T * 1000).toFixed(1) + " ms"; st.phase = "idle"; st.side = -st.side; go.disabled = false; skip.hidden = true; result(T); setTimeout(function () { if (st.phase === "idle") setBlade(0); }, 900); }
      skip.onclick = end;
      if (RM) { end(); return; }
      st.phase = "load";
      function frame(now) {
        var e = (now - t0) / 1000;
        if (e < tLoad * fLoad) { st.phase = "load"; var x = e / fLoad / tLoad; fingerDot(x); clk.textContent = "0.0 ms"; }
        else {
          st.phase = "swing";
          var ts = (e - tLoad * fLoad) / fSwing; if (ts >= tSwing) { end(); return; }
          var sMM = vw * ts; setBlade(sMM); fingerDot((st.mode === "click" ? 1 : 0) + (st.mode === "click" ? 4 : 5) * sMM / TRAVEL);
          var t1 = (TRAVEL / 2 - OPEN_MM / 2) / vw; openT = Math.max(0, Math.min(T, ts - t1));
          clk.textContent = (openT * 1000).toFixed(1) + " ms";
        }
        st.raf = requestAnimationFrame(frame);
      }
      st.raf = requestAnimationFrame(frame);
    }
    go.addEventListener("click", run);
    clear.addEventListener("click", function () { st.dots = []; dotsG.innerHTML = ""; });
    return { destroy: function () { cancelAnimationFrame(st.raf); } };
  });

  /* ---- the gallop: what a shutter time does to a running horse (simulated) ---- */
  var SPEED = 16;   // m/s: a mile in 1 min 40 s, the "1:40 gait" in the title of the 1878 cards
  var TIMES = [
    { T: 1 / 1000, t: "1/1000", n: "Muybridge, 1878 (claimed)" },
    { T: 1 / 423, t: "1/423", n: "this camera, fattest printer" },
    { T: 1 / 322, t: "1/322", n: "this camera, typical" },
    { T: 1 / 176, t: "1/176", n: "this camera, thinnest printer" },
    { T: 1 / 28, t: "1/28", n: "no click, slow push" },
    { T: 1 / 4, t: "1/4", n: "a quick count" },
    { T: 1, t: "1 s", n: "time picture, count 1" }
  ];
  function horse(c, x, y, s, ph) {   // a plain drawn horse, facing right; x,y = middle of the back; s = px per metre; ph = stride 0..1
    var TAU = Math.PI * 2, b = Math.sin(TAU * ph) * 0.05 * s;
    c.save(); c.translate(x, y + b); c.fillStyle = "#26221e"; c.strokeStyle = "#26221e"; c.lineCap = "round"; c.lineJoin = "round";
    c.beginPath(); c.ellipse(0, 0.15 * s, 0.75 * s, 0.32 * s, 0, 0, TAU); c.fill();   // barrel
    c.beginPath(); c.moveTo(0.45 * s, -0.05 * s); c.lineTo(0.95 * s, -0.55 * s); c.lineTo(1.12 * s, -0.5 * s); c.lineTo(0.85 * s, 0.25 * s); c.closePath(); c.fill();   // neck
    c.beginPath(); c.ellipse(1.15 * s, -0.45 * s, 0.3 * s, 0.12 * s, 0.5, 0, TAU); c.fill();   // head
    c.lineWidth = 0.12 * s; c.beginPath(); c.moveTo(-0.72 * s, 0); c.quadraticCurveTo(-1.05 * s, 0.05 * s + Math.sin(TAU * ph) * 0.1 * s, -1.05 * s, 0.5 * s); c.stroke();   // tail
    var legs = [[-0.5, 0.0], [-0.4, 0.12], [0.5, 0.42], [0.6, 0.54]];   // [hip x, phase offset]: hind pair, then fore pair
    c.lineWidth = 0.11 * s;
    legs.forEach(function (L, i) {
      var p = TAU * (ph + L[1]), fore = i > 1, sw = Math.sin(p);
      var a1 = (fore ? 0.15 : -0.05) + 0.7 * sw, kx = L[0] * s + Math.sin(a1) * 0.48 * s, ky = 0.3 * s + Math.cos(a1) * 0.48 * s;
      var bend = (fore ? -1 : 1) * (0.35 + 0.65 * Math.max(0, Math.cos(p)));
      var a2 = a1 + bend, fx = kx + Math.sin(a2) * 0.5 * s, fy = ky + Math.cos(a2) * 0.5 * s;
      c.beginPath(); c.moveTo(L[0] * s, 0.25 * s); c.lineTo(kx, ky); c.lineTo(fx, fy); c.stroke();
    });
    c.restore();
  }
  function exposeFrame(w, h, phase0, T, mWide) {   // average many drawings over the time the shutter is open
    var cv = document.createElement("canvas"); cv.width = w; cv.height = h; var c = cv.getContext("2d", { willReadFrequently: true });
    var N = T > 0.2 ? 60 : T > 0.02 ? 36 : 16, acc = new Float32Array(w * h), s = w / mWide;
    for (var i = 0; i < N; i++) {
      var t = (i / (N - 1) - 0.5) * T, dx = SPEED * t * s, ph = phase0 + t * 2.3;
      c.fillStyle = "#f4efe6"; c.fillRect(0, 0, w, h);
      c.fillStyle = "#cfc6b6"; c.fillRect(0, h * 0.78, w, h * 0.22);
      for (var k = 0; k < 8; k++) { c.fillStyle = "#e3dccf"; c.fillRect((k + 0.5) * w / 8 - 1, 0, 2, h * 0.78); }   // marks on the wall behind
      horse(c, w / 2 + dx, h * 0.78 - 1.05 * s, s, ((ph % 1) + 1) % 1);
      var d = c.getImageData(0, 0, w, h).data;
      for (var j = 0, q = 0; j < d.length; j += 4, q++) acc[q] += d[j];
    }
    var img = c.createImageData(w, h);
    for (var q2 = 0, j2 = 0; q2 < acc.length; q2++, j2 += 4) { var v = acc[q2] / N; img.data[j2] = v; img.data[j2 + 1] = v * 0.98; img.data[j2 + 2] = v * 0.94; img.data[j2 + 3] = 255; }
    c.putImageData(img, 0, 0);
    return cv;
  }
  reg("sim", "l05_gallop", function (host, api) {
    var K = (api && api.colour) || "#0f8b8d";
    var r = root(host, K), st = { i: 2, ph: 0.55 };
    var big = el("canvas", { width: 720, height: 400, role: "img" }), strip = el("canvas", { width: 720, height: 150, role: "img", "aria-label": "Twelve small frames in a row, like the 1878 cards, all taken at the chosen shutter time." });
    var stage = el("div", { "class": "lx-stage" }, [big, el("div", { "class": "lx-tag", text: "simulated" })]);
    r.appendChild(stage); r.appendChild(el("div", { "class": "lx-stage", style: "margin-top:8px" }, [strip]));
    var tSeg = seg("Shutter time", TIMES.map(function (x, i) { return { v: i, t: x.t }; }), 2, function (v) { st.i = v; draw(); });
    var phS = slider({ label: "Moment in the stride:", min: 0, max: 99, step: 1, value: 55, fmt: function (v) { return v + "%"; }, on: function (v) { st.ph = v / 100; drawBig(); } });
    r.appendChild(el("div", { "class": "lx-row" }, [el("div", { "class": "lx-ctl" }, [el("label", { text: "Shutter time, seconds" }), tSeg]), phS]));
    var cM = chip("the horse moves"), cB = chip("of its body length"), cN = chip("what set this time");
    r.appendChild(el("div", { "class": "lx-read" }, [cM, cB, cN]));
    var out = say(r);
    function drawBig() {
      var x = TIMES[st.i], c = big.getContext("2d");
      c.drawImage(exposeFrame(720, 400, st.ph, x.T, 5), 0, 0);
      c.fillStyle = "rgba(45,42,38,.75)"; c.font = "600 15px system-ui,sans-serif"; c.fillText("shutter open " + x.t + " s · horse at 16 m a second", 14, 26);
      big.setAttribute("aria-label", "Simulated picture of a galloping horse with the shutter open " + x.t + " s. " + out.textContent);
    }
    function drawStrip() {
      var c = strip.getContext("2d"), x = TIMES[st.i]; c.fillStyle = "#2D2A26"; c.fillRect(0, 0, 720, 150);
      for (var k = 0; k < 12; k++) { var col = k % 6, row = Math.floor(k / 6); c.drawImage(exposeFrame(112, 66, k / 12, x.T, 5), 6 + col * 119, 6 + row * 72); }
    }
    function draw() {
      var x = TIMES[st.i], m = SPEED * x.T, pct = m / 2.4 * 100;
      cM.val(m < 1 ? (m * 100).toFixed(m < 0.1 ? 1 : 0) + " cm" : m.toFixed(m < 3 ? 1 : 0) + " m", pct > 10 ? "bad" : "good");
      cB.val(pct < 1 ? pct.toFixed(1) + "%" : Math.round(pct) + "%", pct > 10 ? "bad" : "good");
      cN.val(x.t + " s"); cN.querySelector("span").textContent = x.n;
      out.textContent = "At " + x.t + " s the horse moves " + cM.querySelector("b").textContent + " while the shutter is open, " + cB.querySelector("b").textContent + " of its body. " +
        (pct < 3 ? "Frozen: you could count its legs." : pct < 30 ? "Smeared: the legs are a blur." : "Gone: a ghost streak across the picture.");
      drawBig(); drawStrip();
    }
    phS.init(); onVis(api, draw);
    return { destroy: function () {} };
  });

  /* ---- figures ---- */
  reg("fig", "fig_l05_blade", function () {
    var b = '<rect width="560" height="300" fill="#fff"/>';
    b += '<g transform="translate(150 270)"><path d="M-98,-90 L-168,-150 A222,222 0 0 1 168,-150 L98,-90 A130,130 0 0 0 -98,-90Z M-13,-170 a13,13 0 1,0 26,0 a13,13 0 1,0 -26,0Z" fill="#8145C0" fill-rule="evenodd" stroke="#3A1F5C" stroke-width="2"/>';
    b += '<path d="M-14,0 L-60,-110 L60,-110 L14,0Z" fill="#8145C0" stroke="#3A1F5C" stroke-width="2"/><circle r="10" fill="#eee" stroke="#3A1F5C" stroke-width="2"/></g>';
    b += '<circle cx="150" cy="100" r="58" fill="none" stroke="#D9601A" stroke-width="3" stroke-dasharray="7 5"/>';
    b += '<path d="M330,70 h200 M330,70 l14,-8 M330,70 l14,8" stroke="#2D2A26" stroke-width="2" fill="none"/>';
    b += '<text x="346" y="58" font-size="15" font-weight="600" fill="#2D2A26">window: the only way in</text>';
    b += '<line x1="172" y1="100" x2="330" y2="70" stroke="#2D2A26" stroke-width="1.5"/>';
    b += '<text x="330" y="140" font-size="15" font-weight="600" fill="#A4460E">lens (orange ring)</text>';
    b += '<text x="330" y="186" font-size="15" font-weight="600" fill="#2D2A26">swings 15 mm at the lens</text>';
    b += '<text x="330" y="208" font-size="14" fill="#625C53">for 5 mm at the finger: 3 to 1</text>';
    b += '<text x="330" y="262" font-size="15" font-weight="600" fill="#2D2A26">peg: the blade turns on it</text>';
    b += '<line x1="168" y1="268" x2="326" y2="258" stroke="#2D2A26" stroke-width="1.5"/>';
    b += '<path d="M60,40 A140,140 0 0 1 240,40" fill="none" stroke="#D9601A" stroke-width="2.5" marker-end="url(#ah5)"/><defs><marker id="ah5" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10Z" fill="#D9601A"/></marker></defs>';
    b += '<text x="12" y="292" font-size="11" fill="#625C53">seen from inside the camera</text>';
    return svgFig(560, 300, "The shutter blade, a purple fan on a peg with one round window. Pressing the rocker swings it so the window passes the lens once; at rest solid plastic covers the lens.", b);
  });
  reg("fig", "fig_l05_force", function () {
    var x0 = 60, y0 = 240, w = 440, h = 190, b = '<rect width="560" height="300" fill="#fff"/>';
    b += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + (x0 + w) + '" y2="' + y0 + '" stroke="#2D2A26" stroke-width="2"/><line x1="' + x0 + '" y1="' + y0 + '" x2="' + x0 + '" y2="' + (y0 - h) + '" stroke="#2D2A26" stroke-width="2"/>';
    var d = "M" + x0 + "," + y0; for (var i = 1; i <= 40; i++) { var x = i / 40; d += " L" + (x0 + x * 88).toFixed(1) + "," + (y0 - Math.pow(x, 1.4) * 2.3 / 2.6 * h).toFixed(1); }
    d += " L" + (x0 + 96) + "," + (y0 - 22) + " L" + (x0 + w) + "," + (y0 - 18);
    b += '<path d="' + d + '" fill="none" stroke="#0f8b8d" stroke-width="4" stroke-linejoin="round"/>';
    b += '<circle cx="' + (x0 + 88) + '" cy="' + (y0 - 2.3 / 2.6 * h) + '" r="8" fill="#D9601A"/>';
    b += '<text x="' + (x0 + 104) + '" y="' + (y0 - 2.3 / 2.6 * h + 5) + '" font-size="17" font-weight="700" fill="#2D2A26">about 2.3 N: the click</text>';
    b += '<text x="' + (x0 + 104) + '" y="' + (y0 - 2.3 / 2.6 * h + 26) + '" font-size="14" fill="#625C53">the tooth jumps out of its notch</text>';
    b += '<text x="' + (x0 + 210) + '" y="' + (y0 - 34) + '" font-size="15" font-weight="600" fill="#0f8b8d">let go at once: the blade flies</text>';
    b += '<text x="' + (x0 + 10) + '" y="' + (y0 - 70) + '" font-size="13" fill="#625C53" transform="rotate(-62 ' + (x0 + 10) + ' ' + (y0 - 70) + ')">loading: nothing moves yet</text>';
    b += '<text x="' + (x0 + w) + '" y="' + (y0 + 26) + '" font-size="13" fill="#625C53" text-anchor="end">how far the finger has pressed →</text>';
    b += '<text x="' + (x0 - 8) + '" y="' + (y0 - h - 10) + '" font-size="13" fill="#625C53">push ↑</text>';
    return svgFig(560, 300, "A graph of push against how far the finger has pressed. The push climbs steeply to a peak of about 2.3 newtons, the click, then drops at once: the blade flies through its swing.", b);
  });
  reg("fig", "fig_l05_ruler", function () {
    var x0 = 40, step = 60, y = 150, b = '<rect width="560" height="240" fill="#fff"/>';
    function X(v) { return x0 + (v + 1.5) * step; }
    b += '<rect x="' + X(-1) + '" y="' + (y - 34) + '" width="' + (X(3) - X(-1)) + '" height="68" fill="#dff3e4" rx="6"/>';
    b += '<text x="' + X(1) + '" y="' + (y + 50) + '" font-size="13" font-weight="600" fill="#1d6b35" text-anchor="middle">film forgives 1 under, 3 over</text>';
    b += '<line x1="' + X(-1.5) + '" y1="' + y + '" x2="' + X(6) + '" y2="' + y + '" stroke="#2D2A26" stroke-width="2"/>';
    for (var k = -1; k <= 5; k++) b += '<line x1="' + X(k) + '" y1="' + (y - 8) + '" x2="' + X(k) + '" y2="' + (y + 8) + '" stroke="#2D2A26" stroke-width="2"/><text x="' + X(k) + '" y="' + (y + 28) + '" font-size="13" text-anchor="middle" fill="#2D2A26">' + (k > 0 ? "+" : "") + k + '</text>';
    b += '<circle cx="' + X(0.5) + '" cy="' + y + '" r="10" fill="#0f8b8d"/><text x="' + X(0.5) + '" y="' + (y + 80) + '" font-size="14" font-weight="600" text-anchor="middle" fill="#0f8b8d">click: +0.5</text>';
    b += '<circle cx="' + X(4) + '" cy="' + y + '" r="10" fill="#c0392b"/><text x="' + X(4) + '" y="' + (y + 60) + '" font-size="14" font-weight="600" text-anchor="middle" fill="#c0392b">slow push: +4</text>';
    b += '<path d="M' + X(0.5) + ',' + (y - 16) + ' Q' + X(2.25) + ',' + (y - 90) + ' ' + X(4) + ',' + (y - 16) + '" fill="none" stroke="#c0392b" stroke-width="2" stroke-dasharray="5 4"/><text x="' + X(2.25) + '" y="' + (y - 64) + '" font-size="13" text-anchor="middle" fill="#c0392b">+3.5 steps (11.5× the light)</text>';
    b += '<text x="' + X(-1.5) + '" y="24" font-size="14" fill="#625C53">steps too much light, full sun, small dot, ISO 400</text>';
    return svgFig(560, 240, "A ruler of steps of light. The film still makes a picture from 1 step under to 3 over. With the click, full sun at the small dot sits at plus half a step, inside. A slow push without a click adds three and a half steps, landing at plus 4, outside.", b);
  });
  reg("fig", "fig_l05_second", function () {
    var b = '<rect width="620" height="230" fill="#fff"/>', x0 = 20, w = 580, n = 322;
    for (var i = 0; i < n; i++) { var x = x0 + i * w / n; b += '<rect x="' + x.toFixed(2) + '" y="70" width="' + (w / n * 0.7).toFixed(2) + '" height="70" fill="' + (i === 161 ? "#ffd640" : "#2D2A26") + '"/>'; }
    b += '<rect x="' + (x0 + 161 * w / n - 6) + '" y="58" width="14" height="94" fill="none" stroke="#D9601A" stroke-width="3"/>';
    b += '<text x="20" y="40" font-size="17" font-weight="700" fill="#2D2A26">One second, cut into 322 slices</text>';
    b += '<text x="' + (x0 + 161 * w / n) + '" y="178" font-size="15" font-weight="700" text-anchor="middle" fill="#A4460E">this one: light reaches the film</text>';
    b += '<text x="20" y="212" font-size="13" fill="#625C53">each slice about 3.1 thousandths of a second (the model\'s figure)</text>';
    return svgFig(620, 230, "A bar standing for one second, cut into 322 thin slices. One slice is lit: that is how long this camera's shutter is open.", b);
  });
})();
