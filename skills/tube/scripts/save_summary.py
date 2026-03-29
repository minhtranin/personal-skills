#!/usr/bin/env python3
"""
Save a summary entry to the data directory.
Usage: save_summary.py --video-id ID --url URL --title TITLE
                       --summary TEXT --key-points TEXT [--transcript TEXT]
                       [--data-dir DIR]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".youtube-summary"


def sanitize_id(video_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", video_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--key-points", default="")
    parser.add_argument("--transcript", default="")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    video_id = sanitize_id(args.video_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Save individual summary file
    entry = {
        "video_id": video_id,
        "url": args.url,
        "title": args.title,
        "summary": args.summary,
        "key_points": args.key_points,
        "transcript": args.transcript,
        "date": now,
    }
    summary_file = data_dir / f"{video_id}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    # Update index
    index_file = data_dir / "index.json"
    index = []
    if index_file.exists():
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)

    # Remove existing entry for this video if any
    index = [i for i in index if i.get("video_id") != video_id]

    snippet = args.summary[:200].replace("\n", " ") if args.summary else ""
    index.append({
        "video_id": video_id,
        "url": args.url,
        "title": args.title,
        "snippet": snippet,
        "date": now,
    })

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Saved: {summary_file}")


if __name__ == "__main__":
    main()
