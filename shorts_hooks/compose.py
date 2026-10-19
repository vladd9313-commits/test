"""Put a rendered hook over the start of a Short.
usage: python3 compose.py SHORT.mp4 HOOK_FRAMES_DIR OUT.mp4 WORK_DIR [--timer]

frames 0–41  hook, with the Short's own live word captions keyed in: in the bottom band, whatever differs from the
             re-rendered scene (same layers, same Ken Burns zoom) is caption, so road markings and white props stay out
frames 42–44 crossfade into the Short's real frames; from 45 on the Short plays untouched
audio        original voice + generic hook SFX, ducked under the voice and peak-limited"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter

short, hdir, out, work = sys.argv[1:5]; timer = "--timer" in sys.argv
here = os.path.dirname(os.path.abspath(__file__)); tmp = tempfile.mkdtemp()
N, X0 = 45, 42
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", short, "-frames:v", str(N), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
real = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3)
BAND = slice(1370, 1590)
import json
L = json.load(open(os.path.join(work, "layers.json")))
scene = Image.open(os.path.join(work, "far.png")).convert("RGBA"); scene.alpha_composite(Image.open(os.path.join(work, "fg.png")))
if os.path.exists(os.path.join(work, "badge.png")):
    scene.alpha_composite(Image.open(os.path.join(work, "badge.png")), (int(L["badge"][0] * 2), int(L["badge"][1] * 2)))
def kb_scene(n):                                   # the scene as the Short shows it at frame n (centre zoom)
    s = L["kb"]["s0"] + L["kb"]["rate_per_s"] * n / 30; a = 2 / s
    return np.asarray(scene.convert("RGB").transform((1080, 1920), Image.AFFINE, (a, 0, 2 * (540 - 540 / s), 0, a, 2 * (960 - 960 / s)), resample=Image.BILINEAR)).astype(np.float32)
for n in range(N):
    h = np.asarray(Image.open(os.path.join(hdir, f"h{n:03d}.png")).convert("RGB")).astype(np.float32)
    r = real[n].astype(np.float32)
    band = r[BAND]
    diff = np.abs(band - kb_scene(n)[BAND]).max(axis=2)
    cap = ((diff > 60) & ((band.min(axis=2) >= 225) | (band.max(axis=2) <= 70)))
    tall = np.convolve((cap.sum(axis=0) >= 14).astype(float), np.ones(25), "same") > 0   # glyph columns; thin edges of road marks are not
    cap = (cap & tall[None, :]).astype(np.uint8) * 255
    m = Image.fromarray(cap).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    a = np.asarray(m).astype(np.float32)[..., None] / 255
    h[BAND] = h[BAND] * (1 - a) + band * a
    if n >= X0:
        x = (n - X0) / 3; h = h * (1 - x) + r * x
    Image.fromarray(np.clip(h + .5, 0, 255).astype(np.uint8)).save(os.path.join(tmp, f"c{n:03d}.png"))
sfx = os.path.join(tmp, "sfx.wav")
subprocess.run([sys.executable, os.path.join(here, "sfx_generic.py"), sfx] + (["--timer"] if timer else []), check=True, capture_output=True)
fc = (f"[0:v]format=yuv420p[a];[1:v]format=yuv420p[b];[a][b]blend=all_expr='if(lt(N\\,{N})\\,B\\,A)'[v];"
      "[0:a]aresample=48000,asplit[voice][sc];[2:a]volume=0.5[fx];[fx][sc]sidechaincompress=threshold=0.05:ratio=3:attack=5:release=150[fxd];"
      "[voice][fxd]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false:latency=1[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", short, "-framerate", "30", "-i", os.path.join(tmp, "c%03d.png"), "-i", sfx,
                "-filter_complex", fc, "-map", "[v]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
print("ok", out)
