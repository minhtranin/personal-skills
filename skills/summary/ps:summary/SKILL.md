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

**Y6 — Output:**
```
YouTube Summary
└── <Title>
    ├── URL     : <url>
    ├── Fetched : <date>
    ├── Summary
    │   └── <3-5 sentences>
    └── Key Points
        ├── • <point>
        └── ...
```

**Y7 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/save_summary.py" \
  --video-id "<id>" --url "<url>" \
  --title "<title>" --summary "<summary-text>" \
  --key-points '<json-array>' --transcript "<excerpt>"
```

**Y8 — Diagram** (only if `--diagram` or user explicitly asks):
```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```
If `ok`: generate full architectural/technical diagram, write to `/tmp/summary_diagram.excalidraw`, then render:
```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/summary_diagram.excalidraw --output /tmp/summary_diagram.png
```
Display the PNG.

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

**M4 — Output:**
```
Medium Summary
└── <Title>
    ├── Author  : <author>
    ├── URL     : <url>
    ├── Fetched : <date>
    ├── Summary
    │   └── <3-5 sentences>
    └── Key Points
        ├── • <point>
        └── ...
```

**M5 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<slug-from-url>" --url "<url>" \
  --title "<title>" --author "<author>" \
  --summary "<summary-text>" \
  --key-points '<json-array-of-points>'
```

**M6 — Diagram** (only if `--diagram` or user explicitly asks): generate technical architecture diagram, render same as Y8.

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

**J8 — Diagram** (only if `--diagram` or user explicitly asks): generate status-flow diagram, render same as Y8.

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

**G4 — Output:**
```
GitHub Summary
└── <owner>/<repo>
    ├── Stars    : <stars>
    ├── Language : <language>
    ├── License  : <license>
    ├── Updated  : <date>
    ├── Fetched  : <date>
    ├── Summary
    │   └── <3-5 sentences>
    └── Key Points
        ├── • <point>
        └── ...
```

**G5 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/save_github_summary.py" \
  --url "<url>" --full-name "<owner>/<repo>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**G6 — Diagram** (only if `--diagram` or user explicitly asks): generate full architectural diagram with `--scale 2`, render same as Y8.

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

**A4 — Output:**
```
Amazon/AWS Summary
└── <Title>
    ├── Author  : <author>
    ├── URL     : <url>
    ├── Fetched : <date>
    ├── Summary
    │   ├── Problem  : <paragraph>
    │   ├── Solution : <paragraph>
    │   ├── Build    : <paragraph>
    │   └── Outcomes : <paragraph>
    ├── Key Points
    │   ├── • <insight>
    │   └── ...
    └── Tech Stack
        ├── <Service> — <purpose>
        └── ...
```

**A5 — Save:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<slug>" --url "<url>" \
  --title "<title>" --author "<author>" \
  --summary "<summary-text>" --key-points '<json-array>'
```

**A6 — Diagram** (only if `--diagram` or user explicitly asks): generate AWS architecture diagram grouped by layer (Interface → API → Compute → Intelligence → Observability → Storage), render same as Y8.

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

**S7 — Diagram** (only if `--diagram` or user explicitly asks): generate participant interaction diagram, render same as Y8.
