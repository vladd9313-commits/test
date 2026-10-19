#!/bin/sh
# compose_all.sh FRAMES_ROOT REVIEW_PREFIX_DIR — compose + review every Short in shorts.tsv
F=$1; R=$2
while IFS='	' read n tools scr mp4 id; do
  t=""; case $n in caveman_highway|caveman_waiting_room|caveman_firefighter) t=--timer;; esac
  out=${mp4%.mp4}_hook.mp4
  python3 compose.py $mp4 $F/$n $out work/$n $t < /dev/null | tail -1
  sh review.sh $mp4 $out $R/rv_$n < /dev/null | sed "s/^/$n: /"
done < shorts.tsv
