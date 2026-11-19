/* CURVE 35: the camera in 3D.  three.js (self-hosted, js/three.min.js); meshes from media/3d/camera.json (made by site/assets3d.py).
   Two uses, one loader:
   Camera3D.hero(box, data)   -> { destroy() }  the closed camera in the hero.  It turns gently toward the pointer; on touch it turns slowly by itself.
                                                 With reduced motion, or with no WebGL, the still picture in the box stays and nothing moves.
   Camera3D.viewer(sec, data) -> { destroy() }  the big viewer.  A slider (0..4) takes it apart stage by stage; the stage buttons jump to a stage;
                                                 dragging the picture turns it.  Every change is smoothed (lerp) and drawn in one requestAnimationFrame loop
                                                 that runs only while something is still moving.  Reduced motion: no smoothing, it jumps.  No WebGL: the still.
   Nothing here reads layout on scroll; the canvas is sized only by a ResizeObserver. */
(function () {
  "use strict";
  var threeP = null;
  function loadThree(url) {
    if (window.THREE) return Promise.resolve(window.THREE);
    if (threeP) return threeP;
    threeP = new Promise(function (ok, no) {
      var s = document.createElement("script"); s.src = url; s.async = true;
      s.onload = function () { window.THREE ? ok(window.THREE) : no(new Error("three.js did not load")); };
      s.onerror = function () { threeP = null; no(new Error("three.js did not load")); };
      document.head.appendChild(s);
    });
    return threeP;
  }
  var meshP = null;
  function loadMeshes(src) {
    if (!meshP) meshP = fetch(src).then(function (r) { if (!r.ok) throw new Error("meshes: " + r.status); return r.json(); }).catch(function (e) { meshP = null; throw e; });
    return meshP;
  }
  function webgl() {
    try { var c = document.createElement("canvas"); return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl"))); } catch (e) { return false; }
  }
  function reducedMotion() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
  function b64(s, Type) {
    var bin = atob(s), n = bin.length, u = new Uint8Array(n);
    for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return new Type(u.buffer);
  }
  function clamp(x, a, b) { a = a == null ? 0 : a; b = b == null ? 1 : b; return x < a ? a : x > b ? b : x; }
  function ease(x) { x = clamp(x); return x * x * (3 - 2 * x); }
  // model axes (x right, y toward the subject, z up) -> three.js axes (y up): (x, z, -y)
  function toThree(v) { return [v[0], v[2], -v[1]]; }

  // one scene from the mesh file
  function makeScene(THREE, J) {
    var scene = new THREE.Scene();
    // r155+ lights are physical: the old (legacy) look is the same intensities times pi, so nothing has to switch the renderer to legacy mode
    var k = THREE.REVISION && Number(THREE.REVISION) >= 155 ? Math.PI : 1;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8078, 0.8 * k));
    var key = new THREE.DirectionalLight(0xffffff, 0.8 * k); key.position.set(-120, 200, -160); scene.add(key);
    var fill = new THREE.DirectionalLight(0xffffff, 0.35 * k); fill.position.set(160, 60, 120); scene.add(fill);
    var parts = [];
    J.parts.forEach(function (P) {
      var q = b64(P.v, Uint16Array), idx = b64(P.i, P.idx32 ? Uint32Array : Uint16Array), pos = new Float32Array(q.length);
      for (var k = 0; k < q.length; k += 3) {
        var x = P.lo[0] + q[k] / 65535 * P.span[0], y = P.lo[1] + q[k + 1] / 65535 * P.span[1], z = P.lo[2] + q[k + 2] / 65535 * P.span[2];
        pos[k] = x; pos[k + 1] = z; pos[k + 2] = -y;
      }
      var g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setIndex(new THREE.BufferAttribute(idx, 1));
      var col = new THREE.Color(P.color); if (!(THREE.ColorManagement && THREE.ColorManagement.enabled) && col.convertSRGBToLinear) col.convertSRGBToLinear();   // r152+ converts hex strings itself
      var isLens = P.key === "lens";
      var mat = new THREE.MeshStandardMaterial({ color: col, flatShading: true, roughness: isLens ? 0.15 : 0.62, metalness: 0, transparent: true, opacity: isLens ? 0.9 : 1 });
      var mesh = new THREE.Mesh(g, mat);
      var edges = new THREE.LineSegments(new THREE.EdgesGeometry(g, 28), new THREE.LineBasicMaterial({ color: P.key === "body" ? 0x6b6661 : 0x2d2a26, transparent: true, opacity: P.key === "body" ? 0.55 : 0.35 }));
      var grp = new THREE.Group(); grp.add(mesh); grp.add(edges); scene.add(grp);
      parts.push({ key: P.key, stage: P.stage, ex: toThree(P.explode), grp: grp, mats: [mat, edges.material], base: [mat.opacity, edges.material.opacity], geos: [g, edges.geometry] });
    });
    return { scene: scene, parts: parts };
  }
  function makeRenderer(THREE, box, cls) {
    var r = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
    r.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    if ("outputColorSpace" in r && THREE.SRGBColorSpace) r.outputColorSpace = THREE.SRGBColorSpace; else r.outputEncoding = THREE.sRGBEncoding;
    var c = r.domElement; c.className = cls; c.setAttribute("aria-hidden", "true");
    box.appendChild(c);
    return r;
  }
  // the camera's eye: az/el in degrees around the model's middle, far enough back to fit `radius`
  function aim(cam, center, az, el, radius) {
    az *= Math.PI / 180; el *= Math.PI / 180;
    var fit = radius / Math.sin(cam.fov * Math.PI / 360) / Math.min(1, cam.aspect * 0.92);
    var t = toThree([Math.sin(az) * Math.cos(el), Math.cos(az) * Math.cos(el), Math.sin(el)]);
    cam.position.set(center.x + t[0] * fit, center.y + t[1] * fit, center.z + t[2] * fit); cam.lookAt(center);
  }
  function disposeAll(renderer, S) {
    if (S) S.parts.forEach(function (o) { o.geos.forEach(function (g) { g.dispose(); }); o.mats.forEach(function (m) { m.dispose(); }); });
    if (renderer) { renderer.dispose(); if (renderer.forceContextLoss) renderer.forceContextLoss(); var c = renderer.domElement; if (c && c.parentNode) c.parentNode.removeChild(c); }
  }
  // runs while visible; pauses offscreen and in hidden tabs
  function visibility(el, cb) {
    var io = null, on = true;
    if (window.IntersectionObserver) { io = new IntersectionObserver(function (es) { on = es[es.length - 1].isIntersecting; cb(on && !document.hidden); }, { rootMargin: "80px" }); io.observe(el); }
    function vis() { cb(on && !document.hidden); }
    document.addEventListener("visibilitychange", vis);
    return function () { if (io) io.disconnect(); document.removeEventListener("visibilitychange", vis); };
  }

  // ------------------------------------------------------------------ the hero: closed, turning toward the pointer
  function hero(box, data) {
    var dead = false, renderer = null, S = null, raf = 0, offs = [];
    function still(why) { box.setAttribute("data-why", why); }
    if (reducedMotion()) { still("reduced-motion"); return { destroy: function () {} }; }
    if (!webgl()) { still("no-webgl"); return { destroy: function () {} }; }
    var touch = window.matchMedia && window.matchMedia("(hover: none)").matches;
    Promise.all([loadThree(data.three), loadMeshes(data.src)]).then(function (res) {
      if (dead) return;
      var THREE = res[0];
      try { renderer = makeRenderer(THREE, box, "h3d-canvas"); } catch (e) { still("no-webgl"); return; }
      S = makeScene(THREE, res[1]);
      var cam = new THREE.PerspectiveCamera(26, 1, 1, 4000), center = new THREE.Vector3(0, 2, -9);
      var BASE = { az: -32, el: 18 }, cur = { az: BASE.az - 30, el: BASE.el }, tgt = { az: BASE.az, el: BASE.el };
      var running = false, visible = true, t0 = performance.now();
      function size() { var w = box.clientWidth, h = box.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); kick(); }
      function frame(now) {
        raf = 0; if (dead || !visible) { running = false; return; }
        if (touch) tgt.az = BASE.az + 22 * Math.sin((now - t0) / 4200);       // a slow turn by itself
        cur.az += (tgt.az - cur.az) * 0.07; cur.el += (tgt.el - cur.el) * 0.07;
        aim(cam, center, cur.az, cur.el, 64); renderer.render(S.scene, cam);
        if (touch || Math.abs(tgt.az - cur.az) > 0.02 || Math.abs(tgt.el - cur.el) > 0.02) raf = requestAnimationFrame(frame); else running = false;
      }
      function kick() { if (!running && visible && !dead) { running = true; raf = requestAnimationFrame(frame); } }
      function onMove(e) {
        var x = e.clientX / (window.innerWidth || 1) - 0.5, y = e.clientY / (window.innerHeight || 1) - 0.5;
        tgt.az = BASE.az + clamp(x, -0.5, 0.5) * 56; tgt.el = BASE.el - clamp(y, -0.5, 0.5) * 18; kick();
      }
      if (!touch) { window.addEventListener("pointermove", onMove, { passive: true }); offs.push(function () { window.removeEventListener("pointermove", onMove); }); }
      var ro = window.ResizeObserver ? new ResizeObserver(size) : null; if (ro) { ro.observe(box); offs.push(function () { ro.disconnect(); }); }
      offs.push(visibility(box, function (v) { visible = v; if (v) kick(); }));
      size(); kick();
      box.classList.add("h3d-ready"); still("live");
    }).catch(function (e) { if (!dead) { still("load-failed"); if (window.console) console.warn("CURVE 35: 3D hero off (" + e.message + ")"); } });
    return { destroy: function () { dead = true; if (raf) cancelAnimationFrame(raf); offs.forEach(function (f) { f(); }); disposeAll(renderer, S); } };
  }

  // ------------------------------------------------------------------ the viewer: take it apart with a slider, turn it by dragging
  function viewer(sec, data) {
    var dead = false, renderer = null, S = null, raf = 0, offs = [];
    var range = sec.querySelector(".x3-range"), stage = sec.querySelector(".x3-stage");
    var btns = Array.prototype.slice.call(sec.querySelectorAll("[data-go]")), caps = Array.prototype.slice.call(sec.querySelectorAll(".x3-cap"));
    var reduce = reducedMotion();
    function label(v) {      // which stage the slider is on: 0 closed, 1..4
      var i = Math.round(v); caps.forEach(function (c) { c.hidden = Number(c.dataset.i) !== i; });
      btns.forEach(function (b) { b.setAttribute("aria-pressed", String(Number(b.dataset.go) === i)); });
      if (range) range.setAttribute("aria-valuetext", (caps[i] && caps[i].getAttribute("data-say")) || String(i));
    }
    function still(why) { sec.classList.add("x3-static"); sec.setAttribute("data-why", why); }
    var api = { set: null };
    // the controls work (they move the captions) even before, or without, the 3D
    function onInput() { var v = Number(range.value); label(v); if (api.set) api.set(v); }
    if (range) { range.addEventListener("input", onInput); offs.push(function () { range.removeEventListener("input", onInput); }); }
    btns.forEach(function (b) {
      function go() { var v = Number(b.dataset.go); if (range) range.value = String(v); label(v); if (api.set) api.set(v); }
      b.addEventListener("click", go); offs.push(function () { b.removeEventListener("click", go); });
    });
    label(range ? Number(range.value) : 0);
    // keys on the slider: arrows and Page keys go one stage; Home and End to closed and fully open
    function onKey(e) {
      var v = Number(range.value), n = null;
      if (e.key === "ArrowRight" || e.key === "ArrowUp" || e.key === "PageUp") n = Math.min(4, Math.floor(v + 0.001) + 1);
      else if (e.key === "ArrowLeft" || e.key === "ArrowDown" || e.key === "PageDown") n = Math.max(0, Math.ceil(v - 0.001) - 1);
      else if (e.key === "Home") n = 0; else if (e.key === "End") n = 4;
      if (n == null) return;
      e.preventDefault(); range.value = String(n); onInput();
    }
    if (range) { range.addEventListener("keydown", onKey); offs.push(function () { range.removeEventListener("keydown", onKey); }); }
    if (!webgl()) { still("no-webgl"); return { destroy: function () { offs.forEach(function (f) { f(); }); } }; }
    Promise.all([loadThree(data.three), loadMeshes(data.src)]).then(function (res) {
      if (dead) return;
      var THREE = res[0];
      try { renderer = makeRenderer(THREE, stage, "x3-canvas"); } catch (e) { still("no-webgl"); return; }
      S = makeScene(THREE, res[1]);
      var cam = new THREE.PerspectiveCamera(26, 1, 1, 4000), center = new THREE.Vector3(0, 2, -9);
      var V = data.view || { az: -40, el: 22 };
      var cur = { v: range ? Number(range.value) : 0, az: V.az, el: V.el - 4 }, tgt = { v: cur.v, az: V.az, el: V.el - 4 };
      var running = false, visible = true, K = reduce ? 1 : 0.12;
      function size() { var w = stage.clientWidth, h = stage.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); draw(); }
      function draw() {
        var open = 0;
        S.parts.forEach(function (o) {
          var m = ease(cur.v - (o.stage - 1)); open = Math.max(open, m);
          o.grp.position.set(o.ex[0] * m, o.ex[1] * m, o.ex[2] * m);
          if (o.key === "pinring") { o.grp.visible = m > 0.02; o.mats[0].opacity = o.base[0] * m; o.mats[1].opacity = o.base[1] * m; }
        });
        var c = center.clone(); c.y += 14 * open; c.z += -46 * open;
        aim(cam, c, cur.az, cur.el, (66 + 40 * open) * (cam.aspect < 1 ? 1.18 : 1));
        renderer.render(S.scene, cam);
      }
      function frame() {
        raf = 0; if (dead || !visible) { running = false; return; }
        cur.v += (tgt.v - cur.v) * K; cur.az += (tgt.az - cur.az) * K; cur.el += (tgt.el - cur.el) * K;
        draw();
        if (Math.abs(tgt.v - cur.v) > 0.001 || Math.abs(tgt.az - cur.az) > 0.02 || Math.abs(tgt.el - cur.el) > 0.02) raf = requestAnimationFrame(frame); else running = false;
      }
      function kick() { if (!running && visible && !dead) { running = true; raf = requestAnimationFrame(frame); } }
      api.set = function (v) { tgt.v = clamp(v, 0, 4); kick(); };
      // drag to turn (pointer events; touch-action keeps vertical page scrolling)
      var drag = null;
      function down(e) { drag = { x: e.clientX, y: e.clientY, az: tgt.az, el: tgt.el }; stage.classList.add("x3-grab"); if (stage.setPointerCapture) try { stage.setPointerCapture(e.pointerId); } catch (_) {} }
      function move(e) {
        if (!drag) return;
        tgt.az = drag.az - (e.clientX - drag.x) * 0.35; tgt.el = clamp(drag.el + (e.clientY - drag.y) * 0.2, -10, 50); kick();
      }
      function up() { drag = null; stage.classList.remove("x3-grab"); }
      stage.addEventListener("pointerdown", down); stage.addEventListener("pointermove", move); stage.addEventListener("pointerup", up); stage.addEventListener("pointercancel", up);
      offs.push(function () { stage.removeEventListener("pointerdown", down); stage.removeEventListener("pointermove", move); stage.removeEventListener("pointerup", up); stage.removeEventListener("pointercancel", up); });
      // keys on the turn buttons
      Array.prototype.slice.call(sec.querySelectorAll("[data-turn]")).forEach(function (b) {
        function t() { tgt.az += Number(b.dataset.turn); kick(); }
        b.addEventListener("click", t); offs.push(function () { b.removeEventListener("click", t); });
      });
      var ro = window.ResizeObserver ? new ResizeObserver(size) : null; if (ro) { ro.observe(stage); offs.push(function () { ro.disconnect(); }); }
      offs.push(visibility(sec, function (v) { visible = v; if (v) kick(); }));
      size();
      sec.classList.add("x3-ready"); sec.setAttribute("data-why", "live");
    }).catch(function (e) { if (!dead) { still("load-failed"); if (window.console) console.warn("CURVE 35: 3D viewer off (" + e.message + ")"); } });
    return { destroy: function () { dead = true; if (raf) cancelAnimationFrame(raf); offs.forEach(function (f) { f(); }); disposeAll(renderer, S); } };
  }

  // ------------------------------------------------------------------ the build guide: the camera as it stands after one step
  // Camera3D.stepper(box, data) -> { set(model), destroy() }.  model (site/build.py, from canon/steps.yaml): in (parts in by then), new (the parts this
  // step moves), pose (part -> [x, y, z] mm where it sits at this step, if not in its place), az, el (the eye).  Parts not in yet are faint ghosts in
  // their places; the new parts glow and fly in from their exploded direction.  Reduced motion: they are simply there.  No WebGL: the box keeps its picture.
  function stepper(box, data) {
    var dead = false, renderer = null, S = null, raf = 0, offs = [], want = null, api = { set: function (m) { want = m; } };
    var reduce = reducedMotion();
    function still(why) { box.setAttribute("data-why", why); }
    if (!webgl()) { still("no-webgl"); return { set: function () {}, destroy: function () {} }; }
    Promise.all([loadThree(data.three), loadMeshes(data.src)]).then(function (res) {
      if (dead) return;
      var THREE = res[0];
      try { renderer = makeRenderer(THREE, box, "st3-canvas"); } catch (e) { still("no-webgl"); return; }
      S = makeScene(THREE, res[1]);
      var GLOW = new THREE.Color(0xff8a3d);
      S.parts.forEach(function (o) { o.cur = { x: 0, y: 0, z: 0, a: 1, g: 0 }; o.tgt = { x: 0, y: 0, z: 0, a: 1, g: 0 }; o.mats[0].emissive = GLOW.clone(); o.mats[0].emissiveIntensity = 0; });
      var cam = new THREE.PerspectiveCamera(26, 1, 1, 4000), center = new THREE.Vector3(0, 2, -9);
      var view = { az: -35, el: 22 }, cv = { az: -35, el: 22 }, drag = null, running = false, visible = true, t0 = 0, flying = [];
      function size() { var w = box.clientWidth, h = box.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); kick(); }
      function apply(m) {
        var inn = {}, nw = {}; (m.in || []).forEach(function (k) { inn[k] = 1; }); (m.new || []).forEach(function (k) { nw[k] = 1; });
        flying = [];
        S.parts.forEach(function (o) {
          var p = toThree((m.pose && m.pose[o.key]) || [0, 0, 0]), was = o.tgt.a > 0.5;
          o.tgt.x = p[0]; o.tgt.y = p[1]; o.tgt.z = p[2]; o.tgt.a = inn[o.key] ? 1 : (o.key === "pinring" ? 0 : 0.1); o.tgt.g = nw[o.key] ? 1 : 0;
          if (nw[o.key] && !reduce) {          // fly in from its exploded direction
            var e = o.ex, l = Math.sqrt(e[0] * e[0] + e[1] * e[1] + e[2] * e[2]) || 1, d = was ? 0 : 46;
            if (d) { o.cur.x = p[0] + e[0] / l * d; o.cur.y = p[1] + e[1] / l * d; o.cur.z = p[2] + e[2] / l * d; o.cur.a = 0.15; }
            flying.push(o);
          }
          if (reduce) { o.cur.x = o.tgt.x; o.cur.y = o.tgt.y; o.cur.z = o.tgt.z; o.cur.a = o.tgt.a; o.cur.g = o.tgt.g; }
        });
        view.az = m.az == null ? -35 : m.az; view.el = m.el == null ? 22 : m.el; if (reduce) { cv.az = view.az; cv.el = view.el; }
        t0 = performance.now(); kick();
      }
      function draw(now) {
        var pulse = reduce ? 0.55 : 0.4 + 0.25 * Math.sin((now - t0) / 260);
        S.parts.forEach(function (o) {
          o.grp.position.set(o.cur.x, o.cur.y, o.cur.z);
          var a = o.cur.a, base = o.base;
          o.grp.visible = a > 0.02;
          o.mats[0].opacity = base[0] * a; o.mats[0].depthWrite = a > 0.5;
          o.mats[1].opacity = a < 0.5 ? 0.12 : base[1];
          o.mats[0].emissiveIntensity = o.cur.g * pulse * 0.45;
        });
        aim(cam, center, cv.az, cv.el, 70 * (cam.aspect < 1 ? 1.2 : 1));
        renderer.render(S.scene, cam);
      }
      function frame(now) {
        raf = 0; if (dead || !visible) { running = false; return; }
        var K = reduce ? 1 : 0.1, moving = false;
        S.parts.forEach(function (o) {
          ["x", "y", "z", "a", "g"].forEach(function (k) { var d = o.tgt[k] - o.cur[k]; if (Math.abs(d) > 0.003) { o.cur[k] += d * K; moving = true; } else o.cur[k] = o.tgt[k]; });
        });
        cv.az += (view.az - cv.az) * (reduce ? 1 : 0.08); cv.el += (view.el - cv.el) * (reduce ? 1 : 0.08);
        if (Math.abs(view.az - cv.az) > 0.02 || Math.abs(view.el - cv.el) > 0.02) moving = true;
        var glowing = !reduce && S.parts.some(function (o) { return o.tgt.g > 0; }) && now - t0 < 4000;     // the new part glows a while, then rests
        draw(now);
        if (moving || glowing) raf = requestAnimationFrame(frame); else { running = false; draw(t0 + 1e9); }
      }
      function kick() { if (!running && visible && !dead) { running = true; raf = requestAnimationFrame(frame); } }
      function down(e) { drag = { x: e.clientX, y: e.clientY, az: view.az, el: view.el }; box.classList.add("x3-grab"); if (box.setPointerCapture) try { box.setPointerCapture(e.pointerId); } catch (_) {} }
      function move(e) { if (!drag) return; view.az = drag.az - (e.clientX - drag.x) * 0.35; view.el = clamp(drag.el + (e.clientY - drag.y) * 0.2, -10, 60); kick(); }
      function up() { drag = null; box.classList.remove("x3-grab"); }
      box.addEventListener("pointerdown", down); box.addEventListener("pointermove", move); box.addEventListener("pointerup", up); box.addEventListener("pointercancel", up);
      offs.push(function () { box.removeEventListener("pointerdown", down); box.removeEventListener("pointermove", move); box.removeEventListener("pointerup", up); box.removeEventListener("pointercancel", up); });
      var ro = window.ResizeObserver ? new ResizeObserver(size) : null; if (ro) { ro.observe(box); offs.push(function () { ro.disconnect(); }); }
      offs.push(visibility(box, function (v) { visible = v; if (v) kick(); }));
      api.set = apply; api.turn = function (d) { view.az += d; kick(); };
      if (want) apply(want);
      size();
      box.classList.add("st3-ready"); still("live");
    }).catch(function (e) { if (!dead) { still("load-failed"); if (window.console) console.warn("CURVE 35: 3D step view off (" + e.message + ")"); } });
    return { set: function (m) { api.set(m); }, turn: function (d) { if (api.turn) api.turn(d); }, destroy: function () { dead = true; if (raf) cancelAnimationFrame(raf); offs.forEach(function (f) { f(); }); disposeAll(renderer, S); } };
  }

  window.Camera3D = { hero: hero, viewer: viewer, stepper: stepper };
})();
