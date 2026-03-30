#!/usr/bin/env python3
"""
Fetch GitHub repository info via GitHub API.
Outputs JSON: { owner, repo, description, language, stars, forks,
                readme, topics, file_tree, recent_commits }
"""
import json, os, re, sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError

def gh_get(path, token=None):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ps:github-summary"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as r:
            return json.load(r)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise

def gh_raw(url):
    try:
        req = Request(url, headers={"User-Agent": "ps:github-summary"})
        with urlopen(req, timeout=15) as r:
            return r.read().decode(errors="replace")
    except Exception:
        return ""

def parse_github_url(url):
    url = url.strip().rstrip("/")
    m = re.search(r"github\.com[/:]([^/]+)/([^/\s?#]+)", url)
    if not m:
        return None, None
    return m.group(1), m.group(2).removesuffix(".git")

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_github_repo.py <github-url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    owner, repo = parse_github_url(url)
    if not owner:
        print(f"ERROR: Could not parse GitHub URL: {url}", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    # Repo metadata
    meta = gh_get(f"/repos/{owner}/{repo}", token)
    if not meta:
        print(f"ERROR: Repo {owner}/{repo} not found or not accessible", file=sys.stderr)
        sys.exit(1)

    # README
    readme_data = gh_get(f"/repos/{owner}/{repo}/readme", token)
    readme_text = ""
    if readme_data and readme_data.get("download_url"):
        readme_text = gh_raw(readme_data["download_url"])[:6000]

    # File tree (top-level + one level deep)
    tree_data = gh_get(f"/repos/{owner}/{repo}/git/trees/HEAD?recursive=0", token)
    file_tree = []
    if tree_data and tree_data.get("tree"):
        file_tree = [item["path"] for item in tree_data["tree"][:80]]

    # Recent commits
    commits_data = gh_get(f"/repos/{owner}/{repo}/commits?per_page=10", token)
    recent_commits = []
    if commits_data:
        for c in commits_data[:10]:
            msg = c.get("commit", {}).get("message", "").split("\n")[0]
            author = c.get("commit", {}).get("author", {}).get("name", "")
            date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
            recent_commits.append({"message": msg, "author": author, "date": date})

    # Languages
    langs_data = gh_get(f"/repos/{owner}/{repo}/languages", token)
    languages = list(langs_data.keys())[:6] if langs_data else []

    result = {
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "description": meta.get("description") or "",
        "homepage": meta.get("homepage") or "",
        "stars": meta.get("stargazers_count", 0),
        "forks": meta.get("forks_count", 0),
        "watchers": meta.get("watchers_count", 0),
        "open_issues": meta.get("open_issues_count", 0),
        "default_branch": meta.get("default_branch", "main"),
        "language": meta.get("language") or "",
        "languages": languages,
        "topics": meta.get("topics") or [],
        "license": (meta.get("license") or {}).get("spdx_id") or "",
        "created_at": (meta.get("created_at") or "")[:10],
        "updated_at": (meta.get("updated_at") or "")[:10],
        "readme": readme_text,
        "file_tree": file_tree,
        "recent_commits": recent_commits,
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
