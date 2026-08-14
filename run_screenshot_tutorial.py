#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""screenshot-infographic-skill 端到端运行脚本（命令行 / 自动化用）。

串联：取色 → 提取 favicon → 裁剪功能区域 → 填充模板 → 无头浏览器渲染 PNG。

用法
----
  # 默认用仓库自带的 examples/screenshot.png 跑一遍演示，结果输出到 output/
  python run_screenshot_tutorial.py

  # 用你自己的截图（Windows 用 set，macOS/Linux 用 export）
  set SCREENSHOT=D:/path/to/your.png
  python run_screenshot_tutorial.py

前置：请先运行 `python install.py` 安装依赖（会在本目录创建隔离 .venv）。

想换成你自己的产品：修改下方「改成你自己的产品信息」区块，
并在 DETAILS 里调整每个细节图对应的截图裁剪坐标（归一化 0~1）。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.resolve()
SKILL = BASE  # 本脚本就位于 skill 根目录

# social_post 是纯标准库模块，直接 import 即可（无需 venv 依赖）
sys.path.insert(0, str(BASE / "scripts"))
from social_post import build_social_post, write_social_post


def _split_brand(brand):
    """品牌名按语义断行：仅在 '·' / '.' 处断开（空格保留完整），用于封面主/副标题。

    例：「世界是一片荒原.AI 思维导图」→ ('世界是一片荒原', 'AI 思维导图')；
        「美图秀秀」→ ('美图秀秀', '')。
    """
    for sep in ("·", "."):
        if sep in brand:
            m, s = brand.split(sep, 1)
            return m.strip(), s.strip()
    return brand.strip(), ""

# 优先使用 install.py 创建的隔离 venv，否则回退系统 python3
if sys.platform == "win32":
    VENV_PY = BASE / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PY = BASE / ".venv" / "bin" / "python"
PY = str(VENV_PY) if VENV_PY.exists() else "python3"

# 截图来源：默认用仓库自带的 examples，可用环境变量 SCREENSHOT 覆盖
SCREENSHOT = Path(os.environ.get("SCREENSHOT", str(BASE / "examples" / "screenshot.png"))).resolve()

# 输出目录（独立隔离，已加入 .gitignore，不会污染源码）
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

# ===================== 产品信息（真实使用请覆盖）=====================
# 默认用仓库自带 demo 产品（examples/screenshot.png 即该产品截图），便于一键演示。
# 真实使用时，用环境变量覆盖为「截图里对应产品的真实名字 / 网址 / 副标题 / 分类」：
#   set BRAND_NAME=你的产品名
#   set BRAND_URL=https://你的产品网址/
#   set BRAND_SUBTITLE=一句话副标题
#   set BRAND_CATEGORY=产品分类（如「AI/科技」「美食/餐饮」「教育/知识」）
# 不覆盖则沿用 demo 产品——切勿直接用于你自己的截图。
BRAND = os.environ.get("BRAND_NAME", "世界是一片荒原.AI 思维导图")
URL = os.environ.get("BRAND_URL", "https://th3hj2tsh4.coze.site/")
SUBTITLE = os.environ.get("BRAND_SUBTITLE", "聊天生成 · 文档解析 · 一键导出")
CATEGORY = os.environ.get("BRAND_CATEGORY", "AI/科技")
BADGE = "功能导览"
RADIUS = 18
# =================================================================

# ===================== 极简传播封面（独立一张，不编号）=====================
# 设计：顶部栏目小字 + 居中大图标 + 超大品牌名 + ≤12字 slogan + 可选 desc。
# 背景跟随主题色；品牌名过长时拆成「主标题 + 副标题」两层（保留完整品牌，不缩写）。
# 栏目名 series 由 agent 根据用户输入推导并与用户确认；此处给默认值便于一键演示。
COVER_SERIES = "AI 工具实测"
COVER_BRAND_MAIN, COVER_BRAND_SUB = _split_brand(BRAND)
COVER_SLOGAN = "聊天一句话，画出脑图"
COVER_DESC = "导入文档也能变导图"
# =================================================================

