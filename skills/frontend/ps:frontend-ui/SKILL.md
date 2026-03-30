---
name: ps:frontend-ui
description: Premium UI color system generator and reviewer. Generates production-ready CSS custom property token systems (warm/cool/dark) with brand-tinted neutrals, temperature-aware shadows, and text hierarchy. Reviews existing CSS for pure neutrals and color temperature issues. Use when the user runs /ps:frontend-ui or asks to generate a UI color system, review CSS colors, or make UI look premium/expensive.
argument-hint: <brand-hex> [--warm | --cool] [--review] [--dark]
allowed-tools: [Bash, Read, Write, Edit]
---

# Frontend UI — Premium Color System

**Arguments:** $ARGUMENTS

---

## Reference Article — Full Text
*"The One Color Decision That Makes a UI Look Expensive" by Usman Writes*

Open any product that reads as "premium." Linear. Stripe. Vercel. Raycast. Look past the brand color. Look at the backgrounds, the borders, the muted text, and the shadows. There is a decision happening at that level that most designers never consciously make. And it is the one that separates a UI that feels designed from one that feels assembled.

They never use a pure neutral. Not #FFFFFF. Not #F5F5F5. Not #000000. Every surface carries a trace of the brand hue. Every shadow leans into the same temperature. Every muted text color is warm or cool, not flat grey. The brand color does not sit on top of the design. It runs through it. That is the decision. One decision. Everything else is a consequence of getting it right.

### Why Pure Neutrals Kill a UI

The physical world does not use pure white. Paper has warmth. Packaging has a tint. Fabric has an undertone. Every material you associate with quality has a hue embedded in its neutral. Digital UI inherited the same instinct. A card sitting on #FFFFFF inside a page of #F8F8F8 reads like a spreadsheet. The same card on #FFFDF8 inside #F7F4EF reads like it was made by someone who noticed things. The gap between those two cards is 2 to 3 percent of warm hue in every neutral. That is the entire secret.

### The Three Places This Decision Lives

**1. Tinted Backgrounds and Surfaces**

The most common mistake: a blue brand color dropped onto a grey neutral system. The blue floats. It looks like a guest in its own house. The fix is to generate every neutral by mixing your brand hue into the grey scale. Not visibly. Just enough that the background leans the same direction as the brand.

```css
/* Dead: pure grey neutrals, disconnected from brand */
:root {
  --brand:      #2563EB;
  --bg:         #F8F8F8;
  --surface:    #FFFFFF;
  --border:     #E5E5E5;
  --text-muted: #6B6B6B;
}
/* Alive: every neutral carries a trace of the brand hue */
:root {
  --brand:      #2563EB;
  --bg:         #F5F7FF;  /* white + 3% brand blue */
  --surface:    #FAFBFF;  /* white + 1.5% brand blue */
  --border:     #E4E8F5;  /* grey + 5% brand blue */
  --text-muted: #6B7280;  /* cool grey, already blue-leaning */
}
```

The background never needs to shout blue. It just needs to lean blue. The brand color drops into that field and feels like it belongs.

**2. Shadows That Carry Temperature**

`box-shadow: 0 4px 12px rgba(0,0,0,0.1)` is on every UI tutorial published in the last ten years. It is also always wrong. A shadow is the absence of light. The color of that absence is shaped by the ambient light around the surface. On a warm surface, the shadow leans amber. On a cool surface, it leans blue-violet. Pure black has none of this. It reads as a Photoshop effect layered on top of the design, not a physical property of the surface.

```css
/* Generic: pure black, reads as pasted on */
.card {
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.10),
    0 4px 16px rgba(0, 0, 0, 0.08);
}
/* Premium: shadow carries the brand hue */
/* Blue brand */
.card {
  box-shadow:
    0 1px 3px rgba(37, 99, 235, 0.08),
    0 4px 16px rgba(37, 99, 235, 0.06),
    0 0 0 1px rgba(37, 99, 235, 0.04);
}
/* Warm brand */
.card {
  box-shadow:
    0 1px 3px rgba(120, 80, 40, 0.08),
    0 4px 16px rgba(120, 80, 40, 0.05),
    0 0 0 1px rgba(120, 80, 40, 0.04);
}
```

The opacity values are low on purpose. The goal is not to tint the shadow visibly. The goal is to prevent it from reading as a flat black sticker. The `0 0 0 1px` layer creates a hairline border through the shadow property — no border declaration, no layout shift, and it inherits the same temperature as the rest of the stack.

