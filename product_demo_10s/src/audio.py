"""Music + SFX for the 10 s demo, synthesized with numpy only.
120 BPM, bar = 2 s. Accents: 0.0 start, 2.0 groove in, 4.0 drop thud, 6.0 reveal hit, 8.0 logo hit.
Usage: python3 audio.py OUT.wav  (also writes stems next to it)"""
import sys, wave, numpy as np

SR = 48000; DUR = 10.0; N = int(SR * DUR)
rng = np.random.default_rng(3)
t_all = np.arange(N) / SR

def buf(): return np.zeros(N)
def add(dst, sig, at):
    i = int(round(at * SR)); j = min(N, i + len(sig))
    if i < N: dst[i:j] += sig[:j - i]
def env_adsr(n, a, d, s, r, sus_len):
    a, d, r = int(a * SR), int(d * SR), int(r * SR); sl = max(0, int(sus_len * SR))
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)), np.full(sl, s), np.linspace(s, 0, max(r, 1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def additive(f, dur, bright=0.5, decay=None, detune=0.0):
    n = int(dur * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    for k in range(1, 14):
        amp = (1 / k) * bright ** (k - 1)
        if amp < 1e-3 or f * k > 16000: break
        hd = np.exp(-tt * (decay * (1 + 0.35 * k))) if decay else 1
        out += amp * hd * np.sin(2 * np.pi * f * k * tt * (1 + detune) + k)
    return out
def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))
def noise(dur): return rng.standard_normal(int(dur * SR))
def reverb(x, sec=1.1, wet=0.22):
    n = int(sec * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 6.0 / sec)
    ir = fft_filter(ir, lo=200, hi=7000); ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n; y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x + wet * y

# ---------------- music ----------------
CH = [  # (start, end, chord midi notes, bass root)
    (0.0, 2.0, [57, 60, 64, 69], 45),   # Am
    (2.0, 4.0, [53, 57, 60, 65], 41),   # F
    (4.0, 6.0, [55, 59, 62, 67], 43),   # G (build)
    (6.0, 8.0, [48, 55, 60, 64], 48),   # C
    (8.0, 10.0, [48, 55, 62, 64, 67], 36)]  # Cadd9 final
pad, arp, bass, drums = buf(), buf(), buf(), buf()
for s, e, notes, root in CH:
    L = min(e, 10) - s + (0.0 if e < 10 else 0)
    for m in notes:
        for dt in (-0.003, 0.003):
            sig = additive(hz(m), L + 0.6, bright=0.35, detune=dt) * env_adsr(int((L + 0.6) * SR), 0.25, 0.2, 0.8, 0.6, L - 0.45)
            add(pad, sig * 0.05, s)
    # arpeggio 16ths, brightness opens through the intro
    pattern = notes + [notes[1] + 12, notes[2] + 12]
    step = 0.125; k = 0; tt = s
    while tt < e - 1e-6 and tt < 9.0:
        bright = 0.25 + 0.5 * min(1, tt / 2.0) if tt < 2 else 0.75
        if not (5.75 <= tt < 6.0):          # breath before reveal
            m = pattern[k % len(pattern)] + 12
            vel = 0.55 + 0.45 * (k % 4 == 0)
            add(arp, additive(hz(m), 0.35, bright=bright, decay=9) * vel * 0.07, tt)
        k += 1; tt += step
    # bass 8ths from the groove
    if s >= 2.0:
        if s < 8.0:
            for i in range(int((e - s) / 0.25)):
                tt = s + i * 0.25
                if 5.75 <= tt < 6.0: continue
                b = additive(hz(root), 0.22, bright=0.55, decay=7) * env_adsr(int(0.22 * SR), 0.004, 0.05, 0.7, 0.08, 0.08)
                add(bass, b * (0.32 if i % 2 == 0 else 0.22), tt)
        else:
            add(bass, additive(hz(root), 2.0, bright=0.5, decay=1.3) * 0.38, s)

def kick(level=1.0, length=0.32):
    n = int(length * SR); tt = np.arange(n) / SR
    f = 48 + 110 * np.exp(-tt * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    return level * (np.sin(ph) * np.exp(-tt * 9) + 0.25 * fft_filter(noise(length), lo=2000)[:n] * np.exp(-tt * 120))
def hat(level=1.0):
    n = noise(0.06); return level * fft_filter(n, lo=7000) * np.exp(-np.arange(len(n)) / SR * 60)
def clap(level=1.0):
    x = fft_filter(noise(0.25), lo=900, hi=6000); e = np.exp(-np.arange(len(x)) / SR * 18)
    for o in (0.0, 0.012, 0.024): e[int(o * SR):] += 0.0
    return level * x * e
for i in range(16):
    tt = 2.0 + i * 0.5
    if tt >= 8.0: break
    if 5.5 <= tt < 6.0: continue
    add(drums, kick(0.55), tt)
for i in range(32):
    tt = 2.25 + i * 0.5
    if tt >= 8.0: break
    if 5.5 <= tt < 6.0: continue
    add(drums, hat(0.11), tt)
for tt in (6.5, 7.5):
    add(drums, clap(0.22), tt)

# ---------------- SFX ----------------
sfx = buf()
def whoosh(dur, f0, f1, level, rise=0.6):
    n = int(dur * SR); x = noise(dur); out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        u = i / n; fc = f0 * (f1 / f0) ** u
        out[i:i + blk] = fft_filter(x[i:i + blk], lo=fc * 0.6, hi=fc * 1.6)
    tt = np.arange(n) / n; e = np.where(tt < rise, tt / rise, (1 - tt) / (1 - rise)) ** 1.5
    return level * out * e
def mx(*xs):
    n = max(len(x) for x in xs); return sum(np.pad(x, (0, n - len(x))) for x in xs)
def blip(f, dur, level, decay=30):
    tt = np.arange(int(dur * SR)) / SR; return level * np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)
def click(level):
    x = fft_filter(noise(0.03), lo=1500, hi=9000); return level * x * np.exp(-np.arange(len(x)) / SR * 220)
def thud(level, f0=95, f1=42):
    n = int(0.45 * SR); tt = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-tt * 18)
    return level * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 8) + 0.3 * fft_filter(noise(0.45), hi=900) * np.exp(-tt * 30))
