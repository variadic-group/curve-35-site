/* CURVE 35, lesson 06: interactive pieces and figures. Numbers from course/FACTS.md and build/*.json (model ONE-135 v2.14). */
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

  /* ================= lesson 6: one picture at a time ================= */
  var PITCH = 4.75, FRAME = 38, PIC = 36, CORE = 5.9, FULL = 10.1, NPIC = 36;
  var THICK = Math.PI * (FULL * FULL - CORE * CORE) / (NPIC * FRAME);   // film thickness that makes 36 pictures fill 5.9 -> 10.1 mm (about 0.15 mm)
  function rollR(L) { return Math.sqrt(CORE * CORE + THICK * Math.max(0, L) / Math.PI); }

  reg("sim", "l06_wind", function (host, api) {
    var K = (api && api.colour) || "#2b6cb0", RM = !!(api && api.reducedMotion);
    var r = root(host, K);
    var S = 4, W = 720, H = 400, gx = 360, fy = 170, fh = 35 * S;   // gate centre x; film top y
    var st = { D: 0, shots: [], lastD: null, knob: 0, red: 0 };
    var s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "The film seen from behind, with its holes. The blue frame wheel's teeth sit in the top row of holes. Turn the green knob to wind; take a picture when the arrow comes home." });
    s.appendChild(sv("rect", { x: 0, y: 0, width: W, height: H, fill: "#f7f4ee" }));
    var defs = sv("defs", {}); var cp = sv("clipPath", { id: "l06clip" }); cp.appendChild(sv("rect", { x: 110, y: 0, width: 500, height: H })); defs.appendChild(cp); s.appendChild(defs);
    // rolls
    var shell = sv("rect", { x: 22, y: fy - 10, width: 86, height: fh + 20, rx: 14, fill: "#3b3f44" }); s.appendChild(shell);
    var shellRoll = sv("circle", { cx: 65, cy: fy + fh / 2, r: 24, fill: "#7a5230", stroke: "#2D2A26" }); s.appendChild(shellRoll);
    var knob = sv("g", { tabindex: 0, role: "slider", "aria-label": "Green wind knob: drag round, or use the arrow keys", "aria-valuemin": 0, "aria-valuemax": 1400, style: "cursor:grab;outline:none" });
    knob.appendChild(sv("circle", { cx: 65, cy: 70, r: 42, fill: "#2f9e57", stroke: "#1c5e34", "stroke-width": 3 }));
    for (var g = 0; g < 12; g++) knob.appendChild(sv("rect", { x: 63, y: 30, width: 4, height: 10, fill: "#1c5e34", transform: "rotate(" + g * 30 + " 65 70)" }));
    var knobMark = sv("line", { x1: 65, y1: 70, x2: 65, y2: 36, stroke: "#fff", "stroke-width": 5, "stroke-linecap": "round" }); knob.appendChild(knobMark);
    s.appendChild(knob);
    var spoolBox = sv("rect", { x: 612, y: fy - 10, width: 96, height: fh + 20, rx: 14, fill: "#e4ddd0" }); s.appendChild(spoolBox);
    var redRoll = sv("circle", { cx: 660, cy: fy + fh / 2, r: FULL * S, fill: "#7a5230", stroke: "#2D2A26" }); s.appendChild(redRoll);
    s.appendChild(sv("circle", { cx: 660, cy: fy + fh / 2, r: CORE * S, fill: "#c62828" }));
    var redMark = sv("line", { x1: 660, y1: fy + fh / 2, x2: 660, y2: fy + fh / 2 - CORE * S, stroke: "#fff", "stroke-width": 3 }); s.appendChild(redMark);
    // film
    var film = sv("g", { "clip-path": "url(#l06clip)" }); s.appendChild(film);
    var strip = sv("g", {}); film.appendChild(strip);
    // gate
    s.appendChild(sv("rect", { x: gx - PIC / 2 * S, y: fy + 5.5 * S, width: PIC * S, height: 24 * S, fill: "none", stroke: "#D9601A", "stroke-width": 3 }));
    function T(x, y, t, a, c, sz, w) { var e = sv("text", { x: x, y: y, "text-anchor": a || "middle", fill: c || "#2D2A26", "font-size": sz || 13, "font-weight": w || 600 }); e.textContent = t; s.appendChild(e); return e; }
    T(gx, fy + fh + 26, "the picture: 36 × 24 mm (orange: where the light lands)", "middle", "#A4460E", 13);
    T(65, fy + fh + 26, "film's shell", "middle", "#2D2A26", 12); T(660, fy + fh + 26, "red spool", "middle", "#2D2A26", 12);
    T(65, 132, "drag me", "middle", "#1c5e34", 12);
    // frame wheel: pitch radius 38/2π mm, teeth in the top row of holes
    var wr = FRAME / (2 * Math.PI) * S, wcx = gx + 4 * PITCH * S, wcy = fy + 2.8 * S - wr;   // centre above a hole
    var wheel = sv("g", {});
    wheel.appendChild(sv("circle", { cx: 0, cy: 0, r: wr - 3, fill: "#2b6cb0", stroke: "#173f6b", "stroke-width": 2 }));
    for (var k = 0; k < 8; k++) wheel.appendChild(sv("path", { d: "M-5," + (wr - 4) + " L0," + (wr + 7) + " L5," + (wr - 4) + "Z", fill: "#2b6cb0", stroke: "#173f6b", "stroke-width": 1.5, transform: "rotate(" + k * 45 + ")" }));
    wheel.appendChild(sv("path", { d: "M0,0 L0," + (-wr + 7), stroke: "#fff", "stroke-width": 4, "stroke-linecap": "round" }));
    wheel.appendChild(sv("path", { d: "M-6," + (-wr + 14) + " L0," + (-wr + 4) + " L6," + (-wr + 14) + "Z", fill: "#fff" }));
    var wg = sv("g", { transform: "translate(" + wcx + " " + wcy + ")" }); wg.appendChild(wheel); s.appendChild(wg);
    var home = sv("path", { d: "M" + (wcx - 7) + "," + (wcy - wr - 16) + " L" + (wcx + 7) + "," + (wcy - wr - 16) + " L" + wcx + "," + (wcy - wr - 6) + "Z", fill: "#2D2A26" }); s.appendChild(home);
    var homeT = T(wcx, wcy - wr - 22, "arrow home = one picture", "middle", "#2D2A26", 12);
    var flash = sv("rect", { x: gx - PIC / 2 * S, y: fy + 5.5 * S, width: PIC * S, height: 24 * S, fill: "#fff6b0", opacity: 0 }); s.appendChild(flash);
    r.appendChild(el("div", { "class": "lx-stage" }, [s, el("div", { "class": "lx-tag", text: "film simulated" })]));
    // controls
    var wind1 = el("button", { type: "button", "class": "lx-btn", text: "Wind 1 mm" }), wind5 = el("button", { type: "button", "class": "lx-btn", text: "Wind 5 mm" });
    var shoot = el("button", { type: "button", "class": "lx-btn go", text: "Take a picture" }), reset = el("button", { type: "button", "class": "lx-btn", text: "New roll" });
    r.appendChild(el("div", { "class": "lx-row" }, [shoot, wind1, wind5, reset]));
    var cN = chip("pictures taken"), cW = chip("frame wheel turns since the last picture"), cR = chip("red knob turns, this picture"), cRR = chip("film roll on the red spool");
    r.appendChild(el("div", { "class": "lx-read" }, [cN, cW, cR, cRR]));
    var out = say(r);
    var Lstart = NPIC * FRAME;   // a loaded 36-picture film on the red spool
    function drawStrip() {
      while (strip.firstChild) strip.removeChild(strip.firstChild);
      var u0 = Math.floor((st.D - 70) / PITCH) - 2, u1 = Math.ceil((st.D + 70) / PITCH) + 2;
      strip.appendChild(sv("rect", { x: 0, y: fy, width: W, height: fh, fill: "#8a5a2b" }));
      st.shots.forEach(function (sh, i) {   // exposed pictures, darker, numbered
        var x = gx + (sh.u - PIC / 2 - st.D) * S;
        strip.appendChild(sv("rect", { x: x, y: fy + 5.5 * S, width: PIC * S, height: 24 * S, fill: sh.bad ? "rgba(198,40,40,.55)" : "rgba(30,20,10,.55)", stroke: sh.bad ? "#c62828" : "none", "stroke-width": 3 }));
        var tt = sv("text", { x: x + PIC * S / 2, y: fy + fh / 2 + 6, "text-anchor": "middle", fill: "#fff", "font-size": 18, "font-weight": 700 }); tt.textContent = (i + 1) + (sh.bad ? " overlaps!" : ""); strip.appendChild(tt);
      });
      for (var k = u0; k <= u1; k++) {
        var x = gx + (k * PITCH - st.D) * S;
        strip.appendChild(sv("rect", { x: x - 1.4 * S, y: fy + 1.0 * S, width: 2.8 * S, height: 2 * S, rx: 2, fill: "#f7f4ee" }));
        strip.appendChild(sv("rect", { x: x - 1.4 * S, y: fy + fh - 3.0 * S, width: 2.8 * S, height: 2 * S, rx: 2, fill: "#f7f4ee" }));
      }
    }
    function update(msg) {
      drawStrip();
      var ang = -st.D / FRAME * 360; wheel.setAttribute("transform", "rotate(" + ang.toFixed(2) + ")");
      knob.setAttribute("transform", "rotate(" + (-st.knob).toFixed(1) + " 65 70)"); knob.setAttribute("aria-valuenow", Math.round(st.D)); knob.setAttribute("aria-valuetext", Math.round(st.D) + " mm of film wound");
      var Lred = Lstart - st.D, rr = rollR(Lred);
      redRoll.setAttribute("r", (rr * S).toFixed(1)); redMark.setAttribute("transform", "rotate(" + (st.red * 360).toFixed(1) + " 660 " + (fy + fh / 2) + ")");
      shellRoll.setAttribute("r", (Math.sqrt(16 + THICK * st.D / Math.PI) * S * 1.1).toFixed(1));
      var since = st.lastD == null ? null : (st.D - st.lastD) / FRAME;
      var at = since != null && Math.abs(since - 1) < 0.03;
      home.setAttribute("fill", at ? "#2f9e57" : "#2D2A26"); homeT.textContent = at ? "HOME: take the picture" : "arrow home = one picture";
      cN.val(st.shots.length + " of " + NPIC);
      cW.val(since == null ? "–" : since.toFixed(2), since == null ? "" : at ? "good" : since > 1.05 ? "bad" : "");
      cR.val(since == null ? "–" : (st.redThis || 0).toFixed(2));
      cRR.val("r " + rr.toFixed(1) + " mm");
      if (msg) out.textContent = msg;
    }
    function wind(mm) {
      if (st.shots.length >= NPIC && mm > 0) { out.textContent = "That was the last picture. Wind on until the arrow stops, then three more turns, and all the film is home in its shell."; }
      var Lred = Lstart - st.D; if (Lred - mm < 0) mm = Lred;
      st.red += mm / (2 * Math.PI * rollR(Lred));   // the red spool turns less when its roll is fat
      st.redThis = (st.redThis || 0) + mm / (2 * Math.PI * rollR(Lred));
      st.knob += mm / (2 * Math.PI * Math.sqrt(16 + THICK * st.D / Math.PI)) * 360;
      st.D += mm; update();
    }
    function take() {
      var u = st.D, bad = st.shots.some(function (x) { return Math.abs(x.u - u) < PIC; });
      var gap = st.shots.length ? u - st.shots[st.shots.length - 1].u - PIC : null;
      st.shots.push({ u: u, bad: bad }); st.lastD = st.D; st.redThis = 0;
      if (!RM) { flash.setAttribute("opacity", 0.9); setTimeout(function () { flash.setAttribute("opacity", 0); }, 160); }
      update(bad ? "Double picture! You wound only " + (gap + PIC).toFixed(1) + " mm, less than 36: two pictures sit on top of each other." :
        gap == null ? "Picture 1. Now turn the green knob and watch the blue wheel: stop when its arrow comes home." :
        gap > 4 ? "Picture " + st.shots.length + ". You wound " + (gap + PIC).toFixed(1) + " mm: " + (gap - 2).toFixed(1) + " mm of film wasted, but no harm done." :
        "Picture " + st.shots.length + ". Eight holes, 38 mm, one turn of the wheel: spot on.");
    }
    wind1.onclick = function () { wind(1); }; wind5.onclick = function () { wind(5); }; shoot.onclick = take;
    reset.onclick = function () { st.D = 0; st.shots = []; st.lastD = null; st.knob = 0; st.red = 0; st.redThis = 0; update("New roll: 36 pictures, wound out onto the red spool. Take picture 1."); };
    knob.addEventListener("keydown", function (e) { if (e.key === "ArrowRight" || e.key === "ArrowUp") { wind(e.shiftKey ? 5 : 1); e.preventDefault(); } if (e.key === " " || e.key === "Enter") { take(); e.preventDefault(); } });
    var drag = null;
    function ptAng(e) { var b = s.getBoundingClientRect(), x = (e.clientX - b.left) / b.width * W - 65, y = (e.clientY - b.top) / b.height * H - 70; return Math.atan2(y, x); }
    knob.addEventListener("pointerdown", function (e) { drag = ptAng(e); knob.setPointerCapture(e.pointerId); e.preventDefault(); });
    knob.addEventListener("pointermove", function (e) {
      if (drag == null) return; var a = ptAng(e), d = a - drag; if (d > Math.PI) d -= 2 * Math.PI; if (d < -Math.PI) d += 2 * Math.PI; drag = a;
      if (d < 0) { var rs = Math.sqrt(16 + THICK * st.D / Math.PI); wind(-d * rs); }   // turning anticlockwise winds the film home; the knob has no reverse
    });
    knob.addEventListener("pointerup", function () { drag = null; });
    update("Picture 1 is ready in the gate. Press \"Take a picture\", then wind with the green knob (drag it anticlockwise) or the buttons, and stop when the blue arrow comes home.");
    return { destroy: function () {} };
  });

  reg("sim", "l06_roll", function (host, api) {
    var K = (api && api.colour) || "#2b6cb0";
    var r = root(host, K), st = { n: 36 };
    var W = 720, H = 360, s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "The red spool's roll of film, seen end on, and below it the whole roll of 36 pictures spaced two ways: by turns of the spool, and by eight holes." });
    s.appendChild(sv("rect", { width: W, height: H, fill: "#fff" }));
    var roll = sv("g", {}); s.appendChild(roll);
    var Sx = 9, cx = 130, cy = 120;
    function T(x, y, t, a, c, sz, w) { var e = sv("text", { x: x, y: y, "text-anchor": a || "start", fill: c || "#2D2A26", "font-size": sz || 13, "font-weight": w || 600 }); e.textContent = t; s.appendChild(e); return e; }
    var tR = T(250, 50, "", "start", "#2D2A26", 18, 700), tL = T(250, 78, "", "start", "#2D2A26", 15, 400);
    var bx = 250, by = 100, bs = 5;   // bars: one turn's length against one picture
    var barTurn = sv("rect", { x: bx, y: by, height: 22, fill: "#c62828" }), barPic = sv("rect", { x: bx, y: by + 30, width: 38 * bs, height: 22, fill: K });
    s.appendChild(barTurn); s.appendChild(barPic);
    var tT = T(bx, by + 17, "", "start", "#fff", 13), tP = T(bx + 6, by + 47, "8 holes: always 38 mm", "start", "#fff", 13);
    var rowA = sv("g", {}), rowB = sv("g", {}); s.appendChild(rowA); s.appendChild(rowB);
    T(20, 236, "36 pictures if you count TURNS of the red spool (one turn each):", "start", "#c62828", 13);
    T(20, 306, "36 pictures if you count 8 HOLES (what the frame wheel does):", "start", K, 13);
    var tA = T(20, 290, "", "start", "#625C53", 12, 400);
    r.appendChild(el("div", { "class": "lx-stage" }, [s]));
    var sl = slider({ label: "Pictures still on the red spool:", min: 0, max: 36, step: 1, value: 36, fmt: function (v) { return v; }, on: function (v) { st.n = v; draw(); } });
    r.appendChild(el("div", { "class": "lx-row" }, [sl]));
    var out = say(r);
    function strip(g, y, pos) {   // pos: start of each picture in mm along the roll
      while (g.firstChild) g.removeChild(g.firstChild);
      var tot = pos[pos.length - 1] + 40, sc = 680 / tot;
      g.appendChild(sv("rect", { x: 20, y: y, width: tot * sc, height: 30, fill: "#8a5a2b" }));
      pos.forEach(function (p, i) {
        var over = i > 0 && p - pos[i - 1] < PIC;
        g.appendChild(sv("rect", { x: 20 + p * sc, y: y + 4, width: PIC * sc, height: 22, fill: over ? "rgba(198,40,40,.85)" : "rgba(255,240,200,.75)", stroke: over ? "#c62828" : "none" }));
      });
    }
    var posTurn = [], posHole = [], Lr = NPIC * FRAME, u = 0;
    for (var i = 0; i < NPIC; i++) { posHole.push(i * FRAME); posTurn.push(u); u += 2 * Math.PI * rollR(Lr - u); }
    strip(rowA, 244, posTurn); strip(rowB, 314, posHole);
    var gap0 = posTurn[1] - posTurn[0] - PIC, gapN = posTurn[35] - posTurn[34] - PIC;
    tA.textContent = "first gap " + gap0.toFixed(0) + " mm wasted … last gap " + gapN.toFixed(1) + " mm: the spacing is all over the place";
    function draw() {
      var L = st.n * FRAME, rr = rollR(L), turn = 2 * Math.PI * rr;
      while (roll.firstChild) roll.removeChild(roll.firstChild);
      roll.appendChild(sv("circle", { cx: cx, cy: cy, r: FULL * Sx + 4, fill: "#f3efe7", stroke: "#DDD6CA" }));
      var d = "", a = 0, rad = CORE;   // the film as a spiral, layer by layer
      while (rad < rr) { var x = cx + rad * Sx * Math.cos(a), y = cy + rad * Sx * Math.sin(a); d += (d ? "L" : "M") + x.toFixed(1) + "," + y.toFixed(1); a += 0.12; rad += THICK * 0.12 / (2 * Math.PI); }
      roll.appendChild(sv("path", { d: d || "M0,0", fill: "none", stroke: "#8a5a2b", "stroke-width": 1.3 }));
      roll.appendChild(sv("circle", { cx: cx, cy: cy, r: CORE * Sx, fill: "#c62828" }));
      roll.appendChild(sv("line", { x1: cx, y1: cy, x2: cx + rr * Sx, y2: cy, stroke: "#2D2A26", "stroke-width": 2, "stroke-dasharray": "4 3" }));
      tR.textContent = "radius " + rr.toFixed(1) + " mm   →   one turn = 2 × 3.14 × " + rr.toFixed(1) + " = " + turn.toFixed(1) + " mm";
      tL.textContent = "one turn is " + (turn / FRAME).toFixed(2) + " pictures (" + (turn / PITCH).toFixed(1) + " holes)";
      barTurn.setAttribute("width", turn * bs); tT.textContent = "one turn: " + turn.toFixed(0) + " mm";
      out.textContent = "With " + st.n + " pictures on the red spool its roll has a radius of " + rr.toFixed(1) + " mm, so one turn moves " + turn.toFixed(1) + " mm of film: " + (turn / FRAME).toFixed(2) + " of a picture. Eight holes are always 38 mm.";
    }
    sl.init();
    return { destroy: function () {} };
  });

  /* ---- figures ---- */
  reg("fig", "fig_l06_holes", function () {
    var S = 7, x0 = 30, y0 = 60, b = '<rect width="620" height="370" fill="#fff"/>';
    b += '<rect x="' + x0 + '" y="' + y0 + '" width="' + 76 * S + '" height="' + 35 * S + '" fill="#8a5a2b"/>';
    b += '<rect x="' + (x0 + 1 * S) + '" y="' + (y0 + 5.5 * S) + '" width="' + 36 * S + '" height="' + 24 * S + '" fill="#f3d9a8"/>';
    b += '<rect x="' + (x0 + 39 * S) + '" y="' + (y0 + 5.5 * S) + '" width="' + 36 * S + '" height="' + 24 * S + '" fill="#f3d9a8" opacity=".6"/>';
    for (var k = 0; k < 16; k++) { var x = x0 + (k * 4.75 + 1.0) * S; b += '<rect x="' + x + '" y="' + (y0 + 1 * S) + '" width="' + 2.8 * S + '" height="' + 2 * S + '" rx="3" fill="#fff"/><rect x="' + x + '" y="' + (y0 + 32 * S) + '" width="' + 2.8 * S + '" height="' + 2 * S + '" rx="3" fill="' + (k < 8 ? "#2b6cb0" : "#fff") + '"/>'; }
    b += '<text x="' + (x0 + 19 * S) + '" y="' + (y0 + 19 * S) + '" font-size="22" font-weight="700" text-anchor="middle" fill="#2D2A26">36 × 24 mm</text>';
    b += '<path d="M' + (x0 + 1 * S) + ',' + (y0 - 14) + ' h' + 38 * S + '" stroke="#2D2A26" stroke-width="2"/><path d="M' + (x0 + 1 * S) + ',' + (y0 - 20) + ' v12 M' + (x0 + 39 * S) + ',' + (y0 - 20) + ' v12" stroke="#2D2A26" stroke-width="2"/>';
    b += '<text x="' + (x0 + 20 * S) + '" y="' + (y0 - 22) + '" font-size="15" font-weight="700" text-anchor="middle" fill="#2D2A26">one picture + its 2 mm gap = 38 mm</text>';
    b += '<text x="' + x0 + '" y="' + (y0 + 35 * S + 30) + '" font-size="16" font-weight="700" fill="#2b6cb0">8 blue holes × 4.75 mm = 38.00 mm</text>';
    b += '<text x="' + x0 + '" y="' + (y0 + 35 * S + 52) + '" font-size="14" fill="#625C53">the same at the start of the roll and at the end: the film carries its own ruler</text>';
    return svgFig(620, 370, "A strip of 35 mm film. Each picture is 36 by 24 mm with a 2 mm gap after it: 38 mm. Eight holes, 4.75 mm apart, are exactly 38 mm.", b);
  });
  reg("fig", "fig_l06_path", function () {
    var b = '<rect width="620" height="260" fill="#fff"/>';
    b += '<rect x="30" y="70" width="90" height="120" rx="16" fill="#3b3f44"/><text x="75" y="215" font-size="14" font-weight="600" text-anchor="middle" fill="#2D2A26">film\'s shell</text><circle cx="75" cy="40" r="26" fill="#2f9e57"/><text x="75" y="45" font-size="12" text-anchor="middle" fill="#fff" font-weight="700">green</text>';
    b += '<rect x="120" y="110" width="380" height="40" fill="#8a5a2b"/><rect x="250" y="100" width="120" height="60" fill="none" stroke="#D9601A" stroke-width="3"/><text x="310" y="185" font-size="13" text-anchor="middle" fill="#A4460E" font-weight="600">picture</text>';
    b += '<circle cx="420" cy="88" r="22" fill="#2b6cb0"/><text x="420" y="58" font-size="13" text-anchor="middle" fill="#2b6cb0" font-weight="600">frame wheel</text>';
    b += '<circle cx="545" cy="130" r="48" fill="#7a5230"/><circle cx="545" cy="130" r="24" fill="#c62828"/><text x="545" y="215" font-size="14" font-weight="600" text-anchor="middle" fill="#2D2A26">red spool</text>';
    b += '<defs><marker id="a6" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10Z" fill="#2D2A26"/></marker></defs>';
    b += '<path d="M150,226 H500" stroke="#625C53" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#a6)"/><text x="325" y="252" font-size="13" text-anchor="middle" fill="#625C53">1. loading: the whole film wound OUT (about 25 turns for 24 pictures)</text>';
    b += '<path d="M500,30 H150" stroke="#2D2A26" stroke-width="3" marker-end="url(#a6)"/><text x="325" y="14" font-size="13" text-anchor="middle" fill="#2D2A26" font-weight="600">2. after each picture: green knob winds it BACK into the dark shell</text>';
    return svgFig(620, 260, "The film's path. Loading winds the whole film out of its shell onto the red spool. After each picture the green knob winds it back into the shell, past the gate, while the film's holes turn the blue frame wheel.", b);
  });
})();

