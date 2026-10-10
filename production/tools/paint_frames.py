"""Draw simple MS-Paint-style frames for every script line (fallback when no AI images are available).

usage: python3 tools/paint_frames.py <out_dir> [--only N,N,...]
Each frame is built from the line's scene description: a setting (day, night, desert, Egypt, sea, lab ...),
up to four characters with an expression, a few props/symbols, and the narration line as a caption.
"""
import math, os, random, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
from parse_script import load

W, H = 1920, 1080
GROUND = 800
OL = (20, 20, 20)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SKIN = (255, 222, 186)

# ----------------------------------------------------------------------------- drawing helpers
STICKLY = os.environ.get("FRAME_STYLE") == "stickly"   # minimalist muted stickman style
CREAM = (246, 241, 222)

def mute(c, k=0.5, base=(165, 158, 130)):
    return tuple(int(v * (1 - k) + b * k) for v, b in zip(c, base)) if STICKLY else c

def mute_image(img):
    m = ImageEnhance.Color(img).enhance(0.35)
    m = Image.blend(m, Image.new("RGB", img.size, (140, 160, 165)), 0.22)
    img.paste(m)

class P:
    def __init__(self, img, rnd):
        self.img, self.d, self.r = img, ImageDraw.Draw(img), rnd

    def wob(self, pts, amt=3):
        if STICKLY: return list(pts)
        return [(x + self.r.uniform(-amt, amt), y + self.r.uniform(-amt, amt)) for x, y in pts]

    def poly(self, pts, fill, w=6, wob=2):
        pts = self.wob(pts, wob)
        self.d.polygon(pts, fill=fill)
        self.d.line(pts + [pts[0]], fill=OL, width=w, joint="curve")

    def ell(self, box, fill, w=6):
        x0, y0, x1, y1 = box
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0) / 2, abs(y1 - y0) / 2
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in [i * 2 * math.pi / 36 for i in range(36)]]
        self.poly(pts, fill, w, wob=max(1, min(rx, ry) * 0.03))

    def line(self, pts, w=6, fill=OL):
        self.d.line(self.wob(pts, 1.5), fill=fill, width=w, joint="curve")

    def rect(self, box, fill, w=6):
        x0, y0, x1, y1 = box
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, w)

    def text(self, xy, s, size, fill=(255, 235, 59), stroke=8, anchor="mm"):
        f = ImageFont.truetype(FONT, size)
        self.d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=OL, anchor=anchor)

# ----------------------------------------------------------------------------- backgrounds
def mountains(p, col=(150, 150, 150), y=GROUND):
    x = -100
    while x < W + 100:
        w = p.r.randint(300, 520); h = p.r.randint(180, 330)
        p.poly([(x, y), (x + w / 2, y - h), (x + w, y)], col)
        x += w * 0.75

def grass(p, col=(67, 175, 72)):
    p.rect((-10, GROUND, W + 10, H + 10), col)

def bg_day(p):
    p.rect((-10, -10, W + 10, H + 10), (79, 195, 247), 0); mountains(p); grass(p)
    for _ in range(2):
        x, y = p.r.randint(100, W - 300), p.r.randint(60, 220)
        for dx in (0, 70, 140): p.ell((x + dx, y, x + dx + 120, y + 70), (255, 255, 255), 4)

def bg_night(p):
    p.rect((-10, -10, W + 10, H + 10), (26, 35, 90), 0)
    for _ in range(40):
        x, y = p.r.randint(0, W), p.r.randint(0, 500); p.d.ellipse((x, y, x + 6, y + 6), fill=(255, 255, 220))
    mx, my = p.r.choice([(200, 140), (1650, 150)])
    p.d.ellipse((mx, my, mx + 130, my + 130), fill=(255, 255, 240)); p.d.ellipse((mx + 40, my - 15, mx + 170, my + 115), fill=(26, 35, 90))
    mountains(p, (90, 90, 110)); grass(p, (30, 90, 40))

def bg_interior(p):
    p.rect((-10, -10, W + 10, H + 10), (78, 52, 46), 0)
    for y in range(40, GROUND, 90):
        off = 0 if (y // 90) % 2 else 110
        for x in range(-off, W, 220): p.d.rectangle((x, y, x + 210, y + 80), outline=(55, 35, 30), width=5)
    p.rect((-10, GROUND, W + 10, H + 10), (93, 64, 55))

def bg_desert(p):
    p.rect((-10, -10, W + 10, H + 10), (144, 202, 249), 0)
    p.ell((1550, 70, 1730, 250), (255, 213, 79))
    p.poly([(-50, GROUND - 40), (600, GROUND - 160), (1300, GROUND - 60), (W + 50, GROUND - 180), (W + 50, H + 10), (-50, H + 10)], (251, 192, 45))
    p.rect((-10, GROUND + 20, W + 10, H + 10), (240, 180, 40))

def bg_egypt(p):
    bg_desert(p)
    for x, s in ((250, 380), (700, 260), (1450, 330)):
        p.poly([(x - s, GROUND - 20), (x, GROUND - 20 - s * 1.1), (x + s, GROUND - 20)], (230, 190, 90))
    p.poly([(-20, GROUND + 60), (W + 20, GROUND + 30), (W + 20, GROUND + 120), (-20, GROUND + 150)], (66, 165, 245))

def bg_sea(p):
    p.rect((-10, -10, W + 10, H + 10), (129, 212, 250), 0)
    p.rect((-10, 520, W + 10, H + 10), (30, 136, 229))
    for y in range(580, H, 70):
        for x in range(0, W, 160): p.d.arc((x, y, x + 110, y + 40), 200, 340, fill=(255, 255, 255), width=5)

def bg_lab(p):
    p.rect((-10, -10, W + 10, H + 10), (224, 224, 224), 0)
    p.rect((-10, GROUND, W + 10, H + 10), (176, 190, 197))
    p.rect((1300, 220, 1800, 250), (141, 110, 99))
    for i, c in enumerate([(239, 83, 80), (102, 187, 106), (66, 165, 245), (255, 202, 40)]):
        x = 1340 + i * 110; p.rect((x, 120, x + 40, 220), c, 4)

def bg_classroom(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 236, 179), 0)
    p.rect((200, 80, 1720, 560), (46, 125, 50), 10)
    p.rect((-10, GROUND, W + 10, H + 10), (161, 136, 127))

