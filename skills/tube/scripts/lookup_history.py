#!/usr/bin/env python3
"""
Look up a previously saved summary by URL or video ID.
Usage: lookup_history.py <url-or-video-id> [--data-dir DIR]

Exit codes:
  0  — found, prints JSON to stdout
  1  — not found
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DEFAULT_DATA_DIR = Path.home() / ".youtube-summary"


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from a URL or return as-is if already an ID."""
    s = url_or_id.strip()

    # youtu.be/ID
    m = re.match(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)

    # youtube.com/watch?v=ID
    m = re.match(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)

    # youtube.com/shorts/ID or /embed/ID or /v/ID
    m = re.match(r"(?:https?://)?(?:www\.)?youtube\.com/(?:shorts|embed|v)/([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)

    # Bare 11-char video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", s):
        return s

    return re.sub(r"[^a-zA-Z0-9_-]", "_", s)


def sanitize_id(video_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", video_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="YouTube URL or video ID to look up")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    video_id = sanitize_id(extract_video_id(args.query))

    summary_file = data_dir / f"{video_id}.json"
    if summary_file.exists():
        with open(summary_file, encoding="utf-8") as f:
            data = json.load(f)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Also search index by URL in case ID didn't match exactly
    index_file = data_dir / "index.json"
    if index_file.exists():
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)
        for entry in index:
            if entry.get("url", "").strip() == args.query.strip():
                alt_file = data_dir / f"{entry['video_id']}.json"
                if alt_file.exists():
                    with open(alt_file, encoding="utf-8") as f:
                        data = json.load(f)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
