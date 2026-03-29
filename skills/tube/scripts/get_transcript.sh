#!/usr/bin/env bash
# Usage: get_transcript.sh <youtube-url>
# Downloads the transcript/subtitles from a YouTube video using yt-dlp.
# Outputs plain text to stdout.

set -e

URL="$1"
if [ -z "$URL" ]; then
  echo "Usage: get_transcript.sh <youtube-url>" >&2
  exit 1
fi

# Check yt-dlp
if ! command -v yt-dlp &>/dev/null; then
  echo "ERROR: yt-dlp is not installed." >&2
  echo "Run: pip install yt-dlp" >&2
  exit 2
fi

TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

# Try auto-generated English subtitles first, then manual English
yt-dlp \
  --skip-download \
  --write-auto-sub \
  --write-sub \
  --sub-lang "en.*" \
  --sub-format "vtt" \
  --convert-subs "vtt" \
  -o "$TMPDIR_WORK/video" \
  "$URL" 2>/dev/null || true

VTT_FILE=$(find "$TMPDIR_WORK" -name "*.vtt" | head -1)

if [ -z "$VTT_FILE" ]; then
  # Fallback: try getting description + info as context
  echo "[No subtitles found. Fetching video metadata instead...]"
  yt-dlp --skip-download --print "%(title)s\n%(description)s" "$URL" 2>/dev/null
  exit 0
fi

# Strip VTT formatting: remove timestamps, tags, and blank lines
python3 - "$VTT_FILE" <<'PYEOF'
import sys, re

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    content = f.read()

# Remove WEBVTT header
content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
# Remove cue identifiers (lines that are just numbers or timestamps)
content = re.sub(r'^\d+\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^\d{2}:\d{2}.*-->.+\n', '', content, flags=re.MULTILINE)
# Remove VTT tags like <c>, </c>, <00:00:00.000>
content = re.sub(r'<[^>]+>', '', content)
# Deduplicate adjacent identical lines (common in auto-subs)
lines = content.splitlines()
seen_prev = None
deduped = []
for line in lines:
    line = line.strip()
    if line and line != seen_prev:
        deduped.append(line)
        seen_prev = line
    elif not line:
        seen_prev = None

print(' '.join(deduped))
PYEOF
