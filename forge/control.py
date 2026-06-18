"""forge.control — GUI-agnostic facade for the forge engine.

The UI talks exclusively through this module.  Engine internals (synthesis,
DSP, file I/O) are never imported by the UI directly.

All methods raise NotImplementedError until the corresponding engine phase
is complete.  This lets the Qt shell (Phase 7) be wired and tested against
stub responses before real synthesis lands.

Completed stubs are filled in phase-by-phase:
  Phase 3 → list_instruments, render_instrument
  Phase 4 → render_pattern
  Phase 5 → render_track
  Phase 9 → load_project, save_project
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Instrument queries

def list_instruments() -> list[dict]:
    """Return the registry of available instruments.

    Each entry: ``{"id": str, "family": str, "params": list[ParamSchema]}``.
    """
    from forge.instruments.registry import list_instruments as _list
    return _list()


def render_instrument(
    instrument_id: str,
    params: dict[str, Any],
    seed: int = 0,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a single instrument hit/note/texture to an AudioBuffer.

    Args:
        instrument_id: Registry key (e.g. ``"kick"``, ``"wind"``).
        params:        Parameter dict; keys match the instrument's param schema.
        seed:          RNG seed for this render.
    """
    from forge.instruments.registry import get_instrument
    from forge.core.rng import RngContext
    entry = get_instrument(instrument_id)
    rng = RngContext(seed).spawn(instrument_id).rng
    return entry["fn"](params, rng)


# ---------------------------------------------------------------------------
# Pattern queries

