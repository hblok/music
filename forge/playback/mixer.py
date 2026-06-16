"""forge.playback.mixer — dumb multi-channel callback mixer.

CallbackMixer holds N channel slots.  Each slot loops its buffer (if
loop_enabled) and applies per-channel gain/mute/solo.  A fresh buffer
can be hot-swapped in at the next loop boundary with no click.

The callback is called by the sounddevice audio thread:
  - NO memory allocation inside the callback.
  - NO synthesis — only reading from pre-rendered float32 arrays.
  - A threading.Lock guards the slot list; individual slot buffer swaps
    use atomic Python assignment (GIL makes single-reference writes safe).

Usage::

    mixer = CallbackMixer(sr=44100)
    ch0 = mixer.add_channel("kick")
    mixer.load_channel("kick", numpy_float32_stereo_array)
    mixer.set_gain("kick", 0.8)
    # pass mixer.callback to sounddevice OutputStream
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import numpy as np


class ChannelSlot:
    """One channel slot in the mixer.

    Attributes:
        name:         Identifier (used by the UI).
        gain:         Linear amplitude scale (default 1.0).
        muted:        If True, output is silenced.
        solo:         If True, only soloed channels are audible.
        loop_enabled: Whether to loop the buffer.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.gain: float = 1.0
        self.muted: bool = False
        self.solo: bool = False
        self.loop_enabled: bool = True

        # Audio-thread-facing buffer (float32, (N, 2) or None).
        # Written from UI thread; read from audio thread.
        # GIL makes single-reference assignment atomic in CPython.
        self._data: Optional[np.ndarray] = None
        self._pending: Optional[np.ndarray] = None  # awaiting loop-boundary swap
        self._position: int = 0  # read head (samples)
        self._swap_lock = threading.Lock()

    # ---------------------------------------------------------------- UI thread

    def load(self, data: np.ndarray) -> None:
        """Queue *data* (float32 stereo (N,2)) for swap at next loop boundary."""
        arr = data.astype(np.float32, copy=False)
        if arr.ndim == 1:
            arr = np.column_stack([arr, arr])
        with self._swap_lock:
            self._pending = arr

    def unload(self) -> None:
        with self._swap_lock:
            self._pending = None
        self._data = None

    # ---------------------------------------------------------------- audio thread

    def _apply_pending(self) -> None:
        """Swap in a pending buffer (called at loop boundary from audio thread)."""
        with self._swap_lock:
            if self._pending is not None:
                self._data = self._pending
                self._pending = None
                self._position = 0

    def fill(self, out: np.ndarray, n_frames: int) -> None:
        """Add this channel's contribution into *out* (shape (n_frames, 2)).

        Called from the audio thread.  Does NOT zero *out* — the caller
        must initialize it.  Returns without writing if muted or no data.
        """
        if self._data is None:
            self._apply_pending()
        if self._data is None or self.muted:
            return

        data = self._data
        L = len(data)
        if L == 0:
            return

        pos = self._position
        filled = 0
        g = self.gain

        while filled < n_frames:
            remaining = L - pos
            want = n_frames - filled
            chunk = min(want, remaining)
            out[filled : filled + chunk] += data[pos : pos + chunk] * g
            filled += chunk
            pos += chunk

            if pos >= L:
                if self.loop_enabled:
                    self._apply_pending()  # swap at loop boundary
                    data = self._data  # may have changed
                    L = len(data) if data is not None else 0
                    pos = 0
                    if L == 0:
                        break
                else:
                    self._position = L
                    return

        self._position = pos


class CallbackMixer:
    """Multi-channel dumb mixer for the sounddevice OutputStream callback.

    Args:
        sr: Sample rate (must match the OutputStream).
    """

    def __init__(self, sr: int = 44100) -> None:
        self.sr = sr
        self._slots: dict[str, ChannelSlot] = {}
        self._lock = threading.Lock()  # for slot list mutations from UI thread
        self._on_position: Optional[Callable[[int], None]] = None  # samples
        self._position: int = 0  # global mix position (samples)

    # ---------------------------------------------------------------- channel management (UI thread)

    def add_channel(self, name: str) -> ChannelSlot:
        """Add a new channel slot.  Returns the slot."""
        slot = ChannelSlot(name)
        with self._lock:
            self._slots[name] = slot
        return slot

    def remove_channel(self, name: str) -> None:
        with self._lock:
            self._slots.pop(name, None)

    def channel_names(self) -> list[str]:
        with self._lock:
            return list(self._slots.keys())

    def get_channel(self, name: str) -> Optional[ChannelSlot]:
        with self._lock:
            return self._slots.get(name)

    # ---------------------------------------------------------------- convenience setters (UI thread)

    def load_channel(self, name: str, data: np.ndarray) -> None:
        """Load a new buffer into channel *name* (queued for swap at loop boundary)."""
        with self._lock:
            slot = self._slots.get(name)
        if slot is not None:
            slot.load(data)

    def set_gain(self, name: str, gain: float) -> None:
        with self._lock:
            slot = self._slots.get(name)
        if slot is not None:
            slot.gain = float(gain)

    def set_muted(self, name: str, muted: bool) -> None:
        with self._lock:
            slot = self._slots.get(name)
        if slot is not None:
            slot.muted = bool(muted)

    def set_solo(self, name: str, solo: bool) -> None:
        with self._lock:
            slot = self._slots.get(name)
        if slot is not None:
            slot.solo = bool(solo)

    # ---------------------------------------------------------------- position (UI thread readable)

    @property
    def position_samples(self) -> int:
        return self._position

    def set_position_callback(self, cb: Callable[[int], None]) -> None:
        self._on_position = cb

    def reset_position(self) -> None:
        self._position = 0
        with self._lock:
            for slot in self._slots.values():
                slot._position = 0

    # ---------------------------------------------------------------- audio callback

    def callback(
        self,
        outdata: np.ndarray,  # (frames, 2) float32 — written by this method
        frames: int,
        _time,
        _status,
    ) -> None:
        """sounddevice callback — called from the audio thread."""
        out = np.zeros((frames, 2), dtype=np.float32)

        with self._lock:
            slots = list(self._slots.values())

        # Determine if any channel is solo'd
        any_solo = any(s.solo for s in slots)

        for slot in slots:
            if any_solo and not slot.solo:
                continue
            slot.fill(out, frames)

        outdata[:] = out
        self._position += frames

        if self._on_position is not None:
            self._on_position(self._position)

    # ---------------------------------------------------------------- mix math helpers (for tests)

    def mix_offline(self, n_frames: int) -> np.ndarray:
        """Mix *n_frames* frames offline (no sounddevice). Returns (n, 2) float32.

        Useful for unit tests: drives the same logic as the real callback
        without needing an audio device.
        """
        out = np.zeros((n_frames, 2), dtype=np.float32)
        slots = list(self._slots.values())
        any_solo = any(s.solo for s in slots)
        for slot in slots:
            if any_solo and not slot.solo:
                continue
            slot.fill(out, n_frames)
        self._position += n_frames
        if self._on_position is not None:
            self._on_position(self._position)
        return out
