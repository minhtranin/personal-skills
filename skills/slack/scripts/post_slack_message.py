#!/usr/bin/env python3
"""
Post a new message to any Slack channel or DM.
Usage:
  post_slack_message.py --to <channel-id-or-url-or-name> --message <text>

Examples:
  post_slack_message.py --to C1234567 --message "hello team"
  post_slack_message.py --to "#general" --message "hello team"
  post_slack_message.py --to https://grapplefund.slack.com/archives/D01T8UKQ7QA --message "hi"

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


def resolve_channel(target: str) -> tuple[str, str]:
    """
    Returns (channel_id, workspace_domain) from various input formats:
      - https://grapplefund.slack.com/archives/C1234567/...  → C1234567
      - https://grapplefund.slack.com/archives/C1234567      → C1234567
      - C1234567 or D1234567                                  → as-is
      - #general or general                                   → needs lookup (returned as-is, API resolves)
    """
    # Full Slack URL — extract channel ID and domain
    m = re.match(r"https?://([a-z0-9-]+\.slack\.com)/archives/([A-Z0-9]+)", target)
    if m:
        return m.group(2), m.group(1)

    # Already a channel/DM ID
    if re.match(r"^[A-Z0-9]{9,11}$", target):
        return target, ""

    # #channel-name or channel-name — pass as-is, Slack API accepts channel names too
    name = target.lstrip("#")
    return name, ""


def workspace_domain_from_token(token: str) -> str:
    """Extract workspace domain hint from xoxc token (team ID only, not domain)."""
    return ""


def slack_post_api(method: str, params: dict, token: str, cookie: str, domain: str = "") -> dict:
    base = f"https://{domain}/api" if domain else "https://slack.com/api"
    url  = f"{base}/{method}"

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
    parser.add_argument("--to",      required=True,
                        help="Channel ID, channel name (#general), or Slack channel URL")
    parser.add_argument("--message", required=True, help="Message text to post")
    args = parser.parse_args()

    token, cookie = load_tokens()
    channel_id, domain = resolve_channel(args.to)

    result = slack_post_api(
        "chat.postMessage",
        {
            "channel": channel_id,
            "text":    args.message,
        },
        token, cookie, domain,
    )

    ts      = result.get("ts", "")
    channel = result.get("channel", channel_id)
    print(f"Posted to {channel} (ts={ts})")


if __name__ == "__main__":
    main()
