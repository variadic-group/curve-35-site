/* CURVE 35, lesson 9 "The camera in your pocket": the exposure triangle and the stops ladder.
   Camera numbers: course/FACTS.md (dots f/16.4, f/11.1, f/9.6; about 1/322 s; ISO 400 film; which dot for which sky).
   Phone numbers are typical, not one model: one fixed aperture around f/1.8, shutter times down to a few thousandths of a second and far shorter,
   ISO from about 50 upward.  Everything drawn here is simulated. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.sim || !C.U) return;
  var U = C.U;

  // light: EV at ISO 100 for a normal picture.  Full sun is sunny 16 (f/16, 1/100 s, ISO 100: EV 14.6).
  var LIGHT = { sun: { ev: 14.6, say: "full sun" }, hazy: { ev: 13.6, say: "hazy sun" }, cloud: { ev: 12.8, say: "bright cloud" }, indoors: { ev: 7, say: "a lit room" }, night: { ev: 4, say: "a street at night" } };
  var DOTS = { small: 16.4, middle: 11.1, large: 9.6 };
  function log2(x) { return Math.log(x) / Math.LN2; }
  function evOf(N, t, iso) { return log2(N * N / t) - log2(iso / 100); }
  function tSay(t) { if (t >= 0.95) return U.fmt(t, 1) + " s"; var d = 1 / t; return "1/" + (d >= 100 ? Math.round(d / 10) * 10 : Math.round(d)) + " s"; }
  function fSay(N) { return "f/" + (N < 10 ? N.toFixed(1) : Math.round(N)); }
  function isoSay(i) { return "ISO " + (i >= 100 ? Math.round(i / 10) * 10 : Math.round(i)); }
  function stopsSay(x) { return (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(1); }

  // ------------------------------------------------------------------ the exposure triangle: a scene, three settings, four side effects
  C.sim("l09_triangle", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div"), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var st = U.stage(left, { aspect: 2 / 3, maxH: 520 });
    left.appendChild(U.h("p", { class: "sim-cap" }, "Simulated. Focus is on the rider; the rider is going 5 m a second."));
    var S = { light: "sun", N: 1.8, t: 1 / 4000, iso: 50 };
    var cl = U.choice({ label: "The light", value: "sun", options: [{ v: "sun", label: "Full sun" }, { v: "cloud", label: "Cloud" }, { v: "indoors", label: "Indoors" }, { v: "night", label: "Night" }], onChange: function (v) { S.light = v; upd(); } });
    var sN = U.slider({ label: "Aperture", min: 1.4, max: 22, log: true, value: S.N, fmt: fSay, onInput: function (v) { S.N = v; upd(); }, hint: "Smaller number: bigger hole, more light, softer background." });
    var sT = U.slider({ label: "Shutter time", min: 1 / 8000, max: 1, log: true, value: S.t, fmt: tSay, onInput: function (v) { S.t = v; upd(); }, hint: "Longer: more light, more smear." });
    var sI = U.slider({ label: "ISO", min: 50, max: 6400, log: true, value: S.iso, fmt: isoSay, onInput: function (v) { S.iso = v; upd(); }, hint: "Higher: a brighter picture from the same light, and more noise." });
    right.appendChild(cl.el); right.appendChild(sN.el); right.appendChild(sT.el); right.appendChild(sI.el);
    var row = U.h("div", { class: "sim-row" }); right.appendChild(row);
    row.appendChild(U.button("Auto ISO", function () {
      var iso = 100 * Math.pow(2, log2(S.N * S.N / S.t) - LIGHT[S.light].ev); sI.set(U.clamp(iso, 50, 6400));
    }, "sim-go"));
    row.appendChild(U.button("Phone in the sun", function () { cl.set("sun", true); S.light = "sun"; sN.set(1.8, true); sT.set(1 / 4000, true); S.N = 1.8; S.t = 1 / 4000; sI.set(50); }));
    row.appendChild(U.button("Phone at night", function () { cl.set("night", true); S.light = "night"; sN.set(1.8, true); sT.set(1 / 15, true); S.N = 1.8; S.t = 1 / 15; sI.set(800); }));
    row.appendChild(U.button("CURVE 35 settings", function () { cl.set("sun", true); S.light = "sun"; sN.set(16.4, true); sT.set(1 / 322, true); S.N = 16.4; S.t = 1 / 322; sI.set(400); }));
    var set = U.readouts(wrap, [{ k: "b", label: "Brightness", cls: "sim-hi" }, { k: "m", label: "Rider moves" }, { k: "d", label: "Background" }, { k: "n", label: "Noise" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); wrap.appendChild(verdict);
    var say = U.alt(wrap);

    // the picture: a small internal canvas, scaled up
    var W = 300, H = 200, base = U.scene(W, H), blurOf = U.blurCache(base);
    var work = document.createElement("canvas"); work.width = W; work.height = H; var wx = work.getContext("2d", { willReadFrequently: true });
    var out = document.createElement("canvas"); out.width = W; out.height = H; var ox = out.getContext("2d");
    var rider = document.createElement("canvas"); rider.width = 64; rider.height = 76; drawRider(rider.getContext("2d"));
    var LIN = new Float32Array(256); for (var k = 0; k < 256; k++) LIN[k] = U.lin(k);
    var GAUSS = new Float32Array(1 << 16), r = U.rng(7); for (var g = 0; g < GAUSS.length; g++) { var u1 = r() || 1e-9, u2 = r(); GAUSS[g] = Math.sqrt(-2 * Math.log(u1)) * Math.cos(6.2832 * u2); }
    var P0 = 900, READ = 2;   // photons a pixel gets from a mid grey at a normal ISO 100 exposure; read noise in photons (a simple model)

    function drawRider(g) {
      g.lineCap = "round"; g.lineJoin = "round";
      g.strokeStyle = "#1d1d1d"; g.lineWidth = 3;
      g.beginPath(); g.arc(14, 60, 12, 0, 7); g.stroke(); g.beginPath(); g.arc(50, 60, 12, 0, 7); g.stroke();
      g.strokeStyle = "#1f6fd1"; g.lineWidth = 3.5; g.beginPath(); g.moveTo(14, 60); g.lineTo(28, 40); g.lineTo(46, 40); g.lineTo(50, 60); g.moveTo(28, 40); g.lineTo(32, 60); g.lineTo(46, 40); g.stroke();
      g.strokeStyle = "#e33b2e"; g.lineWidth = 6; g.beginPath(); g.moveTo(30, 36); g.lineTo(38, 18); g.stroke();      // body
      g.strokeStyle = "#2b2b2b"; g.lineWidth = 4; g.beginPath(); g.moveTo(31, 36); g.lineTo(36, 48); g.lineTo(32, 60); g.stroke();   // leg
      g.strokeStyle = "#e33b2e"; g.lineWidth = 3.5; g.beginPath(); g.moveTo(37, 22); g.lineTo(46, 32); g.stroke();       // arm
      g.fillStyle = "#e0b48f"; g.beginPath(); g.arc(40, 12, 6, 0, 7); g.fill();
      g.fillStyle = "#f2c94c"; g.beginPath(); g.arc(40, 9, 6.5, Math.PI, 0); g.fill();
    }

    function upd() {
      var L = LIGHT[S.light], over = L.ev - evOf(S.N, S.t, S.iso), a = L.ev - log2(S.N * S.N / S.t);
      var bg = 14 / S.N, smearPx = 205 * S.t, moveCm = 500 * S.t, noise = 100 / Math.sqrt(P0 * Math.pow(2, a));
      paint(over, a, bg, smearPx);
      var bS = Math.abs(over) < 0.35 ? "just right" : stopsSay(over) + " <small>stops</small>";
      set({ b: bS, m: (moveCm < 1 ? moveCm.toFixed(1) : Math.round(moveCm)) + " <small>cm</small>", d: bg > 5 ? "very soft" : bg > 2 ? "soft" : bg > 1 ? "a little soft" : "sharp", n: (noise < 3 ? "clean" : noise < 8 ? "a little" : noise < 18 ? "grainy" : "very grainy") + " <small>" + Math.round(noise) + " %</small>" });
      var parts = [];
      if (over > 0.35) parts.push("Too bright by " + over.toFixed(1) + " stops: the sky has gone white.");
      else if (over < -0.35) parts.push("Too dark by " + (-over).toFixed(1) + " stops.");
      else parts.push("The brightness is right.");
      if (moveCm > 4) parts.push("The rider smears: " + Math.round(moveCm) + " cm of movement while the shutter is open.");
      if (noise > 8) parts.push("Noise: too little light reached the sensor, and ISO only turned up the volume.");
      if (bg > 5) parts.push("The wide-open hole leaves the background very soft.");
      if (parts.length === 1 && Math.abs(over) < 0.35) parts.push("Sharp rider, clean picture. Every setting is paying its way.");
      verdict.textContent = parts.join(" ");
      say(fSay(S.N) + ", " + tSay(S.t) + ", " + isoSay(S.iso) + " in " + L.say + ". " + parts.join(" "));
      st.redraw();
    }
    function paint(over, a, bg, smearPx) {
      U.paint(wx, blurOf(bg), 0, 0, W, H, 1, { film: false });
      var copies = Math.max(1, Math.min(40, Math.ceil(smearPx))), x0 = 96, y0 = H - 82;
      for (var i = 0; i < copies; i++) { wx.globalAlpha = copies > 1 ? Math.min(1, 1.6 / copies) : 1; wx.drawImage(rider, x0 + (copies > 1 ? (i / (copies - 1) - 0.5) * smearPx : 0), y0); }
      wx.globalAlpha = 1;
      var src = wx.getImageData(0, 0, W, H), d = src.data, dst = ox.createImageData(W, H), o = dst.data;
      var gain = Math.pow(2, over), photonsPerUnit = P0 * Math.pow(2, a) / 0.18, off = (Math.random() * 60000) | 0;
      for (var p = 0, q = 0; p < d.length; p += 4, q += 3) {
        for (var c = 0; c < 3; c++) {
          var v = LIN[d[p + c]], n = v * photonsPerUnit, sd = Math.sqrt(n + READ * READ);
          var m = (n + sd * GAUSS[(q + c + off) & 65535]) / photonsPerUnit * gain;
          m = (1 - Math.exp(-1.6 * Math.max(0, m))) / 0.8;
          o[p + c] = U.srgb(m);
        }
        o[p + 3] = 255;
      }
      ox.putImageData(dst, 0, 0);
    }
    st.draw = function (g, w, h) { g.imageSmoothingEnabled = true; g.drawImage(out, 0, 0, w, h); U.simTag(g, 8, h - 8); };
    upd();
    return { destroy: function () { st.destroy(); } };
  });

  // ------------------------------------------------------------------ the stops ladder: your camera's three settings against a phone's
  C.sim("l09_stops", function (el, api) {
    var wrap = U.h("div", { class: "sim-wrap" }); el.appendChild(wrap);
    var st = U.stage(wrap, { aspect: function (w) { return w < 560 ? 1.05 : 0.5; }, maxH: 470, cls: "sim-light" });
    var cols = U.h("div", { class: "sim-cols" }); wrap.appendChild(cols);
    var left = U.h("div", { class: "sim-ctls" }), right = U.h("div", { class: "sim-ctls" }); cols.appendChild(left); cols.appendChild(right);
    var S = { sky: "sun", t: 1 / 4000, iso: 50, N: 1.8 };
    var SKY = { sun: "small", hazy: "middle", cloud: "large" };
    var cs = U.choice({ label: "The sky (your camera picks its dot)", value: "sun", options: [{ v: "sun", label: "Full sun: small dot" }, { v: "hazy", label: "Hazy: middle" }, { v: "cloud", label: "Bright cloud: large" }], onChange: function (v) { S.sky = v; balance(); } });
    left.appendChild(cs.el);
    var sT = U.slider({ label: "Phone: shutter time", min: 1 / 16000, max: 1 / 30, log: true, value: S.t, fmt: tSay, onInput: function (v) { S.t = v; upd(); } });
    var sI = U.slider({ label: "Phone: ISO", min: 25, max: 3200, log: true, value: S.iso, fmt: isoSay, onInput: function (v) { S.iso = v; upd(); } });
    left.appendChild(sT.el); left.appendChild(sI.el);
    left.appendChild(U.button("Let the phone balance it", balance, "sim-go"));
    var set = U.readouts(right, [{ k: "a", label: "Aperture" }, { k: "t", label: "Time" }, { k: "i", label: "ISO" }, { k: "s", label: "Total", cls: "sim-hi" }]);
    var verdict = U.h("p", { class: "sim-verdict" }); right.appendChild(verdict);
    var say = U.alt(wrap);
    var ORANGE = "#D9601A";

    function curve() { var dot = SKY[S.sky]; return { dot: dot, N: DOTS[dot], t: 1 / 322, iso: 400 }; }
    function diffs() {
      var c = curve();
      return { c: c, a: 2 * log2(c.N / S.N), t: log2(S.t / c.t), i: log2(S.iso / c.iso) };
    }
    function balance() {
      var D = diffs(), want = -(D.a + D.t), iso = 400 * Math.pow(2, want);
      if (iso < 25) { var tt = S.t * iso / 25; sT.set(U.clamp(tt, 1 / 16000, 1 / 30), true); S.t = sT.get(); D = diffs(); iso = 400 * Math.pow(2, -(D.a + D.t)); }
      sI.set(U.clamp(iso, 25, 3200), true); S.iso = sI.get(); upd();
    }
    function upd() {
      var D = diffs(), sum = D.a + D.t + D.i;
      set({ a: stopsSay(D.a) + " <small>stops</small>", t: stopsSay(D.t) + " <small>stops</small>", i: stopsSay(D.i) + " <small>stops</small>", s: (Math.abs(sum) < 0.2 ? "0" : stopsSay(sum)) + " <small>stops</small>" });
      var v = Math.abs(sum) < 0.2 ? "Balanced: the same light on the picture, spent differently. The phone's big hole buys " + D.a.toFixed(1) + " stops; it spends them on a shorter time and a lower ISO."
        : sum > 0 ? "The phone's picture would be " + sum.toFixed(1) + " stops brighter. Shorten the time or lower the ISO."
        : "The phone's picture would be " + (-sum).toFixed(1) + " stops darker. Lengthen the time or raise the ISO.";
      verdict.textContent = v;
      say("Your camera: " + D.c.dot + " dot, " + fSay(D.c.N) + ", about 1/322 s, ISO 400 film. Phone: f/1.8, " + tSay(S.t) + ", " + isoSay(S.iso) + ". Differences in stops: aperture " + stopsSay(D.a) + ", time " + stopsSay(D.t) + ", ISO " + stopsSay(D.i) + ", total " + stopsSay(sum) + ". " + v);
      st.redraw();
    }
    st.draw = function (g, W, H) {
      var D = diffs(), c = D.c, narrow = W < 560, padL = narrow ? 14 : 120, padR = 16, span = 15, x0 = padL, x1 = W - padR, mid = (x0 + x1) / 2, px = (x1 - x0) / span;
      g.fillStyle = "#fff"; g.fillRect(0, 0, W, H);
      var rows = [
        { name: "Aperture", side: "bigger hole →", ticks: [32, 22, 16, 11, 8, 5.6, 4, 2.8, 2, 1.4], pos: function (N) { return 2 * log2(c.N / N); }, lab: function (N) { return "f/" + N; }, cv: c.N, pv: S.N, cl: fSay(c.N), pl: "f/1.8, fixed" },
        { name: "Time", side: "longer →", ticks: [1 / 16000, 1 / 8000, 1 / 4000, 1 / 2000, 1 / 1000, 1 / 500, 1 / 250, 1 / 125, 1 / 60, 1 / 30, 1 / 15], pos: function (t) { return log2(t / c.t); }, lab: function (t) { return "1/" + Math.round(1 / t); }, cv: c.t, pv: S.t, cl: "1/322", pl: tSay(S.t) },
        { name: "ISO", side: "more sensitive →", ticks: [25, 50, 100, 200, 400, 800, 1600, 3200, 6400], pos: function (i) { return log2(i / c.iso); }, lab: function (i) { return String(i); }, cv: c.iso, pv: S.iso, cl: "400 film", pl: isoSay(S.iso).replace("ISO ", "") }
      ];
      var top = narrow ? 40 : 34, rowH = (H - top - (narrow ? 70 : 54)) / 3;
      U.label(g, "← less light", x0, 18, { color: "#625C53", size: 12, weight: 600 });
      U.label(g, "more light →", x1, 18, { color: "#625C53", size: 12, weight: 600, align: "right" });
      rows.forEach(function (R, k) {
        var y = top + rowH * k + rowH * 0.55;
        if (narrow) U.label(g, R.name, x0, y - rowH * 0.36, { color: "#2D2A26", size: 13, weight: 700 });
        else U.label(g, R.name, 14, y + 5, { color: "#2D2A26", size: 15, weight: 700 });
        g.strokeStyle = "#DDD6CA"; g.lineWidth = 2; g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
        R.ticks.forEach(function (tv, i) {
          var x = mid + R.pos(tv) * px; if (x < x0 - 1 || x > x1 + 1) return;
          g.strokeStyle = "#B9B0A2"; g.lineWidth = 1; g.beginPath(); g.moveTo(x, y - 5); g.lineTo(x, y + 5); g.stroke();
          if (!narrow || i % 2 === 0) U.label(g, R.lab(tv), x, y + 20, { color: "#625C53", size: narrow ? 10 : 11, weight: 400, align: "center" });
        });
        var cx = mid, pxp = U.clamp(mid + R.pos(R.pv) * px, x0, x1);
        if (Math.abs(pxp - cx) > 6) U.arrow(g, cx, y - 14, pxp, y - 14, api.ink || "#333", 2);
        var dv = R.pos(R.pv);
        if (Math.abs(dv) > 0.05) U.label(g, stopsSay(dv), (cx + pxp) / 2, y - 22, { color: api.ink || "#333", size: 12, weight: 700, align: "center" });
        g.fillStyle = ORANGE; g.beginPath(); g.arc(cx, y, 8, 0, 7); g.fill(); g.strokeStyle = "#2D2A26"; g.lineWidth = 1.5; g.stroke();
        g.fillStyle = api.colour; g.beginPath(); g.rect(pxp - 7, y - 7, 14, 14); g.fill(); g.stroke();
      });
      var sum = D.a + D.t + D.i, yb = H - (narrow ? 46 : 30);
      g.fillStyle = ORANGE; g.beginPath(); g.arc(x0 + 8, yb, 7, 0, 7); g.fill();
      U.label(g, "your camera (" + c.dot + " dot, fixed)", x0 + 20, yb + 4, { color: "#2D2A26", size: 12, weight: 600 });
      var lx = narrow ? x0 : x0 + 250, ly = narrow ? yb + 22 : yb;
      g.fillStyle = api.colour; g.fillRect(lx + 1, ly - 7, 14, 14);
      U.label(g, "a phone   ·   total " + (Math.abs(sum) < 0.2 ? "0" : stopsSay(sum)) + " stops", lx + 22, ly + 4, { color: "#2D2A26", size: 12, weight: 600 });
    };
    balance();
    return { destroy: function () { st.destroy(); } };
  });
})();

/* Lesson 9's picture (hero_fig, and its card): the exposure triangle.  The hole, the time and the sensitivity share out one picture's light. */
(function () {
  "use strict";
  var C = window.CURVE; if (!C || !C.fig) return;
  var INK = "#2D2A26", COL = "#C2306B", SOFT = "#F7DDE8";
  function T(x, y, s, size, w, fill, a) { return '<text x="' + x + '" y="' + y + '" font-family="Inter, sans-serif" font-size="' + size + '" font-weight="' + w + '" fill="' + fill + '"' + (a ? ' text-anchor="' + a + '"' : "") + ">" + s + "</text>"; }
  function node(x, y, icon) { return '<circle cx="' + x + '" cy="' + y + '" r="36" fill="#fff" stroke="' + INK + '" stroke-width="3"/>' + icon; }
  C.fig("fig_l09_triangle", function () {
    var b = '<rect width="640" height="360" fill="#fff"/><path d="M320 62 L104 288 L536 288 Z" fill="' + SOFT + '" stroke="' + COL + '" stroke-width="7" stroke-linejoin="round"/>';
    b += node(320, 62, '<circle cx="320" cy="62" r="22" fill="' + INK + '"/><circle cx="320" cy="62" r="9" fill="#fff"/>');
    b += node(104, 288, '<circle cx="104" cy="288" r="22" fill="none" stroke="' + INK + '" stroke-width="3"/><path d="M104 288 V272 M104 288 L116 294" stroke="' + INK + '" stroke-width="3.5" stroke-linecap="round"/>');
    var g = ""; [[-10, -9], [6, -12], [12, 3], [-3, 4], [-13, 10], [4, 14]].forEach(function (p) { g += '<circle cx="' + (536 + p[0]) + '" cy="' + (288 + p[1]) + '" r="4.5" fill="' + INK + '"/>'; });
    b += node(536, 288, g);
    b += T(370, 58, "the hole", 26, 800, INK) + T(370, 86, "f/16 … f/1.8", 19, 600, "#625C53") +
      T(104, 350, "the time", 24, 800, INK, "middle") + T(536, 350, "the sensitivity", 24, 800, INK, "middle") +
      T(320, 206, "one picture's light", 24, 800, COL, "middle") + T(320, 236, "give a stop here, take one there", 18, 600, "#625C53", "middle");
    return C.U.svg(640, 360, b, "The exposure triangle. The size of the hole, the time it stays open and how sensitive the film or sensor is share out one picture's worth of light: give a stop to one and you take a stop from another.");
  });
})();
