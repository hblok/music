# Music system — ideas for later

## 1. Opus conversion (immediate win)

Add an ffmpeg conversion step to each generator script so a `.opus` file is
written alongside the `.wav`. ~98% size reduction, no audible quality loss
in a game context.

```python
import subprocess
subprocess.run(["ffmpeg", "-i", "arrakis_winds_v2.wav",
                "-c:a", "libopus", "-b:a", "96k",
                "arrakis_winds_v2.opus"])
```

Browser support: all modern browsers. Opus at 96 kbps sounds better than
MP3 at 128 kbps. Good first step before tackling Web Audio API.

Other compressed formats for reference:

| Format     | ~Size (from 35 MB WAV) | Browser support        | Notes               |
|------------|------------------------|------------------------|---------------------|
| Opus       | 1–2 MB @ 96 kbps       | All modern             | Best choice         |
| OGG Vorbis | 3–4 MB @ 128 kbps      | All except old Safari  | Fallback for Opus   |
| MP3        | 4–5 MB @ 128 kbps      | Universal              | Widest compat       |
| AAC        | 3–4 MB                 | Universal              | Apple ecosystem     |

MIDI and tracker formats (MOD/XM/IT) are not suitable: MIDI has no concept
of noise, drones or Karplus-Strong synthesis; tracker formats could carry
the darbuka/oud samples but not the wind/ambient layers, and would require
a separate in-browser player (e.g. libopenmpt-wasm).

---

## 2. Web Audio API port (right long-term answer)

Since every track is 100% procedural math, it can be ported to JavaScript
and generated at runtime in the browser — zero audio files, zero download,
music that responds to game state in real time.

The Web Audio API has direct equivalents for everything we use:

| Python (numpy/scipy)              | Web Audio API                        |
|-----------------------------------|--------------------------------------|
| `signal.butter` + `sosfilt`       | `BiquadFilterNode`                   |
| `np.sin(2π·f·t)` (oscillator)     | `OscillatorNode`                     |
| `rng.standard_normal` (noise)     | `AudioBufferSourceNode` + noise buf  |
| `signal.fftconvolve` (reverb)     | `ConvolverNode`                      |
| Karplus-Strong (oud)              | `DelayNode` + `GainNode` feedback    |
| `slow_noise` LFO envelopes        | `LFONode` / `AudioParam` automation  |

[Tone.js](https://tonejs.github.io/) wraps the Web Audio API and makes this
significantly easier to write — recommended starting point.

### Suggested porting order

1. **`generate_arrakis.py` first** — simplest track (no beat grid, no
   Karplus-Strong), mostly oscillators + filters + noise. Good proof of
   concept with low complexity.
2. **`generate_ambient.py`** — adds the pad/LFO chord system and echo tails.
3. **`generate_base_attack.py` last** — most complex: step sequencer for the
   maqsum darbuka, Karplus-Strong oud, and the battle-state envelope.

### Dynamic game-state integration (the real payoff)

Once in Web Audio API, the music can respond to game events in real time:

- **Worm approaching**: increase rumble layer volume, slow gust LFO rate.
- **Battle intensity**: speed up the maqsum BPM, increase explosion density,
  raise the darbuka sub-kick gain — all driven by unit counts or proximity.
- **Base destroyed**: cut the groove instantly (already designed this way),
  let wind + drone play the aftermath.
- **Victory / silence**: crossfade to `arrakis_winds` by smoothly fading the
  darbuka and oud, leaving only the ambient layers.

The battle track's maqsum is a natural step-sequencer node graph: a JS
`setInterval` or `AudioContext.currentTime`-scheduled loop that fires
darbuka hits, with BPM exposed as a parameter the game engine can write to.

---

## 3. Other future track ideas

- **Harvester at work** — slower, mechanical pulse (like a combine harvester
  rhythm); distant; the drone shifts to a lower pitch as the machine digs.
- **Victory / stillness after battle** — very sparse; a single duduk phrase
  over the wind; no rhythm; fades to silence.
- **Sandstorm** — the wind layer taken to an extreme: a dense, highpassed
  wall of noise with fast amplitude modulation (flutter), no tonal content
  at all; 30–60 second loop.
- **Palace / interior** — move away from Phrygian dominant; try Hijaz Kar
  (D Eb F# G Ab B C) for a more ornate, interior-world sound; ney flute
  rather than duduk timbre; more reverb, less wind.

Shortlisted next (full write-ups in `more_ideas.md`):

- ~~**Kwisatz Haderach** (B1)~~ — DONE (`generate_kwisatz_haderach.py`).
- **Spice Agony (Reverend Mother Mix)** (B2) — downtempo dub-psy, ~85 BPM;
  half-time kick, tape-echo skanks, one 303 note per bar with full-bar sweeps.
- ~~**Litany Against Fear** (B4)~~ — DONE (`generate_litany_against_fear.py`,
  design notes in `litany_against_fear_notes.md`).
- ~~**Gurney's Song** (C2)~~ — DONE (`generate_gurneys_song.py`, design
  notes in `gurneys_song_notes.md`).
