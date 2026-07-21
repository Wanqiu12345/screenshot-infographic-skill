# Agnes 图片模型接入指南（可选增强）

本 skill 可用 [Agnes AI](https://agnes-ai.com) 的**免费**图片生成 API 产出 3D 概念插画，
显著提升教程图的视觉精美度（接近小红书上「纯文案 → 精美信息图」的效果）。

- 它是**可选增强**：不配置 `AGNES_API_KEY` 时，skill 自动降级到内置 SVG 图标，基础出图不受影响。
- 它是**免费的**：Agnes 图片 API 全免费，国内站可直连，无需代理。
- 它**零额外依赖**：`scripts/agnes_image.py` 仅用 Python 标准库（urllib），任意本机 Python 即可运行。

---

## 1. 获取 API Key

1. 打开 https://agnes-ai.com 注册账号。
2. 进入 Settings → API Keys，创建一个密钥（形如 `sk-xxxx`）。
3. 把 key 设为环境变量（推荐，不要写进任何脚本/仓库）：

   ```bash
   # Windows (PowerShell / CMD)
   set AGNES_API_KEY=sk-xxxx

   # macOS / Linux
   export AGNES_API_KEY=sk-xxxx
   ```

> 也可以调用 `generate_image(..., api_key="sk-xxxx")` 显式传入，但这只适合临时测试。

---

## 2. 验证是否可用（本机运行）

在本机（有外网、能直连 Agnes 的电脑）运行：

```bash
python scripts/agnes_image.py \
  --prompt "a 3D rendered cute whale lighthouse, blue and white tech style, soft shadow, minimalist" \
  --size 768x1024 \
  --out test_agnes.png
```

成功会打印 `SAVED: <路径>` 并生成 `test_agnes.png`。
失败会打印 `ERROR: ...`（常见：401 key 无效、无外网、5xx 服务端繁忙）。

> ⚠️ 注意：本 skill 的渲染流程是在**用户本机**跑的，所以 Agnes 调用也在本机发生。
> 如果你所在环境（例如某些 Agent 沙箱）没有外网出口，会连不上——这是环境限制，不是代码问题。

---

## 3. API 要点（实测确认）

| 项目 | 内容 |
|---|---|
| Base URL | `https://apihub.agnes-ai.com/v1` |
| 端点 | `POST /v1/images/generations` |
| 认证 | `Authorization: Bearer <API_KEY>`（OpenAI 兼容格式） |
| 文生图模型 | `agnes-image-2.1-flash` |
| 图生图模型 | `agnes-image-2.0-flash`（需 `extra_body.image` 传源图 URL） |
| 响应 | `{"data":[{"url":"https://..."}]}` |
| 费用 | 全部免费 |
| 网络 | 国内站，本机可直连，无需代理 |
| 稳定性 | 无 SLA，高峰期可能 5xx（`agnes_image.py` 已自动退避重试 3 次）|

### size 取值表（重要）

`size` 用 `宽x高` 像素字符串。**不支持比例字符串（如 "9:16" 会被忽略返回正方形）**。

| size | 比例 | 用途 |
|---|---|---|
| `1024x768` | 4:3 | 横屏 |
| `1024x1024` | 1:1 | 正方形（默认） |
| `768x1024` | **3:4** | 竖版教程图（推荐） |
| `720x1280` | 9:16 | 竖版短视频 |
| `576x1024` | 9:16 | 竖版短视频 |

**禁止**：`"9:16"`（被忽略）、`"1080x1920"`（直接 500 错误）。

---

## 4. Prompt 结构建议

文生图质量强烈依赖 prompt 的详细程度。推荐结构：

```
[主体] + [场景/环境] + [风格] + [光照] + [构图] + [质量要求]
```

示例（科技风 3D 插画）：

```
a 3D rendered isometric icon of a document flying into a funnel,
blue and white tech style, soft studio lighting, clean minimalist,
C4D Octane render, isolated on light background
```

图生图（用 `agnes-image-2.0-flash`）：

```
[需要改变什么] + [需要保持什么不变]
```

---

## 5. 在 skill 里怎么用

`scripts/agnes_image.py` 暴露一个函数：

```python
from agnes_image import generate_image

local_path = generate_image(
    prompt="a 3D rendered whale lighthouse, blue tech style",
    size="768x1024",                 # 竖版 3:4
    model="agnes-image-2.1-flash",   # 文生图
    # image_urls=[...],              # 图生图时填源图 URL
    out_path="assets/generated/whale.png",
    # api_key="sk-xxx",              # 省略则读 AGNES_API_KEY 环境变量
)
# local_path 是下载后的本地 PNG 路径，可直接 <img src> 嵌入模板
```

典型接入点：

- **截图模式（可选增强）**：在 `run_screenshot_tutorial.py` 里，为概览图顶部 / 细节图「核心价值」区生成一张 3D 概念图，填入模板的 `<img class="concept">` 槽位。
- **纯文案模式（规划中）**：把用户文案结构化成 N 页，每页带一个 `concept_prompt`，逐页生成 3D 插画后嵌入杂志风模板。

---

## 6. 降级策略

| 情况 | 行为 |
|---|---|
| 未设置 `AGNES_API_KEY` | 跳过 3D 图，模板用内置 SVG 图标占位，正常出图 |
| `401` key 无效 | 抛错并提示用户去 agnes-ai.com 重新获取 |
| `5xx` 服务端繁忙 | 自动退避重试 3 次，仍失败则降级到 SVG 图标（业务层应 catch 后降级）|
| 无外网 | 调用失败，业务层应 catch 并降级到 SVG 图标 |

建议业务层这样写：

```python
try:
    concept_img = generate_image(prompt, size="768x1024")
except Exception:
    concept_img = None   # 模板里 concept_img 为 None 时不渲染 <img>，用 SVG 兜底
```
