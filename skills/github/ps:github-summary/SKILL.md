---
name: ps:github-summary
description: Fetch and summarize a GitHub repository — description, tech stack, architecture, recent activity, and key takeaways. Generates a diagram of the repo structure. Use when the user runs /ps:github-summary <github-url> or asks to summarize/explore a GitHub repo.
argument-hint: <github-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# GitHub Repository Summarizer

The user wants to summarize a GitHub repository.

**Arguments:** $ARGUMENTS

Parse the GitHub URL from the arguments. If `--refresh` is present, skip the history check.

---

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/github/fetch_github_repo.py" 2>/dev/null
```

If not found, run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Stop if it fails.

---

## Step 1 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/lookup_github.py" "<URL>"
```

- **Exit 0 (found):** Show cached full_name, summary, key points, diagram, and date. Ask: *"Already summarized on <date>. Use cached result? Pass --refresh to re-fetch."* Stop here if user confirms.
- **Exit 1 (not found):** Continue.

---

## Step 2 — Fetch repo data

```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/fetch_github_repo.py" "<URL>"
```

Outputs JSON with fields: `owner`, `repo`, `full_name`, `description`, `stars`, `forks`, `language`, `languages`, `topics`, `license`, `created_at`, `updated_at`, `readme`, `file_tree`, `recent_commits`.

If fetch fails or repo not found, tell the user and stop.

> **Tip:** Set `GITHUB_TOKEN` env var for higher rate limits and private repos.

---

## Step 3 — Analyze and summarize

Using the fetched data, produce:

1. **Summary** (3–5 sentences): What the repo does, who it's for, the core tech approach, and current maturity/activity level.
2. **Key Points** (6–10 bullets):
   - Purpose & use case
   - Tech stack (languages, frameworks, notable deps from README)
   - Architecture highlights (inferred from file tree + README)
   - Notable features
   - Activity level (stars, recent commits, last update)
   - How to get started (from README install/usage section)

---

## Step 4 — Output to user

Present in clean markdown:

```
## <owner>/<repo> ⭐ <stars>
**<description>**
*<language> · <license> · updated <updated_at>*

### Summary
...

### Key Points
...
```

Then: *"Want a diagram of this repo? (y/n)"*

---

## Step 5 — Save to history (run immediately, do not wait for diagram)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<URL>" \
  --full-name "<FULL_NAME>" \
  --description "<DESCRIPTION>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --stars "<STARS>" \
  --language "<LANGUAGE>" \
  --topics "<COMMA_SEPARATED_TOPICS>"
```

---

## Step 6 — Diagram (only if user says yes)

Check playwright:
```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: tell user excalidraw deps are not installed and stop.

If `ok`: Generate a **full architectural diagram** — not a concept map summary. Include all technical depth from the repo: directory structure, key modules and their responsibilities, data flows, tech stack details, API surface, configuration patterns, and how components connect. Cover everything visible from the README and file tree. Write to `/tmp/github_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/github_diagram.excalidraw --output /tmp/github_diagram.png --scale 2
```

Display PNG with the Read tool. Then update saved entry — `save_github_summary.py` will automatically copy the PNG from `/tmp/` to a persistent `~/.github-summary/diagrams/<slug>.png`:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<URL>" \
  --full-name "<FULL_NAME>" \
  --description "<DESCRIPTION>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --stars "<STARS>" \
  --language "<LANGUAGE>" \
  --topics "<TOPICS>" \
  --diagram-png "/tmp/github_diagram.png"
```
