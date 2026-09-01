#!/usr/bin/env python
"""用系统浏览器(无头)把 HTML 渲染成高清 PNG。
用法: python render.py <html_path> <out_png> [width] [height] [scale]
默认 1080x1440 (3:4 竖版), scale=2 -> 输出 2160x2880。
自动查找 Edge / Chrome / Chromium。
"""
import sys, os, subprocess, tempfile, shutil, glob


def find_browser():
    candidates = []
    if os.name == "nt":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pfx = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(pfx, r"Microsoft\Edge\Application\msedge.exe"),
            os.path.join(pf, r"Microsoft\Edge\Application\msedge.exe"),
            os.path.join(pf, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(pfx, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:
        for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
            p = shutil.which(name)
            if p:
                candidates.append(p)
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def main():
    if len(sys.argv) < 3:
        print("usage: render.py <html_path> <out_png> [width] [height] [scale]")
        sys.exit(1)
    html = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    width = sys.argv[3] if len(sys.argv) > 3 else "1080"
    height = sys.argv[4] if len(sys.argv) > 4 else "1440"
    scale = sys.argv[5] if len(sys.argv) > 5 else "2"

    browser = find_browser()
    if not browser:
        print("ERROR: 未找到 Chromium 内核浏览器（Edge / Chrome / Chromium）。")
        print("   Windows 推荐安装 Microsoft Edge；macOS 推荐 Chrome；")
        print("   Linux 服务器/容器请安装 chromium，例如：")
        print("     Debian/Ubuntu : sudo apt-get update && sudo apt-get install -y chromium")
        print("     RHEL/Fedora   : sudo dnf install -y chromium")
        print("     Arch          : sudo pacman -S chromium")
        print("   装好后重试即可。")
        sys.exit(2)

    userdir = tempfile.mkdtemp(prefix="tutgen_")
    url = "file:///" + html.replace("\\", "/")
    # 最小环境：宿主注入的 NODE_OPTIONS / ELECTRON_RUN_AS_NODE / CHROME_CRASHPAD_PIPE_NAME
    # 等变量会让 Chromium 无头模式秒退（2026-09-01 实测），只传必需项。
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "USERPROFILE": os.environ.get("USERPROFILE", ""),
    }
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-sandbox", "--disable-dev-shm-usage", f"--user-data-dir={userdir}",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        "--default-background-color=00000000",
        f"--screenshot={out}", url,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=90, env=safe_env)
    finally:
        shutil.rmtree(userdir, ignore_errors=True)

    if os.path.exists(out):
        print(f"OK: {out}")
    else:
        print("ERROR: screenshot not produced")
        sys.exit(3)


if __name__ == "__main__":
    main()
