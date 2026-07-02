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

**Y3 — Output summary:**

Output a text summary in terminal:

```
YouTube Summary
└── <title>
    ├── URL     : <url>
    ├── Summary
    │   └── <3-5 sentences covering main topic and key takeaways>
    └── Key Points
        ├── • <point>
        └── ...
```

---

## [medium] Medium Article

**M1 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" "<url>"
```

**M2 — Output summary:**

Output a text summary in terminal:

```
Medium Summary
└── <title> — <author>
    ├── URL     : <url>
    ├── Summary
    │   └── <3-5 sentences covering main argument and conclusions>
    └── Key Points
        ├── • <point>
        └── ...
```

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

**J3.1 — Interpret strikethrough text:**

In the fetched `description` and `comments`, any text wrapped in `~~...~~` is **strikethrough** in Jira. Treat it as **removed / superseded / no longer required** — QC or the reporter struck it out instead of hard-deleting it. Rules:
- Do **not** list struck-through text as an active requirement, scope item, or key point.
- When struck text sits next to its replacement (a before→after edit), report only the current (non-struck) version, and note the change if it's material — e.g. "Requirement changed: was X, now Y."
- If a whole requirement/section is struck with no replacement, either omit it or mention it once as "Removed: …" so the reader knows it was dropped — never as something still to be done.

**J3.5 — Inspect image attachments (if any):**

If `fetch_jira.py` returned an `attachments` field with image files, download them locally:
```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/download_jira_images.py" '<attachments-json>'
```

Returns `[{filename, mime_type, path}]`. Inspect each downloaded image path with the current agent/model's native image understanding; do **not** call an external vision API or require `GEMINI_API_KEY`.

Use image findings only when they add useful context beyond the issue text, such as screenshots showing UI state, error messages, diagrams, affected screens, or expected behavior. Incorporate useful findings into **Summary** and **Key Points**, and add an **Images** section only when the image materially clarifies the requirement or bug. If images are decorative, duplicated, inaccessible, or not helpful, omit the section and continue.

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
    ├── Images (optional, only if useful)
    │   ├── • <filename>: <useful visual context, if any>
    │   └── ...
    └── Comment Highlights
        ├── • <highlight>
        └── ...
```

---

## [github] GitHub Repository

**G1 — Fetch repo:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/github/fetch_github_repo.py" "<url>"
```

**G2 — Output summary:**

Output a text summary in terminal:

```
GitHub Summary
└── <owner>/<repo>
    ├── URL         : <url>
    ├── Description : <description>
    ├── Tech Stack  : <languages / frameworks>
    ├── Summary
    │   └── <3-5 sentences covering purpose, architecture, notable patterns>
    └── Key Points
        ├── • <point>
        └── ...
```

---

## [amazon] AWS / Amazon Blog

**A1 — Fetch article:**
```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<url>"
```

**A2 — Output summary:**

Output a text summary in terminal:

```
AWS Blog Summary
└── <title> — <author>
    ├── URL      : <url>
    ├── Category : <category>
    ├── Summary
    │   └── <3-5 sentences covering the AWS solution and key services used>
    └── Key Points
        ├── • <point>
        └── ...
```

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
