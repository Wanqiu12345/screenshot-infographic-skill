# Changelog

## 2.0.5 (2026-11-05)

本版针对「陌生人下载后第 2～3 次真实使用会翻车」的一批问题做修复，来源是逐项实测审核
（含带中文+空格路径的净室安装、8 种页型全覆盖、异常图片与恶意配置注入）。

### 安全（务必处理）

- **`scripts/__pycache__/agnes_image.cpython-31{2,3}.pyc` 里残留 v1 的硬编码 API Key**
  和 `apihub.agnes-ai.com` 地址。源码 `agnes_image.py` 在 v2.0.0 已删，但编译产物没删，
  且 `.pyc` 是二进制、普通 grep `*.py` 查不到。**已删除全部 `__pycache__`**（含
  `fill_template` / `color_system` / `generate_text_images` 等 v1 残骸）。
  该 key 从 v1.2.4 起就随源码公开在仓库历史里，**请到 Agnes 后台吊销**——
  删文件不会删历史，clone 后 `git log -p` 仍可翻出。

### 修复：会静默误导用户的

- **`--only` 在 `run_text_tutorial.py` 里 100% 失效**：参数定义成单值字符串，
  `render_cfg` 里 `for n in only` 变成逐字符迭代，报「页名 0,0,_,c,o,v,e,r 不存在」。
  现改为 `nargs="*"`，与 `text_v2.py` 直调语义一致。
- **配置路径写错会静默渲染内置演示并返回 0**：用户以为自己的配置生效了，其实出的是别人的示例图。
  现显式传参即强校验，不存在就报错退出。
- **截图模式会「假成功」**：`render_page` 只看文件是否存在、不看浏览器退出码，也不先删旧图，
  浏览器崩溃时会把上次的旧图当成功。现改为「先删旧图 + 校验退出码 + 校验文件非空」。
- **文案模式渲染失败不影响退出码**（全 FAIL 也返回 0），脚本/CI 无法感知。现失败即退出 1。

### 修复：配置一写错就崩/卡死

- **文案里的 `<script>` 或未闭合标签会让单页卡满 180 秒超时**（实测两个模式都能复现），
  `<span style=...>` 还会直接注入版面。现所有字段统一转义：`b/strong/em/i/br` 白名单保留，
  其他完整标签丢弃，`&<>` 转义；实测注入配置 3 秒正常出图。
- **UTF-8 BOM 的配置直接崩**（`Unexpected UTF-8 BOM`）——中文 Windows 上用记事本存 JSON 默认带 BOM。
  三处读配置统一改 `utf-8-sig`。
- **缺必填字段一律裸 `KeyError` + traceback**：现渲染前统一校验，报「第 N 页（type=chain）缺少必填字段 'steps'」。
- **`meta` / `pg` 文档写成通用字段、代码却是硬取**：实测最小配置直接 `KeyError: 'meta'`。现改为可选，缺省留空。
- **截图模式 coords 高度为 0 触发 `ZeroDivisionError`**：现归一化夹到 [0,1] 并保证至少 1px。

### 修复：体验与环境

- **`install.py` 的失败路径全是裸 traceback**（venv 损坏 → `WinError 216`、离线 → `CalledProcessError`、
  路径含单引号 → 自检命令 SyntaxError）。现每步失败给一句能照做的提示；自检改为经 `argv` 传路径，
  不再把路径拼进 `-c` 源码。
- **跳过 `install.py` 直接跑截图模式 → 双层 traceback**，全程没提「请先运行 install.py」。现启动前检测 Pillow 并直说。
- **文案模式每页在输出目录留 `_prof/` 浏览器配置（7.1 MB/页，超时那页 492 MB）**：
  改为 `mkdtemp` + `finally` 清理，实测输出目录从 42 MB 降到 156 KB。
- **`SAFE_ENV` 只保留 Windows 变量**（无 `HOME`/`LANG`/`TMPDIR`），macOS/Linux 上可能找不到配置目录或字体回退异常；
  `file:///` + 绝对路径在 POSIX 下会拼成 4 个斜杠。现统一走 `render.safe_env()` 与 `pathlib.as_uri()`。
- **超长英文单词溢出被直接裁切**（中文会自动换行，英文 100 字符会冲出边界）：全局加 `overflow-wrap:anywhere`。

### 修复：分发与文档

- **release zip 里的 README 有 7 张图全裂**：`assets/` 与 examples 展示图被排除在包外。
  现随包发出，包体 3.6 MB（图齐全，README 打开即所见）。
