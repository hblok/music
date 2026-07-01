# Gurney's Song — design notes (C2)

Working notes so a fresh session can build `generate_gurneys_song.py`
without re-deriving anything. Spec source: `more_ideas.md` C2.

## Concept

The album's only **performed** piece. Gurney Halleck alone with his
baliset between battles — one instrument, one-take feel, rubato. No wind,
no drone, no beat grid. He plays the album's main theme (THEME_A) as a
song: the same melody the duduk carries in water_of_life and
kwisatz_haderach, now plucked. Intimate close-mic feel: small room, not
cathedral.

- Length ~4:45 (285 s). Nominal pulse 66 BPM but fully rubato.
- Key: D Phrygian dominant (D Eb F# G A Bb C) — album home key.
- Seed: `np.random.default_rng(9)  # nine strings`.
- Output: `/workspace/music/gurneys_song.wav`.

## The instrument (new recipe → CLAUDE.md once proven)

**Baliset** = 9-string, 3 courses × 3 strings. Extend the oud
Karplus-Strong (CLAUDE.md "Oud" entry, `generate_fall_of_arrakeen.py
oud_note` is the best copy source):

- Per note render 3 KS strings at `f·[0.9975, 1.0, 1.0035]`,
  gains `[0.55, 1.0, 0.7]` — triple-course chorus, richer than oud's 2.
- Excitation: noise buffer of one period smoothed by a **3-tap** average
  (between oud's 5-tap warm and santur's 2-tap bright).
- Damp ≈ **0.9955** (longer sustain than oud's 0.992 — solo instrument
  must ring). Bandpass 90–5200 Hz. Cache one render per (midi, damp) —
  plucks are reused constantly.
- **Harmonic/flageolet**: same KS one octave up, damp 0.990, gain 0.5,
  narrower bandpass (200–3000). Used in the bridge.
- **Strum**: chord = list of midis low→high; stagger onsets 12–25 ms
  (down-strum = low first, up-strum reversed), per-string gain jitter
  ±15 %. Slight pan spread across the course (−0.15..+0.15).
- **Body resonance IR**: two damped modes — decaying sines at ~110 Hz
  (τ≈0.12 s) and ~220 Hz (τ≈0.09 s) — summed into a short IR,
  `fftconvolve` onto the dry instrument, mixed in at ~0.18. This is what
  makes it a wooden instrument and not a synth pluck.
- **Room**: short reverb IR ~0.9 s, wet ≈ 0.12 only. Intimate.
- **Performance dirt** (sells "performed"): (a) fret-slide squeak — 60 ms
  highpassed (>2 kHz) noise chirp, gain ~0.05, before large position
  shifts, sparse (p≈0.4); (b) room tone at ~0.015 gain (lowpassed noise)
  so silence is never digital black; (c) one audible breath before the
  final chorus (optional).

## Rubato (the point of the piece)

- Events placed on a nominal 66 BPM grid, then warped:
  `onset += slow_noise(±55 ms)` + **phrase-final ritardando** (last 2
  beats of each 4-bar phrase stretch ×1.15–1.3).
- Velocity = 0.75 + 0.25·slow_noise, accents on phrase downbeats.
- Never quantize: two takes of the same phrase must not align.

## Material

THEME_A (from kwisatz/water, durations in beats here, midi):
`D(62)·2 F#(66)·1 Eb(63)·1 D·2 C(60)·2 D·3 | Eb·1 F#·2 A(69)·2 G(67)·2
F#·1 Eb·1 | D·4 C·2 Eb·2 D·4`

Chords (Phrygian dominant, voiced on open-ish courses D2 A2 D3):
- **D**: 38 50 57 62 66 (D A D F# — the home strum)
- **Eb**: 39 51 58 63 67 (the flat-II shimmer)
- **Cm**: 36 48 55 60 63
- **Gm**: 43 50 58 62 (Bb on top)
- Progression, chorus: `D D Eb D | D Cm D D | Eb Eb D Gm | Cm Eb D D`

## Structure (~285 s)

| t | section | content |
|---|---------|---------|
| 0:00 | tuning | 3–4 open-course plucks, one slide up, a harmonic; he settles |
| 0:25 | verse 1 | fingerpicked THEME_A, low register (62-based), sparse thumb D2 pedal |
| 1:25 | chorus 1 | strummed progression, moderate, down-down-up feel but rubato |
| 2:05 | verse 2 | THEME_A up an octave (74-based) over steady thumb D2/A2 alternation |
| 2:55 | bridge | quietest point: harmonics + free arpeggios on Eb and Cm |
| 3:30 | chorus 2 | biggest strums, melody notes on top of the chords |
| 4:10 | coda | first phrase of THEME_A fragmenting, big ritardando, final D strum rings ~6 s, hand-mute thud, 3 s room tone |

## Build conventions (same as all tracks)

Standalone script, numpy+scipy only, duplicate helpers (midi_to_hz, fade,
slow_noise, make_reverb_ir, add_at). Commit-bus with per-layer peak norm
is overkill here — few layers (instrument, dirt, room tone); simple sum +
gentle `tanh(1.1x)` safety, target RMS ~0.10–0.14 (this is a quiet track,
sits between ambient and groove). Print duration + section RMS at end.
WAV to /workspace/music, stage script in git, don't commit.
