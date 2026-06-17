"""forge.ui.main — application entry point.

Usage::

    python -m forge.ui.main
    # or
    python -m forge.ui.main --bpm 138 --sr 44100
"""

from __future__ import annotations

import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="Forge modular music workstation")
    parser.add_argument("--bpm", type=float, default=120.0)
    parser.add_argument("--sr", type=int, default=44100)
    args = parser.parse_args(argv)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor

    app = QApplication.instance() or QApplication(sys.argv)

    # Force a light Fusion theme so custom-drawn widgets and Qt widgets
    # both render with a light background and dark text.
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
    from forge.ui.window import MainWindow

    service = PlaybackService(sr=args.sr, bpm=args.bpm)
    window = MainWindow(service)
    window.show()

    exit_code = app.exec()
    service.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
