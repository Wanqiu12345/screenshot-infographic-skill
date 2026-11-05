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


def run(cmd, hint=None, **kw):
    """执行命令，失败时给一句人能照做的提示，而不是抛一串 traceback。"""
    print(f"> {' '.join(map(str, cmd))}")
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] 命令执行失败（退出码 {e.returncode}）")
        if hint:
            print("    " + hint)
        sys.exit(1)
    except OSError as e:
        print(f"\n[!] 无法执行命令：{e}")
        if hint:
            print("    " + hint)
        sys.exit(1)


def find_browser():
    """返回 (浏览器名, 可执行路径) 或 None。

    直接复用 scripts/render.py 的查找逻辑（Windows 查 Program Files 与
    LOCALAPPDATA、macOS 查 /Applications、Linux 走 shutil.which 全 PATH），
    避免这里和渲染器各维护一份候选列表、其中一份漏掉某些安装位置。
    """
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        from render import find_browser as _find
    except ImportError:
        return None
    path = _find()
    if not path:
        return None
    return Path(path).name, path


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
        run([sys.executable, "-m", "venv", str(VENV)],
            hint="创建虚拟环境失败。请确认 Python 安装完整（Windows 建议从 python.org 重装并勾选"
                 " tcl/tk 与 pip），或手动删除本目录下的 .venv 后重试。")
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
        run([str(python), "-m", "ensurepip", "--upgrade"],
            hint="venv 内缺少 pip 且无法自动安装。Linux 可先安装 python3-venv / python3-pip 后重试。")

    print("[→] 安装依赖...")
    try:
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("[!] pip 自身升级失败，通常不影响使用，继续安装依赖")

    if REQUIREMENTS.exists():
        run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            hint="装依赖失败，通常是网络问题。可换国内镜像重试：\n"
                 "       .venv\\Scripts\\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Pillow")
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

    # 4b. 检查演示素材（截图模式的默认输入；缺了跑演示会直接报「找不到截图」）
    demo = ROOT / "examples" / "screenshot.png"
    if demo.exists():
        print(f"[✓] 演示截图就位: {demo}")
    else:
        print(f"[!] 缺少演示截图 {demo}，截图模式的一键演示会失败")
        print("   可用环境变量指定自己的截图：set SCREENSHOT=D:\\path\\to\\your.png")

    # 5. 验证关键脚本
    print("[→] 验证关键脚本...")
    # 路径经 argv 传入，不拼进 -c 源码：路径含单引号（如 O'Brien）时拼字符串会 SyntaxError
    run([str(python), "-c",
         "import sys; sys.path.insert(0, sys.argv[1]); "
         "import render, social_post, text_v2, screenshot_v2; "
         "print('import ok: render / social_post / text_v2 / screenshot_v2')",
         str(ROOT / "scripts")],
        hint="关键脚本导入失败，多半是 .venv 损坏：删除本目录下的 .venv 后重跑 python install.py")

    banner("安装完成")
    print("使用方式：")
    print("  1. 文案模式演示:  python run_text_tutorial.py")
    print("  2. 截图模式演示:  python run_screenshot_tutorial.py")
    print("  3. 或直接在对话里对 AI 说「用 screenshot-infographic-skill 给 XX 做一套配图」")


if __name__ == "__main__":
    main()
