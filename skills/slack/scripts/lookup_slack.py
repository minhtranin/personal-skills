#!/usr/bin/env python3
"""
Look up a saved Slack thread summary by URL or thread ID.
Exit 0 = found (prints JSON), Exit 1 = not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".slack-summary"


def url_to_thread_id(url: str) -> str:
    m = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url)
    if m:
        return f"{m.group(1)}_{m.group(2)}_{m.group(3)}"
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", url)[:80]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    tid = url_to_thread_id(args.query)

    f = data_dir / f"{tid}.json"
    if f.exists():
        print(f.read_text(encoding="utf-8"))
        sys.exit(0)

    # Search index by URL
    index_file = data_dir / "index.json"
    if index_file.exists():
        for entry in json.loads(index_file.read_text()):
            if entry.get("url", "").strip() == args.query.strip():
                alt = data_dir / f"{entry['thread_id']}.json"
                if alt.exists():
                    print(alt.read_text(encoding="utf-8"))
                    sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
