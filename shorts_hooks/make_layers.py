"""Cut the channel's own characters out of the stick-figure renderer as alpha PNG layers.
Each layer is rendered twice (black and white background) and matted exactly from the difference.
usage: python3 make_layers.py OUT_DIR "<scene for layer>" name [--hide human|cat] ..."""
import os, sys, numpy as np
TOOLS = "/home/user/test/video7_you_in_oogs_world/tools"
os.environ.update(FRAME_STYLE="stickly", FRAME_W="1080", FRAME_H="1920", FRAME_GROUND="1320", FRAME_SCALE="1.1", FRAME_OUT_W="2160")
sys.path.insert(0, TOOLS)
import paint_frames as pf
from PIL import Image

orig = {k: getattr(pf, k) for k in ("scene_setting", "light_pass", "shadows", "mute_image", "human", "cat")}
def layer(scene, hide, out):
    shots = []
    for col in ((0, 0, 0), (255, 255, 255)):
        pf.scene_setting = lambda low, ctx, c=col: (lambda p: p.rect((-10, -10, pf.W + 10, pf.H + 10), c, 0))
        pf.light_pass = pf.shadows = pf.mute_image = lambda *a, **k: None
        pf.human, pf.cat = orig["human"], orig["cat"]
        import random
        dummy = pf.P(pf.blank(), random.Random(0))            # draw the hidden character off-canvas, keep its geometry
        if hide == "human": pf.human = lambda p, *a, **k: orig["human"](dummy, *a, **k)
        if hide == "cat": pf.cat = lambda p, *a, **k: orig["cat"](dummy, *a, **k)
        tmp = out + ".tmp.png"; pf.render(scene, None, 1000, tmp, {}); shots.append(np.asarray(Image.open(tmp).convert("RGB")).astype(np.float32)); os.remove(tmp)
    b, w = shots
    a = np.clip(1 - (w - b).mean(axis=2) / 255, 0, 1)
    rgb = np.where(a[..., None] > 1e-3, b / np.maximum(a[..., None], 1e-3), 0)
    Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA").save(out)
    ys, xs = np.where(a > 0.05); print(os.path.basename(out), "bbox", xs.min(), ys.min(), xs.max(), ys.max())

out = sys.argv[1]
pf.save_frame = lambda img, o: img.resize((2160, 3840), Image.LANCZOS).save(o)
for scene, name, hide in [("{GUY} terrified, a lion angry in the snow, an exclamation mark", "guy", "cat"),
                          ("{GUY} terrified, a lion angry in the snow", "lion", "human")]:
    layer(scene, hide, os.path.join(out, name + ".png"))
# clean background plate (no characters): the real snow setting
for k, v in orig.items(): setattr(pf, k, v)
pf.render("in the snow", None, 1000, os.path.join(out, "bg.png"), {})
# same plate with the characters' contact shadows (characters drawn off-canvas, so only their shadows land on the snow)
import random
dummy = pf.P(pf.blank(), random.Random(0))
pf.human = lambda p, *a, **k: orig["human"](dummy, *a, **k); pf.cat = lambda p, *a, **k: orig["cat"](dummy, *a, **k)
pf.render("{GUY} terrified, a lion angry in the snow", None, 1000, os.path.join(out, "bg_shadows.png"), {})
