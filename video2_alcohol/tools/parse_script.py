"""Parse script_part*.txt into blocks/lines/sentences (shared by TTS, docs, prompts, montage)."""
import glob, os, re

CHAR = {
    "CAVE": "a prehistoric caveman with messy dark brown hair and a ragged brown fur tunic",
    "WOMAN": "a prehistoric woman with long messy dark brown hair and a brown fur dress",
    "GUY": "a modern man with short brown hair, a blue t-shirt and khaki pants",
    "CAT": "a small sandy-tan African wildcat with faint dark stripes, long legs and huge round eyes",
    "HOUSECAT": "an orange tabby house cat with huge round eyes",
    "EGYPT": "an ancient Egyptian man with a black bob haircut and a white linen kilt",
    "SCI": "a scientist with round glasses, messy hair and a white lab coat",
    "APE": "a funny brown ape ancestor with shaggy fur, a pale face and huge round eyes",
    "SUMER": "an ancient Sumerian man with a long curly black beard, a bald head and a fringed wool skirt",
}
STYLE = ("simple MS Paint style cartoon illustration, flat solid colors, thick uneven black outlines, "
         "round-headed stick-like characters with huge round white eyes and small black pupils, minimal shading, "
         "simple background with bright blue sky, gray rocky mountains and flat green grass unless the scene says otherwise, "
         "funny educational YouTube explainer style, 16:9, no captions")

SHORT = {"CAVE": "the caveman", "WOMAN": "the woman", "GUY": "the man", "CAT": "the wildcat",
         "HOUSECAT": "the house cat", "EGYPT": "the Egyptian man", "SCI": "the scientist", "APE": "the ape", "SUMER": "the Sumerian man"}

STYLE_STICKLY = ("minimalist stick figure cartoon, characters with big round cream-colored heads, small black dot eyes "
                 "with heavy half-closed lids and a deadpan expression, thin black stick legs, small black hands, simple "
                 "clothing in muted colors, clean smooth black outlines, flat muted desaturated colors, plain slate blue-gray "
                 "background with a khaki ground line, very simple props, no shading, educational YouTube explainer style, 16:9, no captions")

def expand(scene):
    scene = re.sub(r"\{(\w+)\}'s", lambda m: SHORT[m.group(1)] + "'s", scene)
    # "a tiny {CAVE}" -> "a tiny prehistoric caveman ..." (drop the description's own article)
    scene = re.sub(r"\b(a|an|the) ((?:\w+ )*?)\{(\w+)\}",
                   lambda m: f"{m.group(1)} {m.group(2)}" + re.sub(r"^(a|an) ", "", CHAR[m.group(3)]), scene)
    return re.sub(r"\{(\w+)\}", lambda m: CHAR[m.group(1)], scene)

def load(root=None):
    root = root or os.path.join(os.path.dirname(__file__), "..")
    blocks = []
    for path in sorted(glob.glob(os.path.join(root, "script_part*.txt"))):
        for raw in open(path, encoding="utf-8"):
            raw = raw.rstrip("\n")
            if raw.startswith("## "):
                bid, title = [s.strip() for s in raw[3:].split("|", 1)]
                blocks.append({"id": bid, "title": title, "lines": []})
            elif "|" in raw:
                text, scene = [s.strip() for s in raw.split("|", 1)]
                blocks[-1]["lines"].append({"text": text, "scene": scene})
    # group lines into sentences (a sentence ends with . ? ! or a closing quote after them)
    for b in blocks:
        sents, cur = [], []
        for i, ln in enumerate(b["lines"]):
            cur.append(i)
            if re.search(r'[.?!]["”]?$', ln["text"]):
                sents.append(cur); cur = []
        if cur: sents.append(cur)
        b["sentences"] = sents
    return blocks
