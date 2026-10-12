"""Write youtube_metadata.txt for the kissing video: title, A/B titles, description with chapters from the voiceover timings, tags."""
import json, os
root = os.path.join(os.path.dirname(__file__), "..")
tim = json.load(open(os.path.join(root, "voiceover", "timings.json")))
CHAPTERS = {
    "B01": "Was that a kiss?", "B02": "The kiss paradox", "B03": "What counts as a kiss?",
    "B04": "Kissing may be 20 million years old", "B05": "Who 'invented' kissing? (myth)",
    "B06": "Suspect 1: grooming", "B07": "Suspects 2 and 3: kiss-feeding and the sniff",
    "B08": "Neanderthal tooth plaque", "B09": "The tree-chewing Neanderthal", "B10": "Fewer than half of 168 cultures",
    "B11": "Noses, greetings and culture", "B12": "Lips, closed eyes and the head tilt", "B13": "A kiss is a close-up check",
    "B14": "The make-up kiss is older than us", "B15": "The first kissing rules", "B16": "Rome overdoes it",
    "B17": "Germs, cameras and Hollywood", "B18": "Why kissing should have died out", "B19": "Why the kiss survived",
    "B20": "Back to the fire",
}
def tc(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"
first = {}
for t in tim: first.setdefault(t["block"], t["start"])
chapters = "\n".join(f"{tc(first[b] if b != 'B01' else 0)} {CHAPTERS[b]}" for b in sorted(first))
desc = f"""45,000 years ago, someone by the fire leans in close... and sniffs your cheek. Was that a kiss?

Our ape ancestors were probably kissing somewhere around 17 to 21 million years ago. Yet when anthropologists checked 168 cultures, romantic kissing was recorded in fewer than half of them. So did ancient humans actually kiss? In this video: what scientists count as a kiss, the 2025 Oxford study on the origin of kissing, the three big theories (grooming, kiss-feeding and the sniff), Neanderthal tooth plaque and a microbe swap, the Maori hongi and the Inuit kunik, why most people tilt their head to the right, the estimated 80 million bacteria in a 10-second kiss, chimps' make-up kisses, the first kissing rules in Mesopotamia and Persia, the Roman emperor who banned everyday kissing, the first movie-kiss scandal, and why the kiss survived it all.

{chapters}

#ancienthumans #history #kissing"""
tags = ("did ancient humans kiss, when did humans start kissing, why do humans kiss, history of kissing, did cavemen kiss, "
        "did neanderthals kiss, origin of kissing, evolution of kissing, first kiss in history, why do we kiss, science of kissing, "
        "chimpanzee kiss, bonobos, neanderthals, ancient humans, ancient history, ancient rome, human evolution, explained")
assert len(tags) <= 500, len(tags)
out = f"""TITLE
Did Ancient Humans Actually Kiss?

ALT TITLES (A/B test)
Kissing May Be 20 Million Years Old. So Why Didn't Everyone?
How Ancient Humans Actually Learned to Kiss

DESCRIPTION
{desc}

TAGS
{tags}

THUMBNAILS
thumbnail/thumbnail_A_ew_why.jpg (main), thumbnail/thumbnail_B_blame_the_apes.jpg (A/B)

SETTINGS
Audience: No, it's not made for kids. Age restriction: No. Category: Education.
"""
open(os.path.join(root, "youtube_metadata.txt"), "w", encoding="utf-8").write(out)
print(out[:400]); print("tags chars:", len(tags))
