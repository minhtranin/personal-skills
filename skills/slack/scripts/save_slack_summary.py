#!/usr/bin/env python3
"""
Save a Slack thread summary to ~/.slack-summary/.
Usage: save_slack_summary.py --thread-id ID --url URL --channel CHANNEL
                             --summary TEXT --key-points TEXT
                             --participants LIST [--data-dir DIR]
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".slack-summary"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread-id",    required=True)
    parser.add_argument("--url",          required=True)
    parser.add_argument("--channel",      default="")
    parser.add_argument("--parent-text",  default="")
    parser.add_argument("--summary",      default="")
    parser.add_argument("--key-points",   default="")
    parser.add_argument("--participants", default="")
    parser.add_argument("--reply-count",  default="0")
    parser.add_argument("--diagram-png",  default="")
    parser.add_argument("--data-dir",     default=str(DEFAULT_DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)

    tid  = re.sub(r"[^a-zA-Z0-9_.-]", "_", args.thread_id)[:80]
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = {
        "thread_id":    tid,
        "url":          args.url,
        "channel":      args.channel,
        "parent_text":  args.parent_text[:300],
        "summary":      args.summary,
        "key_points":   args.key_points,
        "participants": args.participants,
        "reply_count":  args.reply_count,
        "diagram_png":  args.diagram_png,
        "date":         now,
    }

    (data_dir / f"{tid}.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    index_file = data_dir / "index.json"
    index = json.loads(index_file.read_text()) if index_file.exists() else []
    index = [i for i in index if i.get("thread_id") != tid]
    index.append({
        "thread_id":   tid,
        "url":         args.url,
        "channel":     args.channel,
        "parent_text": args.parent_text[:120].replace("\n", " "),
        "snippet":     args.summary[:200].replace("\n", " "),
        "reply_count": args.reply_count,
        "date":        now,
    })
    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {data_dir / tid}.json")


if __name__ == "__main__":
    main()
