#!/usr/bin/env python3
"""
Save a Medium article summary to ~/.medium-summary/.
Usage: save_medium.py --slug SLUG --url URL --title TITLE --author AUTHOR
                      --summary TEXT --key-points TEXT [--text TEXT]
                      [--data-dir DIR]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".medium-summary"


def slugify(text: str) -> str:
    """Turn a URL or title into a safe filename slug."""
    # Try to extract slug from Medium URL path
    m = re.search(r"/([a-z0-9-]+-[a-f0-9]{8,12})/?$", text)
    if m:
        return m.group(1)[:80]
    # Fallback: sanitize
    text = re.sub(r"https?://[^/]+", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:80] or "article"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--key-points", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--diagram-png", default="")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(args.slug)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = {
        "slug": slug,
        "url": args.url,
        "title": args.title,
        "author": args.author,
        "summary": args.summary,
        "key_points": args.key_points,
        "text": args.text[:4000],
        "diagram_png": args.diagram_png,
        "date": now,
    }

    summary_file = data_dir / f"{slug}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    # Update index
    index_file = data_dir / "index.json"
    index = []
    if index_file.exists():
        with open(index_file, encoding="utf-8") as f:
            index = json.load(f)

    index = [i for i in index if i.get("slug") != slug]
    index.append({
        "slug": slug,
        "url": args.url,
        "title": args.title,
        "author": args.author,
        "snippet": args.summary[:200].replace("\n", " "),
        "date": now,
    })

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Saved: {summary_file}")


if __name__ == "__main__":
    main()
