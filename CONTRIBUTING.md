# 参与贡献 · Contributing

感谢你愿意为 **Screenshot Tutorial Generator** 贡献代码、文案或示例！本文件说明如何参与。

---

## 一、提 Issues

- **Bug 反馈**：请附上使用的模式（截图 / 纯文案）、输入素材（截图路径或文案 JSON）、报错日志、以及期望效果。
- **功能建议**：说明使用场景，越具体越好（例如「希望纯文案模式支持长图拼接」）。
- 模板类问题：贴出你用的 `jinan_drg.json` / `config.json` 片段，方便复现。

---

## 二、本地开发环境

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-fork>/screenshot-infographic-skill.git
cd screenshot-infographic-skill

# 2. 一键安装依赖（创建隔离 .venv，装 Pillow + rapidocr-onnxruntime，检测浏览器）
python install.py

# 3. 跑通现有示例，确认环境 OK
python run_text_tutorial.py examples/jinan_drg.json --out /tmp/test --use-existing
```

> 纯文案模式的文生图依赖 Agnes API（国内站可直连、免费）。默认内置一个免费兜底 key；
> 想用自己的 key，设环境变量 `AGNES_API_KEY` 即可覆盖（见 README）。

---

## 三、项目结构速览

```
screenshot-infographic-skill/
├── SKILL.md                  # 技能主指令（触发词、双轨流程、关键规则）
├── run_screenshot_tutorial.py# 截图模式端到端
├── run_text_tutorial.py      # 纯文案模式端到端
├── scripts/
│   ├── color_system.py       # 专业色彩系统（截图取色 / 文案主题配色）
│   ├── extract_theme.py      # 从截图提取明暗/主色/圆角
│   ├── ocr_locate.py         # OCR 定位按钮坐标
│   ├── extract_favicon.py    # 从截图标签页提取 favicon
│   ├── crop_region.py        # 按归一化坐标裁剪功能区域
│   ├── agnes_image.py        # 封装 Agnes 文生图 / 图生图（含超时与重试）
│   ├── generate_text_images.py # 并发生成 3D 插画（自愈：重试 + 补漏）
│   ├── fill_template.py      # 填充 HTML 模板
│   └── render.py             # 系统浏览器无头渲染 PNG
├── templates/                # overview / detail / text_cover / text_section
├── references/               # design_notes / color_guide / text_mode_design
└── examples/                 # 示例截图、favicon、成套输出图
```

---

## 四、常见扩展点

### 1. 新增纯文案版式（layout）
- 在 `templates/text_section.html` 增加 `.xxx` 的 CSS 与结构。
- 在 `scripts/fill_template.py` 的 `build_body()` 里加一个分支渲染该 layout 的 HTML。
- 在 `references/text_mode_design.md` 的 Layout 枚举表补一行说明。

### 2. 新增主题预设（preset）
- 在 `scripts/color_system.py` 的 `THEME_PRESETS` 里加一个 `{accent, theme}` 条目。

### 3. 新增文案主题配色（category）
- 在 `color_system.py` 的 `CATEGORY_ACCENT` 里加一个 `主题名: 主色` 映射。

### 4. 调整色彩系统
- 所有取色/和谐/对比度逻辑集中在 `color_system.py`，改这里即可全局生效。

---

## 五、代码风格与自检

- Python 用 4 空格缩进，保持与现有脚本一致；优先用标准库，第三方依赖最小化。
- **提交前请 `py_compile` 自检**：
  ```bash
  python -m py_compile scripts/*.py run_screenshot_tutorial.py run_text_tutorial.py
  ```
- HTML 模板用 CSS 变量占位（`__ACCENT__` 等），不要在模板里写死颜色。
- 插画槽位一律用 `object-fit: contain`，避免 3D 插画被裁切（历史教训）。
- 大数字等易溢出元素，字号用 `clamp()` 并预留左右安全边距。

---

## 六、提交 Pull Request

1. 从 `main` 切出特性分支：`feat/xxx` 或 `fix/xxx`。
2. 保持提交原子化，commit message 用「动作 + 简述」（如 `fix: 大数字元字被裁切`）。
3. 在 PR 描述里说明：改了什么、为什么、如何验证。
4. 同步更新 `CHANGELOG.md`（新增一个 `## x.y.z` 小节）与必要的 `references/` 文档。
5. 维护者 review 通过后合并。

---

## 七、许可证

贡献即表示你同意你的代码在 **MIT License** 下发布。详见 `LICENSE`。
