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
- If output is JSON (lookup succeeded): show cached result. Say *"Cached from <date> — pass --refresh to re-fetch."* **Stop.**
- Otherwise: continue.

Skip history check if `--refresh` is present.

## Step 1 — Fetch article

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<URL>" --max-chars 8000
```

Outputs JSON: `title`, `author`, `category`, `url`, `text`. If `text` is empty, stop with error.

Extract slug from URL (last path segment before trailing slash).

## Step 2 — Produce output + Save immediately

From the `text`, produce **three sections**:

### A. Summary (narrative)
4 short paragraphs, no headers, no bullets:
1. **Problem** — what pain/gap the company faced
2. **Solution** — what they built, which AWS services are central, how agents/components work together
3. **Build & decisions** — key technical choices (model selection, guardrails, frameworks, why specific services)
4. **Outcomes & lessons** — measurable results + non-obvious insights worth remembering

### B. Key Points
5–8 bullets capturing what's worth taking away from this article: decisions made, patterns used, results achieved, lessons learned. These are article-level insights, **not** tech descriptions.

Examples:
- Embedding domain expert knowledge into prompts had more impact than model selection alone
- Built in 16 weeks using a 30,000-hour cross-functional sprint — Bedrock significantly accelerated the build
- Treat Guardrails as non-negotiable from day one in regulated environments, not a retrofit

### C. Tech Stack
One entry per AWS service or tool, format: `Name — what it does in this project (one concrete sentence)`

Examples:
- `Amazon Bedrock — runs foundation models for all 5 agents; each agent uses a task-optimal model`
- `Bedrock Guardrails — enforces regulatory compliance across all agent interactions`

Separate entries with `|` (pipe).

### Output to user

```
## <TITLE>
**Category:** <category> | **Author:** <author> | **Source:** [AWS Blog](<url>)

### Summary
<4-paragraph narrative>

### Key Points
- <insight>
- <insight>
...

### Tech Stack
<Name — description>
...
```

Then: *"Saved. Browse history: `/ps:web`. Want a diagram? (y/n)"* — skip if `--diagram` flag.

### Save immediately (do not wait for diagram)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" --url "<URL>" --title "<TITLE>" --author "<AUTHOR>" \
  --category "<CATEGORY>" --summary "<4_PARAGRAPH_SUMMARY>" \
  --key-points "<KEY_POINTS_PIPE_SEPARATED>" \
  --tech-stack "<TECH_STACK_PIPE_SEPARATED>" \
  --text "<TEXT[:4000]>"
```

## Step 3 — Diagram (if user says yes or --diagram flag)

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: inform and stop.

If `ok`: generate a layered architecture diagram. Each tech/service box label format:
```
ServiceName
<short purpose phrase>
```
Example: `Amazon Bedrock\nFM provider\nper-agent model selection`

Group by layer: Interface → API → Compute/Agents → Intelligence → Observability → Storage

Write to `/tmp/amazon_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/amazon_diagram.excalidraw --output /tmp/amazon_diagram.png
```

Display PNG with Read tool. Update entry with `--diagram-png /tmp/amazon_diagram.png` (include all other args too).
