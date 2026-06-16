"""forge.ui.mixer — per-layer volume faders and mute buttons.

MixerWidget shows one strip per instrument (or layer) with:
  - A vertical fader (0 dB at top; -inf at bottom)
  - A mute button
  - A label

Usage::

    mixer = MixerWidget(["kick", "hat", "bass"], parent)
    mixer.levelsChanged.connect(on_levels)  # {name: (volume, muted)}
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class _Strip(QWidget):
    """Single mixer strip: label + fader + mute."""

    changed = Signal()

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name

        self._fader = QSlider(Qt.Orientation.Vertical)
        self._fader.setRange(0, 100)
        self._fader.setValue(80)
        self._fader.setFixedHeight(100)

        self._mute_btn = QPushButton("M")
        self._mute_btn.setCheckable(True)
        self._mute_btn.setFixedSize(24, 24)

        label = QLabel(name[:6])
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label)
        layout.addWidget(self._fader, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._mute_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._fader.valueChanged.connect(lambda _: self.changed.emit())
        self._mute_btn.toggled.connect(lambda _: self.changed.emit())

    @property
    def volume(self) -> float:
        """Linear volume 0.0–1.0 (fader position mapped from 0–100)."""
        return self._fader.value() / 100.0

    @property
    def muted(self) -> bool:
        return self._mute_btn.isChecked()

    def set_volume(self, v: float) -> None:
        self._fader.setValue(int(v * 100))


class MixerWidget(QWidget):
    """Horizontal row of mixer strips.

    Args:
        layer_names: Names for each strip (instrument ids or labels).
        parent:      Optional parent.
    """

    levelsChanged = Signal(dict)   # {name: {"volume": float, "muted": bool}}

    def __init__(
        self,
        layer_names: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._strips: dict[str, _Strip] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        for name in layer_names:
            strip = _Strip(name, self)
            strip.changed.connect(self._emit)
            self._strips[name] = strip
            layout.addWidget(strip)

    def _emit(self) -> None:
        self.levelsChanged.emit(self.levels())

    def levels(self) -> dict:
        """Current levels: ``{name: {"volume": float, "muted": bool}}``."""
        return {
            name: {"volume": strip.volume, "muted": strip.muted}
            for name, strip in self._strips.items()
        }

    def set_volume(self, name: str, v: float) -> None:
        if name in self._strips:
            self._strips[name].set_volume(v)
