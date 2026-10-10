"""Three high-contrast stick-figure thumbnails (1280x720) for a YouTube "Test & compare" A/B test of the cats video.

usage: FRAME_STYLE=stickly python3 tools/make_ab_thumbnails.py <out_dir>
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
sys.path.insert(0, os.path.dirname(__file__))
import paint_frames as pf

pf.mute = lambda c, k=0.5, base=None: c          # thumbnails need saturated colours, keep only the clean line style
W, H, OL = pf.W, pf.H, pf.OL

def headline(img, text, y=120, fill=(255, 235, 59), maxw=None):
    d = ImageDraw.Draw(img); size = 210; maxw = maxw or W - 90
    while d.textlength(text, font=ImageFont.truetype(pf.FONT, size)) > maxw: size -= 6
    d.text((W / 2, y), text, font=ImageFont.truetype(pf.FONT, size), fill=fill, stroke_width=20, stroke_fill=OL, anchor="mm")

def radial(c_in, c_out):
    img = Image.new("RGB", (W, H), c_out)
    glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse((W * 0.2, H * 0.15, W * 0.8, H * 1.25), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(Image.new("RGB", (W, H), c_in), img, glow)

def cat_layer(kind, s, e, flip=1, look=0, seed=1, ground=None, height=None):
    """Draw one cat on a transparent layer; a taller layer + lower ground keeps huge cats from being clipped."""
    old = pf.GROUND
    if ground is not None: pf.GROUND = ground
    try:
        lay = Image.new("RGBA", (W, height or H), (0, 0, 0, 0)); cp = pf.P(lay, random.Random(seed))
        pf.cat(cp, kind, W / 2, s, e, flip=flip, look=look)
    finally:
        pf.GROUND = old
    return lay

# --- A: NOBODY TAMED IT — one big smug cat sitting in a grain pot, dark teal background
def thumb_a(out):
    img = radial((40, 120, 130), (12, 48, 56))
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p = pf.P(fg, random.Random(3))
    top = pf.grain_pot(p, 1180, 1.0)
    for x, y in ((330, 740), (520, 790)): pf.mouse(p, x, y, 1.6)
    img.paste(fg, (0, 260), fg)
    # the cat goes straight onto the frame so its ears are not cut off by the shifted pot layer
    lay = cat_layer("HOUSECAT", 1.5, "smug", flip=-1, look=-1)
    img.paste(lay, (int(1180 - W / 2), int(top - (pf.GROUND + 40) + 95 + 260)), lay)
    headline(img, "NOBODY TAMED IT", y=112)
    img.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

# --- B: 50% WILD — one huge cat head, left half house cat on a cozy background, right half wildcat on savanna
def thumb_b(out):
    left = Image.new("RGB", (W, H), (255, 214, 170)); right = Image.new("RGB", (W, H), (214, 120, 40))
    pf.P(right, random.Random(5)).ell((1520, 230, 1800, 510), (255, 213, 79))   # savanna sun
    s, g = 3.0, 2400
    hx = W / 2 + 20 * s; hy = (g + 40) - 110 * s - 170 * s
    off = (int(W / 2 - hx), int(660 - hy))
    house = cat_layer("HOUSECAT", s, "happy", seed=6, ground=g, height=3000)
    wild = cat_layer("CAT", s, "angry", seed=6, ground=g, height=3000)
    left.paste(house, off, house); right.paste(wild, off, wild)
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    zig = [(W / 2 + (25 if i % 2 else -25), y) for i, y in enumerate(range(0, H + 60, 60))]
    md.polygon([(W, 0), (W, H)] + list(reversed(zig)), fill=255)
    img = Image.composite(right, left, mask)
    ImageDraw.Draw(img).line(zig, fill=OL, width=14)
    headline(img, "50% WILD", y=112)
    img.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

# --- C: WHY A CAT? — top-down grave: human skeleton and a small cat skeleton side by side, shocked scientist
def thumb_c(out):
    img = Image.new("RGB", (W, H), (120, 84, 56)); p = pf.P(img, random.Random(8))
    p.ell((230, 330, 1330, 1010), (78, 52, 36), 8)                                # grave pit
    bone = (250, 248, 236)
    def b(pts, w=18): p.line(pts, w + 8); p.line(pts, w, bone)                    # outlined bone
    # human skeleton lying on its back, head on the left
    b([(470, 560), (800, 560)], 16)                                               # spine
    for i in range(4):                                                            # ribs
        x = 520 + i * 55
        b([(x, 560), (x + 20, 490), (x + 45, 470)], 10); b([(x, 560), (x + 20, 630), (x + 45, 650)], 10)
    p.ell((780, 515, 870, 605), bone, 7)                                          # pelvis
    b([(860, 540), (1040, 510), (1210, 520)]); b([(860, 580), (1040, 610), (1210, 600)])   # legs
    b([(500, 520), (620, 430), (760, 420)], 14); b([(500, 600), (620, 690), (760, 700)], 14)  # arms
    p.ell((340, 495, 480, 625), bone, 7)                                          # skull
    p.d.ellipse((380, 535, 405, 560), fill=OL); p.d.ellipse((380, 575, 405, 600), fill=OL)
    # small cat skeleton curled next to it
    p.ell((560, 800, 640, 870), bone, 6)
    for sx in (-1, 1): p.poly([(600 + sx * 30, 810), (600 + sx * 38, 770), (600 + sx * 12, 802)], bone, 5)
    p.d.arc((620, 780, 860, 940), 180, 360, fill=bone, width=14)
    for i in range(5): x = 660 + i * 38; p.line([(x, 810), (x, 850)], 7, bone)
    p.d.arc((820, 830, 960, 950), 260, 80, fill=bone, width=9)
    # drawn on the left and mirrored, so the scientist stands on the right and points at the grave
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pf.human(pf.P(lay, random.Random(9)), "SCI", W - 1560, 1.05, "shock", "point")
    lay = ImageOps.mirror(lay)
    img.paste(lay, (0, 60), lay)
    headline(img, "WHY A CAT?", y=112)
    img.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    thumb_a(os.path.join(out, "ab_A_nobody_tamed_it.jpg"))
    thumb_b(os.path.join(out, "ab_B_50_percent_wild.jpg"))
    thumb_c(os.path.join(out, "ab_C_why_a_cat.jpg"))
    print("ok")
