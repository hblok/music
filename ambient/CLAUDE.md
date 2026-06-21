# CLAUDE.md — ambient/ generators

Implementation guide for the long-form ambient generators in this directory.
The shared **stack, common architecture, and conventions** live in
`../dune/CLAUDE.md` (numpy+scipy only, stdlib `wave` output, everything
synthesized, seeded RNG, `commit()` mix-bus, per-section RMS checks, the
`add_at`/`glide_curve`/`reverb` helpers). Read that first; this file covers
only what is specific to the ambient work.

## Tracks

- **lost** — `lost.py` (v2, ~7:50) → renders `lost_v2.wav` — a long-form
  emotional ambient journey in D: LOVE → CONFUSION → LOSS → DREAD/ANGST →
  SADNESS → HOPE. (A trance reworking of the same journey lives at
  `../trance/lost_v3.py`.)
- **qasida** — `persian.py` (~8 min, 480 s) → renders `/workspace/music/qasida.wav`
  — Persian/Arabic ambient trance in **C Phrygian Dominant** (Maqam Hijaz /
  Dastgah Homayoun: C D♭ E F G A♭ B♭), inspired by the analysis of
  `Persian_Trance_LdGhQaBCbcE.mp3`. 96 BPM, 192 bars. Uses forge instruments
  via `../forge/instruments/`.

## persian.py — structure and design

### Two-part file layout

```
PART 1 — INSTRUMENTS & EFFECTS
  SR, BPM/BAR/STEP constants, section boundaries, MIDI note constants
  IR_ROOM_{L,R}, IR_HALL_{L,R}  — reverb impulse responses
  NEY_PHRASE_{A,B,C,OUTRO}      — ney note lists [(midi, dur_s), ...]
  OUD_PHRASE_{A,B}              — oud overlap lists [(midi, t_off, dur), ...]
  _DOUM_STEPS, _TEK_STEPS, _GHOST_STEPS  — darbuka bar pattern
  _PAD_NOTES, _CHOIR_NOTES, _SANTUR_PITCHES
  render_drone(), render_wind(), render_pad(), render_choir()
  render_ney(), render_oud_phrase(), render_santur_run()
  render_bass_hit(), render_darbuka_bar()

PART 2 — COMPOSITION
  compose(seed)  — builds the AudioBuffer; all placement here
  main()         — writes /workspace/music/qasida.wav
```

### Section arc (192 bars = 480 s at 96 BPM)

| Section  | Range        | Content |
|----------|-------------|---------|
| INTRO    | 0–80 s       | Drone fades in; silence above it |
| RISE     | 80–160 s     | Wind enters; darbuka and bass begin; first ney |
| BUILD    | 160–240 s    | Choir swells appear; oud phrases start |
| PEAK     | 240–400 s    | Santur runs added; all layers full |
| UNWIND   | 400–460 s    | Gradual thinning; percussion fades |
| OUTRO    | 460–480 s    | Solo ney farewell phrase; drone fades |

### Instrument choices and reverb rules

- **Drone** (`forge.instruments.textures.drone`) — C2 root, full track, no reverb
- **Wind** (`textures.wind`) — RISE to OUTRO, no reverb (already diffuse)
- **Pad chord** (`strings.pad_chord`) — C4/G4/Bb4, no reverb (too long for FFT)
- **Choir** (`voices.choir`) — hall reverb IR (2.5 s / 2.0 decay); 45 s swells
- **Ney** (`voices.voice_phrase` with `ney_mode=True`) — room reverb (1.8 s / 1.4 decay)
- **Oud** (`strings.oud`) — overlapping notes assembled manually; room reverb
- **Santur** (`strings.santur`) — ascending run, staggered 0.35 s per note; room reverb
- **Bass** (`bass.psy_bass_note`) — C2/G2 hits on beats 0 and 8; no reverb
- **Darbuka** (`percussion.make_doum` + `make_tek`) — Maqsum pattern, humanised ±10 ms

### Reverb note
`reverb(x, ir, wet)` trims the convolution result to `len(x)`, so the reverb
tail is lost. Pad the input with zeros before calling to capture the ring-out:
```python
padded = np.concatenate([mono, np.zeros(int(tail_s * SR))])
out = reverb(padded, IR_ROOM_L, wet=0.38)[:len(mono)]
```

### Analysis source
`/repos/music/inspiration/Persian_Trance_LdGhQaBCbcE_inspector/analysis_notes.md`

## The three composition lessons (from user feedback — read before editing)

