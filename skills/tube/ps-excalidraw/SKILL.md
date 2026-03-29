---
name: ps-excalidraw
description: Generate an Excalidraw diagram from a description and render it to PNG. Use when the user runs /ps-excalidraw <description> or asks to create a diagram/chart/flowchart/architecture diagram.
argument-hint: <description-of-diagram>
allowed-tools: [Bash, Read, Write]
---

# Excalidraw Diagram Generator

The user wants to create a diagram.

**Arguments:** $ARGUMENTS

## Step 0 — Bootstrap if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/excalidraw/render_excalidraw.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

## Step 1 — Ensure dependencies

```bash
bash "$HOME/.local/share/personal-skills/scripts/excalidraw/setup.sh"
```

If exit non-zero, show error and stop.

## Step 2 — Generate the .excalidraw JSON

Based on the user's description in `$ARGUMENTS`, generate a valid Excalidraw JSON file.

Write it to a temp file:

```bash
cat > /tmp/diagram.excalidraw << 'EXCALIDRAW_EOF'
<YOUR_GENERATED_JSON>
EXCALIDRAW_EOF
```

### Excalidraw JSON format

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "personal-skills",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "exportBackground": true
  },
  "files": {}
}
```

### Element types

**Rectangle:**
```json
{"type":"rectangle","id":"r1","x":100,"y":100,"width":200,"height":80,"strokeColor":"#1e1e2e","backgroundColor":"#cba6f7","fillStyle":"solid","strokeWidth":2,"roughness":1,"opacity":100,"text":"Label","fontSize":16,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","roundness":{"type":3}}
```

**Text:**
```json
{"type":"text","id":"t1","x":100,"y":200,"width":200,"height":25,"text":"Hello","fontSize":18,"fontFamily":1,"textAlign":"center","verticalAlign":"top","strokeColor":"#1e1e2e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":1,"roughness":1,"opacity":100}
```

**Arrow:**
```json
{"type":"arrow","id":"a1","x":200,"y":180,"width":0,"height":60,"points":[[0,0],[0,60]],"strokeColor":"#1e1e2e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,"roughness":1,"opacity":100,"startArrowhead":null,"endArrowhead":"arrow","startBinding":{"elementId":"r1","focus":0,"gap":5},"endBinding":{"elementId":"r2","focus":0,"gap":5}}
```

**Diamond:**
```json
{"type":"diamond","id":"d1","x":100,"y":100,"width":160,"height":80,"strokeColor":"#1e1e2e","backgroundColor":"#a6e3a1","fillStyle":"solid","strokeWidth":2,"roughness":1,"opacity":100}
```

**Ellipse:**
```json
{"type":"ellipse","id":"e1","x":100,"y":100,"width":180,"height":80,"strokeColor":"#1e1e2e","backgroundColor":"#89dceb","fillStyle":"solid","strokeWidth":2,"roughness":1,"opacity":100}
```

### Layout guidelines

- Space elements at least 40px apart
- Use 120–180px row height for boxes, 50px for arrows between them
- For flowcharts: top-to-bottom layout, x centered around 400, y starts at 80, increment by 150
- For architecture: group related boxes, use arrows to show data flow
- Keep total diagram under 1200px wide, 1600px tall

### Color palette (Catppuccin Mocha)

- Purple (highlight): `#cba6f7`
- Green (success/done): `#a6e3a1`
- Blue (info/system): `#89dceb`
- Yellow (warning/decision): `#f9e2af`
- Red (error/critical): `#f38ba8`
- Peach (action): `#fab387`
- Text/stroke: `#1e1e2e`
- Background: `#ffffff`

## Step 3 — Render to PNG

```bash
python3 "$HOME/.local/share/personal-skills/scripts/excalidraw/render_excalidraw.py" \
  /tmp/diagram.excalidraw --output /tmp/diagram.png
```

If successful, the PNG path is printed to stdout.

## Step 4 — Display the result

Read and display the PNG image using the Read tool:

```
Read /tmp/diagram.png
```

Then tell the user:
- The diagram was rendered to `/tmp/diagram.png`
- They can copy it with: `cp /tmp/diagram.png ~/diagram.png`
- Raw JSON is at `/tmp/diagram.excalidraw`
- They can open the `.excalidraw` file at excalidraw.com to edit it
