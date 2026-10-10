"""Draw simple MS-Paint-style frames for every script line (fallback when no AI images are available).

usage: python3 tools/paint_frames.py <out_dir> [--only N,N,...]
Each frame is built from the line's scene description: a setting (day, night, desert, Egypt, sea, lab ...),
up to four characters (each with its own expression), a few props/symbols, and the narration line as a caption.
"""
import math, os, random, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
from parse_script import load

W, H = int(os.environ.get("FRAME_W", 1920)), int(os.environ.get("FRAME_H", 1080))
GROUND = int(os.environ.get("FRAME_GROUND", 800))
CHAR_SCALE = float(os.environ.get("FRAME_SCALE", 1.0))   # bigger characters for vertical Shorts frames
TOPY = GROUND - 800                                        # shifts overlay symbols down on tall canvases
TITLE_BOTTOM = 410 if TOPY > 0 else 0                      # the Shorts title band (drawn later as captions)
SKY_Y = TOPY - 90 if TOPY > 0 else 70                      # sun / moon row, just under the title
OL = (20, 20, 20)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SKIN = (255, 222, 186)
FACE = {"nobrow": False, "tears": False, "sweat": False, "old": False}                   # per-scene face options, set by render()
SKY = {"moon": True, "discs": []}                          # no moon when a quoted word fills the sky row; sun/moon spots

def X(v): return v * W / 1920      # x of a layout designed for the 1920-wide frame
def Y(v): return v + TOPY          # y of a sky element, kept at the same height above the ground

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

def stars(p, n, y1):
    for _ in range(n):
        x, y = p.r.randint(0, W), p.r.randint(0, int(y1)); p.d.ellipse((x, y, x + 6, y + 6), fill=(255, 255, 220))

def moon(p):
    if not SKY["moon"]: return
    mx, my = p.r.choice([(60, SKY_Y), (W - 260, SKY_Y)] if TOPY > 0 else [(200, 140), (1650, 150)])
    sky = p.img.getpixel((int(min(mx + 178, W - 1)), int(my + 60)))
    p.d.ellipse((mx, my, mx + 130, my + 130), fill=(255, 255, 240)); p.d.ellipse((mx + 40, my - 15, mx + 170, my + 115), fill=sky)
    SKY["discs"].append((mx + 65, my + 65, 80))

def bg_day(p):
    p.rect((-10, -10, W + 10, H + 10), (79, 195, 247), 0); mountains(p); grass(p)
    for _ in range(2):
        x = p.r.randint(100, W - 300)
        y = p.r.randint(SKY_Y, SKY_Y + 60) if TOPY > 0 else p.r.randint(60, 220)
        for dx in (0, 70, 140): p.ell((x + dx, y, x + dx + 120, y + 70), (255, 255, 255), 4)

def bg_night(p):
    p.rect((-10, -10, W + 10, H + 10), (26, 35, 90), 0)
    stars(p, 40 if TOPY == 0 else 60, Y(500)); moon(p)
    mountains(p, (90, 90, 110)); grass(p, (30, 90, 40))

def night_overlay(p, outdoor):
    """Darken any background for scenes that say night/moon; outdoors also gets stars and a moon."""
    p.img.paste(Image.blend(p.img, Image.new("RGB", p.img.size, (16, 24, 66)), 0.55))
    if outdoor:
        stars(p, 30, max(SKY_Y + 200, 220)); moon(p)

def bg_interior(p):
    p.rect((-10, -10, W + 10, H + 10), (78, 52, 46), 0)
    for y in range(40, GROUND, 90):
        off = 0 if (y // 90) % 2 else 110
        for x in range(-off, W, 220): p.d.rectangle((x, y, x + 210, y + 80), outline=(55, 35, 30), width=5)
    p.rect((-10, GROUND, W + 10, H + 10), (93, 64, 55))

def bg_desert(p):
    p.rect((-10, -10, W + 10, H + 10), (144, 202, 249), 0)
    sx, sy = (W - 315, SKY_Y - 10) if TOPY > 0 else (1550, 70)
    p.ell((sx, sy, sx + 170, sy + 170), (255, 213, 79)); SKY["discs"].append((sx + 85, sy + 85, 95))
    p.poly([(-50, GROUND - 40), (X(600), GROUND - 160), (X(1300), GROUND - 60), (W + 50, GROUND - 180), (W + 50, H + 10), (-50, H + 10)], (251, 192, 45))
    p.rect((-10, GROUND + 20, W + 10, H + 10), (240, 180, 40))

def bg_egypt(p):
    bg_desert(p)
    for x, s in ((250, 380), (700, 260), (1450, 330)):
        p.poly([(X(x) - s, GROUND - 20), (X(x), GROUND - 20 - s * 1.1), (X(x) + s, GROUND - 20)], (230, 190, 90))
    p.poly([(-20, GROUND + 60), (W + 20, GROUND + 30), (W + 20, GROUND + 120), (-20, GROUND + 150)], (66, 165, 245))

def bg_sea(p):
    p.rect((-10, -10, W + 10, H + 10), (129, 212, 250), 0)
    p.rect((-10, Y(520), W + 10, H + 10), (30, 136, 229))
    for y in range(Y(580), H, 70):
        for x in range(0, W, 160): p.d.arc((x, y, x + 110, y + 40), 200, 340, fill=(255, 255, 255), width=5)

def bg_lab(p):
    p.rect((-10, -10, W + 10, H + 10), (224, 224, 224), 0)
    p.rect((-10, GROUND, W + 10, H + 10), (176, 190, 197))
    cols = [(239, 83, 80), (102, 187, 106), (66, 165, 245), (255, 202, 40)]
    if TOPY > 0:     # tall frame: a lab bench with flasks behind the characters, visible between them
        top = GROUND - 260
        p.rect((-10, top, W + 10, top + 34), (141, 110, 99)); p.rect((-10, top + 34, W + 10, GROUND), (189, 189, 189), 5)
        for i in range(8):
            x = 40 + i * (W - 80) / 8 + 20; c = cols[i % 4]
            p.rect((x, top - 110, x + 46, top), c, 4); p.rect((x + 12, top - 150, x + 34, top - 110), (236, 239, 241), 4)
        return
    p.rect((1300, 220, 1800, 250), (141, 110, 99))
    for i, c in enumerate(cols):
        x = 1340 + i * 110; p.rect((x, 120, x + 40, 220), c, 4)

def bg_classroom(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 236, 179), 0)
    p.rect((X(200), Y(80), X(1720), Y(560)), (46, 125, 50), 10)
    p.rect((-10, GROUND, W + 10, H + 10), (161, 136, 127))

def bg_living(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 224, 178), 0)
    p.rect((X(1400), Y(120), X(1800), Y(480)), (179, 229, 252), 8)
    p.line([(X(1600), Y(120)), (X(1600), Y(480))], 8); p.line([(X(1400), Y(300)), (X(1800), Y(300))], 8)
    p.rect((-10, GROUND, W + 10, H + 10), (188, 143, 100))
    for x in range(0, W, 240): p.line([(x, GROUND), (x - 80, H)], 4)

def couch(p):
    col = (141, 110, 99)
    p.rect((40, GROUND - 340, W - 40, GROUND - 130), col, 6)
    p.rect((20, GROUND - 170, W - 20, GROUND - 30), (161, 128, 115), 6)
    for x0 in (10, W - 110): p.rect((x0, GROUND - 250, x0 + 100, GROUND - 20), col, 6)

def bg_medieval(p):
    p.rect((-10, -10, W + 10, H + 10), (120, 130, 145), 0)
    for i, x in enumerate(range(-50, W, 330)):
        h = 300 + (i % 3) * 60
        p.poly([(x, GROUND), (x, GROUND - h), (x + 140, GROUND - h - 120), (x + 280, GROUND - h), (x + 280, GROUND)], (121, 85, 72))
        p.rect((x + 100, GROUND - 140, x + 180, GROUND), (62, 39, 35), 5)
    p.rect((-10, GROUND, W + 10, H + 10), (97, 97, 97))

