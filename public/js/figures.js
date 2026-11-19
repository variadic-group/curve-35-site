/* CURVE 35: one clean figure for each lesson, drawn from that lesson's own numbers (course/out/lNN/lesson.json, course/FACTS.md).
   Large type, few labels: they must read when the figure is a quarter of the page wide.
   Ink and paper come from the page's CSS variables; orange marks the thing the lesson is about. */
(function () {
  "use strict";
  var W = 360, H = 220;
  function svg(title, body) {
    return '<svg class="lf" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + title.replace(/"/g, "&quot;") + '" xmlns="http://www.w3.org/2000/svg">' + body + "</svg>";
  }
  function t(x, y, s, cls, anchor) { return '<text x="' + x + '" y="' + y + '"' + (cls ? ' class="' + cls + '"' : "") + (anchor ? ' text-anchor="' + anchor + '"' : "") + ">" + s + "</text>"; }
  function l(x1, y1, x2, y2, cls) { return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '"' + (cls ? ' class="' + cls + '"' : "") + "/>"; }
  function rect(x, y, w, h, cls, rx) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '"' + (rx ? ' rx="' + rx + '"' : "") + ' class="' + cls + '"/>'; }
  function tree(x, base, h, flip) {   // a small tree standing on base (flip: hanging upside down from base)
    var s = flip ? -1 : 1, top = base - s * h, mid = base - s * h * 0.3, w = h * 0.34;
    return '<path class="acc-fill" d="M' + x + " " + top + " L" + (x - w) + " " + mid + " L" + (x + w) + " " + mid + 'Z"/>' + l(x, mid, x, base, "thick");
  }
  var F = {};

  F[1] = function () {   // a hole: rays cross, the picture lands upside down
    var hx = 200, hy = 118, bx = 300, x0 = 46, top = 58, bot = 178;
    var yTop = hy + (hy - top) * (bx - hx) / (hx - x0), yBot = hy - (bot - hy) * (bx - hx) / (hx - x0);
    return svg("A tree, a pinhole and a box. Rays from the top and the bottom of the tree cross at the 0.24 mm hole and land upside down on the back of the box, 28.9 mm away. The hole is f/120.",
      tree(x0, bot, bot - top) + rect(hx, 78, bx - hx, 80, "box") + l(hx, 78, hx, hy - 3, "wall") + l(hx, hy + 3, hx, 158, "wall") +
      l(x0, top, bx, yTop, "ray") + l(x0, bot, bx, yBot, "ray") + tree(bx - 26, yBot, yTop - yBot, true) +
      t(hx, 62, "0.24 mm", "lab", "middle") + t(356, 34, "f/120", "big acc", "end") + t((hx + bx) / 2, 196, "28.9 mm", "lab", "middle"));
  };

  F[2] = function () {   // a lens: a fan of rays from one point to one point on curved film
    var b = '<circle cx="30" cy="118" r="6" class="acc-fill"/>';
    [-36, -18, 0, 18, 36].forEach(function (d) { b += l(30, 118, 196, 118 + d, "ray") + l(196, 118 + d, 286, 118, "ray"); });
    b += '<ellipse cx="196" cy="118" rx="9" ry="46" class="lens"/><path d="M296 58 A 92 92 0 0 1 296 178" class="film"/><circle cx="287" cy="118" r="5" class="acc-fill"/>' +
      t(20, 36, "f/9.5", "big") + t(196, 52, "lens", "lab", "middle") + t(20, 208, "150× a pinhole's light", "lab acc");
    return svg("A point of light sends a fan of rays into the lens, which bends them all to one point on the curved film. At f/9.5 the lens lets in about 150 times the light of lesson 1's pinhole.", b);
  };

  F[3] = function () {   // what the film forgives: one step too little, three too much
    var x0 = 30, step = 50, y = 124, b = rect(x0 + step, y - 30, step * 4, 60, "band", 4) + l(x0, y, x0 + step * 6, y, "thick");
    for (var i = 0; i <= 6; i++) b += l(x0 + step * i, y - 9, x0 + step * i, y + 9, "thick");
    b += t(x0 + step, y + 44, "½×", "lab", "middle") + t(x0 + step * 2, y + 44, "1×", "lab strong", "middle") + t(x0 + step * 5, y + 44, "8×", "lab", "middle");
    b += t(x0 + step * 3, 74, "still a picture", "lab acc", "middle") + t(x0 + step * 3, 208, "the light", "lab", "middle");
    return svg("A scale of light. Colour negative film still makes a picture from half the right light to eight times it: one step too little, three steps too much.", b);
  };

  F[4] = function () {   // the three dots, to scale
    var s = 19, b = "", xs = [64, 180, 296], d = [1.96, 2.88, 3.34], f = ["f/16", "f/11", "f/9.5"];
    xs.forEach(function (x, i) { b += '<circle cx="' + x + '" cy="98" r="' + (d[i] * s / 2) + '" class="dot"/>' + t(x, 166, f[i], "big", "middle") + t(x, 196, d[i] + " mm", "lab", "middle"); });
    b += t(122, 40, "×2.16", "lab acc", "middle") + t(238, 40, "×1.35", "lab acc", "middle");
    return svg("The three holes in the wheel, to scale: 1.96 mm is f/16, 2.88 mm is f/11, 3.34 mm is f/9.5. Small to middle lets in 2.16 times the light; middle to large 1.35 times.", b);
  };

  F[5] = function () {   // a quick click against a slow push
    var x0 = 24, full = 312, w = full / 11.5;
    return svg("How long the shutter is open. With its click: about 1/322 of a second. Pushed slowly with no click: about 1/28 of a second, 11.5 times as long.",
      t(x0, 46, "a quick click", "lab") + rect(x0, 58, w, 34, "acc-fill") + t(x0 + w + 12, 84, "1/322 s", "big") +
      t(x0, 140, "a slow push", "lab") + rect(x0, 152, full, 34, "grey-fill") + t(x0 + full - 10, 177, "1/28 s", "big", "end"));
  };

  F[6] = function () {   // the film's holes: 8 holes is one picture
    var x0 = 34, p = 36, y = 70, b = rect(6, y, 348, 116, "filmstrip");
    for (var i = 0; i < 9; i++) b += rect(x0 + i * p - 8, y + 9, 16, 14, "hole", 2) + rect(x0 + i * p - 8, y + 93, 16, 14, "hole", 2);
    b += rect(x0 - 8, y + 30, 8 * p - 10, 56, "frame") + t(x0 + 4 * p - 13, y + 66, "36 × 24 mm", "lab ink", "middle");
    b += l(x0, 50, x0 + 8 * p, 50, "dim") + l(x0, 43, x0, 57, "dim") + l(x0 + 8 * p, 43, x0 + 8 * p, 57, "dim") + t(x0 + 4 * p, 36, "8 holes = 38 mm", "lab acc", "middle");
    return svg("A strip of 35 mm film with its holes 4.75 mm apart. Eight holes make 38 mm: one 36 by 24 mm picture and the gap after it. The frame wheel has eight teeth, so it turns once for each picture.", b);
  };

  F[7] = function () {   // a light trap: each bounce keeps most of the light out
    var b = '<path d="M14 54 H204 V128 H346" class="trapwall"/><path d="M14 100 H158 V174 H346" class="trapwall"/>';
    b += '<polyline points="14,77 181,77 181,151 346,151" class="acc-stroke"/>';
    b += t(14, 36, "light", "lab") + t(220, 92, "0.3", "big") + t(346, 112, "0.09", "big acc", "end") + t(346, 206, "two corners", "lab", "end");
    return svg("A ray of light trying to get in through a gap with two corners. At each corner it has to bounce, and each bounce sends back at most 0.3 of it: 0.3 after one corner, 0.09 after two.", b);
  };

  F[8] = function () {   // lines of plastic, layer on layer
    var b = "", rows = 5, cols = 6, w = 44, h = 22, x0 = 20, y0 = 64;
    for (var r = 0; r < rows; r++) for (var c = 0; c < cols; c++) b += rect(x0 + c * w + (r % 2 ? 0 : 0), y0 + r * h, w - 3, h - 3, r === 2 ? "acc-fill" : "bead", 10);
    b += t(x0 + cols * w + 8, y0 + 2 * h + 16, "0.2 mm", "lab");
    b += t(x0, 44, "one line: 0.45 mm", "lab") + t(x0, 208, "the body: 164 layers", "lab");
    return svg("A cut through printed plastic: rows of flattened lines, each about 0.45 mm wide, stacked in layers 0.2 mm tall. The body is 164 layers.", b);
  };

  F[9] = function () {   // how hard each click is
    var x0 = 132, s = 30, b = "", rows = [["back", 0.6, 0.6], ["rocker", 2.3, 2.3], ["dot", 2.4, 2.4], ["front plate", 3, 5]];
    rows.forEach(function (r, i) {
      var y = 26 + i * 46;
      b += t(x0 - 12, y + 22, r[0], "lab", "end") + rect(x0, y, r[1] * s, 30, i === 3 ? "acc-fill" : "grey-fill");
      if (r[2] > r[1]) b += rect(x0 + r[1] * s, y, (r[2] - r[1]) * s, 30, "acc-fill light");
      b += t(x0 + r[2] * s + 8, y + 22, (r[2] > r[1] ? r[1] + "–" + r[2] : r[1]) + " N", "lab strong");
    });
    return svg("How hard each click is: the back about 0.6 newtons, the rocker 2.3, a dot 2.4, the front plate about 3 to 5, the hardest push in the build.", b);
  };

  F[10] = function () {   // the sight crosses the lens's line far away
    return svg("Side view of the sight. The pad at the back sits 30 mm above the lens's line; the point at the front is a little lower. The line through them crosses the lens's line about 2.8 m away.",
      l(14, 160, 346, 160, "thick") + t(14, 194, "the lens's line", "lab") +
      '<circle cx="34" cy="72" r="7" class="acc-fill"/><circle cx="92" cy="80" r="7" class="acc-fill"/>' + l(34, 72, 336, 160, "acc-stroke") +
      l(34, 80, 34, 160, "dim") + t(44, 126, "30 mm", "lab") + t(346, 128, "2.8 m", "big", "end"));
  };

  F[11] = function () {   // the picture is 0.75 × the distance tall
    return svg("Seen from the side, what the camera takes in widens from the lens. The picture is 0.75 times the distance tall, so a person 1.7 m tall fills it from about 2.3 m away.",
      '<path d="M24 118 L320 44 L320 192 Z" class="cone"/><circle cx="24" cy="118" r="6" class="acc-fill"/>' +
      '<circle cx="290" cy="64" r="12" class="person"/><path d="M290 76 V146 M290 146 L274 186 M290 146 L306 186 M290 96 L270 126 M290 96 L310 126" class="person-line"/>' +
      t(14, 32, "height = 0.75 × distance", "lab") + t(346, 214, "1.7 m tall, 2.3 m away", "lab", "end"));
  };

  F[12] = function () {   // which of five things is sharpest
    var d = [["1 m", 0.086], ["1.5", 0.049], ["2", 0.033], ["4 m", 0.023], ["far", 0.040]], x0 = 30, b = "", base = 172;
    d.forEach(function (r, i) {
      var h = r[1] * 1350, x = x0 + i * 64;
      b += rect(x, base - h, 42, h, i === 3 ? "acc-fill" : "grey-fill") + t(x + 21, base + 28, r[0], i === 3 ? "lab strong" : "lab", "middle");
    });
    b += l(20, base, 346, base, "thick") + t(346, 36, "4 m is sharpest", "lab acc", "end");
    return svg("Blur in the middle of the picture at the large dot, for things at 1, 1.5, 2 and 4 m and far away: 0.086, 0.049, 0.033, 0.023 and 0.040 mm. The thing 4 m away is the sharpest.", b);
  };

  window.FIG = function (n) { return F[n] ? F[n]() : ""; };
})();
