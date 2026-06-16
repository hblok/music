# Forge Inventory

Maps every `def` in the legacy generator scripts to its target forge module.
Produced during Phase 0; updated as migration proceeds.

Legend: `[done]` = extracted, `[pending]` = awaiting extraction.

---

## Core helpers — duplicated across scripts, one canonical copy each

| Legacy name | Occurrences | Forge target | Notes |
|---|---|---|---|
| `midi_to_hz` | 26 scripts | `forge.core.dsp` | Identical in all scripts |
| `fade` | 16 scripts | `forge.core.dsp` | Raises-cosine in/out; signature varies (default seconds differ per script) |
| `slow_noise` | 19 scripts | `forge.core.dsp` | Sparse normals → 3-pt smooth → interp → normalize; `**power` variant used at call sites |
| `make_reverb_ir` | 22 scripts | `forge.core.reverb` | Exponentially decaying noise, dark-tail LP, energy-normalized; seeds 7/11 for L/R |
| `reverb` | 20 scripts | `forge.core.reverb` | `fftconvolve`, tail renorm to dry peak; some scripts use `oaconvolve` (ambient/lost.py) |
| `reverb_mono` | 1 script (ambient/lost.py) | `forge.core.reverb` | Same as `reverb`; expose as alias |
| `reverb_layer` | 1 script (ambient/lost.py) | `forge.core.reverb` | Applies `reverb_mono` to L and R; convenience wrapper |
| `add_at` | 19 scripts | `forge.core.buffer` (AudioBuffer method) | Bounds-safe mono-into-mono placement; wrapped as `AudioBuffer.add_at` |
| `commit` | 15 scripts | `forge.core.mixbus` (MixBus method) | Peak-normalize then weighted-add into global mix; `env` variant in some scripts |
| `bar_t` | 14 scripts | `forge.core.grid` (Grid method) | `(bar*4 + beat) * BEAT`; GRID0 offset present in some scripts |
| `glide_curve` | 13 scripts | `forge.core.dsp` | One-pole IIR portamento smoother on a frequency target array |
| `ramp` | 1 script (ambient/lost.py) | `forge.core.dsp` | `np.interp` on (t, times, values); general piecewise-linear helper |
| `raised_cosine` | 1 script (dune/generate_ambient.py) | `forge.core.dsp` | `0.5 - 0.5*cos(2π·k/n)`; symmetric 0→1→0 window |
| `fft_bandpass` | 1 script (dune/generate_ambient.py) | `forge.core.dsp` | Numpy-only (no scipy); kept for scripts that predate scipy install |
| `feedback_delay` | 1 script (dune/generate_ambient.py) | `forge.core.dsp` | Tapped feedback echo |
| `place_pan` | 2 scripts (ambient/lost.py, trance/lost_v3.py, lost_v4.py) | `forge.core.buffer` | Calls `add_at` with constant-power pan; convenience helper |

---

## Script inventory — RNG seeds and grid constants