def bg_village(p):
    bg_day(p)
    for x in ((120, 1500) if TOPY == 0 else (20, W - 320)):
        p.rect((x, GROUND - 260, x + 300, GROUND + 10), (188, 143, 100))
        p.poly([(x - 30, GROUND - 260), (x + 150, GROUND - 380), (x + 330, GROUND - 260)], (161, 136, 60))
        p.rect((x + 110, GROUND - 130, x + 190, GROUND + 10), (62, 39, 35), 5)

def bg_map(p):
    p.rect((-10, -10, W + 10, H + 10), (100, 181, 246), 0)
    blobs = [(150, 200, 800, 700), (900, 150, 1700, 650), (1100, 600, 1500, 1000), (300, 650, 650, 1000)]
    for x0, y0, x1, y1 in blobs: p.ell((X(x0), y0 * H / 1080, X(x1), y1 * H / 1080), (165, 214, 167))

def bg_space(p):
    p.rect((-10, -10, W + 10, H + 10), (13, 17, 40), 0)
    for _ in range(80):
        x, y = p.r.randint(0, W), p.r.randint(0, H); p.d.ellipse((x, y, x + 5, y + 5), fill=(255, 255, 255))
    p.ell((-400, Y(820), W + 400, Y(2400)), (66, 165, 245))

def bg_red(p):
    p.rect((-10, -10, W + 10, H + 10), (183, 28, 28), 0); grass(p, (120, 20, 20))

def bg_plain(p):
    p.rect((-10, -10, W + 10, H + 10), (255, 249, 196), 0)

def bg_timeline(p):
    bg_plain(p); p.line([(X(120), Y(420)), (X(1800), Y(420))], 12)
    p.poly([(X(1800), Y(390)), (X(1800) + 60, Y(420)), (X(1800), Y(450))], OL, 4)
    for x in range(200, 1800, 200): p.line([(X(x), Y(400)), (X(x), Y(440))], 8)

def bg_jungle(p):
    p.rect((-10, -10, W + 10, H + 10), (129, 199, 132), 0)
    for x in range(-50, W, 260):
        p.rect((x + 80, 0, x + 140, GROUND + 20), (121, 85, 72), 5)
        p.ell((x - 40, -60, x + 260, 260), (46, 125, 50), 6)
    for x in range(0, W, 180): p.line([(x, 0), (x + 30, 300)], 6, (56, 142, 60))
    grass(p, (85, 139, 47))

def bg_greek(p):
    p.rect((-10, -10, W + 10, H + 10), (129, 212, 250), 0)
    p.rect((-10, Y(560), W + 10, GROUND), (30, 136, 229))
    p.rect((X(250), Y(150), X(1670), Y(230)), (245, 245, 240)); p.poly([(X(220), Y(150)), (X(960), Y(40)), (X(1700), Y(150))], (245, 245, 240))
    cw = 70 if TOPY == 0 else 44
    for x in range(300, 1700, 230): p.rect((X(x), Y(230), X(x) + cw, GROUND), (245, 245, 240), 6)
    p.rect((-10, GROUND, W + 10, H + 10), (215, 204, 200))

def bg_mesop(p):
    bg_desert(p)
    p.poly([(X(1150), GROUND - 20), (X(1250), GROUND - 160), (X(1550), GROUND - 160), (X(1650), GROUND - 20)], (188, 143, 100))
    p.poly([(X(1250), GROUND - 160), (X(1320), GROUND - 280), (X(1480), GROUND - 280), (X(1550), GROUND - 160)], (188, 143, 100))
    p.rect((X(1360), GROUND - 360, X(1440), GROUND - 280), (188, 143, 100))
    for x in ((100, 500) if TOPY == 0 else (40,)):
        p.rect((x, GROUND - 200, x + 260, GROUND + 10), (205, 160, 110)); p.rect((x + 95, GROUND - 100, x + 165, GROUND + 10), (62, 39, 35), 5)

def bg_cave(p):
    p.rect((-10, -10, W + 10, H + 10), (93, 64, 55), 0)
    p.poly([(-10, -10), (W + 10, -10), (W + 10, 160), (1500, 260), (1100, 180), (700, 270), (300, 170), (-10, 250)], (62, 39, 35), 6)
    p.rect((-10, GROUND, W + 10, H + 10), (121, 85, 72))

SETTINGS = [
    (("jungle", "forest floor", "palm tree", "vine", "treeshrew", "mango"), bg_jungle),
    (("greek", "greece", "symposium", "kottabos", "marble", "toga", "senate", "senator", "roman", "bacchus"), bg_greek),
    (("sumer", "sumerian", "mesopotamia", "babylon", "ur", "hammurabi", "ninkasi", "tavern keeper", "cuneiform", "scribe", "enkidu", "wild man", "gilgamesh", "shepherds", "wedge-shaped", "clay tablet"), bg_mesop),
    (("cave", "stone bowl", "stone mortar", "mortar"), bg_cave),  # (keywords, painter) - first match wins
    (("space", "rocket", "capsule", "orbit"), bg_space),
    (("timeline", "calendar", "family tree", "diagram", "bar chart", "chain of icons"), bg_timeline),
    (("map", "globe", "the earth", "world map"), bg_map),
    (("lab", "microscope", "computer screen", "dna", "x-ray", "brain scan", "journal"), bg_lab),
    (("chalkboard", "classroom", "whiteboard", "blueprint"), bg_classroom),
    (("medieval", "witch", "pope", "castle", "plague", "bonfire", "villagers"), bg_medieval),
    (("egypt", "pyramid", "nile", "pharaoh", "bastet", "temple", "mummy", "mummies", "tomb", "sekhmet", "ra", "hieroglyph"), bg_egypt),
    (("sea", "boat", "ship", "canoe", "viking", "island", "harbor", "port", "waves", "baltic"), bg_sea),
    (("desert", "savanna", "sand", "sun-baked"), bg_desert),
    (("storehouse", "granary", "grain pot", "torch", "dark corner", "darkness", "barn", "warehouse", "post office", "den", "tavern", "monastery", "hall"), bg_interior),
    (("couch", "sofa", "living room", "bedroom", "apartment", "laptop", "bed", "mattress", "kitchen", "table", "desk", "bathtub", "box", "window", "pet store", "café", "office", "video call", "door"), bg_living),
    (("night", "moon", "3:00", "5:00", "dark hallway", "stars"), bg_night),
    (("village", "hut", "huts", "mud-brick"), bg_village),
    (("turning red", "dramatic"), bg_red),
]
INDOOR = (bg_interior, bg_lab, bg_classroom, bg_living, bg_cave, bg_plain, bg_timeline, bg_red, bg_space, bg_map)

# ----------------------------------------------------------------------------- characters
EXPR = [  # (keywords, expression) - matched at the start of a word, first group wins
    (("sleep", "asleep", "z letters", "eyes closed", "closed eyes", "slowly closing", "dozing"), "sleep"),
    (("hiss", "angry", "furious", "glaring", "glare", "frowning", "offended", "shouting", "unhappy", "disgust"), "angry"),
    (("shock", "surpris", "horror", "terrified", "frightened", "scared", "jaw dropped", "jaws dropped", "eyes huge", "eyes wide",
      "wide awake", "alarmed", "gasping", "mouth open", "freezing", "frozen", "panic", "worried", "sweating", "nervous", "paranoid"), "shock"),
    (("sad", "cry", "tears", "disappointed", "mourning", "sigh", "pitying"), "sad"),
    (("confus", "question mark", "scratching his head", "squinting", "thinking"), "confused"),
    (("smug", "smirk", "evil genius", "unbothered", "unimpressed", "bored", "yawning", "ignoring", "like a king"), "smug"),
    (("happy", "smil", "cheer", "laugh", "proud", "thumbs up", "joy", "goofy", "love", "heart", "satisfied", "hug", "waving",
      "excited", "celebrat", "dancing", "relieved"), "happy"),
]

