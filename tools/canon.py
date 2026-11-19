#!/usr/bin/env python3
"""The canon: CURVE 35's single source of truth (canon/*.yaml), loaded, checked and merged.

    python3 tools/canon.py            check every reference, print a summary, write canon/INDEX.md, build/canon.json, site/data/products.json
    python3 tools/canon.py --check    check only (exit 1 on a broken reference)

Generators import it:  import canon; C = canon.load()   (C["parts"], C["steps"], C["lessons"], C["facts"], C["checks"], C["glossary"],
C["offers"], C["company"], C["panels"], C["short_links"]; each list also as a dict by id: C["part"], C["step"], C["lesson"], C["fact"], C["check"]).
Text in the canon may name a fact as {fact_id} (its 'say') or {fact_id:field}; load() fills them in.  Nothing here writes outside
canon/INDEX.md, build/canon.json and site/data/products.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canon"
FILES = ("company", "parts", "steps", "lessons", "facts", "checks", "glossary", "offers")
WORDS_PER_S = 2.8            # the machine voice (tools/voice.py), measured on the step clips: about 2.8 spoken words a second
NARRATION_S = (20, 40)
TEMPLATE = re.compile(r"\{([a-z][a-z0-9_]*)(?::([a-z_]+))?\}")

def _yaml(name):
    import yaml
    return yaml.safe_load((CANON / f"{name}.yaml").read_text(encoding="utf-8"))

def raw():
    """The YAML as written, nothing filled in."""
    return {n: _yaml(n) for n in FILES}

def fact_text(f, field=None):
    if field and field != "say":
        v = f.get(field)
        if v is None: raise KeyError(f"fact {f['id']} has no field '{field}'")
        return str(v)
    if "say" in f: return str(f["say"])
    v = f["value"]; return (" x ".join(str(x) for x in v) if isinstance(v, list) else str(v)) + (f" {f['unit']}" if f.get("unit") else "")

def fill(v, facts, missing):
    """Every {fact_id} / {fact_id:field} in v, recursively, replaced by the fact's words."""
    if isinstance(v, str):
        def sub(m):
            f = facts.get(m.group(1))
            if f is None: missing.append(m.group(0)); return m.group(0)
            try: return fact_text(f, m.group(2))
            except KeyError as e: missing.append(str(e)); return m.group(0)
        return TEMPLATE.sub(sub, v)
    if isinstance(v, list): return [fill(x, facts, missing) for x in v]
    if isinstance(v, dict): return {k: fill(x, facts, missing) for k, x in v.items()}
    return v

def short_links(C):
    """curve35.com/<path> -> route, in a stable order: the company's links, with the build steps after 'build', the lessons after 'lessons', the other steps last."""
    out = {}
    build = {s["short"]: f"build-{s['id']}" for s in C["steps"] if s["section"] == "BUILD"}
    for path, route in C["company"]["short_links"].items():
        out[path] = route
        if path == "build": out.update(build)
        if path == "lessons": out.update({L["short"]: L["route"] for L in C["lessons"]})
    out.update({s["short"]: f"build-{s['id']}" for s in C["steps"] if s["short"] not in out})
    return out

_cache = None
def load(fresh=False):
    """The canon with every template filled in, plus dicts by id.  Raises ValueError if a template names a fact that does not exist."""
    global _cache
    if _cache is not None and not fresh: return _cache
    R = raw(); facts = {f["id"]: f for f in R["facts"]["facts"]}; missing = []
    C = {"company": fill(R["company"], facts, missing), "parts": R["parts"]["parts"], "guide_order": R["parts"]["guide_order"], "build_order": R["parts"]["build_order"],
         "sections": fill(R["steps"]["sections"], facts, missing), "steps": fill(R["steps"]["steps"], facts, missing), "trouble": fill(R["steps"]["trouble"], facts, missing),
         "lessons": fill(R["lessons"]["lessons"], facts, missing), "facts": R["facts"]["facts"], "panels": fill(R["facts"]["panels"], facts, missing),
         "checks": fill(R["checks"]["checks"], facts, missing), "glossary": fill(R["glossary"]["terms"], facts, missing), "offers": fill(R["offers"], facts, missing)}
    C["parts"] = fill(C["parts"], facts, missing)
    if missing: raise ValueError("unknown fact in a template: " + ", ".join(sorted(set(missing))))
    for k, one in (("parts", "part"), ("steps", "step"), ("lessons", "lesson"), ("facts", "fact"), ("checks", "check")): C[one] = {x["id"]: x for x in C[k]}
    C["product"] = {p["id"]: p for p in C["offers"]["products"]}
    C["short_links"] = short_links(C)
    _cache = C
    return C

