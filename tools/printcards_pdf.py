"""The print sheets as a PDF: build/CURVE-35_print_sheets.pdf.  Reads build/printcards.json, the pictures that tools/printcards.py made,
and the layer-by-layer audit (tools/printrules.py) of this version and of the one before."""
import os, sys, json
sys.path.insert(0, "tools")
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle
from PIL import Image as PImage
from docs import P_, H1, H2, SM, p, table, INK, GREY, RULE, TINT
from booklet import NAME, MODEL, PREV
from printcards import PARTS, SAID, SHORT, PIC
PW, PH = landscape(letter); W = PW - 30 * mm
Q = ParagraphStyle("q", parent=P_, fontName="LS", fontSize=10.5, leading=14, textColor=GREY, leftIndent=8, borderPadding=0, spaceAfter=4)
CAP = ParagraphStyle("cap", parent=SM, alignment=1, fontSize=8.5, leading=11)
PS_ = ParagraphStyle("ps", parent=P_, fontSize=9.2, leading=12.4, spaceAfter=3)
H3 = ParagraphStyle("h3", parent=H2, fontSize=11.5, leading=14, spaceBefore=2, spaceAfter=2)
def footer(c, d):
    c.setFont("LS", 7.5); c.setFillColor(GREY); c.drawString(15 * mm, 9 * mm, f"{NAME} ({MODEL}).  Worked out from the print files and the slicer's tool paths; nothing here has been printed."); c.drawRightString(PW - 15 * mm, 9 * mm, str(d.page))
f1 = lambda v, u="": "-" if v is None else (f"{v:.0f}{u}" if abs(v) >= 100 else f"{v:.1f}{u}")
sw = lambda v: "under 0.01 mm" if v < 0.005 else f"{v:.2f} mm"
def thin_now(r): return "none" if r["thin"][1] == 0 else (f"{r['thin'][1]}, kept on purpose" if r["kept"] == r["thin"][1] else f"{r['thin'][1]} ({r['kept']} kept on purpose)")
def cap_rules(r, i):
    thin, tall = r["thin"][i], r["tall"][i]; a = "no thin places" if thin == 0 else f"{thin} thin place{'s' if thin != 1 else ''}" + (" (kept on purpose)" if i == 1 and r["kept"] == thin else "")
    return a + ", " + ("no tall free-standing pieces" if tall == 0 else f"{tall} tall free-standing piece{'s' if tall != 1 else ''}")
def pair(files, wbox, hmax, caps):
    """pictures side by side at one scale, a caption under each"""
    sizes = [PImage.open(f).size for f in files]; sc = min(min(wbox / z[0], hmax / z[1]) for z in sizes)
    t = Table([[Image(f, width=z[0] * sc, height=z[1] * sc) for f, z in zip(files, sizes)], [Paragraph(c_, CAP) for c_ in caps]], colWidths=[wbox + 6] * len(files))
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "BOTTOM"), ("LINEAFTER", (0, 0), (-2, -1), 0.6, RULE), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)])); return t
def rows_for(d, tall):
    n = d["now"]; b = d["before"][0]; r = d["rules"]; c0, c1 = r["carries"]
    R = [["", f"Before ({PREV})", "Now"],
         ["Stands on", f1(b["stands_on_mm2"], " mm2"), f1(n["stands_on_mm2"], " mm2")],
         ["Height on the bed", f1(b["height_mm"], " mm"), f1(n["height_mm"], " mm")],
         ["Places thinner than three lines of plastic (1.2 mm)", str(r["thin"][0]) if r["thin"][0] else "none", thin_now(r)],
         ["Free-standing pieces too tall for their width", str(r["tall"][0]) if r["tall"][0] else "none", str(r["tall"][1]) if r["tall"][1] else "none"]]
    if tall:
        R += [["The level that carries the most for its width (the rule: at most 5 times)", f"{c0['above_mm']:.0f} mm on {c0['width_mm']:.1f} mm: {c0['ratio']:.1f} times", f"{c1['above_mm']:.0f} mm on {c1['width_mm']:.1f} mm: {c1['ratio']:.1f} times"],
              ["How far the top sways for each newton the nozzle drags on it", sw(b['sway_mm_per_N']), sw(n['sway_mm_per_N'])]]
    R += [["First layer: separate pieces on the bed, openings in them", f"{b['first_layer_pieces']} and {b['first_layer_openings']}", f"{n['first_layer_pieces']} and {n['first_layer_openings']}"],
          ["Longest span printed over open air", f1(b["longest_bridge_mm"], " mm"), f1(n["longest_bridge_mm"], " mm")],
          ["Shortest layer (short layers stay soft)", f1(b["shortest_layer_s"], " s"), f1(n["shortest_layer_s"], " s")],
          ["Print time and weight, slow printer", "", f"{n['print_time']}, {n['grams']:.1f} g"]]
    return R
