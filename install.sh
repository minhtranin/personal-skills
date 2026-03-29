#!/usr/bin/env bash
# personal-skills installer
#
# Install latest:
#   curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
#
# Install specific version:
#   curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --version v1.2.0
#
# Update to latest:
#   curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --update
#
# Check current version:
#   curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --version-check
#
# Local clone:
#   bash install.sh [--version v1.2.0] [--update] [--version-check]

set -e

GITHUB_REPO="minhtranin/personal-skills"
GITHUB_API="https://api.github.com/repos/$GITHUB_REPO"
SCRIPTS_INSTALL_DIR="$HOME/.local/share/personal-skills"
VERSION_FILE="$SCRIPTS_INSTALL_DIR/.version"

# Agent commands directories
CLAUDE_DIR="$HOME/.claude/commands"
ANTIGRAVITY_DIR="$HOME/.antigravity/commands"
OPENCODE_DIR="$HOME/.opencode/commands"

# ── Parse args ───────────────────────────────────────────────────────────────

TARGET_VERSION=""
MODE_UPDATE=false
MODE_VERSION_CHECK=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)       TARGET_VERSION="$2"; shift 2 ;;
    --update)        MODE_UPDATE=true; shift ;;
    --version-check) MODE_VERSION_CHECK=true; shift ;;
    *) shift ;;
  esac
done

# ── Detect local vs remote mode ──────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -d "$SCRIPT_DIR/skills" ]; then
  MODE="local"
  REPO_ROOT="$SCRIPT_DIR"
  # Read version from local VERSION file if present
  LOCAL_VERSION="$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo "local")"
else
  MODE="remote"
  command -v curl    &>/dev/null || { echo "ERROR: curl is required.   sudo apt install curl  |  brew install curl";   exit 1; }
  command -v python3 &>/dev/null || { echo "ERROR: python3 is required. sudo apt install python3 | brew install python3"; exit 1; }
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

current_version() {
  cat "$VERSION_FILE" 2>/dev/null || echo "none"
}

latest_release_tag() {
  curl -fsSL "$GITHUB_API/releases/latest" | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])"
}

raw_base_for_ref() {
  local ref="$1"
  echo "https://raw.githubusercontent.com/$GITHUB_REPO/$ref"
}

tree_for_ref() {
  local ref="$1"
  curl -fsSL "$GITHUB_API/git/trees/$ref?recursive=1"
}

# ── --version-check ──────────────────────────────────────────────────────────

if $MODE_VERSION_CHECK; then
  installed="$(current_version)"
  if [ "$MODE" = "remote" ]; then
    latest="$(latest_release_tag)"
    echo "Installed : $installed"
    echo "Latest    : $latest"
    [ "$installed" = "$latest" ] && echo "Status    : up to date" || echo "Status    : update available"
  else
    echo "Installed : $installed"
    echo "Repo      : $LOCAL_VERSION (local)"
  fi
  exit 0
fi

# ── Resolve target ref ───────────────────────────────────────────────────────

if [ "$MODE" = "remote" ]; then
  if $MODE_UPDATE || [ -z "$TARGET_VERSION" ]; then
    echo ""
    echo "→ Fetching latest release..."
    TARGET_VERSION="$(latest_release_tag)"
    echo "  Latest release: $TARGET_VERSION"
  fi
  GITHUB_RAW="$(raw_base_for_ref "$TARGET_VERSION")"
  GIT_REF="$TARGET_VERSION"
fi

# ── Banner ───────────────────────────────────────────────────────────────────

echo ""
echo "personal-skills installer"
echo "========================="
[ "$MODE" = "remote" ] && echo "Version : $TARGET_VERSION" || echo "Version : $LOCAL_VERSION (local)"
echo "Install : $SCRIPTS_INSTALL_DIR"
echo ""

# ── Check if already up to date (update mode only) ───────────────────────────

if $MODE_UPDATE && [ "$MODE" = "remote" ]; then
  installed="$(current_version)"
  if [ "$installed" = "$TARGET_VERSION" ]; then
    echo "Already up to date ($installed). Nothing to do."
    exit 0
  fi
  echo "Updating $installed → $TARGET_VERSION ..."
  echo ""
fi

# ── 1. Install scripts ───────────────────────────────────────────────────────

echo "→ Installing helper scripts..."