def products_json(C):
    """site/data/products.json, as it has always looked (lesson numbers, not ids; no part lists)."""
    out = {"note": "Written by tools/canon.py from canon/offers.yaml: edit the canon, not this file. " + C["offers"]["store_note"], "currency": C["offers"]["currency"], "groups": C["offers"]["groups"], "products": []}
    for p in C["offers"]["products"]:
        q = {k: v for k, v in p.items() if k != "parts"}
        q["lessons"] = [int(L[1:]) for L in p["lessons"]]
        out["products"].append(q)
    return out

# ----------------------------------------------------------------------------------------------------------------------------- checking
def _json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def _get(d, path):
    for k in path:
        if isinstance(d, list): d = d[int(k)]
        else: d = d[str(k)]
    return d

def _decimals(v):
    s = repr(float(v)) if isinstance(v, float) else str(v)
    return len(s.split(".")[1]) if "." in s and isinstance(v, float) else 0

def _secs(t):
    return sum(int(n) * {"h": 3600, "m": 60, "s": 1}[u] for n, u in re.findall(r"(\d+)([hms])", t))

def derive(name, C):
    """The facts that are computed rather than read: each from the result files or from the canon itself."""
    build = [p for s in C["steps"] if s["section"] == "BUILD" for p in (s.get("parts") or {})]
    pieces = list(dict.fromkeys(build))
    printed = [p for p in pieces if C["part"][p]["kind"] == "printed"]
    F = lambda i: C["fact"][i]["value"]
    if name == "camera_pieces": return len(pieces)
    if name == "printed_pieces": return len(printed)
    if name == "slice_total_grams": s = _json("build/slicecheck.json"); return sum(s[p]["grams"] for p in printed)
    if name == "slice_total_hours": s = _json("build/slicecheck.json"); return sum(_secs(s[p]["time"]) for p in printed) / 3600
    if name == "holes_times_pitch": return F("holes_per_picture") * F("sprocket_pitch")
    if name == "double_of_time_counts_iso400": return [2 * x for x in F("time_counts_iso400")]
    if name == "double_of_time_counts_iso200": return [2 * x for x in F("time_counts_iso200")]
    if name == "pinhole_light_ratio": return (_json("build/pinhole.json")["f_number_kit_disc"] / _json("build/exposure.json")["printers"]["typical"]["stops"][2]["f_number"]) ** 2
    if name.startswith("light_"):
        O = _json("build/optics.json"); leak = [x for k, x in O.items() if isinstance(x, dict) and "escaped_confirmed" in x and k.startswith("leak: closed")]
        return {"light_cases": len(leak), "light_rays_million": sum(x["rays"] for x in leak) / 1e6, "light_rays_in": sum(x["escaped_confirmed"] for x in leak)}[name]
    if name == "fit_printers": return len([k for k in _json("build/tolerance.json") if k != "as drawn"])
    if name == "lessons_main": return sum(1 for L in C["lessons"] if L["shelf"] == "main")
    if name == "lessons_maker": return sum(1 for L in C["lessons"] if L["shelf"] == "maker")
    if name == "build_steps": return sum(1 for s in C["steps"] if s["section"] == "BUILD")
    if name == "pdf_pages":
        from pypdf import PdfReader
        return len(PdfReader(str(ROOT / "build/CURVE-35_kit_booklet.pdf")).pages)
    raise KeyError(f"no derivation called '{name}'")

def agrees(value, src, tol=None):
    if isinstance(value, list):
        return isinstance(src, list) and len(src) == len(value) and all(agrees(a, b, tol) for a, b in zip(value, src))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not isinstance(src, (int, float)): return False
        if tol is not None: return abs(src - value) <= tol
        return round(src, _decimals(value)) == value
    return str(value) == str(src) or str(value) in str(src)