- **README 的复制即用命令漏了 `BRAND_URL`**：只设 `BRAND_NAME` 时概览页地址栏仍是作者 demo 网址。
  已补进示例并加提醒。
- `requirements.txt` 加版本上限 `Pillow>=10.0.0,<15`；SKILL.md 删掉代码从不读取的 `total` 字段。

### 验证

净室解压 + 带中文与空格路径安装 + 两条模式端到端 + 全部 8 种页型（stats / chain / timeline /
compare / vs / takeaway / flow / cover）+ 恶意配置 + 异常图片（纯白/纯黑/1×1/8000px/CMYK/伪装 png）全部通过。

## 2.0.4 (2026-11-05)

本版是一次「有人真的在用」之后的全量体检：把两条模式各自跑通、逐项对代码与文档，
修掉 6 处会直接影响使用的问题。**无需改配置，升级即生效。**

### 修复

- **发布包缺 `examples/screenshot.png`，下载 zip 后截图模式演示直接失败**（最严重）。原 `package_skill.py` 把 `examples/*.png` 全部排除，但那张图是 `run_screenshot_tutorial.py` 的默认演示输入，解压后一跑就 `找不到截图`。现改为只排除「示例成图」（`00_`~`05_`、`wf_agent_v2_*`），演示输入随包发出；同时 `run_screenshot_tutorial.py` 在缺图时给出可照做的两条出路，而不是裸报路径。
- **截图模式的「品牌色跟随截图」实际看不见**。`pick_accent()` 一直在正确提取截图主色，但整个渲染器里品牌色只用在细节页左侧竖线的一个 20×20 小圆点上，大标题、编号、分隔线全是固定深蓝 `#12203C`，`brand2` / `brand_tint` 算出来从未使用。拿红色品牌截图进去，出来是「深蓝标题 + 几个暗红褐小点」。现把品牌色注入真正被看见的位置：整页顶部品牌条、内容页大标题、概览页「功能拆解」标题与 01–06 编号、细节页步骤竖线、封面大标题；金色退到强调位。
- **深色截图下品牌色几乎不可见**。原逻辑对深色主题也压到 `v=0.28`，`#151A22` 底上等于糊掉。现按主题分开给明度：浅色底 `v=0.34`、深色底 `v=0.62`，实测深青绿截图从 `#1E4741`（看不见）变为 `#479E91`（清晰）。
- **文案模式 `--only` 写错页名时静默出 0 张**，用户以为成功了。现明确报错并列出配置里的可用页名。
- **文案模式渲染失败不体现在退出码**，脚本全 FAIL 也返回 0，CI/批处理无法感知。现失败即 `SystemExit`。
- **Linux / 容器上中文可能渲染成方框**：字体栈缺 `Noto Sans CJK SC`（思源黑体在各大发行版的实际注册名），CSS 2 处 + SVG 2 处已补。
- **`install.py` 的浏览器查找比渲染器弱一档**：Linux 只查 `/usr/bin` 固定路径、Windows 不查 `LOCALAPPDATA` 安装的 Chrome。现直接复用 `scripts/render.py::find_browser`（Linux 走 `shutil.which` 扫全 PATH），并新增「演示截图是否存在」检查。
- **打包会把临时调试目录一起带走**：实测曾打出 2842 KB / 52 文件的包，里面混进 `_verify_color/` 的 16 张调试图。现以下划线开头的目录一律排除，正常包 19 文件 / 344 KB。

### 文档

- 删掉「文案模式可在配置 JSON 里用 `primary` 字段指定主色」的说法——渲染器从来不读该字段，主色写死在 `TOKENS` 里，README / README_EN / SKILL.md 三处同步更正。
- SKILL.md 的截图模式说明改为如实描述品牌色落在哪些元素、深浅主题各自的明度取值。
- 刷新 `examples/` 下 10 张展示图（旧图还是改版前的视觉，与当前输出不符）。

### 兼容性

两条模式的配置格式、命令行参数均无变化；`scripts/` 内四个模块的公开函数签名除 `pick_accent()` 新增两个带默认值的关键字参数（`v`、`s_cap`）外无改动。

## 2.0.3 (2026-11-05)

### 修复

- **Windows 上 `install.py` 会在装依赖之前中断**（GitHub 用户反馈，本机已复现）。原写法是 `pip.exe install --upgrade pip`，pip 内置的 `protect_pip_from_modification_on_windows()` 会判定「用 pip.exe 改 pip 自己」，先下载完新版本再抛错：

  ```
  ERROR: To modify pip, please run the following command:
  ...\.venv\Scripts\python.exe -m pip install --upgrade pip
  ```

  退出码 1，叠加脚本里的 `subprocess.run(check=True)`，整个安装在装依赖之前就带 traceback 退出。现在统一调 venv 内的 `python -m pip`，绕开 pip.exe 的文件占用。

