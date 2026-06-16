"""RngContext — hierarchical seeded RNG contexts.

The core determinism guarantee: given the same master seed and the same
sequence of child names, every `RngContext.spawn()` chain produces the same
`np.random.Generator` state every time, independent of what other children
exist.

Design:
  - A `RngContext` wraps `np.random.SeedSequence` so that parent→child paths
    are encoded as entropy lists: `SeedSequence([master, child_int, ...])`.
  - Child integers are derived from the string key via a deterministic CRC32
    hash (no Python hash-randomization).
  - Two children from the same parent with different keys produce independent
    streams; reordering children does not affect each other.
  - The root's `.rng` draws are *separate* from any child's draws (each gets
    its own SeedSequence leaf).

Usage::

    ctx = RngContext(42)
    kick_rng  = ctx.spawn("kick").rng
    piano_rng = ctx.spawn("piano").rng
    # Both are independent; neither is affected by the other being spawned.
"""

from __future__ import annotations

import zlib

import numpy as np


def _key_to_int(key: str) -> int:
    """Deterministic (process-stable) integer from a string key."""
    return zlib.crc32(key.encode("utf-8")) & 0xFFFFFFFF


class RngContext:
    """A node in a hierarchical RNG tree.

    Args:
        seed:  Master seed (int or None for a random seed).
        _path: Internal entropy path; do not pass manually.
    """

    def __init__(self, seed: int, _path: tuple[int, ...] = ()) -> None:
        self._seed: int = seed
        self._path: tuple[int, ...] = _path
        # build entropy list: [master, ...path_ints]
        entropy: list[int] | int = (
            [seed, *_path] if _path else seed
        )
        self._seq = np.random.SeedSequence(entropy)
        self._rng = np.random.default_rng(self._seq)

    # ---------------------------------------------------------------- core API

    @property
    def rng(self) -> np.random.Generator:
        """The `numpy.random.Generator` for this context node."""
        return self._rng

    def spawn(self, key: str) -> "RngContext":
        """Return a child `RngContext` derived from *key*.

        The child is independent of all siblings and of the parent's own
        generator draws.  Calling ``spawn`` with the same key twice returns
        two *separate* but *identically-seeded* contexts.
        """
        child_int = _key_to_int(key)
        return RngContext(self._seed, self._path + (child_int,))

    # ---------------------------------------------------------------- helpers

    @property
    def seed(self) -> int:
        return self._seed

    def fresh(self) -> "RngContext":
        """Return a new independent root RngContext with the same master seed.

        Useful when you need a completely fresh context (e.g. for re-rendering
        a layer without consuming the parent's draws).
        """
        return RngContext(self._seed, self._path)
