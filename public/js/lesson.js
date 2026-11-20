/* CURVE 35: the lesson page renderer.   CURVE.renderLesson(n, el, ctx) -> Promise of {destroy()}
   Reads data/lessons/lNN.json (main shelf, lessons 1 to 9) or ctx.data (e.g. data/lessons/m01.json for the maker shelf) and builds one page:
   a coloured hero band (big number, the question, the hook, up to 3 chips, the film or a still in an ink-outlined card, "In this lesson" tiles),
   then the lesson's sections in order, a teacher view ("Teaching this?") and a slide mode (full screen, arrow keys, Esc).
   The section kinds and the JSON shape are listed in site/COURSE_V2.md, "Renderer".
   ctx (all optional): {media: {film, vtt, poster}, lessons: [...], section: "id to open at" ("teach" opens the teacher view, "slides" the slides),
                        base: "path prefix", data: "path of the json", go(hash): the shell's own navigation, makers: "#makers",
                        bar: true (always draw our strip 1-9 + Makers) | false (never) | unset (draw it unless the shell has a .chapbar next to el)}
   Needs js/sims/common.js (CURVE.U and the sim and figure registry). */
(function () {
  "use strict";
  var C = window.CURVE = window.CURVE || {};
  var REG = window.CURVE_REG = window.CURVE_REG || { sims: {}, figs: {} };
  var PENDING = "curve-lesson-goto", TEACH_KEY = "curve-lesson-teach";

  // The main shelf: nine lessons, one colour each.  A lesson's own "colour" wins on its page.
  var COLOURS = ["#1F8A70", "#2B6CD8", "#D23F31", "#E8641B", "#0E9AA7", "#1E5AA8", "#4B5563", "#B7791F", "#C2306B"];
  var TITLES = ["The pinhole", "The lens", "Film", "Aperture", "The shutter", "Winding on", "Light traps", "Aiming and framing", "Your phone's camera"];
  var QUESTIONS = ["How can a hole make a picture?", "If a hole already makes a picture, why does anyone need a lens?", "How does a strip of plastic remember a picture?",
    "Why do camera numbers go 8, 11, 16?", "How do you make a piece of plastic move that fast, the same way every time?", "How does the camera know it has moved the film exactly one picture?",
    "How can a box full of gaps be dark inside?", "Same camera, same film. Why are some pictures better than others?", "Your phone has no film, no dots and no blade. So how does it take a picture?"];
  // kind -> [the tag above the title, its style].  Old names (why, text, play, camera) are aliases.
  var ALIAS = { why: "story", text: "story", play: "sim", camera: "kit", timeline: "story" };
  var TAG = { story: ["The story", "ink"], why: ["Why this piece exists", "ink"], predict: ["Your guess first", "yel"], sim: ["Play with it", "col"], film: ["Watch", "ink"],
    kit: ["In your camera", "col"], phone: ["Your phone does this too", "ink"], maths: ["The maths", "ink"], "try": ["Try it", "col"], quiz: ["Check yourself", "yel"], next: ["Next", "ink"],
    roll: ["Photo challenge", "yel"] };

  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function list(v) { return Array.isArray(v) ? v : (v == null || v === "" ? [] : [v]); }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function reduced() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
  function hex(c) { c = c.replace("#", ""); return [parseInt(c.substr(0, 2), 16), parseInt(c.substr(2, 2), 16), parseInt(c.substr(4, 2), 16)]; }
  function mix(a, b, t) { var x = hex(a), y = hex(b); return "#" + [0, 1, 2].map(function (i) { var v = Math.round(x[i] * (1 - t) + y[i] * t); return (v < 16 ? "0" : "") + v.toString(16); }).join(""); }
  function lumin(c) { var x = hex(c).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2]; }
  function inkOf(c) { var t = 0; while (t < 0.9 && (1.05 / (lumin(mix(c, "#000000", t)) + 0.05)) < 5.2) t += 0.05; return mix(c, "#000000", t); }
  function textOn(c) { return lumin(c) > 0.35 ? "#1b1a18" : "#ffffff"; }
  function lid(L, sec) { return (L.maker ? "maker-" + L.n : "lesson-" + L.n) + (sec ? "-" + sec : ""); }
  function img(base, name) { if (!name) return ""; return /[\/.]/.test(name) ? base + name : base + "media/img/" + name + ".webp"; }
  function stepName(code) { var m = String(code).match(/^([a-z])(\d+)$/i); if (!m) return String(code).toUpperCase(); return ({ b: "BUILD", f: "FILM IN", p: "PHOTOS", o: "FILM OUT", h: "THE HOLE" }[m[1].toLowerCase()] || m[1].toUpperCase()) + " " + m[2]; }
  function kindOf(s) { return ALIAS[s.kind] || s.kind; }
  function tagOf(s) { var t = TAG[s.kind] || TAG[kindOf(s)] || ["", "ink"]; return [s.label != null ? s.label : t[0], t[1]]; }
  function firstPara(h) { var m = String(h || "").match(/<p[^>]*>[\s\S]*?<\/p>/i); return m ? m[0] : (h ? "<p>" + h + "</p>" : ""); }
  function letter(i) { return "ABCDEFG".charAt(i); }

  // ------------------------------------------------------------------ pieces
  function figure(f, base) {
    if (!f) return "";
    var inner = "";
    if (f.svg) { var fn = REG.figs[f.svg]; try { inner = fn ? fn() : ""; } catch (e) { inner = ""; } if (!inner) return ""; }
    else if (f.img) inner = '<img src="' + esc(img(base, f.img)) + '" alt="' + esc(f.alt || f.caption || "") + '" loading="lazy" onerror="this.closest(\'figure\').hidden=true">';
    else return "";
    return '<figure class="lp-fig' + (f.img ? " lp-fig-img" : "") + '">' + inner + (f.caption ? "<figcaption>" + esc(f.caption) + "</figcaption>" : "") + "</figure>";
  }
  function strip(items) {
    items = list(items); if (!items.length) return "";
    return '<ol class="lp-tl" aria-label="Timeline">' + items.map(function (it) { return '<li><span class="lp-tl-y">' + esc(it.year) + '</span><span class="lp-tl-w">' + (it.what || "") + "</span></li>"; }).join("") + "</ol>";
  }
  function prose(h) { return h ? '<div class="lp-prose">' + h + "</div>" : ""; }
  function filmHTML(L, o) {
    var m = o.media || {};
    if (!m.film) return "";
    return '<div class="lp-film"><video controls preload="none" playsinline' + (m.poster ? ' poster="' + esc(o.base + m.poster) + '"' : "") + ' src="' + esc(o.base + m.film) + '" aria-label="Film: ' + esc(L.title) + '"></video></div>';
  }
  // a multiple-choice block: predict (no marks) or one quiz item.  Wired by a delegated click (choose()).
  function choicesHTML(q, choices, answer, mode, extra) {
    return '<div class="lp-mc" data-mode="' + mode + '" data-answer="' + (+answer || 0) + '">' + (q ? '<p class="lp-q">' + esc(q) + "</p>" : "") +
      '<ul class="lp-ch">' + list(choices).map(function (c, i) {
        return '<li><button type="button" class="lp-c" data-i="' + i + '" aria-pressed="false"><span class="lp-c-l" aria-hidden="true">' + letter(i) + '</span><span class="lp-c-t">' + esc(c) + "</span></button></li>";
      }).join("") + "</ul>" + (extra || "") + "</div>";
  }

  var R = {};
  R.story = function (s, L, o) {
    var fig = figure(s.figure, o.base);
    return (s.lead ? '<p class="lp-lead">' + s.lead + "</p>" : "") + '<div class="lp-cols' + (fig ? "" : " lp-one") + '">' + prose(s.body) + (fig ? '<div class="lp-side">' + fig + "</div>" : "") + "</div>" +
      strip(s.timeline || s.items) + prose(s.after);
  };
  R.phone = R.story;
  R.predict = function (s) {
    return prose(s.body) + choicesHTML(s.q, s.choices, s.answer, "predict",
      '<p class="lp-mc-note">Pick one before you read on. No marks: being wrong first is how this works.</p>' +
      '<div class="lp-reveal" hidden><p class="lp-verdict"></p>' + (s.reveal || "") + "</div>");
  };
  R.sim = function (s) {
    var sims = list(s.sims).length ? list(s.sims) : (s.sim ? [{ sim: s.sim, intro: s.intro, after: s.after }] : []);
    return (s.intro && list(s.sims).length ? '<p class="lp-lead">' + s.intro + "</p>" : "") + sims.map(function (x) {
      return '<div class="lp-play">' + (x.title ? '<h3 class="lp-h3">' + esc(x.title) + "</h3>" : "") + (x.intro ? '<p class="lp-intro">' + x.intro + "</p>" : "") +
        '<div class="lp-sim" data-sim="' + esc(x.sim) + '"><div class="lp-sim-wait">Loading…</div></div>' +
        (x.after ? '<p class="lp-after"><strong>What you just saw.</strong> ' + x.after + "</p>" : "") + "</div>";
    }).join("");
  };
  R.film = function (s, L, o) { return prose(s.body) + (filmHTML(L, o) || figure(L.still, o.base)); };
  R.kit = function (s, L, o) {
    var pic = s.render ? '<figure class="lp-fig lp-fig-img lp-render"><img src="' + esc(img(o.base, s.render)) + '" alt="' + esc(s.alt || s.caption || "") + '" loading="lazy" onerror="this.closest(\'figure\').hidden=true">' +
      '<figcaption>' + esc(s.caption || "") + "</figcaption></figure>" : "";
    var steps = list(s.step).map(function (code) { return '<a class="lp-go" href="#build-' + esc(code) + '">Build step ' + esc(stepName(code)) + ' <span aria-hidden="true">→</span></a>'; }).join(" ");
    return '<div class="lp-cols lp-cam">' + '<div class="lp-side">' + pic + "</div>" + '<div class="lp-prose">' + (s.body || "") + (steps ? '<p class="lp-steps-go">' + steps + "</p>" : "") + "</div></div>";
  };
  R.maths = function (s) {
    return '<details class="lp-maths"><summary><span class="lp-sum-k">Open the sum</span> <span>' + esc(s.summary || "") + '</span></summary><div class="lp-maths-in">' +
      '<ol class="lp-lines">' + list(s.lines).map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("") + "</ol>" + prose(s.body) + "</div></details>";
  };
  R["try"] = function (s) {
    return (s.lead ? '<p class="lp-lead">' + s.lead + "</p>" : "") + '<div class="lp-try">' +
      '<div class="lp-need"><p class="lp-mini">' + esc(s.minutes || 15) + " minutes · you need</p><ul>" + list(s.needs).map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>" +
      '<div class="lp-do"><ol>' + list(s.steps).map(function (x) { return "<li><span>" + x + "</span></li>"; }).join("") + "</ol>" +
      (s.notice ? '<p class="lp-notice"><strong>What you will see.</strong> ' + s.notice + "</p>" : "") + (s.safety ? '<p class="lp-safety"><strong>Safety.</strong> ' + esc(s.safety) + "</p>" : "") + "</div></div>";
  };
  function quizItem(it, i, total) {
    return '<li class="lp-qi"><p class="lp-mini">Question ' + (i + 1) + " of " + total + "</p>" + choicesHTML(it.q, it.choices, it.answer, "quiz",
      '<div class="lp-reveal" hidden><p class="lp-verdict"></p><p>' + (it.why || "") + "</p></div>") + "</li>";
  }
  R.quiz = function (s) {
    var items = list(s.items);
    return prose(s.body) + '<div class="lp-quiz" data-n="' + items.length + '"><ol class="lp-qs">' + items.map(function (it, i) { return quizItem(it, i, items.length); }).join("") + "</ol>" +
      '<p class="lp-score" aria-live="polite"><span class="lp-score-t">' + items.length + ' questions. Tap an answer to see if you are right.</span> <button type="button" class="lp-btn lp-again" hidden>Try again</button></p></div>';
  };
  // the photo challenge at the end of a main lesson: a strip of numbered frames, then what to look for when the scans come back
  R.roll = function (s) {
    var shots = list(s.shots), n = +s.frames || shots.length;
    return (s.lead ? '<p class="lp-lead">' + esc(s.lead) + "</p>" : "") + '<div class="lp-roll"><p class="lp-roll-n"><span class="lp-roll-c">' + n + "</span> " + (n === 1 ? "frame" : "frames") + ' of your roll</p><ol class="lp-roll-shots">' +
      shots.map(function (x, i) { return '<li><span class="lp-roll-f" aria-hidden="true">' + (i + 1) + "</span><span>" + esc(x) + "</span></li>"; }).join("") + "</ol>" +
      (s.look ? '<p class="lp-roll-look"><strong>When the scans come back.</strong> ' + esc(s.look) + "</p>" : "") +
      (s.link && s.link.href ? '<p><a class="lp-go" href="' + esc(s.link.href) + '">' + esc(s.link.text || "Next") + ' <span aria-hidden="true">→</span></a></p>' : "") + "</div>";
  };
  R.next = function (s, L) {
    var nx = s.lesson != null ? s.lesson : (L.maker ? null : (L.n < 9 ? L.n + 1 : null));
    var big = "";
    if (s.href) big = '<a class="lp-nextq" href="' + esc(s.href) + '"><span class="lp-mini">' + esc(s.kicker || "Next") + "</span><strong>" + esc(s.question || "") + '</strong><span class="lp-arrow" aria-hidden="true">→</span></a>';
    else if (nx) big = '<a class="lp-nextq" href="#lesson-' + nx + '" style="--c:' + (COLOURS[nx - 1] || "#888") + ";--c-on:" + textOn(COLOURS[nx - 1] || "#888") + '"><span class="lp-nextn" aria-hidden="true">' + nx + '</span><span class="lp-mini">Lesson ' + nx + " · " + esc(TITLES[nx - 1] || "") + "</span><strong>" + esc(s.question || QUESTIONS[nx - 1] || "") + '</strong><span class="lp-arrow" aria-hidden="true">→</span></a>';
    var links = list(s.links).slice(0, 3);
    return (s.body ? prose(s.body) : "") + big + (links.length ? '<p class="lp-mini lp-out-h">Good things elsewhere</p><ul class="lp-out">' + links.map(function (f) {
      var host = ""; try { host = new URL(f.url).hostname.replace(/^www\./, ""); } catch (e) { }
      return '<li><a href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.title) + '</a> <span class="lp-host">' + esc(host) + "</span>" + (f.why ? "<br><span>" + esc(f.why) + "</span>" : "") + "</li>";
    }).join("") + "</ul>" : "");
  };

  function headOf(s, L, i, big) {
    var t = tagOf(s);
    return '<p class="lp-tagline"><span class="lp-num" aria-hidden="true">' + pad(i + 1) + "</span>" + (t[0] ? '<span class="lp-tag lp-tag-' + t[1] + '">' + esc(t[0]) + "</span>" : "") + "</p>" +
      (s.title ? "<h" + big + ' id="' + lid(L, s.id) + '-h">' + esc(s.title) + "</h" + big + ">" : "<h" + big + ' id="' + lid(L, s.id) + '-h" class="sr-only">' + esc(t[0]) + "</h" + big + ">");
  }
  function sectionHTML(s, L, o, i, unit) {
    var r = R[kindOf(s)] || R.story, body;
    try { body = r(s, L, o); } catch (e) { body = ""; if (window.console) console.error(e); }
    return '<section class="lp-s lp-k-' + esc(kindOf(s)) + '" id="' + lid(L, s.id) + '" data-sec="' + esc(s.id) + '" aria-labelledby="' + lid(L, s.id) + '-h"><div class="lp-in">' +
      (unit || "") + headOf(s, L, i, 2) + body + "</div></section>";
  }

  // ------------------------------------------------------------------ units: a lesson is a few short units, each whole on its own, with its own minutes.
  // The film is one unit's worth and never the whole lesson; nothing is padded out to a period (19 November 2026).
  function unitsOf(L) { return list(L.units).filter(function (u) { return u && list(u.sections).length; }); }
  function unitMins(us) { return us.reduce(function (a, u) { return a + (+u.minutes || 0); }, 0); }
  function unitHTML(u, k, n, L) {
    return '<p class="lp-unit" id="' + lid(L, "unit-" + (k + 1)) + '"><span class="lp-unit-n" aria-hidden="true">' + (k + 1) + '</span><span class="sr-only">Unit ' + (k + 1) + " of " + n + ": </span>" +
      '<span class="lp-unit-t">' + esc(u.title) + '</span><span class="lp-unit-m">' + esc(u.minutes) + " min</span></p>";
  }
  function bodyHTML(L, o) {
    var us = unitsOf(L), first = {};
    us.forEach(function (u, k) { first[list(u.sections)[0]] = k; });
    return L.sections.map(function (s, i) { return sectionHTML(s, L, o, i, first[s.id] != null ? unitHTML(us[first[s.id]], first[s.id], us.length, L) : ""); }).join("");
  }

  // ------------------------------------------------------------------ the teacher view
  function teachHTML(L) {
    var T = L.teach; if (!T) return "";
    var per = list(T.period), total = per.reduce(function (a, p) { return a + (+p.minutes || 0); }, 0) || 1;
    var bar = per.length ? '<div class="lp-tp-bar" aria-hidden="true">' + per.map(function (p, i) {
      return '<span style="flex:' + (+p.minutes || 1) + '" class="lp-tp-seg lp-tp-' + (i % 3) + '"><b>' + esc(p.minutes) + "</b> " + esc(p.phase || "") + "</span>";
    }).join("") + "</div>" : "";
    var D = T.differentiation || {};
    function blk(h, inner) { return inner ? '<div class="lp-tb"><h3>' + h + "</h3>" + inner + "</div>" : ""; }
    function ul(a, tag) { a = list(a); return a.length ? "<" + (tag || "ul") + ">" + a.map(function (x) { return "<li>" + x + "</li>"; }).join("") + "</" + (tag || "ul") + ">" : ""; }
    var us = unitsOf(L), all = unitMins(us), short3 = us.length > 2 ? [us[0], us[1], us[us.length - 1]] : us;
    var ubar = us.length ? '<div class="lp-tp-bar" aria-hidden="true">' + us.map(function (u, i) { return '<span style="flex:' + (+u.minutes || 1) + '" class="lp-tp-seg lp-tp-' + (i % 3) + '"><b>' + esc(u.minutes) + "</b></span>"; }).join("") + "</div>" : "";
    var ulist = us.length ? ubar + '<ol class="lp-tp">' + us.map(function (u, i) { return '<li><span class="lp-tp-m">' + esc(u.minutes) + ' min</span><span class="lp-tp-ph">Unit ' + (i + 1) + "</span><span><b>" + esc(u.title) + ".</b> " + esc(u.what || "") + "</span></li>"; }).join("") + "</ol>" : "";
    var ways = us.length ? "<ul><li><b>" + esc(us[0].minutes) + " minutes:</b> unit 1 on its own, as a starter.</li>" +
      (us.length > 2 ? "<li><b>" + unitMins(short3) + " minutes:</b> units 1, 2 and " + us.length + ": the idea, seen and checked.</li>" : "") +
      "<li><b>" + all + " minutes:</b> all " + us.length + ", in one sitting or over two.</li></ul><p>Each unit stands on its own. Stop after any of them and nothing is left half done.</p>" : "";
    return '<section class="lp-teach" id="' + lid(L, "teach") + '" aria-labelledby="' + lid(L, "teach") + '-h" hidden><div class="lp-in"><div class="lp-teach-card">' +
      '<div class="lp-teach-top"><div><p class="lp-mini">For the teacher · lesson ' + esc(L.code || L.n) + '</p><h2 id="' + lid(L, "teach") + '-h">' + (us.length ? "The lesson plan: " + us.length + " units, " + all + " minutes if you teach them all" : "The lesson plan: one " + total + "-minute period") + "</h2></div>" +
      '<div class="lp-teach-act"><button type="button" class="lp-btn lp-btn-main" data-act="slides">Show the slides <span aria-hidden="true">▶</span></button><button type="button" class="lp-btn lp-btn-quiet" data-act="teach">Leave teacher mode</button></div></div>' +
      '<div class="lp-teach-grid"><div>' +
      blk("By the end, students can", ul(T.objectives, "ol")) + blk("You need", ul(T.materials)) +
      blk("The misconception to listen for", T.misconception ? "<p>" + T.misconception + "</p>" : "") +
      blk("Safety", T.safety ? "<p>" + esc(T.safety) + "</p>" : "") +
      "</div><div>" +
      blk("The units", ulist) + blk("Short on time?", ways) +
      blk(us.length ? "One way to run it as a " + total + "-minute class" : "The period, minute by minute", bar + '<ol class="lp-tp">' + per.map(function (p) { return '<li><span class="lp-tp-m">' + esc(p.minutes) + ' min</span><span class="lp-tp-ph">' + esc(p.phase || "") + "</span><span>" + (p.what || "") + "</span></li>"; }).join("") + "</ol>") +
      blk("Questions to ask", list(T.questions).length ? '<ol class="lp-tq">' + list(T.questions).map(function (q) { return "<li><p>" + esc(q.q) + '</p><details><summary>Show the answer</summary><p>' + esc(q.a) + "</p></details></li>"; }).join("") + "</ol>" : "") +
      blk("Exit ticket", T.exit_ticket ? '<p class="lp-exit">' + esc(T.exit_ticket) + "</p>" : "") +
      blk("Every student in", (D.support || D.stretch || D.access) ? "<dl class=\"lp-dif\">" + (D.support ? "<dt>Support</dt><dd>" + esc(D.support) + "</dd>" : "") + (D.stretch ? "<dt>Stretch</dt><dd>" + esc(D.stretch) + "</dd>" : "") + (D.access ? "<dt>Access</dt><dd>" + esc(D.access) + "</dd>" : "") + "</dl>" : "") +
      "</div></div></div></div></section>";
  }

  // ------------------------------------------------------------------ slides
  function slideList(L) {
    var want = list(L.slides).length ? list(L.slides) : list(L.teach && (L.teach.slides || L.teach.slides_from_sections));
    var secs = want.length ? want.map(function (id) { return L.sections.filter(function (s) { return s.id === id; })[0]; }).filter(Boolean) : L.sections.filter(function (s) { return kindOf(s) !== "next"; });
    var out = [{ kind: "title" }];
    secs.forEach(function (s) {
      var k = kindOf(s);
      if (k === "sim") { var sims = list(s.sims).length ? list(s.sims) : (s.sim ? [{ sim: s.sim, intro: s.intro }] : []); sims.forEach(function (x) { out.push({ s: s, sim: x }); }); }
      else if (k === "quiz") list(s.items).forEach(function (it, i) { out.push({ s: s, item: it, i: i, n: list(s.items).length }); });
      else out.push({ s: s });
    });
    return out;
  }
  function slideHTML(sl, L, o) {
    if (sl.kind === "title") return '<div class="lp-sl-title"><span class="lp-bignum" aria-hidden="true">' + esc(L.code || L.n) + '</span><p class="lp-mini">' + (L.maker ? "For makers" : "Lesson " + L.n + " of 9") + "</p><h2>" + esc(L.title) + '</h2><p class="lp-sl-hook"><strong>' + esc(L.question) + "</strong></p>" + (L.hook ? '<p class="lp-sl-hook">' + L.hook + "</p>" : "") + "</div>";
    var s = sl.s, k = kindOf(s), t = tagOf(s), head = '<p class="lp-tagline">' + (t[0] ? '<span class="lp-tag lp-tag-' + t[1] + '">' + esc(t[0]) + "</span>" : "") + "</p>";
    var title = sl.sim ? (sl.sim.title || s.title) : sl.item ? "Question " + (sl.i + 1) + " of " + sl.n : s.title;
    head += title ? "<h2>" + esc(title) + "</h2>" : "";
    var body = "";
    if (sl.sim) body = (sl.sim.intro ? '<p class="lp-sl-lead">' + sl.sim.intro + "</p>" : "") + '<div class="lp-sim" data-sim="' + esc(sl.sim.sim) + '"><div class="lp-sim-wait">Loading…</div></div>';
    else if (sl.item) body = choicesHTML(sl.item.q, sl.item.choices, sl.item.answer, "quiz", '<div class="lp-reveal" hidden><p class="lp-verdict"></p><p>' + (sl.item.why || "") + "</p></div>");
    else if (k === "predict") body = choicesHTML(s.q, s.choices, s.answer, "predict", '<div class="lp-reveal" hidden><p class="lp-verdict"></p>' + (s.reveal || "") + "</div>");
    else if (k === "maths") body = '<ol class="lp-lines">' + list(s.lines).map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("") + "</ol>";
    else if (k === "roll") body = '<div class="lp-do"><ol>' + list(s.shots).map(function (x) { return "<li><span>" + esc(x) + "</span></li>"; }).join("") + "</ol></div>";
    else if (k === "try") body = '<div class="lp-do"><ol>' + list(s.steps).map(function (x) { return "<li><span>" + x + "</span></li>"; }).join("") + "</ol></div>";
    else if (k === "kit") body = '<div class="lp-sl-two">' + (s.render ? '<figure class="lp-fig lp-fig-img"><img src="' + esc(img(o.base, s.render)) + '" alt="' + esc(s.alt || "") + '"></figure>' : "") + '<div class="lp-sl-text">' + firstPara(s.body) + "</div></div>";
    else if (k === "film") body = filmHTML(L, o);
    else if (k === "next") body = '<p class="lp-sl-lead">' + esc(s.question || QUESTIONS[L.n] || "") + "</p>";
    else {
      var fig = figure(s.figure, o.base), tl = list(s.timeline || s.items);
      if (fig) body = '<div class="lp-sl-two"><div class="lp-sl-text">' + (s.lead ? "<p>" + s.lead + "</p>" : firstPara(s.body)) + "</div>" + fig + "</div>";
      else body = '<div class="lp-sl-text">' + (s.lead ? "<p>" + s.lead + "</p>" : firstPara(s.body)) + "</div>" + strip(tl);
    }
    return '<div class="lp-sl-in">' + head + body + "</div>";
  }

  // ------------------------------------------------------------------ the page
  // the lesson's diagram (hero_fig: a figure its sims file registers), large, in the hero
  function heroFig(L) {
    var fn = L.hero_fig && REG.figs[L.hero_fig], svg = "";
    if (fn) { try { svg = fn() || ""; } catch (e) { svg = ""; } }
    return svg ? '<figure class="lp-card lp-herofig">' + svg + (L.hero_fig_caption ? '<figcaption class="lp-cap">' + esc(L.hero_fig_caption) + "</figcaption>" : "") + "</figure>" : "";
  }
  function mmss(t) { t = Math.max(0, Math.round(+t || 0)); return Math.floor(t / 60) + ":" + pad(t % 60); }
  // v10: the lesson's film in a near-theatre: wide, a dark surround, one big play button, captions on.  No film: the lesson's diagram, large.
  function theatreHTML(L, o) {
    var m = o.media || {}; if (L.film === false || !m.film) return "";
    var chs = list(m.chapters).filter(function (c) { return c && c.title != null; });
    return '<section class="lp-theatre" aria-label="The film: ' + esc(L.title) + '"><div class="lp-th-in"><div class="lp-th-screen">' +
      '<video preload="none" playsinline' + (m.poster ? ' poster="' + esc(o.base + m.poster) + '"' : "") + ' src="' + esc(o.base + m.film) + '" aria-label="Film: ' + esc(L.title) + '"></video>' +
      '<button type="button" class="lp-th-play" data-act="play"><span class="lp-th-tri" aria-hidden="true"></span><span class="lp-th-lab">Play the film' + (m.duration_s ? '<small>' + mmss(m.duration_s) + (m.captions || m.vtt || m.vtt_src ? " · captions on" : "") + "</small>" : "") + "</span></button></div>" +
      (chs.length > 1 ? '<ol class="lp-th-ch" aria-label="Chapters">' + chs.map(function (c) { return '<li><button type="button" data-t="' + (+c.t || 0) + '"><span>' + mmss(c.t) + "</span>" + esc(c.title) + "</button></li>"; }).join("") + "</ol>" : "") +
      "</div></section>";
  }
  function stripHTML(L, o) {
    if (o.shellBar) return '<nav class="lp-sub" aria-label="Sections of this lesson"><div class="lp-sub-in"><p class="lp-sub-t"><span>' + (L.maker ? "Maker lesson " + esc(L.code || L.n) : "Lesson " + L.n) + "</span> &middot; " + esc(L.title) + "</p>" + dotsHTML(L) + '</div><div class="lp-progress" aria-hidden="true"><i></i></div></nav>';
    var nums = TITLES.map(function (t, i) {
      var n = i + 1, cur = !L.maker && n === L.n;
      return '<li><a href="#lesson-' + n + '"' + (cur ? ' aria-current="page"' : "") + ' style="--c:' + COLOURS[i] + '" title="' + esc(n + ". " + t) + '"><span class="sr-only">Lesson ' + n + ": " + esc(t) + "</span><span aria-hidden=\"true\">" + n + "</span></a></li>";
    }).join("");
    return '<nav class="lp-bar" aria-label="Lessons"><div class="lp-bar-in"><a class="lp-bar-home" href="#lessons">Lessons</a><ol class="lp-nums">' + nums + "</ol>" +
      '<a class="lp-bar-makers"' + (L.maker ? ' aria-current="page"' : "") + ' href="' + esc(o.makers) + '">Makers</a></div><div class="lp-progress" aria-hidden="true"><i></i></div></nav>';
  }
  // the lesson's sections as a row of dots: they fill as you scroll past each one; each one jumps to its section
  function dotsHTML(L) {
    return '<ol class="lp-dots">' + L.sections.map(function (s, i) {
      if (kindOf(s) === "next") return "";
      var t = tagOf(s);
      return '<li><a href="#' + lid(L, s.id) + '" data-sec="' + esc(s.id) + '" title="' + esc(pad(i + 1) + " " + (s.title || t[0] || "")) + '"><span class="sr-only">' + esc(pad(i + 1) + ": " + (s.title || t[0] || "")) + "</span></a></li>";
    }).join("") + "</ol>";
  }
  function tilesHTML(L) {
    var us = unitsOf(L);
    if (us.length) return '<nav class="lp-tiles lp-tiles-u" aria-label="The units of this lesson"><p class="lp-mini">' + us.length + " units · do one, or all " + us.length + '</p><ol>' + us.map(function (u, k) {
      return '<li><a href="#' + lid(L, "unit-" + (k + 1)) + '"><span class="lp-tile-n">' + (k + 1) + '</span><span class="lp-tile-k">' + esc(u.minutes) + ' min</span><span class="lp-tile-t">' + esc(u.title) + "</span></a></li>";
    }).join("") + "</ol></nav>";
    return '<nav class="lp-tiles" aria-label="In this lesson"><p class="lp-mini">In this lesson</p><ol>' + L.sections.map(function (s, i) {
      if (kindOf(s) === "next") return "";
      var t = tagOf(s); if (!s.title || s.title === t[0]) t = ["", ""];
      return '<li><a href="#' + lid(L, s.id) + '" data-sec="' + esc(s.id) + '"><span class="lp-tile-n">' + pad(i + 1) + '</span><span class="lp-tile-k">' + esc(t[0] || "") + '</span><span class="lp-tile-t">' + esc(s.title || t[0] || "") + "</span></a></li>";
    }).join("") + "</ol></nav>";
  }
  function pageHTML(L, o) {
    var kick = L.maker ? "Maker lesson " + esc(L.code || ("M" + L.n)) : "Lesson " + L.n + " of 9";
    var chips = list(L.chips).slice(0, 3).map(function (c, i) { return '<li class="lp-chip' + (i === 0 ? " lp-chip-on" : "") + '">' + esc(c) + "</li>"; }).join("");
    var acts = (L.teach ? '<button type="button" class="lp-switch" data-act="teach" role="switch" aria-checked="false"><span class="lp-sw" aria-hidden="true"><i></i></span>Teacher mode</button>' : "") +
      '<button type="button" class="lp-btn lp-btn-quiet lp-t-only" data-act="slides">Show as slides <span aria-hidden="true">▶</span></button>';
    var theatre = theatreHTML(L, o), fig = theatre ? "" : heroFig(L);
    var head = '<header class="lp-head' + (theatre ? " lp-head-film" : "") + '"><div class="lp-in"><div class="lp-hero' + (fig ? "" : " lp-hero-one") + '"><div class="lp-hero-t">' +
      '<p class="lp-kick"><span class="lp-bignum" aria-hidden="true">' + esc(L.maker ? (L.code || "M" + L.n) : L.n) + "</span>" + kick + "</p><h1>" + esc(L.title) + "</h1>" +
      '<p class="lp-qline">' + esc(L.question) + "</p>" +
      (L.hook ? '<p class="lp-hook">' + L.hook + "</p>" : "") + (chips ? '<ul class="lp-chips">' + chips + "</ul>" : "") + '<p class="lp-acts">' + acts + "</p></div>" +
      (fig ? '<div class="lp-hero-m">' + fig + "</div>" : "") + "</div></div></header>" + theatre +
      '<div class="lp-tilesband"><div class="lp-in">' + tilesHTML(L) + "</div></div>";
    return stripHTML(L, o) + head + teachHTML(L) + '<div class="lp-body">' + bodyHTML(L, o) + "</div>";
  }

  // ------------------------------------------------------------------ wiring
  function mountSim(box, L, sims, slide) {
    if (box.__on) return; box.__on = true;
    var id = box.getAttribute("data-sim"), fn = REG.sims[id]; box.innerHTML = "";
    if (!fn) { (box.closest(".lp-play") || box).hidden = true; return; }
    var visFns = [];
    var api = { colour: L.colour, ink: inkOf(L.colour), reducedMotion: reduced(), facts: C.FACTS || {}, n: L.n, slide: !!slide, U: C.U, onVisible: function (f) { visFns.push(f); } };
    try { var h = fn(box, api) || {}; sims.push(h); } catch (e) { (box.closest(".lp-play") || box).hidden = true; if (window.console) console.error(e); }
    if (visFns.length && C.U) sims.push({ destroy: C.U.onVisible(box, function (on) { visFns.forEach(function (f) { f(on); }); }, true) });
  }
  function wire(root, L, o, sims) {
    $$(".lp-film video, .lp-theatre video", root).forEach(function (v) { addTrack(v, o); });
    $$(".lp-body .lp-sim", root).forEach(function (box) {
      if (!window.IntersectionObserver) { mountSim(box, L, sims); return; }
      var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); mountSim(box, L, sims); } }, { rootMargin: "600px" });
      io.observe(box); sims.push({ destroy: function () { io.disconnect(); } });
    });
  }
  function addTrack(v, o) {
    if (!(o.media && (o.media.vtt || o.media.vtt_src))) return;
    var inClaude = !!(window.claude && typeof window.claude.use === "function");
    try { var url; if (o.media.vtt_src && (!inClaude || !o.media.vtt)) url = o.base + o.media.vtt_src; else { url = URL.createObjectURL(new Blob([o.media.vtt], { type: "text/vtt" })); o.urls.push(url); } var tr = document.createElement("track"); tr.kind = "captions"; tr.label = "English"; tr.srclang = "en"; tr.src = url; tr.default = true; v.appendChild(tr); } catch (e) { /* no captions */ }
  }
  // a click on a choice in a predict block or a quiz item
  function choose(btn) {
    var mc = btn.closest(".lp-mc"); if (!mc || mc.classList.contains("lp-done")) return;
    var i = +btn.getAttribute("data-i"), ans = +mc.getAttribute("data-answer"), mode = mc.getAttribute("data-mode"), right = i === ans;
    mc.classList.add("lp-done"); mc.setAttribute("data-right", right ? "1" : "0");
    $$(".lp-c", mc).forEach(function (b, j) {
      b.setAttribute("aria-pressed", j === i ? "true" : "false");
      if (j === ans) b.classList.add("lp-c-ans");
      if (j === i && !right) b.classList.add("lp-c-wrong");
      if (mode === "quiz") b.disabled = j !== i && j !== ans;
    });
    var rv = mc.querySelector(".lp-reveal"), vd = rv && rv.querySelector(".lp-verdict");
    if (vd) vd.textContent = mode === "predict" ? (right ? "You called it: " + letter(ans) + "." : "You picked " + letter(i) + ". The answer is " + letter(ans) + ".") :
      (right ? ["Right.", "Yes, exactly.", "Spot on.", "That's it."][i % 4] : "Not quite: it's " + letter(ans) + ".");
    if (rv) rv.hidden = false;
    var q = btn.closest(".lp-quiz"); if (q) score(q);
  }
  function score(q) {
    var n = +q.getAttribute("data-n"), done = $$(".lp-mc.lp-done", q), ok = done.filter(function (m) { return m.getAttribute("data-right") === "1"; }).length;
    var t = q.querySelector(".lp-score-t"), again = q.querySelector(".lp-again");
    if (done.length < n) t.textContent = ok + " right so far, " + (n - done.length) + " to go.";
    else { t.textContent = "You got " + ok + " of " + n + ". " + (ok === n ? "Every one. You could teach this." : ok >= n - 1 ? "Nearly all: read the one you missed again." : "Have another look at the story and the sims, then try again."); again.hidden = false; }
  }
  function resetQuiz(q) {
    $$(".lp-mc", q).forEach(function (mc) { mc.classList.remove("lp-done"); mc.removeAttribute("data-right"); $$(".lp-c", mc).forEach(function (b) { b.disabled = false; b.setAttribute("aria-pressed", "false"); b.classList.remove("lp-c-ans", "lp-c-wrong"); }); var rv = mc.querySelector(".lp-reveal"); if (rv) rv.hidden = true; });
    q.querySelector(".lp-again").hidden = true; q.querySelector(".lp-score-t").textContent = q.getAttribute("data-n") + " questions. Tap an answer to see if you are right.";
  }

  function render(L, el, ctx) {
    var shellBar = ctx.bar === false ? true : ctx.bar === true ? false : !!(el.parentNode && el.parentNode.querySelector(".chapbar"));
    var o = { base: ctx.base || "", media: L.film === false ? {} : (ctx.media || {}), urls: [], shellBar: shellBar, makers: ctx.makers || "#makers" }, sims = [], offs = [];
    L.maker = !!(L.maker || /^m/i.test(String(L.code || "")));
    L.colour = /^#[0-9a-f]{6}$/i.test(L.colour || "") ? L.colour : (COLOURS[L.n - 1] || "#4B5563");
    L.sections = list(L.sections).filter(function (x) { return x && typeof x === "object"; });
    L.sections.forEach(function (x, i) { if (!x.id) x.id = x.kind || "s" + (i + 1); if (!x.kind) x.kind = "text"; });
    var root = document.createElement("div"); root.className = "lp"; root.setAttribute("data-lesson", L.n);
    var vars = { "--lc": L.colour, "--lc-ink": inkOf(L.colour), "--lc-soft": mix(L.colour, "#FFFFFF", 0.86), "--lc-pale": mix(L.colour, "#FFFFFF", 0.94), "--lc-on": textOn(L.colour) };
    for (var k in vars) root.style.setProperty(k, vars[k]);
    root.innerHTML = pageHTML(L, o);
    el.innerHTML = ""; el.appendChild(root);
    wire(root, L, o, sims);
    function on(t, ev, fn, opt) { t.addEventListener(ev, fn, opt); offs.push(function () { t.removeEventListener(ev, fn, opt); }); }

    // ---- teacher mode (v10): off by default; on, it shows the lesson plan, the teacher notes and the slides.  Remembered in this browser.
    var tpanel = root.querySelector(".lp-teach");
    function teach(show, scroll) {
      root.classList.toggle("lp-teacher", !!show); if (tpanel) tpanel.hidden = !show;
      $$("[data-act=teach]", root).forEach(function (b) { if (b.getAttribute("role") === "switch") b.setAttribute("aria-checked", show ? "true" : "false"); });
      try { localStorage.setItem(TEACH_KEY, show ? "1" : "0"); } catch (e) { }
      if (show && scroll && tpanel) tpanel.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" });
    }
    var tOn = !!ctx.teach; try { tOn = tOn || localStorage.getItem(TEACH_KEY) === "1"; } catch (e) { }
    teach(tOn, false);
    function playFilm(t) {
      var th = root.querySelector(".lp-theatre"), v = th && th.querySelector("video"); if (!v) return;
      th.classList.add("lp-th-on"); v.controls = true; v.preload = "auto";
      if (t != null) { try { v.currentTime = t; } catch (e) { } }
      var p = v.play(); if (p && p.catch) p.catch(function () { }); v.focus({ preventScroll: true });
    }

    // ---- slide mode
    var deck = null;
    function openSlides(at, gesture) {
      if (deck) return;
      var list_ = slideList(L), cur = 0, ssims = [], prevFocus = document.activeElement;
      var ov = document.createElement("div"); ov.className = "lp lp-deck"; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", "Slides: " + L.title);
      for (var k2 in vars) ov.style.setProperty(k2, vars[k2]);
      ov.innerHTML = '<div class="lp-deck-top"><span class="lp-deck-n">' + esc(L.maker ? L.code || "M" + L.n : L.n) + '</span><span class="lp-deck-t">' + esc(L.title) + '</span><span class="lp-deck-c" aria-live="polite"></span>' +
        '<button type="button" class="lp-btn lp-btn-quiet" data-d="close" aria-label="Close the slides (Esc)">Close <span aria-hidden="true">✕</span></button></div>' +
        '<div class="lp-deck-stage" tabindex="-1"></div><div class="lp-deck-foot"><button type="button" class="lp-btn" data-d="prev" aria-label="Previous slide">← Back</button><ol class="lp-deck-dots">' +
        list_.map(function (_, i) { return '<li><button type="button" data-d="' + i + '" aria-label="Slide ' + (i + 1) + '"></button></li>'; }).join("") + '</ol><button type="button" class="lp-btn lp-btn-main" data-d="next" aria-label="Next slide">Next →</button></div>';
      document.body.appendChild(ov); document.documentElement.classList.add("lp-deck-open");
      var stage = ov.querySelector(".lp-deck-stage");
      function show(i) {
        ssims.forEach(function (h) { try { h.destroy && h.destroy(); } catch (e) { } }); ssims = [];
        cur = Math.max(0, Math.min(list_.length - 1, i));
        var sl = list_[cur];
        stage.innerHTML = '<div class="lp-slide lp-k-' + esc(sl.s ? kindOf(sl.s) : "title") + '">' + slideHTML(sl, L, o) + "</div>";
        $$(".lp-sim", stage).forEach(function (b) { mountSim(b, L, ssims, true); });
        $$("video", stage).forEach(function (v) { addTrack(v, o); });
        ov.querySelector(".lp-deck-c").textContent = (cur + 1) + " / " + list_.length;
        $$(".lp-deck-dots button", ov).forEach(function (b, j) { if (j === cur) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current"); });
        ov.querySelector("[data-d=prev]").disabled = cur === 0; ov.querySelector("[data-d=next]").disabled = cur === list_.length - 1;
        stage.scrollTop = 0;
      }
      function key(e) {
        if (e.target && /input|select|textarea/i.test(e.target.tagName) && e.key !== "Escape") return;
        if (e.key === "Escape") { e.preventDefault(); close(); }
        else if (e.key === "ArrowRight" || e.key === "PageDown" || (e.key === " " && !(e.target && e.target.tagName === "BUTTON"))) { e.preventDefault(); show(cur + 1); }
        else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); show(cur - 1); }
        else if (e.key === "Home") { e.preventDefault(); show(0); }
        else if (e.key === "End") { e.preventDefault(); show(list_.length - 1); }
      }
      function click(e) {
        var b = e.target.closest && e.target.closest("button"); if (!b) return;
        if (b.classList.contains("lp-c")) { choose(b); return; }
        var d = b.getAttribute("data-d"); if (d == null) return;
        if (d === "close") close(); else if (d === "prev") show(cur - 1); else if (d === "next") show(cur + 1); else show(+d);
      }
      function close() {
        ssims.forEach(function (h) { try { h.destroy && h.destroy(); } catch (e) { } }); ssims = [];
        document.removeEventListener("keydown", key, true); ov.removeEventListener("click", click);
        if (document.fullscreenElement === ov && document.exitFullscreen) { try { document.exitFullscreen(); } catch (e) { } }
        ov.parentNode && ov.parentNode.removeChild(ov); document.documentElement.classList.remove("lp-deck-open"); deck = null;
        if (prevFocus && prevFocus.focus) try { prevFocus.focus({ preventScroll: true }); } catch (e) { }
      }
      document.addEventListener("keydown", key, true); ov.addEventListener("click", click);
      if (gesture && ov.requestFullscreen && !ctx.noFullscreen) { try { var p = ov.requestFullscreen(); if (p && p.catch) p.catch(function () { }); } catch (e) { } }
      deck = { close: close };
      show(at || 0); stage.focus({ preventScroll: true });
    }
    on(document, "fullscreenchange", function () { if (deck && !document.fullscreenElement && !reduced()) { /* left full screen with Esc: the deck stays as an overlay; Esc again closes it */ } });

    // ---- clicks on the page
    on(root, "click", function (e) {
      var b = e.target.closest && e.target.closest("button");
      if (b && b.classList.contains("lp-c")) { choose(b); return; }
      if (b && b.classList.contains("lp-again")) { resetQuiz(b.closest(".lp-quiz")); return; }
      if (b && b.closest(".lp-th-ch") && b.hasAttribute("data-t")) { playFilm(+b.getAttribute("data-t")); return; }
      if (b && b.getAttribute("data-act")) {
        var act = b.getAttribute("data-act");
        if (act === "teach") teach(!root.classList.contains("lp-teacher"), true);
        else if (act === "play") playFilm();
        else if (act === "slides") openSlides(0, true);
        return;
      }
      var t = e.target.closest && e.target.closest(".lp-tiles a[data-sec], .lp-dots a[data-sec]");
      if (t) { e.preventDefault(); go(t.getAttribute("data-sec"), true); return; }
      var a = e.target.closest && e.target.closest("a[href^='#lesson-']"); if (!a) return;
      var m = a.getAttribute("href").match(/^#lesson-(\d+)(?:-(.+))?$/); if (!m || !m[2]) return;
      e.preventDefault();
      if (+m[1] === L.n && !L.maker) go(m[2], true);
      else { try { sessionStorage.setItem(PENDING, m[1] + ":" + m[2]); } catch (x) { } if (ctx.go) ctx.go("#lesson-" + m[1]); else location.hash = "#lesson-" + m[1]; }
    });
    function go(id, smooth) {
      if (id === "teach") { teach(true, true); return; }
      if (id === "film") { var th = root.querySelector(".lp-theatre"); if (th) th.scrollIntoView({ behavior: smooth && !reduced() ? "smooth" : "auto", block: "start" }); return; }
      if (id === "slides") { openSlides(0); return; }
      var t = document.getElementById(lid(L, id)); if (!t) return;
      var d = t.querySelector("details.lp-maths"); if (d) d.open = true;
      t.scrollIntoView({ behavior: smooth && !reduced() ? "smooth" : "auto", block: "start" });
      var h = t.querySelector("h2"); if (h) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); }
    }
    // under the shell's own bar, ours sticks just below it
    if (shellBar) {
      var sb = el.parentNode && el.parentNode.querySelector(".chapbar");
      var fit = function () { root.style.setProperty("--lp-top", Math.round(sb ? sb.getBoundingClientRect().height : 0) + "px"); };
      fit(); on(window, "resize", fit);
    }
    // reading progress
    var bar = root.querySelector(".lp-progress i"), body = root.querySelector(".lp-body");
    var dots = $$(".lp-dots a", root), secEls = dots.map(function (a) { return document.getElementById(lid(L, a.getAttribute("data-sec"))); }), lastOn = -2;
    function onScroll() {
      if (!bar) return; var rb = body.getBoundingClientRect(), p = Math.max(0, Math.min(1, (window.innerHeight * 0.5 - rb.top) / Math.max(1, rb.height))); bar.style.transform = "scaleX(" + p.toFixed(3) + ")";
      // the dots: every section whose top has passed the upper third of the screen is filled; the last of those is the one you are in
      var on = -1, line = window.innerHeight * 0.35; secEls.forEach(function (x, i) { if (x && x.getBoundingClientRect().top < line) on = i; });
      if (on === lastOn) return; lastOn = on;
      dots.forEach(function (a, i) { a.classList.toggle("lp-dot-past", i <= on); if (i === on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current"); });
    }
    on(window, "scroll", onScroll, { passive: true }); on(window, "resize", onScroll); onScroll();

    var want = ctx.section; try { var pend = sessionStorage.getItem(PENDING); if (pend && +pend.split(":")[0] === L.n) want = want || pend.split(":").slice(1).join(":"); sessionStorage.removeItem(PENDING); } catch (e) { }
    if (!want) { var hm = (location.hash || "").match(new RegExp("^#" + lid(L) + "-(.+)$")); if (hm) want = decodeURIComponent(hm[1]); }
    if (want) setTimeout(function () { go(want, false); }, 60);

    return { root: root, lesson: L, teach: teach, slides: openSlides, destroy: function () {
      if (deck) deck.close();
      sims.forEach(function (h) { try { h.destroy && h.destroy(); } catch (e) { } }); sims = [];
      offs.forEach(function (f) { f(); }); offs = [];
      o.urls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (e) { } });
    } };
  }

  /* The loader the shell calls.  Fetches data/lessons/lNN.json (or ctx.data, or uses ctx.lesson); destroys whatever lesson el held before. */
  C.renderLesson = function (n, el, ctx) {
    ctx = ctx || {}; n = +n || n;
    if (el.__curveLesson) { try { el.__curveLesson.destroy(); } catch (e) { } el.__curveLesson = null; }
    el.innerHTML = '<div class="lp lp-loading"><p class="lp-mini">Opening the lesson…</p></div>';
    var url = (ctx.base || "") + (ctx.data || "data/lessons/l" + pad(+n) + ".json");
    var got = ctx.lesson ? Promise.resolve(ctx.lesson) : (window.fetch ? fetch(url, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }) : Promise.reject(new Error("no fetch")));
    return got.then(function (L) {
      L.n = L.n || n; var h = render(L, el, ctx); el.__curveLesson = h; return h;
    }, function () {
      var c = COLOURS[(+n || 1) - 1] || "#4B5563";
      el.innerHTML = '<div class="lp" style="--lc:' + c + ";--lc-ink:" + inkOf(c) + ";--lc-soft:" + mix(c, "#FFFFFF", 0.86) + '"><header class="lp-head"><div class="lp-in"><div class="lp-hero lp-hero-one"><div class="lp-hero-t"><span class="lp-bignum" aria-hidden="true">' + esc(n) + '</span><p class="lp-kick">Lesson ' + esc(n) + " · " + esc(TITLES[n - 1] || "") + "</p><h1>" + esc(QUESTIONS[n - 1] || "") + '</h1><p class="lp-hook"><a href="#lessons">All the lessons</a></p></div></div></div></header></div>';
      return { destroy: function () { } };
    });
  };
  C.lessonColours = COLOURS;
  C.lessonTitles = TITLES;
  C.lessonQuestions = QUESTIONS;
})();
