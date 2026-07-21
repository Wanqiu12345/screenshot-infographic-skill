#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""专业配色系统 (Color System)
根据「截图主品牌色 + 明暗主题」推导一整套和谐、有层次、能引导视线的教程图配色。

设计依据（详见 references/color_guide.md）：
1. 60-30-10 法则：60% 中性背景、30% 主色、10% 互补强调色（重点引导）。
2. 色轮和谐：功能色板采用「类比色阶」——以主色相为锚，在 ±60° 扇形内等距取色。
3. 无障碍对比：功能色固定到安全 S/L，保证白字可读。
4. 明暗自适应：深色主题下功能色更亮更饱和。

内部约定：所有 RGB 颜色统一用 0-1 浮点数，只在 `rgb_to_hex` / `rgba_str` 里转为 0-255。
用法:
  python color_system.py <accent_hex> [light|dark]
  python color_system.py <accent_hex> [light|dark] <bg_hex>
"""
import sys
import json
import colorsys

HERE = sys.path[0] if sys.path else "."


# ---------- 颜色转换（内部统一用 0-1）----------
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(c):
    c = tuple(clamp(x) for x in c)
    return "#%02X%02X%02X" % (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))


def rgb_to_hsl(r, g, b):
    """r,g,b ∈ [0,1] -> h,s,l ∈ [0,1]"""
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif mx == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        h /= 6.0
    return h, s, l


def hsl_to_rgb(h, s, l):
    """h,s,l ∈ [0,1] -> r,g,b ∈ [0,1]"""
    h = h % 1.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = l - c / 2.0
    if h < 1 / 6:
        r, g, b = c, x, 0.0
    elif h < 2 / 6:
        r, g, b = x, c, 0.0
    elif h < 3 / 6:
        r, g, b = 0.0, c, x
    elif h < 4 / 6:
        r, g, b = 0.0, x, c
    elif h < 5 / 6:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return (r + m, g + m, b + m)


def rgba_str(c, a):
    c = tuple(clamp(x) for x in c)
    return "rgba(%d,%d,%d,%.3f)" % (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255), a)


def hsl_hex(h, s, l):
    return rgb_to_hex(hsl_to_rgb(h, s, l))


def is_grayish(c):
    return max(c) - min(c) < (26 / 255.0)


# ---------- 色相区 -> 调性 ----------
def hue_mood(h):
    deg = int(h * 360) % 360
    if deg < 15 or deg >= 345:
        return "红", "warm"
    if deg < 45:
        return "橙", "warm"
    if deg < 70:
        return "黄", "warm"
    if deg < 160:
        return "绿", "cool"
    if deg < 200:
        return "青", "cool"
    if deg < 255:
        return "蓝", "cool"
    if deg < 290:
        return "紫", "cool"
    return "品红", "warm"


# ---------- 核心：构建完整 palette ----------
def build_palette(accent_hex, theme="light", bg_hex=None):
    ar, ag, ab = hex_to_rgb(accent_hex)
    h, s, l = rgb_to_hsl(ar, ag, ab)
    mood, temp = hue_mood(h)

    # 规范化主色到「可作为品牌主色」的安全区间
    if theme == "light":
        s = clamp(s, 0.45, 0.85)
        l = clamp(l, 0.40, 0.62)
    else:
        s = clamp(s, 0.55, 0.92)
        l = clamp(l, 0.55, 0.72)
    primary = hsl_to_rgb(h, s, l)
    primary_hex = rgb_to_hex(primary)

    # 中性色（背景 / 卡片 / 文字）—— 60% 基底
    if theme == "light":
        if bg_hex is None or is_grayish(hex_to_rgb(bg_hex)):
            page_bg = (0.98, 0.97, 0.95)  # #FAF8F3
        else:
            br, bg, bb = hex_to_rgb(bg_hex)
            page_bg = tuple(min(1.0, x + (1.0 - x) * 0.55) for x in (br, bg, bb))
        card_bg = (1.0, 1.0, 1.0)
        text_main = (0.169, 0.165, 0.157)  # #2B2A28
        text_sub = (0.424, 0.404, 0.373)  # #6C675F
    else:
        if bg_hex is None or not is_grayish(hex_to_rgb(bg_hex)):
            page_bg = (0.086, 0.094, 0.114)  # #16181D
        else:
            page_bg = tuple(max(0.0, x * 0.62) for x in hex_to_rgb(bg_hex))
        card_bg = (0.133, 0.145, 0.169)  # #22252B
        text_main = (0.949, 0.945, 0.933)  # #F2F1EE
        text_sub = (0.659, 0.643, 0.612)  # #A8A49C

    # 30% 主色系统
    accent_soft = rgba_str(primary, 0.12 if theme == "light" else 0.22)

    # 类比辅色（+28°）
    sec_h = (h + 28 / 360.0) % 1.0
    sec_l = l + 0.04 if theme == "light" else l
    secondary = hsl_to_rgb(sec_h, clamp(s, 0.4, 0.85), clamp(sec_l, 0, 1))
    secondary_hex = rgb_to_hex(secondary)
    secondary_soft = rgba_str(secondary, 0.14 if theme == "light" else 0.22)

    # 10% 互补强调色（+180°），重点引导用
    acc2_h = (h + 180 / 360.0) % 1.0
    acc2_s = clamp(s * 0.92, 0.45, 0.85)
    acc2_l = (l + 0.03) if theme == "light" else (l + 0.06)
    accent2 = hsl_to_rgb(acc2_h, acc2_s, clamp(acc2_l, 0, 1))
    accent2_hex = rgb_to_hex(accent2)
    accent2_soft = rgba_str(accent2, 0.12 if theme == "light" else 0.22)

    # 6 色功能色板（类比色阶，引导视线）
    # 以主色为锚，在 ±60° 内等距取 6 色，S/L 固定 -> 和谐且可区分
    offsets = [-58, -35, -12, 12, 35, 58]
    if theme == "light":
        f_s, f_l = 0.66, 0.50
    else:
        f_s, f_l = 0.75, 0.64
    feature, feature_soft = [], []
    for off in offsets:
        fh = (h + off / 360.0) % 1.0
        fc = hsl_to_rgb(fh, f_s, f_l)
        feature.append(rgb_to_hex(fc))
        feature_soft.append(rgba_str(fc, 0.14 if theme == "light" else 0.22))

    line = rgba_str(text_sub, 0.18 if theme == "light" else 0.26)

    palette = {
        "page_bg": rgb_to_hex(page_bg),
        "card_bg": rgb_to_hex(card_bg),
        "text_main": rgb_to_hex(text_main),
        "text_sub": rgb_to_hex(text_sub),
        "accent": primary_hex,
        "accent_soft": accent_soft,
        "secondary": secondary_hex,
        "secondary_soft": secondary_soft,
        "accent2": accent2_hex,
        "accent2_soft": accent2_soft,
        "feature": feature,
        "feature_soft": feature_soft,
        "line": line,
    }
    return {
        "theme": theme,
        "accent": primary_hex,
        "mood": mood,
        "temperature": temp,
        "palette": palette,
    }


# ---------- 纯文案模式：主题 / 命名预设 -> 配色 ----------
# 无截图时，由文案主题（category）或用户指定的命名预设（preset）决定主色。
CATEGORY_ACCENT = {
    "AI": "#2A8E9E", "科技": "#2A8E9E", "人工智能": "#2A8E9E", "AI/科技": "#2A8E9E",
    "财经": "#1E5BB8", "数据": "#1E5BB8", "金融": "#1E5BB8", "投资": "#1E5BB8",
    "美食": "#E8743B", "餐饮": "#E8743B", "烘焙": "#E8743B",
    "教育": "#4A9E6F", "学习": "#4A9E6F", "知识": "#5B7BC0",
    "健康": "#3FB89B", "医疗": "#3FB89B", "养生": "#3FB89B",
    "职场": "#355C9E", "商业": "#355C9E", "创业": "#7A5BC0", "营销": "#7A5BC0",
    "旅行": "#2E9E8F", "旅游": "#2E9E8F", "生活方式": "#C0804A", "情感": "#C25B8E",
    "游戏": "#9B5CFF", "数码": "#2A8E9E", "默认": "#2A8E9E",
}

# 命名主题预设（参考主流小红书配图工具，给用户更直观的风格选择）。
# 每项为 (accent, theme)；page_bg/card_bg 等中性色仍由 build_palette 推导。
THEME_PRESETS = {
    "cream":    ("#2A8E9E", "light"),   # 奶油风（AI/科技常见，浅暖底）
    "redbook":  ("#FB4E44", "light"),   # 红书红
    "obsidian": ("#5B6CFF", "dark"),    # 黑曜石（深色冷调）
    "cyber":    ("#9B5CFF", "dark"),    # 赛博朋克（深色紫）
    "minimal":  ("#222831", "light"),   # 极简高级（近黑主色）
    "forest":   ("#2E9E6F", "light"),   # 森绿
    "sunset":   ("#E8743B", "light"),   # 暖橙
    "ocean":    ("#1E5BB8", "light"),   # 商务蓝
}


def resolve_category(category):
    if not category:
        return CATEGORY_ACCENT["默认"]
    c = category.strip()
    if c in CATEGORY_ACCENT:
        return CATEGORY_ACCENT[c]
    for k, v in CATEGORY_ACCENT.items():
        if k != "默认" and k in c:
            return v
    return CATEGORY_ACCENT["默认"]


def build_palette_from_category(category, theme=None):
    accent = resolve_category(category)
    return build_palette(accent, theme or "light")


def build_palette_from_preset(preset_name, theme=None):
    if preset_name in THEME_PRESETS:
        accent, th = THEME_PRESETS[preset_name]
        return build_palette(accent, theme or th)
    return build_palette(CATEGORY_ACCENT["默认"], theme or "light")


def build_palette_for_text(category=None, preset=None, theme=None):
    """纯文案模式主入口：优先用命名预设，其次用主题分类，最后回退默认。"""
    if preset and preset in THEME_PRESETS:
        return build_palette_from_preset(preset, theme)
    if category:
        return build_palette_from_category(category, theme)
    return build_palette(CATEGORY_ACCENT["默认"], theme or "light")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: color_system.py <accent_hex> [light|dark] [bg_hex]"}))
        sys.exit(1)
    accent = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else "light"
    bg = sys.argv[3] if len(sys.argv) > 3 else None
    out = build_palette(accent, theme, bg)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
