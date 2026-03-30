---
name: ps:excalidraw
description: Generate an Excalidraw diagram from a description and render it to PNG. Use when the user runs /ps-excalidraw <description> or asks to create a diagram/chart/flowchart/architecture diagram.
argument-hint: <description>
allowed-tools: [Bash, Read, Write, Edit]
---

# Excalidraw Diagram Creator

Generate `.excalidraw` JSON files that **argue visually**, not just display information.

**Arguments:** $ARGUMENTS

---

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh" 2>/dev/null
```

If not found, run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Stop if it fails.

Then check dependencies:

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/check_deps.sh"
```

Stop if it fails.

**Scripts path:** `$HOME/.local/share/personal-skills/scripts/excalidraw/`
**References:** `$HOME/.local/share/personal-skills/scripts/excalidraw/references/`

---

## Customization

**All colors and brand-specific styles live in one file:** `references/color-palette.md`. Read it before generating any diagram and use it as the single source of truth for all color choices — shape fills, strokes, text colors, evidence artifact backgrounds, everything.

Read the references now:
```bash
cat "$HOME/.local/share/personal-skills/scripts/excalidraw/references/color-palette.md"
cat "$HOME/.local/share/personal-skills/scripts/excalidraw/references/element-templates.md"
```

---

## Core Philosophy

**Diagrams should ARGUE, not DISPLAY.**

A diagram isn't formatted text. It's a visual argument that shows relationships, causality, and flow that words alone can't express. The shape should BE the meaning.

**The Isomorphism Test**: If you removed all text, would the structure alone communicate the concept? If not, redesign.

**The Education Test**: Could someone learn something concrete from this diagram, or does it just label boxes? A good diagram teaches—it shows actual formats, real event names, concrete examples.

---

## Depth Assessment (Do This First)

Before designing, determine what level of detail this diagram needs:

### Simple/Conceptual Diagrams
Use abstract shapes when:
- Explaining a mental model or philosophy
- The audience doesn't need technical specifics
- The concept IS the abstraction (e.g., "separation of concerns")

### Comprehensive/Technical Diagrams
Use concrete examples when:
- Diagramming a real system, protocol, or architecture
- The diagram will be used to teach or explain (e.g., YouTube video)
- The audience needs to understand what things actually look like
- You're showing how multiple technologies integrate

**For technical diagrams, you MUST include evidence artifacts** (see below).

---

## Research Mandate (For Technical Diagrams)

**Before drawing anything technical, research the actual specifications.**

If you're diagramming a protocol, API, or framework:
1. Look up the actual JSON/data formats
2. Find the real event names, method names, or API endpoints
3. Understand how the pieces actually connect
4. Use real terminology, not generic placeholders

---

## Evidence Artifacts

Evidence artifacts are concrete examples that prove your diagram is accurate and help viewers learn. Include them in technical diagrams.

| Artifact Type | When to Use | How to Render |
|---------------|-------------|---------------|
| **Code snippets** | APIs, integrations, implementation details | Dark rectangle + syntax-colored text |
| **Data/JSON examples** | Data formats, schemas, payloads | Dark rectangle + colored text |
| **Event/step sequences** | Protocols, workflows, lifecycles | Timeline pattern (line + dots + labels) |
| **UI mockups** | Showing actual output/results | Nested rectangles mimicking real UI |
| **Real input content** | Showing what goes IN to a system | Rectangle with sample content visible |
| **API/method names** | Real function calls, endpoints | Use actual names from docs, not placeholders |

---

## Multi-Zoom Architecture

Comprehensive diagrams operate at multiple zoom levels simultaneously:

### Level 1: Summary Flow
A simplified overview showing the full pipeline or process at a glance.

### Level 2: Section Boundaries
Labeled regions that group related components.

### Level 3: Detail Inside Sections
Evidence artifacts, code snippets, and concrete examples within each section.

---

## Design Process (Do This BEFORE Generating JSON)

