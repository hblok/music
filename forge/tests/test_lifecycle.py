"""Phase 8 tests: versioned spec, save/load ProjectDoc, WAV export, legacy import."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ---------------------------------------------------------------------------
# migrate_project_dict

class TestMigrateProjectDict(unittest.TestCase):
    def _migrate(self, d):
        from forge.spec.serialize import migrate_project_dict
        return migrate_project_dict(d)

    def test_plan3_dict_passthrough(self):
        d = {"schema_version": "3.0", "title": "t", "bpm": 138.0, "channels": [], "sections": []}
        result = self._migrate(d)
        self.assertEqual(result["schema_version"], "3.0")
        self.assertIn("channels", result)

    def test_plan2_gets_schema_version(self):
        plan2 = {
            "title": "My Track",
            "bpm": 138.0,
            "sr": 44100,
            "seed": 0,
            "normalize": True,
            "target": 0.85,
            "fade_out_s": 2.0,
            "sections": [
                {
                    "name": "intro",
                    "start_bar": 0,
                    "length_bars": 8,
                    "gain": 1.0,
                    "schedules": [
                        {
                            "bpm": 138.0,
                            "length_bars": 8,
                            "tracks": [
                                {"instrument": "kick", "steps": [1, 0, 0, 0, 1, 0, 0, 0,
                                                                   1, 0, 0, 0, 1, 0, 0, 0]},
                                {"instrument": "hat",  "steps": [0, 1, 0, 1, 0, 1, 0, 1,
                                                                   0, 1, 0, 1, 0, 1, 0, 1]},
                            ]
                        }
                    ]
                }
            ]
        }
        result = self._migrate(plan2)
        self.assertEqual(result["schema_version"], "3.0")
        self.assertIn("channels", result)
        self.assertEqual(len(result["channels"]), 2)  # kick + hat

    def test_plan2_creates_sections_order(self):
        plan2 = {
            "bpm": 138.0,
            "sections": [
                {"name": "intro", "length_bars": 8, "schedules": []},
                {"name": "drop",  "length_bars": 16, "schedules": []},
            ]
        }
        result = self._migrate(plan2)
        self.assertEqual(len(result["sections"]), 2)
        self.assertEqual(result["sections"][0]["name"], "intro")
        self.assertEqual(result["sections"][1]["length_bars"], 16)

    def test_plan2_deduplicates_instruments(self):
        plan2 = {
            "bpm": 138.0,
            "sections": [
                {
                    "name": "A",
                    "length_bars": 8,
                    "schedules": [{"bpm": 138.0, "length_bars": 8,
                                   "tracks": [{"instrument": "kick", "steps": [1]*16}]}]
                },
                {
                    "name": "B",
                    "length_bars": 8,
                    "schedules": [{"bpm": 138.0, "length_bars": 8,
                                   "tracks": [{"instrument": "kick", "steps": [0]*16},
                                              {"instrument": "hat",  "steps": [1]*16}]}]
                },
            ]
        }
        result = self._migrate(plan2)
        ids = [ch["instrument_id"] for ch in result["channels"]]
        self.assertEqual(ids.count("kick"), 1)  # deduplicated
        self.assertIn("hat", ids)

    def test_idempotent(self):
        plan2 = {"bpm": 138.0, "sections": []}
        r1 = self._migrate(plan2)
        r2 = self._migrate(r1)
        self.assertEqual(r1, r2)

    def test_step_values_converted(self):
        plan2 = {
            "bpm": 138.0,
            "sections": [{
                "name": "S",
                "length_bars": 4,
                "schedules": [{"bpm": 138.0, "length_bars": 4,
                               "tracks": [{"instrument": "kick",
                                           "steps": [1, 0, {"on": True, "accent": True}, 0]}]}]
            }]
        }
        result = self._migrate(plan2)
        steps = result["channels"][0]["steps"]
        self.assertTrue(steps[0]["on"])
        self.assertFalse(steps[1]["on"])
        self.assertTrue(steps[2].get("accent"))


# ---------------------------------------------------------------------------
# save_project_doc / load_project_doc (round-trip)

class TestSaveLoadProjectDoc(unittest.TestCase):
    def _make_doc(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="Round Trip Test", bpm=120.0, seed=42)
        ch = PatternChannel("kick", n_steps=8)
        ch.steps[0].on = True
        ch.steps[4].on = True
        doc.add_channel(ch)
        doc.add_section("intro", 8)
        return doc

    def test_round_trip(self):
        from forge.spec.serialize import load_project_doc, save_project_doc
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_project_doc(doc, path)
            doc2 = load_project_doc(path)
        self.assertEqual(doc2.title, "Round Trip Test")
        self.assertAlmostEqual(doc2.bpm, 120.0)
        self.assertEqual(doc2.seed, 42)
        self.assertEqual(len(doc2.channels), 1)
        self.assertEqual(doc2.channels[0].instrument_id, "kick")
        self.assertTrue(doc2.channels[0].steps[0].on)
        self.assertTrue(doc2.channels[0].steps[4].on)

    def test_round_trip_sections(self):
        from forge.spec.serialize import load_project_doc, save_project_doc
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_project_doc(doc, path)
            doc2 = load_project_doc(path)
        self.assertEqual(len(doc2.sections), 1)
        self.assertEqual(doc2.sections[0]["name"], "intro")

    def test_atomic_write(self):
        from forge.spec.serialize import save_project_doc
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_project_doc(doc, path)
            # No .tmp file should remain
            tmp_file = path.with_suffix(".tmp.json")
            self.assertFalse(tmp_file.exists())
            self.assertTrue(path.exists())

    def test_file_is_valid_json(self):
        from forge.spec.serialize import save_project_doc
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_project_doc(doc, path)
            with path.open() as f:
                d = json.load(f)
        self.assertEqual(d["schema_version"], "3.0")

    def test_load_plan2_via_doc_loader(self):
        from forge.spec.serialize import load_project_doc
        plan2 = {
            "title": "legacy",
            "bpm": 140.0,
            "sections": [
                {"name": "intro", "length_bars": 4, "schedules": [
                    {"bpm": 140.0, "length_bars": 4,
                     "tracks": [{"instrument": "kick", "steps": [1]*16}]}
                ]}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan2.json"
            with path.open("w") as f:
                json.dump(plan2, f)
            doc = load_project_doc(path)
        self.assertAlmostEqual(doc.bpm, 140.0)
        self.assertEqual(len(doc.channels), 1)
        self.assertEqual(doc.channels[0].instrument_id, "kick")

    def test_schema_version_preserved(self):
        from forge.spec.serialize import load_project_doc, save_project_doc
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_project_doc(doc, path)
            doc2 = load_project_doc(path)
            d2 = doc2.to_dict()
        self.assertEqual(d2["schema_version"], "3.0")


# ---------------------------------------------------------------------------
# WAV export

class TestExportWav(unittest.TestCase):
    def _make_doc(self, bpm=600.0):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="Export Test", bpm=bpm, seed=0)
        ch = PatternChannel("kick")
        ch.steps[0].on = True
        doc.add_channel(ch)
        doc.add_section("section", 1)
        return doc

    def test_export_creates_wav(self):
        from forge import control
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            control.export_wav_from_doc(doc, path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_export_wav_is_readable(self):
        import wave
        from forge import control
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            control.export_wav_from_doc(doc, path)
            with wave.open(str(path), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 2)
                self.assertEqual(wf.getframerate(), 44100)
                self.assertGreater(wf.getnframes(), 0)

    def test_export_deterministic(self):
        import numpy as np
        from forge import control
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "out1.wav"
            p2 = Path(tmp) / "out2.wav"
            buf1 = control.export_wav_from_doc(doc, p1)
            buf2 = control.export_wav_from_doc(doc, p2)
        np.testing.assert_array_equal(buf1.data, buf2.data)

    def test_export_uses_section_length(self):
        import wave
        from forge import control
        from forge.document.model import ProjectDoc
        from forge.document.channels import PatternChannel
        doc = ProjectDoc(bpm=600.0)
        doc.add_channel(PatternChannel("kick"))
        doc.add_section("A", 2)
        doc.add_section("B", 4)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            control.export_wav_from_doc(doc, path)
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
        # 6 bars at bpm=600 → 6 * 4 * 60/600 = 2.4 s → ~105840 frames
        self.assertGreater(frames, 50000)

    def test_export_loop_fold(self):
        from forge import control
        doc = self._make_doc(bpm=600.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out_loop.wav"
            buf = control.export_wav_from_doc(doc, path, loop_fold=True)
            self.assertTrue(path.exists())
            self.assertGreater(buf.data.shape[0], 0)


# ---------------------------------------------------------------------------
# Import forge project spec → ProjectDoc

class TestImportProjectSpec(unittest.TestCase):
    def test_sleeper_awakens_importable(self):
        import sys
        from pathlib import Path as _Path
        sys.path.insert(0, str(_Path(__file__).parent.parent.parent.parent))
        from examples.sleeper_awakens_mini import build_project
        from forge.spec.serialize import migrate_project_dict
        spec = build_project()
        d = spec.to_dict()
        migrated = migrate_project_dict(d)
        self.assertEqual(migrated["schema_version"], "3.0")
        self.assertGreater(len(migrated["channels"]), 0)

    def test_sleeper_awakens_doc_loadable(self):
        import sys
        import tempfile
        from pathlib import Path as _Path
        sys.path.insert(0, str(_Path(__file__).parent.parent.parent.parent))
        from examples.sleeper_awakens_mini import build_project
        from forge.spec.serialize import load_project_doc, save_project_doc
        spec = build_project()
        plan2_dict = spec.to_dict()
        with tempfile.TemporaryDirectory() as tmp:
            p = _Path(tmp) / "sleeper.json"
            import json
            with p.open("w") as f:
                json.dump(plan2_dict, f)
            doc = load_project_doc(p)
        self.assertAlmostEqual(doc.bpm, 145.0)
        self.assertGreater(len(doc.channels), 0)
        # All channels should be PatternChannels (no texture/automation in sleeper)
        from forge.document.channels import PatternChannel
        for ch in doc.channels:
            self.assertIsInstance(ch, PatternChannel)


# ---------------------------------------------------------------------------
# Window lifecycle (offscreen Qt)

class TestMainWindowLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_open_doc_menu_exists(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(bpm=138.0)
        w = MainWindow(svc)
        # Check that the File menu has the tracker entries
        menu_bar = w.menuBar()
        file_action = menu_bar.actions()[0]
        file_menu = file_action.menu()
        self.assertIsNotNone(file_menu)
        titles = [a.text() for a in file_menu.actions() if not a.isSeparator()]
        self.assertTrue(any("Tracker" in t for t in titles), f"Got: {titles}")

    def test_export_wav_no_doc_shows_status(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(bpm=138.0)
        w = MainWindow(svc)
        # No doc loaded — export should set status message, not crash
        w._on_export_wav()
        status = w._status_label.text()
        self.assertIn("No tracker", status)

    def test_save_doc_no_doc_shows_status(self):
        from forge.playback.service import PlaybackService
        from forge.ui.window import MainWindow
        svc = PlaybackService(bpm=138.0)
        w = MainWindow(svc)
        w._on_save_doc()
        status = w._status_label.text()
        self.assertIn("No tracker", status)


if __name__ == "__main__":
    unittest.main()
