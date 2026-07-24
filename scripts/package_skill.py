#!/usr/bin/env python3
"""把当前 skill 打包成可分发 zip，提交前调用一次即可。

产出：<skill根>/release/screenshot-tutorial-generator.zip
解压后得到顶层文件夹 screenshot-tutorial-generator/，可直接复制到
~/.workbuddy/skills/ 或 .workbuddy/skills/ 完成安装。

已排除：.git / __pycache__ / *.pyc / output / scratch / .workbuddy /
release / dist / node_modules / *.zip / *.log 等无关产物。
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "release")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "screenshot-tutorial-generator.zip")

EXCLUDE_DIRS = {
    ".git", "__pycache__", "output", "output_text", "output_screenshot",
    "scratch", ".workbuddy", "release", "dist", "assets",
    "node_modules", ".venv", "venv", "build", "tmp",
}
EXCLUDE_EXT = {".pyc", ".pyo", ".zip", ".log"}


def should_exclude(rel: str) -> bool:
    parts = rel.split(os.sep)
    # 运行时产物目录（以 output_ 开头等）一律排除
    if any(p in EXCLUDE_DIRS or p.startswith("output_") for p in parts):
        return True
    # 示例大图仅用于仓库展示，分发包剔除以减小体积（install.py 对缺失为软校验）
    if "examples" in parts and rel.lower().endswith(".png"):
        return True
    return os.path.splitext(rel)[1].lower() in EXCLUDE_EXT


count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            full = os.path.join(base, fn)
            rel = os.path.relpath(full, ROOT)
            if should_exclude(rel):
                continue
            z.write(full, os.path.join("screenshot-tutorial-generator", rel))
            count += 1

size = os.path.getsize(OUT)
print(f"wrote {OUT}")
print(f"files={count} size={size} bytes ({size/1024:.0f} KB)")