if [ "$MODE" = "local" ]; then
  for ns_dir in "$REPO_ROOT"/skills/*/; do
    ns="$(basename "$ns_dir")"
    [ -d "$ns_dir/scripts" ] || continue
    mkdir -p "$SCRIPTS_INSTALL_DIR/scripts/$ns"
    cp -r "$ns_dir/scripts"/. "$SCRIPTS_INSTALL_DIR/scripts/$ns/"
    chmod +x "$SCRIPTS_INSTALL_DIR/scripts/$ns/"*.sh 2>/dev/null || true
    echo "  ✓ scripts/$ns/"
  done
else
  SCRIPT_PATHS=$(tree_for_ref "$GIT_REF" | python3 -c "
import sys, json
for f in json.load(sys.stdin)['tree']:
    p = f['path']
    if p.startswith('skills/') and '/scripts/' in p and f['type'] == 'blob':
        print(p)
")
  for filepath in $SCRIPT_PATHS; do
    ns=$(echo "$filepath" | cut -d'/' -f2)
    filename=$(basename "$filepath")
    mkdir -p "$SCRIPTS_INSTALL_DIR/scripts/$ns"
    curl -fsSL "$GITHUB_RAW/$filepath" -o "$SCRIPTS_INSTALL_DIR/scripts/$ns/$filename"
    echo "  ✓ scripts/$ns/$filename"
  done
  find "$SCRIPTS_INSTALL_DIR/scripts" -name "*.sh" -exec chmod +x {} \;
fi

# ── 2. Install SKILL.md files into each detected agent ───────────────────────

echo ""
echo "→ Installing skill commands..."

install_skills() {
  local agent_name="$1"
  local commands_dir="$2"

  [ -d "$(dirname "$commands_dir")" ] || return 0  # parent dir (agent root) doesn't exist — skip

  mkdir -p "$commands_dir"

  if [ "$MODE" = "local" ]; then
    for skill_dir in "$REPO_ROOT"/skills/*/ps-*/; do
      [ -f "$skill_dir/SKILL.md" ] || continue
      skill_name="$(basename "$skill_dir")"
      cp "$skill_dir/SKILL.md" "$commands_dir/$skill_name.md"
      echo "  ✓ $agent_name: /$skill_name"
    done
  else
    SKILL_PATHS=$(tree_for_ref "$GIT_REF" | python3 -c "
import sys, json
for f in json.load(sys.stdin)['tree']:
    p = f['path']
    if p.endswith('SKILL.md') and f['type'] == 'blob':
        skill_name = p.split('/')[-2]
        if skill_name.startswith('ps-'):
            print(p)
")
    for filepath in $SKILL_PATHS; do
      skill_name=$(basename "$(dirname "$filepath")")
      curl -fsSL "$GITHUB_RAW/$filepath" -o "$commands_dir/$skill_name.md"
      echo "  ✓ $agent_name: /$skill_name"
    done
  fi
}

install_skills "Claude Code"  "$CLAUDE_DIR"
install_skills "Antigravity"  "$ANTIGRAVITY_DIR"
install_skills "OpenCode"     "$OPENCODE_DIR"

# ── 3. Save installed version ────────────────────────────────────────────────

if [ "$MODE" = "remote" ]; then
  echo "$TARGET_VERSION" > "$VERSION_FILE"
elif [ -f "$REPO_ROOT/VERSION" ]; then
  cp "$REPO_ROOT/VERSION" "$VERSION_FILE"
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "Done! Installed: $(current_version)"
echo ""
echo "Commands:"
echo "  /ps-tube-summary <youtube-url>   — summarize a YouTube video"
echo "  /ps-medium-summary <medium-url>  — summarize a Medium article"
echo "  /ps-jira-summary <PROJ-123>      — summarize a Jira issue"
echo "  /ps-jira-plantask <PROJ-123>    — plan + break + create subtasks from a Jira issue"
echo "  /ps-slack-login                  — save Slack tokens"
echo "  /ps-slack-summary <thread-url>   — summarize a Slack thread"
echo "  /ps-web                          — browse all history in browser"
echo ""
echo "Manage:"
echo "  # Check for updates"
echo "  curl -fsSL https://raw.githubusercontent.com/$GITHUB_REPO/main/install.sh | bash -s -- --version-check"
echo ""
echo "  # Update to latest"
echo "  curl -fsSL https://raw.githubusercontent.com/$GITHUB_REPO/main/install.sh | bash -s -- --update"
echo ""
echo "  # Install specific version"
echo "  curl -fsSL https://raw.githubusercontent.com/$GITHUB_REPO/main/install.sh | bash -s -- --version v1.2.0"
