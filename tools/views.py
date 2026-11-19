"""Every part seen square-on from above, from the front and from the side, and in three-quarter view, as it lies on the print bed.
Writes build/views/*.png and build/ONE-135_part_views.pdf."""
import subprocess, os, json, sys, concurrent.futures as cf
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
SCAD = "scad/one135.scad"; OUT = "build/views"; os.makedirs(OUT, exist_ok=True)
PARTS = [("front", "Front plate"), ("wheel", "Aperture wheel"), ("blade", "Shutter blade"), ("body", "Body"), ("back", "Back"), ("roller", "Frame wheel"), ("knob", "Wind knob (print two: one is a spare)"), ("spool", "Take-up spool (one piece)"), ("pinring", "Pinhole ring (takes the lens's place for the lens-less build)")]
VIEWS = [("top", "from above", (0, 0, 0)), ("front", "from the front", (90, 0, 0)), ("side", "from the side", (90, 0, 90)), ("iso", "three-quarter", (58, 0, 32))]
def render(part, view, rot, size=(900, 680)):
    out = f"{OUT}/{part}_{view}.png"
    if os.path.exists(out) and os.path.getmtime(out) > max(os.path.getmtime(SCAD), os.path.getmtime("scad/layout.scad")): return out
    cmd = ["xvfb-run", "-a", "openscad", "-o", out, f"--imgsize={size[0]},{size[1]}", "--colorscheme=Tomorrow", "--projection=o", "--viewall", "--autocenter", f"--camera=0,0,0,{rot[0]},{rot[1]},{rot[2]},300",
           "-D", 'PART="g_print"', "-D", f'G_P="p_{part}"', SCAD]
    subprocess.run(cmd, capture_output=True, text=True, timeout=900); im = Image.open(out).convert("RGB"); bg = Image.new("RGB", im.size, im.getpixel((0, 0))); box = ImageChops.difference(im, bg).getbbox()
    if box: im = im.crop((max(box[0] - 20, 0), max(box[1] - 20, 0), min(box[2] + 20, im.width), min(box[3] + 20, im.height)))
    im.save(out); return out
if __name__ == "__main__":
    jobs = [(p, v, r) for p, _ in PARTS for v, _, r in VIEWS]
    with cf.ThreadPoolExecutor(3) as ex: list(ex.map(lambda j: render(*j), jobs))
    pc = json.load(open("build/printcheck.json")); W, H = landscape(letter); c = canvas.Canvas("build/ONE-135_part_views.pdf", pagesize=(W, H)); c.setTitle("ONE-135 part views")
    for p, name in PARTS:
        c.setFont("Helvetica-Bold", 20); c.drawString(36, H - 44, name); c.setFont("Helvetica", 11); c.setFillGray(0.35)
        if p in pc: s = pc[p]["size"]; c.drawString(36, H - 62, f"as it lies on the print bed: {s[0]:.1f} x {s[1]:.1f} mm, {s[2]:.1f} mm tall; {pc[p]['on_bed_mm2']:.0f} mm2 on the bed; {pc[p]['volume_cm3']:.1f} cm3")
        else:
            import trimesh; m = trimesh.load(f"build/print/one135_{p}.stl"); s = m.extents; c.drawString(36, H - 62, f"as it lies on the print bed: {s[0]:.1f} x {s[1]:.1f} mm, {s[2]:.1f} mm tall; {m.volume / 1000:.2f} cm3")
        c.setFillGray(0)
        for i, (v, lab, _) in enumerate(VIEWS):
            x0 = 36 + (i % 2) * (W - 72) / 2; y0 = 36 + (1 - i // 2) * (H - 120) / 2; w, h = (W - 72) / 2 - 12, (H - 120) / 2 - 22; im = Image.open(f"{OUT}/{p}_{v}.png"); k = min(w / im.width, h / im.height)
            c.drawImage(ImageReader(f"{OUT}/{p}_{v}.png"), x0 + (w - im.width * k) / 2, y0 + (h - im.height * k) / 2, im.width * k, im.height * k); c.setFont("Helvetica", 9); c.setFillGray(0.4); c.drawString(x0, y0 + h + 6, lab); c.setFillGray(0)
        c.showPage()
    c.save()
    for k in range((len(PARTS) + 2) // 3):               # contact sheets, three parts each
        sheet = Image.new("RGB", (4 * 420, 3 * 320), "white")
        for r, (p, _) in enumerate(PARTS[3 * k: 3 * k + 3]):
            for q, (v, _, _) in enumerate(VIEWS): im = Image.open(f"{OUT}/{p}_{v}.png"); im.thumbnail((410, 310)); sheet.paste(im, (q * 420 + (410 - im.width) // 2, r * 320 + (310 - im.height) // 2))
        sheet.save(f"{OUT}/sheet_{k}.png")
    print("views:", len(jobs))
