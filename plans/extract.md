# Instruments still to extract

Handover list for another AI. Everything below is **not yet** in an importable
library. Survey date 2026-09-29.

## Already done (don't redo)

- `tracks/ebm/instruments/` — all ebm tracks.
- `tracks/dune/instruments/` — 17 modules from the `generate_*.py` tracks
  (kick, darbuka, drums, frame_drum, tick_clock, hoofbeat, bass, acid, fx, choir,
  duduk_ney, war_horn, strings, sung_voice, navigator, impact_fx).
- `tracks/trance/instruments/*.md` — documentation catalog; the importable
  `.py` library (drums, basses, leads, keys, plucks, pads, textures, voice,
  morgenland, flightpath + `_common`) now exists too (sections 1, 1a, 1b).
- `tracks/psy/instruments/` — sections 2 (leads, bass, pads, drums, fx).
- `tracks/ambient/instruments/` — section 3 (`lost_ambient.py`, `persian.py`;
  persian depends on forge, see its README).
- **Still open:** section 4 (house — needs a user decision) and section 5
  (dune leftovers — only on request).

## Method (copy it, don't reinvent)

Follow `tracks/dune/instruments/README.md` ("How the survey was done") and
`tracks/ebm/instruments/README.md` (conventions):

- One module per instrument family, in `tracks/<genre>/instruments/`.
- Plain functions returning ONE event, mono float array, peak 1.0, 44100 Hz,
  taking explicit `dur` (no baked-in tempo unless the genre has one).
- Copy source code **verbatim** (or reconcile byte-near duplicates); docstring
  names the `script:function` sources. Keep the `lru_cache`/dict caches.
- `__main__` audition renders gaps-separated hits to `auditions/<module>.wav`
  and asserts peak/finiteness. Support `--out`.
- A shared `_common.py` per directory; keep it small.
- **Do not modify the source track scripts.** Imports go one way only.
- After each library, add a module table to that directory's `README.md`.
- Where a track "owns" a sound (see `trance/instruments/README.md`), keep the
  ownership note in the module docstring.

## 1. Trance → `.py` library (highest value)

`tracks/trance/instruments/` has the catalog in `.md` but nothing importable.
Create `.py` modules mirroring the md files: `drums.py`, `basses.py`, `leads.py`,
`keys.py`, `plucks.py`, `pads.py`, `textures.py`, `voice.py` (+ `_common.py`).
The md files already hold the function source and pointers — start there, then
check them against the scripts. Skip entries the catalog marks retired
(~~struck~~: lost_v3 bass, hollow pulse lead, skyline piano, hybrid sung voice).

### 1a. Scripts the catalog does not mention at all

These have **zero** catalog coverage; survey them first, extract what is new.

| script | uncovered functions worth extracting |
|---|---|
| `morgenland.py` / `_v2` / `_v3` | `santur_note`, `santur_trem` (compare with `dune` `santur_note` — likely same lineage; reconcile), `sub_note`, `make_sub_boom`, `make_doum`/`make_tek` (darbuka pair; overlaps `dune/instruments/darbuka.py` — diff, then reuse or fork), `swell`, `pad_chord`, `build_half`/`acid_path` (acid melody grammar — see silver_wire) |
| `flightpath.py` | `bass_stab`, `osc_bar`, `buzz_path`, `cell_timbre`, `hammer_ev`/`chain_ev`/`trill_ev`/`swell_ev` (the bee-run event kinds), `chord_stab`, `wedge`, `make_sub_boom` |
| `farlight.py` (v1) | check `bell_note`, `lead_phrase`, `pluck` vs `farlight_v2` — extract only real differences |
| `nachtkind_v1.py`, `nachtkind_v2.py` | `make_shaker`, `bass_cutoff`, `place_pads`; diff `piano_note`/`lead_phrase`/`make_stab` against v3 |
| `tech_noir_v2.py`, `generate_tech_noir.py` | diff against `tech_noir_v3` (`make_slam`, `make_anvil`, `brass_phrase`); extract only differing voicings |
| `silver_wire.py`, `silver_wire_v3.py` | diff `acid_note` vs v2; v1/v3 may carry other kicks/basses |
| `maschinenherz_v2.py`, `lost_v4.py` | diff only; list what differs |
| `unsung_probe.py` | probe script for the dead-end sung voice — **skip** |

### 1b. Extract-but-cross-reference

`make_kick`, `make_clap`, `make_hat`, `psy_bass_note`, `acid_note` exist in
`dune/instruments/` too. Do **not** copy a second time: diff the trance variant,
and if it is only a tuning difference, add it as a named variant in the trance
module with a docstring pointing to the dune one.

