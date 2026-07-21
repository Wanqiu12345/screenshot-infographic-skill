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

    if platform.system() == "Windows":
        pip = VENV / "Scripts" / "pip.exe"
        python = VENV / "Scripts" / "python.exe"
    else:
        pip = VENV / "bin" / "pip"
        python = VENV / "bin" / "python"

    # 3. 升级 pip 并安装依赖
    print("[→] 安装依赖...")
    run([str(pip), "install", "--upgrade", "pip"])
    if REQUIREMENTS.exists():
        run([str(pip), "install", "-r", str(REQUIREMENTS)])
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
    example_shot = ROOT / "examples" / "screenshot.png"
    if example_shot.exists():
        run([str(python), str(ROOT / "scripts" / "extract_theme.py"), str(example_shot)])
    else:
        run([str(python), "-c", "import scripts.extract_theme; import scripts.color_system; print('import ok')"])
        print("[!] 未找到 examples/screenshot.png，仅完成导入验证")

    banner("安装完成")
    print("使用方式：")
    print(f"  1. 激活虚拟环境: {VENV}")
    print("  2. 修改 run_screenshot_tutorial.py 中的截图路径与品牌信息")
    print("  3. 运行: python run_screenshot_tutorial.py")


if __name__ == "__main__":
    main()