def expr_or_none(text):
    s = text.lower()
    for keys, e in EXPR:
        if any(re.search(r"\b" + re.escape(k), s) for k in keys): return e
    return None

def expression(scene):
    return expr_or_none(scene) or "neutral"

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
            if FACE["nobrow"]: continue
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
    "APE":   dict(shirt=(93, 64, 55), legs=(93, 64, 55), hair="messy", hair_col=(78, 52, 46), skin=(230, 195, 160), fur=True, ears=True),
    "SUMER": dict(shirt=(230, 210, 170), legs=(200, 150, 100), hair="bald", hair_col=(20, 20, 20), skin=(200, 150, 100), beard=True),
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
    hand = 1                                                  # index of the hand that points / holds things
    if arms == "up": targets = [(x - 150 * s, neck - 160 * s), (x + 150 * s, neck - 160 * s)]
    elif arms == "point":                                     # point toward the middle of the frame
        if look < 0: targets = [(x - 210 * s, neck + 20 * s), (x + 95 * s, hip + 10 * s)]; hand = 0
        else: targets = [(x - 95 * s, hip + 10 * s), (x + 210 * s, neck + 20 * s)]
    elif arms == "head": targets = [(x - hr - 40 * s, hy + 10 * s), (x + hr + 40 * s, hy + 10 * s)]   # hands beside the head
    elif arms == "shrug": targets = [(x - 170 * s, neck - 20 * s), (x + 170 * s, neck - 20 * s)]
    else: targets = [(x - 105 * s, hip + 20 * s), (x + 105 * s, hip + 20 * s)]
    for (tx, ty), sx in zip(targets, (-1, 1)):
        a = (x + sx * 52 * s, neck + 18 * s)
        p.line([a, (tx, ty)], int(30 * s) + 8); p.line([a, (tx, ty)], int(30 * s), coat)
        p.d.ellipse((tx - 17 * s, ty - 17 * s, tx + 17 * s, ty + 17 * s), fill=OL)
    if hold: prop(p, hold, targets[hand][0], targets[hand][1], s)
    hair = {"messy": (70, 50, 38), "short": (45, 38, 32), "long": (20, 20, 20), "bob": (20, 20, 20)}.get(c["hair"])
    if c.get("fur"): hair = (90, 68, 52)
    if kind == "SCI" or FACE["old"]: hair = (165, 165, 165)
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
        p.ell((x - hr * 0.8, hy - hr * (0.8 if FACE["nobrow"] else 0.45), x + hr * 0.8, hy + hr), CREAM, 0)
    if c.get("helmet"):
        p.d.chord((x - hr * 1.05, hy - hr * 1.1, x + hr * 1.05, hy + hr * 0.3), 180, 360, fill=(140, 140, 140), outline=OL, width=5)
    if c.get("beard"):
        p.d.chord((x - hr * 0.75, hy + hr * 0.1, x + hr * 0.75, hy + hr * 1.5), 0, 180, fill=(30, 30, 30), outline=OL, width=5)
    eyes(p, x, hy + hr * 0.02, hr * 0.33, e, look)
    if FACE["nobrow"]:                                        # bare shiny forehead and shaved-brow stubble
        sy0 = -0.64 if c["hair"] == "bob" else -0.37
        p.d.ellipse((x - hr * 0.4, hy + hr * sy0, x + hr * 0.02, hy + hr * (sy0 + 0.12)), fill=(255, 255, 255))
        for sx in (-1, 1):
            ex = x + sx * hr * 0.35 + look * hr * 0.08
            for k in (-1, 0, 1): p.d.ellipse((ex + k * hr * 0.09 - 3 * s, hy - hr * 0.19 - 3 * s, ex + k * hr * 0.09 + 3 * s, hy - hr * 0.19 + 3 * s), fill=(214, 150, 140))
    if FACE["sweat"]:
        p.ell((x + hr * 0.92, hy - hr * 0.7, x + hr * 1.12, hy - hr * 0.32), (129, 212, 250), 3)
    if c.get("glasses"):
        for dx in (-1, 1): p.d.ellipse((x + dx * hr * 0.35 - hr * 0.3, hy - hr * 0.3, x + dx * hr * 0.35 + hr * 0.3, hy + hr * 0.3), outline=OL, width=5)
    if not c.get("beard"): mouth(p, x, hy + hr * 0.42, s, e)
    if e == "sad" and FACE["tears"]:
        for sx in (-1, 1):
            tx = x + sx * hr * 0.35 + look * hr * 0.08
            p.ell((tx - hr * 0.08, hy + hr * 0.14, tx + hr * 0.08, hy + hr * 0.42), (100, 181, 246), 3)
    return dict(x=x, s=s, look=look, head=(x, hy, hr * 1.05), top=hy - hr * 1.12, mouth=(x, hy + hr * 0.42),
                body=(x - 85 * s, neck, x + 85 * s, gy), hand=targets[hand], hw=85 * s)

def ape_stickly(p, x, s, e, arms, look):
    """Chimp: dark fur all over, pale face and muzzle, big round ears, hunched body, long arms down to the knees."""
    gy = GROUND + 40; fur = mute((92, 64, 50), 0.3); face = (228, 198, 160)
    hr = 100 * s; hx = x + look * 18 * s; hy = gy - 455 * s
    for sx in (-1, 1):
        pts = [(x + sx * 45 * s, gy - 170 * s), (x + sx * 85 * s, gy - 85 * s), (x + sx * 70 * s, gy - 8 * s)]
        p.line(pts, int(40 * s) + 8); p.line(pts, int(40 * s), fur)
        p.d.ellipse((x + sx * 70 * s - 32 * s, gy - 20 * s, x + sx * 70 * s + 32 * s, gy + 10 * s), fill=OL)
    p.ell((x - 115 * s, gy - 390 * s, x + 115 * s, gy - 120 * s), fur, 5)
    p.ell((x - 58 * s, gy - 330 * s, x + 58 * s, gy - 175 * s), mute((150, 115, 90), 0.3), 0)
    hand = 1
    if arms == "up": targets = [(x - 175 * s, gy - 640 * s), (x + 175 * s, gy - 640 * s)]
    elif arms == "point":
        if look < 0: targets = [(x - 235 * s, gy - 380 * s), (x + 150 * s, gy - 60 * s)]; hand = 0
        else: targets = [(x - 150 * s, gy - 60 * s), (x + 235 * s, gy - 380 * s)]
    elif arms == "head": targets = [(hx - hr - 40 * s, hy), (hx + hr + 40 * s, hy)]
    elif arms == "shrug": targets = [(x - 200 * s, gy - 380 * s), (x + 200 * s, gy - 380 * s)]
    else: targets = [(x - 150 * s, gy - 70 * s), (x + 150 * s, gy - 70 * s)]
    for (tx, ty), sx in zip(targets, (-1, 1)):
        a = (x + sx * 88 * s, gy - 345 * s)
        p.line([a, (tx, ty)], int(36 * s) + 8); p.line([a, (tx, ty)], int(36 * s), fur)
        p.d.ellipse((tx - 22 * s, ty - 22 * s, tx + 22 * s, ty + 22 * s), fill=OL)
    for sx in (-1, 1):
        ex = hx + sx * hr * 1.02
        p.ell((ex - hr * 0.36, hy - hr * 0.42, ex + hr * 0.36, hy + hr * 0.3), fur, 5)
        p.ell((ex - hr * 0.19, hy - hr * 0.25, ex + hr * 0.19, hy + hr * 0.13), face, 0)
    p.ell((hx - hr, hy - hr, hx + hr, hy + hr), fur, 5)
    p.ell((hx - hr * 0.72, hy - hr * 0.62, hx + hr * 0.72, hy + hr * 0.82), face, 4)
    p.ell((hx - hr * 0.52, hy + hr * 0.14, hx + hr * 0.52, hy + hr * 0.86), (238, 214, 182), 4)
    eyes(p, hx, hy - hr * 0.2, hr * 0.27, e, look)
    for sx in (-1, 1): p.d.ellipse((hx + sx * hr * 0.12 - 5 * s, hy + hr * 0.3 - 4 * s, hx + sx * hr * 0.12 + 5 * s, hy + hr * 0.3 + 4 * s), fill=OL)
    mouth(p, hx, hy + hr * 0.56, s * 0.9, e)
    return dict(x=x, s=s, look=look, head=(hx, hy, hr * 1.3), top=hy - hr * 1.05, mouth=(hx, hy + hr * 0.56),
                body=(x - 120 * s, gy - 390 * s, x + 120 * s, gy), hand=targets[hand], hw=120 * s)

