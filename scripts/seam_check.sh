#!/bin/bash
# 全接缝 PSNR 质检：每个 connector 的首帧应对上一段 dive 末帧、末帧应对下一段 dive 首帧。
# 用法：bash scripts/seam_check.sh previz|final [desk|mobile]
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODE="${1:-previz}"; CHAIN="${2:-desk}"
if [ "$CHAIN" = "mobile" ]; then VID="work/vid/$MODE-m"; SUF="-m"; else VID="work/vid/$MODE"; SUF=""; fi
TMP="work/qa_frames/seams_${MODE}_${CHAIN}"
mkdir -p "$TMP"

psnr() { # a b  -> 打印 average 值
  ffmpeg -v info -i "$1" -i "$2" -lavfi psnr -f null - 2>&1 | grep -o "average:[0-9.]*" | cut -d: -f2
}

fail=0
for i in 1 2 3 4 5 6 7; do
  j=$((i+1))
  conn="$VID/conn_${i}_${j}${SUF}.mp4"
  [ -s "$conn" ] || { echo "conn_${i}_${j}: MISSING"; fail=1; continue; }
  cf="$TMP/c${i}_first.png"; cl="$TMP/c${i}_last.png"
  ffmpeg -v error -y -ss 0 -i "$conn" -frames:v 1 "$cf"
  ffmpeg -v error -y -sseof -0.1 -i "$conn" -frames:v 1 "$cl"
  # frames 目录与 vid 同级：work/frames/<mode>[-m]
  p1=$(psnr "$cf" "work/frames/$MODE$SUF/last_$i.png")
  p2=$(psnr "$cl" "work/frames/$MODE$SUF/first_$j.png")
  echo "seam $i->$j  start(vs last_$i)=${p1}dB  end(vs first_$j)=${p2}dB"
done
echo "=== seam check $MODE $CHAIN done（经验阈值：构图级合格 ≥18dB，首帧通常 >30dB）==="
