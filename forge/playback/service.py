"""forge.playback.service — real-time audio playback via sounddevice.

PlaybackService wraps a sounddevice OutputStream with a callback that reads
from an AudioBuffer.  The UI calls play/pause/stop/seek; the callback runs
in a high-priority audio thread.

Design constraints:
  - No imports from forge.ui here (engine → UI is forbidden).
  - The callback does NO memory allocation; it only reads from pre-rendered data.
  - If no buffer is loaded, the callback outputs silence.

Usage::

    svc = PlaybackService(sr=44100, bpm=138.0)
    svc.load(buf)   # AudioBuffer from control.render_instrument / render_track
    svc.play()
    # …
    svc.stop()
    svc.close()
"""

from __future__ import annotations

import threading
from typing import Callable

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.playback.clock import PlaybackClock

try:
    import sounddevice as _sd
    _SD_AVAILABLE = True
except OSError:
    _SD_AVAILABLE = False


class PlaybackService:
    """Manages real-time playback of a single AudioBuffer.

    Args:
        sr:           Sample rate (must match the AudioBuffer).
        bpm:          Tempo for position display.
        block_size:   Callback block size in frames (0 = driver default).
        on_position:  Optional callback called each block with current bar pos.
    """

    def __init__(
        self,
        sr: int = 44100,
        bpm: float = 120.0,
        *,
        block_size: int = 0,
        on_position: Callable[[float], None] | None = None,
    ) -> None:
        self.sr = sr
        self.clock = PlaybackClock(bpm=bpm, sr=sr)
        self._block_size = block_size
        self._on_position = on_position
        self._buf: AudioBuffer | None = None
        self._stream: "_sd.OutputStream | None" = None  # type: ignore[name-defined]
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Buffer management

    def load(self, buf: AudioBuffer) -> None:
        """Replace the current buffer (takes effect immediately)."""
        with self._lock:
            self._buf = buf

    def unload(self) -> None:
        with self._lock:
            self._buf = None

    # ------------------------------------------------------------------
    # Transport

    def play(self) -> None:
        """Start playback.  Opens the stream if not already open."""
        self.clock.play()
        if _SD_AVAILABLE and (self._stream is None or not self._stream.active):
            self._open_stream()

    def pause(self) -> None:
        self.clock.pause()

    def stop(self) -> None:
        self.clock.stop()

    def seek(self, sample: int) -> None:
        self.clock.seek(sample)

    def seek_bar(self, bar: float) -> None:
        from forge.core.grid import Grid
        grid = Grid(self.clock.bpm, sr=self.sr)
        self.clock.seek(int(bar * grid.bar * self.sr))

    def close(self) -> None:
        """Stop and close the audio stream."""
        self.clock.stop()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    # ------------------------------------------------------------------
    # Properties

    @property
    def is_playing(self) -> bool:
        return self.clock.is_playing

    @property
    def position_bars(self) -> float:
        return self.clock.position_bars

    @property
    def position_seconds(self) -> float:
        return self.clock.position_seconds

    @property
    def bar_beat_string(self) -> str:
        return self.clock.bar_beat_string()

    # ------------------------------------------------------------------
    # Internal

    def _open_stream(self) -> None:
        if not _SD_AVAILABLE:
            return
        try:
            self._stream = _sd.OutputStream(
                samplerate=self.sr,
                channels=2,
                dtype="float32",
                blocksize=self._block_size,
                callback=self._callback,
            )
            self._stream.start()
        except Exception:  # noqa: BLE001 — no audio device in CI/headless env
            self._stream = None

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        _time,
        _status,
    ) -> None:
        """sounddevice audio callback — runs in the audio thread."""
        pos = self.clock.position_samples
        with self._lock:
            buf = self._buf

        if buf is None or not self.clock.is_playing:
            outdata[:] = 0.0
            return

        n = len(buf)
        if pos >= n:
            # stop at end
            outdata[:] = 0.0
            self.clock.pause()
            return

        avail = min(frames, n - pos)
        outdata[:avail] = buf.data[pos : pos + avail].astype(np.float32)
        if avail < frames:
            outdata[avail:] = 0.0

        self.clock.advance(avail)

        if self._on_position is not None:
            self._on_position(self.clock.position_bars)
