#!/usr/bin/env python3
"""
Download image attachments from a Jira issue for model-side inspection.
Reads credentials from env: JIRA_EMAIL, JIRA_API_TOKEN

Usage: download_jira_images.py '<attachments_json>'

Input:  JSON array of {id, filename, mime_type, content_url}
Output: JSON array of {filename, mime_type, path}
        Empty list [] if no image attachments are provided.
Exit 0 = success, Exit 1 = input/config error
"""

import base64
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.request


EXT_BY_MIME = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def safe_filename(name: str, fallback: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    clean = clean.strip("._")
    return clean or fallback


def download_image(url: str, auth: str) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": auth})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def main():
    if len(sys.argv) < 2:
        print("Usage: download_jira_images.py '<attachments_json>'", file=sys.stderr)
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
    output_dir = Path(tempfile.mkdtemp(prefix="jira_images_"))
    results = []

    for index, attachment in enumerate(attachments, start=1):
        filename = attachment.get("filename") or f"image_{index}"
        mime_type = attachment.get("mime_type") or "image/png"
        content_url = attachment.get("content_url") or ""
        if not content_url:
            continue

        target_name = f"{index}_{safe_filename(filename, f'image_{index}')}"
        if "." not in Path(target_name).name:
            target_name += EXT_BY_MIME.get(mime_type, "")
        target_path = output_dir / target_name

        try:
            target_path.write_bytes(download_image(content_url, jira_auth))
        except Exception as e:
            print(f"WARN: skipping {filename}: {e}", file=sys.stderr)
            continue

        results.append({
            "filename": filename,
            "mime_type": mime_type,
            "path": str(target_path),
        })

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
