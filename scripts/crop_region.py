#!/usr/bin/env python
"""按归一化坐标从截图裁剪出一个功能区域(用于细节图的局部放大)。
用法: python crop_region.py <image> <out> <x> <y> <w> <h> [pad]
坐标均为 0~1 归一化值; pad 为额外留白比例(默认 0.04)。
"""
import sys
from PIL import Image


def main():
    if len(sys.argv) < 7:
        print("usage: crop_region.py <image> <out> <x> <y> <w> <h> [pad]")
        sys.exit(1)
    path, out = sys.argv[1], sys.argv[2]
    x, y, w, h = [float(v) for v in sys.argv[3:7]]
    pad = float(sys.argv[7]) if len(sys.argv) > 7 else 0.04

    img = Image.open(path).convert("RGB")
    W, H = img.size
    left = max(0, (x - pad) * W)
    top = max(0, (y - pad) * H)
    right = min(W, (x + w + pad) * W)
    bottom = min(H, (y + h + pad) * H)
    crop = img.crop((int(left), int(top), int(right), int(bottom)))
    crop.save(out)
    print(f"cropped {crop.size} -> {out}")


if __name__ == "__main__":
    main()
