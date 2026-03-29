#!/usr/bin/env python3
"""
Save a Jira issue summary to ~/.jira-summary/.
Usage: save_jira.py --key PROJ-123 --url URL --issue-summary TEXT
                    --type TYPE --status STATUS --reporter R --assignee A
                    --summary TEXT --key-points TEXT [--data-dir DIR]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".jira-summary"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--issue-summary", default="")   # original Jira title
    parser.add_argument("--type", default="")
    parser.add_argument("--status", default="")
    parser.add_argument("--reporter", default="")
    parser.add_argument("--assignee", default="")
    parser.add_argument("--summary", default="")         # AI-generated summary
    parser.add_argument("--key-points", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    key = args.key.upper()

    entry = {
        "key": key,
        "url": args.url,
        "issue_summary": args.issue_summary,
        "type": args.type,
        "status": args.status,
        "reporter": args.reporter,
        "assignee": args.assignee,
        "summary": args.summary,
        "key_points": args.key_points,
        "description": args.description[:4000],
        "date": now,
    }

    (data_dir / f"{key}.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    index_file = data_dir / "index.json"
    index = json.loads(index_file.read_text()) if index_file.exists() else []
    index = [i for i in index if i.get("key") != key]
    index.append({
        "key": key,
        "url": args.url,
        "issue_summary": args.issue_summary,
        "status": args.status,
        "assignee": args.assignee,
        "snippet": args.summary[:200].replace("\n", " "),
        "date": now,
    })
    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {data_dir / key}.json")


if __name__ == "__main__":
    main()
