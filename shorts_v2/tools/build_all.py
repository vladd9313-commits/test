"""Write judged Shorts scripts to shorts_v2/scripts, render them with make_short_v2.py and write metadata.

usage: python3 build_all.py <judged.json> <kokoro_dir> [--jobs 2] [--only slug,slug]
"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, "..")
ap = argparse.ArgumentParser(); ap.add_argument("judged"); ap.add_argument("kokoro")
ap.add_argument("--jobs", type=int, default=2); ap.add_argument("--only")
a = ap.parse_args()

RELATED = {"cats": "Why Did Cats Choose Ancient Humans?",
           "alcohol": "How Ancient Humans Actually Discovered Alcohol?",
           "sleep": "How Did Ancient Humans Sleep Without Getting Eaten?"}
items = json.load(open(a.judged))
if a.only: items = [i for i in items if i["slug"] in a.only.split(",")]
os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
for it in items:
    f = it["final"]
    with open(os.path.join(root, "scripts", it["slug"] + ".txt"), "w", encoding="utf-8") as fh:
        fh.write(f"# title: {f['title_overlay'].strip()}\n")
        for l in f["lines"]:
            fh.write(f"{l['text'].strip().replace('|', ',')} | {l['scene'].strip().replace('|', ',')}\n")

def render(it):
    out = os.path.join(root, "out", it["slug"] + ".mp4")
    r = subprocess.run([sys.executable, os.path.join(here, "make_short_v2.py"), os.path.join(root, "scripts", it["slug"] + ".txt"),
                        a.kokoro, out], capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if l.startswith("{")]
    return it["slug"], (json.loads(last[-1]) if last else {"error": r.stderr[-800:]})

with ThreadPoolExecutor(a.jobs) as ex:
    done = dict(ex.map(render, items))
for k, v in done.items(): print(k, v)

meta = ["SHORTS v2 — titles, descriptions, tags and the long video to link (YouTube Studio > Content > Short > Related video)", ""]
for it in items:
    f = it["final"]; d = done.get(it["slug"], {})
    meta += [f"=== {it['slug']}.mp4 ({d.get('duration', '?')} s) ===",
             f"RELATED VIDEO: {RELATED[it['video']]}",
             "TITLE", f["yt_title"], "DESCRIPTION", f["yt_description"], "TAGS", f["yt_tags"], ""]
open(os.path.join(root, "shorts_metadata.txt"), "w", encoding="utf-8").write("\n".join(meta))