| Script | Seed | BPM | Duration (s) | Notes |
|---|---|---|---|---|
| `dune/generate_ambient.py` | 42 | — | 180 | Pure numpy (no scipy); FFT bandpass |
| `dune/generate_arrakis.py` | 1965 | — | 210 | First scipy script; seed = novel pub year |
| `dune/generate_arrakis_winds_v3.py` | (IR-specific) | — | ? | No global rng line found; IRs only |
| `dune/generate_base_attack.py` | ? | 128 | 195 | karplus_strong with seed_noise param |
| `dune/generate_fall_of_arrakeen.py` | ? | 148 | 365 | Largest script; GRID0 offset present |
| `dune/generate_game_voices.py` | 2342 | — | — | Voice FX only; out of forge scope |
| `dune/generate_kanly.py` | ? | 112 | 220 | Gallop/hoof percussion |
| `dune/generate_maker_comes.py` | ? | 104 | 440 | Long narrative track |
| `dune/generate_night_pursuit.py` | ? | 104 | 225 | Karplus+voice+bass |
| `dune/generate_samples.py` | 10191 | 128 | — | Audition/samples script |
| `dune/generate_samples_arrakeen.py` | 10191 | 148 | — | Audition/samples script |
| `dune/generate_samples_maker.py` | 2024 | 104 | — | Audition/samples script |
| `dune/generate_samples_pursuit.py` | 1984 | 104 | — | Audition/samples script |
| `dune/generate_samples_sleeper.py` | 303 | 145 | — | Audition/samples script |
| `dune/generate_samples_water.py` | 140 | 140 | — | Audition/samples script |
| `dune/generate_sandstorm_coriolis.py` | ? | — | 72 | Short game-state loop; commit-based |
| `dune/generate_sleeper_awakens.py` | ? | 145 | 570 | Longest track; psy-trance |
| `dune/generate_spice_must_flow.py` | 1969 | 64 | 270 | Game-state loop; seamless fold |
| `dune/generate_stillsuit.py` | ? | 96 | — | Game-state loop |
| `dune/generate_voice_final.py` | 2342 | — | — | Voice FX; out of scope |
| `dune/generate_voice_fx.py` | 2342 | — | — | Voice FX; out of scope |
| `dune/generate_voice_languages.py` | 2342 | — | — | Voice FX; out of scope |
| `dune/generate_voice_samples.py` | (per-call) | — | — | Voice FX; out of scope |
| `dune/generate_voice_samples_good.py` | (per-call) | — | — | Voice FX; out of scope |
| `dune/generate_voice_showcase.py` | (per-call) | — | — | Voice FX; out of scope |
| `dune/generate_water_of_life.py` | ? | 140 | 440 | Psy-trance; acid+voice |
| `ambient/lost.py` | 1893 | — | 470 | Uses `oaconvolve`; seed = Munch Scream year |
| `trance/generate_tech_noir.py` | ? | 13/16 | 265 | Odd time sig; brass/love phrases |
| `trance/lost_v3.py` | 130 | 130 | 410 | Trance rework of ambient lost |
| `trance/lost_v4.py` | 130 | 130 | 410 | Current version of trance lost |
| `trance/nachtkind_v1.py` | 1993 | 139 | 331 | Frankfurt trance; reference |
| `trance/nachtkind_v2.py` | 1993 | 139 | 331 | Current version |
| `trance/tech_noir_v2.py` | ? | 13/16 | 265 | Parallel take; kept for reference |

---

## Instrument recipes — by forge family

### `forge.instruments.textures`

| Recipe | Occurrences | Description |
|---|---|---|
| wind | 8+ scripts | Two-band noise (120–900 Hz whoosh + 2–7 kHz hiss); gusts via `slow_noise`; slow stereo pan drift |
| drone | 6+ scripts | D1 additive sines (fund + 2nd + 3rd + 3.003× beating); slow breath LFO |
| swell (dissonant cluster) | 1 (ambient/lost.py) | Detuned ±0.6% additive saw cluster for dread/angst sections |

### `forge.instruments.percussion`

| Recipe | Occurrences | Description |
|---|---|---|
| `make_doum` | 11 | Darbuka doum: pitch-falling sine + narrow bandpass body; low thump |
| `make_tek` | 11 | Darbuka tek: high-band click + ring; `ghost=True` variant at half gain |
| `make_kick` | 8 | 909-style: pitch-falls 55→27 Hz, `tanh` drive, layered sub |
| `make_kick_stack` | 1 (fall_of_arrakeen) | Layered kick variant with sub boom option |
| `make_hat` | 10 | Closed/open hi-hat via `open_=True`; noise through HP filter |
| `make_clap` | 8 | Layered noise bursts with slight timing scatter |
| `make_snare` | 4 | Noise + tonal body; `buzz=True` for snare roll variant |
| `make_war_drum` | 7 | Large membrane: deep pitch-fall + resonant body |
| `make_frame_hit` | 6 | Frame drum single stroke |
| `frame_roll` | 6 | Frame drum roll (repeating hits) |
| `make_shaker` | 4 | Short filtered noise bursts at beat subdivision |
| `make_ride` | 3 (trance) | 909-style ride cymbal |
| `make_crash` | 4 (trance) | Cymbal crash |
| `make_tom` | 1 (fall_of_arrakeen) | Tom at given f0 |
| `make_anvil` | 2 (tech_noir) | Metallic clang; 13/16 machine texture |
| `make_slam` | 2 (tech_noir) | Heavy impact |
| `make_tap` | 2 (tech_noir) | Light tap/snare |
| `make_tick` | 3 (night_pursuit, kanly, maker) | Clock tick / percussion accent |
| `click` | 1 (stillsuit) | Bandpass noise ping; game-state tick |

### `forge.instruments.strings`

