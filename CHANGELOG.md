# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [VOXUANTHUAN-m10] - 2026-04-26

### Removed
- `skills/excalidraw/` — entire excalidraw skill dropped (Playwright/Chromium renderer was unreliable due to CDN ESM loading failures in headless mode)
- All diagram steps across `ps:summary` no longer reference excalidraw scripts or `render_excalidraw.py`
- `excalidraw` command removed from `ps:bot-telegram` help text, skill registry, and BotFather command list

### Changed
- `ps:summary` — diagram steps (Y8, M6, J8, G6, A6, S7) now generate a self-contained HTML file at `/tmp/summary_diagram.html` — pure HTML + CSS, no external deps, open directly in Chrome
- `ps:summary` — HTML diagram format guidelines updated: pick the right visual per section (cards+arrows for flows, `<table>` for comparisons, `<ul>` tree for hierarchies, timeline for sequences, inline bars for metrics)

## [VOXUANTHUAN-Cr7] - 2026-04-25

### Fixed
- `detect_type.py` — recognize Medium partner domains: `gitconnected.com`, `towardsdatascience.com`, `betterprogramming.pub`, `plainenglish.io`
- `ps:summary` SKILL.md — all 6 save sections now document required CLI args (`--slug`, `--url`, `--summary`, etc.) instead of bare commands

## [JUNVO-08] - 2026-04-24

### Added
- `ps:summary` — unified summary skill that auto-detects content type (YouTube, Medium, Jira, GitHub, AWS/Amazon blog, Slack) from URL or issue key using a lightweight Python detector (`detect_type.py`)

### Removed
- `ps:tube-summary`, `ps:medium-summary`, `ps:jira-summary`, `ps:github-summary`, `ps:amazon-summary`, `ps:slack-summary` — replaced by `ps:summary`

## [junvo-gift-07] - 2026-04-24

### Removed
- `ps:excalidraw` skill — command removed (excalidraw scripts remain as shared renderer for other skills)

## [junvo-gift-06] - 2026-04-18

### Fixed
- `install.sh` — corrected Antigravity skills install path from `~/.gemini/antigravity/global_skills` to `~/.gemini/antigravity/skills`

## [junvo-gift-05] - 2026-04-17

### Changed
- `ps:jira-plantask` — added task design rules: no file overlap between tasks, include Acceptance Criteria and Where to Test in every task

## [junvu-gift-04] - 2026-04-17

### Added
- `scripts/jira/jira_adf.py` — markdown-to-ADF (Atlassian Document Format) converter supporting headings, tables, bullet lists, ordered lists, bold text, code blocks, and horizontal rules
- Subtask descriptions now render as **proper Jira formatting** (headings, tables, bullet lists) instead of flat text paragraphs

### Changed
- `ps:jira-plantask` — subtask description template redesigned: `## Goal` + `## Changes` (Area|Change|Impact table) + `## Acceptance Criteria` + `## Where to Test`
- `ps:jira-plantask` — inline `text_to_adf` replaced with shared `jira_adf` module in both create (Step 6) and edit (Step 9) scripts
- `ps:jira-plantask` — custom subtask flow (Step 7) updated to collect changes as table rows

## [junvu-gift-03] - 2026-04-15

### Changed
- `ps:pr-create` — PR description now uses table format (Area | Fix | Impact) instead of bullet points for better readability on GitHub

## [junvu-gift-02] - 2026-04-15

### Added
- `ps:pr-create` skill — create GitHub PRs using team standard format (FEAT/FIX prefix, GRAP ticket, Jira link, short bullet summary, no co-author)

## [thuanvo-gift-0.1] - 2026-04-02

