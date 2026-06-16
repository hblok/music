"""forge.ui.pattern_editor — 16-step button grid per instrument.

PatternEditor shows a row of 16 toggle buttons for one instrument, plus a
selector for the instrument.  It emits a PatternSpec-compatible dict when the
grid changes.

Usage::

    editor = PatternEditor(parent)
    editor.patternChanged.connect(on_pattern)   # PatternSpec dict
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class StepButton(QPushButton):
    """A single step toggle button — on = lit, off = dim."""

    def __init__(self, index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.index = index
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self._update_style()
        self.toggled.connect(lambda _: self._update_style())

    def _update_style(self) -> None:
        if self.isChecked():
            self.setStyleSheet("background-color: #4a9eff; border: 1px solid #2266aa;")
        else:
            self.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")


class PatternRow(QWidget):
    """One row of 16 step buttons for one instrument."""

    changed = Signal()

    def __init__(
        self,
        instrument_id: str,
        n_steps: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.instrument_id = instrument_id
        self._n_steps = n_steps
        self._buttons: list[StepButton] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        name_label = QLabel(instrument_id[:8])
        name_label.setFixedWidth(64)
        layout.addWidget(name_label)

        for i in range(n_steps):
            btn = StepButton(i, self)
            btn.toggled.connect(lambda _, b=btn: self.changed.emit())
            self._buttons.append(btn)
            layout.addWidget(btn)

    def steps(self) -> list[int]:
        """Return 0/1 list for each step."""
        return [1 if btn.isChecked() else 0 for btn in self._buttons]

    def set_steps(self, steps: list[int]) -> None:
        for i, v in enumerate(steps[:self._n_steps]):
            self._buttons[i].setChecked(bool(v))

    def clear(self) -> None:
        for btn in self._buttons:
            btn.setChecked(False)


class PatternEditor(QWidget):
    """Multi-row 16-step pattern editor.

    Shows one PatternRow per active instrument and emits a PatternSpec dict
    on any change so the caller can re-render via control.render_pattern.
    """

    patternChanged = Signal(dict)   # PatternSpec dict
    renderRequested = Signal(dict)  # PatternSpec dict

    def __init__(
        self,
        bpm: float = 138.0,
        length_bars: int = 4,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bpm = bpm
        self._length_bars = length_bars
        self._rows: list[PatternRow] = []

        layout = QVBoxLayout(self)

        # Toolbar: instrument selector + add/remove row
        toolbar = QHBoxLayout()
        self._instrument_combo = QComboBox()
        self._populate_combo()
        add_btn = QPushButton("+ Add row")
        add_btn.clicked.connect(self._add_row)
        clear_btn = QPushButton("Clear all")
        clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(QLabel("Instrument:"))
        toolbar.addWidget(self._instrument_combo)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(clear_btn)

        # BPM / bars controls
        bpm_row = QHBoxLayout()
        self._bpm_spin = QSpinBox()
        self._bpm_spin.setRange(60, 200)
        self._bpm_spin.setValue(int(bpm))
        self._bpm_spin.valueChanged.connect(self._on_settings_changed)
        self._bars_spin = QSpinBox()
        self._bars_spin.setRange(1, 32)
        self._bars_spin.setValue(length_bars)
        self._bars_spin.valueChanged.connect(self._on_settings_changed)
        bpm_row.addWidget(QLabel("BPM:"))
        bpm_row.addWidget(self._bpm_spin)
        bpm_row.addWidget(QLabel("Bars:"))
        bpm_row.addWidget(self._bars_spin)

        render_btn = QPushButton("▶ Render pattern")
        render_btn.clicked.connect(self._on_render)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(2)

        layout.addLayout(toolbar)
        layout.addLayout(bpm_row)
        layout.addWidget(self._rows_container)
        layout.addWidget(render_btn)

    def _populate_combo(self) -> None:
        try:
            from forge import control
            for entry in control.list_instruments():
                self._instrument_combo.addItem(entry["id"])
        except Exception:  # noqa: BLE001
            for iid in ("kick", "hat", "snare", "bass", "wind"):
                self._instrument_combo.addItem(iid)

    def _add_row(self) -> None:
        iid = self._instrument_combo.currentText()
        row = PatternRow(iid, parent=self._rows_container)
        row.changed.connect(self._emit)
        self._rows.append(row)
        self._rows_layout.addWidget(row)
        self._emit()

    def _clear_all(self) -> None:
        for row in self._rows:
            row.setParent(None)
        self._rows.clear()
        self._emit()

    def _on_settings_changed(self) -> None:
        self._bpm = float(self._bpm_spin.value())
        self._length_bars = self._bars_spin.value()
        self._emit()

    def _emit(self) -> None:
        self.patternChanged.emit(self.to_pattern_spec())

    def _on_render(self) -> None:
        self.renderRequested.emit(self.to_pattern_spec())

    def to_pattern_spec(self) -> dict:
        """Build a PatternSpec dict from the current editor state."""
        return {
            "bpm": self._bpm,
            "length_bars": self._length_bars,
            "tracks": [
                {
                    "instrument": row.instrument_id,
                    "steps": row.steps(),
                }
                for row in self._rows
            ],
        }
