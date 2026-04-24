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
CLAUDE_DIR="$HOME/.claude/skills"                          # folder-per-skill structure
ANTIGRAVITY_DIR="$HOME/.gemini/antigravity/skills"          # folder-per-skill structure
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
  command -v unzip   &>/dev/null || { echo "ERROR: unzip is required.  sudo apt install unzip  |  brew install unzip";  exit 1; }
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

current_version() {
  cat "$VERSION_FILE" 2>/dev/null || echo "none"
}

latest_release_tag() {
  curl -fsSL "$GITHUB_API/releases/latest" | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])"
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

# ── Resolve target version ───────────────────────────────────────────────────

if [ "$MODE" = "remote" ]; then
  if $MODE_UPDATE || [ -z "$TARGET_VERSION" ]; then
    echo ""
    echo "→ Fetching latest release..."
    TARGET_VERSION="$(latest_release_tag)"
    echo "  Latest release: $TARGET_VERSION"
  fi
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

# ── Download release zip (remote mode) ───────────────────────────────────────

if [ "$MODE" = "remote" ]; then
  TMPDIR_WORK="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR_WORK"' EXIT

  ZIP_URL="https://github.com/$GITHUB_REPO/archive/refs/tags/$TARGET_VERSION.zip"
  ZIP_FILE="$TMPDIR_WORK/release.zip"

  echo "→ Downloading release $TARGET_VERSION..."
  curl -fsSL --retry 3 --retry-delay 2 "$ZIP_URL" -o "$ZIP_FILE"

  echo "→ Extracting..."
  unzip -q "$ZIP_FILE" -d "$TMPDIR_WORK"

  # The zip extracts to e.g. personal-skills-v0.4.3/ or personal-skills-0.4.3/
  REPO_ROOT="$(find "$TMPDIR_WORK" -maxdepth 1 -type d -name "personal-skills-*" | head -1)"
  if [ -z "$REPO_ROOT" ]; then
    echo "ERROR: could not find extracted repo directory in zip"
    exit 1
  fi
fi

# ── 1. Install scripts ───────────────────────────────────────────────────────

echo "→ Installing helper scripts..."

for ns_dir in "$REPO_ROOT"/skills/*/; do
  ns="$(basename "$ns_dir")"
  [ -d "$ns_dir/scripts" ] || continue
  mkdir -p "$SCRIPTS_INSTALL_DIR/scripts/$ns"
  cp -r "$ns_dir/scripts"/. "$SCRIPTS_INSTALL_DIR/scripts/$ns/"
  chmod +x "$SCRIPTS_INSTALL_DIR/scripts/$ns/"*.sh 2>/dev/null || true
  echo "  ✓ scripts/$ns/"
done

# ── 2. Install SKILL.md files into each detected agent ───────────────────────

echo ""
echo "→ Installing skill commands..."

# Install as flat .md files (Claude Code, OpenCode style)
install_skills_flat() {
  local agent_name="$1"
  local commands_dir="$2"

  [ -d "$(dirname "$commands_dir")" ] || return 0  # parent dir doesn't exist — skip

  mkdir -p "$commands_dir"

  for skill_dir in "$REPO_ROOT"/skills/*/ps:*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name="$(basename "$skill_dir")"
    cp "$skill_dir/SKILL.md" "$commands_dir/$skill_name.md"
    echo "  ✓ $agent_name: /$skill_name"
  done
}

# Install as folder-per-skill with SKILL.md (Antigravity global_skills style)
install_skills_folder() {
  local agent_name="$1"
  local skills_dir="$2"

  [ -d "$(dirname "$skills_dir")" ] || return 0  # parent dir doesn't exist — skip

  mkdir -p "$skills_dir"

  for skill_dir in "$REPO_ROOT"/skills/*/ps:*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$skills_dir/$skill_name"
    cp "$skill_dir/SKILL.md" "$skills_dir/$skill_name/SKILL.md"
    echo "  ✓ $agent_name: /$skill_name"
  done
}

install_skills_folder "Claude Code"  "$CLAUDE_DIR"
install_skills_folder "Antigravity"  "$ANTIGRAVITY_DIR"
install_skills_flat   "OpenCode"     "$OPENCODE_DIR"

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
echo "  /ps:summary <url-or-issue-key>   — summarize YouTube / Medium / Jira / GitHub / AWS / Slack (auto-detect)"
echo "  /ps:jira-plantask <PROJ-123>     — plan + break + create subtasks from a Jira issue"
echo "  /ps:slack-answer <thread-url>    — research codebase and draft a reply to a Slack thread"
echo "  /ps:web                          — browse all history in browser"
echo "  /ps:bot-telegram                 — Telegram bot: chat with Claude Code from your phone"
echo ""
if [ "$MODE" = "remote" ]; then
  echo "What's new in $TARGET_VERSION:"
  curl -fsSL "$GITHUB_API/releases/latest" 2>/dev/null \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('body',''))" \
    | head -20
fi