### Changed
- All summarizer skills now use **ASCII tree / hierarchy style** output instead of flat markdown headers
- Each skill has a consistent tree structure tailored to its content type:
  - `ps:jira-summary` — metadata header + SUMMARY + KEY POINTS (PROBLEM/SCOPE/FIX/ALTERNATIVES/BLOCKERS/DECISION) + COMMENT HIGHLIGHTS
  - `ps:tube-summary` — VIDEO_ID header + SUMMARY + KEY POINTS
  - `ps:medium-summary` — SLUG/Author/URL header + SUMMARY + KEY POINTS
  - `ps:amazon-summary` — metadata header + SUMMARY (PROBLEM/SOLUTION/BUILD/OUTCOMES) + KEY POINTS + TECH STACK
  - `ps:github-summary` — repo/stars header + SUMMARY + KEY POINTS (PURPOSE/TECH STACK/ARCHITECTURE/FEATURES/ACTIVITY/GETTING STARTED)
  - `ps:slack-summary` — channel/replies header + SUMMARY + KEY POINTS (DECISIONS/ACTION ITEMS/OPEN QUESTIONS/NOTABLE REACTIONS) + PARTICIPANTS

## [0.5.8] - 2026-04-02

### Fixed
- `save_medium.py`, `save_summary.py` (tube), `save_github_summary.py`, `save_amazon_summary.py`: diagram PNG is now copied from `/tmp/` to a persistent `~/.{medium,youtube,github,amazon}-summary/diagrams/<slug>.png` on save — diagrams no longer disappear after reboot
- All four skills now store the persistent path in `diagram_png` so the web server at `/medium/<slug>`, `/youtube/<id>`, etc. can always serve the image

### Changed
- `ps:medium-summary` SKILL.md Step 3: diagram instruction updated to generate **full architectural/technical diagrams** (not concept map summaries), and to re-call `save_medium.py` with `--diagram-png` after rendering so the persistent copy is made
- `ps:tube-summary` SKILL.md Step 6: same full-diagram instruction + persistent path note
- `ps:github-summary` SKILL.md diagram step: persistent path note added

## [0.5.7] - 2026-04-01

### Fixed
- `excalidraw` renderer: all text elements now use fontFamily `3` (Nunito clean sans-serif) instead of the default hand-drawn Virgil font — diagrams are now readable at all sizes
- `install.sh`: replaced "Manage:" curl command block at end of install output with latest release changelog from GitHub API

## [0.5.2] - 2026-03-30

### Fixed
- `ps:web`: key points now rendered as bullet list on detail pages — handles `|`-separated (GitHub), newline-separated (YouTube/Medium/etc.), and strips leading `-`/`•`/`*` chars

## [0.5.1] - 2026-03-30

### Added
- `ps:web`: GitHub tab and detail history page — shows all `/ps:github-summary` results with full_name, language, stars, description, topics, diagram

### Changed
- `ps:web` nav now includes GitHub count alongside YouTube, Medium, Jira, Slack
- GitHub history loaded directly from `~/.github-summary/*.json` (slug-per-file, no index.json)
- Clear history supports GitHub scope

## [0.5.0] - 2026-03-30

### Added
- `excalidraw` skill namespace — extracted from `tube` into its own standalone namespace (`skills/excalidraw/`)
- `skills/excalidraw/ps:excalidraw/SKILL.md` — full rewrite using upstream [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill): visual argument methodology, multi-zoom architecture, evidence artifacts, render-validate loop, section-by-section JSON strategy
- `skills/excalidraw/scripts/check_deps.sh` — checks `uv` + `playwright`, installs if missing
- `skills/excalidraw/scripts/references/` — `render_excalidraw.py`, `render_template.html`, `color-palette.md`, `element-templates.md`, `pyproject.toml`

### Changed
- All summary skills (`tube`, `medium`, `jira`, `slack`, `github`) migrated to new excalidraw renderer: `uv run python render_excalidraw.py` via `scripts/excalidraw/references/`
- Playwright dependency check replaced with `check_deps.sh` in all summary skills
- `tube/check_deps.sh`: `pip3` → `uv tool install` (yt-dlp), `uv pip install` (libs)
- `bot/setup.sh`: `pip3 install` → `uv pip install`
- `bot/telegram_bot.py`: install hints → `uv pip install`
- `bot/ps:bot-telegram`: dep check and launch commands use `uv run --with`
- `slack/check_slack_tokens.sh`: `pip3 install` → `uv pip install`
- `tube/web_server.py`, `tube/get_transcript.sh`: install hints → `uv`

