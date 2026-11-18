# -*- coding: utf-8 -*-
"""换背景：替换模板里 4 张背景位图，并把封面/封底/章节页的文字改成深底配色。"""
import os
import re
import shutil
import sys
import io
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu
from pptx.oxml.ns import qn

DECK = "骆绍杰-电气工程及其自动化-职业生涯规划.pptx"
BG_DIR = "media_bg"
TMP = "_bg_tmp.pptx"

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0x9F, 0xE2, 0xF5)
MUTED = RGBColor(0xBB, 0xD6, 0xE6)
CYAN_TXT = RGBColor(0x6F, 0xD3, 0xEA)
CYAN_LINE = RGBColor(0x19, 0xB9, 0xD8)

# ---------------------------------------------------------------- 1. 换位图
BG_FILES = ["image1.png", "image2.png", "image3.png", "image4.png"]
new_bytes = {}
for n in BG_FILES:
    p = os.path.join(BG_DIR, n)
    if not os.path.exists(p):
        raise SystemExit(f"missing background {p}")
    new_bytes[n] = open(p, "rb").read()

zin = zipfile.ZipFile(DECK, "r")
zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
replaced = 0
for item in zin.infolist():
    data = zin.read(item.filename)
    base = os.path.basename(item.filename)
    if item.filename.startswith("ppt/media/") and base in new_bytes:
        data = new_bytes[base]
        replaced += 1
    zout.writestr(item, data)
zout.close()
zin.close()
shutil.move(TMP, DECK)
print("backgrounds replaced:", replaced)


# ---------------------------------------------------------------- 2. 文字配色
def walk(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from walk(sh.shapes)
        else:
            yield sh


def colour(shape, index, rgb, size=None, bold=None):
    p = shape.text_frame.paragraphs[index]
    for r in p.runs:
        r.font.color.rgb = rgb
        if size:
            r.font.size = size
        if bold is not None:
            r.font.bold = bold


prs = Presentation(DECK)

# 封面 & 封底
for idx in (1, 22):
    s = prs.slides[idx - 1]
    for name, col in (("标题 1", WHITE),
                      ("副标题 2", LIGHT),
                      ("文本占位符 4", MUTED),
                      ("文本占位符 3", MUTED)):
        for sh in s.shapes:
            if sh.name == name and sh.has_text_frame:
                for i in range(len(sh.text_frame.paragraphs)):
                    colour(sh, i, col)

# 章节页：编号用浅青，标题用白；装饰线改青色；删掉多余描边框
for idx in (3, 7, 10, 16, 20):
    s = prs.slides[idx - 1]
    drop = []
    for sh in s.shapes:
        if sh.name in ("文本框 22", "文本框 5") and sh.has_text_frame and len(sh.text_frame.paragraphs) >= 2:
            colour(sh, 0, CYAN_TXT)
            colour(sh, 1, WHITE)
        elif sh.name == "任意多边形: 形状 33":
            sh.line.color.rgb = CYAN_LINE
            sh.line.width = Emu(28575)
        elif sh.name == "矩形 48":
            drop.append(sh)
    for sh in drop:
        el = sh._element
        el.getparent().remove(el)

prs.save(DECK)
print("text recoloured")
