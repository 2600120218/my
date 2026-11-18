# -*- coding: utf-8 -*-
"""第二份 PPT 的收尾：换背景、把模板的蓝青系整体改成石墨+琥珀、封面文字改白。"""
import colorsys
import os
import re
import shutil
import sys, io
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu

DECK = "职业生涯规划-电气工程及其自动化-考研升学方向.pptx"
BG_DIR = "media_bg3"
TMP = "_bg3_tmp.pptx"

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SAND = RGBColor(0xE7, 0xD0, 0x8A)
MUTED = RGBColor(0xBF, 0xD2, 0xC2)
AMBER = RGBColor(0xD8, 0xB2, 0x3F)

TARGET_HUE = 158 / 360.0
HUE_LO, HUE_HI = 172 / 360.0, 268 / 360.0


# ---------------------------------------------------------------- 颜色映射
def remap_hex(hx):
    hx = hx.upper()
    r, g, b = int(hx[0:2], 16) / 255, int(hx[2:4], 16) / 255, int(hx[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.06:
        return hx
    if HUE_LO <= h <= HUE_HI:
        h = TARGET_HUE
        if s > 0.40 and l < 0.75:
            l = 0.20 + (l - 0.20) * 0.60
            s = min(s, 0.80)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return "%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))
    return hx


HEX_RE = re.compile(r'(val|lastClr)="([0-9A-Fa-f]{6})"')
changed = 0


def remap_xml(text):
    global changed

    def sub(m):
        global changed
        new = remap_hex(m.group(2))
        if new != m.group(2).upper():
            changed += 1
        return f'{m.group(1)}="{new}"'

    return HEX_RE.sub(sub, text)


# ---------------------------------------------------------------- 位图
def recolour_hue(src_bytes, out_path, hue_lo=0.47, hue_hi=0.75, sat_min=0.12,
                 target=0.439, sat_scale=1.0):
    im = Image.open(io.BytesIO(src_bytes))
    has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    rgba = im.convert("RGBA")
    arr = np.array(rgba).astype(np.float32) / 255.0
    rgb = arr[..., :3]
    mx = rgb.max(2)
    mn = rgb.min(2)
    diff = mx - mn
    sat = np.where(mx > 0, diff / np.maximum(mx, 1e-6), 0)
    hue = np.zeros_like(mx)
    m = (diff > 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    idx = m & (mx == r)
    hue[idx] = ((g[idx] - b[idx]) / diff[idx]) % 6
    idx = m & (mx == g)
    hue[idx] = ((b[idx] - r[idx]) / diff[idx]) + 2
    idx = m & (mx == b)
    hue[idx] = ((r[idx] - g[idx]) / diff[idx]) + 4
    hue = hue / 6.0

    mask = (hue >= hue_lo) & (hue <= hue_hi) & (sat >= sat_min)
    if not mask.any():
        (rgba if has_alpha else im.convert("RGB")).save(out_path, "PNG", optimize=True)
        return 0

    hh = np.where(mask, target, hue)
    ss = np.where(mask, np.clip(sat * sat_scale, 0, 1), sat)
    vv = mx
    i = (hh * 6.0).astype(np.int32) % 6
    f = hh * 6.0 - np.floor(hh * 6.0)
    p = vv * (1 - ss)
    q = vv * (1 - f * ss)
    t = vv * (1 - (1 - f) * ss)
    out = np.zeros_like(rgb)
    conds = [i == k for k in range(6)]
    out[conds[0]] = np.stack([vv, t, p], -1)[conds[0]]
    out[conds[1]] = np.stack([q, vv, p], -1)[conds[1]]
    out[conds[2]] = np.stack([p, vv, t], -1)[conds[2]]
    out[conds[3]] = np.stack([p, q, vv], -1)[conds[3]]
    out[conds[4]] = np.stack([t, p, vv], -1)[conds[4]]
    out[conds[5]] = np.stack([vv, p, q], -1)[conds[5]]

    out = np.where(mask[..., None], out * 0.88, out)
    res = np.concatenate([out * 255.0, arr[..., 3:4] * 255.0], axis=2)
    img = Image.fromarray(np.clip(res, 0, 255).astype(np.uint8), "RGBA")
    if has_alpha:
        img.save(out_path, "PNG", optimize=True)
    else:
        img.convert("RGB").save(out_path, "PNG", optimize=True)
    return int(mask.sum())


# ---------------------------------------------------------------- 打包
bg_bytes = {}
for n in ("image1.png", "image2.png", "image3.png", "image4.png"):
    p = os.path.join(BG_DIR, n)
    if not os.path.exists(p):
        raise SystemExit("missing " + p)
    bg_bytes[n] = open(p, "rb").read()

# 需要统一色调的位图：卡通插画两个人像、广西地图
def warm_grade(src_path, out_path, desat=0.42, gain=(1.02, 1.02, 0.97)):
    im = Image.open(src_path).convert("RGB")
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * gain[0])))
    g = g.point(lambda v: min(255, int(v * gain[1])))
    b = b.point(lambda v: min(255, int(v * gain[2])))
    out = Image.merge("RGB", (r, g, b))
    from PIL import ImageEnhance
    out = ImageEnhance.Color(out).enhance(1 - desat)
    out.save(out_path, "PNG", optimize=True)
    return out.size


