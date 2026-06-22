# CLAUDE.md — forge/instruments/

Quick reference for the instrument layer so you don't have to re-read every
module. See `../CLAUDE.md` for engine-wide architecture.

**An instrument is a pure function** `(params, rng) -> AudioBuffer`. The
registry (`registry.py`) is the single source of truth for discovery; the GUI
auto-builds sliders from each instrument's `ParamSchema` list; the control
facade dispatches `render_instrument` through it.

---

## The protocol

```python
def make_x(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
    sr = ctx.get("sr", 44100)
    val = float(params.get("val", DEFAULT))   # always .get with a default
    ...
    return AudioBuffer.from_mono(sig, sr=sr)   # or from_stereo(L, R, sr=sr)
```

**Non-obvious rules (these bite):**

- `rng` is a **`np.random.Generator`**, *not* an `RngContext`. Call sites pass
  `rng_ctx.spawn("some-key").rng`. Inside the instrument just use
  `rng.standard_normal(n)`, `rng.uniform(...)`, etc.
- **Determinism:** the `RenderCache` key is `(instrument_id, params)` and
  ignores `rng` — so identical params must give identical output. All
  randomness must flow from `rng`; the caller guarantees a stable stream by
  spawning a fixed key.
- **Never raise on a missing key.** Read every param with
  `params.get(name, default)`, falling back to the schema default.
- **Gain-stage politely.** Peak-normalise (or keep peak ≲ 1.0) before
  returning; `MixBus.commit` / `master()` do final level. Don't return hot
  buffers — one loud instrument steals everyone's headroom.
- **Reuse `core/`** — `core.dsp` (`lowpass`/`bandpass`/`highpass`,
  `midi_to_hz`, `glide_curve`, `warm_partials`, `raised_cosine_attack`,
  `slow_noise`, `sine_phase`) and `core.reverb`. Don't hand-roll filters.

### Three buffer shapes

| Shape | Length is set by | Examples |
|-------|------------------|----------|
| **hit / note** | params only (fixed); cached | all percussion, fx, single notes (`ney`, `piano`, `bass`, `oud`…) |
| **phrase** | `sum(dur for _, dur in params["notes"])` | `voice`, `cello`, `lead`, `horn`, `sax` |
| **chord** | `params["duration"]` | `pad`, `choir`, `tremolo_strings` |
| **texture** | `int(ctx["duration"] * sr)` | `wind`, `drone`, `swell`, `worm_rumble`, `shepard_wind`, `breath` |

Phrase/note instruments take MIDI numbers (`midi_to_hz`). `notes` /
`midi_notes` list params use `ParamSchema(kind="choice", default=[...])`.

---

## Module → family map

One file per coherent family. Families currently in `REGISTRY`:
`texture, percussion, strings, voice, reed, bass, fx`.

| Module | Family | Instruments (registry id → callable) |
|--------|--------|--------------------------------------|
| `textures.py` | texture | `wind` `drone` `swell` `worm_rumble` `shepard_wind` `breath` |
| `percussion.py` | percussion | `doum` `tek` `kick` `hat` `clap` `snare` `war_drum` `frame_hit` `frame_roll` `tick` `clock` `anvil` `slam` `tap` |
| `strings.py` | strings | `harp`(karplus_strong) `piano`(piano_note) `cello`(cello_line) `pad`(pad_chord) `tremolo_strings` `santur` `oud` |
| `voices.py` | voice | `voice`(voice_phrase, duduk) `choir` `lead`(lead_phrase) `ney`(make_ney) `chant`(make_chant) `horn`(make_horn) |
| `reed.py` | reed | `sax`(sax_phrase, alto saxophone) |
| `bass.py` | bass | `bass`(bass_note) `psy_bass`(psy_bass_note) `acid`(acid_note) |
| `fx.py` | fx | `zap` `riser` `explosion` `heart` `rev_cymbal` `boom` `sub_boom` `machine_chug` `thopter` |

