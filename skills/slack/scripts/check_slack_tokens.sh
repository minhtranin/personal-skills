#!/usr/bin/env bash
# Check if Slack tokens are available — from saved file or desktop app.
# Exit 0 = ready, Exit 1 = not configured
#
# Token priority:
#   1. ~/.local/share/personal-skills/slack-tokens.json  (manually saved)
#   2. SLACK_TOKEN + SLACK_COOKIE env vars
#   3. Auto-extracted from Slack desktop app storage

TOKENS_FILE="$HOME/.local/share/personal-skills/slack-tokens.json"
SCRIPTS_DIR="$HOME/.local/share/personal-skills/scripts/slack"

# ── 1. Check saved tokens file ────────────────────────────────────────────────
if [ -f "$TOKENS_FILE" ]; then
  TOKEN=$(python3 -c "import json; d=json.load(open('$TOKENS_FILE')); print(d.get('token',''))" 2>/dev/null)
  if [ -n "$TOKEN" ]; then
    echo "[ok] Slack tokens loaded from $TOKENS_FILE"
    exit 0
  fi
fi

# ── 2. Check env vars ─────────────────────────────────────────────────────────
if [ -n "$SLACK_TOKEN" ] && [ -n "$SLACK_COOKIE" ]; then
  echo "[ok] Slack tokens loaded from environment"
  exit 0
fi

# ── 3. Try auto-extract from desktop app ─────────────────────────────────────
EXTRACT=$(python3 "$SCRIPTS_DIR/get_slack_tokens.py" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$EXTRACT" ]; then
  # Save extracted tokens
  mkdir -p "$(dirname "$TOKENS_FILE")"
  echo "$EXTRACT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
workspaces = data.get('workspaces', {})
if not workspaces:
    sys.exit(1)
# Use first workspace
ws = next(iter(workspaces.values()))
out = {'token': ws.get('token',''), 'd': ws.get('d',''), 'all_workspaces': workspaces}
print(json.dumps(out, indent=2))
" > "$TOKENS_FILE" 2>/dev/null
  chmod 600 "$TOKENS_FILE"
  echo "[ok] Slack tokens auto-extracted from desktop app and saved"
  exit 0
fi

# ── Not found — print setup instructions ─────────────────────────────────────
echo ""
echo "  Slack tokens not configured."
echo ""
echo "  The easiest way — extract from your browser (1 minute):"
echo ""
echo "  ── Step 1 ──────────────────────────────────────────────────────────"
echo "  Open https://app.slack.com in Chrome or Edge"
echo "  Make sure you are logged in to your workspace"
echo ""
echo "  ── Step 2: Get xoxd token ──────────────────────────────────────────"
echo "  Press F12 → Application tab → Storage → Cookies → app.slack.com"
echo "  Find the cookie named: d"
echo "  Copy its Value  (starts with xoxd-...)"
echo ""
echo "  ── Step 3: Get xoxc token ──────────────────────────────────────────"
echo "  Press F12 → Network tab → in filter box type: api"
echo "  Click any request in the list"
echo "  In Headers → Request Headers → find: Authorization"
echo "  Copy the value  (starts with xoxc-...)"
echo ""
echo "  ── Step 4: Save tokens ─────────────────────────────────────────────"
echo "  Run /ps-slack-login and paste both values when prompted by Claude"
echo ""
exit 1