# 概览卡片：把产品全部核心功能拆成 6 张小卡
ITEMS = [
    {"num": "01", "icon": "chat", "title": "聊天输入生成", "desc": "在底部输入框描述需求，AI 自动把一句话变成完整的思维导图。"},
    {"num": "02", "icon": "file", "title": "导入文档解析", "desc": "上传 Word 或 PDF，AI 自动提炼文档结构并生成对应导图。"},
    {"num": "03", "icon": "layers", "title": "多图表类型", "desc": "支持思维导图、架构图、流程图、时序图、关系图五种表达方式。"},
    {"num": "04", "icon": "palette", "title": "多种视觉风格", "desc": "经典、手绘、商务、极简线框四种风格，匹配不同使用场景。"},
    {"num": "05", "icon": "plus", "title": "手动添加节点", "desc": "选中节点后点击添加，自由补充或调整导图结构。"},
    {"num": "06", "icon": "download", "title": "多格式导出", "desc": "一键导出高清图片、PDF 或 XMind 文件，方便分享与二次编辑。"},
]

# 细节图：每个功能一张，coords 为截图归一化裁剪框 (x, y, w, h)
DETAILS = [
    {
        "slug": "chat_gen", "idx": 2, "tag": "核心功能",
        "title": "聊天生成思维导图",
        "lead": "在底部输入框用自然语言描述需求，AI 会自动理解并生成对应的思维导图。",
        "coords": (0.05, 0.72, 0.90, 0.24),
        "value": {"title": "为什么方便", "text": "不需要学习复杂软件，像聊天一样说一句话，就能在几秒内得到一张结构清晰的导图，大幅降低脑图工具的使用门槛。"},
        "tip": {"title": "适用场景", "text": "适合把一句话想法快速可视化，比如会议纪要、读书笔记、项目规划、学习提纲等。描述越具体，生成的层级越准确。"},
        "steps": [
            {"title": "聚焦输入框", "desc": "在页面底部找到对话输入栏，这里支持自然语言，不用写复杂指令。"},
            {"title": "描述你的需求", "desc": "输入一句话，例如“帮我生成一个项目管理的思维导图”或“整理一份 Python 学习大纲”。"},
            {"title": "AI 自动成图", "desc": "按 Enter 发送后，模型会自动提炼层级关系，几秒钟内在画布上渲染出完整导图。"},
            {"title": "按需微调", "desc": "生成后可以继续补充、删除或调整节点，直到结构符合你的预期。"},
        ],
    },
    {
        "slug": "import_doc", "idx": 3, "tag": "核心功能",
        "title": "导入文档自动解析",
        "lead": "支持上传 Word 或 PDF 文档，AI 自动提取核心内容并转换成思维导图。",
        "coords": (0.60, 0.00, 0.30, 0.10),
        "value": {"title": "为什么方便", "text": "省去复制粘贴和手动整理层级的时间，几十页文档能在几秒内转成可交互导图，方便后续编辑和分享。"},
        "tip": {"title": "使用建议", "text": "文档结构越清晰，生成的导图越准确；适合会议纪要、论文、报告等已有文档的再整理。"},
        "steps": [
            {"title": "点击导入文档", "desc": "在页面右上角找到“导入文档”按钮，点击后选择本地文件。"},
            {"title": "选择 Word / PDF", "desc": "目前支持 .docx 和 .pdf 两种格式，选中后等待上传完成。"},
            {"title": "自动解析生成", "desc": "AI 会提取文档标题与段落结构，自动转换成可交互的思维导图，无需手动复制粘贴。"},
            {"title": "检查并调整", "desc": "生成后检查节点是否完整，对缺失或冗余的层级进行手动补充或删减。"},
        ],
    },
    {
        "slug": "chart_type", "idx": 4, "tag": "特色功能",
        "title": "多种图表类型切换",
        "lead": "除了思维导图，还能一键切换架构图、流程图、时序图、关系图等不同表达方式。",
        "coords": (0.45, 0.00, 0.35, 0.10),
        "value": {"title": "为什么实用", "text": "同一套内容可以瞬间换成不同视图，满足工作汇报、技术文档、流程梳理等多种表达场景，不用反复画图。"},
        "tip": {"title": "怎么选", "text": "展示层级结构用思维导图；描述系统架构选架构图；梳理流程用流程图；强调交互顺序用时序图。"},
        "steps": [
            {"title": "找到类型选择器", "desc": "在页面顶部工具栏中间，当前显示为“类型 思维导图”的下拉入口。"},
            {"title": "切换图表类型", "desc": "点击后在思维导图、架构图、流程图、时序图、关系图中选择一种。"},
            {"title": "实时重排预览", "desc": "画布中的内容会按照新类型的布局规则自动重排，立刻看到不同表达效果。"},
            {"title": "保存为对应格式", "desc": "切换后可直接导出对应类型的图片或文件，方便插入到 PPT、文档或笔记中。"},
        ],
    },
    {
        "slug": "export", "idx": 5, "tag": "核心功能",
        "title": "多格式一键导出",
        "lead": "完成编辑后，可将导图导出为高清图片、PDF 文档或 XMind 文件，方便分享和二次编辑。",
        "coords": (0.00, 0.04, 0.28, 0.16),
        "value": {"title": "为什么灵活", "text": "图片适合社交媒体分享，PDF 适合打印和报告，XMind 适合在专业脑图软件中继续编辑，覆盖大多数使用场景。"},
        "tip": {"title": "格式选择", "text": "发社交媒体用图片；写报告用 PDF；需要在其他思维导图软件里继续编辑就选 XMind。"},
        "steps": [
            {"title": "确认导图内容", "desc": "先检查当前画布上的导图是否完整，节点和结构是否已调整到满意状态。"},
            {"title": "选择导出格式", "desc": "在页面左上角点击“导出图片”“导出 PDF”或“导出 XMind”中的任意一个按钮。"},
            {"title": "下载并使用", "desc": "等待生成完成后下载文件，即可用于汇报、分享或导入到其他工具继续编辑。"},
            {"title": "批量分享", "desc": "也可以把图片直接粘贴到微信、飞书、Notion 等平台，方便团队协同。"},
        ],
    },
]

