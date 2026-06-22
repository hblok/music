"""soundmatch.app — PySide6 entry point for Sound-Match Studio.

Usage::

    python -m soundmatch.app
    python -m soundmatch.app --sr 44100 FILE
"""

from __future__ import annotations

import argparse
import logging
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sound-Match Studio")
    parser.add_argument("--sr", type=int, default=44100, help="Sample rate")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("file", nargs="?", default=None, help="Reference audio file to load")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger(__name__)
    log.info("Sound-Match Studio starting (sr=%d)", args.sr)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor

    app = QApplication.instance() or QApplication(sys.argv)

    # Force a light Fusion theme (matching the Forge app)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#ececec"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#cc0000"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#3a8ee8"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    from forge.playback.service import PlaybackService
    from soundmatch.ui.window import MainWindow

    service = PlaybackService(sr=args.sr, bpm=120.0)
    window = MainWindow(service)
    window.show()

    # Auto-load file if provided
    if args.file:
        from pathlib import Path
        window.reference_panel.load_audio(Path(args.file), sr=args.sr)

    exit_code = app.exec()
    service.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
