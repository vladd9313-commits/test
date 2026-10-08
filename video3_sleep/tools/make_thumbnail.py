"""Stick-figure thumbnail (1280x720) for the sleep video: sleeping caveman, a guard by the fire, a lion's eyes in the dark."""
import os, random, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from paint_frames import P, W, H, GROUND, FONT, bg_night, human, fire, cat, STICKLY, mute_image

def build(text, out, seed=5):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    bg_night(p)
    if STICKLY: mute_image(scene)
    fire(p, 960)
    human(p, "CAVE", 520, 1.05, "sleep", "down")
    human(p, "WOMAN", 1380, 1.05, "shock", "point")
    for k, (dx, dy) in enumerate(((0, 0), (60, -70), (130, -150))):
        p.text((640 + dx, 260 + dy), "Z", 90 - k * 12, fill=(255, 255, 255), stroke=7)
    # glowing predator eyes in the dark
    for x, y in ((1690, 520), (1760, 520), (180, 600), (240, 600)):
        p.ell((x - 22, y - 16, x + 22, y + 16), (255, 235, 59), 4); p.d.ellipse((x - 6, y - 10, x + 6, y + 10), fill=(20, 20, 20))
    canvas = Image.new("RGB", (W, H), (40, 46, 66)); canvas.paste(scene, (0, 160))
    size = 190
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size)) > W - 80: size -= 6
    P(canvas, rnd).text((W / 2, 135), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    build("WHO STAYED AWAKE?", os.path.join(out, "thumbnail_A_who_stayed_awake.jpg"))
    build("HOW DID THEY SLEEP?", os.path.join(out, "thumbnail_B_how_did_they_sleep.jpg"))
