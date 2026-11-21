/* CURVE 35, lesson 07: interactive pieces and figures. Numbers from course/FACTS.md and build/*.json (model ONE-135 v2.14). */
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

  /* ================= lesson 7: keeping the dark in ================= */
  // Joint drawn at 60 px per mm: gap 0.6 mm (36 px), the back's ridge reaching 1.9 mm (114 px) past the body's edge (WEDGE.md, build/aimleak.json)
  var GEO = {
    straight: { name: "a straight gap", walls: [[120, 100, 600, 100], [120, 136, 600, 136]], inside: function (x, y) { return x >= 600; } },
    corner: { name: "one corner", walls: [[120, 100, 400, 100], [400, 100, 400, 390], [120, 136, 364, 136], [364, 136, 364, 390]], inside: function (x, y) { return y >= 388; } },
    joint: { name: "the camera's back joint", walls: [[120, 100, 296, 100], [296, 100, 296, 250], [296, 250, 368, 250], [368, 250, 368, 100], [368, 100, 600, 100],
      [120, 136, 260, 136], [260, 136, 260, 286], [260, 286, 404, 286], [404, 286, 404, 136], [404, 136, 600, 136]], inside: function (x, y) { return x >= 600; } }
  };
  Object.keys(GEO).forEach(function (k) { GEO[k].walls.push([120, 0, 120, 100], [120, 136, 120, 400]); });
  var SOLIDS = {   // filled shapes for drawing: back (light grey in pictures) above, body (near black) below
    straight: { back: [[0, 0, 720, 100]], body: [[120, 136, 600, 264]] },
    corner: { back: [[0, 0, 720, 100], [400, 100, 320, 300]], body: [[120, 136, 244, 264]] },
    joint: { back: [[0, 0, 720, 100], [296, 100, 72, 150]], body: [[120, 136, 140, 264], [260, 286, 144, 114], [404, 136, 196, 264]] }
  };
  function hit(ox, oy, dx, dy, w) {   // ray o + t d against segment w; returns t or Infinity
    var ex = w[2] - w[0], ey = w[3] - w[1], den = dx * ey - dy * ex; if (Math.abs(den) < 1e-9) return Infinity;
    var t = ((w[0] - ox) * ey - (w[1] - oy) * ex) / den, u = ((w[0] - ox) * dy - (w[1] - oy) * dx) / den;
    return t > 1e-6 && u >= 0 && u <= 1 ? t : Infinity;
  }
  function trace(geo, ox, oy, dx, dy, refl, matte, maxB) {
    var pts = [[ox, oy]], p = 1, n = 0, G = GEO[geo];
    for (var guard = 0; guard < 40; guard++) {
      var best = Infinity, bw = null;
      G.walls.forEach(function (w) { var t = hit(ox, oy, dx, dy, w); if (t < best) { best = t; bw = w; } });
      // the ray leaves the drawing: did it reach the film side?
      var tOut = Infinity, ex = ox + dx * 2000, ey = oy + dy * 2000;
      if (best === Infinity) { pts.push([ex, ey]); return { pts: pts, p: G.inside(ex, ey) ? p : 0, n: n, out: G.inside(ex, ey) }; }
      var hx = ox + dx * best, hy = oy + dy * best;
      if (G.inside(hx, hy) || (geo !== "corner" && hx >= 600)) { pts.push([hx, hy]); return { pts: pts, p: p, n: n, out: true }; }
      pts.push([hx, hy]);
      if (hx <= 120.5 && n > 0) return { pts: pts, p: 0, n: n, out: false };
      n++; p *= refl;
      if (p < 1e-5 || n > maxB) return { pts: pts, p: 0, n: n, out: false };
      var wx = bw[2] - bw[0], wy = bw[3] - bw[1], L = Math.hypot(wx, wy), nx = -wy / L, ny = wx / L;
      if (nx * dx + ny * dy > 0) { nx = -nx; ny = -ny; }
      if (matte) { var a = Math.asin(2 * Math.random() - 1), tx = -ny, ty = nx; dx = nx * Math.cos(a) + tx * Math.sin(a); dy = ny * Math.cos(a) + ty * Math.sin(a); }
      else { var dd = dx * nx + dy * ny; dx -= 2 * dd * nx; dy -= 2 * dd * ny; }
      ox = hx + nx * 0.01; oy = hy + ny * 0.01;
    }
    return { pts: pts, p: 0, n: n, out: false };
  }

  reg("sim", "l07_trap", function (host, api) {
    var K = (api && api.colour) || "#37474f";
    var r = root(host, K), st = { geo: "joint", refl: 0.3, matte: true, tx: 30, ty: 118, fan: true, seed: 0 };
    var cv = el("canvas", { width: 720, height: 400, role: "img", tabindex: 0, "aria-label": "A cut through a gap in the camera. Drag the torch on the left; rays bounce through the gap and lose light at each bounce." });
    cv.style.cursor = "grab";
    r.appendChild(el("div", { "class": "lx-stage" }, [cv, el("div", { "class": "lx-tag", text: "rays simulated" })]));
    var gSeg = seg("Gap", [{ v: "straight", t: "Straight gap" }, { v: "corner", t: "One corner" }, { v: "joint", t: "The back's joint" }], "joint", function (v) { st.geo = v; draw(); });
    var mSeg = seg("Surface", [{ v: true, t: "Matte: bounces every way" }, { v: false, t: "Mirror-smooth" }], true, function (v) { st.matte = v; draw(); });
    var fSeg = seg("Rays", [{ v: true, t: "A torch: 600 rays" }, { v: false, t: "One ray" }], true, function (v) { st.fan = v; draw(); });
    var rS = slider({ label: "Each bounce keeps:", min: 0.05, max: 0.95, step: 0.05, value: 0.3, fmt: function (v) { return v.toFixed(2) + (Math.abs(v - 0.3) < 0.01 ? " (the model's worst case for black)" : v > 0.7 ? " (white plastic)" : ""); }, on: function (v) { st.refl = v; draw(); } });
    r.appendChild(el("div", { "class": "lx-row" }, [gSeg]));
    r.appendChild(el("div", { "class": "lx-row" }, [mSeg, fSeg]));
    r.appendChild(el("div", { "class": "lx-row" }, [rS, el("button", { type: "button", "class": "lx-btn go", text: "Fire again", onclick: function () { draw(); } })]));
    var cA = chip("rays that reach the film"), cL = chip("light that reaches the film"), cB = chip("most bounces on the way");
    r.appendChild(el("div", { "class": "lx-read" }, [cA, cL, cB]));
    var out = say(r);
    function draw() {
      var c = cv.getContext("2d"), S = SOLIDS[st.geo];
      c.fillStyle = "#fffbe6"; c.fillRect(0, 0, 120, 400);   // daylight outside
      c.fillStyle = "#0e0f10"; c.fillRect(120, 0, 600, 400);
      S.back.forEach(function (b) { c.fillStyle = "#c9cdd1"; c.fillRect(b[0], b[1], b[2], b[3]); });
      S.body.forEach(function (b) { c.fillStyle = "#2a2d31"; c.fillRect(b[0], b[1], b[2], b[3]); });
      c.fillStyle = "#fffbe6"; c.fillRect(0, 0, 120, 400); c.fillStyle = "rgba(0,0,0,.5)"; c.fillRect(118, 0, 2, 100); c.fillRect(118, 136, 2, 264);
      // film side
      c.fillStyle = "rgba(255,255,255,.08)";
      if (st.geo === "corner") c.fillRect(364, 380, 36, 20); else c.fillRect(600, 100, 120, 36);
      c.font = "600 13px system-ui,sans-serif"; c.fillStyle = "#2D2A26"; c.fillText("back (light grey in pictures)", 430, 60);
      c.fillStyle = "#e8e8e8"; c.fillText(st.geo === "corner" ? "to the film ↓" : "to the film →", st.geo === "corner" ? 410 : 610, st.geo === "corner" ? 380 : 160);
      c.fillText("body", 520, 330);
      c.fillStyle = "#7a6a00"; c.fillText("daylight", 16, 390);
      c.fillStyle = "#e8e8e8"; c.font = "400 12px system-ui,sans-serif"; c.fillText("gap 0.6 mm", 140, 160);
      if (st.geo === "joint") c.fillText("ridge reaches 1.9 mm in", 300, 270);
      // torch
      var ax = 120, ay = 118, dx0 = ax - st.tx, dy0 = ay - st.ty, L0 = Math.hypot(dx0, dy0); dx0 /= L0; dy0 /= L0;
      c.save(); c.translate(st.tx, st.ty); c.rotate(Math.atan2(dy0, dx0)); c.fillStyle = "#D9601A"; c.fillRect(-26, -10, 30, 20); c.fillStyle = "#ffe680"; c.fillRect(2, -12, 8, 24); c.restore();
      var N = st.fan ? 600 : 1, arrived = 0, light = 0, maxB = 0, drawn = 0;
      for (var i = 0; i < N; i++) {
        var a = st.fan ? (i / (N - 1) - 0.5) * 0.5 : 0, ca = Math.cos(a), sa = Math.sin(a), dx = dx0 * ca - dy0 * sa, dy = dx0 * sa + dy0 * ca;
        var R = trace(st.geo, st.tx, st.ty, dx, dy, st.refl, st.matte, 12);
        if (R.out && R.p > 0) { arrived++; light += R.p; maxB = Math.max(maxB, R.n); }
        if (!st.fan || i % 6 === 0 || (R.out && R.p > 0)) {
          drawn++; var p = 1;
          for (var j = 1; j < R.pts.length; j++) {
            c.strokeStyle = "rgba(255,214,64," + Math.max(0.04, Math.min(1, p * (st.fan ? 0.5 : 1))).toFixed(3) + ")"; c.lineWidth = st.fan ? 1.2 : 3;
            c.beginPath(); c.moveTo(R.pts[j - 1][0], R.pts[j - 1][1]); c.lineTo(R.pts[j][0], R.pts[j][1]); c.stroke();
            if (!st.fan && j < R.pts.length - 1) { c.fillStyle = "#fff"; c.font = "600 12px system-ui,sans-serif"; p *= st.refl; c.fillText((p).toFixed(p < 0.01 ? 4 : 2), R.pts[j][0] + 5, R.pts[j][1] - 5); }
            else if (j < R.pts.length - 1) p *= st.refl;
          }
        }
      }
      var share = light / N;
      cA.val(arrived + " of " + N, arrived ? "" : "good");
      cL.val(share === 0 ? "none" : share >= 0.01 ? (share * 100).toFixed(1) + "%" : "1 part in " + Math.round(1 / share).toLocaleString("en"), share > 0.01 ? "bad" : "good");
      cB.val(arrived ? String(maxB) : "–");
      out.textContent = "Through " + GEO[st.geo].name + ", " + (st.matte ? "matte" : "mirror-smooth") + " walls keeping " + st.refl.toFixed(2) + " a bounce: " + arrived + " of " + N + " rays reach the film side, carrying " +
        (share === 0 ? "no light at all." : share >= 0.01 ? (share * 100).toFixed(1) + "% of the light." : "about 1 part in " + Math.round(1 / share).toLocaleString("en") + " of the light.") +
        (st.geo === "straight" ? " Line the torch up with the gap and light walks straight in." : "");
    }
    var dragging = false;
    function pos(e) { var b = cv.getBoundingClientRect(); st.tx = Math.max(15, Math.min(105, (e.clientX - b.left) / b.width * 720)); st.ty = Math.max(15, Math.min(385, (e.clientY - b.top) / b.height * 400)); draw(); }
    cv.addEventListener("pointerdown", function (e) { dragging = true; cv.setPointerCapture(e.pointerId); pos(e); });
    cv.addEventListener("pointermove", function (e) { if (dragging) pos(e); });
    cv.addEventListener("pointerup", function () { dragging = false; });
    cv.addEventListener("keydown", function (e) { var k = { ArrowUp: [0, -6], ArrowDown: [0, 6], ArrowLeft: [-6, 0], ArrowRight: [6, 0] }[e.key]; if (k) { st.tx = Math.max(15, Math.min(105, st.tx + k[0])); st.ty = Math.max(15, Math.min(385, st.ty + k[1])); draw(); e.preventDefault(); } });
    rS.init(); onVis(api, draw);
    return { destroy: function () {} };
  });

  reg("sim", "l07_bounces", function (host, api) {
    var K = (api && api.colour) || "#37474f";
    var r = root(host, K), st = { refl: 0.3, n: 3 };
    var W = 720, H = 300, s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Bars showing how much light is left after each bounce." });
    s.appendChild(sv("rect", { width: W, height: H, fill: "#fff" }));
    var g = sv("g", {}); s.appendChild(g);
    r.appendChild(el("div", { "class": "lx-stage" }, [s]));
    var rS = slider({ label: "Each bounce keeps:", min: 0.05, max: 0.95, step: 0.05, value: 0.3, fmt: function (v) { return v.toFixed(2) + (Math.abs(v - 0.3) < 0.01 ? " (the model)" : ""); }, on: function (v) { st.refl = v; draw(); } });
    var nS = slider({ label: "Corners on the way in:", min: 0, max: 6, step: 1, value: 3, fmt: function (v) { return v; }, on: function (v) { st.n = v; draw(); } });
    r.appendChild(el("div", { "class": "lx-row" }, [rS, nS]));
    var cL = chip("light left"), cP = chip("one part in"), cS = chip("the sum");
    r.appendChild(el("div", { "class": "lx-read" }, [cL, cP, cS]));
    var out = say(r);
    function draw() {
      while (g.firstChild) g.removeChild(g.firstChild);
      var x0 = 60, bw = 80, base = 250, top = 30;
      for (var i = 0; i <= 6; i++) {
        var v = Math.pow(st.refl, i), hgt = v * (base - top), on = i <= st.n, x = x0 + i * (bw + 14);
        g.appendChild(sv("rect", { x: x, y: base - Math.max(hgt, 1.5), width: bw, height: Math.max(hgt, 1.5), fill: on ? (i === st.n ? "#D9601A" : "#ffd640") : "#e6e1d8", stroke: "#2D2A26", "stroke-width": on ? 1.5 : 0 }));
        var t1 = sv("text", { x: x + bw / 2, y: base + 20, "text-anchor": "middle", "font-size": 13, fill: "#2D2A26", "font-weight": 600 }); t1.textContent = i === 0 ? "straight" : i + (i === 1 ? " bounce" : " bounces"); g.appendChild(t1);
        var t2 = sv("text", { x: x + bw / 2, y: base - Math.max(hgt, 1.5) - 6, "text-anchor": "middle", "font-size": 12, fill: "#625C53" }); t2.textContent = v >= 0.01 ? v.toFixed(v >= 0.1 ? 2 : 3) : v.toFixed(5).replace(/0+$/, ""); g.appendChild(t2);
      }
      var v = Math.pow(st.refl, st.n), sum = st.n ? Array(st.n).fill(st.refl.toFixed(2)).join(" × ") + " = " + (v < 0.001 ? v.toExponential(1) : +v.toFixed(5)) : "nothing taken away: 1";
      cL.val(v >= 0.01 ? (v * 100).toFixed(1) + "%" : (v * 100).toPrecision(2) + "%", v > 0.05 ? "bad" : "good");
      cP.val(Math.round(1 / v).toLocaleString("en")); cS.val(st.n ? st.refl.toFixed(2) + "^" + st.n : "1"); cS.querySelector("span").textContent = sum;
      out.textContent = "After " + st.n + " bounce" + (st.n === 1 ? "" : "s") + " that each keep " + st.refl.toFixed(2) + ", at most " + (v * 100).toPrecision(2) + "% is left: one part in " + Math.round(1 / v).toLocaleString("en") + ". And most bounced light heads the wrong way, so the real share is smaller.";
    }
    rS.init(); nS.init(); draw();
    return { destroy: function () {} };
  });

  /* ---- figures ---- */
  reg("fig", "fig_l07_lamps", function () {
    var b = '<rect width="620" height="300" fill="#fff"/><rect x="300" y="20" width="16" height="260" fill="#2D2A26"/><rect x="300" y="142" width="16" height="16" fill="#fff"/><rect x="560" y="20" width="14" height="260" fill="#e7e1d6"/>';
    var lamps = [[60, 60, "#ffcf33"], [60, 150, "#ff9a3d"], [60, 240, "#ffcf33"]];
    lamps.forEach(function (L, i) {
      var sy = 150 + (150 - L[1]) * (260 / 248), off = i === 2;
      b += '<circle cx="' + L[0] + '" cy="' + L[1] + '" r="16" fill="' + L[2] + '" stroke="#2D2A26" stroke-width="2"/>';
      if (!off) b += '<line x1="' + L[0] + '" y1="' + L[1] + '" x2="560" y2="' + sy + '" stroke="' + L[2] + '" stroke-width="3"/><circle cx="560" cy="' + sy + '" r="10" fill="' + L[2] + '"/>';
      else b += '<line x1="' + L[0] + '" y1="' + L[1] + '" x2="110" y2="' + (L[1] - 4) + '" stroke="' + L[2] + '" stroke-width="3"/><circle cx="560" cy="' + sy + '" r="10" fill="none" stroke="#625C53" stroke-dasharray="3 3"/>';
    });
    b += '<rect x="104" y="200" width="12" height="70" fill="#625C53"/><text x="124" y="292" font-size="13" fill="#625C53">screen one lamp: only its spot goes out</text>';
    b += '<text x="318" y="135" font-size="13" fill="#2D2A26" font-weight="600">one opening</text><text x="470" y="296" font-size="13" fill="#2D2A26" font-weight="600">wall</text>';
    b += '<text x="20" y="22" font-size="15" font-weight="700" fill="#2D2A26">About 1021: each spot comes straight from its own lamp</text>';
    return svgFig(620, 300, "Three lamps shine through one opening onto a wall. Each makes its own spot on the far side, crossed over. Screen one lamp and only its spot goes out: light goes in straight lines.", b);
  });
  reg("fig", "fig_l07_waysin", function () {
    var b = '<rect width="700" height="330" fill="#fff"/>';
    b += '<rect x="120" y="110" width="400" height="150" rx="22" fill="#2a2d31"/><rect x="150" y="100" width="340" height="16" rx="6" fill="#c9cdd1"/>';
    b += '<circle cx="190" cy="96" r="22" fill="#2f9e57"/><circle cx="450" cy="96" r="24" fill="#c62828"/><circle cx="380" cy="100" r="13" fill="#2b6cb0"/><circle cx="320" cy="185" r="34" fill="#D9601A"/><circle cx="320" cy="185" r="12" fill="#1a1a1a"/>';
    function call(x1, y1, x2, y2, t1, t2) { return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="#2D2A26" stroke-width="1.5"/><text x="' + x2 + '" y="' + (y2 - 20) + '" font-size="14" font-weight="700" fill="#2D2A26">' + t1 + '</text><text x="' + x2 + '" y="' + (y2 - 5) + '" font-size="12" fill="#625C53">' + t2 + '</text>'; }
    b += call(190, 74, 10, 50, "green winder: 0.65 mm of room", "head lies flat; ring in a channel; block behind");
    b += call(450, 72, 470, 50, "red winder: the same", "no straight line past either");
    b += call(380, 88, 250, 86, "frame wheel's opening", "the leakiest of the three on top");
    b += call(500, 116, 530, 170, "back's joint", "ridge in a groove, 1.9 mm deep");
    b += call(320, 219, 380, 322, "the lens: the one way in", "only when the shutter opens");
    b += call(126, 230, 20, 322, "front plate's edge", "hooks pull it flat on the body");
    return svgFig(700, 330, "The ways light could try to get into the camera: the two winders, the frame wheel's opening, the back's joint, the front plate's edge, and the lens. Only the lens is meant to let light in, and only while the shutter is open.", b);
  });
})();

