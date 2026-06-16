"""forge.playback.clock — playback transport clock.

Tracks the current position in the audio stream and converts between
sample position, seconds, and bars.  The clock is updated by the
PlaybackService callback and read by the UI transport widget.

Thread-safety: position_samples is written by the audio callback thread
and read by the UI thread.  On CPython the GIL makes integer assignment
atomic enough for this single-reader / single-writer use; no extra lock is used.
"""

from __future__ import annotations

import time


class PlaybackClock:
    """Transport position counter.

    Args:
        bpm: Tempo in BPM (used for bar/beat display).
        sr:  Sample rate.
    """

    def __init__(self, bpm: float = 120.0, sr: int = 44100) -> None:
        self.bpm = bpm
        self.sr = sr
        self._position: int = 0  # samples from start
        self._playing: bool = False
        self._wall_start: float = 0.0  # wall-clock time when play started

    # ------------------------------------------------------------------
    # Transport control (called from UI thread)

    def play(self) -> None:
        if not self._playing:
            self._playing = True
            self._wall_start = time.monotonic()

    def pause(self) -> None:
        self._playing = False

    def stop(self) -> None:
        self._playing = False
        self._position = 0

    def seek(self, sample: int) -> None:
        self._position = max(0, sample)

    # ------------------------------------------------------------------
    # Position update (called from audio callback thread)

    def advance(self, n_frames: int) -> None:
        if self._playing:
            self._position += n_frames

    # ------------------------------------------------------------------
    # Queries (UI thread)

    @property
    def position_samples(self) -> int:
        return self._position

    @property
    def position_seconds(self) -> float:
        return self._position / self.sr

    @property
    def position_bars(self) -> float:
        beat = 60.0 / self.bpm
        bar = beat * 4.0
        return self._position / (bar * self.sr)

    @property
    def is_playing(self) -> bool:
        return self._playing

    def bar_beat_string(self) -> str:
        """Format as 'bar:beat' (1-indexed) for the status bar."""
        bar_f = self.position_bars
        bar = int(bar_f) + 1
        beat_f = (bar_f - int(bar_f)) * 4.0
        beat = int(beat_f) + 1
        return f"{bar:3d}:{beat}"
