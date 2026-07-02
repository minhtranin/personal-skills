# AGENTS.md — Codebase Guide for Agentic Coding Agents

## Project Overview

A monorepo of personal productivity skills (shell commands) installed via `curl | bash`. Each skill lives under `skills/<namespace>/` with helper scripts and a SKILL.md prompt file. There is no build system, no package manager for the main repo, and no test framework.

## Build / Lint / Test Commands

There are **no tests, no linter config, and no build step**. The only CI workflow (`.github/workflows/release.yml`) creates GitHub Releases on tag push.

### Validation you can run

```bash
# Bash syntax check (all shell scripts)
bash -n install.sh && echo "OK"
find skills -name '*.sh' -exec bash -n {} \; -exec echo "OK: {}" \;

# Python syntax check (all Python scripts)
find skills -name '*.py' -exec python3 -m py_compile {} \;

# Verify install.sh runs in local mode
bash install.sh
```

### Release process

```bash
# Bump VERSION file, commit, tag, push — CI handles the rest
git tag v0.5.0 && git push --tags
```

## Repository Structure

```
skills/<namespace>/
  ps:<command>/SKILL.md    # Prompt file installed as a slash-command
  scripts/                 # Helper scripts (Bash + Python)
install.sh                 # Auto-discovering installer; no edits needed for new skills
VERSION                    # Single line, e.g. "0.4.9"
CLAUDE.md                  # Claude Code project guide (authoritative conventions)
```

Namespaces: `tube`, `medium`, `jira`, `slack`, `github`, `frontend`, `bot`.

## Code Style — Python Scripts

All scripts are standalone CLI tools — no shared modules, no `__init__.py`, no virtualenv.

### Shebang and docstring
```python
#!/usr/bin/env python3
"""
<One-line description>.
Usage: script_name.py <args>
Exit codes: 0 = success, 1 = not found / config error, 2 = API / dependency error
"""
```

### Imports
- **stdlib only** for most scripts: `urllib.request`, `json`, `re`, `argparse`, `pathlib`, `sys`, `os`, `datetime`
- **Never use `requests`** — always `urllib.request.urlopen()`
- Third-party imports guarded with try/except that prints to stderr and exits:
```python
try:
    from flask import Flask
except ImportError:
    print("ERROR: flask is not installed. Run: pip install flask", file=sys.stderr)
    sys.exit(2)
```
- Order: stdlib first, then third-party. No local imports (scripts are standalone).

### CLI arguments
Use `argparse` for all new scripts:
```python
parser = argparse.ArgumentParser()
parser.add_argument("query", help="URL or identifier")
parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
args = parser.parse_args()
```
Older scripts may use `sys.argv` directly — prefer argparse for new code.

### Naming
- Functions: `snake_case` — e.g. `extract_video_id()`, `parse_slack_url()`
- Constants: `UPPER_SNAKE_CASE` — e.g. `DEFAULT_DATA_DIR`, `TOKENS_FILE`
- Private helpers: `_leading_underscore()`
- Type hints: optional but encouraged for new code — e.g. `def slugify(text: str) -> str:`

### Error handling
- **Exit codes**: `0` = success, `1` = not found / config error / auth failure, `2` = API error / missing dependency
- **Errors to stderr**: `print(f"ERROR: ...", file=sys.stderr)`
- **Network calls** wrapped in try/except with HTTPError handling
- Never raise exceptions for expected conditions — use exit codes

### Output
- **JSON to stdout**: `print(json.dumps(data, ensure_ascii=False))` or with `indent=2` for human-readable
- **Always `ensure_ascii=False`** to preserve Unicode
- **Save scripts** print confirmation: `print(f"Saved: {path}")`

### File I/O
- Data dirs: `Path.home() / ".<namespace>-summary/"` (e.g. `~/.youtube-summary/`)
- Always create parents: `data_dir.mkdir(parents=True, exist_ok=True)`
- Always use `encoding="utf-8"` on read/write
- Index pattern: maintain `index.json` alongside individual `<id>.json` files
- Dedup before append: filter out existing entry by key before appending

### HTTP requests
```python
req = urllib.request.Request(url, headers={"User-Agent": "personal-skills/1.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    data = json.loads(r.read())
```

## Code Style — Bash Scripts

### Header
```bash
#!/usr/bin/env bash
set -e
```

### Naming
- Constants/important vars: `UPPER_SNAKE_CASE` — e.g. `TOKENS_FILE`, `SCRIPTS_DIR`
- Functions: `snake_case` — e.g. `check_deps()`, `check_yt_dlp()`

### Error handling
- Exit codes match Python convention: `exit 0` success, `exit 1` config/missing, `exit 2` tool not found
- Usage errors: `echo "Usage: script.sh <args>" >&2; exit 1`
- Tool checks: `command -v <tool> &>/dev/null || { echo "ERROR: ..." >&2; exit 2; }`
- Temp files: always `trap 'rm -rf "$TMPDIR"' EXIT`

### User interaction
- Interactive prompts: `read -r -p "Install? [y/N] " answer`
- Status markers: `echo "  [ok] ..."`, `echo "  [missing] ..."`
- Section headers: `echo "── Step N: ... ──"`

### Inline Python
Prefer embedding Python one-liners or heredocs for complex text processing:
```bash
python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])"
```

## SKILL.md File Pattern

Every SKILL.md follows this structure:
1. YAML frontmatter with `name`, `description`, `argument-hint`, `allowed-tools`
2. Step 0: Bootstrap check — verify scripts exist at `$HOME/.local/share/personal-skills/scripts/<ns>/`, curl-pipe installer if missing
3. Step 1+: Skill-specific logic following **history cache pattern** (see below)
4. `--refresh` flag bypasses cache in all fetch/summarize skills

## Core Patterns

### History cache pattern (all summary skills)
1. Run `lookup_<ns>.py <url>` — exit 0 = cached (return JSON), exit 1 = not found
2. If cached and no `--refresh`, offer cached result
3. Fetch fresh data via `fetch_<ns>.py <url>`
4. Output summary to user immediately
5. Run `save_<ns>.py` to persist

### Credential pattern
- **Jira**: env vars `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL` — validated by `check_jira_credentials.sh`
- **Slack**: auto-extracted from LevelDB → saved file → env vars — validated by `check_slack_tokens.sh`
- **GitHub**: optional `GITHUB_TOKEN`/`GH_TOKEN` for higher rate limits

### Adding a new skill namespace
1. Create `skills/<namespace>/scripts/` with helper scripts
2. Create `skills/<namespace>/ps:<name>/SKILL.md` for each command
3. Add Step 0 bootstrap check to each SKILL.md
4. Update skills tables in `CLAUDE.md` and `README.md`
5. `install.sh` auto-discovers new namespaces — no edits needed

## Key Constraints

- **No `requests` library** — all HTTP via `urllib.request`
- **No test framework** — validate with `python3 -m py_compile` and `bash -n`
- **Scripts are standalone** — no shared Python modules, no `__init__.py`
- **Never commit secrets** — tokens are stored at runtime with `chmod 600`
- **Preserve Unicode** — always `ensure_ascii=False` in JSON output
- **UTF-8 everywhere** — always specify `encoding="utf-8"` in file I/O
