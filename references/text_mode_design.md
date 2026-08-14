# 纯文案模式设计规范（Text Mode）

纯文案模式让 skill 接收**一段自由文案 + 主题/预设**，不依赖截图，自动生成成套小红书风格信息图。适合把长文/观点/数据做成多页视觉卡片。

## 1. 与截图模式的关系

- **底层复用**：`color_system.py` 配色推导、`fill_template.py` 模板填充、`render.py` 无头浏览器渲染、页脚页码系统。
- **新增部分**：主题/预设 → 配色、`agnes_image.py` 文生图 3D 插画、`text_cover.html` / `text_section.html` 杂志风模板、文案结构化 schema。
- **调用入口**：`run_text_tutorial.py`。

## 2. 输入 Schema（text_config.json）

```json
{
  "title": "帖子标题",
  "theme": "light",
  "preset": "cream",
  "category": "AI/科技",
  "brand": "大能AI",
  "url": "小红书 @大能AI",
  "cover": {
    "kicker": "AI 趋势观察",
    "title": "封面大标题",
    "subtitle": "副标题",
    "summary": "封面底部一句话总结",
    "visual_prompt": "3D rendered whale lighthouse, blue and white tech style..."
  },
  "pages": [
    {
      "layout": "timeline",
      "top_label": ["WHY TOMORROW", "RELEASE SIGNALS"],
      "page_title": "页面标题",
      "lead": "一句话引导",
      "items": [],
      "summary": "页面底部总结条",
      "visual_prompt": "3D rendered ..."
    }
  ]
}
```

### 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | str | 整个帖子的主题，用于 fallback 封面标题 |
| `theme` | `"light"` / `"dark"` | 默认 `light` |
| `preset` | str | 命名主题预设，优先于 `category`。可选：`cream/redbook/obsidian/cyber/minimal/forest/sunset/ocean` |
| `category` | str | 主题分类，无 `preset` 时用于映射主色。见 `color_system.CATEGORY_ACCENT` |
| `brand` / `url` | str | 页脚内容，可单独给或都不给 |
| `cover` | object | 封面配置 |
| `pages` | array | 内容页，每页一个 layout |

### 封面字段

| 字段 | 说明 |
|---|---|
| `kicker` | 左上角小字，如 `AI 趋势观察` |
| `title` | 大标题（衬线字体） |
| `subtitle` | 副标题（强调色） |
| `summary` | 封面底部总结条 |
| `visual_prompt` | 3D 文生图提示词（⚠️ **不要要求画面出现任何文字/字母/数字/符号**——免费生图模型画字必乱码；`agnes_image.py` 已自动给每条 prompt 追加「禁止文字」约束，无需手动加） |

### 内容页通用字段

| 字段 | 说明 |
|---|---|
| `layout` | 见下方 Layout 枚举 |
| `top_label` | 字符串数组，如 `["WHY TOMORROW", "RELEASE SIGNALS"]`，用 `/` 连接显示在左上角 |
| `page_title` | 页面大标题 |
| `lead` | 标题下一行说明 |
| `summary` | 底部总结条（必填，避免空条） |
| `visual_prompt` | 本页 3D 插画提示词（同封面：不要要求画面出现文字/字母/数字/符号，代码已自动禁止） |
| `page_mode` | 可选 `"stack"`（默认，垂直流式）或 `"split"`（旧双栏），一般用默认即可 |

## 3. Layout 枚举

| layout | 用途 | 专属字段 |
|---|---|---|
| `timeline` | 时间线/里程碑 | `items: [{date, title, desc}]` |
| `grid_cards` | 2×2 彩色卡片 | `items: [{icon, title, desc}]` |
| `big_number` | 超大数字强调 | `number`, `label`, `desc` |
| `price_table` | 价格表/档位对比 | `rows: [{plan, price, note}]` |
| `metrics` | 指标列表 | `metrics: [{value, name, desc}]` |
| `quote` | 金句/语录 | `quote` |
| `definition` | 名词解释 | `term`, `explanation` |
| `spec_list` | 标签清单（名称/适用人群/使用场景 等一眼看懂的结构，适合小白介绍页） | `rows: [{label, value}]` |
| `summary` | 结尾/总结/CTA | `statement`, `cta`, `tags` |

### 内容页排版规则（v1.3.3+）

