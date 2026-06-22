"""soundmatch.ui.spectrogram — shared spectrogram widget (matplotlib FigureCanvas).

Factors the spectrogram drawing out of inspector/plots.py into a reusable
Qt widget.  Both the metrics_panel and ab_viewer use this — no copy-paste.
"""

from __future__ import annotations

import numpy as np

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
    """Embeddable waveform widget using matplotlib FigureCanvasQTAgg.

    Displays a time-domain waveform of the given audio.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent=None):
        self._fig = Figure(figsize=(5, 1.2), dpi=100, tight_layout=True)
        super().__init__(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_visible(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(40)

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
        self._ax.clear()
        self._ax.set_visible(True)
        draw_waveform(self._ax, y, sr, duration_s=duration_s, title=title)
        self.draw()

    def set_selection(self, start_s: float, end_s: float) -> None:
        """Highlight a time region on the waveform.

        Parameters
        ----------
        start_s: Start time in seconds.
        end_s  : End time in seconds.
        """
        # Add a shaded region
        self._ax.axvspan(start_s, end_s, color="#3a8ee8", alpha=0.25)
        self.draw()

    def clear(self) -> None:
        """Clear the display."""
        self._ax.clear()
        self._ax.set_visible(False)
        self.draw()
