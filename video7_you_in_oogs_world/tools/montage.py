"""Assemble the final video: one image per script line, cut exactly on the voiceover timings.

usage:
  python3 tools/montage.py --images <folder> [--audio voiceover/voiceover.mp3] [--timings voiceover/timings.json]
                           [--out final_video.mp4] [--size 1920x1080] [--fps 30] [--music bg.mp3] [--no-motion]

Images are matched to prompts by sorted file name (1.png, 2.png ... or img_001.jpg ...), i.e. the N-th image
belongs to the N-th line of image_prompts.txt. Each image gets a gentle zoom/pan (Ken Burns) so the video
keeps moving even inside a 2-3 second shot; cuts land on the start of the narration line the image illustrates.
"""
import argparse, json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
here = os.path.dirname(os.path.abspath(__file__))
ap.add_argument("--images", required=True)
ap.add_argument("--audio", default=os.path.join(here, "..", "voiceover", "voiceover.mp3"))
ap.add_argument("--timings", default=os.path.join(here, "..", "voiceover", "timings.json"))
ap.add_argument("--out", default="final_video.mp4")
ap.add_argument("--size", default="1920x1080")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--music", help="optional background music, ducked under the voice")
ap.add_argument("--music-volume", type=float, default=0.07)
ap.add_argument("--no-motion", action="store_true")
ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
ap.add_argument("--crf", type=int, default=20)
a = ap.parse_args()

W, H = map(int, a.size.lower().split("x"))
natural = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]
imgs = sorted([f for f in os.listdir(a.images) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))], key=natural)
tim = json.load(open(a.timings))
audio_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", a.audio]).decode())
if not imgs: sys.exit("no images found in " + a.images)
if len(imgs) != len(tim):
    print(f"WARNING: {len(imgs)} images for {len(tim)} script lines - "
          f"{'extra images are ignored' if len(imgs) > len(tim) else 'the last images are reused'}", file=sys.stderr)

# frame-exact boundaries: shot i runs from line i start to line i+1 start (first from 0, last to audio end)
starts = [0.0] + [t["start"] for t in tim[1:]]
bounds = [round(s * a.fps) for s in starts] + [round(audio_len * a.fps)]
tmp = tempfile.mkdtemp(prefix="montage_")

# a small set of camera moves, cycled so neighbouring shots never move the same way
MOVES = [("1.0+0.06*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),            # slow zoom in, centre
         ("1.06-0.06*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),           # slow zoom out
         ("1.07", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),                    # pan left -> right
         ("1.0+0.05*on/{n}", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*0.3"),            # zoom in, upper third
         ("1.07", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)")]                # pan right -> left

def render(i):
    n = bounds[i + 1] - bounds[i]
    src = os.path.join(a.images, imgs[min(i, len(imgs) - 1)])
    out = os.path.join(tmp, f"{i:05d}.mp4")
    fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    if a.no_motion:
        vf = f"{fit},fps={a.fps}"
    else:
        z, x, y = (s.format(n=max(n - 1, 1)) for s in MOVES[i % len(MOVES)])
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},setsar=1,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={a.fps}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                    "-r", str(a.fps), out], check=True)
    return out

n_shots = len(tim)
with ThreadPoolExecutor(a.jobs) as ex:
    clips = []
    for k, c in enumerate(ex.map(render, range(n_shots))):
        clips.append(c)
        if k % 50 == 0: print(f"shot {k+1}/{n_shots}", flush=True)
lst = os.path.join(tmp, "list.txt")
open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))

cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", a.audio]
if a.music:
    cmd += ["-stream_loop", "-1", "-i", a.music, "-filter_complex",
            f"[2:a]volume={a.music_volume}[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]"]
else:
    cmd += ["-map", "0:v", "-map", "1:a"]
cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out]
subprocess.run(cmd, check=True)
print("done:", a.out)
