---
name: ps:amazon-summary
description: Fetch and summarize an AWS/Amazon blog post, clearly highlighting technical stack, AWS services, and architecture patterns. Use when the user runs /ps:amazon-summary <url> or asks to summarize an AWS/Amazon blog post.
argument-hint: <aws-blog-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# AWS / Amazon Blog Summarizer

The user wants to summarize an AWS or Amazon blog post.

**Arguments:** $ARGUMENTS

Parse the blog URL from the arguments. If `--refresh` is present, skip the history check.

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" 2>/dev/null
```

If not found, run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Stop if it fails.

## Step 1 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/lookup_amazon.py" "<URL>"
```

- **Exit 0 (found):** Show cached title, author, category, summary, key points, and date. Ask: *"Already summarized on <date>. Use cached result? Pass --refresh to re-fetch."* Stop here if user confirms or doesn't respond.
- **Exit 1 (not found):** Continue.

## Step 2 — Fetch article

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<URL>"
```

This outputs JSON with fields: `title`, `author`, `category`, `url`, `text`.

Parse the JSON. If `text` is empty or fetch failed, tell the user and stop.

Extract the slug from the URL (last path segment before trailing slash).

## Step 3 — Summarize with technical focus

Using the article `text`, produce:

1. **Summary** — 3–5 sentences covering: the problem/use case, the solution approach, and the outcome. Mention specific AWS services and technologies by name.

2. **Key Points** — bulleted list of 8–12 concrete takeaways. Structure them in this order:
   - **[Tech Stack]** AWS services and technologies used (e.g., Amazon Bedrock, Lambda, SageMaker, CDK) — list each on its own bullet
   - **[Architecture]** How the components connect and interact
   - **[Implementation]** Specific steps, patterns, or design decisions
   - **[Results/Metrics]** Measurable outcomes (speed, cost, accuracy, time-to-build)
   - **[Key Insights]** Non-obvious learnings or best practices

   Prefix technical bullets with `[Tech]`, `[Arch]`, `[Impl]`, `[Result]`, or `[Insight]` tags.

## Step 4 — Output to user immediately

Present in clean markdown:

```
## <TITLE>

**Category:** <category> | **Author:** <author> | **Source:** [AWS Blog](<url>)

### Summary
<summary>

### Key Points
<key_points as bullet list>
```

Then on a new line: *"Browse all history with `/ps:web`. Want a diagram for this? (y/n)"*

## Step 5 — Save to history (run immediately, do not wait for diagram)

Extract slug from the URL (last path segment, e.g. `how-lendi-revamped-...`).

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" \
  --url "<URL>" \
  --title "<TITLE>" \
  --author "<AUTHOR>" \
  --category "<CATEGORY>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --text "<ARTICLE_TEXT_FIRST_4000_CHARS>"
```

## Step 6 — Diagram (only if user says yes)

If the user replies `y` or `yes`:

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: tell the user excalidraw deps are not installed and stop.

If `ok`: generate an architecture diagram — blog title as central box, AWS services as connected nodes, grouped by layer (Data / Compute / Orchestration / Interface). Write to `/tmp/amazon_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/amazon_diagram.excalidraw --output /tmp/amazon_diagram.png
```

Display PNG with the Read tool. Then update the saved entry with the diagram path:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" \
  --url "<URL>" \
  --title "<TITLE>" \
  --author "<AUTHOR>" \
  --category "<CATEGORY>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --text "<ARTICLE_TEXT_FIRST_4000_CHARS>" \
  --diagram-png "/tmp/amazon_diagram.png"
```
