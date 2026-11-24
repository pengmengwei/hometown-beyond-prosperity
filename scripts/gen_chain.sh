#!/bin/bash
# 整条运镜链渲染。用法：
#   bash scripts/gen_chain.sh previz   # 480p，dive 8s / conn 5s（先跑这条验证）
#   bash scripts/gen_chain.sh final    # 1080p，dive 8s / conn 5s
#   MODE=mobile bash scripts/gen_chain.sh final   # 竖屏链（需要竖屏首帧，见 gen_mobile 脚本）
# 断点安全：已存在的 mp4 自动跳过；失败看 work/logs/<name>.err 后重跑本脚本。
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=/usr/bin/python3
GEN="scripts/arkgen25.py"
MODE="${1:-previz}"
CHAIN="${CHAIN:-desk}"          # desk | mobile
NAMES="1 2 3 4 5 6 7 8"

if [ "$MODE" = "final" ]; then RES=1080p; else RES=480p; fi
DIVE_DUR=8; CONN_DUR=5
if [ "$CHAIN" = "mobile" ]; then
  SUF="-m"; STILLDIR=work/stills_m
else
  SUF=""; STILLDIR=work/stills
fi
OUT="work/vid/$MODE$SUF"; FR="work/frames/$MODE$SUF"
mkdir -p "$OUT" "$FR" work/logs

run() { # logbase cmd...
  local base="$1"; shift
  if [ -s "$OUT/$base.mp4" ]; then echo "$base exists, skip"; return 0; fi
  "$@" > "work/logs/$base.log" 2> "work/logs/$base.err" \
    && echo "$base OK" || { echo "$base FAIL"; tail -3 "work/logs/$base.err"; }
}

# ---- Phase 1: 8 dives（各自从定帧起画）----
echo "=== Phase 1: dives ($MODE $CHAIN, $RES) ==="
pids=""
for n in $NAMES; do
  run "dive_$n$SUF" $PY "$GEN" dive \
    --prompt "work/prompts/dive_$n.txt" \
    --start "$STILLDIR/still_$n.png" \
    --out "$OUT/dive_$n$SUF.mp4" --res "$RES" --dur "$DIVE_DUR" &
  pids="$pids $!"
  if [ "$(jobs -r | wc -l)" -ge 3 ]; then wait -n 2>/dev/null || wait; fi
done
wait

# 全部 dive 成功才抽帧、继续转场
for n in $NAMES; do
  [ -s "$OUT/dive_$n$SUF.mp4" ] || { echo "dive_$n missing, stop before connectors"; exit 1; }
done

# ---- Phase 2: 抽每段 dive 的首帧/末帧 ----
echo "=== Phase 2: boundary frames ==="
for n in $NAMES; do
  ffmpeg -v error -y -ss 0 -i "$OUT/dive_$n$SUF.mp4" -frames:v 1 -q:v 2 "$FR/first_$n.png"
  ffmpeg -v error -y -sseof -0.15 -i "$OUT/dive_$n$SUF.mp4" -frames:v 1 -q:v 2 "$FR/last_$n.png"
done
echo "frames -> $FR"

# ---- Phase 3: 7 connectors（首帧=上一段末帧，末帧=下一段首帧，双锁）----
echo "=== Phase 3: connectors ==="
prev=""
for n in $NAMES; do
  if [ -n "$prev" ]; then
    run "conn_${prev}_$n$SUF" $PY "$GEN" conn \
      --prompt "work/prompts/conn_$prev.txt" \
      --start "$FR/last_$prev.png" --end "$FR/first_$n.png" \
      --out "$OUT/conn_${prev}_$n$SUF.mp4" --res "$RES" --dur "$CONN_DUR" &
    if [ "$(jobs -r | wc -l)" -ge 3 ]; then wait -n 2>/dev/null || wait; fi
  fi
  prev="$n"
done
wait
echo "=== chain $MODE $CHAIN done ==="
ls -la "$OUT"
