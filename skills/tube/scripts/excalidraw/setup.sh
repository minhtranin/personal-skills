#!/usr/bin/env bash
# Setup Excalidraw renderer: installs playwright and Chromium if missing

set -e

# Check playwright python package
if ! python3 -c "import playwright" &>/dev/null 2>&1; then
  echo "Installing playwright..."
  if command -v pip3 &>/dev/null; then
    pip3 install playwright -q
  elif command -v pip &>/dev/null; then
    pip install playwright -q
  else
    echo "ERROR: pip not found. Install pip first." >&2
    exit 1
  fi
fi

# Check if Chromium is installed for Playwright
if ! python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    import os, pathlib
    exe = p.chromium.executable_path
    if not pathlib.Path(exe).exists():
        raise FileNotFoundError(exe)
" &>/dev/null 2>&1; then
  echo "Installing Playwright Chromium..."
  python3 -m playwright install chromium
fi

echo "Excalidraw renderer ready."
