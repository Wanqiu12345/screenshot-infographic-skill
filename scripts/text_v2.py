#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""text_v2 —— 纯文案模式 × 晚秋简约风（v2 表意型排版引擎）渲染器。

由 stylelab_20260830/make_v2.py 原型移植进 skill（2026-09-01），
article_26（1200 agent 事件）/ article_27（Workflow vs Agent）即该引擎产出。

设计原则（v2 表意型排版定稿结论）：
1. 视觉元素必须编码内容，不做纯装饰（点阵网络=群体、竖链=因果、纵向时间线=演进）。
2. 每页 flex 撑满 1080×1440，不允许底部大片真空。
3. 字号阶梯固定，正文层级清晰；主色 #1A3A6B + 哑光金 #B08D45，无彩虹六色。
4. 无 Agnes 3D 插画、零文生图依赖，离线可跑。
5. 无头渲染必须传最小环境变量（SAFE_ENV）：宿主注入的 NODE_OPTIONS 等变量
   会让 Edge 无头模式秒退。

用法（CLI，与 run_text_tutorial.py --style v2 配套）：
    python scripts/text_v2.py <v2_config.json> [--out 输出目录] [--only 00_xxx ...]

v2_config.json 结构（见 examples/wf_agent_v2.json）：
    slug / footer_brand(可选，默认 晚秋AI日记) /
    pages[{type: cover|stats|chain|timeline|compare|vs|takeaway, name, ...版式字段}]
"""
import json
import math
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from render import find_browser  # noqa: E402  复用浏览器查找逻辑

# Edge 无头截图必须跑在「最小环境」下
SAFE_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    "TEMP": os.environ.get("TEMP", ""),
    "TMP": os.environ.get("TMP", ""),
    "USERPROFILE": os.environ.get("USERPROFILE", ""),
}

TOKENS = {
    "bg": "#FBFAF8", "ink": "#12203C", "ink2": "#3E4759", "ink_soft": "#6C7686",
    "line": "#DED9CE", "line2": "#EAE5DA",
    "brand": "#1A3A6B", "brand2": "#2E5490", "brand_tint": "#E9EEF6",
    "gold": "#B08D45", "gold2": "#C9A961", "gold_tint": "#F5EFE1",
    "faint": "#A6A096",
}

# 页脚品牌名（render_cfg 里按 cfg.footer_brand 覆盖）
FBRAND = "晚秋AI日记"

CSS = """
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:__BG__;}
.page{
  width:1080px;height:1440px;background:__BG__;color:__INK__;
  padding:72px 84px 52px;display:flex;flex-direction:column;position:relative;overflow:hidden;
  font-family:'PingFang SC','HarmonyOS Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif;
  -webkit-font-smoothing:antialiased;
}

/* ---- 页眉 ---- */
.hd{display:flex;justify-content:space-between;align-items:baseline;
  font-size:17px;letter-spacing:5px;font-weight:600;flex:0 0 auto;}
.hd .tag{color:__GOLD__;}
.hd .pg{color:__FAINT__;font-weight:500;letter-spacing:3px;}

/* ---- 标题 / 导语（固定高度，不伸缩） ---- */
.h2{font-size:58px;font-weight:800;line-height:1.18;margin-top:34px;letter-spacing:-2px;flex:0 0 auto;}
.lead{font-size:24px;color:__INK_SOFT__;line-height:1.6;margin-top:14px;max-width:880px;flex:0 0 auto;}

/* ---- body：占据 header 与 footer 之间的全部剩余空间 ---- */
.body{margin-top:36px;flex:1;min-height:0;display:flex;flex-direction:column;}
.body.fill{justify-content:space-between;}

/* ---- 页脚：永远吸在底部 ---- */
.foot{margin-top:auto;padding-top:18px;display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid __LINE__;font-size:16px;color:__FAINT__;letter-spacing:2px;flex:0 0 auto;}

