#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""screenshot_v2 —— 截图模式 × 晚秋简约风（v2 表意型排版）渲染器。

由 stylelab_20260901/make_shot_v2.py 原型移植进 skill（2026-09-01）。
设计原则承接 v2 引擎结论：
1. 纯排版 + 1px 细线，无彩虹功能色、无渐变徽章、无重投影、无 3D 插画。
2. 每页 flex 撑满 1080×1440，不允许底部大片真空。
3. 字号阶梯固定；品牌色从截图主色自动推导（降饱和、压暗成「高级感」色），
   金色 #B08D45 只做小面积强调。
4. 细节裁剪是「碎片」不是完整页面：不加浏览器假地址条，只加细线框；
   碎片高度 < 300px 时自动放大（最多 2 倍）保证可读。
5. 无头渲染必须传最小环境变量（SAFE_ENV）：宿主注入的 NODE_OPTIONS 等
   变量会让 Edge 无头模式秒退。

用法（CLI，与 run_screenshot_tutorial.py --style v2 配套）：
    python scripts/screenshot_v2.py <v2_config.json>

v2_config.json 结构（见 run_screenshot_tutorial.build_v2_config）：
    screenshot / brand / brand_main / brand_sub / url / subtitle /
    series / category / cover{kicker,title_lines,subtitle,show_screenshot,note,date} /
    items[{num,title,desc}] / details[{slug,idx,tag,title,lead,coords,value,tip,steps}]
    可选 out_dir：输出目录（默认 <skill根>/output）
"""
import collections
import colorsys
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
from render import find_browser  # noqa: E402  复用浏览器查找逻辑

SAFE_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    "TEMP": os.environ.get("TEMP", ""),
    "TMP": os.environ.get("TMP", ""),
    "USERPROFILE": os.environ.get("USERPROFILE", ""),
}

GOLD = "#B08D45"
GOLD2 = "#C9A961"


# ==========================================================
# 色彩：从截图推导品牌色（降饱和、压暗）
# ==========================================================
def _hsl_to_hex(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def pick_accent(img_path, default="#1A3A6B"):
    im = Image.open(img_path).convert("RGB").resize((72, 72))
    cand = []
    for r, g, b in im.getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if s > 0.30 and 0.15 < v < 0.95:
            cand.append((h, s, v))
    if len(cand) < 40:
        return default
    buckets = collections.Counter(int(h * 36) for h, s, v in cand)
    hb = buckets.most_common(1)[0][0]
    sel = [x for x in cand if int(x[0] * 36) == hb]
    h = sum(x[0] for x in sel) / len(sel)
    s = min(0.58, sum(x[1] for x in sel) / len(sel) + 0.08)
    return _hsl_to_hex(h, s, 0.28)


def is_dark(img_path):
    im = Image.open(img_path).convert("L").resize((48, 48))
    px = list(im.getdata())
    return sum(px) / len(px) < 110


def _hex_to_hsv(hx):
    hx = hx.lstrip("#")
    r, g, b = (int(hx[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def _lighten(hx, dl):
    h, s, v = _hex_to_hsv(hx)
    return _hsl_to_hex(h, s, min(0.92, v + dl))


def build_tokens(img_path):
    if is_dark(img_path):
        base = {
            "bg": "#151A22", "ink": "#E8ECF3", "ink2": "#C2CAD8", "ink_soft": "#8B95A7",
            "line": "#333B49", "line2": "#272E3A", "card": "#1B212B",
            "brand": pick_accent(img_path, "#7FA3D8"),
        }
        base["brand2"] = _lighten(base["brand"], 0.16)
        base["brand_tint"] = "#20293A"
    else:
        base = {
            "bg": "#FBFAF8", "ink": "#12203C", "ink2": "#3E4759", "ink_soft": "#6C7686",
            "line": "#DED9CE", "line2": "#EAE5DA", "card": "#FFFFFF",
            "brand": pick_accent(img_path, "#1A3A6B"),
        }
        base["brand2"] = _lighten(base["brand"], 0.18)
        base["brand_tint"] = "#F1EEE6"
    return base


def css(T):
    tpl = """
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:__BG__;}
.page{
  width:1080px;height:1440px;background:__BG__;color:__INK__;
  padding:72px 84px 52px;display:flex;flex-direction:column;position:relative;overflow:hidden;
  font-family:'PingFang SC','HarmonyOS Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif;
  -webkit-font-smoothing:antialiased;
}
.hd{display:flex;justify-content:space-between;align-items:baseline;
  font-size:17px;letter-spacing:5px;font-weight:600;flex:0 0 auto;}
