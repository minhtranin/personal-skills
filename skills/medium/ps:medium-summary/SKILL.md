---
name: ps:medium-summary
description: Fetch a Medium article via Freedium and summarize its main points. Use when the user runs /ps-medium-summary <url> or asks to summarize a Medium article.
argument-hint: <medium-url> [--refresh]
allowed-tools: [Bash, Read, Write]
---

# Medium Article Summarizer

The user wants to summarize a Medium article.

**Arguments:** $ARGUMENTS

Parse the Medium URL from the arguments. If `--refresh` is present, skip the history check.

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" 2>/dev/null
```

If not found, run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Stop if it fails.

## Step 1 — Check history (skip if --refresh)

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/lookup_medium.py" "<URL>"
```

- **Exit 0 (found):** Show cached title, author, summary, key points, and date. Ask: *"Already summarized on <date>. Use cached result? Pass --refresh to re-fetch."* Stop here if user confirms or doesn't respond.
- **Exit 1 (not found):** Continue.

## Step 2 — Fetch article via Freedium

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" "<URL>"
```

This outputs JSON with fields: `title`, `author`, `url`, `text`.

Parse the JSON. If `text` is empty or the fetch failed, tell the user and stop.

## Step 3 — Summarize

Using the article `text`, produce:

1. **Summary** — 3–5 sentence overview: the problem being solved, the approach, and the conclusion.
2. **Key Points** — bulleted list of 5–10 concrete takeaways (include code snippets or commands if relevant).

## Step 4 — Output to user immediately

Present the title, author, summary and key points in clean markdown.

Then on a new line: *"Browse all history with `/ps:web`. Want a diagram for this? (y/n)"*

## Step 5 — Save to history (run immediately, do not wait for diagram)

Extract slug from the URL (the last path segment, e.g. `nesti-got-tired-...-da01328b3345`).

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<SLUG>" \
  --url "<URL>" \
  --title "<TITLE>" \
  --author "<AUTHOR>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --text "<ARTICLE_TEXT_FIRST_4000_CHARS>"
```

## Step 6 — Diagram (only if user says yes)

If the user replies `y` or `yes`:

```bash
python3 -c "import playwright" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: tell the user playwright is not installed and stop.

If `ok`: generate a concept map — article title as central box, key points as connected leaf nodes grouped by theme. Write to `/tmp/medium_diagram.excalidraw`, render:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/tube/excalidraw/render_excalidraw.py" \
  /tmp/medium_diagram.excalidraw --output /tmp/medium_diagram.png
```

Display PNG with the Read tool. Then update the saved entry with the diagram path:

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<SLUG>" \
  --url "<URL>" \
  --title "<TITLE>" \
  --author "<AUTHOR>" \
  --summary "<SUMMARY_TEXT>" \
  --key-points "<KEY_POINTS_TEXT>" \
  --text "<ARTICLE_TEXT_FIRST_4000_CHARS>" \
  --diagram-png "/tmp/medium_diagram.png"
```
