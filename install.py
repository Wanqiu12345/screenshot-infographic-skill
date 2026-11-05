#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一键安装脚本：创建隔离 venv、安装依赖、检查浏览器可用性。

用法:
  python install.py
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"


def banner(msg):
    print("\n" + "=" * 60)
    print(msg)
    print("=" * 60)


def run(cmd, **kw):
    print(f"> {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kw)


def find_browser():
    """返回 (浏览器名, 可执行路径) 或 None"""
    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates = [
            Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
            Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        ]
    elif system == "Darwin":
        candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ]
    else:
        candidates = [Path(p) for p in [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/microsoft-edge",
        ]]
    for c in candidates:
        if c.exists():
            return c.name, str(c)
    return None


def main():
    banner("Screenshot Tutorial Generator 安装脚本")

    # 1. Python 版本检查
    if sys.version_info < (3, 10):
        print(f"[!] 需要 Python 3.10+，当前 {sys.version}")
        sys.exit(1)
    print(f"[✓] Python {sys.version_info.major}.{sys.version_info.minor} 已满足")

    # 2. 创建 venv
    if not VENV.exists():
        print(f"[→] 创建隔离虚拟环境: {VENV}")
        run([sys.executable, "-m", "venv", str(VENV)])
    else:
        print(f"[✓] 虚拟环境已存在: {VENV}")

    python = VENV / ("Scripts" if platform.system() == "Windows" else "bin") / (
        "python.exe" if platform.system() == "Windows" else "python")

    if not python.exists():
        print(f"[!] 未找到 {python}，虚拟环境可能创建失败，请删除 {VENV} 后重试")
        sys.exit(1)

    # 3. 升级 pip 并安装依赖
    #
    # 这里统一用 `venv 里的 python -m pip`，不用 pip.exe，原因有两条：
    #   1) Windows 上 pip.exe 给自己升级会撞上 pip 的内置保护。pip 源码里
    #      misc.py::protect_pip_from_modification_on_windows 会在
    #      「argv[0] 是 pip/pip3/pip3.x」且操作是修改 pip 时直接抛错：
    #      ERROR: To modify pip, please run the following command: ... python.exe -m pip ...
    #      退出码 1，再叠加下面的 check=True，整个安装就此中断。
    #   2) `sys.executable` 也不可靠：用户直接用系统 Python 执行 install.py 时，
    #      它指向系统解释器，装出来的包落在宿主机环境，venv 里照样没有 Pillow，
    #      第 5 步的 import 校验必然失败。
    # 用 venv 的 python 显式调 -m pip，两个坑一起避开，也不依赖用户是否激活了 venv。
    print("[→] 检查 venv 内的 pip...")
    if subprocess.run([str(python), "-m", "pip", "--version"],
                      capture_output=True).returncode != 0:
        print("[→] venv 内没有 pip（部分 Linux 发行版不自带），执行 ensurepip")
        run([str(python), "-m", "ensurepip", "--upgrade"])

    print("[→] 安装依赖...")
    try:
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("[!] pip 自身升级失败，通常不影响使用，继续安装依赖")

    if REQUIREMENTS.exists():
        run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    else:
        print(f"[!] 未找到 {REQUIREMENTS}，跳过依赖安装")

    # 4. 检查浏览器
    browser = find_browser()
    if browser:
        name, path = browser
        print(f"[✓] 找到浏览器: {name} ({path})")
    else:
        print("[!] 未找到 Edge / Chrome / Chromium，请安装后重试")
        print("   Windows 推荐安装 Microsoft Edge；macOS 推荐 Chrome；Linux 推荐 Chromium")

    # 5. 验证关键脚本
    print("[→] 验证关键脚本...")
    run([str(python), "-c",
         "import sys; sys.path.insert(0, r'%s'); "
         "import render; import social_post; import text_v2; import screenshot_v2; "
         "print('import ok: render / social_post / text_v2 / screenshot_v2')"
         % str(ROOT / "scripts")])

    banner("安装完成")
    print("使用方式：")
    print("  1. 文案模式演示:  python run_text_tutorial.py")
    print("  2. 截图模式演示:  python run_screenshot_tutorial.py")
    print("  3. 或直接在对话里对 AI 说「用 screenshot-infographic-skill 给 XX 做一套配图」")


if __name__ == "__main__":
    main()
