"""forge.ui.automation_lane — breakpoint-curve editor for texture envelopes
and automation lanes.

Three classes:

  BreakpointCurveWidget  — raw Qt canvas: draw / move / delete breakpoints.
  TextureLane            — wraps the curve; bound to a ProjectDoc TextureChannel.
  AutomationLane         — wraps the curve; bound to a ProjectDoc AutomationChannel.

Coordinate conventions
  x-axis: bar number (0 .. bar_count)
  y-axis: value      (lo .. hi, typically 0.0 .. 1.0)

Mouse interaction on BreakpointCurveWidget
  Left-click on empty area  → add a breakpoint
  Left-drag on existing dot → move it
  Right-click on dot        → remove it
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc


# ---------------------------------------------------------------------------
# Colours

_C_BG = "#1a1a2e"
_C_GRID = "#333355"
_C_LINE = "#3a8ee8"
_C_DOT = "#e8a03a"
_C_DOT_OUTLINE = "#ffffff"


# ---------------------------------------------------------------------------
# BreakpointCurveWidget

class BreakpointCurveWidget(QWidget):
    """Interactive breakpoint curve editor (no Qt-level scroll; fits in a panel).

    Signals:
        curveChanged(list):  emitted with list of ``(bar, value)`` tuples whenever
                             the curve is modified.
    """

    curveChanged = Signal(list)

    _PAD = 8
    _DOT_R = 5
    _PICK_R = 12

    def __init__(
        self,
        *,
        bar_count: float = 8.0,
        lo: float = 0.0,
        hi: float = 1.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bar_count = float(bar_count)
        self._lo = float(lo)
        self._hi = float(hi)
        # Each point is a mutable list [bar, value] so we can hold a reference
        # during drag without index-tracking after sort.
        self._pts: list[list[float]] = []
        self._drag_pt: list[float] | None = None  # reference into _pts

        self.setMinimumSize(160, 64)
        self.setMouseTracking(True)

    # ---------------------------------------------------------------- public API

    def set_points(self, points) -> None:
        """Replace all points from an iterable of ``(bar, value)``."""
        self._pts = sorted([list(p) for p in points], key=lambda p: p[0])
        self._drag_pt = None
        self.update()

    def points(self) -> list[tuple[float, float]]:
        """Return sorted list of ``(bar, value)`` tuples."""
        return [(p[0], p[1]) for p in sorted(self._pts, key=lambda p: p[0])]

    def add_point(self, bar: float, value: float) -> None:
        """Programmatically add a point and emit curveChanged."""
        self._pts.append([float(bar), float(value)])
        self._pts.sort(key=lambda p: p[0])
        self.update()
        self.curveChanged.emit(self.points())

    def remove_point(self, idx: int) -> None:
        """Programmatically remove point at *idx* (sorted order) and emit curveChanged."""
        sorted_pts = sorted(self._pts, key=lambda p: p[0])
        target = sorted_pts[idx]
        self._pts.remove(target)
        self.update()
        self.curveChanged.emit(self.points())

    # ---------------------------------------------------------------- coordinate helpers

    def _to_px(self, bar: float, value: float) -> tuple[float, float]:
        pad = self._PAD
        w, h = self.width(), self.height()
        x = pad + (bar / self._bar_count) * (w - 2 * pad)
        span = self._hi - self._lo or 1.0
        y = pad + (1.0 - (value - self._lo) / span) * (h - 2 * pad)
        return x, y

    def _from_px(self, x: float, y: float) -> tuple[float, float]:
        pad = self._PAD
        w, h = self.width(), self.height()
        bar = max(0.0, min(self._bar_count, (x - pad) / max(w - 2 * pad, 1) * self._bar_count))
        span = self._hi - self._lo or 1.0
        val = self._lo + (1.0 - (y - pad) / max(h - 2 * pad, 1)) * span
        val = max(self._lo, min(self._hi, val))
        return bar, val

    def _nearest(self, x: float, y: float) -> tuple[list[float] | None, float]:
        """Return (point_ref, dist) for the nearest point within _PICK_R."""
        best_pt, best_d = None, float("inf")
        for pt in self._pts:
            px, py = self._to_px(pt[0], pt[1])
            d = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
            if d < self._PICK_R and d < best_d:
                best_pt, best_d = pt, d
        return best_pt, best_d

    # ---------------------------------------------------------------- painting

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(_C_BG))

        # Bar grid lines
        pen = QPen(QColor(_C_GRID))
        pen.setWidth(1)
        painter.setPen(pen)
        for bar in range(int(self._bar_count) + 1):
            px, _ = self._to_px(float(bar), self._lo)
            painter.drawLine(int(px), 0, int(px), self.height())

        sorted_pts = sorted(self._pts, key=lambda p: p[0])

        # Curve line
        if len(sorted_pts) >= 2:
            pen = QPen(QColor(_C_LINE))
            pen.setWidth(2)
            painter.setPen(pen)
            pxs = [self._to_px(p[0], p[1]) for p in sorted_pts]
            for i in range(len(pxs) - 1):
                painter.drawLine(int(pxs[i][0]), int(pxs[i][1]),
                                 int(pxs[i + 1][0]), int(pxs[i + 1][1]))

        # Dots
        r = self._DOT_R
        for pt in sorted_pts:
            px, py = self._to_px(pt[0], pt[1])
            painter.setBrush(QColor(_C_DOT))
            painter.setPen(QPen(QColor(_C_DOT_OUTLINE), 1))
            painter.drawEllipse(int(px) - r, int(py) - r, 2 * r, 2 * r)

    # ---------------------------------------------------------------- mouse

    def mousePressEvent(self, event) -> None:
        x, y = event.position().x(), event.position().y()
        if event.button() == Qt.MouseButton.RightButton:
            pt, _ = self._nearest(x, y)
            if pt is not None:
                self._pts.remove(pt)
                self._drag_pt = None
                self.update()
                self.curveChanged.emit(self.points())
        else:
            pt, _ = self._nearest(x, y)
            if pt is not None:
                self._drag_pt = pt
            else:
                bar, val = self._from_px(x, y)
                new_pt = [bar, val]
                self._pts.append(new_pt)
                self._drag_pt = new_pt
                self.update()
                self.curveChanged.emit(self.points())

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pt is None:
            return
        x, y = event.position().x(), event.position().y()
        bar, val = self._from_px(x, y)
        self._drag_pt[0] = bar
        self._drag_pt[1] = val
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_pt is not None:
            self._drag_pt = None
            self._pts.sort(key=lambda p: p[0])
            self.update()
            self.curveChanged.emit(self.points())


# ---------------------------------------------------------------------------
# TextureLane

class TextureLane(QWidget):
    """Envelope editor bound to a ``TextureChannel`` in a ``ProjectDoc``.

    The lane shows a breakpoint curve over *bar_count* bars.  Editing the
    curve writes back through ``doc.replace_envelope()``.

    Args:
        channel_idx: Index of the TextureChannel in *doc*.
        doc:         Live ProjectDoc.
        bar_count:   Horizontal span of the lane in bars.
        parent:      Optional parent widget.
    """

    def __init__(
        self,
        channel_idx: int,
        doc: "ProjectDoc",
        *,
        bar_count: float = 8.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._channel_idx = channel_idx
        self._doc = doc
        self._applying = False

        ch = doc.channel(channel_idx)
        label_text = getattr(ch, "instrument_id", "texture")

        self._curve = BreakpointCurveWidget(bar_count=bar_count, lo=0.0, hi=1.0)
        self._curve.curveChanged.connect(self._on_curve_changed)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(48)
        clear_btn.clicked.connect(self._on_clear)

        header = QHBoxLayout()
        header.addWidget(QLabel(label_text))
        header.addStretch()
        header.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addLayout(header)
        layout.addWidget(self._curve)

        self._refresh_from_doc()
        doc.subscribe(self._on_doc_changed)

    def _refresh_from_doc(self) -> None:
        ch = self._doc.channel(self._channel_idx)
        pts = [(b.bar, b.value) for b in ch.envelope]
        self._curve.set_points(pts)

    def _on_doc_changed(self, txn) -> None:
        if self._applying:
            return
        affected = txn.affected_channel_indices()
        if self._channel_idx not in affected:
            return
        self._applying = True
        try:
            self._refresh_from_doc()
        finally:
            self._applying = False

    def _on_curve_changed(self, points: list) -> None:
        if self._applying:
            return
        self._applying = True
        try:
            self._doc.replace_envelope(self._channel_idx, points)
        finally:
            self._applying = False

    def _on_clear(self) -> None:
        self._doc.replace_envelope(self._channel_idx, [])


# ---------------------------------------------------------------------------
# AutomationLane

class AutomationLane(QWidget):
    """Automation breakpoint editor bound to an ``AutomationChannel``.

    The lane allows drawing a piecewise-linear control curve over *bar_count*
    bars with a value range of [*lo*, *hi*].  Edits write back through
    ``doc.replace_automation_bps()``.

    A target-selector row at the top lets the user change which parameter the
    lane controls:

    * **Param** field  — editable string (e.g. "master_gain", "cutoff").
    * **Channel** spinbox — -1 = global/master target; 0+ = that PatternChannel.

    Changes to the selectors call ``doc.set_automation_target()``.

    Args:
        channel_idx: Index of the AutomationChannel in *doc*.
        doc:         Live ProjectDoc.
        bar_count:   Horizontal span of the lane in bars.
        lo, hi:      Value range (default 0.0 .. 1.0).
        parent:      Optional parent widget.
    """

    def __init__(
        self,
        channel_idx: int,
        doc: "ProjectDoc",
        *,
        bar_count: float = 8.0,
        lo: float = 0.0,
        hi: float = 1.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._channel_idx = channel_idx
        self._doc = doc
        self._applying = False

        ch = doc.channel(channel_idx)

        # --- target-selector row ---
        self._param_edit = QLineEdit(getattr(ch, "target_param", "master_gain"))
        self._param_edit.setPlaceholderText("param name")
        self._param_edit.setFixedWidth(100)
        self._param_edit.editingFinished.connect(self._on_target_changed)

        self._channel_spin = QSpinBox()
        self._channel_spin.setRange(-1, 255)
        self._channel_spin.setSpecialValueText("global")  # -1 displays as "global"
        tc = getattr(ch, "target_channel", None)
        self._channel_spin.setValue(tc if tc is not None else -1)
        self._channel_spin.valueChanged.connect(self._on_target_changed)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("param:"))
        target_row.addWidget(self._param_edit)
        target_row.addWidget(QLabel("ch:"))
        target_row.addWidget(self._channel_spin)
        target_row.addStretch()

        # --- curve row ---
        self._curve = BreakpointCurveWidget(bar_count=bar_count, lo=lo, hi=hi)
        self._curve.curveChanged.connect(self._on_curve_changed)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(48)
        clear_btn.clicked.connect(self._on_clear)

        header = QHBoxLayout()
        header.addStretch()
        header.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addLayout(target_row)
        layout.addLayout(header)
        layout.addWidget(self._curve)

        self._refresh_from_doc()
        doc.subscribe(self._on_doc_changed)

    # ---------------------------------------------------------------- internal

    def _refresh_from_doc(self) -> None:
        ch = self._doc.channel(self._channel_idx)
        pts = [(b.bar, b.value) for b in ch.breakpoints]
        self._curve.set_points(pts)
        # Sync selectors (guard against re-entrancy via _applying).
        self._param_edit.setText(getattr(ch, "target_param", "master_gain"))
        tc = getattr(ch, "target_channel", None)
        self._channel_spin.setValue(tc if tc is not None else -1)

    def _on_doc_changed(self, txn) -> None:
        if self._applying:
            return
        affected = txn.affected_channel_indices()
        if self._channel_idx not in affected:
            return
        self._applying = True
        try:
            self._refresh_from_doc()
        finally:
            self._applying = False

    def _on_curve_changed(self, points: list) -> None:
        if self._applying:
            return
        self._applying = True
        try:
            self._doc.replace_automation_bps(self._channel_idx, points)
        finally:
            self._applying = False

    def _on_target_changed(self) -> None:
        """Called when the param field or channel spinbox is committed."""
        if self._applying:
            return
        param = self._param_edit.text().strip() or "master_gain"
        raw = self._channel_spin.value()
        tc: int | None = None if raw < 0 else raw
        self._applying = True
        try:
            self._doc.set_automation_target(self._channel_idx, param, tc)
        finally:
            self._applying = False

    def _on_clear(self) -> None:
        self._doc.replace_automation_bps(self._channel_idx, [])
