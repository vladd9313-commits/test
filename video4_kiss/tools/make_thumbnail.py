"""Stick-figure thumbnails (1280x720) for the kissing video.

A 'EW. WHY?'        - a caveman leans in with red puckered lips, a cavewoman backs off with a big question mark.
B 'BLAME THE APES'  - a chimp plants a grooming peck on a startled caveman's head, where a huge cartoon bug sits.
usage: FRAME_STYLE=stickly python3 tools/make_thumbnail.py <out_dir>
"""
import os, random, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import paint_frames as pf
from paint_frames import P, W, H, FONT, OL

pf.mute = lambda c, k=0.5, base=None: c          # thumbnails keep saturated colours, only the clean line style
RED = (229, 57, 53)

def lips(p, x, y, s):
    p.ell((x - 34 * s, y - 20 * s, x + 34 * s, y + 20 * s), RED, 5); p.line([(x - 28 * s, y), (x + 28 * s, y)], 4)

def bug(p, x, y, s):
    p.ell((x - 70 * s, y - 45 * s, x + 70 * s, y + 45 * s), (110, 160, 60), 6)
    for k in (-1, 0, 1):
        for sx in (-1, 1): p.line([(x + k * 35 * s, y + 30 * s), (x + k * 45 * s + sx * 10 * s, y + 75 * s)], 6)
    for sx in (-1, 1):
        p.line([(x + sx * 25 * s, y - 40 * s), (x + sx * 50 * s, y - 95 * s)], 5)
        ex = x + sx * 28 * s; p.ell((ex - 22 * s, y - 32 * s, ex + 22 * s, y + 12 * s), (255, 255, 255), 4)
        p.d.ellipse((ex - 8 * s + 6 * s, y - 14 * s, ex + 8 * s + 6 * s, y + 2 * s), fill=OL)

def frame(text, draw_scene, out, bg=(40, 46, 66), seed=5):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    draw_scene(p)
    canvas = Image.new("RGB", (W, H), bg); canvas.paste(scene, (0, 170))
    size = 200
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size)) > W - 80: size -= 6
    P(canvas, rnd).text((W / 2, 140), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

def scene_a(p):
    pf.bg_night(p); pf.fire(p, 960, 1.3)
    g = pf.human(p, "CAVE", 560, 1.1, "happy", "down", look=1)
    lips(p, g["mouth"][0] + 60, g["mouth"][1], 1.3)
    pf.FACE["sweat"] = True
    g2 = pf.human(p, "WOMAN", 1380, 1.1, "shock", "shrug", look=-1)
    pf.FACE["sweat"] = False
    p.text((g2["head"][0] + 230, g2["head"][1] - 40), "?", 300, fill=(255, 255, 255), stroke=14)

def scene_b(p):
    pf.bg_jungle(p)
    s = 1.2; c = 700; d = 112 * s
    g1 = pf.human(p, "APE", c - d, s, "happy", "down", look=1)
    g2 = pf.human(p, "APE", c + d, s, "happy", "down", look=-1)
    my = (g1["mouth"][1] + g2["mouth"][1]) / 2
    lips(p, c, my, 0.9)
    pf.heart(p, c, min(g1["top"], g2["top"]) - 15, 1.0)
    g = pf.human(p, "CAVE", 1480, 1.15, "shock", "point", look=-1)
    p.text((g["head"][0] + 200, g["head"][1] - 30), "!", 280, fill=RED, stroke=14)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    frame("EW. WHY?", scene_a, os.path.join(out, "thumbnail_A_ew_why.jpg"))
    frame("BLAME THE APES", scene_b, os.path.join(out, "thumbnail_B_blame_the_apes.jpg"), bg=(46, 70, 52))
    print("ok")