/* Lesson 7's picture (hero_fig, and its card): a light trap.  Light that gets into a gap must turn corners; each bounce sends back at most 0.3 of it. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#4B5563", SUN = "#F2B807";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  C.fig("fig_l07_trap", function () {
    var b = '<rect width="640" height="360" fill="#fff"/><rect x="420" y="276" width="212" height="76" fill="#1d1b19"/>' +
      '<path d="M20 100 H372 V220 H520" fill="none" stroke="' + COL + '" stroke-width="16" stroke-linejoin="miter"/><path d="M20 180 H292 V300 H420" fill="none" stroke="' + COL + '" stroke-width="16" stroke-linejoin="miter"/>' +
      '<line x1="20" y1="140" x2="332" y2="140" stroke="' + SUN + '" stroke-width="13" stroke-linecap="round"/>' +
      '<line x1="332" y1="140" x2="332" y2="260" stroke="' + SUN + '" stroke-width="6" stroke-linecap="round" opacity=".8"/>' +
      '<line x1="332" y1="260" x2="600" y2="260" stroke="' + SUN + '" stroke-width="2.5" stroke-linecap="round" opacity=".6"/>' +
      '<circle cx="332" cy="140" r="9" fill="#fff" stroke="' + INK + '" stroke-width="2.5"/><circle cx="332" cy="260" r="9" fill="#fff" stroke="' + INK + '" stroke-width="2.5"/>' +
      T(20, 72, "light", 26, 800, INK) + T(392, 160, "0.3", 30, 800, INK) + T(630, 236, "0.09", 34, 800, INK, "end") +
      T(526, 324, "dark inside", 22, 700, "#fff", "middle") + T(632, 46, "each corner: at most 0.3 gets past", 19, 600, "#625C53", "end");
    return C.U.svg(640, 360, b, "A light trap. Light getting into a gap has to bounce round two corners. Each bounce lets at most 0.3 of it through: 0.3 after one corner, 0.09 after two, so the inside stays dark.");
  });
})();
