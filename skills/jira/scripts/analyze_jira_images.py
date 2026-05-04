#!/usr/bin/env python3
"""
Analyze image attachments from a Jira issue using Gemini Vision API.
Reads credentials from env: JIRA_EMAIL, JIRA_API_TOKEN, GEMINI_API_KEY

Usage: analyze_jira_images.py '<attachments_json>'

Input:  JSON array of {id, filename, mime_type, content_url}
Output: JSON array of {filename, description}
        Empty list [] if GEMINI_API_KEY is unset or no images provided.
Exit 0 = success, Exit 1 = error
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error


GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
PROMPT = (
    "This image is attached to a software development Jira issue. "
    "Describe what it shows in 2–3 concise sentences, focusing on "
    "anything relevant to understanding the issue (e.g. UI state, "
    "error messages, data, diagrams)."
)


def download_image(url: str, auth: str) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": auth})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def gemini_describe(image_bytes: bytes, mime_type: str, api_key: str) -> str:
    payload = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}},
                {"text": PROMPT},
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        f"{GEMINI_URL}?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())

    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()


def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[]")
        return

    if len(sys.argv) < 2:
        print("Usage: analyze_jira_images.py '<attachments_json>'", file=sys.stderr)
        sys.exit(1)

    try:
        attachments = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not attachments:
        print("[]")
        return

    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    if not email or not token:
        print("ERROR: JIRA_EMAIL and JIRA_API_TOKEN required to download attachments", file=sys.stderr)
        sys.exit(1)
    jira_auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()

    results = []
    for att in attachments:
        filename    = att.get("filename", "image")
        mime_type   = att.get("mime_type", "image/png")
        content_url = att.get("content_url", "")
        if not content_url:
            continue
        try:
            image_bytes = download_image(content_url, jira_auth)
            description = gemini_describe(image_bytes, mime_type, api_key)
            results.append({"filename": filename, "description": description})
        except Exception as e:
            print(f"WARN: skipping {filename}: {e}", file=sys.stderr)

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
