#!/usr/bin/env python3
"""生成 README / OG 用的 1200x630 预览图（macOS PingFang 中文字体）。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
W, H = 1200, 630
BG = (12, 16, 14)
INK = (236, 232, 220)
SOFT = (165, 171, 160)
ACCENT = (159, 184, 160)
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

canvas = Image.new("RGB", (W, H), BG)
# 右侧用影院定帧压暗做背景
bg = Image.open("work/stills/still_8.png").convert("RGB").resize((760, H))
bg = ImageEnhance.Brightness(bg).enhance(0.42)
canvas.paste(bg, (W - 760, 0))
# 左侧渐变压暗，保证文字可读
grad = Image.new("L", (620, H), 0)
gd = ImageDraw.Draw(grad)
for x in range(620):
    gd.line([(x, 0), (x, H)], fill=int(255 * (1 - x / 620)))
dark = Image.new("RGB", (620, H), BG)
canvas.paste(dark, (0, 0), grad)

d = ImageDraw.Draw(canvas)
f_kicker = ImageFont.truetype(FONT, 26, index=0)
f_title = ImageFont.truetype(FONT, 74, index=0)
f_sub = ImageFont.truetype(FONT, 27, index=0)
f_meta = ImageFont.truetype(FONT, 22, index=0)

x = 78
d.rounded_rectangle([x, 96, x + 250, 146], radius=25, outline=(90, 100, 92), width=2)
d.text((x + 26, 105), "手绘动画 · 滚动叙事", font=f_kicker, fill=SOFT)
d.text((x, 200), "我亲爱的，", font=f_title, fill=INK)
d.text((x, 296), "繁荣之外的故乡", font=f_title, fill=INK)
d.text((x, 418), "一次向动画电影《大世界》致敬的沉浸式阅读", font=f_sub, fill=SOFT)
d.text((x, 470), "8 章手绘场景 · 一镜穿行 · 30 段 AI 运镜", font=f_meta, fill=ACCENT)
d.text((x, 540), "Seedream 5.5 定帧    ×    Seedance 2.5 运镜", font=f_meta, fill=(120, 128, 120))

canvas.save("preview.jpg", quality=90)
print("ok preview.jpg", os.path.getsize("preview.jpg") // 1024, "KB")
