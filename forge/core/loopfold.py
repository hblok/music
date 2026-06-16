"""forge.core.loopfold — on-grid seamless loop folding.

The "v3 fold" pattern used in spice_must_flow and other game-state loops:
render ``N + XF`` samples (where XF is a grid-aligned crossfade tail), then
equal-power overlap-add the tail back onto the head so the loop seam lands
exactly on a bar boundary and the groove phase is consistent across the wrap.

Usage::

    grid = Grid(bpm=64.0)
    xf_bars = 2
    # render to an extended buffer (BARS + xf_bars bars)
    full_buf = ...
    looped = loop_fold(full_buf, loop_bars=BARS, xf_bars=xf_bars, grid=grid)
    # looped is exactly BARS bars long and loops seamlessly
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid


def loop_fold(
    buf: AudioBuffer,
    loop_bars: float,
    xf_bars: float,
    grid: Grid,
) -> AudioBuffer:
    """Overlap-add the tail of *buf* onto the head to create a seamless loop.

    *buf* must be at least ``loop_bars + xf_bars`` bars long (rendered with the
    extra tail).  The output is exactly ``loop_bars`` bars (rounded to the
    nearest sample).

    The crossfade is an equal-power (sine/cosine) blend over the XF region:
      - The main body fades *out* over the XF region.
      - The tail (which will wrap to the start) fades *in* over the same region.

    This is the "v3 fold" in spice_must_flow.py.
    """
    sr = buf.sr
    n_loop = int(round(loop_bars * grid.bar * sr))
    n_xf = int(round(xf_bars * grid.bar * sr))

    if len(buf) < n_loop + n_xf:
        raise ValueError(
            f"Buffer length {len(buf)} < loop ({n_loop}) + xf ({n_xf}) samples"
        )

    out = AudioBuffer(n_loop, sr)
    # copy the main loop body
    out.data[:] = buf.data[:n_loop]

    # equal-power crossfade window
    xf_t = np.arange(n_xf, dtype=np.float64) / n_xf  # 0..1
    fade_out = np.cos(xf_t * np.pi / 2.0)            # 1 → 0
    fade_in = np.sin(xf_t * np.pi / 2.0)             # 0 → 1

    # blend the end of the loop region with the start of the tail
    # the tail starts at sample n_loop
    tail = buf.data[n_loop : n_loop + n_xf]
    n_blend = min(n_xf, n_loop, len(tail))

    out.data[:n_blend] = (
        out.data[:n_blend] * fade_in[:n_blend, np.newaxis]
        + tail[:n_blend] * fade_out[:n_blend, np.newaxis]
    )
    out.data[n_loop - n_blend : n_loop] = (
        out.data[n_loop - n_blend : n_loop] * fade_out[:n_blend, np.newaxis]
        + tail[:n_blend] * fade_in[:n_blend, np.newaxis]
    )

    return out


def check_seam(
    buf: AudioBuffer,
    tolerance: float = 0.05,
) -> dict:
    """Check the sample-level continuity at the loop seam (start and end).

    Returns a dict with:
      ``"start_sample"``, ``"end_sample"``: float64 amplitude at first/last sample.
      ``"discontinuity"``: abs difference between them (lower is better).
      ``"ok"``: True if discontinuity < *tolerance*.
    """
    start_L = float(buf.L[0])
    end_L = float(buf.L[-1])
    start_R = float(buf.R[0])
    end_R = float(buf.R[-1])
    disc = max(abs(end_L - start_L), abs(end_R - start_R))
    return {
        "start_L": start_L,
        "end_L": end_L,
        "start_R": start_R,
        "end_R": end_R,
        "discontinuity": disc,
        "ok": disc < tolerance,
    }
