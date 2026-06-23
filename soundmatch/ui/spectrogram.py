"""soundmatch.ui.spectrogram — shared spectrogram widget (matplotlib FigureCanvas).

Factors the spectrogram drawing out of inspector/plots.py into a reusable
Qt widget.  Both the metrics_panel and ab_viewer use this — no copy-paste.
"""

from __future__ import annotations

import logging
import numpy as np

log = logging.getLogger(__name__)

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QSizePolicy

import matplotlib
matplotlib.use("Agg")  # ensure headless-safe backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def draw_spectrogram(
    ax: matplotlib.axes.Axes,
    y: np.ndarray,
    sr: int,
    *,
    hop: int = 4096,
    n_mels: int = 128,
    cmap: str = "magma",
    title: str | None = None,
    xlim: tuple[float, float] | None = None,
) -> None:
    """Draw a mel spectrogram onto a matplotlib Axes.

    This is the shared helper used both here and by inspector/plots.py.
    No Qt dependency — pure matplotlib.

    Parameters
    ----------
    ax    : Matplotlib Axes to draw onto.
    y     : Mono audio signal.
    sr    : Sample rate.
    hop   : Hop length for the STFT.
    n_mels: Number of mel bands.
    cmap  : Colormap name.
    title : Optional title string.
    xlim  : Optional (t_min, t_max) in seconds.
    """
    import librosa
    import librosa.display

    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, hop_length=hop)
    S_db = librosa.power_to_db(S, ref=np.max)
    librosa.display.specshow(
        S_db, sr=sr, hop_length=hop, x_axis="time",
        y_axis="mel", ax=ax, cmap=cmap,
    )
    if title:
        ax.set_title(title, fontsize=9)
    if xlim is not None:
        ax.set_xlim(xlim)


def draw_waveform(
    ax: matplotlib.axes.Axes,
    y: np.ndarray,
    sr: int,
    *,
    duration_s: float | None = None,
    color: str = "#4a9eda",
    linewidth: float = 0.3,
    alpha: float = 0.85,
    title: str | None = None,
    xlim: tuple[float, float] | None = None,
) -> None:
    """Draw a waveform onto a matplotlib Axes.

    Parameters
    ----------
    ax         : Matplotlib Axes to draw onto.
    y          : Mono audio signal (may be a display-downsampled array).
    sr         : Sample rate (used only when duration_s is None).
    duration_s : Total audio duration in seconds. Pass this when y is
                 downsampled so the time axis remains correct.
    color      : Line color.
    linewidth  : Line width.
    alpha      : Alpha.
    title      : Optional title string.
    xlim       : Optional (t_min, t_max) in seconds.
    """
    total = duration_s if duration_s is not None else len(y) / sr
    times = np.linspace(0, total, len(y))
    ax.plot(times, y, color=color, linewidth=linewidth, alpha=alpha, rasterized=True)
    ax.set_ylabel("Amplitude")
    if title:
        ax.set_title(title, fontsize=9)
    if xlim is not None:
        ax.set_xlim(xlim)


