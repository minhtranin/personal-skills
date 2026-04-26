---
name: ps:summary
description: Summarize any content — YouTube video, Medium article, Jira issue, GitHub repo, AWS/Amazon blog, or Slack thread. Auto-detects content type from URL or issue key.
---

# ps:summary

Summarize any content — YouTube video, Medium article, Jira issue, GitHub repo, AWS/Amazon blog, or Slack thread. Auto-detects content type from URL or issue key.

## Usage

```
/ps:summary <url-or-issue-key> [--refresh] [--diagram]
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

## Diagram file naming

All diagram files use a timestamped name to avoid collisions:

```bash
DIAGRAM_FILE="/tmp/summary_diagram_$(date +%Y%m%d_%H%M%S).html"
```

Use this variable whenever writing a diagram file. Tell the user the exact path after writing.

---

## HTML diagram — base template

The CSS template is pre-built at:
```
$HOME/.local/share/personal-skills/scripts/summary/diagram_header.html
```

**Always read this file first, then append only the `<body>` content** — never regenerate the CSS or `<head>` boilerplate. This makes diagram generation fast. The template already includes styles for: cards, color themes, badges, subcards, vertical/horizontal arrows, tables, trees, timelines, progress bars, and legend maps.

Write the complete file as: template content + your body HTML + `</body></html>`.

---

## [youtube] YouTube Video

**Y1 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/lookup_history.py" "<url>"
```
Exit 0 = cached — show result and stop.

**Y2 — Check deps:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh"
```

**Y3 — Fetch title + transcript in parallel:**
```bash
yt-dlp --get-title "<url>" 2>/dev/null || echo "Unknown Title"
bash "$HOME/.local/share/personal-skills/scripts/tube/get_transcript.sh" "<url>"
```

**Y4 — Single pass: save + diagram together**

Run save in background, then immediately generate the HTML diagram:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/save_summary.py" \
  --video-id "<id>" --url "<url>" --title "<title>" \
  --summary "<summary-text>" --key-points '<json-array>' \
  --transcript "<excerpt>" &
```

Read the base template, then write `$DIAGRAM_FILE` using template CSS + body content that visually represents the architecture, flow, or key concepts from the video.

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [medium] Medium Article

**M1 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/lookup_medium.py" "<url>"
```
Exit 0 = cached — show result and stop.

**M2 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" "<url>"
```

**M3 — Single pass: save + diagram together**

Run save in background, then immediately generate the HTML diagram:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<slug-from-url>" --url "<url>" --title "<title>" \
  --author "<author>" --summary "<summary-text>" \
  --key-points '<json-array-of-points>' &
```

Read the base template, then write `$DIAGRAM_FILE` using template CSS + body content that visualizes the article's concepts, architecture, or flow.

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [jira] Jira Issue

**J1 — Check credentials:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/jira/check_jira_credentials.sh"
```
Stop if missing.

**J2 — Normalize** — bare key (e.g. `PROJ-123`) used directly; URL → extract issue key from path.

**J3 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/lookup_jira.py" "<issue-key>"
```
Exit 0 = cached — show result and stop.

**J4 — Fetch issue:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" "<issue-key>"
```

**J5 — Summarize** — 3–5 sentence summary + 5–10 key points (problem, scope, fix, alternatives, blockers, decisions) + 2–3 comment highlights.

**J6 — Output to terminal:**
```
Jira Summary
└── [<TYPE>] <KEY>: <Summary>
    ├── Status   : <status>
    ├── Priority : <priority>
    ├── Assignee : <assignee>
    ├── Reporter : <reporter>
    ├── Fetched  : <date>
    ├── Summary
    │   └── <3-5 sentences>
    ├── Key Points
    │   ├── • <point>
    │   └── ...
    └── Comment Highlights
        ├── • <highlight>
        └── ...
```

**J7 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/save_jira.py" \
  --key "<issue-key>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**J8 — Ask for diagram:**

After saving, ask the user:

> Want a visual diagram for this? (y/n)

If yes: read the base template, write `$DIAGRAM_FILE` with body content showing the issue status flow, affected components, or implementation plan. Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [github] GitHub Repository

**G1 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/lookup_github.py" "<url>"
```
Exit 0 = cached — show result and stop.

**G2 — Fetch repo:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/fetch_github_repo.py" "<url>"
```

**G3 — Single pass: save + diagram together**

Run save in background, then immediately generate the HTML diagram:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<url>" --full-name "<owner>/<repo>" \
  --summary "<summary-text>" --key-points '<json-array>' &
```

Read the base template, then write `$DIAGRAM_FILE` using template CSS + body content showing the repo architecture, component relationships, or data flow.

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [amazon] AWS / Amazon Blog

**A1 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/lookup_amazon.py" "<url>"
```
Exit 0 = cached — show result and stop.

**A2 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<url>"
```

**A3 — Single pass: save + diagram together**

Run save in background, then immediately generate the HTML diagram:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<slug>" --url "<url>" --title "<title>" --author "<author>" \
  --summary "<summary-text>" --key-points '<json-array>' &
```

Read the base template, then write `$DIAGRAM_FILE` using template CSS + body content showing the AWS architecture grouped by layer (Interface → Compute → Intelligence → Storage → Observability).

Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## [slack] Slack Thread

**S1 — Check tokens:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/slack/check_slack_tokens.sh"
```
Stop if missing.

**S2 — Check history** (skip if `--refresh`):
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/lookup_slack.py" "<url>"
```
Exit 0 = cached — show result and stop.

**S3 — Fetch thread:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" "<url>"
```
Exit codes: 0 = success, 1 = auth expired (re-run check_slack_tokens.sh and retry), 2 = fatal error.

**S4 — Summarize** — 3–5 sentence summary + 5–10 key points (decisions, action items, open questions) + participant list with roles.

**S5 — Output to terminal:**
```
Slack Summary
└── #<channel> thread
    ├── Replies      : <count>
    ├── Participants : <names>
    ├── Date         : <date>
    ├── Fetched      : <date>
    ├── Summary
    │   └── <3-5 sentences>
    ├── Key Points
    │   ├── • <point>
    │   └── ...
    └── Participants
        ├── <name> — <role/contribution>
        └── ...
```

**S6 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<id>" --url "<url>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**S7 — Ask for diagram:**

After saving, ask the user:

> Want a visual diagram for this? (y/n)

If yes: read the base template, write `$DIAGRAM_FILE` with body content showing participant interactions, decision flow, or action item owners. Tell the user: `Diagram saved — open <DIAGRAM_FILE> in Chrome.`

---

## HTML diagram body — what to generate

When writing the body content (appended after the base template), pick the right visual per section:

| Content type | Visual |
|---|---|
| Architecture / service flow | Cards + arrows (use `.card`, `.h-arrow`, `.v-arrow`) |
| Comparison / migration map | Table (use `.tbl`) |
| Hierarchy / file tree / org | Tree (use `.tree` with nested `<ul>`) |
| Sequential steps / phases | Timeline (use `.timeline`, `.tl-item`) |
| Scores / metrics / rankings | Progress bars (use `.metric`, `.bar-track`, `.bar-fill`) |

Rules:
- Use color themes to encode meaning: `.orange` = entry/trigger, `.blue` = core logic, `.purple` = AI/LLM, `.red` = storage, `.green` = async/background, `.amber` = queue/buffer, `.teal` = external service
- Use `.badge` for service labels, `.sub` for internal detail blocks inside a card
- Use `.footer` + `.mmap` for migration/legend tables at the bottom
- Body starts with `<h1>` title and ends before `</body></html>`