def render_pattern(
    pattern: dict[str, Any],
    seed: int = 0,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a step pattern to an AudioBuffer.

    Args:
        pattern: Pattern document (see forge.spec.schema.PatternSpec).
        seed:    RNG seed.
    """
    from forge.patterns.groove import render_pattern_spec
    return render_pattern_spec(pattern, seed=seed)


# ---------------------------------------------------------------------------
# Track / project queries

def render_track(
    project: dict[str, Any],
    output_path: Path | None = None,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a complete project to an AudioBuffer (and optionally to WAV).

    ProjectSpec format::

        {
            "title": "My Track",
            "bpm": 138.0,
            "seed": 0,
            "sections": [
                {
                    "name": "intro",
                    "start_bar": 0,
                    "length_bars": 8,
                    "gain": 1.0,
                    "schedules": [ <PatternSpec>, ... ]
                }
            ],
            "master_gain_curve": [[bar, value], ...],  # optional
            "normalize": true,
            "fade_out_s": 2.0
        }

    Args:
        project:     Project document.
        output_path: If given, the rendered WAV is also written here.
    """
    from forge.arrange.section import Section
    from forge.arrange.track import Track
    from forge.patterns.schedule import Schedule

    bpm = float(project["bpm"])
    seed = int(project.get("seed", 0))
    title = str(project.get("title", "track"))
    sr = int(project.get("sr", 44100))

    track = Track(bpm, title=title, sr=sr)

    for sec_spec in project.get("sections", []):
        sec = Section(
            name=str(sec_spec["name"]),
            start_bar=int(sec_spec["start_bar"]),
            length_bars=int(sec_spec["length_bars"]),
            gain=float(sec_spec.get("gain", 1.0)),
        )
        for sched_spec in sec_spec.get("schedules", []):
            sched_spec = dict(sched_spec)
            if "bpm" not in sched_spec:
                sched_spec["bpm"] = bpm
            if "length_bars" not in sched_spec:
                sched_spec["length_bars"] = sec.length_bars
            sec.add_schedule(Schedule.from_pattern_spec(sched_spec))
        track.add_section(sec)

    if "master_gain_curve" in project:
        from forge.arrange.curves import Curve
        track.set_master_gain_curve(Curve(project["master_gain_curve"]))

    return track.render(
        seed=seed,
        normalize=bool(project.get("normalize", True)),
        target=float(project.get("target", 0.85)),
        fade_out_s=float(project.get("fade_out_s", 2.0)),
        output_path=Path(output_path) if output_path is not None else None,
    )


def load_project(path: Path) -> dict[str, Any]:
    """Load a project document from a JSON file.

    Returns the parsed and validated project dict (see forge.spec.schema).
    Raises FileNotFoundError, json.JSONDecodeError, or ValueError on bad input.
    """
    from forge.spec.serialize import load_project_dict
    return load_project_dict(Path(path))


def save_project(project: dict[str, Any], path: Path) -> None:
    """Serialize a project document to a JSON file."""
    from forge.spec.serialize import save_project as _save
    _save(project, Path(path))


# ---------------------------------------------------------------------------
# Tracker channel / section rendering (Phase 2+ scheduler entry points)

def render_channel(
    channel: "forge.document.channels.PatternChannel",  # type: ignore[name-defined]
    bpm: float,
    length_bars: int,
    *,
    n_steps: int = 16,
    seed: int = 0,
    sr: int = 44100,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a single PatternChannel to an AudioBuffer.

    This is a pure, picklable function — safe to call from a background
    thread or process pool.

    Args:
        channel:     A PatternChannel from ``forge.document.channels``.
        bpm:         Project tempo.
        length_bars: Pattern length in bars.
        n_steps:     Steps per bar (default 16).
        seed:        RNG seed for this render.
        sr:          Sample rate.
    """
    from forge.document.channels import PatternChannel as _PatCh
    if not isinstance(channel, _PatCh):
        raise TypeError("render_channel expects a PatternChannel")

    pattern_dict = {
        "bpm": bpm,
        "length_bars": length_bars,
        "n_steps": n_steps,
        "tracks": [channel.to_track_dict()],
    }
    return render_pattern(pattern_dict, seed=seed)


def _apply_reverb_bus(
    reverb_bus: "forge.core.buffer.AudioBuffer",  # type: ignore[name-defined]
    master_buf: "forge.core.buffer.AudioBuffer",  # type: ignore[name-defined]
    sr: int,
    return_gain: float = 0.65,
) -> None:
    """Mix reverb wet returns from *reverb_bus* into *master_buf* in-place.

    Builds ONE shared stereo IR pair (seeds 7 and 11, matching the legacy
    convention), then convolves each side of the bus independently.  CPU cost
    is O(N_samples * log(N_samples)) regardless of how many channels fed the
    bus — linear in channel count since each extra channel just added to the
    bus buffer before this single convolution step.

    Args:
        reverb_bus:   Pre-gain-panned mix of all reverb-send channels scaled
                      by their per-channel reverb_send.  NOT mutated.
        master_buf:   Dry master mix.  The wet tail is ADDED into this buffer.
        sr:           Sample rate (passed to make_stereo_ir_pair).
        return_gain:  Wet return level (0.65 → tail clearly audible without
                      swamping the dry mix).
    """
    from forge.core.reverb import make_stereo_ir_pair, reverb as _reverb

    ir_L, ir_R = make_stereo_ir_pair(seconds=2.0, decay=3.5, sr=sr)
    wet_L = _reverb(reverb_bus.data[:, 0], ir_L, wet=1.0)
    wet_R = _reverb(reverb_bus.data[:, 1], ir_R, wet=1.0)
    master_buf.data[:, 0] += wet_L * return_gain
    master_buf.data[:, 1] += wet_R * return_gain


def _apply_gain_pan(buf: "forge.core.buffer.AudioBuffer", gain: float, pan: float) -> None:  # type: ignore[name-defined]
    """Scale *buf* in-place by *gain* and apply constant-power *pan*.

    Pan range: −1.0 (hard L) … 0.0 (centre) … +1.0 (hard R).
    The constant-power law maps pan→angle θ = (pan+1)·π/4, then:
        L *= cos(θ)·√2,  R *= sin(θ)·√2
    At centre (pan=0, θ=π/4): cos=sin=1/√2, so ×√2 gives unity on both sides.
    """
    import numpy as np

    if gain != 1.0:
        buf.data *= gain
    if pan != 0.0:
        theta = (pan + 1.0) * (np.pi / 4.0)
        buf.data[:, 0] *= np.cos(theta) * np.sqrt(2.0)
        buf.data[:, 1] *= np.sin(theta) * np.sqrt(2.0)


def _render_doc_sections(
    doc: "forge.document.model.ProjectDoc",  # type: ignore[name-defined]
    *,
    muted_channels: "set[int] | None" = None,
    fallback_length_bars: int = 8,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Shared render core: walk sections in order, honour per-section step overrides.

    Each PatternChannel is rendered independently so that its per-channel gain
    and pan can be applied before summing into the master mix.  The RNG seed for
    channel *ci* in section *si* is ``doc.seed + si + ci * 1009`` to guarantee
    collision-free, deterministic streams across all channel/section pairs.

    When ``doc.sections`` is non-empty, each section is rendered separately and
    placed into a full-length master buffer at the correct bar offset with the
    per-section gain applied.

    When ``doc.sections`` is empty, each channel is rendered as one
    ``fallback_length_bars`` pattern.

    ``TextureChannel`` entries are rendered over the full song length and mixed
    in at t=0 with their own gain/pan applied.

    ``AutomationChannel`` entries whose ``target_param == "master_gain"`` are
    applied last as a piecewise-linear gain multiplier over the whole buffer.

    Channels whose index is in *muted_channels* are skipped entirely.

    Returns the UN-mastered ``AudioBuffer``.
    """
    import numpy as np
    from forge.arrange.curves import Curve
    from forge.core.buffer import AudioBuffer
    from forge.core.grid import Grid
    from forge.document.channels import AutomationChannel, PatternChannel, TextureChannel

    if muted_channels is None:
        muted_channels = set()

    channels = doc.channels
    pat_indices = [
        i for i, ch in enumerate(channels)
        if isinstance(ch, PatternChannel) and i not in muted_channels
    ]
    tex_channels = [
        (i, ch) for i, ch in enumerate(channels)
        if isinstance(ch, TextureChannel) and i not in muted_channels
    ]
    auto_master_gain = [
        (i, ch) for i, ch in enumerate(channels)
        if isinstance(ch, AutomationChannel)
        and ch.target_channel is None
        and ch.target_param == "master_gain"
        and i not in muted_channels
    ]
    # Per-channel automation lanes: target a specific PatternChannel's instrument param.
    # Key: target PatternChannel index → list of AutomationChannels.
    from collections import defaultdict as _defaultdict
    auto_per_channel: dict = _defaultdict(list)
    for i, ch in enumerate(channels):
        if (
            isinstance(ch, AutomationChannel)
            and ch.target_channel is not None
            and i not in muted_channels
        ):
            auto_per_channel[ch.target_channel].append(ch)

    grid = Grid(doc.bpm, doc.sr)

    # ---- fallback: no sections → render each channel separately ----
    if not doc.sections:
        total_bars = fallback_length_bars
        total_samples = grid.n_samples(total_bars)
        master_buf = AudioBuffer(total_samples, doc.sr)
        reverb_bus = AudioBuffer(total_samples, doc.sr)
        any_reverb_send = False

        for ci in pat_indices:
            ch = channels[ci]
            pattern_dict = {
                "bpm": doc.bpm,
                "length_bars": total_bars,
                "n_steps": ch.n_steps,
                "tracks": [ch.to_track_dict()],
            }
            seed = doc.seed + ci * 1009
            # Build per-step param override closure if this channel has automation lanes.
            override_fn = None
            if ci in auto_per_channel:
                from forge.arrange.curves import Curve as _Curve
                _curves = {
                    auto_ch.target_param: _Curve(
                        [(b.bar, b.value) for b in auto_ch.breakpoints]
                    )
                    for auto_ch in auto_per_channel[ci]
                    if len(auto_ch.breakpoints) >= 2
                }
                if _curves:
                    def override_fn(bar_idx, step_idx, n_steps, _c=_curves, _off=0):
                        abs_bar = _off + bar_idx + (step_idx / n_steps)
                        return {p: c.at(abs_bar) for p, c in _c.items()}
            from forge.patterns.groove import render_pattern_spec as _rps
            ch_buf = _rps(pattern_dict, seed=seed, param_override=override_fn)
            _apply_gain_pan(ch_buf, ch.gain, ch.pan)
            master_buf.data += ch_buf.data[:total_samples]
            # Accumulate reverb send (after gain+pan so spatial position is preserved).
            rs = ch.reverb_send
            if rs > 0.0:
                reverb_bus.data += ch_buf.data[:total_samples] * rs
                any_reverb_send = True

        # Mix textures into the fallback buffer.
        for _ci, tex_ch in tex_channels:
            tex_buf = render_texture_channel(
                tex_ch, total_bars, doc.bpm, seed=doc.seed, sr=doc.sr
            )
            _apply_gain_pan(tex_buf, tex_ch.gain, tex_ch.pan)
            master_buf.add_at(tex_buf.data, 0.0)
            # Accumulate texture reverb send.
            rs = tex_ch.reverb_send
            if rs > 0.0:
                n_tex = min(len(tex_buf.data), total_samples)
                reverb_bus.data[:n_tex] += tex_buf.data[:n_tex] * rs
                any_reverb_send = True

        # Apply shared reverb bus BEFORE master_gain automation.
        if any_reverb_send:
            _apply_reverb_bus(reverb_bus, master_buf, doc.sr)

        # Apply master-gain automation to the fallback buffer.
        n = master_buf.data.shape[0]
        for _ci, auto_ch in auto_master_gain:
            bps = auto_ch.breakpoints
            if len(bps) < 2:
                continue
            curve = Curve([(b.bar, b.value) for b in bps])
            gain_samples = curve.sample(n, doc.bpm, sr=doc.sr)
            master_buf.data *= gain_samples[:, np.newaxis]

        return master_buf

    # ---- section-aware render ----
    total_bars = sum(s["length_bars"] for s in doc.sections)
    total_samples = grid.n_samples(total_bars)
    master_buf = AudioBuffer(total_samples, doc.sr)
    reverb_bus = AudioBuffer(total_samples, doc.sr)
    any_reverb_send = False

    # Render each PatternChannel independently across all sections.
    for ci in pat_indices:
        ch = channels[ci]
        # Pre-build automation curves for this channel (if any lanes target it).
        ch_auto_curves = {}
        if ci in auto_per_channel:
            from forge.arrange.curves import Curve as _Curve
            for auto_ch in auto_per_channel[ci]:
                if len(auto_ch.breakpoints) >= 2:
                    ch_auto_curves[auto_ch.target_param] = _Curve(
                        [(b.bar, b.value) for b in auto_ch.breakpoints]
                    )

        # Build a full-length per-channel buffer by placing each section at its offset.
        ch_full = AudioBuffer(total_samples, doc.sr)
        start_bar = 0
        for si, sec in enumerate(doc.sections):
            sec_bars = int(sec["length_bars"])
            sec_gain = float(sec.get("gain", 1.0))

            steps = doc.get_section_steps(si, ci)
            step_values = [sd.to_step_value() for sd in steps]
            pattern_dict = {
                "bpm": doc.bpm,
                "length_bars": sec_bars,
                "n_steps": ch.n_steps,
                "tracks": [{
                    "instrument": ch.instrument_id,
                    "steps": step_values,
                    "params": dict(ch.params),
                }],
            }
            # Deterministic, collision-free seed per channel/section pair.
            seed = doc.seed + si + ci * 1009

            # Build per-step param override closure for this section if needed.
            override_fn = None
            if ch_auto_curves:
                def override_fn(bar_idx, step_idx, n_steps,
                                _curves=ch_auto_curves, _off=start_bar):
                    abs_bar = _off + bar_idx + (step_idx / n_steps)
                    return {p: c.at(abs_bar) for p, c in _curves.items()}

            from forge.patterns.groove import render_pattern_spec as _rps
            sec_buf = _rps(pattern_dict, seed=seed, param_override=override_fn)
            ch_full.add_at(sec_buf.data, grid.bar_t(start_bar), gain=sec_gain)
            start_bar += sec_bars

        # Apply per-channel gain + pan then sum into master.
        _apply_gain_pan(ch_full, ch.gain, ch.pan)
        master_buf.data += ch_full.data
        # Accumulate reverb send (after gain+pan so spatial position is preserved).
        rs = ch.reverb_send
        if rs > 0.0:
            reverb_bus.data += ch_full.data * rs
            any_reverb_send = True

    # Mix each TextureChannel over the full song length at t=0.
    for _ci, tex_ch in tex_channels:
        tex_buf = render_texture_channel(
            tex_ch, total_bars, doc.bpm, seed=doc.seed, sr=doc.sr
        )
        _apply_gain_pan(tex_buf, tex_ch.gain, tex_ch.pan)
        master_buf.add_at(tex_buf.data, 0.0)
        # Accumulate texture reverb send.
        rs = tex_ch.reverb_send
        if rs > 0.0:
            n_tex = min(len(tex_buf.data), total_samples)
            reverb_bus.data[:n_tex] += tex_buf.data[:n_tex] * rs
            any_reverb_send = True

    # Apply shared reverb bus BEFORE master_gain automation.
    if any_reverb_send:
        _apply_reverb_bus(reverb_bus, master_buf, doc.sr)

    # Apply master-gain automation curves (multiply together when >1 lane).
    n = master_buf.data.shape[0]
    for _ci, auto_ch in auto_master_gain:
        bps = auto_ch.breakpoints
        if len(bps) < 2:
            continue
        curve = Curve([(b.bar, b.value) for b in bps])
        gain_samples = curve.sample(n, doc.bpm, sr=doc.sr)
        master_buf.data *= gain_samples[:, np.newaxis]

    return master_buf


def _render_for_fold(
    doc: "forge.document.model.ProjectDoc",  # type: ignore[name-defined]
    total_bars: float,
    *,
    xf_bars: float = 2.0,
    warmup_bars: int = 2,
    muted_channels: "set[int] | None" = None,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a doc with a warmup prefix, then fold into a seamless loop.

    A clickless seam needs the loop body to start already in steady state — the
    decay tails of the previous cycle's hits must be present at bar 0.  We get
    that by rendering ``warmup_bars + total_bars`` bars as ONE continuous pattern
    (so hits ring across the bar grid) and discarding the leading *warmup_bars*
    inside ``_fold_doc_buffer``.

    LIMITATION: the continuous render uses each channel's *default* steps (the
    section-free fallback path), NOT per-section ``channel_steps`` overrides.
    Honouring overrides here would require a cross-section continuous render
    (sections currently cut decay tails at their boundary), which is out of
    scope.  In practice seamless loops are single repeating game-state patterns
    (``arrakis_winds``/``spice_must_flow``/``stillsuit``/``sandstorm``), whose
    loop *is* the channel default, so this is not a limitation for the intended
    use.  Normal (non-seamless) playback/export is unaffected and fully
    section-aware.

    Args:
        doc:            Live ProjectDoc.
        total_bars:     The desired loop length in bars.
        xf_bars:        Crossfade width in bars.
        warmup_bars:    Extra bars to render before the loop (discarded after fold).
        muted_channels: Channels to skip.
    """
    extended_bars = warmup_bars + int(total_bars)
    big_buf = _render_doc_sections(
        _SectionlessDocView(doc),  # type: ignore[arg-type]
        muted_channels=muted_channels,
        fallback_length_bars=extended_bars,
    )
    return _fold_doc_buffer(big_buf, total_bars, doc.bpm, doc.sr, xf_bars, warmup_bars=warmup_bars)


class _SectionlessDocView:
    """Read-only ProjectDoc proxy that hides sections, forcing the fallback
    (single repeating pattern) render path in ``_render_doc_sections``."""

    def __init__(self, d: "forge.document.model.ProjectDoc") -> None:  # type: ignore[name-defined]
        self._d = d

    @property
    def sections(self) -> list:
        return []

    @property
    def channels(self):
        return self._d.channels

    @property
    def bpm(self) -> float:
        return self._d.bpm

    @property
    def sr(self) -> int:
        return self._d.sr

    @property
    def seed(self) -> int:
        return self._d.seed

    def get_section_steps(self, si, ci):
        return self._d.get_section_steps(si, ci)


def _fold_doc_buffer(
    body: "forge.core.buffer.AudioBuffer",  # type: ignore[name-defined]
    total_bars: float,
    bpm: float,
    sr: int,
    xf_bars: float,
    *,
    warmup_bars: int = 2,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Fold *body* into a seamless loop buffer of exactly *total_bars* bars.

    A looping song's natural continuation after its end IS its head, so we
    replay the head of the *stable* body as the crossfade tail before folding.

    To ensure the loop body is in a steady state (instruments already ringing
    with correct pre-ring from the previous cycle), *body* should be
    ``warmup_bars + total_bars`` bars long.  The first *warmup_bars* are
    discarded and only the tail ``total_bars`` portion is used for the loop.
    If *body* is exactly *total_bars* bars long (legacy callers), the warmup
    step is skipped gracefully.

    Args:
        body:         Render buffer — either ``total_bars`` long (no pre-roll)
                      or ``(warmup_bars + total_bars)`` bars long (pre-rolled).
        total_bars:   Desired loop length in bars.
        bpm:          Project tempo.
        sr:           Sample rate.
        xf_bars:      Crossfade width in bars (clamped to ``total_bars / 2``).
        warmup_bars:  Number of leading bars to discard from *body* before
                      folding (default 2).  Pass 0 to disable.
    """
    from forge.core.buffer import AudioBuffer
    from forge.core.grid import Grid
    from forge.core.loopfold import loop_fold as _lf

    grid = Grid(bpm, sr)
    # Clamp xf_bars so the extended buffer works and to avoid trivial loops.
    xf_bars = min(float(xf_bars), total_bars / 2.0)
    n_xf = int(round(xf_bars * grid.bar * sr))
    n_loop = grid.n_samples(total_bars)

    if n_xf <= 0 or n_loop <= 0:
        return body  # nothing meaningful to fold

    # Determine if body contains a warmup prefix.
    # Use the actual buffer length to derive the warmup offset, which avoids
    # floating-point accumulation errors in bar→samples conversion.
    if warmup_bars > 0 and len(body) > n_loop:
        n_warmup = len(body) - n_loop  # whatever's left before the loop portion
        stable = AudioBuffer(n_loop, sr)
        stable.data[:] = body.data[n_warmup: n_warmup + n_loop]
    else:
        # Body is already the right length; use it directly.
        stable = body

    # Build an extended buffer: stable loop body + head-replay as the xf tail.
    ext = AudioBuffer(n_loop + n_xf, sr)
    ext.data[:n_loop] = stable.data[:n_loop]
    # Replay the head into the crossfade tail region.
    ext.data[n_loop: n_loop + n_xf] += stable.data[:n_xf]
    return _lf(ext, total_bars, xf_bars, grid)


def export_wav_from_doc(
    doc: "forge.document.model.ProjectDoc",  # type: ignore[name-defined]
    path: "Path",
    *,
    length_bars: int | None = None,
    loop_fold: bool = False,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a ``ProjectDoc``'s pattern channels and write to a WAV file.

    All ``PatternChannel`` entries are rendered together as a single pattern
    mix.  Texture and automation channels are currently skipped (their
    rendering is handled separately via ``render_texture_channel``).

    Args:
        doc:          Live ProjectDoc.
        path:         Output WAV path.
        length_bars:  Override render length.  If *None*, inferred from the
                      doc's sections (or defaults to 8 bars).
        loop_fold:    If *True*, apply loop folding for a seamless loop
                      suitable for game state music.  Also activated when
                      ``doc.seamless_loop`` is True.
    """
    from forge.core.mastering import master, write_wav

    if length_bars is None:
        if doc.sections:
            length_bars = sum(s["length_bars"] for s in doc.sections)
        else:
            length_bars = 8

    should_fold = loop_fold or doc.seamless_loop
    if should_fold:
        xf_bars = getattr(doc, "loop_xf_bars", 2.0)
        buf = _render_for_fold(doc, length_bars, xf_bars=xf_bars)
    else:
        buf = _render_doc_sections(doc, fallback_length_bars=length_bars)

    buf = master(buf)
    write_wav(buf, Path(path))
    return buf


def render_doc_for_playback(
    doc: "forge.document.model.ProjectDoc",  # type: ignore[name-defined]
    *,
    muted_channels: "set[int] | None" = None,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render all (non-muted) PatternChannels to a single AudioBuffer for live playback.

    Like ``export_wav_from_doc`` but returns the buffer without writing a file.
    Used by the Play button to render the project before handing off to
    PlaybackService.

    When ``doc.seamless_loop`` is True the buffer is folded before mastering so
    that the player (which already loops the buffer at its boundary) loops
    without an audible click at the wrap point.

    Args:
        doc:             Live ProjectDoc.
        muted_channels:  Set of channel indices to skip (muted in the UI).
    """
    from forge.core.mastering import master

    if muted_channels is None:
        muted_channels = set()

    if doc.sections:
        fallback_length_bars = sum(s["length_bars"] for s in doc.sections)
    else:
        fallback_length_bars = 8

    if doc.seamless_loop:
        xf_bars = getattr(doc, "loop_xf_bars", 2.0)
        core = _render_for_fold(doc, fallback_length_bars, xf_bars=xf_bars, muted_channels=muted_channels)
    else:
        core = _render_doc_sections(doc, muted_channels=muted_channels, fallback_length_bars=fallback_length_bars)

    return master(core)


def loop_seam_report(
    doc: "forge.document.model.ProjectDoc",  # type: ignore[name-defined]
    *,
    length_bars: int | None = None,
) -> dict:
    """Render + fold *doc* and return a full loop quality report.

    The report is produced by ``forge.analysis.loops.full_loop_report`` and
    includes both seam-discontinuity and RMS-flatness sub-reports.

    Args:
        doc:          Live ProjectDoc.
        length_bars:  Override render length.  If *None*, inferred from doc.

    Returns::

        {
            "seam": {"discontinuity": float, "ok": bool, ...},
            "flatness": {"slope": float, "ok": bool, ...},
            "ok": bool,
        }
    """
    from forge.analysis.loops import full_loop_report

    if length_bars is None:
        if doc.sections:
            length_bars = sum(s["length_bars"] for s in doc.sections)
        else:
            length_bars = 8

    xf_bars = getattr(doc, "loop_xf_bars", 2.0)
    folded = _render_for_fold(doc, length_bars, xf_bars=xf_bars)
    return full_loop_report(folded)


def seam_report(
    buf: "forge.core.buffer.AudioBuffer",  # type: ignore[name-defined]
    *,
    tolerance: float = 0.05,
) -> dict:
    """Return the seam-discontinuity report for an already-folded buffer.

    Thin passthrough to ``forge.analysis.loops.seam_report`` so the UI never
    imports ``forge.analysis`` directly.

    Args:
        buf:       Already-folded AudioBuffer.
        tolerance: Maximum acceptable discontinuity (0–1 scale).
    """
    from forge.analysis.loops import seam_report as _sr
    return _sr(buf, tolerance=tolerance)


def render_texture_channel(
    channel: "forge.document.channels.TextureChannel",  # type: ignore[name-defined]
    length_bars: int,
    bpm: float,
    *,
    seed: int = 0,
    sr: int = 44100,
) -> "forge.core.buffer.AudioBuffer":  # type: ignore[name-defined]
    """Render a TextureChannel with its envelope applied as a gain curve.

    The instrument is rendered at the full length derived from *length_bars* and
    *bpm*.  If the channel has envelope breakpoints, they are applied as a
    piecewise-linear gain multiplier (0.0–1.0 range) over time.

    Args:
        channel:     A TextureChannel from ``forge.document.channels``.
        length_bars: Render length in bars.
        bpm:         Project tempo.
        seed:        RNG seed.
        sr:          Sample rate.
    """
    import numpy as np
    from forge.document.channels import TextureChannel as _TexCh
    if not isinstance(channel, _TexCh):
        raise TypeError("render_texture_channel expects a TextureChannel")

    bar_dur_s = 4.0 * 60.0 / bpm  # seconds per bar
    duration_s = float(length_bars) * bar_dur_s

    params = dict(channel.params)
    params["duration"] = duration_s

    buf = render_instrument(channel.instrument_id, params, seed=seed + channel.seed)

    if channel.envelope:
        sorted_env = sorted(channel.envelope, key=lambda b: b.bar)
        bar_dur_samples = sr * bar_dur_s
        xs = np.array([b.bar * bar_dur_samples for b in sorted_env])
        ys = np.array([b.value for b in sorted_env])
        n = buf.data.shape[0]
        t = np.arange(n, dtype=np.float64)
        gain = np.interp(t, xs, ys, left=ys[0], right=ys[-1])
        buf.data *= gain[:, np.newaxis]

    return buf
