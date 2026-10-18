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
    k = pf.SS; scene = pf.blank(); p = P(scene, rnd)
    draw_scene(p)
    canvas = Image.new("RGB", (W * k, H * k), bg); canvas.paste(scene, (0, 170 * k))
    size = 190
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size * k)) > (W - 80) * k: size -= 6
    P(canvas, rnd).text((W / 2, 140), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

def scene_a(p):
    pf.bg_snow(p)
    pf.FACE["sweat"] = True
    pf.human(p, "GUY", 620, 1.15, "shock", "head", look=1)
    pf.FACE["sweat"] = False
    pf.cat(p, "LION", 1250, 1.15, "angry", flip=1, look=-1)
    big_timer(p, 1560, 250, "4 SEC")

def scene_b(p):
    pf.bg_night(p)
    pf.bg_snow(p)
    pf.night_overlay(p, True, True)
    pf.FACE["sweat"] = True
    pf.human(p, "GUY", 600, 1.15, "shock", "down", look=1)
    pf.FACE["sweat"] = False
    pf.human(p, "CAVE", 1150, 1.05, "smug", "down", look=-1)
    big_timer(p, 1580, 520, "20 MIN", 110)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    frame("YOU LASTED 4 SECONDS", scene_a, os.path.join(out, "thumbnail_A_you_lasted_4_seconds.jpg"), bg=(90, 30, 25))
    frame("YOU VS THE ICE AGE", scene_b, os.path.join(out, "thumbnail_B_you_vs_ice_age.jpg"), bg=(30, 45, 80))
    print("ok")
