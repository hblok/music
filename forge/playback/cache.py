"""forge.playback.cache — content-addressed buffer cache.

Two-layer cache: an in-memory LRU sitting in front of an on-disk store.

  - Keys are 16-hex-char SHA-256 hashes produced by
    ``forge.document.transaction.channel_content_hash``.
  - Values are (N, 2) float32 numpy arrays (stereo audio data).
  - The in-memory layer is a bounded OrderedDict (LRU eviction).
  - The on-disk layer stores numpy .npy files under *cache_dir*.

Usage::

    cache = ContentAddressedCache(cache_dir=Path("~/.cache/forge_tracker"))
    buf = cache.get(key)           # None on miss
    cache.put(key, np_array)
    cache.clear_memory()           # evict memory only
    cache.clear_disk()             # remove all on-disk files
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np


_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "forge_tracker"
_DEFAULT_MAX_MEMORY = 64  # max number of buffers in memory


class ContentAddressedCache:
    """Two-layer (memory + disk) content-addressed audio buffer cache.

    Thread-safe: all methods acquire an internal lock.

    Args:
        cache_dir:  Directory for on-disk .npy files.  Created on demand.
        max_memory: Maximum number of buffers in the memory layer (LRU eviction).
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_memory: int = _DEFAULT_MAX_MEMORY,
    ) -> None:
        self._dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._max_memory = max_memory
        self._mem: OrderedDict[str, np.ndarray] = OrderedDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API

    def get(self, key: str) -> Optional[np.ndarray]:
        """Return the cached buffer for *key*, or None on a miss.

        Checks memory first; falls back to disk.  A disk hit is promoted
        to memory (LRU refresh).
        """
        with self._lock:
            # Memory hit
            if key in self._mem:
                self._mem.move_to_end(key)
                return self._mem[key]

            # Disk hit
            path = self._disk_path(key)
            if path.exists():
                try:
                    arr = np.load(str(path))
                    self._mem_put(key, arr)
                    return arr
                except Exception:  # noqa: BLE001 — corrupted file; treat as miss
                    path.unlink(missing_ok=True)

        return None

    def put(self, key: str, data: np.ndarray) -> None:
        """Store *data* (float32, shape (N, 2)) under *key*.

        Writes to memory and disk atomically.
        """
        arr = data.astype(np.float32, copy=False)
        with self._lock:
            self._mem_put(key, arr)
            self._disk_put(key, arr)

    def has(self, key: str) -> bool:
        """Return True if *key* is in memory or on disk."""
        with self._lock:
            return key in self._mem or self._disk_path(key).exists()

    def clear_memory(self) -> None:
        with self._lock:
            self._mem.clear()

    def clear_disk(self) -> None:
        with self._lock:
            if self._dir.exists():
                for f in self._dir.glob("*.npy"):
                    f.unlink(missing_ok=True)

    def clear_all(self) -> None:
        self.clear_memory()
        self.clear_disk()

    def memory_size(self) -> int:
        with self._lock:
            return len(self._mem)

    def disk_size(self) -> int:
        with self._lock:
            if not self._dir.exists():
                return 0
            return sum(1 for _ in self._dir.glob("*.npy"))

    # ------------------------------------------------------------------
    # Internal

    def _mem_put(self, key: str, arr: np.ndarray) -> None:
        """Add to memory cache with LRU eviction (lock must be held)."""
        if key in self._mem:
            self._mem.move_to_end(key)
        else:
            self._mem[key] = arr
            if len(self._mem) > self._max_memory:
                self._mem.popitem(last=False)

    def _disk_put(self, key: str, arr: np.ndarray) -> None:
        """Write *arr* to disk under *key* (lock must be held)."""
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._disk_path(key)
        # Use a temp filename that already ends in .npy so numpy doesn't
        # append a second .npy suffix.
        tmp = self._dir / f"_tmp_{key}.npy"
        np.save(str(tmp), arr)
        tmp.replace(path)  # atomic on POSIX

    def _disk_path(self, key: str) -> Path:
        return self._dir / f"{key}.npy"
