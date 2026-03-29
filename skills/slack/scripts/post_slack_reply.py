#!/usr/bin/env python3
"""
Post a reply to a Slack thread.
Usage: post_slack_reply.py --url <slack-thread-url> --message <text>

Reads tokens from:
  ~/.local/share/personal-skills/slack-tokens.json

Exit 0 = success, Exit 1 = auth error, Exit 2 = post error
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

TOKENS_FILE = Path.home() / ".local/share/personal-skills/slack-tokens.json"


def load_tokens() -> tuple[str, str]:
    if TOKENS_FILE.exists():
        d = json.loads(TOKENS_FILE.read_text())
        t, c = d.get("token", ""), d.get("d", "")
        if t and c:
            return t, c
    t = os.environ.get("SLACK_TOKEN", "")
    c = os.environ.get("SLACK_COOKIE", "")
    if t and c:
        return t, c
    print("ERROR: No Slack tokens found. Run check_slack_tokens.sh first.", file=sys.stderr)
    sys.exit(1)


def parse_slack_url(url: str) -> tuple[str, str]:
    """Returns (channel_id, thread_ts)."""
    m = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url)
    if m:
        return m.group(1), f"{m.group(2)}.{m.group(3)}"
    m = re.search(r"/thread/([A-Z0-9]+)-(\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)
    print(f"ERROR: Cannot parse Slack URL: {url}", file=sys.stderr)
    sys.exit(2)


def workspace_domain_from_url(url: str) -> str:
    m = re.match(r"https?://([a-z0-9-]+\.slack\.com)", url)
    return m.group(1) if m else ""


def slack_post(method: str, params: dict, token: str, cookie: str, domain: str = "") -> dict:
    base = f"https://{domain}/api" if domain else "https://slack.com/api"
    url = f"{base}/{method}"

    boundary = "----WebKitFormBoundaryPersonalSkills"
    body_parts = []
    fields = dict(params)
    fields["token"] = token
    for key, value in fields.items():
        body_parts.append(
            f"------{boundary[6:]}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n"
        )
    body = ("".join(body_parts) + f"------{boundary[6:]}--\r\n").encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary=----{boundary[6:]}",
            "Cookie": f"d={cookie}",
            "User-Agent": "Mozilla/5.0",
        },
    )
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
            print(f"ERROR: Slack auth failed ({err}). Re-extract tokens with F12 DevTools.", file=sys.stderr)
            sys.exit(1)
        print(f"ERROR: Slack API error: {err}", file=sys.stderr)
        sys.exit(2)

    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",     required=True, help="Slack thread URL")
    parser.add_argument("--message", required=True, help="Reply text to post")
    args = parser.parse_args()

    token, cookie = load_tokens()
    channel_id, thread_ts = parse_slack_url(args.url)
    domain = workspace_domain_from_url(args.url)

    result = slack_post(
        "chat.postMessage",
        {
            "channel":   channel_id,
            "thread_ts": thread_ts,
            "text":      args.message,
        },
        token, cookie, domain,
    )

    ts = result.get("ts", "")
    print(f"Posted reply (ts={ts})")


if __name__ == "__main__":
    main()
