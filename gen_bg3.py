# -*- coding: utf-8 -*-
"""第三份 PPT 的背景：米白纸 + 墨绿 + 金线（学术 / 备考气质）。
与第一份（深藏青+亮青）、第二份（石墨+琥珀）都不同。"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw

W, H = 1920, 1080
OUT = "media_bg3"
os.makedirs(OUT, exist_ok=True)

GREEN_A = (12, 42, 36)
GREEN_B = (22, 74, 62)
PAPER_A = (252, 251, 245)
PAPER_B = (238, 244, 237)
GOLD = (201, 162, 39)
GOLD_LIGHT = (228, 205, 138)
GREEN = (15, 59, 51)


def gradient(c1, c2, angle="v"):
    if angle == "v":
        t = np.linspace(0, 1, H)[:, None]
    else:
        xx = np.linspace(0, 1, W)[None, :]
        yy = np.linspace(0, 1, H)[:, None]
        t = np.clip(xx * 0.55 + yy * 0.45, 0, 1)
    arr = np.zeros((H, W, 3), float)
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


def grid(d, step, color, w=1):
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=color, width=w)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=color, width=w)


def dots(d, x0, x1, y0, y1, step, color, r=1):
    for gx in range(x0, x1, step):
        for gy in range(y0, y1, step):
            d.ellipse([gx, gy, gx + 2 * r, gy + 2 * r], fill=color)


def stairs(d, x0, y0, steps, w, h, color, alpha=110):
    """上升台阶线稿，寓意一步一步往上考。"""
    x, y = x0, y0
    pts = [(x, y)]
    for i in range(steps):
        x += w
        pts.append((x, y))
        y -= h
        pts.append((x, y))
    d.line(pts, fill=color + (alpha,), width=3)
    d.line([(x0, y0 + 4), (x0 + steps * w, y0 + 4)], fill=color + (alpha // 3,), width=2)
    for i in range(steps + 1):
        cx = x0 + i * w
        cy = y0 - i * h
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color + (min(255, alpha + 60),))


# ---------------------------------------------------------------- 内容页
def content_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((1560, 40), 900, (255, 255, 255), 180))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 18, W - 10, 18, H - 10, 44, (15, 59, 51, 26))
    L, T, R, B = 53, 136, 1868, 1053
    for (x, y, dx, dy) in [(70, 72, 1, 1), (W - 70, 72, -1, 1),
                           (70, H - 62, 1, -1), (W - 70, H - 62, -1, -1)]:
        d.line([(x, y), (x + 24 * dx, y)], fill=(201, 162, 39, 130), width=3)
        d.line([(x, y), (x, y + 24 * dy)], fill=(201, 162, 39, 130), width=3)
    for rr in (280, 350):
        d.arc([1860 - rr, 1030 - rr, 1860 + rr, 1030 + rr], 185, 270,
              fill=(15, 59, 51, 40), width=2)
    img = Image.alpha_composite(img, lay)

    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    for i in range(20, 0, -1):
        cd.rounded_rectangle([L - i * 0.6, T + 5 - i * 0.6, R + i * 0.6, B + 8 + i * 0.6],
                             radius=24, outline=(40, 55, 45, 4), width=1)
    cd.rounded_rectangle([L, T, R, B], radius=24, fill=(255, 255, 255, 255))
    cd.rounded_rectangle([L, T, R, B], radius=24, outline=(201, 162, 39, 235), width=2)
    img = Image.alpha_composite(img, card)
    return img.convert("RGB")


# ---------------------------------------------------------------- 目录页
def toc_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((300, 470), 900, (255, 255, 255), 150))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 1000, W - 20, 60, H - 60, 44, (15, 59, 51, 22))
    # 墨绿圆角方块托住"目录"
    d.rounded_rectangle([150, 230, 594, 674], radius=40, fill=GREEN + (255,))
    d.rounded_rectangle([150, 230, 594, 674], radius=40, outline=GOLD + (150,), width=3)
    # 方块外的金色细弧
    for rr in (300, 372):
        d.arc([372 - rr, 452 - rr, 372 + rr, 452 + rr], 150, 330,
              fill=(201, 162, 39, 80), width=2)
    # 右下台阶线稿
    stairs(d, 1080, 930, 4, 170, 62, GOLD, 120)
    # 左下细线
    d.line([(0, 1010), (700, 1010)], fill=(15, 59, 51, 45), width=2)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 章节页
def section_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((150, 560), 900, (255, 255, 255), 140))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 30, 480, 60, H - 60, 44, (15, 59, 51, 26))
    for rr in (150, 210):
        d.arc([120 - rr, 540 - rr, 120 + rr, 540 + rr], 250, 60,
              fill=(201, 162, 39, 90), width=3)
    stairs(d, 70, 900, 3, 110, 52, GREEN, 90)
    d.line([(0, 140), (420, 140)], fill=(201, 162, 39, 120), width=3)
    img = Image.alpha_composite(img, lay)

    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([520, 196, 1920, 884], radius=24, fill=GREEN + (255,))
    img = Image.alpha_composite(img, panel)

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([520, 196, 546, 884], radius=9, fill=GOLD + (255,))
    for rr in (300, 228, 156):
        d.arc([1720 - rr, 800 - rr, 1720 + rr, 800 + rr], 180, 330,
              fill=(201, 162, 39, 70), width=3)
    dots(d, 600, 900, 760, 880, 40, (255, 255, 255, 26))
    d.rounded_rectangle([520, 196, 1918, 884], radius=24, outline=(201, 162, 39, 90), width=2)
    for (cx0, cy0, dx, dy) in [(566, 236, 1, 1), (1874, 236, -1, 1)]:
        d.line([(cx0, cy0), (cx0 + 22 * dx, cy0)], fill=(201, 162, 39, 180), width=3)
        d.line([(cx0, cy0), (cx0, cy0 + 22 * dy)], fill=(201, 162, 39, 180), width=3)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 封面
def cover_bg():
    img = gradient(GREEN_A, GREEN_B, angle="d")
    img.alpha_composite(radial((260, 540), 950, (60, 160, 130), 70))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    grid(d, 60, (255, 255, 255, 7))
    # 左侧上升台阶
    stairs(d, 120, 900, 4, 150, 72, GOLD, 150)
    # 同心弧
    for rr in (240, 330, 420):
        d.arc([250 - rr, 470 - rr, 250 + rr, 470 + rr], 150, 385,
              fill=(201, 162, 39, 55), width=3)
    # 坐标轴
    d.line([(60, 980), (820, 980)], fill=(255, 255, 255, 60), width=2)
    d.line([(60, 980), (60, 640)], fill=(255, 255, 255, 45), width=2)
    # 右侧刻度
    for i in range(9):
        d.line([(1836, 120 + i * 26), (1872, 120 + i * 26)], fill=(255, 255, 255, 30), width=2)
    # 金色斜线
    for i, a in enumerate((34, 22, 12)):
        d.line([(1150 + i * 26, 1080), (1920, 1080 - (620 - i * 26))],
               fill=(201, 162, 39, a), width=2)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


if __name__ == "__main__":
    for name, fn in {"image1.png": content_bg, "image2.png": cover_bg,
                     "image3.png": toc_bg, "image4.png": section_bg}.items():
        im = fn()
        im.save(os.path.join(OUT, name), "PNG", optimize=True)
        print("saved", name, im.size)
