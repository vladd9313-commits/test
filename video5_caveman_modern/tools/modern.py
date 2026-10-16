"""Modern places, props and the survival timer for the caveman-in-the-modern-world video.

Imported by paint_frames.py after its helpers exist: every painter takes the P canvas and reads layout constants
from paint_frames (W, H, GROUND, X, Y, OL) at call time, so the same code works for 16:9 and vertical Shorts frames.
"""
import math, re
pf = None                                   # set by paint_frames.py to itself (works when it runs as __main__ too)

GLASS = (179, 229, 252)
STEEL = (176, 190, 197)

def _floor(p, col):
    p.rect((-10, pf.GROUND, pf.W + 10, pf.H + 10), col)

def _wall(p, col):
    p.rect((-10, -10, pf.W + 10, pf.H + 10), col, 0)

# ----------------------------------------------------------------------------- backgrounds
def bg_city(p):
    W, G, X = pf.W, pf.GROUND, pf.X
    _wall(p, (129, 212, 250))
    for i, x in enumerate(range(-60, W + 60, 260)):
        h = 380 + (i * 137) % 260
        col = ((144, 164, 174), (188, 170, 164), (176, 190, 197), (161, 136, 127))[i % 4]
        p.rect((x, G - h, x + 230, G), col, 6)
        for wy in range(int(G - h + 40), int(G - 60), 90):
            for wx in (x + 30, x + 130): p.rect((wx, wy, wx + 70, wy + 50), GLASS, 4)
    _floor(p, (120, 120, 120))
    p.rect((-10, G + 110, W + 10, pf.H + 10), (80, 80, 84), 0)
    for x in range(0, W, 240): p.rect((x, G + 170, x + 120, G + 186), (250, 250, 250), 0)

def bg_library(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (215, 204, 200)); _floor(p, (141, 110, 99))
    cols = [(198, 40, 40), (46, 125, 50), (21, 101, 192), (249, 168, 37), (106, 27, 154), (93, 64, 55)]
    for x0 in range(-40, W, 380):
        p.rect((x0, max(G - 640, 20), x0 + 330, G), (121, 85, 72), 6)
        top = max(G - 640, 20)
        for k, sy in enumerate(range(int(top) + 30, G - 40, 150)):
            p.rect((x0 + 15, sy + 110, x0 + 315, sy + 125), (93, 64, 55), 3)
            bx = x0 + 22
            while bx < x0 + 300:
                bw = 22 + (bx * 7 + sy) % 18; bh = 70 + (bx * 3 + k * 11) % 35
                p.rect((bx, sy + 110 - bh, bx + bw, sy + 110), cols[(bx + sy) % 6], 3); bx += bw + 4

def bg_gym(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (207, 216, 220)); _floor(p, (84, 110, 122))
    p.rect((X_(80), G - 520, X_(560), G - 200), (236, 239, 241), 6)          # mirror
    for k in range(3): p.line([(X_(120) + k * 120, G - 480), (X_(200) + k * 120, G - 260)], 5, (255, 255, 255))
    rx = W - X_(380)                                                          # dumbbell rack
    p.rect((rx, G - 210, rx + X_(320), G - 190), (55, 71, 79), 5)
    for k in range(4): dumbbell(p, rx + 50 + k * X_(75), G - 225, 0.6)
    for lx in (rx + 10, rx + X_(300)): p.rect((lx, G - 190, lx + 16, G + 20), (55, 71, 79), 4)

def X_(v): return pf.X(v)

def bg_office(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (236, 239, 241)); _floor(p, (144, 164, 174))
    p.rect((X_(1250), G - 640, X_(1800), G - 300), GLASS, 8)
    p.line([(X_(1525), G - 640), (X_(1525), G - 300)], 8)
    for x in (X_(40), X_(700)):                                               # desks with screens behind the people
        p.rect((x, G - 190, x + 420, G - 165), (161, 136, 127), 5)
        for lx in (x + 20, x + 380): p.rect((lx, G - 165, lx + 20, G + 30), (121, 85, 72), 4)
        p.rect((x + 140, G - 330, x + 290, G - 220), (38, 50, 56), 6); p.rect((x + 200, G - 220, x + 230, G - 190), (96, 125, 139), 4)

def bg_office_kitchen(p):
    bg_office(p)
    W, G = pf.W, pf.GROUND
    p.rect((-10, G - 260, W + 10, G - 230), (189, 189, 189), 5)
    p.rect((-10, G - 230, W + 10, G + 30), (224, 224, 224), 5)

