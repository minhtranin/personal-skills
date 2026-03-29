---
name: ps:tube-summary
description: Download the transcript from a YouTube video and summarize its main points. Use when the user runs /ps-tube-summary <url> or asks to summarize a YouTube video.
argument-hint: <youtube-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# YouTube Video Summarizer

The user wants to summarize a YouTube video.

**Arguments:** $ARGUMENTS

Parse the URL from the arguments. If `--refresh` flag is present, skip the history check and re-summarize.

## Step 0 — Bootstrap scripts if missing

Check if scripts are installed:

```bash
ls "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh" 2>/dev/null
```

If that file does not exist, run the installer silently:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Wait for it to complete before continuing. If it fails, tell the user to run the installer manually and stop.

## Step 1 — Check history (skip if --refresh)

Before doing any network work, check if this video was already summarized:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/lookup_history.py" "<URL>"
```

- **Exit 0 (found):** Parse the JSON output. Present the cached result in clean markdown — title, summary, key points, and the date it was summarized. Then ask: *"Already summarized on <date>. Use cached result? Pass --refresh to force re-download."* If the user says yes or does not respond, stop here.
- **Exit 1 (not found):** Continue to Step 2.

## Step 2 — Check dependencies

```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh"
```

If the script exits non-zero (user declined to install), stop.

## Step 3 — Extract the video ID

Parse the video ID from the URL:
- `youtube.com/watch?v=VIDEO_ID` → extract `v=` param
- `youtu.be/VIDEO_ID` → extract path segment
- `youtube.com/shorts/VIDEO_ID` → extract path segment

## Step 4 — Fetch the video title

```bash
yt-dlp --skip-download --print "%(title)s" "<URL>"
```

## Step 5 — Get the transcript

```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/get_transcript.sh" "<URL>"
```

Capture the full output as the transcript text.

## Step 6 — Summarize

Using the transcript (or video description if no transcript was available), produce:

1. **Summary** — 3–5 sentence overview: what the video is about, the main argument, and the conclusion.
2. **Key Points** — bulleted list of 5–10 concrete takeaways or facts.

## Step 7 — Save to history

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/save_summary.py" \
  --video-id "<VIDEO_ID>" \
  --url "<URL>" \
  --title "<TITLE>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --transcript "<TRANSCRIPT_FIRST_4000_CHARS>"
```

## Step 8 — Optional diagram (skip silently if unavailable)

```bash
python3 -c "import playwright" 2>/dev/null && echo "ok" || echo "skip"
```

If `ok`: generate a concept map — video title as central box, key points as connected leaf nodes grouped by theme. Write to `/tmp/tube_diagram.excalidraw`, then:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/excalidraw/render_excalidraw.py" \
  /tmp/tube_diagram.excalidraw --output /tmp/tube_diagram.png 2>/dev/null
```

If PNG was created, display it with the Read tool. If anything fails, skip silently.

## Step 9 — Output to user

Present the summary and key points in clean markdown. Mention they can browse all history with `/ps-web`.
