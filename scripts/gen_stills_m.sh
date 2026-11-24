#!/bin/bash
# 9:16 竖屏定帧（供手机原生竖屏链当首帧）。并发 2，断点可重跑。
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=/usr/bin/python3
mkdir -p work/stills_m work/logs

refs_1="reference/ref1.webp"
refs_2="reference/ref1.webp"
refs_3="reference/ref1.webp"
refs_4="reference/ref1.webp reference/ref2.webp"
refs_5="reference/ref1.webp reference/ref5.webp"
refs_6="reference/ref3.webp reference/ref5.webp"
refs_7="reference/ref2.webp reference/ref3.webp"
refs_8="reference/ref6.webp"

job() {
  local n="$1"; shift
  if [ -s "work/stills_m/still_$n.png" ]; then echo "m-still_$n exists, skip"; return; fi
  $PY scripts/arkgen25.py still --prompt "work/prompts_m/still_m_$n.txt" \
    --out "work/stills_m/still_$n.png" --size 1152x2048 --ref "$@" \
    > "work/logs/mstill_$n.log" 2> "work/logs/mstill_$n.err" \
    && echo "m-still_$n OK" || echo "m-still_$n FAIL"
}

for n in 1 2 3 4 5 6 7 8; do
  eval "refs=\$refs_$n"
  job "$n" $refs &
  if [ "$(jobs -r | wc -l)" -ge 2 ]; then wait -n 2>/dev/null || wait; fi
done
wait
echo "=== mobile stills done ==="
ls -la work/stills_m/
