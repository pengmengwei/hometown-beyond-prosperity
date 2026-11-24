#!/usr/bin/env python3
"""从横屏定帧 prompt 生成 9:16 竖屏版本：替换最后的构图句，风格前言保持逐字一致。"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.makedirs("work/prompts_m", exist_ok=True)

VERT = {
    1: "9:16 竖构图，藤编躺椅与茶几位于画面下半部，上半部留给墨绿夜空、远处烟囱剪影与交错电线，主体居中，两侧留出纵深。",
    2: "9:16 竖构图，蹲坐的女人与旧行李在画面下方三分之一处，工厂烟囱与灰黄浓烟占据上半部浑浊天空，空旷马路自下而上延伸。",
    3: "9:16 竖构图，小土坟与生锈狗碗在前景下方，黑绿色污染河道从画面底部向远方延伸，两岸垃圾与残竹在两侧，远处楼群压在地平线。",
    4: "9:16 竖构图，抽烟的男人与旧三轮车在画面下方，霓虹门面与湿洼反光向上延伸，交错电线划过画面顶部，人物居中偏下。",
    5: "9:16 竖构图，发光的保安亭在画面下半部，暖光方块在黑夜中格外突出，上半部留给空旷夜路、树影与唯一一盏路灯。",
    6: "9:16 竖构图，圆桌与两个男人位于画面下方，裸露灯泡与盘旋的香烟烟雾在画面上方，发黄瓷砖墙向顶部延伸，纵深感强。",
    7: "9:16 竖构图，玻璃柜台与金吊坠在画面下方三分之一，吊坠是唯一高光，高耸货架与惨白荧光灯管从两侧向上压迫。",
    8: "9:16 竖构图，孤独的观众剪影与暗红座椅在画面下方，巨大的冷白色发光银幕占据上方，光束中的尘埃自上而下飘浮。",
}

for n, comp in VERT.items():
    src = open(f"work/prompts/still_{n}.txt", encoding="utf-8").read().strip()
    # 去掉最后一句横屏构图描述（以 16:9 开头到结尾）
    src = re.sub(r"16:9 横构图[^\n]*$", "", src).strip()
    out = src + "\n\n场景竖版构图：" + comp + "\n"
    with open(f"work/prompts_m/still_m_{n}.txt", "w", encoding="utf-8") as f:
        f.write(out)
    print("ok", n)
print("mobile prompts ready")
