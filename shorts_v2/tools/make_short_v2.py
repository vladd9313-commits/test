"""Shorts template v2: one topic, 20-35 s, full-screen vertical art, word-by-word captions, fast hook, loopable ending.

Script format (shorts_v2/scripts/<slug>.txt):
    # title: YOUR CAT THINKS YOU CAN'T HUNT      <- big headline at the top of the screen (2-6 words)
    narration line | scene description           <- one line = one picture (2-3 s)
    ...
The first narration line is the hook. Write the last line so that it flows back into the first one (loop).

usage: python3 make_short_v2.py <script.txt> <kokoro_dir> <out.mp4> [--music track.mp3] [--speed 1.08]
"""
import argparse, json, os, re, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import ImageFont

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("script"); ap.add_argument("kokoro"); ap.add_argument("out")
ap.add_argument("--music"); ap.add_argument("--music-volume", type=float, default=0.10)
ap.add_argument("--speed", type=float, default=1.08); ap.add_argument("--voice", default="am_michael")
a = ap.parse_args()

SR = 24000
os.environ.update(FRAME_STYLE=os.environ.get("FRAME_STYLE", "stickly"), FRAME_W="1080", FRAME_H="1920",
                  FRAME_GROUND="1320", FRAME_SCALE="1.1")
sys.path.insert(0, here)
import paint_frames as pf                      # picks up the vertical canvas settings above
from kokoro_onnx import Kokoro

# ---------------------------------------------------------------- parse
title, lines = "", []
for raw in open(a.script, encoding="utf-8"):
    raw = raw.strip()
    if raw.lower().startswith("# title:"): title = raw.split(":", 1)[1].strip()
    elif "|" in raw and not raw.startswith("#"):
        t, sc = [x.strip() for x in raw.split("|", 1)]
        lines.append({"text": t, "scene": sc})
sents, cur = [], []
for i, l in enumerate(lines):
    cur.append(i)
    if re.search(r'[.?!]["”]?$', l["text"]): sents.append(cur); cur = []
if cur: sents.append(cur)

# ---------------------------------------------------------------- voice
k = Kokoro(os.path.join(a.kokoro, "kokoro-v1.0.onnx"), os.path.join(a.kokoro, "voices-v1.0.bin"))
def trim(x, thr=0.008):
    idx = np.where(np.abs(x) > thr)[0]
    return x if len(idx) == 0 else x[max(idx[0] - int(0.01 * SR), 0): idx[-1] + int(0.05 * SR)]

SAY = {"3 a.m.": "three A M", "a.m.": "A M", "chicha": "cheecha", "Ekirch": "Ek-urch", "Ninkasi": "Nin-kahsee"}
def speakable(x):
    for k_, v in SAY.items(): x = x.replace(k_, v)
    return x

PAUSE = 0.16
chunks, t, words = [], 0.0, []
for si, sent in enumerate(sents):
    text = " ".join(lines[i]["text"] for i in sent)
    audio, _ = k.create(speakable(text), voice=a.voice, speed=a.speed, lang="en-us")
    audio = trim(np.asarray(audio, dtype=np.float32)); dur = len(audio) / SR
    w = [len(lines[i]["text"]) + 3 for i in sent]; acc = 0
    for i, wi in zip(sent, w):
        st = t + dur * acc / sum(w); acc += wi; en = t + dur * acc / sum(w)
        lines[i]["start"], lines[i]["end"] = st, en
        toks = lines[i]["text"].split(); cw = [len(x) + 1 for x in toks]; c = 0
        for tok, wc in zip(toks, cw):
            words.append({"w": tok, "s": st + (en - st) * c / sum(cw), "e": st + (en - st) * (c + wc) / sum(cw), "line": i}); c += wc
    chunks.append(audio); t += dur
    if si < len(sents) - 1:
        chunks.append(np.zeros(int(PAUSE * SR), np.float32)); t += PAUSE
lines[-1]["end"] = t
voice = np.concatenate(chunks)

