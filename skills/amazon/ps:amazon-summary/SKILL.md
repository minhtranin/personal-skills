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
- If the output is JSON (lookup succeeded): show cached title, author, category, summary, tech stack, date. Say *"Cached from <date> — pass --refresh to re-fetch."* **Stop.**
- Otherwise: continue.

Skip history check if `--refresh` is present.

## Step 1 — Fetch article (truncated for speed)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/fetch_amazon_blog.py" "<URL>" --max-chars 8000
```

Outputs JSON: `title`, `author`, `category`, `url`, `text`. If `text` is empty, stop with error.

Extract slug from the URL (last path segment before trailing slash).

## Step 2 — Produce output + Save immediately

### Summary (narrative — no bullet Key Points)

Write **4 short paragraphs**, each a few sentences. Weave insights naturally into the story:

1. **Problem** — what pain/gap the company faced and why it mattered
2. **Solution** — what they built, which AWS services are central to it, and how agents/components work together
3. **Build & decisions** — key technical or design choices (e.g. model selection strategy, guardrails, why EKS, how MCP connects things)
4. **Outcomes & lessons** — measurable results + 1-2 non-obvious insights worth remembering

Do NOT use bullet points or headers inside the summary. Write it as flowing prose.

### Tech Stack (replaces Key Points)

For each AWS service or tool used, write one entry in this exact format:
```
TechName — what it does in this specific project (one concrete sentence)
```

Examples:
- `Amazon Bedrock — runs foundation models for all 5 specialized agents; each agent uses a task-optimal model rather than always the most powerful one`
- `Bedrock Guardrails — enforces regulatory and content compliance across all agent interactions, non-negotiable in Australian financial services`
- `Amazon EKS — hosts and auto-scales the 5 AI agents under variable customer demand`

Separate entries with `|` (pipe) for storage.

### Output format

```
## <TITLE>
**Category:** <category> | **Author:** <author> | **Source:** [AWS Blog](<url>)

### Summary
<4-paragraph narrative>

### Tech Stack
<Name — description>
<Name — description>
...
```

Then: *"Saved. Browse history: `/ps:web`. Want a diagram? (y/n)"* — skip asking if `--diagram` flag was passed.

### Save immediately (do not wait for diagram)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/amazon/save_amazon_summary.py" \
  --slug "<SLUG>" --url "<URL>" --title "<TITLE>" --author "<AUTHOR>" \
  --category "<CATEGORY>" --summary "<4_PARAGRAPH_SUMMARY>" \
  --key-points "<TECH_STACK_PIPE_SEPARATED>" \
  --text "<TEXT[:4000]>"
```

## Step 3 — Diagram (if user says yes or --diagram flag)

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: inform and stop.

If `ok`: generate a layered architecture diagram. **Each tech/service box must include a short purpose line** — format each node label as:
```
ServiceName
<one short phrase: what it does>
```
Example node: `Amazon Bedrock\nFM provider\nper-agent model selection`

Group nodes by layer: Interface → API → Compute/Agents → Intelligence → Observability → Storage

Write to `/tmp/amazon_diagram.excalidraw`, render:

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
