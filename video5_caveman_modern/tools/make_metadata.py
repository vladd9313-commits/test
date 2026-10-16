"""Write youtube_metadata.txt (title, A/B titles, description with chapters from the voiceover timings, tags) and shorts/shorts_metadata.txt."""
import json, os
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
TITLE = "How Long a Caveman Would Last in Every Modern Place"
CHAPTERS = {"B01": "Oog wakes up in your city", "B02": "The rules", "B03": "1. The library", "B04": "2. The gym",
            "B05": "3. The office", "B06": "4. The zoo", "B07": "5. The all-you-can-eat buffet", "B08": "6. The supermarket",
            "B09": "7. The mall escalator", "B10": "8. Airport security", "B11": "9. The subway", "B12": "10. The highway",
            "B13": "11. The real deadliest place", "B14": "What if Oog grew up here?"}
def tc(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"
first = {}
for t in tim: first.setdefault(t["block"], t["start"])
chapters = "\n".join(f"{tc(first[b] if b != 'B01' else 0)} {CHAPTERS[b]}" for b in sorted(first))
desc = f"""A 40,000-year-old caveman wakes up in your city. We drop him into 11 modern places and start a timer.

Meet Oog: a real Homo sapiens, same brain as you, very good with a spear, and he has never seen a wheel, a door handle or a written word. In the library he lasts all day. On the highway, about four seconds. But the place that could actually kill him looks completely safe. In this video: why a goat at the petting zoo breaks his brain, why he probably can't digest your milk, what a moving staircase looks like to a hunter, why a subway car is six mammoths, why even kids misjudge fast cars, and the crowd diseases that are younger than farming.

{chapters}

#caveman #history #ancienthumans"""
tags = ("caveman in the modern world, how long would a caveman last, how long you'd last, caveman, stone age, ancient humans, "
        "could a caveman survive today, prehistoric human, ice age, hunter gatherers, hadza, funny history, history explained, "
        "stick figure animation, animated explainer, survival, what if, neanderwhy")
assert len(tags) <= 500, len(tags)
open(os.path.join(root, "youtube_metadata.txt"), "w", encoding="utf-8").write(f"""TITLE
{TITLE}

ALT TITLES (A/B test)
A Caveman Wakes Up in 2026. How Long Does He Last?
We Dropped a Caveman Into 11 Modern Places

DESCRIPTION
{desc}

TAGS
{tags}

THUMBNAILS
thumbnail/thumbnail_A_lasted_4_seconds.jpg (main), thumbnail/thumbnail_B_deadliest_place.jpg (A/B)

SETTINGS
Audience: No, it's not made for kids. Age restriction: No. Category: Education.
""")
SH = [("caveman_highway", "A Caveman on a Highway Lasts 4 Seconds 🚗",
       "The fastest thing a caveman ever saw was a charging lion. Highway cars go faster, and there are hundreds of them. Full video: tap the video link on this Short. #shorts #caveman #history",
       "caveman, caveman on a highway, how long would a caveman last, caveman in the modern world, stone age, ancient humans, lion speed, judging car speed, freeze response, funny history, history shorts, stick figure animation, shorts"),
      ("caveman_goat", "A Friendly Goat Would Break a Caveman's Brain 🐐",
       "Goats were only tamed around ten thousand years ago. In a caveman's world, every animal runs away or attacks, so a goat that walks up to you is very suspicious. Full video: tap the video link on this Short. #shorts #caveman #animals",
       "caveman, petting zoo, goat, domestication, when were goats domesticated, cave lion, ice age animals, caveman in the modern world, ancient humans, funny history, history shorts, stick figure animation, shorts"),
      ("caveman_waiting_room", "The Deadliest Place for a Caveman Isn't the Highway 🤒",
       "Many of our worst crowd diseases are younger than farming. Measles may be only about 2,500 years old, and a caveman has never met it. Full video: tap the video link on this Short. #shorts #caveman #science",
       "caveman, measles, crowd diseases, history of disease, vaccines, immunity, farming, caveman in the modern world, ancient humans, science facts, history shorts, stick figure animation, shorts")]
lines = ["SHORTS for video 5 — titles, descriptions, tags; Related video = " + TITLE, ""]
for slug, t, d, tg in SH:
    lines += [f"=== {slug}.mp4 ===", f"RELATED VIDEO: {TITLE}", "TITLE", t, "DESCRIPTION", d, "TAGS", tg, ""]
open(os.path.join(root, "shorts", "shorts_metadata.txt"), "w", encoding="utf-8").write("\n".join(lines))
print(chapters); print("tags", len(tags))
