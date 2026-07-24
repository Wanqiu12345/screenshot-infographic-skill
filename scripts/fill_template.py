#!/usr/bin/env python
"""读取 config.json，拼装 items/steps，嵌入图片(base64)，填充模板，输出 HTML。
用法: python fill_template.py <config.json> <out.html>

config 字段见 references/design_notes.md。type = "overview" | "detail"。
"""
import sys, os, json, base64, mimetypes

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(os.path.dirname(HERE), "templates")

ICONS = {
    "chat": '<path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.6-.8L3 21l1.9-5.7A8.4 8.4 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 12v6M9 15h6"/>',
    "tree": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><path d="M14 7h4a2 2 0 0 1 2 2v2M7 14v2a2 2 0 0 0 2 2h2"/>',
    "palette": '<circle cx="13.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="10.5" r="2.5"/><circle cx="8.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="12.5" r="2.5"/><path d="M12 2a10 10 0 1 0 0 20 2 2 0 0 0 2-2 2 2 0 0 1 2-2h2a4 4 0 0 0 4-4 10 10 0 0 0-10-10z"/>',
    "plus": '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5z"/><path d="M2 12l10 5 10-5M2 17l10 5 10-5"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 7 19.4a1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H1a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 7a1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V1a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.2 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H23a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    "bolt": '<path d="M13 2 3 14h7l-1 8 10-12h-7z"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    # 纯文案模式补充语义图标
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "money": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/>',
    "code": '<path d="m8 6-6 6 6 6M16 6l6 6-6 6"/>',
    "speed": '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><path d="m12 12 4-3"/>',
    "scale": '<path d="M12 3v18M5 7h14M5 7l-3 6h6zM19 7l-3 6h6z"/>',
    "book": '<path d="M4 4h11a2 2 0 0 1 2 2v14a1 1 0 0 0-1-1H4z"/><path d="M9 4v14"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10c1 1 1 2 1 3h6c0-1 0-2 1-3a6 6 0 0 0-4-10z"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8M21 7h-5M21 7v5"/>',
    "gift": '<rect x="3" y="8" width="18" height="4"/><path d="M5 12v8h14v-8M12 8v12M12 8S9 3 6 5s1 3 6 3zM12 8s3-5 6-3-1 3-6 3z"/>',
    "warning": '<path d="M12 3 2 20h20z"/><path d="M12 9v5M12 17h.01"/>',
    "quote2": '<path d="M7 7h4v4H7zM7 11c0 3 2 5 5 5M14 7h4v4h-4zM14 11c0 3 2 5 5 5"/>',
}

# 合并纯文案补充图标
ICONS.update({
    "clock": ICONS["clock"], "target": ICONS["target"], "money": ICONS["money"],
    "code": ICONS["code"], "speed": ICONS["speed"], "scale": ICONS["scale"],
    "book": ICONS["book"], "bulb": ICONS["bulb"], "check": ICONS["check"],
    "trend": ICONS["trend"], "gift": ICONS["gift"], "warning": ICONS["warning"],
})


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgba(h, a):
    r, g, b = hex_to_rgb(h)
    return f"rgba({r},{g},{b},{a})"


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:{mime};base64,{b64}"


def icon_svg(key):
    p = ICONS.get(key, ICONS["star"])
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


def build_footer(f):
    if not f:
        return ""
    parts = []
    if f.get("brand"):
        parts.append(f'<span>{f["brand"]}</span>')
    if f.get("url"):
        parts.append(f'<span>· {f["url"]}</span>')
    if f.get("page"):
        parts.append(f'<span class="pg">{f["page"]}</span>')
    return '<div class="footer">' + " ".join(parts) + "</div>"


def common_repl(html, cfg):
    pal = cfg["palette"]
    radius = str(cfg.get("radius", 18))
    accent = pal["accent"]
    accent_soft = pal.get("accent_soft") or rgba(accent, 0.13)
    secondary = pal.get("secondary") or accent
    secondary_soft = pal.get("secondary_soft") or rgba(secondary, 0.14)
    accent2 = pal.get("accent2") or secondary
    accent2_soft = pal.get("accent2_soft") or rgba(accent2, 0.12)
    line = pal.get("line") or rgba(pal.get("text_sub", "#000000"), 0.20)
    html = html.replace("__PAGE_BG__", pal["page_bg"])
    html = html.replace("__CARD_BG__", pal["card_bg"])
    html = html.replace("__ACCENT__", accent)
    html = html.replace("__ACCENT_SOFT__", accent_soft)
    html = html.replace("__SECONDARY__", secondary)
    html = html.replace("__SECONDARY_SOFT__", secondary_soft)
    html = html.replace("__ACCENT2__", accent2)
    html = html.replace("__ACCENT2_SOFT__", accent2_soft)
    html = html.replace("__TEXT_MAIN__", pal["text_main"])
    html = html.replace("__TEXT_SUB__", pal["text_sub"])
    html = html.replace("__LINE__", line)
    html = html.replace("__RADIUS__", radius)
    return html


