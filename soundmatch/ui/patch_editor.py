"""soundmatch.ui.patch_editor — instrument selector, param sliders, layer list, seed.

Layer tabs at the top switch between primary instrument and any added layers.
All layers share one instrument combo + InstrumentPanel that rebuilds when you
switch tab.  A "Root note" row lets you override the MIDI pitch that the phrase
derives from chord detection.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

log = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from forge.instruments.registry import REGISTRY, list_instruments
from forge.ui.instrument_panel import InstrumentPanel, _FloatSlider

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_note_name(midi: int) -> str:
    return f"{_NOTE_NAMES[midi % 12]}{(midi // 12) - 1}"


class PatchEditor(QWidget):
    """Patch editor: layer tabs, shared instrument combo + sliders, root note, seed.

    Signals:
        patchChanged(instrument_id, params, layers, seed):
            Emitted (debounced) whenever any patch parameter changes.
        suggestRequested():
            Emitted when "💡 Suggest" is clicked.
        noteOverride(midi):
            Emitted when the user changes the root note override.
            midi == -1 means "clear override, derive from chord detection".
    """

    patchChanged = Signal(str, dict, list, int)
    suggestRequested = Signal()
    noteOverride = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("patch-editor")

        self._debounce = QTimer(self)
        self._debounce.setInterval(300)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._emit_patch)

        # Per-layer data: index -1 = primary, 0+ = extra layers
        self._primary_instrument: str = ""
        self._primary_params: dict[str, Any] = {}
        self._layer_data: list[dict[str, Any]] = []  # [{'id': str, 'params': dict}]
        self._active_idx: int = -1  # which layer is being edited

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Layer tab row ─────────────────────────────────────────────
        self._tab_row = QHBoxLayout()
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        self._primary_btn = QPushButton("Primary")
        self._primary_btn.setCheckable(True)
        self._primary_btn.setChecked(True)
        self._primary_btn.setObjectName("layer-tab-primary")
        self._primary_btn.clicked.connect(lambda _=False: self._switch_to(-1))
        self._btn_group.addButton(self._primary_btn, 0)
        self._tab_row.addWidget(self._primary_btn)

        self._layer_btns: list[QPushButton] = []

        self._add_btn = QPushButton("+ Layer")
        self._add_btn.setObjectName("add-layer-btn")
        self._add_btn.clicked.connect(self._on_add_layer)
        self._tab_row.addWidget(self._add_btn)
        self._tab_row.addStretch()
        layout.addLayout(self._tab_row)

        # ── Instrument combo + remove ─────────────────────────────────
        inst_row = QHBoxLayout()
        inst_row.addWidget(QLabel("Instrument:"))
        self._inst_combo = QComboBox()
        self._inst_combo.setObjectName("instrument-combo")
        self._populate_instruments()
        self._inst_combo.currentTextChanged.connect(self._on_instrument_changed)
        inst_row.addWidget(self._inst_combo, stretch=1)

        self._remove_btn = QPushButton("Remove Layer")
        self._remove_btn.setObjectName("remove-layer-btn")
        self._remove_btn.setVisible(False)
        self._remove_btn.clicked.connect(self._on_remove_active)
        inst_row.addWidget(self._remove_btn)
        layout.addLayout(inst_row)

        # ── Param panel (scrollable) ──────────────────────────────────
        self._param_panel: InstrumentPanel | None = None
        self._param_container = QWidget()
        self._param_layout = QVBoxLayout(self._param_container)
        self._param_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("param-scroll")
        scroll.setWidget(self._param_container)
        layout.addWidget(scroll, stretch=1)

        # ── Root note override ────────────────────────────────────────
        note_row = QHBoxLayout()
        note_row.addWidget(QLabel("Note:"))
        self._note_display = QLabel("— (from chord detection)")
        self._note_display.setObjectName("note-display")
        note_row.addWidget(self._note_display, stretch=1)
        note_row.addWidget(QLabel("Override:"))
        self._note_combo = QComboBox()
        self._note_combo.setObjectName("note-override-combo")
        self._note_combo.addItem("auto", userData=-1)
        for octave in range(-1, 9):
            for name in _NOTE_NAMES:
                midi = (octave + 1) * 12 + _NOTE_NAMES.index(name)
                if 0 <= midi <= 127:
                    self._note_combo.addItem(f"{name}{octave}", userData=midi)
        self._note_combo.currentIndexChanged.connect(self._on_note_override)
        note_row.addWidget(self._note_combo)
        layout.addLayout(note_row)

        # ── Seed + actions ────────────────────────────────────────────
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self._seed_spin = QSpinBox()
        self._seed_spin.setObjectName("seed-spin")
        self._seed_spin.setRange(0, 2**31 - 1)
        self._seed_spin.setValue(42)
        self._seed_spin.valueChanged.connect(lambda _: self._schedule_emit())
        seed_row.addWidget(self._seed_spin)

        reroll_btn = QPushButton("Reroll")
        reroll_btn.setObjectName("reroll-btn")
        reroll_btn.clicked.connect(self._on_reroll)
        seed_row.addWidget(reroll_btn)

        suggest_btn = QPushButton("💡 Suggest")
        suggest_btn.setObjectName("suggest-btn")
        suggest_btn.setToolTip("Run a coarse param search to find a good starting patch")
        suggest_btn.clicked.connect(self.suggestRequested.emit)
        seed_row.addWidget(suggest_btn)

        seed_row.addStretch()
        layout.addLayout(seed_row)

        # Initialise with the first available instrument
        self._primary_instrument = self._current_combo_id()
        self._primary_params = self._default_params(self._primary_instrument)
        self._rebuild_param_panel(self._primary_instrument, self._primary_params)

    # ── Layer tabs ────────────────────────────────────────────────────

    def _switch_to(self, idx: int) -> None:
        """Save current panel state, then switch active layer to idx."""
        self._sync_active_params()
        self._active_idx = idx
        self._refresh_view()

    def _sync_active_params(self) -> None:
        """Flush current slider values into the active layer's stored dict."""
        if self._param_panel is None:
            return
        p = self._param_panel.current_params()
        if self._active_idx == -1:
            self._primary_params = p
        elif 0 <= self._active_idx < len(self._layer_data):
            self._layer_data[self._active_idx]["params"] = p

    def _refresh_view(self) -> None:
        """Rebuild instrument combo + param panel for the current active layer."""
        if self._active_idx == -1:
            inst_id = self._primary_instrument
            params = self._primary_params
        else:
            d = self._layer_data[self._active_idx]
            inst_id = d["id"]
            params = d["params"]

        # Sync instrument combo without triggering _on_instrument_changed
        self._inst_combo.blockSignals(True)
        for i in range(self._inst_combo.count()):
            if self._inst_combo.itemData(i) == inst_id:
                self._inst_combo.setCurrentIndex(i)
                break
        self._inst_combo.blockSignals(False)

        # Sync tab button check states
        self._primary_btn.setChecked(self._active_idx == -1)
        for i, btn in enumerate(self._layer_btns):
            btn.setChecked(i == self._active_idx)

        self._remove_btn.setVisible(self._active_idx >= 0)
        self._rebuild_param_panel(inst_id, params)

    def _on_add_layer(self) -> None:
        first_id = self._first_instrument_id()
        self._layer_data.append({"id": first_id, "params": self._default_params(first_id)})
        idx = len(self._layer_btns)

        btn = QPushButton(f"Layer {idx + 1}")
        btn.setCheckable(True)
        btn.setObjectName(f"layer-tab-{idx}")
        captured_idx = idx
        btn.clicked.connect(lambda _=False, ci=captured_idx: self._switch_to(ci))
        self._btn_group.addButton(btn, idx + 1)
        self._layer_btns.append(btn)
        # Insert before the "+ Layer" button (which is second-to-last before stretch)
        self._tab_row.insertWidget(self._tab_row.count() - 2, btn)

        self._switch_to(idx)
        self._schedule_emit()

    def _on_remove_active(self) -> None:
        idx = self._active_idx
        if idx < 0 or idx >= len(self._layer_data):
            return
        self._layer_data.pop(idx)
        btn = self._layer_btns.pop(idx)
        self._btn_group.removeButton(btn)
        self._tab_row.removeWidget(btn)
        btn.deleteLater()
        # Renumber remaining layer buttons
        for i, b in enumerate(self._layer_btns):
            b.setText(f"Layer {i + 1}")
        self._switch_to(-1)
        self._schedule_emit()

    # ── Instrument combo ──────────────────────────────────────────────

    def _populate_instruments(self) -> None:
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in list_instruments():
            grouped[entry["family"]].append(entry["id"])
        for family in sorted(grouped):
            self._inst_combo.addItem(f"── {family} ──", userData=None)
            for iid in grouped[family]:
                self._inst_combo.addItem(iid, userData=iid)
        for i in range(self._inst_combo.count()):
            if self._inst_combo.itemData(i) is not None:
                self._inst_combo.setCurrentIndex(i)
                break

    def _current_combo_id(self) -> str:
        data = self._inst_combo.currentData()
        if data is not None:
            return data
        text = self._inst_combo.currentText()
        return text if text in REGISTRY else "kick"

    def _first_instrument_id(self) -> str:
        for i in range(self._inst_combo.count()):
            d = self._inst_combo.itemData(i)
            if d is not None:
                return d
        return "kick"

    def _on_instrument_changed(self, _text: str) -> None:
        inst_id = self._current_combo_id()
        defaults = self._default_params(inst_id)
        if self._active_idx == -1:
            self._primary_instrument = inst_id
            self._primary_params = defaults
        elif 0 <= self._active_idx < len(self._layer_data):
            self._layer_data[self._active_idx] = {"id": inst_id, "params": defaults}
        self._rebuild_param_panel(inst_id, defaults)
        self._schedule_emit()

    # ── Param panel ───────────────────────────────────────────────────

    def _default_params(self, instrument_id: str) -> dict[str, Any]:
        entry = REGISTRY.get(instrument_id)
        if entry is None:
            return {}
        return {s.name: s.default for s in entry["params"] if s.kind != "choice"}

    def _rebuild_param_panel(self, instrument_id: str, params: dict[str, Any]) -> None:
        if self._param_panel is not None:
            self._param_layout.removeWidget(self._param_panel)
            self._param_panel.deleteLater()
            self._param_panel = None

        entry = REGISTRY.get(instrument_id)
        if entry is None:
            return
        schemas = [s.to_dict() for s in entry["params"]]
        self._param_panel = InstrumentPanel(instrument_id, schemas, self._param_container)
        # Apply stored values to the sliders
        self._apply_params_to_panel(params)
        self._param_panel.paramsChanged.connect(lambda _: self._schedule_emit())
        self._param_layout.addWidget(self._param_panel)

    def _apply_params_to_panel(self, params: dict[str, Any]) -> None:
        """Push stored param values into the current panel's controls."""
        if self._param_panel is None:
            return
        for name, ctrl in self._param_panel._controls.items():
            if name not in params:
                continue
            val = params[name]
            if isinstance(ctrl, _FloatSlider):
                ctrl.set_value(float(val))
            elif hasattr(ctrl, "setChecked"):
                ctrl.setChecked(bool(val))
            elif hasattr(ctrl, "setValue"):
                ctrl.setValue(int(val))

    # ── Note override ─────────────────────────────────────────────────

    def _on_note_override(self, _idx: int) -> None:
        midi = self._note_combo.currentData()
        if midi is None:
            return
        self.noteOverride.emit(int(midi))

    def set_phrase_notes(self, midi_notes: list[int]) -> None:
        """Update the note display with the current phrase's MIDI pitches."""
        if not midi_notes:
            self._note_display.setText("—")
            return
        names = ", ".join(midi_to_note_name(m) for m in midi_notes[:4])
        if len(midi_notes) > 4:
            names += f" … ({len(midi_notes)} notes)"
        self._note_display.setText(names)

    # ── Seed ──────────────────────────────────────────────────────────

    def _on_reroll(self) -> None:
        import numpy as np
        rng = np.random.default_rng()
        self._seed_spin.setValue(int(rng.integers(0, 2**31 - 1)))

    # ── Debounce / emit ───────────────────────────────────────────────

    def _schedule_emit(self) -> None:
        self._debounce.start()

    def _emit_patch(self) -> None:
        self._sync_active_params()
        inst_id = self._primary_instrument
        params = dict(self._primary_params)
        layers = [(d["id"], dict(d["params"])) for d in self._layer_data]
        seed = self._seed_spin.value()
        log.debug("patchChanged: %s seed=%d layers=%d", inst_id, seed, len(layers))
        self.patchChanged.emit(inst_id, params, layers, seed)

    # ── Public API ────────────────────────────────────────────────────

    @property
    def instrument_id(self) -> str:
        self._sync_active_params()
        return self._primary_instrument

    @property
    def params(self) -> dict[str, Any]:
        self._sync_active_params()
        return dict(self._primary_params)

    @property
    def layers(self) -> list[tuple[str, dict[str, Any]]]:
        self._sync_active_params()
        return [(d["id"], dict(d["params"])) for d in self._layer_data]

    @property
    def seed(self) -> int:
        return self._seed_spin.value()

    def set_patch(
        self,
        instrument_id: str,
        params: dict[str, Any],
        layers: list[tuple[str, dict[str, Any]]],
        seed: int,
    ) -> None:
        """Programmatically set the full patch (e.g. from project load or Promote)."""
        self._debounce.stop()

        # Remove existing layer buttons
        for btn in self._layer_btns:
            self._btn_group.removeButton(btn)
            self._tab_row.removeWidget(btn)
            btn.deleteLater()
        self._layer_btns.clear()
        self._layer_data.clear()

        # Primary
        self._primary_instrument = instrument_id
        self._primary_params = dict(params)

        # Layers
        for i, (inst_id, lparams) in enumerate(layers):
            self._layer_data.append({"id": inst_id, "params": dict(lparams)})
            btn = QPushButton(f"Layer {i + 1}")
            btn.setCheckable(True)
            btn.setObjectName(f"layer-tab-{i}")
            captured = i
            btn.clicked.connect(lambda _=False, ci=captured: self._switch_to(ci))
            self._btn_group.addButton(btn, i + 1)
            self._layer_btns.append(btn)
            self._tab_row.insertWidget(self._tab_row.count() - 2, btn)

        # Seed
        self._seed_spin.blockSignals(True)
        self._seed_spin.setValue(seed)
        self._seed_spin.blockSignals(False)

        # Switch to primary view and rebuild
        self._active_idx = -1
        self._primary_btn.setChecked(True)
        for btn in self._layer_btns:
            btn.setChecked(False)
        self._remove_btn.setVisible(False)

        # Update instrument combo
        self._inst_combo.blockSignals(True)
        for i in range(self._inst_combo.count()):
            if self._inst_combo.itemData(i) == instrument_id:
                self._inst_combo.setCurrentIndex(i)
                break
        self._inst_combo.blockSignals(False)

        self._rebuild_param_panel(instrument_id, self._primary_params)
        self._schedule_emit()
