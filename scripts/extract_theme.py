#!/usr/bin/env python
"""从截图提取配色方案:明暗主题、背景色、强调色、圆角风格。
用法: python extract_theme.py <image_path>
输出: JSON 到 stdout
"""
import sys, os, json, colorsys
from collections import Counter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from color_system import build_palette


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def hexc(c):
    return "#%02X%02X%02X" % (c[0], c[1], c[2])


def analyze(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    small = img.resize((160, max(1, int(160 * h / w))))
    px = list(small.getdata())
    n = len(px)

    avg_lum = sum(luminance(p) for p in px) / n
    theme = "light" if avg_lum > 150 else "dark"

    def quant(c):
        return (c[0] // 24 * 24, c[1] // 24 * 24, c[2] // 24 * 24)

    cnt = Counter(quant(p) for p in px)
    bg = cnt.most_common(1)[0][0]

    accent = None
    best_score = -1
    for c, freq in cnt.most_common(60):
        r, g, b = [x / 255 for x in c]
        hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
        if ss > 0.3 and vv > 0.35:
            score = ss * (freq ** 0.5)
            if score > best_score:
                best_score = score
                accent = c

    if accent is None:
        accent = (90, 108, 224) if theme == "light" else (120, 170, 255)

    edge_thin = detect_corner_style(img)
    radius_style = "sharp" if edge_thin else "soft"

    if theme == "light":
        page_bg = lighten(bg, 0.55) if is_grayish(bg) else "#FAF8F3"
        card_bg = "#FFFFFF"
        text_main = "#2B2A28"
        text_sub = "#6C675F"
    else:
        page_bg = darken(bg, 0.4) if not is_grayish(bg) else "#16181D"
        card_bg = "#22252B"
        text_main = "#F2F1EE"
        text_sub = "#A8A49C"

    # 交给专业色彩系统推导完整 palette（主色/辅色/互补强调/6 功能色/中性）
    full = build_palette(hexc(accent), theme, hexc(bg))
    return {
        "size": [w, h],
        "ratio": round(w / h, 3),
        "avg_lum": round(avg_lum, 1),
        "theme": theme,
        "bg": hexc(bg),
        "accent": full["accent"],
        "mood": full["mood"],
        "temperature": full["temperature"],
        "radius_style": radius_style,
        "palette": full["palette"],
    }


def is_grayish(c):
    return max(c) - min(c) < 24


def lighten(c, f):
    return hexc(tuple(min(255, int(x + (255 - x) * f)) for x in c))


def darken(c, f):
    return hexc(tuple(max(0, int(x * (1 - f))) for x in c))


def detect_corner_style(img):
    w, h = img.size
    corners = [(6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7)]
    center = img.getpixel((w // 2, h // 2))
    diffs = 0
    for cx, cy in corners:
        p = img.getpixel((cx, cy))
        if sum(abs(a - b) for a, b in zip(p, center)) > 60:
            diffs += 1
    return diffs >= 3


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: extract_theme.py <image_path>"}))
        sys.exit(1)
    print(json.dumps(analyze(sys.argv[1]), ensure_ascii=False, indent=2))
