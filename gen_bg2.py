# -*- coding: utf-8 -*-
"""第二份 PPT 的背景：石墨 + 琥珀，工业图纸风。
和第一份（深藏青 + 亮青）完全不同的一套视觉。"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1920, 1080
OUT = "media_bg2"
os.makedirs(OUT, exist_ok=True)

GRAPHITE_A = (24, 20, 16)
GRAPHITE_B = (43, 35, 26)
PAPER_A = (252, 249, 244)
PAPER_B = (245, 239, 230)
AMBER = (224, 138, 60)
AMBER_DEEP = (196, 107, 23)
CREAM = (250, 243, 231)


def gradient(c1, c2, angle="v"):
    h, w = H, W
    if angle == "v":
        t = np.linspace(0, 1, h)[:, None]
    else:
        xx = np.linspace(0, 1, w)[None, :]
        yy = np.linspace(0, 1, h)[:, None]
        t = np.clip(xx * 0.6 + yy * 0.4, 0, 1)
    arr = np.zeros((h, w, 3), float)
    for i in range(3):
        arr[:, :, i] = c1[i] + (c2[i] - c1[i]) * t
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def radial(center, radius, color, max_alpha):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * max_alpha
    arr = np.zeros((H, W, 4), np.uint8)
    for i in range(3):
        arr[..., i] = color[i]
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_grid(d, step, color, w=1):
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=color, width=w)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=color, width=w)


def dots(d, x0, x1, y0, y1, step, color):
    for gx in range(x0, x1, step):
        for gy in range(y0, y1, step):
            d.ellipse([gx, gy, gx + 3, gy + 3], fill=color)


def gear(d, cx, cy, r, color, teeth=18, width=3):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55],
              outline=color, width=width)
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        x1, y1 = cx + r * math.cos(a), cy + r * math.sin(a)
        x2, y2 = cx + (r + 16) * math.cos(a), cy + (r + 16) * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=color, width=width)


# ---------------------------------------------------------------- 内容页
def content_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((1520, 60), 900, (255, 255, 255), 190))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 20, W - 10, 20, H - 10, 40, (120, 96, 66, 22))
    # 角标
    L, T, R, B = 53, 136, 1868, 1053
    for (x, y, dx, dy) in [(70, 70, 1, 1), (W - 70, 70, -1, 1),
                           (70, H - 60, 1, -1), (W - 70, H - 60, -1, -1)]:
        d.line([(x, y), (x + 26 * dx, y)], fill=(196, 107, 23, 110), width=3)
        d.line([(x, y), (x, y + 26 * dy)], fill=(196, 107, 23, 110), width=3)
    # 右下角细弧
    for rr in (300, 380):
        d.arc([1830 - rr, 1010 - rr, 1830 + rr, 1010 + rr], 180, 275,
              fill=(196, 107, 23, 45), width=2)
    img = Image.alpha_composite(img, lay)

    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    for i in range(20, 0, -1):
        cd.rounded_rectangle([L - i * 0.6, T + 5 - i * 0.6, R + i * 0.6, B + 8 + i * 0.6],
                             radius=28, outline=(60, 44, 26, 4), width=1)
    cd.rounded_rectangle([L, T, R, B], radius=26, fill=(255, 255, 255, 255))
    cd.rounded_rectangle([L, T, R, B], radius=26, outline=(224, 138, 60, 255), width=2)
    img = Image.alpha_composite(img, card)
    return img.convert("RGB")


# ---------------------------------------------------------------- 目录页
def toc_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((280, 470), 900, (255, 255, 255), 160))

    cx, cy, r = 372, 452, 232
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 940, W - 20, 60, H - 60, 42, (120, 96, 66, 20))
    for rr in (r + 60, r + 116):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 330,
              fill=(196, 107, 23, 60), width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(233, 168, 108, 255))
    for rr, a in ((150, 110), (178, 70)):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 275,
              fill=(255, 255, 255, a), width=3)
    # 工业线稿：传送带
    y = 900
    d.line([(0, y), (W, y)], fill=(196, 107, 23, 55), width=3)
    d.line([(0, y + 46), (W, y + 46)], fill=(196, 107, 23, 45), width=2)
    for x in range(60, W, 150):
        d.rectangle([x, y + 10, x + 54, y + 36], outline=(196, 107, 23, 70), width=2)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 章节页
def section_bg():
    img = gradient(GRAPHITE_A, GRAPHITE_B, angle="d")
    img.alpha_composite(radial((120, 600), 950, (224, 138, 60), 62))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    draw_grid(d, 54, (255, 255, 255, 7))
    gear(d, 210, 470, 168, (224, 138, 60, 120), teeth=20, width=3)
    for i, a in enumerate((60, 42, 28)):
        d.line([(-40, 980 - i * 24), (700, 140 - i * 24)], fill=(224, 138, 60, a), width=2)
    d.line([(0, 860), (250, 860), (250, 700), (430, 700)], fill=(224, 138, 60, 110), width=3)
    for (x, y) in [(430, 700), (0, 860)]:
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(224, 138, 60, 150))
    img = Image.alpha_composite(img, lay)

    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([520, 196, 1920, 884], radius=26, fill=CREAM + (255,))
    img = Image.alpha_composite(img, panel)

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([520, 196, 548, 884], radius=9, fill=AMBER_DEEP + (255,))
    # 面板右侧淡纹
    for rr in (300, 228, 156):
        d.arc([1700 - rr, 800 - rr, 1700 + rr, 800 + rr], 180, 330,
              fill=(196, 107, 23, 55), width=3)
    dots(d, 600, 900, 760, 880, 40, (120, 96, 66, 40))
    d.rounded_rectangle([520, 196, 1918, 884], radius=26, outline=(196, 107, 23, 90), width=2)
    for (cx0, cy0, dx, dy) in [(562, 234, 1, 1), (1876, 234, -1, 1)]:
        d.line([(cx0, cy0), (cx0 + 22 * dx, cy0)], fill=(196, 107, 23, 170), width=3)
        d.line([(cx0, cy0), (cx0, cy0 + 22 * dy)], fill=(196, 107, 23, 170), width=3)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 封面
def cover_bg():
    img = gradient(GRAPHITE_A, GRAPHITE_B, angle="d")
    img.alpha_composite(radial((250, 560), 980, (224, 138, 60), 76))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    draw_grid(d, 54, (255, 255, 255, 7))
    gear(d, 300, 520, 196, (224, 138, 60, 105), teeth=22, width=3)
    d.arc([300 - 300, 520 - 300, 300 + 300, 520 + 300], 140, 400,
          fill=(224, 138, 60, 60), width=2)
    # 传送带 + 工件
    d.line([(0, 880), (900, 880)], fill=(224, 138, 60, 90), width=3)
    d.line([(0, 916), (900, 916)], fill=(224, 138, 60, 60), width=2)
    for x in (90, 260, 430, 600, 770):
        d.rectangle([x, 840, x + 52, 872], outline=(224, 138, 60, 120), width=3)
    # 电路折线
    d.line([(0, 160), (240, 160), (240, 268), (410, 268)], fill=(224, 138, 60, 130), width=4)
    for p in [(0, 160), (410, 268)]:
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(224, 138, 60, 170))
    # 右侧刻度
    for i in range(9):
        d.line([(1836, 120 + i * 26), (1872, 120 + i * 26)], fill=(255, 255, 255, 26), width=2)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


if __name__ == "__main__":
    for name, fn in {"image1.png": content_bg, "image2.png": cover_bg,
                     "image3.png": toc_bg, "image4.png": section_bg}.items():
        im = fn()
        im.save(os.path.join(OUT, name), "PNG", optimize=True)
        print("saved", name, im.size)
