#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes AI 图片生成封装（screenshot-tutorial-generator 用）

用途：
- 纯文案模式：为每一页生成 3D 概念插画（文生图）。
- 截图模式（可选增强）：为功能卡片生成 3D 装饰插画 / 品牌主视觉。

特点：
- 使用 Agnes AI 免费图片 API（OpenAI 兼容格式）。端点 `apihub.agnes-ai.com` 目前主要面向**中国大陆网络可直连**，无需代理；海外/受限网络可能连不上，此时调用方应降级到 SVG 图标占位（见 generate_text_images 的优雅降级）。
- 零第三方依赖（仅用标准库 urllib），本机任意 Python 即可运行。
- 读取环境变量 AGNES_API_KEY；未设置时自动使用内置的**共享演示 key**（仅作零配置体验，有速率限制，且依赖网络可直连上述端点）。生产或频繁使用、或处于海外网络时，请自配 `AGNES_API_KEY`（https://agnes-ai.com 注册获取）。
- 对 5xx 服务端错误自动重试（峰值可能不稳定）。

API 要点（实测确认）：
- 端点：POST https://apihub.agnes-ai.com/v1/images/generations
- 文生图模型：agnes-image-2.1-flash
- 图生图模型：agnes-image-2.0-flash（需 extra_body.image 传源图 URL）
- size 支持：1024x768(4:3) / 1024x1024(1:1) / 768x1024(3:4) / 720x1280(9:16) / 576x1024(9:16)
- 不支持 "9:16" 比例字符串（会被忽略返回正方形），也不支持 1080x1920（会 500）
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://apihub.agnes-ai.com/v1"
TIMEOUT = 420
MAX_RETRY = 2

# 内置兜底 key（Agnes 为免费模型，用户授权直接硬编码进 skill，未设置环境变量时自动使用）。
# 优先级：显式参数 > 环境变量 AGNES_API_KEY > 此兜底。
FALLBACK_API_KEY = "sk-Vloi42yn2SLHdv3mhRf7ar53WphOlS3Vrf2NrS0F9bOInScJ"


def get_api_key(explicit=None):
    key = explicit or os.environ.get("AGNES_API_KEY") or FALLBACK_API_KEY
    if not key:
        raise RuntimeError(
            "未设置 AGNES_API_KEY。请到 https://agnes-ai.com 注册并在 "
            "Settings -> API Keys 创建密钥，然后 `export AGNES_API_KEY=sk-xxx`。"
        )
    return key


def _post(payload, api_key, timeout=TIMEOUT):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/images/generations",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_err = None
    for attempt in range(MAX_RETRY):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 4xx 客户端错误（含 401 key 无效）不重试，直接抛出
            if 400 <= e.code < 500:
                detail = e.read().decode("utf-8", "ignore")
                raise RuntimeError(f"Agnes API {e.code} 错误：{detail}")
            # 5xx 服务端错误，退避重试
            last_err = e
            time.sleep(10 * (attempt + 1))
        except Exception as e:  # 网络抖动等
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Agnes 图片生成在 {MAX_RETRY} 次重试后仍失败：{last_err}")


def _download(url, out_path, timeout=TIMEOUT):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out_path.write_bytes(resp.read())
    return str(out_path)


def generate_image(prompt, size="768x1024", model="agnes-image-2.1-flash",
                   image_urls=None, out_path=None, api_key=None, timeout=None):
    """生成一张图片并下载到本地，返回本地路径。

    Args:
        prompt: 详细的中文/英文描述。建议结构：
                [主体] + [场景/环境] + [风格] + [光照] + [构图] + [质量要求]
        size: 输出尺寸，竖版教程图推荐 "768x1024"(3:4) 或 "720x1280"(9:16)。
        model: "agnes-image-2.1-flash"(文生图) / "agnes-image-2.0-flash"(图生图)。
        image_urls: 图生图时的源图 URL 列表（用 agnes-image-2.0-flash）。
        out_path: 本地保存路径；省略则存到 <skill>/assets/generated/。
        api_key: 显式 key；省略则读 AGNES_API_KEY 环境变量。
    Returns:
        本地图片路径字符串。
    """
    api_key = get_api_key(api_key)
    timeout = timeout or TIMEOUT
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if image_urls:
        payload["extra_body"] = {"image": list(image_urls), "response_format": "url"}

    body = _post(payload, api_key, timeout)
    items = (body or {}).get("data") or []
    if not items or "url" not in items[0]:
        raise RuntimeError(f"Agnes 未返回图片 URL：{body}")

    if out_path is None:
        out_path = Path(__file__).resolve().parent.parent / "assets" / "generated"
        out_path.mkdir(parents=True, exist_ok=True)
        out_path = out_path / f"agnes_{int(time.time() * 1000)}.png"

    return _download(items[0]["url"], out_path, timeout)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Agnes AI 图片生成（验证用）")
    p.add_argument("--prompt", required=True, help="图片描述")
    p.add_argument("--size", default="768x1024", help="尺寸，如 768x1024 / 720x1280")
    p.add_argument("--model", default="agnes-image-2.1-flash")
    p.add_argument("--out", default=None, help="本地输出路径")
    p.add_argument("--api-key", default=None, help="显式传入 key（也可靠环境变量）")
    p.add_argument("--img2img", nargs="*", default=None, help="图生图源图 URL 列表")
    a = p.parse_args()
    try:
        path = generate_image(a.prompt, a.size, a.model, a.img2img, a.out, a.api_key)
        print(f"SAVED: {path}")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