| Recipe | Occurrences | Description |
|---|---|---|
| `karplus_strong` | 5 | Warm pluck: smoothed excitation, damp≈0.992–0.9955, cached per pitch |
| `pluck` | 5 | Lighter pluck variant (simpler than KS in some scripts) |
| `piano_note` | 4 | Felt piano: stretched-inharmonic partials, two detuned strings, felt thunk, lowpass; cached per pitch |
| `cello_line` | 2 (trance/lost_v3, lost_v4) | Bowed cello: detuned additive saw + bow noise + vibrato |
| `tremolo_strings` | 7 | Tremolo string chords via rapid gain oscillation |
| `pad_chord` | 7 | Detuned saw-stack sustained chord with slow attack/release |
| `oud_note` | 1 (fall_of_arrakeen) | Plucked oud: Karplus-Strong with oud-like pick |

### `forge.instruments.voices`

| Recipe | Occurrences | Description |
|---|---|---|
| `voice_phrase` | 6 | Duduk/ney-like melodic voice: additive harmonics, portamento via `glide_curve`, vibrato, lowpass; full phrase renderer |
| `ney_phrase` | 5 | Breathy ney variant of voice_phrase with more breath noise |
| `chant_note` | multiple | Single chant note: pulsed fundamental + harmonics, resonant body |
| `lead_phrase` | 4 (trance) | Detuned saw stack lead with warmth recipe applied |
| `brass_phrase` | 2 (tech_noir) | Rolled-off saw brass with warmth recipe |
| `horn_phrase` | 1 (fall_of_arrakeen) | Horn/brass phrase with growl parameter |
| `choir` / polytonal stacking | 1 (ambient/lost.py) | Formant-bandpassed glottal source; vowel oo/ah |
| `flute` / ney solo | 1 (ambient/lost.py) | Low harmonics + breath noise; blooming vibrato |

### `forge.instruments.bass`

| Recipe | Occurrences | Description |
|---|---|---|
| `bass_note` | 9 | Context-dependent: trance = warm detuned saw + sine sub (warmth recipe); dune = similar; each script has its own tuning |
| `psy_bass_note` | 6 | Psy-trance sub-bass: deep pitch-fall + sine sub; gated duration |
| `acid_note` | 5 | 303-style: resonant filter sweep (low Q blend), accent/slide variants |
| `bass_hit` | 2 (tech_noir) | 13/16 machine-style bass hit |

### `forge.instruments.fx`

| Recipe | Occurrences | Description |
|---|---|---|
| `make_zap` | 4 | Laser/zap: exponential pitch fall + noise burst |
| `riser` | 9 | White noise + pitch-rising tone, building into a drop |
| `explosion` | 1 (fall_of_arrakeen) | Layered noise burst + pitch-fall + rumble tail |
| `make_boom` / `make_sub_boom` | 2 | Sub-bass impact |
| `rev_cymbal` | 1 (fall_of_arrakeen) | Reversed cymbal for transition |
| `heart` / `heart_thump` | 2 (ambient/lost.py, fall_of_arrakeen) | Soft two-thump heartbeat; the through-line in lost |
| `riser` (variant) | 1 | See above |

---

## Voice FX — out of scope for forge (game voice processing, not music synthesis)

These helpers process gTTS speech via time-stretching, pitch-shifting, and
radio/Benegesserit effects. They depend on OLA time-stretch and optional
TTS file I/O. They live in `dune/generate_voice_*.py` and have no place in
forge; a separate voice-FX pipeline would own them.

`ola_stretch`, `time_pitch_adjust`, `load_wav_mono`, `save_stereo`,
`apply_reverb` (voice version), `noise_gate`, `radio_click`, `intercom`,
`fx_intercom`, `fx_benegesserit`, `fx_bitcrush`, `fx_ringmod`,
`pitch_layer`, `process_and_save`, `run_gtts`, `gtts_to_wav`

---

## Pattern / arrangement helpers

