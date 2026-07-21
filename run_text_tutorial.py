#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯文案模式端到端执行器（screenshot-tutorial-generator）

输入：一段已经由 AI 结构化好的文案配置 text_config.json（字段见 references/text_mode_design.md）。
流程：主题/预设 -> 配色 -> 文生图生成每页 3D 插画（自愈：单图重试 + 收尾补漏）-> 填模板 -> 无头浏览器渲染成套 PNG。

用法：
  python run_text_tutorial.py examples/jinan_drg.json --out output_text
  python run_text_tutorial.py my_text.json                # 默认输出到 ./output_text
  python run_text_tutorial.py examples/jinan_drg.json --no-image   # 跳过文生图（仅看排版占位）
  python run_text_tutorial.py examples/jinan_drg.json --use-existing  # 已有 assets/ 直接复用渲染
"""
import sys, os, re, json, argparse, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))

from color_system import build_palette_for_text
import agnes_image
from generate_text_images import ensure_asset, is_valid

PY = sys.executable
TPL_BUILD = os.path.join(HERE, "scripts", "fill_template.py")
RENDER = os.path.join(HERE, "scripts", "render.py")
DEFAULT_DEMO = os.path.join(HERE, "examples", "jinan_drg.json")


def agnes_reachable(host="apihub.agnes-ai.com", timeout=10):
    """快速探测 Agnes 图片服务是否可直连（HTTP 层）。主要在能连中国大陆网络时成立。
    不可直连时上层应跳过文生图、直接降级为占位渲染，避免自愈重试长时间空耗。
    用 HTTP 探测（而非仅 TCP），可同时覆盖「TCP 通但 HTTP 被墙/超时」的情况。
    """
    import urllib.request, urllib.error
    url = f"https://{host}/"
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True
    except urllib.error.HTTPError:
        # 能拿到任何 HTTP 响应（含 401/404）即说明网络通，放行交给真正的生成逻辑处理
        return True
    except Exception:
        return False


def slug(s, n=14):
    s = re.sub(r'[^\w一-龥]+', '', s or '')
    return s[:n] or "page"


def build_and_render(cfg_json, html_path, png_path):
    subprocess.run([PY, TPL_BUILD, cfg_json, html_path], check=True)
    subprocess.run([PY, RENDER, html_path, png_path], check=True)


def main():
    ap = argparse.ArgumentParser(description="纯文案模式：结构化文案 -> 成套教程图")
    ap.add_argument("config", nargs="?", default=DEFAULT_DEMO,
                    help="text_config.json 路径（省略则用内置示例）")
    ap.add_argument("--out", default="output_text", help="输出目录")
    ap.add_argument("--no-image", action="store_true", help="跳过文生图，仅渲染排版占位")
    ap.add_argument("--use-existing", action="store_true", help="已有 assets/ 图片时直接复用，不重新生成")
    ap.add_argument("--retries", type=int, default=3, help="单图失败重试次数")
    ap.add_argument("--per-image-timeout", type=int, default=420,
                    help="单次生成等待上限(秒)；默认 420 覆盖 Agnes 峰值 5-6 分钟生成")
    a = ap.parse_args()

    cfg_path = a.config if os.path.exists(a.config) else DEFAULT_DEMO
    cfg = json.load(open(cfg_path, encoding="utf-8"))

    base = os.path.abspath(a.out)
    assets = os.path.join(base, "assets")
    os.makedirs(assets, exist_ok=True)

    theme = cfg.get("theme", "light")
    pal_res = build_palette_for_text(cfg.get("category"), cfg.get("preset"), theme)
    palette = pal_res["palette"]
    print(f"[配色] theme={pal_res['theme']} accent={pal_res['accent']} mood={pal_res['mood']}/{pal_res['temperature']}")

    pages = cfg.get("pages", [])
    total = 1 + len(pages)
    brand = cfg.get("brand", "")
    url = cfg.get("url", "")
    radius = cfg.get("radius", 18)
    cover = cfg.get("cover", {})

    # ============ 阶段1：生成全部 3D 插画（自愈）============
    asset_jobs = [("cover", cover.get("visual_prompt"), os.path.join(assets, "cover.png"))]
    for i, pg in enumerate(pages, 1):
        asset_jobs.append((f"page{i}", pg.get("visual_prompt"), os.path.join(assets, f"page{i}.png")))

    if not a.no_image:
        if not agnes_reachable():
            print("[!] 无法直连 Agnes 图片服务 apihub.agnes-ai.com（可能是网络/地区限制；该服务主要面向中国大陆直连）。")
            print("    已跳过 3D 插画生成，仅渲染排版占位图。如需插画：设置环境变量 AGNES_API_KEY 并确保网络可直连该服务。")
        else:
            # 主生成
            for name, prompt, out in asset_jobs:
                ensure_asset(prompt, out, retries=a.retries, timeout=a.per_image_timeout,
                            backoff=8, use_existing=a.use_existing)
            # 收尾补漏：仍缺失的单独再跑
            for name, prompt, out in asset_jobs:
                if is_valid(out):
                    continue
                print(f"[SWEEP] 补漏 {name}")
                for _ in range(2):
                    if is_valid(out):
                        break
                    ensure_asset(prompt, out, retries=1, timeout=a.per_image_timeout, backoff=8)
                    time.sleep(8)

    # ============ 阶段2：渲染（此时资产应已齐全；仍缺失则占位）============
    # 封面
    cover_img = os.path.join(assets, "cover.png") if is_valid(os.path.join(assets, "cover.png")) else None
    cov_cfg = {
        "type": "text_cover", "palette": palette, "radius": radius,
        "cover": cover, "title": cfg.get("title", cover.get("title", "")),
        "footer": {"brand": brand, "url": url, "page": f"1 / {total}"},
    }
    if cover_img:
        cov_cfg["_cover_img"] = cover_img
    j = os.path.join(base, "_cover.json")
    json.dump(cov_cfg, open(j, "w", encoding="utf-8"), ensure_ascii=False)
    build_and_render(j, os.path.join(base, "_cover.html"), os.path.join(base, "01_cover.png"))

    # 内容页
    for i, pg in enumerate(pages, 1):
        img = os.path.join(assets, f"page{i}.png") if is_valid(os.path.join(assets, f"page{i}.png")) else None
        pcfg = dict(pg)
        pcfg["type"] = "text_section"
        pcfg["palette"] = palette
        pcfg["radius"] = radius
        pcfg["pageinfo"] = f"{i + 1} / {total}"
        pcfg["footer"] = {"brand": brand, "url": url, "page": f"{i + 1} / {total}"}
        if img:
            pcfg["_img"] = img
        j = os.path.join(base, f"_page{i}.json")
        json.dump(pcfg, open(j, "w", encoding="utf-8"), ensure_ascii=False)
        build_and_render(j, os.path.join(base, f"_page{i}.html"),
                         os.path.join(base, f"{i + 1:02d}_{slug(pg.get('page_title', pg.get('layout', 'page')))}.png"))

    print(f"[完成] 共 {total} 张，输出目录：{base}")


if __name__ == "__main__":
    main()
