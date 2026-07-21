# 设计规范与 config 结构

## 出图规格
- 尺寸：**1080 × 1440（3:4 竖版）**，渲染 scale=2 → 实际 2160×2880 高清 PNG。
- 一套默认 4~5 张：`01_overview.png` + `02_xxx.png` … `05_xxx.png`。
- 命名：`01_overview.png`、`02_<功能英文/拼音>.png`，序号两位。

## 配色方案（来自 extract_theme.py + color_system.py）
`extract_theme.py` 先识别截图的明暗、背景、主品牌色，然后调用 `color_system.py` 推导完整配色。

`palette` 对象：
```
{
  "page_bg":   "整页背景色（跟随截图明暗）",
  "card_bg":   "卡片背景（浅色=白，深色=深灰）",
  "text_main": "主文字色",
  "text_sub":  "次要文字色",
  "accent":    "主色（截图品牌色，或优雅兜底）",
  "accent_soft": "主色 12% 透明度，用于 tip/图标背景",
  "secondary": "类比辅色（色轮 +28°），增加层次",
  "secondary_soft": "辅色 soft",
  "accent2":   "互补强调色（色轮 +180°），用于重点引导",
  "accent2_soft": "互补强调色 soft",
  "feature":   ["6 个功能卡片色，色轮 ±60° 内等距分布"],
  "feature_soft": ["6 个功能卡片色的 soft 版本"],
  "line":      "细线/边框色，由 text_sub 派生"
}
```
`radius`：圆角像素，soft 风格用 20，sharp（科技感）用 8。
设计依据见 `references/color_guide.md`（60-30-10 法则、色轮和谐、WCAG 对比度）。

## overview config
```json
{
  "type": "overview",
  "palette": { ... },
  "radius": 20,
  "logo_image": "logo.png（优先）",
  "logo_icon": "tree（其次，使用 SVG 图标）",
  "logo_text": "思（最后回退，最多 1 个汉字）",
  "brand": "品牌名",
  "subtitle": "一句话副标题",
  "badge": "6 大核心功能",
  "urlbar": "mindmap.app",
  "screenshot": "绝对路径/screenshot.png",
  "items": [
    {"num": "01", "icon": "chat", "title": "功能名", "desc": "一句话说明"}
  ],
  "footer": {"brand": "品牌名", "url": "网址(可省)", "page": "1 / 5"}
}
```
- `logo_image` / `logo_icon` / `logo_text` 三选一，优先级也是这个顺序。`logo_text` 会被截断到 1 个汉字/2 个字母，防止长名字硬塞进 60×60 图标。
- `footer` 可为 null（品牌智能判断：什么都没给就不加）。
- 概览图 items 建议 4~6 条，太多会超出 1440 高度。
- 6 个 item 会自动应用 `palette.feature` 6 色：图标底、图标描边、编号、标题、左侧色条。

## detail config
```json
{
  "type": "detail",
  "palette": { ... },
  "radius": 20,
  "tag": "核心功能",
  "pageinfo": "2 / 5",
  "title": "导入文档，一键成图",
  "lead": "一段引导语，说明这个功能解决什么问题",
  "crop": "绝对路径/crop_02.png",
  "feature_color": "#2BD385",
  "steps": [
    {"n": 1, "title": "步骤标题", "desc": "具体操作说明"}
  ],
  "value": {"title": "为什么方便", "text": "一段话说明这个功能带来的好处，用互补强调色高亮"},
  "tip": {"title": "小提示", "text": "一段补充说明或适用场景，用来填满画面底部"},
  "footer": {"brand": "...", "url": "...", "page": "2 / 5"}
}
```
- `crop` 由 crop_region.py 裁出的功能局部图。
- steps 建议 **3~4 条**，每条标题 + 详细说明。
- `value`（可选但推荐）用互补强调色 `accent2` 高亮，作为重点引导。
- `tip`（可选但推荐）放在步骤下方，既提供额外价值，又能避免 1080×1440 画面底部大面积空白。
- `feature_color`（可选）为细节图指定一个功能色，让该图与概览中对应卡片颜色呼应。
- 需要“整图 + 圈选标记”模式时，把 `crop` 换成 `screenshot` 并加 `mode: "full"` + `marker: {"x": 50, "y": 50, "r": 60}`：
  ```json
  {
    "mode": "full",
    "screenshot": "绝对路径/screenshot.png",
    "marker": {"x": 4, "y": 58, "r": 55}
  }
  ```

## 可用图标 key
chat, file, tree, palette, plus, download, search, layers, edit, share,
image, settings, star, link, sparkle, bolt, grid
（未匹配的 key 回退到 star）

## 明暗自适应经验
- avg_lum > 150 → light；否则 dark。
- 浅色截图 → 暖白底 (#FAF8F3)，柔和大圆角。
- 深色/科技截图 → 深色底 (#16181D)，冷色强调，小圆角。

## 细节图表现方式
- 小控件（按钮/图标）：crop 时 pad 给 0.06~0.1，放大展示 + 说明。
- 大区域（面板/列表）：pad 给 0.02，保留上下文。
- 需要箭头指向时，可在 detail.html 的 .figure 内叠加 SVG（进阶，可选）。

## 完整调用链
1. `extract_theme.py <shot>` → 调用 `color_system.py` 推导主题、主色、完整 palette
2. 定位功能区域：优先 `ocr_locate.py <shot> "按钮文字"` 自动定位，再扩 2%~4% padding；
   OCR 失败再目测，目测后先裁剪出来看一眼确认；
   仍不确定时用九宫格让用户指认。
3. （每个功能）`crop_region.py <shot> <crop.png> x y w h [pad]`
4. 写 `config_XX.json`
5. `fill_template.py config_XX.json page_XX.html`
6. `render.py page_XX.html 0X_name.png 1080 1440 2`
7. 展示全部 PNG（WorkBuddy 用 present_files；其他工具直接打开 output/*.png）
