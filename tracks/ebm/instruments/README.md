# The EBM instrument library — tracks/ebm/instruments/

A library of single sounds for 1993-flavoured EBM (blueprints:
`../../../inspiration/EBM_1990s.md` and `Apop_Soli_Deo_Gloria.md`).
Each module is one instrument: plain functions that return ONE event as
a mono float array (peak 1.0, 44100 Hz), plus a `__main__` that renders
an audition WAV.  Built by ear, one sound at a time, before any track.

**This directory IMPORTS.**  A deliberate departure (2026-09-05) from the
copy-don't-import rule of `../../dune` and `../../trance`: a future track
script does

```python
sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
from sh101_bass import note, render_cell, CELLS
from eps_kick import kick
```

and places the clips with its own `add_at()` into its layer buffers ahead
of its `commit()` — the same contract as `make_kick()` / `bass_note()`
in every generate_*.py.  The bus (weights, pump, reverb, master) stays
in the track script; nothing here is stereo, reverbed or mastered.

## Running

```bash
cd tracks/ebm/instruments
python3 sh101_bass.py              # -> /workspace/music/ebm/instruments/sh101_bass.wav
python3 juno.py --out /tmp/x.wav   # the only flag
python3 demo_groove.py             # the engine together, 8 bars
```

Every audition = isolated hits at several settings (with gaps), then
the instrument's typical 2-bar loop; long ones print a timeline
(`  20.00s  strings PWM Am`).  Each `__main__` asserts peak, length and
finiteness — that is the module's check.  Audition WAVs are ephemeral
and overwritten; the demo WAVs are kept (never overwrite a demo the
user has listened to — new demos get new names).

## Conventions

- **Grid:** `_common.BPM = 122` (the *Soli Deo Gloria* slam), `STEP` = a
  16th, `BAR`; `place(buf, x, step)` on the grid, `add_at(buf, x, s)` in
  seconds.  Known gap: the tempo is fixed at import — a 147 or 109 track
  needs a `set_tempo()` with the helpers reading it live (do it when that
  track starts).
- **Register:** bass root **A2** (midi 45) — the SH-101 sub-octave then
  sits at 55 Hz; at A1 it lands at 27 Hz and eats headroom (measured).
- **Dirt:** `_common.dirt(x, hold, bits, lowpass)` = the Ensoniq EPS:
  zero-order-hold decimation (`hold=2` ≈ a 22 kHz sample, 3 ≈ 15 kHz),
  13-bit quantise, optional lowpass.  Sampled things default `hold=2`
  (drums, bass, hit uses 3); analog things default `hold=1` (Juno, 808,
  guitar).
- **Caching:** `note`, `voice`, `hit`, `chug`, `bark` and the 808 hits are
  `lru_cache`d — pass tuples, never modify a returned array.
- **Randomness:** one shared `_common.rng` (seed 1993); a track calls
  `_common.seed(n)` once.  Noise-based hits differ per call — render once,
  place many (as the track scripts do with `KICK = make_kick()`).
- **Style:** the repo Python style guide (`../../../CLAUDE.md`).

## The instruments

