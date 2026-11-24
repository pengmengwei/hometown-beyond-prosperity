#!/bin/bash
# 成片渲染完成后的收尾：接缝复检 → 编码进 site/assets/vid（覆盖预演版）。
# 用法：bash scripts/finish.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "########## 横屏 1080p 接缝复检 ##########"
bash scripts/seam_check.sh final desk

echo "########## 竖屏 1080p 接缝复检 ##########"
bash scripts/seam_check.sh final mobile

echo "########## 编码横屏成片（crf20 gop8）##########"
bash scripts/encode.sh final desk

echo "########## 编码竖屏成片（720p gop4）##########"
bash scripts/encode.sh final mobile

echo "########## 站点视频清单 ##########"
ls -la site/assets/vid | head -40
echo "总大小：$(du -sh site/assets/vid | cut -f1)"
echo "DONE"
