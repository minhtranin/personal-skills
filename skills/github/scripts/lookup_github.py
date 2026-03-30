#!/usr/bin/env python3
"""Lookup cached GitHub repo summary. Exit 0 = found, Exit 1 = not found."""
import json, os, sys, re

CACHE_DIR = os.path.expanduser("~/.github-summary")

def slug(url):
    m = re.search(r"github\.com[/:]([^/]+)/([^/\s?#]+)", url)
    if not m: return None
    return f"{m.group(1)}__{m.group(2).removesuffix('.git')}"

def main():
    if len(sys.argv) < 2: sys.exit(1)
    s = slug(sys.argv[1])
    if not s: sys.exit(1)
    path = os.path.join(CACHE_DIR, f"{s}.json")
    if not os.path.exists(path): sys.exit(1)
    with open(path) as f:
        print(f.read())

if __name__ == "__main__":
    main()
