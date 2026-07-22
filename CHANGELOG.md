# Changelog

## 1.3.0 (2026-07-22)

### 新增：极简传播封面（每种模式各一张 `00_cover.png`）
- **动机**：原有概览图信息过密，不适合直接发小红书/公众号信息流；新增一张极简封面专供传播。
- 新增模板 `templates/cover.html`：顶部小字栏目名 + 居中大图标(圆角方块框) + 超大品牌名(JS 自适应缩放防溢出) + ≤12 字 slogan + 可选 ≤20 字说明；无页脚或仅极淡品牌水印。
- `scripts/fill_template.py`：新增 `build_cover()`，`type="cover"` 接入渲染管线；图标为空时自动降级为「首字渐变圆角方块」文字 logo。
- 截图模式 `run_screenshot_tutorial.py`：提取 favicon 后组装封面（栏目名/品牌名/slogan 由 agent 蒸馏并与用户确认），渲染 `00_cover.png` 放在最前，概览顺延 `1/N`。
- 纯文案模式 `run_text_tutorial.py`：用文生图 3D 主视觉当封面图标，新增 `00_cover.png` 独立加在最前；丰富封面 `01_cover.png` 与内容页页码整体 +1。
- 设计约定：背景跟随主题色、文字中性克制、唯一色彩爆点=图标/品牌色；品牌名不缩写（仅 >16 字才拆主/副标题）；封面不编号。
- `SKILL.md`：核心产出、确认门（新增「栏目名确认」步骤）、关键规则新增「极简传播封面」整节。

## 1.2.5 (2026-07-21)

### 改进：生图禁用文字，避免免费模型乱码
- **背景**：Agnes 免费生图模型渲染文字必然乱码（字母/数字/符号显示为无意义笔画）。
- `scripts/agnes_image.py`：新增常量 `NO_TEXT_SUFFIX`，在 `generate_image` 中**自动追加**到每一条生图 prompt（`--no text, no letters... 画面中严禁出现任何文字...`）。从此无论 `visual_prompt` 写什么，模型都不会去画字。
- `references/text_mode_design.md`：`visual_prompt` 字段说明补「不要要求文字」提示。

## 1.2.3 (2026-07-21)

### 开源发布前最后收口
- 新增 `CONTRIBUTING.md`：外部贡献者参与指南（环境搭建、项目结构、扩展点、代码风格、PR 流程）。
- 新增 `assets/cover.png` + `assets/cover_source.html`：品牌封面横幅（1280×640，scale 2），用于 GitHub 仓库社交预览与 README 顶部展示。封面用本 skill 自己的离线渲染生成，无需联网生图。
- 更新 `README.md`：顶部引用 `assets/cover.png`，补齐技能品牌视觉。

## 1.2.2 (2026-07-21)

### 修复：纯文案模式 3D 插画与大数字显示被裁切
- **根因**：`templates/text_section.html` 和 `text_cover.html` 中的 `.hero img` 使用 `object-fit: cover`， Agnes 生成的 3:4 竖版 3D 插画被右侧固定槽位硬裁剪，导致主体（如第 3 页的图标组合）被截断。
- `text_section.html` + `text_cover.html`：`.hero img` 从 `object-fit: cover` 改为 `object-fit: contain`，确保插画主体完整显示；留白由页面背景色填充，保持杂志风干净。
- **根因**：`big_number` 版式中数字字号固定 130px 且 `white-space: nowrap`，左侧内容栏宽度不够，"1078 元" 整体溢出被 `overflow: hidden` 截断（"元" 字显示不全）。
- `text_section.html`：`.bignum .n` 字号从 `130px` 改为 `clamp(80px, 10vw, 110px)`，并给卡片左右 padding 留出安全边距，确保数字和单位完整可见。

## 1.2.1 (2026-07-21)

### 修复：文生图卡住 / 偶发失败被静默跳过
- **根因**：`agnes_image.py` 的 `TIMEOUT=120` 小于 Agnes 峰值 5-6 分钟的生成耗时，导致正常的慢图被反复超时→重试→最终判失败并被静默跳过，表现为"某张图卡住/缺失"。
- `agnes_image.py`：`TIMEOUT` 120→420（覆盖峰值生成耗时，不再误杀慢图）；`MAX_RETRY` 3→2（缩短单图最坏耗时）；`generate_image()` 新增可配 `timeout` 参数。
- `generate_text_images.py` 重写为**自愈编排器**：
  - 主并行 pass（线程池，并发可配）。
  - 单图失败（5xx/抖动）在编排层自动重试 `--retries` 次（指数退避）。
  - **收尾补漏 sweep**：主 pass 后自动检查缺失资产并串行补生成 `--missing-retries` 轮——失败的图被"单独再跑一遍"且无需人工介入。
  - 明确汇报 `成功/跳过(已存在)/缺失`，仍有缺失时退出码非 0。
- `run_text_tutorial.py`：接入 `ensure_asset`，把"生成阶段"与"渲染阶段"拆开（先确保所有图齐全再渲染，避免先渲染出占位图）；失败图同样走补跑。
- 新增 `--per-image-timeout`、`--retries`、`--missing-retries`、`--backoff` 可调参数。

## 1.2.0 (2026-07-21)

### 新增
- 纯文案模式：用户只发一段文案即可生成成套小红书风格信息图（`run_text_tutorial.py`）。
- 杂志风模板：`text_cover.html` 封面 + `text_section.html` 内容页，支持 8 种 layout。
- 文案版式：timeline / grid_cards / big_number / price_table / metrics / quote / definition / summary。
- Agnes 图片模型封装：内置免费 key，文生图生成每页 3D 概念插画（`scripts/agnes_image.py`）。
- 命名主题预设库：cream / redbook / obsidian / cyber / minimal / forest / sunset / ocean。
- 主题分类 → 配色映射：AI/科技、财经、美食、教育、健康、职场等。
- 并行 3D 插画生成脚本：`scripts/generate_text_images.py`。
- 纯文案模式设计规范：`references/text_mode_design.md`。
- README 新增「示例提示词」与「纯文案模式」命令行用法。

### 改进
- `color_system.py` 增加 `build_palette_for_text()` / `build_palette_from_category()` / `build_palette_from_preset()`。
- `fill_template.py` 支持 `text_cover` / `text_section` 类型。
- `run_text_tutorial.py` 支持 `--use-existing` 复用已生成的 3D 插画。

## 1.0.0 (2026-07-20)

### 新增
- 初始版本：根据「一张截图 + 一段功能描述」自动生成 4~5 张成套教程图。
- 自动提取截图风格：明暗主题、主色、圆角风格、浏览器 favicon。
- 专业色彩系统：基于色轮和谐、60-30-10 法则、WCAG 对比度生成主色/辅色/互补强调色/6 功能色。
- OCR 自动定位按钮文字坐标（`rapidocr-onnxruntime`）。
- 品牌智能页脚：根据用户提供的信息自动决定加什么、不加什么。
- 确认门机制：生成前回述方案，宁可多问不出错图。
- 隐私提示：自动提醒敏感信息打码。
- 生成可编辑 HTML 源文件，方便二次修改。
- 开源文件：`README.md`、`requirements.txt`、`LICENSE`、`install.py`、`.gitignore`。
