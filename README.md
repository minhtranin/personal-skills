# personal-skills

A growing collection of personal productivity skills for AI coding agents.

Supports **Claude Code**, **Antigravity**, and **OpenCode** — installs into all detected agents automatically.

---

## Skills

### `tube` — YouTube tools

| Command | Description |
|---|---|
| `/ps-tube-summary <url> [--refresh]` | Summarize a YouTube video (uses cached result if already done) |
| `/ps-web [--port 5050]` | Browse all summaries (YouTube + Medium) in a local web UI |

### `medium` — Medium articles

| Command | Description |
|---|---|
| `/ps-medium-summary <url> [--refresh]` | Fetch article via Freedium mirror and summarize (uses cached result if already done) |

### `jira` — Jira issues

| Command | Description |
|---|---|
| `/ps-jira-summary <PROJ-123 or url> [--refresh]` | Fetch issue description + all comments and summarize |
| `/ps-jira-plantask <PROJ-123> [--no-create] [--refresh]` | Research codebase, produce an implementation plan, break into independent subtasks, create them in Jira, then guide step-by-step implementation |

Requires env vars: `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL`

### `slack` — Slack threads

| Command | Description |
|---|---|
| `/ps-slack-login` | Save Slack session tokens (guided DevTools extraction) |
| `/ps-slack-summary <thread-url> [--refresh]` | Fetch Slack thread + all replies and summarize |

Tokens are extracted from Slack desktop app storage automatically, or manually via DevTools.

---

## Install

### Latest release

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

### Specific version

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --version v1.0.0
```

### Update to latest

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --update
```

### Check current version

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --version-check
```

**What it does:**
1. Resolves the target version (latest release or specified tag)
2. Downloads helper scripts to `~/.local/share/personal-skills/scripts/`
3. Detects which agents are installed (Claude Code, Antigravity, OpenCode)
4. Copies skill command files into each agent's commands directory
5. Saves installed version to `~/.local/share/personal-skills/.version`

### Requirements

- `curl` + `python3` (for the installer)
- `yt-dlp`, `flask` (for the skills themselves — prompted on first use if missing)

---

## Usage

```
/ps-tube-summary https://youtube.com/watch?v=...
```

Run the same URL again → shows the cached summary instantly, asks if you want to re-fetch.

```
/ps-tube-summary https://youtube.com/watch?v=... --refresh
```

Force re-download and re-summarize.

```
/ps-web
/ps-web --port 5051
```

Opens a local web server at `http://localhost:5050` listing all past summaries.

---

## Data storage

All history stored locally per namespace:

```
~/.youtube-summary/     # YouTube summaries
~/.medium-summary/      # Medium summaries
~/.jira-summary/        # Jira summaries
~/.slack-summary/       # Slack thread summaries
  ├── index.json         # Index of all summaries
  └── <id>.json          # Per-entry detail
```

---

## Repository structure

```
personal-skills/
├── skills/
│   └── tube/
│       ├── ps-tube-summary/
│       │   └── SKILL.md          # /ps-tube-summary command
│       ├── ps-web/
│       │   └── SKILL.md          # /ps-web command
│       └── scripts/
│           ├── check_deps.sh         # Dependency checker + auto-installer
│           ├── get_transcript.sh     # yt-dlp transcript extractor
│           ├── lookup_history.py     # History cache lookup
│           ├── save_summary.py       # Persist summary to ~/.youtube-summary/
│           └── web_server.py         # Flask history browser
├── CLAUDE.md                     # Claude Code project instructions
└── install.sh                    # curl-pipe installer
```

---

## Adding a new skill namespace

1. Create `skills/<namespace>/scripts/` with helper scripts
2. Create `skills/<namespace>/ps-<name>/SKILL.md` per command
3. `install.sh` auto-discovers new namespaces — no changes needed