### Catalogue (id — shape, channels — character)

**texture** — all `texture` shape, mono unless noted:
`wind` filtered-noise wind band · `drone` layered detuned-partial bed (note the
beat-tone gotcha in `../../ambient/CLAUDE.md`) · `swell` slow rising
noise/tone · `worm_rumble` deep sub rumble · `shepard_wind` endless-rising
Shepard wind · `breath` breathy air.

**percussion** — all hit, mono: `doum`/`tek` darbuka low/rim · `kick`
pitch-swept synth kick · `hat` hi-hat (`open_` bool) · `clap` layered noise ·
`snare` · `war_drum` deep tom · `frame_hit`/`frame_roll` frame drum · `tick`
`clock` `anvil` `slam` `tap`.

**strings**: `harp` KS pluck (note) · `piano` felt/inharmonic (note) · `cello`
bowed phrase (phrase) · `pad` detuned-saw chord (chord, **stereo**) ·
`tremolo_strings` flickering section (chord, **stereo**) · `santur` hammered
dulcimer 2-course KS (note) · `oud` double-course lute + body BP (note).

**voice**: `voice` duduk additive phrase (phrase) · `choir` vowel-formant pad
(chord, **stereo**) · `lead` detuned-saw trance lead (phrase, **stereo**) ·
`ney` breathy flute (note) · `chant` Sardaukar throat (note) · `horn`
carnyx/war horn brass (phrase or single midi+duration).

**reed**: `sax` alto saxophone — reed-buzz harmonics through an `iirpeak` body
formant, per-note tonguing, delayed vibrato bloom (phrase or single
midi+duration). Modelled on `../../inspiration/black_box/intro_report.md`.

**bass**: `bass` warm saw (note) · `psy_bass` pitch-falling psy (note) ·
`acid` 303-style (note).

**fx**: `zap` `riser` (build) `explosion` `heart` (beat) `rev_cymbal` (reverse
swell) `boom` `sub_boom` `machine_chug` `thopter` (rotor).

---

## ParamSchema

```python
ParamSchema(name, kind, default, lo=None, hi=None, choices=None, label=None, unit=None)
```

- `kind`: `"float" | "int" | "bool" | "choice"`.
- **Floats must set `lo`/`hi`** — the GUI builds sliders from them and a test
  enforces it (`*_slider_buildable`).
- List/tuple params (`notes`, `midi_notes`) use `kind="choice"` with the list
  as `default` (see `sax`/`cello`/`pad`).
- `label` and `unit` (`"Hz"`, `"s"`, `"dB"`) are display-only.

---

## Adding a new instrument

1. **Pick the module** by family (or create one — see below). Add the callable
   `make_<name>(params, rng, **ctx)` and a `<NAME>_PARAMS = [ParamSchema(...)]`
   list next to it.
2. **Register it** in `registry.py`: add the import, then a line under the
   matching family block:
   `"my_id": _entry(make_my, MY_PARAMS, "family"),`
3. **Test it** in `forge/tests/test_instruments.py` — at minimum: in-registry
   with correct family, non-silent + all-finite, slider-buildable, plus one
   behavioural check. Run `python3 -m unittest forge.tests.test_instruments`.
4. **Update the catalogue table above.**

### When to add a new module / reorganise

- One file per coherent family. If the new instrument doesn't fit an existing
  family, create `<family>.py` and a new family string — that's exactly why
  `reed.py` exists (the saxophone is a reed aerophone, not a "voice").
- **Historical wrinkle:** `voices.py` is a catch-all melodic file holding true
  voices (`choir`, `chant`), a wind (`ney`), brass (`horn`) and a synth `lead`.
  Prefer routing *new* winds/brass/reeds to dedicated modules rather than
  growing `voices.py`. Don't bulk-move existing instruments without a real
  reason — it churns the `registry.py` imports and the tests for no listener
  benefit.

The `test_all_families_present` test uses `assertIn`, so adding a family is
safe; there is no hard-coded instrument count to update.