/* ================= 封面 ================= */
.cv{width:1080px;height:1440px;background:__BG__;color:__INK__;position:relative;overflow:hidden;
  padding:72px 84px 58px;display:flex;flex-direction:column;
  font-family:'PingFang SC','HarmonyOS Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif;}
.cv .cl{display:flex;justify-content:space-between;align-items:baseline;
  font-size:17px;letter-spacing:6px;font-weight:600;color:__FAINT__;flex:0 0 auto;}
.cv .kick{font-size:19px;letter-spacing:5px;color:__GOLD__;font-weight:600;margin-top:48px;flex:0 0 auto;}
.cv .tt{font-size:94px;font-weight:800;line-height:1.1;letter-spacing:-4px;margin-top:18px;flex:0 0 auto;}
.cv .net{margin-top:30px;flex:0 0 auto;}
.cv .mid{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;}
.cv .sub{font-size:29px;color:__INK2__;font-weight:600;line-height:1.5;margin-top:30px;
  letter-spacing:-.5px;max-width:860px;flex:0 0 auto;}
.cv .sum{display:flex;margin-top:6px;flex:0 0 auto;}
.cv .sum .sc{flex:1;padding:28px 32px 26px;border:1px solid __LINE__;background:#FFFFFF;}
.cv .sum .sc+.sc{border-left:none;}
.cv .sum .sc .h{font-size:16px;letter-spacing:4px;font-weight:700;color:__GOLD__;}
.cv .sum .sc .t{font-size:27px;font-weight:800;margin-top:12px;letter-spacing:-.5px;}
.cv .sum .sc .d{font-size:19px;color:__INK_SOFT__;margin-top:8px;line-height:1.55;}
.cv .rule{width:88px;height:4px;background:__GOLD__;margin:32px 0 26px;flex:0 0 auto;}
.cv .bot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
  font-size:17px;letter-spacing:3px;color:__FAINT__;border-top:1px solid __LINE__;padding-top:20px;flex:0 0 auto;}

/* ================= 数据页 stats：三项均分撑满 ================= */
.st{flex:1;min-height:0;display:flex;align-items:center;gap:34px;padding:0 8px;
  border-top:1px solid __LINE__;}
.st:last-child{border-bottom:1px solid __LINE__;}
.st .big{font-size:138px;font-weight:800;color:__BRAND__;line-height:.88;
  letter-spacing:-6px;min-width:420px;flex:0 0 auto;}
.st .unit{font-size:36px;font-weight:700;color:__BRAND2__;letter-spacing:-1px;margin-left:6px;}
.st .side{flex:1;min-width:0;}
.st .lab{font-size:33px;font-weight:700;line-height:1.3;letter-spacing:-.5px;}
.st .note{font-size:22px;color:__INK_SOFT__;line-height:1.6;margin-top:10px;}

/* ================= 因果链 chain：五步均分撑满 ================= */
.chain-wrap{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:space-between;}
.ch{flex:1;min-height:0;display:flex;gap:26px;align-items:center;}
.ch .rail{position:relative;width:26px;height:100%;flex:0 0 auto;}
.ch .rail .ln{position:absolute;left:12px;top:0;bottom:0;width:1px;background:__LINE__;}
.ch .rail .dot{position:absolute;left:0;width:24px;height:24px;border-radius:50%;
  background:__BRAND__;top:50%;margin-top:-12px;}
.ch .rail .dot.last{background:__GOLD__;width:28px;height:28px;left:-2px;margin-top:-14px;}
.ch .cnt{flex:1;min-width:0;}
.ch .t{font-size:31px;font-weight:700;line-height:1.3;letter-spacing:-.5px;}
.ch .q{font-size:21px;color:__INK2__;line-height:1.55;margin-top:8px;
  padding-left:18px;border-left:3px solid __GOLD2__;font-style:italic;}
.ch .d{font-size:22px;color:__INK_SOFT__;line-height:1.55;margin-top:8px;}
.ch .d2{font-size:19px;color:__BRAND2__;font-weight:600;margin-top:9px;letter-spacing:.5px;}

/* ================= 时间线 timeline：纵向节点均分撑满 ================= */
.tl{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:space-between;}
.tl .node{flex:1;min-height:0;display:flex;gap:26px;align-items:center;}
.tl .node .rail{position:relative;width:26px;height:100%;flex:0 0 auto;}
.tl .node .rail .ln{position:absolute;left:12px;top:0;bottom:0;width:1px;background:__LINE__;}
.tl .node .rail .dot{position:absolute;left:0;width:24px;height:24px;border-radius:50%;background:__BRAND__;top:50%;margin-top:-12px;}
.tl .node .rail .dot.key{width:28px;height:28px;margin-top:-14px;background:__GOLD__;}
.tl .node .card{flex:1;min-width:0;}
.tl .node .dt{font-size:19px;font-weight:700;color:__GOLD__;letter-spacing:2px;}
.tl .node .tt{font-size:30px;font-weight:700;line-height:1.3;letter-spacing:-.5px;margin-top:6px;}
.tl .node .ds{font-size:22px;color:__INK_SOFT__;line-height:1.6;margin-top:8px;}

/* ================= 对比 compare：两列均分撑满（主句+副句） ================= */
.cp{display:flex;flex:1;min-height:0;}
.cp .col{display:flex;flex-direction:column;padding-top:6px;}
.cp .col.a{width:400px;flex:0 0 auto;padding-right:36px;border-right:1px solid __LINE__;}
.cp .col.b{flex:1;min-width:0;padding-left:36px;}
.cp .lb{font-size:17px;letter-spacing:5px;font-weight:700;color:__FAINT__;
  padding-bottom:18px;border-bottom:2px solid __LINE__;flex:0 0 auto;}
.cp .col.b .lb{color:__BRAND__;border-bottom-color:__GOLD__;}
.cp .col ul{flex:1;display:flex;flex-direction:column;justify-content:space-between;margin-top:18px;}
.cp li{list-style:none;display:flex;flex-direction:column;justify-content:center;min-height:0;}
.cp li .m{font-size:25px;line-height:1.4;color:__INK2__;}
.cp li .s{font-size:19px;color:__FAINT__;line-height:1.5;margin-top:7px;}
.cp .col.b li .m{color:__INK__;font-weight:700;}
.cp .col.b li .s{color:__INK_SOFT__;}
.cp li em{font-style:normal;color:__BRAND__;font-weight:800;}

/* ================= 三列对比表 vs：维度 × 左 × 右 ================= */
.vs{flex:1;min-height:0;display:flex;flex-direction:column;}
.vs .hr{flex:0 0 auto;display:flex;border-bottom:2px solid __INK__;padding-bottom:14px;}
.vs .hr .c{font-size:17px;letter-spacing:4px;font-weight:700;color:__FAINT__;
  padding-left:26px;display:flex;align-items:flex-end;}
.vs .dim{width:186px;flex:0 0 auto;}
.vs .wf{width:330px;flex:0 0 auto;}
.vs .ag{flex:1;min-width:0;}
.vs .row{flex:1;min-height:0;display:flex;border-bottom:1px solid __LINE__;}
.vs .row:last-child{border-bottom:2px solid __INK__;}
.vs .row .dim{display:flex;align-items:center;font-size:25px;font-weight:800;letter-spacing:1px;line-height:1.3;}
.vs .row .wf,.vs .row .ag{display:flex;flex-direction:column;justify-content:center;padding:0 26px;
  border-left:1px solid __LINE2__;}
.vs .m{font-size:23px;font-weight:600;line-height:1.35;}
.vs .s{font-size:18px;color:__INK_SOFT__;line-height:1.45;margin-top:6px;}
.vs .row .ag .m{color:__BRAND__;}
.vs .hr .c.wf{color:__GOLD__;}
.vs .hr .c.ag{color:__BRAND__;}

/* ================= 结论 takeaway ================= */
.tk{flex:1;display:flex;flex-direction:column;min-height:0;}
.tk .hl{font-size:44px;font-weight:800;line-height:1.42;color:__BRAND__;
  letter-spacing:-1.5px;padding-bottom:30px;border-bottom:2px solid __GOLD__;flex:0 0 auto;}
.tk .ps{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:space-evenly;}
.tk p{font-size:26px;line-height:1.78;color:__INK2__;}
.tk p b{color:__INK__;font-weight:700;}
.tk .lim{margin-top:26px;padding:24px 28px;background:__BRAND_TINT__;border-radius:2px;flex:0 0 auto;}
.tk .lim .h{font-size:17px;letter-spacing:4px;font-weight:700;color:__BRAND__;}
.tk .lim p{font-size:22px;line-height:1.62;color:__INK2__;margin-top:10px;}

/* ================= 收尾条 ================= */
.eb{margin-top:26px;background:__BRAND__;color:#fff;border-radius:2px;
  padding:28px 36px;font-size:24px;line-height:1.6;font-weight:600;flex:0 0 auto;}
"""


def _css(tpl):
    for k, v in TOKENS.items():
        tpl = tpl.replace("__%s__" % k.upper(), v)
    return tpl


# ==========================================================
# 表意型 SVG：点阵网络
# ==========================================================
def agent_network(cols=12, rows=6, w=912, h=330, hub_at=(5.5, 2.5)):
    gx0, gy0, gx1, gy1 = 30, 26, w - 30, h - 26
    dx = (gx1 - gx0) / (cols - 1.0)
    dy = (gy1 - gy0) / (rows - 1.0)

    def pos(i, j):
        return (gx0 + i * dx, gy0 + j * dy)

    paths = [
        [(5, 3), (4, 3), (3, 4), (2, 4), (1, 5), (0, 5)],
        [(6, 2), (7, 2), (8, 1), (9, 1), (10, 0), (11, 0)],
        [(5, 2), (4, 1), (3, 1), (2, 0), (1, 0)],
        [(6, 3), (7, 4), (8, 4), (9, 5), (10, 5), (11, 5)],
        [(5, 4), (5, 5), (6, 1), (6, 0)],
    ]
    linked = set()
    for p in paths:
        for c in p:
            linked.add(c)

    hub = (gx0 + hub_at[0] * dx, gy0 + hub_at[1] * dy)
    s = ['<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (w, h, w, h)]

    for i in range(cols):
        for j in range(rows):
            if (i, j) in linked:
                continue
            x, y = pos(i, j)
            s.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" opacity="0.26"/>' % (x, y, TOKENS["brand"]))

    for p in paths:
        pts = [hub] + [pos(i, j) for i, j in p]
        d = " ".join("%.1f,%.1f" % (x, y) for x, y in pts)
        s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.6" '
                 'stroke-linejoin="round" stroke-opacity="0.92"/>' % (d, TOKENS["gold2"]))

    for (i, j) in sorted(linked):
        x, y = pos(i, j)
        s.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s"/>' % (x, y, TOKENS["brand"]))

    s.append('<circle cx="%.1f" cy="%.1f" r="21" fill="%s"/>' % (hub[0], hub[1], TOKENS["brand"]))
    s.append('<circle cx="%.1f" cy="%.1f" r="33" fill="none" stroke="%s" '
             'stroke-width="1.4" opacity="0.5"/>' % (hub[0], hub[1], TOKENS["gold"]))

    s.append("</svg>")
    return "".join(s)


# ==========================================================
# 表意型 SVG：固定路径 vs 自主循环
#   左：一串单向方块 —— 路径在写代码时就定死了
#   右：中心模型 + 环形回路 —— 下一步由模型自己决定
# ==========================================================
def flow_vs_loop(w=912, h=380):
    T = TOKENS
    mid = w / 2.0
    rx = mid + 40                      # 右栏起点
    cx, cy, R = mid + (mid - 40) / 2.0 + 10, 190, 92

    s = ['<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">'
         % (w, h, w, h)]
    s.append('<defs>'
             '<marker id="aw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" '
             'markerHeight="6.5" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
             '<marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
             '</defs>' % (T["brand2"], T["gold2"]))

    s.append('<g font-family="PingFang SC,HarmonyOS Sans SC,Microsoft YaHei,sans-serif">')

    # 栏目标题
    s.append('<text x="0" y="24" font-size="17" letter-spacing="5" font-weight="700" '
             'fill="%s">WORKFLOW</text>' % T["gold"])
    s.append('<text x="%.0f" y="24" font-size="17" letter-spacing="5" font-weight="700" '
             'fill="%s">AGENT</text>' % (rx, T["gold"]))
    s.append('<line x1="%.1f" y1="38" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>'
             % (mid, mid, h - 44, T["line"]))

    # ---- 左：固定路径 ----
    bw, bh, by = 58, 60, 152
    xs = [0, 98, 196, 294, 392]
    for i, x in enumerate(xs):
        last = (i == len(xs) - 1)
        s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="%s" '
                 'stroke="%s" stroke-width="1.8"/>'
                 % (x, by, bw, bh, T["gold"] if last else T["brand_tint"],
                    T["gold"] if last else T["brand2"]))
        if not last:
            y = by + bh / 2.0
            s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" '
                     'stroke-width="2" marker-end="url(#aw)"/>'
                     % (x + bw + 6, y, xs[i + 1] - 8, y, T["brand2"]))
    s.append('<text x="0" y="%d" font-size="22" fill="%s">步骤写死在代码里</text>'
             % (h - 30, T["ink_soft"]))

    # ---- 右：自主循环 ----
    def pt(a, r=None):
        r = R if r is None else r
        t = math.radians(a)
        return (cx + r * math.cos(t), cy + r * math.sin(t))

    for a1, a2 in [(6, 74), (96, 164), (186, 254), (276, 344)]:
        x1, y1 = pt(a1)
        x2, y2 = pt(a2)
        s.append('<path d="M%.1f,%.1f A%.1f,%.1f 0 0 1 %.1f,%.1f" fill="none" '
                 'stroke="%s" stroke-width="2.6" marker-end="url(#ag)"/>'
                 % (x1, y1, R, R, x2, y2, T["gold2"]))

    for a in (86, 176, 266, 356):        # 环上的工具节点
        x, y = pt(a)
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="1" opacity="0.28"/>' % (cx, cy, x, y, T["brand"]))
        s.append('<circle cx="%.1f" cy="%.1f" r="14" fill="%s"/>' % (x, y, T["brand2"]))

    s.append('<circle cx="%.1f" cy="%.1f" r="40" fill="%s"/>' % (cx, cy, T["brand"]))
    s.append('<circle cx="%.1f" cy="%.1f" r="54" fill="none" stroke="%s" '
             'stroke-width="1.4" opacity="0.5"/>' % (cx, cy, T["gold"]))
    s.append('<text x="%.0f" y="%d" font-size="22" fill="%s">下一步由模型自己定</text>'
             % (rx, h - 30, T["ink_soft"]))

    s.append("</g></svg>")
    return "".join(s)


# ==========================================================
# 页面构造器
# ==========================================================
def _page(meta, pg, title, lead, body, fill=True, endbar=None):
    cls = "body fill" if fill else "body"
    eb = ('<div class="eb">%s</div>' % endbar) if endbar else ""
    return ('<div class="page"><div class="hd"><span class="tag">%s</span>'
            '<span class="pg">%s</span></div>'
            '<div class="h2">%s</div><div class="lead">%s</div>'
            '<div class="%s">%s</div>%s'
            '<div class="foot"><span>%s</span><span>第 %s 页</span></div></div>'
            % (meta, pg, title, lead, cls, body, eb, FBRAND, pg))


def p_cover(c, page_index=0, total=5):
    kick = ('<div class="kick">%s</div>' % c["kicker"]) if c.get("kicker") else ""
    tt = "<br>".join(c["title_lines"])
    n = c.get("net", True)
    if n == "flow":
        net = '<div class="net">%s</div>' % flow_vs_loop()
    elif isinstance(n, dict):
        net = '<div class="net">%s</div>' % agent_network(**n)
    elif n:
        net = '<div class="net">%s</div>' % agent_network()
    else:
        net = ""
    sub = ('<div class="sub">%s</div>' % c["subtitle"]) if c.get("subtitle") else ""
    cards = "".join('<div class="sc"><div class="h">%s</div><div class="t">%s</div>'
                    '<div class="d">%s</div></div>' % (x["h"], x["t"], x["d"])
                    for x in c.get("sum", []))
    sum_html = ('<div class="sum">%s</div>' % cards) if cards else ""
    en = "LATE FALL AI DIARY" if FBRAND == "晚秋AI日记" else FBRAND
    return ('<div class="cv"><div class="cl"><span>%s · %s</span><span>%s</span></div>%s'
            '<div class="tt">%s</div>%s<div class="mid">%s</div>%s<div class="rule"></div>'
            '<div class="bot"><span>%s</span><span>第 01 / %02d 页</span></div></div>'
            % (en, FBRAND, c.get("date", ""), kick, tt, sub, net, sum_html,
               c.get("note", ""), total))


def p_stats(p):
    rows = []
    for it in p["items"]:
        rows.append('<div class="st"><div class="big">%s<span class="unit">%s</span></div>'
                    '<div class="side"><div class="lab">%s</div><div class="note">%s</div></div></div>'
                    % (it[0], it[1], it[2], it[3]))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""), "".join(rows), fill=True, endbar=p.get("endbar"))


def p_chain(p):
    n = len(p["steps"])
    rows = []
    for i, s in enumerate(p["steps"]):
        last = " last" if i == n - 1 else ""
        d = ('<div class="d">%s</div>' % s[1]) if len(s) > 1 and s[1] else ""
        d2 = ('<div class="d2">%s</div>' % s[2]) if len(s) > 2 and s[2] else ""
        rows.append('<div class="ch"><div class="rail"><div class="ln"></div>'
                    '<div class="dot%s"></div></div>'
                    '<div class="cnt"><div class="t">%s</div>%s%s</div></div>'
                    % (last, s[0], d, d2))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""),
                 '<div class="chain-wrap">%s</div>' % "".join(rows), fill=True, endbar=p.get("endbar"))


def p_timeline(p):
    nodes = []
    for it in p["nodes"]:
        key = " key" if it.get("key") else ""
        nodes.append('<div class="node"><div class="rail"><div class="ln"></div>'
                     '<div class="dot%s"></div></div>'
                     '<div class="card"><div class="dt">%s</div>'
                     '<div class="tt">%s</div><div class="ds">%s</div></div></div>'
                     % (key, it["dt"], it["tt"], it["ds"]))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""),
                 '<div class="tl">%s</div>' % "".join(nodes),
                 fill=True, endbar=p.get("endbar"))


def _cp_item(x):
    if isinstance(x, dict):
        s = ('<div class="s">%s</div>' % x["s"]) if x.get("s") else ""
        return '<li><div class="m">%s</div>%s</li>' % (x["m"], s)
    return '<li><div class="m">%s</div></li>' % x


def p_compare(p):
    body = ('<div class="cp"><div class="col a"><div class="lb">%s</div><ul>%s</ul></div>'
            '<div class="col b"><div class="lb">%s</div><ul>%s</ul></div></div>'
            % (p["left_label"], "".join(_cp_item(x) for x in p["left_items"]),
               p["right_label"], "".join(_cp_item(x) for x in p["right_items"])))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""), body, fill=True, endbar=p.get("endbar"))


def p_vs(p):
    rows = ['<div class="hr"><div class="dim"></div>'
            '<div class="c wf">%s</div><div class="c ag">%s</div></div>'
            % (p.get("left_label", "WORKFLOW"), p.get("right_label", "AGENT"))]
    for it in p["rows"]:
        rows.append('<div class="row"><div class="dim">%s</div>'
                    '<div class="wf"><div class="m">%s</div><div class="s">%s</div></div>'
                    '<div class="ag"><div class="m">%s</div><div class="s">%s</div></div></div>'
                    % (it["dim"], it["wf"], it["wf_s"], it["ag"], it["ag_s"]))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""),
                 '<div class="vs">%s</div>' % "".join(rows), fill=True, endbar=p.get("endbar"))


def p_takeaway(p):
    ps = '<div class="ps">%s</div>' % "".join("<p>%s</p>" % x for x in p["paras"])
    lim = ""
    if p.get("limit"):
        lim = ('<div class="lim"><div class="h">%s</div><p>%s</p></div>'
               % (p["limit"][0], p["limit"][1]))
    return _page(p["meta"], p["pg"], p["title"], p.get("lead", ""),
                 '<div class="tk"><div class="hl">%s</div>%s%s</div>' % (p["highlight"], ps, lim),
                 fill=True, endbar=p.get("endbar"))


BUILDERS = {"cover": p_cover, "stats": p_stats, "chain": p_chain, "timeline": p_timeline,
            "compare": p_compare, "vs": p_vs, "takeaway": p_takeaway}


def render_cfg(cfg, out_dir=None, only=None):
    """渲染一套 v2 表意型排版。返回生成的 PNG 路径列表。

    out_dir 默认 <skill根>/output_text；HTML 中间产物在 <out_dir>/_html。
    """
    global FBRAND
    FBRAND = cfg.get("footer_brand") or "晚秋AI日记"

    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(SCRIPT_DIR), "output_text")
    out_dir = os.path.abspath(out_dir)
    hdir = os.path.join(out_dir, "_html")
    os.makedirs(hdir, exist_ok=True)
    browser = find_browser()
    if not browser:
        raise SystemExit("❌ 未找到可用的无头浏览器（Edge/Chrome），请先安装。")

    total = len(cfg["pages"])
    head = ('<!doctype html><html lang="zh"><head><meta charset="utf-8">'
            '<style>%s</style></head><body>' % _css(CSS))

    files = []
    for i, p in enumerate(cfg["pages"]):
        name = "%02d_%s" % (i, p.get("name", p["type"]))
        if only and name not in only:
            continue
        typ = p["type"]
        if typ not in BUILDERS:
            raise SystemExit("❌ 未知版式 type=%r（page %s）。可用：%s"
                             % (typ, name, "/".join(sorted(BUILDERS))))
        body = p_cover(p, i + 1, total) if typ == "cover" else BUILDERS[typ](p)
        hp = os.path.join(hdir, "%s.html" % name)
        with open(hp, "w", encoding="utf-8") as f:
            f.write(head + body + "</body></html>")
        op = os.path.join(out_dir, "%s.png" % name)
        if os.path.exists(op):
            os.remove(op)
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-sandbox", "--disable-dev-shm-usage",
                        "--user-data-dir=%s" % os.path.join(out_dir, "_prof", name),
                        "--force-device-scale-factor=2", "--window-size=1080,1440",
                        "--default-background-color=00000000",
                        "--screenshot=%s" % op, "file:///" + hp.replace("\\", "/")],
                       capture_output=True, timeout=180, env=SAFE_ENV)
        ok = os.path.exists(op)
        print("  %-30s %s" % (name, "OK" if ok else "FAIL"))
        if ok:
            files.append(op)
    return files


def main():
    import argparse
    ap = argparse.ArgumentParser(description="纯文案模式 v2：表意型排版引擎（晚秋简约风）")
    ap.add_argument("content", help="v2 内容 JSON 路径（结构见 examples/wf_agent_v2.json）")
    ap.add_argument("--out", default=None, help="输出目录（默认 <skill根>/output_text）")
    ap.add_argument("--only", nargs="*", default=None, help="只渲染指定页，如 00_cover 03_五个差别")
    a = ap.parse_args()
    cfg = json.load(open(a.content, encoding="utf-8"))
    t0 = time.time()
    print("[%s]" % cfg.get("slug", "?"))
    fs = render_cfg(cfg, a.out, a.only)
    print("完成 %d 张，用时 %.1fs，输出目录：%s" % (len(fs), time.time() - t0, os.path.abspath(a.out or os.path.join(os.path.dirname(SCRIPT_DIR), "output_text"))))


if __name__ == "__main__":
    main()
