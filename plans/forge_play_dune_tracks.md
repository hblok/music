# Plan — Make Forge play the dune/ catalog

> **Goal.** Get the Forge tracker to *load and play* the procedurally-composed
> tracks under `dune/` (and `ambient/`, `trance/`), starting from the
> arrangements it can already *store*. This is a focused bridge between
> Plan 3 (tracker GUI — done) and Plan 4 (full DAW — future): it does **not**
> need real-time MIDI, recording, or a native engine. It only closes the gaps
> between the document model and the offline render path.
>
> **Audience.** Hand each phase to a Sonnet sub-agent. Phases are ordered by
> dependency; each ends with a concrete acceptance test. Renders are
> **listening-approved, not bit-exact** (the legacy scripts use one global RNG
> in source order; Forge uses hierarchical `RngContext` — see
> `forge/INVENTORY.md` "RNG usage summary").

## Status quo — what already works (June 2026)

A first conversion landed: `examples/water_of_life_drop.py` →
`examples/water_of_life_drop.json`. It expresses **DROP 1 of
`generate_water_of_life.py`** as a 7-channel, 16-step psy-trance loop
(kick / psy_bass / acid / open-hat / closed-hat / doum / tek) using only
instruments already in `forge.instruments.registry`. It opens in the GUI
(File → Open Tracker Project) and Play loops the groove (~27 s, 16 bars).

That track was chosen because its drop is the *one* part of the dune catalog
that is genuinely a repeating 16-step grid of registry instruments. Getting
**any more** of the catalog to play requires the work below.

## The core problem

The document model (`forge/document/`) is richer than the render path that
plays it. `ProjectDoc` can store sections, per-section step overrides,
texture channels, automation lanes, and per-channel seeds — the GUI edits all
of them — but the two functions that actually produce audio throw most of it
away:

- `control.render_doc_for_playback(doc, muted_channels)` — what **Play** calls
  (`ui/window.py:400`).
- `control.export_wav_from_doc(doc, path)` — what **Export WAV** calls
  (`ui/window.py:559`).

Both do the same thing (`forge/control.py:198`–`294`): collect every
`PatternChannel`, call `ch.to_track_dict()` (which emits only the channel's
*default* 16 steps), wrap them in **one** `PatternSpec` of
`length_bars = sum(section lengths)`, hardcode `n_steps=16`, and render with
`render_pattern`. Net effect: **one 16-step pattern, looped, mono, flat.**

Everything below is "stop throwing that away."

> Note: the *engine* format (`ProjectSpec` + `control.render_track`, see
> `examples/sleeper_awakens_mini.py`) already honours sections, per-section
> schedules, `gain`, `master_gain_curve`, and per-track `bars`/`every`. It is
> a useful reference implementation — but it is **not** what the GUI
> loads/plays. The GUI round-trips `ProjectDoc` via
> `serialize.save_project_doc` / `load_project_doc`. The fix is to bring the
> doc render path up to (and past) the engine path, not to switch formats.

---

## Phase 1 — Section-aware playback & export  ★ highest impact

**Problem.** Per-section `channel_steps` overrides (stored in
`doc.sections[i]["channel_steps"]`, edited live in the tracker, round-tripped
by `serialize`, see `examples/example_tracker.json`) are **ignored** at
render. So intro → build → drop → breakdown all play identically. No dune
track has a static 16-step arrangement; this is the gate on all of them.

**Implement.** Rewrite the render core shared by `render_doc_for_playback`
and `export_wav_from_doc` to walk sections in order:

- For each section `s` (in `doc.sections` order) of `s["length_bars"]` bars,
  build a `PatternSpec` whose tracks are, per `PatternChannel` `c`:
  `doc.get_section_steps(section_idx, c)` if an override exists, else the
  channel default (`model.py` already has `get_section_steps`, which falls
  back correctly).
- Render each section to its own buffer and concatenate on the bar grid
  (reuse `arrange.section.Section` / `arrange.track.Track`, which already do
  exactly this for the engine format — prefer composing them over a new
  concatenator).
