"""Paint-style YouTube thumbnail (1280x720): shocked caveman, smug wildcat on a grain pot, big yellow question."""
import os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from paint_frames import P, W, H, GROUND, bg_village, human, cat, grain_pot, crown, mouse, FONT

def build(text, out, seed=7):
    rnd = random.Random(seed)
    scene = Image.new("RGB", (W, H), "white"); p = P(scene, rnd)
    bg_village(p)
    human(p, "CAVE", 520, 1.12, "shock", "point")
    top = grain_pot(p, 1330, 1.1)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pl = P(layer, rnd)
    cat(pl, "CAT", W / 2, 1.0, "smug", flip=-1, look=-1)
    scene.paste(layer, (int(1330 - W / 2), int(top - (GROUND + 40) + 25)), layer)
    for x, y in ((880, 860), (1000, 890), (1720, 870), (170, 880)):
        mouse(p, x, y, 1.1)
    # push the scene down to free the top for the headline
    canvas = Image.new("RGB", (W, H), (79, 195, 247))
    canvas.paste(scene, (0, 150))
    cp = P(canvas, rnd)
    cp.text((W / 2, 135), text, 190, fill=(255, 235, 59), stroke=18)
    canvas.resize((1280, 720), Image.LANCZOS).save(out, quality=95)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for name, text in (("thumbnail_A_cats_chose_us.jpg", "CATS CHOSE US?"),
                       ("thumbnail_B_who_tamed_who.jpg", "WHO TAMED WHO?")):
        build(text, os.path.join(out, name))