def human(p, kind, x, s, e, arms="down", look=0, hold=None):
    if STICKLY:
        if kind == "APE": return ape_stickly(p, x, s, e, arms, look)
        return human_stickly(p, kind, x, s, e, arms, look, hold)
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
    if c.get("ears"):
        for sx in (-1, 1): p.ell((x + sx * hr * 1.05 - hr * 0.35, hy - hr * 0.3, x + sx * hr * 1.05 + hr * 0.35, hy + hr * 0.4), skin, 5)
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
    if c.get("beard"):
        p.poly([(x - hr * 0.8, hy + hr * 0.5), (x + hr * 0.8, hy + hr * 0.5), (x + hr * 0.45, hy + hr * 1.7), (x - hr * 0.45, hy + hr * 1.7)], c["hair_col"], 5)
    eyes(p, x, hy - hr * 0.05, hr * 0.33, e, look)
    if c.get("glasses"):
        for dx in (-1, 1): p.d.ellipse((x + dx * hr * 0.35 - hr * 0.42, hy - hr * 0.47, x + dx * hr * 0.35 + hr * 0.42, hy + hr * 0.37), outline=OL, width=6)
    if not c.get("beard"): mouth(p, x, hy + hr * 0.5, s, e)
    if e == "sad": p.ell((x + hr * 0.5, hy + hr * 0.3, x + hr * 0.65, hy + hr * 0.55), (100, 181, 246), 3)
    if e == "shock" or "sweat" in kind: p.ell((x + hr * 1.0, hy - hr * 0.7, x + hr * 1.18, hy - hr * 0.4), (129, 212, 250), 3)
    return dict(x=x, s=s, look=look, head=(x, hy, hr * 1.1), top=hy - hr * 1.15, mouth=(x, hy + hr * 0.5),
                body=(x - 80 * s, neck, x + 80 * s, gy), hand=targets[1], hw=80 * s)

CATS = {
    "CAT": dict(body=(215, 179, 119), stripe=(120, 90, 50)),
    "HOUSECAT": dict(body=(251, 140, 0), stripe=(200, 90, 0)),
    "BLACKCAT": dict(body=(40, 40, 40), stripe=None, eye=(255, 235, 59)),
    "LEOPARDCAT": dict(body=(230, 190, 120), spots=(90, 60, 30)),
    "PERSIAN": dict(body=(250, 250, 250), stripe=None, fluffy=True),
    "SPHYNX": dict(body=(248, 187, 208), stripe=None),
    "MAINECOON": dict(body=(141, 110, 99), stripe=(90, 60, 40), fluffy=True),
    "DOG": dict(body=(161, 110, 70), stripe=None, dog=True),
    "LION": dict(body=(214, 170, 90), stripe=None, mane=(150, 90, 40)),
    "LEOPARD": dict(body=(230, 190, 110), spots=(60, 40, 20)),
    "HYENA": dict(body=(190, 160, 110), spots=(90, 70, 40), dog=True),
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
    if c.get("mane"):
        for i in range(14):
            a = i * 2 * math.pi / 14
            p.ell((hx + hr * 1.15 * math.cos(a) - hr * 0.42, hy + hr * 1.1 * math.sin(a) - hr * 0.42, hx + hr * 1.15 * math.cos(a) + hr * 0.42, hy + hr * 1.1 * math.sin(a) + hr * 0.42), mute(c["mane"], 0.35), 4)
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
        for dx in (-1, 1):
            ex = hx + dx * er * 1.15; box = (ex - er, hy - er * 1.2, ex + er, hy + er * 0.6)
            if kind == "BLACKCAT" and e in ("sleep", "happy"):
                if e == "sleep": p.line([(ex - er * 0.8, hy - er * 0.3), (ex + er * 0.8, hy - er * 0.3)], 6, (255, 235, 59))
                else: p.d.arc((ex - er * 0.75, hy - er * 0.9, ex + er * 0.75, hy + er * 0.3), 200, 340, fill=(255, 235, 59), width=8)
                continue
            p.ell(box, (255, 235, 59), 4)
            if kind != "BLACKCAT": continue
            inner, outer = ex - dx * er * 1.05, ex + dx * er * 1.05
            lid = {"angry": (hy - er * 0.85, hy - er * 1.5), "sad": (hy - er * 1.5, hy - er * 0.9),
                   "smug": (hy - er * 0.55, hy - er * 0.55), "neutral": (hy - er * 0.7, hy - er * 0.7), "confused": (hy - er * 0.7, hy - er * 0.5)}.get(e)
            if lid:
                p.d.polygon([(inner, lid[0]), (outer, lid[1]), (outer, hy - er * 1.7), (inner, hy - er * 1.7)], fill=c["body"])
                p.line([(inner, lid[0]), (outer, lid[1])], 6)
            if e == "shock": p.d.ellipse((ex - er * 0.22, hy - er * 0.5, ex + er * 0.22, hy - er * 0.06), fill=OL)
    else:
        eyes(p, hx, hy - er * 0.3, er, e, look)
    p.poly([(hx - 12 * s, hy + hr * 0.3), (hx + 12 * s, hy + hr * 0.3), (hx, hy + hr * 0.45)], (240, 98, 146), 3)
    for sx in (-1, 1):
        for dy in (-8, 8): p.line([(hx + sx * hr * 0.35, hy + hr * 0.45 + dy * s), (hx + sx * hr * 1.25, hy + hr * 0.35 + dy * 2.5 * s)], 3)
    mouth(p, hx, hy + hr * 0.5, s * 0.6, e if e != "shock" else "shock")
    return dict(x=x, s=s, look=look, head=(hx, hy, hr * (1.5 if c.get("mane") else 1.1)), top=hy - hr * 1.35,
                mouth=(hx, hy + hr * 0.5), body=(x - 120 * s, by - 120 * s, x + 120 * s, gy), hand=(hx, hy), hw=125 * s,
                mane=bool(c.get("mane")))

def mouse(p, x, y, s=0.5, dead=False):
    if dead:                                                  # belly up, legs in the air, X eyes
        p.line([(x - 55 * s, y - 5 * s), (x - 140 * s, y + 10 * s)], 5)
        for dx in (-30, -8, 14, 34): p.line([(x + dx * s, y - 38 * s), (x + dx * s + 6 * s, y - 72 * s)], 5)
        p.ell((x - 60 * s, y - 45 * s, x + 60 * s, y + 18 * s), (176, 176, 176), 5)
        p.ell((x + 30 * s, y - 2 * s, x + 66 * s, y + 30 * s), (240, 180, 190), 4)
        ex, ey, k = x + 32 * s, y - 16 * s, 9 * s
        p.line([(ex - k, ey - k), (ex + k, ey + k)], 4); p.line([(ex - k, ey + k), (ex + k, ey - k)], 4)
        return
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

def fire(p, x, s=1.0):
    gy = GROUND + 40
    for dx in (-60, 0, 60):
        log = [(x + (dx - 50) * s, gy), (x + (dx + 50) * s, gy - 30 * s)]
        p.line(log, int(18 * s) + 8); p.line(log, int(18 * s), (121, 85, 72))
    p.poly([(x - 90 * s, gy - 20 * s), (x - 40 * s, gy - 170 * s), (x, gy - 90 * s), (x + 30 * s, gy - 230 * s), (x + 90 * s, gy - 20 * s)], (255, 112, 67), 6)
    p.poly([(x - 45 * s, gy - 25 * s), (x, gy - 130 * s), (x + 45 * s, gy - 25 * s)], (255, 235, 59), 4)

def hut(p, x):
    gy = GROUND + 40
    p.rect((x - 170, gy - 260, x + 170, gy), (188, 143, 100)); p.poly([(x - 200, gy - 260), (x, gy - 400), (x + 200, gy - 260)], (161, 136, 60))
    p.rect((x - 45, gy - 140, x + 45, gy), (62, 39, 35), 5)

def boat(p, x, y=640):
    p.poly([(x - 330, y), (x + 330, y), (x + 240, y + 110), (x - 240, y + 110)], (141, 98, 60), 7)
    p.line([(x, y), (x, y - 330)], 10)
    p.poly([(x + 8, y - 320), (x + 230, y - 120), (x + 8, y - 60)], (255, 248, 225), 6)

def bed(p, x, s, part="all"):
    """part: 'all' = a bed standing on its own; 'back' = headboard behind a person; 'front' = blanket over a person in bed."""
    gy = GROUND + 40; hw = 160 * s; m = mute if part == "front" else (lambda c: c)
    if part in ("all", "back"):
        p.rect((x - hw - 14 * s, gy - 310 * s, x - hw + 22 * s, gy), m((141, 98, 60)), 5)
        p.ell((x - hw + 10 * s, gy - 245 * s, x - hw + 115 * s, gy - 185 * s), m((255, 255, 255)), 4)
    if part == "back": return
    top = gy - (235 if part == "front" else 190) * s
    p.rect((x - hw, top, x + hw, gy - 60 * s), m((250, 250, 245)), 5)
    p.rect((x - hw + (40 if part == "front" else 90) * s, top - 10 * s, x + hw + 8 * s, gy - 50 * s), m((110, 150, 200)), 5)
    p.rect((x - hw + (40 if part == "front" else 90) * s, top - 10 * s, x + hw + 8 * s, top + 22 * s), m((250, 250, 245)), 5)
    if part == "front": p.rect((x - hw - 6 * s, gy - 70 * s, x + hw + 14 * s, gy + 4 * s), m((141, 98, 60)), 5)
    else:
        for lx in (x - hw + 4 * s, x + hw - 22 * s): p.rect((lx, gy - 60 * s, lx + 18 * s, gy), m((121, 85, 72)), 4)

def nest(p, x, s):
    gy = GROUND + 40; hw = 175 * s
    p.d.chord((x - hw, gy - 190 * s, x + hw, gy + 10 * s), 0, 180, fill=mute((121, 85, 60), 0.3), outline=OL, width=5)
    for i in range(7):
        a = x - hw * 0.85 + i * hw * 0.26
        p.line([(a, gy - 85 * s), (a + 55 * s, gy - 25 * s)], 5); p.line([(a + 55 * s, gy - 85 * s), (a, gy - 25 * s)], 5)
    for i in range(6):
        lx = x - hw + 25 * s + i * hw * 0.36
        p.ell((lx - 28 * s, gy - 122 * s, lx + 28 * s, gy - 80 * s), mute((76, 160, 70), 0.3), 4)

def straw(p, pts, s, gold=False):
    w = max(8, int(12 * s))
    p.line(pts, w + 8); p.line(pts, w, (240, 196, 60) if gold else mute((236, 214, 160), 0.2))
    if gold:                                                  # lapis lazuli bands
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (70 * s)))
            for k in range(n):
                t = (k + 0.5) / n; bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                p.d.ellipse((bx - w * 0.75, by - w * 0.75, bx + w * 0.75, by + w * 0.75), fill=(30, 80, 200), outline=OL, width=3)

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