| Legacy name | Script(s) | Forge target | Notes |
|---|---|---|---|
| `acid_bars` | sleeper, water_of_life, fall_of_arrakeen | `forge.patterns.groove` | Places an acid riff over bars |
| `bass_bar_16` | maker_comes | `forge.patterns.schedule` | 16th-note bass schedule for one bar |
| `play_theme` | night_pursuit, kanly, maker, fall | `forge.patterns.groove` | Renders a note-list theme at a bar offset |
| `play_riff` | maker_comes | `forge.patterns.groove` | Like play_theme with random octave jumps |
| `fill` | trance/lost_v3, lost_v4 | `forge.patterns.step` | Rotates through a list of bar-length patterns |
| `roll` | trance/lost_v3, lost_v4 | `forge.patterns.groove` | 16th-note hi-hat roll over a range of bars |
| `kick_gain` | trance scripts | `forge.arrange.curves` | Piecewise gain curve; drives kick level vs section |
| `bass_gain` / `bass_cutoff` / `bass_root` | nachtkind | `forge.arrange.curves` | Per-bar parameter curves |
| `rhythm_on` | sleeper, water_of_life | `forge.patterns.schedule` | Boolean mask: is the rhythm section active at bar b? |
| `groove_on` | fall_of_arrakeen | `forge.patterns.schedule` | Same concept; returns gain for groove section |
| `outro_gain` | sleeper, water_of_life | `forge.arrange.curves` | Gain ramp for outro section |
| `snare_march_bar` | fall_of_arrakeen | `forge.patterns.groove` | Renders one bar of snare march |
| `section_of` | trance/lost_v3, lost_v4 | `forge.arrange.section` | Returns section name for bar b |
| `place_voice` | many | `forge.patterns.groove` | Renders voice phrase and `add_at` to L/R layers |
| `place_ney` | maker_comes | `forge.patterns.groove` | Same for ney |
| `place_horn` | fall_of_arrakeen | `forge.patterns.groove` | Same for horn |
| `place_lead` | trance/lost_v3, lost_v4 | `forge.patterns.groove` | Same for lead phrase |
| `place_piano_theme` | trance/lost_v3, lost_v4 | `forge.patterns.groove` | Piano theme with left-hand octave option |
| `chant_bar` | maker_comes | `forge.patterns.groove` | Renders one bar of chant |
| `play_riff` | maker_comes | `forge.patterns.groove` | Riff with probabilistic octave jumps |
| `place_pads` | nachtkind_v1 | `forge.patterns.groove` | Chord pad schedule over bars |
| `place_note` | nachtkind_v1 | `forge.patterns.groove` | Single note placement helper |
| `place_theme` | nachtkind_v1 | `forge.patterns.groove` | Nachtkind piano theme renderer |
| `place_frag` | kanly | `forge.patterns.groove` | Voice fragment placement |
| `place_gallop` | kanly | `forge.patterns.groove` | Horse gallop pattern scheduler |

---

## RNG usage summary

**Single global `rng`:** all narrative and loop scripts use one `np.random.default_rng(seed)` that feeds every stochastic draw in source order. Reordering draws or extracting a component into forge will change subsequent draws — this is the "RNG break" the plan acknowledges.

**IR-specific `rng`:** reverb IRs always use their own fresh `np.random.default_rng(seed)` (seeds 7 and 11 for L/R), independent of the main rng. This pattern is already hierarchical and maps directly to forge `RngContext.spawn('ir_L')` etc.

**Forge strategy:** adopt hierarchical `SeedSequence`-based seeding from the start. Each migration is a listening-approved re-render (not bit-exact), because the child RNGs are derived differently than the legacy sequential draws.

---

## Reference renders manifest

Scripts to run for baseline WAV captures (excluding voice-FX and sample-audition scripts):

| Script | Expected output |
|---|---|
| `dune/generate_ambient.py` | `ambient_track.wav` |
| `dune/generate_arrakis.py` | `arrakis_winds_v2.wav` |
| `dune/generate_arrakis_winds_v3.py` | `arrakis_winds_v3.wav` |
| `dune/generate_base_attack.py` | `base_attack.wav` |
| `dune/generate_fall_of_arrakeen.py` | `fall_of_arrakeen_v2.wav` |
| `dune/generate_kanly.py` | `kanly.wav` (or similar) |
| `dune/generate_maker_comes.py` | `maker_comes.wav` |
| `dune/generate_night_pursuit.py` | `night_pursuit.wav` |
| `dune/generate_sandstorm_coriolis.py` | `sandstorm_coriolis.wav` |
| `dune/generate_sleeper_awakens.py` | `sleeper_awakens.wav` |
| `dune/generate_spice_must_flow.py` | `spice_must_flow.wav` |
| `dune/generate_stillsuit.py` | `stillsuit.wav` |
| `dune/generate_water_of_life.py` | `water_of_life.wav` |
| `ambient/lost.py` | `lost_v2.wav` |
| `trance/lost_v4.py` | `lost_v5.wav` |
| `trance/nachtkind_v2.py` | `nachtkind.wav` |
| `trance/generate_tech_noir.py` | `tech_noir.wav` |
