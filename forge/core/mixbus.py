"""MixBus — commit-and-free weighted mix accumulator.

Each layer renders into its own temporary arrays, calls `MixBus.commit()`,
then lets those arrays go out of scope.  The bus accumulates the weighted,
peak-normalized contributions without ever holding all layers in memory at
once.

The optional `env` argument to `commit` is an array of the same length as the
layer; it is applied *before* normalization so it does not distort the mix
weights relative to each other.
"""

from __future__ import annotations

import numpy as np

from forge.core.buffer import AudioBuffer


class MixBus:
    """Accumulates peak-normalized, weighted layers into a stereo mix.

    Args:
        n_samples: Total buffer length in samples.
        sr:        Sample rate in Hz (default 44100).
    """

    def __init__(self, n_samples: int, sr: int = 44100) -> None:
        self._n: int = n_samples
        self.sr: int = sr
        self._L: np.ndarray = np.zeros(n_samples, dtype=np.float64)
        self._R: np.ndarray = np.zeros(n_samples, dtype=np.float64)
        self._n_layers: int = 0

    # ---------------------------------------------------------------- commit

    def commit(
        self,
        L: np.ndarray,
        R: np.ndarray,
        weight: float,
        env: np.ndarray | None = None,
    ) -> None:
        """Add a layer to the mix.

        The layer is peak-normalized then scaled by *weight*.  If *env* is
        given it is multiplied into the layer first (e.g. section ducking or
        the "harvester listens" silence envelope from spice_must_flow).

        After this call the caller should discard L and R; their memory is no
        longer needed.
        """
        if env is not None:
            L = L * env
            R = R * env

        peak = max(float(np.max(np.abs(L))), float(np.max(np.abs(R))), 1e-12)
        norm = weight / peak

        # lengths may differ if a layer is shorter than the full track
        n = min(self._n, len(L), len(R))
        self._L[:n] += L[:n] * norm
        self._R[:n] += R[:n] * norm
        self._n_layers += 1

    def commit_buffer(
        self,
        buf: AudioBuffer,
        weight: float,
        env: np.ndarray | None = None,
    ) -> None:
        """Convenience overload that accepts an AudioBuffer."""
        self.commit(buf.L, buf.R, weight, env)

    # ---------------------------------------------------------------- read

    @property
    def n_layers(self) -> int:
        """Number of layers committed so far."""
        return self._n_layers

    def render(self) -> AudioBuffer:
        """Return the accumulated mix as an AudioBuffer (does not consume the bus).

        The returned buffer is a *copy*; the bus continues to accumulate.
        """
        return AudioBuffer.from_stereo(self._L.copy(), self._R.copy(), self.sr)

    def render_peak(self) -> float:
        """Peak amplitude of the current accumulated mix."""
        return max(float(np.max(np.abs(self._L))),
                   float(np.max(np.abs(self._R))))

    def reset(self) -> None:
        """Zero the accumulator and layer count (reuse the bus for a new render)."""
        self._L[:] = 0.0
        self._R[:] = 0.0
        self._n_layers = 0
