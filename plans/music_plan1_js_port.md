# Plan 1 — JavaScript Port for Dune Game Integration

> **Standalone briefing document.** This plan is self-contained: it describes
> the existing system in conceptual terms and everything an implementing
> agent needs. It does not depend on any other plan being completed first.

## Background (context for the implementing agent)

The source system is a collection of **fully procedural music generators
written in Python (numpy + scipy)**. There are no audio samples and no
external audio assets: every instrument — wind, drones, duduk- and ney-like
melodic voices, Karplus-Strong plucked strings (oud, santur), darbuka and
war-drum percussion, 303-style acid lines, trance kicks, throat chants,
explosions — is synthesized from oscillators, filtered noise, envelopes, and
convolution reverb. Each track is one deterministic offline render: a single
seeded RNG drives all randomness, layers are synthesized as full-length
float buffers, mixed with per-layer weights, peak-normalized, and written as
44.1 kHz stereo 16-bit WAV.

Musically, everything shares **one key (D) and one mode family (D Phrygian
dominant / D minor pentatonic)** so tracks blend into each other. The
catalog covers RTS music *states*: a quiet exploration/ambient loop, an
economy/harvesting loop, a tension/enemy-sighted loop, battle and chase
tracks, long-form "album" pieces, and a sandstorm **overlay** designed to be
faded in over whatever state track is playing. Several tracks are
**seamless loops** built by equal-power-folding the render tail into the
head (on the bar grid where a beat exists). The target game is a
browser-based RTS written in JavaScript.

## Goal / Scope

Port the music system to JavaScript so the game can play it natively, with
two levels of ambition:

1. **Tier 1 (must have): in-browser offline rendering.** Reproduce the
   generative logic in JS so tracks are synthesized client-side into audio
   buffers and played/looped by the game — zero shipped audio files, tiny
   code footprint instead of tens of MB of audio.
2. **Tier 2 (the payoff): dynamic, game-state-driven music.** Expose the
   generators as a real-time-controllable system: state transitions
   (explore → tension → battle → aftermath) as musically-aligned crossfades,
   continuous parameters (battle intensity, worm proximity, storm strength)
   driving layer gains, event density, and tempo, and overlays mixed on top.

Out of scope: any GUI/editor tooling, new musical content beyond what is
needed to validate the port, and server-side rendering.

## Key Challenges

- **Numerical parity.** The Python renders are the ground truth the
  author has approved by ear. A JS port must sound *equivalent*, not
  necessarily be bit-identical. Define an explicit equivalence standard
  early (see Phase 0), because chasing bit-exactness across different FFT,
  filter, and RNG implementations is a tar pit.
- **Deterministic RNG.** The Python side uses a seeded PRNG for everything
  (gust curves, ghost notes, event placement). JS needs a seedable PRNG
  with equivalent statistical behavior; `Math.random` is not seedable.
  Decide whether to (a) re-implement the same PRNG algorithm for matching
  sequences, or (b) accept different-but-same-character randomness per
  seed. Option (b) is acceptable for textures (wind) but risky for
  *composed* randomness (which bars get fills) — prefer (a) where the
  randomness is structural.
- **Offline render cost in the browser.** Tracks are minutes long with
  10–30 layers; naive sample-by-sample JS will be slow. Mitigations:
  `OfflineAudioContext` for node-expressible parts, typed arrays +
  WebAssembly-friendly inner loops for custom DSP (Karplus-Strong,
  custom filters), Web Workers so rendering never blocks the game, and
  rendering tracks lazily/in priority order during the game's load and
  menu phases.
- **DSP primitive gaps.** scipy's Butterworth/`sosfilt`, `iirpeak`,
  `fftconvolve`, and polyphase resampling have no direct stdlib JS
  equivalents. The port needs a small DSP kernel: biquad cascades designed
  from the same analog prototypes, an FFT (for convolution reverb), and
  the handful of envelope/smoothing helpers the generators rely on.
- **Seamless looping in the browser.** The loop tracks depend on
  sample-accurate looping. `AudioBufferSourceNode.loop` is gapless; any
  compressed-file fallback must use formats that decode gaplessly (WAV/OGG,
  not MP3 — MP3 encoder padding breaks loop points).
- **Real-time vs offline tension (Tier 2).** The Python generators are
  whole-track compositions with long-range structure. Real-time
  game-driven music can't know the future. The architecture must separate
  *texture layers* (wind, drone, percussion grooves — loopable,
  gain-controllable in real time) from *composed arcs* (builds, drops,
  codas — better kept as pre-rendered one-shot stingers/sections triggered
  at musical boundaries).

