"""Layers for a Short's motion hook, cut from the channel's own renderer and from the Short itself.

usage: python3 build_layers.py TOOLS_DIR SCRIPT.txt SHORT.mp4 OUT_DIR

Writes into OUT_DIR:
  far.png     the setting's background only (as the renderer paints it: muted + lit)
  fg.png      everything drawn over it (characters, props, symbols, contact shadows), exact alpha matte
  badge.png   the timer badge, if the first scene has one
  title_N.png the Short's title lines, keyed from its real first frame
  layers.json focus points (heads), badge rect, title rects, Ken Burns fit, first cut time
The fg matte comes from rendering twice over black and white: every step of the renderer is affine per pixel,
so alpha = 1 - (w - b) / (W - B), where W and B are pure white / black run through the same light and mute passes."""
import inspect, json, os, random, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter

tools, script, short, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
os.environ.update(FRAME_STYLE="stickly", FRAME_W="1080", FRAME_H="1920", FRAME_GROUND="1320", FRAME_SCALE="1.1", FRAME_OUT_W="2160")
sys.path.insert(0, tools)
import paint_frames as pf
modern = getattr(pf, "modern", None)

title, scene = "", None
for raw in open(script, encoding="utf-8"):
    raw = raw.strip()
    if raw.lower().startswith("# title:"): title = raw.split(":", 1)[1].strip()
    elif "|" in raw and not raw.startswith("#") and scene is None: scene = raw.split("|", 1)[1].strip()

SIZE = (2160, 3840)
TMP = tempfile.mkdtemp()
if hasattr(pf, 'save_frame'): pf.save_frame = lambda img, o: img.save(o)
SRC = inspect.getsource(pf.render)
POST_MUTE, POST_LIGHT = 'mute_image(img)' in SRC, 'light_pass(img)' in SRC
if os.environ.get('HOOK_OLD_LOOK'):            # Short rendered before contact shadows and the light pass existed
    pf.shadows = lambda *a, **k: None; pf.light_pass = lambda *a, **k: None; POST_LIGHT = False
orig_setting, orig_human, orig_cat = pf.scene_setting, pf.human, pf.cat
orig_timer = modern.timer if modern else None
heads, trect = [], {}

def rec(fn):
    def w(p, *a, **k):
        g = fn(p, *a, **k)
        if isinstance(g, dict) and "head" in g: heads.append([float(v) for v in g["head"][:3]])
        return g
    return w
def run(fill=None, timer=True):
    heads.clear()
    pf.human, pf.cat = rec(orig_human), rec(orig_cat)
    def solid(low, ctx, c=fill):
        real = orig_setting(low, ctx)
        def paint(p):
            real(pf.P(Image.new('RGB', p.img.size), p.r)); p.rect((-10, -10, pf.W + 10, pf.H + 10), c, 0)
        return paint
    pf.scene_setting = solid if fill else orig_setting
    if modern and orig_timer:
        def tm(p, label):
            r = orig_timer(p, label); trect["r"] = [float(v) for v in r]; return r
        modern.timer = tm
    o = os.path.join(TMP, 'x.png'); pf.render(scene, None, 1000, o, {})
    return np.asarray(Image.open(o).convert('RGB').resize(SIZE, Image.LANCZOS)).astype(np.float32)

full = run()
b, w = run((0, 0, 0)), run((255, 255, 255))
H = list(heads)
# pure black / white through the same post passes (mute for the stickly style, then the light pass)
def plate(c):
    img = pf.blank(color=c) if hasattr(pf, 'blank') else Image.new('RGB', (pf.W, pf.H), c)
    if pf.STICKLY and POST_MUTE: pf.mute_image(img)
    if POST_LIGHT: pf.light_pass(img)
    return np.asarray(img.resize(SIZE, Image.LANCZOS).convert("RGB")).astype(np.float32)
B, Wt = plate((0, 0, 0)), plate((255, 255, 255))
den = np.maximum((Wt - B).mean(axis=2), 1)
a = np.clip(1 - (w - b).mean(axis=2) / den, 0, 1)
col = np.where(a[..., None] > 1e-3, (b - (1 - a[..., None]) * B) / np.maximum(a[..., None], 1e-3), 0)
fg = np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8)
# far plate: the real full render with the foreground removed is not recoverable, so paint the setting alone
pf.scene_setting = orig_setting
rnd = random.Random(1000); img = pf.blank() if hasattr(pf, 'blank') else Image.new('RGB', (pf.W, pf.H), (255, 255, 255)); p = pf.P(img, rnd)
sc, _ = (modern.split_timer(scene) if modern else (scene, None))
low = pf.strip_q(sc).lower(); painter = orig_setting(low, {})
painter(p)
if pf.STICKLY and POST_MUTE: pf.mute_image(img)
if POST_LIGHT: pf.light_pass(img)
far = img.resize(SIZE, Image.LANCZOS).convert("RGB")
info = {"native_ss": int(getattr(pf, 'SS', 1)), "title": title, "scene": scene, "heads": [[h[0], h[1], h[2]] for h in H]}
# timer badge into its own layer
if "r" in trect:
    x0, y0, x1, y1 = trect["r"]; m = 8
    X0, Y0, X1, Y1 = [int(round(v * 2)) for v in (x0 - m, y0 - m, x1 + m, y1 + m)]
    Image.fromarray(fg[Y0:Y1, X0:X1]).save(os.path.join(out, "badge.png"))
    fg[Y0:Y1, X0:X1, 3] = 0
    info["badge"] = [X0 / 2, Y0 / 2, X1 / 2, Y1 / 2]
    size = 64 if pf.TOPY == 0 else 70; r = size * 0.62                  # clock face, as modern.timer draws it
    info["clock"] = [x0 + 26 + r, (y0 + y1) / 2, r]