def sparkle(p, x, y, r=40):
    k = r * 0.3
    p.poly([(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)], (255, 241, 118), 3)

def big_x(p, cx, cy, r):
    w = max(26, int(r * 0.2))
    for a, b in (((cx - r, cy - r), (cx + r, cy + r)), ((cx + r, cy - r), (cx - r, cy + r))):
        p.d.line([a, b], fill=OL, width=w + 10); p.d.line([a, b], fill=(229, 57, 53), width=w)

def stone_tablet(p, x, y, label, s=1.0):
    p.poly([(x - 200 * s, y + 130 * s), (x - 210 * s, y - 90 * s), (x - 120 * s, y - 150 * s), (x + 120 * s, y - 150 * s), (x + 210 * s, y - 90 * s), (x + 200 * s, y + 130 * s)], (176, 176, 176), 7)
    p.text((x, y - 5 * s), label, int((95 if len(label) < 6 else 70) * s), fill=(80, 80, 80), stroke=0)

def free_spots(rnd, k, size, circles, rects, near=None, tries=500):
    """Up to k points for small symbols that keep clear of heads, bodies, the title band and each other."""
    y0, y1 = TITLE_BOTTOM + size + 10, GROUND - 100
    cands = []
    for _ in range(tries):
        x, y = rnd.uniform(70 + size, W - (160 if TOPY > 0 else 70) - size), rnd.uniform(y0, y1)
        if any(math.hypot(x - cx, y - cy) < r + size * 0.9 for cx, cy, r in circles): continue
        if any(a - size * 1.05 < x < c + size * 1.05 and b - size * 1.05 < y < d + size * 1.05 for a, b, c, d in rects): continue
        cands.append((x, y))
    if near: cands.sort(key=lambda q: math.hypot(q[0] - near[0], q[1] - near[1]))
    picked = []
    for q in cands:
        if all(math.hypot(q[0] - u[0], q[1] - u[1]) > size * 2.3 for u in picked): picked.append(q)
        if len(picked) == k: break
    return picked

# ----------------------------------------------------------------------------- scene composer
CHAR_WORDS = [
    (r"\{APE\}|\bapes?\b|chimp|monkey", "APE"), (r"\{SUMER\}|sumerians?|scribe|tavern keeper|babylon|wild man|enkidu|shepherds?", "SUMER"),
    (r"\{CAVE\}|farmer|caveman|cavemen|cavepeople|hunter|natufian|worker|early humans?|homo erectus|teenager|volunteer", "CAVE"), (r"\{WOMAN\}|prehistoric woman|old woman|old cavewoman|grandmother|witch", "WOMAN"),
    (r"\{GUY\}|stranger|customer|tourists?|postmaster", "GUY"), (r"\{EGYPT\}|egyptians?|pharaoh|pilgrim", "EGYPT"),
    (r"\{SCI\}|historians?|scientists?|diodorus|herodotus|greek man|researcher", "SCI"),
    (r"roman|emperor|greek man|greek men|senators?|soldiers?", "ROMAN"), (r"monk|brewer|peasants?|medieval|hadza|husband|family|neighbou?r", "PERSON"), (r"viking", "VIKING"), (r"crowd|villagers|peasant|soldiers|sailors|people|family", "PERSON"),
    (r"black cat", "BLACKCAT"), (r"leopard cat", "LEOPARDCAT"), (r"persian cat", "PERSIAN"), (r"sphynx", "SPHYNX"),
    (r"maine coon", "MAINECOON"), (r"\{CAT\}|wildcats?|kittens?|bastet", "CAT"),
    (r"\{HOUSECAT\}|house cat|tabby", "HOUSECAT"),
    (r"lions?\b|lioness", "LION"), (r"leopards?", "LEOPARD"), (r"hyenas?", "HYENA"), (r"\bdogs?\b|chihuahua|great dane", "DOG"), (r"\bwol(f|ves)\b", "WOLF"),
]
HUMAN_KINDS = set(HUMANS)
OTHER_CATS = ("CAT", "BLACKCAT", "LEOPARDCAT", "PERSIAN", "SPHYNX", "MAINECOON")
COUNT = {"two": 2, "three": 3, "four": 4}
FUNC = set("a an the at to of and or with by from toward towards beside next near behind under over on in into onto up down "
           "is are who as for while than then his her its their him them it he she they one".split())

