"""forge.arrange.track — top-level track orchestration.

A Track holds an ordered list of Sections, renders them into a shared buffer,
applies optional Curve automation, and finally masters the result.

Usage::

    track = Track(bpm=138.0, title="Sleeper Awakens")
    track.add_section(intro)
    track.add_section(drop)
    track.add_curve(master_gain_curve)
    buf = track.render(seed=130)
    from forge.core.mastering import write_wav
    write_wav(buf, Path("out/sleeper_awakens.wav"))

control.render_track delegates here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from forge.arrange.section import Section
from forge.core.buffer import AudioBuffer
from forge.core.grid import Grid
from forge.core.mastering import master, write_wav
from forge.core.rng import RngContext
from forge.instruments.base import RenderCache


class Track:
    """Orchestrates sections into a finished AudioBuffer.

    Args:
        bpm:    Tempo.  All sections must share the same tempo (no tempo
                automation in this phase).
        title:  Used as the RNG key root.
        sr:     Sample rate.
    """

    def __init__(self, bpm: float, *, title: str = "track", sr: int = 44100) -> None:
        if bpm <= 0:
            raise ValueError(f"bpm must be positive, got {bpm}")
        self.bpm = bpm
        self.title = title
        self.sr = sr
        self._sections: list[Section] = []
        self._master_gain_curve: "forge.arrange.curves.Curve | None" = None  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Building

    def add_section(self, section: Section) -> "Track":
        """Append *section*.  Returns self for chaining."""
        self._sections.append(section)
        return self

    def set_master_gain_curve(self, curve: "forge.arrange.curves.Curve") -> "Track":  # type: ignore[name-defined]
        """Apply a Curve to the final master buffer after mixing."""
        self._master_gain_curve = curve
        return self

    # ------------------------------------------------------------------
    # Rendering

    def total_bars(self) -> int:
        """Total track length in bars (end of last section)."""
        if not self._sections:
            return 0
        return max(s.end_bar for s in self._sections)

    def render(
        self,
        seed: int = 0,
        *,
        cache: RenderCache | None = None,
        normalize: bool = True,
        target: float = 0.85,
        fade_out_s: float = 2.0,
        output_path: Path | None = None,
    ) -> AudioBuffer:
        """Render all sections into one mastered AudioBuffer.

        Args:
            seed:        RNG seed.
            cache:       optional shared RenderCache.
            normalize:   peak-normalize to *target*.
            target:      peak target (0.0–1.0).
            fade_out_s:  fade-out applied by mastering (seconds).
            output_path: if given, the WAV is also written here.
        """
        grid = Grid(self.bpm, sr=self.sr)
        total_n = grid.n_samples(self.total_bars())
        buf = AudioBuffer(total_n, sr=self.sr)

        rng_root = RngContext(seed).spawn(self.title)

        for sec in self._sections:
            sec_ctx = rng_root.spawn(sec.name)
            sec_buf = sec.render(sec_ctx, cache=cache, sr=self.sr)
            t = grid.bar_t(sec.start_bar)
            buf.add_at(sec_buf.data, t)

        # apply master gain curve if set
        if self._master_gain_curve is not None:
            curve_samples = self._master_gain_curve.sample(
                total_n, self.bpm, sr=self.sr
            )
            buf.data *= curve_samples[:, np.newaxis]

        mastered = master(
            buf,
            target=target if normalize else 1.0,
            fade_out_s=fade_out_s,
            limit=True,
        )

        if output_path is not None:
            write_wav(mastered, output_path, normalize=False)

        return mastered

    # ------------------------------------------------------------------
    # Serialisation helpers

    def to_dict(self) -> dict[str, Any]:
        """Minimal metadata dict (no schedule data — not a full spec)."""
        return {
            "title": self.title,
            "bpm": self.bpm,
            "sr": self.sr,
            "total_bars": self.total_bars(),
            "n_sections": len(self._sections),
        }
