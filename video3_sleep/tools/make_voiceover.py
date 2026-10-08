"""Synthesize the voiceover with Kokoro (local neural TTS) and write per-line timings.

usage: python3 make_voiceover.py <kokoro_dir> <out_dir> [voice] [speed]
Outputs: voiceover.wav, timings.json (one entry per script line = one image).
"""
import json, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
import parse_script
from kokoro_onnx import Kokoro

kdir, out = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
only = sys.argv[5] if len(sys.argv) > 5 else None
SENT_PAUSE, BLOCK_PAUSE, SR = 0.42, 1.0, 24000
k = Kokoro(os.path.join(kdir, "kokoro-v1.0.onnx"), os.path.join(kdir, "voices-v1.0.bin"))

SAY = {"1300s": "thirteen hundreds", "1990s": "nineteen nineties", "Ju/'hoansi": "Zhu-twa-see", "Swartkrans": "Swart-krahns",
       "Wiessner": "Weesner", "Ekirch": "Ek-urch", "REM sleep": "R E M sleep", "five in the morning": "five in the morning",
       "a.m.": "A M", "Sibudu": "Sih-boo-doo"}
def speakable(text):
    for k_, v in SAY.items(): text = text.replace(k_, v)
    return text

def trim(a, thr=0.008):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a
    s, e = max(idx[0] - int(0.02*SR), 0), min(idx[-1] + int(0.06*SR), len(a))
    return a[s:e]

chunks, timings, t = [], [], 0.0
n = 0
for b in parse_script.load(os.path.join(os.path.dirname(__file__), "..")):
    if only and b["id"] != only: continue
    for si, sent in enumerate(b["sentences"]):
        lines = [b["lines"][i] for i in sent]
        text = " ".join(l["text"] for l in lines)
        audio, sr = k.create(speakable(text), voice=voice, speed=speed, lang="en-us")
        audio = trim(np.asarray(audio, dtype=np.float32))
        dur = len(audio) / SR
        weights = [len(l["text"]) + 4 for l in lines]
        tot, acc = sum(weights), 0
        for l, w in zip(lines, weights):
            st = t + dur * acc / tot; acc += w
            timings.append({"n": n, "block": b["id"], "text": l["text"], "scene": l["scene"],
                            "start": round(st, 3), "end": round(t + dur * acc / tot, 3)})
            n += 1
        chunks.append(audio); t += dur
        pause = BLOCK_PAUSE if si == len(b["sentences"]) - 1 else SENT_PAUSE
        chunks.append(np.zeros(int(pause * SR), dtype=np.float32)); t += pause
        # the image stays on screen through the pause
        timings[-1]["end"] = round(t, 3)
    print(b["id"], round(t, 1), flush=True)
os.makedirs(out, exist_ok=True)
sf.write(os.path.join(out, "voiceover.wav"), np.concatenate(chunks), SR)
json.dump(timings, open(os.path.join(out, "timings.json"), "w"), indent=1, ensure_ascii=False)
print("total", round(t, 2), "s, lines", len(timings))
