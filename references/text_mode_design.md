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
| `visual_prompt` | 3D 文生图提示词 |

### 内容页通用字段

| 字段 | 说明 |
|---|---|
| `layout` | 见下方 Layout 枚举 |
| `top_label` | 字符串数组，如 `["WHY TOMORROW", "RELEASE SIGNALS"]`，用 `/` 连接显示在左上角 |
| `page_title` | 页面大标题 |
| `lead` | 标题下一行说明 |
| `summary` | 底部总结条（必填，避免空条） |
| `visual_prompt` | 本页 3D 插画提示词 |

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
| `summary` | 结尾/总结/CTA | `statement`, `cta`, `tags` |

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
- 命名：`01_cover.png`, `02_<slug>.png`, `03_<slug>.png`, ...
- 同时保留 `_cover.json`, `_page*.json`, `_cover.html`, `_page*.html` 与 `assets/` 图片，方便二次修改。

## 7. 推荐用法

```bash
# 1. 让 AI 把文案结构化后写入 text_config.json
# 2. 并行生成 3D 插画（可选，提速）
python scripts/generate_text_images.py text_config.json --out output_text

# 3. 渲染成套 PNG
python run_text_tutorial.py text_config.json --out output_text --use-existing
```

或在支持 Skill 的 AI 客户端对话中直接说：

> 用 screenshot-tutorial-generator 技能，根据下面这段文案给我做 5 张小红书风格的配图。主题：AI/科技。包含 1 张封面 + 4 张内容页。文案如下：……

技能会：
1. 把文案结构化（schema）并回述确认；
2. 根据主题/预设选配色；
3. 为每页生成 3D 插画；
4. 杂志风排版并输出成套 PNG。
