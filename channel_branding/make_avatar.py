"""Channel avatar variants (800x800) drawn with the same stick-figure renderer as the videos.

usage: FRAME_STYLE=stickly python3 channel_branding/make_avatar.py <out_dir>
YouTube shows the avatar as a circle (98 px on desktop, ~48 px in comments), so every variant is a big face, no text.
"""
import os, random, sys
os.environ.update(FRAME_W="2000", FRAME_H="2400", FRAME_GROUND="2000", FRAME_STYLE="stickly")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "video4_kiss", "tools"))
from PIL import Image, ImageDraw
import paint_frames as pf

S = 2.0                                                       # character scale on the big canvas
LW = 3.2                                                      # outlines ~3x thicker so they survive the 98 px circle
_poly, _line = pf.P.poly, pf.P.line
pf.P.poly = lambda self, pts, fill, w=6, wob=2: _poly(self, pts, fill, int(w * LW) if w else 0, wob)
pf.P.line = lambda self, pts, w=6, fill=pf.OL: _line(self, pts, int(w * LW), fill)
_arc = ImageDraw.ImageDraw.arc                                # brows, smiles and lids drawn as arcs get the same boost
ImageDraw.ImageDraw.arc = lambda self, xy, start, end, fill=None, width=1: _arc(self, xy, start, end, fill, int(width * LW))

def face(kind, e="neutral", look=0, x=1000, extra=None, bg=(232, 93, 4), s=S):
    img = Image.new("RGB", (pf.W, pf.H), bg); p = pf.P(img, random.Random(7))
    if extra: extra(p, "back")
    g = pf.human(p, kind, x, s, e, "down", look)
    if extra: extra(p, "front", g)
    return img, g

def crop(img, g, k=1.9, dy=0.2):
    cx, cy, r = g["head"]; half = r * k; cy += r * dy
    return img.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half))).resize((800, 800), Image.LANCZOS)

def circle_preview(av, sizes=(98, 48)):
    """How YouTube shows it: circles at real sizes, on light and dark backgrounds."""
    out = Image.new("RGB", (560, 260), (255, 255, 255)); d = ImageDraw.Draw(out)
    d.rectangle((280, 0, 560, 260), fill=(15, 15, 15))
    for i, bgx in enumerate((0, 280)):
        x = bgx + 30
        for sz in sizes:
            a = av.resize((sz, sz), Image.LANCZOS); m = Image.new("L", (sz, sz), 0); ImageDraw.Draw(m).ellipse((0, 0, sz - 1, sz - 1), fill=255)
            out.paste(a, (x, 130 - sz // 2), m); x += sz + 30
    return out

def fire_glow(p, layer, g=None):
    if layer == "front":
        cx, cy, r = g["head"]
        for k, col in ((1.9, (60, 45, 70)), (1.5, (95, 55, 60))):          # warm glow behind the shoulder
            pass
        pf.fire_at = None
        x0, y0 = cx + r * 1.25, cy + r * 1.55
        p.poly([(x0 - 120, y0), (x0 - 55, y0 - 230), (x0, y0 - 120), (x0 + 40, y0 - 300), (x0 + 120, y0)], (255, 112, 67), 6)
        p.poly([(x0 - 60, y0 - 5), (x0, y0 - 150), (x0 + 60, y0 - 5)], (255, 235, 59), 5)

def qmark(p, layer, g=None, col=(255, 235, 59)):
    if layer == "front":
        cx, cy, r = g["head"]; p.text((cx + r * 1.12, cy - r * 0.55), "?", int(r * 1.05), fill=col, stroke=int(r * 0.09))

def qmark_white(p, layer, g=None): qmark(p, layer, g, (255, 255, 255))

VARIANTS = {
    "H_curious_orange_qmark": dict(kind="CAVE", e="confused", bg=(232, 93, 4), look=1, extra=qmark_white, x=900),
    "I_curious_slate_qmark": dict(kind="CAVE", e="confused", bg=(38, 70, 83), look=1, extra=qmark, x=900),
    "F_caveman_curious_orange": dict(kind="CAVE", e="confused", bg=(232, 93, 4), look=1),
    "G_caveman_curious_slate": dict(kind="CAVE", e="confused", bg=(38, 70, 83), look=1),
    "A_caveman_orange":   dict(kind="CAVE", e="neutral", bg=(232, 93, 4)),
    "B_caveman_question": dict(kind="CAVE", e="neutral", bg=(38, 70, 83), extra=qmark, x=900),
    "C_caveman_smug_teal": dict(kind="CAVE", e="smug", bg=(42, 157, 143), look=1),
    "D_cavewoman_yellow": dict(kind="WOMAN", e="neutral", bg=(244, 162, 97)),
    "E_caveman_fire_night": dict(kind="CAVE", e="neutral", bg=(29, 35, 70), extra=fire_glow, look=1, x=900),
}

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for name, v in VARIANTS.items():
        kw = dict(v); x = kw.pop("x", 1000)
        img, g = face(x=x, **kw)
        if name[0] in "BHI": g = dict(g, head=(g["head"][0] + g["head"][2] * 0.35, g["head"][1], g["head"][2]))
        if name.startswith("E"): g = dict(g, head=(g["head"][0] + g["head"][2] * 0.45, g["head"][1] + g["head"][2] * 0.25, g["head"][2]))
        av = crop(img, g); av.save(os.path.join(out, f"avatar_{name}.png"))
        circle_preview(av).save(os.path.join(out, f"preview_{name}.png"))
    print("ok", len(VARIANTS))
