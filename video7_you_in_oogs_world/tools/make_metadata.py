"""Write youtube_metadata.txt (title, A/B titles, description with chapters from the voiceover timings, tags) and shorts/shorts_metadata.txt."""
import json, os
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
TITLE = "How Long Would YOU Last in a Caveman's World?"
CHAPTERS = {"B01": "Now it's your turn", "B02": "The rules", "B03": "1. A night in Oog's cave", "B04": "2. The barefoot walk",
            "B05": "3. Gathering berries", "B06": "4. Making fire", "B07": "5. An Ice Age night outside", "B08": "6. Dinner",
            "B09": "Scoreboard + 7. Meeting strangers", "B10": "8. The mammoth hunt", "B11": "9. The cave lion",
            "B12": "What actually keeps you alive", "B13": "Which part would you fail first?"}
def tc(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"
first = {}
for t in tim: first.setdefault(t["block"], t["start"])
chapters = "\n".join(f"{tc(first[b] if b != 'B01' else 0)} {CHAPTERS[b]}" for b in sorted(first))
desc = f"""You wake up 40,000 years ago next to Oog, with no phone and no shoes. We put you through 9 parts of a caveman's day and start a timer.

In Oog's cave you last all night. Facing a cave lion alone, about four seconds. In this video: the Hadza study that found only 18 minutes when everyone was asleep, the 2019 study of barefoot calluses, why gathering the wrong berries is so easy, how hard friction fire really is, how cold the Ice Age was, why bone marrow was a prized food, why you can't outrun a lion, and the Neanderthal from Shanidar Cave whose injuries suggest that people cared for each other.

{chapters}

#caveman #iceage #ancienthumans"""
tags = ("how long would you last, could you survive the stone age, ice age survival, caveman, how long would you survive as a caveman, "
        "stone age life, ancient humans, hunter gatherers, cave lion, mammoth hunt, shanidar 1, neanderthal, history explained, "
        "funny history, stick figure animation, what if, neanderwhy")
assert len(tags) <= 500, len(tags)
open(os.path.join(root, "youtube_metadata.txt"), "w", encoding="utf-8").write(f"""TITLE
{TITLE}

ALT TITLES (A/B test)
You Wake Up 40,000 Years Ago. How Long Do You Last?
We Sent You to the Ice Age. It Went Badly.

DESCRIPTION
{desc}

TAGS
{tags}

THUMBNAILS
thumbnail/thumbnail_A_you_lasted_4_seconds.jpg (main), thumbnail/thumbnail_B_you_vs_ice_age.jpg (A/B)

SETTINGS
Audience: No, it's not made for kids. Age restriction: No. Category: Education.
""")
SH = [("you_vs_lion", "You Can't Outrun a Cave Lion 🦁",
       "Usain Bolt's top speed was about 44 km/h. A charging lion can hit around 80. In the Ice Age, running alone was the worst plan. Full video: tap the video link on this Short. #shorts #iceage #history",
       "cave lion, could you outrun a lion, usain bolt vs lion, ice age, stone age survival, caveman, how long would you last, ancient humans, history shorts, stick figure animation, shorts"),
      ("you_barefoot", "Your Feet Wouldn't Survive the Stone Age 🦶",
       "People who usually walk barefoot had calluses about 30% thicker in a 2019 study, without losing sensitivity. Your feet? Soft like bread. Full video: tap the video link on this Short. #shorts #science #history",
       "barefoot, calluses, walking barefoot, 2019 calluses study, stone age, hunter gatherers, caveman, how long would you last, science facts, history shorts, stick figure animation, shorts"),
      ("you_shanidar", "This Neanderthal Survived Because of His Friends 🫶",
       "Shanidar 1 was probably blind in one eye, with a withered arm and a limp, yet his injuries healed and he lived for years. Many researchers think his group took care of him. Full video: tap the video link on this Short. #shorts #neanderthal #history",
       "shanidar 1, neanderthal, shanidar cave, caring neanderthals, prehistoric compassion, ancient humans, human evolution, caveman, history shorts, stick figure animation, shorts")]
lines = ["SHORTS for video 7 — titles, descriptions, tags; Related video = " + TITLE, ""]
for slug, t, d, tg in SH:
    lines += [f"=== {slug}.mp4 ===", f"RELATED VIDEO: {TITLE}", "TITLE", t, "DESCRIPTION", d, "TAGS", tg, ""]
open(os.path.join(root, "shorts", "shorts_metadata.txt"), "w", encoding="utf-8").write("\n".join(lines))
print(chapters); print("tags", len(tags))