## Proposed Architecture / Approach

Three layers, cleanly separated:

1. **DSP kernel (pure functions on Float32Array/Float64Array).**
   Oscillators with phase-accumulated pitch glides, seeded noise
   generators, biquad/SOS filter runners, FFT convolution, envelope and
   smoothed-random ("slow noise") control-signal helpers, Karplus-Strong
   string engine, equal-power loop folding, peak/RMS utilities. No Web
   Audio dependency — runnable in a Worker and in Node (for testing).
   This kernel is where parity with Python is enforced.

2. **Instrument & track layer.** Each instrument is a function from
   (parameters, RNG) → buffer or note-event renderer; each track is a
   declarative-ish assembly: layer list, per-layer schedule on a bar grid,
   mix weights, mastering chain (shelves, soft limiter), loop fold. Port
   the *recipes*, not the line-by-line code. Keep one shared module —
   unlike the Python side's deliberate per-script duplication, the JS port
   should centralize helpers (the duplication existed for script
   standaloneness, which doesn't apply here).

3. **Game-facing runtime ("music director").** A small API the game calls:
   `init()` (kick off background rendering of the state loops in priority
   order), `setState('explore'|'economy'|'tension'|'battle'|...)`
   (crossfade on the next musical boundary), `setOverlay('storm', amount)`,
   `setParam('intensity', x)`, `trigger('worm'|'victory'|'defeat')`.
   Internally: an `AudioContext` mixer graph with one bus per state track,
   equal-power crossfades, and overlay buses. Tier 1 ships with just
   state-loop playback + crossfade; Tier 2 adds parameterized layers.

**Validation harness (critical):** a Node-based test runner that renders
tracks/instruments with the JS kernel and compares against reference WAVs
exported from Python — comparing per-band RMS over time windows, onset
times of scheduled events, and loudness envelopes (not raw samples). Plus
human listening checkpoints at each milestone; the author's ear is the
final acceptance test.

**Pragmatic fallback:** keep the option of shipping a few tracks as
pre-rendered OGG/Opus files (the Python renders, compressed) for anything
that proves too expensive to port. The architecture should make
"pre-rendered buffer" and "JS-rendered buffer" interchangeable behind the
same music-director API, so the port can land incrementally without
blocking game integration.

## Milestones / Phases

- **Phase 0 — Parity standard & skeleton.** Define the equivalence
  criteria (psychoacoustic, not bit-exact: matching event times, band-RMS
  envelopes within tolerance, author listening sign-off). Stand up the JS
  DSP kernel with tests against small Python-generated reference clips
  (a filtered noise gust, one Karplus-Strong pluck, one reverb IR).
- **Phase 1 — First track end-to-end (proof of concept).** Port the
  simplest texture track (the desert-ambience family: wind + drone +
  sparse events, no beat grid) including its seamless loop fold. Render in
  a Worker, loop it gaplessly in the browser, A/B against the Python WAV.
- **Phase 2 — Game integration, Tier 1.** Implement the music-director
  API, background/priority rendering, state crossfading, and the
  pre-rendered-buffer fallback path. Integrate with the game's state
  machine. Ship point: the game has working dynamic-state music even if
  only some tracks are JS-rendered.
- **Phase 3 — Rhythmic engine.** Port the beat-grid machinery: step
  sequencing, percussion kit synthesis, gated bass, plucked-string riffs,
  and the on-grid loop fold. Deliver the economy and tension loops.
- **Phase 4 — Full battle/psy palette.** Acid lines with per-note filter
  sweeps, kick stacks with sidechain pumping, mastering shelves/limiter.
  Deliver battle music and the storm overlay (including its no-lull AGC).
- **Phase 5 — Tier 2 dynamics.** Split ported tracks into real-time
  controllable layer groups; expose intensity/proximity parameters;
  stingers for one-shot events (worm strike, victory/defeat codas);
  musically-quantized transitions. Tune with in-game playtesting.

## Dependencies / Assumptions

- Target is modern evergreen browsers with Web Audio API, Workers, and
  (optionally) WebAssembly; no legacy-browser support required.
- Reference WAV renders of every track can be produced from the Python
  system on demand and used as golden files; the Python system remains the
  compositional source of truth during the port.
- The game's code can be modified to call the music-director API and can
  surface the needed state/parameter signals (game state, battle
  intensity, storm events).
- A human listener (the project author) is available for acceptance
  listening at each phase.
- Optional integration point: if a modular Python framework or a track
  GUI exists later, its declarative track descriptions could be compiled
  to this JS runtime — design the track-assembly layer as data-driven
  enough not to preclude that, but do not depend on it.
