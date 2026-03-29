#!/usr/bin/env python3
"""
Look up a previously saved Jira summary by issue key or URL.
Usage: lookup_jira.py <key-or-url> [--data-dir DIR]

Exit codes:
  0  found — prints JSON to stdout
  1  not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".jira-summary"


def normalize_key(arg: str) -> str:
    if re.match(r"^[A-Z][A-Z0-9_]+-\d+$", arg):
        return arg.upper()
    m = re.search(r"/(?:browse|issues?)/([A-Z][A-Z0-9_]+-\d+)", arg)
    if m:
        return m.group(1).upper()
    return arg.upper()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    key = normalize_key(args.query)

    f = data_dir / f"{key}.json"
    if f.exists():
        print(f.read_text(encoding="utf-8"))
        sys.exit(0)

    # Search index by URL
    index_file = data_dir / "index.json"
    if index_file.exists():
        for entry in json.loads(index_file.read_text()):
            if normalize_key(entry.get("url", "")) == key or entry.get("key", "") == key:
                alt = data_dir / f"{entry['key']}.json"
                if alt.exists():
                    print(alt.read_text(encoding="utf-8"))
                    sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
