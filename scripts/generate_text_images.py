#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行生成纯文案模式所需的所有 3D 插画（自愈：失败自动重试 + 收尾补漏）。

用法：
  python scripts/generate_text_images.py examples/text_demo.json --out output_text
  python scripts/generate_text_images.py examples/text_demo.json --out output_text --use-existing

自愈策略（解决"某张图卡住/偶发失败被静默跳过"）：
  1. 主并行 pass：用线程池并发生成，单图超时由 --per-image-timeout 控制（默认 420s，
     覆盖 Agnes 峰值 5-6 分钟的生成耗时，避免误杀正常的慢图）。
  2. 单图失败（5xx/网络抖动）在编排层自动重试 --retries 次（指数退避）。
  3. 收尾补漏 sweep：主 pass 结束后，自动检查哪些资产仍缺失/过小，串行补生成
     --missing-retries 轮——失败的图会被"单独再跑一遍"，无需人工介入。
  4. 明确汇报：打印 成功/跳过(已存在)/缺失 数量；仍有缺失则退出码非 0，
     让上层（run_text_tutorial）决定是占位还是中止。

注意：4xx（key 无效 / prompt 违规）在 agnes_image 内部已判定为不可重试，会立即报错。
"""
import sys, os, json, argparse, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agnes_image


def ensure_asset(prompt, out_path, *, retries=3, timeout=420, backoff=8, use_existing=False):
    """确保 out_path 存在一张有效图片（>1KB）。失败按 retries 自动重试。返回路径或 None。"""
    if not prompt:
        return None
    if use_existing and os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        return out_path
    last = None
    for attempt in range(1, retries + 1):
        try:
            return agnes_image.generate_image(prompt, size="768x1024", out_path=out_path, timeout=timeout)
        except Exception as e:
            last = e
            print(f"[WARN] {os.path.basename(out_path)} 第{attempt}次失败：{e}", file=sys.stderr)
            if attempt < retries:
                time.sleep(backoff * attempt)
    print(f"[ERR]  {os.path.basename(out_path)} 经 {retries} 次重试仍失败：{last}", file=sys.stderr)
    return None


def is_valid(p):
    return bool(p) and os.path.exists(p) and os.path.getsize(p) > 1024


def main():
    ap = argparse.ArgumentParser(description="并行生成纯文案模式 3D 插画（自愈）")
    ap.add_argument("config", help="text_config.json")
    ap.add_argument("--out", default="output_text", help="输出目录")
    ap.add_argument("--workers", type=int, default=3, help="并发数")
    ap.add_argument("--retries", type=int, default=3, help="单图失败重试次数")
    ap.add_argument("--per-image-timeout", type=int, default=420,
                    help="单次生成等待上限(秒)；默认 420 覆盖 Agnes 峰值 5-6 分钟生成")
    ap.add_argument("--missing-retries", type=int, default=2, help="收尾补漏重试轮数")
    ap.add_argument("--backoff", type=int, default=8, help="重试退避基数(秒)")
    ap.add_argument("--use-existing", action="store_true", help="已存在的资产直接复用，不重新生成")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    assets = os.path.join(os.path.abspath(a.out), "assets")
    os.makedirs(assets, exist_ok=True)

    jobs = []
    cover = cfg.get("cover", {})
    jobs.append((cover.get("visual_prompt"), os.path.join(assets, "cover.png")))
    for i, pg in enumerate(cfg.get("pages", []), 1):
        jobs.append((pg.get("visual_prompt"), os.path.join(assets, f"page{i}.png")))

    def run_one(prompt, out):
        return ensure_asset(prompt, out, retries=a.retries, timeout=a.per_image_timeout,
                            backoff=a.backoff, use_existing=a.use_existing)

    # ---- 主并行 pass ----
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures = {ex.submit(run_one, p, o): o for p, o in jobs}
        for f in as_completed(futures):
            o = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"[ERR]  {os.path.basename(o)} 异常：{e}", file=sys.stderr)

    # ---- 收尾补漏 sweep：任何缺失资产自动单独补跑 ----
    for prompt, out in jobs:
        if is_valid(out):
            continue
        print(f"[SWEEP] 补漏 {os.path.basename(out)}")
        for _ in range(a.missing_retries):
            if is_valid(out):
                break
            ensure_asset(prompt, out, retries=1, timeout=a.per_image_timeout, backoff=a.backoff)
            time.sleep(a.backoff)

    ok = sum(1 for _, o in jobs if is_valid(o))
    skip = sum(1 for _, o in jobs if a.use_existing and is_valid(o))
    miss = len(jobs) - ok
    print(f"[完成] 资产目录 {assets}")
    print(f"[统计] 成功 {ok}/{len(jobs)}，跳过(已存在) {skip}，缺失 {miss}")
    if miss:
        sys.exit(1)


if __name__ == "__main__":
    main()
