#!/usr/bin/env python3
"""把 work/stills 下的 PNG 定帧转成网站用的 webp 海报（横屏 1800 宽 / 竖屏 1000 宽）。"""
import os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIRS = [("work/stills", "site/assets", 1800), ("work/stills_m", "site/assets", 1000)]
os.chdir(ROOT)
os.makedirs("site/assets", exist_ok=True)

n = 0
for src_dir, out_dir, width in SRC_DIRS:
    if not os.path.isdir(src_dir):
        continue
    for fn in sorted(os.listdir(src_dir)):
        if not fn.lower().endswith(".png"):
            continue
        stem = os.path.splitext(fn)[0]                 # still_1 / still_1 ...
        tag = "-m" if src_dir.endswith("_m") else ""
        out = os.path.join(out_dir, f"{stem}{tag}.webp")
        im = Image.open(os.path.join(src_dir, fn)).convert("RGB")
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        im.save(out, "WEBP", quality=84, method=6)
        print("ok", out, f"{os.path.getsize(out)//1024}KB")
        n += 1
print(f"{n} posters done")