/* Lesson 6's picture (hero_fig, and its card): the frame wheel's 8 teeth sit in the film's holes; one turn of the wheel is 8 holes, one picture. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#1E5AA8";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  C.fig("fig_l06_wheel", function () {
    var b = '<rect width="640" height="360" fill="#fff"/><rect x="8" y="222" width="624" height="110" rx="4" fill="#C98A3A" stroke="' + INK + '" stroke-width="3"/>';
    for (var k = -4; k <= 4; k++) { var x = 320 + k * 69; b += '<rect x="' + (x - 9) + '" y="230" width="18" height="16" rx="3" fill="#fff" stroke="' + INK + '" stroke-width="1.5"/><rect x="' + (x - 9) + '" y="308" width="18" height="16" rx="3" fill="#fff" stroke="' + INK + '" stroke-width="1.5"/>'; }
    b += '<rect x="44" y="254" width="552" height="46" fill="#F6E7C6" stroke="' + INK + '" stroke-width="2" stroke-dasharray="7 5"/>' + T(320, 285, "8 holes = one picture", 24, 800, INK, "middle");
    for (var i = 0; i < 8; i++) b += '<rect x="-8" y="62" width="16" height="28" rx="2" fill="' + COL + '" stroke="' + INK + '" stroke-width="2" transform="translate(320 150) rotate(' + (i * 45) + ')"/>';
    b += '<circle cx="320" cy="150" r="70" fill="' + COL + '" stroke="' + INK + '" stroke-width="3"/><path d="M320 96 L302 126 H313 V176 H327 V126 H338 Z" fill="#fff" stroke="' + INK + '" stroke-width="1.5"/>' +
      '<path d="M434 92 A122 122 0 0 1 442 196" fill="none" stroke="' + INK + '" stroke-width="3.5"/><path d="M442 196 l-12 -12 l15 -2 z" fill="' + INK + '"/>' +
      T(150, 120, "8 teeth", 28, 800, COL, "middle") + '<line x1="198" y1="112" x2="236" y2="118" stroke="' + INK + '" stroke-width="2.5"/>' +
      T(462, 150, "one turn", 26, 800, INK);
    return C.U.svg(640, 360, b, "The blue frame wheel has 8 teeth that sit in the holes along the film's edge. As the film moves, the wheel turns: one full turn is 8 holes, exactly one picture.");
  });
})();
