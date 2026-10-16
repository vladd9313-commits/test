"""Stick-figure thumbnails (1280x720) for the periods video.

A 'ONLY 100?'  - a smug cavewoman with a small '100' tablet next to a shocked modern woman with a huge '450' tablet.
B 'NO PADS?!'   - a cavewoman in the forest, shocked, a bear peeking from the trees.
usage: FRAME_STYLE=stickly python3 tools/make_thumbnail.py <out_dir>
"""
import os, random, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import paint_frames as pf
from paint_frames import P, W, H, FONT, OL

pf.mute = lambda c, k=0.5, base=None: c          # thumbnails keep saturated colours, only the clean line style
RED = (229, 57, 53)

def frame(text, draw_scene, out, bg=(40, 46, 66), seed=5):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    draw_scene(p)
    canvas = Image.new("RGB", (W, H), bg); canvas.paste(scene, (0, 170))
    size = 200
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size)) > W - 80: size -= 6
    P(canvas, rnd).text((W / 2, 140), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

def tablet(p, x, y, label, s):
    p.poly([(x - 120 * s, y + 70 * s), (x - 120 * s, y - 40 * s), (x - 80 * s, y - 80 * s), (x + 80 * s, y - 80 * s), (x + 120 * s, y - 40 * s), (x + 120 * s, y + 70 * s)], (176, 176, 176), 7)
    p.text((x, y - 5 * s), label, int(90 * s), fill=(60, 60, 60), stroke=0)

def scene_a(p):
    pf.bg_living(p)
    g = pf.human(p, "WOMAN", 600, 1.1, "smug", "down", look=1)
    tablet(p, 230, g["head"][1] + 40, "100", 0.75)
    pf.FACE["sweat"] = True
    g2 = pf.human(p, "LADY", 1240, 1.1, "shock", "head", look=-1)
    pf.FACE["sweat"] = False
    tablet(p, 1660, g2["head"][1] + 60, "450", 1.3)

def scene_b(p):
    pf.bg_jungle(p)
    pf.cat(p, "BEAR", 1480, 1.0, "smug", flip=-1, look=-1)
    pf.FACE["sweat"] = True
    g = pf.human(p, "WOMAN", 640, 1.2, "shock", "head", look=1)
    pf.FACE["sweat"] = False
    p.text((g["head"][0] + 260, g["head"][1] - 40), "?", 300, fill=(255, 255, 255), stroke=14)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    frame("ONLY 100?", scene_a, os.path.join(out, "thumbnail_A_only_100.jpg"))
    frame("NO PADS?!", scene_b, os.path.join(out, "thumbnail_B_no_pads.jpg"), bg=(46, 70, 52))
    print("ok")
