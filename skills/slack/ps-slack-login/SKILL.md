---
name: ps-slack-login
description: Save Slack tokens (xoxc + xoxd) so other Slack skills can authenticate. Use when the user runs /ps-slack-login or needs to set up Slack credentials.
argument-hint: [--token xoxc-... --cookie xoxd-...]
allowed-tools: [Bash, Read, Write]
---

# Slack Token Setup

**Arguments:** $ARGUMENTS

If `--token` and `--cookie` are already present in the arguments, skip to Step 2.

## Step 1 — Obtain tokens from Slack

Tell the user:

> To use Slack skills, you need two session tokens from the Slack desktop app or web app.
> Here's how to get them:
>
> **In Slack Desktop (Windows/Mac/Linux):**
> 1. Open Slack and press **F12** (or Cmd+Option+I on Mac) to open DevTools
> 2. Go to the **Application** tab → **Cookies** → `https://app.slack.com`
> 3. Find the cookie named **`d`** — copy its **Value** (starts with `xoxd-`)
> 4. Go to the **Network** tab, filter by `XHR`, send any message or click around
> 5. Click any `api` request → **Headers** → find `Authorization: xoxc-...`
> 6. Copy that token value (starts with `xoxc-`)
>
> **In Slack Web (browser):**
> 1. Open `https://app.slack.com` and press **F12**
> 2. Same steps as above

Then ask the user to provide both values:

```
Please paste your xoxc token:
```

Wait for xoxc token, then:

```
Please paste your xoxd cookie value (the value of the 'd' cookie):
```

Wait for xoxd value.

## Step 2 — Save tokens

```bash
python3 "$HOME/.local/share/personal-skills/scripts/slack/save_slack_tokens.py" \
  --token "<XOXC_TOKEN>" \
  --cookie "<XOXD_VALUE>"
```

- **Exit 0:** Tell user: "Tokens saved and validated successfully! You can now use `/ps-slack-summary`."
- **Exit 1:** Show the error and ask the user to double-check they copied the correct values.
