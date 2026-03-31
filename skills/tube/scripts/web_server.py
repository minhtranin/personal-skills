#!/usr/bin/env python3
"""
personal-skills web server — browse YouTube and Medium summary history.
Usage: python3 web_server.py [--port 5050]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import shutil

try:
    from flask import Flask, render_template_string, abort, request, redirect, url_for, send_file
except ImportError:
    print("ERROR: flask is not installed. Run: uv pip install flask", file=sys.stderr)
    sys.exit(2)

YOUTUBE_DIR = Path.home() / ".youtube-summary"
MEDIUM_DIR  = Path.home() / ".medium-summary"
JIRA_DIR    = Path.home() / ".jira-summary"
SLACK_DIR   = Path.home() / ".slack-summary"
GITHUB_DIR  = Path.home() / ".github-summary"
AMAZON_DIR  = Path.home() / ".amazon-summary"

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def load_index(data_dir: Path) -> list[dict]:
    f = data_dir / "index.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8"))


def load_entry(data_dir: Path, key: str) -> dict | None:
    f = data_dir / f"{key}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def load_github_index() -> list[dict]:
    """GitHub uses one .json file per repo (no index.json)."""
    if not GITHUB_DIR.exists():
        return []
    entries = []
    for f in sorted(GITHUB_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_slug"] = f.stem
            entries.append(data)
        except Exception:
            pass
    return entries


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

BASE_STYLE = """
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; background: #f5f5f5; }
  nav { display: flex; gap: 16px; margin-bottom: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 12px; }
  nav a { text-decoration: none; color: #555; font-size: 0.92rem; padding: 4px 0; }
  nav a.active { color: #2563eb; border-bottom: 2px solid #2563eb; font-weight: 600; }
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: #777; font-size: 0.88rem; margin-bottom: 1.8rem; }
  .card { background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; padding: 16px 20px; margin-bottom: 12px; text-decoration: none; display: block; color: inherit; transition: box-shadow .15s; }
  .card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.09); }
  .card h2 { margin: 0 0 5px; font-size: 1rem; }
  .card .meta { font-size: 0.8rem; color: #999; margin-bottom: 6px; }
  .card .badge { display: inline-block; font-size: 0.72rem; padding: 1px 7px; border-radius: 10px; margin-right: 6px; font-weight: 600; }
  .badge-yt    { background: #fee2e2; color: #b91c1c; }
  .badge-med   { background: #e0f2fe; color: #0369a1; }
  .badge-jira  { background: #ede9fe; color: #6d28d9; }
  .badge-slack  { background: #fef3c7; color: #92400e; }
  .badge-github { background: #f0fdf4; color: #15803d; }
  .badge-amazon { background: #fff7ed; color: #c2410c; }
  .card .snippet { font-size: 0.88rem; color: #555; line-height: 1.5; }
  .empty { text-align: center; color: #aaa; padding: 60px 0; font-size: 0.95rem; }
  .back { font-size: 0.88rem; margin-bottom: 1.5rem; }
  .back a { color: #2563eb; text-decoration: none; }
  .page-title { font-size: 1.4rem; margin-bottom: 4px; }
  .page-meta { font-size: 0.83rem; color: #999; margin-bottom: 1.5rem; }
  .page-meta a { color: #2563eb; }
  .section { background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; padding: 18px 22px; margin-bottom: 14px; }
  .section h3 { margin: 0 0 10px; font-size: 0.88rem; text-transform: uppercase; letter-spacing: .05em; color: #666; }
  .section p, .section pre { margin: 0; font-size: 0.93rem; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
  .fulltext { max-height: 420px; overflow-y: auto; background: #f8f8f8; border-radius: 6px; padding: 14px; font-size: 0.83rem; color: #444; white-space: pre-wrap; line-height: 1.6; }
  .btn-danger { display: inline-block; background: #dc2626; color: #fff; border: none; border-radius: 6px; padding: 6px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer; text-decoration: none; }
  .btn-danger:hover { background: #b91c1c; }
  .btn-secondary { display: inline-block; background: #e5e7eb; color: #374151; border: none; border-radius: 6px; padding: 6px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer; text-decoration: none; }
  .btn-secondary:hover { background: #d1d5db; }
  .tech-stack { margin: 0; }
  .tech-stack dt { font-weight: 700; color: #c2410c; font-size: 0.88rem; margin-top: 10px; }
  .tech-stack dd { margin: 2px 0 0 1.2em; font-size: 0.88rem; color: #374151; line-height: 1.55; }
  .summary-para { margin: 0 0 0.75em; font-size: 0.93rem; line-height: 1.7; }
  .summary-para:last-child { margin-bottom: 0; }
  .confirm-box { background: #fff; border: 1px solid #fca5a5; border-radius: 10px; padding: 28px 32px; max-width: 480px; margin: 60px auto; text-align: center; }
  .confirm-box h2 { margin: 0 0 8px; font-size: 1.15rem; color: #dc2626; }
  .confirm-box p { color: #555; font-size: 0.93rem; margin: 0 0 22px; line-height: 1.6; }
  .confirm-box .actions { display: flex; gap: 12px; justify-content: center; }
  .nav-right { margin-left: auto; }
</style>
"""

NAV_TEMPLATE = """
<nav>
  <a href="/" class="{{ 'active' if active == 'all' else '' }}">All ({{ total }})</a>
  <a href="/youtube" class="{{ 'active' if active == 'youtube' else '' }}">YouTube ({{ yt_count }})</a>
  <a href="/medium" class="{{ 'active' if active == 'medium' else '' }}">Medium ({{ med_count }})</a>
  <a href="/amazon" class="{{ 'active' if active == 'amazon' else '' }}">AWS Blog ({{ amazon_count }})</a>
  <a href="/github" class="{{ 'active' if active == 'github' else '' }}">GitHub ({{ gh_count }})</a>
  <a href="/jira" class="{{ 'active' if active == 'jira' else '' }}">Jira ({{ jira_count }})</a>
  <a href="/slack" class="{{ 'active' if active == 'slack' else '' }}">Slack ({{ slack_count }})</a>
  <span class="nav-right">
    <a href="/clear{% if active != 'all' %}/{{ active }}{% endif %}" class="btn-danger">Clear{% if active != 'all' %} {{ active|capitalize }}{% endif %} History</a>
  </span>
</nav>
"""

LIST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>personal-skills history</title>
  """ + BASE_STYLE + """
</head>
<body>
  """ + NAV_TEMPLATE + """
  <h1>{{ title }}</h1>
  <p class="subtitle">{{ items|length }} item(s)</p>
  {% if items %}
    {% for item in items %}
    <a class="card" href="{{ item._detail_url }}">
      {% if item._type == 'youtube' %}
        <span class="badge badge-yt">YouTube</span>
      {% elif item._type == 'medium' %}
        <span class="badge badge-med">Medium</span>
      {% elif item._type == 'slack' %}
        <span class="badge badge-slack">Slack</span>
      {% elif item._type == 'amazon' %}
        <span class="badge badge-amazon">AWS Blog</span>
      {% elif item._type == 'github' %}
        <span class="badge badge-github">GitHub</span>
      {% else %}
        <span class="badge badge-jira">Jira</span>
      {% endif %}
      <h2>{{ item.get('key', '') }}{% if item.get('key') %} — {% endif %}{{ item.get('full_name') or item.get('title') or item.get('issue_summary') or item.get('channel') or item.get('url') }}</h2>
      <div class="meta">
        {{ item.url }} &nbsp;·&nbsp; {{ item.date }}
        {% if item.get('author') %} &nbsp;·&nbsp; {{ item.author }}{% endif %}
        {% if item.get('category') %} &nbsp;·&nbsp; {{ item.category }}{% endif %}
        {% if item.get('language') %} &nbsp;·&nbsp; {{ item.language }}{% endif %}
        {% if item.get('stars') %} &nbsp;·&nbsp; ★ {{ item.stars }}{% endif %}
        {% if item.get('status') %} &nbsp;·&nbsp; {{ item.status }}{% endif %}
        {% if item.get('assignee') %} &nbsp;·&nbsp; {{ item.assignee }}{% endif %}
        {% if item.get('reply_count') %} &nbsp;·&nbsp; {{ item.reply_count }} replies{% endif %}
      </div>
      {% if item.snippet %}
      <div class="snippet">{{ item.snippet[:180] }}</div>
      {% endif %}
    </a>
    {% endfor %}
  {% else %}
    <div class="empty">No summaries yet.</div>
  {% endif %}
</body>
</html>"""

CONFIRM_CLEAR_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Clear history</title>
  """ + BASE_STYLE + """
</head>
<body>
  """ + NAV_TEMPLATE + """
  <div class="confirm-box">
    <h2>Clear {{ label }} history?</h2>
    <p>This will permanently delete <strong>{{ count }} item(s)</strong> from <code>{{ path }}</code>.<br>This cannot be undone.</p>
    <div class="actions">
      <form method="post" action="/clear/{{ scope }}/confirm">
        <button type="submit" class="btn-danger">Yes, delete all</button>
      </form>
      <a href="{{ back_url }}" class="btn-secondary">Cancel</a>
    </div>
  </div>
</body>
</html>"""

CLEARED_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cleared</title>
  """ + BASE_STYLE + """
</head>
<body>
  """ + NAV_TEMPLATE + """
  <div class="confirm-box" style="border-color:#bbf7d0">
    <h2 style="color:#16a34a">Cleared</h2>
    <p>{{ label }} history has been deleted.</p>
    <a href="{{ back_url }}" class="btn-secondary">Back</a>
  </div>
</body>
</html>"""

DETAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{ data.title or 'Summary' }}</title>
  """ + BASE_STYLE + """
</head>
<body>
  <div class="back"><a href="{{ back_url }}">&larr; Back</a></div>
  <div class="page-title">
    {% if data.get('key') %}<span style="color:#6d28d9">{{ data.key }}</span> — {% endif %}
    {{ data.get('full_name') or data.get('issue_summary') or data.get('title') or data.get('video_id') or data.get('slug') }}
  </div>
  <div class="page-meta">
    <a href="{{ data.url }}" target="_blank" rel="noopener">{{ data.url }}</a>
    &nbsp;·&nbsp; {{ data.date }}
    {% if data.get('author') %} &nbsp;·&nbsp; by {{ data.author }}{% endif %}
    {% if data.get('category') %} &nbsp;·&nbsp; <span style="color:#c2410c;font-weight:600">{{ data.category }}</span>{% endif %}
    {% if data.get('language') %} &nbsp;·&nbsp; {{ data.language }}{% endif %}
    {% if data.get('stars') %} &nbsp;·&nbsp; ★ {{ data.stars }}{% endif %}
    {% if data.get('status') %} &nbsp;·&nbsp; <strong>{{ data.status }}</strong>{% endif %}
    {% if data.get('assignee') %} &nbsp;·&nbsp; {{ data.assignee }}{% endif %}
    {% if data.get('priority') %} &nbsp;·&nbsp; {{ data.priority }}{% endif %}
  </div>

  {% if data.get('description') %}
  <div class="section">
    <h3>Description</h3>
    <p>{{ data.description }}</p>
  </div>
  {% endif %}

  {% if data.get('topics') %}
  <div class="section">
    <h3>Topics</h3>
    <p>{{ data.topics }}</p>
  </div>
  {% endif %}

  {% if data.summary %}
  <div class="section">
    <h3>Summary</h3>
    {% if source_type == 'amazon' %}
      {% for para in data.summary.split('\n\n') %}
        {% if para.strip() %}<p class="summary-para">{{ para.strip() }}</p>{% endif %}
      {% endfor %}
    {% else %}
      <p>{{ data.summary }}</p>
    {% endif %}
  </div>
  {% endif %}

  {% if data.key_points %}
  <div class="section">
    {% if source_type == 'amazon' %}
      <h3>Tech Stack</h3>
      {% set pts = data.key_points.replace('\r\n', '\n') %}
      {% if '|' in pts %}{% set items = pts.split('|') %}
      {% elif '\n' in pts %}{% set items = pts.split('\n') %}
      {% else %}{% set items = [pts] %}{% endif %}
      <dl class="tech-stack">
        {% for pt in items %}
          {% set pt = pt.strip() %}
          {% if pt %}
            {% if ' — ' in pt %}
              {% set parts = pt.split(' — ', 1) %}
              <dt>{{ parts[0] }}</dt><dd>{{ parts[1] }}</dd>
            {% else %}
              <dt>{{ pt }}</dt>
            {% endif %}
          {% endif %}
        {% endfor %}
      </dl>
    {% else %}
      <h3>Key Points</h3>
      {% set pts = data.key_points.replace('\r\n', '\n') %}
      {% if '|' in pts %}{% set items = pts.split('|') %}
      {% elif '\n' in pts %}{% set items = pts.split('\n') %}
      {% else %}{% set items = [pts] %}{% endif %}
      <ul style="margin:0;padding-left:1.4em;line-height:1.8;font-size:0.93rem;color:#333">
        {% for pt in items %}
          {% set pt = pt.strip().lstrip('-•* ') %}
          {% if pt %}<li>{{ pt }}</li>{% endif %}
        {% endfor %}
      </ul>
    {% endif %}
  </div>
  {% endif %}

  {% if data.get('diagram_png') %}
  <div class="section">
    <h3>Diagram</h3>
    <img src="/diagram?path={{ data.diagram_png | urlencode }}"
         style="max-width:100%;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.10);"
         alt="diagram" />
  </div>
  {% endif %}

  {% if data.transcript or data.text %}
  <div class="section">
    <h3>{{ 'Transcript' if data.transcript else 'Full Text' }}</h3>
    <div class="fulltext">{{ data.transcript or data.text }}</div>
  </div>
  {% endif %}
</body>
</html>"""

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Flask(__name__)


def all_items():
    yt     = [dict(e, _type="youtube", _detail_url=f"/youtube/{e['video_id']}") for e in load_index(YOUTUBE_DIR)]
    med    = [dict(e, _type="medium",  _detail_url=f"/medium/{e['slug']}")      for e in load_index(MEDIUM_DIR)]
    jira   = [dict(e, _type="jira",    _detail_url=f"/jira/{e['key']}")         for e in load_index(JIRA_DIR)]
    slack  = [dict(e, _type="slack",   _detail_url=f"/slack/{e['thread_id']}") for e in load_index(SLACK_DIR)]
    github = [dict(e, _type="github",  _detail_url=f"/github/{e['_slug']}")    for e in load_github_index()]
    amazon = [dict(e, _type="amazon",  _detail_url=f"/amazon/{e['slug']}")     for e in load_index(AMAZON_DIR)]
    combined = sorted(yt + med + jira + slack + github + amazon, key=lambda x: x.get("date", ""), reverse=True)
    return combined, len(yt), len(med), len(jira), len(slack), len(github), len(amazon)


def safe_key(key: str) -> str:
    if not all(c.isalnum() or c in "-_." for c in key):
        abort(400)
    return key


def nav_ctx(active, items, yt_count, med_count, jira_count, slack_count, gh_count=0, amazon_count=0):
    return dict(active=active, total=len(items),
                yt_count=yt_count, med_count=med_count, jira_count=jira_count,
                slack_count=slack_count, gh_count=gh_count, amazon_count=amazon_count)


@app.route("/")
def index():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    return render_template_string(LIST_TEMPLATE, title="All Summaries", items=items,
        **nav_ctx("all", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/youtube")
def youtube_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    yt_items = [i for i in items if i["_type"] == "youtube"]
    return render_template_string(LIST_TEMPLATE, title="YouTube Summaries", items=yt_items,
        **nav_ctx("youtube", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/medium")
def medium_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    med_items = [i for i in items if i["_type"] == "medium"]
    return render_template_string(LIST_TEMPLATE, title="Medium Summaries", items=med_items,
        **nav_ctx("medium", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/amazon")
def amazon_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    amazon_items = [i for i in items if i["_type"] == "amazon"]
    return render_template_string(LIST_TEMPLATE, title="AWS Blog Summaries", items=amazon_items,
        **nav_ctx("amazon", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/github")
def github_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    gh_items = [i for i in items if i["_type"] == "github"]
    return render_template_string(LIST_TEMPLATE, title="GitHub Summaries", items=gh_items,
        **nav_ctx("github", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/jira")
def jira_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    jira_items = [i for i in items if i["_type"] == "jira"]
    return render_template_string(LIST_TEMPLATE, title="Jira Summaries", items=jira_items,
        **nav_ctx("jira", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/slack")
def slack_list():
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    slack_items = [i for i in items if i["_type"] == "slack"]
    return render_template_string(LIST_TEMPLATE, title="Slack Summaries", items=slack_items,
        **nav_ctx("slack", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count))


@app.route("/youtube/<video_id>")
def youtube_detail(video_id: str):
    data = load_entry(YOUTUBE_DIR, safe_key(video_id))
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/youtube", source_type="")


@app.route("/medium/<slug>")
def medium_detail(slug: str):
    data = load_entry(MEDIUM_DIR, safe_key(slug))
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/medium", source_type="")


@app.route("/github/<path:slug>")
def github_detail(slug: str):
    safe = slug.replace("/", "__")
    if not all(c.isalnum() or c in "-_." for c in safe):
        abort(400)
    data = load_entry(GITHUB_DIR, safe)
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/github", source_type="")


@app.route("/jira/<key>")
def jira_detail(key: str):
    # Allow uppercase alphanumeric + dash for Jira keys (e.g. PROJ-123)
    if not re.match(r"^[A-Z0-9_]+-\d+$", key.upper()):
        abort(400)
    data = load_entry(JIRA_DIR, key.upper())
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/jira", source_type="")


@app.route("/slack/<thread_id>")
def slack_detail(thread_id: str):
    data = load_entry(SLACK_DIR, safe_key(thread_id))
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/slack", source_type="")


@app.route("/amazon/<slug>")
def amazon_detail(slug: str):
    data = load_entry(AMAZON_DIR, safe_key(slug))
    if data is None:
        abort(404)
    return render_template_string(DETAIL_TEMPLATE, data=data, back_url="/amazon", source_type="amazon")


# ---------------------------------------------------------------------------
# Diagram image route
# ---------------------------------------------------------------------------

@app.route("/diagram")
def serve_diagram():
    from flask import request as req
    path = req.args.get("path", "")
    p = Path(path)
    if not p.exists() or p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif"):
        abort(404)
    return send_file(str(p), mimetype="image/png")


# ---------------------------------------------------------------------------
# Slack token extraction server (separate port 5051)
# ---------------------------------------------------------------------------

def run_token_server():
    from flask import Flask, request, jsonify, render_template_string
    import json
    from pathlib import Path

    TOKENS_FILE = Path.home() / ".local/share/personal-skills/slack-tokens.json"
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)

    TOKEN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Slack Token Extractor — personal-skills</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; color: #222; }
    h1 { font-size: 22px; }
    .box { border: 1px solid #ddd; border-radius: 8px; padding: 24px; margin: 20px 0; background: #f9f9f9; }
    .box p { margin: 8px 0; font-size: 14px; }
    .token-preview { font-family: monospace; font-size: 12px; background: #eee; padding: 6px 10px; border-radius: 4px; word-break: break-all; margin: 6px 0; }
    .btn { background: #4a154b; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 16px; }
    .btn:hover { opacity: 0.9; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .status { margin-top: 16px; padding: 12px; border-radius: 6px; font-size: 14px; display: none; }
    .status.ok { background: #d4edda; color: #155724; display: block; }
    .status.err { background: #f8d7da; color: #721c24; display: block; }
    .note { font-size: 12px; color: #888; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>Slack Token Extractor</h1>
  <p>Extract your Slack session tokens for personal-skills.</p>

  <div class="box">
    <p><strong>1.</strong> Open <strong>app.slack.com</strong> in this browser and log in</p>
    <p><strong>2.</strong> Come back here and click <strong>Extract Tokens</strong></p>
    <p><strong>3.</strong> Tokens saved to <code>~/.local/share/personal-skills/slack-tokens.json</code></p>
  </div>

  <div class="box" id="preview-box" style="display:none">
    <p><strong>xoxc token:</strong></p>
    <div class="token-preview" id="xoxc-preview">—</div>
    <p><strong>xoxd cookie:</strong></p>
    <div class="token-preview" id="xoxd-preview">—</div>
  </div>

  <button class="btn" id="extract-btn" onclick="extractTokens()">Extract Tokens</button>

  <div class="status" id="status"></div>
  <p class="note">Tokens never leave your machine.</p>

  <script>
    function extractTokens() {
      const btn = document.getElementById("extract-btn");
      btn.disabled = true; btn.textContent = "Extracting...";

      let xoxc = null, xoxd = null;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith("xoxc_")) { xoxc = localStorage.getItem(key); break; }
      }
      const cookies = document.cookie.split(";");
      for (const c of cookies) {
        const [k, v] = c.trim().split("=");
        if (k === "d") xoxd = v;
      }

      if (!xoxc) {
        document.getElementById("status").className = "status err";
        document.getElementById("status").textContent = "xoxc token not found. Make sure you're logged into Slack in this browser, then reload and try again.";
        btn.disabled = false; btn.textContent = "Extract Tokens";
        return;
      }

      document.getElementById("preview-box").style.display = "block";
      document.getElementById("xoxc-preview").textContent = xoxc.slice(0, 40) + "...";
      document.getElementById("xoxd-preview").textContent = xoxd ? xoxd.slice(0, 40) + "..." : "(not found)";

      fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: xoxc, d: xoxd })
      })
      .then(r => r.json())
      .then(data => {
        const s = document.getElementById("status");
        if (data.ok) {
          s.className = "status ok"; s.textContent = "✓ Tokens saved! You can now use /ps:slack-summary.";
        } else {
          s.className = "status err"; s.textContent = "Error: " + (data.error || "unknown");
        }
        btn.disabled = false; btn.textContent = "Extract Tokens";
      })
      .catch(err => {
        const s = document.getElementById("status");
        s.className = "status err"; s.textContent = "Network error: " + err.message;
        btn.disabled = false; btn.textContent = "Extract Tokens";
      });
    }
  </script>
</body>
</html>"""

    token_app = Flask(__name__)

    @token_app.route("/")
    def token_page():
        return render_template_string(TOKEN_PAGE)

    @token_app.route("/save", methods=["POST"])
    def save_tokens():
        try:
            data = request.get_json()
            if not data or not data.get("token"):
                return jsonify({"ok": False, "error": "Missing token"}), 400
            tokens = {"token": data["token"], "d": data.get("d", "")}
            TOKENS_FILE.write_text(json.dumps(tokens, ensure_ascii=False, indent=2))
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    print("Slack token extraction server: http://localhost:5051")
    print("Open http://localhost:5051 in your browser while logged into Slack.")
    token_app.run(host="127.0.0.1", port=5051, debug=False, use_reloader=False)


# ---------------------------------------------------------------------------
# Clear routes
# ---------------------------------------------------------------------------

SCOPE_META = {
    "all":     ("All",      [YOUTUBE_DIR, MEDIUM_DIR, JIRA_DIR, SLACK_DIR, GITHUB_DIR, AMAZON_DIR], "/"),
    "youtube": ("YouTube",  [YOUTUBE_DIR], "/youtube"),
    "medium":  ("Medium",   [MEDIUM_DIR],  "/medium"),
    "amazon":  ("AWS Blog", [AMAZON_DIR],  "/amazon"),
    "github":  ("GitHub",   [GITHUB_DIR],  "/github"),
    "jira":    ("Jira",     [JIRA_DIR],    "/jira"),
    "slack":   ("Slack",    [SLACK_DIR],   "/slack"),
}


def _count_scope(dirs):
    total = 0
    for d in dirs:
        idx = d / "index.json"
        if idx.exists():
            total += len(json.loads(idx.read_text(encoding="utf-8")))
        elif d == GITHUB_DIR and d.exists():
            total += len(list(d.glob("*.json")))
    return total


def _clear_scope(dirs):
    for d in dirs:
        if d.exists():
            shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)


def _nav_ctx_empty():
    return dict(active="all", total=0, yt_count=0, med_count=0, jira_count=0, slack_count=0, gh_count=0, amazon_count=0)


@app.route("/clear", defaults={"scope": "all"})
@app.route("/clear/<scope>")
def clear_confirm(scope: str):
    if scope not in SCOPE_META:
        abort(404)
    label, dirs, back_url = SCOPE_META[scope]
    count = _count_scope(dirs)
    path_hint = ", ".join(str(d) for d in dirs)
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    ctx = nav_ctx("all", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count)
    return render_template_string(CONFIRM_CLEAR_TEMPLATE,
        label=label, count=count, path=path_hint, scope=scope, back_url=back_url, **ctx)


@app.route("/clear/<scope>/confirm", methods=["POST"])
def clear_execute(scope: str):
    if scope not in SCOPE_META:
        abort(404)
    label, dirs, back_url = SCOPE_META[scope]
    _clear_scope(dirs)
    items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count = all_items()
    ctx = nav_ctx("all", items, yt_count, med_count, jira_count, slack_count, gh_count, amazon_count)
    return render_template_string(CLEARED_TEMPLATE, label=label, back_url=back_url, **ctx)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="personal-skills history server")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--slack-tokens", action="store_true",
                        help="Start Slack token extraction server on port 5051")
    args = parser.parse_args()

    if args.slack_tokens:
        run_token_server()
        return

    print(f"Starting personal-skills server on http://localhost:{args.port}")
    print(f"YouTube history : {YOUTUBE_DIR}")
    print(f"Medium history  : {MEDIUM_DIR}")
    print("Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
