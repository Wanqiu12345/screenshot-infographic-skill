#!/usr/bin/env python
"""从浏览器截图中尝试提取浏览器标签页 favicon。

用法:
    python extract_favicon.py <screenshot.png> <out_icon.png>

策略:
1. 裁剪顶部条（高度约 0.12 的截图）和左侧区域（宽度约 0.15 的截图）。
2. 使用 RapidOCR 找到最靠左上角的文本行，favicon 通常在该文本行的左侧。
3. 如果 OCR 失败或找不到文本，回退到固定左上角裁剪（0.00,0.00,0.04,0.04）。
4. 对裁剪结果进行背景去除、居中，输出 64x64 或 128x128 的透明 PNG。
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_OCR = True
except Exception:
    HAS_OCR = False


def dominant_color(img):
    """返回图像最常见颜色（RGB）。"""
    small = img.resize((40, 40))
    from collections import Counter
    data = list(small.get_flattened_data())
    cnt = Counter(data)
    return cnt.most_common(1)[0][0]


def is_light(color):
    r, g, b = color[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150


def find_text_leftmost_top(img_path, max_y_ratio=0.12, max_x_ratio=0.25):
    """返回最靠近左上角的文本行中心 (cx, cy, x1, x2, y1, y2) 归一化坐标。"""
    if not HAS_OCR:
        return None
    engine = RapidOCR()
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    result = engine(str(img_path))
    if not result or not result[0]:
        return None

    best = None
    best_score = float('inf')
    for box, text, score in result[0]:
        if not text.strip():
            continue
        x1, y1 = box[0]
        x2, y2 = box[2]
        cx = (x1 + x2) / 2 / w
        cy = (y1 + y2) / 2 / h
        if cy > max_y_ratio or cx > max_x_ratio:
            continue
        # 找最靠左上角的
        score_val = cx + cy
        if score_val < best_score:
            best_score = score_val
            best = (cx, cy, x1 / w, x2 / w, y1 / h, y2 / h)
    return best


def remove_background(img_rgba, threshold=35):
    """把最常见颜色当作背景移除，返回处理后的 RGBA 图像。"""
    data = list(img_rgba.get_flattened_data())
    from collections import Counter
    bg = Counter(data).most_common(1)[0][0]
    bg_r, bg_g, bg_b, bg_a = bg
    new_data = []
    for r, g, b, a in data:
        if abs(r - bg_r) < threshold and abs(g - bg_g) < threshold and abs(b - bg_b) < threshold:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img_rgba.putdata(new_data)
    return img_rgba


def find_icon_bbox(img_rgba, min_pixels=20):
    """返回非透明像素的 bounding box，若无明显图标返回 None。"""
    bbox = img_rgba.getbbox()
    if not bbox:
        return None
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    if w < min_pixels or h < min_pixels:
        return None
    return bbox


def extract_favicon(screenshot_path, out_path, size=80):
    img = Image.open(screenshot_path).convert("RGB")
    w, h = img.size

    text = find_text_leftmost_top(screenshot_path)
    if text:
        cx, cy, x1, x2, y1, y2 = text
        text_top = int(y1 * h)
        text_bottom = int(y2 * h)
        text_left = int(x1 * w)
        text_h = text_bottom - text_top
        # 裁剪文本左侧的整个条带（从图像左边缘到文本左边缘），纵向略扩展
        pad_y = max(4, text_h // 3)
        strip = img.crop((0, max(0, text_top - pad_y), text_left, min(h, text_bottom + pad_y)))
        strip = strip.convert("RGBA")
        strip = remove_background(strip)

        # 在条带里找第一个非背景对象（favicon）
        bbox = find_icon_bbox(strip, min_pixels=max(10, text_h // 3))
        if bbox:
            bx1, by1, bx2, by2 = bbox
            # 如果条带里还有多个物体，只取最靠左且尺寸合理的一个
            icon_w, icon_h = bx2 - bx1, by2 - by1
            # 扩展一点边距，避免裁太紧
            margin = max(2, icon_w // 10)
            bx1 = max(0, bx1 - margin)
            by1 = max(0, by1 - margin)
            bx2 = min(strip.width, bx2 + margin)
            by2 = min(strip.height, by2 + margin)
            crop = strip.crop((bx1, by1, bx2, by2))
        else:
            # 找不到明确图标，回退到固定左上角
            crop = img.crop((0, 0, int(w * 0.04), int(h * 0.04))).convert("RGBA")
            crop = remove_background(crop)
    else:
        # 回退：固定左上角裁剪
        crop = img.crop((0, 0, int(w * 0.04), int(h * 0.04))).convert("RGBA")
        crop = remove_background(crop)

    # 如果去背景后几乎全透明，说明背景判断失败，回退原图
    alpha_sum = sum(a for r, g, b, a in list(crop.get_flattened_data()))
    if alpha_sum < 255 * 10:
        crop = img.crop((0, 0, int(w * 0.04), int(h * 0.04))).convert("RGBA")

    # 居中裁剪成正方形（保持图标居中，保留透明背景）
    cw, ch = crop.size
    s = max(cw, ch)
    square = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    left = (s - cw) // 2
    top = (s - ch) // 2
    square.paste(crop, (left, top))
    square = square.resize((size, size), Image.LANCZOS)
    square.save(out_path, "PNG")
    return out_path


def main():
    if len(sys.argv) < 3:
        print("usage: extract_favicon.py <screenshot.png> <out_icon.png>")
        sys.exit(1)
    p = extract_favicon(sys.argv[1], sys.argv[2])
    print(p)


if __name__ == "__main__":
    main()
