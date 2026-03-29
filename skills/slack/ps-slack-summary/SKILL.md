---
name: ps-slack-summary
description: Fetch a Slack thread and all its replies then summarize. Use when the user runs /ps-slack-summary <thread-url> or asks to summarize a Slack thread or conversation.
argument-hint: <slack-thread-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# Slack Thread Summarizer

**Arguments:** $ARGUMENTS

Parse the Slack thread URL. If `--refresh` is present, skip history check.

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

## Step 1 — Check tokens

```bash
bash "$HOME/.local/share/personal-skills/scripts/slack/check_slack_tokens.sh"
```

- **Exit 0:** continue.
- **Exit 1:** show the printed instructions to the user exactly as-is and stop. Tell them to run `/ps-slack-login` after saving tokens.

## Step 2 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/lookup_slack.py" "<URL>"
```

- **Exit 0 (found):** show cached channel, summary, key points, date. Ask: *"Already summarized on <date>. Use cached? Pass --refresh to re-fetch."* Stop if user confirms.
- **Exit 1:** continue.

## Step 3 — Fetch thread

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" "<URL>"
```

Outputs JSON: `channel_name`, `thread_ts`, `parent` (author, text), `replies[]` (author, ts, text, reactions), `participants[]`, `reply_count`.

- If exit 1 (auth error): tell the user tokens expired and they need to run `/ps-slack-login` again.
- If exit 2: show error and stop.

## Step 4 — Summarize

Using the parent message and all replies, produce:

1. **Summary** — 3–5 sentences: what the thread is about, the main question or topic, and how it was resolved or where it stands.
2. **Key Points** — 5–10 bullets: important decisions, action items, open questions, notable reactions.
3. **Participants** — list who contributed and their main position/role in the discussion.

## Step 5 — Save

Extract thread ID from URL (channel + timestamp parts):

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<CHANNEL_ID>_<THREAD_TS>" \
  --url "<URL>" \
  --channel "<CHANNEL_NAME>" \
  --parent-text "<PARENT_MESSAGE_FIRST_200_CHARS>" \
  --summary "<AI_SUMMARY>" \
  --key-points "<KEY_POINTS>" \
  --participants "<COMMA_SEPARATED_NAMES>" \
  --reply-count "<COUNT>"
```

## Step 6 — Optional diagram (skip silently if unavailable)

```bash
python3 -c "import playwright" 2>/dev/null && echo "ok" || echo "skip"
```

If `ok`: generate a participant interaction diagram — each participant as a node, arrows showing who replied to whom (based on thread flow), topic as a title box at the top. Write to `/tmp/slack_diagram.excalidraw`, then:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/excalidraw/render_excalidraw.py" \
  /tmp/slack_diagram.excalidraw --output /tmp/slack_diagram.png 2>/dev/null
```

If PNG was created, display it with the Read tool. If anything fails, skip silently.

## Step 7 — Output

```
## #<channel> — <thread topic>
**Replies:** <count> · **Participants:** <names> · **Date:** <date>

### Summary
...

### Key Points
...

### Participants
...
```

Mention they can browse all history with `/ps-web`.
