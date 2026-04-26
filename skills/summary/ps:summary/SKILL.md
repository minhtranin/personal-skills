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

**Y3 — Fetch title:**
```bash
yt-dlp --get-title "<url>" 2>/dev/null || echo "Unknown Title"
```

**Y4 — Get transcript:**
```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/get_transcript.sh" "<url>"
```

**Y5 — Summarize** — 3–5 sentence summary + 5–10 key points from transcript.

**Y6 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/save_summary.py" \
  --video-id "<id>" --url "<url>" \
  --title "<title>" --summary "<summary-text>" \
  --key-points '<json-array>' --transcript "<excerpt>"
```

**Y7 — Diagram** (always — no terminal output, go straight to HTML):

Generate a self-contained HTML diagram at `/tmp/summary_diagram.html` that visually represents the architecture, flow, or key concepts from the video. Then tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

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

**M3 — Summarize** — 3–5 sentence summary + 5–8 key points.

**M4 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<slug-from-url>" --url "<url>" \
  --title "<title>" --author "<author>" \
  --summary "<summary-text>" \
  --key-points '<json-array-of-points>'
```

**M5 — Diagram** (always — no terminal output, go straight to HTML):

Generate a self-contained HTML diagram at `/tmp/summary_diagram.html` that visualizes the article's concepts, architecture, or flow. Then tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

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

**J6 — Output:**
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

If yes: generate a self-contained HTML diagram at `/tmp/summary_diagram.html` showing the issue status flow, affected components, or implementation plan. Tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

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

**G3 — Summarize** — 3–5 sentence summary + 6–10 key points (purpose, tech stack, architecture, features, activity, getting started).

**G4 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<url>" --full-name "<owner>/<repo>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**G5 — Diagram** (always — no terminal output, go straight to HTML):

Generate a self-contained HTML diagram at `/tmp/summary_diagram.html` showing the repo architecture, component relationships, or data flow. Then tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

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

**A3 — Summarize** — Four-paragraph summary (Problem → Solution → Build & Decisions → Outcomes & Lessons) + 5–8 key insights + tech stack list (`ServiceName — purpose`).

**A4 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<slug>" --url "<url>" \
  --title "<title>" --author "<author>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**A5 — Diagram** (always — no terminal output, go straight to HTML):

Generate a self-contained HTML diagram at `/tmp/summary_diagram.html` showing the AWS architecture grouped by layer (Interface → Compute → Intelligence → Storage → Observability). Then tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

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

**S5 — Output:**
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

If yes: generate a self-contained HTML diagram at `/tmp/summary_diagram.html` showing participant interactions, decision flow, or action item owners. Tell the user:

> Diagram saved — open `/tmp/summary_diagram.html` in Chrome.

---

## HTML Diagram Format (all types)

When generating `/tmp/summary_diagram.html`, follow these rules:

- **Self-contained** — no CDN links, no external scripts, pure HTML + inline CSS
- **Pick the right visual for each section** — don't default to cards for everything:
  - **Cards + CSS arrows** → architecture flows, service relationships, step-by-step pipelines
  - **Table** (`<table>`) → comparisons, migration maps, spec lists, key-value metadata
  - **Tree** (nested `<ul>` with CSS lines) → hierarchies, file structures, decision trees, org charts
  - **Horizontal bar / inline progress** (CSS `width %`) → scores, metrics, rankings
  - **Timeline** (vertical list with connectors) → sequential events, changelogs, phases
- **Color-coded** — use border + background color pairs to encode meaning (not decoration)
- **CSS arrows** between cards: vertical (`↓`) and horizontal (`→`) using flex + CSS border tricks — no SVG, no canvas
- **Numbered steps** where flow order matters
- **Badges** (small pill labels) for service names, roles, or status
- **Legend or summary table** at the bottom when there are many components
- Output path is always `/tmp/summary_diagram.html`
- Tell the user to open it in Chrome after writing
