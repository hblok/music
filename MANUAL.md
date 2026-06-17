# Forge Tracker — User Manual

Run with:

```bash
python3 -m forge.ui.main
```

---

## Window layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ▶  ⏸  ⏹   1:1  [═══════════════════ seek ═════════════════════]│  ← Transport
├──────────────────────────────────────────────────────────────────┤
│  kick  [●···][····][●···][····]  intro (8)  build (8)  drop (16) │  ← Timeline
│  hat   [●·●·][●·●·][●·●·][●·●·]                                  │
│  bass  [·····················]                                   │
├────────────┬─────────────────────────────────────────────────────┤
│  Sections  │  + Channel  − Channel                               │
│  intro ●   │  kick  [ on  ][  A ][  g ][ p ] [ on  ][ A ]...    │
│  build     │  hat   [ on  ][  A ][  g ][ p ] [ on  ][ A ]...    │
│  drop      │  bass  [    ][    ][    ][   ] ...                  │
│  [+] [✕]  │                                                     │
├────────────┴─────────────────────────────────────────────────────┤
│  Workshop (kick)                       │  A/B Compare            │
│  Instrument: [kick ▾]                  │  [Snap A] [Snap B]      │
│  Tuning ─────●──────── 0.5             │  [Toggle A/B]           │
│  Decay  ────────●───── 0.3             │                         │
│  Seed: [0] [Reroll]   [▶ Audition] cached                        │
└────────────────────────────────────────┴────────────────────────-┘
  Status bar: Ready
```

The **Mixer** is a floating dock panel (right side by default). Drag its title bar to float it as an independent window or dock it to any edge.

---

## Transport bar (top)

| Control | Action |
|---------|--------|
| `▶` | Render the project then start playback |
| `⏸` | Pause at current position |
| `⏹` | Stop and rewind to the start |
| Seek slider | Scrub to any position |
| `1:1` label | Current position as bar:beat |

**Pressing Play triggers a background render.** The status bar shows "Rendering for playback…" for a few seconds, then playback starts automatically. Any edit (toggling a step, changing a param, adding a channel) marks the buffer stale so the next Play re-renders with the latest changes. A second Play press while the project is unchanged reuses the cached buffer and starts immediately.

Hovering over the position label shows a tooltip like "Rendering: 2 channel(s)" when background channel renders are in progress.

---

## Timeline strip (below transport)

A bird's-eye view of the whole arrangement. Each section occupies a horizontal slice proportional to its bar count. Within each slice, one row per channel shows which steps are active (blue = on, orange = accented).

- **Click a section** in the timeline to select it — the tracker grid switches to show and edit that section's pattern.
- The active section header is highlighted in blue.

---

## Sections panel (left)

Lists the named sections of your track in playback order.

| Button | Action |
|--------|--------|
| `+ Add` | Prompt for a name; appends a new section |
| `✕` | Delete the selected section |
| `✎` | Rename the selected section |
| `▲ ▼` | Reorder sections |
| `⎘` | Duplicate the selected section |
| `bars: N` spinner | Change the length of the selected section in bars |

Clicking a section selects it: the transport loop range is set to that section's bar range, and the tracker grid switches to show that section's step pattern.

---

## Tracker grid (centre)

One row per channel. Each cell is a 16th-note step.

| Action | Result |
|--------|--------|
| Left-click a step | Toggle on/off; also selects this channel in the Workshop |
| `Space` | Toggle step at cursor |
| `A` | Toggle accent on cursor step |
| `G` | Toggle ghost on cursor step |
| `← →` | Move cursor left/right |
| `Ctrl+C / Ctrl+V` | Copy/paste step block |
| Right-click or `P` | Per-step param override popover |
| `Delete` | Clear cursor step |

### Per-section patterns

Each section can have its own independent step pattern per channel. Select a section (via the sections list or the timeline) — the tracker shows that section's pattern. Editing steps writes to the section override, leaving other sections' patterns unchanged. If a section has no override, it inherits the channel's default pattern.

The **drop** section in the example project has no overrides and shows the channel defaults.

### Adding / removing channels

The **`+ Channel`** and **`− Channel`** buttons above the tracker grid manage channels:

- **`+ Channel`** opens a picker listing all 27 instruments; the new channel is appended with a default empty pattern.
- **`− Channel`** removes the currently selected channel (the one whose row you last clicked).

Both operations are undoable (Ctrl+Z).

---

## Workshop panel (bottom)

Shows the synthesis controls for the **currently selected channel**. Click any step in a tracker row to select that channel.

### Instrument picker

The **Instrument** drop-down lists all 27 registered synthesis engines. Changing the selection rewires the channel to a different synthesiser — the step pattern is preserved, the sound changes. The param sliders below update immediately to reflect the new instrument's parameters.

### Parameters

Each instrument exposes its own synthesis parameters as sliders (floats), spinboxes (ints), or checkboxes (bools). Every slider move records an undoable transaction.

### Seed / Reroll

Many instruments use a random seed for subtle variations. The **Seed** spinbox pins an exact value. **Reroll** picks a new random seed for browsing.

### Audition / cached

**▶ Audition** renders this channel alone (4 bars) in a background thread and loads it for immediate playback. Repeated auditions with unchanged params are instant (cache hit) — that's what **"cached"** means next to the button.

---

## Mixer panel (floating dock)

One fader strip per channel, labelled with the instrument name.

- **Fader** — output gain (0–100%).
- **M button** — mute/unmute the channel.

The mixer is a floating dock widget. Drag its title bar to undock it as a standalone window, move it to another edge, or close it entirely. Reopen it from the View menu if closed (or restart the app).

---

## A/B Compare (bottom right)

Compare two parameter states without losing either:

1. Dial in a sound. Click **Snap A** — the current state of all channels is frozen as snapshot A.
2. Tweak further. Click **Snap B** — current state frozen as B.
3. **Toggle A/B** — instantly swaps between the two states. The tracker grid and Workshop update to reflect the active snapshot.

Snapshots are session-only; they are not saved to disk.

---

## File menu

| Item | What it does |
|------|--------------|
| **New project** | Resets to the default 3-channel starter (kick / hat / bass, intro + drop sections) |
| **Open Tracker project…** | Loads a `.json` file (schema version 3.0) |
| **Save Tracker project…** | Saves the current project as `.json` |
| **Export WAV…** | Renders all channels across all sections to a stereo 44.1 kHz WAV |
| **Quit** | Exit the application |

### Example project

`examples/example_tracker.json` ships with four channels (kick, hat, snare, bass) and three sections:

- **intro** — sparse half-time feel; each channel has its own section pattern override.
- **build** — four-on-floor kick, 8th-note hat, backbeat snare, busier bass.
- **drop** — no overrides; channels play their default patterns.

Load it via **File → Open Tracker project…**

### Autosave

A background autosave writes to `{tmpdir}/forge_autosave.json` every 10 seconds. If the app crashes, recover by opening that file.

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `Space` | Toggle step at cursor (tracker grid must have focus) |
| `A` | Accent step at cursor |
| `G` | Ghost step at cursor |
| `← →` | Move cursor in tracker row |
| `Ctrl+C / Ctrl+V` | Copy / paste step block |
| `Delete` | Clear cursor step |

---

## What is not yet built

- **Real-time step rendering** — edits are not heard live during looped playback; press Play again after editing to re-render.
- **MIDI input / export**
- **Per-step pitch / note values** — steps are on/off (with accent/ghost/probability); pitched sequencing is not yet implemented.
- **Waveform view** — a scrolling waveform display showing rendered audio across the arrangement.
