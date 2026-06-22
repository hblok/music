"""soundmatch.ui.patch_editor — instrument selector, param sliders, layer list, seed.

Wraps ``forge.ui.instrument_panel.InstrumentPanel`` for the auto-built param
sliders (it already maps ``ParamSchema`` to sliders/checkboxes).  Adds a
layer list for the tonal+snap split, a seed spin-box, and emits a debounced
``patchChanged(instrument_id, params, layers, seed)`` signal.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from forge.instruments.registry import REGISTRY, list_instruments
from forge.ui.instrument_panel import InstrumentPanel


class _LayerRow(QWidget):
    """A single layer row: instrument combo + remove button."""

    changed = Signal()
    removeRequested = Signal(object)  # self

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.setObjectName("layer-instrument-combo")
        self._populate_combo()
        self._combo.currentTextChanged.connect(lambda _: self.changed.emit())
        layout.addWidget(self._combo, stretch=1)

        # Placeholder for params label (user uses the main panel to tweak)
        self._params_label = QLabel("default params")
        self._params_label.setObjectName("layer-params-label")
        layout.addWidget(self._params_label, stretch=1)

        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("layer-remove-btn")
        remove_btn.setFixedWidth(24)
        remove_btn.clicked.connect(lambda: self.removeRequested.emit(self))
        layout.addWidget(remove_btn)

    def _populate_combo(self) -> None:
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in list_instruments():
            grouped[entry["family"]].append(entry["id"])
        for family in sorted(grouped):
            for iid in grouped[family]:
                self._combo.addItem(iid)

    @property
    def instrument_id(self) -> str:
        return self._combo.currentText()

    @property
    def params(self) -> dict[str, Any]:
        """Return default params for the selected instrument."""
        entry = REGISTRY.get(self.instrument_id)
        if entry is None:
            return {}
        return {s.name: s.default for s in entry["params"] if s.kind != "choice"}


class PatchEditor(QWidget):
    """Patch editor: instrument selector, auto-built sliders, layer list, seed.

    Signals:
        patchChanged(instrument_id, params, layers, seed):
            Emitted (debounced) when any patch parameter changes.

    Args:
        parent: Optional parent widget.
    """

    patchChanged = Signal(str, dict, list, int)  # instrument_id, params, layers, seed

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("patch-editor")

        # Debounce timer: coalesce rapid slider moves into one signal.
        self._debounce = QTimer(self)
        self._debounce.setInterval(300)  # ms
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._emit_patch)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Instrument selector ──────────────────────────────────────
        inst_group = QGroupBox("Instrument")
        inst_layout = QVBoxLayout(inst_group)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Primary:"))
        self._inst_combo = QComboBox()
        self._inst_combo.setObjectName("instrument-combo")
        self._populate_instruments()
        self._inst_combo.currentTextChanged.connect(self._on_instrument_changed)
        sel_row.addWidget(self._inst_combo, stretch=1)
        inst_layout.addLayout(sel_row)

        # Reuse forge InstrumentPanel for auto-built sliders
        self._param_panel: InstrumentPanel | None = None
        self._param_container = QWidget()
        self._param_layout = QVBoxLayout(self._param_container)
        self._param_layout.setContentsMargins(0, 0, 0, 0)
        inst_layout.addWidget(self._param_container)

        layout.addWidget(inst_group)

        # ── Seed ─────────────────────────────────────────────────────
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
        seed_row.addStretch()
        layout.addLayout(seed_row)

        # ── Layers ───────────────────────────────────────────────────
        layers_group = QGroupBox("Layers")
        self._layers_layout = QVBoxLayout(layers_group)

        add_btn = QPushButton("+ Add Layer")
        add_btn.setObjectName("add-layer-btn")
        add_btn.clicked.connect(self._on_add_layer)
        self._layers_layout.addWidget(add_btn)

        self._layer_rows: list[_LayerRow] = []
        layout.addWidget(layers_group)

        # Build the initial param panel
        self._rebuild_param_panel(self._inst_combo.currentText())

    # ── Instrument combo ─────────────────────────────────────────────

    def _populate_instruments(self) -> None:
        """Populate the instrument combo, grouped by family."""
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in list_instruments():
            grouped[entry["family"]].append(entry["id"])
        for family in sorted(grouped):
            self._inst_combo.addItem(f"── {family} ──", userData=None)
            for iid in grouped[family]:
                self._inst_combo.addItem(iid, userData=iid)
        # Select first real instrument
        for i in range(self._inst_combo.count()):
            if self._inst_combo.itemData(i) is not None:
                self._inst_combo.setCurrentIndex(i)
                break

    def _current_instrument_id(self) -> str:
        data = self._inst_combo.currentData()
        if data is not None:
            return data
        # Fallback: use currentText if itemData not set
        text = self._inst_combo.currentText()
        if text in REGISTRY:
            return text
        return "kick"  # safe fallback

    # ── Param panel ──────────────────────────────────────────────────

    def _rebuild_param_panel(self, instrument_id: str) -> None:
        """Rebuild the InstrumentPanel for the given instrument."""
        # Clear old panel
        if self._param_panel is not None:
            self._param_layout.removeWidget(self._param_panel)
            self._param_panel.deleteLater()
            self._param_panel = None

        # Get schemas as dicts for InstrumentPanel
        entry = REGISTRY.get(instrument_id)
        if entry is None:
            return
        schemas = [p.to_dict() for p in entry["params"]]

        self._param_panel = InstrumentPanel(instrument_id, schemas, self._param_container)
        self._param_panel.paramsChanged.connect(lambda _: self._schedule_emit())
        self._param_layout.addWidget(self._param_panel)

    # ── Layers ───────────────────────────────────────────────────────

    def _on_add_layer(self) -> None:
        row = _LayerRow(self)
        row.changed.connect(self._schedule_emit)
        row.removeRequested.connect(self._on_remove_layer)
        self._layer_rows.append(row)
        # Insert before the "Add Layer" button
        add_btn = self.sender()
        if isinstance(add_btn, QPushButton):
            idx = self._layers_layout.indexOf(add_btn)
            self._layers_layout.insertWidget(idx, row)
        else:
            self._layers_layout.insertWidget(self._layers_layout.count() - 1, row)
        self._schedule_emit()

    def _on_remove_layer(self, row: _LayerRow) -> None:
        if row in self._layer_rows:
            self._layer_rows.remove(row)
            self._layers_layout.removeWidget(row)
            row.deleteLater()
            self._schedule_emit()

    # ── Seed ─────────────────────────────────────────────────────────

    def _on_reroll(self) -> None:
        import numpy as np
        rng = np.random.default_rng()
        self._seed_spin.setValue(int(rng.integers(0, 2**31 - 1)))

    # ── Slots ────────────────────────────────────────────────────────

    def _on_instrument_changed(self, text: str) -> None:
        inst_id = self._current_instrument_id()
        self._rebuild_param_panel(inst_id)
        self._schedule_emit()

    # ── Debounce ─────────────────────────────────────────────────────

    def _schedule_emit(self) -> None:
        self._debounce.start()

    def _emit_patch(self) -> None:
        inst_id = self._current_instrument_id()
        params = self._param_panel.current_params() if self._param_panel else {}
        layers = [(row.instrument_id, row.params) for row in self._layer_rows]
        seed = self._seed_spin.value()
        self.patchChanged.emit(inst_id, params, layers, seed)

    # ── Public API ───────────────────────────────────────────────────

    @property
    def instrument_id(self) -> str:
        return self._current_instrument_id()

    @property
    def params(self) -> dict[str, Any]:
        return self._param_panel.current_params() if self._param_panel else {}

    @property
    def layers(self) -> list[tuple[str, dict[str, Any]]]:
        return [(row.instrument_id, row.params) for row in self._layer_rows]

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
        """Programmatically set the patch (e.g. from a loaded project)."""
        # Set instrument
        for i in range(self._inst_combo.count()):
            if self._inst_combo.itemData(i) == instrument_id:
                self._inst_combo.setCurrentIndex(i)
                break
        # Rebuild panel + set params is handled by _on_instrument_changed
        # Set seed
        self._seed_spin.setValue(seed)
        # Set layers
        for row in list(self._layer_rows):
            self._on_remove_layer(row)
        for inst, lparams in layers:
            row = _LayerRow(self)
            row.changed.connect(self._schedule_emit)
            row.removeRequested.connect(self._on_remove_layer)
            # Set the instrument
            idx = row._combo.findText(inst)
            if idx >= 0:
                row._combo.setCurrentIndex(idx)
            self._layer_rows.append(row)
            self._layers_layout.insertWidget(self._layers_layout.count() - 1, row)