**3. Text Color Hierarchy With Temperature**

Pure black text on a white background is the accessibility floor. It is the minimum. It is not the target. Every premium product uses a near-black with a slight hue shift. The muted text color leans into the brand temperature rather than going straight grey. The hierarchy reads correctly, and the whole surface feels coherent.

```css
/* Flat: no temperature, no relationship to the brand */
:root {
  --text-primary:   #000000;
  --text-secondary: #666666;
  --text-muted:     #999999;
}
/* Warm brand: every tier leans amber */
:root {
  --text-primary:   #1A1614;
  --text-secondary: #4A4440;
  --text-muted:     #9A8E85;
}
/* Cool brand: every tier leans blue-grey */
:root {
  --text-primary:   #0F1623;
  --text-secondary: #3D4A5C;
  --text-muted:     #7B8CA0;
}
```

These values pass WCAG AA at body sizes. Nothing is being sacrificed. Temperature is being added within the existing contrast budget.

### The Full Token System

```css
/* Warm brand: editorial, fintech, premium SaaS */
:root[data-theme="warm"] {
  --color-bg:           #F7F3EE;
  --color-surface:      #FDFAF7;
  --color-surface-2:    #F2EDE6;
  --color-border:       #E8DDD2;
  --color-border-strong:#C8B8A8;
  --color-text:         #1A1410;
  --color-text-2:       #4A3E34;
  --color-text-muted:   #9A8878;
  --color-brand:        #C4502A;
  --color-brand-subtle: #F5EAE4;
  --shadow-sm: 0 1px 3px rgba(100,60,30,0.08), 0 0 0 1px rgba(100,60,30,0.04);
  --shadow-md: 0 4px 16px rgba(100,60,30,0.10), 0 1px 4px rgba(100,60,30,0.06);
  --shadow-lg: 0 12px 40px rgba(100,60,30,0.12), 0 2px 8px rgba(100,60,30,0.06);
}
/* Cool brand: dev tools, analytics, B2B tech */
:root[data-theme="cool"] {
  --color-bg:           #F4F6FA;
  --color-surface:      #FAFBFD;
  --color-surface-2:    #EDF0F7;
  --color-border:       #DDE3EE;
  --color-border-strong:#BCC6DA;
  --color-text:         #0F1520;
  --color-text-2:       #3A4560;
  --color-text-muted:   #7A8BA0;
  --color-brand:        #2563EB;
  --color-brand-subtle: #EEF3FF;
  --shadow-sm: 0 1px 3px rgba(30,50,100,0.08), 0 0 0 1px rgba(30,50,100,0.04);
  --shadow-md: 0 4px 16px rgba(30,50,100,0.10), 0 1px 4px rgba(30,50,100,0.06);
  --shadow-lg: 0 12px 40px rgba(30,50,100,0.12), 0 2px 8px rgba(30,50,100,0.06);
}
```

### A Real Card Component

```css
.card {
  background:    var(--color-surface);
  border:        1px solid var(--color-border);
  border-radius: 8px;
  box-shadow:    var(--shadow-md);
  padding:       24px;
}
.card-label {
  font-size:      0.7rem;
  font-weight:    500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color:          var(--color-text-muted);
  margin-bottom:  8px;
}
.card-title {
  font-size:     1.25rem;
  font-weight:   600;
  color:         var(--color-text);
  line-height:   1.3;
  margin-bottom: 8px;
}
.card-body {
  font-size:   0.9rem;
  line-height: 1.65;
  color:       var(--color-text-2);
}
.card-badge {
  display:        inline-block;
  background:     var(--color-brand-subtle);  /* hue-accurate tint, not generic grey */
  color:          var(--color-brand);
  font-size:      0.72rem;
  font-weight:    500;
  letter-spacing: 0.06em;
  padding:        3px 10px;
  border-radius:  4px;
  margin-top:     16px;
}
```

The badge uses `--color-brand-subtle` — not a generic light blue, not a washed-out orange. A hue-accurate tint of the brand itself at very low saturation. That one token is what makes the badge feel like it belongs in the system rather than being imported from a component library.

### Dark Mode: The Same Rule, Different Direction

Dark mode is not a black background. It is a dark tinted background.

```css
:root[data-theme="dark"] {
  --color-bg:      #0F1117;
  --color-surface: #161B27;
  --color-border:  #1E2738;
  --color-text:    #E8EDF5;
  --color-text-2:  #8A9AB5;
  --shadow-sm: 0 0 0 1px rgba(100,140,255,0.08);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(100,140,255,0.06);
}
```

