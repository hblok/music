"""forge.ui.project_view — instrument browser and project tree widget.

Two panels:
  InstrumentBrowser — scrollable list of all registry instruments, grouped
                      by family; double-click opens an InstrumentPanel.
  ProjectTree       — a QTreeWidget showing sections and their tracks;
                      driven by a ProjectSpec dict.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class InstrumentBrowser(QGroupBox):
    """Scrollable list of registry instruments grouped by family.

    Emits ``instrumentSelected(str)`` when an item is single-clicked.
    Emits ``instrumentActivated(str)`` on double-click.
    """

    instrumentSelected = Signal(str)
    instrumentActivated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Instruments", parent)
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self._list.itemClicked.connect(
            lambda item: self.instrumentSelected.emit(item.data(Qt.ItemDataRole.UserRole))
        )
        self._list.itemDoubleClicked.connect(
            lambda item: self.instrumentActivated.emit(item.data(Qt.ItemDataRole.UserRole))
        )

        self._populate()

    def _populate(self) -> None:
        try:
            from forge import control
            instruments = control.list_instruments()
        except Exception:  # noqa: BLE001
            return

        by_family: dict[str, list[dict]] = {}
        for entry in instruments:
            by_family.setdefault(entry["family"], []).append(entry)

        for family in sorted(by_family):
            header = QListWidgetItem(f"── {family.upper()} ──")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(header)
            for entry in by_family[family]:
                item = QListWidgetItem(f"  {entry['id']}")
                item.setData(Qt.ItemDataRole.UserRole, entry["id"])
                self._list.addItem(item)


class ProjectTree(QGroupBox):
    """QTreeWidget showing the section/track hierarchy of a ProjectSpec dict."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Project", parent)
        layout = QVBoxLayout(self)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name", "Bars", "Instruments"])
        self._tree.setColumnWidth(0, 120)
        layout.addWidget(self._tree)

    def load(self, project: dict) -> None:
        """Populate the tree from a ProjectSpec dict."""
        self._tree.clear()
        title = project.get("title", "Untitled")
        root = QTreeWidgetItem([title, "", ""])
        self._tree.addTopLevelItem(root)

        for sec in project.get("sections", []):
            sec_item = QTreeWidgetItem([
                sec.get("name", ""),
                str(sec.get("length_bars", "")),
                "",
            ])
            root.addChild(sec_item)

            for sched in sec.get("schedules", []):
                instruments = ", ".join(
                    t.get("instrument", "?")
                    for t in sched.get("tracks", [])
                )
                sched_item = QTreeWidgetItem([
                    f"pattern",
                    str(sched.get("length_bars", "")),
                    instruments,
                ])
                sec_item.addChild(sched_item)

        self._tree.expandAll()

    def clear(self) -> None:
        self._tree.clear()