### Step 0: Assess Depth Required
- **Simple/Conceptual**: Abstract shapes, labels, relationships
- **Comprehensive/Technical**: Concrete examples, code snippets, real data

### Step 1: Understand Deeply
- What does each concept **DO**?
- What relationships exist between concepts?
- What's the core transformation or flow?

### Step 2: Map Concepts to Patterns

| If the concept... | Use this pattern |
|-------------------|------------------|
| Spawns multiple outputs | **Fan-out** |
| Combines inputs into one | **Convergence** |
| Has hierarchy/nesting | **Tree** |
| Is a sequence of steps | **Timeline** |
| Loops or improves continuously | **Spiral/Cycle** |
| Is an abstract state or context | **Cloud** |
| Transforms input to output | **Assembly line** |
| Compares two things | **Side-by-side** |
| Separates into phases | **Gap/Break** |

### Step 3: Ensure Variety
Each major concept must use a different visual pattern.

### Step 4: Sketch the Flow
Mentally trace how the eye moves through the diagram.

### Step 5: Generate JSON
Build the JSON one section at a time for large diagrams.

### Step 6: Render & Validate (MANDATORY)
Run the render-view-fix loop.

---

## Large / Comprehensive Diagram Strategy

**For comprehensive or technical diagrams, build the JSON one section at a time.**

- Create the base file with the JSON wrapper and first section
- Add one section per edit
- Use descriptive string IDs (e.g., `"trigger_rect"`, `"arrow_fan_left"`)
- Namespace seeds by section (section 1 uses 100xxx, section 2 uses 200xxx)
- Update cross-section bindings as you go

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

---

## Shape Meaning

| Concept Type | Shape |
|--------------|-------|
| Labels, descriptions, details | **none** (free-floating text) |
| Section titles, annotations | **none** (free-floating text) |
| Markers on a timeline | small `ellipse` (10-20px) |
| Start, trigger, input | `ellipse` |
| End, output, result | `ellipse` |
| Decision, condition | `diamond` |
| Process, action, step | `rectangle` |
| Abstract state, context | overlapping `ellipse` |

**Rule**: Default to no container. Add shapes only when they carry meaning. Aim for <30% of text elements inside containers.

---

## Modern Aesthetics

- `roughness: 0` — Clean, crisp edges (default for professional diagrams)
- `opacity: 100` for all elements
- `fontFamily: 3`, `fontSize: 16`

---

## Render & Validate (MANDATORY)

After generating or editing the Excalidraw JSON, render it to PNG and view it — in a loop until it's right.

### How to Render

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv run python render_excalidraw.py <path-to-file.excalidraw>
```

Then use the **Read tool** on the PNG to view it.

### The Loop

1. **Render & View** — Run the render script, then Read the PNG.
2. **Audit against your original vision** — Does the visual structure match what you designed?
3. **Check for visual defects** — Text clipped, overlapping, arrows misaligned, uneven spacing.
4. **Fix** — Edit the JSON to address issues found.
5. **Re-render & re-view** — Repeat until done (typically 2-4 iterations).

### First-Time Setup

```bash
REFS="$HOME/.local/share/personal-skills/scripts/excalidraw/references"
cd "$REFS" && uv sync && uv run playwright install chromium
```

---

## Output

Save the generated `.excalidraw` file to the current working directory and display the rendered PNG path to the user.

---

## Quality Checklist

### Depth & Evidence
1. Research done for technical diagrams
2. Evidence artifacts included
3. Multi-zoom levels present
4. Concrete over abstract

### Conceptual
5. Isomorphism: visual structure mirrors concept behavior
6. Argument: diagram SHOWS something text can't
7. Variety: each major concept uses a different visual pattern

### Technical
8. Text in `text` field contains only readable words
9. `fontFamily: 3`, `roughness: 0`, `opacity: 100`
10. Container ratio: <30% of text elements inside containers

### Visual Validation (Render Required)
11. Rendered to PNG and visually inspected
12. No text overflow or overlapping elements
13. Arrows connect to intended elements
14. Balanced composition