def microwave(p, x, s=1.0):
    G = pf.GROUND; y = G - 230
    p.rect((x - 150 * s, y - 170 * s, x + 150 * s, y), (236, 239, 241), 6)
    p.rect((x - 130 * s, y - 150 * s, x + 50 * s, y - 20 * s), (55, 71, 79), 5)
    for k in range(3): p.d.ellipse((x + 90 * s - 10, y - 140 * s + k * 40 * s, x + 90 * s + 10, y - 120 * s + k * 40 * s), fill=pf.OL)

def bg_zoo(p):
    W, G = pf.W, pf.GROUND
    pf.bg_day(p)
    p.rect((-10, G - 120, W + 10, G - 100), (121, 85, 72), 4)                 # fence
    for x in range(0, W, 90): p.rect((x, G - 160, x + 22, G + 10), (141, 98, 60), 4)
    sx = W - X_(360)
    p.rect((sx, max(G - 560, 30), sx + X_(300), max(G - 470, 120)), (255, 202, 40), 6)
    p.text((sx + X_(150), max(G - 515, 75)), "ZOO", 60, fill=(62, 39, 35), stroke=0)

def bg_buffet(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (255, 224, 178)); _floor(p, (161, 136, 127))
    p.rect((-10, G - 230, W + 10, G - 200), (189, 189, 189), 5)
    p.rect((-10, G - 200, W + 10, G + 20), (215, 204, 200), 5)
    foods = [(255, 167, 38), (139, 195, 74), (239, 83, 80), (121, 85, 72), (255, 241, 118)]
    for i, x in enumerate(range(30, W - 100, 230)):
        p.ell((x, G - 280, x + 190, G - 215), (250, 250, 250), 5)
        p.ell((x + 30, G - 300, x + 160, G - 240), foods[i % 5], 4)

def bg_supermarket(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (245, 245, 245)); _floor(p, (224, 224, 224))
    cols = [(239, 83, 80), (255, 202, 40), (102, 187, 106), (66, 165, 245), (255, 138, 101), (171, 71, 188)]
    for x0 in range(-30, W, 470):
        top = max(G - 560, 40)
        p.rect((x0, top, x0 + 420, G), (176, 190, 197), 6)
        for k, sy in enumerate(range(int(top) + 20, G - 30, 130)):
            p.rect((x0 + 10, sy + 100, x0 + 410, sy + 112), (96, 125, 139), 3)
            for j, bx in enumerate(range(x0 + 20, x0 + 390, 46)):
                p.rect((bx, sy + 40, bx + 38, sy + 100), cols[(j + k + x0) % 6], 3)

def bg_mall(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (255, 243, 224)); _floor(p, (215, 204, 200))
    p.rect((-10, max(G - 470, 60), W + 10, max(G - 440, 90)), (189, 189, 189), 5)   # upper floor
    for x in range(0, W, 420):
        p.rect((x + 20, max(G - 420, 110), x + 360, G - 80), GLASS, 6)
        p.rect((x + 20, max(G - 470, 60) - 70, x + 360, max(G - 470, 60)), (255, 138, 101), 5)

def escalator(p, low):
    if "escalator" not in low: return
    W, G = pf.W, pf.GROUND
    x0, x1 = X_(140), X_(1780); top = max(G - 470, 80)
    p.poly([(x0, G + 20), (x0 + 120, G + 20), (x1, top + 60), (x1, top), (x1 - 120, top)], (120, 144, 156), 7)
    p.poly([(x0, G + 20), (x1 - 120, top), (x1, top), (x1, top + 30), (x0 + 60, G + 30)], (69, 90, 100), 6)
    n = 14
    for k in range(1, n):
        t = k / n; x = x0 + (x1 - 120 - x0) * t; y = G + 20 + (top - G - 20) * t
        p.line([(x, y), (x + 70, y)], 4, (236, 239, 241))

def bg_airport(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (227, 242, 253)); _floor(p, (176, 190, 197))
    p.rect((-10, max(G - 620, 30), W + 10, max(G - 300, 200)), GLASS, 6)        # big window
    for x in range(0, W, 320): p.line([(x, max(G - 620, 30)), (x, max(G - 300, 200))], 6)
    p.rect((X_(1300) - 10, G - 140, X_(1800), G - 80), (96, 125, 139), 5)       # conveyor belt
    for x in range(int(X_(1310)), int(X_(1790)), 60): p.d.ellipse((x, G - 132, x + 40, G - 92), outline=pf.OL, width=3)

