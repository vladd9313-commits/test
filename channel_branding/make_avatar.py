"""Channel avatar variants (800x800) drawn with the same stick-figure renderer as the videos.

usage: python3 channel_branding/make_avatar.py <out_dir>          # 9 draft variants + previews
       python3 channel_branding/make_avatar.py <out_dir> final    # the chosen avatar (avatar_final.png)
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


# ----------------------------------------------------------------------------- final avatar (judge panel pick H + tweaks)
def final_avatar(path):
    """Curious caveman on orange: big face, brows on the skin, one-shoulder hide, a '?' made of a crooked stick and a pebble."""
    import math
    N = 1600; O = 28                                          # drawn at 2x, outline 28 px -> 14 px at 800
    OLc, CREAMc = (20, 20, 20), (246, 241, 222)
    img = Image.new("RGB", (N, N), (232, 93, 4)); d = ImageDraw.Draw(img)
    def poly(pts, fill): d.polygon(pts, fill=fill); d.line(pts + [pts[0]], fill=OLc, width=O, joint="curve")
    def ell(box, fill): d.ellipse(box, fill=fill, outline=OLc, width=O)
    hx, hy, r = 660, 780, 455
    # body: bare right shoulder, hide over the left shoulder with a jagged edge and spots
    poly([(hx - 520, N + 40), (hx - 470, hy + 470), (hx - 120, hy + 400), (hx + 120, hy + 400), (hx + 470, hy + 470), (hx + 540, N + 40)], CREAMc)
    hide = [(hx - 560, N + 40), (hx - 500, hy + 460), (hx - 260, hy + 400)]
    for k in range(7):                                        # zigzag strap edge running down to the right
        t = k / 6; x0 = hx - 260 + t * 700; y0 = hy + 400 + t * 470
        hide.append((x0 + 35, y0 + (25 if k % 2 else -25)))
    hide += [(hx + 520, N + 40)]
    poly(hide, (104, 68, 38))
    for sx, sy, rr in ((hx - 300, hy + 560, 34), (hx - 120, hy + 690, 28), (hx - 380, hy + 730, 30), (hx + 40, hy + 800, 26)):
        d.ellipse((sx - rr, sy - rr * 0.75, sx + rr, sy + rr * 0.75), fill=(70, 44, 24))
    # head
    ell((hx - r, hy - r, hx + r, hy + r), CREAMc)
    # shaggy hair: jagged crown with a zigzag fringe high on the forehead
    hair = []
    for i in range(15):
        a = math.pi * (1.0 + i / 14); rr = r * (1.22 if i % 2 else 1.04)
        hair.append((hx + rr * math.cos(a), hy - r * 0.05 + rr * math.sin(a) * 0.95))
    fringe_y = hy - r * 0.68
    for k in range(8, -1, -1):                                # zigzag fringe from right to left
        x0 = hx - r * 0.98 + k * (r * 1.96 / 8); hair.append((x0, fringe_y + (40 if k % 2 else -10)))
    poly(hair, (84, 56, 34))
    # brows on the skin: left flat, right raised
    d.line([(hx - 255, hy - 170), (hx - 85, hy - 178)], fill=OLc, width=32)
    _arc(d, (hx + 80, hy - 250, hx + 260, hy - 110), 200, 340, OLc, 32)   # unpatched arc: real 32 px
    # eyes looking a little up-right, deadpan
    for ex in (hx - 165, hx + 165):
        d.ellipse((ex - 38 + 12, hy - 95 - 38, ex + 38 + 12, hy - 95 + 38), fill=OLc)
    # wavy, puzzled mouth
    d.line([(hx - 95, hy + 195), (hx - 35, hy + 178), (hx + 25, hy + 192), (hx + 85, hy + 176)], fill=OLc, width=28, joint="curve")
    # the '?' as a crooked stick with a pebble dot
    q = [(1195, 560), (1190, 445), (1250, 365), (1350, 350), (1430, 405), (1445, 495), (1395, 575), (1330, 625), (1315, 725)]
    d.line(q, fill=OLc, width=96, joint="curve"); d.line(q, fill=(214, 172, 104), width=62, joint="curve")
    for cx_, cy_ in ((q[0][0], q[0][1]), (q[-1][0], q[-1][1])):
        d.ellipse((cx_ - 48, cy_ - 48, cx_ + 48, cy_ + 48), fill=OLc); d.ellipse((cx_ - 31, cy_ - 31, cx_ + 31, cy_ + 31), fill=(214, 172, 104))
    for kx, ky in ((1420, 460), (1262, 390)):                # knots on the wood
        d.ellipse((kx - 12, ky - 9, kx + 12, ky + 9), fill=(150, 110, 60))
    ell((1258, 795, 1378, 892), (176, 176, 176))              # pebble dot
    img.resize((800, 800), Image.LANCZOS).save(path)
    return Image.open(path)

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2] == "final":
    av = final_avatar(os.path.join(sys.argv[1], "avatar_final.png"))
    circle_preview(av).save(os.path.join(sys.argv[1], "preview_final.png"))
