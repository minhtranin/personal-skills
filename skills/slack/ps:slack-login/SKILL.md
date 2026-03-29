---
name: ps:slack-login
description: Save Slack tokens (xoxc + xoxd) so other Slack skills can authenticate. Use when the user runs /ps:slack-login or needs to set up Slack credentials.
argument-hint: [--token xoxc-... --cookie xoxd-...]
allowed-tools: [Bash, Read]
---

# Slack Token Setup

**Arguments:** $ARGUMENTS

If `--token` and `--cookie` are already present in the arguments, skip to Step 3.

## Step 1 — Start token extraction server

Start the local token server on port 5051:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/web_server.py" --slack-tokens
```

Keep it running. Do NOT press Ctrl+C yet.

## Step 2 — Instructions for user

Tell the user:

> 1. Keep the token server running in the background
> 2. Open **Chrome/Edge** and go to **https://app.slack.com** — make sure you're logged in to your workspace
> 3. In the same browser, open a new tab and visit: **http://localhost:5051**
> 4. Click **"Extract Tokens"** — the page will grab xoxc and xoxd from your Slack session
> 5. Come back here and say "done" so I can verify the tokens were saved

Wait for the user to say "done" or confirm the tokens were extracted.

## Step 3 — Verify tokens

```bash
bash "$HOME/.local/share/personal-skills/scripts/slack/check_slack_tokens.sh"
```

- **Exit 0:** Tell user: "Tokens saved and validated! You can now use `/ps:slack-summary`."
- **Exit 1:** Show the printed error and stop.