def char_info(scene):
    """Characters in order of mention: [{name, seg}]; name is KIND or KIND:s (small/kitten), seg is the text about it.
    'two/three/four {X}' repeats a kind, 'tiny/baby/small {X}' or '{X} kitten' draws a smaller one."""
    found = []
    for pat, kind in CHAR_WORDS:
        for m in re.finditer(r"(?<![A-Za-z])(?:" + pat + r")", scene, re.I):
            found.append((m.start(), -(m.end() - m.start()), m.end(), kind, m.group(0)))
    found.sort()
    hits, last = [], -1
    for st, _, en, kind, txt in found:
        if st < last: continue                                # overlapping match ("leopard cat" vs "leopard")
        if hits and not scene[hits[-1][1]:st].strip():        # "{HOUSECAT} kitten", "Hadza people", "Hadza hunter": one character
            keep = hits[-1][2] if kind == hits[-1][2] or re.match(r"kitten", txt, re.I) else kind   # the last noun wins
            hits[-1] = (hits[-1][0], en, keep, hits[-1][3] + " " + txt); last = en; continue
        hits.append((st, en, kind, txt)); last = en
    if re.search(r"(crowd|line|group|dozen)s? of [\w ]*?(mice|rats|wolves|cats)", scene, re.I):
        hits = [h for h in hits if h[2] != "PERSON"]
    starts = [0]
    for i in range(1, len(hits)):
        st, k = hits[i][0], 0
        while k < 2:
            m = re.search(r"([A-Za-z'-]+)\s+$", scene[hits[i - 1][1]:st])
            if not m or m.group(1).lower() in FUNC: break
            st = hits[i - 1][1] + m.start(1); k += 1
        starts.append(st)
    out = []
    for i, (st, en, kind, txt) in enumerate(hits):
        seg = scene[starts[i]:(starts[i + 1] if i + 1 < len(hits) else len(scene))]
        before = scene[max(0, st - 24):st]
        if kind == "HOUSECAT" and "{HOUSECAT}" not in scene and any(o["name"].split(":")[0] in OTHER_CATS for o in out): continue
        small = bool(re.search(r"\bkitten", txt, re.I) or re.match(r"\W*kittens?\b", scene[en:en + 12], re.I)
                     or re.search(r"\b(tiny|baby|little|small)\s+(\w+\s+)?$", before, re.I))
        cm = re.search(r"\b(two|three|four)\s+(\w+\s+)?$", before, re.I)
        name = kind + (":s" if small else "")
        if re.search(r"\b(another|second|third|fourth)\s+(\w+\s+)?$", before, re.I):
            out.append({"name": name, "seg": seg}); continue
        same = [o for o in out if o["name"] == name]
        for o in same: o["seg"] += " " + seg
        for _ in range((COUNT[cm.group(1).lower()] if cm else 1) - len(same)): out.append({"name": name, "seg": seg})
    if any(w in scene.lower() for w in ("three cats", "all three cats", "lineup of", "group of five", "dozens of cats")):
        out += [{"name": k, "seg": ""} for k in ("HOUSECAT", "CAT") if k not in [o["name"] for o in out]]
    return out[:4]

def characters(scene):
    return [o["name"] for o in char_info(scene)]

def arms_for(scene):
    s = scene.lower()
    def has(keys): return any(re.search(r"\b" + re.escape(k), s) for k in keys)
    if has(("cheer", "arms in the air", "triumph", "hands raised", "celebrat", "dancing", "raising")): return "up"
    if has(("point", "finger raised", "one finger", "showing", "holding up")): return "point"
    if has(("hands on his head", "hands on her head", "hands on their head", "head in his hands", "head exploding", "facepalm", "covering his eyes", "covering his ears", "cheeks")): return "head"
    if has(("shrug", "palms up")): return "shrug"
    return "down"

def pick_setting(low):
    for keys, painter in SETTINGS:
        if any(re.search(r"\b" + re.escape(k) + r"\b", low) for k in keys): return painter
    return None

