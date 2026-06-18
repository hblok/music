# Forge Tracker — Color Design: Summary, Issues, and Intent

## Overview

The tracker UI has two distinct color systems that work together:

1. **Per-channel colors** — identify which channel (instrument) a row belongs to
2. **Per-step state colors** — communicate the musical state of each individual step cell

---

## Per-Channel Colors

Each channel (instrument) is assigned a fixed color from a palette of 8, cycling if there are more than 8 channels. The same color is used consistently across all views: the timeline strip, the channel label in the tracker grid, and the step cells themselves.

| Index | Color   | Hex       |
|-------|---------|-----------|
| 0     | Blue    | `#3a8ee8` |
| 1     | Green   | `#3ab96e` |
| 2     | Orange  | `#e8783a` |
| 3     | Purple  | `#9b3ae8` |
| 4     | Pink    | `#e83a82` |
| 5     | Teal    | `#28bebe` |
| 6     | Gold    | `#c8aa28` |
| 7     | Red     | `#dc3c3c` |

The channel color is the "home color" for a step cell — it is the background of an active (on) step with no modifiers applied.

---

## Step Cell States and Their Colors

Each step cell can be in one of several mutually exclusive visual states. The hierarchy from highest to lowest priority:

| State | Background color | Intent |
|-------|-----------------|--------|
| **Selected** (click-selected channel) | `#8090cc` (slate blue) | Shows which channel the Workshop panel is currently editing |
| **On + Accent** | `#e8a03a` (amber/orange) | Loud, emphasized hit — universally warm/hot color |
| **On + Ghost** | `#3aae6e` (green) | Quiet, secondary hit — soft/subtle color |
| **On + Probability < 1.0** | `#9855d4` (purple) | Probabilistic step — distinct color signals non-determinism |
| **On (no modifier)** | Channel color (e.g. `#3a8ee8`) | Normal active step |
| **Off (strong beat)** | Channel color tinted at 38% alpha over white | Beat groups 0 and 2 (beats 1 and 3 of the bar) |
| **Off (weak beat)** | Channel color tinted at 22% alpha over white | Beat groups 1 and 3 (beats 2 and 4 of the bar) |

### Beat group coloring

16 steps are divided into four groups of four (one per beat). Groups 0 and 2 (steps 1–4 and 9–12) are "strong" beats (beats 1 and 3) and receive a slightly darker tint. Groups 1 and 3 (steps 5–8 and 13–16) are "weak" beats (beats 2 and 4) and receive a lighter tint. This mirrors standard drum machine conventions where darker = more structurally significant.

### Keyboard cursor

The cursor (moved with ← →, used for Space/A/G keyboard editing) is shown as a **2px white inner ring + 1px dark outer border** overlaid on the cell. It does not change the cell's background color — the step's on/off/accent/ghost state remains fully readable through the cursor. This was a deliberate choice: filling the cursor with a distinct color (e.g. hot pink was tried) was confusing because it looked like a step state rather than a navigation indicator.

### Text color

- **Active step** (on, selected, or accented): white text
- **Inactive step** (off): dark channel color at 45% brightness — readable on the tinted background without being harsh

---

## Modifier Rows (A / g / p)

Below each row of step cells are three rows of per-step modifier buttons, aligned column-by-column to the step cells above:

| Row | Label | Active color | Inactive color | Meaning |
|-----|-------|-------------|----------------|---------|
| A   | Accent | Orange `#e88c28` | Gray `#c8c8c8` | Step fires at ×1.5 gain (~+3.5 dB) |
| g   | Ghost  | Green `#3ab96e`  | Gray `#c8c8c8` | Step fires at ×0.4 gain (~−8 dB) |
| p   | Probability | Purple `#9b3ae8` | Gray `#c8c8c8` | Step fires with probability 0.0–1.0 |

The active state colors intentionally match the corresponding step cell state colors (A → amber, g → green, p → purple) so the connection between the button and its effect on the step cell is visually immediate.

---

## Issues Encountered

### 1. Qt Fusion style overrides stylesheet background colors

**Problem:** Setting `background-color` via `setStyleSheet` on a plain `QWidget` subclass has no effect when the app uses `app.setStyle("Fusion")`. Fusion paints the widget background from the palette, ignoring the stylesheet.

**Failed attempt:** Setting `_C_OFF_EVEN` / `_C_OFF_ODD` constants and applying them via `setStyleSheet`. The step cells appeared as uniform gray regardless of the set color.

**Solution:** Override `paintEvent` on `_StepCell` and draw the background with `QPainter.fillRect`. This bypasses Qt's style engine entirely. Store the current background as a `QColor` instance variable; call `self.update()` at the end of `_refresh()` to trigger a repaint. The child `QLabel` (which shows the step number or note name) must have `Qt.WidgetAttribute.WA_TranslucentBackground` set so it doesn't paint over the custom background.

### 2. Off-state color only showed gray tones

**Problem (first attempt):** Off-state colors were defined as two gray constants (`#e8e8e8` / `#d8d8d8`). The intent was a subtle inactive appearance, but it made all channels look identical and the step cells unreadable.

**Solution:** Compute per-instance tinted off-colors by blending the channel color with white at two alpha levels (38% for strong beats, 22% for weak beats). This keeps off-steps visually tied to the channel while still clearly distinguishing them from on-steps.

### 3. Dark/light beat group assignment was inverted

**Problem:** Initial implementation used 22% alpha (lighter) for groups 0 and 2 (strong beats) and 38% (darker) for groups 1 and 3 (weak beats). The visual result contradicted standard convention — darker should indicate more structural weight.

**Solution:** Swapped the alpha values so strong beats (groups 0 and 2) use 38% (darker) and weak beats (groups 1 and 3) use 22% (lighter).

### 4. Cursor color confused step state

**Problem:** The keyboard cursor was rendered by filling the step cell background with a distinct hot-pink color (`#e83a6e`). This made the cursor look like a distinct step state (or an error indicator), and it hid the underlying on/off/accent information of the step.

**Solution:** Removed cursor from the background fill logic. The cursor is now drawn as a 2px white inner ring + 1px dark-color outer border in `paintEvent`, overlaid on whatever the step's natural color is. The step's on/off/accent/ghost state remains fully visible; the cursor is communicated purely by outline.

---

## What Each Color Is Supposed to Convey

| Color | What it communicates |
|-------|----------------------|
| Channel color (full saturation) | This step is **on** — the instrument fires here |
| Channel color (38% tint) | Step is **off**, strong beat position — background reference for beat 1 or 3 |
| Channel color (22% tint) | Step is **off**, weak beat position — background reference for beat 2 or 4 |
| Amber / orange | **Accent** — this hit is louder than normal |
| Green | **Ghost** — this hit is quieter than normal |
| Purple | **Probability** — this hit is non-deterministic |
| Slate blue | **Selected channel** — the Workshop panel is editing this channel |
| White border ring | **Keyboard cursor** — this is where Space/A/G keyboard commands act |

The guiding principle is that color answers two questions at a glance:
1. *Which instrument is this?* → channel color (consistent across timeline, label, and step cells)
2. *What kind of hit is this?* → semantic accent/ghost/probability color, or the channel color at full strength for a plain hit