- Apply per-section `gain` (add a `"gain"` field to the section dict; default
  1.0; the arrangement UI should expose it).

**Files.** `forge/control.py` (render core), `forge/document/model.py`
(ensure `gain` survives `to_dict`/`from_dict`), `ui/arrangement.py` (gain
control — optional this phase).

**Acceptance.** A doc with two sections that set different `channel_steps`
for the kick renders two audibly different halves; `export_wav_from_doc`
length == `sum(length_bars)` bars; existing `test_lifecycle.py` still green;
new test asserts section 0 vs section 1 RMS differ when only section 1 has
the kick enabled.

---

## Phase 2 — Texture & automation channels in the mix

**Problem.** `render_doc_for_playback` filters to `PatternChannel` only
(`control.py:278`); `TextureChannel` and `AutomationChannel` are dropped.
Every dune track is built on continuous **wind + drone** beds plus pads /
strings / swells; without textures the tracks are skeletons. A working
single-channel texture renderer already exists
(`control.render_texture_channel`, envelope → gain) — it just isn't summed in.

**Implement.**
- Render each `TextureChannel` over the full song length via
  `render_texture_channel` (envelope breakpoints in bars → gain curve) and
  mix into the master buffer with its per-channel gain.
- Apply `AutomationChannel` lanes whose `target_param == "master_gain"` as a
  master gain curve over the whole song (piecewise-linear over bars). This is
  the doc-model equivalent of the engine path's `master_gain_curve` and of
  the dune scripts' `energy`/`calm` curve.
- Respect mutes for textures too.

**Files.** `forge/control.py`, `forge/document/channels.py` (confirm
`TextureChannel`/`AutomationChannel` round-trip — they do).

**Acceptance.** A doc with one `wind` texture + one `kick` pattern plays both;
a `master_gain` automation lane from 0→1 over the first 2 bars produces a
measurable fade-in (per-`analysis.loudness` RMS trend); textures obey mute.

---

## Phase 3 — Per-channel mixer: apply gain, add pan

**Problem.** Two sub-gaps:
1. **Channel volume is collected but never applied.** `ui/window.py` tracks
   `self._channel_volumes` but `render_doc_for_playback` only receives
   `muted_channels` — the mixer faders do nothing to the rendered buffer.
2. **No pan.** There is no `pan` field anywhere in `document/`, `control.py`,
   or `playback/mixer.py`; every channel sums to center. Dune tracks place
   nearly every layer with a constant-power pan (and Haas width).

**Implement.**
- Add an optional `gain` (default 1.0) and `pan` (−1..+1, default 0) to
  `PatternChannel` / `TextureChannel` (`channels.py` to_dict/from_dict +
  `model.py` edit API + transactions).
- Render core: scale each channel buffer by its gain and place with
  constant-power pan (`cos/sin(θ)`, θ = (pan+1)·π/4). `AudioBuffer.add_at_pan`
  already exists per `forge/CLAUDE.md` — use it.
- Pass channel gains (not just mutes) from `ui/window.py` into the render
  call; bind `MixerWidget` pan knobs.

**Files.** `document/channels.py`, `document/model.py`, `control.py`,
`ui/window.py`, `ui/mixer.py`.

**Acceptance.** A two-channel doc panned hard L/R shows energy separation
between WAV channels; a channel at gain 0.5 halves its contribution;
`test_mixer.py` extended.

---

## Phase 4 — Per-step velocity & per-channel n_steps

**Problem.**
1. Steps are on / accent (×1.5) / ghost (×0.4) only (`groove.py:74`). Dune
   layers use arbitrary per-hit gains (bass `.8/.7/.95`, darbuka levels, hat
   `0.35`). The `water_of_life_drop` conversion had to flatten these.
2. `n_steps` is hardcoded to 16 in the render core (`control.py:236,290`),
   ignoring each channel's own `n_steps`. Triplet grids (e.g. kanly's
   3-hits-per-beat gallop) and other subdivisions can't play.

**Implement.**
- Add optional per-step `gain`/`velocity` float to `StepData`
  (`channels.py`) and honour it in `render_groove`/`render_loop`
  (`patterns/groove.py`) multiplicatively with accent/ghost.
