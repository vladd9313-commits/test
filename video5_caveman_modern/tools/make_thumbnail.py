"""Stick-figure thumbnails (1280x720) for the caveman-in-the-modern-world video.

A 'HE LASTED 4 SECONDS'  - the caveman frozen on a highway between cars, a big red timer.
B 'DEADLIEST PLACE?'      - the caveman smiling in a waiting room next to a coughing man, timer '10 DAYS'.
usage: FRAME_STYLE=stickly python3 tools/make_thumbnail.py <out_dir>
"""
import os, random, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import paint_frames as pf
import modern
from paint_frames import P, W, H, FONT

pf.mute = lambda c, k=0.5, base=None: c          # thumbnails keep saturated colours, only the clean line style
RED = (229, 57, 53)

def big_timer(p, x, y, label, size=150):
    f = ImageFont.truetype(FONT, size); tw = p.d.textlength(label, font=f); r = size * 0.6
    x0, x1 = x - (tw + 2 * r + 90) / 2, x + (tw + 2 * r + 90) / 2
    p.d.rounded_rectangle((x0, y - size * 0.8, x1, y + size * 0.8), radius=int(size * 0.5), fill=RED, outline=pf.OL, width=12)
    cx = x0 + 30 + r
    p.d.ellipse((cx - r, y - r, cx + r, y + r), fill=(255, 255, 255), outline=pf.OL, width=9)
    p.d.rectangle((cx - 16, y - r - 30, cx + 16, y - r), fill=pf.OL)
    p.d.line([(cx, y), (cx, y - r * 0.7)], fill=pf.OL, width=11); p.d.line([(cx, y), (cx + r * 0.5, y + r * 0.15)], fill=pf.OL, width=11)
    p.text((cx + r + 30 + tw / 2, y + 4), label, size, fill=(255, 255, 255), stroke=10)

def frame(text, draw_scene, out, bg=(40, 46, 66), seed=5):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    draw_scene(p)
    canvas = Image.new("RGB", (W, H), bg); canvas.paste(scene, (0, 170))
    size = 190
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size)) > W - 80: size -= 6
    P(canvas, rnd).text((W / 2, 140), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

def scene_a(p):
    modern.bg_highway(p)
    modern.car(p, 330, pf.GROUND + 60, 1.25, (229, 57, 53))
    pf.FACE["sweat"] = True
    g = pf.human(p, "CAVE", 960, 1.15, "shock", "head", look=-1)
    pf.FACE["sweat"] = False
    modern.car(p, 1620, pf.GROUND + 60, 1.25, (30, 136, 229))
    big_timer(p, 1520, 440, "4 SEC")

def scene_b(p):
    modern.bg_waiting(p)
    pf.human(p, "GUY", 480, 1.1, "sad", "down", look=1)
    g = pf.human(p, "CAVE", 1000, 1.1, "happy", "down", look=-1)
    p.text((175, 300), "COUGH", 70, fill=(255, 255, 255), stroke=9)
    big_timer(p, 1580, 470, "10 DAYS", 105)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    frame("HE LASTED 4 SECONDS", scene_a, os.path.join(out, "thumbnail_A_lasted_4_seconds.jpg"))
    frame("DEADLIEST PLACE?", scene_b, os.path.join(out, "thumbnail_B_deadliest_place.jpg"), bg=(46, 70, 52))
    print("ok")
