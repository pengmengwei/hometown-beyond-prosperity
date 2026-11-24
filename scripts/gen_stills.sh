#!/bin/bash
# 批量生成场景定帧（并发 3）。用法: bash scripts/gen_stills.sh
# 已存在的定帧跳过；失败的看 work/logs/still_N.err 后单独重跑。
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=/usr/bin/python3
mkdir -p work/stills work/logs

# 每个场景的参考图（风格参考，prompt 内已声明禁止照搬内容）
refs_2="reference/ref1.webp"
refs_3="reference/ref1.webp"
refs_4="reference/ref1.webp reference/ref2.webp"
refs_5="reference/ref1.webp reference/ref5.webp"
refs_6="reference/ref3.webp reference/ref5.webp"
refs_7="reference/ref2.webp reference/ref3.webp"
refs_8="reference/ref6.webp"

job() {
  local n="$1"; shift
  if [ -s "work/stills/still_$n.png" ]; then echo "still_$n exists, skip"; return; fi
  $PY scripts/arkgen25.py still --prompt "work/prompts/still_$n.txt" \
    --out "work/stills/still_$n.png" --size 2048x1152 --ref "$@" \
    > "work/logs/still_$n.log" 2> "work/logs/still_$n.err" \
    && echo "still_$n OK" || echo "still_$n FAIL"
}

pids=""
for n in 2 3 4 5 6 7 8; do
  eval "refs=\$refs_$n"
  job "$n" $refs &
  pids="$pids $!"
  # 每 3 个收一次，限制并发
  if [ "$(jobs -r | wc -l)" -ge 3 ]; then wait -n 2>/dev/null || wait; fi
done
wait
echo "=== batch done ==="
ls -la work/stills/