- Honour each channel's `n_steps` in the render core (the engine
  `render_groove` already supports per-pattern `n_steps`; the doc render core
  must stop hardcoding 16 and build one track per distinct `n_steps`, or one
  pattern per channel).

**Files.** `document/channels.py`, `patterns/step.py`, `patterns/groove.py`,
`control.py`. **Acceptance.** A step at gain 0.5 is ~6 dB below a gain-1 step;
a 12-step channel plays a triplet feel against a 16-step channel; tests added
to `test_patterns.py` / `test_tracker_editor.py`.

---

## Phase 5 — Loop-fold for seamless game-state loops

**Problem.** Half the dune catalog is **game-state loops** that must be
gapless (`arrakis_winds_v3`, `spice_must_flow`, `stillsuit`,
`sandstorm_coriolis`). `export_wav_from_doc` has a `loop_fold=` arg but the
GUI never sets it, and `render_doc_for_playback` never folds, so the player
clicks at the wrap. `core.loopfold.loop_fold` + `analysis.loops` already
implement and validate the fold.

**Implement.** A per-project "seamless loop" flag (doc field) → export folds
the tail into the head over N bars; the player loops the folded buffer
seamlessly (the `CallbackMixer` already does boundary-accurate looping —
`playback/mixer.py`). Surface the seam report (`analysis.loops.seam_report`)
in the UI status line.

**Files.** `document/model.py` (flag), `control.py`, `ui/window.py`,
`ui/transport.py`. **Acceptance.**
`full_loop_report(buf, seam_tolerance=0.05, max_slope=0.005)["ok"]` is True
for a folded export (the criterion in `forge/CLAUDE.md`).

---

## Phase 6 — Per-channel parameter automation (the sweeps)

**Problem.** Dune tracks modulate *instrument* params over time: acid cutoff
sweeps over each 16-bar phrase, bass walks a cadence every 4th bar, gains
drift on `slow_noise`. `AutomationChannel` currently targets only named
engine params (e.g. `master_gain`), not a specific channel's instrument
param. This is why `water_of_life_drop` had to freeze the acid cutoff at a
single mid-sweep value.

**Implement.** Let an `AutomationChannel` target `("channel", idx, param)`
(e.g. acid `cutoff`). During render, sample the lane per bar/step and inject
the value into that step's params before `render_cached`. Keep it
breakpoint-based (bars → value), piecewise-linear. Expose in
`ui/automation_lane.py` (the curve editor already exists).

**Files.** `document/channels.py` (target encoding), `control.py` (render
injection), `patterns/groove.py` (accept a per-step param override callback),
`ui/automation_lane.py`. **Acceptance.** An acid channel with a cutoff lane
300→1800 over 16 bars produces a rising spectral centroid across the loop
(measure with an FFT centroid helper); the `water_of_life_drop` acid sweep is
restorable.

---

## Phase 7 — Reverb sends & stereo polish

**Problem.** No reverb anywhere in the render path (`grep reverb control.py
playback/` is empty), though `core/reverb.py` is complete and dune tracks
lean on it heavily (duduk/ney/strings/zaps are 35–80 % wet). Channels are
also dry-mono (no Haas).

**Implement.** A per-channel `reverb_send` (0..1) and a single shared stereo
IR pair (`core.reverb.make_stereo_ir_pair`); sum wet returns into the master.
Optional Haas width per channel. Keep it one global reverb bus (not per-
channel IRs) for cost.

**Files.** `document/channels.py`, `control.py`, `ui/mixer.py`.
**Acceptance.** A channel at `reverb_send=0.8` shows a measurable decay tail
past its note; CPU cost stays linear in channel count.

---

## Phase 8 — Missing instruments for full catalog coverage

