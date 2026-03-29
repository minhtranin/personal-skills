---
name: ps:jira-summary
description: Fetch a Jira issue (description + all comments) and summarize it. Use when the user runs /ps-jira-summary <issue-key-or-url> or asks to summarize a Jira ticket.
argument-hint: <PROJ-123 or jira-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# Jira Issue Summarizer

**Arguments:** $ARGUMENTS

Parse the issue key or URL. If `--refresh` is present, skip history check.

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

## Step 1 — Check credentials

```bash
bash "$HOME/.local/share/personal-skills/scripts/jira/check_jira_credentials.sh"
```

- **Exit 0:** continue.
- **Exit 1:** show the printed instructions to the user exactly as-is and stop. Do not proceed.

## Step 2 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/lookup_jira.py" "<KEY_OR_URL>"
```

- **Exit 0 (found):** show cached title, status, summary, key points, date. Ask: *"Already summarized on <date>. Use cached result? Pass --refresh to re-fetch."* Stop if user confirms.
- **Exit 1:** continue.

## Step 3 — Fetch from Jira

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" "<KEY_OR_URL>"
```

Outputs JSON: `key`, `url`, `summary`, `type`, `status`, `priority`, `reporter`, `assignee`, `created`, `updated`, `description`, `comments[]`.

## Step 4 — Summarize

Using `description` + all `comments`:

1. **Summary** — 3–5 sentences: what the issue is, current status, what's needed.
2. **Key Points** — 5–10 bullets: problem, decisions, blockers, next steps.
3. **Comment Highlights** — if >3 comments, call out 2–3 most significant ones.

## Step 5 — Optional diagram (skip silently if unavailable)

```bash
python3 -c "import playwright" 2>/dev/null && echo "ok" || echo "skip"
```

If `ok`: generate a status-flow diagram — issue title as central box, reporter → assignee as actors, current status badge, 2–3 key points as connected nodes. Write to `/tmp/jira_diagram.excalidraw`, then:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/excalidraw/render_excalidraw.py" \
  /tmp/jira_diagram.excalidraw --output /tmp/jira_diagram.png 2>/dev/null
```

If PNG was created (`/tmp/jira_diagram.png` exists), display it with the Read tool. Set `DIAGRAM_PNG=/tmp/jira_diagram.png`, otherwise set `DIAGRAM_PNG=""`. If anything fails, skip silently and set `DIAGRAM_PNG=""`.

## Step 6 — Save

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<KEY>" --url "<URL>" --issue-summary "<TITLE>" \
  --type "<TYPE>" --status "<STATUS>" \
  --reporter "<REPORTER>" --assignee "<ASSIGNEE>" \
  --summary "<AI_SUMMARY>" --key-points "<KEY_POINTS>" \
  --description "<DESCRIPTION_FIRST_4000_CHARS>" \
  --diagram-png "$DIAGRAM_PNG"
```

## Step 7 — Output

```
## PROJ-123 — <title>
**Status:** <status> · **Assignee:** <assignee> · **Priority:** <priority>

### Summary
...

### Key Points
...

### Comment Highlights
...
```

Mention they can browse history with `/ps:web`.
