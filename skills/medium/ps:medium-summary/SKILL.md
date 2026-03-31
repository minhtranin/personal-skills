---
name: ps:medium-summary
description: Fetch a Medium article via Freedium and summarize its main points. Use when the user runs /ps-medium-summary <url> or asks to summarize a Medium article.
argument-hint: <medium-url> [--refresh] [--diagram]
allowed-tools: [Bash, Read, Write]
---

# Medium Article Summarizer

**Arguments:** $ARGUMENTS

Parse the Medium URL. Flags: `--refresh` bypasses cache. `--diagram` auto-generates diagram without asking.

## Step 0 — Bootstrap + History check (one shot)

```bash
ls "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" 2>/dev/null \
  && python3 "$HOME/.local/share/personal-skills/scripts/medium/lookup_medium.py" "<URL>" 2>/dev/null \
  && echo "CACHED" || echo "FETCH"
```

- If scripts missing: run installer first: `curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash`
- If output contains JSON (exit 0 from lookup): show cached title, author, summary, key points, date. Say *"Cached from <date> — pass --refresh to re-fetch."* **Stop.**
- Otherwise: continue to fetch.

Skip history check if `--refresh` is present.

## Step 1 — Fetch article

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/fetch_medium.py" "<URL>" --max-chars 8000
```

Outputs JSON: `title`, `author`, `url`, `text`. If `text` is empty, stop with error.

Extract slug from the URL (last path segment, e.g. `nesti-got-tired-...-da01328b3345`).

## Step 2 — Summarize + Save in parallel

Produce immediately from the `text`:

1. **Summary** — 3–5 sentences: problem, approach, conclusion.
2. **Key Points** — 5–10 concrete bullets (include code/commands if relevant).

**Output to user right away**, then immediately save (do not wait for user response):

```bash
python3 "$HOME/.local/share/personal-skills/scripts/medium/save_medium.py" \
  --slug "<SLUG>" --url "<URL>" --title "<TITLE>" --author "<AUTHOR>" \
  --summary "<SUMMARY>" --key-points "<KEY_POINTS>" \
  --text "<TEXT[:4000]>"
```

End with: *"Saved. Browse history: `/ps:web`. Want a diagram? (y/n)"* — or skip asking if `--diagram` flag was passed.

## Step 3 — Diagram (if user says yes or --diagram flag)

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null && echo "ok" || echo "skip"
```

If `skip`: inform user and stop. If `ok`: generate concept map (title = central box, key points = leaf nodes grouped by theme). Write to `/tmp/medium_diagram.excalidraw`, render:

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py /tmp/medium_diagram.excalidraw --output /tmp/medium_diagram.png
```

Display PNG with Read tool. Update saved entry with `--diagram-png /tmp/medium_diagram.png`.
