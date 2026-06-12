# Plan 4 — Full-Featured DAW (Digital Audio Workstation)

> **Standalone briefing document.** This plan is self-contained: it describes
> the existing system in conceptual terms and everything an implementing
> agent needs. It does not depend on any other plan being completed first
> (a tracker GUI or modular framework, if they exist, become components;
> if not, this plan builds the equivalents it needs — see Dependencies /
> Assumptions).

## Background (context for the implementing agent)

The starting point is a **fully procedural music system in Python
(numpy + scipy)**: a themed album of ambient/action/psy-trance tracks and
RTS game-state loops, synthesized entirely from code — parameterized
instrument recipes (textures, Karplus-Strong strings, percussion kits,
melodic voices, acid lines, kick stacks, FX), bar-grid sequencing, layered
arrangement with energy curves, mastering, and deterministic seeded
rendering to stereo WAV. The current workflow is offline and code-driven;
the long-term vision is a professional-grade production environment that
keeps this generative engine as its signature instrument while adding the
capabilities of a real DAW: external input, recording, editing, and mixing.

## Goal / Scope

Build a **desktop DAW** whose differentiator is that procedural synthesis
is a first-class citizen alongside conventional audio/MIDI. Capabilities:

- **Multi-track timeline**: audio tracks, MIDI/instrument tracks, and
  *generator tracks* (clips whose content is a deterministic procedural
  recipe + parameters + seed).
- **MIDI input**: play the procedural instruments live from a MIDI
  keyboard; record MIDI clips; edit them in a piano-roll.
- **Audio import & recording**: bring in external samples/files
  (drag-and-drop, format decoding) and record from audio devices
  (microphone/line-in) onto audio tracks, with monitoring.
- **Mixing**: per-track channel strips (gain, pan, mute/solo), insert
  effect chains, send/return buses, master bus with metering, and
  **automation lanes** for any parameter.
- **Editing**: clip-level arrange/trim/fade/crossfade; non-destructive.
- **Export**: offline render of the session to WAV (and compressed
  formats), with the guarantee that purely-procedural sessions render
  deterministically.

Out of scope (explicitly, to keep "full-featured" bounded): third-party
plugin hosting (VST/AU/CLAP) in v1, video scoring, notation, surround
formats, collaboration/cloud features. Note plugin hosting as the most
likely v2 extension and avoid architectural decisions that preclude it.

## Key Challenges

- **A real-time audio engine is a different beast.** Everything existing
  is offline batch DSP. A DAW needs a low-latency callback-driven engine:
  a processing graph evaluated in fixed-size blocks, lock-free
  communication between UI and audio threads, no allocation or blocking in
  the audio callback. This is the highest-risk component. Two-pronged
  strategy:
  1. **Dual-mode instruments.** Keep the offline renderers as the source
     of truth, and give each procedural instrument a *real-time face*:
     either block-based re-implementation of its recipe (feasible for most
     — oscillator/filter/envelope recipes translate naturally) or
     cached-buffer triggering (render the note offline on first use, then
     trigger from cache — acceptable for percussion/plucks, where the
     existing system already caches per-note renders).
  2. **Python for the shell, native-speed core for the hot path.** The
     audio callback and graph execution should run outside the GIL —
     options: a small compiled core (Rust/C++ bound to Python), numpy
     block processing carefully kept allocation-free, or an existing
     embeddable engine library. Decide via the Phase 0 spike; do not
     commit the whole project to pure-Python real-time before measuring.
- **Latency targets.** Live MIDI performance needs round-trip latency
  ~10 ms (256-sample blocks); recording needs accurate latency
  compensation so recorded material lands on the grid. Both must be
  designed in from the start, not retrofitted.
- **Two timelines, one session.** Generator clips are deterministic and
  re-renderable; audio recordings are immutable captures; MIDI clips are
  editable events. The session model must unify them: a shared
  tempo/transport map, per-clip content types, and a render system that
  knows what can be regenerated vs what must be preserved (never
  overwrite or discard recorded audio; treat captures as append-only).
- **Mixing architecture.** Insert chains, sends, automation, and metering
  form a directed graph with ordering and fan-out; automation must be
  sample-accurate enough for fades yet cheap. Borrow the established
  industry model (tracks → inserts → sends → buses → master) rather than
  inventing one.
- **The generative heritage.** The existing system's value is its recipes
  *and its lessons* (loudness discipline, anti-fatigue envelope rules,
  loop craftsmanship, "game loops never build"). The DAW should carry
  these forward as built-in analysis tools (per-section loudness reports,
  loop-seam validation, sustained-high-frequency warnings) — features no
  off-the-shelf DAW has, and the reason to build rather than buy.