def flutter(level):
    x = fft_filter(noise(0.28), lo=1200, hi=7000); tt = np.arange(len(x)) / SR
    return level * x * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * tt)) * np.sin(np.pi * tt / tt[-1])
def chime(level):
    out = np.zeros(int(1.4 * SR))
    for i, m in enumerate([84, 88, 91, 96]):
        s = additive(hz(m), 1.2, bright=0.2, decay=3.5); o = int(i * 0.045 * SR); out[o:o + len(s)] += s
    return level * out

add(sfx, whoosh(0.9, 300, 2400, 0.22), 0.0)
for tt, lv in ((0.42, .05), (0.86, .045), (1.22, .05), (1.62, .04)): add(sfx, flutter(lv), tt)
add(sfx, mx(click(0.10), blip(1800, 0.06, 0.04, 60)), 1.48)                       # card flip tick
add(sfx, whoosh(0.7, 1800, 250, 0.16, rise=0.35), 1.9)                         # scatter / panel rise
add(sfx, blip(1250, 0.09, 0.08, 45), 2.48)                                     # hover
add(sfx, mx(click(0.22), blip(700, 0.05, 0.06, 70)), 2.62)                        # grab
add(sfx, whoosh(1.15, 600, 1400, 0.085, rise=0.5), 2.75)                       # drag swish
add(sfx, thud(0.62), 4.0); add(sfx, click(0.16), 4.06)                         # drop + snap
def p_of(t):
    u = min(1, max(0, (t - 4.15) / 1.7)); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
ts = np.linspace(4.15, 5.85, 4000); ps = np.array([p_of(x) for x in ts])
for q in (0.25, 0.5, 0.75): add(sfx, blip(2200 + q * 800, 0.05, 0.05, 80), ts[np.argmax(ps >= q)])
rn = int(1.35 * SR); rt = np.arange(rn) / SR                                    # riser 4.6 -> 5.95
riser = 0.05 * np.sin(2 * np.pi * np.cumsum(300 + 900 * (rt / rt[-1]) ** 2) / SR) * (rt / rt[-1]) ** 2
riser = mx(riser, whoosh(1.35, 500, 6000, 0.12, rise=0.97))
add(sfx, riser, 4.6)
add(sfx, thud(0.55, 120, 50), 6.0); add(sfx, fft_filter(noise(0.6), lo=3000) * np.exp(-np.arange(int(0.6 * SR)) / SR * 7) * 0.08, 6.0)
add(sfx, chime(0.10), 6.04)
add(sfx, mx(blip(1600, 0.08, 0.06, 40), blip(2400, 0.08, 0.03, 40)), 6.32)         # ready pill
add(sfx, whoosh(0.8, 2200, 300, 0.12, rise=0.4), 7.35)                          # pull back
add(sfx, thud(0.7, 110, 38), 8.0); add(sfx, chime(0.08), 8.02)                  # logo hit

# ---------------- mix ----------------
music = reverb(pad + arp, 1.4, 0.3) + bass + drums
fx = reverb(sfx, 0.7, 0.12)
mix = music * 0.9 + fx
fade = np.ones(N); fn = int(0.35 * SR); fade[-fn:] = np.linspace(1, 0, fn) ** 2; fade[:int(0.005 * SR)] = np.linspace(0, 1, int(0.005 * SR))
mix *= fade
peak = np.max(np.abs(mix)); mix *= 0.89 / peak            # peak ~ -1 dBFS
def save(path, x):
    x = np.clip(x, -1, 1); d = (x * 32767).astype('<i2')
    with wave.open(path, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(d, 2).tobytes())
out = sys.argv[1]; save(out, mix)
save(out.replace('.wav', '_music.wav'), music * fade * 0.89 / peak); save(out.replace('.wav', '_sfx.wav'), fx * fade * 0.89 / peak)
print('peak before norm', round(float(peak), 3))
