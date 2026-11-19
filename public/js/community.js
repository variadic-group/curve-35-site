/* CURVE 35: the Builds gallery's one link to shared storage.
   community() -> Promise of an adapter, or null when this view has no shared storage.

   Uses the page's "db" and "user" capabilities, as the lead declares them:
     capabilities: { downloads: true, db: { rules: [ {path: "builds", read: "view", write: "owner"}, {path: "builds/{self}", write: "interact"} ] }, user: {} }
   So each person writes ONE document, builds/<their uid> (their latest post, set whole), and everyone reads the "builds" collection.

   Adapter:
     a.uid                      the visitor's id, or null
     a.watch(next, fail)        -> unsubscribe().  next(posts, {fromCache}) with posts newest first (at most 60); fail(err) with err.code
     a.post(fields)             -> Promise.  Sets builds/<uid> to {name, title, body, link, kind, createdAt, uid}
     a.mine()                   -> Promise of the visitor's own post, or null
   Everything here is plain text from strangers: the page escapes it before showing it. No images: text and one optional link. */
(function () {
  "use strict";
  var LIMIT = 60;
  var P = null;

  function clip(s, n) { return String(s == null ? "" : s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").trim().slice(0, n); }
  function safeLink(u) {
    u = clip(u, 300);
    if (!u) return "";
    if (!/^https:\/\/[^\s<>"']+$/i.test(u)) return "";        // https only, no spaces or quotes
    return u;
  }
  function clean(d, id) {
    if (!d || typeof d !== "object") return null;
    var kind = d.kind === "remix" ? "remix" : "build";
    var t = Number(d.createdAt) || 0;
    var post = { id: String(id || d.uid || ""), name: clip(d.name, 40), title: clip(d.title, 80), body: clip(d.body, 1200), link: safeLink(d.link), kind: kind, createdAt: t, uid: clip(d.uid, 128) };
    return post.title || post.body ? post : null;
  }

  function community() {
    if (P) return P;
    P = (async function () {
      if (!window.claude || typeof window.claude.use !== "function") return null;
      var db = null, user = null, uid = null;
      try { db = await window.claude.use("db"); } catch (e) { db = null; }
      if (!db) return null;
      try { user = await window.claude.use("user"); uid = user && typeof user.id === "function" ? await user.id() : null; } catch (e) { uid = null; }

      // TODO(lead): these are the only db calls. Match them to the real API if it differs.
      function query() { return db.collection("builds").orderBy("createdAt", "desc").limit(LIMIT); }
      function myDoc() { return db.doc("builds/" + uid); }

      function snapPosts(snap) {
        var out = [];
        (snap && snap.docs || []).forEach(function (doc) {
          var d = typeof doc.data === "function" ? doc.data() : doc;
          var p = clean(d, doc.id); if (p) out.push(p);
        });
        out.sort(function (a, b) { return b.createdAt - a.createdAt; });
        return out;
      }

      return {
        uid: uid,
        watch: function (next, fail) {
          var done = false, unsub = null;
          var timer = setTimeout(function () { if (!done) { done = true; fail({ code: "unavailable", message: "no answer in 10 s" }); } }, 10000);
          try {
            // TODO(lead): onSnapshot(next, error); snap.metadata.fromCache as described.
            unsub = query().onSnapshot(function (snap) {
              var fromCache = !!(snap && snap.metadata && snap.metadata.fromCache);
              if (!fromCache && !done) { done = true; clearTimeout(timer); }
              next(snapPosts(snap), { fromCache: fromCache });
            }, function (err) {
              done = true; clearTimeout(timer); fail(err || { code: "unavailable" });
            });
          } catch (e) { done = true; clearTimeout(timer); fail(e); }
          return function () { clearTimeout(timer); try { if (typeof unsub === "function") unsub(); } catch (e) { /* gone */ } };
        },
        post: function (fields) {
          if (!uid) return Promise.reject({ code: "invalid_argument", message: "no visitor id" });
          var row = { name: clip(fields.name, 40), title: clip(fields.title, 80), body: clip(fields.body, 1200), link: safeLink(fields.link),
                      kind: fields.kind === "remix" ? "remix" : "build", createdAt: Date.now(), uid: uid };
          // TODO(lead): set the whole doc builds/<uid>.
          return Promise.resolve(myDoc().set(row)).then(function () { return row; });
        },
        mine: function () {
          if (!uid) return Promise.resolve(null);
          // TODO(lead): one read of builds/<uid>.
          return Promise.resolve(myDoc().get()).then(function (doc) {
            if (!doc) return null;
            if (doc.exists === false) return null;
            return clean(typeof doc.data === "function" ? doc.data() : doc, uid);
          }).catch(function () { return null; });
        }
      };
    })().catch(function () { return null; });
    return P;
  }
  window.CURVE_COMMUNITY = { community: community };
})();