- **顺带修掉社区建议写法里的一个坑**：把 `pip.exe` 换成 `sys.executable` 只在「已激活 venv」时正确。用户直接用系统 Python 执行 `install.py` 时，`sys.executable` 指向系统解释器，依赖会装进宿主机环境，venv 里仍然没有 Pillow，第 5 步 `import screenshot_v2` 必然 `ModuleNotFoundError`。现在显式使用 `VENV/Scripts/python.exe`，与是否激活 venv 无关。

- **pip 自身升级改为失败不阻断**：内网、代理或镜像源下升级 pip 经常失败，但不影响装依赖，不该因此中断整个安装。

### 新增

- venv 内缺 pip 时自动执行 `python -m ensurepip --upgrade`（部分 Linux 发行版的 `python -m venv` 不自带 pip）。
- venv 创建失败时给出可操作的提示（建议删除 `.venv` 后重试），不再直接抛异常栈。

## 2.0.2 (2026-10-30)

### 修复

- **`compare` / `chain` 页型内容不足时被拉散**：两者原用 `justify-content: space-between` 把条目均匀铺满整页，条目少时上半页和下半页各留一大块空白、中间条目彼此相距 150px 以上（实测一页三条观点时最明显）。改为内容整体居中 + 固定间距：`compare` 用 `center` + `gap:52px`，`chain` 用 `center` + 每步 `padding:44px 0`（连接竖线保持连续）。内容多时仍然自然撑满，不再散架。
- 新增经验：`compare` 页型适合「每侧 4 条以上」或每条说明有 2 行的场景；条目再少建议改用 `flow` 的双窗口拼法，页面更饱满。

## 2.0.1 (2026-10-16)

### 修复

- **封面 `net: "branch"` 示意图的标签原本写死**：固定显示「同一个输入 / TEXT OUT / DECISION」，跨主题复用时会与内容语义对不上（实测做「逆向工具」主题封面时明显跑偏）。新增 `net_labels: {q, left, right}` 覆盖这三处文案，不传则保持默认值，向后兼容。
- 顶部问题条宽度改为随文字长度自适应（`max(400, len*26+80)`），短标题不再显得空、长标题不溢出。

## 2.0.0 (2026-09-18)

### 破坏性变更：移除 v1 模式，单轨化「晚秋简约」引擎

- **`--style` 参数移除**：两个入口（`run_text_tutorial.py` / `run_screenshot_tutorial.py`）不再有 v1/v2 之分，直接走晚秋简约渲染器（`text_v2.py` / `screenshot_v2.py`）。旧 v1 配置（`visual_prompt` 格式）不再兼容。
- **v1 全链路删除**（-2996 行）：`fill_template.py`、`generate_text_images.py`、`agnes_image.py`（Agnes 3D 插画）、`color_system.py`、`crop_region.py`、`ocr_locate.py`、`extract_favicon.py`、`extract_theme.py`、`templates/` 全部 HTML 模板、`references/` 旧设计文档、`examples/jinan_drg_*` v1 示例。保留 `render.py`（浏览器查找 + SAFE_ENV，被两个 v2 渲染器复用）与 `social_post.py`（赠品文案）。
- **依赖精简**：`requirements.txt` 只剩 Pillow；两种模式均为纯排版渲染，**完全离线可跑**，不依赖任何图片生成 API 与 OCR。
- **README / README_EN / CONTRIBUTING 重写**：全部对齐单轨现实（v1 的 Agnes、OCR、templates、references、`--style` 等说明已清除），确保用户拿到即可照做。

### 新增

- **文案模式新页型 `flow`**：终端窗口框（圆点 + 等宽字标签 + 右上角 tag）+ 金色直角分叉连接线 + 概率条（最高项自动强调）+ 选项块（支持 `{text, note}` 注释行）。三种拼法：输入分叉双窗口（冲突对比）、输入 + 选项块（举例）、双窗口直接对比（机制分析）；支持 `mid` 中段文字与 `after`/`after_gray`/`note` 通用底部字段。
- **封面新增 `net: "branch"` 示意图**（一个输入分叉成两种输出）与 `title_size` 字段（长标题降字号）。
- **文案模式入口新增 `--only`**：按页面 name 或文件名只渲染单页，调试用。
- 版面铁律入文档：卡片/窗口高度内容自适应 + 最小高度；密度不够时补叙事内容而非拉大间距。

### 修复

