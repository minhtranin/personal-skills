#!/usr/bin/env python3
"""Detect summary content type from a URL or Jira issue key."""
import sys, re

def detect(s):
    s = s.strip()
    if "youtube.com" in s or "youtu.be" in s:          return "youtube"
    if "medium.com"  in s or "freedium" in s:          return "medium"
    if "slack.com/archives" in s:                       return "slack"
    if "github.com"  in s:                             return "github"
    if "aws.amazon.com" in s or "amazon.com/blogs" in s or "amazon.science" in s: return "amazon"
    if "atlassian.net" in s:                            return "jira"
    if re.match(r"^[A-Z][A-Z0-9]+-\d+$", s):           return "jira"
    return "unknown"

if __name__ == "__main__":
    print(detect(sys.argv[1]) if len(sys.argv) > 1 else "unknown")
