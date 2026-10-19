#!/bin/sh
# Rebuild the lion Short with its motion hook.
#   1) python3 ../make_layers.py assets          (character / background layers from the channel renderer)
#   2) node ../render_hook.js hook.html $W/sub frames 30 1.5334 8   (8 subframes per frame → motion blur)
#   3) sh build.sh $W                            (this script)
set -e
W=$1; S=/home/user/test/video7_you_in_oogs_world/shorts
python3 hook_sfx.py "$W/sfx.wav"
ffmpeg -v error -y -framerate 240 -i "$W/sub/s%05d.png" \
  -vf "tmix=frames=8,select='eq(mod(n\,8)\,7)',setpts=N/30/TB" -r 30 -c:v libx264 -crf 12 -pix_fmt yuv420p "$W/hook_only.mp4"
# hook covers frames 0–41, crossfades into the Short's own frames 42–44, then the Short plays untouched.
# SFX are ducked under the original voice and the mix is peak-limited.
ffmpeg -v error -y -i "$S/you_vs_lion.mp4" -i "$W/hook_only.mp4" -i "$W/sfx.wav" -filter_complex \
"[0:v]format=yuv420p[a];[1:v]format=yuv420p[b];[a][b]blend=all_expr='if(lt(N\,42)\,B\,if(lt(N\,45)\,A*(N-42)/3+B*(1-(N-42)/3)\,A))'[v];\
[0:a]aresample=48000,asplit[voice][sc];[2:a]volume=0.85[fx];[fx][sc]sidechaincompress=threshold=0.05:ratio=3:attack=5:release=150[fxd];\
[voice][fxd]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=false[aout]" \
  -map "[v]" -map "[aout]" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$S/you_vs_lion_hook.mp4"
echo done