def bg_living(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 224, 178), 0)
    p.rect((1400, 120, 1800, 480), (179, 229, 252), 8); p.line([(1600, 120), (1600, 480)], 8); p.line([(1400, 300), (1800, 300)], 8)
    p.rect((-10, GROUND, W + 10, H + 10), (188, 143, 100))
    for x in range(0, W, 240): p.line([(x, GROUND), (x - 80, H)], 4)

def bg_medieval(p):
    p.rect((-10, -10, W + 10, H + 10), (120, 130, 145), 0)
    for i, x in enumerate(range(-50, W, 330)):
        h = 300 + (i % 3) * 60
        p.poly([(x, GROUND), (x, GROUND - h), (x + 140, GROUND - h - 120), (x + 280, GROUND - h), (x + 280, GROUND)], (121, 85, 72))
        p.rect((x + 100, GROUND - 140, x + 180, GROUND), (62, 39, 35), 5)
    p.rect((-10, GROUND, W + 10, H + 10), (97, 97, 97))

def bg_village(p):
    bg_day(p)
    for x in (120, 1500):
        p.rect((x, GROUND - 260, x + 300, GROUND + 10), (188, 143, 100))
        p.poly([(x - 30, GROUND - 260), (x + 150, GROUND - 380), (x + 330, GROUND - 260)], (161, 136, 60))
        p.rect((x + 110, GROUND - 130, x + 190, GROUND + 10), (62, 39, 35), 5)

def bg_map(p):
    p.rect((-10, -10, W + 10, H + 10), (100, 181, 246), 0)
    blobs = [(150, 200, 800, 700), (900, 150, 1700, 650), (1100, 600, 1500, 1000), (300, 650, 650, 1000)]
    for b in blobs: p.ell(b, (165, 214, 167))

def bg_space(p):
    p.rect((-10, -10, W + 10, H + 10), (13, 17, 40), 0)
    for _ in range(80):
        x, y = p.r.randint(0, W), p.r.randint(0, H); p.d.ellipse((x, y, x + 5, y + 5), fill=(255, 255, 255))
    p.ell((-400, 820, W + 400, 2400), (66, 165, 245))

def bg_red(p):
    p.rect((-10, -10, W + 10, H + 10), (183, 28, 28), 0); grass(p, (120, 20, 20))

def bg_plain(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 249, 196), 0)

def bg_timeline(p):
    bg_plain(p); p.line([(120, 420), (1800, 420)], 12)
    p.poly([(1800, 390), (1860, 420), (1800, 450)], OL, 4)
    for x in range(200, 1800, 200): p.line([(x, 400), (x, 440)], 8)

SETTINGS = [  # (keywords, painter) - first match wins
    (("space", "rocket", "capsule", "orbit"), bg_space),
    (("timeline", "calendar", "family tree", "diagram", "bar chart", "chain of icons"), bg_timeline),
    (("map", "globe", "the earth", "world map"), bg_map),
    (("lab", "microscope", "computer screen", "dna", "x-ray", "brain scan", "journal"), bg_lab),
    (("chalkboard", "classroom", "whiteboard", "blueprint"), bg_classroom),
    (("medieval", "witch", "pope", "castle", "plague", "bonfire", "villagers"), bg_medieval),
    (("egypt", "pyramid", "nile", "pharaoh", "bastet", "temple", "mummy", "mummies", "tomb", "pelusium", "persian", "diodorus", "herodotus", "greek", "roman"), bg_egypt),
    (("sea", "boat", "ship", "canoe", "viking", "island", "harbor", "port", "waves", "baltic"), bg_sea),
    (("desert", "savanna", "sand", "sun-baked"), bg_desert),
    (("storehouse", "granary", "grain pot", "torch", "dark corner", "darkness", "barn", "warehouse", "post office", "den"), bg_interior),
    (("night", "moon", "3:00", "5:00", "dark hallway", "stars"), bg_night),
    (("couch", "living room", "apartment", "laptop", "bed", "kitchen", "table", "desk", "bathtub", "box", "window", "pet store", "café", "office", "video call", "door"), bg_living),
    (("village", "hut", "huts", "mud-brick"), bg_village),
    (("turning red", "dramatic"), bg_red),
]

# ----------------------------------------------------------------------------- characters
EXPR = [  # (keywords, expression)
    (("sleep", "asleep", "z letters", "eyes closed", "closed eyes", "slowly closing"), "sleep"),
    (("hiss", "angry", "furious", "glaring", "glare", "frowning", "offended", "shouting", "unhappy"), "angry"),
    (("shock", "surpris", "horror", "terrified", "frightened", "scared", "jaw dropped", "eyes huge", "eyes wide",
      "alarmed", "gasping", "mouth open", "freezing", "frozen", "panic", "worried", "sweating", "nervous", "paranoid"), "shock"),
    (("sad", "cry", "tears", "disappointed", "mourning", "sigh"), "sad"),
    (("confus", "question mark", "scratching his head", "squinting", "thinking"), "confused"),
    (("smug", "smirk", "evil genius", "unbothered", "unimpressed", "bored", "yawning", "ignoring", "like a king"), "smug"),
    (("happy", "smil", "cheer", "laugh", "proud", "thumbs up", "joy", "goofy", "love", "heart", "satisfied", "hug", "waving", "excited"), "happy"),
]

def expression(scene):
    s = scene.lower()
    for keys, e in EXPR:
        if any(k in s for k in keys): return e
    return "neutral"

