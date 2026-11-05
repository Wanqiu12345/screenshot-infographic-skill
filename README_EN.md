# 📸 Screenshot & Text → Infographic Generator

> **TL;DR**: You send **one screenshot** or **a paragraph of text**, and this AI skill generates a complete set of on-brand tutorial / infographic images — ready to post on Xiaohongshu, WeChat, or any community. No design or coding needed.

> 🇨🇳 中文文档：[README.md](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![Version](https://img.shields.io/badge/version-2.0.5-1A3A6B.svg)](CHANGELOG.md)

![Cover](assets/cover.png)

---

## What it solves

Making product tutorial images is tedious: manual cropping, inconsistent styling, time-consuming layout. This skill handles all of it:

| You provide | It returns |
|---|---|
| One screenshot + a feature description | 1 cover + 1 overview + several per-feature detail images |
| A paragraph of text (a topic) | 1 cover + several content-page infographics |

All images are **1080×1440 (3:4 portrait) high-res PNG** (rendered at 2× = 2160×2880), with consistent footers and page numbers.

Visual style is "late-autumn minimal": a single brand color (auto-derived from your screenshot in screenshot mode; default deep blue `#1A3A6B` in text mode) + muted gold accents + warm white background + 1px hairline separators. Pure typography, **works fully offline** — no illustration APIs, no OCR, no external services.

## Two modes

### Mode 1: Screenshot → Feature tutorial

Send a product screenshot + a feature description. Returns a minimal cover, an overview (features broken into cards), and per-feature detail pages (auto-cropped regions, zoomed in). Brand color is auto-derived from the screenshot's dominant color, and the light/dark theme follows the screenshot's average brightness.

### Mode 2: Text → Infographic

Send a topic or copy. The AI structures it into pages and renders them with "semantic layouts" — visual elements that encode meaning: vertical chains = causality, timelines = evolution, comparison tables = differences, terminal-window flow diagrams (with connector lines, probability bars, option chips), big-number pages, and takeaway pages.

**8 page types**, chosen by what the content means — not a template library:

| `stats` big numbers | `timeline` |
|---|---|
| ![stats](examples/page_stats.png) | ![timeline](examples/page_timeline.png) |

| `flow` terminal-window comparison |
|---|
| ![flow](examples/page_flow.png) |

Plus `cover`, `chain` (vertical causality), `compare` (two-column), `vs` (row-by-row table), `takeaway` (closing verdict).
Field reference in [SKILL.md](SKILL.md); runnable minimal config in [examples/all_page_types.json](examples/all_page_types.json).

## Who it's for (and who it isn't)

**Good fit:** indie developers who need a feature-tour set without a designer; writers producing 5–10 consistent portrait images per article; anyone who **cannot upload screenshots or drafts to an online service** (intranet, NDA, regulated environments); people who want to script the pipeline (JSON config in, CLI out).

**Not a fit:** anyone expecting "type a sentence, get a beautiful AI illustration" — this tool does **not generate illustrations**, it typesets; teams needing drag-and-drop editing, multiplayer, or share links (use Scribe / Canva instead); people who need a million-template library — we ship 8 page types, enough but not fancy.

The trade-off is deliberate: **trading template count for text that never renders wrong, pixel-precise layout, and offline reproducibility.** For an infographic, the text and numbers *are* the product — exactly where generative models are least reliable.

## Installation

Prerequisites: **Python 3.10+** and a Chromium-based browser (Edge on Windows, Chrome on macOS, Chromium on Linux).

```bash
git clone https://github.com/Wanqiu12345/screenshot-infographic-skill.git
cd screenshot-infographic-skill
python install.py          # creates an isolated .venv, installs Pillow, checks browser
```

Then copy the folder into your client's skill directory:

| Client | Directory |
|---|---|
| Claude Code | `~/.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` |

### Verify the install

```bash
python run_text_tutorial.py        # renders the bundled demo to output_text/
python run_screenshot_tutorial.py  # renders the bundled demo screenshot to output/
```

If `00_cover.png` and friends appear in the output directory, you're set ✅.

## Usage

The recommended way is simply talking to your AI assistant:

> Use the `screenshot-infographic-skill` skill to make a feature tutorial set from this screenshot. Features: ... Brand name: ...

> Use the `screenshot-infographic-skill` skill to make an infographic set about: "What is X, explained simply".

Before generating anything, the skill **reads its plan back to you for confirmation** (page count, layout per page, copy direction, footer brand) — it would rather ask than produce wrong images.

CLI (for automation):

```bash
# Text mode: render a structured config JSON
python run_text_tutorial.py my_config.json --out my_output_dir
python run_text_tutorial.py my_config.json --out my_output_dir --only 03_page_name   # single page for debugging

# Screenshot mode: brand info via env vars
SCREENSHOT=/path/to/your.png BRAND_NAME="Your Product" BRAND_URL=https://your.site/ python run_screenshot_tutorial.py
# Don't skip BRAND_URL: otherwise the browser bar in the overview page keeps the demo URL
```

Config field reference for text mode lives in [SKILL.md](SKILL.md); a working example is [examples/wf_agent_v2.json](examples/wf_agent_v2.json).

## How it works

```mermaid
flowchart LR
    A[Screenshot + description / topic text] --> B[AI structures content into pages]
    B --> C[Plan read-back confirmation]
    C --> D[Headless browser renders 3:4 PNG set]
```

Key technical points:

- **Brand color auto-derivation**: dominant screenshot color desaturated and darkened into a single brand color (screenshot mode).
- **Semantic layouts**: pages fill 1080×1440 via `flex:1` — no large empty areas.
- **SAFE_ENV headless rendering**: minimal environment variables passed to the browser, avoiding crashes caused by injected `NODE_OPTIONS` / `ELECTRON_RUN_AS_NODE` in host environments.
- **Editable HTML kept**: text mode writes HTML sources to `_html/` inside the output dir; screenshot mode keeps its HTML, `crop_*.png`, `screenshot_config.json` and `theme_tokens.json` in the output root. Re-run to re-render after edits.
- **No API key, no network**: the skill never calls an image-generation model. If you need illustrations, let the host AI client (e.g. WorkBuddy's ImageGen) produce them and let this skill handle layout only — credentials stay with the client.

## Repository layout

```text
screenshot-infographic-skill/
├── SKILL.md                      # Main instructions + config field reference
├── run_screenshot_tutorial.py    # Screenshot mode entry
├── run_text_tutorial.py          # Text mode entry
├── install.py                    # One-command installer
├── scripts/
│   ├── text_v2.py                # Text mode renderer (8 page types)
│   ├── screenshot_v2.py          # Screenshot mode renderer
│   ├── render.py                 # Headless browser rendering (SAFE_ENV)
│   ├── social_post.py            # Bonus social-media copy generator
│   └── package_skill.py          # Distributable zip packer
├── assets/                       # README cover image
└── examples/                     # Demo inputs and outputs
```

## Known limitations

1. **System fonts** → minor line-break differences across OSes (never clipping). Generate a set on one machine.
2. **Sparse content leaves white space** — give each page at least 3–4 items.
3. **No online editor** — edit JSON/HTML and re-render.
4. **PNG only** — no SVG/PDF/PPT export.
5. **Up to 180 s per page**, no progress output. Normal pages take 2–16 s.

## Notes & gotchas

- **A Chromium-based browser is required** for rendering. On headless Linux servers, install one first (`sudo apt-get install -y chromium` on Debian/Ubuntu). `render.py` auto-detects and passes `--no-sandbox` / `--disable-dev-shm-usage` for containers.
- Outputs go to `output/` (screenshot mode) and `output_text/` (text mode), both gitignored.
- All paths are relative (`__file__`-based) — the folder runs from anywhere.

## FAQ

**Q: What resolution are the images?**
A: 1080×1440 portrait 3:4, rendered at 2× (2160×2880).

**Q: Can I customize colors?**
A: Screenshot mode derives the brand color from your screenshot automatically. Text mode uses a fixed palette (deep blue `#1A3A6B` + matte gold `#B08D45` + warm white `#FBFAF8`) defined in `TOKENS` inside `scripts/text_v2.py`; the config JSON cannot override it, which keeps a series of images visually consistent.

**Q: Does it need internet or an image-generation API?**
A: No. Both modes are pure typographic rendering — fully offline after install, and your screenshots or drafts never leave your machine.

**Q: Why not use an image-generation model?**
A: Because infographics are made of exact text and numbers. Generative models misdraw letters and digits, cannot guarantee consistent typography across a 12-page set, and give different output for the same input. We render HTML/CSS/SVG through a headless browser instead — the same approach as Vercel Satori and Puppeteer. The cost is a fixed layout library; the benefit is that not a single character renders wrong.

**Q: Slight layout differences between two machines?**
A: Known limitation. Rendering uses system fonts (YaHei on Windows / PingFang on macOS / Noto on Linux), so line breaks shift a little. Nothing gets clipped, but generate a whole set on one machine.

**Q: Can I get SVG / PDF / PPT?**
A: Not yet — PNG only.

**Q: Images have blank areas or misplacement?**
A: Check your config JSON field names first (e.g. timeline uses `nodes`, not `events`; chain `steps` are arrays, not dicts). Full reference in [SKILL.md](SKILL.md).

## Contributing / License

- PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
- MIT License, see [LICENSE](LICENSE).
- Changelog: [CHANGELOG.md](CHANGELOG.md).

---

Made for people who hate making tutorial screenshots by hand. 🙌
