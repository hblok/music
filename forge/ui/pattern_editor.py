"""forge.ui.pattern_editor — tracker step-grid pattern editor.

Two classes:

  PatternRow / PatternEditor  — original 16-step toggle API (unchanged;
                                existing tests still pass).

  TrackerRow / TrackerEditor  — Phase 5 full tracker grid:
    - 16 (or n_steps) cells, each with: on/off toggle, accent, ghost,
      probability columns.
    - Keyboard-first navigation: arrow keys move the cursor; Space toggles;
      A = accent; G = ghost.
    - Copy/paste of step blocks (Ctrl+C / Ctrl+V on selection).
    - Per-step param override popover (right-click or "P" key).
    - Bound to a ProjectDoc channel via its channel index; every edit is a
      transaction (undoable).
    - Emits ``channelChanged(channel_idx)`` so the caller can re-render.

Usage (legacy)::

    editor = PatternEditor(bpm=138.0, length_bars=4)
    editor.patternChanged.connect(on_pattern)

Usage (tracker)::

    editor = TrackerEditor(channel_idx=0, doc=my_doc, parent=w)
    editor.channelChanged.connect(lambda idx: sched.get_or_schedule(...))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc


# ---------------------------------------------------------------------------
# Original API (unchanged — all pre-existing tests pass)

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
            self.setStyleSheet("background-color: #3a8ee8; border: 1px solid #1a5fa8; color: #fff;")
        else:
            self.setStyleSheet("background-color: #e0e0e0; border: 1px solid #aaa; color: #333;")


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


# ---------------------------------------------------------------------------
# Tracker cell widget

_CELL_W = 36
_CELL_H = 32
_MOD_H = 22        # height of accent / ghost / prob rows

# Per-channel colour palette (mirrors timeline.py _CHANNEL_COLORS)
_CHANNEL_COLORS_HEX = [
    "#3a8ee8",   # blue
    "#3ab96e",   # green
    "#e8783a",   # orange
    "#9b3ae8",   # purple
    "#e83a82",   # pink
    "#28bebe",   # teal
    "#c8aa28",   # gold
    "#dc3c3c",   # red
]

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_to_name(midi: int) -> str:
    """Return note name for a MIDI number, e.g. 60 → 'C4'."""
    return f"{_NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


class _StepCell(QWidget):
    """One step cell in the tracker grid.

    Contains a toggle button (on/off) with the step index shown, plus visual
    indicators for accent (A), ghost (g), and probability (dim colour).
    The actual data lives in the ProjectDoc; this widget just shows state.
    """

    clicked = Signal(int)  # step index

    # Fixed semantic colours (shared across all channels)
    # Off-state alternates between two shades to mark beat groups of 4
    _C_OFF_EVEN = "#c8c8c8"   # groups 0, 2  (steps 1-4, 9-12)
    _C_OFF_ODD  = "#b0b0b0"   # groups 1, 3  (steps 5-8, 13-16)
    _C_ON_ACCENT = "#e8a03a"
    _C_ON_GHOST = "#3aae6e"
    _C_ON_PROB = "#9855d4"
    _C_CURSOR = "#e83a6e"
    _C_SELECTED = "#8090cc"

    def __init__(
        self,
        step_idx: int,
        channel_color: str = _CHANNEL_COLORS_HEX[0],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.step_idx = step_idx
        self._channel_color = channel_color
        self._on = False
        self._accent = False
        self._ghost = False
        self._probability = 1.0
        self._params: dict = {}
        self._cursor = False
        self._selected = False

        self.setFixedSize(_CELL_W, _CELL_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._label = QLabel(str(step_idx + 1), self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setGeometry(0, 0, _CELL_W, _CELL_H)
        font = QFont()
        font.setPointSize(7)
        self._label.setFont(font)
        self._refresh()

    def set_state(
        self,
        on: bool,
        accent: bool = False,
        ghost: bool = False,
        probability: float = 1.0,
        params: dict | None = None,
    ) -> None:
        self._on = on
        self._accent = accent
        self._ghost = ghost
        self._probability = probability
        self._params = params or {}
        self._refresh()

    def set_cursor(self, active: bool) -> None:
        self._cursor = active
        self._refresh()

    def set_selected(self, active: bool) -> None:
        self._selected = active
        self._refresh()

    def _refresh(self) -> None:
        off_color = self._C_OFF_ODD if (self.step_idx // 4) % 2 else self._C_OFF_EVEN
        if self._cursor:
            bg = self._C_CURSOR
        elif self._selected:
            bg = self._C_SELECTED
        elif self._on:
            if self._accent:
                bg = self._C_ON_ACCENT
            elif self._ghost:
                bg = self._C_ON_GHOST
            elif self._probability < 1.0:
                bg = self._C_ON_PROB
            else:
                bg = self._channel_color
        else:
            bg = off_color
        is_active = self._on or self._cursor or self._selected
        text_color = "#444" if not is_active else "#fff"
        border_color = "#666" if self._cursor else "#999" if not is_active else "#0006"
        self.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border_color};"
        )
        self._label.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
        # Show MIDI note name when a pitch override is set, otherwise show step number
        if "midi" in self._params:
            self._label.setText(_midi_to_name(int(self._params["midi"])))
        else:
            self._label.setText(str(self.step_idx + 1))

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.step_idx)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Per-step param override popover

class _StepParamDialog(QDialog):
    """A small dialog to edit per-step param overrides."""

    def __init__(
        self,
        step_idx: int,
        current_params: dict,
        instrument_params: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Step {step_idx + 1} param overrides")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._edits: dict[str, QLineEdit] = {}

        for schema in instrument_params[:8]:   # show first 8 params
            name = schema["name"]
            edit = QLineEdit()
            if name in current_params:
                edit.setText(str(current_params[name]))
            else:
                edit.setPlaceholderText(f"default ({schema.get('default', '')})")
            form.addRow(name, edit)
            self._edits[name] = edit

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_params(self) -> dict:
        result = {}
        for name, edit in self._edits.items():
            text = edit.text().strip()
            if text:
                try:
                    result[name] = float(text)
                except ValueError:
                    pass
        return result


# ---------------------------------------------------------------------------
# TrackerRow: one instrument row with accent/ghost/prob columns

class TrackerRow(QWidget):
    """One tracker row: label + step cells + accent + ghost + prob columns."""

    stepToggled = Signal(int)         # step_idx
    accentToggled = Signal(int)       # step_idx
    ghostToggled = Signal(int)        # step_idx
    probClicked = Signal(int)         # step_idx (open prob editor)
    stepParamClicked = Signal(int)    # step_idx

    def __init__(
        self,
        instrument_id: str,
        n_steps: int = 16,
        channel_color: str = _CHANNEL_COLORS_HEX[0],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.instrument_id = instrument_id
        self._n_steps = n_steps
        self._cells: list[_StepCell] = []
        self._accent_btns: list[QToolButton] = []
        self._ghost_btns: list[QToolButton] = []
        self._prob_btns: list[QToolButton] = []

        # Grid: col 0 = label (spans all 4 rows); cols 1..n_steps = steps/mods
        grid = QGridLayout(self)
        grid.setContentsMargins(2, 1, 2, 1)
        grid.setSpacing(2)

        lbl = QLabel(instrument_id[:8])
        lbl.setFixedWidth(64)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(lbl, 0, 0, 4, 1)   # span all 4 rows

        # Row 0: step cells
        for i in range(n_steps):
            cell = _StepCell(i, channel_color, self)
            cell.clicked.connect(self.stepToggled)
            self._cells.append(cell)
            grid.addWidget(cell, 0, i + 1)

        _btn_base = (
            "QToolButton { background: #c8c8c8; border: 1px solid #999;"
            " color: #444; font-weight: bold; }"
            " QToolButton:hover { background: #b8b8b8; }"
        )
        _accent_style = (
            _btn_base
            + " QToolButton:checked { background: #e8a03a; border-color: #b87020;"
            " color: #fff; }"
        )
        _ghost_style = (
            _btn_base
            + " QToolButton:checked { background: #3aae6e; border-color: #1e7a48;"
            " color: #fff; }"
        )
        _prob_style = (
            _btn_base
            + " QToolButton:checked { background: #9855d4; border-color: #6a2ea0;"
            " color: #fff; }"
        )

        # Row 1: accent buttons
        for i in range(n_steps):
            btn = QToolButton()
            btn.setText("A")
            btn.setFixedSize(_CELL_W, _MOD_H)
            btn.setCheckable(True)
            btn.setToolTip(f"Step {i+1} accent")
            btn.setStyleSheet(_accent_style)
            btn.clicked.connect(lambda checked, idx=i: self.accentToggled.emit(idx))
            self._accent_btns.append(btn)
            grid.addWidget(btn, 1, i + 1)

        # Row 2: ghost buttons
        for i in range(n_steps):
            btn = QToolButton()
            btn.setText("g")
            btn.setFixedSize(_CELL_W, _MOD_H)
            btn.setCheckable(True)
            btn.setToolTip(f"Step {i+1} ghost")
            btn.setStyleSheet(_ghost_style)
            btn.clicked.connect(lambda checked, idx=i: self.ghostToggled.emit(idx))
            self._ghost_btns.append(btn)
            grid.addWidget(btn, 2, i + 1)

        # Row 3: probability buttons
        for i in range(n_steps):
            btn = QToolButton()
            btn.setText("p")
            btn.setFixedSize(_CELL_W, _MOD_H)
            btn.setToolTip(f"Step {i+1} probability")
            btn.setStyleSheet(_prob_style)
            btn.clicked.connect(lambda checked, idx=i: self.probClicked.emit(idx))
            self._prob_btns.append(btn)
            grid.addWidget(btn, 3, i + 1)

    # ---- state sync

    def refresh_step(self, step_idx: int, step_data) -> None:
        """Sync cell and column buttons from a StepData object."""
        cell = self._cells[step_idx]
        cell.set_state(
            on=step_data.on,
            accent=step_data.accent,
            ghost=step_data.ghost,
            probability=step_data.probability,
            params=step_data.params,
        )
        self._accent_btns[step_idx].setChecked(step_data.accent)
        self._ghost_btns[step_idx].setChecked(step_data.ghost)
        prob_txt = f"{step_data.probability:.0%}" if step_data.probability < 1.0 else "p"
        self._prob_btns[step_idx].setText(prob_txt)

    def refresh_all(self, steps) -> None:
        for i, step in enumerate(steps[:self._n_steps]):
            self.refresh_step(i, step)

    def set_cursor(self, step_idx: int) -> None:
        for i, cell in enumerate(self._cells):
            cell.set_cursor(i == step_idx)

    def set_selected(self, start: int, end: int) -> None:
        for i, cell in enumerate(self._cells):
            cell.set_selected(start <= i < end)


# ---------------------------------------------------------------------------
# TrackerEditor: full tracker grid bound to a ProjectDoc PatternChannel

class TrackerEditor(QWidget):
    """Tracker grid editor for a single PatternChannel in a ProjectDoc.

    Keyboard shortcuts (when editor has focus):
      Space        — toggle current step on/off
      A            — toggle accent on current step
      G            — toggle ghost on current step
      P            — open per-step param popover
      Left/Right   — move cursor
      Ctrl+A       — select all steps
      Ctrl+C       — copy selected steps
      Ctrl+V       — paste at cursor
      Del/Backspace— clear current/selected steps
      Ctrl+Z       — undo (proxied to doc)
      Ctrl+Y/Shift+Ctrl+Z — redo

    Args:
        channel_idx: Index of the PatternChannel in *doc*.
        doc:         The ProjectDoc to edit.
        parent:      Optional parent widget.
    """

    channelChanged = Signal(int)        # emitted after every edit (channel_idx)
    cursorMoved = Signal(int)           # emitted when cursor moves (step_idx)
    volumeChanged = Signal(int, float)  # (channel_idx, 0.0–1.0)
    muteChanged = Signal(int, bool)     # (channel_idx, muted)
    soloRequested = Signal(int)         # channel_idx wants to be the only active channel
    removeRequested = Signal(int)       # channel_idx should be deleted

    def __init__(
        self,
        channel_idx: int,
        doc: "ProjectDoc",
        parent: QWidget | None = None,
    ) -> None:
        from forge.document.channels import PatternChannel
        ch = doc.channel(channel_idx)
        if not isinstance(ch, PatternChannel):
            raise TypeError("TrackerEditor requires a PatternChannel")

        super().__init__(parent)
        self._channel_idx = channel_idx
        self._doc = doc
        self._cursor = 0
        self._sel_start: int | None = None
        self._sel_end: int | None = None
        self._clipboard: list | None = None
        self._active_section: int | None = None

        channel_color = _CHANNEL_COLORS_HEX[channel_idx % len(_CHANNEL_COLORS_HEX)]

        # Faint channel-colour tint on the row background
        r = int(channel_color[1:3], 16)
        g = int(channel_color[3:5], 16)
        b = int(channel_color[5:7], 16)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            f"TrackerEditor {{ background-color: rgba({r}, {g}, {b}, 20); }}"
        )

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.setSpacing(4)

        # ── Left control panel ──────────────────────────────────────────────
        ctrl = QWidget()
        ctrl.setFixedWidth(120)
        ctrl_h = QHBoxLayout(ctrl)
        ctrl_h.setContentsMargins(0, 2, 4, 2)
        ctrl_h.setSpacing(4)

        # Vertical volume slider
        self._vol_slider = QSlider(Qt.Orientation.Vertical)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(18)
        self._vol_slider.setMinimumHeight(50)
        self._vol_slider.setToolTip("Volume (0–100 %)")
        self._vol_slider.valueChanged.connect(
            lambda v: self.volumeChanged.emit(channel_idx, v / 100.0)
        )
        ctrl_h.addWidget(self._vol_slider)

        # Label + buttons
        right_v = QVBoxLayout()
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(3)

        self._inst_label = QLabel(ch.instrument_id)
        font = QFont()
        font.setBold(True)
        font.setPointSize(8)
        self._inst_label.setFont(font)
        right_v.addWidget(self._inst_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)
        self._mute_btn = QPushButton("M")
        self._mute_btn.setCheckable(True)
        self._mute_btn.setFixedSize(32, 22)
        self._mute_btn.setToolTip("Mute this channel")
        self._mute_btn.toggled.connect(
            lambda checked: self.muteChanged.emit(channel_idx, checked)
        )
        self._solo_btn = QPushButton("S")
        self._solo_btn.setFixedSize(32, 22)
        self._solo_btn.setToolTip("Solo — mute all other channels")
        self._solo_btn.clicked.connect(lambda: self.soloRequested.emit(channel_idx))
        btn_row.addWidget(self._mute_btn)
        btn_row.addWidget(self._solo_btn)
        right_v.addLayout(btn_row)
        right_v.addStretch()

        ctrl_h.addLayout(right_v)
        outer.addWidget(ctrl)

        # ── Step grid ───────────────────────────────────────────────────────
        self._row = TrackerRow(ch.instrument_id, ch.n_steps, channel_color, self)
        self._row.stepToggled.connect(self._on_step_toggled)
        self._row.accentToggled.connect(self._on_accent_toggled)
        self._row.ghostToggled.connect(self._on_ghost_toggled)
        self._row.probClicked.connect(self._on_prob_clicked)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._row)
        outer.addWidget(scroll, stretch=1)

        # ── Remove button ────────────────────────────────────────────────────
        rem_btn = QPushButton("×")
        rem_btn.setFixedSize(24, 24)
        rem_btn.setToolTip("Remove this channel")
        rem_btn.clicked.connect(lambda: self.removeRequested.emit(channel_idx))
        outer.addWidget(rem_btn)

        # Initial refresh
        self._refresh_all()

        # Subscribe to doc changes
        doc.subscribe(self._on_doc_changed)

    # ---------------------------------------------------------------- public setters (for solo logic)

    def set_muted(self, muted: bool) -> None:
        """Set mute state without triggering extra signals if already set."""
        if self._mute_btn.isChecked() != muted:
            self._mute_btn.setChecked(muted)

    # ---------------------------------------------------------------- section support

    def set_section(self, section_idx: int | None) -> None:
        """Switch to editing a specific section's pattern (None = channel default)."""
        self._active_section = section_idx
        self._refresh_all()

    def _get_steps(self) -> list:
        """Return current steps (section override or channel default)."""
        if self._active_section is not None:
            return self._doc.get_section_steps(self._active_section, self._channel_idx)
        ch = self._doc.channel(self._channel_idx)
        return list(ch.steps)

    # ---------------------------------------------------------------- refresh

    def _refresh_all(self) -> None:
        steps = self._get_steps()
        self._row.refresh_all(steps)
        self._row.set_cursor(self._cursor)
        ch = self._doc.channel(self._channel_idx)
        self._inst_label.setText(ch.instrument_id)

    def _refresh_step(self, step_idx: int) -> None:
        steps = self._get_steps()
        self._row.refresh_step(step_idx, steps[step_idx])

    # ---------------------------------------------------------------- mouse interactions

    def _on_step_toggled(self, step_idx: int) -> None:
        self._cursor = step_idx
        self.cursorMoved.emit(step_idx)  # clicking a step selects this channel
        if self._active_section is not None:
            self._doc.toggle_section_step(self._active_section, self._channel_idx, step_idx)
        else:
            self._doc.toggle_step(self._channel_idx, step_idx)
        self.channelChanged.emit(self._channel_idx)

    def _on_accent_toggled(self, step_idx: int) -> None:
        steps = self._get_steps()
        new_val = not steps[step_idx].accent
        if self._active_section is not None:
            self._doc.set_section_step(self._active_section, self._channel_idx, step_idx, "accent", new_val)
        else:
            self._doc.set_step(self._channel_idx, step_idx, "accent", new_val)
        self.channelChanged.emit(self._channel_idx)

    def _on_ghost_toggled(self, step_idx: int) -> None:
        steps = self._get_steps()
        new_val = not steps[step_idx].ghost
        if self._active_section is not None:
            self._doc.set_section_step(self._active_section, self._channel_idx, step_idx, "ghost", new_val)
        else:
            self._doc.set_step(self._channel_idx, step_idx, "ghost", new_val)
        self.channelChanged.emit(self._channel_idx)

    def _on_prob_clicked(self, step_idx: int) -> None:
        self._open_prob_dialog(step_idx)

    def _open_prob_dialog(self, step_idx: int) -> None:
        steps = self._get_steps()
        step = steps[step_idx]
        from PySide6.QtWidgets import QInputDialog
        prob, ok = QInputDialog.getDouble(
            self,
            f"Step {step_idx + 1} probability",
            "Probability (0.0–1.0):",
            step.probability,
            0.0,
            1.0,
            2,
        )
        if ok:
            if self._active_section is not None:
                self._doc.set_section_step(self._active_section, self._channel_idx, step_idx, "probability", prob)
            else:
                self._doc.set_step(self._channel_idx, step_idx, "probability", prob)
            self.channelChanged.emit(self._channel_idx)

    def _open_param_dialog(self, step_idx: int) -> None:
        from forge import control
        ch = self._doc.channel(self._channel_idx)
        instruments = {e["id"]: e for e in control.list_instruments()}
        inst_params = instruments.get(ch.instrument_id, {}).get("params", [])
        dlg = _StepParamDialog(step_idx, ch.steps[step_idx].params, inst_params, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_params = dlg.get_params()
            for k, v in new_params.items():
                self._doc.set_step_param(self._channel_idx, step_idx, k, v)
            self.channelChanged.emit(self._channel_idx)

    # ---------------------------------------------------------------- keyboard

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        mods = event.modifiers()

        ch = self._doc.channel(self._channel_idx)
        n = ch.n_steps

        # Navigation
        if key == Qt.Key.Key_Left:
            self._cursor = max(0, self._cursor - 1)
            self._row.set_cursor(self._cursor)
            self.cursorMoved.emit(self._cursor)
            return

        if key == Qt.Key.Key_Right:
            self._cursor = min(n - 1, self._cursor + 1)
            self._row.set_cursor(self._cursor)
            self.cursorMoved.emit(self._cursor)
            return

        # Toggle on/off
        if key == Qt.Key.Key_Space:
            if self._active_section is not None:
                self._doc.toggle_section_step(self._active_section, self._channel_idx, self._cursor)
            else:
                self._doc.toggle_step(self._channel_idx, self._cursor)
            self.channelChanged.emit(self._channel_idx)
            return

        # Accent
        if key == Qt.Key.Key_A and not (mods & Qt.KeyboardModifier.ControlModifier):
            steps = self._get_steps()
            new_val = not steps[self._cursor].accent
            if self._active_section is not None:
                self._doc.set_section_step(self._active_section, self._channel_idx, self._cursor, "accent", new_val)
            else:
                self._doc.set_step(self._channel_idx, self._cursor, "accent", new_val)
            self.channelChanged.emit(self._channel_idx)
            return

        # Ghost
        if key == Qt.Key.Key_G:
            steps = self._get_steps()
            new_val = not steps[self._cursor].ghost
            if self._active_section is not None:
                self._doc.set_section_step(self._active_section, self._channel_idx, self._cursor, "ghost", new_val)
            else:
                self._doc.set_step(self._channel_idx, self._cursor, "ghost", new_val)
            self.channelChanged.emit(self._channel_idx)
            return

        # Per-step params
        if key == Qt.Key.Key_P:
            self._open_param_dialog(self._cursor)
            return

        # Select all
        if key == Qt.Key.Key_A and (mods & Qt.KeyboardModifier.ControlModifier):
            self._sel_start = 0
            self._sel_end = n
            self._row.set_selected(0, n)
            return

        # Copy
        if key == Qt.Key.Key_C and (mods & Qt.KeyboardModifier.ControlModifier):
            start = self._sel_start if self._sel_start is not None else self._cursor
            end = self._sel_end if self._sel_end is not None else self._cursor + 1
            self._clipboard = self._get_steps()[start:end]
            return

        # Paste
        if key == Qt.Key.Key_V and (mods & Qt.KeyboardModifier.ControlModifier):
            if self._clipboard:
                if self._active_section is not None:
                    import copy
                    steps = self._get_steps()
                    for offset, src in enumerate(self._clipboard):
                        idx = self._cursor + offset
                        if idx < len(steps):
                            steps[idx] = copy.copy(src)
                    self._doc.set_section_steps(self._active_section, self._channel_idx, steps)
                else:
                    self._doc.paste_steps(self._channel_idx, self._cursor, self._clipboard)
                self.channelChanged.emit(self._channel_idx)
            return

        # Delete / clear
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self._active_section is not None:
                steps = self._get_steps()
                if self._sel_start is not None and self._sel_end is not None:
                    for i in range(self._sel_start, self._sel_end):
                        steps[i].on = False
                else:
                    steps[self._cursor].on = False
                self._doc.set_section_steps(self._active_section, self._channel_idx, steps)
            else:
                if self._sel_start is not None and self._sel_end is not None:
                    for i in range(self._sel_start, self._sel_end):
                        self._doc.set_step(self._channel_idx, i, "on", False)
                else:
                    self._doc.set_step(self._channel_idx, self._cursor, "on", False)
            self.channelChanged.emit(self._channel_idx)
            return

        # Undo / Redo
        if key == Qt.Key.Key_Z and (mods & Qt.KeyboardModifier.ControlModifier):
            self._doc.undo()
            return

        if key in (Qt.Key.Key_Y,) and (mods & Qt.KeyboardModifier.ControlModifier):
            self._doc.redo()
            return

        if (key == Qt.Key.Key_Z
                and (mods & Qt.KeyboardModifier.ControlModifier)
                and (mods & Qt.KeyboardModifier.ShiftModifier)):
            self._doc.redo()
            return

        super().keyPressEvent(event)

    # ---------------------------------------------------------------- doc sync

    def _on_doc_changed(self, txn) -> None:
        # Guard: our channel may have been removed
        if self._channel_idx >= self._doc.channel_count():
            return
        for change in txn.changes:
            k = change.path[0]
            if k == "ab_restore":
                self._refresh_all()
                return
            if (k == "section_steps"
                    and change.path[1] == self._active_section
                    and change.path[2] == self._channel_idx):
                self._refresh_all()
                return
        affected = txn.affected_channel_indices()
        if self._channel_idx in affected:
            self._refresh_all()

    # ---------------------------------------------------------------- public API

    def to_pattern_spec(self) -> dict:
        """Return a PatternSpec dict for the current channel state."""
        ch = self._doc.channel(self._channel_idx)
        return {
            "bpm": self._doc.bpm,
            "length_bars": 4,
            "tracks": [ch.to_track_dict()],
        }

    @property
    def cursor(self) -> int:
        return self._cursor
