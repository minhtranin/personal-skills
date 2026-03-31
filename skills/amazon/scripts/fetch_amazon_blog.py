#!/usr/bin/env python3
"""
Fetch an AWS/Amazon blog post and extract clean plain text.
Usage: fetch_amazon_blog.py <url>

Outputs JSON:
  { "title": "...", "author": "...", "category": "...", "url": "...", "text": "..." }

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


class BlogExtractor(HTMLParser):
    """Extract title, author, and body text from AWS/Amazon blog HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = ""
        self.paragraphs = []

        self._skip = False
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "nav", "header", "footer", "aside"}

        self._in_title = False
        self._in_article = False
        self._article_depth = 0
        self._current_text = []

        # Article body selectors — AWS Blog uses several patterns
        self._article_classes = {
            "blog-post-content", "aws-blog-post", "blog-post__body",
            "blog-post-content-container", "entry-content", "post-content",
            "article-content", "lb-post-content",
        }

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in self._skip_tags:
            self._skip = True
            self._skip_depth = 1
            return
        if self._skip:
            self._skip_depth += 1
            return

        classes = set((attrs_dict.get("class") or "").split())

        if not self._in_article:
            if tag in ("div", "article", "section") and classes & self._article_classes:
                self._in_article = True
                self._article_depth = 1
                return
            # Fallback: <article> tag directly
            if tag == "article":
                self._in_article = True
                self._article_depth = 1
                return

        if self._in_article and tag in ("div", "article", "section"):
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

        if self._in_article and tag in ("div", "article", "section"):
            self._article_depth -= 1
            if self._article_depth == 0:
                self._in_article = False

        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "li", "pre", "blockquote", "td", "figcaption"}:
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
            # Strip site suffix like " | AWS Machine Learning Blog"
            self.title = re.sub(r"\s*[\|–\-]\s*(AWS|Amazon).*$", "", stripped).strip()
            return

        if self._in_article:
            self._current_text.append(stripped)


def extract_meta(html: str) -> dict:
    """Extract author and title from meta tags."""
    result = {}

    # OG title
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        result["og_title"] = m.group(1).strip()

    # Author from meta
    for pattern in [
        r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']article:author["\'][^>]+content=["\']([^"\']+)["\']',
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            result["author"] = m.group(1).strip()
            break

    # Author from common byline patterns in AWS blogs
    if "author" not in result:
        patterns = [
            r'class="[^"]*author[^"]*"[^>]*>([^<]{3,60})</[^>]+>',
            r'by\s+<[^>]+>([^<]{3,60})</[^>]+>',
            r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]{3,60})"',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.I)
            if m:
                candidate = m.group(1).strip()
                # Filter out generic strings
                if len(candidate) > 2 and "<" not in candidate:
                    result["author"] = candidate
                    break

    return result


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def extract_category(url: str) -> str:
    """Extract blog category from URL path, e.g. 'machine-learning'."""
    m = re.search(r"aws\.amazon\.com/blogs/([^/]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"amazon\.com/blogs/([^/]+)", url)
    if m:
        return m.group(1)
    return ""


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="AWS/Amazon blog URL")
    args = parser.parse_args()

    url = normalize_url(args.url)
    category = extract_category(url)

    try:
        html = fetch(url)
    except Exception as e:
        print(f"ERROR: Failed to fetch {url}: {e}", file=sys.stderr)
        sys.exit(1)

    extractor = BlogExtractor()
    extractor.feed(html)

    meta = extract_meta(html)
    title = extractor.title or meta.get("og_title", "")
    author = extractor.author or meta.get("author", "")
    body = "\n\n".join(extractor.paragraphs).strip()

    # Fallback: grab all visible text from <main> or body
    if not body:
        class FallbackExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.lines = []
                self._skip = False
            def handle_starttag(self, tag, attrs):
                if tag in {"script", "style", "nav", "header", "footer"}:
                    self._skip = True
            def handle_endtag(self, tag):
                if tag in {"script", "style", "nav", "header", "footer"}:
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
        "title": title,
        "author": author,
        "category": category,
        "url": url,
        "text": body,
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
