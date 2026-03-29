---
name: ps:slack-answer
description: Fetch a Slack thread, research the current directory codebase to find the best answer, draft a reply, then ask the user to confirm before posting. Use when the user runs /ps:slack-answer <thread-url> or asks to answer/reply to a Slack thread.
argument-hint: <slack-thread-url> [--refresh]
allowed-tools: [Bash, Read, Write, Agent]
---

# Slack Thread Answerer

**Arguments:** $ARGUMENTS

Parse the Slack thread URL. If `--refresh` is present, skip history check.

---

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

---

## Step 1 — Check tokens

```bash
bash "$HOME/.local/share/personal-skills/scripts/slack/check_slack_tokens.sh"
```

- **Exit 0:** continue.
- **Exit 1:** show the printed instructions to the user exactly as-is and stop.

---

## Step 2 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/lookup_slack.py" "<URL>"
```

- **Exit 0 (found):** show cached channel, summary, key points. Ask: *"Already summarized on <date>. Use cached context? Pass --refresh to re-fetch."* Use cached if user confirms, else re-fetch.
- **Exit 1:** continue to Step 3.

---

## Step 3 — Fetch thread

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py" "<URL>"
```

Outputs JSON: `channel_name`, `thread_ts`, `parent` (author, text), `replies[]` (author, ts, text, reactions), `participants[]`, `reply_count`.

- If exit 1 (auth error): tell the user tokens expired — re-extract manually using F12 DevTools, then run `save_slack_tokens.py --token xoxc-... --cookie xoxd-...`.
- If exit 2: show error and stop.

---

## Step 4 — Summarize the thread context

From the fetched thread, extract:

1. **The core question or problem** — what is the thread asking for? (1–3 sentences)
2. **Key details** — any constraints, error messages, code snippets, context already given in the thread
3. **What is NOT yet answered** — identify the open question that still needs a response

Output this context block immediately:

```
## #<channel> — <thread topic>
**Replies:** <count> · **Participants:** <names> · **Date:** <date>

### What the thread is asking
...

### Context & details given
...

### Open question needing an answer
...
```

---

## Step 5 — Research the codebase

Use the **Explore** agent to deeply research the current working directory to find the most relevant answer to the open question. Provide the full thread context (core question + details) as the research goal.

Search for:
- Source files, components, functions, or modules directly related to the topic
- README, docs, config files, or knowledge files (e.g. `docs/`, `knowledge/`, `*.md`, `*.txt`)
- Recent changes (git log) that may explain the current state
- Tests or examples that demonstrate correct usage

The agent should return:
- The most relevant file(s) and code section(s) that answer the question
- A direct answer based on what was found
- Any caveats, limitations, or "it depends" nuances from the code

If the current directory has no relevant code (e.g. it's a config-only or empty dir), note that and proceed with general knowledge only.

---

## Step 6 — Draft the reply

Using the research findings from Step 5, draft a Slack reply message that:

- **Directly answers** the open question in 2–5 sentences
- **References specific code** if found (file name, function name, or key concept — not full paths)
- **Includes a code block** if a snippet would help (use triple backticks)
- **Is conversational** — written as a helpful team member would reply in Slack, not as formal docs
- **Ends with a follow-up** if there are caveats or the answer depends on context

Show the draft reply to the user:

```
═══════════════════════════════════════════════════
DRAFT REPLY for #<channel> — <thread topic>
═══════════════════════════════════════════════════

<drafted reply text>

═══════════════════════════════════════════════════
Sources used: <comma-separated file names or "general knowledge">
```

Then ask: **"Post this reply to the thread? (y/n/e=edit)"**

---

## Step 7 — Handle user response

### If `n` — do nothing
Tell the user the reply was not posted. Offer: *"Copy the draft above to paste manually."*

### If `e` — edit
Ask: *"What would you like to change?"* Apply the edit, show the updated draft, and ask again: *"Post this updated reply? (y/n)"*

### If `y` — post the reply

Post the reply to the Slack thread:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/post_slack_reply.py" \
  --url "<THREAD_URL>" \
  --message "<REPLY_TEXT>"
```

- **Exit 0:** show `✓ Reply posted to #<channel>.`
- **Exit 1 (auth error):** tell the user tokens expired, re-extract with F12.
- **Exit 2:** show error message and stop.

---

## Step 8 — Save to history (always, regardless of whether reply was posted)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_summary.py" \
  --thread-id "<CHANNEL_ID>_<THREAD_TS>" \
  --url "<URL>" \
  --channel "<CHANNEL_NAME>" \
  --parent-text "<PARENT_MESSAGE_FIRST_200_CHARS>" \
  --summary "<THREAD_SUMMARY>" \
  --key-points "<KEY_POINTS_AND_DRAFT_REPLY>" \
  --participants "<COMMA_SEPARATED_NAMES>" \
  --reply-count "<COUNT>"
```

Then: *"Browse all history with `/ps:web`."*