warm_grade(os.path.join("media_src", "image22.png"),
           os.path.join("media_src", "_w_image22.png"))
print("warm graded image22")

tint_src = ("image5.png", "image6.png", "image14.png")
tint_out = {}
for n in tint_src:
    src = os.path.join("media_src", n)
    if not os.path.exists(src):
        print("skip", n)
        continue
    tmp_p = os.path.join("media_src", "_t_" + n)
    cnt = recolour_hue(open(src, "rb").read(), tmp_p)
    tint_out[n] = open(tmp_p, "rb").read()
    print("tinted", n, "pixels", cnt)

# 听诊器照片换成工程师工作照（直接顶掉原素材的字节）
if os.path.exists(os.path.join("media_src", "image15.jpeg")):
    warm_grade(os.path.join("media_src", "image15.jpeg"),
               os.path.join("media_src", "_w_image15.png"), desat=0.55,
               gain=(1.0, 1.03, 1.0))
    tint_out["image29.jpeg"] = open(os.path.join("media_src", "_w_image15.png"), "rb").read()
    print("replaced image29.jpeg -> warm image15")
if os.path.exists(os.path.join("media_src", "_w_image22.png")):
    tint_out["image22.png"] = open(os.path.join("media_src", "_w_image22.png"), "rb").read()

zin = zipfile.ZipFile(DECK, "r")
zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
n_bg = n_tint = n_xml = 0
for item in zin.infolist():
    fn = item.filename
    data = zin.read(fn)
    base = os.path.basename(fn)
    if fn.startswith("ppt/media/") and base in bg_bytes:
        data = bg_bytes[base]
        n_bg += 1
    elif fn.startswith("ppt/media/") and base in tint_out:
        data = tint_out[base]
        n_tint += 1
    elif fn.startswith("ppt/") and fn.endswith(".xml"):
        try:
            txt = data.decode("utf-8")
            new = remap_xml(txt)
            if new != txt:
                data = new.encode("utf-8")
                n_xml += 1
        except UnicodeDecodeError:
            pass
    zout.writestr(item, data)
zout.close()
zin.close()
shutil.move(TMP, DECK)
print(f"backgrounds={n_bg} tinted={n_tint} xml={n_xml} colors={changed}")


# ---------------------------------------------------------------- 文字配色
def walk(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from walk(sh.shapes)
        else:
            yield sh


def paint(shape, index, rgb, size=None):
    p = shape.text_frame.paragraphs[index]
    for r in p.runs:
        r.font.color.rgb = rgb
        if size:
            r.font.size = size


prs = Presentation(DECK)

for idx in (1, 22):
    s = prs.slides[idx - 1]
    for name, col in (("标题 1", WHITE), ("副标题 2", SAND),
                      ("文本占位符 4", MUTED), ("文本占位符 3", MUTED)):
        for sh in s.shapes:
            if sh.name == name and sh.has_text_frame:
                for i in range(len(sh.text_frame.paragraphs)):
                    paint(sh, i, col)

# 目录页“目录”二字在墨绿方块上，改白
for sh in prs.slides[1].shapes:
    if sh.name == "标题 1" and sh.has_text_frame:
        for i in range(len(sh.text_frame.paragraphs)):
            paint(sh, i, WHITE)

# 章节页：编号改成金色，删掉旧的描边框
for idx in (3, 7, 10, 16, 20):
    s = prs.slides[idx - 1]
    drop = []
    for sh in s.shapes:
        if sh.name in ("文本框 22", "文本框 5") and sh.has_text_frame \
                and len(sh.text_frame.paragraphs) >= 2:
            paint(sh, 0, AMBER)
            paint(sh, 1, WHITE)
        elif sh.name == "任意多边形: 形状 33":
            sh.line.color.rgb = AMBER
            sh.line.width = Emu(28575)
        elif sh.name == "矩形 48":
            drop.append(sh)
    for sh in drop:
        el = sh._element
        el.getparent().remove(el)

# 第 21 页两条竖排标题压在绿色飘带上，需要白字
for sh in prs.slides[20].shapes:
    if sh.name in ("文本框 153", "文本框 154") and sh.has_text_frame:
        for i in range(len(sh.text_frame.paragraphs)):
            paint(sh, i, WHITE)

prs.save(DECK)
print("text recoloured")