# 概览卡片顺序：01聊天 02导入 03图表 04风格 05添加 06导出
FEATURE_IDX_MAP = {"chat_gen": 0, "import_doc": 1, "chart_type": 2, "export": 5}


def run(*args):
    subprocess.run([PY, *map(str, args)], check=True)


def main():
    if not SCREENSHOT.exists():
        raise SystemExit(f"[!] 找不到截图：{SCREENSHOT}\n    请设置环境变量 SCREENSHOT 指向你的截图，或放入 examples/screenshot.png")

    # 1. 取色 + 色彩系统推导
    print("[1/5] 取色与色彩系统推导 ...")
    result = subprocess.run([PY, str(SKILL / "scripts" / "extract_theme.py"), str(SCREENSHOT)],
                            capture_output=True, text=True, check=True)
    try:
        theme = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        raise RuntimeError("extract_theme did not return valid JSON")
    (OUT / "theme.json").write_text(json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8")
    pal = theme["palette"]

    # 2. 提取品牌图标（从浏览器标签页自动提取 favicon）
    print("[2/5] 提取品牌 favicon ...")
    favicon_path = OUT / "favicon_logo.png"
    run(SKILL / "scripts" / "extract_favicon.py", SCREENSHOT, favicon_path)

    # 2.5 极简封面（独立一张，放在最前，不编号）
    print("[2.5/6] 组装极简封面 ...")
    favicon_ok = favicon_path.exists() and favicon_path.stat().st_size > 300
    cover_cfg = {
        "type": "cover",
        "icon_image": str(favicon_path) if favicon_ok else None,
        "icon_text": BRAND[:1],
        "series": COVER_SERIES,
        "brand_main": COVER_BRAND_MAIN,
        "brand_sub": COVER_BRAND_SUB,
        "slogan": COVER_SLOGAN,
        "desc": COVER_DESC,
        "palette": pal,
        "radius": RADIUS,
        "watermark": BRAND,
    }
    cover_cfg_path = OUT / "cover_config.json"
    cover_cfg_path.write_text(json.dumps(cover_cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. 概览图配置
    print("[3/6] 组装概览图 ...")
    overview_cfg = {
        "type": "overview",
        "logo_image": str(favicon_path),
        "brand": BRAND,
        "subtitle": SUBTITLE,
        "badge": BADGE,
        "urlbar": URL,
        "screenshot": str(SCREENSHOT),
        "palette": pal,
        "radius": RADIUS,
        "items": ITEMS,
        "footer": {"brand": BRAND, "url": URL, "page": "1 / 5"},
    }
    overview_cfg_path = OUT / "overview_config.json"
    overview_cfg_path.write_text(json.dumps(overview_cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. 细节图配置 + 裁剪
    print("[4/5] 裁剪功能区域并组装细节图 ...")
    detail_cfgs = []
    for d in DETAILS:
        crop_path = OUT / f"crop_{d['slug']}.png"
        x, y, w, h = d["coords"]
        run(SKILL / "scripts" / "crop_region.py", SCREENSHOT, crop_path, x, y, w, h, 0.02)
        cfg = {
            "type": "detail",
            "tag": d["tag"],
            "pageinfo": f"{d['idx']} / 5",
            "title": d["title"],
            "lead": d["lead"],
            "crop": str(crop_path),
            "palette": pal,
            "radius": RADIUS,
            "feature_color": pal["feature"][FEATURE_IDX_MAP.get(d["slug"], 0)],
            "value": d.get("value"),
            "tip": d["tip"],
            "footer": {"brand": BRAND, "url": URL, "page": f"{d['idx']} / 5"},
            "steps": d["steps"],
        }
        cfg_path = OUT / f"detail_config_{d['slug']}.json"
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        detail_cfgs.append((d["slug"], d["idx"], cfg_path))

    # 5. 渲染
    print("[5/6] 渲染封面 PNG ...")
    run(SKILL / "scripts" / "fill_template.py", cover_cfg_path, OUT / "cover_out.html")
    run(SKILL / "scripts" / "render.py", OUT / "cover_out.html", OUT / "00_cover.png", 1080, 1440, 2)

    print("[6/6] 渲染概览 + 细节 PNG（无头浏览器，2× 高清）...")
    run(SKILL / "scripts" / "fill_template.py", overview_cfg_path, OUT / "overview_out.html")
    run(SKILL / "scripts" / "render.py", OUT / "overview_out.html", OUT / "01_overview.png", 1080, 1440, 2)
    for slug, idx, cfg_path in detail_cfgs:
        run(SKILL / "scripts" / "fill_template.py", cfg_path, OUT / f"detail_out_{slug}.html")
        run(SKILL / "scripts" / "render.py", OUT / f"detail_out_{slug}.html", OUT / f"{idx:02d}_{slug}.png", 1080, 1440, 2)

    # 6. 随图附赠小红书文案（一律使用真实产品名，不写死 demo 品牌）
    social_theme = {
        "topic": BRAND,
        "subject": BRAND,
        "category": CATEGORY,
        "hook": SUBTITLE,
        "points": [it["title"] for it in ITEMS],
        "closing": "了解清楚之后，需要时直接拿来用就行。",
    }
    post = build_social_post(social_theme)
    sp = write_social_post(post, OUT)
    print(f"[赠品] 已生成小红书文案：{sp}")
    print(f"       标题：{post['title']}（{post['title_len']} 字）｜备选：{' / '.join(post['alt_titles'])}")

    print("\n[✓] 完成！输出在:", OUT)
    for name in ["00_cover.png", "01_overview.png", "02_chat_gen.png", "03_import_doc.png", "04_chart_type.png", "05_export.png"]:
        print("   -", name)


if __name__ == "__main__":
    main()
