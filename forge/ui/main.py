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

    app = QApplication.instance() or QApplication(sys.argv)

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
