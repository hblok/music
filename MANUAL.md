# Forge Tracker — User Manual

Run with:

```bash
python3 -m forge.ui.main
```

---

## Window layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ▶/⏸  ⏹   1:1  [═══════════════════ seek ══════════════════════════]│  ← Transport
├──────────────────────────────────────────────────────────────────────┤
│  kick ████░░░░  intro (8)   build (8)   drop (16)       ┆           │  ← Timeline
│  hat  ░██░██░░                                          ┆           │    (coloured rows,
│  bass ░░░░░░░░                                          ┆           │     playhead line)
├────────────┬─────────────────────────────────────────────────────────┤
│  Sections  │  │▌ kick  [ on  ][ A ][ g ][ p ] ... [ on  ][ A ] ...  ×│
│  intro ●   │  │▌ hat   [ on  ][ A ][ g ][ p ] ...                   ×│
│  build     │  │▌ bass  [    ][   ][   ][   ] ...                    ×│
│  drop      │                                                         │
│  [+] [✕]  │                                                         │
├────────────┴─────────────────────────────────────────────────────────┤
│  Workshop (kick)                          │  A/B Compare             │
│  Instrument: [kick ▾] [+]                 │  [Snap A] [Snap B]       │
│  Tuning ─────●──────── 0.5               │  [Toggle A/B]            │
│  Seed: [0] [Reroll]   [▶ Audition] cached │                          │
└───────────────────────────────────────────┴──────────────────────────┘
  Status bar: Ready
```

The **│▌** symbol above represents the vertical volume fader on the left of each channel row. The **×** on the right removes that channel.

The **Mixer** is a floating dock panel (right side by default). Drag its title bar to float it as a separate window or dock it to another edge.

---

## Transport bar (top)

| Control | Action |
|---------|--------|
| `▶` / `⏸` | **Toggle play/pause.** First press renders the project then starts playback; while playing the button shows ⏸ — click again to pause. |
| `⏹` | Stop and rewind to bar 1 |
| Seek slider | Scrub to any position |
| `1:1` label | Current position as bar:beat |

**First press renders the project.** The status bar shows "Rendering for playback…" for a few seconds, then playback starts automatically. Any edit (toggling a step, changing a param, adding or removing a channel) marks the buffer stale, so the next ▶ press re-renders with the latest changes. If nothing has changed since the last render, play resumes instantly.

Hovering over the position label shows a tooltip like "Rendering: 2 channel(s)" when background channel renders are in progress.

---

## Timeline strip (below transport)

A bird's-eye view of the whole arrangement. Each section occupies a horizontal slice proportional to its bar count. Within each slice, one row per channel shows which steps are active.

- **Each channel has its own colour** — kick is blue, hat green, snare orange, bass purple, etc. Step dots use the channel colour; accent steps show a lighter shade of the same hue. The same colour is used for the channel label on the left.
- **Click a section** to select it — the tracker grid switches to that section's pattern and the section header highlights in blue.
- **Red vertical line** — the playhead shows the current playback position in real time, moving as the track plays and snapping back to bar 1 on Stop.

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

Clicking a section selects it: the transport loop range updates and the tracker grid switches to that section's pattern.

---

## Tracker grid (centre)

One row per channel. Each cell is a 16th-note step.

### Per-channel controls (left of each row)

Each channel row has a compact left panel:

| Control | Purpose |
|---------|---------|
| **Vertical fader** | Output volume for this channel (0–100%). Muted channels are skipped during the next render. |
| **M** | Mute — silences this channel on the next render. |
| **S** | Solo — mutes all other channels. Click S again (or unmute manually) to restore. |

The **×** button on the right end of each row removes that channel (undoable with Ctrl+Z).

### Step editing

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

Each section can have its own independent step pattern per channel. Select a section (via the sections list or the timeline) — the tracker shows that section's pattern. Editing steps writes to the section override; other sections are unaffected. If a section has no override it inherits the channel's default pattern.

### Adding channels

Click the **`+`** button next to the instrument dropdown in the Workshop panel. A new channel is appended using whichever instrument is currently shown in the dropdown.

---

## Workshop panel (bottom)

Shows the synthesis controls for the **currently selected channel**. Click any step in a tracker row to select that channel.

### Instrument picker

The **Instrument** drop-down lists all 27 registered synthesis engines. Changing the selection rewires the channel to a different synthesiser — the step pattern is preserved, the sound changes. The param sliders below update immediately to reflect the new instrument's parameters.

The **`+`** button next to the dropdown adds a new channel using the currently selected instrument.

### Parameters

Each instrument exposes its own synthesis parameters as sliders (floats), spinboxes (ints), or checkboxes (bools). Every slider move records an undoable transaction.

### Seed / Reroll

Many instruments use a random seed for subtle variations. The **Seed** spinbox pins an exact value. **Reroll** picks a new random seed for browsing variations.

### Audition / cached

**▶ Audition** renders this channel alone (4 bars) in a background thread and loads it for immediate playback. Repeated auditions with unchanged params are instant (cache hit) — that's what **"cached"** means next to the button.

---

## Mixer panel (floating dock)

One strip per channel, labelled with the instrument name.

- **Fader** — output gain.
- **M button** — mute/unmute.

The mixer is a floating dock widget. Drag its title bar to undock it as a standalone window, move it to another edge, or close and reopen it as needed. Note: the per-channel faders in the tracker rows and the mixer dock are independent UI controls — the tracker row faders are the ones applied during playback rendering.

---

## A/B Compare (bottom right)

A tool for comparing two parameter states side by side without losing either:

1. Dial in a sound you like. Click **Snap A** — the current state of all channels is frozen as snapshot A.
2. Tweak further. Click **Snap B** — the new state is frozen as B.
3. **Toggle A/B** — instantly swaps between the two frozen states so you can hear the difference.

Useful when you want to decide between two kick sounds, two bass lines, or two overall mixes before committing. Snapshots are session-only and not saved to disk.

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

- **Real-time step rendering** — edits are not heard live during playback; press ▶ again after editing to re-render with the changes.
- **MIDI input / export**
- **Per-step pitch / note values** — steps are on/off (with accent/ghost/probability); pitched sequencing is not yet implemented.
- **Waveform view** — a scrolling waveform display showing rendered audio across the arrangement.
