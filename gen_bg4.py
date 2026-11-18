# -*- coding: utf-8 -*-
"""第四份 PPT 的背景：暖灰纸 + 深藏青 + 铁路红（全篇浅色，极简）。
与前三分（深藏青、石墨、墨绿）都不同。"""
import os
import numpy as np
from PIL import Image, ImageDraw

W, H = 1920, 1080
OUT = "media_bg4"
os.makedirs(OUT, exist_ok=True)

PAPER_A = (249, 247, 244)
PAPER_B = (238, 234, 228)
INK = (27, 36, 48)
RED = (192, 80, 63)
RED_DEEP = (166, 62, 48)
LINE = (214, 206, 196)


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


def dots(d, x0, x1, y0, y1, step, color, r=1):
    for gx in range(x0, x1, step):
        for gy in range(y0, y1, step):
            d.ellipse([gx, gy, gx + 2 * r, gy + 2 * r], fill=color)


def rails(d, x0, y0, length, gap, sleeper, color, width=3, alpha=110):
    """两条平行轨 + 枕木，向右下略微延伸。"""
    d.line([(x0, y0), (x0 + length, y0 - 40)], fill=color + (alpha,), width=width)
    d.line([(x0, y0 + gap), (x0 + length, y0 - 40 + gap)], fill=color + (alpha,), width=width)
    n = int(length / sleeper)
    for i in range(n + 1):
        x = x0 + i * sleeper
        y = y0 - 40 * (i / n)
        d.line([(x, y - 6), (x, y + gap + 6)], fill=color + (alpha // 2,), width=2)


# ---------------------------------------------------------------- 内容页
def content_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((1600, 40), 900, (255, 255, 255), 200))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 18, W - 10, 18, H - 10, 46, (60, 50, 40, 18))
    L, T, R, B = 53, 136, 1868, 1053
    for (x, y, dx, dy) in [(70, 74, 1, 1), (W - 70, 74, -1, 1),
                           (70, H - 64, 1, -1), (W - 70, H - 64, -1, -1)]:
        d.line([(x, y), (x + 26 * dx, y)], fill=RED + (170,), width=3)
        d.line([(x, y), (x, y + 26 * dy)], fill=RED + (170,), width=3)
    # 右下细轨
    rails(d, 1560, 1010, 320, 26, 48, RED, 2, 70)
    img = Image.alpha_composite(img, lay)

    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    for i in range(22, 0, -1):
        cd.rounded_rectangle([L - i * 0.6, T + 6 - i * 0.6, R + i * 0.6, B + 9 + i * 0.6],
                             radius=10, outline=(60, 50, 40, 4), width=1)
    cd.rounded_rectangle([L, T, R, B], radius=10, fill=(255, 255, 255, 255))
    cd.rounded_rectangle([L, T, R, B], radius=10, outline=(214, 206, 196, 255), width=2)
    # 左上角红色小色块
    cd.rectangle([L, T, L + 120, T + 8], fill=RED + (255,))
    img = Image.alpha_composite(img, card)
    return img.convert("RGB")


# ---------------------------------------------------------------- 目录页
def toc_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((320, 470), 900, (255, 255, 255), 160))

    cx, cy, r = 372, 452, 232
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 980, W - 20, 60, H - 60, 46, (60, 50, 40, 16))
    for rr in (r + 54, r + 104):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 330, fill=RED + (90,), width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED + (255,))
    for rr, a in ((150, 100), (178, 60)):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 275,
              fill=(255, 255, 255, a), width=3)
    rails(d, 1020, 900, 800, 34, 62, INK, 3, 90)
    d.line([(0, 1010), (700, 1010)], fill=(60, 50, 40, 40), width=2)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 章节页
def section_bg():
    img = gradient(PAPER_A, PAPER_B)
    img.alpha_composite(radial((160, 560), 900, (255, 255, 255), 150))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 30, 470, 60, H - 60, 46, (60, 50, 40, 18))
    rails(d, 40, 880, 420, 30, 60, INK, 3, 110)
    d.rectangle([0, 0, 12, H], fill=RED + (255,))
    d.line([(60, 150), (430, 150)], fill=RED + (120,), width=3)
    img = Image.alpha_composite(img, lay)

    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for i in range(18, 0, -1):
        pd.rounded_rectangle([520 - i * 0.8, 196 - i * 0.8, 1920, 884 + i * 0.8],
                             radius=12, outline=(60, 50, 40, 3), width=1)
    pd.rounded_rectangle([520, 196, 1920, 884], radius=10, fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, panel)

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([520, 196, 556, 884], radius=6, fill=RED + (255,))
    d.rounded_rectangle([520, 196, 1918, 884], radius=10, outline=(214, 206, 196, 255), width=2)
    d.line([(600, 240), (600, 300)], fill=RED + (150,), width=3)
    d.line([(600, 270), (660, 270)], fill=RED + (110,), width=3)
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


# ---------------------------------------------------------------- 封面
def cover_bg():
    img = gradient(PAPER_A, PAPER_B, angle="d")
    img.alpha_composite(radial((300, 520), 950, (255, 255, 255), 190))

    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    dots(d, 20, 760, 20, H - 20, 48, (60, 50, 40, 16))
    d.rectangle([0, 0, 14, H], fill=RED + (255,))
    # 左侧透视线路：从画面左下角向远处收
    vx, vy = 900, 520
    d.line([(-40, 1080), (vx, vy)], fill=INK + (130,), width=4)
    d.line([(120, 1080), (vx + 90, vy + 30)], fill=INK + (130,), width=4)
    for i in range(1, 11):
        t = (i / 11.0) ** 1.5
        x1 = -40 + (vx + 40) * t
        y1 = 1080 + (vy - 1080) * t
        x2 = 120 + (vx + 90 - 120) * t
        y2 = 1080 + (vy + 30 - 1080) * t
        d.line([(x1, y1), (x2, y2)], fill=INK + (55,), width=2)
    # 标题上方的红色短线
    d.rectangle([790, 150, 1090, 158], fill=RED + (255,))
    img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


if __name__ == "__main__":
    for name, fn in {"image1.png": content_bg, "image2.png": cover_bg,
                     "image3.png": toc_bg, "image4.png": section_bg}.items():
        im = fn()
        im.save(os.path.join(OUT, name), "PNG", optimize=True)
        print("saved", name, im.size)