### Removed
- `skills/tube/ps:excalidraw/` — old excalidraw command (now in `skills/excalidraw/`)
- `skills/tube/scripts/excalidraw/` — old renderer scripts (`render_excalidraw.py`, `render_template.html`, `setup.sh`)
- `skills/tube/scripts/renderer/` — old node_modules-based renderer

## [0.3.3] - 2026-03-29

### Removed
- `/ps:slack-login` command — no longer needed, tokens auto-extracted from Slack desktop app

### Changed
- `check_slack_tokens.sh`: auto-extract from Slack desktop app storage first (LevelDB), then fallback to saved file, then manual F12 instructions
- `get_slack_tokens.py`: added Linux Snap and Flatpak storage paths, fixed WSL detection for Windows username
- `ps:slack-summary` auth error now refers to manual re-extraction via F12 + `save_slack_tokens.py`

## [0.3.2] - 2026-03-29

### Added
- `/ps:excalidraw` — generate Excalidraw diagrams from description and render to PNG via Playwright + headless Chromium
- Optional diagram step in all summary skills (`/ps:tube-summary`, `/ps:medium-summary`, `/ps:jira-summary`, `/ps:slack-summary`) — silently skipped if `playwright` is not installed
- `render_excalidraw.py` + `render_template.html` renderer using `@excalidraw/excalidraw` ESM CDN
- `setup.sh` for one-time Playwright + Chromium install
- Fixed remote install to preserve subdirectory structure under `scripts/`

## [0.3.1] - 2026-03-29

### Changed
- All summary skills now output result immediately before optional diagram step
- User prompted: "Want a diagram for this? (y/n)" after each summary
- Diagram is saved after display and updates the history entry with the PNG path
- Web UI `/ps:web` now shows embedded diagrams on detail pages via `/diagram` route

## [0.3.0] - 2026-03-29

### Added
- `/ps:excalidraw` — generate Excalidraw diagrams from a description and render to PNG via Playwright + headless Chromium
- Optional diagram step in all summary skills (`/ps:tube-summary`, `/ps:medium-summary`, `/ps:jira-summary`, `/ps:slack-summary`) — silently skipped if `playwright` is not installed
- `render_excalidraw.py` + `render_template.html` renderer using `@excalidraw/excalidraw` ESM CDN
- `setup.sh` for one-time Playwright + Chromium install
- Fixed remote install to preserve subdirectory structure under `scripts/`

## [0.2.0] - 2026-03-29

### Added
- `/ps-medium-summary` — fetch Medium articles via Freedium mirror, summarize with history cache
- `/ps-jira-summary` — fetch Jira issue description + all comments, summarize with history cache
- `/ps-jira-plantask` — research codebase, produce implementation plan, break into independent subtasks, create in Jira, guide step-by-step implementation
- `/ps-slack-summary` — fetch Slack thread + all replies using xoxc/xoxd tokens and summarize
- `/ps-slack-login` — guided setup to save Slack session tokens (DevTools extraction guide)
- `/ps-web` now shows YouTube, Medium, Jira, and Slack summaries in a unified UI with per-source tabs
- `/ps-web` Clear History button with per-namespace confirmation UI

## [0.1.0] - 2026-03-29

### Added
- `/ps-tube-summary` — download YouTube transcript and summarize with history cache
- `/ps-web` — local Flask web UI to browse summary history
- `--refresh` flag to bypass history cache and re-fetch
- Auto-bootstrap: scripts auto-download on first use if missing
- `install.sh` with `--version`, `--update`, `--version-check` flags
- Supports Claude Code, Antigravity, OpenCode
