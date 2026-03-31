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


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def extract_category(url: str) -> str:
    """Extract blog category from URL path, e.g. 'machine-learning'."""
    m = re.search(r"(?:aws\.)?amazon\.com/blogs/([^/]+)", url)
    return m.group(1) if m else ""


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


def strip_tags(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_article_body(html: str) -> str:
    """Extract article body using known AWS blog section selectors."""
    # AWS blog: <section class="blog-post-content ...">
    # Also try: <div class="blog-post-content ...">
    # Also try: property="articleBody"
    patterns = [
        r'<(?:section|div)[^>]*\bclass="[^"]*blog-post-content[^"]*"[^>]*>(.*?)</(?:section|div)>',
        r'<(?:section|div|article)[^>]*\bproperty="articleBody"[^>]*>(.*?)</(?:section|div|article)>',
        r'<(?:div|article)[^>]*\bclass="[^"]*entry-content[^"]*"[^>]*>(.*?)</(?:div|article)>',
        r'<article[^>]*>(.*?)</article>',
    ]
    for pat in patterns:
        # Use DOTALL but limit greediness via a large chunk (AWS blog content < 200KB)
        m = re.search(pat, html, re.DOTALL | re.I)
        if m:
            body = strip_tags(m.group(1))
            if len(body) > 200:
                return body
    return ""


def extract_title(html: str) -> str:
    """Extract page title from OG meta or <title> tag."""
    # OG title is cleanest
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html, re.I)
    if m:
        return m.group(1).strip()
    # <title> tag — strip site suffix
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        title = m.group(1).strip()
        title = re.sub(r"\s*[\|–\-]\s*(AWS|Amazon|Artificial Intelligence).*$", "", title, flags=re.I)
        return title.strip()
    return ""


def extract_author(html: str) -> str:
    """Extract author from structured data or byline patterns."""
    # Schema.org Person name
    m = re.search(r'property=["\']name["\'][^>]*>\s*([^<]{3,80})\s*</span>', html, re.I)
    if m:
        candidate = m.group(1).strip()
        if candidate and "<" not in candidate:
            return candidate
    # Byline: "by <span>Name</span>"
    m = re.search(r'\bby\s+<[^>]+>\s*([^<]{3,80})\s*</[^>]+>', html, re.I)
    if m:
        candidate = m.group(1).strip()
        if candidate and "<" not in candidate:
            return candidate
    # Meta author
    m = re.search(r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return m.group(1).strip()
    # JSON-LD "author" field
    m = re.search(r'"author"\s*:\s*\{\s*"name"\s*:\s*"([^"]{3,80})"', html)
    if m:
        return m.group(1).strip()
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="AWS/Amazon blog URL")
    parser.add_argument("--max-chars", type=int, default=8000,
                        help="Truncate article text to this length (default 8000)")
    args = parser.parse_args()

    url = normalize_url(args.url)
    category = extract_category(url)

    try:
        html = fetch(url)
    except Exception as e:
        print(f"ERROR: Failed to fetch {url}: {e}", file=sys.stderr)
        sys.exit(1)

    body = extract_article_body(html)
    title = extract_title(html)
    author = extract_author(html)

    result = {
        "title": title,
        "author": author,
        "category": category,
        "url": url,
        "text": body[:args.max_chars],
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