`#18181B` is zinc-900. No hue. No temperature. It is a default. `#0F1117` leans into the blue-dark family. The surface at `#161B27` is clearly in the same conversation as the brand. The text at `#E8EDF5` is off-white, cool-leaning, not clinical. On dark backgrounds, shadows become glows. The `0 0 0 1px` layer becomes a luminance border rather than a depth border. Same principle. Opposite direction.

### One Test Before You Ship

Desaturate the screen to greyscale. If the hierarchy still reads clearly, the temperature work is invisible and correct. If the design collapses, the tints were doing structural work they should not be doing. Color temperature is a layer on top of a sound greyscale system. Not a replacement for it.

### Three Rules That Apply Everywhere

1. **Never use a pure neutral.** `#FFFFFF`, `#000000`, `#808080` belongs to no brand. Every neutral in a production token set carries a hue, even if it is just 2 percent.
2. **Match shadow color to brand temperature.** Blue brand, blue-tinted shadows. Warm brand, amber-tinted shadows. Pure black shadows belong to nothing and look like it.
3. **Tint every interactive state.** Hover, focus, active. All of them use `--color-brand-subtle` or a more saturated version of the surface. Never a flat grey overlay.

The decision is not complicated. It is just easy to skip when moving fast. Everything premium you have seen is built on this.

---

---

## Step 0 — Parse arguments

From `$ARGUMENTS`, extract:
- `BRAND_HEX` — the brand color (e.g. `#2563EB`). If not provided, ask the user.
- `--warm` — force warm temperature system
- `--cool` — force cool temperature system
- `--dark` — also generate dark mode tokens
- `--review` — review existing CSS files in the project instead of generating

If `--review` is present, skip to **Step 4 — Review mode**.

---

## Step 2 — Detect brand temperature

If neither `--warm` nor `--cool` is given, auto-detect from the brand hex:

```python
# Parse the brand hex, check hue angle
# Hue 0-60 or 300-360 → warm (red, orange, yellow, magenta)
# Hue 60-300 → cool (green, cyan, blue, purple)
import colorsys
r,g,b = int(hex[1:3],16)/255, int(hex[3:5],16)/255, int(hex[5:7],16)/255
h,s,v = colorsys.rgb_to_hsv(r,g,b)
hue_deg = h * 360
temperature = "warm" if (hue_deg < 60 or hue_deg > 300) else "cool"
```

Tell the user: *"Detected: [warm/cool] temperature system for brand [HEX]."*

---

## Step 3 — Generate token system

### Rule: never use a pure neutral
Every background, surface, border, shadow, and text color carries 2–5% brand hue.

Generate and output the complete CSS token system:

**For COOL brand** (dev tools, analytics, B2B SaaS):
```css
:root {
  /* Brand */
  --color-brand:        <BRAND_HEX>;
  --color-brand-subtle: <brand at 8% opacity on white>;

  /* Backgrounds — white + 1.5–3% brand blue */
  --color-bg:           <slightly blue-tinted white>;
  --color-surface:      <near white, 1% brand>;
  --color-surface-2:    <slightly deeper, 3% brand>;

  /* Borders */
  --color-border:       <grey + 5% brand>;
  --color-border-strong:<darker grey + 8% brand>;

  /* Text — blue-grey leaning */
  --color-text:         <near black, cool tint ~#0F1623>;
  --color-text-2:       <mid dark, cool ~#3D4A5C>;
  --color-text-muted:   <mid grey, cool ~#7B8CA0>;

  /* Shadows — brand-tinted, NOT rgba(0,0,0,...) */
  --shadow-sm: 0 1px 3px rgba(R,G,B, 0.08), 0 0 0 1px rgba(R,G,B, 0.04);
  --shadow-md: 0 4px 16px rgba(R,G,B, 0.10), 0 1px 4px rgba(R,G,B, 0.06);
  --shadow-lg: 0 12px 40px rgba(R,G,B, 0.12), 0 2px 8px rgba(R,G,B, 0.06);
}
```