.hd .tag{color:__GOLD__;}
.hd .pg{color:__INK_SOFT__;font-weight:500;letter-spacing:3px;opacity:.7;}
.h2{font-size:54px;font-weight:800;line-height:1.18;margin-top:32px;letter-spacing:-2px;flex:0 0 auto;}
.lead{font-size:23px;color:__INK_SOFT__;line-height:1.6;margin-top:14px;max-width:900px;flex:0 0 auto;}
.body{margin-top:34px;flex:1;min-height:0;display:flex;flex-direction:column;}
.foot{margin-top:auto;padding-top:18px;display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid __LINE__;font-size:16px;color:__INK_SOFT__;letter-spacing:2px;
  flex:0 0 auto;opacity:.75;}

/* ================= 截图框（概览 & 细节通用） ================= */
.shot{flex:0 0 auto;background:__CARD__;border:1px solid __LINE__;border-radius:4px;
  overflow:hidden;display:flex;flex-direction:column;}
.shot .bar{display:flex;align-items:center;gap:8px;padding:12px 18px;
  border-bottom:1px solid __LINE2__;background:__CARD__;}
.shot .bar .dot{width:9px;height:9px;border-radius:50%;border:1px solid __INK_SOFT__;opacity:.55;}
.shot .bar .url{flex:1;text-align:center;font-size:14px;color:__INK_SOFT__;
  letter-spacing:.5px;margin:0 110px;white-space:nowrap;overflow:hidden;}
.shot img{display:block;width:100%;}

/* ================= 概览：功能拆解（表格化，无彩虹色） ================= */
.ov-hd{display:flex;align-items:baseline;gap:18px;margin-top:32px;flex:0 0 auto;}
.ov-hd .t{font-size:30px;font-weight:800;letter-spacing:1px;}
.ov-hd .n{font-size:18px;color:__GOLD__;font-weight:700;letter-spacing:3px;}
.ov-hd .ln{flex:1;height:1px;background:__LINE__;}
.ov-list{flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;
  grid-auto-rows:1fr;column-gap:56px;margin-top:10px;}
.ov-it{display:flex;align-items:center;gap:22px;border-bottom:1px solid __LINE__;}
.ov-it .no{font-size:40px;font-weight:800;color:__GOLD__;letter-spacing:-1px;
  width:64px;flex:0 0 auto;line-height:1;}
.ov-it .tx{flex:1;min-width:0;}
.ov-it .tx h3{font-size:26px;font-weight:700;letter-spacing:-.5px;}
.ov-it .tx p{font-size:19px;color:__INK_SOFT__;line-height:1.55;margin-top:7px;}

/* ================= 细节页 ================= */
/* 细节裁剪是「碎片」不是完整页面：不加浏览器条，只加细线框 */
.fig{flex:0 0 auto;display:flex;justify-content:center;margin-top:2px;}
.fig .frag{border:1px solid __LINE__;border-radius:4px;background:__CARD__;padding:14px;
  max-width:100%;}
.fig .frag img{display:block;max-width:100%;}
.stp{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:space-between;
  margin-top:26px;}
.stp .row{flex:1;min-height:0;display:flex;gap:22px;align-items:center;}
.stp .rail{position:relative;width:22px;height:100%;flex:0 0 auto;}
.stp .rail .ln{position:absolute;left:10px;top:0;bottom:0;width:1px;background:__LINE__;}
.stp .row:last-child .rail .ln{bottom:auto;height:50%;}
.stp .row:first-child .rail .ln{top:50%;bottom:0;}
.stp .rail .dot{position:absolute;left:0;width:20px;height:20px;border-radius:50%;
  background:__BRAND__;top:50%;margin-top:-10px;}
.stp .row:last-child .rail .dot{background:__GOLD__;}
.stp .cnt{flex:1;min-width:0;display:flex;flex-direction:column;gap:7px;}
.stp .head{display:flex;align-items:baseline;gap:18px;}
.stp .no{font-size:16px;font-weight:700;color:__GOLD__;letter-spacing:2px;flex:0 0 auto;}
.stp .t{font-size:27px;font-weight:700;letter-spacing:-.5px;}
.stp .d{font-size:20px;color:__INK_SOFT__;line-height:1.55;}
.note{flex:0 0 auto;display:flex;margin-top:26px;border:1px solid __LINE__;
  border-left:3px solid __GOLD__;background:__CARD__;border-radius:3px;}
.note .cell{flex:1;min-width:0;padding:20px 24px;}
.note .cell+.cell{border-left:1px solid __LINE2__;}
.note .h{font-size:15px;letter-spacing:4px;font-weight:700;color:__GOLD__;}
.note p{font-size:18px;color:__INK2__;line-height:1.6;margin-top:8px;}

