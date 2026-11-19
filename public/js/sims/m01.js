/* CURVE 35, maker lesson M1 "Designed for a printer": interactive pieces and figures.  Numbers: course/FACTS.md, build/slicecheck.json, build/tolerance.json, WEDGE.md, scad/one135.scad. */
(function () {
  "use strict";
  /* --- small helpers (this file stands alone) --- */
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === "text") e.textContent = attrs[k]; else if (k === "html") e.innerHTML = attrs[k]; else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]); else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function sv(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs || {}) e.setAttribute(k, attrs[k]); return e; }
  function css() {
    if (document.getElementById("mx-style")) return;
    var s = document.createElement("style"); s.id = "mx-style";
    s.textContent = [
      ".mx{font:400 15px/1.45 var(--sans,system-ui,sans-serif);color:var(--stage-ink,#2D2A26);--k:var(--mx-k,#0f8b8d)}",
      ".mx *{box-sizing:border-box}",
      ".mx-stage{background:#fff;border:2px solid #000;border-radius:14px;overflow:hidden;position:relative}",
      ".mx-stage svg,.mx-stage canvas{display:block;width:100%;height:auto;touch-action:none}",
      ".mx-row{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:flex-end;margin:14px 0 0}",
      ".mx-ctl{display:flex;flex-direction:column;gap:6px;min-width:220px;flex:1}",
      ".mx-ctl label{font-weight:600;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--stage-mute,#625C53)}",
      ".mx-ctl output{font-weight:600;color:var(--stage-ink,#2D2A26);text-transform:none;letter-spacing:0;font-size:14px}",
      ".mx input[type=range]{width:100%;accent-color:var(--lc,var(--k))}",
      ".mx input[type=range]:disabled{opacity:.35}",
      ".mx-btn{font:600 15px/1 var(--sans,system-ui,sans-serif);border:1.5px solid #6b6356;background:var(--stage-2,#fff);color:var(--stage-ink,#2D2A26);border-radius:12px;padding:12px 16px;cursor:pointer}",
      ".mx-btn:hover{border-color:var(--lc,var(--k))}",
      ".mx-btn.go{background:var(--lc,var(--k));border-color:var(--lc,var(--k));color:var(--lc-on,#fff)}",
      ".mx-btn:disabled{opacity:.45;cursor:default}",
      ".mx-seg{display:inline-flex;flex-wrap:wrap;gap:6px}",
      ".mx-seg button{font:600 13.5px/1 var(--sans,system-ui,sans-serif);border:1.5px solid #6b6356;border-radius:10px;background:var(--stage-2,#fff);color:var(--stage-ink,#2D2A26);padding:10px 12px;cursor:pointer}",
      ".mx-seg button:hover{border-color:var(--lc,var(--k))}",
      ".mx-seg button[aria-pressed=true]{background:var(--lc,var(--k));border-color:var(--lc,var(--k));color:var(--lc-on,#fff)}",
      ".mx-read{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:8px;margin:14px 0 0}",
      ".mx-chip{background:var(--stage-2,#EFEBE3);border:1.5px solid #3a352d;border-radius:12px;padding:9px 12px;color:var(--stage-ink,#2D2A26)}",
      ".mx-chip b{display:block;font-size:22px;line-height:1.15;font-variant-numeric:lining-nums tabular-nums}",
      ".mx-chip span{font-size:11.5px;color:var(--stage-mute,#625C53);text-transform:uppercase;letter-spacing:.05em}",
      ".mx-chip.bad{background:#5a1f17;border-color:#e2553f}.mx-chip.good{background:#173d26;border-color:#3fbf6a}",
      ".mx-chip.bad span,.mx-chip.good span{color:#e8e1d4}.mx-chip.bad b,.mx-chip.good b{color:#fff}",
      ".mx-say{margin:12px 0 0;font-size:15px;line-height:1.5;min-height:1.5em;color:var(--stage-ink,#2D2A26);border-top:1px solid #3a352d;padding-top:12px}",
      ".mx-tag{position:absolute;right:10px;top:8px;font:600 11px/1 var(--sans,system-ui,sans-serif);letter-spacing:.06em;text-transform:uppercase;background:#1b1a18;color:#fff;padding:5px 8px;border-radius:6px}",
      ".mx svg text{font-family:var(--sans,system-ui,sans-serif)}"
    ].join("\n");
    document.head.appendChild(s);
  }
  function root(host, colour) { css(); var r = el("div", { "class": "mx" }); r.style.setProperty("--mx-k", colour || "#0f8b8d"); host.appendChild(r); return r; }
  function slider(o) {   // {label, min, max, step, value, fmt, on}
    var out = el("output"), inp = el("input", { type: "range", min: o.min, max: o.max, step: o.step, value: o.value });
    var id = "mx" + Math.random().toString(36).slice(2, 8); inp.id = id;
    var lab = el("label", { "for": id }, [o.label + " ", out]);
    function upd() { var v = +inp.value; out.textContent = o.fmt ? o.fmt(v) : v; inp.setAttribute("aria-valuetext", out.textContent); o.on && o.on(v); }
    inp.addEventListener("input", upd);
    var box = el("div", { "class": "mx-ctl" }, [lab, inp]); box.input = inp; box.set = function (v) { inp.value = v; upd(); }; box.init = upd; return box;
  }
  function seg(label, items, value, on) {   // items: [{v, t}]
    var g = el("div", { "class": "mx-seg", role: "group", "aria-label": label }), bs = [];
    items.forEach(function (it) {
      var b = el("button", { type: "button", "aria-pressed": String(it.v === value), text: it.t, onclick: function () { pick(it.v); } });
      b._v = it.v; bs.push(b); g.appendChild(b);
    });
    function pick(v) { bs.forEach(function (b) { b.setAttribute("aria-pressed", String(b._v === v)); }); on(v); }
    g.pick = pick; return g;
  }
  function chip(label) { var b = el("b"), c = el("div", { "class": "mx-chip" }, [b, el("span", { text: label })]); c.val = function (t, cls) { b.textContent = t; c.className = "mx-chip" + (cls ? " " + cls : ""); }; return c; }
  function say(r) { var p = el("p", { "class": "mx-say", "aria-live": "polite" }); r.appendChild(p); return p; }
  function onVis(api, fn) { var done = false; function go(on) { if (on === false || done) return; done = true; fn(); } if (api && api.onVisible) { api.onVisible(go); setTimeout(function () { go(true); }, 1500); } else go(true); }
  function reg(kind, name, fn) {
    var C = window.CURVE = window.CURVE || {};
    if (typeof C[kind] === "function") C[kind](name, fn);
    else { (C["_" + kind + "Queue"] = C["_" + kind + "Queue"] || []).push([name, fn]); }
  }
  function svgFig(w, h, title, body) { return '<svg viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + title.replace(/"/g, "&quot;") + '" xmlns="http://www.w3.org/2000/svg" width="100%" style="font-family:var(--sans,system-ui,sans-serif)">' + body + "</svg>"; }
  function fmtFrac(s) { return "1/" + Math.round(1 / s); }
  /* --- end helpers --- */


  /* ================= M1: designed for a printer ================= */
  var LAYER = 0.2, LINE = 0.45;   // mm
  var PRN = [{ e: -0.15, t: "far too thin" }, { e: -0.08, t: "thin" }, { e: 0, t: "as drawn" }, { e: 0.10, t: "typical" }, { e: 0.15, t: "fat" }, { e: 0.25, t: "far too fat" }];

  reg("sim", "m01_slice", function (host, api) {
    var K = (api && api.colour) || "#2f855a";
    var r = root(host, K), st = { shape: "ledge", ang: 40, span: 10, layer: 30 };
    var cv = el("canvas", { width: 720, height: 420, role: "img" });
    r.appendChild(el("div", { "class": "mx-stage" }, [cv, el("div", { "class": "mx-tag", text: "printing simulated" })]));
    var sSeg = seg("Shape", [{ v: "ledge", t: "A slope" }, { v: "bridge", t: "A bridge" }], "ledge", function (v) { st.shape = v; aS.input.disabled = v !== "ledge"; bS.input.disabled = v !== "bridge"; draw(); });
    var aS = slider({ label: "Slope, from upright:", min: 0, max: 90, step: 1, value: 40, fmt: function (v) { return v + "°" + (v === 90 ? " (a flat shelf)" : ""); }, on: function (v) { st.ang = v; draw(); } });
    var bS = slider({ label: "Bridge span:", min: 2, max: 40, step: 1, value: 10, fmt: function (v) { return v + " mm" + (v === 10 ? " (about the front plate's foot pockets)" : ""); }, on: function (v) { st.span = v; draw(); } });
    var lS = slider({ label: "Layers printed:", min: 1, max: 30, step: 1, value: 30, fmt: function (v) { return v + " of 30 (" + (v * LAYER).toFixed(1) + " mm)"; }, on: function (v) { st.layer = v; draw(); } });
    bS.input.disabled = true;
    r.appendChild(el("div", { "class": "mx-row" }, [sSeg]));
    r.appendChild(el("div", { "class": "mx-row" }, [aS, bS]));
    r.appendChild(el("div", { "class": "mx-row" }, [lS]));
    var cA = chip("each layer leans out"), cS = chip("of each new line rests on the last"), cV = chip("verdict");
    r.appendChild(el("div", { "class": "mx-read" }, [cA, cS, cV]));
    var out = say(r);
    function bead(c, x, y, w, h, col) { c.fillStyle = col; c.beginPath(); var rr = h / 2; c.moveTo(x + rr, y); c.lineTo(x + w - rr, y); c.arc(x + w - rr, y + rr, rr, -Math.PI / 2, Math.PI / 2); c.lineTo(x + rr, y + h); c.arc(x + rr, y + rr, rr, Math.PI / 2, Math.PI * 1.5); c.fill(); c.strokeStyle = "rgba(0,0,0,.25)"; c.lineWidth = 1; c.stroke(); }
    function draw() {
      var c = cv.getContext("2d"), W = 720, H = 420, base = 380;
      c.fillStyle = "#fbfaf7"; c.fillRect(0, 0, W, H);
      c.fillStyle = "#9aa3ab"; c.fillRect(0, base, W, H - base); c.fillStyle = "#2D2A26"; c.font = "600 13px system-ui,sans-serif"; c.fillText("printer bed", 12, base + 26);
      if (st.shape === "ledge") {
        var S = 50, lh = LAYER * S, lw = LINE * S, x0 = 160;   // 50 px per mm
        var shift = LAYER * Math.tan(st.ang * Math.PI / 180), sup = Math.max(0, 1 - shift / LINE), off = 0, sag = 0;
        for (var i = 0; i < st.layer; i++) {
          var y = base - (i + 1) * lh;
          for (var k = 0; k < 4; k++) bead(c, x0 + k * lw, y, lw, lh, "#5c8f6e");   // the upright wall: 4 lines
          var ox = x0 + 4 * lw + Math.min(off, 400) * S;
          if (i > 0) { off += shift; if (sup < 0.5) sag += (0.5 - sup) * lh * 1.4; }
          var col = sup >= 0.5 ? K : sup > 0 ? "#e08a2c" : "#c62828";
          var ex = x0 + 4 * lw + off * S;
          // fill between wall and the outer line
          var inner = x0 + 4 * lw; if (ex - inner > 0) bead(c, inner, y + Math.min(sag, 120) * 0.4, ex - inner, lh, "#7fae8f");
          bead(c, ex, y + Math.min(sag, 160), lw, lh, i === 0 ? "#5c8f6e" : col);
          if (ex + lw > W - 10) break;
        }
        // nozzle
        var ny = base - st.layer * lh - 4, nx = x0 + 4 * lw + off * S + lw / 2;
        c.fillStyle = "#555"; c.beginPath(); c.moveTo(nx - 10, ny - 40); c.lineTo(nx + 10, ny - 40); c.lineTo(nx + 3, ny); c.lineTo(nx - 3, ny); c.fill();
        c.fillStyle = "#2D2A26"; c.font = "600 14px system-ui,sans-serif";
        c.fillText("each line 0.45 mm wide, each layer 0.2 mm tall (drawn 50× life size)", 12, 24);
        // angle guide
        c.strokeStyle = "rgba(45,42,38,.5)"; c.setLineDash([5, 4]); c.beginPath(); c.moveTo(x0 + 4 * lw + lw, base - lh); c.lineTo(x0 + 4 * lw + lw + Math.tan(45 * Math.PI / 180) * 300, base - lh - 300); c.stroke(); c.setLineDash([]);
        c.fillText("45°", x0 + 4 * lw + lw + 210, base - lh - 220);
        cA.val((shift).toFixed(2) + " mm"); cS.val(Math.round(sup * 100) + "%", sup >= 0.5 ? "good" : "bad");
        var v = sup >= 0.5 ? "prints" : sup > 0 ? "droops" : "falls on air";
        cV.val(v, sup >= 0.5 ? "good" : "bad");
        out.textContent = "At " + st.ang + "° from upright each layer leans out " + shift.toFixed(2) + " mm, so " + Math.round(sup * 100) + "% of each new 0.45 mm line sits on the one below: it " + v + "." +
          (st.ang > 45 && st.ang < 50 ? " Right on the edge: the camera keeps to 45° or less." : "");
      } else {
        var S2 = 12, sp = st.span, px0 = 360 - sp * S2 / 2, px1 = 360 + sp * S2 / 2, ph = 200;
        c.fillStyle = "#5c8f6e"; c.fillRect(px0 - 80, base - ph, 80, ph); c.fillRect(px1, base - ph, 80, ph);
        var sagmm = Math.min(3, 0.004 * sp * sp), sagpx = sagmm * S2 * (st.layer / 30);
        c.strokeStyle = sp <= 12 ? K : sp <= 25 ? "#e08a2c" : "#c62828"; c.lineWidth = 9; c.lineCap = "round";
        c.beginPath(); c.moveTo(px0 - 4, base - ph - 4); c.quadraticCurveTo(360, base - ph - 4 + 2 * sagpx, px1 + 4, base - ph - 4); c.stroke();
        c.fillStyle = "#2D2A26"; c.font = "600 14px system-ui,sans-serif";
        c.fillText("a line stretched between two posts, like a rope (drawn 12× life size)", 12, 24);
        c.fillText(sp + " mm", 360 - 20, base - ph + 40);
        c.font = "400 12px system-ui,sans-serif"; c.fillText("sag drawn to show the trend, not measured", 12, 46);
        var ok = sp <= 12;
        cA.val(sp + " mm"); cA.querySelector("span").textContent = "span over air";
        cS.val(sagmm < 0.1 ? "a hair" : sagmm.toFixed(1) + " mm"); cS.querySelector("span").textContent = "sag (trend)";
        cV.val(ok ? "short: fine" : sp <= 25 ? "saggy" : "a mess", ok ? "good" : "bad");
        out.textContent = "A bridge of " + sp + " mm: " + (ok ? "short, so the hot line stays taut and the layers above can sit on it. The pockets for the front plate's feet are roofed by bridges about 10.6 mm long, and the parts print with the fan on so each line sets before it can sag." : "the longer the span, the more the line sags before it cools. Keep bridges short.");
      }
      cv.setAttribute("aria-label", out.textContent);
    }
    aS.init(); lS.init(); draw();
    return { destroy: function () {} };
  });

  /* ---- fat printers, thin printers: three gaps, the fit gauge, and the wedge rule (build/tolerance.json, WEDGE.md, scad FIT) ---- */
  reg("sim", "m01_fit", function (host, api) {
    var K = (api && api.colour) || "#7C8A1A";
    var r = root(host, K), st = { e: 0.10, fit: 0.65, view: "gaps" };
    var W = 720, H = 360, s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img" });
    s.appendChild(sv("rect", { width: W, height: H, fill: "#fff" }));
    var g = sv("g", {}); s.appendChild(g);
    var vSeg = seg("What to look at", [{ v: "gaps", t: "Gaps and the fit gauge" }, { v: "joints", t: "Three ways to join two parts" }], "gaps", function (v) { st.view = v; fS.style.display = v === "gaps" ? "" : "none"; draw(); });
    r.appendChild(el("div", { "class": "mx-row", style: "margin:0 0 12px" }, [vSeg]));
    r.appendChild(el("div", { "class": "mx-stage" }, [s]));
    var eS = slider({ label: "Your printer: every wall comes out", min: -0.15, max: 0.25, step: 0.01, value: 0.10, fmt: function (v) { var p = PRN.filter(function (x) { return Math.abs(x.e - v) < 0.005; })[0]; return (v > 0 ? v.toFixed(2) + " mm fat" : v < 0 ? (-v).toFixed(2) + " mm thin" : "exactly as drawn") + (p ? " (" + p.t + ")" : ""); }, on: function (v) { st.e = v; if (pSeg) pSeg.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", String(Math.abs(b._v - v) < 0.005)); }); draw(); } });
    var pSeg = null, fS = slider({ label: "FIT in one135.scad (room round each knob):", min: 0.2, max: 1.0, step: 0.05, value: 0.65, fmt: function (v) { return v.toFixed(2) + " mm" + (Math.abs(v - 0.65) < 0.001 ? " (as shipped)" : ""); }, on: function (v) { st.fit = v; draw(); } });
    pSeg = seg("The five printers in the model", PRN.map(function (p) { return { v: p.e, t: (p.e > 0 ? "+" : p.e < 0 ? "−" : "±") + Math.abs(p.e).toFixed(2) }; }), 0.10, function (v) { eS.set(v); });
    r.appendChild(el("div", { "class": "mx-row" }, [eS, fS]));
    r.appendChild(el("div", { "class": "mx-row" }, [el("div", { "class": "mx-ctl" }, [el("label", { text: "Jump to a printer the model checked" }), pSeg])]));
    var c1 = chip(""), c2 = chip(""), c3 = chip("");
    r.appendChild(el("div", { "class": "mx-read" }, [c1, c2, c3]));
    var out = say(r);
    function T(x, y, t, a, c, sz, w) { var e = sv("text", { x: x, y: y, "text-anchor": a || "middle", fill: c || "#2D2A26", "font-size": sz || 13, "font-weight": w || 600 }); e.textContent = t; g.appendChild(e); return e; }
    function lab(c, t) { c.querySelector("span").textContent = t; }
    function ring(cx, cy, gap, title, sub) {   // a shaft in a bore; the gap drawn 60x
      var R = 60, gpx = gap * 60;
      g.appendChild(sv("circle", { cx: cx, cy: cy, r: R + 28, fill: "#2a2d31" }));
      g.appendChild(sv("circle", { cx: cx, cy: cy, r: R, fill: "#fff" }));
      g.appendChild(sv("circle", { cx: cx, cy: cy, r: Math.min(R + 10, R - gpx), fill: gap <= 0 ? "#c62828" : "#2f9e57", opacity: gap <= 0 ? 0.85 : 1 }));
      if (gap <= 0) g.appendChild(sv("circle", { cx: cx, cy: cy, r: R, fill: "none", stroke: "#fff", "stroke-width": 2, "stroke-dasharray": "5 4" }));
      T(cx, cy - R - 40, title, "middle", "#2D2A26", 14, 700);
      T(cx, cy + 6, gap <= 0 ? "BINDS" : "", "middle", "#fff", 18, 700);
      T(cx, cy + R + 50, gap <= 0 ? "no room" : gap.toFixed(2) + " mm all round", "middle", gap <= 0 ? "#c62828" : "#1d6b35", 14, 700);
      T(cx, cy + R + 68, sub, "middle", "#625C53", 12, 400);
    }
    function gaps() {
      var e = st.e, knob = st.fit - 2 * e, mach = 0.2 - 2 * e;
      ring(110, 130, knob, "knob in its slot", "drawn: FIT = " + st.fit.toFixed(2) + " mm");
      ring(300, 130, mach, "a machinist's fit", "drawn: 0.20 mm");
      var gx = 440, gy = 60, key = 3.0 + 2 * e, best = null;
      T(570, 30, "fit gauge: a 3.0 mm key, slots a tenth apart", "middle", "#2D2A26", 14, 700);
      for (var N = -3; N <= 8; N++) {
        var drawn = 3.0 + 0.1 * N, printed = drawn - 2 * e, x = gx + (N + 3) * 22, fits = key <= printed + 1e-9;
        if (fits && best === null) best = N;
        var hpx = Math.max(2, printed * 24);
        g.appendChild(sv("rect", { x: x, y: gy + 20, width: 18, height: 200, fill: "#2a2d31" }));
        g.appendChild(sv("rect", { x: x + 3, y: gy + 20 + (200 - hpx) / 2, width: 12, height: hpx, fill: fits ? "#dff3e4" : "#fde2dc" }));
        T(x + 9, gy + 240, String(N), "middle", "#2D2A26", 12, 600);
        T(x + 9, gy + 256, drawn.toFixed(1), "middle", "#625C53", 10, 400);
      }
      var kh = key * 24, bx = best === null ? null : gx + (best + 3) * 22;
      g.appendChild(sv("rect", { x: gx - 36, y: gy + 20 + (200 - kh) / 2, width: 24, height: kh, fill: K, rx: 3 }));
      T(gx - 24, gy + 290, "key " + key.toFixed(2), "middle", K, 12, 700);
      if (bx !== null) g.appendChild(sv("path", { d: "M" + (bx + 10) + "," + (gy + 4) + " l-7,-12 h14Z", fill: "#D9601A" }));
      T(590, gy + 290, "slot number; width as drawn (mm)", "middle", "#625C53", 12, 400);
      T(110, 330, "gaps drawn 60× bigger", "middle", "#625C53", 11, 400);
      lab(c1, "knob: room left all round"); lab(c2, "the 0.2 mm machinist's fit"); lab(c3, "gauge: narrowest slot the key enters");
      c1.val(knob <= 0 ? "binds" : knob.toFixed(2) + " mm", knob <= 0 ? "bad" : "good");
      c2.val(mach <= 0 ? "binds" : mach.toFixed(2) + " mm", mach <= 0 ? "bad" : "good");
      c3.val(best === null ? "none" : "slot " + best + " → " + (best * 0.025 >= 0 ? "+" : "") + (best * 0.025).toFixed(3) + " mm");
      var worst = st.fit - 0.5;
      out.textContent = "Walls " + (e >= 0 ? e.toFixed(2) + " mm fat" : (-e).toFixed(2) + " mm thin") + ": every gap loses twice that. The knob keeps " + (knob <= 0 ? "nothing: it binds." : knob.toFixed(2) + " mm.") +
        " The 0.2 mm fit " + (mach <= 0 ? "binds solid." : "keeps " + mach.toFixed(2) + " mm.") + " The key prints " + key.toFixed(2) + " mm and first drops into slot " + best + ": " + best + " × 0.025 = " + (best * 0.025).toFixed(3) + " mm, your printer's number." +
        (Math.abs(st.fit - 0.65) > 0.001 ? " With FIT = " + st.fit.toFixed(2) + ", the fattest printer the model checks (+0.25) " + (worst <= 0 ? "binds the knobs." : "still leaves " + worst.toFixed(2) + " mm.") : "");
    }
    var M = 40;
    function joints() {
      var e = st.e;
      var cx = 120, base = 250, hole = 3.3 - 2 * e, peg = 3.0 + 2 * e, gap = (hole - peg) / 2;   // a stepped peg drawn 0.15 mm loose a side
      g.appendChild(sv("rect", { x: cx - 100, y: base - 100, width: 200, height: 100, fill: "#2a2d31" }));
      g.appendChild(sv("rect", { x: cx - hole / 2 * M, y: base - 100, width: hole * M, height: 100, fill: "#fff" }));
      var pegTop = gap < 0 ? base - 200 : base - 110;
      g.appendChild(sv("rect", { x: cx - peg / 2 * M, y: pegTop, width: peg * M, height: 130, fill: gap < 0 ? "#c62828" : K, rx: 3 }));
      T(cx, 34, "STEP: needs the printer", "middle", "#2D2A26", 14, 700);
      T(cx, base + 28, gap < 0 ? "won't go in" : gap > 0.25 ? "rattles: " + gap.toFixed(2) + " mm a side" : "fits: " + gap.toFixed(2) + " mm a side", "middle", gap < 0 || gap > 0.25 ? "#c62828" : "#1d6b35", 13, 700);
      var wx = 360, a = 43 * Math.PI / 180, dh = 2 * e / Math.sin(a), top = base - 100, ww = 70;   // a 43-degree wedge: its seat moves 2e / sin(43)
      g.appendChild(sv("path", { d: "M" + (wx - 110) + "," + top + " H" + (wx - ww) + " L" + wx + "," + (top + ww / Math.tan(a)) + " L" + (wx + ww) + "," + top + " H" + (wx + 110) + " V" + base + " H" + (wx - 110) + "Z", fill: "#2a2d31" }));
      var sy = top - 40 - dh * M * 0.5;
      g.appendChild(sv("path", { d: "M" + (wx - ww) + "," + sy + " L" + wx + "," + (sy + ww / Math.tan(a)) + " L" + (wx + ww) + "," + sy + " V" + (sy - 70) + " H" + (wx - ww) + "Z", fill: K, transform: "translate(0 40)" }));
      T(wx, 34, "WEDGE: finds its own fit", "middle", "#2D2A26", 14, 700);
      T(wx, base + 28, "always snug; sits " + (dh >= 0 ? dh.toFixed(2) + " mm higher" : (-dh).toFixed(2) + " mm lower"), "middle", "#1d6b35", 13, 700);
      var fx = 600;
      g.appendChild(sv("rect", { x: fx - 100, y: top, width: 200, height: 100, fill: "#2a2d31" }));
      g.appendChild(sv("rect", { x: fx - 60 - e * M, y: top - 60, width: 120 + 2 * e * M, height: 60, fill: K, rx: 3 }));
      g.appendChild(sv("line", { x1: fx - 110, y1: top, x2: fx + 110, y2: top, stroke: "#D9601A", "stroke-width": 3 }));
      T(fx, 34, "FLAT FACE: exact", "middle", "#2D2A26", 14, 700);
      T(fx, base + 28, "set by layers: unchanged", "middle", "#1d6b35", 13, 700);
      T(fx, top - 70, "wider or narrower, it rests on the same layer", "middle", "#625C53", 11, 400);
      T(360, H - 30, "A flat face where the position must be exact. A wedge everywhere else.", "middle", "#2D2A26", 15, 700);
      lab(c1, "stepped peg in a hole"); lab(c2, "wedge (the plate's 43° hooks)"); lab(c3, "flat face (the lens seat)");
      c1.val(gap < 0 ? "binds" : gap > 0.25 ? "rattles" : "fits", gap < 0 || gap > 0.25 ? "bad" : "good");
      c2.val((dh >= 0 ? "+" : "") + dh.toFixed(2) + " mm", "good"); c3.val("0.00 mm", "good");
      out.textContent = "Walls " + (e >= 0 ? e.toFixed(2) + " mm fat" : (-e).toFixed(2) + " mm thin") + ". A peg drawn 0.15 mm loose a side " + (gap < 0 ? "jams." : gap > 0.25 ? "rattles." : "fits.") + " The 43° wedge stays snug and only sits " + Math.abs(dh).toFixed(2) + " mm " + (dh >= 0 ? "higher" : "lower") + ". The flat face does not move at all: up and down, a printer counts whole layers.";
    }
    function draw() {
      while (g.firstChild) g.removeChild(g.firstChild);
      if (st.view === "gaps") gaps(); else joints();
      s.setAttribute("aria-label", out.textContent);
    }
    fS.init(); eS.init();
    return { destroy: function () {} };
  });

  /* ---- figures ---- */
  reg("fig", "fig_m01_layers", function () {
    var S = 90, lw = LINE * S, lh = LAYER * S, b = '<rect width="620" height="300" fill="#fff"/>', x0 = 120, base = 250;
    for (var i = 0; i < 5; i++) for (var k = 0; k < 3; k++) { var x = x0 + k * lw + i * LAYER * S, y = base - (i + 1) * lh; b += '<rect x="' + x + '" y="' + y + '" width="' + lw + '" height="' + lh + '" rx="' + lh / 2 + '" fill="' + (k === 2 ? "#2f855a" : "#7fae8f") + '" stroke="#fff"/>'; }
    b += '<line x1="' + (x0 + 3 * lw) + '" y1="' + base + '" x2="' + (x0 + 3 * lw + 5 * LAYER * S) + '" y2="' + (base - 5 * lh) + '" stroke="#D9601A" stroke-width="2.5" stroke-dasharray="6 4"/>';
    b += '<text x="' + (x0 + 3 * lw + 60) + '" y="' + (base - 40) + '" font-size="15" font-weight="700" fill="#A4460E">45°: each layer steps out 0.2 mm</text>';
    b += '<text x="' + (x0 + 3 * lw + 60) + '" y="' + (base - 18) + '" font-size="13" fill="#625C53">each line rests over half on the one below</text>';
    b += '<text x="20" y="34" font-size="15" font-weight="700" fill="#2D2A26">lines 0.45 mm wide · layers 0.2 mm tall (drawn 90× life size)</text>';
    b += '<rect x="0" y="' + base + '" width="620" height="50" fill="#9aa3ab"/>';
    return svgFig(620, 300, "Lines of plastic 0.45 mm wide stacked in layers 0.2 mm tall. Leaning out at 45 degrees, each layer steps out 0.2 mm, so each new line still rests more than half on the line below.", b);
  });
  reg("fig", "fig_m01_grain", function () {
    var b = '<rect width="620" height="280" fill="#fff"/>';
    b += '<g transform="translate(40 60)">';
    for (var i = 0; i < 6; i++) b += '<rect x="0" y="' + i * 12 + '" width="220" height="12" rx="6" fill="#7fae8f" stroke="#fff"/>';
    b += '<path d="M240,36 q30,-50 60,0" fill="none" stroke="#2f855a" stroke-width="4"/><text x="0" y="110" font-size="15" font-weight="700" fill="#2f855a">bend ALONG the lines: springs back</text><text x="0" y="130" font-size="13" fill="#625C53">about 30 MPa before it gives (the model)</text></g>';
    b += '<g transform="translate(360 30)">';
    for (var j = 0; j < 10; j++) b += '<rect x="0" y="' + j * 12 + '" width="60" height="12" rx="6" fill="#7fae8f" stroke="#fff"/>';
    b += '<path d="M-6,66 h72" stroke="#c62828" stroke-width="3" stroke-dasharray="4 3"/><text x="80" y="70" font-size="14" font-weight="700" fill="#c62828">snaps here</text>';
    b += '<text x="0" y="160" font-size="15" font-weight="700" fill="#c62828">bend ACROSS the layers</text><text x="0" y="180" font-size="13" fill="#625C53">about 15 MPa: half</text></g>';
    b += '<text x="40" y="270" font-size="14" font-weight="600" fill="#2D2A26">So every spring in the camera is printed lying flat, bending along its layers.</text>';
    return svgFig(620, 280, "A printed part has a grain like wood. Bent along its lines it springs back, about 30 megapascals in the model. Bent across its layers it splits along a layer line at about 15. So every spring in the camera bends along its layers.", b);
  });
  reg("fig", "fig_m01_gauge", function () {
    var b = '<rect width="620" height="260" fill="#fff"/>', x0 = 120;
    for (var N = -3; N <= 8; N++) { var w = (3 + 0.1 * N) * 12, x = x0 + (N + 3) * 38; b += '<rect x="' + x + '" y="60" width="34" height="130" fill="#2a2d31"/><rect x="' + (x + 17 - w / 2 * 0.4) + '" y="' + (125 - w) + '" width="' + w * 0.4 + '" height="' + 2 * w + '" fill="#fff"/><text x="' + (x + 17) + '" y="212" font-size="12" text-anchor="middle" fill="#2D2A26">' + N + '</text>'; }
    b += '<rect x="40" y="89" width="40" height="72" rx="4" fill="#2f855a"/><text x="60" y="182" font-size="12" text-anchor="middle" fill="#2f855a" font-weight="700">key 3.0</text>';
    b += '<text x="20" y="34" font-size="15" font-weight="700" fill="#2D2A26">Slots 2.7 to 3.8 mm, a tenth apart. The narrowest the key enters is N.</text>';
    b += '<text x="20" y="245" font-size="15" font-weight="700" fill="#A4460E">your printer\'s walls are about 0.025 × N mm too fat</text>';
    return svgFig(620, 260, "The fit gauge: a 3.0 mm key and twelve slots from 2.7 to 3.8 mm, a tenth apart. The narrowest slot the key enters, N, says the printer's walls are about 0.025 times N millimetres too fat.", b);
  });
})();
