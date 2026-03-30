#!/usr/bin/env python3
"""
Auto-extract xoxc + xoxd tokens from the Slack desktop app.

Supports:
  Windows (native)  : %APPDATA%\Slack\storage\
  Windows via WSL   : /mnt/c/Users/<user>/AppData/Roaming/Slack/storage/
  macOS             : ~/Library/Application Support/Slack/storage/
  Linux (.deb/.rpm) : ~/.config/Slack/Local Storage/leveldb/  (xoxc)
                      ~/.config/Slack/Cookies                  (xoxd, decrypted via keyring)

Output JSON: { "workspaces": { "TXXXXXXX": { "token": "xoxc-...", "d": "xoxd-..." } } }
Exit 0 = found, Exit 1 = not found / error
"""

import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate Slack storage directory (for xoxc via LevelDB)
# ---------------------------------------------------------------------------

def find_slack_storage() -> Path | None:
    candidates = []

    # Linux native (.deb/.rpm) — Electron Local Storage LevelDB
    candidates.append(Path.home() / ".config/Slack/Local Storage/leveldb")
    # Legacy path (older Slack versions)
    candidates.append(Path.home() / ".config/Slack/storage")

    # Linux Snap
    snap_base = Path.home() / "snap" / "slack" / "current"
    if snap_base.exists():
        candidates.append(snap_base / ".config/Slack/Local Storage/leveldb")
        candidates.append(snap_base / ".config/Slack/storage")

    # Linux Flatpak
    candidates.append(Path.home() / ".var/app/com.slack.Slack/data/Slack/Local Storage/leveldb")
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
        proc = Path("/proc/version")
        if not proc.exists() or "microsoft" not in proc.read_text().lower():
            return None
        win_user = os.environ.get("USERPROFILE", "")
        if win_user:
            m = re.search(r"[Cc]:\\[Uu]sers\\([^\\]+)", win_user)
            if m:
                return m.group(1)
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
# LevelDB reader — extracts xoxc tokens
# ---------------------------------------------------------------------------

def read_leveldb_simple(storage_dir: Path) -> dict[str, str]:
    """
    Extract key-value pairs from LevelDB without a full LevelDB library.
    Scans .ldb and .log files for xoxc/xoxd token patterns using regex.
    """
    results = {}
    token_pattern = re.compile(rb'xox[cdp]-[0-9A-Za-z%-]+')

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
        parts = xoxc.split("-")
        team_id = parts[1] if len(parts) > 1 else "unknown"
        results[team_id] = {"token": xoxc, "d": xoxd}

    if results:
        return results

    # Fallback: collect all tokens found
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
# Linux: decrypt xoxd from Slack Cookies via Secret Service keyring
# ---------------------------------------------------------------------------

def extract_xoxd_linux() -> str | None:
    """
    On Linux, Slack stores the xoxd cookie encrypted in ~/.config/Slack/Cookies
    using AES-CBC with a key from the system keyring (Secret Service / GNOME Keyring).
    """
    cookies_path = Path.home() / ".config/Slack/Cookies"
    if not cookies_path.exists():
        return None

    try:
        import hashlib
        import sqlite3
        from Crypto.Cipher import AES
        import secretstorage

        # Get Slack's encryption key from keyring
        bus = secretstorage.dbus_init()
        col = secretstorage.get_default_collection(bus)
        slack_secret = None
        for item in col.get_all_items():
            if item.get_attributes().get("application") == "Slack":
                slack_secret = item.get_secret()
                break

        if not slack_secret:
            return None

        # Derive AES-128 key via PBKDF2-SHA1
        aes_key = hashlib.pbkdf2_hmac("sha1", slack_secret, b"saltysalt", 1, dklen=16)

        # Read encrypted d cookie
        conn = sqlite3.connect(f"file:{cookies_path}?mode=ro", uri=True)
        row = conn.execute("SELECT encrypted_value FROM cookies WHERE name='d'").fetchone()
        conn.close()

        if not row:
            return None

        enc = bytes(row[0])
        if len(enc) < 19:
            return None

        prefix = enc[:3]
        if prefix == b"v10":
            iv = b" " * 16
            cipher_text = enc[3:]
        elif prefix == b"v11":
            iv = enc[3:19]
            cipher_text = enc[19:]
        else:
            return None

        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(cipher_text)
        pad = decrypted[-1]
        decrypted = decrypted[:-pad]
        text = decrypted.decode(errors="replace")

        # Extract clean xoxd- token (skip any garbage prefix bytes)
        m = re.search(r"xoxd-[0-9A-Za-z%\-_]+", text)
        return m.group(0) if m else None

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    storage = find_slack_storage()
    workspaces = {}

    if storage:
        workspaces = read_leveldb_simple(storage)

    # On Linux, try to decrypt xoxd from Cookies if not already found
    if sys.platform != "darwin" and not any("d" in v for v in workspaces.values()):
        xoxd = extract_xoxd_linux()
        if xoxd:
            if workspaces:
                # Attach xoxd to the first workspace found
                first_key = next(iter(workspaces))
                workspaces[first_key]["d"] = xoxd
            else:
                workspaces["unknown"] = {"d": xoxd}

    if not workspaces:
        print("ERROR: No Slack tokens found in storage.", file=sys.stderr)
        if storage:
            print(f"Storage path checked: {storage}", file=sys.stderr)
        else:
            print("Slack desktop app storage not found.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"workspaces": workspaces, "storage_path": str(storage or "")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
