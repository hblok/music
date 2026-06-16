"""Phase 10 tests: worked example, project browser, window polish."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ---------------------------------------------------------------------------
# Worked example: sleeper_awakens_mini

class TestSleeperAwakensExample(unittest.TestCase):
    def test_project_spec_builds(self):
        # Import without running main()
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from examples.sleeper_awakens_mini import build_project
        project = build_project()
        self.assertEqual(project.title, "Sleeper Awakens Mini")
        self.assertAlmostEqual(project.bpm, 145.0)
        # should have 4 sections: intro, drop, outro, wind
        self.assertEqual(len(project.sections), 4)

    def test_project_renders(self):
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from examples.sleeper_awakens_mini import build_project
        from forge import control
        project = build_project()
        buf = control.render_track(project.to_dict())
        self.assertGreater(buf.peak(), 0)
        # 16 bars at 145 BPM: 16 * (60/145 * 4) ≈ 26.5s
        self.assertGreater(buf.len_seconds(), 20.0)

    def test_project_save_load_roundtrip(self):
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from examples.sleeper_awakens_mini import build_project
        from forge.spec.serialize import load_project, save_project
        project = build_project()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sleeper.json"
            save_project(project, path)
            loaded = load_project(path)
            self.assertEqual(loaded.title, project.title)


# ---------------------------------------------------------------------------
# InstrumentBrowser

class TestInstrumentBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_browser_creates(self):
        from forge.ui.project_view import InstrumentBrowser
        browser = InstrumentBrowser()
        browser.show()
        self.assertGreater(browser._list.count(), 0)
        browser.close()

    def test_browser_has_families(self):
        from forge.ui.project_view import InstrumentBrowser
        browser = InstrumentBrowser()
        all_text = [
            browser._list.item(i).text()
            for i in range(browser._list.count())
        ]
        combined = " ".join(all_text).lower()
        for family in ("percussion", "bass", "fx"):
            self.assertIn(family, combined)
        browser.close()

    def test_instrument_selected_signal(self):
        from forge.ui.project_view import InstrumentBrowser
        received = []
        browser = InstrumentBrowser()
        browser.instrumentSelected.connect(received.append)
        # find a real instrument item
        for i in range(browser._list.count()):
            item = browser._list.item(i)
            iid = item.data(1)  # UserRole = 1
            if iid:
                browser._list.itemClicked.emit(item)
                break
        browser.close()


# ---------------------------------------------------------------------------
# ProjectTree

class TestProjectTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def _project_dict(self):
        return {
            "title": "Test Project",
            "bpm": 138.0,
            "sections": [
                {
                    "name": "intro",
                    "start_bar": 0,
                    "length_bars": 4,
                    "schedules": [
                        {
                            "bpm": 138.0,
                            "length_bars": 4,
                            "tracks": [
                                {"instrument": "kick", "steps": [1, 0] * 8},
                                {"instrument": "hat", "steps": [0, 1] * 8},
                            ],
                        }
                    ],
                }
            ],
        }

    def test_tree_loads_project(self):
        from forge.ui.project_view import ProjectTree
        tree = ProjectTree()
        tree.load(self._project_dict())
        root = tree._tree.topLevelItem(0)
        self.assertIsNotNone(root)
        self.assertEqual(root.text(0), "Test Project")

    def test_tree_has_sections(self):
        from forge.ui.project_view import ProjectTree
        tree = ProjectTree()
        tree.load(self._project_dict())
        root = tree._tree.topLevelItem(0)
        self.assertEqual(root.childCount(), 1)
        sec_item = root.child(0)
        self.assertEqual(sec_item.text(0), "intro")

    def test_tree_clears(self):
        from forge.ui.project_view import ProjectTree
        tree = ProjectTree()
        tree.load(self._project_dict())
        tree.clear()
        self.assertEqual(tree._tree.topLevelItemCount(), 0)


# ---------------------------------------------------------------------------
# Window save/load wiring

class TestWindowSaveLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_window_has_open_save_actions(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120.0)
        win = MainWindow(svc)
        # find the File menu
        file_menu = None
        for action in win.menuBar().actions():
            if "file" in action.text().lower():
                file_menu = action.menu()
                break
        self.assertIsNotNone(file_menu)
        action_texts = [a.text() for a in file_menu.actions()]
        combined = " ".join(action_texts).lower()
        self.assertIn("open", combined)
        self.assertIn("save", combined)
        win.close()
        svc.close()

    def test_on_save_without_project_shows_status(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(sr=44100, bpm=120.0)
        win = MainWindow(svc)
        win._on_save()  # no project loaded
        status = win._status_label.text()
        self.assertIn("No project", status)
        win.close()
        svc.close()


# ---------------------------------------------------------------------------
# Regression: all prior phases still pass after Phase 10 additions

class TestRegressionSuite(unittest.TestCase):
    def test_control_list_instruments(self):
        from forge import control
        result = control.list_instruments()
        self.assertGreater(len(result), 5)

    def test_control_render_instrument(self):
        from forge import control
        from forge.core.buffer import AudioBuffer
        buf = control.render_instrument("kick", {}, seed=0)
        self.assertIsInstance(buf, AudioBuffer)
        self.assertGreater(buf.peak(), 0)

    def test_control_render_pattern(self):
        from forge import control
        from forge.core.buffer import AudioBuffer
        spec = {
            "bpm": 138.0,
            "length_bars": 1,
            "tracks": [{"instrument": "kick",
                         "steps": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]}],
        }
        buf = control.render_pattern(spec, seed=0)
        self.assertIsInstance(buf, AudioBuffer)

    def test_control_render_track(self):
        from forge import control
        from forge.core.buffer import AudioBuffer
        project = {
            "title": "Regression", "bpm": 138.0, "seed": 0,
            "sections": [{"name": "s", "start_bar": 0, "length_bars": 2,
                "schedules": [{"bpm": 138.0, "length_bars": 2,
                    "tracks": [{"instrument": "kick",
                                 "steps": [1, 0, 0, 0] * 4}]}]}],
        }
        buf = control.render_track(project)
        self.assertIsInstance(buf, AudioBuffer)

    def test_control_save_load(self):
        from forge import control
        with tempfile.TemporaryDirectory() as tmpdir:
            p = {"title": "T", "bpm": 120.0, "sections": []}
            path = Path(tmpdir) / "t.json"
            control.save_project(p, path)
            loaded = control.load_project(path)
            self.assertEqual(loaded["title"], "T")


if __name__ == "__main__":
    unittest.main()
