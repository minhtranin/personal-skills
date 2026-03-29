#!/usr/bin/env python3
"""
Look up a previously saved Medium summary by URL or slug.
Usage: lookup_medium.py <url-or-slug> [--data-dir DIR]

Exit codes:
  0  found — prints JSON to stdout
  1  not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".medium-summary"


def slugify(text: str) -> str:
    m = re.search(r"/([a-z0-9-]+-[a-f0-9]{8,12})/?$", text)
    if m:
        return m.group(1)[:80]
    text = re.sub(r"https?://[^/]+", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:80] or "article"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Medium URL or slug")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    slug = slugify(args.query)

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
