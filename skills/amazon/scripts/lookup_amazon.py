#!/usr/bin/env python3
"""
Look up a previously saved Amazon/AWS blog summary by URL or slug.
Usage: lookup_amazon.py <url-or-slug> [--data-dir DIR]

Exit codes:
  0  found — prints JSON to stdout
  1  not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".amazon-summary"


def url_to_slug(text: str) -> str:
    """Extract slug from AWS blog URL or sanitize text."""
    # Try to extract last path segment from URL
    # e.g. https://aws.amazon.com/blogs/machine-learning/how-lendi-.../
    text = text.strip().rstrip("/")
    m = re.search(r"/([a-z0-9][a-z0-9-]{4,})\/?$", text)
    if m:
        return m.group(1)[:120]
    # Fallback: sanitize
    text = re.sub(r"https?://[^/]+", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:120] or "article"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="AWS blog URL or slug")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    slug = url_to_slug(args.query)

    # Direct slug lookup
    f = data_dir / f"{slug}.json"
    if f.exists():
        print(f.read_text(encoding="utf-8"))
        sys.exit(0)

    # Search index by exact URL
    index_file = data_dir / "index.json"
    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
        for entry in index:
            if entry.get("url", "").strip().rstrip("/") == args.query.strip().rstrip("/"):
                alt = data_dir / f"{entry['slug']}.json"
                if alt.exists():
                    print(alt.read_text(encoding="utf-8"))
                    sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
