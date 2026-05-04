#!/usr/bin/env bash
# Checks and optionally installs yt-dlp and Python dependencies

set -e

MISSING=()

check_yt_dlp() {
  if command -v yt-dlp &>/dev/null; then
    echo "[ok] yt-dlp found: $(yt-dlp --version)"
  else
    MISSING+=("yt-dlp")
    echo "[missing] yt-dlp"
  fi
}

check_python() {
  if command -v python3 &>/dev/null; then
    echo "[ok] python3 found: $(python3 --version)"
  else
    MISSING+=("python3")
    echo "[missing] python3"
  fi
}

check_python_libs() {
  for lib in flask; do
    if uv run --with "$lib" python3 -c "import $lib" &>/dev/null 2>&1; then
      echo "[ok] python lib '$lib' found"
    else
      MISSING+=("uv:$lib")
      echo "[missing] python lib '$lib'"
    fi
  done
}

check_yt_dlp
check_python
check_python_libs

if [ ${#MISSING[@]} -eq 0 ]; then
  echo ""
  echo "All dependencies are installed."
  exit 0
fi

echo ""
echo "Missing dependencies: ${MISSING[*]}"
echo ""
read -r -p "Would you like to install them now? [y/N] " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
  for item in "${MISSING[@]}"; do
    if [ "$item" = "yt-dlp" ]; then
      echo "Installing yt-dlp..."
      uv tool install yt-dlp
    elif [ "$item" = "python3" ]; then
      echo "ERROR: python3 must be installed manually."
      echo "  Ubuntu/Debian: sudo apt install python3"
      echo "  macOS:         brew install python3"
      exit 1
    elif [[ "$item" == uv:* ]]; then
      lib="${item#uv:}"
      echo "Installing python lib '$lib'..."
      uv pip install "$lib"
    fi
  done
  echo ""
  echo "Done. All dependencies installed."
else
  echo "Skipped. Some features may not work without the dependencies."
  exit 1
fi
