#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯文案模式端到端执行器（screenshot-infographic-skill）

输入：表意型排版配置 JSON（字段见 SKILL.md「文案模式配置」节）。
引擎：scripts/text_v2.py —— 晚秋简约风，纯排版无插画，离线可跑。

用法：
  python run_text_tutorial.py my_config.json --out output_dir
  python run_text_tutorial.py                        # 无参数则跑内置演示 examples/wf_agent_v2.json

（历史版本的 v1 杂志风 + Agnes 3D 插画流程已在 v2.0.0 移除，
  旧 v1 配置（visual_prompt 格式）不再兼容。）
"""
import sys, os, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
V2_DEMO = os.path.join(HERE, "examples", "wf_agent_v2.json")


def main():
    ap = argparse.ArgumentParser(description="纯文案模式：结构化文案 -> 成套表意型排版图")
    ap.add_argument("config", nargs="?", default=None,
                    help="配置 JSON 路径（省略则跑内置演示 examples/wf_agent_v2.json）")
    ap.add_argument("--out", default="output_text", help="输出目录")
    ap.add_argument("--only", default=None,
                    help="只渲染指定页面（按 name 或文件名匹配，调试用）")
    a = ap.parse_args()

    cfg_path = a.config if (a.config and os.path.exists(a.config)) else V2_DEMO
    if not os.path.exists(cfg_path):
        sys.exit(f"[!] 找不到配置文件：{cfg_path}")
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    pages = cfg.get("pages", [])
    if not cfg.get("slug") or not pages or not all(isinstance(p.get("type"), str) for p in pages):
        sys.exit(
            "❌ 配置不是「表意型排版」格式（需要 slug + pages[].type 字段）。\n"
            "   旧 v1 文案格式（cover.visual_prompt / pages[].visual_prompt，Agnes 3D 插画）"
            "已在 v2.0.0 移除，不再兼容。\n"
            "   当前格式示例见 examples/wf_agent_v2.json；直接跑演示：python run_text_tutorial.py"
        )
    from text_v2 import render_cfg
    out = os.path.abspath(a.out)
    files = render_cfg(cfg, out_dir=out, only=a.only)
    print(f"[完成] 共 {len(files)} 张，输出目录：{out}")


if __name__ == "__main__":
    main()
