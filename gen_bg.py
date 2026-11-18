# -*- coding: utf-8 -*-
"""生成 4 张新背景：内容页 / 目录 / 章节分隔 / 封面。
风格：深蓝技术底 + 电路线条，去掉模板原有的卡通人物与云朵。"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
OUT = "media_bg"
os.makedirs(OUT, exist_ok=True)

NAVY_A = (7, 20, 34)
NAVY_B = (13, 40, 64)
LIGHT_A = (247, 251, 255)
LIGHT_B = (228, 240, 251)
CYAN = (25, 185, 216)
CYAN_LT = (94, 205, 238)


# ---------------------------------------------------------------- utilities
def gradient(c1, c2, size=(W, H), angle="v"):
    w, h = size
    if angle == "v":
        t = np.linspace(0, 1, h)[:, None]
        arr = np.zeros((h, w, 3), float)
        for i in range(3):
            arr[:, :, i] = c1[i] + (c2[i] - c1[i]) * t
    else:  # diagonal
        xx = np.linspace(0, 1, w)[None, :]
        yy = np.linspace(0, 1, h)[:, None]
        t = np.clip((xx * 0.7 + yy * 0.3), 0, 1)
        arr = np.zeros((h, w, 3), float)
        for i in range(3):
            arr[:, :, i] = c1[i] + (c2[i] - c1[i]) * t
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def overlay(base, layer_fn, blur=0):
    """layer_fn 在一张 RGBA 透明图上作画，再叠到 base 上。"""
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer_fn(ImageDraw.Draw(lay))
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(lay) if base.mode == "RGBA" else base.paste(
        Image.alpha_composite(base.convert("RGBA"), lay).convert("RGB"), (0, 0))
    return base


def radial(size, center, radius, color, max_alpha):
    """独立 alpha 的径向柔光，避免高斯模糊把透明区颜色带进来。"""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * max_alpha
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_grid(d, step=48, color=(255, 255, 255, 8), w=1, size=(W, H)):
    for x in range(0, size[0], step):
        d.line([(x, 0), (x, size[1])], fill=color, width=w)
    for y in range(0, size[1], step):
        d.line([(0, y), (size[0], y)], fill=color, width=w)


def circuit(d, pts, color=(25, 185, 216, 90), w=3, node=6):
    d.line(pts, fill=color, width=w, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - node, p[1] - node, p[0] + node, p[1] + node], fill=color)


def rounded(img, radius=22, inset=0, fill=(255, 255, 255, 255)):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([inset, inset, img.size[0] - inset, img.size[1] - inset],
                        radius=radius, fill=fill)
    return lay


# ---------------------------------------------------------------- 1 内容页
def content_bg():
    img = gradient(LIGHT_A, LIGHT_B).convert("RGBA")

    # 右上柔光
    img.alpha_composite(radial((W, H), (1760, 120), 900, (255, 255, 255), 200))

    def art(d):
        draw_grid(d, 44, (25, 42, 69, 7))
        draw_grid(d, 220, (25, 42, 69, 11))
        # 左下大圆弧
        for r in (430, 540, 650):
            d.arc([80 - r, 980 - r, 80 + r, 980 + r], 200, 350,
                  fill=(25, 185, 216, 34), width=3)
        # 右上细弧
        for r in (300, 380):
            d.arc([1830 - r, 120 - r, 1830 + r, 120 + r], 100, 250,
                  fill=(25, 185, 216, 30), width=3)
        # 电路走线（右上角、左下角）
        circuit(d, [(1560, 0), (1560, 96), (1690, 96), (1690, 210)], (25, 185, 216, 60), 3, 5)
        circuit(d, [(1920, 300), (1810, 300), (1810, 190)], (25, 185, 216, 45), 3, 5)
        circuit(d, [(0, 820), (120, 820), (120, 930)], (25, 185, 216, 45), 3, 5)
        circuit(d, [(300, 1080), (300, 1000), (430, 1000)], (25, 185, 216, 40), 3, 5)
        # 四角定位点
        for (x, y) in [(24, 24), (W - 24, 24), (24, H - 24), (W - 24, H - 24)]:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(25, 185, 216, 90))
    img = overlay(img, art)

    # 白色内容卡片（原模板的卡片就在这张底图里）
    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    L, T, R, B, RAD = 53, 136, 1868, 1053, 26
    for i in range(22, 0, -1):
        cd.rounded_rectangle([L - i * 0.6, T + 6 - i * 0.6, R + i * 0.6, B + 8 + i * 0.6],
                             radius=RAD + 6, outline=(10, 32, 54, 4), width=1)
    cd.rounded_rectangle([L, T, R, B], radius=RAD, fill=(255, 255, 255, 255))
    cd.rounded_rectangle([L, T, R, B], radius=RAD, outline=(23, 185, 218, 255), width=2)
    img = Image.alpha_composite(img, card)

    return img.convert("RGB")


# ---------------------------------------------------------------- 2 目录页
def toc_bg():
    img = gradient(LIGHT_A, LIGHT_B).convert("RGBA")

    img.alpha_composite(radial((W, H), (300, 480), 900, (255, 255, 255), 170))

    cx, cy, r = 372, 452, 232

    def art(d):
        draw_grid(d, 44, (25, 42, 69, 6))
        # 圆外同心弧
        for rr in (r + 62, r + 118):
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 330,
                  fill=(25, 185, 216, 42), width=3)
        # 主圆
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CYAN_LT + (255,))
        # 圆内装饰弧（偏左上，避开"目录"文字）
        for rr, a in ((150, 90), (178, 55)):
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 275,
                  fill=(255, 255, 255, a), width=3)
        # 电路
        circuit(d, [(0, 900), (250, 900), (250, 760), (420, 760)], (25, 185, 216, 55), 3, 5)
        circuit(d, [(1500, 1080), (1500, 900), (1320, 900)], (25, 185, 216, 45), 3, 5)
        circuit(d, [(1180, 0), (1180, 120), (1330, 120), (1330, 250)], (25, 185, 216, 50), 3, 5)
        # 右侧淡点阵
        for gx in range(1360, W, 74):
            for gy in range(110, H - 90, 74):
                d.ellipse([gx, gy, gx + 3, gy + 3], fill=(25, 42, 69, 24))
    img = overlay(img, art)
    return img.convert("RGB")


# ---------------------------------------------------------------- 3 章节页
def section_bg():
    img = gradient(NAVY_A, NAVY_B).convert("RGBA")

    def art(d):
        draw_grid(d, 46, (255, 255, 255, 7))
        # 左侧同心圆（叶轮/定子意象）
        for rr in (150, 235, 330, 430):
            d.arc([-60 - rr, 560 - rr, -60 + rr, 560 + rr], 250, 60,
                  fill=(25, 185, 216, 60), width=3)
        # 左侧电路
        circuit(d, [(0, 190), (200, 190), (200, 320), (360, 320)], (25, 185, 216, 110), 3, 6)
        circuit(d, [(0, 900), (170, 900), (170, 790), (330, 790)], (25, 185, 216, 90), 3, 6)
        circuit(d, [(90, 1080), (90, 960)], (25, 185, 216, 70), 3, 5)
        # 光带
        for i, a in enumerate((26, 18, 12)):
            d.line([(-40, 1010 - i * 26), (760, 130 - i * 26)], fill=(25, 185, 216, a), width=2)
    img = overlay(img, art)

    img.alpha_composite(radial((W, H), (60, 620), 900, (25, 185, 216), 60))

    # 深青面板（承接原来的大色块，改用深色以承载白色文字）
    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([520, 196, 1920, 884], radius=26, fill=(14, 52, 74, 255))
    img = Image.alpha_composite(img, panel)

    # 面板内渐变与细节
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(lay)
    for i in range(884 - 196):
        t = i / (884 - 196)
        a = int(16 * (1 - t))
        d2.line([(540, 196 + i), (1900, 196 + i)], fill=(25, 185, 216, a))
    # 左侧亮青竖条
    d2.rounded_rectangle([520, 196, 548, 884], radius=9, fill=CYAN + (255,))
    # 右下同心弧
    gcx, gcy = 1700, 800
    for rr in (300, 228, 156):
        d2.arc([gcx - rr, gcy - rr, gcx + rr, gcy + rr], 180, 330,
               fill=(25, 185, 216, 55), width=3)
    # 点阵
    for gx in range(600, 900, 40):
        for gy in range(760, 880, 40):
            d2.ellipse([gx, gy, gx + 3, gy + 3], fill=(255, 255, 255, 30))
    # 面板边框
    d2.rounded_rectangle([520, 196, 1918, 884], radius=26,
                         outline=(25, 185, 216, 70), width=2)
    # 四角标记
    for (cx0, cy0, dx, dy) in [(560, 232, 1, 1), (1878, 232, -1, 1)]:
        d2.line([(cx0, cy0), (cx0 + 22 * dx, cy0)], fill=(25, 185, 216, 160), width=3)
        d2.line([(cx0, cy0), (cx0, cy0 + 22 * dy)], fill=(25, 185, 216, 160), width=3)
    img = Image.alpha_composite(img, lay)

    return img.convert("RGB")


# ---------------------------------------------------------------- 4 封面
def cover_bg():
    img = gradient(NAVY_A, NAVY_B, angle="d").convert("RGBA")

    def art(d):
        draw_grid(d, 48, (255, 255, 255, 6))
        # 叶轮同心弧（左侧）
        for rr in (210, 300, 395, 500, 615):
            d.arc([300 - rr, 540 - rr, 300 + rr, 540 + rr], 152, 388,
                  fill=(25, 185, 216, 58), width=3)
        # 放射线
        for i in range(12):
            ang = math.radians(-40 + i * 12)
            d.line([(300, 540), (300 + 700 * math.cos(ang), 540 + 700 * math.sin(ang))],
                   fill=(25, 185, 216, 20), width=2)
        # 电路
        circuit(d, [(0, 150), (240, 150), (240, 268), (430, 268)], (25, 185, 216, 120), 4, 7)
        circuit(d, [(0, 950), (300, 950), (300, 830), (470, 830)], (25, 185, 216, 100), 4, 7)
        circuit(d, [(620, 1080), (620, 900), (760, 900)], (25, 185, 216, 70), 3, 6)
        # 右下斜线
        for i, a in enumerate((30, 20, 12)):
            d.line([(1240 + i * 30, 1080), (1920, 1080 - (680 - i * 30))],
                   fill=(25, 185, 216, a), width=2)
        # 右侧刻度装饰
        for i in range(9):
            y = 120 + i * 26
            d.line([(1836, y), (1872, y)], fill=(255, 255, 255, 26), width=2)
    img = overlay(img, art)

    img.alpha_composite(radial((W, H), (140, 560), 980, (25, 185, 216), 78))
    return img.convert("RGB")


# ---------------------------------------------------------------- run
if __name__ == "__main__":
    jobs = {
        "image1.png": content_bg,
        "image2.png": cover_bg,
        "image3.png": toc_bg,
        "image4.png": section_bg,
    }
    for name, fn in jobs.items():
        im = fn()
        im.save(os.path.join(OUT, name), "PNG", optimize=True)
        print("saved", name, im.size)
