"""AudioBuffer — stereo float64 buffer with time-indexed helpers.

The canonical representation for all audio in forge: a (N, 2) float64 array
paired with a sample rate.  All layers are rendered into AudioBuffers and
committed into a MixBus; intermediate float arrays should not be kept alive
longer than needed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class AudioBuffer:
    """Stereo float64 audio buffer.

    Attributes:
        data: (N, 2) float64 ndarray, channels 0=L, 1=R.
        sr:   Sample rate in Hz (default 44100).
    """

    def __init__(self, n_samples: int, sr: int = 44100) -> None:
        self.data: np.ndarray = np.zeros((n_samples, 2), dtype=np.float64)
        self.sr: int = sr

    # ---------------------------------------------------------------- factories

    @classmethod
    def from_stereo(
        cls, L: np.ndarray, R: np.ndarray, sr: int = 44100
    ) -> "AudioBuffer":
        """Create a buffer from two mono arrays of equal length."""
        if len(L) != len(R):
            raise ValueError(f"L/R length mismatch: {len(L)} vs {len(R)}")
        buf = cls(len(L), sr)
        buf.data[:, 0] = L
        buf.data[:, 1] = R
        return buf

    @classmethod
    def from_mono(cls, x: np.ndarray, sr: int = 44100) -> "AudioBuffer":
        """Broadcast a mono signal to both channels."""
        buf = cls(len(x), sr)
        buf.data[:, 0] = x
        buf.data[:, 1] = x
        return buf

    # ---------------------------------------------------------------- properties

    @property
    def L(self) -> np.ndarray:
        """View of the left channel (do not resize)."""
        return self.data[:, 0]

    @property
    def R(self) -> np.ndarray:
        """View of the right channel (do not resize)."""
        return self.data[:, 1]

    def __len__(self) -> int:
        return len(self.data)

    def len_seconds(self) -> float:
        return len(self.data) / self.sr

    # ---------------------------------------------------------------- metrics

    def peak(self) -> float:
        """Peak absolute amplitude across both channels."""
        return float(np.max(np.abs(self.data)))

    def peak_channel(self, ch: int) -> float:
        return float(np.max(np.abs(self.data[:, ch])))

    def rms(self) -> float:
        """Overall RMS across both channels."""
        return float(np.sqrt(np.mean(self.data ** 2)))

    def rms_channel(self, ch: int) -> float:
        return float(np.sqrt(np.mean(self.data[:, ch] ** 2)))

    def section_rms(self, n_sections: int = 8) -> list[float]:
        """Per-section RMS (n_sections equal-length slices, both channels)."""
        size = len(self.data) // n_sections
        return [
            float(np.sqrt(np.mean(self.data[i * size : (i + 1) * size] ** 2)))
            for i in range(n_sections)
        ]

    # ---------------------------------------------------------------- mutation

    def normalize(self, target: float = 0.85) -> "AudioBuffer":
        """Peak-normalize in place; returns self."""
        pk = self.peak()
        if pk > 1e-12:
            self.data *= target / pk
        return self

    def add_at(
        self,
        x: np.ndarray,
        start_s: float,
        gain: float = 1.0,
    ) -> None:
        """Add *x* into this buffer at *start_s* seconds, bounds-safe.

        *x* may be:
          - 1-D mono (N,): added to both channels.
          - 2-D stereo (N, 2): added to both channels directly.
        """
        i0 = int(start_s * self.sr)
        if i0 >= len(self.data) or i0 + len(x) <= 0:
            return
        # handle negative start_s (x starts before buffer origin)
        x_off = max(0, -i0)
        i0 = max(0, i0)
        n = min(len(self.data) - i0, len(x) - x_off)
        if n <= 0:
            return
        src = x[x_off : x_off + n]
        if src.ndim == 1:
            self.data[i0 : i0 + n, 0] += src * gain
            self.data[i0 : i0 + n, 1] += src * gain
        else:
            self.data[i0 : i0 + n] += src * gain

    def add_at_pan(
        self,
        x: np.ndarray,
        start_s: float,
        pan: float,
        gain: float = 1.0,
    ) -> None:
        """Add mono *x* at *start_s* with constant-power *pan* (0=L, 1=R)."""
        angle = pan * np.pi / 2.0
        self.add_at(
            np.column_stack([
                x * np.cos(angle),
                x * np.sin(angle),
            ]),
            start_s,
            gain,
        )

    def copy(self) -> "AudioBuffer":
        buf = AudioBuffer(len(self.data), self.sr)
        buf.data[:] = self.data
        return buf

    def zero(self) -> None:
        """Zero out all samples in place."""
        self.data[:] = 0.0
