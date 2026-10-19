"""Generic SFX layer for a Short hook (0–1.5 s), synced to hook_generic.html. numpy only.
usage: python3 sfx_generic.py OUT.wav [--timer]   (48 kHz mono, 2.6 s incl. tails)"""
import sys, wave, numpy as np

SR = 48000; N = int(2.6 * SR); rng = np.random.default_rng(5)
out = np.zeros(N)
def add(sig, at):
    i = int(round(at * SR)); j = min(N, i + len(sig)); out[i:j] += sig[:j - i]
def bp(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if lo: g /= np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: g /= np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))
def noise(d): return rng.standard_normal(int(d * SR))
def sweep(d, f0, f1, level, peak=0.5):
    n = int(d * SR); x = noise(d); y = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        fc = f0 * (f1 / f0) ** (i / n); y[i:i + blk] = bp(x[i:i + blk], fc * .55, fc * 1.7)
    u = np.arange(n) / n; e = np.where(u < peak, u / peak, (1 - u) / (1 - peak)) ** 1.6
    return level * y * e
def boom(level, f0=120, f1=40, d=0.5, click=0.25):
    n = int(d * SR); t = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-t * 16)
    return level * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + click * bp(noise(d), 1500, 7000) * np.exp(-t * 60))
def tick(level, f=3200):
    t = np.arange(int(.03 * SR)) / SR; return level * (np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + .5 * bp(noise(.03), 3000) * np.exp(-t * 300))
def bell(level, f=1320, d=1.0):
    t = np.arange(int(d * SR)) / SR
    return level * sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * k) for a, m, k in ((1, 1, 4), (.5, 2.76, 7), (.3, 5.4, 11)))

add(sweep(0.32, 600, 3000, .30, peak=.25), 0.0)            # camera already rushing in
add(boom(.75), 0.06)                                         # "YOU" punch
add(sweep(0.20, 4000, 900, .34, peak=.45), 0.44)             # whip-pan to the lion
add(boom(.85, 150, 45, .45, .5), 0.50)                       # "VS" hit, in the voice gap 0.45–0.51
add(boom(.35, 90, 40, .35, .2), 0.62)                      # landing on focus B
add(sweep(0.42, 2500, 350, .26, peak=.3), 0.95)              # pull back
TIMER = '--timer' in sys.argv
# clock ticks while the hand spins down (hand angle eo5 → ticks get sparser), then the slam; without a timer, a soft pop as the title lands
if TIMER:
  for k, tt in enumerate((1.03, 1.07, 1.11, 1.16, 1.21, 1.27, 1.33)): add(tick(.10 + .02 * (k % 2)), tt)
  add(boom(.6, 110, 50, .4, .3), 1.35); add(bell(.18), 1.35)
else:
  add(boom(.35, 160, 70, .3, .4), 1.22); add(bell(.08, 1760, .6), 1.24)
out *= 0.9 / np.abs(out).max()
d16 = (np.clip(out, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d16.tobytes())
print('ok')
