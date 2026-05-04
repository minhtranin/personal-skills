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

Outputs JSON: `key`, `url`, `summary`, `type`, `status`, `priority`, `reporter`, `assignee`, `created`, `updated`, `description`, `comments[]`, `attachments[]`.

## Step 3.5 — Analyze image attachments (skip if no images)

If `attachments` is non-empty, run:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/analyze_jira_images.py" '<ATTACHMENTS_JSON>'
```

- Requires `GEMINI_API_KEY` env var. If unset, the script exits silently with `[]` — skip without warning.
- Outputs JSON array of `{filename, description}`. Carry these descriptions into Step 4 as **image context**.

## Step 4 — Summarize

Using `description` + all `comments` + image descriptions from Step 3.5 (if any):

1. **Summary** — 3–5 sentences: what the issue is, current status, what's needed.
2. **Key Points** — 5–10 bullets: problem, decisions, blockers, next steps.
3. **Comment Highlights** — if >3 comments, call out 2–3 most significant ones.
4. **Images** — if image descriptions were returned in Step 3.5, list each as `filename: <description>`.

## Step 5 — Output immediately

```
## PROJ-123 — <title>
**Status:** <status> · **Assignee:** <assignee> · **Priority:** <priority>

### Summary
...

### Key Points
...

### Comment Highlights
...

### Images  ← only if image descriptions exist
- filename.png: <description>
```

Then on a new line: *"Browse history with `/ps:web`. Want a diagram for this? (y/n)"*

## Step 6 — Save (run immediately, do not wait for diagram)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<KEY>" --url "<URL>" --issue-summary "<TITLE>" \
  --type "<TYPE>" --status "<STATUS>" \
  --reporter "<REPORTER>" --assignee "<ASSIGNEE>" \
  --summary "<AI_SUMMARY>" --key-points "<KEY_POINTS>" \
  --description "<DESCRIPTION_FIRST_4000_CHARS>"
```

## Step 7 — Diagram (only if user says yes)

If the user replies `y` or `yes`:

```bash
python3 -c "import playwright" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: tell the user to install playwright (`pip3 install playwright && python3 -m playwright install chromium`) and stop.

If `ok`: generate a status-flow diagram — issue title as central box, reporter → assignee as actors, current status badge, 2–3 key points as connected nodes. Write to `/tmp/jira_diagram.excalidraw`, render:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/excalidraw/render_excalidraw.py" \
  /tmp/jira_diagram.excalidraw --output /tmp/jira_diagram.png
```

Display PNG with the Read tool. Then update the saved entry:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<KEY>" --url "<URL>" --issue-summary "<TITLE>" \
  --type "<TYPE>" --status "<STATUS>" \
  --reporter "<REPORTER>" --assignee "<ASSIGNEE>" \
  --summary "<AI_SUMMARY>" --key-points "<KEY_POINTS>" \
  --description "<DESCRIPTION_FIRST_4000_CHARS>" \
  --diagram-png "/tmp/jira_diagram.png"
```
