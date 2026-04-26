---
name: ps:summary
description: Summarize any content — YouTube video, Medium article, Jira issue, GitHub repo, AWS/Amazon blog, or Slack thread. Auto-detects content type from URL or issue key.
---

# ps:summary

Summarize any content — YouTube video, Medium article, Jira issue, GitHub repo, AWS/Amazon blog, or Slack thread. Auto-detects content type from URL or issue key.

## Usage

```
/ps:summary <url-or-issue-key>
```

**Examples:**
- `/ps:summary https://www.youtube.com/watch?v=abc123`
- `/ps:summary https://medium.com/some-article`
- `/ps:summary PROJ-123`
- `/ps:summary https://myorg.atlassian.net/browse/PROJ-123`
- `/ps:summary https://github.com/owner/repo`
- `/ps:summary https://aws.amazon.com/blogs/...`
- `/ps:summary https://myorg.slack.com/archives/C.../p...`

---

## Step 0 — Bootstrap

```bash
ls "$HOME/.local/share/personal-skills/scripts/summary/detect_type.py" 2>/dev/null && echo "ok" || echo "missing"
```

If `missing`:
```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

---

## Step 1 — Detect content type

```bash
python3 "$HOME/.local/share/personal-skills/scripts/summary/detect_type.py" "<input>"
```

Output: `youtube` | `medium` | `jira` | `github` | `amazon` | `slack` | `unknown`

If `unknown`: tell the user "Could not detect content type for: `<input>`. Supported inputs: YouTube URL, Medium/Freedium URL, Jira issue key (e.g. PROJ-123) or URL, GitHub URL, AWS/Amazon blog URL, Slack thread URL." and stop.

---

## Step 2 — Route to matching handler

Follow the section below that matches Step 1 output.

---

## Diagram output — filename

Always use a timestamped filename:
```bash
DIAGRAM_FILE="/tmp/summary_diagram_$(date +%Y%m%d_%H%M%S).html"
DIAGRAM_LINK="file://$DIAGRAM_FILE"
```

---

## Diagram output — base CSS template

The CSS is pre-built. **Always read this file first**, then append only the `<body>` content — never regenerate CSS or `<head>` boilerplate:

```
$HOME/.local/share/personal-skills/scripts/summary/diagram_header.html
```

Write the complete file as: **template content + your body HTML + `</body></html>`**.

---

## Saving to web history

For all types, persist the record so the web UI can show it. **Instead of storing a text summary, store the diagram file link** so the web history entry is a clickable `file://` URL that opens the HTML diagram directly in Chrome.

Pass `--summary "$DIAGRAM_LINK"` to the save script for non-Jira/non-Slack types.

For Jira and Slack: if the user requests a diagram, also pass `--diagram-path "$DIAGRAM_LINK"` alongside the text summary.

---

## [youtube] YouTube Video

**Y1 — Check deps:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh"
```

**Y2 — Fetch title + transcript:**
```bash
yt-dlp --get-title "<url>" 2>/dev/null || echo "Unknown Title"
bash "$HOME/.local/share/personal-skills/scripts/tube/get_transcript.sh" "<url>"
```

**Y3 — Generate diagram + save in parallel:**

Generate diagram: read base CSS template → write `$DIAGRAM_FILE` with body content visualizing the video's architecture, flow, or key concepts.

Save in background:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/save_summary.py" \
  --video-id "<id>" --url "<url>" --title "<title>" \
  --summary "$DIAGRAM_LINK" --key-points '[]' --transcript "<excerpt>" &
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [medium] Medium Article

**M1 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" "<url>"
```

**M2 — Generate diagram + save in parallel:**

Generate diagram: read base CSS template → write `$DIAGRAM_FILE` with body content visualizing the article's concepts, architecture, or flow.

Save in background:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<slug-from-url>" --url "<url>" --title "<title>" \
  --author "<author>" --summary "$DIAGRAM_LINK" --key-points '[]' &
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [jira] Jira Issue