**For WARM brand** (fintech, editorial, premium SaaS):
```css
:root {
  /* Brand */
  --color-brand:        <BRAND_HEX>;
  --color-brand-subtle: <brand at 8% on warm white>;

  /* Backgrounds — white + 2–4% amber */
  --color-bg:           ~#F7F3EE;
  --color-surface:      ~#FDFAF7;
  --color-surface-2:    ~#F2EDE6;

  /* Borders — warm grey */
  --color-border:       ~#E8DDD2;
  --color-border-strong:~#C8B8A8;

  /* Text — amber-leaning */
  --color-text:         ~#1A1410;
  --color-text-2:       ~#4A3E34;
  --color-text-muted:   ~#9A8878;

  /* Shadows — amber-tinted */
  --shadow-sm: 0 1px 3px rgba(R,G,B, 0.08), 0 0 0 1px rgba(R,G,B, 0.04);
  --shadow-md: 0 4px 16px rgba(R,G,B, 0.10), 0 1px 4px rgba(R,G,B, 0.06);
  --shadow-lg: 0 12px 40px rgba(R,G,B, 0.12), 0 2px 8px rgba(R,G,B, 0.06);
}
```

Compute actual hex values mathematically by mixing brand RGB into the grey scale at the stated percentages.

If `--dark` was requested, also generate:
```css
:root[data-theme="dark"] {
  /* Dark: blue-dark family, NOT zinc-900 (#18181B has no hue) */
  --color-bg:      <brand-tinted dark ~#0F1117 for cool>;
  --color-surface: <slightly lighter ~#161B27>;
  --color-border:  <subtle border ~#1E2738>;
  --color-text:    <off-white, cool ~#E8EDF5>;
  --color-text-2:  <mid ~#8A9AB5>;
  /* Shadows become glows in dark mode */
  --shadow-sm: 0 0 0 1px rgba(R,G,B, 0.08);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(R,G,B, 0.06);
}
```

---

## Step 3b — Output a ready-to-use card component

Always include a card component that uses the generated tokens:

```css
.card {
  background:    var(--color-surface);
  border:        1px solid var(--color-border);
  border-radius: 8px;
  box-shadow:    var(--shadow-md);
  padding:       24px;
}
.card-title {
  font-size: 1.25rem; font-weight: 600;
  color: var(--color-text); line-height: 1.3; margin-bottom: 8px;
}
.card-body {
  font-size: 0.9rem; line-height: 1.65;
  color: var(--color-text-2);
}
.card-badge {
  display: inline-block;
  background: var(--color-brand-subtle);  /* hue-accurate tint, not generic grey */
  color: var(--color-brand);
  font-size: 0.72rem; font-weight: 500; letter-spacing: 0.06em;
  padding: 3px 10px; border-radius: 4px; margin-top: 16px;
}
```

Then remind the user: **"Greyscale test: desaturate your screen (Cmd+Shift+A on Mac / browser devtools). If hierarchy still reads clearly, the temperature work is invisible and correct."**

---

## Step 4 — Review mode (`--review`)

Scan CSS/SCSS/Tailwind config files in the current directory for color temperature issues:

```bash
grep -rn "#ffffff\|#FFFFFF\|#000000\|#f5f5f5\|#F5F5F5\|rgba(0,0,0\|rgba(0, 0, 0" \
  --include="*.css" --include="*.scss" --include="*.ts" --include="*.tsx" \
  --include="*.js" --include="*.jsx" . 2>/dev/null | head -40
```

For each finding, report:
- **File:line** — the pure neutral found
- **Issue** — why it hurts the premium feel
- **Fix** — the brand-tinted replacement to use

Categories:
| Found | Issue | Fix |
|---|---|---|
| `#ffffff` / `#FFFFFF` | Pure white surface | Use `--color-surface` or `#FAFBFF` |
| `#f5f5f5` / `#F5F5F5` | Grey background, no brand | Use `--color-bg` tinted version |
| `rgba(0,0,0,...)` in shadow | Cold black shadow | Use brand-tinted `rgba(R,G,B,...)` |
| `#000000` in text | Pure black, clinical | Use `--color-text` near-black with hue |
| `#666666` / `#999999` muted | Flat grey, no temperature | Use `--color-text-muted` cool/warm version |

Output a summary:
```
Found N color temperature issues across X files.
Most impactful fix: <the one change that will have biggest visual impact>
```

---

## Step 5 — Save tokens to file (optional)

Ask: **"Save tokens to `tokens.css`? (y/n)"**

If yes, write the generated CSS to `tokens.css` in the current directory.

---

## Tips printed at the end

Always print:
```
Three rules that apply everywhere:
  1. Never use a pure neutral — every token carries a hue, even 2%
  2. Match shadow color to brand temperature (blue brand → blue shadows)
  3. Tint every interactive state — hover/focus use --color-brand-subtle, never flat grey overlay
```