def eyes(p, cx, cy, r, e, look=0):
    if STICKLY:
        for sx in (-1, 1):
            x = cx + sx * r * 1.05 + look * r * 0.25
            if e in ("sleep", "happy"):
                if e == "sleep": p.line([(x - r * 0.5, cy), (x + r * 0.5, cy)], 5)
                else: p.d.arc((x - r * 0.45, cy - r * 0.3, x + r * 0.45, cy + r * 0.5), 200, 340, fill=OL, width=6)
                continue
            dr = r * (0.3 if e == "shock" else 0.24)
            p.d.ellipse((x - dr, cy - dr, x + dr, cy + dr), fill=OL)
            if e in ("neutral", "smug", "confused"):        # heavy deadpan lid
                p.line([(x - r * 0.6, cy - r * 0.32), (x + r * 0.55, cy - r * 0.38)], 5)
            elif e == "angry":                               # inner end low, outer end high: a frowning V
                p.line([(x - sx * r * 0.6, cy - r * 0.3), (x + sx * r * 0.5, cy - r * 0.75)], 6)
            elif e == "sad":                                 # inner end high: worried brows
                p.line([(x - sx * r * 0.6, cy - r * 0.75), (x + sx * r * 0.5, cy - r * 0.35)], 6)
            elif e == "shock":
                p.d.arc((x - r * 0.6, cy - r * 1.1, x + r * 0.6, cy - r * 0.3), 200, 340, fill=OL, width=5)
        return
    for dx in (-r * 1.05, r * 1.05):
        x = cx + dx
        if e == "sleep":
            p.line([(x - r * 0.8, cy), (x + r * 0.8, cy)], 6); continue
        rr = r * (1.25 if e == "shock" else 1.0)
        p.ell((x - rr, cy - rr, x + rr, cy + rr), (255, 255, 255), 5)
        pr = r * (0.22 if e == "shock" else 0.32)
        px = x + look * r * 0.35
        p.d.ellipse((px - pr, cy - pr, px + pr, cy + pr), fill=OL)
        if e == "angry":
            p.line([(x - rr, cy - rr * 1.2 + (rr * 0.5 if dx < 0 else 0)), (x + rr, cy - rr * 1.2 + (0 if dx < 0 else rr * 0.5))], 7)
        if e == "sad":
            p.line([(x - rr, cy - rr * 1.1 + (0 if dx < 0 else rr * 0.4)), (x + rr, cy - rr * 1.1 + (rr * 0.4 if dx < 0 else 0))], 6)

def mouth(p, cx, cy, s, e):
    if STICKLY:
        if e == "happy": p.d.arc((cx - 28 * s, cy - 22 * s, cx + 28 * s, cy + 14 * s), 20, 160, fill=OL, width=5)
        elif e == "shock": p.d.ellipse((cx - 9 * s, cy - 6 * s, cx + 9 * s, cy + 16 * s), fill=OL)
        elif e in ("sad", "angry"): p.d.arc((cx - 24 * s, cy, cx + 24 * s, cy + 26 * s), 200, 340, fill=OL, width=5)
        elif e != "sleep": p.line([(cx - 20 * s, cy + 6 * s), (cx + 22 * s, cy + 4 * s)], 5)
        return
    if e in ("happy", "smug"):
        p.d.arc((cx - 40 * s, cy - 30 * s, cx + 40 * s, cy + 25 * s), 20 if e == "smug" else 10, 160 if e == "happy" else 120, fill=OL, width=7)
    elif e == "shock":
        p.ell((cx - 16 * s, cy - 8 * s, cx + 16 * s, cy + 30 * s), (120, 20, 20), 5)
    elif e in ("sad", "angry"):
        p.d.arc((cx - 35 * s, cy, cx + 35 * s, cy + 45 * s), 200, 340, fill=OL, width=7)
    elif e == "confused":
        p.line([(cx - 30 * s, cy + 10 * s), (cx - 5 * s, cy + 2 * s), (cx + 30 * s, cy + 14 * s)], 6)
    elif e != "sleep":
        p.line([(cx - 25 * s, cy + 10 * s), (cx + 25 * s, cy + 10 * s)], 6)

HUMANS = {
    "CAVE":  dict(shirt=(141, 98, 60), legs=SKIN, hair="messy", hair_col=(78, 52, 30), fur=True),
    "WOMAN": dict(shirt=(121, 85, 72), legs=SKIN, hair="long", hair_col=(62, 39, 25), fur=True),
    "GUY":   dict(shirt=(30, 136, 229), legs=(205, 180, 120), hair="short", hair_col=(109, 76, 50)),
    "EGYPT": dict(shirt=(250, 250, 245), legs=(205, 150, 100), hair="bob", hair_col=(20, 20, 20), skin=(205, 150, 100)),
    "SCI":   dict(shirt=(250, 250, 250), legs=(80, 80, 90), hair="messy", hair_col=(140, 140, 140), glasses=True),
    "ROMAN": dict(shirt=(198, 40, 40), legs=SKIN, hair="short", hair_col=(60, 40, 20)),
    "VIKING": dict(shirt=(93, 64, 55), legs=(120, 90, 60), hair="long", hair_col=(230, 160, 40), helmet=True),
    "PERSON": dict(shirt=(156, 204, 101), legs=(120, 100, 80), hair="short", hair_col=(60, 40, 20)),
}

