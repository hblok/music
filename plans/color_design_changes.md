# Forge Tracker — Color Design: Verification Report

**Date:** 2026-06-18
**Source plan:** `plans/color_design_tracker.md`
**Code verified:** `forge/ui/pattern_editor.py`, `forge/ui/timeline.py`, `forge/ui/window.py`, `forge/ui/main.py`, `forge/patterns/groove.py`
**Scope:** read-only verification. No code was modified.

---

## Verdict

The core color *system* is implemented faithfully: the 8-color channel palette,
the per-step state colors (accent / ghost / probability), the off-state beat-group
tints, the keyboard-cursor ring, and the modifier-button colors all match the plan's
intent, and the four "Issues Encountered" fixes are all present in the code.

There is **one substantive mismatch** (the slate-blue "Selected" color means
something different in the code than the plan describes) and **a handful of smaller
doc/code drift items**. Details below, each tagged 🔴 high / 🟡 medium / 🟢 low.

---

## What matches the plan ✅

| Plan element | Code location | Status |
|---|---|---|
| 8-color channel palette (blue…red) | `pattern_editor.py:242-251` | ✅ exact hex match |
| Palette mirrored in timeline | `timeline.py:24-33` | ✅ identical RGB values |
| On+Accent = `#e8a03a` | `pattern_editor.py:272` | ✅ |
| On+Ghost = `#3aae6e` | `pattern_editor.py:273` | ✅ |
| On+Prob<1.0 = `#9855d4` | `pattern_editor.py:274` | ✅ |
| Selected = `#8090cc` (value) | `pattern_editor.py:276` | ✅ value matches (semantics differ — see #1) |
| On (no modifier) = channel color | `pattern_editor.py:366` | ✅ |
| State priority order (selected→accent→ghost→prob→on→off) | `pattern_editor.py:356-368` | ✅ |
| Off strong-beat = channel @ 38% over white | `pattern_editor.py:307` | ✅ |
| Off weak-beat = channel @ 22% over white | `pattern_editor.py:308` | ✅ |
| Beat-group assignment (groups 0,2 strong / 1,3 weak) | `pattern_editor.py:354` | ✅ `(idx//4)%2==0` correct |
| Cursor = 2px white ring + 1px dark border, no bg fill | `pattern_editor.py:383-396` | ✅ |
| Active text white / inactive text = channel×0.45 | `pattern_editor.py:310-312, 370-371` | ✅ |
| Modifier inactive gray `#c8c8c8` | `pattern_editor.py:499` | ✅ |
| Modifier active colors match step-cell state colors (the *intent*) | `pattern_editor.py:505,510,515` | ✅ code honors intent (but plan's table hexes are stale — see #2) |
| Accent ×1.5 / ghost ×0.4 gain | `groove.py:74, 138` | ✅ `gain = 1.5 if accent else (0.4 if ghost else 1.0)` |

**Issues Encountered (plan §"Issues") — all four fixes confirmed present:**

1. Fusion override → `QPainter.fillRect` in `paintEvent` + `WA_TranslucentBackground`
   on the label: `main.py:29` (`setStyle("Fusion")`), `pattern_editor.py:319, 383-396`. ✅
2. Off-state gray → per-instance tint blended with white: `pattern_editor.py:301-308`. ✅
3. Strong/weak alpha inversion fixed (38% strong, 22% weak): `pattern_editor.py:307-308`. ✅
4. Hot-pink cursor fill removed → outline-only cursor: `pattern_editor.py:388-392`. ✅

---

## Discrepancies & changes needed

### 1. 🔴 Slate-blue `#8090cc` means "step-range selection," not "selected channel"

**Plan says** (state table + "what each color conveys"): slate blue =
> "Shows which channel the Workshop panel is currently editing" / "Selected channel — the Workshop panel is editing this channel."

**Code reality:** `_StepCell._selected` / `_C_SELECTED` is driven **only** by
`TrackerRow.set_selected(start, end)` (`pattern_editor.py:579-581`), whose **only**
non-test caller is the **Ctrl+A "select all steps"** path
(`pattern_editor.py:888-891`). It highlights a *range of step cells within one row*
for copy/paste — it is not a channel-level indicator.

The channel the Workshop panel edits is tracked separately as
`window._selected_channel`; selecting it (`window.py:238` `cursorMoved → _select_channel`,
`window.py:298-301`) only **swaps the Workshop panel** — it produces **no slate-blue
highlight** and, in fact, no distinct highlight at all beyond the always-on faint
channel-color row tint (`pattern_editor.py:642-645`).

So the value (`#8090cc`) and its top priority position are implemented correctly, but
the **meaning documented in the plan is not what the code does.**

**Recommended change** (pick one):
- **(Doc, minimal)** Update the plan so slate blue is described as the **step-range
  copy/paste selection** color, and note that the Workshop-edited channel currently has
  no dedicated highlight. *This matches shipped behavior.*
- **(Code, if the plan's intent is desired)** Add a channel-level "selected" highlight
  (e.g. a 2px channel-color border on the focused/selected `TrackerEditor`, or wire
  `window._select_channel` to mark the editor) and choose a *different* color/treatment
  for the step-range selection so the two concepts don't collide on `#8090cc`.

**Related behavior note:** the step-range selection is "sticky." Nothing clears
`_sel_start/_sel_end` or calls `set_selected` with a narrowed range after Ctrl+A
(no clear on cursor move at `pattern_editor.py:840-849`, or on click at `:767-774`).
Because `_selected` outranks every other state in `_refresh` (`:356`), a select-all
turns the whole row slate blue and **hides all on/off/accent/ghost info until the row
is rebuilt**. Worth addressing if the channel-highlight redesign is taken up.

---

### 2. 🟡 Plan's "Modifier Rows" table hexes contradict the plan's own stated intent (code is correct)

The plan's Modifier Rows table lists active colors:

| Row | Plan table | Code (`pattern_editor.py`) | Step-cell state color |
|---|---|---|---|
| A (accent) | `#e88c28` | `#e8a03a` (`:505`) | `#e8a03a` (`:272`) |
| g (ghost) | `#3ab96e` | `#3aae6e` (`:510`) | `#3aae6e` (`:273`) |
| p (prob) | `#9b3ae8` | `#9855d4` (`:515`) | `#9855d4` (`:274`) |

The plan's prose immediately below that table says the active colors *"intentionally
match the corresponding step cell state colors."* The **code does exactly that** — the
modifier buttons use the step-state trio. The **plan table is the outlier**: its values
are stale, and `#3ab96e` / `#9b3ae8` are actually the *channel palette* green/purple
(indices 1 and 3), not the step-state colors.

**Recommended change (Doc):** correct the Modifier Rows table to
`#e8a03a` / `#3aae6e` / `#9855d4` so it agrees with both the code and the plan's own
"intentionally match" sentence. No code change needed.

---

### 3. 🟢 Dead constant `_C_CURSOR = "#e83a6e"`

`pattern_editor.py:275` still defines the old hot-pink cursor color, but it is
referenced nowhere (the cursor is now drawn as a white/dark outline — Issue #4). This
is the leftover of the fix described in the plan.

**Recommended change (Code, cleanup):** remove the unused `_C_CURSOR` constant.
*(Flagged only; not removed, per the no-code-change instruction.)*

---

### 4. 🟢 Tracker channel **label** is not drawn in the channel color

The plan states the channel color is used consistently across
*"the timeline strip, the channel label in the tracker grid, and the step cells."*

- Timeline label **is** colored: `timeline.py:134` (`ch_color.darker(140)`). ✅
- Tracker labels are **not** colored: `TrackerRow` label (`pattern_editor.py:486-488`)
  and `TrackerEditor._inst_label` (`pattern_editor.py:677-682`) apply no channel color —
  they render in the default palette text color.

The only channel-color cue in the tracker editor is the faint always-on row background
tint (`rgba(...,20)`, `pattern_editor.py:642-645`). So the *claim* "the channel label …
uses the channel color" is not literally true for the tracker grid.

**Recommended change** (pick one):
- **(Code)** Tint the tracker label text with the channel color (e.g.
  `darker(140)`, matching the timeline) to deliver the consistency the plan promises.
- **(Doc)** Soften the wording to "a channel-color tint on the row background" for the
  tracker, reserving "colored label text" for the timeline.

---

## Minor observations (no change required)

- **Timeline does not use the semantic state colors.** Accent is shown as a *lighter
  shade of the channel color* (`timeline.py:193`, `ch_color.lighter(160)`); ghost and
  probability are not visually distinguished there at all. This is consistent with the
  plan *as written* (the state-color table is explicitly about the tracker step cells),
  but note the amber/green/purple semantics are intentionally **not** mirrored in the
  timeline overview.

- **Plan text-color wording "(on, selected, or accented)"** (plan §"Text color") vs code
  `is_active = self._on or self._selected` (`pattern_editor.py:370`). "Accented" is not
  in the predicate, but it's a non-issue: a cell only shows accent coloring when also
  `on`, and an accent-without-on step paints as a normal off cell. The wording is just
  slightly loose; behavior is correct.

- **Legacy `StepButton` / `PatternRow` / `PatternEditor`** (`pattern_editor.py:64-231`)
  hard-code `#3a8ee8` on / `#e0e0e0` off and predate the color system. The file header
  marks this API "unchanged," and the plan does not cover it — not a defect, just out of
  scope for the color design.

- **No test coverage of colors.** `tests/test_tracker_editor.py` asserts cell *state*
  (`_accent`, `_cursor`, `_selected`) but never the resolved hex/`_bg_color`. The color
  design is therefore enforced only by the plan + code, not by tests. Optional: add a
  couple of `_refresh()`-then-assert-`_bg_color` tests to lock the mapping in.

---

## Summary of recommended changes

| # | Sev | Type | Change |
|---|-----|------|--------|
| 1 | 🔴 | Doc or Code | Reconcile slate-blue `#8090cc`: either document it as the step-range selection color (matches code) **or** implement a real channel-selected highlight + a distinct selection color. Also consider clearing the sticky select-all highlight. |
| 2 | 🟡 | Doc | Fix Modifier Rows table to `#e8a03a` / `#3aae6e` / `#9855d4` (code already correct). |
| 3 | 🟢 | Code | Remove unused `_C_CURSOR` constant. |
| 4 | 🟢 | Doc or Code | Either color the tracker label text with the channel color, or soften the "channel label uses the channel color" claim for the tracker. |
