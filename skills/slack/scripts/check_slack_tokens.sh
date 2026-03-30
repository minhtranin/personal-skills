#!/usr/bin/env bash
# Check if Slack tokens are available.
# Exit 0 = ready, Exit 1 = not configured
#
# Token priority:
#   1. Auto-extract from Slack desktop app storage (LevelDB)  ← always try first
#   2. Saved tokens file (~/.local/share/personal-skills/slack-tokens.json)

TOKENS_FILE="$HOME/.local/share/personal-skills/slack-tokens.json"
SCRIPTS_DIR="$HOME/.local/share/personal-skills/scripts/slack"

# ── 1. Try auto-extract from Slack desktop app storage ─────────────────────────
# Install deps needed for Linux cookie decryption (silent, best-effort)
python3 -c "import secretstorage, Crypto" 2>/dev/null || \
  pip3 install --quiet --break-system-packages secretstorage pycryptodome 2>/dev/null || true

EXTRACT=$(python3 "$SCRIPTS_DIR/get_slack_tokens.py" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$EXTRACT" ]; then
  mkdir -p "$(dirname "$TOKENS_FILE")"
  echo "$EXTRACT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
workspaces = data.get('workspaces', {})
if not workspaces:
    sys.exit(1)
# Use first workspace, store xoxd as 'd' for compatibility
ws = next(iter(workspaces.values()))
out = {'token': ws.get('token',''), 'd': ws.get('d',''), 'all_workspaces': workspaces}
print(json.dumps(out, indent=2))
" > "$TOKENS_FILE" 2>/dev/null
  chmod 600 "$TOKENS_FILE" 2>/dev/null
  echo "[ok] Slack tokens auto-extracted from desktop app ($SCRIPTS_DIR/get_slack_tokens.py)"
  exit 0
fi

# ── 2. Check saved tokens file ─────────────────────────────────────────────────
if [ -f "$TOKENS_FILE" ]; then
  TOKEN=$(python3 -c "import json; d=json.load(open('$TOKENS_FILE')); print(d.get('token',''))" 2>/dev/null)
  if [ -n "$TOKEN" ]; then
    echo "[ok] Slack tokens loaded from $TOKENS_FILE"
    exit 0
  fi
fi

# ── Not found ─────────────────────────────────────────────────────────────────
echo ""
echo "  Slack tokens not configured."
echo ""
echo "  Detected platform:"
case "$(uname -s)" in
  Linux)
    if [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null; then
      echo "  WSL (Windows Subsystem for Linux)"
      echo "  Auto-extract: looks for Windows Slack at %APPDATA%\\Slack\\storage"
    else
      echo "  Linux (native)"
      echo "  Auto-extract: looks for Slack at ~/.config/Slack/storage"
      if [ -d "$HOME/snap/slack" ]; then
        echo "  (also checked ~/snap/slack/current/.config/Slack/storage)"
      fi
      if [ -d "$HOME/.var/app/com.slack.Slack" ]; then
        echo "  (also checked ~/.var/app/com.slack.Slack/data/Slack/storage)"
      fi
    fi
    ;;
  Darwin) echo "  macOS — auto-extract: looks for ~/Library/Application Support/Slack/storage" ;;
  *)      echo "  $(uname -s)" ;;
esac
echo ""
echo "  Manual fallback (F12 DevTools):"
echo ""
echo "  1. Open Slack desktop app (or https://app.slack.com in browser)"
echo "  2. Press F12 → Application tab"
echo "     - Cookies → find 'd' cookie → copy Value  (starts xoxd-)"
echo "     - Network tab → filter 'api' → find Authorization header  (starts xoxc-)"
echo "  3. Save manually:"
echo ""
echo "     python3 $SCRIPTS_DIR/save_slack_tokens.py --token xoxc-... --cookie xoxd-..."
echo ""
exit 1
