"""Write image_prompts.txt (one prompt per line, same order as timings.json / image files)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse_script import load, expand, STYLE, STYLE_STICKLY
root = os.path.join(os.path.dirname(__file__), "..")
lines = [l for b in load(root) for l in b["lines"]]
for name, style in (("image_prompts.txt", STYLE), ("image_prompts_stickly.txt", STYLE_STICKLY)):
    with open(os.path.join(root, name), "w", encoding="utf-8") as f:
        for l in lines:
            f.write(f"{expand(l['scene'])}, {style}\n")
print(len(lines), "prompts")