**J1 — Check credentials:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/jira/check_jira_credentials.sh"
```
Stop if missing.

**J2 — Normalize** — bare key (e.g. `PROJ-123`) used directly; URL → extract issue key from path.

**J3 — Fetch issue:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" "<issue-key>"
```

**J4 — Output summary as tree in terminal:**
```
Jira Summary
└── [<TYPE>] <KEY>: <title>
    ├── Status   : <status>
    ├── Priority : <priority>
    ├── Assignee : <assignee>
    ├── Reporter : <reporter>
    ├── Summary
    │   └── <3-5 sentences>
    ├── Key Points
    │   ├── • <problem / scope / fix / blockers / decisions>
    │   └── ...
    └── Comment Highlights
        ├── • <highlight>
        └── ...
```

**J5 — Save text summary:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<issue-key>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**J6 — Ask for diagram:**

> Want a visual diagram for this? (y/n)

If yes: read base CSS template → write `$DIAGRAM_FILE` with body content showing issue status flow, affected components, or implementation plan. Then re-save with diagram link:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<issue-key>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>' \
  --diagram-path "$DIAGRAM_LINK"
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [github] GitHub Repository

**G1 — Fetch repo:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/fetch_github_repo.py" "<url>"
```

**G2 — Generate diagram + save in parallel:**

Generate diagram: read base CSS template → write `$DIAGRAM_FILE` with body content showing repo architecture, component relationships, or data flow.

Save in background:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<url>" --full-name "<owner>/<repo>" \
  --summary "$DIAGRAM_LINK" --key-points '[]' &
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [amazon] AWS / Amazon Blog

**A1 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<url>"
```

**A2 — Generate diagram + save in parallel:**

Generate diagram: read base CSS template → write `$DIAGRAM_FILE` with body content showing AWS architecture grouped by layer (Interface → Compute → Intelligence → Storage → Observability).

Save in background:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<slug>" --url "<url>" --title "<title>" --author "<author>" \
  --summary "$DIAGRAM_LINK" --key-points '[]' &
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [slack] Slack Thread

**S1 — Check tokens:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/slack/check_slack_tokens.sh"
```
Stop if missing.

**S2 — Fetch thread:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" "<url>"
```
Exit codes: 0 = success, 1 = auth expired (re-run check_slack_tokens.sh and retry), 2 = fatal error.

**S3 — Output summary as tree in terminal:**
```
Slack Summary
└── #<channel> thread
    ├── Replies      : <count>
    ├── Participants : <names>
    ├── Date         : <date>
    ├── Summary
    │   └── <3-5 sentences>
    ├── Key Points
    │   ├── • <decisions / action items / open questions>
    │   └── ...
    └── Participants
        ├── <name> — <role/contribution>
        └── ...
```

**S4 — Save text summary:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<id>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**S5 — Ask for diagram:**

> Want a visual diagram for this? (y/n)

If yes: read base CSS template → write `$DIAGRAM_FILE` with body content showing participant interactions, decision flow, or action item owners. Then re-save with diagram link:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<id>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>' \
  --diagram-path "$DIAGRAM_LINK"
```

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## HTML diagram body — visual guide

Pick the right element per section:

| Content | Use |
|---|---|
| Architecture / service flow | Cards + arrows (`.card`, `.h-arrow`, `.v-arrow`) |
| Comparison / spec list | Table (`.tbl`) |
| Hierarchy / file tree / org | Tree (`.tree` + nested `<ul>`) |
| Sequential phases / events | Timeline (`.timeline`, `.tl-item`) |
| Scores / metrics | Progress bars (`.metric`, `.bar-track`, `.bar-fill`) |

Color encoding:
- `.orange` — entry / trigger
- `.blue` — core logic / worker
- `.purple` — AI / LLM
- `.red` — storage / database
- `.green` — async / background
- `.amber` — queue / buffer
- `.teal` — external service

Body starts with `<h1>` title. End with `</body></html>`.