- **Scope discipline.** A DAW is an unbounded product. The phases below
  are gated so that each ships a usable tool; resist pulling later-phase
  features earlier.

## Proposed Architecture / Approach

Layered, with the audio engine isolated behind a narrow real-time-safe
boundary:

1. **Audio engine (real-time core).** Device I/O (duplex, via a
   PortAudio-class backend), a block-based processing graph (nodes:
   clip players, instruments, effects, buses; edges: audio/event
   streams), a transport (sample-accurate position, tempo map, loop
   region), MIDI input routing, and a command queue (lock-free) through
   which the rest of the application talks to it. Recording = engine
   writes input blocks to disk-backed buffers. Implementation language
   for this layer decided by the Phase 0 spike (compiled core
   recommended).
2. **Session model.** The document: tracks, clips (audio / MIDI /
   generator), instrument and effect instances with parameters,
   automation lanes, routing, tempo map. Transactional edits → undo/redo;
   serializes to a versioned, human-diffable project format; references
   external audio by content hash with media management.
3. **Render system.** Two consumers of the same graph definition: the
   real-time engine (block mode) and an offline renderer (the existing
   numpy-style whole-buffer mode) for export and for "freeze track".
   Generator clips render through the procedural recipes deterministically;
   freezing/bouncing converts any track to audio for CPU headroom.
4. **Instrument & effect library.** The ported procedural instruments
   (with MIDI-playable interfaces: pitch/velocity → recipe params), a
   sampler instrument for imported audio, and a starter effect set
   (EQ/shelves, compressor/limiter, the system's convolution reverb,
   delay, saturation — most already exist as offline recipes).
5. **UI.** Desktop GUI (Qt recommended): arrangement/timeline view,
   clip editors (piano-roll for MIDI, waveform for audio, parameter panel
   for generator clips), mixer view with channel strips and metering,
   browser (instruments, effects, project media), transport bar. If an
   interactive tracker GUI already exists in the ecosystem, its pattern
   editor can be embedded as the generator-clip editor; otherwise
   generator clips get a simpler parameter-form editor in v1.
6. **Analysis toolkit.** The loudness/loop/fatigue validators as
   first-class panels (run on selection, track, or session).

## Milestones / Phases

Each phase ends with a usable artifact.

- **Phase 0 — Engine spike (de-risk first).** Prototype the real-time
  core: duplex audio I/O, block graph with a test oscillator + one ported
  procedural instrument, MIDI-in → sound, latency measured. Decide the
  core implementation language/stack from evidence. **Gate: live-playable
  instrument at ≤ ~15 ms round trip.**
- **Phase 1 — Playback DAW.** Session model + timeline UI + transport:
  arrange audio clips and generator clips on multiple tracks, per-track
  gain/pan/mute/solo, master bus, offline WAV export. (A "player/arranger"
  — already useful for assembling game music from rendered stems.)
- **Phase 2 — MIDI & instruments.** MIDI tracks, live input, recording,
  piano-roll editing; the procedural instrument library exposed as
  MIDI-playable instruments; sampler for imported audio files.
- **Phase 3 — Recording & editing.** Audio device recording with
  monitoring and latency compensation, non-destructive clip editing
  (trim/fade/crossfade), media management.
- **Phase 4 — Mixing.** Insert effect chains, sends/returns, automation
  lanes (record + draw), metering, freeze/bounce, the analysis toolkit.
- **Phase 5 — Production polish.** Project format hardening +
  autosave/crash recovery, keyboard-driven workflow, export options
  (stems, compressed formats, loop-folded exports for game loops),
  performance optimization, and a full dogfood: produce one new track for
  the album entirely inside the DAW. **That track shipping is the
  acceptance test.**

## Dependencies / Assumptions

- Desktop target (Linux first, where development happens) with working
  duplex audio and optional MIDI hardware. GUI and audio-IO dependencies
  (e.g. Qt/PySide6, a PortAudio binding) are acceptable; a compiled
  component (Rust/C++) is acceptable for the engine core if the Phase 0
  spike shows pure Python can't meet latency.
- The existing procedural recipes (in Python) are available as the source
  of truth for the instrument library; deterministic rendering of
  generator content is a hard requirement.
- Optional foundations, not prerequisites: a modular generation framework
  (would become the instrument library and offline renderer) and a
  tracker GUI (would become the generator-clip editor). If absent, this
  plan implements the narrower equivalents it needs.
- Recorded audio is sacrosanct: the system never deletes or overwrites
  captured material without explicit user confirmation.
- Single user, local machine; no plugin hosting, collaboration, or
  distribution/packaging requirements in v1 (keep plugin hosting open as
  a v2 path).
