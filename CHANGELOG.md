# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
