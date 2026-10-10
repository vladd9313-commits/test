export const meta = {
  name: 'write-shorts-v2-scripts',
  description: 'Write 3 candidate scripts per Short, judge and fix the best one, validate format',
  phases: [
    { title: 'Write', detail: '3 angles per Short' },
    { title: 'Judge', detail: 'pick + fix best, fact-check against source script' },
  ],
}

const RULES = `FORMAT RULES (Shorts template v2):
- Narration: 55-80 words total, 8-13 lines, each line 2-9 words. Spoken at ~175 wpm -> 20-32 seconds.
- Line 1 is the HOOK: max 8 words, a provocative claim that already hints at the payoff, spoken directly to the viewer. Never start with "And", "So", "Now", "But".
- ONE topic only, built around ONE surprising concrete fact (a number, a name, an image).
- The LAST line must loop seamlessly back into line 1 (repeat or lead into the hook phrase) so a replay feels continuous.
- No calls to action, no "subscribe", no "full story" in the narration.
- title_overlay: 2-6 words, ALL CAPS, shown at the top for the whole Short (can equal the hook).
- Every line gets ONE drawable scene for a simple stick-figure renderer. Use these character tokens: {CAVE} caveman, {WOMAN} cavewoman, {GUY} modern man, {CAT} sandy African wildcat, {HOUSECAT} orange tabby, {EGYPT} ancient Egyptian man, {SCI} scientist, {APE} ape ancestor, {SUMER} Sumerian bearded man. Supported animals/props by name: lion, leopard, hyena, dog, wolf, mouse/mice, black cat, grain pot/clay jar, fire/campfire, hut, boat/ship, mummy, skeleton/bones, cardboard box, crown, heart, question mark, light bulb, sparkles, big red X, Z letters (sleeping), stone tablet with a number in quotes like "9,500". Supported settings by keyword: cave, night/moon, desert/savanna, Egypt/pyramid, jungle, sea, lab, chalkboard, living room/couch/bed, medieval village, village/hut, Greek/Roman, Sumer/Mesopotamia, map, timeline. Keep scenes to 1-3 characters and describe emotion (shocked, happy, sad, angry, sleeping, smug, confused).
- FACTS: use only facts that appear in the SOURCE long-video script (it was fact-checked). Keep its hedges ("may", "one idea is", "probably") where it hedged. No new facts.
- Also write: yt_title (max 60 chars, may end with one emoji), yt_description (2 short sentences + "Full story on the channel!" + 3 hashtags incl. #shorts), yt_tags (comma-separated, max 400 chars).`

const SHORTS = [
  { slug: 'cats_dead_mice', video: 'cats', src: '/home/user/test/production/script_part3.txt (block "The desert hunter still living in your house")', brief: 'Why cats bring you dead mice: mother cats teach kittens to hunt; your cat may think you are a hopeless hunter. Existing draft hook: "Your cat thinks you can\'t hunt."' },
  { slug: 'cats_egypt', video: 'cats', src: '/home/user/test/production/script_part2.txt (block "Egypt: when cats became gods")', brief: 'Pick the single strongest Egypt fact: shaving eyebrows when the family cat died (Herodotus), OR killing a cat could get you killed (Diodorus), OR ~19 tons of cat mummies shipped to England as fertilizer. One fact only.' },
  { slug: 'cats_meow', video: 'cats', src: '/home/user/test/production/script_part3.txt (block "How cats hacked the human brain")', brief: 'Adult cats almost never meow at each other — the meow is mostly for humans; kittens meow at mothers; feral cats meow less. Optional: solicitation purr hides a baby-like cry.' },
  { slug: 'alcohol_drunk_goddess', video: 'alcohol', src: '/home/user/test/video2_alcohol/script_part3.txt (block "Egypt: beer for the pyramid builders and a drunk goddess")', brief: 'The Sekhmet myth: Ra dyed beer red, Sekhmet thought it was blood, drank it, passed out, humanity saved by a hangover; Egyptians celebrated a festival of drunkenness.' },
  { slug: 'alcohol_spit_beer', video: 'alcohol', src: '/home/user/test/video2_alcohol/script_part3.txt (block "Every culture found its own drink")', brief: 'Chicha in the Andes started by chewing corn and spitting it into the pot; saliva enzymes turn starch into sugar; Japan had a chewed rice drink.' },
  { slug: 'alcohol_beer_straws', video: 'alcohol', src: '/home/user/test/video2_alcohol/script_part2.txt (block "Sumer: paid in beer, drinking through straws")', brief: 'Sumerian beer was thick and full of husks so people drank through long straws; a gold and lapis straw from the royal tombs of Ur.' },
  { slug: 'sleep_night_watch', video: 'sleep', src: '/home/user/test/video3_sleep/script_part3.txt (block "The night watch: why grandma wakes up at 5 a.m.")', brief: 'Hadza study: 33 people, 20 nights, everyone asleep at the same time for only about 18 minutes total; early birds and night owls may be an ancient night watch.' },
  { slug: 'sleep_3am', video: 'sleep', src: '/home/user/test/video3_sleep/script_part3.txt (block "First sleep and second sleep")', brief: 'Waking at 3 a.m.: historian Roger Ekirch found references to "first sleep" and "second sleep"; people woke for an hour at night and did things; may not mean your body is broken.' },
  { slug: 'sleep_dirty_bed', video: 'sleep', src: '/home/user/test/video3_sleep/script_part1.txt (block "Ape heritage: the nest builders")', brief: 'Chimps build a fresh nest every night; scientists found chimp nests had far fewer bacteria than human beds.' },
]