def check_fact(f, C):
    """-> (state, message): 'ok', 'unchecked' or 'bad'."""
    src = f.get("source", "")
    if f.get("unchecked"): return "unchecked", f["unchecked"]
    try:
        if "derive" in f: got = derive(f["derive"], C)
        elif "path" in f: got = _get(_json(src), f["path"])
        elif "grep" in f:
            text = (ROOT / src).read_text(encoding="utf-8")
            miss = [g for g in f["grep"] if g not in text]
            return ("bad", f"{src} does not say: {miss}") if miss else ("ok", "")
        else: return "bad", "no way to check it (path, derive, grep or unchecked)"
    except Exception as e:
        return "bad", f"could not read it from {src}: {type(e).__name__} {e}"
    t = f.get("transform")
    if t == "reciprocal": got = 1.0 / got
    elif t == "number": m = re.search(r"-?\d+(?:\.\d+)?", str(got)); got = float(m.group(0)) if m else None
    elif t == "count": got = len(got)
    elif t: return "bad", f"unknown transform {t}"
    return ("ok", "") if agrees(f["value"], got, f.get("tol")) else ("bad", f"canon says {f['value']!r}, {src} gives {got!r}")

def validate(C):
    """Every id, file, link and number.  -> (errors, notes, fact states)."""
    E = []; N = []
    def need(ok, msg):
        if not ok: E.append(msg)
    def exists(rel, who):
        need(rel is None or (ROOT / rel).exists(), f"{who}: file {rel} is missing")
    for k in ("parts", "steps", "lessons", "facts", "checks"):
        ids = [x["id"] for x in C[k]]; dup = {i for i in ids if ids.count(i) > 1}
        need(not dup, f"{k}: id used twice: {sorted(dup)}")
    P, S, L, F, K = C["part"], C["step"], C["lesson"], C["fact"], C["check"]
    lesson_ids = set(L)
    # parts
    for p in C["parts"]:
        who = f"part {p['id']}"
        for f in ("name", "kind", "does"): need(p.get(f), f"{who}: no {f}")
        need(p["kind"] in ("printed", "bought", "optional", "gauge"), f"{who}: kind {p['kind']}")
        for s in p.get("steps") or []: need(s in S, f"{who}: step {s} does not exist")
        for l in p.get("lessons") or []: need(l in L, f"{who}: lesson {l} does not exist")
        for c in p.get("checks") or []: need(c in K, f"{who}: check {c} does not exist")
        for f in ("stl", "picture", "thumb"): exists(p.get(f), who)
        if p.get("print_time") is not None or p.get("grams") is not None:
            s = _json("build/slicecheck.json").get(p["id"])
            need(s is not None, f"{who}: has a print time but build/slicecheck.json has no '{p['id']}'")
            if s: need(s["time"] == p.get("print_time") and s["grams"] == p.get("grams"), f"{who}: print time/grams {p.get('print_time')}, {p.get('grams')} but the slicer says {s['time']}, {s['grams']}")
        elif p["kind"] == "printed": N.append(f"{who}: not sliced yet (no print time or grams in build/slicecheck.json)")
    for k in C["guide_order"] + C["build_order"]: need(k in P, f"parts guide_order/build_order: {k} does not exist")
    for p in C["parts"]:
        c = p.get("card")
        if c:
            need(c["lesson"] in (p.get("lessons") or []), f"part {p['id']}: its card's lesson {c['lesson']} is not among its lessons")
            need(c["goes_in"] in (p.get("steps") or []), f"part {p['id']}: its card's step {c['goes_in']} is not among its steps")
    # steps
    secs = {s["key"] for s in C["sections"]}
    for s in C["steps"]:
        who = f"step {s['id']}"
        for f in ("title", "action", "instruction", "check", "short", "lesson", "narration", "picture"): need(s.get(f), f"{who}: no {f}")
        need(s["section"] in secs, f"{who}: section {s['section']} is not in sections")
        need(s["id"] == next(x["letter"] for x in C["sections"] if x["key"] == s["section"]) + str(s["n"]), f"{who}: id does not match its section and number")
        for p in (s.get("parts") or {}):
            need(p in P, f"{who}: part {p} does not exist")
            if p in P: need(s["id"] in (P[p].get("steps") or []), f"{who}: shows part {p}, but part {p} does not list step {s['id']}")
        exists(s.get("picture"), who); exists(s.get("clip"), who)
        if s.get("lesson") in L: need(s["id"] in L[s["lesson"]]["steps"], f"{who}: lesson {s['lesson']} does not list it among its steps")
        else: E.append(f"{who}: lesson {s.get('lesson')} does not exist")
        sec = len(s.get("narration", "").split()) / WORDS_PER_S
        need(NARRATION_S[0] <= sec <= NARRATION_S[1], f"{who}: narration is about {sec:.0f} s spoken; it should be {NARRATION_S[0]} to {NARRATION_S[1]}")
    # lessons
    for l in C["lessons"]:
        who = f"lesson {l['id']}"
        for f in ("title", "question", "hook", "idea", "route", "short", "topic"): need(l.get(f), f"{who}: no {f}")
        for p in l["parts"]:
            need(p in P, f"{who}: part {p} does not exist")
            if p in P: need(l["id"] in (P[p].get("lessons") or []), f"{who}: explains part {p}, but part {p} does not list it")
        for s in l["steps"]: need(s in S, f"{who}: step {s} does not exist")
        for f in l["facts"]: need(f in F, f"{who}: fact {f} does not exist")
        exists(l.get("page"), who); exists(l.get("film_from"), who)
        if l.get("page") and (ROOT / l["page"]).exists():
            R = _json(l["page"]); rolls = [x for x in R.get("sections", []) if x.get("kind") == "roll"]
            need(bool(rolls) == bool(l.get("photo_challenge")), f"{who}: photo_challenge and the page's 'roll' section disagree about whether there is one")
    for p in C["parts"]:
        for l in p.get("lessons") or []:
            if l in L: need(p["id"] in L[l]["parts"], f"part {p['id']}: lists lesson {l}, but lesson {l} does not list the part")
    # facts
    states = {}
    for f in C["facts"]:
        for k in ("value", "unit", "sentence", "source"): need(k in f, f"fact {f['id']}: no {k}")
        st, msg = check_fact(f, C); states[f["id"]] = (st, msg)
        if st == "bad": E.append(f"fact {f['id']}: {msg}")
        if not (f.get("source", "").startswith("ISO") or f.get("unchecked")): exists(f.get("source"), f"fact {f['id']}")
        for g in f.get("used_by", []):
            need((ROOT / g).exists() and f["id"] in (ROOT / g).read_text(encoding="utf-8"), f"fact {f['id']}: used_by {g}, but {g} does not name it")
    # checks
    for c in C["checks"]:
        who = f"check {c['id']}"
        for f in c.get("tools", []) + c.get("results", []): exists(f, who)
        for f in c.get("facts", []): need(f in F, f"{who}: fact {f} does not exist")
        need(c.get("covers") == "all" or any(c["id"] in (p.get("checks") or []) for p in C["parts"]), f"{who}: no part names it (orphan)")
    # glossary
    for t in C["glossary"]:
        for l in t.get("taught", []): need(l in L, f"term {t['term']}: lesson {l} does not exist")
        for p in t.get("parts", []): need(p in P, f"term {t['term']}: part {p} does not exist")
        for s in t.get("steps", []): need(s in S, f"term {t['term']}: step {s} does not exist")
    # offers
    O = C["offers"]; groups = {g["key"] for g in O["groups"]}; prods = C["product"]; progs = {g["id"] for g in O["programs"]}
    ids = [p["id"] for p in O["products"]]; need(len(ids) == len(set(ids)), "offers: a product id is used twice")
    for p in O["products"]:
        who = f"product {p['id']}"
        need(p["group"] in groups, f"{who}: group {p['group']} does not exist")
        need(p.get("guide") in S, f"{who}: guide step {p.get('guide')} does not exist")
        for l in p["lessons"]: need(l in L, f"{who}: lesson {l} does not exist")
        for q in p.get("parts", []): need(q in P, f"{who}: part {q} does not exist")
        need("payment_link" in p, f"{who}: no payment_link field")
        if p.get("basket"): need(isinstance(p.get("price_usd"), (int, float)), f"{who}: in the basket but no single price")
        need(any(p["id"] in w.get("products", []) for w in O["ways"]), f"{who}: in none of the three ways (orphan)")
    for w in O["ways"]:
        for q in w.get("products", []): need(q in prods, f"way {w['id']}: product {q} does not exist")
        for g in w.get("programs", []): need(g in progs, f"way {w['id']}: program {g} does not exist")
        if w.get("contact"): need(w["contact"] in C["company"]["email"], f"way {w['id']}: contact {w['contact']} is not an email in company.yaml")
        need(C["short_links"].get(w.get("short")) in (w.get("route"), {"open": "open-files"}.get(w.get("short"))), f"way {w['id']}: short link /{w.get('short')} does not go to #{w.get('route')}")
    need(len(O["ways"]) == 3, "offers: there should be three ways to get it")
    # company, short links
    for c in C["company"]["contact"]: need(c["email"] in C["company"]["email"], f"company contact: {c['email']} is not an email")
    SL = C["short_links"]; routes = {}
    for s in C["steps"]: routes.setdefault(s["short"], []).append(f"step {s['id']}")
    for l in C["lessons"]: routes.setdefault(l["short"], []).append(f"lesson {l['id']}")
    for path, who in routes.items():
        need(len(who) == 1, f"short link /{path} is claimed by {who}")
        need(path not in C["company"]["short_links"], f"short link /{path} is in company.yaml and also a step's or lesson's")
    for path, route in SL.items(): need(re.fullmatch(r"[a-z0-9-]+", path) and re.fullmatch(r"[a-z0-9-]+", route), f"short link /{path} -> #{route}: not plain")
    qr = ROOT / "build/booklet/qr_paths.json"
    if qr.exists():
        for q in json.loads(qr.read_text()): need(q["path"] in SL, f"the printed guide's QR code /{q['path']} has no short link")
    # orphans
    for p in C["parts"]:
        used = p.get("steps") or p.get("lessons") or any(p["id"] in q.get("parts", []) for q in O["products"])
        need(bool(used), f"part {p['id']}: in no step, lesson or product (orphan)")
    text = json.dumps(raw(), ensure_ascii=False)
    used_f = {m.group(1) for m in TEMPLATE.finditer(text)} | {f for l in C["lessons"] for f in l["facts"]} | {f for c in C["checks"] for f in c.get("facts", [])} | {f["id"] for f in C["facts"] if f.get("used_by")}
    for f in C["facts"]: need(f["id"] in used_f, f"fact {f['id']}: no lesson, check or text uses it (orphan)")
    return E, N, states

