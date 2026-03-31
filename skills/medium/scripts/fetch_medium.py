#!/usr/bin/env python3
"""
Fetch a Medium article via Freedium mirror and extract clean plain text.
Usage: fetch_medium.py <medium-url> [--freedium-host freedium-mirror.cfd]

Outputs JSON:
  { "title": "...", "author": "...", "text": "...", "url": "..." }

Exit codes:
  0  success
  1  fetch/parse error
"""

import argparse
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser


FREEDIUM_HOST = "freedium-mirror.cfd"
FREEDIUM_MIRRORS = [
    "freedium-mirror.cfd",
    "freedium.cfd",
]


class ArticleExtractor(HTMLParser):
    """Extract title, author, and body text from Freedium HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = ""
        self.paragraphs = []

        self._skip = False
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "nav", "header", "footer", "aside"}

        self._in_title = False
        self._current_text = []

        # Freedium wraps article body in <div class="... main-content ...">
        self._in_article = False
        self._article_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Skip noise tags entirely
        if tag in self._skip_tags:
            self._skip = True
            self._skip_depth = 1
            return
        if self._skip:
            self._skip_depth += 1
            return

        # Detect article body — Freedium uses class containing "main-content"
        classes = attrs_dict.get("class", "")
        if not self._in_article and tag == "div" and "main-content" in classes:
            self._in_article = True
            self._article_depth = 1
            return
        if self._in_article and tag == "div":
            self._article_depth += 1

        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if self._skip:
            self._skip_depth -= 1
            if self._skip_depth == 0:
                self._skip = False
            return

        if tag == "title":
            self._in_title = False

        if self._in_article and tag == "div":
            self._article_depth -= 1
            if self._article_depth == 0:
                self._in_article = False

        # Flush accumulated text on block-level end tags
        if tag in {"p", "h1", "h2", "h3", "h4", "li", "pre", "blockquote", "td"}:
            text = " ".join(self._current_text).strip()
            if text:
                self.paragraphs.append(text)
            self._current_text = []

    def handle_data(self, data):
        if self._skip:
            return
        stripped = data.strip()
        if not stripped:
            return

        if self._in_title and not self.title:
            # Strip " - Freedium" suffix
            self.title = re.sub(r"\s*[-|]\s*Freedium\s*$", "", stripped).strip()
            return

        if self._in_article:
            self._current_text.append(stripped)


def normalize_url(url: str) -> str:
    """Ensure URL has https:// scheme."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def freedium_url(medium_url: str, host: str) -> str:
    return f"https://{host}/{medium_url}"


def fetch(url: str) -> str:
    # Use https to avoid 308 redirects from http
    if url.startswith("http://"):
        url = "https://" + url[7:]
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; personal-skills/1.0)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_author(html: str) -> str:
    """Best-effort author extraction from meta or byline."""
    # <meta name="author" content="...">
    m = re.search(r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return m.group(1).strip()
    # Freedium byline pattern: "by AuthorName"
    m = re.search(r'by\s+<[^>]+>([^<]{3,60})</[^>]+>', html)
    if m:
        return m.group(1).strip()
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Medium article URL")
    parser.add_argument("--freedium-host", default=None,
                        help="Freedium mirror host (tries mirrors in order if not set)")
    parser.add_argument("--max-chars", type=int, default=8000,
                        help="Truncate article text to this length (default 8000)")
    args = parser.parse_args()

    medium_url = normalize_url(args.url)

    # Try mirrors in order — use first that returns body text
    mirrors = [args.freedium_host] if args.freedium_host else FREEDIUM_MIRRORS
    html = None
    last_err = None
    for mirror in mirrors:
        free_url = freedium_url(medium_url, mirror)
        try:
            html = fetch(free_url)
            break
        except Exception as e:
            last_err = e
            print(f"WARN: mirror {mirror} failed: {e}", file=sys.stderr)

    if html is None:
        print(f"ERROR: All mirrors failed. Last error: {last_err}", file=sys.stderr)
        sys.exit(1)

    extractor = ArticleExtractor()
    extractor.feed(html)

    author = extractor.author or extract_author(html)
    body = "\n\n".join(extractor.paragraphs).strip()

    if not body:
        # Fallback: grab all visible text
        class FallbackExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.lines = []
                self._skip = False
            def handle_starttag(self, tag, attrs):
                if tag in {"script","style","nav","header","footer"}:
                    self._skip = True
            def handle_endtag(self, tag):
                if tag in {"script","style","nav","header","footer"}:
                    self._skip = False
            def handle_data(self, data):
                if not self._skip:
                    t = data.strip()
                    if t:
                        self.lines.append(t)
        fb = FallbackExtractor()
        fb.feed(html)
        body = "\n".join(fb.lines)

    result = {
        "title": extractor.title,
        "author": author,
        "url": medium_url,
        "freedium_url": free_url,
        "text": body[:args.max_chars],
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
