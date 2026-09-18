# 参与贡献 · Contributing

感谢你愿意为 **Screenshot Tutorial Generator** 贡献代码、文案或示例！本文件说明如何参与。

---

## 一、提 Issues

- **Bug 反馈**：请附上使用的模式（截图 / 纯文案）、输入素材（截图路径或文案 JSON）、报错日志、以及期望效果。
- **功能建议**：说明使用场景，越具体越好（例如「希望文案模式支持新的页型」）。
- 配置类问题：贴出你用的配置 JSON 片段（含 `slug` 和 `pages`），方便复现。

---

## 二、本地开发环境

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-fork>/screenshot-infographic-skill.git
cd screenshot-infographic-skill

# 2. 一键安装依赖（创建隔离 .venv，装 Pillow，检测浏览器）
python install.py

# 3. 跑通现有示例，确认环境 OK
python run_text_tutorial.py                      # 文案模式演示，输出到 output_text/
python run_screenshot_tutorial.py                # 截图模式演示，输出到 output/
```

两种模式都是纯排版渲染（无头浏览器 + Pillow），不依赖任何外部 API，离线可跑。

---

## 三、项目结构速览

```
screenshot-infographic-skill/
├── SKILL.md                  # 技能主指令（触发词、配置字段规范、关键规则）
├── run_screenshot_tutorial.py# 截图模式端到端入口
├── run_text_tutorial.py      # 纯文案模式端到端入口
├── scripts/
│   ├── text_v2.py            # 文案模式渲染器（表意型排版，7 种页型）
│   ├── screenshot_v2.py      # 截图模式渲染器（晚秋简约风）
│   ├── render.py             # 无头浏览器渲染 PNG（SAFE_ENV 环境隔离）
│   ├── social_post.py        # 随图附赠小红书发布文案
│   └── package_skill.py      # 打包分发 zip
└── examples/                 # 示例截图、示例配置、成套输出图
```

---

## 四、常见扩展点

### 1. 新增文案模式页型（type）
- 在 `scripts/text_v2.py` 里加一个 `p_xxx(p)` 构造函数（复用 `_page()` 骨架，注意 `flex:1` 撑满、不留大片真空）。
- 在 `BUILDERS` 注册字典里加一行。
- 在 `SKILL.md` 的「页面类型」表格补一行字段说明。
- 在 `examples/` 加一份示例配置或页面。

### 2. 新增封面示意图（net）
- 在 `scripts/text_v2.py` 里加一个返回 SVG 字符串的函数（参考 `flow_vs_loop` / `branch_svg`），并在 `p_cover` 的 `net` 分支里注册。

### 3. 调整截图模式视觉
- 晚秋简约的配色推导、卡片样式集中在 `scripts/screenshot_v2.py`。

### 4. 无头渲染
- 浏览器查找与环境隔离逻辑集中在 `scripts/render.py`（`find_browser` + `SAFE_ENV`）。**不要绕过它裸调浏览器**——宿主注入的 `NODE_OPTIONS` 等环境变量会让 Chromium 无头模式秒退。

---

## 五、代码风格与自检

- Python 用 4 空格缩进，保持与现有脚本一致；优先用标准库，第三方依赖最小化（目前仅 Pillow）。
- **提交前请 `py_compile` 自检**：
  ```bash
  python -m py_compile scripts/*.py run_screenshot_tutorial.py run_text_tutorial.py
  ```
- 渲染器内 CSS 用 `__PLACEHOLDER__` 占位（如 `__BRAND__` / `__LINE__`），不要写死颜色。
- 卡片 / 窗口高度用「内容自适应 + 最小高度」，不要 `flex:1` 无限撑高（内容会飘空）。
- 大数字等易溢出元素，字号用 `clamp()` 并预留左右安全边距。
- 每页必须 `flex:1` 撑满 1080×1440，**不允许大片真空**；密度不够时优先补叙事内容而不是拉大间距。

---

## 六、提交 Pull Request

1. 从 `main` 切出特性分支：`feat/xxx` 或 `fix/xxx`。
2. 保持提交原子化，commit message 用「动作 + 简述」（如 `fix: 概率条小数值渲染成黑点`）。
3. 在 PR 描述里说明：改了什么、为什么、如何验证。
4. 同步更新 `CHANGELOG.md`（新增一个 `## x.y.z` 小节）与 `SKILL.md` 里受影响的字段说明。
5. 维护者 review 通过后合并。

---

## 七、许可证

贡献即表示你同意你的代码在 **MIT License** 下发布。详见 `LICENSE`。