# ----------------------------------------------------------------------------------------------------------------------------- writing
def index_md(C, states):
    P, S, L, F = C["part"], C["step"], C["lesson"], C["fact"]
    offers_of = lambda pid: [p for p in C["offers"]["products"] if pid in p.get("parts", [])]
    checks_of = lambda pid: [C["check"][c] for c in P[pid].get("checks") or []]
    out = ["# The canon, as a map", "",
           "Written by `tools/canon.py` from `canon/*.yaml`; do not edit by hand (edit the YAML and run `python3 tools/canon.py`).", "",
           f"{len(C['parts'])} parts, {len(C['steps'])} steps, {len(C['lessons'])} lessons, {len(C['facts'])} facts, {len(C['checks'])} checks, {len(C['glossary'])} terms, "
           f"{len(C['offers']['products'])} products in {len(C['offers']['ways'])} ways, {len(C['offers']['programs'])} programs, {len(C['short_links'])} short links.", "",
           "## Each part: steps, lessons, facts, checks, offers", ""]
    for p in C["parts"]:
        les = [L[l] for l in p.get("lessons") or []]
        facts = list(dict.fromkeys(f for l in les for f in l["facts"]))
        out += [f"### {p['name']} (`{p['id']}`, {p['kind']})", "", p["does"][0].upper() + p["does"][1:] + ".", ""]
        if p.get("print_time"): out.append(f"- **Print:** {p['print_time']}, {p['grams']} g, `{p['stl']}`")
        elif p.get("stl"): out.append(f"- **Print:** `{p['stl']}` (not sliced yet)")
        out.append("- **Steps:** " + (", ".join(f"[{s}](https://curve35.com/{S[s]['short']}) {S[s]['title']}" for s in p.get("steps") or []) or "none"))
        out.append("- **Lessons:** " + (", ".join(f"{l['num']} {l['title']} (curve35.com/{l['short']})" for l in les) or "none"))
        out.append("- **Facts (through its lessons):** " + (", ".join(f"`{f}` {fact_text(F[f])}" for f in facts) or "none"))
        out.append("- **Checks:** " + (", ".join(f"{c['name']} (`{', '.join(c['tools'][:1])}`)" for c in checks_of(p["id"])) or "none"))
        out.append("- **Offers:** " + (", ".join(f"{o['name']} ({o['price_text']})" for o in offers_of(p["id"])) or "none"))
        out.append("")
    out += ["## Steps", "", "| Step | Title | Parts | Lesson | Short link |", "|---|---|---|---|---|"]
    for s in C["steps"]: out.append(f"| {s['id']} ({s['section']} {s['n']}) | {s['title']} | {', '.join(s.get('parts') or {}) or '-'} | {s['lesson']} {L[s['lesson']]['title']} | curve35.com/{s['short']} |")
    out += ["", "## Lessons", "", "| Lesson | Question | Parts | Steps | Facts | Photo challenge |", "|---|---|---|---|---|---|"]
    for l in C["lessons"]:
        pc = l.get("photo_challenge"); out.append(f"| {l['num']} {l['title']} (curve35.com/{l['short']}) | {l['question']} | {', '.join(l['parts'])} | {', '.join(l['steps']) or '-'} | {', '.join(l['facts'])} | {(str(pc['frames']) + ' frames') if pc else '-'} |")
    out += ["", "## Facts", "", "| Fact | Says | Source | Checked |", "|---|---|---|---|"]
    for f in C["facts"]:
        st, msg = states.get(f["id"], ("?", "")); out.append(f"| `{f['id']}` | {fact_text(f)} | `{f['source']}`" + (f" {' '.join(map(str, f['path']))}" if f.get("path") else "") + f" | {st}{(': ' + msg) if st != 'ok' and msg else ''} |")
    out += ["", "## Checks", "", "| Check | Proves | Headline | Tools |", "|---|---|---|---|"]
    for c in C["checks"]: out.append(f"| {c['name']} | {c['proves']} | {c['headline']} | {', '.join('`' + t + '`' for t in c['tools'])} |")
    out += ["", "## The three ways to get it", ""]
    for w in C["offers"]["ways"]:
        out += [f"### {w['title']}", "", f"{w['for']} {w['what']}", "", "- " + ", ".join(f"{C['product'][q]['name']} ({C['product'][q]['price_text']})" for q in w["products"])]
        if w.get("programs"): out.append("- Programs: " + ", ".join(g["name"] for g in C["offers"]["programs"] if g["id"] in w["programs"]))
        out.append("")
    out += ["## Short links", "", ", ".join(f"/{k} -> #{v}" for k, v in C["short_links"].items()), ""]
    out += ["## Glossary", ""] + [f"- **{t['term']}**{(' (the guide says ' + repr(t['says']) + ')') if t.get('says') else ''}: {t['means']} Taught in {', '.join(t.get('taught', []))}." for t in C["glossary"]] + [""]
    return "\n".join(out)

