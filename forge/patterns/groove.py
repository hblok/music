"""forge.patterns.groove — render a Schedule into an AudioBuffer.

``render_groove`` is the core engine: it iterates the bar/step grid,
resolves probability rolls, spawns per-hit RNG streams, and places each
instrument hit into a mix buffer.

``render_loop`` extends it with ``loop_fold`` for seamless game-state loops.

PatternSpec dict → Schedule → render_groove → AudioBuffer (→ loop_fold).
"""

from __future__ import annotations

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.loopfold import loop_fold
from forge.core.rng import RngContext
from forge.instruments.base import RenderCache, render_cached
from forge.instruments.registry import get_instrument
from forge.patterns.schedule import Schedule
from forge.patterns.step import StepPattern


def render_groove(
    schedule: Schedule,
    rng_ctx: RngContext,
    *,
    cache: RenderCache | None = None,
    sr: int = 44100,
) -> AudioBuffer:
    """Render *schedule* to an AudioBuffer.

    Each hit gets a deterministic RNG stream derived from
    ``rng_ctx.spawn(f"b{bar}p{pat_idx}s{step_idx}")``, so:
    - probability rolls are reproducible
    - instrument renders are reproducible
    - reordering tracks does NOT change per-track streams (each track is
      identified by its position in the pattern list for that bar)

    Args:
        schedule:  populated Schedule to render.
        rng_ctx:   seeded RngContext; call ``RngContext(seed)`` to create.
        cache:     optional RenderCache to reuse identical hits.
        sr:        sample rate (must match schedule intent).
    """
    grid = Grid(schedule.bpm, sr=sr)
    total_n = grid.n_samples(schedule.length_bars)
    buf = AudioBuffer(total_n, sr=sr)

    step_dur = grid.bar / 16  # base: 16th-note grid

    for bar_idx in range(schedule.length_bars):
        patterns = schedule.get_patterns(bar_idx)
        for pat_idx, pattern in enumerate(patterns):
            entry = get_instrument(pattern.instrument_id)
            step_t = grid.bar / pattern.n_steps  # actual step duration for this pattern

            for step_idx, step in pattern.hits():
                hit_ctx = rng_ctx.spawn(f"b{bar_idx}p{pat_idx}s{step_idx}")

                if step.probability < 1.0:
                    if hit_ctx.rng.random() > step.probability:
                        continue

                iid_rng = hit_ctx.spawn(step.instrument_id)
                hit_buf = render_cached(
                    step.instrument_id,
                    entry["fn"],
                    step.params,
                    iid_rng.rng,
                    cache=cache,
                )

                gain = 1.5 if step.accent else (0.4 if step.ghost else 1.0)
                gain *= step.velocity
                t = grid.bar_t(bar_idx) + step_idx * step_t
                buf.add_at(hit_buf.data, t, gain=gain)

    return buf


def render_loop(
    schedule: Schedule,
    rng_ctx: RngContext,
    *,
    xf_bars: float = 2.0,
    cache: RenderCache | None = None,
    sr: int = 44100,
) -> AudioBuffer:
    """Render *schedule* and apply loop_fold for a seamless game loop.

    Renders ``length_bars + xf_bars`` of content by cycling the schedule,
    then applies equal-power loop_fold so the seam is inaudible.

    Args:
        schedule:  populated Schedule.
        rng_ctx:   seeded RngContext.
        xf_bars:   crossfade width in bars (default 2).
        cache:     optional RenderCache.
        sr:        sample rate.
    """
    import math

    grid = Grid(schedule.bpm, sr=sr)
    # Match loop_fold's own rounding so len(buf) == n_loop + n_xf exactly.
    n_loop = int(round(schedule.length_bars * grid.bar * sr))
    n_xf = int(round(xf_bars * grid.bar * sr))
    total_n = n_loop + n_xf
    total_bars = total_n / (grid.bar * sr)
    buf = AudioBuffer(total_n, sr=sr)

    n_bars_ceil = math.ceil(total_bars)
    for bar_abs in range(n_bars_ceil):
        bar_sched = bar_abs % schedule.length_bars
        t_bar = bar_abs * grid.bar
        if t_bar >= total_bars * grid.bar:
            break

        for pat_idx, pattern in enumerate(schedule.get_patterns(bar_sched)):
            entry = get_instrument(pattern.instrument_id)
            step_t = grid.bar / pattern.n_steps

            for step_idx, step in pattern.hits():
                hit_ctx = rng_ctx.spawn(f"b{bar_sched}p{pat_idx}s{step_idx}")

                if step.probability < 1.0:
                    if hit_ctx.rng.random() > step.probability:
                        continue

                iid_rng = hit_ctx.spawn(step.instrument_id)
                hit_buf = render_cached(
                    step.instrument_id,
                    entry["fn"],
                    step.params,
                    iid_rng.rng,
                    cache=cache,
                )

                gain = 1.5 if step.accent else (0.4 if step.ghost else 1.0)
                gain *= step.velocity
                t = t_bar + step_idx * step_t
                buf.add_at(hit_buf.data, t, gain=gain)

    return loop_fold(buf, schedule.length_bars, xf_bars, grid)


def render_pattern_spec(
    spec: dict,
    seed: int = 0,
    *,
    cache: RenderCache | None = None,
    sr: int = 44100,
) -> AudioBuffer:
    """Top-level convenience: PatternSpec dict → AudioBuffer.

    This is what ``control.render_pattern`` delegates to.

    Args:
        spec:  PatternSpec dict (see forge.patterns.step module docstring).
        seed:  RNG seed.
        cache: optional RenderCache.
        sr:    sample rate.
    """
    from forge.patterns.schedule import Schedule

    sched = Schedule.from_pattern_spec(spec)
    rng_ctx = RngContext(seed).spawn("pattern")
    loop = bool(spec.get("loop", False))

    if loop:
        xf_bars = float(spec.get("xf_bars", 2.0))
        return render_loop(sched, rng_ctx, xf_bars=xf_bars, cache=cache, sr=sr)
    return render_groove(sched, rng_ctx, cache=cache, sr=sr)
