"""forge.ui.timeline — step-pattern arrangement timeline.

Shows a bird's-eye view of the full arrangement: sections on the X axis,
one row per PatternChannel on the Y axis.  Active steps are drawn as
coloured blocks.  Clicking a section emits ``sectionClicked(section_idx)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc

_ROW_H = 18        # height per channel row
_HEADER_H = 22     # height of section-name header strip
_LABEL_W = 64      # width of left channel-label column


class TimelineWidget(QWidget):
    """Step-pattern arrangement overview.

    Each section occupies a horizontal slice proportional to its bar count.
    Within each slice, one row per PatternChannel shows which steps are on.
    Clicking a section emits ``sectionClicked(section_idx)``.

    Args:
        doc:    Live ProjectDoc.
        parent: Optional parent widget.
    """

    sectionClicked = Signal(int)   # section_idx

    def __init__(self, doc: "ProjectDoc", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doc = doc
        self._active_section: int | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        doc.subscribe(self._on_doc_changed)

    def set_doc(self, doc: "ProjectDoc") -> None:
        """Swap to a new ProjectDoc (called by MainWindow on File → Open)."""
        self._doc.unsubscribe(self._on_doc_changed)
        self._doc = doc
        doc.subscribe(self._on_doc_changed)
        self._active_section = None
        self.update()

    def set_active_section(self, idx: int | None) -> None:
        self._active_section = idx
        self.update()

    # ------------------------------------------------------------------

    def _on_doc_changed(self, txn) -> None:
        self.update()

    def _channel_rows(self):
        """Return list of (channel_idx, channel) for PatternChannels only."""
        from forge.document.channels import PatternChannel
        return [(i, ch) for i, ch in enumerate(self._doc.channels)
                if isinstance(ch, PatternChannel)]

    def sizeHint(self):
        from PySide6.QtCore import QSize
        rows = len(self._channel_rows())
        return QSize(600, _HEADER_H + max(rows, 1) * _ROW_H + 4)

    def minimumSizeHint(self):
        return self.sizeHint()

    # ------------------------------------------------------------------
    # Paint

    def paintEvent(self, _event) -> None:
        sections = self._doc.sections
        channel_rows = self._channel_rows()

        total_h = _HEADER_H + max(len(channel_rows), 1) * _ROW_H + 2
        self.setMinimumHeight(total_h)
        self.setMaximumHeight(total_h)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#f5f5f5"))

        if not sections:
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No sections — add one in the Sections panel")
            painter.end()
            return

        total_bars = sum(s["length_bars"] for s in sections)
        if total_bars == 0:
            painter.end()
            return

        draw_w = max(self.width() - _LABEL_W - 2, 1)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        # Draw channel labels on the left
        painter.setPen(QColor("#333"))
        for row_i, (_, ch) in enumerate(channel_rows):
            y = _HEADER_H + row_i * _ROW_H
            painter.drawText(
                2, y, _LABEL_W - 4, _ROW_H,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                ch.instrument_id[:8],
            )

        # Draw section columns
        x = _LABEL_W
        for sec_i, sec in enumerate(sections):
            sec_bars = sec["length_bars"]
            sec_w = int(sec_bars / total_bars * draw_w)
            if sec_w < 1:
                sec_w = 1

            is_active = sec_i == self._active_section

            # Section header
            hdr_color = QColor("#3a8ee8") if is_active else QColor("#dde4ee")
            painter.fillRect(x, 0, sec_w, _HEADER_H, hdr_color)
            painter.setPen(QColor("#ffffff") if is_active else QColor("#333"))
            painter.drawText(
                x + 3, 0, sec_w - 6, _HEADER_H,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                sec["name"],
            )

            # Left border
            painter.setPen(QPen(QColor("#ccc"), 1))
            painter.drawLine(x, 0, x, total_h - 2)

            # Channel rows
            for row_i, (ch_idx, ch) in enumerate(channel_rows):
                y = _HEADER_H + row_i * _ROW_H

                row_bg = QColor("#fafafa") if row_i % 2 == 0 else QColor("#f0f0f0")
                painter.fillRect(x, y, sec_w, _ROW_H, row_bg)

                # Resolve steps: section override if present, else channel default
                cs = sec.get("channel_steps", {})
                key = str(ch_idx)
                if key in cs:
                    from forge.document.channels import StepData
                    raw = cs[key]
                    steps = [StepData.from_step_value(s) for s in raw]
                else:
                    steps = ch.steps

                n = len(steps)
                if n > 0 and sec_w >= n:
                    # Draw individual step blocks
                    step_w = sec_w / n
                    for si, step in enumerate(steps):
                        if step.on:
                            sx = int(x + si * step_w)
                            sw = max(1, int(step_w) - 1)
                            color = QColor("#e8a03a") if step.accent else QColor("#3a8ee8")
                            painter.fillRect(sx, y + 3, sw, _ROW_H - 6, color)
                elif n > 0:
                    # Section too narrow for individual steps — show density bar
                    on_count = sum(1 for s in steps if s.on)
                    if on_count:
                        alpha = min(255, int(100 + 155 * on_count / n))
                        painter.fillRect(x, y + 3, sec_w, _ROW_H - 6, QColor(58, 142, 232, alpha))

            x += sec_w

        # Trailing border
        painter.setPen(QPen(QColor("#ccc"), 1))
        painter.drawLine(x, 0, x, total_h - 2)

        painter.end()

    # ------------------------------------------------------------------
    # Mouse

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        sections = self._doc.sections
        if not sections:
            return
        total_bars = sum(s["length_bars"] for s in sections)
        if total_bars == 0:
            return
        draw_w = max(self.width() - _LABEL_W - 2, 1)
        mx = event.position().x() - _LABEL_W
        if mx < 0:
            return
        x = 0.0
        for sec_i, sec in enumerate(sections):
            sec_w = sec["length_bars"] / total_bars * draw_w
            if mx < x + sec_w:
                self.sectionClicked.emit(sec_i)
                return
            x += sec_w