def main(argv):
    try: C = load(fresh=True)
    except ValueError as e: print("canon: " + str(e)); return 1
    E, N, states = validate(C)
    n = lambda st: sum(1 for s, _ in states.values() if s == st)
    print(f"canon: {len(C['parts'])} parts, {len(C['steps'])} steps, {len(C['lessons'])} lessons, {len(C['facts'])} facts "
          f"({n('ok')} checked against their source, {n('unchecked')} decisions or standards, {n('bad')} wrong), {len(C['checks'])} checks, "
          f"{len(C['glossary'])} terms, {len(C['offers']['products'])} products, {len(C['offers']['programs'])} programs, {len(C['short_links'])} short links")
    for f, (st, msg) in states.items():
        if st == "unchecked": print(f"  unchecked: {f}: {msg}")
    for x in N: print("  note: " + x)
    if E:
        print(f"\n{len(E)} broken:"); [print("  ! " + x) for x in E]; return 1
    if "--check" in argv: print("canon: every reference holds"); return 0
    (CANON / "INDEX.md").write_text(index_md(C, states), encoding="utf-8")
    merged = {k: v for k, v in C.items() if k not in ("part", "step", "lesson", "fact", "check", "product")}
    merged["used_by"] = {"part_offers": {p["id"]: [q["id"] for q in C["offers"]["products"] if p["id"] in q.get("parts", [])] for p in C["parts"]},
                         "check_parts": {c["id"]: [p["id"] for p in C["parts"] if c["id"] in (p.get("checks") or [])] for c in C["checks"]},
                         "fact_lessons": {f["id"]: [l["id"] for l in C["lessons"] if f["id"] in l["facts"]] for f in C["facts"]}}
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/canon.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "site/data/products.json").write_text(json.dumps(products_json(C), ensure_ascii=False, indent=1), encoding="utf-8")
    print("canon: every reference holds; wrote canon/INDEX.md, build/canon.json, site/data/products.json")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