/* ================= 封面 ================= */
.cv{width:1080px;height:1440px;background:__BG__;color:__INK__;position:relative;overflow:hidden;
  padding:72px 84px 58px;display:flex;flex-direction:column;
  font-family:'PingFang SC','HarmonyOS Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif;}
.cv .cl{display:flex;justify-content:space-between;align-items:baseline;
  font-size:17px;letter-spacing:6px;font-weight:600;color:__INK_SOFT__;opacity:.8;flex:0 0 auto;}
.cv .kick{font-size:19px;letter-spacing:5px;color:__GOLD__;font-weight:600;margin-top:44px;flex:0 0 auto;}
.cv .tt{font-size:88px;font-weight:800;line-height:1.12;letter-spacing:-4px;margin-top:18px;flex:0 0 auto;}
.cv .sub{font-size:28px;color:__INK2__;font-weight:600;line-height:1.5;margin-top:26px;
  letter-spacing:-.5px;max-width:860px;flex:0 0 auto;}
.cv .mid{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;}
.cv .shot{flex:0 0 auto;background:__CARD__;border:1px solid __LINE__;border-radius:4px;overflow:hidden;}
.cv .shot img{display:block;width:100%;}
.cv .sum{display:flex;margin-top:6px;flex:0 0 auto;}
.cv .sum .sc{flex:1;padding:26px 30px 24px;border:1px solid __LINE__;background:__CARD__;}
.cv .sum .sc+.sc{border-left:none;}
.cv .sum .sc .h{font-size:15px;letter-spacing:4px;font-weight:700;color:__GOLD__;}
.cv .sum .sc .t{font-size:26px;font-weight:800;margin-top:11px;letter-spacing:-.5px;}
.cv .sum .sc .d{font-size:18px;color:__INK_SOFT__;margin-top:7px;line-height:1.5;}
.cv .rule{width:88px;height:4px;background:__GOLD__;margin:30px 0 24px;flex:0 0 auto;}
.cv .bot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
  font-size:17px;letter-spacing:3px;color:__INK_SOFT__;border-top:1px solid __LINE__;
  padding-top:20px;flex:0 0 auto;opacity:.8;}
