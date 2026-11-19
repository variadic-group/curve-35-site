/* Lesson 2: Why a lens.  Sims: l02_lens (bend it back to a point), l02_curve (flat film against curved film).
   Figures: fig_l02_gather, fig_l02_bighole, fig_l02_section.  Numbers: course/FACTS.md (lens 32 mm, 12 mm across, set for 3.7 m; dots; film on a 32 mm curve). */
(function () {
  "use strict";
  var C = window.CURVE, U = C.U, K = U.colours, O = C.OPTICS;
  var T = 'font-family="Inter, sans-serif"';

  function lensPath(x, y0, y1, bulge) { return '<path d="M' + x + " " + y0 + " Q" + (x + bulge) + " " + ((y0 + y1) / 2) + " " + x + " " + y1 + " Q" + (x - bulge) + " " + ((y0 + y1) / 2) + " " + x + " " + y0 + 'Z" fill="' + K.glass + '" stroke="#2D2A26" stroke-width="2.5"/>'; }
  C.fig("fig_l02_gather", function () {
    var b = '<rect width="640" height="320" fill="#fff"/>', px = 70, py = 160, lx = 330, fx = 560, ys = [70, 115, 160, 205, 250];
    ys.forEach(function (y) { b += '<line x1="' + px + '" y1="' + py + '" x2="' + lx + '" y2="' + y + '" stroke="' + K.ray + '" stroke-width="2.5"/><line x1="' + lx + '" y1="' + y + '" x2="' + fx + '" y2="' + py + '" stroke="' + K.ray + '" stroke-width="2.5"/>'; });
    b += lensPath(lx, 55, 265, 26) + '<rect x="' + fx + '" y="40" width="12" height="240" fill="#6d4f35"/>' +
      '<circle cx="' + px + '" cy="' + py + '" r="10" fill="' + K.sun + '" stroke="#2D2A26" stroke-width="2"/><circle cx="' + fx + '" cy="' + py + '" r="6" fill="' + K.plate + '" stroke="#2D2A26" stroke-width="2"/>' +
      '<text x="' + px + '" y="195" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">one point</text>' +
      '<text x="' + lx + '" y="30" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">lens</text>' +
      '<text x="' + (fx + 6) + '" y="305" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">film: one point again</text>';
    return U.svg(640, 320, b, "Five rays from one point spread over a lens; the lens bends them all back to one point on the film.");
  });
  C.fig("fig_l02_bighole", function () {
    var b = '<rect width="640" height="320" fill="#fff"/>', px = 70, py = 160, wx = 330, fx = 560, ys = [100, 130, 160, 190, 220];
    ys.forEach(function (y) { var yf = py + (y - py) * (fx - px) / (wx - px); b += '<line x1="' + px + '" y1="' + py + '" x2="' + fx + '" y2="' + yf + '" stroke="' + K.ray + '" stroke-width="2.5"/>'; });
    var top = py + (100 - py) * (fx - px) / (wx - px), bot = py + (220 - py) * (fx - px) / (wx - px);
    b += '<rect x="' + (wx - 6) + '" y="20" width="12" height="80" fill="#2D2A26"/><rect x="' + (wx - 6) + '" y="220" width="12" height="80" fill="#2D2A26"/>' +
      '<rect x="' + fx + '" y="20" width="12" height="280" fill="#6d4f35"/><rect x="' + (fx - 3) + '" y="' + top + '" width="18" height="' + (bot - top) + '" fill="' + K.ray + '" opacity=".8"/>' +
      '<circle cx="' + px + '" cy="' + py + '" r="10" fill="' + K.sun + '" stroke="#2D2A26" stroke-width="2"/>' +
      '<text x="' + px + '" y="195" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">one point</text>' +
      '<text x="' + wx + '" y="14" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">a big hole, no glass</text>' +
      '<text x="' + (fx - 14) + '" y="312" text-anchor="end" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">film: a whole disc</text>';
    return U.svg(640, 320, b, "Rays from one point pass straight through a big hole with no glass and land as a wide disc on the film.");
  });
  C.fig("fig_l02_section", function () {
    var cx = 320, cy = 70, R = 210, b = '<rect width="640" height="330" fill="#fff"/>';
    b += '<rect x="40" y="40" width="560" height="270" rx="26" fill="#3A3632"/><rect x="250" y="22" width="140" height="40" rx="6" fill="' + K.plate + '"/>';
    var a0 = Math.asin(230 / R) * 0.62, pts = [];
    for (var i = 0; i <= 40; i++) { var a = -a0 + 2 * a0 * i / 40; pts.push((cx + R * Math.sin(a)).toFixed(1) + "," + (cy + R * Math.cos(a)).toFixed(1)); }
    b += '<polyline points="' + pts.join(" ") + '" fill="none" stroke="#F2E6C9" stroke-width="7"/>';
    [-0.42, 0, 0.42].forEach(function (a) { b += '<line x1="' + cx + '" y1="' + cy + '" x2="' + (cx + R * Math.sin(a)) + '" y2="' + (cy + R * Math.cos(a)) + '" stroke="' + K.ray + '" stroke-width="2" stroke-dasharray="6 5"/>'; });
    b += '<ellipse cx="' + cx + '" cy="' + cy + '" rx="26" ry="9" fill="' + K.glass + '" stroke="#2D2A26" stroke-width="2.5"/>';
    b += '<circle cx="120" cy="225" r="40" fill="#5b5550" stroke="#F2E6C9" stroke-width="3"/><circle cx="520" cy="225" r="40" fill="#D7322B" stroke="#F2E6C9" stroke-width="3"/>';
    b += '<text x="' + cx + '" y="18" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#2D2A26">lens</text>' +
      '<text x="' + (cx + 34) + '" y="170" ' + T + ' font-size="14" font-weight="600" fill="#F2E6C9">32 mm, every way</text>' +
      '<text x="' + cx + '" y="300" text-anchor="middle" ' + T + ' font-size="14" font-weight="600" fill="#F2E6C9">the film, on a curve</text>' +
      '<text x="120" y="290" text-anchor="middle" ' + T + ' font-size="13" fill="#F2E6C9">film shell</text><text x="520" y="290" text-anchor="middle" ' + T + ' font-size="13" fill="#F2E6C9">spool</text>';
    return U.svg(640, 330, b, "The camera seen from above, cut through: the film lies on a curve, every part of it 32 mm from the lens.");
  });

  // ------------------------------------------------------------------ bend it back to a point
  C.sim("l02_lens", function (el, api) {
    var F = api.facts, wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var st = U.stage(wrap, { aspect: function (w) { return w < 560 ? 0.66 : 0.42; }, maxH: 420 });
    wrap.appendChild(U.h("p", { class: "sim-cap" }, "Side view, not to scale: the space behind the lens is stretched so you can see where the rays meet. Drag the lamp."));
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div", { class: "sim-ctls" }), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var S = { u: 3700, mode: "lens", dot: "large", half: false };
    var su = U.slider({ label: "Lamp distance", min: 300, max: 100000, log: true, value: S.u, fmt: function (v) { return v >= 99000 ? "far away" : (v / 1000).toFixed(v < 1000 ? 2 : 1) + " m"; }, onInput: function (v) { S.u = v >= 99000 ? Infinity : v; upd(); } });
    left.appendChild(su.el);
    left.appendChild(U.choice({ label: "In the hole", options: [{ v: "lens", label: "the lens" }, { v: "hole", label: "nothing: just the hole" }], value: "lens", onChange: function (v) { S.mode = v; upd(); } }).el);
    left.appendChild(U.choice({ label: "Dot", options: [{ v: "small", label: "small f/16" }, { v: "middle", label: "middle f/11" }, { v: "large", label: "large f/9.5" }], value: "large", onChange: function (v) { S.dot = v; upd(); } }).el);
    left.appendChild(U.choice({ label: "Your hand", options: [{ v: false, label: "lens clear" }, { v: true, label: "cover half the lens" }], value: false, onChange: function (v) { S.half = v; upd(); } }).el);
    var pv = U.stage(right, { aspect: 2 / 3, maxH: 260 });
    right.appendChild(U.h("p", { class: "sim-cap" }, "The picture (simulated), for a scene at the lamp's distance"));
    var set = U.readouts(right, [{ k: "v", label: "sharp behind lens" }, { k: "b", label: "blur on film", cls: "sim-hi" }, { k: "x", label: "light vs pinhole" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var sc = U.scene(360, 240), blurOf = U.blurCache(sc), geo = {};
    function D() { return F.dots[S.dot].mm; }
    function blur() { var d = D(); return S.mode === "hole" ? d * (1 + O.v(3700) / (isFinite(S.u) ? S.u : 1e12)) : O.defocus(d, S.u); }
    function upd() {
      var d = D(), v = O.v(S.u), b = blur(), N = F.dots[S.dot].f, light = Math.pow(120 / N, 2) * (S.half ? 0.5 : 1), sharp = b < O.sharp_mm;
      set({ v: S.mode === "hole" ? "–" : v.toFixed(2) + " <small>mm</small>", b: (b < 0.1 ? b.toFixed(3) : b.toFixed(2)) + " <small>mm</small>", x: "× " + Math.round(light) });
      var where = isFinite(S.u) ? (S.u / 1000).toFixed(S.u < 1000 ? 2 : 1) + " m away" : "far away";
      var t = S.mode === "hole" ? "No glass: every point lands as a disc " + b.toFixed(1) + " mm wide. As bright as the lens, and a smear." :
        sharp ? "Sharp enough for a postcard (blur under 0.045 mm)." : "Soft: the rays meet " + Math.abs(v - O.v(3700)).toFixed(2) + " mm " + (v > O.v(3700) ? "behind" : "in front of") + " the film.";
      if (S.half && S.mode === "lens") t += " Half the lens covered: the picture is all still there, half as bright.";
      verdict.textContent = t;
      say("A lamp " + where + ", " + (S.mode === "lens" ? "with the lens" : "with no glass") + " at the " + S.dot + " dot (" + d + " mm). Blur on the film " + b.toFixed(3) + " mm. " + t);
      st.redraw(); pv.redraw();
    }
    st.draw = function (g, W, H) {
      var cy = H * 0.56, lx = W * 0.48, fx = W * 0.78, k = W * 0.09, d = D(), ap = H * 0.36 * d / 3.34, lensH = H * 0.4;
      var ux = isFinite(S.u) ? W * 0.04 + (W * 0.36) * (1 - Math.log(S.u / 300) / Math.log(100000 / 300)) : W * 0.02;
      geo = { ux: ux, cy: cy, W: W };
      g.fillStyle = "#0d0b09"; g.fillRect(0, 0, W, H);
      g.strokeStyle = "#3a352d"; g.setLineDash([4, 5]); g.beginPath(); g.moveTo(0, cy); g.lineTo(W, cy); g.stroke(); g.setLineDash([]);
      var v0 = O.v(3700), v = O.v(S.u), xi = fx + (v - v0) * k, n = 7;
      g.globalCompositeOperation = "lighter";
      for (var i = 0; i < n; i++) {
        var y = cy - ap + 2 * ap * i / (n - 1), blocked = S.half && y < cy - 0.5;
        g.strokeStyle = blocked ? "rgba(245,166,35,.35)" : "#F5A623"; g.lineWidth = 2;
        g.beginPath(); if (isFinite(S.u)) g.moveTo(ux, cy); else g.moveTo(0, y); g.lineTo(lx, y); g.stroke();
        if (blocked) continue;
        g.beginPath(); g.moveTo(lx, y);
        if (S.mode === "lens") { var ex = fx + 4, ey = y + (cy - y) * (ex - lx) / (xi - lx); g.lineTo(ex, ey); }
        else { var sy = isFinite(S.u) ? (y - cy) / (lx - ux) : 0, ey2 = y + (isFinite(S.u) ? sy : 0) * (fx - lx); g.lineTo(fx + 4, ey2); }
        g.stroke();
      }
      g.globalCompositeOperation = "source-over";
      // lamp
      if (isFinite(S.u)) { g.fillStyle = "#FFD23F"; g.beginPath(); g.arc(ux, cy, 10, 0, 7); g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 2; g.stroke(); U.label(g, "lamp", ux, cy + 28, { align: "center", color: "#d8d0c2", size: 11 }); }
      else U.label(g, "from far away →", 8, cy - lensH / 2 - 12, { color: "#d8d0c2", size: 11 });
      // the stop and the lens
      g.fillStyle = "#4b453b"; g.fillRect(lx - 3, cy - lensH / 2 - 30, 6, lensH / 2 + 30 - ap); g.fillRect(lx - 3, cy + ap, 6, lensH / 2 + 30 - ap);
      if (S.mode === "lens") { g.fillStyle = "rgba(159,211,230,.45)"; g.strokeStyle = "#9FD3E6"; g.lineWidth = 2; g.beginPath(); g.ellipse(lx + 8, cy, 10, lensH / 2, 0, 0, 7); g.fill(); g.stroke(); }
      if (S.half) { g.fillStyle = "#e0b48f"; g.fillRect(lx - 30, cy - lensH / 2 - 30, 22, lensH / 2 + 30); U.label(g, "hand", lx - 19, cy - lensH / 2 - 36, { align: "center", color: "#e0b48f", size: 11 }); }
      U.label(g, S.mode === "lens" ? "lens + dot" : "dot, no glass", lx, H - 10, { align: "center", color: "#d8d0c2", size: 11 });
      // film
      g.fillStyle = "#f3efe6"; g.fillRect(fx, cy - H * 0.42, 5, H * 0.84); U.label(g, "film", fx + 2, H - 10, { align: "center", color: "#d8d0c2", size: 11 });
      if (S.mode === "lens") { g.fillStyle = "#FFD23F"; g.beginPath(); g.arc(xi, cy, 3.5, 0, 7); g.fill(); U.label(g, "rays meet", xi, cy - 10 - (xi > fx ? 0 : 0), { align: "center", color: "#FFD23F", size: 10 }); }
      // inset: the spot on the film, 40x
      var iw = Math.min(84, Math.round(W * 0.17)), ix = W - iw - 8, iy = 8, b = blur();
      g.fillStyle = "#1e1a15"; g.fillRect(ix, iy, iw, iw); g.strokeStyle = "#5a5246"; g.strokeRect(ix + 0.5, iy + 0.5, iw - 1, iw - 1);
      var r = Math.max(1.2, Math.min(iw * 0.48, b * 40 * 12 / 2)), grd = g.createRadialGradient(ix + iw / 2, iy + iw / 2, 0, ix + iw / 2, iy + iw / 2, r);
      grd.addColorStop(0, "#FFE58A"); grd.addColorStop(0.85, "rgba(255,210,63,.7)"); grd.addColorStop(1, "rgba(255,210,63,0)");
      g.fillStyle = grd; g.beginPath(); if (S.half && S.mode === "lens" && r > 3) { g.arc(ix + iw / 2, iy + iw / 2, r, 0, Math.PI); } else g.arc(ix + iw / 2, iy + iw / 2, r, 0, 7); g.fill();
      U.label(g, "spot ×480", ix + iw / 2, iy + iw + 14, { align: "center", color: "#d8d0c2", size: 10 });
    };
    pv.draw = function (g, W, H) {
      var b = blur(), px = b * sc.w / 36;
      U.paint(g, blurOf(px), 0, 0, W, H, S.half && S.mode === "lens" ? 0.55 : 1, { flip: false, vignette: 0.3 });
      U.simTag(g, 8, H - 8);
    };
    U.drag(st.cv, function (x, y, ph) {
      if (ph === "hover") { st.cv.style.cursor = x < geo.W * 0.42 ? "grab" : "default"; return; }
      if ((ph === "down" || ph === "move") && x < geo.W * 0.46) {
        var t = U.clamp((x - geo.W * 0.04) / (geo.W * 0.36), 0, 1), u = 300 * Math.pow(100000 / 300, 1 - t);
        su.set(u);
      }
    });
    upd();
    return { destroy: function () { st.destroy(); pv.destroy(); } };
  });

  // ------------------------------------------------------------------ flat film against curved film
  C.sim("l02_curve", function (el, api) {
    var F = api.facts, wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 0.62, maxH: 400 });
    left.appendChild(U.h("p", { class: "sim-cap" }, "From above: light from five directions, a single lens, and the film. The hole is drawn three times too big to see it."));
    var pv = U.stage(left, { aspect: 2 / 3, maxH: 420 });
    left.appendChild(U.h("p", { class: "sim-cap" }, "The whole picture of a far scene (simulated). Soft parts are tinted."));
    var S = { flat: true, dot: "large", tint: true };
    right.appendChild(U.choice({ label: "The film", options: [{ v: true, label: "flat, like most cameras" }, { v: false, label: "curved, like yours" }], value: true, onChange: function (v) { S.flat = v; upd(); } }).el);
    right.appendChild(U.choice({ label: "Dot", options: [{ v: "small", label: "small" }, { v: "middle", label: "middle" }, { v: "large", label: "large" }], value: "large", onChange: function (v) { S.dot = v; upd(); } }).el);
    right.appendChild(U.choice({ label: "Show the soft parts", options: [{ v: true, label: "tinted" }, { v: false, label: "plain" }], value: true, onChange: function (v) { S.tint = v; upd(); } }).el);
    var set = U.readouts(right, [{ k: "mid", label: "blur, middle" }, { k: "end", label: "blur, ends" }, { k: "share", label: "sharp for a postcard", cls: "sim-hi" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var sc = U.scene(360, 240), blurOf = U.blurCache(sc), comp = null;
    function blurAt(xmm, ymm) {
      var D = F.dots[S.dot].mm, rho = Math.hypot(xmm, ymm) / Math.hypot(18, 12), th = Math.atan(Math.abs(xmm) / 32);
      return S.flat ? D * (1 - Math.cos(th)) + O.residual(D, rho) * 0.5 : O.residual(D, rho);
    }
    function build() {
      var levels = [0, 0.04, 0.08, 0.16, 0.32, 0.5], imgs = levels.map(function (b) { return blurOf(b * sc.w / 36); }), w = sc.w, h = sc.h, out = new U.Img(w, h);
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
        var xm = (x / w - 0.5) * 36, ym = (y / h - 0.5) * 24, b = Math.min(0.5, blurAt(xm, ym)), j = 0;
        while (j < levels.length - 2 && b > levels[j + 1]) j++;
        var t = U.clamp((b - levels[j]) / (levels[j + 1] - levels[j]), 0, 1), p = (y * w + x) * 3, A = imgs[j].d, B = imgs[j + 1].d;
        for (var c = 0; c < 3; c++) out.d[p + c] = A[p + c] * (1 - t) + B[p + c] * t;
        if (S.tint && b >= O.sharp_mm) { out.d[p] = out.d[p] * 0.85 + 0.15 * 0.9; out.d[p + 1] *= 0.88; out.d[p + 2] *= 0.82; }
      }
      comp = out;
    }
    function upd() {
      var D = F.dots[S.dot].mm, share = O.share(D, S.flat), end = blurAt(18, 0);
      set({ mid: blurAt(0, 0).toFixed(3) + " <small>mm</small>", end: end.toFixed(2) + " <small>mm</small>", share: Math.round(share * 100) + " %" });
      var t = S.flat ? "Flat film: the middle is sharp, the ends are " + Math.round(end / O.sharp_mm) + " times too soft for a postcard." : "Curved film: the film follows the sharp picture. Only a little softer toward the ends.";
      verdict.textContent = t;
      say((S.flat ? "Flat" : "Curved") + " film, " + S.dot + " dot. Sharp enough for a postcard over " + Math.round(share * 100) + " % of the picture; blur at the ends " + end.toFixed(2) + " mm. " + t);
      build(); st.redraw(); pv.redraw();
    }
    st.draw = function (g, W, H) {
      var lx = W * 0.2, cy = H * 0.5, R = Math.min(W * 0.62, H * 0.4 / Math.sin(0.51)), D = F.dots[S.dot].mm, ap = 3 * D / 32 * R / 2, max = 0.51, fx = lx + R;
      g.fillStyle = "#0d0b09"; g.fillRect(0, 0, W, H);
      // where the picture is sharp: a curve
      g.strokeStyle = "rgba(255,210,63,.45)"; g.setLineDash([6, 6]); g.lineWidth = 2; g.beginPath(); g.arc(lx, cy, R, -max - 0.05, max + 0.05); g.stroke(); g.setLineDash([]);
      U.label(g, "sharp here", lx + R * Math.cos(max + 0.06) - 4, cy + R * Math.sin(max + 0.06) + 14, { align: "center", color: "#FFD23F", size: 11 });
      var cols = ["#FF6B4A", "#FFD23F", "#9BE564", "#4FD1E8", "#C9A7FF".replace("C9A7FF", "F2F2F2")];
      [-max, -max / 2, 0, max / 2, max].forEach(function (a, i) {
        var col = cols[i], px = lx + R * Math.cos(a), py = cy + R * Math.sin(a);
        g.strokeStyle = col; g.lineWidth = 1.6; g.globalAlpha = 0.9;
        [-1, 0, 1].forEach(function (s) {
          var sx = lx, sy = cy + s * ap * Math.cos(a), dx = Math.cos(a), dy = Math.sin(a);
          g.beginPath(); g.moveTo(sx - dx * W, sy - dy * W); g.lineTo(sx, sy);
          // after the lens: toward the sharp point, then on to the film
          var ex, ey;
          if (S.flat) { var tt = (fx - sx) / (px - sx); ex = fx; ey = sy + (py - sy) * tt; } else { ex = px; ey = py; }
          g.lineTo(ex, ey); g.stroke();
        });
        g.globalAlpha = 1;
      });
      // lens
      g.fillStyle = "rgba(159,211,230,.5)"; g.strokeStyle = "#9FD3E6"; g.beginPath(); g.ellipse(lx, cy, 7, H * 0.16, 0, 0, 7); g.fill(); g.stroke();
      // film
      g.strokeStyle = "#f3efe6"; g.lineWidth = 6; g.beginPath();
      if (S.flat) { g.moveTo(fx + 3, cy - R * Math.sin(max) - 8); g.lineTo(fx + 3, cy + R * Math.sin(max) + 8); } else g.arc(lx, cy, R + 3, -max - 0.04, max + 0.04);
      g.stroke();
      U.label(g, S.flat ? "flat film" : "curved film, 32 mm from the lens everywhere", S.flat ? fx - 6 : lx + R * 0.55, 18, { align: S.flat ? "right" : "center", color: "#f3efe6", size: 12 });
      U.label(g, "lens", lx, cy + H * 0.16 + 16, { align: "center", color: "#d8d0c2", size: 11 });
    };
    pv.draw = function (g, W, H) { if (comp) U.paint(g, comp, 0, 0, W, H, 1, { vignette: 0.25 }); U.simTag(g, 8, H - 8); };
    upd();
    return { destroy: function () { st.destroy(); pv.destroy(); } };
  });
})();

/* Lesson 2's picture (hero_fig, and its card): a lens bends a fan of rays from one point back to one point on the curved film. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#2B6CD8";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  C.fig("fig_l02_hero", function () {
    var b = '<rect width="640" height="360" fill="#fff"/>';
    [-92, -46, 0, 46, 92].forEach(function (d) { b += '<polyline points="70,180 300,' + (180 + d) + ' 560,180" fill="none" stroke="' + COL + '" stroke-width="3.5" stroke-linejoin="round"/>'; });
    b += '<ellipse cx="300" cy="180" rx="17" ry="112" fill="#9FD3E6" stroke="' + INK + '" stroke-width="3"/>' +
      '<path d="M529.6 58 A260 260 0 0 1 529.6 302" fill="none" stroke="#6d4f35" stroke-width="11" stroke-linecap="round"/>' +
      '<circle cx="70" cy="180" r="10" fill="#F2B807" stroke="' + INK + '" stroke-width="2.5"/><circle cx="560" cy="180" r="10" fill="#F2B807" stroke="' + INK + '" stroke-width="2.5"/>' +
      T(70, 228, "one point", 22, 700, INK, "middle") + T(300, 46, "lens", 24, 700, INK, "middle") + T(560, 344, "curved film", 22, 700, INK, "middle") +
      T(632, 34, "back to one point", 22, 800, COL, "end");
    return C.U.svg(640, 360, b, "A point of light sends a fan of rays into the lens. The lens bends every ray back to a single point on the curved film, so the picture is bright and sharp.");
  });
})();