def render(scene, caption, seed, out, ctx):
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H), (255, 255, 255)); p = P(img, rnd)
    low = scene.lower()
    painter = pick_setting(re.sub(r"\{\w+\}", "", low)) or ctx.get("setting") or bg_day
    SKY["moon"] = not (TOPY > 0 and re.search(r'"([A-Za-z !]{3,24})"', scene))
    ctx["setting"] = painter
    SKY["discs"] = []
    painter(p)
    if re.search(r"\b(night|moon|moonlight|midnight)\b", low) and painter not in (bg_night, bg_space, bg_cave, bg_interior):
        night_overlay(p, painter not in INDOOR)
    if painter is bg_living and re.search(r"\b(couch|sofa)\b", low): couch(p)
    nobrow = r"no eyebrows|bare (shiny )?(brow|forehead)|without eyebrows|eyebrows? gone"
    FACE.update(nobrow=False, tears=bool(re.search(r"\b(cry|crying|cries|tears?|sobbing|weeping)\b", low)))
    e = expression(scene)
    info = char_info(scene)
    if not info and not any(k in low for k in ("map", "globe", "sea", "island", "ship", "timeline", "tablet", "scroll", "book", "pot")):
        info = [{"name": c, "seg": ""} for c in ctx.get("chars", [])]
    ctx["chars"] = [o["name"] for o in info]
    if "island" in low:
        p.ell((W / 2 - 420, Y(560), W / 2 + 420, Y(760)), (251, 192, 45)); p.line([(W / 2, Y(640)), (W / 2 + 20, Y(420))], 14, (121, 85, 72))
        for a in (-1, 1): p.poly([(W / 2 + 20, Y(420)), (W / 2 + a * 170, Y(470)), (W / 2 + a * 60, Y(430))], (67, 160, 71), 5)
    # props in the scene
    props_x = []
    if any(k in low for k in ("grain pot", "clay pot", "grain sack", "grain pots", "sacks", "jar", "stone bowl", "mortar", "tub", "basin", "amphora", "barrel")) and painter not in (bg_sea, bg_map):
        props_x.append(("pot", None))
    if any(k in low for k in ("fire", "campfire", "bonfire")): props_x.append(("fire", None))
    if "hut" in low and "huts" not in low and "village" not in low: props_x.append(("hut", None))
    if any(k in low for k in ("boat", "canoe", "ship", "longship")): props_x.append(("boat", None))
    if any(k in low for k in ("mummy", "mummies")): props_x.append(("mummy", None))
    if any(k in low for k in ("skeleton", "grave", "bone")): props_x.append(("skeleton", None))
    if "box" in low and "toolbox" not in low: props_x.append(("box", None))
    in_bed = bool(info) and bool(re.search(r"\bin (a |his |her |the |their )?(modern |big |messy )?bed\b|\blying (back )?(down )?in bed|\bsitting (up )?(on|in) (his |her |the )?bed", low))
    if re.search(r"\b(bed|beds|mattress)\b", low) and not in_bed and "bed of" not in low: props_x.append(("bed", None))
    has_ape = any(o["name"].split(":")[0] == "APE" for o in info)
    if "nest" in low and not has_ape: props_x.append(("nest", None))
    num = re.search(r'"([\d,:.]+)"', scene) or re.search(r"\b(\d{1,2},\d{3}|\d{3,4})\b", scene)
    if num and any(k in low for k in ("stone", "carved", "certificate", "timeline", "clock")): props_x.append(("tablet", num.group(1)))
    if not info and not props_x and "cat" in low: info = [{"name": "CAT", "seg": scene}]
    items = [(nm, pl, None) for nm, pl in props_x] + [(o["name"], None, ci) for ci, o in enumerate(info)]
    if any(nm == "pot" for nm, _ in props_x) and len(info) >= 2 and re.search(r"\b(around|straws?|between)\b", low):
        pot = [it for it in items if it[0] == "pot"]; other = [it for it in items if it[2] is None and it[0] != "pot"]
        cs = [it for it in items if it[2] is not None]; h = len(cs) // 2
        items = other + cs[:h] + pot + cs[h:]                  # the jar stands in the middle of the group
    n = len(items)
    L, R = (40, W - 130) if TOPY > 0 else (0, W)            # tall frame: keep clear of the Shorts buttons on the right
    slots = [(L + R) / 2] if n <= 1 else [L + (R - L) * (i + 1) / (n + 1) for i in range(n)]
    scale = (1.15 if n <= 2 else (0.9 if n == 3 else 0.72)) * CHAR_SCALE
    quoted = re.search(r'"([A-Za-z !]{3,24})"', scene)
    if quoted and TOPY > 0: scale *= 0.85
    humans_ci = [ci for ci, o in enumerate(info) if o["name"].split(":")[0] in HUMAN_KINDS]
    bed_ci = set([ci for ci in humans_ci if re.search(r"\bbed\b", info[ci]["seg"].lower())] or humans_ci[:1]) if in_bed else set()
    sit_on_pot = "on a grain pot" in low or "on the grain pot" in low or "on top of the grain" in low or "on the pot" in low
    pot_top = pot_slot = None
    if re.search(r"rows? of (clay )?(beer )?jars|thousands of (beer )?jars|many jars", low):
        for k in range(5): grain_pot(p, 110 + k * (W - 260) / 4, 0.42 * scale)
    for i, (name, pl, ci) in enumerate(items):
        x = slots[i]
        if name == "pot": pot_top = (x, grain_pot(p, x, scale)); pot_slot = i
        elif name == "fire" and not STICKLY: fire(p, x, CHAR_SCALE)
        elif name == "hut": hut(p, x)
        elif name == "boat": boat(p, x, Y(640))
        elif name == "mummy": mummy(p, x, GROUND + 40, 1.2 * scale)
        elif name == "skeleton": skeleton(p, x - 200 * CHAR_SCALE, GROUND + 25, 1.25 * CHAR_SCALE)
        elif name == "box": p.rect((x - 170, GROUND - 120, x + 170, GROUND + 60), (215, 160, 90), 7)
        elif name == "bed": bed(p, x, scale)
        elif name == "nest": nest(p, x, scale)
        elif name == "tablet": ts = min(0.8, 0.62 * scale); stone_tablet(p, x, GROUND + 40 - 135 * ts, pl, ts)
        elif ci in bed_ci: bed(p, x, scale, "back")
    if STICKLY: mute_image(img)
    for i, (name, pl, ci) in enumerate(items):                # fire stays bright orange in the muted style
        if name == "fire" and STICKLY: fire(p, slots[i], CHAR_SCALE)
    # characters, each with the expression / pose written next to it
    geoms = []
    every = bool(re.search(r"\b(both|all|everyone|together|each)\b", low))
    for i, (name, pl, ci) in enumerate(items):
        if ci is None: continue
        kind, small = name.split(":")[0], name.endswith(":s")
        if kind not in HUMAN_KINDS and kind not in CATS: continue
        seg = info[ci]["seg"]; x = slots[i]; look = 1 if x < W / 2 else -1
        ce = expr_or_none(seg) or (e if ci == 0 or len(info) == 1 else ("neutral" if e == "sleep" else e))
        if kind in HUMAN_KINDS:
            src = (seg or scene).lower()
            hold = "torch" if "torch" in src and kind == "CAVE" else ("spear" if "spear" in src and kind == "CAVE" else
                   ("sickle" if "sickle" in src else ("wheat" if "wheat" in src and "holding" in src else None)))
            arms = arms_for(seg) if seg else (arms_for(scene) if ci == 0 else "down")
            if arms == "down" and every: arms = arms_for(scene)
            FACE["nobrow"] = bool(re.search(nobrow, src)); FACE["sweat"] = bool(re.search(r"sweat|nervous", src))
            FACE["old"] = bool(re.search(r"grandmother|grandma|old woman|old man|elderly", src))
            g = human(p, kind, x, scale * (0.72 if small else 1), ce, arms, look, hold)
            if ci in bed_ci: bed(p, x, scale, "front"); g["body"] = (g["body"][0], g["body"][1], g["body"][2], GROUND - 195 * scale)
        else:
            if ce != "sleep" and "glowing" in low and "eyes" in low: ce = "glow"
            if re.search(r"\bhiss|fur puffed|puffed-up", (seg or scene).lower()): ce = "angry"
            cs = scale * (1.05 if n <= 2 else 0.95) * (0.6 if small else 1); FACE["nobrow"] = False
            if sit_on_pot and pot_top and kind in ("CAT", "HOUSECAT"):
                img2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p2 = P(img2, rnd)
                g = cat(p2, kind, W / 2, 0.75 * CHAR_SCALE, ce, look=look)
                ox, oy = int(pot_top[0] - W / 2), int(pot_top[1] - (GROUND + 40) + 20)
                img.paste(img2, (ox, oy), img2); p = P(img, rnd)
                g = dict(g, x=g["x"] + ox, head=(g["head"][0] + ox, g["head"][1] + oy, g["head"][2]), top=g["top"] + oy,
                         mouth=(g["mouth"][0] + ox, g["mouth"][1] + oy), body=(g["body"][0] + ox, g["body"][1] + oy, g["body"][2] + ox, g["body"][3] + oy))
            else:
                g = cat(p, kind, x, cs, ce, flip=-look or 1, look=look)
        g.update(kind=kind, seg=seg.lower(), slot=i, ce=ce)
        geoms.append(g)
    if "nest" in low:
        for g in geoms:
            if g["kind"] == "APE": nest(p, g["x"], g["s"])
    # crown on the character it is written next to
    crown_re = r"wearing a (\w+ )?crown|\bcrowned\b|with a crown|\bking\b|\bqueen\b"
    tg = next((g for g in geoms if re.search(crown_re, g["seg"])), None) or (geoms[0] if geoms and re.search(crown_re, low) else None)
    if tg:
        cx, cy, r = tg["head"]
        if tg["kind"] in CATS: crown(p, cx, cy - r * (0.95 if tg.get("mane") else 0.62), tg["s"] * 0.8)
        else: crown(p, cx, tg["top"] + 22 * tg["s"], tg["s"] * 0.9)
    # drinking straws: into the jar, bent over a neighbour's head when not next to it, or held up in the hand
    if re.search(r"\bstraws?\b", low):
        hum = [g for g in geoms if g["kind"] in HUMAN_KINDS]
        sip = hum if every else ([g for g in hum if re.search(r"straw|sip", g["seg"])] or hum[:1])
        gold = bool(re.search(r"\b(gold|golden|lapis)\b", low))
        for g in sip:
            (mx, my), s_ = g["mouth"], g["s"]
            if pot_top:
                px, py = pot_top; d = 1 if px > mx else -1; tip = (px - d * 30 * scale, py + 25 * scale)
                if abs(g["slot"] - pot_slot) <= 1: pts = [(mx + d * 18 * s_, my + 4 * s_), tip]
                else:
                    p0, up = (mx + d * 18 * s_, my + 4 * s_), g["top"] - 140 * s_
                    c1, c2 = (mx + d * 60 * s_, up), (px, up)
                    pts = [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * e_
                                 for a, b, c, e_ in zip(p0, c1, c2, tip)) for t in [k / 24 for k in range(25)]]
            else:
                hx_, hy_ = g["hand"]; pts = [(hx_ - 10 * s_, hy_ + 50 * s_), (hx_ + 40 * s_, max(hy_ - 330 * s_, TITLE_BOTTOM + 40))]
            straw(p, pts, s_, gold)
    if "spit" in low and pot_top:
        for g in geoms:
            if g["kind"] in HUMAN_KINDS and "spit" in g["seg"]:
                (mx, my), (px, py) = g["mouth"], pot_top
                hx_, hy_, hr_ = g["head"]
                for k in range(1, 9):
                    t = k / 9; dx_, dy_ = mx + (px - mx) * t, my + (py - my) * t - math.sin(t * math.pi) * 80; r_ = 15 * g["s"]
                    if math.hypot(dx_ - hx_, dy_ - hy_) < hr_ + r_: continue
                    p.ell((dx_ - r_, dy_ - r_, dx_ + r_, dy_ + r_), (129, 212, 250), 5)
    # mice sit on the floor next to the cat (never in the caption band)
    if re.search(r"\bmice\b|\bmouse\b|\brats?\b", low):
        many = any(k in low for k in ("dozen", "crowd", "swarm", "hundreds", "many", "endless", "line of"))
        cnt = 6 if many else (1 if re.search(r"\b(a|one|the|single)( dead| small| tiny| little)? (mouse|rat)\b", low) else 2)
        dead = "dead" in low
        anchor = next((g for g in geoms if g["kind"] in CATS), geoms[0] if geoms else None)
        for k in range(cnt):
            if many or not anchor: mx_, my_ = rnd.randint(120, W - 120), GROUND + rnd.randint(25, 75)
            else:
                side = anchor["look"]; mx_ = anchor["x"] + side * (anchor["hw"] + 75 + k * 150); my_ = GROUND + 55
            mouse(p, min(max(mx_, 110), W - 110), my_, 1.15 * CHAR_SCALE, dead=dead)
    # symbols: placed beside the head of the character they belong to, clear of faces and the title
    circles = [g["head"] for g in geoms] + SKY["discs"]; rects = [g["body"] for g in geoms]
    if quoted and not num:
        qt = quoted.group(1).upper(); qs = 100
        while qs > 60 and p.d.textlength(qt, font=ImageFont.truetype(FONT, qs)) > W - 180: qs -= 6
        qy = (TOPY + 40) if TOPY > 0 else 140
        p.text((W / 2, qy), qt, qs)
        tw = p.d.textlength(qt, font=ImageFont.truetype(FONT, qs)); rects.append((W / 2 - tw / 2, qy - qs * 0.6, W / 2 + tw / 2, qy + qs * 0.6))
    used = set()
    def beside(gi, size):
        g = geoms[gi]; cx, cy, r = g["head"]; out_side = -1 if g["x"] < W / 2 - 1 else 1
        for side in (out_side, -out_side):
            if (gi, side) in used: continue
            used.add((gi, side))
            nb = [h for h in geoms if (h["x"] - g["x"]) * side > 1]
            if nb:                                            # a neighbour on that side: sit in the gap between the heads
                h = min(nb, key=lambda h: abs(h["x"] - g["x"]))
                if abs(h["head"][0] - cx) - 0.69 * (r + h["head"][2]) < size * 0.9: continue
                return (min((cx + h["head"][0]) / 2, W - (150 if TOPY > 0 else 60) - size / 2), min(cy, h["head"][1]) - max(r, h["head"][2]) * 0.72)
            return (min(max(cx + side * (r + size * 0.55), 60 + size / 2), W - (150 if TOPY > 0 else 60) - size / 2), cy - r * 0.55)
        return (cx, max(g["top"] - size * 0.55, TITLE_BOTTOM + size * 0.55))
    if re.search(r"z letters|sleeping|asleep|\bsleep\b", low):
        sl = [gi for gi, g in enumerate(geoms) if g["ce"] == "sleep"][:2]
        for gi in sl:
            ax, ay = beside(gi, 90)
            for k in range(3): p.text((ax + k * 20, ay - k * 76), "Z", 86 - k * 12, fill=(255, 255, 255), stroke=7)
            circles.append((ax + 20, ay - 76, 110))
        if not geoms:
            for k in range(3): p.text((W / 2 + 120 + k * 60, GROUND - 380 - k * 90), "Z", 96 - k * 12, fill=(255, 255, 255), stroke=7)
    for key, ch, col, sz in (("question mark", "?", (255, 255, 255), 200), ("exclamation", "!", (229, 57, 53), 220)):
        if key not in low: continue
        sz = sz if TOPY > 0 else sz + 60
        gi = next((i for i, g in enumerate(geoms) if key.split()[0] in g["seg"]), 0)
        x_, y_ = beside(gi, sz * 0.6) if geoms else (W / 2, GROUND - 450)
        p.text((x_, y_), ch, sz, fill=col, stroke=12); circles.append((x_, y_, sz * 0.5))
    if any(k in low for k in ("light bulb", "lightbulb")):
        gi = next((i for i, g in enumerate(geoms) if "bulb" in g["seg"]), 0); k = 0.75 if TOPY > 0 else 1
        bx, by = beside(gi, 120 * k) if geoms else ((W - 150, SKY_Y + 60) if TOPY > 0 else (W / 2, 150))
        p.ell((bx - 70 * k, by - 85 * k, bx + 70 * k, by + 75 * k), (255, 241, 118), 6); p.rect((bx - 35 * k, by + 70 * k, bx + 35 * k, by + 120 * k), (158, 158, 158), 5)
        circles.append((bx, by, 105 * k))
    if re.search(r"\b(hearts?|love|loves|loving)\b", low):
        tg = next((g for g in geoms if re.search(r"heart|love", g["seg"])), geoms[0] if geoms else None)
        for x_, y_ in free_spots(rnd, 3, 58, circles, rects, (tg["head"][0], tg["top"]) if tg else None):
            heart(p, x_, y_, 0.9); circles.append((x_, y_, 58))
    if "sparkle" in low:
        tg = next((g for g in geoms if "sparkle" in g["seg"]), geoms[0] if geoms else None)
        near = (tg["head"][0], tg["head"][1]) if tg else ((pot_top[0], pot_top[1]) if pot_top else None)
        if pot_top and re.search(r"(jar|pot)[^,]*sparkle|sparkles? around (it|the jar|the pot)", low): near = (pot_top[0], pot_top[1] - 60)
        for x_, y_ in free_spots(rnd, 6, 38, circles, rects, near): sparkle(p, x_, y_)
    if any(k in low for k in ("big red x", "crossed-out", "crossed out", "red x")):
        prop_slots = [slots[i] for i, it in enumerate(items) if it[2] is None]
        if re.search(r"red x (between|above|over) them", low) and len(geoms) >= 2:
            r_ = 90 * scale; cy_ = max(min(geoms[0]["top"], geoms[1]["top"]) - 0.9 * r_, TITLE_BOTTOM + r_ + 20)
            big_x(p, (geoms[0]["head"][0] + geoms[1]["head"][0]) / 2, cy_, r_)
        elif prop_slots: big_x(p, prop_slots[0], GROUND - 130 * scale, 140 * scale)
        elif geoms:
            g = next((g for g in geoms if re.search(r"red x|crossed", g["seg"])), geoms[0])
            big_x(p, g["x"], (g["top"] + g["body"][3]) / 2, 0.4 * (g["body"][3] - g["top"]))
        else: big_x(p, W / 2, GROUND - 330, 300 if TOPY > 0 else 450)
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
