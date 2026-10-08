"""Cut vertical YouTube Shorts (1080x1920, < 60 s) out of the long video's voiceover and painted frames.

usage: python3 tools/make_shorts.py <kokoro_dir> <voiceover.wav> <out_dir>
"""
import json, os, subprocess, sys, textwrap
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from kokoro_onnx import Kokoro

here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, "..")
kdir, vo_wav, out = sys.argv[1:4]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SR = 24000

SHORTS = [
    dict(slug="short1_night_watch", title="WHY GRANDMA WAKES UP AT 5 AM",
         hook=("Your grandma waking up at five in the morning might be an ancient survival system.", 204),
         ranges=[(187, 195), (200, 207)]),
    dict(slug="short2_3am_wakeup", title="WAKING UP AT 3 AM IS NORMAL?",
         hook=None, ranges=[(232, 234), (236, 250), (262, 264)]),
    dict(slug="short3_dirty_bed", title="YOUR BED IS DIRTIER THAN AN APE'S",
         hook=("Your bed is dirtier than a chimpanzee's.", 58),
         ranges=[(48, 52), (55, 58), (63, 72)]),
]

tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
vo, sr = sf.read(vo_wav, dtype="float32"); assert sr == SR
k = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))
frames_dir = os.path.join(out, "_frames_nocap")
if not os.path.isdir(frames_dir):
    subprocess.run([sys.executable, os.path.join(here, "paint_frames.py"), frames_dir, "--no-caption"], check=True)

def font(n): return ImageFont.truetype(FONT, n)

def card(img_path, title, caption, path, cta=False):
    c = Image.new("RGB", (1080, 1920), (17, 17, 17)); d = ImageDraw.Draw(c)
    y = 170
    for ln in textwrap.wrap(title, 16):
        size = 96
        while d.textlength(ln, font=font(size)) > 940: size -= 4
        d.text((540, y), ln, font=font(size), fill=(255, 235, 59), stroke_width=10, stroke_fill=(0, 0, 0), anchor="mm"); y += size + 16
    im = Image.open(img_path)
    im = im.crop((285, 0, 1635, 1080)).resize((1080, 864))
    c.paste(im, (0, 520)); d.rectangle((0, 520, 1079, 1384), outline=(0, 0, 0), width=8)
    y = 1470
    for ln in textwrap.wrap(caption, 22)[:5]:
        size = 78
        while d.textlength(ln, font=font(size)) > 960: size -= 4
        d.text((540, y), ln, font=font(size), fill=(255, 255, 255), stroke_width=9, stroke_fill=(0, 0, 0), anchor="mm"); y += 96
    if cta:
        d.text((540, 1840), "Full story on the channel", font=font(52), fill=(255, 235, 59), stroke_width=6, stroke_fill=(0, 0, 0), anchor="mm")
    c.save(path, quality=92)

for sh in SHORTS:
    sd = os.path.join(out, sh["slug"]); fd = os.path.join(sd, "frames"); os.makedirs(fd, exist_ok=True)
    audio, timings, t = [], [], 0.0
    items = []
    if sh["hook"]:
        a, _ = k.create(sh["hook"][0], voice="am_michael", speed=0.85, lang="en-us")
        a = np.concatenate([np.asarray(a, dtype=np.float32), np.zeros(int(0.25 * SR), dtype=np.float32)])
        items.append((sh["hook"][0], sh["hook"][1], a))
    for a_, b_ in sh["ranges"]:
        for n in range(a_, b_ + 1):
            x = tim[n - 1]
            items.append((x["text"], n, vo[int(x["start"] * SR):int(x["end"] * SR)]))
    for i, (text, frame_no, a) in enumerate(items):
        timings.append({"n": i, "text": text, "start": round(t, 3), "end": round(t + len(a) / SR, 3)})
        card(os.path.join(frames_dir, f"{frame_no:03d}.jpg"), sh["title"], text,
             os.path.join(fd, f"{i + 1:03d}.jpg"), cta=(i == len(items) - 1))
        audio.append(a); t += len(a) / SR
    wav = os.path.join(sd, "audio.wav"); sf.write(wav, np.concatenate(audio), SR)
    json.dump(timings, open(os.path.join(sd, "timings.json"), "w"), indent=1)
    mp4 = os.path.join(root, "shorts", sh["slug"] + ".mp4"); os.makedirs(os.path.dirname(mp4), exist_ok=True)
    subprocess.run([sys.executable, os.path.join(here, "montage.py"), "--images", fd, "--audio", wav,
                    "--timings", os.path.join(sd, "timings.json"), "--out", mp4, "--size", "1080x1920", "--crf", "26"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", mp4 + ".tmp.mp4"], check=True)
    os.replace(mp4 + ".tmp.mp4", mp4)
    print(sh["slug"], round(t, 1), "s")