def human_stickly(p, kind, x, s, e, arms, look, hold):
    c = HUMANS[kind]; gy = GROUND + 40
    hip = gy - 200 * s; neck = hip - 210 * s; hr = 120 * s; hy = neck - hr * 0.92
    for dx in (-28, 28):
        p.line([(x + dx * s * 0.6, hip), (x + dx * s, gy)], 6)
        p.d.ellipse((x + dx * s - 30 * s + (12 * s if dx > 0 else -12 * s), gy - 14 * s, x + dx * s + 30 * s + (12 * s if dx > 0 else -12 * s), gy + 12 * s), fill=OL)
    coat = mute(c["shirt"])
    p.poly([(x - 62 * s, neck), (x + 62 * s, neck), (x + 82 * s, hip + 50 * s), (x - 82 * s, hip + 50 * s)], coat, 5)
    p.line([(x, neck + 5), (x, hip + 45 * s)], 4)
    for sx in (-1, 1): p.line([(x + sx * 4, neck), (x + sx * 38 * s, neck + 55 * s)], 4)
    if arms == "up": targets = [(x - 150 * s, neck - 160 * s), (x + 150 * s, neck - 160 * s)]
    elif arms == "point": targets = [(x - 95 * s, hip + 10 * s), (x + 210 * s, neck + 20 * s)]
    elif arms == "head": targets = [(x - 65 * s, hy - 30 * s), (x + 65 * s, hy - 30 * s)]
    elif arms == "shrug": targets = [(x - 170 * s, neck - 20 * s), (x + 170 * s, neck - 20 * s)]
    else: targets = [(x - 105 * s, hip + 20 * s), (x + 105 * s, hip + 20 * s)]
    for (tx, ty), sx in zip(targets, (-1, 1)):
        a = (x + sx * 52 * s, neck + 18 * s)
        p.line([a, (tx, ty)], int(30 * s) + 8); p.line([a, (tx, ty)], int(30 * s), coat)
        p.d.ellipse((tx - 17 * s, ty - 17 * s, tx + 17 * s, ty + 17 * s), fill=OL)
    if hold: prop(p, hold, targets[1][0], targets[1][1], s)
    hair = {"messy": (70, 50, 38), "short": (45, 38, 32), "long": (20, 20, 20), "bob": (20, 20, 20)}.get(c["hair"])
    if c.get("fur"): hair = (90, 68, 52)
    if c["hair"] == "long":
        p.poly([(x - hr * 1.1, hy - hr * 0.2), (x + hr * 1.1, hy - hr * 0.2), (x + hr * 1.15, hy + hr * 1.5), (x - hr * 1.15, hy + hr * 1.5)], hair, 5)
    if c.get("ears"):
        for sx in (-1, 1): p.ell((x + sx * hr - hr * 0.3, hy - hr * 0.2, x + sx * hr + hr * 0.3, hy + hr * 0.35), CREAM, 5)
    p.ell((x - hr, hy - hr, x + hr, hy + hr), CREAM, 5)
    if c["hair"] == "messy":
        pts = [(x + hr * (1.18 if i % 2 else 1.0) * math.cos(math.pi + i * math.pi / 12), hy - hr * 0.12 + hr * (1.18 if i % 2 else 1.0) * math.sin(math.pi + i * math.pi / 12) * 0.9) for i in range(13)]
        p.poly(pts, hair, 5)
    elif c["hair"] in ("short", "long"):
        p.d.chord((x - hr, hy - hr, x + hr, hy + hr * 0.2), 180, 360, fill=hair, outline=OL, width=5)
    elif c["hair"] == "bob":
        p.d.chord((x - hr * 1.12, hy - hr * 1.12, x + hr * 1.12, hy + hr * 0.9), 160, 380, fill=hair, outline=OL, width=5)
        p.ell((x - hr * 0.8, hy - hr * 0.45, x + hr * 0.8, hy + hr), CREAM, 0)
    if c.get("helmet"):
        p.d.chord((x - hr * 1.05, hy - hr * 1.1, x + hr * 1.05, hy + hr * 0.3), 180, 360, fill=(140, 140, 140), outline=OL, width=5)
    if c.get("beard"):
        p.d.chord((x - hr * 0.75, hy + hr * 0.1, x + hr * 0.75, hy + hr * 1.5), 0, 180, fill=(30, 30, 30), outline=OL, width=5)
    eyes(p, x, hy + hr * 0.02, hr * 0.33, e, look)
    if c.get("glasses"):
        for dx in (-1, 1): p.d.ellipse((x + dx * hr * 0.35 - hr * 0.3, hy - hr * 0.3, x + dx * hr * 0.35 + hr * 0.3, hy + hr * 0.3), outline=OL, width=5)
    if not c.get("beard"): mouth(p, x, hy + hr * 0.42, s, e)

def human(p, kind, x, s, e, arms="down", look=0, hold=None):
    if STICKLY: return human_stickly(p, kind, x, s, e, arms, look, hold)
    c = HUMANS[kind]; skin = c.get("skin", SKIN)
    gy = GROUND + 40
    hip = gy - 230 * s; neck = hip - 230 * s; hr = 105 * s; hy = neck - hr * 0.9
    # legs
    for dx in (-35, 35):
        p.line([(x + dx * s, hip), (x + dx * 1.3 * s, gy)], int(16 * s) + 4, c["legs"] if not c.get("fur") else SKIN)
        p.line([(x + dx * s, hip), (x + dx * 1.3 * s, gy)], 5)
    # body
    if c.get("fur"):
        p.poly([(x - 75 * s, neck), (x + 75 * s, neck), (x + 95 * s, hip + 30 * s), (x + 30 * s, hip + 10 * s), (x - 20 * s, hip + 40 * s), (x - 95 * s, hip + 25 * s)], c["shirt"])
    else:
        p.poly([(x - 75 * s, neck), (x + 75 * s, neck), (x + 80 * s, hip + 15 * s), (x - 80 * s, hip + 15 * s)], c["shirt"])
    # arms
    if arms == "up":
        targets = [(x - 170 * s, neck - 170 * s), (x + 170 * s, neck - 170 * s)]
    elif arms == "point":
        targets = [(x - 90 * s, hip), (x + 230 * s, neck - 60 * s)]
    elif arms == "head":
        targets = [(x - 70 * s, hy - 40 * s), (x + 70 * s, hy - 40 * s)]
    elif arms == "shrug":
        targets = [(x - 190 * s, neck - 30 * s), (x + 190 * s, neck - 30 * s)]
    else:
        targets = [(x - 120 * s, hip + 10 * s), (x + 120 * s, hip + 10 * s)]
    for (tx, ty), sx in zip(targets, (-1, 1)):
        p.line([(x + sx * 70 * s, neck + 20 * s), (tx, ty)], int(14 * s) + 4, skin if c.get("fur") else c["shirt"])
        p.line([(x + sx * 70 * s, neck + 20 * s), (tx, ty)], 5)
        p.ell((tx - 18 * s, ty - 18 * s, tx + 18 * s, ty + 18 * s), skin, 4)
    if hold: prop(p, hold, targets[1][0], targets[1][1], s)
    # head + hair
    if c["hair"] == "long":
        p.poly([(x - hr * 1.15, hy - hr * 0.3), (x + hr * 1.15, hy - hr * 0.3), (x + hr * 1.2, hy + hr * 1.6), (x - hr * 1.2, hy + hr * 1.6)], c["hair_col"])
    p.ell((x - hr, hy - hr, x + hr, hy + hr), skin)
    if c["hair"] == "messy":
        pts = []
        for i in range(13):
            a = math.pi + i * math.pi / 12
            rr = hr * (1.28 if i % 2 else 1.02)
            pts.append((x + rr * math.cos(a), hy - hr * 0.1 + rr * math.sin(a) * 0.95))
        p.poly(pts, c["hair_col"], 5, wob=4)
    elif c["hair"] in ("short", "long"):
        p.poly([(x - hr * 1.02, hy - hr * 0.15), (x - hr * 0.8, hy - hr * 0.85), (x, hy - hr * 1.12), (x + hr * 0.8, hy - hr * 0.85), (x + hr * 1.02, hy - hr * 0.15), (x + hr * 0.3, hy - hr * 0.55), (x - hr * 0.4, hy - hr * 0.5)], c["hair_col"], 5)
    elif c["hair"] == "bob":
        p.poly([(x - hr * 1.15, hy + hr * 0.6), (x - hr * 1.1, hy - hr * 0.8), (x, hy - hr * 1.15), (x + hr * 1.1, hy - hr * 0.8), (x + hr * 1.15, hy + hr * 0.6), (x + hr * 0.8, hy + hr * 0.6), (x + hr * 0.75, hy - hr * 0.35), (x - hr * 0.75, hy - hr * 0.35), (x - hr * 0.8, hy + hr * 0.6)], c["hair_col"], 5)
    if c.get("helmet"):
        p.d.pieslice((x - hr * 1.05, hy - hr * 1.15, x + hr * 1.05, hy + hr * 0.6), 180, 360, fill=(158, 158, 158), outline=OL, width=6)
        for sx in (-1, 1): p.poly([(x + sx * hr * 0.9, hy - hr * 0.5), (x + sx * hr * 1.6, hy - hr * 1.5), (x + sx * hr * 1.1, hy - hr * 0.8)], (255, 248, 225), 5)
    eyes(p, x, hy - hr * 0.05, hr * 0.33, e, look)
    if c.get("glasses"):
        for dx in (-1, 1): p.d.ellipse((x + dx * hr * 0.35 - hr * 0.42, hy - hr * 0.47, x + dx * hr * 0.35 + hr * 0.42, hy + hr * 0.37), outline=OL, width=6)
    mouth(p, x, hy + hr * 0.5, s, e)
    if e == "sad": p.ell((x + hr * 0.5, hy + hr * 0.3, x + hr * 0.65, hy + hr * 0.55), (100, 181, 246), 3)
    if e == "shock" or "sweat" in kind: p.ell((x + hr * 1.0, hy - hr * 0.7, x + hr * 1.18, hy - hr * 0.4), (129, 212, 250), 3)

