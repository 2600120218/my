# -*- coding: utf-8 -*-
"""交付前自检：页数、标题序列、图表数据、空文本、文本溢出粗查。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pptx import Presentation
from pptx.util import Emu

f = "骆绍杰-电气工程及其自动化-职业生涯规划.pptx"
p = Presentation(f)
print("幻灯片数:", len(p.slides))
print("尺寸:", round(Emu(p.slide_width).inches, 3), "x", round(Emu(p.slide_height).inches, 3))


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from walk(sh.shapes)
        else:
            yield sh


for i, s in enumerate(p.slides, 1):
    texts = []
    charts = 0
    for sh in walk(s.shapes):
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append(sh.text_frame.text.replace("\n", " / "))
        if getattr(sh, "has_chart", False) and sh.has_chart:
            charts += 1
    head = texts[0][:40] if texts else "(无文本)"
    print(f"{i:02d} 文本块={len(texts):2d} 图表={charts} | {head}")


# 图表数据复核
for idx in (8,):
    for sh in walk(p.slides[idx - 1].shapes):
        if getattr(sh, "has_chart", False) and sh.has_chart:
            ch = sh.chart
            print("图表", sh.name, list(ch.plots[0].categories)[:3], "...",
                  [list(sr.values)[-2:] for sr in ch.series])
