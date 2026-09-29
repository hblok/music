# The Dune instrument library -- tracks/dune/instruments/

A library of single sounds extracted from the 20+ `generate_*.py` tracks
in `../`. Each module is one instrument family: plain functions that
return ONE event as a mono (or, for the wide ambient/choir pieces, a
stereo `(L, R)`) float array at 44100 Hz, plus a `__main__` audition that
renders a demo WAV and asserts peak/finiteness.

**This directory IMPORTS** -- the same deliberate departure (2026-09-05,
`tracks/ebm/instruments`) from the "copy, don't import" rule that every
`tracks/dune/generate_*.py` script itself still follows (see
`../CLAUDE.md`). **No existing track script was modified to build this
library.** Every function here was extracted (copied verbatim, or
reconciled from near-identical duplicates -- see each module's docstring
for the exact source-script pointers) from the 20+ generators; the
generators remain untouched, standalone, self-contained files exactly as
before. A *new* track can now do:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "instruments"))
from kick import trance_kick, kick_stack
from darbuka import make_doum, make_tek
```

and place clips with its own `add_at()` into its own layer buffers ahead
of its own `commit()` -- the same contract every `make_*()` / `*_note()`
helper already has in the generators. The bus (weights, reverb,
sidechain, master) stays in the track script; nothing here is
stereo-panned, reverbed or mastered except the handful of functions that
say so explicitly (mostly the choir/mass-vocal/FM-lead stereo pairs).

## Running

```bash
cd tracks/dune/instruments
python3 kick.py                 # -> auditions/kick.wav
python3 acid.py --out /tmp/x.wav
```

Every module's `__main__` renders isolated hits/phrases (with gaps
between them) into `auditions/<module>.wav`, then asserts every returned
array's peak is close to 1.0 (a few multi-harmonic voice/pad functions
that don't self-normalize in the source scripts are asserted with a
looser bound, noted in-line) and is fully finite. `auditions/` is
scratch output, safe to delete/regenerate; it is not meant to be
committed as "content", just as a smoke test artifact.

## How the survey was done

`tracks/dune/*.py` was walked (excluding the TTS voice-line pipeline
scripts `generate_voice_*.py` / `generate_game_voices.py` /
`generate_samples*.py`, which are a separate subsystem) and every
top-level function definition was grouped by name and hashed, to find
which "same-named" functions across files are byte-identical, which are
near-identical tuning variants, and which are one-offs. That survey is
the source of truth for every "identical in X / variant in Y" claim in
the module docstrings below -- nothing here is a guess from reading two
files side by side.

## Conventions

- **No baked-in tempo.** Unlike `tracks/ebm/instruments` (fixed 122 BPM
  grid), the dune tracks each set their own tempo, so every function
  here takes an explicit `dur` (seconds) rather than reading a
  module-level `BPM`/`STEP`. `_common.BPM`/`STEP`/`BEAT`/`BAR` exist only
  as a reference tempo for each module's own audition demo.
- **Contract:** a function returns ONE rendered event, peak-normalized to
  1.0 (`_common.norm`), at `_common.SR` (44100 Hz) -- mono, except the
  handful of functions whose source scripts return a stereo `(L, R)`
  pair directly (documented per-function: `mass_chant_note`,
  `mass_chant`, `fm_lead_note`, and the `gallop_pattern`/`place_*` helpers
  that write into caller-supplied stereo buffers).
- **Determinism:** every module seeds its own
  `rng = np.random.default_rng(...)` at import time, using the same
  thematic seed the majority-source track used (1965 = kanly/base_attack,
  10191 = water_of_life/fall_of_arrakeen, 1993 = sihaya, 2001 = the
  navigator...). Two calls to a cached function (`oud_note`,
  `baliset_note`, `acid_note`, `sing_phrase`, ...) return the identical
  array; two calls to an uncached noise-based one (`make_tek`,
  `chant_note`, ...) differ, exactly as in the source scripts -- render
  once, place many.
- **Caching:** pitched/filtered voices that are called hundreds of times
  per track (acid, bass, oud, baliset, choir, sung voice) memoize into a
  private module-level dict keyed on the same rounded parameters the
  source scripts use -- keep the cache if you extend one of these
  functions.
- **Fidelity over polish:** where a source function's output legitimately
  peaks a little over 1.0 before the track's own mix-bus gain stage
  brings it back down (e.g. `chant_note`/`sing_phrase`'s harmonic
  stacking), this library reproduces that exactly rather than adding a
  normalization the original never had -- the affected modules'
  auditions use a documented, looser assertion bound instead of silently
  "fixing" the recipe.
- **Style:** the repo Python style guide (`../../../CLAUDE.md`) --
  pathlib, `unittest` (not used here; auditions use plain asserts,
  matching the ebm/trance instrument libraries), explicit imports.

## The instruments

| module | functions | character | key knobs |
|---|---|---|---|
| `kick.py` | `trance_kick`, `kick_stack`, `sub_boom`, `driven_kick` | The four kick families: the 140-145 BPM trance kick (`generate_water_of_life.py`), the war-psy room-shake stack + its dedicated sub-boom layer (`generate_fall_of_arrakeen.py`), and spice_agony's doubly-tanh-driven deep kick | `f0/f1/sweep/decay`, `click_gain`, `click_bp`, `sub_f0/f1/sweep`, `drive1/drive2` |
| `darbuka.py` | `make_doum`, `make_tek`, `MAQSUM`, `place_maqsum_bar` | The doumbek/darbuka hand-drum pair (deep resonant doum + bright rimshot-y tek) and the classic maqsum rhythm cell | `ghost`, `band`, `ping_hz`, `dur` |
| `drums.py` | `war_drum`, `tom`, `hat`, `snare`, `snare_march_bar`, `MARCH`, `clap`, `shaker` | The Western drum-kit elements shared across the war-psy tracks: low tuned war drum, melodic tom, closed/open hat, field snare (+ its march pattern with a buzz-roll accent), clap, shaker | `f0/f1/sweep`, `skin_band`, `open_`, `buzz` |
| `frame_drum.py` | `frame_hit`, `frame_roll` | The wide, soft frame-drum (bendir/riq-family) hit and its accelerating roll | `rate0/rate1`, `gain0/gain1` |
| `tick_clock.py` | `tick`, `clock_pattern` | The bone-dry alternating tick(left)/tock(right) ostinato -- the "John Wick clock" constant under night_pursuit/kanly/maker_comes | `tock`, `ping_gain`, `click_decay`, `ping_decay` |
| `hoofbeat.py` | `hoof`, `gallop_pattern` | Kanly's galloping steed/worm-rider hoofbeats: pitched thump + dust burst, alternating lead/trail L/R pan for the gait | `lead`, `cells`, `pan_lead` |
| `bass.py` | `bass_note`, `bass_note_agony`, `psy_bass_note` | The gated sub/bass family: the plain two-harmonic saturated bass (kanly/maker_comes/night_pursuit/muaddib/sihaya/stillsuit), spice_agony's darker driven variant, and the rolling 20-harmonic psy-bass engine (fall_of_arrakeen/kwisatz_haderach/sleeper_awakens/the_navigator/jihad) | `dur` (gate length), harmonics baked in per function |
| `acid.py` | `acid_note`, `acid_note_jihad`, `acid_note_simple` | The TB-303-style resonant acid line: canonical dual bright/dark filter + `iirpeak` resonance + optional slide, jihad's harder-edged reimplementation, and water_of_life's simpler single-filter variant | `cutoff`, `accent`, `slide_to`, `dur` |
| `fx.py` | `zap`, `riser`, `rev_cymbal`, `tremolo_strings` | Shared transition/atmosphere FX: laser zap (+ jihad's faster variant), 10-band noise-sweep riser (+ jihad's linear-sweep variant), reverse cymbal swell (+ jihad's faster decay), detuned tremolo string pad (+ jihad's variant) | `fast`, `style="jihad"`, `decay`, `chord`, `trem_hz` |
| `choir.py` | `chant_note`, `chant_note_simple`, `chant_note_choir`, `mass_chant_note`, `mass_chant` | The Sardaukar/Fremen throat-chant choir: single-voice glottal-harmonic chant through dark formants (3 variants across tracks), stacked into a detuned/jittered 12-voice mass choir (2 variants: kwisatz_haderach/jihad's tremolo version vs sihaya/muaddib's plain version) | `pulse`, `scatter`, `voices` |
| `duduk_ney.py` | `voice_phrase`, `ney_phrase`, `place_voice` | The melodic wind voice for every duduk/ney phrase: glide+vibrato sine-plus-harmonics tone, warm reedy duduk mode or airy breath-noise ney mode | `ney` flag, `lp` |
| `war_horn.py` | `horn_phrase`, `screamed_horn_phrase`, `place_horn` | The carnyx-style Sardaukar/Fremen war horn: brassy harmonic stack with a pitch scoop and slow growl, plus jihad's more extreme "screamed" scream-formant variant | `growl`, `lp`, `octave`, `distant` |
| `strings.py` | `ks_string`, `oud_note`, `baliset_note`, `render_pluck`, `strum_times`, `santur_note` | Karplus-Strong plucked/struck strings: the low-level string primitive, the double-course oud, the triple-course baliset (Gurney Halleck's instrument, + flageolet "harm" mode), a strum scheduler, and the struck (hammered) santur | `kind="harm"`, `dur`, `damp`, `up` (strum direction) |
| `sung_voice.py` | `sing_phrase`, `sing`, `VOWELS` | Sihaya's Paul/Chani sung-voice engine: glottal source through per-vowel `iirpeak` formants, crossfaded between notes, closed-"m" hum consonant, hum-only wordless mode | `female`, `hum`, `det`, `fs2` |
| `navigator.py` | `fm_lead_note`, `choir_pad`, `arp_pluck`, `tarang_doum`, `gas_bubble`, `stillpoint_hit` | The_navigator-only instruments: 2-op FM lead (bright->warm sweep), pulsed multi-formant ambient choir pad, short FM arp pluck, tuned tabla-tarang "doum", gas-bubble foley blip, long inharmonic-partial stillpoint bell | `idx0/idx1/ratio`, `pulse_hz`, `root_midi` |
| `impact_fx.py` | `explosion`, `explosion_arrakeen`, `worm_rumble`, `anvil` | Big low-end impact/atmosphere FX: brown-noise + sub-sine explosion (2 variants), the sandworm's sub-bass approach rumble, the Sardaukar anvil-strike bell hit | `sub_f`, `dur` |

## Source-script pointers not (yet) covered by a module

A few one-off pieces surfaced by the survey were deliberately left out of
this first pass -- they are either pure arrangement/mixing glue already
covered generically by `_common.py` (`bar_t`, `commit`, `groove_on`,
`acid_bars`, `place_frag`, ...), or full ambient beds (wind/drone/sunrise
shimmer/klaxon) that are closer to "one track's arrangement" than a
reusable discrete instrument. If a future track wants one of these as a
real instrument, the same survey-and-extract approach used here applies;
`../CLAUDE.md` documents each track's full recipe list if you need the
exact source function in the meantime.
