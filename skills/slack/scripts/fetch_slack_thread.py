#!/usr/bin/env python3
"""
Fetch a Slack thread (parent message + all replies) including nested threads.
Usage: fetch_slack_thread.py <slack-thread-url>

Reads tokens from (in order):
  1. ~/.local/share/personal-skills/slack-tokens.json
  2. SLACK_TOKEN + SLACK_COOKIE env vars

Output JSON:
  { channel_id, channel_name, thread_ts, parent, replies[], participants[] }

Exit 0 = success, Exit 1 = auth error, Exit 2 = fetch error
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

TOKENS_FILE = Path.home() / ".local/share/personal-skills/slack-tokens.json"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def load_tokens() -> tuple[str, str]:
    """Returns (xoxc_token, xoxd_cookie)."""
    # File
    if TOKENS_FILE.exists():
        d = json.loads(TOKENS_FILE.read_text())
        t, c = d.get("token", ""), d.get("d", "")
        if t and c:
            return t, c

    # Env vars
    t = os.environ.get("SLACK_TOKEN", "")
    c = os.environ.get("SLACK_COOKIE", "")
    if t and c:
        return t, c

    print("ERROR: No Slack tokens found. Run /ps-slack-login first.", file=sys.stderr)
    sys.exit(1)


def slack_get(method: str, params: dict, token: str, cookie: str) -> dict:
    qs = urllib.parse.urlencode(params)
    url = f"https://slack.com/api/{method}?{qs}"
    req = urllib.request.Request(url, headers={
        "Authorization": token,
        "Cookie": f"d={cookie}",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} calling {method}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if not data.get("ok"):
        err = data.get("error", "unknown")
        if err in ("invalid_auth", "not_authed", "token_expired", "token_revoked"):
            print(f"ERROR: Slack auth failed ({err}). Run /ps-slack-login to refresh tokens.", file=sys.stderr)
            sys.exit(1)
        print(f"ERROR: Slack API error: {err}", file=sys.stderr)
        sys.exit(2)

    return data


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

def parse_slack_url(url: str) -> tuple[str, str]:
    """
    Returns (channel_id, thread_ts) from a Slack thread URL.
    URL formats:
      https://workspace.slack.com/archives/C1234567/p1234567890123456
      https://app.slack.com/client/T1234/C1234/thread/C1234-1234567890.123456
    """
    # Standard: /archives/CHANNEL/pTIMESTAMP
    m = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url)
    if m:
        channel = m.group(1)
        ts = f"{m.group(2)}.{m.group(3)}"
        return channel, ts

    # Thread permalink with dash format
    m = re.search(r"/thread/([A-Z0-9]+)-(\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    print(f"ERROR: Cannot parse Slack URL: {url}", file=sys.stderr)
    print("Expected format: https://workspace.slack.com/archives/C1234567/p1234567890123456", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def get_channel_name(channel_id: str, token: str, cookie: str) -> str:
    try:
        data = slack_get("conversations.info", {"channel": channel_id}, token, cookie)
        ch = data.get("channel", {})
        return ch.get("name") or ch.get("name_normalized") or channel_id
    except SystemExit:
        return channel_id


def resolve_users(user_ids: set, token: str, cookie: str) -> dict[str, str]:
    """Returns {user_id: display_name}."""
    names = {}
    for uid in user_ids:
        try:
            data = slack_get("users.info", {"user": uid}, token, cookie)
            u = data.get("user", {})
            profile = u.get("profile", {})
            name = (profile.get("display_name")
                    or profile.get("real_name")
                    or u.get("name")
                    or uid)
            names[uid] = name
        except SystemExit:
            names[uid] = uid
    return names


def format_message(msg: dict, user_names: dict) -> dict:
    uid  = msg.get("user", msg.get("bot_id", "unknown"))
    return {
        "author":    user_names.get(uid, uid),
        "ts":        msg.get("ts", ""),
        "text":      msg.get("text", ""),
        "reactions": [f":{r['name']}: ×{r['count']}" for r in msg.get("reactions", [])],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_slack_thread.py <slack-thread-url>", file=sys.stderr)
        sys.exit(1)

    token, cookie = load_tokens()
    channel_id, thread_ts = parse_slack_url(sys.argv[1])

    # Fetch all replies (paginated)
    replies = []
    cursor  = None
    while True:
        params = {"channel": channel_id, "ts": thread_ts, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = slack_get("conversations.replies", params, token, cookie)
        messages = data.get("messages", [])
        replies.extend(messages)
        meta = data.get("response_metadata", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            break

    if not replies:
        print("ERROR: No messages found for this thread.", file=sys.stderr)
        sys.exit(2)

    parent = replies[0]
    thread_replies = replies[1:]

    # Collect all user IDs and resolve names
    user_ids = set()
    for msg in replies:
        uid = msg.get("user") or msg.get("bot_id")
        if uid:
            user_ids.add(uid)

    user_names = resolve_users(user_ids, token, cookie)
    channel_name = get_channel_name(channel_id, token, cookie)

    print(json.dumps({
        "channel_id":   channel_id,
        "channel_name": channel_name,
        "thread_ts":    thread_ts,
        "url":          sys.argv[1],
        "parent":       format_message(parent, user_names),
        "replies":      [format_message(m, user_names) for m in thread_replies],
        "participants": list(user_names.values()),
        "reply_count":  len(thread_replies),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
