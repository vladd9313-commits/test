#!/bin/sh
# review.sh ORIG.mp4 HOOKED.mp4 OUTPREFIX — specs, frame sheet, seam strip, SFX vs voice levels
O=$1; Hk=$2; P=$3
ffprobe -v error -count_frames -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,nb_read_frames -show_entries format=duration -of compact "$Hk" | tr '\n' ' '; echo
ffprobe -v error -count_frames -show_entries stream=nb_read_frames -show_entries format=duration -of compact "$O" | tr '\n' ' '; echo
ffmpeg -v error -y -i "$Hk" -vf "select='lt(n\,48)*not(mod(n\,3))',scale=180:-1,tile=8x2" -frames:v 1 "${P}_sheet.jpg"
ffmpeg -v error -y -i "$Hk" -vf "select='between(n\,39\,47)',scale=200:-1,tile=9x1" -frames:v 1 "${P}_seam.jpg"
for f in "$O" "$Hk"; do ffmpeg -v error -y -i "$f" -t 2.2 -ac 1 -ar 48000 -f s16le "$f.raw"; done
python3 -c "
import numpy as np
a=np.fromfile('$O.raw','<i2')/32768; b=np.fromfile('$Hk.raw','<i2')/32768; n=min(len(a),len(b)); d=b[:n]-a[:n]
print(' '.join(f'{t}:{20*np.log10(np.sqrt((a[int(t*48000):int(t*48000)+2400]**2).mean())+1e-9):.0f}/{20*np.log10(np.sqrt((d[int(t*48000):int(t*48000)+2400]**2).mean())+1e-9):.0f}' for t in (0.06,0.5,0.62,1.0,1.25,1.35,2.0)), ' peak', round(20*np.log10(np.abs(b).max()),1))"
rm -f "$O.raw" "$Hk.raw"
