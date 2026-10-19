#!/bin/sh
# render_all.sh FRAMES_ROOT name...  — 3 hooks at a time
R=$1; shift
printf '%s\n' "$@" | xargs -P 3 -I{} sh -c "node render_generic.js work/{} $R/{} 46 8 > $R/{}.log 2>&1; echo done {}"