| module | functions | character | key knobs |
|---|---|---|---|
| `sh101_bass.py` | `note`, `render_cell`, `CELLS`, `svf_lowpass` | THE engine: saw + sub-octave square, resonant SVF with a filter-envelope pluck, hard gate, dirt. Cells: stomp, gallop, offbeat, rolling, riff | `cutoff=(open, floor)`, `env`, `res` (2.5 = the declared bite), `sub`, `wave`, `gate_frac` |
| `eps_kick.py` | `kick`, `loop` | 909-family pitch dive driven hard, truncated, decimated; no sub layer (the 101 owns the low end) | `f_start/f_end/sweep`, `decay`, `drive`, `cut` |
| `eps_snare.py` | `snare`, `loop` | the 2-and-4 slam: two head modes, wires, a plate tail cut dead by the gate; a GROOVE instrument (tech_noir's slam is punctuation) | `tone` (body vs wires), `plate`, `cut`, `snap`, `drive` |
| `hats.py` | `hat`, `carpet` | closed/open, mono, the hold=2 fold-down is the EPS hat | `decay`, `hp`, accent cell, `open_steps` |
| `juno.py` | `voice` + presets `pad`, `strings`, `stab`, `organ`, `brass`, `bass`, `lead`, `zap`, `noise_sweep`; `arp`, `stab_loop`, `pad_loop`, `bass_loop`; `chorus` | the Juno-60: saw/square/pulse/PWM + sub + noise, 24 dB SVF (pluck, bloom `fatt`, `sweep`, key `track`), 4-position `hpf`, delayed `vib`, chorus I/II/I+II, arpeggiator up/down/updown/random | see `voice()` docstring; presets are dicts of it |
| `eps_hit.py` | `hit`, `loop` | the chopped orchestral / choir stab (`kind="orch"|"choir"`), hold=3 | `chord`, `dur` (the truncation), `decay` |
| `bark.py` | `bark`, `chant`, `VOWELS` | the harsh-vocal slot, instrumental: consonant onset, morphing formants, falling pitch, fry rasp, distortion, gate | `vowel/vowel2`, `onset` k/d/s, `fall`, `rasp`, `drive` |
| `kit808.py` | `kick`, `snare`, `hat`, `clap`, `cowbell`, `rim`, `clave`, `maracas`, `tom`, `pattern`, `PATTERN` | the TR-808 for interludes/bookends; six-square-wave metal, analog-clean by default | kick `decay/tone`, snare `snappy`, `hold` |
| `seethe.py` | `seethe` | the Stitch bed: pink-tilted noise through a slowly swept resonant LP, sub with a slow beat, grit pulse, breath, optional 8th-note `throb`; a long bed, not an event | `sweep`, `rate`, `res`, `sub`, `grit`, `throb` |
| `riff.py` | `chug`, `riff` | the one guitar: Karplus-Strong power chord, double-tracked, palm-mute or open, tanh amp, cab, body thump. A texture, one track only (declared) | `drive`, `mute`, `body`, `cab`, cell with x/b/3/5/o |

`_common.py` — SR, BPM/STEP/BAR, `midi_to_hz`, `norm`, `dirt`, `gate`,
`bp_noise`/`hp_noise`, `steps_buffer`, `place`/`add_at`, `seed`,
`write_wav`, `audition`, `out_arg`.  The one shared file; keep it small.

## The demos (context, by ear)

| script → wav | what it proves |
|---|---|
| `demo_groove.py` | the engine: kick + slam + hats + SH-101, stomp then gallop, 8 bars. **The listen-test keeper — do not overwrite** |
| `demo_colour.py` | + Juno stabs (verse quiet / chorus up), pad bed, one orchestral hit |
| `demo_bark.py` | + barks: one per bar, then the chant cell |
| `demo_arp808.py` | the *Arp (808 Edit)* archetype: 808 pattern under a Juno updown arp + pad |
| `demo_seethe.py` | the *Stitch* archetype: half-time, slam on 3, seethe bed, cluster pad, low barks |
| `demo_riff.py` | the *Burnin' Heretic* archetype: chugs as texture from bar 5, open chord last |

Raw on purpose: no reverb, no sidechain, no master — those are the track's.

A/B and stem workflow for the track scripts: `../LISTENING.md`.

## Declared exceptions (argue them in the track's notes doc)

1. Bass resonance Q 2.5 above the warmth recipe's 1.2 — guardrails: the
   cutoff always moves (the envelope), `tanh(1.0)`, a sub for body.
2. The snare as a continuous groove element with a gated plate (the only
   reverb on a drum).
3. The riff: one track only, as a stab, never the lead.
4. This directory imports (see top).

## Verdicts so far (2026-09-05)

- SH-101 bass: keeper.  Juno: keeper, "great potential".  demo_groove:
  keeper.  Everything after the Juno is awaiting a listen.
- TR-08 one-shots, when recorded into `/workspace/music/refs/tr08/`, are
  the calibration targets for `kit808.py` — reference only, never sampled
  into a track.