def build():
    D = json.load(open("build/printcards.json")); tot = lambda k, i: sum(D[q]["rules"][k][i] for q, _, _ in PARTS); kept = sum(D[q]["rules"]["kept"] for q, _, _ in PARTS); unex = sum(D[q]["rules"]["unexplained"] for q, _, _ in PARTS)
    over = lambda i: [t for q, t, _ in PARTS if D[q]["rules"]["carries"][i]["ratio"] > 5.0]
    S = [Paragraph(f"How each part prints: {NAME}", H1), Paragraph(f"{MODEL}.  Every part as it stands on the bed, before this pass ({PREV}) and now.  Numbers come from the print files and the slicer; nothing has been printed.", SM)]
    S += [p("This pass asked one question of every part: <b>is there anything on it that stands alone, is poorly held up, or is finer than a printer lays down?</b> A new check (tools/printrules.py) reads each print file layer by layer, the way it lies on the bed, and counts three things: "
            "places thinner than three lines of plastic (1.2 mm with a 0.4 mm nozzle); small free-standing pieces that are tall for their width; and levels that carry more than five times their own width above them. "
            + ("It also looks for floors and roofs thinner than three layers (0.6 mm): there were none, before or now." if tot("skins", 0) + tot("skins", 1) == 0 else f"It also looks for floors and roofs thinner than three layers (0.6 mm): {tot('skins', 0)} before, {tot('skins', 1)} now.")),
          p(f"<b>Before: {tot('thin', 0)} thin places, {tot('tall', 0)} tall free-standing pieces, {len(over(0))} parts over the five-times rule ({' and '.join(t.split(' (')[0].lower() for t in over(0))}). "
            f"Now: {tot('thin', 1)} thin places" + (f", {'both' if kept == 2 else 'all'} kept on purpose and explained on the body's page" if kept == tot('thin', 1) and kept else "") + f"; {tot('tall', 1) or 'no'} tall free-standing pieces; {len(over(1)) or 'no'} part over the five-times rule.</b> "
            + ("Every narrow strip that is left (1.2 to 2.2 mm wide) is named on the last page: it is either a spring that is meant to bend or a low wall joined to its part along its whole length." if not unex else f"{unex} narrow strips are not yet explained."))]
    head = ["Part", "Stands on", "Height", "Thin places, before to now", "Tall free-standing pieces", "Most carried for its width", "Longest span over open air", "Shortest layer", "Changed in this pass"]
    rows = [head]
    for key, title, olds in PARTS:
        d = D[key]; n = d["now"]; r = d["rules"]; c0, c1 = r["carries"]; tall = n["height_mm"] > 12 and key not in ("back", "body")
        rows.append([title.split(" (")[0], f1(n["stands_on_mm2"], " mm2"), f1(n["height_mm"], " mm"), f"{r['thin'][0]} to {r['thin'][1]}" + (" (kept)" if r["kept"] else "") if (r["thin"][0] or r["thin"][1]) else "none", f"{r['tall'][0]} to {r['tall'][1]}" if r["tall"][0] else "none",
                     ((f"{c0['ratio']:.1f} to {c1['ratio']:.1f} times" if abs(c0["ratio"] - c1["ratio"]) > 0.05 else f"{c1['ratio']:.1f} times") if tall else "flat part"), f1(n["longest_bridge_mm"], " mm"), f1(n["shortest_layer_s"], " s"), SHORT[key]])
    S += [Spacer(1, 4), table(rows, [W * 0.11, W * 0.07, W * 0.06, W * 0.10, W * 0.09, W * 0.10, W * 0.08, W * 0.07, W * 0.32], small=True)]
    S += [Spacer(1, 5), p("<b>How to read the columns.</b> <i>Most carried for its width</i> takes each level of the part, measures the round bar that would be as stiff as that level, and divides what stands above it by that width. "
                         "<i>Longest span over open air</i> counts only bridges with nothing drawn beneath them; the closed top that every solid part lays over its own infill is left out. "
                         "<i>Shortest layer</i> is for the part printed alone at the slow printer's speeds; on the plate, with other parts beside it, every layer takes longer."),
          p("<b>Print in this order:</b> the fit gauge (ten minutes), then the test slab with the front plate, shutter and wheel (under two hours), then the rest on one plate. The cooling tower on the plate stands beside the spool and the frame wheel so that their small top layers have time to set.")]
    for key, title, olds in PARTS:
        d = D[key]; n = d["now"]; tall = n["height_mm"] > 12 and key not in ("back", "body"); said, changed, why = SAID[key]; F = d["facts"]; changed, why = changed.format(**F), why.format(**F)
        wide = key in ("back", "body", "front"); pics = pair([f"{PIC}{key}_old.png", f"{PIC}{key}_new.png"], W * (0.47 if wide else 0.20), (57 if wide else 62) * mm, [f"before ({PREV})", "now, as it stands on the bed (same scale)"])
        text = [Paragraph("What changed", H3), Paragraph(changed, PS_), Paragraph("Can a printer make it?" if key == "front" else "Why it prints", H3), Paragraph(why.replace("<b>Can a printer make it?</b> ", ""), PS_)]
        if wide: body = [pics, Spacer(1, 3), Table([[text[:2], text[2:]]], colWidths=[W * 0.5, W * 0.5], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 10)]))]
        else: body = [Table([[pics, text]], colWidths=[W * 0.46, W * 0.54], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))]
        S += [PageBreak(), Paragraph(title, H1)] + ([Paragraph(f"You said: “{said}”", Q)] if said else []) + body + [Spacer(1, 5), table(rows_for(d, tall), [W * 0.44, W * 0.28, W * 0.28])]
    # the audit's own pictures for the three parts it changed most, and the list of what is left
    S += [PageBreak(), Paragraph("What the layer-by-layer check sees", H1), Paragraph(f"Each part from above, as it lies on the bed.  Red: thinner than 1.2 mm.  Orange: free-standing and tall for its width.  Blue: a narrow strip, 1.2 to 2.2 mm wide.  Purple: thin, kept on purpose.  Left: {PREV}.  Right: now.", SM)]
    for key in ("back", "body", "front"):
        S += [pair([f"build/printrules_v24/{key}.png", f"build/printrules/{key}.png"], W * 0.47, 49 * mm, [f"{D[key]['title']}, before: {cap_rules(D[key]['rules'], 0)}", f"now: {cap_rules(D[key]['rules'], 1)}"]), Spacer(1, 2)]
    S += [PageBreak(), Paragraph("Every narrow strip that is left, by name", H1), Paragraph("Strips 1.2 to 2.2 mm wide and at least 12 mm long: three to five lines of plastic.  A spring is meant to bend and is strength-checked (tools/fea_cases.py).  A low wall is joined to its part along its whole length.", SM)]
    rows = [["Part", "Strip", "Width", "Kind"]]
    for key, title, olds in PARTS:
        seen = {}
        for q in D[key]["rules"]["strips"]: seen.setdefault((q["what"].split(" (the same one")[0], q["kind"]), []).append(q["width"])
        rows += [[title.split(" (")[0], what + (f" (x{len(ws)})" if len(ws) > 1 else ""), f"{min(ws):.1f} mm" if max(ws) - min(ws) < 0.1 else f"{min(ws):.1f} to {max(ws):.1f} mm", "spring: meant to bend" if kind == "spring" else ("low wall" if kind == "wall" else "NOT EXPLAINED")] for (what, kind), ws in seen.items()]
    S += [table(rows, [W * 0.14, W * 0.56, W * 0.14, W * 0.16], small=True)]
    kw = sorted({w for key, _, _ in PARTS for w in D[key]["rules"]["kept_why"]})
    if kw: S += [Spacer(1, 6), p("<b>Thin places kept on purpose.</b> " + " ".join(w[0].upper() + w[1:] + "." for w in kw))]
    S += [p("Parts with no narrow strip at all: " + ", ".join(t.split(" (")[0].lower() for k, t, _ in PARTS if not D[k]["rules"]["strips"]) + ".")]
    SimpleDocTemplate(f"build/{NAME.replace(' ', '-')}_print_sheets.pdf", pagesize=landscape(letter), leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm, bottomMargin=15 * mm, title=f"{NAME}: how each part prints", author="Camera Ladder").build(S, onFirstPage=footer, onLaterPages=footer)
    print("print sheets written")
if __name__ == "__main__": build()