CATS = {
    "CAT": dict(body=(215, 179, 119), stripe=(120, 90, 50)),
    "HOUSECAT": dict(body=(251, 140, 0), stripe=(200, 90, 0)),
    "BLACKCAT": dict(body=(40, 40, 40), stripe=None, eye=(255, 235, 59)),
    "LEOPARDCAT": dict(body=(230, 190, 120), spots=(90, 60, 30)),
    "PERSIAN": dict(body=(250, 250, 250), stripe=None, fluffy=True),
    "SPHYNX": dict(body=(248, 187, 208), stripe=None),
    "MAINECOON": dict(body=(141, 110, 99), stripe=(90, 60, 40), fluffy=True),
    "DOG": dict(body=(161, 110, 70), stripe=None, dog=True),
    "WOLF": dict(body=(150, 150, 150), stripe=None, dog=True),
}

def cat(p, kind, x, s, e, flip=1, look=0):
    c = dict(CATS[kind]); gy = GROUND + 40
    for k_ in ("body", "stripe", "spots"):
        if c.get(k_): c[k_] = mute(c[k_], 0.35)
    by = gy - 110 * s
    # tail
    p.line([(x - flip * 90 * s, gy - 40 * s), (x - flip * 200 * s, gy - 90 * s), (x - flip * 180 * s, gy - 230 * s)], int(26 * s) + 6)
    p.line([(x - flip * 90 * s, gy - 40 * s), (x - flip * 200 * s, gy - 90 * s), (x - flip * 180 * s, gy - 230 * s)], int(26 * s), c["body"])
    p.ell((x - 120 * s, by - 120 * s, x + 120 * s, gy), c["body"], 6)
    if c.get("fluffy"):
        for i in range(10):
            a = i * 2 * math.pi / 10; p.ell((x + 110 * s * math.cos(a) - 30 * s, by - 10 * s + 100 * s * math.sin(a) - 30 * s, x + 110 * s * math.cos(a) + 30 * s, by - 10 * s + 100 * s * math.sin(a) + 30 * s), c["body"], 4)
    # head
    hx, hy, hr = x + flip * 20 * s, by - 170 * s, 105 * s
    for sx in (-1, 1):
        ear = [(hx + sx * hr * 0.95, hy - hr * 0.2), (hx + sx * hr * 0.75, hy - hr * 1.35), (hx + sx * hr * 0.2, hy - hr * 0.85)]
        if c.get("dog"): ear = [(hx + sx * hr * 0.9, hy - hr * 0.6), (hx + sx * hr * 1.3, hy + hr * 0.4), (hx + sx * hr * 0.75, hy + hr * 0.2)]
        p.poly(ear, c["body"], 6)
    p.ell((hx - hr, hy - hr * 0.95, hx + hr, hy + hr * 0.95), c["body"], 6)
    if c.get("stripe"):
        for dx in (-25, 0, 25): p.line([(hx + dx * s, hy - hr * 0.9), (hx + dx * s, hy - hr * 0.55)], 6, c["stripe"])
        for i in range(3): p.line([(x - 60 * s + i * 50 * s, by - 80 * s), (x - 45 * s + i * 50 * s, by - 20 * s)], 7, c["stripe"])
    if c.get("spots"):
        for _ in range(8):
            sx_, sy_ = p.r.uniform(-90, 90) * s, p.r.uniform(-90, 80) * s
            p.d.ellipse((x + sx_ - 12 * s, by + sy_ - 12 * s, x + sx_ + 12 * s, by + sy_ + 12 * s), fill=c["spots"])
    er = hr * 0.36
    if kind == "BLACKCAT" or e == "glow":
        for dx in (-1, 1): p.ell((hx + dx * er * 1.15 - er, hy - er * 1.2, hx + dx * er * 1.15 + er, hy + er * 0.6), (255, 235, 59), 4)
    else:
        eyes(p, hx, hy - er * 0.3, er, e, look)
    p.poly([(hx - 12 * s, hy + hr * 0.3), (hx + 12 * s, hy + hr * 0.3), (hx, hy + hr * 0.45)], (240, 98, 146), 3)
    for sx in (-1, 1):
        for dy in (-8, 8): p.line([(hx + sx * hr * 0.35, hy + hr * 0.45 + dy * s), (hx + sx * hr * 1.25, hy + hr * 0.35 + dy * 2.5 * s)], 3)
    mouth(p, hx, hy + hr * 0.5, s * 0.6, e if e != "shock" else "shock")

