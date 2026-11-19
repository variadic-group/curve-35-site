/* CURVE 35 lessons: shared pieces for the interactive sims and figures.
   Loaded on every page after js/data.js and before the sims/lNN.js files and js/lesson.js.
   CURVE.sim(id, fn)  registers a sim:    fn(el, api) builds into el, returns {destroy(){}}.
   CURVE.fig(id, fn)  registers a figure: fn() returns an SVG string.
   CURVE.U            small helpers: sliders, choice buttons, canvases, a simulated scene, blur, exposure.
   Every number about the camera comes from course/FACTS.md (CURVE.FACTS). */
(function () {
  "use strict";
  var C = window.CURVE = window.CURVE || {};
  var REG = window.CURVE_REG = window.CURVE_REG || { sims: {}, figs: {} };
  C.sim = function (id, fn) { REG.sims[id] = fn; };
  C.fig = function (id, fn) { REG.figs[id] = fn; };
  C.sims = REG.sims; C.figs = REG.figs;

  // ------------------------------------------------------------------ the camera's numbers (course/FACTS.md, model ONE-135 v2.14)
  C.FACTS = {
    lens_mm: 32, lens_across_mm: 12, focus_m: 3.7,
    dots: { small: { mm: 1.96, f: 16.4, say: "f/16" }, middle: { mm: 2.88, f: 11.1, say: "f/11" }, large: { mm: 3.34, f: 9.6, say: "f/9.5" } },
    shutter_s: 1 / 322, film_pitch_mm: 4.75, frame_holes: 8, frame_mm: 38, picture: { w: 36, h: 24 }, curve_r_mm: 32,
    sharp_from_m: { small: 1.0, middle: 1.3, large: 1.5 }, sharp_far_pct: { small: 99, large: 62 },
    pinhole: { mm: 0.24, dist_mm: 28.9, f: 120, counts_iso400: { sun: "open, shut", cloud: 1, shade: 3, window: 40 } },
    time_counts_small_iso400: { window: 1, lamps: 5, dim: 20 },
    iso: 400, latitude: { under: 1, over: 3 }, pieces: 9, size_mm: [127, 41, 70], plastic_g: 117, print_h: 9.3,
    wavelength_mm: 0.00055,
    // which dot, ISO 400 (FACTS) and how far off by the model (build/log_dial_exposure.txt part 2), in steps of light; + is more
    which_dot_iso400: [{ sky: "full sun", dot: "small", off: 0.5 }, { sky: "hazy sun", dot: "middle", off: 0.6 }, { sky: "bright cloud", dot: "large", off: 0.0 }],
    turns_24: 25, turns_36: 33
  };

  // ------------------------------------------------------------------ small DOM helpers
  var U = C.U = {};
  U.h = function (tag, attrs, html) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "class") e.className = attrs[k];
      else if (k === "style") e.style.cssText = attrs[k];
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== false && attrs[k] != null) e.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    }
    if (html != null) e.innerHTML = html;
    return e;
  };
  U.esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  U.fmt = function (x, d) { if (!isFinite(x)) return "∞"; return String(+x.toFixed(d == null ? 2 : d)); };
  U.fix = function (x, d) { return isFinite(x) ? x.toFixed(d) : "∞"; };
  U.clamp = function (x, a, b) { return Math.max(a, Math.min(b, x)); };
  U.reduced = function () { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); };
  var uid = 0; U.id = function (p) { return (p || "s") + "-" + (++uid); };

  /* A labelled slider.  o: {label, min, max, step, value, fmt(v) -> text, log: true for a log scale, onInput(v), hint}
     Returns {el, input, get(), set(v, silent)}. With log, the input runs 0..1000 and maps onto min..max. */
  U.slider = function (o) {
    var id = U.id("rng"), wrap = U.h("div", { class: "sim-ctl sim-slider" });
    var lab = U.h("label", { for: id }, '<span class="sim-lab">' + U.esc(o.label) + '</span><output class="sim-val" for="' + id + '"></output>');
    var inp = U.h("input", { type: "range", id: id, min: o.log ? 0 : o.min, max: o.log ? 1000 : o.max, step: o.log ? 1 : (o.step || "any") });
    wrap.appendChild(lab); wrap.appendChild(inp);
    if (o.hint) wrap.appendChild(U.h("span", { class: "sim-hint" }, o.hint));
    var out = lab.querySelector("output"), cur = o.value;
    function toInput(v) { return o.log ? Math.round(1000 * Math.log(v / o.min) / Math.log(o.max / o.min)) : v; }
    function fromInput(x) { return o.log ? o.min * Math.pow(o.max / o.min, x / 1000) : +x; }
    function show() { var t = o.fmt ? o.fmt(cur) : String(cur); out.textContent = t; inp.setAttribute("aria-valuetext", t); }
    inp.value = toInput(cur); show();
    inp.addEventListener("input", function () { cur = fromInput(+inp.value); show(); if (o.onInput) o.onInput(cur); });
    return { el: wrap, input: inp, get: function () { return cur; }, set: function (v, silent) { cur = U.clamp(v, o.min, o.max); inp.value = toInput(cur); show(); if (!silent && o.onInput) o.onInput(cur); } };
  };

  /* A row of choice buttons (one pressed at a time).  o: {label, options: [{v, label}], value, onChange(v)} */
  U.choice = function (o) {
    var wrap = U.h("div", { class: "sim-ctl sim-choice", role: "group", "aria-label": o.label });
    if (o.label) wrap.appendChild(U.h("span", { class: "sim-lab" }, U.esc(o.label)));
    var row = U.h("div", { class: "sim-seg" }); wrap.appendChild(row);
    var btns = o.options.map(function (op) {
      var b = U.h("button", { type: "button", class: "sim-btn" + (op.cls ? " " + op.cls : ""), "aria-pressed": String(op.v === o.value) }, op.label);
      b.addEventListener("click", function () { set(op.v); });
      row.appendChild(b); return b;
    });
    var cur = o.value;
    function set(v, silent) { cur = v; btns.forEach(function (b, i) { b.setAttribute("aria-pressed", String(o.options[i].v === v)); }); if (!silent && o.onChange) o.onChange(v); }
    return { el: wrap, get: function () { return cur; }, set: set };
  };

  U.rng = function (seed) { var x = seed || 1; return function () { x = (x * 1664525 + 1013904223) % 4294967296; return x / 4294967296; }; };
  U.poisson = function (lam, rnd) { var L = Math.exp(-lam), k = 0, p = 1; do { k++; p *= rnd(); } while (p > L && k < 60); return k - 1; };
  U.button = function (label, fn, cls) { var b = U.h("button", { type: "button", class: "sim-btn " + (cls || "") }, label); b.addEventListener("click", fn); return b; };

  /* The text alternative: a live line under every sim that says what the picture shows now. */
  U.alt = function (el) { var p = U.h("p", { class: "sim-alt", "aria-live": "polite" }); el.appendChild(p); return function (t) { p.textContent = t; }; };

  /* Readouts: a row of big numbers.  U.readouts(el, [{k:'f', label:'f-number'}]) -> set({f:'f/120'}) */
  U.readouts = function (el, items) {
    var row = U.h("dl", { class: "sim-read" }), cells = {};
    items.forEach(function (it) {
      var d = U.h("div", { class: "sim-r" + (it.cls ? " " + it.cls : "") });
      d.appendChild(U.h("dt", null, U.esc(it.label))); cells[it.k] = U.h("dd", null, "–"); d.appendChild(cells[it.k]); row.appendChild(d);
    });
    el.appendChild(row);
    return function (vals) { for (var k in vals) if (cells[k]) cells[k].innerHTML = vals[k]; };
  };

  /* A canvas that fills its box at the screen's pixel density.  o: {aspect (h/w), max (css px), min}
     Returns {cv, ctx, w, h, draw}: set .draw = fn(ctx, w, h); it runs on every resize; call st.redraw(). */
  U.stage = function (el, o) {
    o = o || {};
    var box = U.h("div", { class: "sim-stage" + (o.cls ? " " + o.cls : "") }), cv = U.h("canvas", { "aria-hidden": "true" });
    box.appendChild(cv); el.appendChild(box);
    var st = { cv: cv, ctx: cv.getContext("2d"), w: 0, h: 0, box: box, draw: null };
    function size() {
      var w = Math.max(o.min || 240, Math.min(o.max || 1200, box.clientWidth || 600)), h = Math.round(w * ((typeof o.aspect === "function" ? o.aspect(w) : o.aspect) || 0.6));
      if (o.maxH && h > o.maxH) h = o.maxH;
      var d = Math.min(2, window.devicePixelRatio || 1);
      if (w !== st.w || h !== st.h) { st.w = w; st.h = h; cv.width = Math.round(w * d); cv.height = Math.round(h * d); cv.style.width = w + "px"; cv.style.height = h + "px"; st.ctx.setTransform(d, 0, 0, d, 0, 0); }
      st.redraw();
    }
    var raf = 0;
    st.redraw = function () { if (raf) return; raf = requestAnimationFrame(function () { raf = 0; if (st.draw && st.w) { st.ctx.clearRect(0, 0, st.w, st.h); st.draw(st.ctx, st.w, st.h); } }); };
    st.now = function () { if (st.draw && st.w) { st.ctx.clearRect(0, 0, st.w, st.h); st.draw(st.ctx, st.w, st.h); } };
    var ro = window.ResizeObserver ? new ResizeObserver(size) : null;
    if (ro) ro.observe(box); else window.addEventListener("resize", size);
    setTimeout(size, 0);
    st.destroy = function () { if (ro) ro.disconnect(); else window.removeEventListener("resize", size); if (raf) cancelAnimationFrame(raf); };
    return st;
  };

  /* Pointer dragging on an element: fn(x, y, phase) with x, y in the element's CSS pixels. */
  U.drag = function (target, fn) {
    var on = false;
    function pos(e) { var r = target.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
    target.style.touchAction = "none";
    target.addEventListener("pointerdown", function (e) { on = true; try { target.setPointerCapture(e.pointerId); } catch (x) { } var p = pos(e); fn(p[0], p[1], "down", e); });
    target.addEventListener("pointermove", function (e) { var p = pos(e); fn(p[0], p[1], on ? "move" : "hover", e); });
    target.addEventListener("pointerup", function (e) { if (!on) return; on = false; var p = pos(e); fn(p[0], p[1], "up", e); });
    target.addEventListener("pointercancel", function () { on = false; });
  };

  U.label = function (ctx, text, x, y, o) {
    o = o || {};
    ctx.save(); ctx.font = (o.weight || 600) + " " + (o.size || 12) + "px Inter, system-ui, sans-serif"; ctx.textAlign = o.align || "left"; ctx.textBaseline = o.base || "alphabetic";
    if (o.bg) { var w = ctx.measureText(text).width, pad = 4, xx = o.align === "center" ? x - w / 2 : o.align === "right" ? x - w : x; ctx.fillStyle = o.bg; ctx.fillRect(xx - pad, y - (o.size || 12) - 1, w + pad * 2, (o.size || 12) + 6); }
    ctx.fillStyle = o.color || "#fff"; ctx.fillText(text, x, y); ctx.restore();
  };
  U.arrow = function (ctx, x1, y1, x2, y2, col, w) {
    var a = Math.atan2(y2 - y1, x2 - x1), s = 6 + (w || 1.5) * 2;
    ctx.save(); ctx.strokeStyle = ctx.fillStyle = col; ctx.lineWidth = w || 1.5; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * s * 0.6, y2 - Math.sin(a) * s * 0.6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - s * Math.cos(a - 0.4), y2 - s * Math.sin(a - 0.4)); ctx.lineTo(x2 - s * Math.cos(a + 0.4), y2 - s * Math.sin(a + 0.4)); ctx.closePath(); ctx.fill(); ctx.restore();
  };

  // ------------------------------------------------------------------ pictures as numbers: a simulated scene, blur, exposure
  /* Img: {w, h, d: Float32Array of linear RGB, 3 per pixel} */
  function Img(w, h) { this.w = w; this.h = h; this.d = new Float32Array(w * h * 3); }
  U.Img = Img;
  function lin(c) { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function srgb(x) { x = x <= 0 ? 0 : x >= 1 ? 1 : x; return Math.round(255 * (x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055)); }
  var LUT = new Uint8Array(4097); for (var i = 0; i <= 4096; i++) LUT[i] = srgb(i / 4096);
  U.srgb = srgb; U.lin = lin;

  /* The test scene (simulated): a sky, a cloud, a house with a dark doorway, a tree, a path, a kid with a red kite.
     Drawn with the canvas, then read back as linear light.  Bright things (sky, cloud) are near 1, the doorway near 0.03. */
  var sceneCache = {};
  U.scene = function (w, h, kind) {
    var key = w + "x" + h + (kind || "");
    if (sceneCache[key]) return sceneCache[key];
    var cv = document.createElement("canvas"); cv.width = w; cv.height = h; var g = cv.getContext("2d"), s = w / 360;
    var sky = g.createLinearGradient(0, 0, 0, h * 0.62); sky.addColorStop(0, "#7fb6e8"); sky.addColorStop(1, "#cfe5f4"); g.fillStyle = sky; g.fillRect(0, 0, w, h);
    g.fillStyle = "#fbfbf8"; [[70, 46, 22], [92, 40, 26], [114, 48, 20], [96, 54, 18]].forEach(function (c) { g.beginPath(); g.arc(c[0] * s, c[1] * s, c[2] * s, 0, 7); g.fill(); });
    g.fillStyle = "#fff4c2"; g.beginPath(); g.arc(300 * s, 34 * s, 13 * s, 0, 7); g.fill();
    g.fillStyle = "#7da35a"; g.beginPath(); g.moveTo(0, 150 * s); g.quadraticCurveTo(140 * s, 128 * s, 360 * s, 146 * s); g.lineTo(360 * s, h); g.lineTo(0, h); g.fill();
    g.fillStyle = "#5e8a43"; g.fillRect(0, 186 * s, w, h);
    g.fillStyle = "#d8c9a8"; g.beginPath(); g.moveTo(178 * s, h); g.lineTo(196 * s, 168 * s); g.lineTo(206 * s, 168 * s); g.lineTo(240 * s, h); g.fill();
    // the house
    g.fillStyle = "#a9a39a"; g.fillRect(150 * s, 104 * s, 96 * s, 66 * s);
    g.fillStyle = "#b8452c"; g.beginPath(); g.moveTo(142 * s, 106 * s); g.lineTo(198 * s, 70 * s); g.lineTo(254 * s, 106 * s); g.fill();
    g.fillStyle = "#0b0a0a"; g.fillRect(190 * s, 128 * s, 18 * s, 42 * s);
    g.fillStyle = "#e9eef0"; g.fillRect(160 * s, 118 * s, 20 * s, 18 * s); g.fillRect(218 * s, 118 * s, 20 * s, 18 * s);
    g.strokeStyle = "#5a5650"; g.lineWidth = 2 * s; g.strokeRect(160 * s, 118 * s, 20 * s, 18 * s); g.strokeRect(218 * s, 118 * s, 20 * s, 18 * s);
    // the tree
    g.fillStyle = "#5b3b22"; g.fillRect(70 * s, 120 * s, 10 * s, 56 * s);
    g.fillStyle = "#24502a"; [[75, 104, 30], [56, 118, 20], [94, 118, 20], [75, 84, 20]].forEach(function (c) { g.beginPath(); g.arc(c[0] * s, c[1] * s, c[2] * s, 0, 7); g.fill(); });
    // a kid with a kite
    g.fillStyle = "#f2c94c"; g.fillRect(286 * s, 150 * s, 10 * s, 22 * s); g.fillStyle = "#1d1d1d"; g.fillRect(286 * s, 172 * s, 4 * s, 14 * s); g.fillRect(292 * s, 172 * s, 4 * s, 14 * s);
    g.fillStyle = "#e0b48f"; g.beginPath(); g.arc(291 * s, 144 * s, 6 * s, 0, 7); g.fill();
    g.strokeStyle = "#333"; g.lineWidth = 1 * s; g.beginPath(); g.moveTo(296 * s, 152 * s); g.lineTo(330 * s, 74 * s); g.stroke();
    g.fillStyle = "#e33b2e"; g.beginPath(); g.moveTo(330 * s, 60 * s); g.lineTo(342 * s, 74 * s); g.lineTo(330 * s, 90 * s); g.lineTo(318 * s, 74 * s); g.fill();
    var px = g.getImageData(0, 0, w, h).data, im = new Img(w, h), L = new Float32Array(256);
    for (var k = 0; k < 256; k++) L[k] = lin(k);
    for (var p = 0, q = 0; p < px.length; p += 4, q += 3) { im.d[q] = L[px[p]]; im.d[q + 1] = L[px[p + 1]]; im.d[q + 2] = L[px[p + 2]]; }
    sceneCache[key] = im; return im;
  };

  /* Blur that looks like an out-of-focus disc of the given diameter in pixels (three box passes ~ a soft disc). */
  function boxPass(src, dst, w, h, r, horiz) {
    var n = horiz ? w : h, m = horiz ? h : w, step = horiz ? 3 : w * 3, inv = 1 / (2 * r + 1);
    for (var j = 0; j < m; j++) {
      var base = horiz ? j * w * 3 : j * 3;
      for (var c = 0; c < 3; c++) {
        var acc = 0, b = base + c, first = src[b], last = src[b + (n - 1) * step];
        for (var t = -r; t <= r; t++) acc += src[b + U.clamp(t, 0, n - 1) * step];
        for (var i2 = 0; i2 < n; i2++) {
          dst[b + i2 * step] = acc * inv;
          var add = i2 + r + 1, rem = i2 - r;
          acc += (add < n ? src[b + add * step] : last) - (rem >= 0 ? src[b + rem * step] : first);
        }
      }
    }
  }
  U.blur = function (im, diaPx) {
    var out = new Img(im.w, im.h); out.d.set(im.d);
    if (!(diaPx > 0.8)) return out;
    var sigma = diaPx / 4, r = Math.max(1, Math.round(Math.sqrt(12 * sigma * sigma / 3 + 1) / 2 - 0.5)), tmp = new Float32Array(out.d.length);
    for (var k = 0; k < 3; k++) { boxPass(out.d, tmp, im.w, im.h, r, true); boxPass(tmp, out.d, im.w, im.h, r, false); }
    return out;
  };
  /* A cache of blurred copies, by diameter rounded to a quarter pixel. */
  U.blurCache = function (im) { var c = {}; return function (dia) { var k = Math.round(dia * 4) / 4; if (!c[k]) c[k] = U.blur(im, k); return c[k]; }; };

  /* Paint an Img onto a canvas context at (x, y, w, h) with an exposure gain.
     o: {flip: turn it upside down and left-right (as a hole or lens does), neg: show as a negative, mask: [r,g,b] orange of a colour negative,
         grey: black and white, film: a soft shoulder like film or an eye (default true), vignette: 0..1} */
  var paintCv = document.createElement("canvas"), paintCx = paintCv.getContext("2d");
  U.paint = function (ctx, im, x, y, w, h, gain, o) {
    o = o || {}; gain = gain == null ? 1 : gain;
    if (paintCv.width !== im.w || paintCv.height !== im.h) { paintCv.width = im.w; paintCv.height = im.h; }
    var id = paintCx.createImageData(im.w, im.h), out = id.data, d = im.d, n = im.w * im.h, W = im.w, H = im.h;
    for (var p = 0; p < n; p++) {
      var src = o.flip ? (n - 1 - p) : p, q = src * 3, r = d[q] * gain, g = d[q + 1] * gain, b = d[q + 2] * gain;
      if (o.vignette) { var xx = (p % W) / W - 0.5, yy = Math.floor(p / W) / H - 0.5, v = 1 - o.vignette * (xx * xx + yy * yy) * 2.2; r *= v; g *= v; b *= v; }
      if (o.grey) { r = g = b = 0.2126 * r + 0.7152 * g + 0.0722 * b; }
      if (o.film !== false) { r = 1 - Math.exp(-1.6 * r); g = 1 - Math.exp(-1.6 * g); b = 1 - Math.exp(-1.6 * b); r /= 0.8; g /= 0.8; b /= 0.8; }
      if (o.neg) { r = 1 - r; g = 1 - g; b = 1 - b; if (o.mask) { r = r * o.mask[0]; g = g * o.mask[1]; b = b * o.mask[2]; } }
      var k = p * 4;
      out[k] = LUT[(r <= 0 ? 0 : r >= 1 ? 1 : r) * 4096 | 0]; out[k + 1] = LUT[(g <= 0 ? 0 : g >= 1 ? 1 : g) * 4096 | 0]; out[k + 2] = LUT[(b <= 0 ? 0 : b >= 1 ? 1 : b) * 4096 | 0]; out[k + 3] = 255;
    }
    paintCx.putImageData(id, 0, 0);
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.drawImage(paintCv, x, y, w, h); ctx.restore();
  };

  /* The small "simulated" tag on any picture that stands for a photograph. */
  U.simTag = function (ctx, x, y, text) { U.label(ctx, text || "simulated", x, y, { size: 11, color: "#1b1a18", bg: "rgba(255,255,255,0.85)", weight: 600 }); };

  /* Run fn the first time el comes into view (and every time, if again is true).  Returns a stop function. */
  U.onVisible = function (el, fn, again) {
    if (!window.IntersectionObserver) { fn(true); return function () { }; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { fn(true); if (!again) io.disconnect(); } else if (again) fn(false); }); }, { rootMargin: "120px" });
    io.observe(el); return function () { io.disconnect(); };
  };


  // ------------------------------------------------------------------ the camera's optics and film, as simple honest models
  /* Sharp enough for a postcard: a blur on the film under 0.045 mm.  With the lens set for 3.7 m this one number gives FACTS' "sharp from
     1.0 m (small dot), 1.3 m (middle), 1.5 m (large)".  Across the picture, a fit to the model's ray tracing (build/focus.json) on the curved film:
     extra blur = 0.0245 x hole width x (distance from the middle / half the diagonal)^1.25, which gives FACTS' 99 % (small dot) and 62 % (large). */
  C.OPTICS = {
    sharp_mm: 0.045, f: 32, focus_mm: 3700,
    v: function (u_mm) { return isFinite(u_mm) ? 1 / (1 / 32 - 1 / u_mm) : 32; },
    defocus: function (D, u_mm) { var v = C.OPTICS.v(u_mm), v0 = C.OPTICS.v(3700); return D * Math.abs(v - v0) / v; },
    residual: function (D, rho) { return 0.0245 * D * Math.pow(Math.max(0, rho), 1.25); },
    share: function (D, flat) {
      var n = 0, ok = 0;
      for (var x = -17.75; x < 18; x += 0.5) for (var y = -11.75; y < 12; y += 0.5) {
        var rho = Math.hypot(x, y) / Math.hypot(18, 12), th = Math.atan(Math.abs(x) / 32);
        var b = flat ? D * (1 - Math.cos(th)) + C.OPTICS.residual(D, rho) * 0.5 : C.OPTICS.residual(D, rho);
        n++; if (b < 0.045) ok++;
      }
      return ok / n;
    }
  };

  /* Film, simply: it records light from 1 step too little to 3 steps too much of a normal picture (colour negative, build/exposure.json),
     and the lab prints it back to normal.  Outside that window the darks go flat (too little) or the brights go flat (too much).
     U.develop(img, steps, colour) -> {neg, print}: two Imgs of display light, for U.paint(..., {film: false}). */
  function smax(a, b, k) { return (a + b + Math.sqrt((a - b) * (a - b) + k * k)) / 2; }
  function smin(a, b, k) { return (a + b - Math.sqrt((a - b) * (a - b) + k * k)) / 2; }
  U.develop = function (im, steps, colour) {
    var T = -6.6, S = 3.0, k = 0.7, n = im.w * im.h, neg = new Img(im.w, im.h), pr = new Img(im.w, im.h), mask = [1.0, 0.62, 0.36];
    for (var p = 0; p < n * 3; p += 3) {
      var Y = 0.2126 * im.d[p] + 0.7152 * im.d[p + 1] + 0.0722 * im.d[p + 2];
      for (var c = 0; c < 3; c++) {
        var v = colour ? im.d[p + c] : Y, L = Math.log(Math.max(v, 0.0006)) / Math.LN2, e = smin(smax(L + steps, T, k), S, k);
        var dens = (e - T) / (S - T);                        // 0 clear film .. 1 densest
        neg.d[p + c] = (0.04 + 0.92 * (1 - dens)) * (colour ? mask[c] : 1);
        var out = e - steps; pr.d[p + c] = Math.pow(2, out) * 0.95;   // the print: the lab undoes the overall shift
      }
    }
    return { neg: neg, print: pr };
  };

  /* SVG helpers for figures */
  U.svg = function (w, h, body, title) {
    return '<svg class="lfig" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + U.esc(title || "") + '" xmlns="http://www.w3.org/2000/svg">' + (title ? "<title>" + U.esc(title) + "</title>" : "") + body + "</svg>";
  };
  U.colours = { ink: "#2D2A26", ink2: "#625C53", paper: "#F6F3ED", rule: "#DDD6CA", plate: "#D9601A", sun: "#F2B807", ray: "#F5A623", blue: "#2B6CD8", green: "#1F8A70", red: "#D23F31", glass: "#9FD3E6", dark: "#16130F" };
})();
