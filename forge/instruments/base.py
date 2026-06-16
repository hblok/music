"""Instrument protocol and per-note render cache.

An instrument is any callable matching the Instrument Protocol:

    def my_instrument(params: dict, rng: np.random.Generator, **ctx) -> AudioBuffer:
        ...

*ctx* carries context that some instruments need:
    duration:  float — seconds (required for texture instruments; ignored by hit/note instruments)
    sr:        int   — sample rate (default 44100)
    grid:      Grid  — tempo grid (optional; needed by rhythmic textures)

Hit/note instruments return a fixed-length buffer keyed on params.
Texture instruments return a buffer of length ``int(duration * sr)``.

The RenderCache deduplicates hit/note renders: same (instrument_id, frozen_params)
→ same buffer, returned without re-rendering.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import numpy as np

from forge.core.buffer import AudioBuffer

# The instrument callable type
Instrument = Callable[..., AudioBuffer]


class ParamSchema:
    """Describes one parameter of an instrument for GUI auto-building.

    Args:
        name:     Parameter key used in the params dict.
        kind:     One of ``"float"``, ``"int"``, ``"bool"``, ``"choice"``.
        default:  Default value.
        lo, hi:   Range for numeric params (inclusive).
        choices:  List of valid values for ``kind="choice"``.
        label:    Human-readable label (defaults to *name*).
        unit:     Optional unit string (e.g. ``"Hz"``, ``"s"``, ``"dB"``).
    """

    def __init__(
        self,
        name: str,
        kind: str,
        default: Any,
        lo: float | None = None,
        hi: float | None = None,
        choices: list | None = None,
        label: str | None = None,
        unit: str | None = None,
    ) -> None:
        self.name = name
        self.kind = kind
        self.default = default
        self.lo = lo
        self.hi = hi
        self.choices = choices or []
        self.label = label or name
        self.unit = unit

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "default": self.default,
            "lo": self.lo,
            "hi": self.hi,
            "choices": self.choices,
            "label": self.label,
            "unit": self.unit,
        }


def _freeze_params(params: dict) -> str:
    """Deterministic JSON-based hash key for a params dict."""
    serialised = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(serialised.encode()).hexdigest()


class RenderCache:
    """Content-addressed cache for rendered instrument buffers.

    Keyed on ``(instrument_id, frozen_params_hash)``.  Thread-unsafe (single-
    threaded synthesis pipeline); the playback cache (Phase 7) adds locking.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], AudioBuffer] = {}

    def get(self, instrument_id: str, params: dict) -> AudioBuffer | None:
        key = (instrument_id, _freeze_params(params))
        return self._store.get(key)

    def put(self, instrument_id: str, params: dict, buf: AudioBuffer) -> None:
        key = (instrument_id, _freeze_params(params))
        self._store[key] = buf

    def invalidate(self, instrument_id: str | None = None) -> None:
        """Remove all entries for *instrument_id*, or clear everything if None."""
        if instrument_id is None:
            self._store.clear()
        else:
            keys = [k for k in self._store if k[0] == instrument_id]
            for k in keys:
                del self._store[k]

    def __len__(self) -> int:
        return len(self._store)


# Module-level default cache (used by render_cached below)
_default_cache: RenderCache = RenderCache()


def render_cached(
    instrument_id: str,
    instrument: Instrument,
    params: dict,
    rng: np.random.Generator,
    cache: RenderCache | None = None,
    **ctx: Any,
) -> AudioBuffer:
    """Render *instrument* with caching.  Returns the cached result if available.

    The cache key is ``(instrument_id, frozen_params_hash)``; *rng* is NOT part
    of the key because the same params should always give the same output.
    This means the *rng* passed must produce the same stream for equivalent
    params — ensured by using ``RngContext.spawn(instrument_id)`` at the call site.
    """
    if cache is None:
        cache = _default_cache
    buf = cache.get(instrument_id, params)
    if buf is None:
        buf = instrument(params, rng, **ctx)
        cache.put(instrument_id, params, buf)
    return buf
