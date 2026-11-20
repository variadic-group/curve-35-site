/* CURVE 35: one page, hash routes, all data from js/data.js (window.CURVE), written by site/build.py.
   The look: bright and friendly, for ages 14 and up: a yellow hero, ink outlines and hard shadows, one colour per lesson. A clear step-by-step kit, never a toy brand's look.
   Kept calm on purpose: few stickers, no jokes at the reader, only the buttons and the lesson tiles lift on hover.
   Lessons (site/COURSE_V2.md): the main shelf "How a camera works" (#lesson-1 ... #lesson-9) and the maker shelf "Made by a printer"
   (#maker-1 ... #maker-4, on the Files page).  Both are drawn by CURVE.renderLesson (js/lesson.js); the shell keeps the bar and the pager.
   #teach-N opens lesson N in its teacher view (ctx.teach); #teachers explains the teacher views, the slides and the class pack.
   The Builds gallery talks to shared storage only through CURVE_COMMUNITY.community() (js/community.js). */
(function () {
  "use strict";
  var C = window.CURVE || {};
  var G = C.guide || { sections: [], steps: [], parts: [], extras: [], trouble: [] };
  var LESSONS = C.lessons || [];
  var MAKERS = C.makers || [];
  var P = C.products || { groups: [], products: [] };
  var PIC = C.pictures || {};
  var FILES = C.files || { parts: [] };
  var view = document.getElementById("view");
  var say = document.getElementById("say");
  var current = "", cleanup = [];

  // ------------------------------------------------------------------ helpers
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function fmt(s) { return esc(s).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\*([^*]+)\*/g, "<em>$1</em>"); }
  function mmss(t) { t = Math.max(0, Math.round(Number(t) || 0)); return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0"); }
  function money(n) { return "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2 }); }
  function kib(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.round(n / 1024) + " KB"; }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function reduced() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
  function announce(t) { say.textContent = ""; setTimeout(function () { say.textContent = t; }, 30); }
  function img(src, alt, extra) { return src ? '<img' + (/media\/(img|3d)\//.test(src) ? ' class="r"' : "") + ' src="' + esc(src) + '" alt="' + esc(alt) + '" loading="lazy" decoding="async"' + (extra || "") + ">" : ""; }
  function store(key, val) { try { if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null"); localStorage.setItem(key, JSON.stringify(val)); } catch (e) { return null; } return val; }
  function minutes(s) { return Math.max(1, Math.round(s / 60)) + " min film"; }
  // the booklet's three facts, as stickers: the site's signature.  At most one more sticker goes on the same screen.
  function stk(text, tone) { return '<span class="stk stk-' + (tone || "o") + '">' + esc(text) + "</span>"; }
  // colours: a readable ink on any colour, and a soft tint of it
  function rgb(hex) { var n = parseInt(String(hex).slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function lum(hex) { var c = rgb(hex).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; }
  function onColour(hex) { var L = lum(hex); return (L + 0.05) / (0.0080 + 0.05) >= 1.05 / (L + 0.05) ? "#17140F" : "#FFFFFF"; }
  function tint(hex, k) { return "#" + rgb(hex).map(function (v) { return Math.round(v + (255 - v) * k).toString(16).padStart(2, "0"); }).join(""); }
  var LCOL = ["#1F8A70", "#2B6CD8", "#D23F31", "#E8641B", "#0E9AA7", "#1E5AA8", "#4B5563", "#B7791F", "#C2306B"];
  var MCOL = ["#7C8A1A", "#14A08C", "#E0402A", "#8A5CD0"];
  function lcol(L) { return L && /^#[0-9a-f]{6}$/i.test(L.colour || "") ? L.colour : (L && L.shelf === "maker" ? MCOL : LCOL)[((L && L.i) || 0) % 9] || "#4B5563"; }
  // a colour that small text can sit on at 4.5:1 or more (ink or white); darkened a step at a time if neither reaches it
  function safe(hex) {
    var c = rgb(hex), h = hex;
    for (var i = 0; i < 12; i++) { var L = lum(h); if (Math.max((L + 0.05) / 0.058, 1.05 / (L + 0.05)) >= 4.5) return h; c = c.map(function (v) { return Math.round(v * 0.9); }); h = "#" + c.map(function (v) { return v.toString(16).padStart(2, "0"); }).join(""); }
    return h;
  }
  function cvars(c, k) { var s = safe(c); return "--c:" + s + ";--on:" + onColour(s) + ";--t:" + tint(c, k == null ? 0.82 : k); }
  // inside Claude (window.claude.use) the page talks to the artifact host; anywhere else it is a plain static site
  function inClaude() { return !!(window.claude && typeof window.claude.use === "function"); }
  // a lesson's diagram (hero_fig in site/lessons/<id>.json), drawn by its sims file: inline SVG, no image file
  function figSvg(id) { var R = window.CURVE_REG && window.CURVE_REG.figs, fn = R && id && R[id]; if (!fn) return ""; try { return fn() || ""; } catch (e) { return ""; } }
  var VTT = {}; function vttUrl(L) { if (L.vtt_src && !inClaude()) return L.vtt_src; if (!VTT[L.id]) { try { VTT[L.id] = URL.createObjectURL(new Blob([L.vtt || ""], { type: "text/vtt" })); } catch (e) { VTT[L.id] = ""; } } return VTT[L.id]; }
  var STEP = {}; G.steps.forEach(function (s) { STEP[s.code] = s; });
  var SECNAME = { "BUILD": "Build", "FILM IN": "Film in", "PHOTOS": "Photos", "FILM OUT": "Film out", "THE HOLE": "Pinhole experiment" };
  var SECBAR = { "BUILD": "BUILD", "FILM IN": "FILM IN", "PHOTOS": "PHOTOS", "FILM OUT": "FILM OUT", "THE HOLE": "PINHOLE" };

  // ------------------------------------------------------------------ the canon as a graph (site/build.py build_graph): every cross-link on the site comes from here
  var GR = C.graph || { parts: [], steps: [], lessons: {}, facts: [], checks: [], terms: [], offers: [], programs: [], ways: [] };
  var VID = C.video || null;
  var GP = {}, GPK = {}, GS = {}, GF = {}, GC = {}, GT = {}, GO = {}, GPG = {};
  GR.parts.forEach(function (p) { GP[p.id] = p; GPK[p.key] = p; });
  GR.steps.forEach(function (s, i) { s.i = i; GS[s.id] = s; });
  GR.facts.forEach(function (f) { GF[f.id] = f; });
  GR.checks.forEach(function (c) { GC[c.id] = c; });
  GR.terms.forEach(function (t) { GT[t.id] = t; });
  GR.offers.forEach(function (o) { GO[o.id] = o; });
  GR.programs.forEach(function (g) { GPG[g.id] = g; });
  function rid(id) { return String(id).replace(/_/g, "-"); }
  var FACT_BY_RID = {}, CHECK_BY_RID = {}; GR.facts.forEach(function (f) { FACT_BY_RID[rid(f.id)] = f; }); GR.checks.forEach(function (c) { CHECK_BY_RID[rid(c.id)] = c; });
  var LINK = {     // id -> [href, label]
    part: function (id) { var p = GP[id]; return p ? ["#part-" + p.key, p.name] : null; },
    step: function (id) { var s = GS[id]; return s ? ["#build-" + id, (SECNAME[s.sec] || s.sec) + " " + s.n + ": " + s.title] : null; },
    lesson: function (id) { var L = GR.lessons[id]; return L ? ["#" + L.route, (L.shelf === "maker" ? "Maker lesson " : "Lesson ") + L.num + ": " + L.title] : null; },
    term: function (id) { var t = GT[id]; return t ? ["#glossary-" + id, t.term] : null; },
    fact: function (id) { var f = GF[id]; return f ? ["#fact-" + rid(id), f.say] : null; },
    check: function (id) { var c = GC[id]; return c ? ["#check-" + rid(id), c.name] : null; },
    offer: function (id) { var o = GO[id]; return o ? ["#offer-" + id, o.name] : null; },
    program: function (id) { var g = GPG[id]; return g ? ["#program-" + id, g.name] : null; }
  };
  function xchips(kind, ids, label) {
    var items = (ids || []).map(function (id) { return LINK[kind](id); }).filter(Boolean);
    if (!items.length) return "";
    return '<ul class="xchips xc-' + kind + '"' + (label ? ' aria-label="' + esc(label) + '"' : "") + ">" + items.map(function (x) { return '<li><a href="' + x[0] + '">' + esc(x[1]) + "</a></li>"; }).join("") + "</ul>";
  }
  function xrow(name, kind, ids) { var c = xchips(kind, ids, name); return c ? '<div class="xrow"><dt>' + esc(name) + "</dt><dd>" + c + "</dd></div>" : ""; }
  // a small "Related" block at the end of a lesson or the build guide: links from the canon graph, at most eight, none twice
  function relatedBlock(items) {
    var seenH = {}, out = [];
    items.forEach(function (x) { if (x && !seenH[x[0]] && out.length < 8) { seenH[x[0]] = 1; out.push(x); } });
    if (!out.length) return "";
    return '<aside class="related" aria-labelledby="rel-h"><div class="wrap"><h2 id="rel-h">Related</h2><ul>' + out.map(function (x) { return '<li><a href="' + x[0] + '"><span class="rel-k">' + esc(x[2] || "") + "</span>" + esc(x[1]) + "</a></li>"; }).join("") + "</ul></div></aside>";
  }
  function rel(kind, id, tag) { var x = LINK[kind](id); return x ? [x[0], x[1], tag] : null; }
  function relPage(h, label, tag) { return ["#" + h, label, tag || "Page"]; }
  function relatedFor(h, L) {
    var r = [];
    if (L) {
      var G0 = GR.lessons[L.id] || { parts: [], steps: [], terms: [] };
      G0.steps.slice(0, 2).forEach(function (s) { r.push(rel("step", s, "Build step")); });
      G0.terms.slice(0, 2).forEach(function (t) { r.push(rel("term", t, "Word")); });
      Object.keys(GR.lessons).forEach(function (o) { if (o !== L.id && GR.lessons[o].parts.some(function (p) { return G0.parts.indexOf(p) >= 0; })) r.push(rel("lesson", o, "Same part")); });
      r.push(relPage("facts", "The camera in numbers", "Facts"));
      return r;
    }
    if (h === "build") {
      var s = GS[BUILD_AT] || GR.steps[0];
      if (s) { if (s.lesson) r.push(rel("lesson", s.lesson, "Lesson")); s.parts.forEach(function (p) { r.push(rel("part", p.id, "Part")); }); s.terms.forEach(function (t) { r.push(rel("term", t, "Word")); }); }
      return r.concat([relPage("parts", "Every part, in one table"), relPage("help", "Help: something not right?"), relPage("glossary", "Glossary")]);
    }
    return r;
  }

  // ---- glossary words in running text: underlined, a tooltip with the meaning, a link to the word (and from there to where it is taught)
  var GL_N = 0;
  var GL_SKIP = "a,button,h1,h2,h3,h4,summary,label,svg,figure,code,script,style,select,option,textarea,input,.glw,.xchips,.related,[role=tooltip]";
  function glossTip(t) {
    var where = t.taught.map(function (l) { var L = GR.lessons[l]; return L ? (L.shelf === "maker" ? "Maker lesson " : "Lesson ") + L.num : ""; }).filter(Boolean);
    return t.means + (where.length ? " Taught in " + where.join(", ") + "." : "");
  }
  function glossarize(root, ids) {
    if (!root || !GR.terms.length) return;
    var done = {}; $$(".glw[data-term]", root).forEach(function (w) { done[w.getAttribute("data-term")] = 1; });
    var terms = (ids || GR.terms.map(function (t) { return t.id; })).map(function (id) { return GT[id]; }).filter(function (t) { return t && !done[t.id]; });
    terms.sort(function (a, b) { return b.term.length - a.term.length; });
    if (!terms.length) return;
    var blocks = $$("p, li, dd, td", root).filter(function (el) { return !el.closest(GL_SKIP); });
    terms.forEach(function (t) {
      var rx = new RegExp("\\b(" + t.term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/ /g, "\\s+") + ")(s|es)?\\b", "i");
      for (var b = 0; b < blocks.length; b++) {
        var w = document.createTreeWalker(blocks[b], NodeFilter.SHOW_TEXT, null), n, hit = false;
        while ((n = w.nextNode())) {
          if (n.parentNode.closest(GL_SKIP)) continue;
          var m = rx.exec(n.nodeValue); if (!m) continue;
          var after = n.splitText(m.index); after.splitText(m[0].length);
          var id = "gt-" + (++GL_N), wrap = document.createElement("span"); wrap.className = "glw"; wrap.setAttribute("data-term", t.id);
          wrap.innerHTML = '<a class="gl" href="#glossary-' + t.id + '" aria-describedby="' + id + '">' + esc(m[0]) + '</a><span class="gl-tip" role="tooltip" id="' + id + '">' + esc(glossTip(t)) + "</span>";
          after.parentNode.replaceChild(wrap, after); hit = true; break;
        }
        if (hit) break;
      }
    });
  }
  // a tooltip can be put away with Escape (WCAG 1.4.13) and comes back on the next hover or focus
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") $$(".glw").forEach(function (w) { w.classList.add("glw-off"); }); });
  document.addEventListener("pointerover", function (e) { var w = e.target.closest && e.target.closest(".glw"); if (w) w.classList.remove("glw-off"); });
  document.addEventListener("focusin", function (e) { var w = e.target.closest && e.target.closest(".glw"); if (w) w.classList.remove("glw-off"); });

  // ---- three ways in: the owner's positioning (canon/offers.yaml 'ways').  Open and free to print; the kit sells convenience; wholesale for groups
  function waysStrip(here) {
    var W = {}; GR.ways.forEach(function (w) { W[w.id] = w; });
    var free = W["print-free"], kit = W["kit-direct"], whole = W.wholesale;
    function card(cls, h, p, acts) { return '<li class="way ' + cls + '"><h2 class="way-h">' + h + "</h2><p>" + p + '</p><p class="way-a">' + acts + "</p></li>"; }
    var q = mailto(MAIL.schools, "CURVE 35 wholesale quote", "Hello,\n\nWe'd like a wholesale quote.\n\nWho we are (shop, school, makerspace):\nHow many kits:\nWhen:\nShip to (city and country):\n\nAnything else:\n");
    return '<ul class="ways" aria-label="Three ways in">' +
      (free ? card("w-free", "Print it free", "Every file, the source and the lessons. Open, under " + '<a href="#open-files">' + esc("CC BY-NC-SA") + "</a>. Add one lens.", '<a class="btn small" href="#files">Get the files</a>') : "") +
      (kit ? card("w-kit", "Buy the kit", "Skip the printing and the hunt for parts. Printed, checked, posted, with film if you like.", here === "store" ? '<a class="btn small main" href="#offer-starter-kit" data-go="p-starter-kit">See the kits</a><a class="btn small" href="#spares" data-go="p-extras">Add-ons</a>' : '<a class="btn small main" href="#store">See the kits</a>') : "") +
      (whole ? card("w-whole", "Wholesale and programs", "Shops, schools and makerspaces: class sets, case packs and four ready-made programs, by quote.", here === "programs" ? '<a class="btn small main" href="#wholesale" data-go="wholesale">Wholesale terms</a><a class="btn small" href="' + esc(q) + '">Email for a quote</a>' : '<a class="btn small" href="#programs">Programs</a><a class="btn small" href="' + esc(q) + '">Email for a quote</a>') : "") + "</ul>";
  }


  // ------------------------------------------------------------------ lessons: both shelves, by route
  var ROUTE = {};
  LESSONS.forEach(function (L, i) { L.shelfList = LESSONS; L.i = i; ROUTE[L.route] = L; });
  MAKERS.forEach(function (L, i) { L.shelfList = MAKERS; L.i = i; ROUTE[L.route] = L; });
  function lessonName(L) { return (L.shelf === "maker" ? "Maker lesson " : "Lesson ") + L.num; }

  // ------------------------------------------------------------------ the parts
  var FILE = {}; FILES.parts.forEach(function (f) { FILE[f.key] = f; });
  var GPART = {}; G.parts.concat(G.extras || []).forEach(function (p) { GPART[p.key] = p; });
  // every part, with the colour it is printed in (a soft tint of it sits behind its picture)
  var CARDS = G.cards || { parts: [], bonus: [], lesson_parts: {} };     // canon/parts.yaml ('card') and canon/lessons.yaml ('parts'), by way of site/build.py
  var PARTS = CARDS.parts;
  var BONUS = CARDS.bonus;
  var ALLPARTS = PARTS.concat(BONUS), PART = {}; ALLPARTS.forEach(function (p, i) { p.i = i; PART[p.key] = p; });
  function partImg(key) { return (FILE[key] && FILE[key].img) || (GPART[key] && GPART[key].img) || (key === "cassette" ? PIC.cassette : key === "lens" ? PIC.lens : null) || ("media/img/part_" + key + ".webp"); }
  var LESSON_PARTS = CARDS.lesson_parts;
  // a simple row of renders with names (no cards)
  function partsRow(keys, link) {
    return '<ul class="prow">' + keys.map(function (k) {
      var p = PART[k], inner = '<span class="prow-pic">' + img(partImg(k), "", ' width="520" height="390"') + "</span><span>" + esc(p.name) + "</span>";
      return "<li>" + (link ? '<a href="#part-' + k + '">' + inner + "</a>" : inner) + "</li>";
    }).join("") + "</ul>";
  }

  // one film plays at a time
  document.addEventListener("play", function (e) { $$("video").forEach(function (v) { if (v !== e.target && !v.paused) v.pause(); }); }, true);
  // links inside a page that scroll to a part of it (the hash stays the page's own)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-go]"); if (!a) return;
    var el = document.getElementById(a.getAttribute("data-go")); if (!el) return;
    e.preventDefault(); el.setAttribute("tabindex", "-1"); el.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" }); el.focus({ preventScroll: true });
  });

  // ------------------------------------------------------------------ basket (this browser only; nothing is sent until the reader sends the email)
  var META = C.meta || {};                  // canon/company.yaml, by way of site/build.py
  var MAIL = META.email || {};
  function mailLink(m) { return '<a href="mailto:' + esc(m) + '">' + esc(m) + "</a>"; }
  function mailto(to, subject, body) { return "mailto:" + to + "?subject=" + encodeURIComponent(subject) + (body ? "&body=" + encodeURIComponent(body) : ""); }
  var KEY = "curve35-basket", memory = {};
  function loadBasket() { try { var b = JSON.parse(localStorage.getItem(KEY) || "{}"); return b && typeof b === "object" ? b : {}; } catch (e) { return memory; } }
  function saveBasket(b) { memory = b; try { localStorage.setItem(KEY, JSON.stringify(b)); } catch (e) { /* storage off: the basket lives until the page closes */ } countBasket(); }
  var PROD = {}; P.products.forEach(function (p) { PROD[p.id] = p; });
  function price(p) { return p.price_usd === 0 ? "Free" : typeof p.price_usd === "number" ? money(p.price_usd) : p.price_text; }
  function basketItems() { var b = loadBasket(); return Object.keys(b).filter(function (id) { return PROD[id] && PROD[id].basket && b[id] > 0; }).map(function (id) { return { p: PROD[id], q: Math.min(99, Math.floor(b[id])) }; }); }
  function countBasket() {
    var n = basketItems().reduce(function (a, i) { return a + i.q; }, 0), el = document.getElementById("basket-count"), btn = document.getElementById("basket-open");
    if (el) el.textContent = String(n);
    var ti = document.querySelector(".top-in"); if (ti) ti.classList.toggle("has-basket", !!n);
    if (btn) { btn.hidden = !n; btn.setAttribute("aria-label", "Basket: " + n + (n === 1 ? " item" : " items")); }
    return n;
  }
  function addToBasket(id) { var b = loadBasket(); b[id] = Math.min(99, (b[id] || 0) + 1); saveBasket(b); }
  var dlg = document.getElementById("basket");
  function basketBody() {
    var items = basketItems();
    if (!items.length) return '<p>Nothing in here yet.</p><p><a href="#store" data-close>The starter kit</a> is the one to start with.</p>';
    var total = items.reduce(function (a, i) { return a + i.p.price_usd * i.q; }, 0);
    return '<ul class="bl">' + items.map(function (i) {
        return "<li><div><strong>" + esc(i.p.name) + '</strong><br><span class="quiet small">' + price(i.p) + " each</span></div>" +
          '<div class="qty" role="group" aria-label="How many: ' + esc(i.p.name) + '"><button type="button" data-dec="' + i.p.id + '" aria-label="One fewer ' + esc(i.p.name) + '">&minus;</button><output aria-live="polite">' + i.q + '</output><button type="button" data-inc="' + i.p.id + '" aria-label="One more ' + esc(i.p.name) + '">+</button></div>' +
          '<div class="lsub"><span class="tnum">' + money(i.p.price_usd * i.q) + '</span><button type="button" class="linkbtn" data-del="' + i.p.id + '">Remove</button></div></li>';
      }).join("") + "</ul>" +
      '<p class="tot"><span>Total</span><span class="tnum">' + money(total) + '</span></p><p class="note">Before postage and tax.</p>' +
      (PAY.state === "on"
        ? '<button type="button" class="btn main wide-btn" id="pay">Checkout</button>' +
          '<p class="note order-note" id="pay-note">Card payment by Stripe. Postage and tax are shown before you pay.</p>' +
          '<p class="note"><a id="checkout" href="' + esc(orderMail(items, total)) + '">Or order by email</a></p>'
        : '<a class="btn main wide-btn" id="checkout" href="' + esc(orderMail(items, total)) + '">Order by email</a>' +
          '<p class="note order-note">We reply within one business day with a payment link.</p>');
  }
  // Card checkout.  The site's Worker (/api/checkout) turns the basket into a Stripe page when it is switched on.  It is asked once, when the basket
  // first opens.  Until it says yes, and wherever there is no Worker (the site opened from a file), the order goes by email.  Prices are the Worker's, not ours.
  var PAY = { state: "?" };
  function askPay(done) {
    if (PAY.state !== "?") return done();
    if (!/^https?:$/.test(location.protocol) || !window.fetch) { PAY.state = "off"; return done(); }
    PAY.state = "asking";
    fetch("/api/checkout", { headers: { accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : { on: false }; })
      .then(function (d) { PAY.state = d && d.on === true ? "on" : "off"; }, function () { PAY.state = "off"; })
      .then(done);
  }
  function pay(btn) {
    var note = $("#pay-note"), items = basketItems().map(function (i) { return { id: i.p.id, q: i.q }; });
    function failed() { btn.disabled = false; btn.textContent = "Checkout"; if (note) note.textContent = "The card page did not open. Try again, or order by email below."; announce("The card page did not open."); }
    btn.disabled = true; btn.textContent = "One moment";
    fetch("/api/checkout", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ items: items }) })
      .then(function (r) { return r.json().then(function (d) { return r.ok && d && typeof d.url === "string" && /^https:\/\/checkout\.stripe\.com\//.test(d.url) ? d.url : null; }); })
      .then(function (url) { if (url) location.assign(url); else failed(); }, failed);
  }
  // the order, written out for an email to hello@: one line per item, the total, and room for a name and an address
  function orderMail(items, total) {
    var n = items.reduce(function (a, i) { return a + i.q; }, 0);
    var lines = items.map(function (i) { return i.q + " x " + i.p.name + " (" + money(i.p.price_usd) + " each): " + money(i.p.price_usd * i.q); });
    return mailto(MAIL.hello, "CURVE 35 order: " + n + (n === 1 ? " item, " : " items, ") + money(total),
      "Hello, I'd like to order:\n\n" + lines.join("\n") + "\n\nTotal: " + money(total) + " (before postage and tax)\n\nName:\nShip to:\n");
  }
  function drawBasket(focusSel) {
    $("#basket-body").innerHTML = basketBody();
    function set(id, q, sel) { var b = loadBasket(); q = Math.max(0, Math.min(99, Math.floor(Number(q) || 0))); if (q) b[id] = q; else delete b[id]; saveBasket(b); drawBasket(sel); }
    $$("#basket-body [data-inc]").forEach(function (b) { b.onclick = function () { set(b.dataset.inc, (loadBasket()[b.dataset.inc] || 0) + 1, '[data-inc="' + b.dataset.inc + '"]'); }; });
    $$("#basket-body [data-dec]").forEach(function (b) { b.onclick = function () { var q = (loadBasket()[b.dataset.dec] || 0) - 1; set(b.dataset.dec, q, q > 0 ? '[data-dec="' + b.dataset.dec + '"]' : "#basket-x"); }; });
    $$("#basket-body [data-del]").forEach(function (b) { b.onclick = function () { set(b.dataset.del, 0, "#basket-x"); announce("Removed."); }; });
    $$("#basket-body [data-close]").forEach(function (a) { a.onclick = function () { closeBasket(); }; });
    var pb = $("#pay"); if (pb) pb.onclick = function () { pay(pb); };
    if (focusSel) { var el = $(focusSel); if (el) el.focus(); }
  }
  var lastFocus = null;
  function openBasket() {
    lastFocus = document.activeElement; drawBasket();
    if (dlg.showModal) { if (!dlg.open) dlg.showModal(); } else dlg.setAttribute("open", "");
    $("#basket-x").focus();
    if (PAY.state === "?") askPay(function () { if (PAY.state === "on" && dlg.open) drawBasket(); });
  }
  function closeBasket() { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); }
  dlg.addEventListener("close", function () { if (lastFocus && lastFocus.focus) lastFocus.focus(); });
  dlg.addEventListener("click", function (e) { if (e.target === dlg) closeBasket(); });
  $("#basket-x").addEventListener("click", closeBasket);
  $("#basket-open").addEventListener("click", openBasket);
  function addButtons() {
    $$("[data-add]").forEach(function (b) {
      b.addEventListener("click", function () {
        addToBasket(b.dataset.add); var n = countBasket();
        announce(PROD[b.dataset.add].name + " added. " + n + (n === 1 ? " item" : " items") + " in the basket.");
        openBasket();
      });
    });
  }
  function addBtn(p, cls, label) { return p && p.basket ? '<button class="btn ' + (cls || "") + '" type="button" data-add="' + esc(p.id) + '">' + esc(label || "Add to basket") + '<span class="sr-only">: ' + esc(p.name) + "</span></button>" : ""; }

  // ------------------------------------------------------------------ the top bar's menu (narrow screens)
  var menuBtn = $("#menu-btn"), menu = $("#nav-more");
  menuBtn.addEventListener("click", function () { var open = menuBtn.getAttribute("aria-expanded") === "true"; menuBtn.setAttribute("aria-expanded", String(!open)); menu.classList.toggle("open", !open); });
  function closeMenu() { menuBtn.setAttribute("aria-expanded", "false"); menu.classList.remove("open"); }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && menu.classList.contains("open")) { closeMenu(); menuBtn.focus(); } });

  // ------------------------------------------------------------------ pieces shared by pages
  // ---- the camera viewer: a full-width stage; a slider (and five stage buttons) takes it apart, dragging turns it.  camera3d.js draws it.
  var X3_CAPS = [
    ["Closed", "Everything clicked shut. Slide to take it apart."],
    ["1 The dark box", "Body and back. They keep the light off the film."],
    ["2 The film path", "Red spool, green knob, blue frame wheel. One turn, one picture."],
    ["3 The front plate", "The shutter, and the wheel with three holes."],
    ["4 The lens, or a pinhole", "A 12 mm lens presses in. Or the pinhole disc and ring, in the same pocket."]
  ];
  var X3_SHORT = ["Closed", "Dark box", "Film path", "Front plate", "Lens"];
  function explodeSection() {
    var M = C.model3d; if (!M) return "";
    var arrow = function (d) { return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + (d < 0 ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7") + '"/></svg>'; };
    return '<section class="x3" id="inside" aria-labelledby="x3-h"><div class="wrap x3-head"><div><h2 id="x3-h">Take it apart.</h2></div>' +
      '<p class="x3-how">Slide to open it. Drag to turn it.</p></div>' +
      '<div class="x3-stage">' + img(M.still, "The camera taken apart: the black body in the middle, the grey back behind it, the red, green and blue knobs above, the orange front plate in front with the shutter and wheel, and the lens in front of that.", ' class="x3-still" width="' + (M.still_w || 1159) + '" height="' + (M.still_h || 1163) + '"').replace(' class="r"', "") + "</div>" +
      '<div class="wrap x3-bar"><div class="x3-steps" role="group" aria-label="Build stages">' +
      X3_CAPS.map(function (c, i) { return '<button type="button" class="x3-go" data-go="' + i + '" aria-pressed="' + (i === 0) + '">' + (i ? "<b>" + i + "</b>" : "") + esc(X3_SHORT[i]) + "</button>"; }).join("") + "</div>" +
      '<div class="x3-slide"><button type="button" class="x3-turn" data-turn="-40" aria-label="Turn left">' + arrow(-1) + '</button><label class="sr-only" for="x3-range">Take the camera apart</label>' +
      '<input class="x3-range" id="x3-range" type="range" min="0" max="4" step="0.01" value="0"><button type="button" class="x3-turn" data-turn="40" aria-label="Turn right">' + arrow(1) + "</button></div>" +
      '<div class="x3-caps" aria-live="polite">' + X3_CAPS.map(function (c, i) { return '<p class="x3-cap" data-i="' + i + '" data-say="' + esc(c[0]) + '"' + (i ? " hidden" : "") + "><strong>" + esc(c[0]) + "</strong> " + esc(c[1]) + "</p>"; }).join("") + "</div></div></section>";
  }
  function mountExplode() {
    var s = document.getElementById("inside"); if (!s || !window.Camera3D || !C.model3d) return;
    if (window.getComputedStyle(s).display === "none") return;
    var h = window.Camera3D.viewer(s, C.model3d); cleanup.push(function () { h.destroy(); });
    // On a phone the viewer is a small stage with one slider (site.css, v12).  The first time it is on screen it takes itself apart once, slowly, so that
    // nobody has to find the slider to see what it does.  A touch on it stops that, and so does asking for less motion.
    var range = s.querySelector(".x3-range"), stage = s.querySelector(".x3-stage");
    if (!range || !stage || !window.IntersectionObserver || reduced() || !(window.matchMedia && window.matchMedia("(max-width: 600px)").matches)) return;
    var raf = 0, done = false, t0 = 0;
    function stop() { done = true; if (raf) cancelAnimationFrame(raf); raf = 0; }
    function tick(now) {
      if (done) return; if (!t0) t0 = now;
      var k = Math.min(1, (now - t0) / 5200), v = 4 * (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);     // ease in and out, closed to fully open
      range.value = String(v); range.dispatchEvent(new Event("input", { bubbles: true }));
      if (k < 1) raf = requestAnimationFrame(tick); else stop();
    }
    var io = new IntersectionObserver(function (es) { if (!done && !raf && es[es.length - 1].intersectionRatio >= 0.6 && s.classList.contains("x3-ready")) { io.disconnect(); raf = requestAnimationFrame(tick); } }, { threshold: [0, 0.6, 1] });
    io.observe(stage);
    ["pointerdown", "keydown"].forEach(function (ev) { range.addEventListener(ev, stop); stage.addEventListener(ev, stop); });
    cleanup.push(function () { stop(); io.disconnect(); });
  }
  function mountHero() {
    var b = document.getElementById("h3d"); if (!b || !window.Camera3D || !C.model3d) return;
    var h = window.Camera3D.hero(b, C.model3d); cleanup.push(function () { h.destroy(); });
  }
  var SEEN_KEY = "curve35-opened";
  function seen() { return store(SEEN_KEY) || {}; }
  // the main shelf: one colour per lesson.  full: the Lessons page (with the lesson's picture)
  function shelfGrid(list, full) {
    var S = seen();
    return '<ol class="tiles' + (full ? " full" : "") + '" role="list">' + list.map(function (L) {
      var R = L.render, F = figSvg(L.fig);
      return '<li><a class="tile' + (F ? " has-fig" : "") + '" href="#' + L.route + '" style="' + cvars(lcol(L)) + '">' + (F ? '<span class="tl-pic tl-fig" aria-hidden="true">' + F + "</span>" : "") + '<span class="tl-n" aria-hidden="true">' + esc(L.num) + '</span>' +
        '<span class="tl-t"><span class="sr-only">' + lessonName(L) + ": </span>" + esc(L.title) + "</span>" +
        '<span class="tl-q">' + esc(L.question) + "</span>" +
        (!F && full && R ? '<span class="tl-pic" aria-hidden="true">' + img(R.src, "", ' width="900" height="675"') + "</span>" : "") +
        (full ? '<span class="tl-m">' + (L.id === "l08" || L.id === "l09" ? "Part: the whole camera &middot; " : (LESSON_PARTS[L.id] || [])[0] && PART[LESSON_PARTS[L.id][0]] ? "Part: " + esc(PART[LESSON_PARTS[L.id][0]].name) + " &middot; " : "") + (L.duration_s ? minutes(L.duration_s) : "Read and try") + (S[L.id] ? " &middot; opened" : "") + "</span>" : "") + "</a></li>";
    }).join("") + "</ol>";
  }
  // the maker shelf: a tidy row of four
  function makerRow(head) {
    return '<ol class="mrow" role="list">' + MAKERS.map(function (L) {
      var F = figSvg(L.fig);
      return '<li><a href="#' + L.route + '" style="' + cvars(lcol(L), 0.86) + '">' + (F ? '<span class="mr-fig" aria-hidden="true">' + F + "</span>" : "") + '<span class="mr-n" aria-hidden="true">' + esc(L.num) + '</span><span class="mr-t"><span class="sr-only">' + lessonName(L) + ": </span>" + esc(L.title) + "</span>" +
        (head ? "" : '<span class="mr-q">' + esc(L.question) + "</span>") + "</a></li>";
    }).join("") + "</ol>";
  }
  // a part as a collectable card: a band in the colour it is printed in (with its number), its picture on a tint of that colour, its name.
  // full (the Parts page): what it does, three small facts, and (folded away) its steps, checks and where to get it.
  function partCard(p, full, num, of) {
    var f = FILE[p.key] || {}, n = num ? String(num).padStart(2, "0") : "";
    var band = '<span class="pt-band" style="--b:' + p.hex + ";--bo:" + onColour(p.hex) + '" aria-hidden="true"><span>' + (n ? n + (of ? "/" + String(of).padStart(2, "0") : "") : "Extra") + "</span></span>";
    var pic = '<span class="pt-pic" style="--t:' + tint(p.hex, 0.84) + '">' + img(partImg(p.key), full ? "The " + p.name.toLowerCase() : "", ' width="520" height="390"') + "</span>";
    if (!full) return '<li><a class="pt" href="#part-' + p.key + '">' + band + pic + '<span class="pt-name">' + esc(p.name) + "</span></a></li>";
    var stats = [];
    if (f.time) stats.push(["Print", esc(f.time.replace(/ \d+s$/, ""))]);
    if (f.grams != null) stats.push(["Plastic", esc(Math.round(f.grams * 10) / 10) + " g"]);
    if (f.colour) stats.push(["Colour", esc(f.colour.split(",")[0])]);
    if (!stats.length && p.key === "lens") stats = [["Across", "12 mm"], ["Focus", "32 mm"], ["Printed", "no"]];
    if (!stats.length && p.key === "cassette") stats = [["Pictures", "24 or 36"], ["Size", "35 mm"]];
    return '<li class="pt" id="part-' + p.key + '" tabindex="-1">' + band + pic + '<h3 class="pt-name">' + esc(p.name) + "</h3><p>" + esc(p.line) + "</p>" +
      (stats.length ? '<dl class="pt-stats">' + stats.map(function (x) { return "<div><dt>" + x[0] + "</dt><dd>" + x[1] + "</dd></div>"; }).join("") + "</dl>" : "") +
      (GPK[p.key] ? partMore(GPK[p.key], false) : "") + "</li>";
  }

  // ------------------------------------------------------------------ pages
  var pages = {};

  // ---- home (v12): a short pitch.  The way back in for owners is the menu (Start here, Build guide, Lessons, Files, Help).
  //      hero > what's in the box (the one kit block) > how it works (4 steps) > lesson carousel
  //      > four facts (none repeated elsewhere on the page) > the camera viewer > one strip of links > last call
  //      On a phone (site.css, v12): the camera sits above the buttons; the viewer is a small stage with one slider, with the four facts as
  //      stickers under it; the strip of links is left out.
  var REPO = META.repo;
  var CC = META.licence_url;
  function factSay(id, fb) { var f = GF[id]; return String(f && f.say != null ? f.say : fb).replace(/^about /, ""); }
  // the lessons as a swipeable row of colourful tiles: the diagram on white, the number, the title and the hook question
  function lessonCarousel() {
    var arrow = function (d) { return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + (d < 0 ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7") + '"/></svg>'; };
    return '<div class="lcar"><ol class="lcar-track" id="lcar" role="list" tabindex="0" aria-label="The nine lessons: scroll sideways">' + LESSONS.map(function (L) {
      var F = figSvg(L.fig), R = L.render;
      return '<li><a class="ltile" href="#' + L.route + '" style="' + cvars(lcol(L)) + '"><span class="lt-n" aria-hidden="true">' + esc(L.num) + "</span>" +
        '<span class="lt-t"><span class="sr-only">' + lessonName(L) + ": </span>" + esc(L.title) + '</span><span class="lt-q">' + esc(L.question) + "</span>" +
        '<span class="lt-pic" aria-hidden="true">' + (F || (R ? img(R.src, "", ' width="900" height="675"') : "")) + "</span></a></li>";
    }).join("") + "</ol>" +
      '<div class="lcar-nav"><button type="button" class="lcar-b" data-dir="-1" aria-controls="lcar" aria-label="Earlier lessons">' + arrow(-1) + '</button><button type="button" class="lcar-b" data-dir="1" aria-controls="lcar" aria-label="Later lessons">' + arrow(1) + "</button></div></div>";
  }
  function mountCarousel() {
    var t = document.getElementById("lcar"); if (!t) return;
    var bs = $$(".lcar-b");
    function step() { var li = t.querySelector("li"); return li ? li.getBoundingClientRect().width + 20 : 300; }
    function go(d) { t.scrollBy({ left: d * step(), behavior: reduced() ? "auto" : "smooth" }); }
    function ends() { var max = t.scrollWidth - t.clientWidth - 4; bs[0].disabled = t.scrollLeft <= 4; bs[1].disabled = t.scrollLeft >= max; }
    bs.forEach(function (b) { b.addEventListener("click", function () { go(Number(b.dataset.dir)); }); });
    t.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); go(e.key === "ArrowRight" ? 1 : -1); }
    });
    // a tile reached by Tab comes fully into view
    t.addEventListener("focusin", function (e) { var li = e.target.closest && e.target.closest("li"); if (li && li.scrollIntoView) li.scrollIntoView({ block: "nearest", inline: "nearest", behavior: reduced() ? "auto" : "smooth" }); });
    t.addEventListener("scroll", ends, { passive: true }); window.addEventListener("resize", ends); cleanup.push(function () { window.removeEventListener("resize", ends); });
    ends();
  }
  pages.home = function () {
    var S = PROD["starter-kit"] || {}, sp = S.price_usd != null ? money(S.price_usd) : "";
    var heroAlt = "The CURVE 35 camera: a black body, an orange front plate with a round lens, a red knob and a green knob on top";
    // what is in the starter kit, from its canon contents (offers.yaml): short, one line each
    var kitList = ["Every piece of the camera, plus 2 spares", "A pinhole ring and disc", "The printed build guide", "A roll of colour film (" + factSay("kit_film_pictures", "24") + " pictures), with developing and scans"];
    var dots = [factSay("f_small", "f/16"), factSay("f_middle", "f/11"), factSay("f_large", "f/9.5")];
    return '<div class="home">' +
      // HERO
      '<section class="hero" aria-labelledby="hero-h"><div class="wrap hero-in"><div class="hero-text">' +
      '<ul class="hero-stks" aria-label="In short"><li class="stk stk-w">' + esc(String(C.pieces || 9)) + ' pieces</li><li class="stk stk-g">No tools</li><li class="stk stk-b">No glue</li></ul>' +
      '<h1 id="hero-h">Build a real film camera. <span class="hl">Then find out how it works.</span></h1>' +
      '<p class="lead">A 35 mm film camera you build from nine pieces, and learn from.</p>' +
      '<div class="ctas"><a class="btn main big" href="#store">Buy the kit</a><a class="btn big alt" href="#files">Print your own</a></div></div>' +
      '<div class="hero-pic"><span class="hero-stk" aria-hidden="true"><span class="stk stk-o">Real film!</span></span><div class="frame h3d" id="h3d">' + img(PIC.hero, heroAlt, ' class="h3d-still" width="1200" height="900" fetchpriority="high" loading="eager"').replace(' class="r"', "").replace(' loading="lazy"', "") + "</div></div></div></section>" +
      // WHAT'S IN THE BOX: the one kit block on the page
      '<section class="kitbox" aria-labelledby="kb-h"><div class="wrap kitbox-in"><div class="kb-pic frame">' + img(PIC.plan_parts, "Everything in the box laid out: black body, grey back, orange front plate, teal shutter, yellow wheel, red spool, green knob, blue frame wheel, lens, pinhole ring and disc, and a roll of film", ' width="1200" height="900"') + "</div>" +
      '<div class="kb-t"><p class="kb-k">What&rsquo;s in the box</p><h2 id="kb-h">The starter kit' + (sp ? ' <span class="kb-price tnum">' + esc(sp) + "</span>" : "") + "</h2>" +
      '<ul class="kb-list">' + kitList.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" +
      '<p class="kb-act">' + (addBtn(S, "main big", "Add to basket") || '<a class="btn main big" href="#store">See the kit</a>') + '<a class="kb-more" href="#store">Check out the shop</a></p></div></div></section>' +
      // HOW IT WORKS: four pictures, one line each
      '<section class="plan" aria-labelledby="pl-h"><div class="wrap"><h2 id="pl-h">How it works.</h2><ol class="steps4">' +
      '<li><span class="s-n" aria-hidden="true">1</span>' + img(PIC.booklet, "The CURVE 35 build guide on top of the box", ' width="640" height="414"') + '<h3><a href="#start">Open the box</a></h3><p>The pieces and a guide, nothing else.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">2</span>' + img(PIC.plan_build, "The orange front plate held above the black body, with an arrow showing it sliding down into place", ' width="1200" height="900"') + '<h3><a href="#build">Build it</a></h3><p>Each part clicks in. No tools.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">3</span>' + img(PIC.plan_shoot, "The camera seen from behind, aimed at a person waving next to a tree in the sun, with the edges of the picture marked", ' width="1200" height="900"') + '<h3><a href="#build-p1">Shoot a roll</a></h3><p>Take it outside on real film.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">4</span>' + img(PIC.plan_learn, "A lesson diagram: light from the top and the foot of a tree crosses in a small hole and lands upside down on the film", ' width="1200" height="900"') + '<h3><a href="#lessons">Learn how it works</a></h3><p>One short lesson per piece.</p></li></ol></div></section>' +
      // THE CAMERA VIEWER
      explodeSection() +
      // FOUR FACTS: each one said nowhere else on this page (canon/facts.yaml).  The same four cards and the same words on every screen (v13)
      '<section class="guide" aria-labelledby="gd-h"><div class="wrap"><h2 id="gd-h">Small camera, big numbers.</h2>' +
      '<dl class="bns"><div class="bn-y"><dt>' + esc(factSay("shutter_speed", "1/322 s")) + '</dt><dd><span class="bn-l">how long the shutter stays open</span><span class="bn-s">shutter</span></dd></div>' +
      '<div class="bn-b"><dt class="bn-sm">' + dots.map(esc).join(" &middot; ") + '</dt><dd><span class="bn-l">three dots on one wheel set how much light gets in</span><span class="bn-s">three dots for the light</span></dd></div>' +
      '<div class="bn-g"><dt>' + esc(factSay("light_rays", "69 million")) + '</dt><dd><span class="bn-l">light rays traced at the closed camera. None got in.</span><span class="bn-s">light rays tried. None got in.</span></dd></div>' +
      '<div class="bn-o"><dt>' + esc(factSay("print_hours", "9.4 hours")) + '</dt><dd><span class="bn-l">to print every part on your own 3D printer</span><span class="bn-s">to print your own</span></dd></div></dl></div></section>' +
      // LESSONS: a carousel of colourful tiles
      '<section class="learn" aria-labelledby="ln-h"><div class="wrap"><div class="learn-head"><h2 id="ln-h">Nine lessons. Nine questions.</h2>' +
      '<a class="btn" href="#lessons">All lessons</a></div>' + lessonCarousel() + "</div></section>" +
      // PROGRAMS, OPEN FILES, BUILDS: one line
      '<nav class="strip1" aria-label="More"><div class="wrap"><p><a href="#programs">Programs for classes</a><a href="#open-files">Open files</a><a href="#builds">Builds and remixes</a><a href="#teachers">For teachers</a></p></div></nav>' +
      // LAST CALL
      '<section class="final" aria-labelledby="fn-h"><div class="wrap final-in"><div><h2 id="fn-h">Build a camera this week.</h2><p class="final-win">Or print it free.</p></div>' +
      '<div class="final-act"><a class="btn ink big" href="#store">Buy the kit</a><a class="btn big alt" href="#files">Print your own</a></div></div></section></div>';
  };
  pages.home.title = "";
  pages.home.after = function () { mountHero(); mountCarousel(); mountExplode(); addButtons(); };
  pages.home.wide = true;

  // ---- the lessons (v10): both shelves on one page, with a filter by topic; each card: its diagram, the topic, the question, the time and what you do.
  //      Then the final roll: a 24-frame shot list that uses everything, and a self-check to grade it.
  var TEACH_KEY = "curve-lesson-teach";      // the same key as js/lesson.js: teacher mode, remembered in this browser
  function teacherMode(v) { try { if (v === undefined) return localStorage.getItem(TEACH_KEY) === "1"; localStorage.setItem(TEACH_KEY, v ? "1" : "0"); } catch (e) { return false; } return v; }
  var TOPICS = [["light", "Light"], ["mechanism", "Mechanism"], ["pictures", "Taking pictures"], ["making", "Making"]];
  var TOPIC_NAME = {}; TOPICS.forEach(function (t) { TOPIC_NAME[t[0]] = t[1]; });
  function lessonCard(L) {      // v11: a colourful tile, as on home: number and topic, title, the hook question, the diagram on white
    var F = figSvg(L.fig), S = seen(), R = L.render;
    var time = (L.minutes ? L.minutes + " min lesson" : "") + (L.duration_s ? (L.minutes ? " &middot; " : "") + minutes(L.duration_s) : "");
    return '<li data-topic="' + esc(L.topic || "") + '"><article class="lc" style="' + cvars(lcol(L)) + '">' +
      '<p class="lc-top"><span class="lc-n" aria-hidden="true">' + esc(L.num) + '</span><span class="lc-k">' + esc(TOPIC_NAME[L.topic] || "") + "</span>" + (S[L.id] ? '<span class="lc-seen">opened</span>' : "") + "</p>" +
      '<h3><a href="#' + L.route + '"><span class="sr-only">' + lessonName(L) + ": </span>" + esc(L.title) + "</a></h3>" +
      '<p class="lc-q">' + esc(L.question) + "</p>" +
      (F || R ? '<span class="lc-fig" aria-hidden="true">' + (F || img(R.src, "", ' width="900" height="675"')) + "</span>" : "") +
      (time ? '<p class="lc-time">' + time + "</p>" : "") +
      '<p class="lc-teach"><a href="#' + L.route + '-teach">Plan<span class="sr-only">, ' + lessonName(L) + '</span></a><a href="#' + L.route + '-slides">Slides<span class="sr-only">, ' + lessonName(L) + "</span></a></p>" +
      "</article></li>";
  }
  // the final roll: 24 frames, each tied to the lesson that explains it (counts and dots for ISO 400 film, course/FACTS.md)
  var FINAL_ROLL = [
    ["1", 3, "The slate", "Your name, the date and the film on paper, held up in sun about 1.5 m away. Small dot."],
    ["2", 1, "Pinhole, sun", "Before the lens goes in: camera on a wall, large dot, middle click, “open, shut”."],
    ["3", 1, "Pinhole, shade", "Same kind of still scene, out of the sun: count 3."],
    ["4", 1, "Pinhole, indoors", "By a bright window, camera on a table: count 40. Then press the lens in."],
    ["5", 2, "Lens, same scene", "Frame 2's scene again, one press, small dot. Compare the two."],
    ["6", 2, "Near", "Something about 1 m away, small dot."],
    ["7–9", 4, "Three dots", "One scene in hazy sun: small, middle, large."],
    ["10", 5, "Freeze", "A friend jumping, in sun, small dot, about 2.5 m away."],
    ["11", 5, "Crossing", "A bike or a runner going past. Press smoothly."],
    ["12–14", 6, "A sequence", "A friend walking toward you: press, wind until the arrow comes home, press."],
    ["15", 8, "Head to toe", "One person, whole, from about 2.3 m."],
    ["16", 8, "Side light", "A face with the sun falling across it."],
    ["17", 8, "Off-centre", "Your subject just inside an outer line of the sight."],
    ["18", 4, "Cloud", "A bright cloudy scene, large dot."],
    ["19", 9, "Lamps on", "Indoors, camera on a table, small dot: count 5."],
    ["20", 9, "Dim room", "Same, darker: count 20."],
    ["21", 9, "Film against phone", "One scene on film and on your phone. Note the phone's settings."],
    ["22", 8, "Your street", "Where you live, framed the way you'd show a visitor."],
    ["23", 0, "Your best idea", "The picture you would hang on a wall. Use everything above."],
    ["24", 0, "You", "Hand the camera to a friend: you, holding the camera you built."]
  ];
  function finalRoll() {
    return '<section class="froll" id="final-roll" tabindex="-1" aria-labelledby="fr-h"><div class="wrap"><h2 id="fr-h">The final roll</h2>' +
      '<p class="lead">24 frames that use every lesson. Shoot them, get the roll developed, then grade your own scans.</p>' +
      '<p class="fr-load"><strong>Before frame 1:</strong> load the film in shade or indoors, with your back to the window (lesson 7). After frame 24, wind it back into its shell before the back comes off.</p>' +
      '<ol class="fr-list" role="list">' + FINAL_ROLL.map(function (f) {
        var L = f[1] ? LESSONS[f[1] - 1] : null;
        return '<li><span class="fr-n">' + esc(f[0]) + '</span><span class="fr-t"><strong>' + esc(f[2]) + "</strong>" + esc(f[3]) + "</span>" +
          (L ? '<a class="fr-l" href="#' + L.route + '" style="' + cvars(lcol(L)) + '"><span class="sr-only">' + lessonName(L) + ": </span>" + esc(L.title) + "</a>" : '<span class="fr-l fr-all">All</span>') + "</li>";
      }).join("") + "</ol>" +
      '<div class="fr-grade"><h3>Grade it yourself</h3><p>Pick six frames. Score each one 0, 1 or 2 on the first three questions, and answer the fourth in one sentence. Out of 36, plus six sentences.</p>' +
      '<table class="fr-rub"><thead><tr><th scope="col">Question</th><th scope="col">0</th><th scope="col">1</th><th scope="col">2</th></tr></thead><tbody>' +
      "<tr><th scope=\"row\">Sharp where it should be?</th><td>Blurred all over</td><td>Soft, or shaken</td><td>Sharp in the middle</td></tr>" +
      "<tr><th scope=\"row\">Exposed right?</th><td>Nearly blank or nearly black</td><td>Too pale or too dark, but readable</td><td>Detail in the bright and the dark</td></tr>" +
      "<tr><th scope=\"row\">Framed as you aimed?</th><td>Subject cut off or missing</td><td>In, but off where you meant</td><td>Where you aimed it</td></tr>" +
      '<tr><th scope="row">What would you change?</th><td colspan="3">One sentence: the dot, the count, where you stood, the light, or the moment.</td></tr></tbody></table>' +
      '<p class="fr-note">For a class, the sentence matters most: a weak frame with a clear reason scores better than a lucky one with none. For yourself: shoot the frames you scored lowest again.</p></div></div></section>';
  }
  pages.lessons = function () {
    var all = LESSONS.concat(MAKERS), on = teacherMode();
    return '<div class="lessons-page' + (on ? " is-teacher" : "") + '"><section class="les-plate" aria-labelledby="ls-h1"><div class="wrap"><div class="pagehead"><h1 id="ls-h1">Lessons</h1>' +
      '<p class="lead">Nine lessons on how your camera works, four for makers, then a final roll to shoot. Free.</p></div>' +
      '<div class="lf-bar"><div class="lf" role="group" aria-label="Show lessons about"><button type="button" data-topic="" aria-pressed="true">All <span>' + all.length + "</span></button>" +
      TOPICS.map(function (t) { var n = all.filter(function (L) { return L.topic === t[0]; }).length; return '<button type="button" data-topic="' + t[0] + '" aria-pressed="false">' + esc(t[1]) + " <span>" + n + "</span></button>"; }).join("") + "</div>" +
      '<button type="button" class="tswitch" role="switch" aria-checked="' + on + '"><span class="sw" aria-hidden="true"><i></i></span>Teacher mode</button></div></div></section>' +
      '<div class="wrap"><p class="sr-only" id="lf-say" aria-live="polite"></p>' +
      '<h2 class="lg-h" id="lg-main">How a camera works</h2><ol class="lcards" role="list" aria-labelledby="lg-main">' + LESSONS.map(lessonCard).join("") + "</ol>" +
      '<h2 class="lg-h" id="lg-make">For makers</h2><ol class="lcards lc-make" role="list" aria-labelledby="lg-make">' + MAKERS.map(lessonCard).join("") + "</ol></div>" + finalRoll() + "</div>";
  };
  pages.lessons.title = "Lessons";
  pages.lessons.wide = true;
  pages.lessons.after = function () {
    var page = $(".lessons-page"); if (!page) return;
    $$(".lf button").forEach(function (b) {
      b.addEventListener("click", function () {
        var t = b.dataset.topic, n = 0;
        $$(".lf button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        $$(".lcards > li").forEach(function (li) { var show = !t || li.dataset.topic === t; li.hidden = !show; if (show) n++; });
        $$(".lcards").forEach(function (ol) { var any = $$("li", ol).some(function (li) { return !li.hidden; }); ol.hidden = !any; ol.previousElementSibling.hidden = !any; });
        $("#lf-say").textContent = n + (n === 1 ? " lesson" : " lessons") + (t ? " about " + TOPIC_NAME[t].toLowerCase() : "");
      });
    });
    var sw = $(".tswitch");
    if (sw) sw.addEventListener("click", function () { var v = sw.getAttribute("aria-checked") !== "true"; teacherMode(v); sw.setAttribute("aria-checked", String(v)); page.classList.toggle("is-teacher", v); announce(v ? "Teacher mode on: plans and slides are shown." : "Teacher mode off."); });
  };

  // ---- a lesson
  function chapBar(L) {
    var list = L.shelfList;
    return '<nav class="chapbar" aria-label="' + (L.shelf === "maker" ? "Maker lessons" : "Lessons") + '"><div class="chapbar-in"><div class="cb-row"><a class="cb-now" href="' + (L.shelf === "maker" ? "#files" : "#lessons") + '">' + (L.shelf === "maker" ? "Made by a printer" : "How a camera works") + '</a><ol class="cb-strip">' +
      list.map(function (x) { return '<li><a href="#' + x.route + '"' + (x === L ? ' aria-current="page"' : "") + ' style="' + cvars(lcol(x)) + '" title="' + esc(x.title) + '"><span class="sr-only">' + lessonName(x) + ": " + esc(x.title) + '</span><span aria-hidden="true">' + esc(x.num) + "</span></a></li>"; }).join("") +
      "</ol></div></div></nav>";
  }
  function lessonFoot(L) {
    var list = L.shelfList, prev = list[L.i - 1], next = list[L.i + 1];
    if (L.shelf === "main" && L.rich) next = null;      // the lesson page ends with its own "next"
    var Sk = PROD["starter-kit"];
    var X = GR.lessons[L.id], conn = X ? '<aside class="lconn" aria-labelledby="lc-h-' + L.id + '"><h2 id="lc-h-' + L.id + '">This lesson, linked</h2><dl class="xdl">' +
      xrow("Build steps", "step", X.steps) + xrow("Parts", "part", X.parts) + xrow("Numbers", "fact", X.facts) + xrow("Words", "term", X.terms) + "</dl></aside>" : "";
    return '<div class="lesson-foot">' + conn + '<aside class="kitline" aria-label="The parts in this lesson"><p>In your camera</p>' + partsRow(LESSON_PARTS[L.id] || [], true) +
      '<p class="kit-loop">Every part here comes in the kit. <a class="btn small main" href="#store">Buy the kit' + (Sk ? " " + money(Sk.price_usd) : "") + '</a><a class="btn small" href="#files">Print your own</a></p></aside>' +
      '<nav class="pager" aria-label="Other lessons">' + (prev ? '<a href="#' + prev.route + '"><span>' + lessonName(prev) + "</span><strong>" + esc(prev.title) + "</strong></a>" : '<a href="' + (L.shelf === "maker" ? "#files" : "#lessons") + '"><span>Back to</span><strong>All lessons</strong></a>') +
      (next ? '<a class="next" href="#' + next.route + '"><span>' + lessonName(next) + "</span><strong>" + esc(next.title) + "</strong></a>" : (L.shelf === "main" && !list[L.i + 1] ? '<a class="next" href="#files" data-makers><span>For makers</span><strong>Made by a printer</strong></a>' : "")) + "</nav></div>";
  }
  function lessonPage(L) {   // when the renderer is not there: the question, the film, the words of the film
    var film = L.film ? '<figure class="film"><video id="lfilm" controls preload="metadata" playsinline' + (L.poster ? ' poster="' + esc(L.poster) + '"' : "") + '><source src="' + esc(L.film) + '" type="video/mp4">' +
      (L.captions ? '<track kind="captions" srclang="en" label="English" src="' + vttUrl(L) + '" default>' : "") + "</video><figcaption>The film" + (L.duration_s ? ", " + mmss(L.duration_s) : "") + ".</figcaption></figure>" : "";
    var lines = (L.transcript || []).filter(function (x) { return x && x.text; }), chs = L.chapters || [];
    var body = chs.map(function (ch, ci) {
      var t0 = Number(ch.t) || 0, t1 = ci + 1 < chs.length ? Number(chs[ci + 1].t) : 1e9;
      var mine = lines.filter(function (x) { return Number(x.t) >= t0 - 0.5 && Number(x.t) < t1 - 0.5; }).map(function (x) { return esc(x.text); });
      return "<section><h2>" + esc(ch.title) + "</h2><p>" + mine.join(" ") + "</p></section>";
    }).join("");
    var R = L.render;
    return '<header class="lhead"><div class="wrap"><p class="kicker">' + lessonName(L) + " &middot; " + esc(L.title) + "</p><h1>" + esc(L.question) + "</h1></div></header>" +
      '<article class="page lesson">' + film + (L.hook ? '<p class="lead">' + esc(L.hook) + "</p>" : "") + (R ? '<figure>' + img(R.src, R.alt, ' width="900" height="675"') + "<figcaption>" + esc(R.cap) + "</figcaption></figure>" : "") + body + "</article>";
  }
  function intoStrip(a) {   // keep a link of a sideways-scrolling strip in sight, without moving the page
    var ol = a.closest("ol"); if (!ol || ol.scrollWidth <= ol.clientWidth) return;
    var r = a.getBoundingClientRect(), pr = ol.getBoundingClientRect();
    if (r.left < pr.left || r.right > pr.right) ol.scrollLeft += r.left - pr.left - 24;
  }
  function lessonShell(L) {
    return chapBar(L) + '<div class="rich-lesson" id="rich-lesson" data-lesson="' + esc(L.id) + '"></div>' + lessonFoot(L);
  }
  function lessonAfter(L, section, teach) {
    var el = document.getElementById("rich-lesson");
    var cur = $(".cb-strip [aria-current]"); if (cur) intoStrip(cur);
    function fallback() { if (current !== L.route && current !== "teach-" + L.num) return; el.innerHTML = lessonPage(L); }
    if (!(L.rich && window.CURVE && typeof window.CURVE.renderLesson === "function")) { fallback(); return; }
    var ctx = { id: L.id, shelf: L.shelf, media: L, data: "data/lessons/" + L.id + ".json", lessons: LESSONS, makers: "#makers", parts: LESSON_PARTS[L.id] || [],
                reducedMotion: reduced(), section: (teach ? "teach" : section) || undefined, teach: !!teach, go: function (hash) { location.hash = hash; } };
    var busy = false, tmr = 0;
    function words() { busy = true; try { glossarize(el); } catch (e) { /* the words stay plain */ } busy = false; }
    var mo = window.MutationObserver ? new MutationObserver(function () { if (busy) return; clearTimeout(tmr); tmr = setTimeout(words, 150); }) : null;
    if (mo) { mo.observe(el, { childList: true, subtree: true }); cleanup.push(function () { mo.disconnect(); clearTimeout(tmr); }); }
    try {
      var h = window.CURVE.renderLesson(L.n, el, ctx);      // 1 ... 9, or "m1" ... "m4" with ctx.data naming the file
      var kill = function (x) { if (x && typeof x.destroy === "function") cleanup.push(function () { x.destroy(); }); words(); };
      if (h && typeof h.then === "function") h.then(kill, fallback); else kill(h);
    } catch (e) { fallback(); }
  }

  // ---- start here: just opened the box.  An orange plate, what should be in the bag, then three big steps with tick boxes (kept in this browser)
  var START_KEY = "curve35-start";
  pages.start = function () {
    var done = store(START_KEY) || {}, L1 = LESSONS[0];
    var steps = [
      { id: "build", n: 1, tone: "sun", title: "Build it", time: "One afternoon", pic: PIC.b3c, alt: "The front plate sliding down onto the camera until it clicks",
        text: "10 steps. Each has a short film and a check. Looks like the picture? Go on.", links: [["#build-b1", "Start at BUILD 1"], ["#parts", "Meet the parts"]] },
      { id: "roll", n: 2, tone: "tang", title: "Shoot your first roll", time: "24 pictures", pic: PIC.s3, alt: "A finger pressing the shutter rocker on top of the camera",
        text: "Load the film in the shade. Then for every picture: pick a dot, aim, press, wind.", links: [["#build-f1", "Load the film"], ["#build-p1", "Which dot?"]] },
      { id: "lesson1", n: 3, tone: "sky", title: "Open lesson 1", time: L1 && L1.duration_s ? minutes(L1.duration_s) : "", pic: PIC.h_hero, alt: "The camera with the pinhole disc and ring in the lens pocket",
        text: "How can a hole make a picture? Then try the pinhole experiment: lens out, disc and ring in.", links: [["#lesson-1", "Lesson 1"], ["#build-h1", "The pinhole experiment"]] }
    ];
    var k = steps.filter(function (s) { return done[s.id]; }).length;
    var inv = PARTS.map(function (p) { return '<li><span class="inv-pic">' + img(partImg(p.key), "", ' width="520" height="390"') + '</span><span class="inv-n">1&times;</span><span class="inv-name">' + esc(p.name) + "</span></li>"; }).join("") +
      '<li><span class="inv-pic">' + img("media/img/part_blade.webp", "", ' width="520" height="390"') + '</span><span class="inv-n">2&times;</span><span class="inv-name">Spares: shutter, wind knob</span></li>' +
      '<li><span class="inv-pic">' + img("media/img/part_pinring.webp", "", ' width="520" height="390"') + '</span><span class="inv-n">1&times;</span><span class="inv-name">Pinhole ring and disc</span></li>' +
      '<li><span class="inv-pic">' + img(PIC.booklet, "", ' width="520" height="390"') + '</span><span class="inv-n">1&times;</span><span class="inv-name">Build guide</span></li>';
    return '<div class="start">' +
      '<section class="start-plate" aria-labelledby="st-h1"><div class="wrap"><div class="pagehead">' +
      '<h1 id="st-h1">You opened the box. <span class="hl hl-w">Nice.</span></h1><p class="lead">Three things, in this order. Tick them off as you go.</p>' +
      '<p class="meter"><span class="meter-bar" aria-hidden="true"><i id="start-bar" style="width:' + Math.round(k / 3 * 100) + '%"></i></span><span id="start-count">' + k + " of 3 done</span></p></div></div></section>" +
      '<div class="wrap"><section class="inbox" aria-labelledby="ib-h"><h2 id="ib-h">First, check the bag</h2><p>Lay everything out. The starter kit also has a roll of film and a developing code.</p><ul class="inv-grid">' + inv + "</ul></section>" +
      '<ol class="path">' + steps.map(function (s) {
        return '<li class="path-step t-' + s.tone + (done[s.id] ? " done" : "") + '" id="go-' + s.id + '"><span class="big-n" aria-hidden="true">' + s.n + '</span><div class="path-text"><h2>' + esc(s.title) + "</h2>" + (s.time ? '<p class="path-time">' + esc(s.time) + "</p>" : "") + "<p>" + esc(s.text) + "</p>" +
          '<p class="path-links">' + s.links.map(function (l, i) { return '<a class="btn' + (i ? " small" : " main small") + '" href="' + l[0] + '">' + esc(l[1]) + "</a>"; }).join("") + "</p>" +
          '<label class="tick"><input type="checkbox" data-done="' + s.id + '"' + (done[s.id] ? " checked" : "") + "> Done<span class=\"sr-only\">: " + esc(s.title) + "</span></label></div>" +
          '<div class="path-pic">' + img(s.pic, s.alt, ' width="900" height="675"') + "</div></li>";
      }).join("") + "</ol>" +
      '<div class="duo"><section class="duo-card t-pink" aria-labelledby="st-h"><h2 id="st-h">Stuck?</h2><p>Type what you see: "knob won\'t turn", "back won\'t close".</p><a class="btn small" href="#help">Help</a></section>' +
      '<section class="duo-card t-mint" aria-labelledby="dn-h"><h2 id="dn-h">Done all three?</h2><p>Show everyone your camera. Or change the files and post a remix.</p><a class="btn small" href="#builds">Share your build</a></section></div></div></div>';
  };
  pages.start.title = "Start here";
  pages.start.wide = true;
  pages.start.after = function () {
    $$("[data-done]").forEach(function (b) {
      b.addEventListener("change", function () {
        var d = store(START_KEY) || {}; d[b.dataset.done] = b.checked; store(START_KEY, d);
        b.closest(".path-step").classList.toggle("done", b.checked);
        var k = ["build", "roll", "lesson1"].filter(function (x) { return d[x]; }).length;
        $("#start-count").textContent = k + " of 3 done"; $("#start-bar").style.width = Math.round(k / 3 * 100) + "%";
        announce(k + " of 3 done.");
      });
    });
  };

  // ---- the parts: collectable cards, one per piece, two bonus cards, then where to get a new one
  pages.parts = function () {
    return '<div class="wrap parts-page"><div class="pagehead"><h1>Meet the parts.</h1>' +
      '<p class="lead">Eight printed, one lens. <a href="#parts-table" data-go="ptable">See them all in one table</a>.</p></div>' +
      '<ol class="pts full" role="list">' + PARTS.map(function (p, i) { return partCard(p, true, i + 1, PARTS.length); }).join("") + BONUS.map(function (p) { return partCard(p, true, 0); }).join("") + "</ol>" +
      moreParts() + partsTable() + '<div class="parts-after">' +
      '<div class="duo"><section class="duo-card t-sun" aria-labelledby="lo-h"><h2 id="lo-h">Lost one? Broke one?</h2><p>Get a spares pack, or print a new one from the files.</p><p class="path-links"><a class="btn main small" href="#spares">Spares and extras</a><a class="btn small" href="#files">The files</a></p></section>' +
      '<section class="duo-card t-tang" aria-labelledby="co-h"><h2 id="co-h">Want new colours?</h2><p>The colour pack swaps the front plate and both knobs. Or print your own.</p><p class="path-links"><a class="btn main small" href="#spares">Colour pack</a><a class="btn small" href="#builds">Remix ideas</a></p></section></div></div></div>';
  };
  pages.parts.title = "The parts";
  pages.parts.after = function () { wireSort(view); };
  pages.parts.wide = true;

  // ---- the build guide, with its own bar
  function whichDot() {
    var W = C.which_dot; if (!W) return "";
    var size = ["small", "middle", "large"];
    function dots(on) { return '<span class="dots" aria-hidden="true">' + [7, 10, 12].map(function (d, i) { return '<i class="' + (size[i] === on ? "on" : "") + '" style="width:' + d + "px;height:" + d + 'px"></i>'; }).join("") + "</span>"; }
    return '<div class="tablewrap whichdot"><table><caption>Which dot, for ISO ' + esc(W.iso) + " film</caption><thead><tr><th scope=\"col\">The light</th><th scope=\"col\">The dot</th></tr></thead><tbody>" +
      W.rows.map(function (r) { var on = (r[1].match(/^(small|middle|large) dot$/) || [])[1]; return "<tr><td>" + esc(r[0]) + "</td><td>" + (on ? dots(on) : "") + esc(r[1]) + "</td></tr>"; }).join("") + "</tbody></table></div>";
  }
  // ---- the build guide (v2.16): one step at a time.  The camera in 3D as it stands after the step (the new part glows and flies in), the words,
  //      "you know it's right when", the common mistake and its fix, the parts, the lesson, the step's film and narration, its short link and QR code.
  //      A rail of tick boxes (kept in this browser), arrow keys for the next and the last step, the whole film with a chapter per step,
  //      and which steps need which part.  Everything from the canon (C.graph) and, when it is there, the narrated video (C.video).
  var BUILD_AT = null, BUILDER = null;
  var DONE_KEY = "curve35-build-done";
  function doneMap() { var d = store(DONE_KEY); return d && typeof d === "object" ? d : {}; }
  function firstUndone() { var d = doneMap(); for (var i = 0; i < GR.steps.length; i++) if (!d[GR.steps[i].id]) return GR.steps[i].id; return GR.steps.length ? GR.steps[0].id : null; }
  function vsec(id) { return VID && VID.sections && VID.sections[id] || null; }
  var BLOB = {}; function vttBlob(key, text) { if (!text) return ""; if (!BLOB[key]) { try { BLOB[key] = URL.createObjectURL(new Blob([text], { type: "text/vtt" })); } catch (e) { BLOB[key] = ""; } } return BLOB[key]; }
  function stepCount(s) { return GR.steps.filter(function (x) { return x.sec === s.sec; }).length; }
  function qrSvg(q, label) { return q ? '<svg class="qr" viewBox="0 0 ' + q.n + " " + q.n + '" role="img" aria-label="' + esc(label) + '" shape-rendering="crispEdges"><rect width="' + q.n + '" height="' + q.n + '" fill="#fff"/><path d="' + q.d + '" fill="#17140F"/></svg>' : ""; }
  function railHTML() {
    var d = doneMap(), n = GR.steps.filter(function (s) { return d[s.id]; }).length;
    var secs = G.sections.filter(function (sec) { return sec.steps.length; });
    return '<nav class="rail" aria-label="Steps of the build guide"><div class="rail-top"><p class="rail-n" id="rail-n" aria-live="polite">' + n + " of " + GR.steps.length + " steps done</p>" +
      '<p class="rail-keys">Arrow keys: last and next step</p></div><div class="rail-secs">' + secs.map(function (sec) {
        return '<div class="rail-sec sec-' + sec.letter + '"><p class="rail-h">' + esc(SECNAME[sec.key] || sec.key) + '</p><ol class="rail-steps">' + sec.steps.map(function (c) {
          var s = GS[c]; if (!s) return "";
          return '<li data-step="' + c + '"><a href="#build-' + c + '" aria-label="' + esc((SECNAME[s.sec] || s.sec) + " " + s.n + ": " + s.title) + '">' + s.n + '</a><input type="checkbox" id="rd-' + c + '" data-done="' + c + '"' + (d[c] ? " checked" : "") + '><label for="rd-' + c + '"><span class="sr-only">Done: ' + esc((SECNAME[s.sec] || s.sec) + " " + s.n) + "</span></label></li>";
        }).join("") + "</ol></div>";
      }).join("") + "</div></nav>";
  }
  function stepText(s) {
    var L = s.lesson && GR.lessons[s.lesson], G0 = STEP[s.id] || {}, V = vsec(s.id), d = doneMap();
    var i = s.i, prev = GR.steps[i - 1], next = GR.steps[i + 1];
    var parts = s.parts.length ? '<ul class="st-parts" aria-label="Parts used">' + s.parts.map(function (p) {
      var P0 = GP[p.id]; if (!P0) return "";
      return '<li><a href="#part-' + P0.key + '">' + img(partImg(P0.key), "", ' width="40" height="30"') + "<span>" + (p.n > 1 ? p.n + " &times; " : "") + esc(P0.name) + "</span></a></li>"; }).join("") + "</ul>" : '<p class="st-none">No new parts: this step moves what is already there.</p>';
    var clip = (V && V.clip) || s.clip;
    var film = clip ? '<figure class="st-film"><video controls preload="none" playsinline width="640" height="480"' + (s.img ? ' poster="' + esc(s.img) + '"' : "") + ' aria-label="Film of ' + esc(s.title) + '"><source src="' + esc(clip) + '" type="video/mp4">' +
      (V && V.vtt ? '<track kind="captions" srclang="en" label="English" src="' + vttBlob("s-" + s.id, V.vtt) + '" default>' : "") + "</video></figure>" : "";
    var chap = VID && VID.src && V && V.start != null ? '<button type="button" class="btn small" data-seek="' + V.start + '">Watch it in the whole film</button>' :
      (!VID && G.film && (G.film.chapters || []).some(function (c) { return c.code === s.id; }) ? '<button type="button" class="btn small" data-seek="' + G.film.chapters.filter(function (c) { return c.code === s.id; })[0].t + '">Watch it in the whole film</button>' : "");
    var narr = s.narration ? '<details class="st-narr"' + (V && V.audio ? " open" : "") + "><summary>Narration</summary>" + (V && V.audio ? '<audio controls preload="none" src="' + esc(V.audio) + '" aria-label="Narration of ' + esc(s.title) + '"></audio>' : "") + "<p>" + esc(s.narration) + "</p></details>" : "";
    var vlinks = V && V.links && V.links.length ? '<p class="st-vlinks">' + V.links.filter(function (h) { return /^#[a-z0-9-]+$/.test(h); }).map(function (h) { return '<a href="' + h + '">' + esc(h.slice(1).replace(/-/g, " ")) + "</a>"; }).join(" ") + "</p>" : "";
    var short = s.url ? s.url.replace(/^https:\/\//, "") : "";
    return '<div class="st-text">' +
      '<p class="st-eye"><span class="tag">' + esc(SECBAR[s.sec] || s.sec) + "</span> Step " + s.n + " of " + stepCount(s) + "</p>" +
      '<h2 id="st-h" tabindex="-1">' + esc(s.title) + "</h2>" +
      '<p class="st-do">' + esc(s.do) + "</p>" +
      '<div class="st-ok"><p class="st-lab">You know it\'s right when&hellip;</p><p>' + esc(s.check) + "</p></div>" +
      (s.fix ? '<div class="st-mis"><p class="st-lab">' + (s.mistake ? "Common mistake" : "Tip") + "</p>" + (s.mistake ? "<p><strong>" + esc(s.mistake) + "</strong></p>" : "") + "<p>" + (s.mistake ? '<span class="st-fix">Fix:</span> ' : "") + esc(s.fix) + "</p></div>" : "") +
      (s.id === "p1" ? whichDot() : "") +
      '<h3 class="st-sub">Parts</h3>' + parts +
      (L ? '<p class="st-les"><span class="st-lab">The lesson behind it</span><a href="#' + L.route + '">' + esc((L.shelf === "maker" ? "Maker lesson " : "Lesson ") + L.num + ": " + L.title) + "</a></p>" : "") +
      (s.terms.length ? '<p class="st-words"><span class="st-lab">Words</span>' + xchips("term", s.terms, "Words in this step") + "</p>" : "") +
      (s.why ? '<details class="st-why"><summary>Why it is this shape</summary><p>' + esc(s.why) + "</p></details>" : "") +
      '<p class="st-done"><input type="checkbox" id="sd-' + s.id + '" data-done="' + s.id + '"' + (d[s.id] ? " checked" : "") + '><label for="sd-' + s.id + '">I have done this step</label></p>' +
      '<nav class="st-pn" aria-label="Last and next step">' + (prev ? '<a class="btn" href="#build-' + prev.id + '" rel="prev"><span aria-hidden="true">&larr;</span> ' + esc((SECBAR[prev.sec] || prev.sec) + " " + prev.n) + "</a>" : "<span></span>") +
      (next ? '<a class="btn main" href="#build-' + next.id + '" rel="next">' + esc((SECBAR[next.sec] || next.sec) + " " + next.n) + ' <span aria-hidden="true">&rarr;</span></a>' : '<a class="btn main" href="#lessons">On to the lessons</a>') + "</nav></div>" +
      '<div class="st-media">' + film + '<div class="st-media-row">' + chap + "</div>" + narr + vlinks +
      (s.qr ? '<div class="st-short">' + qrSvg(s.qr, "QR code for " + short) + '<p><span class="st-lab">Short link</span><a href="#build-' + s.id + '">' + esc(short) + "</a><span class=\"note\">Scan it from the printed guide to land here.</span></p></div>" : "") + "</div>";
  }
  function newLine(s) {
    var m = s.model || {}, nw = (m.new || []).map(function (k) { return GP[k] ? GP[k].name : k; });
    return nw.length ? "Glowing: " + nw.join(", ") + ". Faint: not in yet." : "Nothing new: the camera as it stands after this step.";
  }
  function stepPanel(id) {
    var s = GS[id] || GR.steps[0]; if (!s) return "";
    return '<section class="stepper" id="stepper" aria-labelledby="st-h"><div class="st-stage-col"><div class="st3" id="st3">' + img(s.img, (s.title || "") + ": " + (s.do || ""), ' class="st3-still" width="960" height="720"').replace(' class="r"', "") + "</div>" +
      '<div class="st3-bar"><button type="button" class="x3-turn" data-turn3="-40" aria-label="Turn the camera left"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></button><p class="st3-cap" id="st3-cap">' + esc(newLine(s)) + '</p><button type="button" class="x3-turn" data-turn3="40" aria-label="Turn the camera right"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></button></div></div>' +
      '<div class="st-body" id="st-body">' + stepText(s) + "</div></section>";
  }
  function theatre() {       // "Watch the build": the narrated video when site/data/video.json is there, else the assembly film; a chapter per step
    var src, dur, poster, chs = [], vtt = "";
    if (VID && VID.src) {
      src = VID.src; dur = VID.dur; poster = VID.poster || (G.film && G.film.poster);
      chs = Object.keys(VID.sections).map(function (k) { var x = VID.sections[k]; return { t: x.start, title: x.title, code: GS[k] ? k : null }; }).filter(function (c) { return c.t != null; }).sort(function (a, b) { return a.t - b.t; });
      vtt = VID.vtt ? vttBlob("full", VID.vtt) : "";
    } else if (G.film) { src = G.film.src; dur = G.film.dur; poster = G.film.poster; chs = (G.film.chapters || []).map(function (c) { return { t: c.t, title: GS[c.code] ? (SECNAME[GS[c.code].sec] || "") + " " + GS[c.code].n + ": " + GS[c.code].title : c.title, code: c.code }; }); }
    if (!src) return "";
    return '<section class="theatre" id="step-film" tabindex="-1" aria-labelledby="th-h"><div class="wrap"><div class="th-head"><h2 id="th-h">Watch the build</h2><p>' + (VID && VID.src ? "The whole build, narrated" : "Every step end to end") + (dur ? ", " + mmss(dur) : "") + ". Pick a chapter to jump to its step.</p></div>" +
      '<div class="th-grid"><figure class="th-film"><video id="wholefilm" controls preload="none" playsinline' + (poster ? ' poster="' + esc(poster) + '"' : "") + '><source src="' + esc(src) + '" type="video/mp4">' + (vtt ? '<track kind="captions" srclang="en" label="English" src="' + vtt + '" default>' : "") + "</video></figure>" +
      (chs.length ? '<ol class="chap th-chap" aria-label="Chapters">' + chs.map(function (ch) { return '<li><button type="button" data-t="' + ch.t + '"' + (ch.code ? ' data-code="' + ch.code + '"' : "") + '><span class="tm">' + mmss(ch.t) + "</span>" + esc(ch.title) + "</button></li>"; }).join("") + "</ol>" : "") + "</div></div></section>";
  }
  function depMatrix() {      // which steps need which parts: a part is fitted (filled) or handled again (ring) at a step
    var parts = GR.parts.filter(function (p) { return p.steps.length; }), steps = GR.steps;
    var fitted = {}; steps.forEach(function (s) { s.parts.forEach(function (p) { fitted[p.id + "|" + s.id] = 1; }); });
    return '<section class="deps" id="deps" aria-labelledby="dp-h"><h2 id="dp-h">Which steps need which parts</h2><p class="lead">A filled dot: the part goes in at that step. A ring: the step uses it again.</p>' +
      '<div class="tablewrap deps-wrap" tabindex="0" role="region" aria-label="Parts and steps"><table class="deps-t"><thead><tr><th scope="col">Part</th>' + steps.map(function (s) {
        return '<th scope="col" class="dsec-' + s.sec.replace(/ /g, "").toLowerCase() + '"><a href="#build-' + s.id + '" aria-label="' + esc((SECNAME[s.sec] || s.sec) + " " + s.n + ": " + s.title) + '">' + esc(s.id) + "</a></th>"; }).join("") + "</tr></thead><tbody>" +
      parts.map(function (p) {
        return '<tr><th scope="row"><a href="#part-' + p.key + '"><span class="sw" style="background:' + esc(p.hex || "#ccc") + '" aria-hidden="true"></span>' + esc(p.name) + "</a></th>" + steps.map(function (s) {
          var f = fitted[p.id + "|" + s.id], u = p.steps.indexOf(s.id) >= 0;
          return "<td>" + (f ? '<span class="dot-f" aria-hidden="true"></span><span class="sr-only">goes in</span>' : u ? '<span class="dot-u" aria-hidden="true"></span><span class="sr-only">used</span>' : "") + "</td>";
        }).join("") + "</tr>";
      }).join("") + "</tbody></table></div></section>";
  }
  pages.build = function () {
    BUILD_AT = BUILD_AT && GS[BUILD_AT] ? BUILD_AT : firstUndone();
    var nums = (C.numbers || []).map(function (x) { return "<dt>" + esc(x.k) + "</dt><dd>" + esc(x.v) + "</dd>"; }).join("");
    var watch = (VID && VID.src) || G.film ? '<a class="btn" href="#build-film">Watch the build</a>' : "";
    return '<div class="wrap guide-page"><div class="pagehead"><h1>The build guide</h1>' +
      '<p class="lead">Ten steps to build, six to load film, four for every picture, two to take it out. One at a time.</p>' +
      '<p class="path-links">' + watch + '<a class="btn" href="#parts">Every part</a><a class="btn" href="#help">Help</a></p></div>' +
      railHTML() + stepPanel(BUILD_AT) +
      '<p class="kitbar">No pieces yet? <a href="#files">Print them free</a>, or <a href="#store">buy the kit</a> and skip the printing.</p></div>' +
      theatre() + '<div class="wrap guide-page">' + depMatrix() + guidesBlock(false) + '<h2>The camera in numbers</h2><dl class="facts">' + nums + '</dl><p><a href="#facts">Every number, and the check that proves it</a></p></div>';
  };
  pages.build.title = "The build guide";
  pages.build.wide = true;
  function buildGo(id, focus) {        // show one step without drawing the page again (the 3D view stays)
    var s = GS[id]; if (!s) return;
    BUILD_AT = id;
    var body = document.getElementById("st-body"); if (!body) return;
    body.innerHTML = stepText(s);
    var st = document.getElementById("st3"), still = st && $(".st3-still", st);
    if (still && s.img) { still.src = s.img; still.alt = s.title + ": " + s.do; }
    var cap = document.getElementById("st3-cap"); if (cap) cap.textContent = newLine(s);
    if (BUILDER) BUILDER.set(s.model);
    $$(".rail li[data-step]").forEach(function (li) { var a = $("a", li); if (li.getAttribute("data-step") === id) { a.setAttribute("aria-current", "step"); intoStrip(a); } else a.removeAttribute("aria-current"); });
    wireStep();
    var r = $(".related"); if (r) r.outerHTML = relatedBlock(relatedFor("build"));
    document.title = (SECNAME[s.sec] || s.sec) + " " + s.n + ": " + s.title + ": CURVE 35";
    if (focus) { var h = document.getElementById("st-h"), box = document.getElementById("stepper"); if (box) box.scrollIntoView({ behavior: "auto", block: "start" }); if (h) h.focus({ preventScroll: true }); announce((SECNAME[s.sec] || s.sec) + " step " + s.n + ": " + s.title); }
  }
  function setDone(id, v) {
    var d = doneMap(); if (v) d[id] = 1; else delete d[id]; store(DONE_KEY, d);
    $$('[data-done="' + id + '"]').forEach(function (b) { b.checked = !!v; });
    var n = GR.steps.filter(function (s) { return d[s.id]; }).length, el = document.getElementById("rail-n"); if (el) el.textContent = n + " of " + GR.steps.length + " steps done";
  }
  function wireStep() {
    $$("#st-body [data-done]").forEach(function (b) { b.addEventListener("change", function () { setDone(b.getAttribute("data-done"), b.checked); }); });
    $$("#st-body [data-seek]").forEach(function (b) { b.addEventListener("click", function () { var v = document.getElementById("wholefilm"); if (!v) return; var f = document.getElementById("step-film"); if (f) f.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" }); v.currentTime = Number(b.getAttribute("data-seek")); v.play().catch(function () {}); v.focus({ preventScroll: true }); }); });
  }
  pages.build.after = function () {
    wireDownloads();
    $$(".rail [data-done]").forEach(function (b) { b.addEventListener("change", function () { setDone(b.getAttribute("data-done"), b.checked); }); });
    var st = document.getElementById("st3");
    if (st && window.Camera3D && window.Camera3D.stepper && C.model3d) { BUILDER = window.Camera3D.stepper(st, C.model3d); cleanup.push(function () { if (BUILDER) BUILDER.destroy(); BUILDER = null; }); }
    $$("[data-turn3]").forEach(function (b) { b.addEventListener("click", function () { if (BUILDER) BUILDER.turn(Number(b.getAttribute("data-turn3"))); }); });
    buildGo(BUILD_AT, false);
    function onKey(e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || e.defaultPrevented) return;
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      var t = e.target; if (t && t.closest && t.closest("input,textarea,select,video,audio,[contenteditable],.tablewrap,.x3-range")) return;
      var s = GS[BUILD_AT]; if (!s) return;
      var o = GR.steps[s.i + (e.key === "ArrowRight" ? 1 : -1)]; if (!o) return;
      e.preventDefault(); location.hash = "build-" + o.id;
    }
    document.addEventListener("keydown", onKey); cleanup.push(function () { document.removeEventListener("keydown", onKey); });
    var v = document.getElementById("wholefilm");
    $$(".th-chap button").forEach(function (b) { b.addEventListener("click", function () { if (!v) return; v.currentTime = Number(b.dataset.t); v.play().catch(function () {}); }); });
    if (v) v.addEventListener("timeupdate", function () {
      var bs = $$(".th-chap button"), on = null;
      bs.forEach(function (b) { if (Number(b.dataset.t) <= v.currentTime + 0.2) on = b; });
      bs.forEach(function (b) { b.setAttribute("aria-current", b === on ? "true" : "false"); });
    });
  };

  // ---- the parts: every part in one sortable table (from the canon), and each card opens to its steps, lessons, checks and where to get it
  function partMore(p, open) {
    return '<details class="pt-more"' + (open ? " open" : "") + "><summary>Steps, checks, where to get it</summary><dl class=\"xdl\">" +
      xrow("Steps", "step", p.steps) + xrow("Checked by", "check", p.checks) + xrow("Words", "term", p.terms) + xrow("Comes in", "offer", p.offers) + "</dl></details>";
  }
  var KIND = { printed: "Printed", bought: "Bought", optional: "Printed, optional", gauge: "Printed, a gauge" };
  function secs(t) { if (!t) return null; var m = String(t).match(/(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?/); return m ? (Number(m[1] || 0) * 3600 + Number(m[2] || 0) * 60 + Number(m[3] || 0)) : null; }
  function partsTable() {
    var rows = GR.parts.map(function (p) {
      var t = secs(p.time);
      return '<tr data-k="' + esc(p.key) + '"><th scope="row" data-v="' + esc(p.name.toLowerCase()) + '"><a href="#part-' + p.key + '">' + esc(p.name) + "</a></th>" +
        '<td data-v="' + esc(p.kind) + '">' + esc(KIND[p.kind] || p.kind) + "</td>" +
        '<td data-v="' + esc(p.colour) + '"><span class="sw" style="background:' + esc(p.hex || "#fff") + '" aria-hidden="true"></span>' + esc(p.colour) + "</td>" +
        '<td class="num" data-v="' + (p.grams == null ? -1 : p.grams) + '">' + (p.grams == null ? '<span class="quiet">&ndash;</span>' : esc(Math.round(p.grams * 10) / 10) + " g") + "</td>" +
        '<td class="num" data-v="' + (t == null ? -1 : t) + '">' + (t == null ? '<span class="quiet">&ndash;</span>' : esc(p.time.replace(/ \d+s$/, ""))) + "</td>" +
        '<td data-v="' + p.steps.length + '">' + (p.steps.length ? p.steps.map(function (s) { return '<a href="#build-' + s + '">' + esc(s) + "</a>"; }).join(" ") : '<span class="quiet">&ndash;</span>') + "</td>" +
        '<td data-v="' + p.lessons.length + '">' + (p.lessons.length ? p.lessons.map(function (l) { var L = GR.lessons[l]; return L ? '<a href="#' + L.route + '" title="' + esc(L.title) + '">' + esc(L.num) + '<span class="sr-only">: ' + esc(L.title) + "</span></a>" : ""; }).join(" ") : '<span class="quiet">&ndash;</span>') + "</td></tr>";
    }).join("");
    var cols = [["Part", "text"], ["Printed or bought", "text"], ["Colour", "text"], ["Grams", "num"], ["Print time", "num"], ["Steps", "num"], ["Lessons", "num"]];
    return '<section class="ptable" id="ptable" aria-labelledby="pt-h"><h2 id="pt-h">Every part, in one table</h2><p class="lead">Sort by any column. Print times and grams are from the slicer, for one camera.</p>' +
      '<div class="tablewrap" tabindex="0" role="region" aria-label="Every part"><table class="sortable"><caption class="sr-only">Every part: printed or bought, colour, grams, print time, the steps and lessons it belongs to. Column buttons sort.</caption><thead><tr>' +
      cols.map(function (c, i) { return '<th scope="col"' + (i === 0 ? ' aria-sort="none"' : "") + ' data-type="' + c[1] + '"><button type="button" data-col="' + i + '">' + esc(c[0]) + '<span class="sort-i" aria-hidden="true"></span></button></th>'; }).join("") +
      "</tr></thead><tbody>" + rows + "</tbody></table></div></section>";
  }
  function wireSort(root) {
    $$("table.sortable", root).forEach(function (t) {
      var ths = $$("thead th", t);
      $$("thead button", t).forEach(function (b) {
        b.addEventListener("click", function () {
          var i = Number(b.dataset.col), th = ths[i], dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending", num = th.dataset.type === "num";
          ths.forEach(function (x) { x.removeAttribute("aria-sort"); }); th.setAttribute("aria-sort", dir);
          var tb = $("tbody", t), rows = $$("tr", tb);
          rows.sort(function (a, c) {
            var x = a.children[i].getAttribute("data-v"), y = c.children[i].getAttribute("data-v");
            var r = num ? Number(x) - Number(y) : String(x).localeCompare(String(y));
            return dir === "ascending" ? r : -r;
          }).forEach(function (r) { tb.appendChild(r); });
          announce("Sorted by " + b.textContent + ", " + dir);
        });
      });
    });
  }
  function moreParts() {     // the parts with no card: the pinhole disc, the near ring, the gauges
    var rest = GR.parts.filter(function (p) { return !PART[p.key]; });
    if (!rest.length) return "";
    return '<section class="mparts" aria-labelledby="mp-h"><h2 id="mp-h">And the small ones</h2><ul class="mp-list">' + rest.map(function (p) {
      return '<li id="part-' + p.key + '" tabindex="-1"><h3>' + esc(p.name) + ' <span class="mp-k">' + esc(KIND[p.kind] || p.kind) + "</span></h3><p>" + esc(p.does[0].toUpperCase() + p.does.slice(1)) + ".</p>" + partMore(p, false) + "</li>";
    }).join("") + "</ul></section>";
  }

  // ---- the glossary: every word, what it means here, where it is taught, and the parts and steps it is about
  pages.glossary = function () {
    var terms = GR.terms.slice().sort(function (a, b) { return a.term.localeCompare(b.term); });
    return '<div class="wrap gloss-page"><div class="pagehead"><h1>Glossary</h1><p class="lead">The camera words in the lessons and the guide: what each means on this camera, and where it is taught.</p></div>' +
      '<ul class="az" aria-label="Words">' + terms.map(function (t) { return '<li><a href="#glossary-' + t.id + '" data-go="term-' + t.id + '">' + esc(t.term) + "</a></li>"; }).join("") + "</ul>" +
      '<ol class="terms" role="list">' + terms.map(function (t) {
        return '<li class="term" id="term-' + t.id + '" tabindex="-1"><h2>' + esc(t.term) + (t.says ? ' <span class="t-says">on the camera: the ' + esc(t.says) + "</span>" : "") + "</h2><p>" + esc(t.means) + '</p><dl class="xdl">' +
          xrow("Taught in", "lesson", t.taught) + xrow("Parts", "part", t.parts) + xrow("Steps", "step", t.steps) + "</dl></li>";
      }).join("") + "</ol></div>";
  };
  pages.glossary.title = "Glossary";
  pages.glossary.wide = true;

  // ---- facts: every public number in a plain sentence, and the check that proves it.  No prices, costs or suppliers: those are not facts about the camera
  pages.facts = function () {
    return '<div class="wrap facts-page"><div class="pagehead"><h1>The camera in numbers</h1><p class="lead">Every number on this site, in a sentence, and the check that proves it. Each check is a program that tested the design before anything was printed.</p></div>' +
      '<section aria-labelledby="ck-h"><h2 id="ck-h">The checks</h2><ul class="checks">' + GR.checks.map(function (c) {
        return '<li id="c-' + rid(c.id) + '" tabindex="-1"><h3>' + esc(c.name) + '</h3><p class="ck-q">' + esc(c.question) + '</p><p class="ck-h">' + esc(c.headline) + "</p><p>" + esc(c.proves) + '</p><dl class="xdl">' +
          xrow("Numbers", "fact", c.facts) + xrow("Parts", "part", c.parts) + "</dl></li>";
      }).join("") + "</ul></section>" +
      '<section aria-labelledby="fn-h2"><h2 id="fn-h2">Every number</h2><ol class="factlist" role="list">' + GR.facts.map(function (f) {
        return '<li id="f-' + rid(f.id) + '" tabindex="-1"><p class="fl-say">' + esc(f.say) + '</p><p class="fl-s">' + esc(f.sentence) + '</p><p class="fl-by">' +
          (f.checks.length ? '<span class="st-lab">Proved by</span>' + xchips("check", f.checks) : '<span class="st-lab">Where it comes from</span>' + esc(f.basis || "")) + "</p>" +
          (f.lessons.length ? '<p class="fl-by"><span class="st-lab">Taught in</span>' + xchips("lesson", f.lessons) + "</p>" : "") + "</li>";
      }).join("") + "</ol></section></div>";
  };
  pages.facts.title = "The camera in numbers";
  pages.facts.wide = true;

  // ---- wholesale on Programs: who, minimums, lead time, contact, and the class sets (each one a target for links to it)
  function wholesaleBlock() {
    var cls = GR.offers.filter(function (o) { return o.group === "class"; });
    var q = mailto(MAIL.schools, "CURVE 35 wholesale quote", "Hello,\n\nWe'd like a wholesale quote.\n\nWho we are (shop, school, makerspace):\nHow many kits:\nWhen:\nShip to (city and country):\n\nAnything else:\n");
    return '<section class="whole" id="wholesale" tabindex="-1" aria-labelledby="wh-h"><h2 id="wh-h">Wholesale</h2><p class="lead">For shops, schools and makerspaces. Tell us how many and when; we reply with a quote.</p>' +
      '<dl class="wh-terms"><div><dt>Who</dt><dd>Shops, schools, homeschool groups, camps, libraries, makerspaces</dd></div><div><dt>Minimums</dt><dd>Ask us</dd></div><div><dt>Lead time</dt><dd>Ask us</dd></div>' +
      "<div><dt>Contact</dt><dd>" + mailLink(MAIL.schools) + (MAIL.hello && MAIL.hello !== MAIL.schools ? " (shops: " + mailLink(MAIL.hello) + ")" : "") + "</dd></div></dl>" +
      '<p class="path-links"><a class="btn main" href="' + esc(q) + '">Email for a wholesale quote</a></p>' +
      (cls.length ? '<div class="tablewrap" tabindex="0" role="region" aria-label="Class sets"><table class="wh-sets"><caption>Class sets</caption><thead><tr><th scope="col">Set</th><th scope="col">What is in it</th><th scope="col">Price</th><th scope="col">Programs</th></tr></thead><tbody>' + cls.map(function (o) {
        var p = PROD[o.id] || {};
        return '<tr id="p-' + o.id + '" tabindex="-1"><th scope="row">' + esc(o.name) + "</th><td>" + esc((p.contents || []).join("; ")) + '</td><td class="tnum">' + esc(o.price || "") + "</td><td>" + (xchips("program", o.programs) || '<span class="quiet">&ndash;</span>') + "</td></tr>";
      }).join("") + "</tbody></table></div>" : "") + "</section>";
  }
  // ---- the rest of the shop, in one list: everything the cards above do not show (each one a target for links to it)
  function priceList(shown) {
    var rest = GR.offers.filter(function (o) { return o.home === "store" && !shown[o.id]; });
    if (!rest.length) return "";
    return '<section class="plist" aria-labelledby="pl-h2"><h2 id="pl-h2">Everything else in the shop</h2><div class="tablewrap" tabindex="0" role="region" aria-label="Everything else in the shop"><table><thead><tr><th scope="col">Item</th><th scope="col">What it is</th><th scope="col">Price</th><th scope="col"><span class="sr-only">Add or ask</span></th></tr></thead><tbody>' +
      rest.map(function (o) {
        var p = PROD[o.id] || {};
        var act = p.basket ? addBtn(p, "small", "Add") : '<a class="btn small" href="' + esc(mailto(MAIL.hello, "CURVE 35: " + o.name)) + '">Ask<span class="sr-only"> about ' + esc(o.name) + "</span></a>";
        return '<tr id="p-' + o.id + '" tabindex="-1"><th scope="row">' + esc(o.name) + "</th><td>" + esc(p.for || (p.contents || [])[0] || "") + (o.parts.length ? xchips("part", o.parts) : "") + '</td><td class="tnum">' + esc(o.price || "") + "</td><td>" + act + "</td></tr>";
      }).join("") + "</tbody></table></div></section>";
  }

  // ---- for teachers: the mission side.  Free plans, slides and teacher views; class sets and the four packages are on Programs
  pages.teachers = function () {
    return '<div class="teachers">' +
      '<section class="teach-plate" aria-labelledby="tc-h1"><div class="wrap tp-in"><div class="pagehead"><p class="kick kick-sun">For teachers</p><h1 id="tc-h1">Teach light, lenses and mechanisms. With the camera in their hands.</h1>' +
      '<p class="lead">Nine lessons, each a 50-minute period. Every one has a plan, slides and a teacher view. Free, no account.</p>' +
      '<div class="ctas"><a class="btn main big" href="#teach-1">Open the lesson 1 plan</a><a class="btn big" href="#lesson-1-slides">Show lesson 1 as slides</a></div></div>' +
      '<ul class="cl-grid"><li><b>50</b><span>minutes, planned minute by minute</span></li><li><b>9</b><span>lessons, one piece of the camera each</span></li><li><b>1</b><span>kit per student, built in a session</span></li><li><b>0</b><span>accounts, for you or for them</span></li></ul></div></section>' +
      '<div class="wrap"><h2 class="t-h">What you get</h2><ul class="t4">' +
      '<li class="t-sun"><h3>Lesson plans</h3><p>The period minute by minute, the materials, the objectives and an exit ticket.</p></li>' +
      '<li class="t-sky"><h3>Slides</h3><p>Each lesson\'s key moments and simulations, full screen. Arrow keys to step.</p></li>' +
      '<li class="t-mint"><h3>Teacher view</h3><p>Questions with answers, the misconception to listen for, support and stretch.</p></li>' +
      '<li class="t-tang"><h3>Hands on</h3><p>Students build first. Then each lesson explains a part they are holding.</p></li></ul>' +
      '<h2 class="t-h">The nine lessons</h2><ol class="tlist" role="list">' + LESSONS.map(function (L) {
        return '<li style="' + cvars(lcol(L)) + '"><span class="tl-n" aria-hidden="true">' + esc(L.num) + '</span><span class="tlist-t"><strong>' + esc(L.title) + "</strong><span>" + esc(L.question) + "</span></span>" +
          '<span class="tlist-a"><a href="#' + L.route + '">Lesson<span class="sr-only"> ' + esc(L.num) + '</span></a><a href="#' + L.route + '-teach">Plan<span class="sr-only">, lesson ' + esc(L.num) + '</span></a><a href="#' + L.route + '-slides">Slides<span class="sr-only">, lesson ' + esc(L.num) + "</span></a></span></li>";
      }).join("") + "</ol>" +
      '<p class="t-mk"><strong>Shop class or club with printers?</strong> Four <a href="#makers">maker lessons</a> cover printing, snap fits, testing and fit to the hand.</p>' +
      '<section class="sets" aria-labelledby="cs-h"><h2 id="cs-h">Class sets and programs</h2><p class="lead">Class sets of 8, 16 or 24 kits, and four ready-made plans: homeschool, a classroom elective, a summer week and a weekend workshop.</p>' +
      '<ul class="pg-mini">' + PROGRAMS.map(function (g) { return '<li class="t-' + g.tone + '"><a href="#programs" data-focus="pg-' + g.id + '"><strong>' + esc(g.name) + "</strong><span>" + esc(g.when) + "</span></a></li>"; }).join("") + "</ul>" +
      '<p class="path-links"><a class="btn main" href="#programs">See the programs</a><a class="btn" href="' + esc(mailto(MAIL.schools, "CURVE 35 for my class")) + '">Email ' + esc(MAIL.schools) + '</a></p></section>' +
      '<p class="after-line">Have printers? Print the parts from the <a href="#files">free files</a> and add lenses: <a href="#spares">three for $5</a>.</p></div></div>';
  };
  pages.teachers.title = "For teachers";
  pages.teachers.wide = true;

  // ---- programs: four ready-made ways to teach with the camera.  Kits at the store's prices; class sets by quote (schools@).
  var PROGRAMS = C.programs || [];          // canon/offers.yaml
  function programQuote(g) {
    return mailto(MAIL.schools, "CURVE 35 quote: " + g.name,
      "Hello,\n\nWe'd like a quote for the " + g.name.toLowerCase() + " program.\n\nWho it's for (school, group or family):\nNumber of students:\nKits wanted:\nDates:\nShip to (city and state):\n\nAnything else:\n");
  }
  pages.programs = function () {
    var S = PROD["starter-kit"], K = PROD["camera-kit"];
    var kitPrice = (S ? "Starter kit " + price(S) : "") + (S && K ? " &middot; " : "") + (K ? "Camera kit " + price(K) : "");
    return '<div class="programs"><section class="pg-plate" aria-labelledby="pg-h1"><div class="wrap"><div class="pagehead"><p class="kick">Programs</p><h1 id="pg-h1">Teach it at home, in a class, in a week or a weekend.</h1>' +
      '<p class="lead">Four ready-made plans for 14 and up. Each one: who it is for, what is included, the schedule.</p>' + waysStrip("programs") +
      '<p class="pg-free"><strong>Included free:</strong> ' + esc(C.programs_free) + '.</p></div></div></section>' +
      '<div class="wrap"><ol class="pg-list" role="list">' + PROGRAMS.map(function (g) {
        var cost = g.price === "quote" ? '<span class="pg-p">Ask for a quote</span>' : '<span class="pg-p">' + kitPrice + "</span>";
        return '<li class="pg t-' + g.tone + '" id="pg-' + g.id + '" tabindex="-1"><div class="pg-head"><h2>' + esc(g.name) + '</h2><p class="pg-when">' + esc(g.when) + "</p></div>" +
          '<div class="pg-body"><div><h3>Who it is for</h3><p>' + esc(g.who) + "</p><h3>What is included</h3><ul>" + g.inc.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>" +
          '<div><h3>The schedule</h3><dl class="pg-plan">' + g.plan.map(function (r) { return "<div><dt>" + esc(r[0]) + "</dt><dd>" + esc(r[1]) + "</dd></div>"; }).join("") + "</dl></div></div>" +
          (GPG[g.id] && GPG[g.id].offers.length ? '<p class="pg-offers"><span class="st-lab">Bought as</span>' + xchips("offer", GPG[g.id].offers) + "</p>" : "") +
          '<p class="pg-buy"><span class="pg-kits">' + esc(g.kits) + "</span>" + cost + '<a class="btn main" href="' + esc(programQuote(g)) + '">Get a quote<span class="sr-only">: ' + esc(g.name) + "</span></a></p></li>";
      }).join("") + "</ol>" + wholesaleBlock() +
      '<p class="after-line">Quotes and questions go to ' + mailLink(MAIL.schools) + '. The free plans and slides for each lesson are on <a href="#teachers">For teachers</a>.</p></div></div>';
  };
  pages.programs.title = "Programs";
  pages.programs.wide = true;

  // ---- open files: what is open, under which licence, where it lives, how to change it and give it back.
  //      The designs, guides, lessons and films are CC BY-NC-SA 4.0 ("open files", not "open source": NC is not open source in the strict sense);
  //      the site code and the tools are open source (MIT); the name and logos are trademarks (site/PUBLIC_LICENSE.md).
  pages.opensource = function () {
    var S = FILES.source || {};
    return '<div class="ospage">' +
      '<section class="os-plate" aria-labelledby="os-h1"><div class="wrap of-in"><div class="pagehead"><p class="kick kick-mint">Open files</p><h1 id="os-h1">All of it is open to print, change and teach with.</h1>' +
      '<p class="lead">The CAD, the print files, the guides, the lessons and the films. Print it, change it, remix it, teach with it. Give credit and share your changes the same way.</p>' +
      '<div class="ctas"><a class="btn main big" href="#files">Download the files</a><a class="btn big" href="' + REPO + '" rel="noopener">The code on GitHub</a></div></div>' +
      '<div class="code-card"><p class="cc-bar"><span aria-hidden="true"><i></i><i></i><i></i></span>variadic-group/curve-35-site</p><dl class="cc-dl"><div><dt>Repository</dt><dd><a href="' + REPO + '" rel="noopener">github.com/variadic-group/curve-35-site</a></dd></div>' +
      '<div><dt>CAD</dt><dd>OpenSCAD, one file' + (S.bytes ? ", " + kib(S.bytes) : "") + '</dd></div><div><dt>Print files</dt><dd>8 parts, no supports</dd></div>' +
      '<div><dt>Designs</dt><dd><a href="' + CC + '" rel="license noopener">CC BY-NC-SA 4.0</a></dd></div><div><dt>Code</dt><dd>MIT, open source</dd></div></dl></div></div></section>' +
      '<div class="wrap"><h2 class="t-h">What is open</h2><ul class="t4">' +
      '<li class="t-mint"><h3>The CAD</h3><p>Every part as OpenSCAD code. Change a number and the part changes.</p></li>' +
      '<li class="t-sun"><h3>The print files</h3><p>Eight parts, 0.2 mm layers, no supports, about 9 hours of printing.</p></li>' +
      '<li class="t-sky"><h3>Guides and lessons</h3><p>The printed guide, the build manual, the nine lessons and their films.</p></li>' +
      '<li class="t-tang"><h3>The code</h3><p>This site and the tools that tested the camera: light, fit, motion and printing.</p></li></ul>' +
      '<section class="lic" id="licence" tabindex="-1" aria-labelledby="lic-h"><h2 class="t-h" id="lic-h">What you can do with it</h2><div class="lic-grid">' +
      '<div class="lic-card t-mint"><h3>Yes</h3><ul><li>Print it, for yourself, a class or a club.</li><li>Change it and remix it.</li><li>Teach with it: the lessons, slides and films too.</li><li>Share what you made, under the same licence.</li></ul></div>' +
      '<div class="lic-card t-pink"><h3>Ask first</h3><ul><li>Selling kits, prints or copies needs our permission.</li><li>The CURVE 35 name and logos are trademarks: not part of the licence.</li></ul><p><strong>Want to sell kits?</strong> Email ' + mailLink(MAIL.hello) + '.</p></div>' +
      '<div class="lic-card t-sun"><h3>Give credit like this</h3><p class="lic-credit">' + esc(META.credit) + '</p><p>Designs, guides, lessons and films: <a href="' + CC + '" rel="license noopener">' + esc(META.licence_designs) + '</a>. The site code and the tools: MIT.</p></div></div>' +
      '<p class="lic-note">The camera on this site is model ' + esc(META.model || "") + '.</p></section>' +
      '<h2 class="t-h">Make a remix</h2><ol class="loop">' +
      '<li><span class="s-n" aria-hidden="true">1</span><h3>Get the files</h3><p>Download the source and the print files, or fork the code.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">2</span><h3>Change one thing</h3><p>A colour, a knob, a ring. The <a href="#makers">maker lessons</a> explain every shape.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">3</span><h3>Print and test</h3><p>Print the fit gauge first. Then shoot a test roll.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">4</span><h3>Share it back</h3><p>Post it on <a href="#builds">Builds</a>, with the credit line. The best remixes get featured.</p></li></ol>' +
      '<section class="makers" id="os-makers" aria-labelledby="osm-h"><p class="kick">For makers</p><h2 id="osm-h">Made by a printer</h2><p class="lead">Four lessons on why every shape in these files is the shape it is.</p>' + makerRow(false) + "</section></div></div>";
  };
  pages.opensource.title = "Open files";
  pages.opensource.wide = true;
  // ---- help
  pages.help = function () {
    return '<div class="page"><p class="kicker"><a href="#build">The build guide</a></p><h1>Help</h1><p class="lead">Something not right? Type what you see. Most fixes take a minute.</p>' +
      '<div class="search" role="search"><label class="sr-only" for="q">Search the help</label><input id="q" type="search" placeholder="For example: knob, back, blank, streaks" autocomplete="off"><p class="note" id="hits" aria-live="polite"></p></div>' +
      '<h2>Common problems</h2><ul class="trouble" id="trouble"></ul><h2>Step by step</h2><ul class="trouble" id="atstep"></ul>' + contactBlock() + "</div>";
  };
  function contactBlock() {           // canon/company.yaml: who to write to, the phone, the post
    return '<section class="contact" id="contact" tabindex="-1" aria-labelledby="ct-h"><h2 id="ct-h">Contact</h2><p>Still stuck, or something to ask? Write to the address that fits.</p><dl class="ct-list">' +
      (META.contact || []).map(function (c) { return "<div><dt>" + mailLink(c.email) + "</dt><dd>" + c.html + "</dd></div>"; }).join("") +
      '<div><dt><a href="tel:' + esc(META.tel) + '">' + esc(META.phone) + "</a></dt><dd>" + esc(META.phone_note) + "</dd></div>" +
      "<div><dt>By post</dt><dd>" + esc(META.company) + ", " + esc(META.address) + "</dd></div></dl></section>";
  }
  pages.help.title = "Help";
  // ---- thanks: where Stripe sends a paid order back to (worker/checkout.js: success_url).  The basket is emptied on the way in (see below).
  pages.thanks = function () {
    return '<div class="page"><h1>Thank you.</h1><p class="lead">Your order is in.</p>' +
      "<p>Stripe has sent a receipt to your email. We will write again when your parcel is on its way.</p>" +
      "<p>A question about it? " + mailLink(MAIL.support) + "</p>" +
      '<p class="ctas"><a class="btn main" href="#start">Start here</a><a class="btn" href="#lessons">Lessons</a></p></div>';
  };
  pages.thanks.title = "Thank you";
  pages.help.after = function () {
    var T = G.trouble, S = G.steps.filter(function (s) { return s.ifnot; });
    function hi(text, words) { var h = esc(text); words.forEach(function (w) { if (w.length > 1) h = h.replace(new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>"); }); return h; }
    function draw() {
      var q = document.getElementById("q").value.trim().toLowerCase(), words = q.split(/\s+/).filter(Boolean);
      function hit(t) { t = t.toLowerCase(); return words.every(function (w) { return t.indexOf(w) >= 0; }); }
      var a = T.filter(function (t) { return hit(t.problem + " " + t.cause + " " + t.fix); }), b = S.filter(function (s) { return hit(s.name + " " + s.do + " " + s.check + " " + s.ifnot); });
      document.getElementById("trouble").innerHTML = a.map(function (t) { return '<li><div class="pr">' + hi(t.problem, words) + '</div><div><span class="lab">Why</span>' + hi(t.cause, words) + '</div><div><span class="lab">Do this</span>' + hi(t.fix, words) + "</div></li>"; }).join("") || "<li>Nothing in this list matches.</li>";
      document.getElementById("atstep").innerHTML = b.map(function (s) { return '<li><div class="pr"><a href="#build-' + s.code + '">' + esc(s.name) + '</a></div><div><span class="lab">You should see</span>' + hi(s.check, words) + '</div><div><span class="lab">If not</span>' + hi(s.ifnot, words) + "</div></li>"; }).join("") || "<li>No step matches.</li>";
      document.getElementById("hits").textContent = q ? (a.length + b.length) + (a.length + b.length === 1 ? " match" : " matches") : "";
    }
    document.getElementById("q").addEventListener("input", draw); draw();
  };

  // ---- open files, and the maker shelf
  var dlP = null;
  function downloadsCap() {   // the page capability "downloads": null when this view cannot save files
    if (!window.claude || typeof window.claude.use !== "function") return Promise.resolve(null);
    if (!dlP) dlP = Promise.resolve().then(function () { return window.claude.use("downloads"); }).catch(function () { return null; });
    return dlP;
  }
  /* One download.  Outside Claude: a plain link to the real file in downloads/.  Inside Claude: a button that unpacks the JSON copy
     and saves it through the "downloads" capability (wired by wireDownloads; hidden until that capability answers). */
  function dlControl(f, label, cls) {
    var name = f.filename || f.file || "";
    if (!inClaude() && f.dl) return '<a class="btn small dlink ' + (cls || "") + '" href="' + esc(f.dl) + '" download>' + esc(label) + '<span class="sr-only"> ' + esc(f.file || name) + "</span></a>";
    if (f.src) return '<button class="btn small dl ' + (cls || "") + '" type="button" data-src="' + esc(f.src) + '" data-name="' + esc(name) + '" hidden>' + esc(label) + '<span class="sr-only"> ' + esc(name) + "</span></button>";
    return "";
  }
  function moreFiles() {
    var M = (FILES.more || []).filter(function (f) { return f.src || f.dl; }); if (!M.length) return "";
    var WHAT = { fit_gauge: "Print first: checks your printer's fit before the real parts", lens_gauge: "Checks the lens pocket against your lens", test_slab: "A quick check of layers and walls", blade_soft: "A fifth softer: keep it if the rocker is hard to press", blade_stiff: "A fifth stiffer: keep it if the click is faint", layout: "All the parts laid out on one bed" };
    return '<h2 class="files-h">Test prints and layout</h2><ul class="files files-more">' + M.map(function (f) {
      return '<li class="file src"><span class="srcicon" aria-hidden="true">' + (f.kind === "scad" ? "{ }" : "&#9651;") + '</span><div class="file-t"><h3>' + esc(f.name) + '</h3><p class="fmeta"><span>' + esc(WHAT[f.key] || "") + "</span><span>" + kib(f.bytes || 0) + "</span></p></div>" + dlControl(f, "Download") + "</li>";
    }).join("") + "</ul>";
  }
  // the printed guides as PDFs, and the whole build film.  all: the Files page (every PDF); otherwise the Build page's five
  function guidesBlock(all) {
    var G2 = (FILES.guides || []).filter(function (g) { return all || g.group !== "more"; }); if (!G2.length) return "";
    var WHAT = { booklet: "The printed guide that comes in the kit", manual: "Every step, with pictures, to print", focus: "Check the focus of a finished camera", light: "Which dot for which light, to stick on",
      sheets: "Every part, flat, with its print settings", card: "The camera on one card", maker: "How the parts were designed to print", film: "Every step end to end" };
    return '<section class="guides" aria-labelledby="gu-h' + (all ? "f" : "b") + '"><h2 id="gu-h' + (all ? "f" : "b") + '">Guides</h2><p class="lead">The printed guides, to keep or print, and the whole build film.</p><ul class="guide-list">' + G2.map(function (g) {
      var watch = g.group === "film" ? '<a class="btn small" href="#build-film">Watch</a>' : "";
      var act = g.group === "film" ? (inClaude() ? "" : dlControl(g, "Download")) : dlControl(g, g.kind === "pdf" ? "PDF" : "Download");
      if (!act && !watch) return "";
      return '<li><span class="gu-ic" aria-hidden="true">' + (g.group === "film" ? "&#9654;" : "PDF") + '</span><span class="gu-t"><strong>' + esc(g.name) + "</strong><span>" + esc(WHAT[g.key] || "") + " &middot; " + kib(g.bytes || 0) + '</span></span><span class="gu-a">' + watch + act + "</span></li>";
    }).join("") + '</ul><p class="dlstate note" role="status"></p></section>';
  }
  function fileRow(f) {
    var meta = [];
    if (f.colour) meta.push("<span>" + esc(f.colour.split(",")[0]) + "</span>");
    if (f.time) meta.push("<span>" + esc(f.time.replace(/ \d+s$/, "")) + "</span>");
    if (f.grams != null) meta.push("<span>" + esc(Math.round(f.grams * 10) / 10) + " g</span>");
    if (f.bytes) meta.push("<span>" + kib(f.bytes) + "</span>");
    var act = f.src || f.dl ? dlControl(f, "Download") : '<span class="nb">Bought, not printed</span>';
    return '<li class="file">' + (f.img ? '<span class="file-pic">' + img(f.img, "", ' width="520" height="390"') + "</span>" : "<span></span>") +
      '<div class="file-t"><h3>' + esc(f.name.charAt(0).toUpperCase() + f.name.slice(1)) + '</h3><p class="fmeta">' + meta.join("") + "</p></div>" + act + "</li>";
  }
  pages.files = function () {
    var ch = C.checked || { rows: [] };
    var rows = ch.rows.map(function (r) { return "<tr><td>" + fmt(r.q) + "</td><td>" + fmt(r.how) + "</td><td>" + fmt(r.result) + "</td></tr>"; }).join("");
    var S = FILES.source || {};
    return '<div class="wrap files-page"><div class="pagehead"><p class="kick">Open files</p><h1>Print it yourself. Free.</h1><p class="lead">Eight parts, no supports, any ordinary printer. Add one lens and you have the camera. <a href="#open-files">What you can do with the files</a>.</p>' +
      '<dl class="bns"><div class="bn-y"><dt>9.4 h</dt><dd>of printing</dd></div><div class="bn-b"><dt>' + esc(FILES.grams || 118) + ' g</dt><dd>of plastic</dd></div><div class="bn-g"><dt>0</dt><dd>supports</dd></div><div class="bn-o"><dt>0.2 mm</dt><dd>layers</dd></div></dl>' +
      '<p class="dlstate note" id="dlstate" role="status">Checking whether this view can save files.</p></div>' +
      '<ol class="files">' + FILES.parts.map(fileRow).join("") +
      '<li class="file src"><span class="srcicon" aria-hidden="true">{ }</span><div class="file-t"><h3>OpenSCAD source</h3><p class="fmeta"><span>Every part, as code</span><span>' + kib(S.bytes || 0) + "</span></p></div>" +
      (S.src || S.dl ? dlControl(S, "Download") : "") + "</li></ol>" +
      moreFiles() + guidesBlock(true) +
      '<section class="makers" id="makers" tabindex="-1" aria-labelledby="mk-h"><p class="kick">For makers</p><h2 id="mk-h">Made by a printer</h2><p class="lead">Four lessons on why every shape in these files is the shape it is.</p>' + makerRow(false) + "</section>" +
      '<div class="two-up"><section aria-labelledby="ps-h"><h2 id="ps-h">Print settings</h2><ul><li>0.2 mm layers, no supports.</li><li>Body, back, shutter and wheel in black: they keep light off the film.</li><li>Frame wheel in blue, the top five layers white for the arrow.</li></ul></section>' +
      '<section aria-labelledby="mi-h"><h2 id="mi-h">Make it yours</h2><ul><li>Print the front plate and knobs in your own colours.</li><li>The back is 126 x 59 mm of flat space for a name.</li><li>Change a number in the source and the part changes.</li></ul><p><a href="#builds">Share what you made</a></p></section></div>' +
      '<details class="tests"><summary>What we tested</summary><div class="tablewrap" tabindex="0" role="region" aria-label="Tests"><table><thead><tr><th scope="col">Question</th><th scope="col">How</th><th scope="col">Result</th></tr></thead><tbody>' + rows + "</tbody></table></div></details>" +
      '<p class="after-line">No printer? <a href="#store">The kits come printed</a>.</p></div>';
  };
  pages.files.title = "Files";
  pages.files.wide = true;
  pages.files.after = function () { wireDownloads($("#dlstate")); };
  // the download buttons on a page (dlControl).  state: where to say what happens; every .dlstate on the page follows it
  function wireDownloads(state) {
    var btns = $$(".dl"), states = $$(".dlstate");
    function say(t) { states.forEach(function (s) { s.textContent = t; }); }
    if (!inClaude()) {
      say($$(".dlink").length ? "Each file downloads straight to your device." : "Downloads aren't available in this view.");
      return;
    }
    if (!state) state = states[0];
    function unavailable() { say("Downloads aren't available in this view."); btns.forEach(function (b) { b.hidden = true; }); }
    if (!btns.length) return;
    downloadsCap().then(function (dl) {
      if (!state || !document.body.contains(state)) return;
      if (!dl) { unavailable(); return; }
      if (typeof DecompressionStream === "undefined") { say("This browser cannot unpack the files. Try a recent browser."); return; }
      say("Each file saves to your device after you confirm it.");
      btns.forEach(function (b) {
        b.hidden = false;
        b.addEventListener("click", function () {
          var label = b.innerHTML; b.disabled = true; b.textContent = "Preparing";
          fetch(b.dataset.src).then(function (r) { if (!r.ok) throw new Error("the file could not be read (" + r.status + ")"); return r.json(); }).then(function (j) {
            var bin = atob(j.data), u = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
            return new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
          }).then(function (buf) {
            return dl.save({ filename: b.dataset.name, data: new Uint8Array(buf) });
          }).then(function () { announce(b.dataset.name + " saved."); say(b.dataset.name + " saved."); }, function (e) {
            var why = e && (e.code || e.name) ? String(e.code || e.name) : ""; say(/declin|deni|cancel|abort|reject/i.test(why + " " + (e && e.message)) ? "Not saved: the download was declined." : "Not saved: " + ((e && e.message) || "the download did not finish") + ".");
          }).then(function () { b.disabled = false; b.innerHTML = label; });
        });
      });
    });
  }

  // ---- builds: the community gallery (js/community.js)
  function postCard(p, mine) {
    var when = p.createdAt ? new Date(p.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "";
    return '<li class="post"><p class="post-top"><span class="ptag">' + (p.kind === "remix" ? "Remix" : "Build") + "</span>" + (mine ? '<span class="ptag mine">Yours</span>' : "") + "</p>" +
      "<h3>" + esc(p.title || "Untitled") + "</h3>" + (p.body ? "<p>" + esc(p.body).replace(/\n+/g, "<br>") + "</p>" : "") +
      (p.link ? '<p><a href="' + esc(p.link) + '" rel="nofollow noopener noreferrer ugc" target="_blank">' + esc(p.link.replace(/^https:\/\//, "").slice(0, 60)) + "</a></p>" : "") +
      '<p class="post-by">' + esc(p.name || "A builder") + (when ? " &middot; " + esc(when) : "") + "</p></li>";
  }
  // what makes a good post: four coloured cards, each with a picture and a door to the page that helps
  function buildIdeas() {
    var I = [["tang", "media/img/part_front.webp", "Your colours", "Front plate and knobs in your own colours: show them off.", "#files", "The free files"],
      ["sun", PIC.b3c, "Your build time", "From the bag to the last click: how long did it take you?", "#build", "The build guide"],
      ["sky", PIC.s3, "Your first roll", "The best picture, and the one that went wrong. Both count.", "#build-p1", "Which dot?"],
      ["mint", PIC.section, "Your remix", "Changed a number in the source? Show what it does.", "#makers", "Maker lessons"]];
    return '<section class="ideas" aria-labelledby="id-h"><h2 id="id-h">What makes a good post</h2><ul class="idea-grid">' + I.map(function (x) {
      return '<li class="idea t-' + x[0] + '"><span class="idea-pic">' + img(x[1], "", ' width="520" height="390"') + "</span><h3>" + esc(x[2]) + "</h3><p>" + esc(x[3]) + '</p><a href="' + x[4] + '">' + esc(x[5]) + "</a></li>";
    }).join("") + "</ul></section>";
  }
  // the contribution loop: build, share, fork, remix; and the slot where featured remixes go
  function buildLoop() {
    return '<ol class="loop loop-b" aria-label="How it works">' +
      '<li><span class="s-n" aria-hidden="true">1</span><h3>Build it</h3><p>Follow the <a href="#build">build guide</a>. Shoot a roll.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">2</span><h3>Share your build</h3><p>Your colours, your build time, your best picture.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">3</span><h3>Change the files</h3><p>Change one thing in the <a href="#open-files">open files</a>.</p></li>' +
      '<li><span class="s-n" aria-hidden="true">4</span><h3>Share a remix</h3><p>Show what your change does. Others print it.</p></li></ol>' +
      '<section class="featured" aria-labelledby="fr-h"><h2 id="fr-h">Featured remixes</h2><ul class="fr-grid"><li class="fr-slot"><strong>Your remix here.</strong><span>The best remixes get a spot on this shelf, with your name on it.</span><a href="#open-files">The open files</a></li>' +
      '<li class="fr-slot"><strong>A new knob?</strong><span>A grip, a strap lug, a lens hood. Change it, print it, test it.</span><a href="#makers" data-makers>Maker lessons</a></li>' +
      '<li class="fr-slot"><strong>A new colourway?</strong><span>Print the front plate and knobs in your colours.</span><a href="#files">The files</a></li></ul></section>';
  }
  function buildsHead() {
    return '<div class="pagehead"><h1>Show us <span class="hl">yours.</span></h1>' +
      '<p class="lead">Built one? Post it. Changed the files? Post the remix. What went well, what didn\'t, what you\'d change.</p></div>' + buildLoop();
  }
  pages.builds = function () {
    if (!inClaude()) return '<div class="wrap builds">' + buildsHead() +
      '<div class="builds-soon"><div><h2>Send us yours.</h2><p>Email a photo to ' + mailLink(MAIL.hello) + ' or tag <strong>#curve35</strong>. Your camera, your remix, your first roll: say which, and the name to show with it.</p>' +
      '<p class="path-links"><a class="btn main" href="' + esc(mailto(MAIL.hello, "My CURVE 35 build", "Hello,\n\nHere is my CURVE 35 (photo attached).\n\nIt's a: build / remix / first roll\nName to show with it (first name or a nickname):\nWhat I did:\n")) + '">Email a photo</a><a class="btn" href="#build">Build one</a></p></div>' +
      '<div class="soon-pic">' + img(PIC.hero, "The CURVE 35 camera: a black body, an orange front plate with a round lens, a red knob and a green knob on top", ' width="1200" height="900"') + "</div></div>" + buildIdeas() + "</div>";
    return '<div class="wrap builds">' + buildsHead() +
      '<div class="builds-grid"><section class="share" aria-labelledby="sh-h"><h2 id="sh-h">Share your build</h2>' +
      '<p class="nb" id="share-state" role="status">Connecting&hellip;</p>' +
      '<form id="share" novalidate hidden><fieldset class="kind"><legend>It\'s a</legend><label><input type="radio" name="kind" value="build" checked> Build</label><label><input type="radio" name="kind" value="remix"> Remix</label></fieldset>' +
      '<label for="s-title">Title</label><input id="s-title" name="title" maxlength="80" required placeholder="My first CURVE 35">' +
      '<label for="s-body">What you did</label><textarea id="s-body" name="body" maxlength="1200" rows="5" placeholder="Which colours, how long it took, your first roll, what you changed"></textarea>' +
      '<label for="s-link">A link to your pictures <span class="quiet">(optional, https)</span></label><input id="s-link" name="link" type="url" maxlength="300" placeholder="https://">' +
      '<label for="s-name">Your name <span class="quiet">(first name or a nickname)</span></label><input id="s-name" name="name" maxlength="40" autocomplete="nickname">' +
      '<p class="nb">No full names, school names or addresses. One post each; posting again replaces yours.</p>' +
      '<button class="btn main" type="submit">Post it</button><p class="msg" id="share-msg" role="status" aria-live="polite"></p></form></section>' +
      '<section class="gallery" aria-labelledby="gl-h"><h2 id="gl-h">The gallery</h2><p class="nb" id="gallery-state" role="status"></p><ul class="posts" id="posts"></ul></section></div>' + buildIdeas() + "</div>";
  };
  pages.builds.title = "Builds";
  pages.builds.wide = true;
  pages.builds.after = function () {
    $$(".ideas a[href='#makers']").forEach(function (a) { a.setAttribute("data-makers", ""); });
    if (!inClaude()) return;
    var state = $("#share-state"), form = $("#share"), gstate = $("#gallery-state"), postsEl = $("#posts"), alive = true, myUid = null;
    cleanup.push(function () { alive = false; });
    function empty(t) { postsEl.innerHTML = '<li class="post-empty"><p><strong>No builds yet.</strong> ' + esc(t) + "</p></li>"; }
    function draw(posts) {
      if (!posts.length) { empty("Build it, shoot a roll, post it here."); return; }
      postsEl.innerHTML = posts.map(function (p) { return postCard(p, myUid && p.uid === myUid); }).join("");
    }
    var cm = window.CURVE_COMMUNITY && window.CURVE_COMMUNITY.community;
    if (!cm) { state.textContent = "Posting isn't available in this view."; empty("When posting is on, builds show up here."); return; }
    cm().then(function (c) {
      if (!alive) return;
      if (!c) { state.textContent = "Posting isn't available in this view."; empty("When posting is on, builds show up here."); return; }
      myUid = c.uid;
      gstate.textContent = "Loading the gallery…";
      var unsub = c.watch(function (posts) { if (!alive) return; gstate.textContent = posts.length ? posts.length + (posts.length === 1 ? " post" : " posts") : ""; draw(posts); },
        function (err) { if (!alive) return; gstate.textContent = (err && err.code) === "unavailable" ? "The gallery isn't answering right now. Try again in a bit." : "The gallery couldn't load (" + ((err && err.code) || "error") + ")."; if (!postsEl.children.length) empty("The gallery will show here when it loads."); });
      cleanup.push(unsub);
      if (!c.uid) { state.textContent = "You can look, but posting is off for you here."; return; }
      form.hidden = false; state.textContent = "Posts are public to everyone who opens this page.";
      c.mine().then(function (m) { if (!m || !alive) return; $("#s-title").value = m.title; $("#s-body").value = m.body; $("#s-link").value = m.link; $("#s-name").value = m.name; var r = form.querySelector('input[value="' + m.kind + '"]'); if (r) r.checked = true; });
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var msg = $("#share-msg"), title = $("#s-title").value.trim(), link = $("#s-link").value.trim();
        if (!title) { msg.textContent = "Give it a title first."; $("#s-title").focus(); return; }
        if (link && !/^https:\/\/\S+$/i.test(link)) { msg.textContent = "Links need to start with https://"; $("#s-link").focus(); return; }
        var btn = form.querySelector("button[type=submit]"); btn.disabled = true; msg.textContent = "Posting…";
        c.post({ title: title, body: $("#s-body").value, link: link, name: $("#s-name").value, kind: (form.querySelector('input[name="kind"]:checked') || {}).value })
          .then(function () { msg.textContent = "Posted. It's in the gallery."; announce("Posted."); },
            function (err) {
              var code = err && err.code;
              if (code === "invalid_argument" || code === "revoked") { msg.textContent = "Posting is off for you here. You can still look."; $$("input, textarea, button", form).forEach(function (x) { x.disabled = true; }); }
              else if (code === "resource_exhausted" || code === "quota_exceeded") msg.textContent = "Too many posts right now. Try again later.";
              else msg.textContent = "That didn't post. Try again in a bit.";
            }).then(function () { if (!btn.closest("form").querySelector("input:disabled")) btn.disabled = false; });
      });
    });
  };

  // ---- store: three price cards, a short list of extras, one last call
  var SVG_SCAN = '<svg viewBox="0 0 48 36" aria-hidden="true"><rect x="2" y="4" width="44" height="28" rx="2" fill="#2B2724"/><g fill="#C9A06B"><rect x="7" y="10" width="10" height="16"/><rect x="19" y="10" width="10" height="16"/><rect x="31" y="10" width="10" height="16"/></g><g fill="#fff"><rect x="6" y="5.5" width="3" height="2"/><rect x="14" y="5.5" width="3" height="2"/><rect x="22" y="5.5" width="3" height="2"/><rect x="30" y="5.5" width="3" height="2"/><rect x="38" y="5.5" width="3" height="2"/><rect x="6" y="28.5" width="3" height="2"/><rect x="14" y="28.5" width="3" height="2"/><rect x="22" y="28.5" width="3" height="2"/><rect x="30" y="28.5" width="3" height="2"/><rect x="38" y="28.5" width="3" height="2"/></g></svg>';
  var SVG_CODE = '<svg viewBox="0 0 48 36" aria-hidden="true"><rect x="3" y="3" width="42" height="30" rx="3" fill="#fff" stroke="#17140F" stroke-width="2"/><path d="M17 12l-6 6 6 6M31 12l6 6-6 6" fill="none" stroke="#E8641B" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var SVG_STK = '<svg viewBox="0 0 48 36" aria-hidden="true"><rect x="6" y="3" width="36" height="30" rx="3" fill="#fff" stroke="#17140F" stroke-width="2"/><circle cx="16" cy="13" r="5" fill="#FFD23F" stroke="#17140F" stroke-width="1.5"/><rect x="25" y="9" width="12" height="8" rx="2" fill="#5AA9FF" stroke="#17140F" stroke-width="1.5"/><path d="M11 27l5-7 5 7z" fill="#5BD17A" stroke="#17140F" stroke-width="1.5"/><rect x="25" y="21" width="12" height="7" rx="3.5" fill="#FF8A3D" stroke="#17140F" stroke-width="1.5"/></svg>';
  // v10: a roll of film and a developing code, drawn the same way, set side by side as many times as the pack holds
  var ROLL_G = '<g><rect x="3" y="7" width="22" height="30" rx="4" fill="#E0A419" stroke="#17140F" stroke-width="2"/><rect x="3" y="14" width="22" height="16" fill="#FFD23F" stroke="#17140F" stroke-width="2"/><rect x="9" y="2" width="10" height="6" rx="1.5" fill="#3A3632" stroke="#17140F" stroke-width="2"/><path d="M25 18h9v9h-9" fill="#C9A06B" stroke="#17140F" stroke-width="2"/><text x="14" y="25.5" font-family="Inter,sans-serif" font-size="7.5" font-weight="800" text-anchor="middle" fill="#17140F">400</text></g>';
  var CODE_G = '<g><rect x="2" y="6" width="34" height="28" rx="3" fill="#fff" stroke="#17140F" stroke-width="2"/><g fill="#17140F"><rect x="6" y="10" width="7" height="7"/><rect x="25" y="10" width="7" height="7"/><rect x="6" y="23" width="7" height="7"/><rect x="16" y="11" width="3" height="3"/><rect x="20" y="15" width="3" height="3"/><rect x="16" y="19" width="3" height="3"/><rect x="25" y="21" width="3" height="3"/><rect x="21" y="25" width="3" height="3"/><rect x="28" y="26" width="3" height="3"/></g><path d="M11 39h16" stroke="#E8641B" stroke-width="3" stroke-linecap="round"/></g>';
  function packSvg(rolls, codes) {      // a pack of several: a little stack, each one a step up and to the right
    var parts = [], x = 0, top = (rolls > 1 || codes > 1) ? 8 : 0;
    function put(g, n, step) { var grp = []; for (var i = 0; i < n; i++) grp.push('<g transform="translate(' + (x + i * step) + "," + (top - i * 4) + ')">' + g + "</g>"); parts = parts.concat(grp.reverse()); x += (n - 1) * step; }
    if (rolls) { put(ROLL_G, rolls, 12); x += 40; }
    if (codes) { put(CODE_G, codes, 12); x += 40; }
    return '<svg class="pack" viewBox="-2 -2 ' + (x + 2) + " " + (46 + top) + '" aria-hidden="true">' + parts.join("") + "</svg>";
  }
  function thumb(src, svg) { return '<span class="th" aria-hidden="true">' + (svg || img(src, "", ' width="96" height="72"')) + "</span>"; }
  function inside(rows) { return '<ul class="pc-list">' + rows.map(function (r) { return "<li>" + thumb(r[0], r[1]) + "<span>" + esc(r[2]) + "</span></li>"; }).join("") + "</ul>"; }
  // the extras, as small coloured cards: picture, name, what is inside, where it is used (the build step and the lesson), price, one button
  var FILM_X = [["film-and-developing", null, packSvg(1, 1), "A roll of colour film and developing for it"],
    ["three-rolls-three-codes", null, packSvg(3, 3), "Three rolls, three developings"],
    ["film-roll", null, packSvg(1, 0), "One roll of colour film, ISO 400, 24 pictures"],
    ["developing-code", null, packSvg(0, 1), "Developing and scans for one roll, by email"]];
  var PART_X = [["pinhole-discs", "media/img/part_pinring.webp", null, "The pinhole experiment: lens out, disc and ring in. One set comes in every kit.", "h2", 1],
    ["swap-pack", "media/img/part_front.webp", null, "A front plate and two knobs in new colours", "b5", 4],
    ["spares-pack", "media/img/part_blade.webp", null, "A shutter and a wind knob", "b5", 5],
    ["lenses-three", PIC.lens, null, "Three lenses in a bag", "b10", 2],
    ["sticker-sheet", null, SVG_STK, "A name label, which-dot stickers and shapes in the kit's colours", "p1", 4]];
  pages.store = function () {
    var S = PROD["starter-kit"], K = PROD["camera-kit"], SHOWN = { "starter-kit": 1, "camera-kit": 1, "the-files": 1 };
    FILM_X.concat(PART_X).forEach(function (e) { if (PROD[e[0]]) SHOWN[e[0]] = 1; });
    var faq = [
      ["Is it hard to build?", "No. Ten steps, no tools. Each step has a short film and a check. The firmest push is about 5 newtons: one thumb."],
      ["Do I need a 3D printer?", "No. The kits come printed. Have a printer? The files are free."],
      ["Where does the film get developed?", "The starter kit includes developing and scans for one roll, sent by email. Any lab that develops 35 mm film can do it too."],
      ["What age is it for?", "14 and up. Younger builders can build it with an adult."],
      ["Can I use it in a class?", "Yes. Every lesson has a 50-minute plan and slides, free. Class sets of 8, 16 or 24 kits: see Programs, or email " + MAIL.schools + " for a quote."]
    ];
    function box(pic, svg, a, b) { return "<li>" + thumb(pic, svg) + "<span><strong>" + esc(a) + "</strong>" + esc(b) + "</span></li>"; }
    // a compact row: picture, name and one line, price, one button
    function xrow2(e) {
      var p = PROD[e[0]]; if (!p) return "";
      var inKit = e[0] === "pinhole-discs";
      return '<li class="srow" id="p-' + esc(e[0]) + '" tabindex="-1"><span class="sr-pic" aria-hidden="true">' + (e[2] || img(e[1], "", ' width="520" height="390"')) + '</span><span class="sr-t"><strong>' + esc(inKit ? "Pinhole set" : p.name) + "</strong><span>" + esc(e[3]) + '</span></span><span class="sr-buy">' + (inKit ? '<span class="xc-in">In every kit</span>' : '<span class="tnum">' + price(p) + "</span>" + addBtn(p, "small", "Add")) + "</span></li>";
    }
    return '<div class="store"><section class="store-plate" aria-labelledby="sp-h1"><div class="wrap"><div class="pagehead"><h1 id="sp-h1">Buy the kit</h1></div>' +
      (S ? '<section class="kstar" id="p-starter-kit" tabindex="-1" aria-labelledby="ks-h"><div class="ks-pic"><div class="frame">' + img(PIC.plan_parts, "Everything in the starter kit laid out: black body, grey back, orange front plate, teal shutter, yellow wheel, red spool, green knob, blue frame wheel, lens, pinhole ring and disc, and a roll of film", ' width="1200" height="900"') + "</div>" +
        '<span class="ks-stk">' + stk("Real film", "o") + "</span></div>" +
        '<div class="ks-t"><h2 id="ks-h">The starter kit</h2><p class="pc-sub">The camera, a roll of film and the developing. Everything for your first roll.</p>' +
        '<ul class="ks-in">' + box(PIC.hero, null, "9 pieces to build", "+ 2 spares") + box(PIC.cassette, null, "1 roll of colour film", "ISO 400, 24 pictures") + box(null, SVG_SCAN, "Developing and scans", "for that roll, by email") + box("media/img/part_pinring.webp", null, "Pinhole set", "ring and disc, for lesson 1") + "</ul>" +
        '<p class="kc-buy"><span class="pc-price tnum">' + price(S) + "</span>" + addBtn(S, "main big") + "</p></div></section>" : "") +
      (K ? '<section class="kcam" id="p-camera-kit" tabindex="-1" aria-labelledby="kc-h"><div class="kcam-pic">' + img(PIC.hero_back, "The camera from the back", ' width="1000" height="750"') + '</div><div class="kcam-t"><h2 id="kc-h">Camera kit</h2><p>Got film? The same camera, pinhole set and guide, without the roll and the developing.</p></div>' +
        '<p class="kc-buy"><span class="pc-price tnum">' + price(K) + "</span>" + addBtn(K, "main") + "</p></section>" : "") + "</div></section>" +
      '<div class="wrap"><section class="extras" id="p-extras" tabindex="-1" aria-labelledby="ex-h"><h2 id="ex-h">Film and developing</h2><ul class="srows">' + FILM_X.map(xrow2).join("") + "</ul>" +
      '<h2 class="ex2">Spares and extras</h2><ul class="srows">' + PART_X.map(xrow2).join("") + "</ul></section>" +
      priceList(SHOWN) +
      '<section class="faq" aria-labelledby="faq-h"><h2 id="faq-h">Questions</h2>' + faq.map(function (q) { return "<details><summary>" + esc(q[0]) + "</summary><p>" + esc(q[1]) + "</p></details>"; }).join("") + "</section>" +
      '<ul class="store-more"><li><a href="#files">Have a printer? The files are free &rarr;</a></li><li><a href="#programs">Classes and shops: programs and wholesale &rarr;</a></li></ul>' +
      '<p class="after-line">Questions about an order? ' + mailLink(MAIL.support) + '.</p></div>' +
      (S ? '<section class="final" aria-labelledby="sf-h"><div class="wrap final-in"><div><h2 id="sf-h">Build a camera this week.</h2><p class="final-price">' + price(S) + '</p></div><ul class="final-list"><li>Starter kit: camera, film, developing</li><li>One afternoon to build</li><li>Nine lessons, free</li></ul><div class="final-act">' + addBtn(S, "ink big") + "</div></div></section>" : "") + "</div>";
  };
  pages.store.title = "Buy the kit";
  pages.store.wide = true;
  pages.store.after = addButtons;

  function notFound(h) { return '<div class="page"><h1>Nothing here.</h1><p class="lead">There is no page called "' + esc(h) + '".</p><p><a class="btn main" href="#home">Home</a></p></div>'; }

  // links that go to a part of another page
  var pendingFocus = null;
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-makers],[data-extras],[data-focus]"); if (!a) return;
    var id = a.hasAttribute("data-makers") ? "makers" : a.getAttribute("data-focus") || "p-extras", pg = id === "makers" ? "files" : /^pg-/.test(id) ? "programs" : "store";
    if (current === pg) { e.preventDefault(); goTo(id, true); return; }
    pendingFocus = id;
  });

  // ------------------------------------------------------------------ router
  var ALIAS = { basket: "store", light: "build-p1", "open-source": "opensource", "open-files": "opensource", open: "opensource", license: "licence", opensrc: "opensource", github: "opensource", program: "programs", schools: "programs", homeschool: "programs", "": "home", community: "builds", gallery: "builds", kit: "store", teach: "teachers", classes: "teachers", teacher: "teachers",
    "lesson-10": "lesson-8", "lesson-11": "lesson-8", "lesson-12": "maker-3", m1: "maker-1", m2: "maker-2", m3: "maker-3", m4: "maker-4" };
  function render() {
    var h = decodeURIComponent(location.hash.replace(/^#/, "")), m, html, after, title, nav, focusId = null, raw = h || "home", wide = false, L = null, section = null;
    if (h === "basket") setTimeout(openBasket, 0);
    var teach = false;
    if ((m = h.match(/^teach-(\d+)$/))) { if (ROUTE["lesson-" + m[1]]) { teach = true; teacherMode(true); h = "lesson-" + m[1]; } else h = "teachers"; }
    if (ALIAS.hasOwnProperty(h)) h = ALIAS[h];
    nav = h;
    closeMenu();
    if ((m = h.match(/^(lesson|maker)-(\d+)(?:-(.+))?$/)) && ROUTE[m[1] + "-" + m[2]]) {
      L = ROUTE[m[1] + "-" + m[2]]; section = m[3] || null;
      if (current === L.route && section) return;      // a part of the lesson already open: the renderer moves to it
      h = teach ? "teach-" + L.num : L.route;
    }
    if (h === "makers") { h = "files"; focusId = "makers"; if (current === "files") { goTo("makers", true); return; } }
    if ((m = h.match(/^build-([a-z]\d+|film)$/)) && (m[1] === "film" || GS[m[1]])) {
      nav = "build";
      if (m[1] === "film") { focusId = "step-film"; if (current === "build" && document.getElementById(focusId)) { goTo(focusId, true); return; } }
      else { if (current === "build" && document.getElementById("stepper")) { buildGo(m[1], true); return; } BUILD_AT = m[1]; focusId = "stepper"; }
      h = "build";
    }
    if (h === "build") nav = "build";
    var X = [[/^glossary-([a-z0-9-]+)$/, "glossary", function (k) { return GT[k] && "term-" + k; }], [/^fact-([a-z0-9-]+)$/, "facts", function (k) { return FACT_BY_RID[k] && "f-" + k; }],
             [/^check-([a-z0-9-]+)$/, "facts", function (k) { return CHECK_BY_RID[k] && "c-" + k; }], [/^program-([a-z0-9-]+)$/, "programs", function (k) { return GPG[k] && "pg-" + k; }],
             [/^offer-([a-z0-9-]+)$/, null, function (k) { return GO[k] && "p-" + k; }], [/^(wholesale)$/, "programs", function () { return "wholesale"; }], [/^(parts-table)$/, "parts", function () { return "ptable"; }], [/^(licence)$/, "opensource", function () { return "licence"; }]];
    for (var xi = 0; xi < X.length; xi++) {
      var xm = h.match(X[xi][0]), xid = xm && X[xi][2](xm[1]);
      if (!xid) continue;
      var pg = X[xi][1] || (GO[xm[1]].home === "programs" ? "programs" : "store");
      nav = pg; focusId = xid;
      if (current === pg && document.getElementById(xid)) { goTo(xid, true); return; }
      h = pg; break;
    }
    if (h === "final-roll") { nav = "lessons"; focusId = "final-roll"; if (current === "lessons") { goTo(focusId, true); return; } h = "lessons"; }
    if (h === "contact") { nav = "help"; focusId = "contact"; if (current === "help") { goTo(focusId, true); return; } h = "help"; }
    if (h === "spares") { nav = "store"; focusId = "p-extras"; if (current === "store") { goTo(focusId, true); return; } h = "store"; }
    if ((m = h.match(/^part-([a-z-]+)$/)) && (PART[m[1]] || GPK[m[1]])) {
      nav = "parts"; focusId = "part-" + m[1];
      if (current === "parts") { goTo(focusId, true); return; }
      h = "parts";
    }
    cleanup.forEach(function (f) { try { f(); } catch (e) { /* gone */ } }); cleanup = [];
    if (L) {
      html = lessonShell(L); after = function () { lessonAfter(L, section, teach); };
      if (teach) title = "Teacher view, " + lessonName(L).toLowerCase() + ": " + L.title;
      title = title || lessonName(L) + ": " + L.title; nav = L.shelf === "maker" ? "files" : "lessons";
      var S = seen(); S[L.id] = 1; store(SEEN_KEY, S);
    }
    else if (pages[h]) { html = pages[h](); after = pages[h].after; title = pages[h].title; wide = !!pages[h].wide; }
    else { html = notFound(raw); title = "No page here"; nav = ""; }
    if (pendingFocus && (h === "files" || h === "store" || h === "programs")) focusId = pendingFocus;
    pendingFocus = null;
    current = h;
    view.className = (wide || L ? "is-wide" : "") + " route-" + (L ? "lesson" : h.replace(/[^a-z0-9-]/g, ""));
    view.innerHTML = html + (L || h === "build" ? relatedBlock(relatedFor(h, L)) : "");
    document.title = (title ? title + ": " : "") + "CURVE 35";
    $$(".nav a, #nav-more a").forEach(function (a) { if (a.dataset.nav === nav) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    if (after) after();
    countBasket();
    if (focusId && document.getElementById(focusId)) goTo(focusId);
    else { window.scrollTo(0, 0); var h1 = $("h1", view); if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); } }
  }
  function goTo(id, smooth) {
    var el = document.getElementById(id); if (!el) return;
    $$(".here").forEach(function (s) { s.classList.remove("here"); }); if (el.classList.contains("step") || /^(part|term|f|c|p|pg)-/.test(id)) el.classList.add("here");
    var dd = el.closest && el.closest("details"); if (dd) dd.open = true;
    el.focus({ preventScroll: true });
    el.scrollIntoView({ behavior: reduced() || !smooth ? "auto" : "smooth", block: /^(part|term|f|p)-/.test(id) ? "center" : "start" });
  }
  // back from Stripe with a paid order: empty the basket, and take the marker out of the address so a reload does not do it again
  if (/[?&]paid=1(&|$)/.test(location.search) && location.hash === "#thanks") {
    saveBasket({});
    try { history.replaceState(null, "", location.pathname + "#thanks"); } catch (e) { /* an old browser keeps ?paid=1 in the address: harmless */ }
  }
  window.addEventListener("hashchange", render);
  $(".skip").addEventListener("click", function (e) { e.preventDefault(); view.focus(); view.scrollIntoView(); });
  window.addEventListener("storage", function (e) { if (e.key === KEY) { countBasket(); if (dlg.open) drawBasket(); } });
  render();
})();