## 2. Psy → new `tracks/psy/instruments/`

Three near-identical scripts (`meridian.py`, `phototaxis.py`, `phototaxis_v2.py`)
with a shared function set. Read `tracks/psy/CLAUDE.md` first.

| module | functions (source) |
|---|---|
| `leads.py` | `lead_note` (meridian), `gurgle_note` (phototaxis, v2 differs — reconcile), `fizz_note`, `glint_note`, `murk_note` |
| `bass.py` | `bass_note` (three variants) |
| `pads.py` | `pad_bed`, `underglow_chord`, `pool_drone` |
| `drums.py` | `goa_kick`, `open_hat`, `closed_hat`, `snare` |
| `fx.py` | `chatter_burst`, `bubble_rise`, `snap` (phototaxis), `tape_flutter`, `harmonic_bloom` (meridian) |
| `_common.py` | `pm_core`, `rc_attack`, `lowpass`/`highpass`, `slow_noise`, `make_reverb_ir` |

Note the layer-writing signature of `chatter_burst`/`bubble_rise`/`tape_flutter`/
`harmonic_bloom` (they take a `layer` + time): convert to return an event
array + offset, like everything else. Say so in the docstring.

## 3. Ambient → new `tracks/ambient/instruments/`

Sources: `persian_opus.py`, `persian.py`, `lost.py`. (`ambient/CLAUDE.md`.)

| module | functions |
|---|---|
| `persian.py` | `render_drone`, `render_air` / `render_wind`, `render_pad`, `render_choir`, `render_ney`, `render_oud_phrase`, `render_santur_run`, `render_bass_hit`, `render_darbuka_bar`, `render_riq_hit` (opus only). Check overlap with `dune` `duduk_ney`, `strings` (oud/santur), `darbuka`, `frame_drum` — reuse/diff first |
| `lost_ambient.py` | `piano`, `harp`, `cello`/`cello_line`, `flute`, `choir`, `bell`, `heart`, `chirp`, `swell`; `feedback_delay` (`generate_ambient.py`) |

The `render_*` functions take a `RngContext` — replace with a module-level
seeded `np.random.default_rng`, matching the dune convention.

## 4. House → decide first

`tracks/house/strike_intro.py`, `strike_variants.py` are a transcription of an
existing record's intro (brass stab chord + snare snap layer, `render_lead`).
Extract only the **synth-brass chord-stab** voice into a small `brass_stab.py`
if wanted. Everything else is composition, not an instrument. Ask the user
before doing this one.

## 5. Dune leftovers (candidates, lower value)

Deliberately left out of the first pass (see dune README, "not (yet) covered").
Extract only if a track wants them:

| candidate | source |
|---|---|
| `make_thump`, `make_kick_water`, `make_kick_sleeper` | `generate_kwisatz_haderach.py` (check vs `kick.py`) |
| `make_knock`, `crowd_sing` | `generate_muaddib.py` |
| `make_boom` | `generate_maker_comes.py` (check vs `impact_fx.explosion`) |
| `heart_thump` | `generate_fall_of_arrakeen.py` |
| `whisper_phrase`, `formant_drone`, `grain`, `acid_note8` | `generate_litany_against_fear.py` |
| `add_squeak`, `body_and_room` | `generate_gurneys_song.py` |
| `fold_whoosh` | `generate_the_navigator.py` (`navigator.py` sibling) |
| `tape_echo`, `skank` | `generate_spice_agony.py` |
| ambient beds: wind, drone, sunrise shimmer, klaxon | `generate_arrakis*.py`, `generate_ambient.py`, `generate_sleeper_awakens.py` |

### Not instruments — out of scope

- TTS voice-line pipeline: `generate_voice_*.py`, `generate_game_voices.py`,
  `generate_samples*.py` (`fx_benegesserit`, `fx_intercom`, `fx_ringmod`,
  `fx_bitcrush`, `pitch_layer`, `radio_click`, `make_ir`). A separate subsystem
  (`tracks/dune/voices.md`). If wanted, that is a *processing-chain* library,
  and its own task.
- Arrangement/mix glue: `bar_t`, `commit`, `place*`, `groove_on`, `*_on`,
  `acid_bars`, `section*`, verification helpers (`check`, `rms_*`, `band_shares`).

## Order of work

1. Trance `.py` from the existing md (biggest, mostly mechanical).
2. Trance 1a scripts (morgenland, flightpath) — new sounds.
3. Psy.
4. Ambient.
5. Dune leftovers, house — only on request.

Per library: commit, update its README, run every `__main__` audition. No track
script changes; run `git status` to confirm only the new `instruments/` files
and README moved.