def mouse(p, x, y, s=0.5):
    p.line([(x - 50 * s, y), (x - 130 * s, y - 30 * s)], 5)
    p.ell((x - 60 * s, y - 50 * s, x + 60 * s, y + 20 * s), (176, 176, 176), 5)
    p.ell((x + 20 * s, y - 80 * s, x + 60 * s, y - 40 * s), (240, 180, 190), 4)
    p.d.ellipse((x + 35 * s, y - 25 * s, x + 47 * s, y - 13 * s), fill=OL)

# ----------------------------------------------------------------------------- props & symbols
def prop(p, name, x, y, s=1.0):
    if name == "torch":
        p.line([(x, y + 20), (x - 20, y + 200 * s)], int(18 * s), (121, 85, 72)); p.line([(x, y + 20), (x - 20, y + 200 * s)], 4)
        p.poly([(x - 35 * s, y + 20), (x, y - 90 * s), (x + 35 * s, y + 20)], (255, 152, 0), 5)
        p.poly([(x - 15 * s, y + 15), (x, y - 40 * s), (x + 15 * s, y + 15)], (255, 235, 59), 3)
    elif name == "spear":
        p.line([(x, y + 250 * s), (x, y - 250 * s)], 10, (121, 85, 72))
        p.poly([(x - 22 * s, y - 230 * s), (x, y - 320 * s), (x + 22 * s, y - 230 * s)], (158, 158, 158), 5)
    elif name == "sickle":
        p.d.arc((x - 60 * s, y - 120 * s, x + 80 * s, y + 20 * s), 180, 330, fill=(158, 158, 158), width=int(22 * s))
    elif name == "wheat":
        for dx in (-30, 0, 30):
            p.line([(x + dx * s, y + 120 * s), (x + dx * s * 1.4, y - 60 * s)], 6, (120, 100, 20))
            p.ell((x + dx * s * 1.4 - 16 * s, y - 120 * s, x + dx * s * 1.4 + 16 * s, y - 40 * s), (255, 202, 40), 4)
    elif name == "fish":
        p.ell((x - 60 * s, y - 25 * s, x + 50 * s, y + 25 * s), (144, 202, 249), 5); p.poly([(x - 55 * s, y), (x - 100 * s, y - 30 * s), (x - 100 * s, y + 30 * s)], (144, 202, 249), 5)
    elif name == "cup":
        p.rect((x - 40 * s, y - 60 * s, x + 40 * s, y + 40 * s), (255, 255, 255), 6)

def grain_pot(p, x, s=1.0, full=True):
    gy = GROUND + 40
    p.ell((x - 150 * s, gy - 300 * s, x + 150 * s, gy), (191, 111, 58), 7)
    p.rect((x - 90 * s, gy - 330 * s, x + 90 * s, gy - 270 * s), (191, 111, 58), 7)
    if full: p.ell((x - 100 * s, gy - 370 * s, x + 100 * s, gy - 300 * s), (255, 202, 40), 6)
    return gy - 330 * s

def fire(p, x):
    gy = GROUND + 40
    for dx in (-60, 0, 60): p.line([(x + dx - 50, gy), (x + dx + 50, gy - 30)], 18, (121, 85, 72))
    p.poly([(x - 90, gy - 20), (x - 40, gy - 170), (x, gy - 90), (x + 30, gy - 230), (x + 90, gy - 20)], (255, 112, 67), 6)
    p.poly([(x - 45, gy - 25), (x, gy - 130), (x + 45, gy - 25)], (255, 235, 59), 4)

def hut(p, x):
    gy = GROUND + 40
    p.rect((x - 170, gy - 260, x + 170, gy), (188, 143, 100)); p.poly([(x - 200, gy - 260), (x, gy - 400), (x + 200, gy - 260)], (161, 136, 60))
    p.rect((x - 45, gy - 140, x + 45, gy), (62, 39, 35), 5)

def boat(p, x, y=640):
    p.poly([(x - 330, y), (x + 330, y), (x + 240, y + 110), (x - 240, y + 110)], (141, 98, 60), 7)
    p.line([(x, y), (x, y - 330)], 10)
    p.poly([(x + 8, y - 320), (x + 230, y - 120), (x + 8, y - 60)], (255, 248, 225), 6)

def pyramid_small(p, x):
    gy = GROUND + 40; p.poly([(x - 200, gy), (x, gy - 220), (x + 200, gy)], (230, 190, 90))

def mummy(p, x, y, s=1.0):
    p.ell((x - 60 * s, y - 220 * s, x + 60 * s, y), (240, 230, 200), 6)
    for i in range(5): p.line([(x - 55 * s, y - 40 * s - i * 35 * s), (x + 55 * s, y - 55 * s - i * 35 * s)], 4, (160, 140, 100))
    p.ell((x - 45 * s, y - 270 * s, x + 45 * s, y - 190 * s), (240, 230, 200), 6)
    for sx in (-1, 1): p.poly([(x + sx * 40 * s, y - 250 * s), (x + sx * 40 * s, y - 300 * s), (x + sx * 10 * s, y - 265 * s)], (240, 230, 200), 4)
    for sx in (-1, 1): p.d.ellipse((x + sx * 18 * s - 8, y - 245 * s - 8, x + sx * 18 * s + 8, y - 245 * s + 8), fill=OL)

def skeleton(p, x, y, s=1.0):
    p.ell((x - 50 * s, y - 50 * s, x + 50 * s, y + 50 * s), (250, 250, 240), 5)
    p.line([(x + 50 * s, y), (x + 330 * s, y)], 10, (250, 250, 240))
    for i in range(5): p.line([(x + (90 + i * 35) * s, y - 40 * s), (x + (90 + i * 35) * s, y + 40 * s)], 6, (250, 250, 240))

