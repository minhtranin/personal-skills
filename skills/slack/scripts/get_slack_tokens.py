#!/usr/bin/env python3
"""
Auto-extract xoxc + xoxd tokens from the Slack desktop app's LevelDB storage.

Supports:
  Windows (native)  : %APPDATA%\Slack\storage\
  Windows via WSL   : /mnt/c/Users/<user>/AppData/Roaming/Slack/storage/
  macOS             : ~/Library/Application Support/Slack/storage/
  Linux             : ~/.config/Slack/storage/

Output JSON: { "workspaces": { "TXXXXXXX": { "token": "xoxc-...", "d": "xoxd-..." } } }
Exit 0 = found, Exit 1 = not found / error
"""

import json
import os
import re
import struct
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate Slack storage directory
# ---------------------------------------------------------------------------

def find_slack_storage() -> Path | None:
    candidates = []

    # Linux native (.deb/.rpm)
    candidates.append(Path.home() / ".config/Slack/storage")

    # Linux Snap
    snap_base = Path.home() / "snap" / "slack" / "current"
    if snap_base.exists():
        candidates.append(snap_base / ".config/Slack/storage")

    # Linux Flatpak
    candidates.append(Path.home() / ".var/app/com.slack.Slack/data/Slack/storage")

    # macOS
    candidates.append(Path.home() / "Library/Application Support/Slack/storage")

    # Windows native (from WSL)
    win_user = _wsl_windows_user()
    if win_user:
        candidates.append(Path(f"/mnt/c/Users/{win_user}/AppData/Roaming/Slack/storage"))

    for path in candidates:
        if path.exists():
            return path

    return None


def _wsl_windows_user() -> str | None:
    """Detect Windows username when running inside WSL."""
    try:
        # /proc/version contains "Microsoft" on WSL
        proc = Path("/proc/version")
        if not proc.exists() or "microsoft" not in proc.read_text().lower():
            return None
        # Try reading from wslenv or environment
        win_user = os.environ.get("USERPROFILE", "")
        if win_user:
            m = re.search(r"[Cc]:\\[Uu]sers\\([^\\]+)", win_user)
            if m:
                return m.group(1)
        # Fallback: list /mnt/c/Users and pick first non-system dir
        users_dir = Path("/mnt/c/Users")
        if users_dir.exists():
            skip = {"Public", "Default", "Default User", "All Users"}
            for d in users_dir.iterdir():
                if d.is_dir() and d.name not in skip:
                    slack_path = d / "AppData/Roaming/Slack/storage"
                    if slack_path.exists():
                        return d.name
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# LevelDB reader (minimal — reads only the log/SST files we need)
# ---------------------------------------------------------------------------

def read_leveldb_simple(storage_dir: Path) -> dict[str, str]:
    """
    Extract key-value pairs from LevelDB without a full LevelDB library.
    Scans .ldb and .log files for xoxc/xoxd token patterns using regex.
    This is intentionally simple — we only need a few specific values.
    """
    results = {}
    token_pattern = re.compile(rb'xox[cdp]-[0-9A-Za-z%-]+')

    # Also look for the workspaces JSON blob
    workspace_pattern = re.compile(
        rb'"token"\s*:\s*"(xoxc-[^"]+)".*?"d"\s*:\s*"(xoxd-[^"]+)"',
        re.DOTALL
    )

    raw_chunks = []

    for ext in ("*.ldb", "*.log", "CURRENT", "MANIFEST*"):
        for f in storage_dir.glob(ext):
            try:
                data = f.read_bytes()
                raw_chunks.append(data)
            except Exception:
                pass

    combined = b"\n".join(raw_chunks)

    # Try structured workspace pattern first
    for m in workspace_pattern.finditer(combined):
        xoxc = m.group(1).decode(errors="replace")
        xoxd = m.group(2).decode(errors="replace")
        # Extract team ID from xoxc token
        parts = xoxc.split("-")
        team_id = parts[1] if len(parts) > 1 else "unknown"
        results[team_id] = {"token": xoxc, "d": xoxd}

    if results:
        return results

    # Fallback: just collect all tokens found
    tokens = [t.decode(errors="replace") for t in token_pattern.findall(combined)]
    xoxc_tokens = [t for t in tokens if t.startswith("xoxc-")]
    xoxd_tokens = [t for t in tokens if t.startswith("xoxd-")]

    for i, xoxc in enumerate(xoxc_tokens):
        parts = xoxc.split("-")
        team_id = parts[1] if len(parts) > 1 else f"workspace_{i}"
        entry = {"token": xoxc}
        if i < len(xoxd_tokens):
            entry["d"] = xoxd_tokens[i]
        results[team_id] = entry

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    storage = find_slack_storage()
    if not storage:
        print("ERROR: Slack desktop app storage not found.", file=sys.stderr)
        print("Make sure Slack desktop app is installed and you have logged in at least once.", file=sys.stderr)
        sys.exit(1)

    workspaces = read_leveldb_simple(storage)
    if not workspaces:
        print("ERROR: No Slack tokens found in storage.", file=sys.stderr)
        print(f"Storage path checked: {storage}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"workspaces": workspaces, "storage_path": str(storage)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
