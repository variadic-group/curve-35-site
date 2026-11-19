/* Lesson 1: A picture from a hole.  Sims: l01_rays (the lamp experiment), l01_hole (pick the hole).  Figures: fig_l01_nofilm, fig_l01_crossing, fig_l01_best.
   Numbers: course/FACTS.md (pinhole 0.24 mm, 28.9 mm from the film, f/120; counts for ISO 400). */
(function () {
  "use strict";
  var C = window.CURVE, U = C.U, K = U.colours;

  // ------------------------------------------------------------------ figures
  function tree(x, y, s, flip) {   // a tree whose foot is at (x, y); flip draws it upside down
    var k = flip ? -1 : 1;
    return '<g transform="translate(' + x + " " + y + ") scale(" + s + " " + (s * k) + ')"><rect x="-5" y="-60" width="10" height="60" fill="#6b4a2c"/>' +
      '<circle cx="0" cy="-78" r="30" fill="#2f6b3a"/><circle cx="-20" cy="-62" r="18" fill="#2f6b3a"/><circle cx="20" cy="-62" r="18" fill="#2f6b3a"/>' +
      '<circle cx="0" cy="-104" r="7" fill="#F2B807"/></g>';
  }
  C.fig("fig_l01_nofilm", function () {
    var b = '<rect width="640" height="360" fill="#fff"/>' + tree(120, 290, 1.4);
    var rays = "";
    [[120, 145, K.sun], [120, 290, "#6b4a2c"]].forEach(function (p) {
      for (var y = 70; y <= 300; y += 23) rays += '<line x1="' + p[0] + '" y1="' + p[1] + '" x2="520" y2="' + y + '" stroke="' + p[2] + '" stroke-width="1.6" opacity=".75"/>';
    });
    b += rays + '<rect x="520" y="60" width="16" height="250" rx="3" fill="#6d4f35"/><rect x="536" y="60" width="44" height="250" fill="url(#g1)"/>' +
      '<defs><linearGradient id="g1" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#b9b2a6"/><stop offset="1" stop-color="#a69e91"/></linearGradient></defs>' +
      '<text x="528" y="44" text-anchor="middle" font-family="Inter, sans-serif" font-size="15" font-weight="600" fill="#2D2A26">film, no hole</text>' +
      '<text x="120" y="330" text-anchor="middle" font-family="Inter, sans-serif" font-size="15" font-weight="600" fill="#2D2A26">every point of the tree…</text>' +
      '<text x="340" y="345" text-anchor="middle" font-family="Inter, sans-serif" font-size="15" fill="#625C53">…lights every point of the film: an even grey</text>';
    return U.svg(640, 360, b, "Without a hole, light from the top and the bottom of a tree reaches every part of the film, so it turns an even grey.");
  });
  C.fig("fig_l01_crossing", function () {
    var b = '<rect width="640" height="360" fill="#fff"/>' + tree(110, 290, 1.4) +
      '<rect x="330" y="30" width="14" height="138" fill="#2D2A26"/><rect x="330" y="182" width="14" height="148" fill="#2D2A26"/>' +
      '<line x1="110" y1="145" x2="560" y2="245" stroke="' + K.sun + '" stroke-width="3"/><line x1="110" y1="290" x2="560" y2="115" stroke="#6b4a2c" stroke-width="3"/>' +
      '<circle cx="110" cy="145" r="6" fill="' + K.sun + '" stroke="#2D2A26"/><circle cx="110" cy="290" r="6" fill="#6b4a2c" stroke="#2D2A26"/>' +
      '<rect x="556" y="60" width="74" height="240" rx="4" fill="#efe9dd" stroke="#6d4f35" stroke-width="4"/>' + tree(593, 115, 1.2, true) +
      '<circle cx="560" cy="245" r="6" fill="' + K.sun + '" stroke="#2D2A26"/><circle cx="560" cy="115" r="6" fill="#6b4a2c" stroke="#2D2A26"/>' +
      '<text x="337" y="22" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#2D2A26">a small hole</text>' +
      '<text x="593" y="322" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="600" fill="#2D2A26">film</text>' +
      '<text x="320" y="350" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" fill="#625C53">top of the tree → bottom of the film. The rays cross in the hole.</text>';
    return U.svg(640, 360, b, "Rays from the top and the bottom of a tree cross in a small hole, so the tree lands upside down on the film.");
  });
  C.fig("fig_l01_best", function () {
    var lam = 0.00055, L = 28.9, W = 640, H = 360, x0 = 70, x1 = 610, y0 = 300, y1 = 30;
    function X(d) { return x0 + (x1 - x0) * Math.log(d / 0.05) / Math.log(2 / 0.05); }
    function Y(b) { return y0 - (y0 - y1) * Math.log(b / 0.02) / Math.log(2 / 0.02); }
    function path(f) { var s = ""; for (var i = 0; i <= 120; i++) { var d = 0.05 * Math.pow(2 / 0.05, i / 120), b = f(d); s += (i ? "L" : "M") + X(d).toFixed(1) + " " + Math.max(y1, Math.min(y0, Y(b))).toFixed(1); } return s; }
    var shadow = function (d) { return d; }, spread = function (d) { return 3.61 * lam * L / d; }, tot = function (d) { return Math.hypot(d, 3.61 * lam * L / d); };
    var b = '<rect width="640" height="360" fill="#fff"/>';
    [0.05, 0.1, 0.24, 0.5, 1, 2].forEach(function (d) { b += '<line x1="' + X(d) + '" y1="' + y0 + '" x2="' + X(d) + '" y2="' + (y0 + 6) + '" stroke="#2D2A26"/><text x="' + X(d) + '" y="' + (y0 + 22) + '" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#2D2A26">' + d + "</text>"; });
    [0.05, 0.1, 0.2, 0.5, 1, 2].forEach(function (v) { b += '<line x1="' + x0 + '" y1="' + Y(v) + '" x2="' + x1 + '" y2="' + Y(v) + '" stroke="#EFEBE3"/><text x="' + (x0 - 8) + '" y="' + (Y(v) + 4) + '" text-anchor="end" font-family="Inter, sans-serif" font-size="12" fill="#625C53">' + v + "</text>"; });
    b += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y0 + '" stroke="#2D2A26" stroke-width="1.5"/><line x1="' + x0 + '" y1="' + y0 + '" x2="' + x0 + '" y2="' + y1 + '" stroke="#2D2A26" stroke-width="1.5"/>';
    b += '<path d="' + path(shadow) + '" fill="none" stroke="' + K.blue + '" stroke-width="2.5" stroke-dasharray="7 6"/><path d="' + path(spread) + '" fill="none" stroke="' + K.red + '" stroke-width="2.5" stroke-dasharray="7 6"/><path d="' + path(tot) + '" fill="none" stroke="#2D2A26" stroke-width="4"/>';
    b += '<circle cx="' + X(0.24) + '" cy="' + Y(tot(0.24)) + '" r="8" fill="' + K.plate + '" stroke="#2D2A26" stroke-width="2"/>' +
      '<text x="' + (X(0.24) + 12) + '" y="' + (Y(tot(0.24)) + 32) + '" font-family="Inter, sans-serif" font-size="14" font-weight="700" fill="#2D2A26">0.24 mm: the least blur</text>' +
      '<text x="' + X(1.4) + '" y="' + (Y(1.4) - 14) + '" font-family="Inter, sans-serif" font-size="13" font-weight="600" fill="' + K.blue + '" text-anchor="middle">shadow of the hole</text>' +
      '<text x="' + X(0.08) + '" y="' + (Y(spread(0.08)) - 10) + '" font-family="Inter, sans-serif" font-size="13" font-weight="600" fill="' + K.red + '">light spreading</text>' +
      '<text x="' + ((x0 + x1) / 2) + '" y="' + (H - 6) + '" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#625C53">hole width, mm (28.9 mm from the film)</text>' +
      '<text x="18" y="' + ((y0 + y1) / 2) + '" transform="rotate(-90 18 ' + ((y0 + y1) / 2) + ')" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" fill="#625C53">blur on the film, mm</text>';
    return U.svg(W, H, b, "A graph of blur against hole width. A big hole blurs by its own width; a very small hole blurs because light spreads. The least blur is at 0.24 mm.");
  });

  // ------------------------------------------------------------------ the lamp experiment: three lamps, a card with a hole, a sheet of paper
  C.sim("l01_rays", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 0.62, maxH: 460 });
    left.appendChild(U.h("p", { class: "sim-cap" }, "Side view. Drag a lamp up or down. Drag the paper left or right."));
    var lamps = [{ c: "#FFD23F", name: "yellow", y: -0.26, on: true }, { c: "#4FD1E8", name: "blue", y: 0, on: true }, { c: "#FF6B4A", name: "red", y: 0.26, on: true }];
    var S = { hole: 4, paper: 0.8, card: true, grab: null };
    var hole = U.slider({ label: "Hole in the card", min: 1, max: 14, step: 0.5, value: 4, fmt: function (v) { return v.toFixed(1) + " mm"; }, onInput: function (v) { S.hole = v; draw(); } });
    var paper = U.slider({ label: "Paper behind the card", min: 0.55, max: 0.97, step: 0.01, value: 0.8, fmt: function (v) { return Math.max(1, Math.round((v * 0.78 - 0.44) / 0.34 * 30)) + " cm"; }, hint: "The lamps are 30 cm in front of the card.", onInput: function (v) { S.paper = v; draw(); } });
    right.appendChild(hole.el); right.appendChild(paper.el);
    var lampBtns = U.h("div", { class: "sim-ctl" }); lampBtns.appendChild(U.h("span", { class: "sim-lab" }, "Lamps on or off"));
    var row = U.h("div", { class: "sim-seg" }); lampBtns.appendChild(row);
    lamps.forEach(function (L) { var b = U.h("button", { type: "button", class: "sim-btn", "aria-pressed": "true" }, '<span style="color:' + L.c + '">●</span> ' + L.name); b.addEventListener("click", function () { L.on = !L.on; b.setAttribute("aria-pressed", String(L.on)); draw(); }); row.appendChild(b); });
    right.appendChild(lampBtns);
    var card = U.choice({ label: "The card", options: [{ v: true, label: "Card with a hole" }, { v: false, label: "No card at all" }], value: true, onChange: function (v) { S.card = v; draw(); } });
    right.appendChild(card.el);
    var say = U.alt(wrap);
    var geo = {};
    st.draw = function (g, W, H) {
      var cx = W * 0.44, cy = H * 0.5, lx = W * 0.1, px = W * S.paper * 0.78, panel = W * 0.8, hpx = S.hole * 2.4;
      geo = { cx: cx, cy: cy, lx: lx, px: px, W: W, H: H };
      g.fillStyle = "#0d0b09"; g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = "lighter";
      var spots = [];
      lamps.forEach(function (L) {
        if (!L.on) return;
        var ly = cy + L.y * H;
        if (!S.card) {
          g.fillStyle = L.c + "22"; g.beginPath(); g.moveTo(lx, ly); g.lineTo(px, cy - H * 0.45); g.lineTo(px, cy + H * 0.45); g.closePath(); g.fill();
          spots.push({ L: L, a: cy - H * 0.45, b: cy + H * 0.45 }); return;
        }
        var t1 = cy - hpx / 2, t2 = cy + hpx / 2;
        function at(y) { return ly + (y - ly) * (px - lx) / (cx - lx); }
        var a = at(t1), b = at(t2);
        g.fillStyle = L.c + "40"; g.beginPath(); g.moveTo(lx, ly); g.lineTo(cx, t1); g.lineTo(px, a); g.lineTo(px, b); g.lineTo(cx, t2); g.closePath(); g.fill();
        g.strokeStyle = L.c; g.lineWidth = 1; g.beginPath(); g.moveTo(lx, ly); g.lineTo(px, (a + b) / 2); g.stroke();
        spots.push({ L: L, a: Math.min(a, b), b: Math.max(a, b) });
      });
      g.globalCompositeOperation = "source-over";
      // lamps
      lamps.forEach(function (L) { var ly = cy + L.y * H; g.fillStyle = L.on ? L.c : "#3a352d"; g.beginPath(); g.arc(lx, ly, 11, 0, 7); g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 2; g.stroke(); });
      // the card
      if (S.card) { g.fillStyle = "#cfc7b8"; g.fillRect(cx - 4, 8, 8, cy - hpx / 2 - 8); g.fillRect(cx - 4, cy + hpx / 2, 8, H - 8 - cy - hpx / 2); U.label(g, "card", cx, 22, { align: "center", color: "#cfc7b8", size: 12 }); }
      // the paper, edge on
      g.fillStyle = "#f3efe6"; g.fillRect(px, cy - H * 0.45, 5, H * 0.9);
      spots.forEach(function (s) { g.fillStyle = s.L.c; g.fillRect(px - 1, s.a, 7, Math.max(2, s.b - s.a)); });
      U.label(g, "paper", px + 2, H - 8, { align: "center", color: "#f3efe6", size: 12 });
      g.fillStyle = "rgba(255,255,255,.25)"; g.beginPath(); g.arc(px + 2, cy, 7, 0, 7); g.fill();
      // the paper, face on: what you would see
      var fx = panel + 16, fw = W - fx - 10;
      if (fw > 40) {
        g.fillStyle = "#e9e4d8"; g.fillRect(fx, cy - H * 0.45, fw, H * 0.9);
        g.globalCompositeOperation = "multiply";
        g.fillStyle = "#4b463e"; g.fillRect(fx, cy - H * 0.45, fw, H * 0.9);
        g.globalCompositeOperation = "lighter";
        spots.forEach(function (s) {
          var m = (s.a + s.b) / 2, r = Math.max(5, (s.b - s.a) * 0.8), k = S.card ? Math.min(1, 26 / (r * r) * (S.hole * S.hole / 16) * 4) : 0.28;
          var gr = g.createRadialGradient(fx + fw / 2, m, 0, fx + fw / 2, m, r * 1.1); gr.addColorStop(0, hexA(s.L.c, k)); gr.addColorStop(0.8, hexA(s.L.c, k * 0.8)); gr.addColorStop(1, hexA(s.L.c, 0));
          g.fillStyle = gr; if (S.card) { g.beginPath(); g.arc(fx + fw / 2, m, r * 1.1, 0, 7); g.fill(); } else { g.fillStyle = hexA(s.L.c, 0.32); g.fillRect(fx, cy - H * 0.45, fw, H * 0.9); }
        });
        g.globalCompositeOperation = "source-over";
        U.label(g, "on the paper", fx + fw / 2, cy - H * 0.45 + 16, { align: "center", color: "#d8d0c2", size: 11 });
      }
      // words
      var on = spots.length, order = S.card ? lamps.filter(function (L) { return L.on; }).map(function (L) { return L.name; }) : [];
      say(!S.card ? "No card: each lamp lights the whole paper, so the colours pile on top of each other into one even wash. No picture." :
        on ? "Each lamp makes its own spot on the paper, " + S.hole.toFixed(1) + " mm hole. From top to bottom on the paper the spots are " + order.slice().reverse().join(", ") + ": the other way up from the lamps. Paper further back: spots bigger and dimmer." : "All the lamps are off: the paper is dark.");
    };
    function hexA(h, a) { var c = h.replace("#", ""); return "rgba(" + parseInt(c.substr(0, 2), 16) + "," + parseInt(c.substr(2, 2), 16) + "," + parseInt(c.substr(4, 2), 16) + "," + Math.max(0, Math.min(1, a)).toFixed(3) + ")"; }
    function draw() { st.redraw(); }
    // the panel heading: drawn above, so add a fixed label element
    U.drag(st.cv, function (x, y, ph) {
      if (ph === "down") {
        S.grab = null;
        if (Math.abs(x - geo.px) < 26) S.grab = "paper";
        else if (Math.abs(x - geo.lx) < 30) { var best = 1e9; lamps.forEach(function (L, i) { var d = Math.abs(y - (geo.cy + L.y * geo.H)); if (d < best) { best = d; S.grab = i; } }); }
      }
      if ((ph === "move" || ph === "down") && S.grab != null) {
        if (S.grab === "paper") paper.set(U.clamp(x / geo.W / 0.78, 0.55, 0.97));
        else { lamps[S.grab].y = U.clamp((y - geo.cy) / geo.H, -0.42, 0.42); draw(); }
      }
      if (ph === "hover") st.cv.style.cursor = (Math.abs(x - geo.px) < 26 || Math.abs(x - geo.lx) < 30) ? "grab" : "default";
      if (ph === "up") S.grab = null;
    });
    return { destroy: st.destroy };
  });

  // ------------------------------------------------------------------ pick the hole: blur against light, on a simulated scene
  C.sim("l01_hole", function (el, api) {
    var F = api.facts, lam = F.wavelength_mm || 0.00055;
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 2 / 3, maxH: 520 });
    var gst = U.stage(left, { aspect: 0.3, maxH: 170, cls: "sim-light" });
    left.appendChild(U.h("p", { class: "sim-cap" }, "Top: the picture on the film (simulated). Below: blur against hole width; the dot is you."));
    var S = { d: 1.2, L: 28.9, auto: true, flip: true };
    var sd = U.slider({ label: "Hole width", min: 0.05, max: 3.34, log: true, value: S.d, fmt: function (v) { return v.toFixed(v < 1 ? 2 : 1) + " mm"; }, onInput: function (v) { S.d = v; upd(); } });
    var sl = U.slider({ label: "Hole to film", min: 20, max: 300, log: true, value: S.L, fmt: function (v) { return v.toFixed(v < 100 ? 1 : 0) + " mm"; }, hint: "Your camera: 28.9 mm. A shoebox: about 300 mm.", onInput: function (v) { S.L = v; upd(); } });
    right.appendChild(sd.el); right.appendChild(sl.el);
    var ex = U.choice({ label: "Light", options: [{ v: true, label: "Count it right" }, { v: false, label: "Always count 1 s" }], value: true, onChange: function (v) { S.auto = v; upd(); } });
    right.appendChild(ex.el);
    var quick = U.h("div", { class: "sim-row" });
    quick.appendChild(U.button("0.24 mm: the best pinhole", function () { sd.set(0.24); sl.set(28.9); }));
    quick.appendChild(U.button("1.96 mm: the small dot, no lens", function () { sd.set(1.96); sl.set(28.9); }));
    quick.appendChild(U.button(S.flip ? "Turn it the right way up" : "As on the film", function (e) { S.flip = !S.flip; e.target.textContent = S.flip ? "Turn it the right way up" : "Back to how the film sees it"; upd(); }));
    right.appendChild(quick);
    var set = U.readouts(right, [{ k: "f", label: "f-number" }, { k: "b", label: "blur on film" }, { k: "t", label: "count, cloud", cls: "sim-hi" }, { k: "best", label: "best hole here" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var sc = U.scene(480, 320), blurOf = U.blurCache(sc);
    function blurMm(d, L) { return Math.hypot(d, 3.61 * lam * L / d); }
    function count(N) { var t = Math.pow(N / 120, 2); return t >= 1 ? (t < 10 ? t.toFixed(1) : Math.round(t)) + " s" : "1/" + Math.round(1 / t) + " s"; }
    function upd() {
      var d = S.d, L = S.L, N = L / d, b = blurMm(d, L), best = 1.9 * Math.sqrt(L * lam);
      set({ f: "f/" + (N < 20 ? N.toFixed(1) : Math.round(N)), b: b.toFixed(2) + " <small>mm</small>", t: count(N), best: best.toFixed(2) + " <small>mm</small>" });
      var ratio = d / best, txt;
      if (ratio > 2.2) txt = "Too big: every point lands as a disc " + d.toFixed(1) + " mm wide. Bright, but a smear." + (d >= 1.9 ? " That's why the camera's own dots can't be the pinhole." : "");
      else if (ratio < 0.45) txt = "Too small: light spreads out after the hole. Dim and soft.";
      else if (Math.abs(Math.log(ratio)) < 0.12) txt = "Just right: about the least blur this depth can give.";
      else txt = ratio > 1 ? "A bit big: brighter, softer." : "A bit small: dimmer, and no sharper.";
      verdict.textContent = txt;
      say("Hole " + d.toFixed(2) + " mm, " + L.toFixed(1) + " mm from the film: f/" + Math.round(N) + ". Each point blurs to about " + b.toFixed(2) + " mm on the film. In bright cloud with ISO 400 film you would count " + count(N) + ". " + txt);
      st.redraw(); gst.redraw();
    }
    st.draw = function (g, W, H) {
      var zoom = S.L / 20, b = blurMm(S.d, S.L), px = b * sc.w / (36 * zoom), gain = S.auto ? 1 : Math.min(400, Math.pow(120 / (S.L / S.d), 2));
      g.fillStyle = "#000"; g.fillRect(0, 0, W, H);
      U.paint(g, blurOf(px), W / 2 - W * zoom / 2, H / 2 - H * zoom / 2, W * zoom, H * zoom, gain, { flip: S.flip, vignette: 0.35 });
      U.simTag(g, 10, H - 10, "simulated: 36 x 24 mm of film" + (S.flip ? ", upside down as it lands" : ", turned the right way up"));
    };
    gst.draw = function (g, W, H) {
      var x0 = 34, x1 = W - 10, y0 = H - 24, y1 = 10, L = S.L;
      function X(d) { return x0 + (x1 - x0) * Math.log(d / 0.05) / Math.log(3.34 / 0.05); }
      function Y(v) { return y0 - (y0 - y1) * U.clamp(Math.log(v / 0.02) / Math.log(4 / 0.02), 0, 1); }
      g.fillStyle = "#fff"; g.fillRect(0, 0, W, H);
      g.strokeStyle = "#2D2A26"; g.lineWidth = 1; g.beginPath(); g.moveTo(x0, y1); g.lineTo(x0, y0); g.lineTo(x1, y0); g.stroke();
      [0.05, 0.1, 0.24, 0.5, 1, 2].forEach(function (d) { U.label(g, String(d), X(d), H - 8, { align: "center", color: "#625C53", size: 10, weight: 400 }); });
      function curve(f, col, w, dash) { g.save(); g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.beginPath(); for (var i = 0; i <= 80; i++) { var d = 0.05 * Math.pow(3.34 / 0.05, i / 80), y = Y(f(d)); if (i) g.lineTo(X(d), y); else g.moveTo(X(d), y); } g.stroke(); g.restore(); }
      curve(function (d) { return d; }, K.blue, 1.5, [5, 4]); curve(function (d) { return 3.61 * lam * L / d; }, K.red, 1.5, [5, 4]); curve(function (d) { return blurMm(d, L); }, "#2D2A26", 3);
      var bx = X(1.9 * Math.sqrt(L * lam)); g.strokeStyle = "#1d7a46"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(bx, y1); g.lineTo(bx, y0); g.stroke(); g.setLineDash([]);
      g.fillStyle = api.colour; g.beginPath(); g.arc(X(S.d), Y(blurMm(S.d, L)), 7, 0, 7); g.fill(); g.strokeStyle = "#2D2A26"; g.lineWidth = 2; g.stroke();
      U.label(g, "blur", 4, 14, { color: "#625C53", size: 10, weight: 600 });
      U.label(g, "shadow of the hole", X(3.3), Y(3.3) + 18, { align: "right", color: K.blue, size: 10 });
      U.label(g, "spreading", X(0.07), Y(3.61 * lam * L / 0.07) + 16, { color: K.red, size: 10 });
    };
    // drag on the graph to choose the hole
    U.drag(gst.cv, function (x, y, ph) { if (ph === "down" || ph === "move") { var W = gst.w, d = 0.05 * Math.pow(3.34 / 0.05, U.clamp((x - 34) / (W - 44), 0, 1)); sd.set(d); } });
    upd();
    return { destroy: function () { st.destroy(); gst.destroy(); } };
  });
})();
