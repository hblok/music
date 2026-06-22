"""forge.playback.service — real-time audio playback via sounddevice.

Two operating modes:
  1. Single-buffer mode (original):
       svc = PlaybackService(sr=44100, bpm=138.0)
       svc.load(buf)   # AudioBuffer from control.render_instrument / render_track
       svc.play()
  2. Mixer mode (Phase 3+):
       svc = PlaybackService.with_mixer(sr=44100, bpm=138.0)
       svc.mixer.load_channel("kick", np_array)
       svc.play()

Design constraints:
  - No imports from forge.ui here (engine → UI is forbidden).
  - The callback does NO memory allocation; it only reads from pre-rendered data.
  - If no buffer is loaded, the callback outputs silence.
  - Degrades gracefully when no audio device is available (CI/headless).
"""

from __future__ import annotations

import threading
from typing import Callable

import numpy as np

from forge.core.buffer import AudioBuffer
from forge.playback.clock import PlaybackClock
from forge.playback.mixer import CallbackMixer

try:
    import sounddevice as _sd
    _SD_AVAILABLE = True
except OSError:
    _SD_AVAILABLE = False


class PlaybackService:
    """Manages real-time audio playback.

    Supports two modes:
      - Single-buffer mode: ``load(AudioBuffer)`` then ``play()``.
      - Mixer mode: instantiate via ``PlaybackService.with_mixer()``; access
        ``svc.mixer`` to manage per-channel buffers.

    Args:
        sr:           Sample rate (must match all loaded buffers).
        bpm:          Tempo for position display.
        block_size:   Callback block size in frames (0 = driver default).
        on_position:  Callback called each block with current bar position.
        mixer:        Optional pre-built CallbackMixer (for mixer mode).
    """

    def __init__(
        self,
        sr: int = 44100,
        bpm: float = 120.0,
        *,
        block_size: int = 0,
        on_position: Callable[[float], None] | None = None,
        mixer: CallbackMixer | None = None,
    ) -> None:
        self.sr = sr
        self.clock = PlaybackClock(bpm=bpm, sr=sr)
        self._block_size = block_size
        self._on_position = on_position
        self._buf: AudioBuffer | None = None
        self._stream: "_sd.OutputStream | None" = None  # type: ignore[name-defined]
        self._lock = threading.Lock()
        self.mixer: CallbackMixer | None = mixer

    @classmethod
    def with_mixer(
        cls,
        sr: int = 44100,
        bpm: float = 120.0,
        *,
        block_size: int = 0,
        on_position: Callable[[float], None] | None = None,
    ) -> "PlaybackService":
        """Create a PlaybackService in mixer mode (multi-channel looping)."""
        m = CallbackMixer(sr=sr)
        return cls(sr=sr, bpm=bpm, block_size=block_size, on_position=on_position, mixer=m)

    # ------------------------------------------------------------------
    # Buffer management

    def load(self, buf: AudioBuffer) -> None:
        """Replace the current buffer and reset position to the start."""
        with self._lock:
            self._buf = buf
        self.clock.seek(0)

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
        cb = self.mixer.callback if self.mixer is not None else self._callback
        try:
            self._stream = _sd.OutputStream(
                samplerate=self.sr,
                channels=2,
                dtype="float32",
                blocksize=self._block_size,
                callback=cb,
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
        """sounddevice audio callback — single-buffer mode."""
        pos = self.clock.position_samples
        with self._lock:
            buf = self._buf

        if buf is None or not self.clock.is_playing:
            outdata[:] = 0.0
            return

        n = len(buf)
        if pos >= n:
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
