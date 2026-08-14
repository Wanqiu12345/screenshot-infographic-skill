# -*- coding: utf-8 -*-
"""随图附赠的小红书发布文案生成器（screenshot-infographic-skill）。

两个运行脚本在产出全部 PNG 之后调用本模块，向 <out>/social_post.md 写入一段
可直接复制去发社交媒体的文案：标题（<20 字）+ 一段正文（要点 + 话题标签）。

设计要点：
- 纯标准库，不依赖任何第三方包，两个运行脚本都能直接 import。
- 标题严格 < 20 个字（中英文/空格均按 1 个字符计），随机抽一个主标题 + 2 个备选。
- 文案遵循技能「文案质量准则」：平实、干净、准确，不使用「说白了/神器/疯狂/上头」
  等口语化或营销腔字眼。
- 文案内容完全由输入配置推导，不联网、不调用大模型，结果可复现（仅标题随机）。
"""
import os
import random
import datetime

MAX_TITLE = 19  # 标题「小于 20 个字」→ 最多 19


def _measure(s):
    """字符计数：中文/英文/空格/标点均按 1 个字符。"""
    return len(s or "")


def _truncate(s, n):
    if _measure(s) <= n:
        return s
    for i in range(min(n, len(s) - 1), max(0, n // 2), -1):
        if s[i] in "，,。！？、；：,!?;: \n\r":
            return s[:i]
    return s[:n]


def _series(category):
    cat = category or ""
    if any(k in cat for k in ("医疗", "健康", "养生")):
        return "健康科普"
    if any(k in cat for k in ("AI", "科技", "人工智能", "数码")):
        return "AI 工具"
    if any(k in cat for k in ("美食", "餐饮", "烘焙")):
        return "美食探店"
    if any(k in cat for k in ("教育", "学习", "知识")):
        return "知识分享"
    if any(k in cat for k in ("财经", "金融", "投资")):
        return "财经干货"
    return "干货分享"


def _build_titles(subject, series):
    subject = (subject or "").strip() or "这个工具"
    # 品牌名含空格时，用第一个词做模板主语（如 DeepSeek Harness → DeepSeek）
    short = subject.split()[0] if " " in subject else subject
    cands = [
        subject,                      # 品牌/主题名本身（如「DeepSeek Harness」）
        f"{short} 到底好在哪",
        f"手把手教你用 {short}",
        f"一文看懂 {short}",
        f"{short} 体验分享",
        f"聊聊 {short}",
        f"{series}｜{short}",
    ]
    ok = [c for c in cands if _measure(c) <= MAX_TITLE]
    if not ok:
        ok = [short[:MAX_TITLE]] or [subject[:MAX_TITLE]]
    return ok


def build_social_post(theme):
    """根据归一化主题生成文案。

    theme 字段：
      topic   主标题/主题（用于文档标题）
      subject 用于标题的短主体（默认取 brand 或 topic）
      category 分类（用于推导栏目与话题标签）
      hook    一句话导语（封面副标题/产品 slogan）
      points  list[str] 关键要点（页面标题或功能标题，最多取 4 条）
      closing 收尾金句（末页 summary）
      tags    list[str] 话题标签（缺省用 [栏目, subject]）
    返回 dict：platform / title / title_len / alt_titles / body / generated_at
    """
    subject = theme.get("subject") or theme.get("topic") or "这个工具"
    series = _series(theme.get("category", ""))
    titles = _build_titles(subject, series)
    random.shuffle(titles)
    title = titles[0]
    alts = titles[1:3]

    hook = (theme.get("hook") or "").strip() or f"最近在了解 {subject}，整理了一版图文笔记。"
    points = [p for p in (theme.get("points") or []) if p][:4]
    closing = (theme.get("closing") or "").strip() or "图文已整理好，拿走不谢。"

    lines = [hook, ""]
    for p in points:
        lines.append(f"▸ {p}")
    if points:
        lines.append("")
    lines.append(closing)
    lines.append("")
    tags = theme.get("tags") or [series, subject]
    tags = [t for t in tags if t][:3]
    lines.append(" ".join(f"#{t}" for t in tags))
    body = "\n".join(lines)

    return {
        "platform": "小红书",
        "title": title,
        "title_len": _measure(title),
        "alt_titles": alts,
        "body": body,
        "generated_at": datetime.date.today().isoformat(),
    }


def write_social_post(post, out_dir):
    """把文案写成 <out>/social_post.md，返回文件路径。"""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "social_post.md")
    blocks = []
    blocks.append("# 小红书发布文案（随图附赠）\n")
    blocks.append(f"> 标题（{post['title_len']} 字，< 20）：**{post['title']}**\n")
    if post["alt_titles"]:
        blocks.append("\n备选标题（挑一个顺眼的用）：")
        for i, t in enumerate(post["alt_titles"], 1):
            blocks.append(f"{i}. {t}（{_measure(t)} 字）")
    blocks.append("\n---\n")
    blocks.append("**正文：**\n")
    blocks.append(post["body"])
    blocks.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    return path


if __name__ == "__main__":
    # 简单自测
    demo = build_social_post({
        "topic": "DeepSeek Harness 发布解读",
        "subject": "DeepSeek Harness",
        "category": "AI/科技",
        "hook": "DeepSeek 首款 Agent 框架，把「一切皆插件」开源给你。",
        "points": ["核心设计：一切皆插件", "四种运行模式，按需切换",
                    "它都能帮你干什么", "为什么这件事值得关注"],
        "closing": "对开发者：多了一个自由、可改、不锁死的新选择。",
        "tags": ["AI 趋势观察", "DeepSeek Harness", "AI工具"],
    })
    print("标题：", demo["title"], demo["title_len"])
    print("备选：", demo["alt_titles"])
    print(demo["body"])
