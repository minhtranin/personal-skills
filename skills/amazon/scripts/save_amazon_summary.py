#!/usr/bin/env python3
"""
Save an Amazon/AWS blog summary to ~/.amazon-summary/.
Usage: save_amazon_summary.py --slug SLUG --url URL --title TITLE
                               --author AUTHOR --category CATEGORY
                               --summary TEXT --key-points TEXT
                               [--text TEXT] [--diagram-png PATH]
                               [--data-dir DIR]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".amazon-summary"


def url_to_slug(text: str) -> str:
    """Extract slug from AWS blog URL or sanitize text."""
    text = text.strip().rstrip("/")
    m = re.search(r"/([a-z0-9][a-z0-9-]{4,})\/?$", text)
    if m:
        return m.group(1)[:120]
    text = re.sub(r"https?://[^/]+", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:120] or "article"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--key-points", default="")
    parser.add_argument("--tech-stack", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--diagram-png", default="")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    slug = url_to_slug(args.slug)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Copy diagram to persistent location so web server can serve it later
    diagram_png = args.diagram_png
    if diagram_png:
        src = Path(diagram_png)
        if src.exists():
            diagrams_dir = data_dir / "diagrams"
            diagrams_dir.mkdir(parents=True, exist_ok=True)
            dest = diagrams_dir / f"{slug}.png"
            import shutil
            shutil.copy2(src, dest)
            diagram_png = str(dest)

    entry = {
        "slug": slug,
        "url": args.url,
        "title": args.title,
        "author": args.author,
        "category": args.category,
        "summary": args.summary,
        "key_points": args.key_points,
        "tech_stack": args.tech_stack,
        "text": args.text[:4000],
        "diagram_png": diagram_png,
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
        "category": args.category,
        "snippet": args.summary[:200].replace("\n", " "),
        "date": now,
    })

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Saved: {summary_file}")


if __name__ == "__main__":
    main()
