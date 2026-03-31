---
name: ps:amazon-summary
description: Fetch and summarize an AWS/Amazon blog post, clearly highlighting technical stack, AWS services, and architecture patterns. Use when the user runs /ps:amazon-summary <url> or asks to summarize an AWS/Amazon blog post.
argument-hint: <aws-blog-url> [--refresh] [--diagram]
allowed-tools: [Bash, Read, Write]
---

# AWS / Amazon Blog Summarizer

**Arguments:** $ARGUMENTS

Parse the blog URL. Flags: `--refresh` bypasses cache. `--diagram` auto-generates diagram without asking.

## Step 0 — Bootstrap + History check (one shot)

```bash
ls "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" 2>/dev/null \
  && python3 "$HOME/.local/share/personal-skills/scripts/amazon/lookup_amazon.py" "<URL>" 2>/dev/null \
  && echo "CACHED" || echo "FETCH"
```

- If scripts missing: run installer first: `curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash`
- If the output is JSON (lookup succeeded): show cached title, author, category, summary, key points, date. Say *"Cached from <date> — pass --refresh to re-fetch."* **Stop.**
- Otherwise: continue.

Skip history check if `--refresh` is present.

## Step 1 — Fetch article (truncated for speed)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<URL>" --max-chars 8000
```

Outputs JSON: `title`, `author`, `category`, `url`, `text`. If `text` is empty, stop with error.

Extract slug from the URL (last path segment before trailing slash).

## Step 2 — Summarize + Save immediately

Produce from the `text`:

1. **Summary** — 3–5 sentences: problem/use case, solution approach, outcome. Name specific AWS services.

2. **Key Points** — 8–12 bullets in this order, prefixed with tags:
   - `[Tech]` — each AWS service or technology on its own bullet
   - `[Arch]` — how components connect
   - `[Impl]` — specific patterns or decisions
   - `[Result]` — measurable outcomes
   - `[Insight]` — non-obvious learnings

**Output to user immediately**, then save right away (do not wait):

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" --url "<URL>" --title "<TITLE>" --author "<AUTHOR>" \
  --category "<CATEGORY>" --summary "<SUMMARY>" --key-points "<KEY_POINTS>" \
  --text "<TEXT[:4000]>"
```

Present output as:

```
## <TITLE>
**Category:** <category> | **Author:** <author> | **Source:** [AWS Blog](<url>)

### Summary
<summary>

### Key Points
<bullet list>
```

End with: *"Saved. Browse history: `/ps:web`. Want a diagram? (y/n)"* — or skip asking if `--diagram` flag was passed.

## Step 3 — Diagram (if user says yes or --diagram flag)

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: inform and stop. If `ok`: generate architecture diagram — title as central box, AWS services as nodes grouped by layer (Interface / API / Compute / Intelligence / Observability / Storage). Write to `/tmp/amazon_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/amazon_diagram.excalidraw --output /tmp/amazon_diagram.png
```

Display PNG with the Read tool. Then update the entry:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" --url "<URL>" --title "<TITLE>" --author "<AUTHOR>" \
  --category "<CATEGORY>" --summary "<SUMMARY>" --key-points "<KEY_POINTS>" \
  --text "<TEXT[:4000]>" --diagram-png "/tmp/amazon_diagram.png"
```