const LINE = { type: 'object', properties: { text: { type: 'string' }, scene: { type: 'string' } }, required: ['text', 'scene'] }
const SCRIPT = { type: 'object', properties: {
  angle: { type: 'string' }, title_overlay: { type: 'string' }, lines: { type: 'array', items: LINE },
  yt_title: { type: 'string' }, yt_description: { type: 'string' }, yt_tags: { type: 'string' } },
  required: ['title_overlay', 'lines', 'yt_title', 'yt_description', 'yt_tags'] }
const CANDS = { type: 'object', properties: { candidates: { type: 'array', items: SCRIPT } }, required: ['candidates'] }
const JUDGED = { type: 'object', properties: {
  winner_index: { type: 'number' }, reasons: { type: 'string' }, fact_check_notes: { type: 'string' }, final: SCRIPT },
  required: ['winner_index', 'reasons', 'fact_check_notes', 'final'] }

const words = s => s.lines.reduce((n, l) => n + l.text.trim().split(/\s+/).length, 0)
function problems(s) {
  const p = []
  const w = words(s)
  if (w < 50 || w > 85) p.push(`narration has ${w} words (target 55-80)`)
  if (s.lines.length < 8 || s.lines.length > 14) p.push(`${s.lines.length} lines (target 8-13)`)
  const hook = s.lines[0] ? s.lines[0].text.trim().split(/\s+/).length : 0
  if (hook > 9) p.push(`hook has ${hook} words (max 8)`)
  if (s.lines[0] && /^(and|so|now|but)\b/i.test(s.lines[0].text.trim())) p.push('hook starts with a filler word')
  s.lines.forEach((l, i) => { if (l.text.includes('|') || l.scene.includes('|')) p.push(`line ${i + 1} contains "|"`) })
  if (/subscribe|full story/i.test(s.lines.map(l => l.text).join(' '))) p.push('CTA inside narration')
  return p
}

const results = await pipeline(SHORTS,
  sh => agent(`You write YouTube Shorts scripts for a stick-figure "ancient humans explained" channel.
Read the SOURCE long-video script first: ${sh.src}. Lines in that file have the format "narration | scene".
Short slug: ${sh.slug}. Brief: ${sh.brief}

Write THREE candidate scripts with clearly different angles (e.g. 1: direct "you" claim hook, 2: shocking-number/image hook, 3: myth-bust "you were told X" hook). ${RULES}`,
    { label: `write:${sh.slug}`, phase: 'Write', schema: CANDS }),
  (cands, sh) => agent(`You are a ruthless YouTube Shorts editor and fact-checker. Read the SOURCE script ${sh.src} to check facts.
Below are candidate scripts for the Short "${sh.slug}" (brief: ${sh.brief}).
Score each on: (a) hook strength in the first 1.5 seconds, (b) one clear topic + one concrete surprising fact, (c) payoff density (no filler), (d) loop: does the last line flow back into line 1, (e) factual faithfulness to the SOURCE (no new facts, hedges kept), (f) every scene is drawable with the renderer limits, (g) format rules.
Pick the best, then FIX every remaining issue with minimal edits (you may graft a better line from another candidate). Return the corrected final script.
${RULES}

CANDIDATES:
${JSON.stringify(cands, null, 1)}`,
    { label: `judge:${sh.slug}`, phase: 'Judge', schema: JUDGED })
    .then(j => j ? { slug: sh.slug, video: sh.video, ...j, problems: problems(j.final), words: words(j.final) } : null))

const ok = results.filter(Boolean)
for (const r of ok) log(`${r.slug}: ${r.words} words, ${r.final.lines.length} lines${r.problems.length ? ' — ISSUES: ' + r.problems.join('; ') : ''}`)
if (ok.length < SHORTS.length) log(`missing: ${SHORTS.filter(s => !ok.find(r => r.slug === s.slug)).map(s => s.slug).join(', ')}`)
return ok
