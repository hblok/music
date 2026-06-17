# Forge Tracker — User Manual

Run with:

```bash
python3 -m forge.ui.main
```

---

## Window layout

```
┌─────────────────────────────────────────────────────────────┐
│  ▶  ⏸  ⏹   1:1  [═══════════════════ seek ════════════════]│  ← Transport
├────────────┬───────────────────────────────┬────────────────┤
│  Sections  │  kick  [● . . . ● . . . ...]  │  Mixer         │
│  intro     │  hat   [● . ● . ● . ● . ...]  │  kick  ──●──   │
│  drop      │  bass  [. . . . . . . . ...]  │  hat   ──●──   │
│            │                               │  bass  ──●──   │
│  [+] [✕]  │                               │                │
├────────────┴───────────────────────────────┴────────────────┤
│  Workshop (kick)                     │  A/B Compare         │
│  Instrument: [kick ▾]                │  [Snap A] [Snap B]   │
│  Tuning ─────●──────── 0.5           │  [Toggle A/B]        │
│  Decay  ────────●───── 0.3           │                      │
│  Seed: [0] [Reroll]                  │                      │
│  [▶ Audition]  cached                │                      │
└──────────────────────────────────────┴──────────────────────┘
  Status bar: Ready
```

---

## Sections panel (left)

The sections panel lists the named sections of your track in playback order.
Each section has a **name** and a **bar length**.

| Button | Action |
|--------|--------|
| `+ Add` | Prompt for a name; appends a new section at the current bar length |
| `✕` | Delete the selected section |
| `✎` | Rename the selected section |
| `▲ ▼` | Reorder sections |
| `⎘` | Duplicate the selected section |
| `bars: N` spinner | Change the selected section's length in bars |

Clicking a section sets the transport loop range to cover that section's bar range.
The default project opens with **intro** (8 bars) and **drop** (16 bars).

---

## Tracker grid (centre)

One row per channel. Each cell is a 16th-note step.

| Action | Result |
|--------|--------|
| Left-click a step | Toggle on/off |
| Click anywhere in a row | Selects that channel in the Workshop panel |

Steps show `●` when active. The pattern loops every 16 steps (one bar).

### Adding a channel

Currently channels are created by editing the project JSON directly or by building a custom `ProjectDoc` in code. A GUI "add channel" button is not yet implemented — it's the obvious next thing to add.

---

## Workshop panel (bottom left)

Shows the controls for the **currently selected channel** (click any row in the tracker to select it).

### Instrument picker

The **Instrument** drop-down lists all 27 registered synthesis engines (kick, hat, snare, bass, pad, lead, etc.). Changing the selection rewires that channel to a different synthesiser immediately. The step pattern is preserved; the sound changes.

Each instrument exposes its own set of synthesis parameters as sliders (floats) or checkboxes (bools). Moving a slider records an undoable transaction in the document.

### Seed / Reroll

Many instruments use a random seed to vary subtle details (phase offsets, noise floor, micro-timing). The **Seed** spinbox lets you pin an exact value. **Reroll** picks a new random seed so you can browse variations.

### Audition / cached

**▶ Audition** renders the current channel (4 bars at the project BPM) in a background thread and loads the result into the playback service so you can hear it immediately.

The render is cached by a content-addressed key derived from the channel's instrument, params, seed, and step pattern. If nothing has changed since the last render, the button reuses the cached buffer instantly — that's what **"cached"** means in the status label next to the button. **"rendering…"** means a background thread is working; clicking play again after a second or two will use the fresh result.

---

## Mixer panel (right)

One fader strip per channel, labelled with the instrument ID.

- Drag the fader to set the output gain for that channel.
- The mute button silences a channel during playback.

---

## Transport bar (top)

| Control | Action |
|---------|--------|
| `▶` | Play from current position |
| `⏸` | Pause |
| `⏹` | Stop and rewind to start |
| Seek slider | Scrub to any position in the track |
| `1:1` label | Shows current position as bar:beat |

The seek slider covers the full track length. After auditioning a channel the slider covers 4 bars; after loading a full project it scales to the total section length.

Hovering over the `1:1` label shows a tooltip like "Rendering: 2 channel(s)" when background renders are in progress.

---

## A/B Compare (bottom right)

Use this to compare two variations of your instrument settings without losing either:

1. Dial in a sound you like. Click **Snap A** — the current state of all channels is frozen as snapshot A.
2. Tweak further. Click **Snap B** — current state frozen as B.
3. **Toggle A/B** — instantly swaps between the two states. The tracker, workshop, and mixer all update to reflect whichever snapshot is active.

Snapshots are session-only; they are not saved to disk.

---

## File menu

| Item | What it does |
|------|--------------|
| **New project** | Resets to the default 3-channel starter project (kick / hat / bass) |
| **Open Tracker project…** | Loads a `.json` file saved by Forge (schema version 3.0) |
| **Save Tracker project…** | Saves the current doc as a `.json` file |
| **Open Engine project…** | Loads a legacy Plan 2 project (the older non-tracker format) |
| **Save Engine project…** | Saves a currently loaded legacy project back to disk |
| **Export WAV…** | Renders the full track (all sections, all channels) to a stereo 44.1 kHz WAV |

**Tracker project vs Engine project:** The tracker project (`schema_version: 3.0`) is the new format — it stores channels, step patterns, instrument params, and sections as first-class objects and is the format you should use for new work. The engine project is the older Plan 2 format (a flat schedule of tracks and sections), kept for loading legacy files. When you open a legacy file, Forge migrates it in memory to the 3.0 format; save it as a Tracker project to keep it in the new format going forward.

### Autosave

A background autosave writes to `{tmpdir}/forge_autosave.json` every 10 seconds. If the application crashes you can recover by opening that file.

---

## What is not yet built

- **Waveform / equalizer timeline view** — a scrolling view showing rendered audio across the arrangement. The scheduler and cache are in place; the widget to draw it is not.
- **Add / remove channels from the GUI** — currently channels are fixed at whatever is in the loaded doc.
- **Undo/redo keyboard shortcuts** — the transaction history exists in the document model but Ctrl+Z is not yet wired to the window.
- **MIDI input / export**
- **Per-section pattern variations** — patterns currently loop the same 16 steps across all sections.
