"""forge.arrange.transitions — cuts, crossfades, and boundary-aligned risers.

Transitions glue sections together.  They operate on rendered AudioBuffers
(not schedules), so they are always a post-render step.

Available:
    crossfade(a, b, xf_samples) → AudioBuffer (equal-power)
    hard_cut(a, b, cut_sample)  → AudioBuffer (sample-accurate cut)
    insert_riser(buf, bar, bpm, rng, *, sr) → None  (adds in-place)
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.rng import RngContext


def crossfade(
    buf_a: AudioBuffer,
    buf_b: AudioBuffer,
    xf_samples: int,
) -> AudioBuffer:
    """Equal-power crossfade between *buf_a* (fading out) and *buf_b* (fading in).

    The result has length ``len(buf_a) + len(buf_b) - xf_samples``.  The
    cross-fade window is centred at the join point.

    Args:
        buf_a:      first buffer (its tail fades out).
        buf_b:      second buffer (its head fades in).
        xf_samples: crossfade overlap length in samples.
    """
    sr = buf_a.sr
    n_a = len(buf_a)
    n_b = len(buf_b)
    xf = min(xf_samples, n_a, n_b)

    out_n = n_a + n_b - xf
    out = AudioBuffer(out_n, sr=sr)

    # straight copy of non-overlapping head of a
    out.data[:n_a - xf] = buf_a.data[:n_a - xf]

    # overlap region: a fades out, b fades in
    t = np.arange(xf, dtype=np.float64) / xf
    fade_out = np.cos(t * np.pi / 2.0)
    fade_in = np.sin(t * np.pi / 2.0)

    a_tail = buf_a.data[n_a - xf:]
    b_head = buf_b.data[:xf]
    blend = a_tail * fade_out[:, np.newaxis] + b_head * fade_in[:, np.newaxis]
    out.data[n_a - xf : n_a] = blend

    # straight copy of non-overlapping tail of b
    out.data[n_a:] = buf_b.data[xf:]

    return out


def hard_cut(
    buf_a: AudioBuffer,
    buf_b: AudioBuffer,
    cut_sample: int | None = None,
) -> AudioBuffer:
    """Concatenate *buf_a* and *buf_b* with a sample-accurate hard cut.

    Args:
        buf_a:       first buffer.
        buf_b:       second buffer.
        cut_sample:  sample in *buf_a* at which to cut (default: end of buf_a).
    """
    if cut_sample is None:
        cut_sample = len(buf_a)
    cut_sample = max(0, min(cut_sample, len(buf_a)))
    out_n = cut_sample + len(buf_b)
    out = AudioBuffer(out_n, sr=buf_a.sr)
    out.data[:cut_sample] = buf_a.data[:cut_sample]
    out.data[cut_sample:] = buf_b.data
    return out


def insert_riser(
    buf: AudioBuffer,
    bar: float,
    bpm: float,
    rng_ctx: RngContext,
    *,
    duration_bars: float = 2.0,
    sr: int = 44100,
) -> None:
    """Add a rev-cymbal riser into *buf* at *bar* (in-place).

    The riser peaks at bar + duration_bars, which should align with a
    section boundary (drop or verse start).

    Args:
        buf:           track buffer to modify.
        bar:           start bar of the riser (where it begins building).
        bpm:           tempo.
        rng_ctx:       RngContext for the riser render.
        duration_bars: length of the riser in bars.
        sr:            sample rate.
    """
    from forge.instruments.registry import get_instrument

    grid = Grid(bpm, sr=sr)
    dur_s = duration_bars * grid.bar
    rng = rng_ctx.spawn("riser").rng
    riser_buf = get_instrument("rev_cymbal")["fn"](
        {"duration": dur_s}, rng
    )
    t = grid.bar_t(bar)
    buf.add_at(riser_buf.data, t, gain=0.4)
