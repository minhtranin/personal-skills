#!/usr/bin/env python3
"""
Save Slack tokens provided by the user.
Usage: save_slack_tokens.py --token xoxc-... --cookie xoxd-...
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

TOKENS_FILE = Path.home() / ".local/share/personal-skills/slack-tokens.json"


def validate_token(token: str, cookie: str) -> tuple[bool, str]:
    """Test tokens against Slack API. Returns (ok, display_name_or_error)."""
    req = urllib.request.Request(
        "https://slack.com/api/auth.test",
        headers={
            "Authorization": f"{token}",
            "Cookie": f"d={cookie}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data.get("ok"):
                return True, f"{data.get('user', '')} @ {data.get('team', '')}"
            return False, data.get("error", "unknown error")
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token",  required=True, help="xoxc-... token")
    parser.add_argument("--cookie", required=True, help="xoxd-... cookie value")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()

    token  = args.token.strip()
    cookie = args.cookie.strip()

    # Strip "d=" prefix if user accidentally included it
    if cookie.startswith("d="):
        cookie = cookie[2:]

    if not token.startswith("xoxc-"):
        print(f"ERROR: Token should start with xoxc-, got: {token[:20]}", file=sys.stderr)
        sys.exit(1)

    if not cookie.startswith("xoxd-"):
        print(f"ERROR: Cookie should start with xoxd-, got: {cookie[:20]}", file=sys.stderr)
        sys.exit(1)

    if not args.skip_validation:
        print("Validating tokens against Slack API...")
        ok, info = validate_token(token, cookie)
        if not ok:
            print(f"ERROR: Token validation failed: {info}", file=sys.stderr)
            print("Check that you copied both values correctly.", file=sys.stderr)
            sys.exit(1)
        print(f"✓ Validated: {info}")

    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_FILE.write_text(json.dumps({"token": token, "d": cookie}, indent=2))
    TOKENS_FILE.chmod(0o600)
    print(f"✓ Saved to: {TOKENS_FILE}")


if __name__ == "__main__":
    main()