"""
    for k, v in T.items():
        tpl = tpl.replace("__%s__" % k.upper(), v)
    tpl = tpl.replace("__GOLD__", GOLD).replace("__GOLD2__", GOLD2)
    return tpl


# ==========================================================
# 页面构造
# ==========================================================
def _page(meta, pg, title, lead, body, total, brand):
    return ('<div class="page"><div class="hd"><span class="tag">%s</span>'
            '<span class="pg">%s</span></div>'
            '<div class="h2">%s</div><div class="lead">%s</div>'
            '<div class="body">%s</div>'
            '<div class="foot"><span>%s</span><span>第 %s / %02d 页</span></div></div>'
            % (meta, pg, title, lead, body, brand, pg, total))


def p_cover(cfg, total):
    c = cfg["cover"]
    tt = "<br>".join(c["title_lines"])
    cards = "".join('<div class="sc"><div class="h">%s</div><div class="t">%s</div>'
                    '<div class="d">%s</div></div>' % (x["h"], x["t"], x["d"])
                    for x in c.get("sum", []))
    sum_html = ('<div class="sum">%s</div>' % cards) if cards else ""
    shot_html = ""
    if c.get("show_screenshot"):
        shot_html = '<div class="shot"><img src="%s"></div>' % cfg["screenshot"]
    return ('<div class="cv"><div class="cl"><span>%s</span><span>%s</span></div>'
            '<div class="kick">%s</div><div class="tt">%s</div>'
            '<div class="sub">%s</div>'
            '<div class="mid">%s%s</div>'
            '<div class="rule"></div>'
            '<div class="bot"><span>%s</span><span>第 01 / %02d 页</span></div></div>'
            % (cfg["series"], c.get("date", ""), c["kicker"], tt, c["subtitle"],
               shot_html, sum_html, c.get("note", ""), total))


def _shot_html(url, img_path):
    return ('<div class="shot"><div class="bar">'
            '<span class="dot"></span><span class="dot"></span><span class="dot"></span>'
            '<span class="url">%s</span></div><img src="%s"></div>'
            % (url, img_path))


def p_overview(cfg, total):
    body = ('%s<div class="ov-hd"><span class="t">功能拆解</span>'
            '<span class="n">%d 项</span><span class="ln"></span></div>'
            '<div class="ov-list">%s</div>'
            % (_shot_html(cfg["url"], cfg["screenshot"]), len(cfg["items"]),
               "".join('<div class="ov-it"><div class="no">%s</div>'
                       '<div class="tx"><h3>%s</h3><p>%s</p></div></div>'
                       % (it["num"], it["title"], it["desc"]) for it in cfg["items"])))
    return _page("FEATURE OVERVIEW", "02", "%s 怎么用" % cfg["brand_main"],
                 cfg["subtitle"], body, total, cfg["brand"])


def p_detail(cfg, d, out_dir, total):
    x, y, w, h = d["coords"]
    im = Image.open(cfg["screenshot"]).convert("RGB")
    W, H = im.size
    box = (round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))
    frag = im.crop(box)
    # 小控件碎片（按钮/工具条）放大到可读高度，最多 2 倍
    fw, fh = frag.size
    if fh < 300:
        k = min(2.0, 300.0 / fh)
        frag = frag.resize((round(fw * k), round(fh * k)), Image.LANCZOS)
    crop = os.path.join(out_dir, "crop_%s.png" % d["slug"])
    frag.save(crop)
    crop_url = crop.replace("\\", "/")

    rows = []
    for i, s in enumerate(d["steps"]):
        rows.append('<div class="row"><div class="rail"><div class="ln"></div>'
                    '<div class="dot"></div></div>'
                    '<div class="cnt"><div class="head"><span class="no">STEP %d</span>'
                    '<span class="t">%s</span></div>'
                    '<span class="d">%s</span></div></div>'
                    % (i + 1, s["title"], s["desc"]))
    body = ('<div class="fig"><div class="frag"><img src="%s"></div></div>'
            '<div class="stp">%s</div>'
            '<div class="note"><div class="cell"><div class="h">%s</div><p>%s</p></div>'
            '<div class="cell"><div class="h">%s</div><p>%s</p></div></div>'
            % (crop_url, "".join(rows),
               d["value"]["title"], d["value"]["text"],
               d["tip"]["title"], d["tip"]["text"]))
    meta = "%s · %s" % (d["tag"].upper(), d["slug"].upper().replace("_", " "))
    return _page(meta, "%02d" % d["idx"], d["title"], d["lead"], body, total,
                 cfg["brand"])


# ==========================================================
# 渲染（最小环境变量，防宿主注入变量导致无头浏览器秒退）
# ==========================================================
def render_page(html_body, T, out_png):
    hp = out_png.replace(".png", ".html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write('<!doctype html><html lang="zh"><head><meta charset="utf-8">'
                '<style>%s</style></head><body>%s</body></html>' % (css(T), html_body))
    browser = find_browser()
    if not browser:
        raise RuntimeError("未找到 Chromium 内核浏览器（Edge / Chrome / Chromium）")
    userdir = tempfile.mkdtemp(prefix="shotv2_")
    try:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-sandbox", "--disable-dev-shm-usage",
                        "--user-data-dir=%s" % userdir,
                        "--force-device-scale-factor=2", "--window-size=1080,1440",
                        "--default-background-color=00000000",
                        "--screenshot=%s" % out_png, "file:///" + hp.replace("\\", "/")],
                       capture_output=True, timeout=180, env=SAFE_ENV)
    finally:
        shutil.rmtree(userdir, ignore_errors=True)
    return os.path.exists(out_png)


def render_all(cfg):
    """渲染整套 v2 图。返回输出目录。cfg 需为完整 v2 配置 dict。"""
    out_dir = cfg.get("out_dir") or os.path.join(SKILL_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    cfg["screenshot"] = os.path.abspath(cfg["screenshot"])
    if not os.path.exists(cfg["screenshot"]):
        raise SystemExit("找不到截图: " + cfg["screenshot"])

    T = build_tokens(cfg["screenshot"])
    print("品牌色(取自截图): %s | 深色主题: %s" % (T["brand"], is_dark(cfg["screenshot"])))
    with open(os.path.join(out_dir, "theme_tokens.json"), "w", encoding="utf-8") as f:
        json.dump(T, f, ensure_ascii=False, indent=2)

    total = 2 + len(cfg["details"])   # 封面 + 概览 + 细节
    t0 = time.time()
    jobs = [("00_cover", p_cover(cfg, total)),
            ("01_overview", p_overview(cfg, total))]
    for d in cfg["details"]:
        jobs.append(("%02d_%s" % (d["idx"], d["slug"]),
                     p_detail(cfg, d, out_dir, total)))

    ok = 0
    for name, body in jobs:
        op = os.path.join(out_dir, "%s.png" % name)
        good = render_page(body, T, op)
        print("  %-22s %s" % (name, "OK" if good else "FAIL"))
        ok += int(bool(good))
    print("完成 %d/%d 张，用时 %.1fs" % (ok, len(jobs), time.time() - t0))
    if ok != len(jobs):
        raise SystemExit("有页面渲染失败，请检查上方 FAIL 项")
    return out_dir


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SKILL_ROOT, "output", "v2_config.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    render_all(cfg)


if __name__ == "__main__":
    main()
