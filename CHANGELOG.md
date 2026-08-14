# Changelog

## 1.3.5 (2026-08-14)

### 修复：截图模式赠品文案改用真实产品名（不再写死 demo 品牌）
- `run_screenshot_tutorial.py`：`BRAND` / `URL` / `SUBTITLE` / `CATEGORY` 改为环境变量可覆盖（`BRAND_NAME` / `BRAND_URL` / `BRAND_SUBTITLE` / `BRAND_CATEGORY`），保留内置 demo 产品作为一键演示默认值。
- 封面主/副标题由新增的 `_split_brand()` 从真实产品名自动推导（仅按 `·` / `.` 断行，空格保留完整品牌），不再硬编码。
- 随图赠品文案（social_post）的 `category` 改用真实分类、收尾金句改为通用表述、话题标签由模块按「栏目 + 产品名」自动推导；标题始终含真实产品名且 < 20 字。
- `SKILL.md` 确认门补充说明：跑截图模式前必须用 `BRAND_NAME` 等环境变量传入截图对应产品的真实信息，默认品牌不可直接用于用户自己的截图。

## 1.3.4 (2026-08-14)

### 新增：随图附赠小红书发布文案
- 新增 `scripts/social_post.py`：两张图集产出后，自动从配置提炼「主题/导语/要点/收尾」生成一段可直接发小红书的文案，写入 `<out>/social_post.md`。
- 标题严格 **< 20 字**（中英文/空格均按 1 字计），随机抽 1 个主标题 + 2 个备选标题，方便挑顺眼的用。
- 正文为「一句话导语 + 要点（最多 4 条，取页面/功能标题）+ 收尾金句 + 话题标签」，平实干净、不使用「说白了/神器/疯狂」等营销腔，遵循技能文案质量准则。
- 纯文案模式：`run_text_tutorial.py` 从 `title/brand/category/cover/各页 page_title+summary` 推导；截图模式：`run_screenshot_tutorial.py` 从 `BRAND/SUBTITLE/功能卡片` 推导。
- 纯标准库实现，不依赖第三方包，两个运行脚本都能直接 import；结果可复现（仅标题随机）。

## 1.3.3 (2026-08-14)

### 优化：纯文案模式内容页改为垂直流式布局
- `templates/text_section.html` 默认从「左文右图双栏」改为「全宽垂直流式」：标题/导语 → 内容 → 插画 → 补充内容 → 总结，阅读动线更自然。
- `grid_cards` 4 项时自动拆成 **2 张在插画上方 + 2 张在插画下方**，插画真正居中，彻底解决左下角大空白、卡片被压窄的问题。
- 其余 layout（timeline / metrics / spec_list / definition 等）默认走全宽，不再挤在窄栏里。
- 插画区域加 `min/max-height` 与 `flex` 自适应：内容少时插画吸收多余空间防空白，内容多时插画收缩防溢出。
- 所有正文加 `-webkit-line-clamp` 兜底，避免极端长文案撑破页面。
- 保留 `page_mode: "split"` 可显式切回旧双栏（兼容旧偏好）。

### 修复：纯文案模式封面不再把空格产品名拆成主/副标题
- `run_text_tutorial.py` 的 `_distill_main/_distill_sub` 移除空格分隔符，只按 `·` / `.` 拆分。
- 修复 `"DeepSeek Harness"` 被错误拆成 `"DeepSeek"`（大标题）+ `"Harness"`（小副标题）的问题；多词产品名现在整体作为封面大标题。

## 1.3.2 (2026-07-24)

### 更名：统一为仓库名 screenshot-infographic-skill
- 技能目录、SKILL.md `name`、分发 zip、文档示例中的 `screenshot-tutorial-generator` 全部统一为 **`screenshot-infographic-skill`**（与 GitHub 仓库名一致）。
- 分发包改为 `release/screenshot-infographic-skill.zip`，解压后顶层文件夹同名，旧 zip 移除。
- 老用户升级：删除旧目录 `~/.workbuddy/skills/screenshot-tutorial-generator`，解压新包即可，功能无任何变化。

## 1.3.1 (2026-07-24)

### 新增：spec_list 布局 + 文案质量准则
- 纯文案模式新增 `spec_list` 布局（标签+内容行），适合「名称/适用人群/使用场景」这类小白友好的规格页。
- `SKILL.md` 新增「文案质量准则」：平实、干净、准确，禁止「说白了/神器/上头」等口水词与营销腔。
- 新增 `scripts/package_skill.py` 打包脚本，约定每次提交随代码分发 zip。

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
