#!/usr/bin/env python
"""可选：用 OCR 在截图中按文字定位控件坐标，输出归一化矩形。
用法: python ocr_locate.py <image> "<关键词>"
输出: JSON {found, box:[x,y,w,h](归一化), text, matches:[...]}

依赖 rapidocr-onnxruntime（轻量，纯 CPU）。未安装时给出提示。
多模态 agent 可直接目测坐标，无需本脚本。
"""
import sys, json


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: ocr_locate.py <image> <keyword>"}))
        sys.exit(1)
    image, keyword = sys.argv[1], sys.argv[2]
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print(json.dumps({
            "error": "rapidocr-onnxruntime not installed",
            "hint": "pip install rapidocr-onnxruntime  (或让多模态 agent 直接目测坐标)"
        }, ensure_ascii=False))
        sys.exit(2)

    from PIL import Image
    W, H = Image.open(image).size
    ocr = RapidOCR()
    result, _ = ocr(image)
    matches = []
    if result:
        for box, text, score in result:
            if keyword in text or text in keyword:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
                matches.append({
                    "text": text,
                    "score": round(float(score), 3),
                    "box": [round(x0 / W, 4), round(y0 / H, 4),
                            round((x1 - x0) / W, 4), round((y1 - y0) / H, 4)],
                })
    out = {"found": bool(matches), "keyword": keyword,
           "img_size": [W, H], "matches": matches}
    if matches:
        out["box"] = matches[0]["box"]
        out["text"] = matches[0]["text"]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
