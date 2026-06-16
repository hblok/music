"""forge.document.autosave — crash-safe autosave for ProjectDoc.

``AutoSave`` subscribes to a ``ProjectDoc`` and writes a JSON snapshot to a
fixed path after every *N* transactions or on explicit ``flush()`` calls.
Writes are atomic (temp-file rename) so a crash during write never corrupts
the autosave file.

On application launch, call ``recover(path)`` to check whether an autosave
exists for a given project path.

No Qt, no DSP — usable headlessly.

Usage::

    saver = AutoSave(doc, path=Path("~/.forge/autosave.json"), interval=10)
    # … user edits …
    saver.flush()   # explicit flush (e.g. on quit)
    saver.stop()    # unsubscribe

Recovery::

    recovered = AutoSave.recover(Path("~/.forge/autosave.json"))
    if recovered is not None:
        doc = recovered
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from forge.document.model import ProjectDoc
    from forge.document.transaction import Transaction


class AutoSave:
    """Transaction-counting autosave subscriber for ``ProjectDoc``.

    Args:
        doc:       The ProjectDoc to watch.
        path:      File path for the autosave JSON.
        interval:  Number of transactions between automatic saves (default 10).
    """

    def __init__(
        self,
        doc: "ProjectDoc",
        path: Path,
        interval: int = 10,
    ) -> None:
        self._doc = doc
        self._path = Path(path)
        self._interval = max(1, int(interval))
        self._count = 0
        # Store the bound method so unsubscribe can use identity comparison.
        self._callback = self._on_change
        doc.subscribe(self._callback)

    # ---------------------------------------------------------------- public

    def flush(self) -> None:
        """Write the current doc state to disk immediately (atomic)."""
        self._write(self._doc.to_dict())

    def stop(self) -> None:
        """Unsubscribe from the doc (no more autosaves)."""
        self._doc.unsubscribe(self._callback)

    @staticmethod
    def recover(path: Path) -> "ProjectDoc | None":
        """Return a ``ProjectDoc`` loaded from the autosave at *path*, or None.

        Returns None if the file does not exist, is empty, or is corrupt.
        """
        path = Path(path)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                d = json.load(fh)
            from forge.document.model import ProjectDoc
            return ProjectDoc.from_dict(d)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def clear(path: Path) -> None:
        """Delete the autosave file at *path* if it exists."""
        path = Path(path)
        if path.exists():
            path.unlink()

    # ---------------------------------------------------------------- private

    def _on_change(self, txn: "Transaction") -> None:
        self._count += 1
        if self._count >= self._interval:
            self._count = 0
            self.flush()

    def _write(self, d: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp.json")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(d, fh, separators=(",", ":"))  # compact for speed
        tmp.replace(self._path)
