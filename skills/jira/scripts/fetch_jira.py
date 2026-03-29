#!/usr/bin/env python3
"""
Fetch a Jira issue (description + all comments) via REST API.
Reads credentials from env: JIRA_EMAIL, JIRA_API_TOKEN, JIRA_URL

Usage: fetch_jira.py <PROJ-123 | jira-issue-url>

Output: JSON { key, url, summary, type, status, priority, reporter,
               assignee, created, updated, description, comments[] }
Exit 0 = success, Exit 1 = config error, Exit 2 = API error
"""

import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error


def get_credentials():
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    url   = os.environ.get("JIRA_URL", "").strip().rstrip("/")
    missing = [k for k, v in [("JIRA_EMAIL", email), ("JIRA_API_TOKEN", token), ("JIRA_URL", url)] if not v]
    if missing:
        print(f"ERROR: Missing env var(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {auth}", url


def extract_key(arg: str) -> str:
    if re.match(r"^[A-Z][A-Z0-9_]+-\d+$", arg):
        return arg
    m = re.search(r"/(?:browse|issues?)/([A-Z][A-Z0-9_]+-\d+)", arg)
    if m:
        return m.group(1)
    print(f"ERROR: Cannot parse issue key from: {arg}", file=sys.stderr)
    sys.exit(1)


def jira_get(path: str, base_url: str, auth: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": auth, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code}: {e.read().decode(errors='replace')[:300]}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)


def extract_text(node) -> str:
    if isinstance(node, str):   return node
    if isinstance(node, list):  return "".join(extract_text(n) for n in node)
    if not isinstance(node, dict): return ""
    t = node.get("type", "")
    ch = node.get("content", [])
    if t == "doc":          return "".join(extract_text(c) for c in ch)
    if t == "paragraph":    return "".join(extract_text(c) for c in ch) + "\n"
    if t == "text":         return node.get("text", "")
    if t == "hardBreak":    return "\n"
    if t == "bulletList":   return "".join(extract_text(c) for c in ch)
    if t == "orderedList":  return "".join(extract_text(c) for c in ch)
    if t == "listItem":     return "• " + "".join(extract_text(c) for c in ch)
    if t == "heading":
        lvl = node.get("attrs", {}).get("level", 2)
        return "\n" + "#" * lvl + " " + "".join(extract_text(c) for c in ch) + "\n"
    if t == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        return f"\n```{lang}\n" + "".join(extract_text(c) for c in ch) + "\n```\n"
    if t == "inlineCode":   return "`" + node.get("text", "") + "`"
    if t == "blockquote":
        inner = "".join(extract_text(c) for c in ch)
        return "\n".join("> " + l for l in inner.splitlines()) + "\n"
    if t == "rule":         return "\n---\n"
    if t == "mention":      return "@" + node.get("attrs", {}).get("text", "someone")
    if ch:                  return "".join(extract_text(c) for c in ch)
    return ""


def display_name(obj) -> str:
    if not obj: return "Unassigned"
    return obj.get("displayName") or obj.get("emailAddress") or "Unknown"


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_jira.py <PROJ-123 | url>", file=sys.stderr)
        sys.exit(1)

    auth, base_url = get_credentials()
    key = extract_key(sys.argv[1])

    fields = "summary,description,comment,status,assignee,reporter,created,updated,priority,issuetype"
    data = jira_get(f"/rest/api/3/issue/{key}?fields={fields}", base_url, auth)
    f = data.get("fields", {})

    # Paginate comments if needed
    comments_raw = f.get("comment", {}).get("comments", [])
    total = f.get("comment", {}).get("total", len(comments_raw))
    start = len(comments_raw)
    while start < total:
        page = jira_get(f"/rest/api/3/issue/{key}/comment?startAt={start}&maxResults=50", base_url, auth)
        comments_raw.extend(page.get("comments", []))
        start += 50

    comments = [
        {
            "author": display_name(c.get("author")),
            "date":   c.get("created", ""),
            "body":   extract_text(c.get("body")).strip() if c.get("body") else "",
        }
        for c in comments_raw
    ]

    print(json.dumps({
        "key":         data.get("key"),
        "url":         f"{base_url}/browse/{data.get('key')}",
        "summary":     f.get("summary", ""),
        "type":        (f.get("issuetype") or {}).get("name", ""),
        "status":      (f.get("status") or {}).get("name", ""),
        "priority":    (f.get("priority") or {}).get("name", ""),
        "reporter":    display_name(f.get("reporter")),
        "assignee":    display_name(f.get("assignee")),
        "created":     f.get("created", ""),
        "updated":     f.get("updated", ""),
        "description": extract_text(f.get("description")).strip() if f.get("description") else "",
        "comments":    comments,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
