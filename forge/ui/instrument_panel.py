"""forge.ui.instrument_panel — per-instrument parameter controls.

InstrumentPanel auto-builds a row of controls from a ParamSchema list
(returned by control.list_instruments()).  Each schema entry becomes:
  - float/int → labelled QSlider
  - bool      → QCheckBox

Usage::

    panel = InstrumentPanel("kick", schemas, parent)
    panel.paramsChanged.connect(on_params_changed)  # dict
    panel.render_btn_clicked.connect(on_render)
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from PySide6.QtCore import Qt


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

    paramsChanged = Signal(dict)       # current param dict
    renderRequested = Signal(str, dict)  # (instrument_id, params)

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