# whoosh on every cut (except the first frame) — short band-passed noise sweep
rng = np.random.default_rng(7)
def whoosh(n=int(0.22 * SR)):
    noise = rng.standard_normal(n).astype(np.float32)
    spec = np.fft.rfft(noise); f = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((f - 2500) / 1800) ** 2); x = np.fft.irfft(spec, n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return 0.18 * x / (np.abs(x).max() + 1e-9) * env
sfx = np.zeros_like(voice)
for l in lines[1:]:
    i0 = max(int((l["start"] - 0.08) * SR), 0); wv = whoosh(); i1 = min(i0 + len(wv), len(sfx))
    sfx[i0:i1] += wv[: i1 - i0]
mix = voice + sfx
tmp = tempfile.mkdtemp(prefix="shortv2_")
wav = os.path.join(tmp, "audio.wav"); sf.write(wav, mix, SR)

# ---------------------------------------------------------------- frames
fdir = os.path.join(tmp, "frames"); os.makedirs(fdir)
ctx = {}
for i, l in enumerate(lines):
    pf.render(l["scene"], None, 1000 + i, os.path.join(fdir, f"{i + 1:03d}.jpg"), ctx)
tim = [{"n": i, "text": l["text"], "start": round(l["start"], 3), "end": round(l["end"], 3)} for i, l in enumerate(lines)]
tj = os.path.join(tmp, "timings.json"); json.dump(tim, open(tj, "w"))
silent = os.path.join(tmp, "video.mp4")
subprocess.run([sys.executable, os.path.join(here, "montage.py"), "--images", fdir, "--audio", wav, "--timings", tj,
                "--out", silent, "--size", "1080x1920", "--fps", "30", "--crf", "24"], check=True,
               stdout=subprocess.DEVNULL)

# ---------------------------------------------------------------- word-by-word captions (ASS)
def ts(x):
    x = max(x, 0); h = int(x // 3600); m = int(x % 3600 // 60); s_ = x % 60
    return f"{h}:{m:02d}:{s_:05.2f}"
def esc(s): return s.replace("{", "(").replace("}", ")")
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,DejaVu Sans,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,9,3,5,60,60,0,1",
       "Style: Title,DejaVu Sans,88,&H003BEBFF,&H003BEBFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,4,8,70,70,190,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
if title:
    ass.append(f"Dialogue: 1,{ts(0)},{ts(t + 0.5)},Title,,0,0,0,,{esc(title.upper())}")
# group words into chunks of max 3 words that never cross a line boundary and always fit on one line,
# clear of the Shorts buttons on the right (x > ~920) and the channel/description block at the bottom
CAPF = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 88)
def cap_w(ws): return CAPF.getlength(" ".join(x["w"].upper() for x in ws)) * 1.08 + 20
groups, g = [], []
for wd in words:
    if g and (len(g) == 3 or g[-1]["line"] != wd["line"] or re.search(r"[.?!,]$", g[-1]["w"]) or cap_w(g + [wd]) > 770):
        groups.append(g); g = []
    g.append(wd)
if g: groups.append(g)
for gi, g in enumerate(groups):
    g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else t + 0.5
    for wi, wd in enumerate(g):
        end = g[wi + 1]["s"] if wi + 1 < len(g) else g_end
        txt = " ".join((r"{\c&H003BEBFF&\fscx108\fscy108}" + esc(x["w"]) + r"{\r}") if j == wi else esc(x["w"]) for j, x in enumerate(g))
        ass.append(f"Dialogue: 0,{ts(wd['s'])},{ts(end)},Cap,,0,0,0,,{{\\pos(510,1470)}}{txt.upper()}")
assf = os.path.join(tmp, "caps.ass"); open(assf, "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------------------------------------------------------- final mux: captions + optional music + loudness
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent]
if a.music:
    cmd += ["-stream_loop", "-1", "-i", a.music, "-filter_complex",
            f"[0:v]ass={assf}[v];[1:a]volume={a.music_volume}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5[a]",
            "-map", "[v]", "-map", "[a]"]
else:
    cmd += ["-vf", f"ass={assf}", "-af", "loudnorm=I=-14:TP=-1.5"]
cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", "-shortest", a.out]
subprocess.run(cmd, check=True)
print(json.dumps({"out": a.out, "duration": round(t, 2), "lines": len(lines), "words": len(words)}))
