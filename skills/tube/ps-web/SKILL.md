---
name: ps-web
description: Launch a local web server to browse personal-skills history (YouTube summaries, etc.). Use when the user runs /ps-web or asks to view their summary history in a browser.
argument-hint: [--port 5050]
allowed-tools: [Bash]
---

# Personal Skills History Browser

The user wants to browse their summary history in a browser.

**Arguments:** $ARGUMENTS

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh" 2>/dev/null
```

If that file does not exist:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

If it fails, tell the user to run the installer manually and stop.

## Step 1 — Check dependencies

```bash
bash "$HOME/.local/share/personal-skills/scripts/tube/check_deps.sh"
```

If dependencies are missing and the user declines to install, stop here.

## Step 2 — Determine port

Default port: `5050`. If the user passed `--port XXXX` in arguments, use that instead.

## Step 3 — Check if port is already in use

```bash
lsof -i :<PORT> 2>/dev/null | head -5
```

If the port is taken, inform the user and suggest `--port 5051`.

## Step 4 — Launch the server in background

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/web_server.py" --port <PORT> &
sleep 1
curl -s -o /dev/null -w "%{http_code}" http://localhost:<PORT>/
```

## Step 5 — Inform the user

Tell the user:
- Server is running at `http://localhost:<PORT>`
- Open it in the browser to see history
- Stop it: `kill $(lsof -ti :<PORT>)` or Ctrl+C if in foreground
- Each `/ps-tube-summary <url>` adds a new entry to the list