def crown(p, x, y, s=1.0):
    p.poly([(x - 60 * s, y), (x - 60 * s, y - 60 * s), (x - 30 * s, y - 25 * s), (x, y - 75 * s), (x + 30 * s, y - 25 * s), (x + 60 * s, y - 60 * s), (x + 60 * s, y)], (255, 213, 79), 5)

def heart(p, x, y, s=1.0, col=(229, 57, 53)):
    p.poly([(x, y + 50 * s), (x - 60 * s, y - 5 * s), (x - 45 * s, y - 45 * s), (x - 15 * s, y - 45 * s), (x, y - 25 * s),
            (x + 15 * s, y - 45 * s), (x + 45 * s, y - 45 * s), (x + 60 * s, y - 5 * s)], col, 5)

def big_x(p):
    for a, b in (((380, 120), (1540, 900)), ((1540, 120), (380, 900))):
        p.d.line([a, b], fill=(229, 57, 53), width=60)

def stone_tablet(p, x, y, label):
    p.poly([(x - 200, y + 130), (x - 210, y - 90), (x - 120, y - 150), (x + 120, y - 150), (x + 210, y - 90), (x + 200, y + 130)], (176, 176, 176), 7)
    p.text((x, y - 5), label, 95 if len(label) < 6 else 70, fill=(80, 80, 80), stroke=0)

# ----------------------------------------------------------------------------- scene composer
CHAR_WORDS = [
    (r"\{CAVE\}|farmer|caveman|hunter", "CAVE"), (r"\{WOMAN\}|prehistoric woman|old woman|witch", "WOMAN"),
    (r"\{GUY\}|stranger|customer|tourists?|postmaster", "GUY"), (r"\{EGYPT\}|egyptians?|pharaoh|pilgrim|priest|scribes", "EGYPT"),
    (r"\{SCI\}|historians?|scientists?|diodorus|herodotus|greek man|researcher", "SCI"),
    (r"roman|emperor", "ROMAN"), (r"viking", "VIKING"), (r"crowd|villagers|peasant|soldiers|sailors|people|family", "PERSON"),
    (r"black cat", "BLACKCAT"), (r"leopard cat", "LEOPARDCAT"), (r"persian cat", "PERSIAN"), (r"sphynx", "SPHYNX"),
    (r"maine coon", "MAINECOON"), (r"\{CAT\}|wildcats?|kittens?|bastet", "CAT"),
    (r"\{HOUSECAT\}|house cat|tabby|cats?\b|larry|tama|simon|félicette", "HOUSECAT"),
    (r"\bdogs?\b|chihuahua|great dane", "DOG"), (r"\bwol(f|ves)\b", "WOLF"),
]
HUMAN_KINDS = set(HUMANS)

def characters(scene):
    found = []
    for pat, kind in CHAR_WORDS:
        for m in re.finditer(pat, scene, re.I):
            found.append((m.start(), kind))
    found.sort()
    out = []
    if re.search(r"(crowd|line|group|dozen)s? of [\w ]*?(mice|rats|wolves|cats)", scene, re.I):
        found = [f for f in found if f[1] != "PERSON"]
    for _, k in found:
        if k == "HOUSECAT" and any(c in out for c in ("CAT", "BLACKCAT", "LEOPARDCAT", "PERSIAN", "SPHYNX", "MAINECOON")) and "{HOUSECAT}" not in scene:
            continue
        if k not in out: out.append(k)
    if any(w in scene.lower() for w in ("three cats", "all three cats", "lineup of", "group of five", "dozens of cats")):
        out = out + [k for k in ("HOUSECAT", "CAT") if k not in out]
    return out[:4]

def arms_for(scene):
    s = scene.lower()
    if any(k in s for k in ("cheer", "arms in the air", "triumph", "hands raised", "celebrat")): return "up"
    if any(k in s for k in ("point", "finger raised", "one finger", "showing")): return "point"
    if any(k in s for k in ("hands on his head", "head in his hands", "head exploding", "facepalm", "covering his eyes", "covering his ears", "cheeks")): return "head"
    if any(k in s for k in ("shrug", "palms up")): return "shrug"
    return "down"

def pick_setting(low):
    for keys, painter in SETTINGS:
        if any(re.search(r"\b" + re.escape(k) + r"\b", low) for k in keys): return painter
    return None