class SpectrogramWidget(FigureCanvas):
    """Embeddable spectrogram widget using matplotlib FigureCanvasQTAgg.

    Displays a mel spectrogram of the given audio.  Used by
    reference_panel, metrics_panel, and ab_viewer.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent=None):
        self._fig = Figure(figsize=(5, 2), dpi=100, tight_layout=True)
        super().__init__(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_visible(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(80)

    def set_audio(self, y: np.ndarray, sr: int, *, title: str | None = None) -> None:
        """Display a mel spectrogram of the given mono audio.

        Parameters
        ----------
        y     : Mono audio signal.
        sr    : Sample rate.
        title : Optional title.
        """
        self._ax.clear()
        self._ax.set_visible(True)
        draw_spectrogram(self._ax, y, sr, title=title)
        self.draw()

    def set_spectrogram_data(
        self,
        S_db: np.ndarray,
        sr: int,
        hop: int,
        *,
        title: str | None = None,
    ) -> None:
        """Display a pre-computed mel spectrogram (avoids re-computing on main thread).

        Parameters
        ----------
        S_db  : Mel spectrogram in dB, shape (n_mels, time).
        sr    : Sample rate used when computing S_db.
        hop   : Hop length used when computing S_db.
        title : Optional title.
        """
        import librosa.display

        self._ax.clear()
        self._ax.set_visible(True)
        librosa.display.specshow(
            S_db, sr=sr, hop_length=hop, x_axis="time",
            y_axis="mel", ax=self._ax, cmap="magma",
        )
        if title:
            self._ax.set_title(title, fontsize=9)
        self.draw()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._ax.set_visible(False)
        self.draw()


class WaveformWidget(FigureCanvas):
    """Embeddable waveform widget with click-and-drag time selection.

    Click and drag horizontally to set a selection region.  The region
    is highlighted and ``selectionChanged(start_s, end_s)`` is emitted
    on mouse release.

    Args:
        parent: Optional parent widget.
    """

    selectionChanged = Signal(float, float)

    def __init__(self, parent=None):
        self._fig = Figure(figsize=(5, 1.2), dpi=100, tight_layout=True)
        super().__init__(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_visible(False)
        self._selection_patch = None
        self._drag_start: float | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(40)

        self.mpl_connect("button_press_event", self._on_mpl_press)
        self.mpl_connect("motion_notify_event", self._on_mpl_motion)
        self.mpl_connect("button_release_event", self._on_mpl_release)

    # ── Drag handlers ──────────────────────────────────────────────────

    def _on_mpl_press(self, event) -> None:
        if event.inaxes is not self._ax or event.xdata is None:
            return
        self._drag_start = float(event.xdata)
        self._update_patch(self._drag_start, self._drag_start)
        self.draw_idle()

    def _on_mpl_motion(self, event) -> None:
        if self._drag_start is None or event.xdata is None:
            return
        x = float(event.xdata)
        start, end = sorted((self._drag_start, x))
        self._update_patch(start, end)
        self.draw_idle()

    def _on_mpl_release(self, event) -> None:
        if self._drag_start is None:
            return
        x = float(event.xdata) if event.xdata is not None else self._drag_start
        start, end = sorted((self._drag_start, x))
        self._drag_start = None
        self._update_patch(start, end)
        self.draw_idle()
        if end - start > 0.05:  # ignore accidental single clicks
            log.debug("waveform selection: %.3f–%.3fs", start, end)
            self.selectionChanged.emit(start, end)

    def _update_patch(self, start_s: float, end_s: float) -> None:
        """Replace the selection patch without triggering a draw."""
        if self._selection_patch is not None:
            try:
                self._selection_patch.remove()
            except ValueError:
                pass
        self._selection_patch = self._ax.axvspan(
            start_s, end_s, color="#3a8ee8", alpha=0.25,
        )

    # ── Public API ─────────────────────────────────────────────────────

    def set_audio(
        self,
        y: np.ndarray,
        sr: int,
        *,
        duration_s: float | None = None,
        title: str | None = None,
    ) -> None:
        """Display a waveform of the given mono audio.

        Parameters
        ----------
        y          : Mono audio signal (may be display-downsampled).
        sr         : Sample rate (used only when duration_s is None).
        duration_s : Total audio duration; pass when y is downsampled.
        title      : Optional title.
        """
        self._selection_patch = None
        self._ax.clear()
        self._ax.set_visible(True)
        draw_waveform(self._ax, y, sr, duration_s=duration_s, title=title)
        self.draw()

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Highlight a time region, replacing any previous highlight.

        Parameters
        ----------
        start_s: Start time in seconds.
        end_s  : End time in seconds.
        """
        self._update_patch(start_s, end_s)
        self.draw()

    def clear(self) -> None:
        """Clear the display."""
        self._selection_patch = None
        self._drag_start = None
        self._ax.clear()
        self._ax.set_visible(False)
        self.draw()
