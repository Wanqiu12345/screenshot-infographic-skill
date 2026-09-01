#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯文案模式端到端执行器（screenshot-infographic-skill）

输入：一段已经由 AI 结构化好的文案配置 text_config.json（字段见 references/text_mode_design.md）。
流程：主题/预设 -> 配色 -> 文生图生成每页 3D 插画（自愈：单图重试 + 收尾补漏）-> 填模板 -> 无头浏览器渲染成套 PNG。

用法：
  python run_text_tutorial.py examples/jinan_drg.json --out output_text
  python run_text_tutorial.py my_text.json                # 默认输出到 ./output_text
  python run_text_tutorial.py examples/jinan_drg.json --no-image   # 跳过文生图（仅看排版占位）
  python run_text_tutorial.py examples/jinan_drg.json --use-existing  # 已有 assets/ 直接复用渲染
  python run_text_tutorial.py --style v2                  # v2 表意型排版（晚秋简约风，无插画离线可跑）
  python run_text_tutorial.py my_v2.json --style v2       # v2 专属配置（见 examples/wf_agent_v2.json）
"""
import sys, os, re, json, argparse, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))

from color_system import build_palette_for_text
import agnes_image
from generate_text_images import ensure_asset, is_valid
from social_post import build_social_post, write_social_post

PY = sys.executable
TPL_BUILD = os.path.join(HERE, "scripts", "fill_template.py")
RENDER = os.path.join(HERE, "scripts", "render.py")
DEFAULT_DEMO = os.path.join(HERE, "examples", "jinan_drg.json")
V2_DEMO = os.path.join(HERE, "examples", "wf_agent_v2.json")


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


def _distill_main(brand):
    """品牌名拆主标题：只按显式分隔符 '.' / '·' 拆分；空格保留，避免把多词产品名（如 DeepSeek Harness）拆散。"""
    if not brand:
        return ""
    for sep in (".", "·"):
        if sep in brand:
            return brand.split(sep, 1)[0].strip()
    return brand.strip()


def _distill_sub(brand):
    if not brand:
        return ""
    for sep in (".", "·"):
        if sep in brand:
            return brand.split(sep, 1)[1].strip()
    return ""


def _short_line(s, n=12):
    """取前 n 字以内的短句；优先在标点/空格处截断，避免把词劈成两半。"""
    s = (s or "").strip().replace("\n", " ")
    if len(s) <= n:
        return s
    # 优先在 n 之前最近的一个中文标点截断
    for i in range(min(n, len(s) - 1), max(0, n // 2 - 1), -1):
        if s[i] in "，,。！？、；：,!?;:\n\r":
            return s[:i + 1]
    # 其次找空格
    cut = s[:n + 1]
    sp = cut.rfind(" ")
    if sp > n // 3:
        return cut[:sp]
    # 兜底硬截断
    return s[:n - 1] + "…"


def _derive_series(cfg):
    cat = cfg.get("category", "") or ""
    if any(k in cat for k in ("医疗", "健康", "养生")):
        return "健康知识小科普"
    if any(k in cat for k in ("AI", "科技", "人工智能", "数码")):
        return "AI 工具实测"
    if any(k in cat for k in ("美食", "餐饮", "烘焙")):
        return "美食探店笔记"
    if any(k in cat for k in ("教育", "学习", "知识")):
        return "知识分享"
    if any(k in cat for k in ("财经", "金融", "投资")):
        return "财经干货分享"
    return "干货分享"


def build_and_render(cfg_json, html_path, png_path):
    subprocess.run([PY, TPL_BUILD, cfg_json, html_path], check=True)
    subprocess.run([PY, RENDER, html_path, png_path], check=True)


def validate_visual_prompts(cfg, skip=False):
    """纯文案模式 schema 校验：cover + 每个 page 都必须有 visual_prompt。

    历史教训（2026-08-14）：某次 pilot 因 p4 漏填 visual_prompt，generate_text_images
    的 ensure_asset 第30行 `if not prompt: return None` 静默跳过，导致 assets/page4.png
    从未生成，模板渲染出「（未生成插画）」占位符，用户发布后才发现。
    改为「显式失败」：缺 prompt 直接 sys.exit 报错，列出具体页面，让用户补全后再跑。
    """
    if skip:
        return
    errors = []
    cover = cfg.get("cover", {})
    if not cover.get("visual_prompt"):
        errors.append("cover（封面）缺少 visual_prompt")
    for i, pg in enumerate(cfg.get("pages", []), 1):
        if not pg.get("visual_prompt"):
            title = pg.get("page_title") or pg.get("layout") or f"第{i}页"
            errors.append(f"pages[{i}]（{title}）缺少 visual_prompt")
    if errors:
        sys.exit(
            "❌ 配置校验失败：以下页面缺少 visual_prompt，继续会生成「未生成插画」占位图。\n"
            + "\n".join(f"  - {e}" for e in errors)
            + "\n\n请为每个页面补全 visual_prompt（3D 插画的英文 prompt），再重新运行。"
            + "\n（如确要纯文字页，请改用 --no-image；不要留空 visual_prompt 后期待自动降级。）"
        )


def run_text_v2(a):
    """--style v2：走表意型排版引擎（scripts/text_v2.py），无 Agnes 插画、离线可跑。

    要求 v2 专属配置（pages 每项带 type: cover/stats/chain/timeline/compare/vs/takeaway）；
    旧 v1 文案配置（visual_prompt 3D 插画格式）不兼容，显式报错指路。
    """
    cfg_path = a.config if (a.config and os.path.exists(a.config)) else V2_DEMO
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    pages = cfg.get("pages", [])
    if not cfg.get("slug") or not pages or not all(isinstance(p.get("type"), str) for p in pages):
        sys.exit(
            "❌ --style v2 需要「表意型排版」专属配置，当前配置像是 v1 旧文案格式（Agnes 3D 插画 + 模板）。\n"
            "   v1 格式请去掉 --style v2 直接运行；v2 格式示例见 examples/wf_agent_v2.json，\n"
            "   直接跑演示：python run_text_tutorial.py --style v2"
        )
    from text_v2 import render_cfg
    out = os.path.abspath(a.out)
    files = render_cfg(cfg, out_dir=out)
    print(f"[完成] v2 表意型排版共 {len(files)} 张，输出目录：{out}")


def main():
    ap = argparse.ArgumentParser(description="纯文案模式：结构化文案 -> 成套教程图")
    ap.add_argument("config", nargs="?", default=None,
                    help="text_config.json 路径（v1 省略则用内置示例；v2 省略则用 examples/wf_agent_v2.json）")
    ap.add_argument("--out", default="output_text", help="输出目录")
    ap.add_argument("--style", choices=["v1", "v2"], default="v1",
                    help="v1=经典杂志风+Agnes 3D 插画（默认，行为不变）；v2=晚秋简约表意型排版（无插画、离线可跑）")
    ap.add_argument("--no-image", action="store_true", help="跳过文生图，仅渲染排版占位")
    ap.add_argument("--no-validate", action="store_true",
                    help="跳过 visual_prompt 配置校验（默认开启：cover/每页缺 visual_prompt 会显式报错，避免生成「未生成插画」占位）")
    ap.add_argument("--use-existing", action="store_true", help="已有 assets/ 图片时直接复用，不重新生成")
    ap.add_argument("--retries", type=int, default=3, help="单图失败重试次数")
    ap.add_argument("--per-image-timeout", type=int, default=420,
                    help="单次生成等待上限(秒)；默认 420 覆盖 Agnes 峰值 5-6 分钟生成")
    a = ap.parse_args()

    # ============ v2 分发：表意型排版引擎（与 v1 流程完全独立） ============
    if a.style == "v2":
        run_text_v2(a)
        return

    cfg_path = a.config if (a.config and os.path.exists(a.config)) else DEFAULT_DEMO
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

    # ============ 阶段0：配置 schema 校验（缺 visual_prompt 显式失败，避免静默占位）============
    if not a.no_image:
        validate_visual_prompts(cfg, skip=a.no_validate)

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
    # 极简传播封面（独立一张，不编号，放在最前；纯文案模式主视觉 3D 图作图标）
    cover_img = os.path.join(assets, "cover.png") if is_valid(os.path.join(assets, "cover.png")) else None
    series = cfg.get("series") or cover.get("kicker") or _derive_series(cfg)
    min_cover_cfg = {
        "type": "cover", "palette": palette, "radius": radius,
        "series": series,
        "icon_image": cover_img,                # 无图时 build_cover 自动降级为文字 logo
        "icon_text": (brand[:1] if brand else "·"),
        "brand_main": cover.get("brand_main") or _distill_main(brand),
        "brand_sub": cover.get("brand_sub") or _distill_sub(brand),
        # slogan 上限提到 24：cover.html 的 .slogan 支持自然换行，硬截到 12 字会产生"…"残句
        "slogan": cover.get("slogan") or _short_line(cover.get("subtitle") or cfg.get("title", ""), 24),
        "desc": cover.get("desc") or _short_line(cover.get("summary", ""), 20),
        "watermark": brand,
    }
    jc = os.path.join(base, "_mincover.json")
    json.dump(min_cover_cfg, open(jc, "w", encoding="utf-8"), ensure_ascii=False)
    build_and_render(jc, os.path.join(base, "_mincover.html"),
                     os.path.join(base, "00_cover.png"))

    # 原「丰富封面」顺延为第 1 张内容页（01_cover.png）
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

    # ============ 阶段3：随图附赠小红书文案 ============
    social_theme = {
        "topic": cfg.get("title", ""),
        "subject": cfg.get("brand") or cfg.get("title", ""),
        "category": cfg.get("category", ""),
        "hook": cover.get("subtitle") or cover.get("title") or cfg.get("title", ""),
        "points": [pg.get("page_title") for pg in pages if pg.get("page_title")],
        "closing": pages[-1].get("summary", "") if pages else "",
        "tags": [series, (cfg.get("brand") or cfg.get("title", "")), "AI工具" if "AI" in (cfg.get("category", "")) else None],
    }
    social_theme["tags"] = [t for t in social_theme["tags"] if t][:3]
    post = build_social_post(social_theme)
    sp = write_social_post(post, base)
    print(f"[赠品] 已生成小红书文案：{sp}")
    print(f"       标题：{post['title']}（{post['title_len']} 字）｜备选：{' / '.join(post['alt_titles'])}")

    print(f"[完成] 极简封面 00_cover.png + 丰富封面与内容页共 {total} 张，输出目录：{base}")


if __name__ == "__main__":
    main()