def render(scene, caption, seed, out, ctx):
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H), (255, 255, 255)); p = P(img, rnd)
    low = scene.lower()
    painter = pick_setting(low) or ctx.get("setting") or bg_day
    ctx["setting"] = painter
    painter(p)
    e = expression(scene)
    chars = characters(scene)
    if not chars and not any(k in low for k in ("map", "globe", "sea", "island", "ship", "timeline", "tablet", "scroll", "book", "pot")):
        chars = ctx.get("chars", [])
    ctx["chars"] = chars
    if "island" in low:
        p.ell((W / 2 - 420, 560, W / 2 + 420, 760), (251, 192, 45)); p.line([(W / 2, 640), (W / 2 + 20, 420)], 14, (121, 85, 72))
        for a in (-1, 1): p.poly([(W / 2 + 20, 420), (W / 2 + a * 170, 470), (W / 2 + a * 60, 430)], (67, 160, 71), 5)
    # props in the scene
    props_x = []
    if any(k in low for k in ("grain pot", "clay pot", "grain sack", "grain pots", "sacks")) and painter not in (bg_sea, bg_map):
        props_x.append(("pot", None))
    if any(k in low for k in ("fire", "campfire", "bonfire")): props_x.append(("fire", None))
    if "hut" in low and "huts" not in low and "village" not in low: props_x.append(("hut", None))
    if any(k in low for k in ("boat", "canoe", "ship", "longship")): props_x.append(("boat", None))
    if any(k in low for k in ("mummy", "mummies")): props_x.append(("mummy", None))
    if any(k in low for k in ("skeleton", "grave", "bone")): props_x.append(("skeleton", None))
    if any(k in low for k in ("pyramid",)) and "egypt" not in [s.__name__ for _, s in SETTINGS]: pass
    if any(k in low for k in ("box",)) and "toolbox" not in low: props_x.append(("box", None))
    n = len(chars) + len(props_x)
    if n == 0: chars = ["CAT"] if "cat" in low else []; n = len(chars) + len(props_x)
    slots = [W / 2] if n <= 1 else [W * (i + 1) / (n + 1) for i in range(n)]
    scale = 1.15 if n <= 2 else (0.9 if n == 3 else 0.72)
    items = props_x + [(c, None) for c in chars]
    # props behind characters when a cat sits "on" them
    sit_on_pot = "on a grain pot" in low or "on the grain pot" in low or "on top of the grain" in low or "on the pot" in low
    pot_top = None
    for i, (name, _) in enumerate(items):
        x = slots[i]
        if name == "pot": pot_top = (x, grain_pot(p, x, scale))
        elif name == "fire": fire(p, x)
        elif name == "hut": hut(p, x)
        elif name == "boat": boat(p, x)
        elif name == "mummy": mummy(p, x, GROUND + 40, 1.2 * scale)
        elif name == "skeleton": skeleton(p, x - 150, GROUND + 60, 0.8)
        elif name == "box": p.rect((x - 170, GROUND - 120, x + 170, GROUND + 60), (215, 160, 90), 7)
    if STICKLY: mute_image(img)
    for i, (name, _) in enumerate(items):
        if name not in HUMAN_KINDS and name not in CATS: continue
        x = slots[i]; look = 1 if x < W / 2 else -1
        if name in HUMAN_KINDS:
            hold = "torch" if "torch" in low and name == "CAVE" else ("spear" if "spear" in low and name == "CAVE" else
                   ("sickle" if "sickle" in low else ("wheat" if "wheat" in low and "holding" in low else None)))
            ce = e if name in chars[:1] or len(chars) == 1 else ("neutral" if e in ("sleep",) else e)
            human(p, name, x, scale, ce, arms_for(scene), look, hold)
            if "crown" in low and ("{CAVE}" in scene or "{GUY}" in scene) and i == len(props_x): crown(p, x, GROUND - 590 * scale, scale)
        else:
            ce = "sleep" if e == "sleep" else ("glow" if "glowing" in low and ("eyes" in low) else e)
            if name == "CAT" and ("hiss" in low or "fur puffed" in low): ce = "angry"
            if sit_on_pot and pot_top and name in ("CAT", "HOUSECAT"):
                # draw a smaller cat sitting on the pot
                img2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p2 = P(img2, rnd)
                cat(p2, name, W / 2, 0.75, ce, look=look)
                dy = pot_top[1] - (GROUND + 40) + 20
                img.paste(img2, (int(pot_top[0] - W / 2), int(dy)), img2); p = P(img, rnd)
            else:
                cat(p, name, x, scale * (1.05 if n <= 2 else 0.95), ce, flip=-look or 1, look=look)
            if "crown" in low and name in ("CAT", "HOUSECAT"): crown(p, x, GROUND - 330 * scale, scale * 0.8)
    # mice
    if re.search(r"\bmice\b|\bmouse\b|\brats?\b", low):
        cnt = 6 if any(k in low for k in ("dozen", "crowd", "swarm", "hundreds", "many", "endless", "line")) else 2
        for k in range(cnt):
            mouse(p, rnd.randint(150, W - 150), rnd.randint(GROUND + 40, H - 190), 0.85)
    # symbols
    if any(k in low for k in ("big red x", "crossed-out", "crossed out", "red x")): big_x(p)
    if "question mark" in low:
        p.text((W - 260, 230), "?", 260, fill=(255, 255, 255), stroke=12)
    if any(k in low for k in ("heart", "love")):
        for k in range(3): heart(p, rnd.randint(300, W - 300), rnd.randint(120, 330), 0.9)
    if any(k in low for k in ("z letters", "sleeping", "asleep")):
        for k, (dx, dy) in enumerate(((0, 0), (70, -80), (150, -170))): p.text((W / 2 + 180 + dx, 260 + dy), "Z", 90 - k * 10, fill=(255, 255, 255), stroke=7)
    if "exclamation" in low: p.text((W - 260, 230), "!", 280, fill=(229, 57, 53), stroke=12)
    if any(k in low for k in ("light bulb", "lightbulb")):
        p.ell((W / 2 - 70, 70, W / 2 + 70, 230), (255, 241, 118), 6); p.rect((W / 2 - 35, 225, W / 2 + 35, 275), (158, 158, 158), 5)
    if "sparkle" in low:
        for k in range(6):
            x, y = rnd.randint(200, W - 200), rnd.randint(80, 500); p.poly([(x, y - 40), (x + 12, y - 12), (x + 40, y), (x + 12, y + 12), (x, y + 40), (x - 12, y + 12), (x - 40, y), (x - 12, y - 12)], (255, 241, 118), 3)
    num = re.search(r'"([\d,:.]+)"', scene) or re.search(r"\b(\d{1,2},\d{3}|\d{3,4})\b", scene)
    if num and any(k in low for k in ("stone", "carved", "certificate", "timeline", "clock")):
        stone_tablet(p, W / 2, 230, num.group(1))
    quoted = re.search(r'"([A-Za-z !]{3,24})"', scene)
    if quoted and not num:
        p.text((W / 2, 140), quoted.group(1).upper(), 110)
    # caption (narration line)
    if not caption:
        img.save(out, quality=92); return
    words = caption.strip()
    f = ImageFont.truetype(FONT, 62)
    lines, cur = [], ""
    for wd in words.split():
        t = (cur + " " + wd).strip()
        if p.d.textlength(t, font=f) > W - 220: lines.append(cur); cur = wd
        else: cur = t
    lines.append(cur)
    y0 = H - 125 - 76 * (len(lines) - 1)
    for k, ln in enumerate(lines):
        p.text((W / 2, y0 + k * 76), ln, 62, fill=(255, 255, 255), stroke=9)
    img.save(out, quality=92)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    only = None
    if "--only" in sys.argv: only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    root = os.path.join(os.path.dirname(__file__), "..")
    lines, i = [], 0
    for b in load(root):
        ctx = {}
        for l in b["lines"]:
            i += 1; lines.append(l)
            if only and i not in only:
                # keep context flowing even for skipped frames
                low = l["scene"].lower(); ctx["setting"] = pick_setting(low) or ctx.get("setting")
                ctx["chars"] = characters(l["scene"]) or ctx.get("chars", [])
                continue
            render(l["scene"], None if "--no-caption" in sys.argv else l["text"], i, os.path.join(out, f"{i:03d}.jpg"), ctx)
    print("frames:", len(lines) if not only else len(only))
