"""forge.ui.instrument_panel — per-instrument parameter controls.

Two classes:
  InstrumentPanel  — original auto-built controls from ParamSchema (unchanged
                     API; existing tests pass unchanged).
  WorkshopPanel    — Phase 4 extension: binds to ProjectDoc + RenderScheduler;
                     adds seed control, reroll, audition button, and a
                     "rendering…/cached" status indicator.

Usage (legacy)::

    panel = InstrumentPanel("kick", schemas, parent)
    panel.paramsChanged.connect(on_params_changed)  # dict

Usage (workshop)::

    panel = WorkshopPanel(channel_idx=0, doc=my_doc, scheduler=sched, parent=w)
    panel.auditionRequested.connect(on_audition)   # (channel_idx, buf)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from PySide6.QtCore import Qt, QMetaObject, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc
    from forge.playback.scheduler import RenderScheduler


class _FloatSlider(QWidget):
    """A labelled slider that maps to a float range."""

    valueChanged = Signal(float)

    def __init__(
        self,
        schema: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._schema = schema
        self._lo = float(schema.get("lo") or 0.0)
        self._hi = float(schema.get("hi") or 1.0)
        self._resolution = 1000

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, self._resolution)
        self._value_label = QLabel()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider, stretch=1)
        layout.addWidget(self._value_label, stretch=0)
        self._value_label.setFixedWidth(60)

        default = float(schema.get("default", self._lo))
        self.set_value(default)

        self._slider.valueChanged.connect(self._on_slider_changed)

    def _on_slider_changed(self, tick: int) -> None:
        v = self._lo + (self._hi - self._lo) * tick / self._resolution
        unit = self._schema.get("unit", "")
        self._value_label.setText(f"{v:.3g} {unit}".strip())
        self.valueChanged.emit(v)

    def set_value(self, v: float) -> None:
        tick = int((v - self._lo) / max(self._hi - self._lo, 1e-12) * self._resolution)
        tick = max(0, min(self._resolution, tick))
        self._slider.setValue(tick)
        unit = self._schema.get("unit", "")
        self._value_label.setText(f"{v:.3g} {unit}".strip())

    @property
    def value(self) -> float:
        tick = self._slider.value()
        return self._lo + (self._hi - self._lo) * tick / self._resolution


class InstrumentPanel(QGroupBox):
    """Auto-built parameter controls for one instrument.

    Args:
        instrument_id: Registry key (e.g. ``"kick"``).
        schemas:       list of ParamSchema dicts from ``list_instruments()``.
        parent:        optional parent widget.
    """

    paramsChanged = Signal(dict)          # current param dict
    renderRequested = Signal(str, dict)   # (instrument_id, params)

    def __init__(
        self,
        instrument_id: str,
        schemas: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(instrument_id, parent)
        self._instrument_id = instrument_id
        self._schemas = schemas
        self._controls: dict[str, QWidget] = {}

        outer = QVBoxLayout(self)

        scroll_content = QWidget()
        form = QFormLayout(scroll_content)
        form.setContentsMargins(4, 4, 4, 4)

        for schema in schemas:
            name = schema["name"]
            label = schema.get("label") or name
            kind = schema.get("kind", "float")

            if kind == "bool":
                ctrl = QCheckBox()
                ctrl.setChecked(bool(schema.get("default", False)))
                ctrl.stateChanged.connect(lambda _, n=name: self._emit())
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

            elif kind in ("float",):
                ctrl = _FloatSlider(schema)
                ctrl.valueChanged.connect(lambda _, n=name: self._emit())
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

            elif kind == "int":
                ctrl = QSpinBox()
                lo = int(schema.get("lo") or 0)
                hi = int(schema.get("hi") or 127)
                ctrl.setRange(lo, hi)
                ctrl.setValue(int(schema.get("default", lo)))
                ctrl.valueChanged.connect(lambda _, n=name: self._emit())
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        outer.addWidget(scroll)

        render_btn = QPushButton("▶ Render & Preview")
        render_btn.clicked.connect(self._on_render)
        outer.addWidget(render_btn)

    def _emit(self) -> None:
        self.paramsChanged.emit(self.current_params())

    def _on_render(self) -> None:
        self.renderRequested.emit(self._instrument_id, self.current_params())

    def current_params(self) -> dict:
        """Return the current parameter dict."""
        result = {}
        for schema in self._schemas:
            name = schema["name"]
            kind = schema.get("kind", "float")
            ctrl = self._controls.get(name)
            if ctrl is None:
                result[name] = schema.get("default")
            elif kind == "bool":
                result[name] = ctrl.isChecked()
            elif kind == "float":
                result[name] = ctrl.value
            elif kind == "int":
                result[name] = ctrl.value()
        return result

    @classmethod
    def from_registry(
        cls,
        instrument_id: str,
        parent: QWidget | None = None,
    ) -> "InstrumentPanel":
        """Build an InstrumentPanel by querying the live registry."""
        from forge import control
        instruments = {e["id"]: e for e in control.list_instruments()}
        entry = instruments[instrument_id]
        return cls(instrument_id, entry["params"], parent)


# ---------------------------------------------------------------------------
# WorkshopPanel — Phase 4 extension

class WorkshopPanel(QGroupBox):
    """Instrument workshop panel bound to a ProjectDoc channel.

    Combines the auto-built param sliders with:
      - Per-instrument seed control (SpinBox) + Reroll button.
      - Cache-backed audition: clicking "Audition" schedules a background
        render via *scheduler*; repeated auditions of unchanged params are
        instant (cache hit).
      - Status indicator showing "rendering…" / "cached / <ms> ms".
      - All slider moves are ProjectDoc transactions (undoable).

    Args:
        channel_idx: Index of the PatternChannel in *doc*.
        doc:         ProjectDoc owning the channel.
        scheduler:   RenderScheduler for background renders.
        bpm:         Project tempo (for render_channel).
        length_bars: Pattern length for audition render (default 4).
        parent:      Optional parent widget.

    Signals:
        auditionReady(channel_idx, np.ndarray): emitted when a rendered buffer
            is ready for playback.  The UI connects this to the mixer.
    """

    auditionReady = Signal(int, object)  # (channel_idx, np.ndarray)
    statusChanged = Signal(str)          # "rendering…" / "cached"

    def __init__(
        self,
        channel_idx: int,
        doc: "ProjectDoc",
        scheduler: "RenderScheduler",
        *,
        bpm: float = 138.0,
        length_bars: int = 4,
        parent: QWidget | None = None,
    ) -> None:
        from forge.document.channels import PatternChannel
        ch = doc.channel(channel_idx)
        if not isinstance(ch, PatternChannel):
            raise TypeError("WorkshopPanel requires a PatternChannel")

        super().__init__(ch.instrument_id, parent)
        self._channel_idx = channel_idx
        self._doc = doc
        self._scheduler = scheduler
        self._bpm = bpm
        self._length_bars = length_bars
        self._schemas: list[dict] = []
        self._controls: dict[str, QWidget] = {}

        # Suppress doc-change re-entry while we are applying slider values
        self._applying = False

        outer = QVBoxLayout(self)

        # Instrument selector row
        inst_row = QHBoxLayout()
        inst_row.addWidget(QLabel("Instrument:"))
        from PySide6.QtWidgets import QComboBox
        self._inst_combo = QComboBox()
        from forge import control
        for entry in control.list_instruments():
            self._inst_combo.addItem(entry["id"])
        self._inst_combo.setCurrentText(ch.instrument_id)
        self._inst_combo.currentTextChanged.connect(self._on_instrument_changed)
        inst_row.addWidget(self._inst_combo)
        outer.addLayout(inst_row)

        # Param form (rebuilt per instrument)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        outer.addWidget(self._scroll_area)

        # Seed row
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 2 ** 31 - 1)
        self._seed_spin.setValue(ch.seed)
        self._seed_spin.valueChanged.connect(self._on_seed_changed)
        reroll_btn = QPushButton("Reroll")
        reroll_btn.clicked.connect(self._on_reroll)
        seed_row.addWidget(self._seed_spin)
        seed_row.addWidget(reroll_btn)
        outer.addLayout(seed_row)

        # Audition + status
        bottom_row = QHBoxLayout()
        audition_btn = QPushButton("▶ Audition")
        audition_btn.clicked.connect(self._on_audition)
        self._status_label = QLabel("ready")
        self._status_label.setFixedWidth(160)
        bottom_row.addWidget(audition_btn)
        bottom_row.addWidget(self._status_label)
        outer.addLayout(bottom_row)

        # Build controls for current instrument
        self._rebuild_params(ch.instrument_id)

        # Listen for doc changes (from undo/redo or other panels)
        doc.subscribe(self._on_doc_changed)

    # ---------------------------------------------------------------- instrument change

    def _on_instrument_changed(self, iid: str) -> None:
        if self._applying:
            return
        self._doc.set_instrument(self._channel_idx, iid)
        self._rebuild_params(iid)
        self.setTitle(iid)

    def _rebuild_params(self, instrument_id: str) -> None:
        from forge import control
        instruments = {e["id"]: e for e in control.list_instruments()}
        entry = instruments.get(instrument_id, {})
        self._schemas = entry.get("params", [])
        self._controls = {}

        content = QWidget()
        form = QFormLayout(content)
        form.setContentsMargins(4, 4, 4, 4)

        ch = self._doc.channel(self._channel_idx)
        current_params = ch.params if hasattr(ch, "params") else {}

        for schema in self._schemas:
            name = schema["name"]
            label = schema.get("label") or name
            kind = schema.get("kind", "float")
            default = current_params.get(name, schema.get("default"))

            if kind == "bool":
                ctrl = QCheckBox()
                ctrl.setChecked(bool(default) if default is not None else False)
                ctrl.stateChanged.connect(lambda _, n=name: self._on_param_changed(n))
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

            elif kind == "float":
                ctrl = _FloatSlider(schema)
                if default is not None:
                    ctrl.set_value(float(default))
                ctrl.valueChanged.connect(lambda _, n=name: self._on_param_changed(n))
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

            elif kind == "int":
                ctrl = QSpinBox()
                lo = int(schema.get("lo") or 0)
                hi = int(schema.get("hi") or 127)
                ctrl.setRange(lo, hi)
                if default is not None:
                    ctrl.setValue(int(default))
                ctrl.valueChanged.connect(lambda _, n=name: self._on_param_changed(n))
                form.addRow(label, ctrl)
                self._controls[name] = ctrl

        self._scroll_area.setWidget(content)

    # ---------------------------------------------------------------- param change

    def _on_param_changed(self, name: str) -> None:
        if self._applying:
            return
        value = self._ctrl_value(name)
        if value is not None:
            self._doc.set_param(self._channel_idx, name, value, coalesce=True)
        self._maybe_audition()

    def _ctrl_value(self, name: str):
        ctrl = self._controls.get(name)
        if ctrl is None:
            return None
        schema = next((s for s in self._schemas if s["name"] == name), None)
        if schema is None:
            return None
        kind = schema.get("kind", "float")
        if kind == "bool":
            return ctrl.isChecked()
        elif kind == "float":
            return ctrl.value
        elif kind == "int":
            return ctrl.value()
        return None

    def current_params(self) -> dict:
        result = {}
        for schema in self._schemas:
            name = schema["name"]
            v = self._ctrl_value(name)
            if v is not None:
                result[name] = v
            else:
                result[name] = schema.get("default")
        return result

    # ---------------------------------------------------------------- seed

    def _on_seed_changed(self, seed: int) -> None:
        if self._applying:
            return
        self._doc.set_seed(self._channel_idx, seed)

    def _on_reroll(self) -> None:
        self._doc.reroll(self._channel_idx)
        self._applying = True
        self._seed_spin.setValue(self._doc.channel(self._channel_idx).seed)
        self._applying = False

    # ---------------------------------------------------------------- audition

    def _maybe_audition(self) -> None:
        """Schedule a background re-render when params change."""
        key = self._doc.channel_cache_key(self._channel_idx)
        if self._scheduler.is_fresh(key):
            self._set_status("cached")
            return
        self._set_status("rendering…")
        ch_snapshot = self._doc.channel(self._channel_idx).copy()
        bpm = self._bpm
        length_bars = self._length_bars

        def render_fn():
            from forge import control
            buf = control.render_channel(ch_snapshot, bpm=bpm, length_bars=length_bars, seed=ch_snapshot.seed)
            return buf.data.astype(np.float32)

        self._scheduler.get_or_schedule(key, render_fn, on_done=self._on_render_done)

    def _on_audition(self) -> None:
        """Explicit audition button: force-schedule even if cached."""
        key = self._doc.channel_cache_key(self._channel_idx)
        cached = self._scheduler._cache.get(key)
        if cached is not None:
            self._set_status("cached")
            self.auditionReady.emit(self._channel_idx, cached)
            return
        self._maybe_audition()

    def _on_render_done(self, key: str, buf: np.ndarray) -> None:
        self._pending_buf = buf
        # Marshal from worker thread to Qt main thread via a zero-delay timer.
        QTimer.singleShot(0, self._emit_audition_ready)
        self._set_status("cached")

    @Slot()
    def _emit_audition_ready(self) -> None:
        buf = getattr(self, "_pending_buf", None)
        if buf is not None:
            self.auditionReady.emit(self._channel_idx, buf)
            self._pending_buf = None

    def _set_status(self, msg: str) -> None:
        self._status_label.setText(msg)
        self.statusChanged.emit(msg)

    # ---------------------------------------------------------------- doc change (undo/redo sync)

    def _on_doc_changed(self, txn) -> None:
        # Guard: our channel may have been removed
        if self._channel_idx >= self._doc.channel_count():
            return
        affected = txn.affected_channel_indices()
        if self._channel_idx not in affected and ("global" not in str(txn.description)):
            return
        self._applying = True
        try:
            ch = self._doc.channel(self._channel_idx)
            # Handle instrument change (undo/redo or external edit)
            if self._inst_combo.currentText() != ch.instrument_id:
                self._inst_combo.setCurrentText(ch.instrument_id)
                self._rebuild_params(ch.instrument_id)
                self.setTitle(ch.instrument_id)
                return
            # Sync seed spin
            self._seed_spin.setValue(ch.seed)
            # Sync param controls
            for name, ctrl in self._controls.items():
                schema = next((s for s in self._schemas if s["name"] == name), None)
                if schema is None:
                    continue
                kind = schema.get("kind", "float")
                v = ch.params.get(name, schema.get("default"))
                if v is None:
                    continue
                if kind == "bool" and hasattr(ctrl, "setChecked"):
                    ctrl.setChecked(bool(v))
                elif kind == "float" and hasattr(ctrl, "set_value"):
                    ctrl.set_value(float(v))
                elif kind == "int" and hasattr(ctrl, "setValue"):
                    ctrl.setValue(int(v))
        finally:
            self._applying = False
