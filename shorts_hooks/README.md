# Motion hooks for Shorts

The first 1.5 s of each Short become a moving hook: rush in on subject A with a big word, whip-pan to subject B with a red word,
pull back into the Short's own framing while its title drops in and the timer badge flies to its corner.
The hook ends on the Short's real frame (layers come from the same renderer, the Ken Burns zoom is measured), crossfades
over frames 42–44, and the original voice and captions run underneath.

1. `python3 build_layers.py TOOLS SCRIPT.txt SHORT.mp4 work/NAME` — far plate, exact fg matte, timer badge, title lines, Ken Burns fit
2. `work/NAME/config.json` — focus points, zooms and words (all in `configs.json`)
3. `node render_generic.js work/NAME FRAMES/NAME 46 8` — 46 frames, 8 sub-frames each (motion blur)
4. `python3 compose.py SHORT.mp4 FRAMES/NAME OUT.mp4 [--timer]` — live captions keyed in, crossfade, SFX ducked under the voice
5. `sh review.sh SHORT.mp4 OUT.mp4 PREFIX` — specs, frame sheet, seam strip, SFX/voice levels

`lion/` is the hand-built first version for "You Can't Outrun a Cave Lion".
