---
name: ps:bot-telegram
description: Set up and run a Telegram bot that lets you chat with Claude Code from your phone — summarize Slack threads, answer threads, summarize YouTube/Medium/Jira, and ask questions about your codebase. Use when the user runs /ps:bot-telegram or asks to set up a Telegram bot.
argument-hint: [--setup | --start | --stop | --status]
allowed-tools: [Bash, Read, Write]
---

# Telegram Bot Setup & Manager

**Arguments:** $ARGUMENTS

---

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/bot/telegram_bot.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

---

## Step 1 — Parse intent from arguments

- No args or `--setup` → run full setup flow (Steps 2–5)
- `--start` → start the bot (Step 6)
- `--stop` → stop the bot (Step 7)
- `--status` → show bot status (Step 8)

---

## Step 2 — Check dependencies

```bash
python3 -c "import telegram; import anthropic; print('ok')" 2>/dev/null || echo "missing"
```

If `missing`, install:

```bash
bash "$HOME/.local/share/personal-skills/scripts/bot/setup.sh"
```

---

## Step 3 — Check if already configured

```bash
cat "$HOME/.local/share/personal-skills/bot-config.json" 2>/dev/null || echo "not configured"
```

If already configured, show:
```
✓ Bot already configured.
  Token  : <first 10 chars>...
  User ID: <id>

Run with --start to launch, or continue to reconfigure.
```
Ask: *"Reconfigure? (y/n)"* — if `n`, skip to Step 6.

---

## Step 4 — Get Telegram bot token

Show the user:

```
To create a Telegram bot:

1. Open Telegram and message @BotFather
2. Send: /newbot
3. Follow prompts — choose a name and username (e.g. "MyPersonalBot", "mypersonal_bot")
4. BotFather will give you a token like: 7123456789:AAF...

Paste your bot token here:
```

Wait for the token input. Validate it looks like `\d+:[\w-]{35,}`.

---

## Step 5 — Get Telegram user ID

Show the user:

```
To get your Telegram user ID:

1. Open Telegram and message @userinfobot
2. It will reply with your User ID (a number like 123456789)

Paste your Telegram User ID here:
```

Wait for the user ID. Then save config:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/bot/telegram_bot.py" \
  --token "<TOKEN>" \
  --user-id <USER_ID> \
  --setup
```

Show output. If success, continue to Step 6.

---

## Step 6 — Start the bot

Check if already running:

```bash
pgrep -f "telegram_bot.py" && echo "running" || echo "stopped"
```

If `running`:
```
✓ Bot is already running (PID: <pid>).
  Send a message to your bot on Telegram to test it.
```
Stop here.

If `stopped`, start in background:

```bash
nohup python3 "$HOME/.local/share/personal-skills/scripts/bot/telegram_bot.py" \
  > "$HOME/.local/share/personal-skills/bot.log" 2>&1 &
echo "PID: $!"
```

Wait 2 seconds, then verify:

```bash
sleep 2 && pgrep -f "telegram_bot.py" && echo "ok" || echo "failed"
```

If `ok`, show:
```
✓ Telegram bot is running!

Open Telegram and message your bot. Try:
  • "summarize this slack thread: <url>"
  • "answer this slack thread: <url>"
  • "summarize this video: <youtube-url>"
  • "what does the auth module do in my codebase?"
  • /clear  — reset conversation

Logs: tail -f ~/.local/share/personal-skills/bot.log
```

If `failed`, show the last 20 lines of the log and stop:

```bash
tail -20 "$HOME/.local/share/personal-skills/bot.log"
```

---

## Step 7 — Stop the bot (`--stop`)

```bash
pkill -f "telegram_bot.py" && echo "stopped" || echo "not running"
```

Show result.

---

## Step 8 — Status (`--status`)

```bash
pgrep -f "telegram_bot.py" && echo "running" || echo "stopped"
```

```bash
tail -20 "$HOME/.local/share/personal-skills/bot.log" 2>/dev/null || echo "(no log)"
```

```bash
cat "$HOME/.local/share/personal-skills/bot-config.json" 2>/dev/null | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Token: {d[\"token\"][:12]}...\nUser ID: {d[\"user_id\"]}')" \
  2>/dev/null || echo "Not configured"
```

Show a summary of status, PID, and last log lines.

---

## What the bot can do

When running, send messages to your Telegram bot:

| You say | Bot does |
|---|---|
| `<slack-thread-url>` | Summarizes the thread |
| `answer this: <slack-url>` | Researches codebase + drafts reply |
| `<youtube-url>` | Summarizes the video |
| `<medium-url>` | Summarizes the article |
| `PROJ-123` or `<jira-url>` | Summarizes the Jira issue |
| Any question | Answers using Claude + your codebase |
| `/clear` | Resets conversation history |

The bot remembers conversation context (last 20 turns) so you can follow up naturally.
