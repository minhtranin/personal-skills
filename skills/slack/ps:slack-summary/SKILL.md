---
name: ps:slack-summary
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
- **Exit 1:** show the printed instructions to the user exactly as-is and stop. Do not mention `/ps-slack-login` — that command no longer exists.

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

- If exit 1 (auth error): tell the user tokens expired — they need to re-extract manually using F12 DevTools (see the instructions from Step 1 above), then run `save_slack_tokens.py --token xoxc-... --cookie xoxd-...`.
- If exit 2: show error and stop.

## Step 4 — Summarize

Using the parent message and all replies, produce:

1. **Summary** — 3–5 sentences: what the thread is about, the main question or topic, and how it was resolved or where it stands.
2. **Key Points** — 5–10 bullets: important decisions, action items, open questions, notable reactions.
3. **Participants** — list who contributed and their main position/role in the discussion.

## Step 5 — Output immediately

Use **ASCII tree / hierarchy style** for all output. Format as follows:

```
#<channel> — <thread topic>
├── Replies      : <count>
├── Participants : <names>
└── Date         : <date>

SUMMARY
└── <3–5 sentences: what the thread is about, main question/topic, how it was resolved or where it stands>

KEY POINTS
├── DECISIONS
│   └── <key decisions made>
├── ACTION ITEMS
│   └── <things people agreed to do>
├── OPEN QUESTIONS
│   └── <unresolved questions>
└── NOTABLE REACTIONS
    └── <any emoji reactions or strong sentiments worth noting>

PARTICIPANTS
├── <name> — <their main position/role in the discussion>
├── <name> — <their main position/role in the discussion>
└── <name> — <their main position/role in the discussion>
```

Then on a new line: *"Browse all history with `/ps:web`. Want a diagram for this? (y/n)"*

## Step 6 — Save (run immediately, do not wait for diagram)

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

## Step 7 — Diagram (only if user says yes)

If the user replies `y` or `yes`:

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: tell the user excalidraw deps are not installed and stop.

If `ok`: generate a participant interaction diagram — each participant as a node, arrows showing who replied to whom, topic as title box at top. Write to `/tmp/slack_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/slack_diagram.excalidraw --output /tmp/slack_diagram.png
```

Display PNG with the Read tool. Then update the saved entry with the diagram path:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<CHANNEL_ID>_<THREAD_TS>" \
  --url "<URL>" \
  --channel "<CHANNEL_NAME>" \
  --parent-text "<PARENT_MESSAGE_FIRST_200_CHARS>" \
  --summary "<AI_SUMMARY>" \
  --key-points "<KEY_POINTS>" \
  --participants "<COMMA_SEPARATED_NAMES>" \
  --reply-count "<COUNT>" \
  --diagram-png "/tmp/slack_diagram.png"
```