The registry has 27 instruments
(`forge/instruments/registry.py`). The recipes for everything below are
already specified in `music/CLAUDE.md` ("Synthesis recipes") and mapped in
`forge/INVENTORY.md` — porting is mechanical (add `make_*` + `*_PARAMS`,
register, add a `test_instruments.py` case, per `forge/CLAUDE.md` "Adding a
new instrument").

| Needed instrument | For tracks | Status / source recipe |
|---|---|---|
| `ney` (breathy flute) | water_of_life, maker_comes | missing — variant of `voice` (`voice_phrase`), harmonics 1/0.25/0.08 + breath noise |
| `chant` (Sardaukar throat) | water_of_life, maker, sleeper | missing — 14-harmonic glottal + 3 formant bandpasses |
| `tremolo_strings` | water_of_life, stillsuit, sleeper | missing — detuned saw stack + 10–12 Hz tremolo (distinct from `pad`) |
| `tick`/`clock` | stillsuit, night_pursuit | missing — 30 ms bandpassed click + damped ping, L/R tick-tock |
| `breath` (stillsuit mask) | stillsuit | missing — bright inhale / dark exhale bandpassed noise, 1/bar |
| `machine_chug` (harvester) | spice_must_flow | missing — 2 detuned band-limited squares, 8th-gate, idle floor |
| `santur` | spice_must_flow | ≈ `harp` (`karplus_strong`) with 2-tap excitation; add as variant |
| `thopter` | spice_must_flow | missing — descending detuned cluster + decelerating wing AM |
| `worm_rumble` | spice, night_pursuit | missing — falling sub 55→27 Hz + LP brown-noise shake |
| `shepard_wind` | sandstorm_coriolis | missing — K whistle voices on a wrapping spectral position |
| `oud`, `horn` | fall_of_arrakeen | missing — KS oud / carnyx horn (12 harmonics + growl AM) |
| `anvil`/`slam`/`tap` | tech_noir | missing — metallic clang / heavy impact / light tap |
| `boom`/`sub_boom` | fall_of_arrakeen, kanly | missing — brown-noise→150 Hz LP + falling sub core |

Already present and sufficient: `wind`, `drone`, `swell`, `kick`, `psy_bass`,
`acid`, `bass`, `hat`, `clap`, `snare`, `doum`, `tek`, `war_drum`,
`frame_hit`, `frame_roll`, `harp`, `piano`, `cello`, `pad`, `voice`, `choir`,
`lead`, `zap`, `riser`, `explosion`, `heart`, `rev_cymbal`.

**Acceptance.** Each new instrument registered, slider-buildable from its
`ParamSchema`, with a render test; spot-checked against the legacy script's
layer.

---

## Payoff map — which tracks become playable after which phase

- **Now:** `water_of_life` DROP 1 groove (the committed example).
- **+P1/P4:** any track's full *rhythmic arrangement* (intro/build/drop/
  breakdown) — psy-trance (`sleeper_awakens`, `water_of_life`), tribal
  (`fall_of_arrakeen` percussion), `kanly` gallop (needs P4 triplets).
- **+P2/P3/P7:** the *full mix* of those tracks — wind/drone/strings beds,
  panning, reverb — i.e. a recognisable rendition end-to-end.
- **+P5:** the game-state loops gapless (`arrakis_winds_v3`,
  `spice_must_flow`, `stillsuit`, `sandstorm_coriolis`).
- **+P6:** the evolving sweeps (acid filter rides, cadence walks) that make
  the drops *move*.
- **+P8:** the melodic/timbral layers unique to each track (ney, chant,
  harvester, shepard wind, …) — full coverage of the catalog.

## Ground rules for implementing agents

- The UI talks **only** through `forge.control` (see `forge/CLAUDE.md`
  "Architecture in one paragraph"). Do not import `core`/`instruments` from
  `ui/`. Add to the facade, don't bypass it.
- Tests are `unittest`, in `forge/tests/`, Qt tests use
  `QT_QPA_PLATFORM=offscreen`. Keep the suite green
  (`python3 -m unittest discover -s forge/tests -p "test_*.py"`).
- Determinism is a hard requirement: seed every stochastic draw through
  `RngContext`. Migrations are listening-approved, not bit-exact.
- Verify loudness discipline with `analysis.loudness` (aftermath < intro;
  sustained sub doesn't out-RMS the climax — the long-form lessons in
  `music/CLAUDE.md`).
