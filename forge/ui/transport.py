"""forge.ui.transport — play/pause/stop/seek transport widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

from forge.playback.service import PlaybackService


class TransportWidget(QWidget):
    """Transport controls (play/pause/stop + position slider + bar display).

    Args:
        service: PlaybackService to control.
        parent:  Optional parent widget.
    """

    positionChanged = Signal(float)  # emitted with position_bars

    def __init__(
        self,
        service: PlaybackService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service

        # --- widgets ---
        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedWidth(36)
        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setFixedWidth(36)
        self._pos_label = QLabel("  1:1")
        self._pos_label.setFixedWidth(60)
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.setValue(0)

        # --- layout ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        for w in (self._play_btn, self._stop_btn,
                  self._pos_label, self._seek_slider):
            layout.addWidget(w)

        # --- connections ---
        self._play_btn.clicked.connect(self._on_play)
        self._stop_btn.clicked.connect(self._on_stop)
        self._seek_slider.sliderMoved.connect(self._on_seek)

        # --- position poll timer ---
        self._timer = QTimer(self)
        self._timer.setInterval(80)  # ~12 fps position update
        self._timer.timeout.connect(self._poll_position)
        self._timer.start()

        self._slider_total_bars: float = 32.0

    # ------------------------------------------------------------------
    # Slots

    def _on_play(self) -> None:
        self._service.play()

    def _on_stop(self) -> None:
        self._service.stop()
        self._seek_slider.setValue(0)
        self._pos_label.setText("  1:1")

    def _on_seek(self, value: int) -> None:
        bar = (value / 1000.0) * self._slider_total_bars
        self._service.seek_bar(bar)

    def _poll_position(self) -> None:
        pos_bars = self._service.position_bars
        self._pos_label.setText(self._service.bar_beat_string)
        if self._slider_total_bars > 0:
            frac = min(pos_bars / self._slider_total_bars, 1.0)
            self._seek_slider.setValue(int(frac * 1000))
        self.positionChanged.emit(pos_bars)
        # Keep play button in sync with actual playback state
        self._play_btn.setText("⏸" if self._service.is_playing else "▶")
        # Render-queue indicator tooltip
        sched = getattr(self, "_scheduler", None)
        if sched is not None:
            n = sched.pending_count()
            self._pos_label.setToolTip(f"Rendering: {n} channel(s)" if n > 0 else "")

    # ------------------------------------------------------------------
    # Public API

    def set_total_bars(self, n_bars: float) -> None:
        """Update slider scale to match track length."""
        self._slider_total_bars = max(n_bars, 1.0)

    def set_scheduler(self, scheduler: "forge.playback.scheduler.RenderScheduler") -> None:  # type: ignore[name-defined]
        """Attach a scheduler so the transport shows a render-queue indicator in the tooltip."""
        self._scheduler = scheduler

    def set_loop_range(self, start_bar: float, end_bar: float) -> None:
        """Record a section loop range (used by the arrangement view)."""
        self._loop_start = start_bar
        self._loop_end = end_bar
