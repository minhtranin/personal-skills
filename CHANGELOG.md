# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