def build_logo(cfg):
    # Priority: logo_image (auto-extracted or user-provided) > logo_icon (SVG) > logo_text (initial)
    if cfg.get("logo_image") and os.path.exists(cfg["logo_image"]):
        return f'<div class="logo"><img src="{data_uri(cfg["logo_image"])}" alt="logo"></div>'
    if cfg.get("logo_icon") and cfg["logo_icon"] in ICONS:
        return f'<div class="logo">{icon_svg(cfg["logo_icon"])}</div>'
    if cfg.get("logo_text"):
        txt = cfg["logo_text"].strip()
        # 最多 1 个汉字或 2 个英文字母，否则只取首字/首字母
        if len(txt) > 2:
            txt = txt[0]
        return f'<div class="logo"><span class="logo-text">{txt}</span></div>'
    return f'<div class="logo">{icon_svg("star")}</div>'


def build_overview(cfg):
    html = open(os.path.join(TPL, "overview.html"), encoding="utf-8").read()
    html = common_repl(html, cfg)
    pal = cfg["palette"]
    html = html.replace("__LOGO__", build_logo(cfg))
    html = html.replace("__BRAND__", cfg.get("brand", ""))
    html = html.replace("__SUBTITLE__", cfg.get("subtitle", ""))
    html = html.replace("__BADGE__", cfg.get("badge", ""))
    html = html.replace("__URLBAR__", cfg.get("urlbar", ""))
    html = html.replace("__SCREENSHOT__", data_uri(cfg["screenshot"]))
    items = []
    feat = pal.get("feature", [pal["accent"]] * len(cfg["items"]))
    feat_soft = pal.get("feature_soft", [rgba(pal["accent"], 0.13)] * len(cfg["items"]))
    for i, it in enumerate(cfg["items"]):
        c = feat[i] if i < len(feat) else pal["accent"]
        cs = feat_soft[i] if i < len(feat_soft) else rgba(c, 0.13)
        items.append(
            f'<div class="item" style="--c:{c};--cs:{cs}">'
            f'<div class="ic">{icon_svg(it.get("icon","star"))}</div>'
            f'<div class="itxt"><h3>{it["title"]}</h3><p>{it["desc"]}</p></div>'
            f'<div class="num">{it["num"]}</div></div>'
        )
    html = html.replace("__ITEMS__", "\n".join(items))
    html = html.replace("__FOOTER__", build_footer(cfg.get("footer")))
    return html


def build_tip(cfg):
    tip = cfg.get("tip") or cfg.get("note")
    if not tip:
        return ""
    title = tip.get("title", "小提示")
    body = tip.get("text", "")
    if not body:
        return ""
    return (
        f'<div class="tip"><div class="tip-icon">!</div>'
        f'<div class="tip-txt"><h4>{title}</h4><p>{body}</p></div></div>'
    )


def build_detail(cfg):
    html = open(os.path.join(TPL, "detail.html"), encoding="utf-8").read()
    html = common_repl(html, cfg)
    # 可选：用功能色覆盖本图强调色，使细节图与概览卡片呼应
    fc = cfg.get("feature_color")
    if fc:
        html = html.replace("__ACCENT__", fc)
        html = html.replace("__ACCENT_SOFT__", rgba(fc, 0.13))
    html = html.replace("__TAG__", cfg.get("tag", ""))
    html = html.replace("__PAGEINFO__", cfg.get("pageinfo", ""))
    html = html.replace("__TITLE__", cfg.get("title", ""))
    html = html.replace("__LEAD__", cfg.get("lead", ""))
    if cfg.get("mode") == "full":
        html = html.replace("__CROP__", data_uri(cfg["screenshot"]))
        m = cfg.get("marker", {})
        marker = (f'<div class="marker" style="left:{m.get("x", 50)}%;top:{m.get("y", 50)}%;'
                  f'width:{m.get("r", 60)}px;height:{m.get("r", 60)}px;"></div>')
    else:
        html = html.replace("__CROP__", data_uri(cfg["crop"]))
        marker = ""
    html = html.replace("__MARKER__", marker)
    steps = []
    for i, st in enumerate(cfg.get("steps", []), 1):
        n = st.get("n", i)
        steps.append(
            f'<div class="step-row"><div class="sn">{n}</div>'
            f'<div class="stx"><h3>{st["title"]}</h3><p>{st["desc"]}</p></div></div>'
        )
    html = html.replace("__STEPS__", "\n".join(steps))
    val = cfg.get("value")
    if val:
        value_html = (f'<div class="value"><h4>{val.get("title", "核心价值")}</h4>'
                      f'<p>{val.get("text", "")}</p></div>')
    else:
        value_html = ""
    html = html.replace("__VALUE__", value_html)
    html = html.replace("__TIP__", build_tip(cfg))
    html = html.replace("__FOOTER__", build_footer(cfg.get("footer")))
    return html


