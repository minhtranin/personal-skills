#!/usr/bin/env bash
# Check dependencies for excalidraw skill

REFS_DIR="$HOME/.local/share/personal-skills/scripts/excalidraw/references"

check_uv() {
    if ! command -v uv &>/dev/null; then
        echo "ERROR: 'uv' is not installed."
        echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
}

check_playwright() {
    if ! uv run --project "$REFS_DIR" python -c "import playwright" &>/dev/null 2>&1; then
        echo "Playwright not found. Installing..."
        cd "$REFS_DIR" && uv sync && uv run playwright install chromium
    fi
}

check_uv || exit 1
check_playwright || exit 1

echo "All excalidraw dependencies OK."
