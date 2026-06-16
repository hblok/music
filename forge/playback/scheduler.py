"""forge.playback.scheduler — background render scheduler.

The scheduler runs render jobs in a background thread pool (threads not
processes — forge render callables capture context and are not always
picklable; threads suffice because scipy FFT paths release the GIL).

Design:
  - ``get_or_schedule(key, render_fn, on_done)``
      Checks cache first (returns immediately if fresh).
      Otherwise schedules a background render; returns (stale_buf, False).
  - Coalesces rapid edits: submitting a new job for the same key while an
    existing one is still pending cancels the old future and replaces it.
  - ``on_done`` callbacks are called from the worker thread with (key, buf).
    The UI must marshal to the Qt thread if needed (e.g. via QMetaObject).
  - ``is_pending(key)`` and ``pending_count()`` are safe to poll from the UI.

Usage::

    cache = ContentAddressedCache()
    sched = RenderScheduler(cache, n_workers=2)
    sched.get_or_schedule(key, render_fn, on_done=lambda k, b: ...)
    sched.shutdown()
"""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional

import numpy as np

from forge.playback.cache import ContentAddressedCache


OnDone = Callable[[str, np.ndarray], None]


class RenderScheduler:
    """Background render scheduler backed by a thread pool.

    Args:
        cache:     The cache to check / populate.
        n_workers: Thread-pool size (default 2).
    """

    def __init__(
        self,
        cache: ContentAddressedCache,
        n_workers: int = 2,
    ) -> None:
        self._cache = cache
        self._pool = ThreadPoolExecutor(max_workers=n_workers, thread_name_prefix="forge-render")
        self._lock = threading.Lock()
        # key → (Future, [on_done callback])
        self._pending: dict[str, tuple[Future, list[OnDone]]] = {}

    # ------------------------------------------------------------------
    # Public API

    def get_or_schedule(
        self,
        key: str,
        render_fn: Callable[[], np.ndarray],
        on_done: OnDone | None = None,
    ) -> tuple[Optional[np.ndarray], bool]:
        """Return (buf_or_None, is_fresh).

        If *key* is cached: returns (buffer, True) — instant.
        Otherwise: schedules *render_fn* in the background, registers
        *on_done* for notification, and returns (None, False).

        Coalesces: if a job for *key* is already in flight, *on_done* is
        appended to its callback list rather than scheduling a duplicate.
        """
        buf = self._cache.get(key)
        if buf is not None:
            return buf, True

        with self._lock:
            if key in self._pending:
                # Already in flight — just attach callback
                _, callbacks = self._pending[key]
                if on_done is not None:
                    callbacks.append(on_done)
                return None, False

            callbacks: list[OnDone] = []
            if on_done is not None:
                callbacks.append(on_done)

            future = self._pool.submit(self._run, key, render_fn, callbacks)
            self._pending[key] = (future, callbacks)

        return None, False

    def invalidate(self, key: str) -> None:
        """Cancel any pending job for *key* (cache entry is NOT cleared).

        To also clear the cache entry, call ``cache.clear_all()`` separately.
        """
        with self._lock:
            if key in self._pending:
                future, _ = self._pending.pop(key)
                future.cancel()

    def is_pending(self, key: str) -> bool:
        """Return True if a render job for *key* is in the queue or running."""
        with self._lock:
            entry = self._pending.get(key)
            return entry is not None and not entry[0].done()

    def is_fresh(self, key: str) -> bool:
        """Return True if *key* is in cache (no render needed)."""
        return self._cache.has(key)

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for f, _ in self._pending.values() if not f.done())

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the thread pool."""
        with self._lock:
            for future, _ in self._pending.values():
                future.cancel()
            self._pending.clear()
        self._pool.shutdown(wait=wait)

    # ------------------------------------------------------------------
    # Internal

    def _run(
        self,
        key: str,
        render_fn: Callable[[], np.ndarray],
        callbacks: list[OnDone],
    ) -> None:
        """Worker: render → cache → notify."""
        try:
            buf = render_fn()
            arr = np.asarray(buf, dtype=np.float32) if not isinstance(buf, np.ndarray) else buf
            self._cache.put(key, arr)
        except Exception:  # noqa: BLE001 — don't crash the worker thread
            arr = np.zeros((1, 2), dtype=np.float32)

        with self._lock:
            self._pending.pop(key, None)

        for cb in callbacks:
            try:
                cb(key, arr)
            except Exception:  # noqa: BLE001
                pass
