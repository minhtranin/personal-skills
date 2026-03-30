#!/usr/bin/env python3
"""Save GitHub repo summary to cache."""
import argparse, json, os, re, sys
from datetime import datetime

CACHE_DIR = os.path.expanduser("~/.github-summary")

def slug(url):
    m = re.search(r"github\.com[/:]([^/]+)/([^/\s?#]+)", url)
    if not m: return None
    return f"{m.group(1)}__{m.group(2).removesuffix('.git')}"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--full-name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--summary", required=True)
    p.add_argument("--key-points", required=True)
    p.add_argument("--stars", default="0")
    p.add_argument("--language", default="")
    p.add_argument("--topics", default="")
    p.add_argument("--diagram-png", default="")
    args = p.parse_args()

    s = slug(args.url)
    if not s:
        print("ERROR: could not parse URL", file=sys.stderr)
        sys.exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)
    data = {
        "url": args.url,
        "full_name": args.full_name,
        "description": args.description,
        "summary": args.summary,
        "key_points": args.key_points,
        "stars": args.stars,
        "language": args.language,
        "topics": args.topics,
        "diagram_png": args.diagram_png,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    path = os.path.join(CACHE_DIR, f"{s}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {path}")

if __name__ == "__main__":
    main()
