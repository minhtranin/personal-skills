# personal-skills — Claude Code project guide

A monorepo of personal productivity skills installed via a single `curl | bash` command.

## How installation works

```
install.sh  (curl-pipe or local)
  ├── downloads/copies scripts → ~/.local/share/personal-skills/scripts/<namespace>/
  └── copies SKILL.md files   → ~/.claude/commands/, ~/.antigravity/commands/, ~/.opencode/commands/
                                 (only for agents whose directory already exists)
```

`install.sh` auto-discovers all namespaces — adding a new skill never requires editing it.

## Project structure

```
skills/<namespace>/
  ps-<command>/SKILL.md    # one file per command → installed as /ps-<command>
  scripts/                 # helper scripts, installed to ~/.local/share/personal-skills/scripts/<namespace>/
```

## Conventions

- **Command prefix:** All commands use `ps-` prefix (e.g. `/ps-tube-summary`, `/ps-web`).
- **Bootstrap in Step 0:** Every SKILL.md checks if scripts are present at runtime. If not, it runs the curl installer automatically before proceeding.
- **History check first:** Every "fetch/summarize" command checks local history before doing any network work. Use `lookup_history.py` and offer the cached result.
- **`--refresh` flag:** Bypass history cache and re-fetch.
- **Dependency check:** Every command runs `check_deps.sh` (or namespace equivalent) before doing work that needs external tools. The script prompts to install if missing.
- **Scripts path:** Always `$HOME/.local/share/personal-skills/scripts/<namespace>/`.

## Current skills

| Namespace | Commands | Status |
|---|---|---|
| `tube` | `/ps-tube-summary`, `/ps-web` | Active |
| `medium` | `/ps-medium-summary` | Active |
| `jira` | `/ps-jira-summary`, `/ps-jira-plantask` | Active |
| `slack` | `/ps-slack-login`, `/ps-slack-summary` | Active |
| `github` | `/ps:github-summary` | Active |
| `frontend` | `/ps:frontend-ui` | Active |
| `excalidraw` | `/ps:excalidraw` | Active |

## Adding a new skill namespace

1. Create `skills/<namespace>/scripts/` with helper scripts
2. Create `skills/<namespace>/ps-<name>/SKILL.md` for each command
3. Add Step 0 bootstrap check to each SKILL.md
4. Update the skills table above and in README.md
5. `install.sh` picks it up automatically — no edits needed

## Scripts reference

### `tube` namespace
| Script | Purpose |
|---|---|
| `check_deps.sh` | Checks yt-dlp, python3, flask — prompts to install if missing |
| `get_transcript.sh <url>` | Downloads VTT via yt-dlp, outputs clean plain text |
| `lookup_history.py <url>` | Exit 0 + JSON if cached, exit 1 if not found |
| `save_summary.py` | Saves entry to `~/.youtube-summary/` |
| `web_server.py` | Flask server for browsing all history (YouTube/Medium/Jira/Slack) |

### `jira` namespace
| Script | Purpose |
|---|---|
| `check_jira_credentials.sh` | Validates `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL` env vars |
| `fetch_jira.py <key>` | Fetches issue + all comments via Jira REST API v3 |
| `lookup_jira.py <key>` | History cache lookup for Jira issues |
| `save_jira_summary.py` | Saves entry to `~/.jira-summary/` |

### `excalidraw` namespace
| Script | Purpose |
|---|---|
| `check_deps.sh` | Checks uv + playwright, installs if missing |
| `references/render_excalidraw.py` | Renders `.excalidraw` JSON to PNG via Playwright |
| `references/render_template.html` | HTML template used by the renderer |
| `references/color-palette.md` | Brand colors and semantic color mapping |
| `references/element-templates.md` | Copy-paste JSON templates for Excalidraw elements |
| `references/pyproject.toml` | uv project config for playwright dependency |

### `slack` namespace
| Script | Purpose |
|---|---|
| `check_slack_tokens.sh` | Checks saved/env/auto-extracted tokens; prints DevTools guide if none found |
| `get_slack_tokens.py` | Scans Slack desktop LevelDB storage to auto-extract xoxc/xoxd tokens |
| `save_slack_tokens.py` | Validates + saves xoxc/xoxd to `~/.local/share/personal-skills/slack-tokens.json` |
| `fetch_slack_thread.py <url>` | Fetches thread + replies via `conversations.replies` API |
| `lookup_slack.py <url>` | History cache lookup for Slack threads |
| `save_slack_summary.py` | Saves entry to `~/.slack-summary/` |
