"""Write youtube_metadata.txt for the periods video: title, A/B titles, description with chapters from the voiceover timings, tags."""
import json, os
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
CHAPTERS = {
    "B01": "100 periods vs 450", "B02": "The period problem is new", "B03": "Why humans have periods at all",
    "B04": "Where the number 100 comes from", "B05": "Reason 1: a later first period",
    "B06": "Reason 2: pregnancy", "B07": "Reason 3: years of breastfeeding",
    "B08": "What did Stone Age women use?", "B09": "Myth: blood attracts predators", "B10": "Myth: periods sync with the moon",
    "B11": "The period hut", "B12": "Egypt: a day off work", "B13": "Myth: the papyrus tampon",
    "B14": "Pliny the Elder's wild claims", "B15": "Medieval 'flowers' and rags", "B16": "The pad nobody would buy",
    "B17": "Tampons and cups", "B18": "The 450-period problem", "B19": "So how did they deal with it?",
    "B20": "Back to the long walk",
}
def tc(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"
first = {}
for t in tim: first.setdefault(t["block"], t["start"])
chapters = "\n".join(f"{tc(first[b] if b != 'B01' else 0)} {CHAPTERS[b]}" for b in sorted(first))
desc = f"""A woman today will have around 450 periods in her life. A Stone Age woman probably had about 100. Same body, same biology. So what was going on?

In this video: why humans have periods when most mammals don't, Beverly Strassmann's study of Dogon women, why the first period came later, how years of breastfeeding paused the cycle, what Stone Age women may have used (sphagnum moss, cattail fluff, soft hide), whether the smell really attracts bears, the menstrual sync and moon myths, period huts, the Egyptian workers who stayed home because their wife had her period, the papyrus tampon myth, Pliny the Elder's wildest claims, medieval "flowers" and rags, the pad nobody would buy, and the invention of Kotex, Tampax and the menstrual cup.

{chapters}

#ancienthumans #history #womenshistory"""
tags = ("how did ancient women deal with periods, periods in ancient times, history of periods, history of menstruation, "
        "cavewomen periods, stone age women, menstruation history, ancient women, period huts, papyrus tampon myth, "
        "menstrual synchrony myth, bears and periods, pliny the elder, ancient egypt, ancient history, human evolution, explained")
assert len(tags) <= 500, len(tags)
out = f"""TITLE
How Did Ancient Women Deal With Periods?

ALT TITLES (A/B test)
Stone Age Women Had 100 Periods. You'll Have 450.
What Did Cavewomen Actually Use for Periods?

DESCRIPTION
{desc}

TAGS
{tags}

THUMBNAILS
thumbnail/thumbnail_A_only_100.jpg (main), thumbnail/thumbnail_B_no_pads.jpg (A/B)

SETTINGS
Audience: No, it's not made for kids. Age restriction: No. Category: Education.
"""
open(os.path.join(root, "youtube_metadata.txt"), "w", encoding="utf-8").write(out)
print(out[:400]); print("tags chars:", len(tags))
