#!/usr/bin/env bash
# Check JIRA_EMAIL, JIRA_API_TOKEN, JIRA_URL are set and valid.
# Prints step-by-step setup guide if anything is missing.
# Exit 0 = ready, Exit 1 = not configured or invalid

MISSING=()
[ -z "$JIRA_EMAIL" ]     && MISSING+=("JIRA_EMAIL")
[ -z "$JIRA_API_TOKEN" ] && MISSING+=("JIRA_API_TOKEN")
[ -z "$JIRA_URL" ]       && MISSING+=("JIRA_URL")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo ""
  echo "  Jira credentials not configured (missing: ${MISSING[*]})"
  echo ""
  echo "  ── Step 1: Get your Jira URL ───────────────────────────────────────"
  echo "  Open any Jira issue in your browser."
  echo "  Your Jira URL is the domain part, e.g.:"
  echo "    https://yourcompany.atlassian.net"
  echo ""
  echo "  ── Step 2: Create an API token ─────────────────────────────────────"
  echo "  1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens"
  echo "  2. Click 'Create API token'"
  echo "  3. Give it a label e.g. 'personal-skills'"
  echo "  4. Click 'Create' then copy the token value"
  echo ""
  echo "  ── Step 3: Add to your shell profile ───────────────────────────────"
  echo ""
  echo "  bash/zsh — add to ~/.bashrc or ~/.zshrc:"
  echo "    export JIRA_EMAIL=\"you@example.com\""
  echo "    export JIRA_API_TOKEN=\"your-token-here\""
  echo "    export JIRA_URL=\"https://yourcompany.atlassian.net\""
  echo ""
  echo "  fish — add to ~/.config/fish/config.fish:"
  echo "    set -gx JIRA_EMAIL \"you@example.com\""
  echo "    set -gx JIRA_API_TOKEN \"your-token-here\""
  echo "    set -gx JIRA_URL \"https://yourcompany.atlassian.net\""
  echo ""
  echo "  ── Step 4: Reload your shell ───────────────────────────────────────"
  echo "  bash/zsh:  source ~/.bashrc   or   source ~/.zshrc"
  echo "  fish:      source ~/.config/fish/config.fish"
  echo ""
  echo "  Then re-run /ps-jira-summary"
  echo ""
  exit 1
fi

# Validate against Jira API
RESP=$(mktemp)
trap 'rm -f "$RESP"' EXIT

HTTP=$(curl -s -o "$RESP" -w "%{http_code}" \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Accept: application/json" \
  "${JIRA_URL%/}/rest/api/3/myself" 2>/dev/null)

case "$HTTP" in
  200)
    NAME=$(python3 -c "import json; d=json.load(open('$RESP')); print(d.get('displayName') or d.get('emailAddress',''))" 2>/dev/null)
    echo "[ok] Connected to Jira as: ${NAME:-$JIRA_EMAIL}"
    exit 0
    ;;
  401)
    echo "[error] Invalid email or API token (HTTP 401)"
    echo "  Regenerate at: https://id.atlassian.com/manage-profile/security/api-tokens"
    exit 1
    ;;
  403)
    echo "[error] Access denied (HTTP 403) — check JIRA_URL: $JIRA_URL"
    exit 1
    ;;
  000)
    echo "[error] Cannot reach $JIRA_URL — check the URL and your network"
    exit 1
    ;;
  *)
    echo "[error] Unexpected HTTP $HTTP from $JIRA_URL"
    exit 1
    ;;
esac