- flow 页选项块拼法中间大片真空（spacer 分配不均）；概率条小数值渲染成小黑点（轨道加粗、填充加深）；双窗口拼法内容飘空（不再 flex 无限撑高）。
- `install.py` 验证步骤对齐单轨（导入 render + social_post）。

## 1.5.0 (2026-09-01)

- **纯文案模式新增 `--style v2`「表意型排版」**：纯排版零插画，视觉元素直接编码内容（竖链=因果、点阵=群体、时间线=演进、三列对比=差异、SVG 示意图封面）；每页 flex 撑满 1080×1440 不留白。渲染器 `scripts/text_v2.py`，示例配置 `examples/wf_agent_v2.json` + 4 张 v2 成图进 `examples/`。
- **修复 `scripts/render.py` 无头渲染隐患**：改为最小环境变量渲染（SAFE_ENV）。宿主注入的 `NODE_OPTIONS` / `ELECTRON_RUN_AS_NODE` / `CHROME_CRASHPAD_PIPE_NAME` 等变量会让 Chromium 无头模式秒退，此前 v1 流程在特定会话环境下会随机失败。
- `README.md` / `README_EN.md` 同步：纯文案模式预览新增 v2 成图（保留 v1 对照）、`--style v2` 用法、配色章节标注 v2 零配置、文案模式流水线图加风格分支、目录树补 `text_v2.py` 与 v2 示例文件。
- 默认行为不变：不带 `--style` 时两种模式均走 v1。

## 1.4.0 (2026-09-01)

### 新增：截图模式 v2「晚秋简约风」（`--style v2`）
- `run_screenshot_tutorial.py` 新增 `--style` 参数：`v1`（默认，老流程行为完全不变）/ `v2`（晚秋简约风）。新增 `build_v2_config()`：从同一套 ITEMS/DETAILS/环境变量自动组装 v2 配置，两种模式共用内容、只切视觉语言。
- 新增渲染器 `scripts/screenshot_v2.py`：纯排版 + 1px 细线，无彩虹功能色、无渐变徽章、无重投影、无 3D 插画。品牌色从截图主色自动推导（HSV 降饱和至 ≤0.58、亮度压至 0.28），金色 `#B08D45` 小面积强调；深浅主题随截图自动判定；每页 flex 撑满 1080×1440 不留大空白。
- v2 细节裁剪为「碎片」：只加细线框、不加浏览器假地址条；高度 < 300px 的控件碎片自动放大（最多 2 倍）。步骤区为竖向轨道 + 「STEP 标题行 / 说明行」两行结构。
- v2 无头渲染强制传最小环境变量（PATH/SYSTEMROOT/TEMP/TMP/USERPROFILE）：宿主注入的 `NODE_OPTIONS` 等变量会让 Edge 无头模式秒退。
- `DETAILS` 的 `chat_gen` 新增 `coords_v2` 字段（v2 模式用更聚焦的输入栏裁剪框 0.26,0.875,0.50,0.115），v1 流程忽略该字段。
- `SKILL.md` 新增「风格选择（v1 经典 / v2 晚秋简约）」章节。
- `README.md` / `README_EN.md` 同步更新：效果预览替换为 v2 成图、新增两种风格说明与 `--style v2` 命令行示例、目录结构补 `screenshot_v2.py`、FAQ 新增风格选择问答。`examples/` 的截图模式预览图（00~05）全部替换为 v2 输出。
- README 二次补全（同日）：「它能帮你解决什么」表格、场景一话术（加「用 v2 晚秋简约风」示例）、安装验证（`--style v2` 演示命令）、配置章节（v2 零配色配置说明）、工作原理流水线图（风格选择分支）。纯文案模式章节与 jinan_drg 预览图未动——该模式代码本次无改动，图文保持一致。

## 1.3.6 (2026-08-14)

### 新增：纯文案模式 visual_prompt 显式校验 + slogan 放宽
- `run_text_tutorial.py` 新增 `validate_visual_prompts(cfg)`：文生图前检查 `cover` 与每个 `page` 的 `visual_prompt` 是否非空；缺失则 `sys.exit` 报错并明确列出缺了哪几页（带 `page_title` / `layout` 便于定位），把「静默生成空白占位」变成「跑命令瞬间就被告知」。
- 新增 `--no-validate` 开关（默认开启校验），资深用户可跳过。
- 封面 slogan 截断上限由 12 字放宽到 24 字（`_short_line(..., 24)`），避免短截产生「…」残句；`cover.html` 的 `.slogan` 支持自然换行。
- 同步更新 `SKILL.md`：版本号与 slogan 上限说明。

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