Image.fromarray(fg).save(os.path.join(out, "fg.png")); far.save(os.path.join(out, "far.png"))
# check: far + fg must rebuild the renderer's own frame
comp = Image.alpha_composite(far.convert("RGBA"), Image.fromarray(fg))
if "badge" in info:
    comp.alpha_composite(Image.open(os.path.join(out, "badge.png")), (int(info["badge"][0] * 2), int(info["badge"][1] * 2)))
info["rebuild_err"] = float(np.abs(np.asarray(comp.convert("RGB")).astype(float) - full).mean())

# ---- the Short itself: first frames, first cut, Ken Burns, title keyed out of frame 0
def frame(n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", short, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3)
cut = subprocess.run(["ffmpeg", "-i", short, "-t", "8", "-vf", "select=gt(scene\\,0.03),showinfo", "-f", "null", "-"], capture_output=True, text=True).stderr
import re
info["first_cut"] = float(re.search(r"pts_time:([0-9.]+)", cut).group(1))
base = Image.fromarray(np.asarray(comp.convert("L")))
def fit(n):
    r = np.asarray(Image.fromarray(frame(n)).convert("L").resize((270, 480), Image.BILINEAR)).astype(float)
    mask = np.zeros_like(r, bool); mask[110:340, 20:250] = True
    best = None
    for s in np.arange(0.99, 1.12, 0.002):
        A_ = 8 / s; C_ = 2 * (540 - 540 / s); F_ = 2 * (960 - 960 / s)
        y = np.asarray(base.transform((270, 480), Image.AFFINE, (A_, 0, C_, 0, A_, F_), resample=Image.BILINEAR)).astype(float)
        d = np.abs(y - r)[mask].mean()
        if best is None or d < best[0]: best = (d, s)
    return best
f0, f40 = fit(0), fit(40)
info["kb"] = {"s0": round(f0[1], 4), "rate_per_s": round((f40[1] - f0[1]) / (40 / 30), 5), "err0": round(f0[0], 2), "err40": round(f40[0], 2)}
# title: yellow fill + its black stroke, keyed from frame 0 (top band only)
F0 = frame(0).astype(int)
band = slice(120, 520)
yel = (F0[band, :, 0] > 200) & (F0[band, :, 1] > 170) & (F0[band, :, 2] < 120)
mk = Image.fromarray((yel * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(23)).filter(ImageFilter.GaussianBlur(1.2))
al = np.asarray(mk).astype(np.uint8)
rows = np.where(yel.any(axis=1))[0]
lines, start = [], rows[0]
for i in range(1, len(rows)):
    if rows[i] - rows[i - 1] > 6: lines.append((start, rows[i - 1])); start = rows[i]
lines.append((start, rows[-1]))
lines = [(r0, r1) for r0, r1 in lines if r1 - r0 >= 40 and r0 + 120 < 400]   # real title rows only (not flames or scene words)
info["title_lines"] = []
for k, (r0, r1) in enumerate(lines):
    y0, y1 = max(0, r0 - 14), min(al.shape[0], r1 + 16)
    cols = np.where(yel[r0:r1 + 1].any(axis=0))[0]; x0, x1 = max(0, cols[0] - 16), min(1080, cols[-1] + 18)
    rgba = np.dstack([F0[band][y0:y1, x0:x1], al[y0:y1, x0:x1]]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(out, f"title_{k}.png"))
    info["title_lines"].append([int(x0), int(y0 + 120), int(x1), int(y1 + 120)])
# colour: fit an affine RGB map from our rebuilt frame to the Short's real frame 0 (older Shorts used a more muted look)
s0 = info["kb"]["s0"]; A_ = 2 / s0
mine = np.asarray(comp.convert("RGB").transform((1080, 1920), Image.AFFINE, (A_, 0, 2 * (540 - 540 / s0), 0, A_, 2 * (960 - 960 / s0)), resample=Image.BILINEAR)).astype(float)
keep = np.ones((1920, 1080), bool); keep[:400] = False; keep[1370:1590] = False
if "badge" in info: x0, y0, x1, y1 = [int(v) for v in info["badge"]]; keep[y0:y1, x0:x1] = False
X = np.c_[mine[keep], np.ones(keep.sum())]; Y = F0[keep].astype(float)
Mfit = np.linalg.lstsq(X[::7], Y[::7], rcond=None)[0]
before, after = np.abs(X[:, :3] - Y).mean(), np.abs(X @ Mfit - Y).mean()
info["color_fit"] = {"before": round(float(before), 2), "after": round(float(after), 2)}
if after < before * 0.8:
    def recolor(path):
        im = np.asarray(Image.open(path)).astype(float); rgb = im[..., :3].reshape(-1, 3)
        im[..., :3] = np.clip(np.c_[rgb, np.ones(len(rgb))] @ Mfit, 0, 255).reshape(im.shape[:2] + (3,))
        Image.fromarray(im.astype(np.uint8), "RGBA" if im.shape[2] == 4 else "RGB").save(path)
    recolor(os.path.join(out, "far.png")); recolor(os.path.join(out, "fg.png")); info["color_fit"]["applied"] = True
json.dump(info, open(os.path.join(out, "layers.json"), "w"), indent=1)
print(json.dumps({k: info[k] for k in ("heads", "badge", "first_cut", "kb", "rebuild_err", "title_lines", "color_fit") if k in info}))