These shaped lost.py v2 and are the heart of the ambient brief:

1. **Interlocking instruments, NOT a lone flute.** The piece must be carried
   by *counterpoint between many voices*, not one melody line over a bed. A
   felt piano runs evolving arpeggios; a Karplus harp answers **an eighth
   behind** (the literal interlock — see `harp_offset`); a bowed cello
   carries bass and laments; choir, glockenspiel and bells colour; the
   **flute is one voice among many**, never the soloist. When adding material,
   add an answering voice, not a louder lead.
2. **A conceptual reference is rendered as TEXTURE, not literal SFX.** The
   "Scream" section is *Munch's painting*, not a scream sound — existential
   dread built from a slow tolling bell, swirling dissonant detuned string
   clusters (`swell`), a relentless dark piano ostinato that **will not
   resolve**, a polytonal choir, and a sub rumble that swells and recedes
   *like the painting's undulating sky*. It builds in density, never screams,
   then dissolves. Resist any urge to drop in a literal sound effect.
3. **The heartbeat is the through-line and is AUDIBLE.** `heart()` runs under
   the whole arc as the spine — full and present, not a subliminal tick.

## Instrument recipes

- **Felt piano** (`piano`): stretched-inharmonic partials
  (`fk = f·k·sqrt(1+B·k²)`), `1/k**1.3` gains, **two detuned strings** per
  note (±0.03 %), a soft felt hammer-thunk, warm lowpass. Cached per pitch.
  This is the lead storyteller — runs the evolving arpeggio patterns.
- **Harp** (`harp`): Karplus-Strong with a warm (smoothed) pick excitation,
  `damp ≈ 0.9955`, cached per pitch. Placed by `harp_offset` an eighth behind
  the piano = the interlocking counterpoint (lesson 1).
- **Bowed cello** (`cello` / `cello_line`): detuned additive saw
  (±0.15 %, `1/k`) + bandpassed bow noise, vibrato, slow bow attack. Carries
  the bass pedal in love/confusion/hope and the falling laments in loss/sad.
- **Flute / ney** (`flute`): nearly pure (low harmonics) + ~8 % breath noise
  riding the envelope, blooming vibrato (~0.4 %), lowpass ~2.8 kHz. Airy,
  floating — and deliberately **just one of the voices**.
- **Choir "ooh/ah"** (`choir`): a `1/k**0.9` glottal source through vowel
  **formant** bandpasses (oo: 320/800/2700 Hz with falling gains; brighter
  "ah" for the dread cluster), multiple detuned notes. Polytonal stacking is
  what makes the dread choir read as anguish.
- **Bells / glockenspiel / tolling bell** (`bell`): inharmonic damped sines
  specified as `(ratio, gain, decay)` tuples — sparkle in hope, the slow toll
  in dread, from the same generator at different registers/decays.
- **Dissonant string swell** (`swell`): detuned cluster (±0.6 %) additive saw
  under a slow tremolo — the swirling Munch texture; minor-second / polytonal
  voicings carry the tension without ever resolving.

## Harmonic arc

D throughout, moving **major → ambiguous → minor → dissonance → major**:
love on Dmaj9–Bm7–G6/9–A7sus; confusion via **chromatic-mediant** harmony
(D–F–Bb–Eb–A7b9) with two voices drifting out of phase; loss drops to D
minor (piano thins to slow chords, cello laments, rain); dread is the
unresolving cluster; sadness is bare aftermath; hope reprises the love
arpeggio reborn in major and fuller. Nature (wind throughout, rain in
loss/dread, stream + birds in hope) frames the scenes — also texture, placed
as events, never the subject.

## Long-form / shared rules

- **Anti-tinnitus** (from `../dune/CLAUDE.md`): any sustained HF tonal element
  must pulse to true silence or fade within ~1 min — applies to bells,
  glock, the choir top.
- **Commit-as-you-go**: for ~8 min of float64 layers, normalize each layer
  and `commit()` it into the mix bus immediately rather than keeping every
  layer alive.
- **Verify with per-section RMS**, and watch the sustained-sub trap: cello
  pedals and the choir carry far more energy than they peak — keep their
  weights modest so quiet scenes don't out-weigh the climax.

## Conventions

Same as `../dune/CLAUDE.md`: one standalone script per track (duplicate
helpers); **revisions get a new WAV name** (`lost_v2.wav`) — never overwrite
a WAV the user has heard; print event times at the end; scripts tracked in
git, generated WAVs go to `/workspace/music/` and are **never committed**;
**stage but do not commit or push without being asked.**