# ---------- 纯文案模式：内容页 layout 渲染 ----------
def _tl_item(it):
    return (f'<div class="tl-item"><div class="tl-date">{it.get("date","")}</div>'
            f'<div class="tl-title">{it.get("title","")}</div>'
            f'<div class="tl-desc">{it.get("desc","")}</div></div>')


def build_body(layout, cfg):
    pal = cfg.get("palette", {})
    feat = pal.get("feature", [pal.get("accent", "#888")])
    feat_soft = pal.get("feature_soft", [rgba(pal.get("accent", "#888"), 0.13)])
    if layout == "timeline":
        items = "".join(_tl_item(i) for i in cfg.get("items", []))
        return f'<div class="tl card" style="padding:14px 20px 14px 44px">{items}</div>'
    if layout == "grid_cards":
        cells = []
        for i, it in enumerate(cfg.get("items", [])):
            c = feat[i % len(feat)]
            cs = feat_soft[i % len(feat_soft)]
            cells.append(
                f'<div class="gc" style="border-top-color:{c}">'
                f'<div class="ic" style="background:{cs};color:{c}">{icon_svg(it.get("icon","star"))}</div>'
                f'<h3>{it.get("title","")}</h3><p>{it.get("desc","")}</p></div>')
        return f'<div class="grid2">{ "".join(cells) }</div>'
    if layout == "big_number":
        return (f'<div class="bignum card"><div class="n">{cfg.get("number","")}</div>'
                f'<div class="l">{cfg.get("label","")}</div>'
                f'<div class="s">{cfg.get("desc","")}</div></div>')
    if layout == "price_table":
        rows = "".join(
            f'<tr><td>{r.get("plan","")}</td><td>{r.get("price","")}</td><td>{r.get("note","")}</td></tr>'
            for r in cfg.get("rows", []))
        return (f'<div class="card" style="padding:16px 22px"><table class="pt">'
                f'<thead><tr><th>档位</th><th>价格</th><th>说明</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div>')
    if layout == "metrics":
        rows = "".join(
            f'<div class="metric"><span class="mv">{m.get("value","")}</span>'
            f'<div><div class="mn">{m.get("name","")}</div>'
            f'<div class="md">{m.get("desc","")}</div></div></div>'
            for m in cfg.get("metrics", []))
        return f'<div class="card" style="padding:8px 24px">{rows}</div>'
    if layout == "quote":
        q = cfg.get("quote", "")
        return (f'<div class="card" style="padding:40px 30px"><div class="quote">'
                f'<span class="mark">“</span>{q}<span class="mark">”</span></div></div>')
    if layout == "definition":
        return (f'<div class="def card" style="padding:30px">'
                f'<div class="term">{cfg.get("term","")}</div>'
                f'<div class="exp">{cfg.get("explanation","")}</div></div>')
    if layout == "spec_list":
        rows = "".join(
            f'<div class="spec-row"><span class="spec-label">{r.get("label","")}</span>'
            f'<div class="spec-val">{r.get("value","")}</div></div>'
            for r in cfg.get("rows", []))
        return f'<div class="card" style="padding:12px 28px">{rows}</div>'
    if layout == "summary":
        tags = " ".join(f'<span class="tag">#{t}</span>' for t in cfg.get("tags", []))
        return (f'<div class="card" style="padding:34px;text-align:center">'
                f'<div class="quote" style="padding:6px"><span class="mark">“</span>'
                f'{cfg.get("statement","")}<span class="mark">”</span></div>'
                f'<div style="margin-top:20px;font-size:27px;color:var(--accent);font-weight:700">'
                f'{cfg.get("cta","")}</div>'
                f'<div style="margin-top:16px;color:var(--text_sub);font-size:24px">{tags}</div></div>')
    # 未知 layout 回退 grid_cards
    return build_body("grid_cards", cfg)


