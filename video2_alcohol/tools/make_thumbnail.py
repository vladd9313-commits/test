"""Paint-style thumbnail (1280x720) for the alcohol video: tipsy caveman with a beer pot and a party ape."""
import os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from paint_frames import P, W, H, GROUND, bg_cave, human, grain_pot, STICKLY

def build(text, out, seed=11):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    bg_cave(p)
    grain_pot(p, 960, 1.0)
    from paint_frames import STICKLY, mute_image
    if STICKLY: mute_image(scene)
    for x, y in ((900, 400), (960, 360), (1020, 410)):
        p.ell((x - 18, y - 18, x + 18, y + 18), (255, 255, 255), 4)          # bubbles
    human(p, "CAVE", 480, 1.12, "happy", "up")
    human(p, "APE", 1450, 1.12, "happy", "point")
    for x, y in (((410, 300), (550, 300)) if STICKLY else ((415, 262), (545, 262))): p.ell((x - 28, y - 16, x + 28, y + 16), (244, 143, 177), 0)  # pink cheeks
    # party hat on the ape
    p.poly([(1385, 135), (1450, -40), (1515, 135)] if STICKLY else [(1385, 125), (1450, -60), (1515, 125)], (233, 30, 99), 6)
    # mango in the ape's hand
    p.ell((1690, 355, 1780, 440) if STICKLY else (1665, 215, 1755, 300), (255, 152, 0), 5)
    canvas = Image.new("RGB", (W, H), (62, 39, 35)); canvas.paste(scene, (0, 160))
    from PIL import ImageDraw, ImageFont
    from paint_frames import FONT
    size = 190
    while ImageDraw.Draw(canvas).textlength(text, font=ImageFont.truetype(FONT, size)) > W - 80: size -= 6
    P(canvas, rnd).text((W / 2, 135), text, size, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    build("WHO GOT DRUNK FIRST?", os.path.join(out, "thumbnail_A_who_got_drunk_first.jpg"))
    build("BEER BEFORE BREAD?", os.path.join(out, "thumbnail_B_beer_before_bread.jpg"))