默认采用 **垂直流式（stack）** 布局：
- 标题/导语在顶部占满全宽；
- 内容区占满全宽，不再挤在左半边；
- `grid_cards` 有 4 项时，自动拆成 **2 张在插画上方 + 2 张在插画下方**，插画居中；
- 其余 layout 的内容全宽置于插画上方，插画在下方作为视觉收尾；
- 插画高度自适应：`min-height:240px / max-height:520px`，内容少时吸收空白、内容多时收缩防溢出；
- 正文统一加 `line-clamp`，防止极端长文案撑破页面。

如需旧版左文右图双栏，可在页面配置里加 `"page_mode": "split"`。

> 文案铁律：内容页必须**说人话且专业**。完整规范见 `SKILL.md`「文案质量准则」，要点：
> - **说人话 ≠ 网络腔**：禁用 `说白了/上头/能打/神器/疯狂/偷懒(拟人)` 等油腻词、夸大词、贬义拟人；平实但准确。
> - **标题传信息不卖情绪**（「四个关键设计」而非「四个让人上头的点」）。
> - **数字客观可溯源**，不注水；每个卖点落到「对你意味着什么」。
> - 介绍类页面首选 `spec_list`（名称 / 它是什么 / 适用人群 / 使用场景），让完全不懂的小白也能秒懂。

## 4. 配色来源

- 有 `preset` → 用 `THEME_PRESETS` 的 accent 与 theme。
- 无 `preset` 有 `category` → 用 `CATEGORY_ACCENT` 映射。
- 都没有 → 默认冷蓝青 `#2A8E9E`。

完整 palette（主色/辅色/互补色/6 功能色）仍由 `color_system.build_palette` 推导。

## 5. 3D 插画生成

- 入口：`run_text_tutorial.py` 内调 `agnes_image.generate_image()`。
- 模型：`agnes-image-2.1-flash`（文生图）。
- 尺寸：竖版 `768x1024`（3:4）。
- 并发：素材多时用 `scripts/generate_text_images.py` 并行生成，再用 `run_text_tutorial.py --use-existing` 渲染。
- 降级：未设置 `AGNES_API_KEY` 或生成失败时，模板显示占位文字，不中断出图。

## 6. 输出

- 默认输出到 `--out` 目录（默认 `output_text/`）。
- 命名：`00_cover.png`（极简传播封面，独立一张不编号）、`01_cover.png`（丰富封面）、`02_<slug>.png`, `03_<slug>.png`, ...
- 同时保留 `_mincover.json`, `_cover.json`, `_page*.json`, `_mincover.html`, `_cover.html`, `_page*.html` 与 `assets/` 图片，方便二次修改。

### 极简传播封面（`00_cover.png`）
- 由 `templates/cover.html` 渲染，专供小红书/公众号信息流直发，结构极简：栏目小字 + 大图标 + 超大品牌名 + ≤12 字 slogan + 可选说明。
- 图标默认复用 `assets/cover.png`（文生图 3D 主视觉）放入圆角方块框；无图时自动降级为「首字渐变圆角方块」文字 logo。
- `cover` 字段可额外提供 `brand_main` / `brand_sub` / `slogan` / `desc` 覆盖自动蒸馏结果（品牌名按 `.`/`·`/空格 拆主副标题；slogan 取 `subtitle` 前 12 字）。
- 顶层 `series` 字段可指定栏目名；缺省时由脚本按 `category` 推导（医疗→健康知识小科普、AI/科技→AI 工具实测 等）。

## 7. 推荐用法

```bash
# 1. 让 AI 把文案结构化后写入 text_config.json
# 2. 并行生成 3D 插画（可选，提速）
python scripts/generate_text_images.py text_config.json --out output_text

# 3. 渲染成套 PNG
python run_text_tutorial.py text_config.json --out output_text --use-existing
```

或在支持 Skill 的 AI 客户端对话中直接说：

> 用 screenshot-infographic-skill 技能，根据下面这段文案给我做 5 张小红书风格的配图。主题：AI/科技。包含 1 张封面 + 4 张内容页。文案如下：……

技能会：
1. 把文案结构化（schema）并回述确认；
2. 根据主题/预设选配色；
3. 为每页生成 3D 插画；
4. 杂志风排版并输出成套 PNG。
