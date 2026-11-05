#!/usr/bin/env python3
"""把当前 skill 打包成可分发 zip，提交前调用一次即可。

产出：<skill根>/release/screenshot-infographic-skill.zip
解压后得到顶层文件夹 screenshot-infographic-skill/，可直接复制到
~/.workbuddy/skills/ 或 .workbuddy/skills/ 完成安装。

已排除：.git / __pycache__ / *.pyc / output / scratch / .workbuddy /
release / dist / node_modules / *.zip / *.log 等无关产物。
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "release")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "screenshot-infographic-skill.zip")

EXCLUDE_DIRS = {
    ".git", "__pycache__", "output", "output_text", "output_screenshot",
    "scratch", ".workbuddy", "release", "dist",
    "node_modules", ".venv", "venv", "build", "tmp",
}
EXCLUDE_EXT = {".pyc", ".pyo", ".zip", ".log"}

# examples 下「示例成图」只服务于 README 展示，不必进分发包；
# 但 examples/screenshot.png 是 run_screenshot_tutorial.py 的默认演示输入，
# 必须随包发出，否则用户解压后跑演示会直接「找不到截图」。
_EXAMPLE_OUTPUT_PREFIX = ("00_", "01_", "02_", "03_", "04_", "05_")
_EXAMPLE_OUTPUT_EXTRA = ("wf_agent_v2_",)


def _is_example_showcase(rel: str) -> bool:
    """examples 下的图现在全部随包发出（README 用它做效果预览）。

    保留该函数是为了以后需要瘦身时有单一开关。
    """
    return False


def should_exclude(rel: str) -> bool:
    parts = rel.split(os.sep)
    # 运行时产物目录（以 output_ 开头等）一律排除
    if any(p in EXCLUDE_DIRS or p.startswith("output_") for p in parts):
        return True
    # 下划线开头的目录视为临时调试产物（如 _verify_color / _prof / _html），不进分发包
    if any(p.startswith("_") and p != "__pycache__" for p in parts[:-1]):
        return True
    if _is_example_showcase(rel):
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
            z.write(full, os.path.join("screenshot-infographic-skill", rel))
            count += 1

size = os.path.getsize(OUT)
print(f"wrote {OUT}")
print(f"files={count} size={size} bytes ({size/1024:.0f} KB)")
