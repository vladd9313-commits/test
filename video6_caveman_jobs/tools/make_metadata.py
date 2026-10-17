"""Write youtube_metadata.txt (title, A/B titles, description with chapters from the voiceover timings, tags) and shorts/shorts_metadata.txt."""
import json, os
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
TITLE = "How Long a Caveman Would Last in Every Job"
CHAPTERS = {"B01": "Oog needs a job", "B02": "The rules", "B03": "1. Night security guard", "B04": "2. Construction worker",
            "B05": "3. Restaurant chef", "B06": "4. Delivery runner", "B07": "5. Schoolteacher", "B08": "6. Barista",
            "B09": "7. Call center", "B10": "8. Cashier", "B11": "Scoreboard + 9. Dog walker", "B12": "10. Firefighter",
            "B13": "The perfect job", "B14": "How fast would he lose YOUR job?"}
def tc(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"
first = {}
for t in tim: first.setdefault(t["block"], t["start"])
chapters = "\n".join(f"{tc(first[b] if b != 'B01' else 0)} {CHAPTERS[b]}" for b in sorted(first))
desc = f"""A 40,000-year-old caveman needs a job. We give him 11 of them and start a timer every time.

Oog is a real Homo sapiens with the same brain as you, but he can't read, has never seen money, and thinks a phone voice is a spirit. As a night guard he's a natural. As a firefighter he lasts three seconds. In this video: the Hadza sleep study that found only 18 minutes when everyone was asleep, why some scientists think cooking made us human, persistence hunting in the Kalahari, the first schools, when people started drinking coffee, the 43,000-year-old Lebombo bone with 29 notches, why Oog has never seen a dog, why fire was treasure in the Ice Age, and the one job where he's the best in the world.

{chapters}

#caveman #history #ancienthumans"""
tags = ("how long would a caveman last, caveman jobs, caveman in the modern world, how long you'd last, caveman, stone age, "
        "ancient humans, hunter gatherers, hadza, persistence hunting, history of fire, funny history, history explained, "
        "stick figure animation, animated explainer, what if, neanderwhy")
assert len(tags) <= 500, len(tags)
open(os.path.join(root, "youtube_metadata.txt"), "w", encoding="utf-8").write(f"""TITLE
{TITLE}

ALT TITLES (A/B test)
We Gave a Caveman 11 Jobs. How Long Did He Last?
A Caveman Gets a Job. It Goes Badly.

DESCRIPTION
{desc}

TAGS
{tags}

THUMBNAILS
thumbnail/thumbnail_A_fired_3_seconds.jpg (main), thumbnail/thumbnail_B_perfect_job.jpg (A/B)

SETTINGS
Audience: No, it's not made for kids. Age restriction: No. Category: Education.
""")
SH = [("caveman_firefighter", "A Caveman Firefighter Lasts 3 Seconds 🔥",
       "In the Ice Age, fire was treasure. If yours went out, you could freeze. So when a caveman sees firefighters attacking a huge fire... Full video: tap the video link on this Short. #shorts #caveman #history",
       "caveman, caveman firefighter, how long would a caveman last, caveman jobs, history of fire, ice age, ancient humans, funny history, history shorts, stick figure animation, shorts"),
      ("caveman_dogs", "A Caveman Has Never Seen a Dog 🐕",
       "The oldest clear genetic evidence of dogs is around 15,000 years old. For a 40,000-year-old caveman, six barking wolf-shaped animals are a problem. Full video: tap the video link on this Short. #shorts #caveman #dogs",
       "caveman, dog domestication, when were dogs domesticated, wolves, dog walker, caveman jobs, ancient humans, funny history, history shorts, stick figure animation, shorts"),
      ("caveman_night_guard", "Only 18 Minutes When Everyone Was Asleep 🌙",
       "Scientists tracked Hadza hunter-gatherers at night: in more than 200 hours, everyone was asleep at the same time for just 18 minutes. That's why a caveman would be the perfect night guard. Full video: tap the video link on this Short. #shorts #sleep #history",
       "hadza sleep study, sentinel hypothesis, night watch, caveman, night security guard, why old people wake up early, sleep science, ancient humans, history shorts, stick figure animation, shorts")]
lines = ["SHORTS for video 6 — titles, descriptions, tags; Related video = " + TITLE, ""]
for slug, t, d, tg in SH:
    lines += [f"=== {slug}.mp4 ===", f"RELATED VIDEO: {TITLE}", "TITLE", t, "DESCRIPTION", d, "TAGS", tg, ""]
open(os.path.join(root, "shorts", "shorts_metadata.txt"), "w", encoding="utf-8").write("\n".join(lines))
print(chapters); print("tags", len(tags))