def scanner(p, geoms, low):
    if not re.search(r"body scanner|scanner", low): return
    g = next((g for g in geoms if "scanner" in g["seg"]), geoms[0] if geoms else None)
    if not g: return
    x0, y0, x1, y1 = g["body"]; top = g["top"] - 50
    for xx in (x0 - 70, x1 + 30): p.rect((xx, top, xx + 40, pf.GROUND + 50), STEEL, 6)
    p.d.chord((x0 - 70, top - 120, x1 + 70, top + 120), 180, 360, fill=STEEL, outline=pf.OL, width=6)
    for k in range(4):                                                         # scan lines
        y = top + 140 + k * (pf.GROUND - top - 100) / 4
        p.d.line([(x0 - 20, y), (x1 + 20, y)], fill=(0, 200, 255), width=5)

def bg_subway(p, low=""):
    W, G = pf.W, pf.GROUND
    _wall(p, (236, 239, 241))
    for y in range(20, G - 140, 70):
        for x in range(-(y // 70 % 2) * 60, W, 120): p.d.rectangle((x, y, x + 115, y + 65), outline=(207, 216, 220), width=3)
    p.rect((-10, max(G - 640, 20), W + 10, max(G - 600, 60)), (255, 202, 40), 0)
    p.rect((-10, G - 140, W + 10, G - 120), (66, 66, 66), 0)
    if "train" in low:
        ty = max(G - 560, 70)
        p.rect((-30, ty, W + 30, G - 130), (189, 189, 189), 7)
        p.rect((-30, ty + 60, W + 30, ty + 95), (25, 118, 210), 0)
        for x in range(40, W, 300): p.rect((x, ty + 130, x + 200, ty + 290), (69, 90, 100), 5)
    _floor(p, (158, 158, 158))
    p.rect((-10, G - 10, W + 10, G + 12), (255, 235, 59), 0)

def car(p, x, y, s=1.0, col=(229, 57, 53)):
    p.poly([(x - 200 * s, y), (x - 200 * s, y - 70 * s), (x - 120 * s, y - 80 * s), (x - 70 * s, y - 150 * s),
            (x + 90 * s, y - 150 * s), (x + 150 * s, y - 80 * s), (x + 200 * s, y - 70 * s), (x + 200 * s, y)], col, 6)
    p.poly([(x - 50 * s, y - 135 * s), (x + 80 * s, y - 135 * s), (x + 120 * s, y - 85 * s), (x - 90 * s, y - 85 * s)], GLASS, 4)
    for wx in (-120, 120): p.ell((x + wx * s - 42 * s, y - 42 * s, x + wx * s + 42 * s, y + 42 * s), (50, 50, 50), 5)

def bg_highway(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (129, 212, 250)); pf.mountains(p, (165, 180, 160), G - 120)
    p.rect((-10, G - 140, W + 10, pf.H + 10), (84, 84, 90), 0)
    for y in (G - 60, G + 90):
        for x in range(0, W, 260): p.rect((x, y, x + 140, y + 14), (250, 250, 250), 0)
    cols = [(229, 57, 53), (30, 136, 229), (255, 202, 40), (67, 160, 71), (250, 250, 250)]
    for i, x in enumerate(range(80, W, 430)): car(p, x, G - 70, 0.55, cols[i % 5])

def bg_waiting(p):
    W, G = pf.W, pf.GROUND
    _wall(p, (200, 230, 201)); _floor(p, (207, 216, 220))
    p.rect((X_(1450), max(G - 600, 40), X_(1750), max(G - 400, 200)), (255, 255, 255), 6)   # a sign with a red cross
    cx, cy = X_(1600), max(G - 500, 120)
    p.rect((cx - 25, cy - 70, cx + 25, cy + 70), (229, 57, 53), 0); p.rect((cx - 70, cy - 25, cx + 70, cy + 25), (229, 57, 53), 0)
    for x in range(30, W, 250):                                                 # a row of chairs
        p.rect((x, G - 150, x + 180, G - 120), (66, 165, 245), 5); p.rect((x, G - 260, x + 30, G - 120), (66, 165, 245), 5)
        for lx in (x + 10, x + 160): p.line([(lx, G - 120), (lx, G + 30)], 6)

def bg_forest(p):
    pf.bg_day(p)
    W, G = pf.W, pf.GROUND
    for x in range(-40, W, 300):
        p.rect((x + 110, G - 300, x + 150, G + 20), (121, 85, 72), 5)
        p.poly([(x + 20, G - 250), (x + 130, G - 520), (x + 240, G - 250)], (46, 125, 50), 6)

# setting keywords, matched before the original list (first match wins)
SETTINGS = [
    (("library", "librarian", "bookshelf"), bg_library),
    (("gym", "treadmill", "dumbbell"), bg_gym),
    (("office kitchen", "microwave"), bg_office_kitchen),
    (("office", "meeting", "desk", "chair"), bg_office),
    (("zoo", "petting zoo", "zookeeper", "cage"), bg_zoo),
    (("buffet", "restaurant", "waiter"), bg_buffet),
    (("supermarket",), bg_supermarket),
    (("mall", "escalator", "stairs"), bg_mall),
    (("airport", "body scanner"), bg_airport),
    (("subway",), bg_subway),
    (("highway",), bg_highway),
    (("waiting room", "doctor"), bg_waiting),
    (("city street", "city", "town"), bg_city),
    (("forest", "rocky cliff"), bg_forest),
]
INDOOR = (bg_library, bg_gym, bg_office, bg_office_kitchen, bg_buffet, bg_supermarket, bg_mall, bg_airport, bg_subway, bg_waiting)

# ----------------------------------------------------------------------------- props
def dumbbell(p, x, y, s=1.0):
    p.line([(x - 70 * s, y), (x + 70 * s, y)], int(16 * s) + 6); p.line([(x - 70 * s, y), (x + 70 * s, y)], int(16 * s), (120, 120, 120))
    for sx in (-1, 1): p.rect((x + sx * 70 * s - 22 * s, y - 45 * s, x + sx * 70 * s + 22 * s, y + 45 * s), (55, 55, 60), 5)

def book(p, x, y, s=1.0):
    p.rect((x - 55 * s, y - 70 * s, x + 55 * s, y + 70 * s), (198, 40, 40), 5)
    p.rect((x - 40 * s, y - 50 * s, x + 40 * s, y - 20 * s), (255, 241, 118), 3)

def treadmill(p, x, s=1.0):
    G = pf.GROUND + 40
    p.poly([(x - 230 * s, G + 10), (x + 200 * s, G + 10), (x + 230 * s, G - 30 * s), (x - 200 * s, G - 30 * s)], (55, 71, 79), 6)
    p.line([(x + 190 * s, G - 30 * s), (x + 220 * s, G - 330 * s)], int(14 * s) + 2)
    p.rect((x + 160 * s, G - 380 * s, x + 280 * s, G - 320 * s), (96, 125, 139), 5)

def clock(p, x, s=1.0):
    G = pf.GROUND; r = 120 * s; cy = G - 220 * s
    p.ell((x - r, cy - r, x + r, cy + r), (255, 255, 255), 7)
    for k in range(12):
        a = k * math.pi / 6; p.line([(x + 0.8 * r * math.cos(a), cy + 0.8 * r * math.sin(a)), (x + 0.92 * r * math.cos(a), cy + 0.92 * r * math.sin(a))], 4)
    p.line([(x, cy), (x, cy - 0.7 * r)], 7); p.line([(x, cy), (x + 0.45 * r, cy + 0.2 * r)], 7)

def goat(p, x, s=1.0, look=1):
    G = pf.GROUND + 40; body = pf.mute((236, 230, 220), 0.3); d = look or 1
    for lx in (-80, -40, 40, 80): p.line([(x + lx * s, G - 120 * s), (x + lx * s, G)], int(14 * s) + 2)
    p.ell((x - 130 * s, G - 230 * s, x + 130 * s, G - 100 * s), body, 6)
    hx, hy = x + d * 140 * s, G - 270 * s
    for sx in (-1, 1): p.d.arc((hx + sx * 20 * s - 50 * s, hy - 120 * s, hx + sx * 20 * s + 30 * s, hy - 20 * s), 180, 300, fill=pf.OL, width=int(12 * s))
    p.ell((hx - 60 * s, hy - 60 * s, hx + 60 * s, hy + 70 * s), body, 6)
    p.poly([(hx - 15 * s, hy + 65 * s), (hx + 15 * s, hy + 65 * s), (hx, hy + 110 * s)], (160, 150, 140), 4)    # beard
    pf.eyes(p, hx, hy - 5 * s, 22 * s, "neutral", d)
    return dict(x=x, s=s, look=d, head=(hx, hy, 70 * s), top=hy - 120 * s, mouth=(hx, hy + 40 * s),
                body=(x - 140 * s, G - 230 * s, x + 140 * s, G), hand=(hx, hy), hw=140 * s, ce="neutral", kind="GOAT", seg="", slot=-1)

def mammoth(p, x, s=1.0, look=-1):
    G = pf.GROUND + 40; fur = pf.mute((121, 85, 72), 0.3); d = look or -1
    for lx in (-150, -70, 70, 150): p.rect((x + lx * s - 35 * s, G - 230 * s, x + lx * s + 35 * s, G), fur, 6)
    p.ell((x - 260 * s, G - 520 * s, x + 260 * s, G - 170 * s), fur, 7)
    hx, hy = x + d * 230 * s, G - 430 * s
    p.ell((hx - 120 * s, hy - 130 * s, hx + 120 * s, hy + 110 * s), fur, 7)
    p.line([(hx + d * 40 * s, hy + 60 * s), (hx + d * 110 * s, hy + 230 * s), (hx + d * 70 * s, hy + 330 * s)], int(46 * s) + 8)
    p.line([(hx + d * 40 * s, hy + 60 * s), (hx + d * 110 * s, hy + 230 * s), (hx + d * 70 * s, hy + 330 * s)], int(46 * s), fur)
    p.d.arc((hx + d * 20 * s - 160 * s, hy, hx + d * 20 * s + 160 * s, hy + 260 * s), 20 if d > 0 else 100, 80 if d > 0 else 160, fill=(255, 248, 225), width=int(26 * s))
    pf.eyes(p, hx + d * 20 * s, hy - 30 * s, 26 * s, "neutral", d)
    return dict(x=x, s=s, look=d, head=(hx, hy, 130 * s), top=G - 540 * s, mouth=(hx, hy + 60 * s),
                body=(x - 270 * s, G - 520 * s, x + 270 * s, G), hand=(hx, hy), hw=270 * s, ce="neutral", kind="MAMMOTH", seg="", slot=-1)

def cage(p, geoms):
    for g in geoms:
        if g["kind"] not in ("LION", "LEOPARD", "WOLF", "HYENA"): continue
        x0, y0, x1, y1 = g["body"]; top = g["top"] - 40; x0 -= 40; x1 += 40
        p.rect((x0, top - 20, x1, top + 10), (96, 96, 96), 5)
        for x in range(int(x0), int(x1) + 1, 60): p.line([(x, top), (x, pf.GROUND + 45)], 12, (90, 90, 90))

def extra_props(low):
    """Slot props that stand in the row with the characters."""
    out = []
    if re.search(r"\bgoats?\b", low): out.append("goat")
    if "mammoth" in low: out.append("mammoth")
    if re.search(r"\ba clock\b", low): out.append("clock")
    if "microwave" in low: out.append("microwave")
    if re.search(r"\ba car\b", low) and "highway" not in low: out.append("car")
    return out

def draw_slot_prop(p, name, x, scale, look=1):
    if name == "goat": return goat(p, x, 0.9 * scale * pf.CHAR_SCALE, look)
    if name == "mammoth": return mammoth(p, x, 1.05 * pf.CHAR_SCALE, look)
    if name == "clock": clock(p, x, 0.9 * scale)
    elif name == "microwave": microwave(p, x, 0.9)
    elif name == "car": car(p, x, pf.GROUND + 40, 0.9 * scale)
    return None

# ----------------------------------------------------------------------------- the survival timer
TIMER_RE = re.compile(r"\s*\[TIMER ([^\]]*)\]")

def split_timer(scene):
    m = TIMER_RE.search(scene)
    return (TIMER_RE.sub("", scene), m.group(1).strip() if m else None)

def timer(p, label):
    """A red stopwatch badge in the top-right corner: the running score of the video."""
    from PIL import ImageFont
    W = pf.W; size = 64 if pf.TOPY == 0 else 70
    f = ImageFont.truetype(pf.FONT, size)
    tw = p.d.textlength(label, font=f); r = size * 0.62
    right = W - (40 if pf.TOPY == 0 else 150); top = 30 if pf.TOPY == 0 else pf.TITLE_BOTTOM - 25
    x0 = right - tw - 2 * r - 70; y1 = top + size * 1.5
    p.d.rounded_rectangle((x0, top, right, y1), radius=int(size * 0.5), fill=(229, 57, 53), outline=pf.OL, width=7)
    cx, cy = x0 + 26 + r, (top + y1) / 2
    p.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=pf.OL, width=5)
    p.d.rectangle((cx - 9, cy - r - 16, cx + 9, cy - r), fill=pf.OL)
    p.d.line([(cx, cy), (cx, cy - r * 0.7)], fill=pf.OL, width=6); p.d.line([(cx, cy), (cx + r * 0.5, cy + r * 0.15)], fill=pf.OL, width=6)
    p.text((cx + r + 22 + tw / 2, cy + 2), label, size, fill=(255, 255, 255), stroke=6)
    return (x0, top, right, y1)
