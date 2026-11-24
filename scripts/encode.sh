#!/bin/bash
# 把渲染好的片段编码成适合滚动擦洗的 mp4。
# 用法：
#   bash scripts/encode.sh previz desk    # 480p 预演 → site/assets/vid（调试用，文件名同成片）
#   bash scripts/encode.sh final desk     # 1080p 横屏成片
#   bash scripts/encode.sh final mobile   # 720p 竖屏成片（-m 后缀）
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODE="${1:?previz|final}"; CHAIN="${2:?desk|mobile}"

if [ "$CHAIN" = "mobile" ]; then
  SRC="work/vid/$MODE-m"; OUT="site/assets/vid"; SUF="-m"
  VF="scale=720:-2,unsharp=5:5:0.8:5:5:0.0"; CRF=23; GOP=4
else
  SRC="work/vid/$MODE"; OUT="site/assets/vid"; SUF=""
  VF="unsharp=5:5:0.8:5:5:0.0"; CRF=20; GOP=8
fi
[ -d "$SRC" ] || { echo "missing $SRC"; exit 1; }
mkdir -p "$OUT"

enc() { # infile outname
  local in="$1" name="$2"
  [ -s "$in" ] || { echo "MISS $in"; return 1; }
  ffmpeg -v error -y -i "$in" -an -vf "$VF" \
    -c:v libx264 -preset slow -crf "$CRF" -pix_fmt yuv420p \
    -g "$GOP" -keyint_min "$GOP" -sc_threshold 0 -movflags +faststart \
    "$OUT/$name"
  echo "enc $name $(du -h "$OUT/$name" | cut -f1)"
}

# 注意：mobile 源文件名已带 -m 后缀（gen_chain 的 CHAIN=mobile 产出），不能再加一次。
for f in "$SRC"/dive_*.mp4; do
  base="$(basename "$f" .mp4)"
  out="$base.mp4"
  [ "$CHAIN" = "desk" ] && out="${base}${SUF}.mp4"
  enc "$f" "$out"
done
for f in "$SRC"/conn_*.mp4; do
  [ -e "$f" ] || continue
  base="$(basename "$f" .mp4)"
  out="$base.mp4"
  [ "$CHAIN" = "desk" ] && out="${base}${SUF}.mp4"
  enc "$f" "$out"
done
echo "=== encode $MODE $CHAIN done ==="
ls -la "$OUT"
