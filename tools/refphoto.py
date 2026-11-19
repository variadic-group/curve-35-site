"""The benchmark table of reference photographs.
  python3 tools/refphoto.py add reference/records/<folder>/record.json     check a record and add it to reference/index.csv (gives it the next number)
  python3 tools/refphoto.py table                                           print the table, newest last, with the change against the record before
  python3 tools/refphoto.py check <record.json>                             check only
A record is a copy of reference/record_template.json, filled in.  Nothing here reads the photographs themselves: the numbers are read off the scan by eye (see REFERENCE_PHOTO.md)."""
import sys, os, json, csv
from refcard import GROUPS, INDEX_COLS, CARD
IDX = "reference/index.csv"

def problems(r):
    """what is wrong with a record, as a list of plain sentences (empty = fine)"""
    P = []; fr = {f.get("frame"): f for f in r.get("frames", [])}
    if r.get("card") != CARD: P.append(f"card must be {CARD}")
    if not r.get("date") or r["date"].startswith("Y"): P.append("date is missing")
    if not r.get("by"): P.append("who took it is missing")
    cam = r.get("camera", {})
    for k in ("version", "change", "printer", "build"):
        if not cam.get(k): P.append(f"camera.{k} is missing")
    if not r.get("film", {}).get("stock"): P.append("film.stock is missing")
    f1 = fr.get(1)
    if not f1: P.append("frame 1 (C, open shade, card in the middle) is missing: that frame is the benchmark")
    else:
        for k in ("finest_group_upright", "finest_group_lying"):
            if f1.get(k) not in GROUPS + [0]: P.append(f"frame 1 {k} must be one of {GROUPS} (or 0 if not even the 5 group can be counted)")
        if abs(float(f1.get("distance_m") or 0) - 4.0) > 0.2 and cam.get("build") == "lens": P.append("frame 1 must be taken from 4 m with the lens build (2 m is allowed for the pinhole ring: the numbers are then halved for you)")
    if 6 in fr and fr[6].get("leak_frame_clear") is None: P.append("frame 6 is there but says nothing about leaks")
    return P

def row(r, rid):
    fr = {f.get("frame"): f for f in r.get("frames", [])}; cam = r["camera"]; scale = 0.5 if abs(float(fr[1].get("distance_m") or 4) - 2.0) < 0.2 else 1.0
    g = lambda n, k: (fr[n].get(k) if n in fr else None); num = lambda v: "" if v is None else (v * scale if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
    corners = [v for n in (2, 3) for v in (g(n, "finest_group_upright"), g(n, "finest_group_lying")) if v is not None]; st = r.get("shutter_time_s") or {}
    vals = [rid, r["date"], r["by"], cam["version"], cam["change"], cam["build"], cam["printer"], r["film"]["stock"], num(g(1, "finest_group_upright")), num(g(1, "finest_group_lying")), num(min(corners)) if corners else "",
            num(min(v for v in (g(4, "finest_group_upright"), g(4, "finest_group_lying")) if v is not None)) if g(4, "finest_group_upright") is not None else "", num(min(v for v in (g(5, "finest_group_upright"), g(5, "finest_group_lying")) if v is not None)) if g(5, "finest_group_upright") is not None else "",
            num(g(6, "leak_frame_clear")), num(g(7, "lines_along_film")), r.get("frame_spacing", ""), num(st.get("fast_press", st.get("brisk_push"))), num(st.get("slow_press", st.get("slow_push"))), num(r.get("shutter_bounce_seen")), r.get("against_previous", "")]
    return dict(zip(INDEX_COLS, vals))

def table():
    rows = list(csv.DictReader(open(IDX))) if os.path.exists(IDX) else []
    if not rows: print("No reference photograph has been recorded yet. The first accepted record becomes the baseline."); return rows
    prev = None
    for r in rows:
        c = float(r["centre_upright"] or 0) + float(r["centre_lying"] or 0); d = "" if prev is None else ("  sharper" if c > prev else "  softer" if c < prev else "  the same"); prev = c
        print(f"{r['id']}  {r['date']}  v{r['version']:<5} {r['build']:<12} centre {r['centre_upright']}/{r['centre_lying']}  corner {r['corner_worst'] or '-'}  leak frame clear: {r['leak_frame_clear'] or '-'}  {r['change'][:40]}{d}")
    return rows

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "table"
    if cmd == "table": table()
    else:
        r = json.load(open(sys.argv[2])); P = problems(r)
        if P: print("Not accepted yet:"); [print("  -", x) for x in P]; sys.exit(1)
        if cmd == "check": print("The record is complete.")
        else:
            rows = list(csv.DictReader(open(IDX))) if os.path.exists(IDX) else []; rid = f"{CARD}-{len(rows) + 1:04d}"; r["id"] = rid; json.dump(r, open(sys.argv[2], "w"), indent=1)
            new = not os.path.exists(IDX); w = csv.DictWriter(open(IDX, "a", newline=""), fieldnames=INDEX_COLS)
            if new: w.writeheader()
            w.writerow(row(r, rid)); print("Added as", rid)