def build_text_cover(cfg):
    html = open(os.path.join(TPL, "text_cover.html"), encoding="utf-8").read()
    html = common_repl(html, cfg)
    cov = cfg.get("cover", {})
    hero = cfg.get("_cover_img")
    hero_html = (f'<img src="{data_uri(hero)}">' if hero and os.path.exists(hero)
                 else '<div style="color:var(--text_sub);font-size:28px">（未生成主视觉图）</div>')
    html = html.replace("__KICKER__", cov.get("kicker", ""))
    html = html.replace("__TITLE__", cov.get("title", cfg.get("title", "")))
    html = html.replace("__SUBTITLE__", cov.get("subtitle", ""))
    html = html.replace("__HERO__", hero_html)
    html = html.replace("__SUMMARY__", cov.get("summary", ""))
    html = html.replace("__FOOTER__", build_footer(cfg.get("footer")))
    return html


def build_cover(cfg):
    """极简传播封面：栏目小字 + 大图标(圆角方块框) + 超大品牌名(自适应缩放) + slogan + 可选 desc。
    封面不编号、背景跟随主题色、唯一色彩爆点=图标/品牌色，文字中性克制。
    """
    html = open(os.path.join(TPL, "cover.html"), encoding="utf-8").read()
    html = common_repl(html, cfg)
    # 图标：图片优先；否则用首字艺术字 logo（渐变圆角方块）
    icon_path = cfg.get("icon_image")
    if icon_path and os.path.exists(icon_path):
        icon_html = f'<img src="{data_uri(icon_path)}">'
    else:
        txt = (cfg.get("icon_text") or (cfg.get("brand_main") or " ")[0]).strip() or "·"
        icon_html = f'<span class="icon-text">{txt}</span>'
    html = html.replace("__ICON__", icon_html)
    html = html.replace("__KICKER__", cfg.get("series", ""))
    html = html.replace("__BRAND_MAIN__", cfg.get("brand_main", ""))
    sub = cfg.get("brand_sub")
    html = html.replace("__BRAND_SUB__", f'<div class="brand-sub">{sub}</div>' if sub else "")
    html = html.replace("__SLOGAN__", cfg.get("slogan", ""))
    desc = cfg.get("desc")
    html = html.replace("__DESC__", f'<div class="desc">{desc}</div>' if desc else "")
    html = html.replace("__WATERMARK__", cfg.get("watermark", ""))
    return html


def build_text_section(cfg):
    html = open(os.path.join(TPL, "text_section.html"), encoding="utf-8").read()
    html = common_repl(html, cfg)
    hero = cfg.get("_img")
    hero_html = (f'<img src="{data_uri(hero)}">' if hero and os.path.exists(hero)
                 else '<div style="color:var(--text_sub);font-size:26px">（未生成插画）</div>')
    labels = cfg.get("top_label") or []
    kicker = " / ".join(labels) if labels else cfg.get("kicker", "")
    html = html.replace("__KICKER__", kicker)
    html = html.replace("__PAGENO__", cfg.get("pageinfo", ""))
    html = html.replace("__PAGETITLE__", cfg.get("page_title", cfg.get("title", "")))
    html = html.replace("__LEAD__", cfg.get("lead", ""))
    html = html.replace("__HERO__", hero_html)
    html = html.replace("__BODY__", build_body(cfg.get("layout", "grid_cards"), cfg))
    html = html.replace("__SUMMARY__", cfg.get("summary", ""))
    html = html.replace("__FOOTER__", build_footer(cfg.get("footer")))
    return html


def main():
    if len(sys.argv) < 3:
        print("usage: fill_template.py <config.json> <out.html>")
        sys.exit(1)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    kind = cfg.get("type", "overview")
    if kind == "overview":
        html = build_overview(cfg)
    elif kind == "detail":
        html = build_detail(cfg)
    elif kind == "text_cover":
        html = build_text_cover(cfg)
    elif kind == "cover":
        html = build_cover(cfg)
    elif kind == "text_section":
        html = build_text_section(cfg)
    else:
        html = build_overview(cfg)
    open(sys.argv[2], "w", encoding="utf-8").write(html)
    print(f"OK: {sys.argv[2]} ({kind})")


if __name__ == "__main__":
    main()
