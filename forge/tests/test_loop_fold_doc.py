"""Acceptance tests for Phase 5 — seamless loop fold via ProjectDoc.

Gate test:  ``full_loop_report(folded_buf, seam_tolerance=0.05,
            max_slope=0.005)["ok"]`` must be True for a steady kick-loop doc.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Helpers

def _make_steady_kick_doc(bpm: float = 300.0, length_bars: int = 4, seed: int = 42):
    """Build a steady kick-only ProjectDoc.

    A single kick on every beat (steps 0, 4, 8, 12) with no automation or
    build-up — the simplest possible game-state loop.  At BPM ≥ 240 the kick
    fully decays between beats and the bars are periodic, which lets the fold
    close the seam cleanly.

    Args:
        bpm:          Project tempo.  Use ≥ 240 for reliable seam closure.
        length_bars:  Section length (the logical loop duration).
        seed:         RNG seed.
    """
    from forge.document.channels import PatternChannel
    from forge.document.model import ProjectDoc

    doc = ProjectDoc(title="SteadyKick", bpm=bpm, seed=seed)
    kick = PatternChannel("kick")
    for i in [0, 4, 8, 12]:   # kick on every beat in a 16-step bar
        kick.steps[i].on = True
    doc.add_channel(kick)
    doc.add_section("loop", length_bars)
    return doc


# ---------------------------------------------------------------------------
# Flag round-trip (save/load)

class TestSeamlessLoopFlag(unittest.TestCase):
    """The seamless_loop and loop_xf_bars flags must survive serialisation."""

    def _make_doc(self):
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="FlagTest", bpm=300.0)
        return doc

    def test_default_false(self):
        doc = self._make_doc()
        self.assertFalse(doc.seamless_loop)

    def test_set_global_toggles_flag(self):
        doc = self._make_doc()
        doc.set_global("seamless_loop", True)
        self.assertTrue(doc.seamless_loop)
        doc.set_global("seamless_loop", False)
        self.assertFalse(doc.seamless_loop)

    def test_default_xf_bars(self):
        doc = self._make_doc()
        self.assertAlmostEqual(doc.loop_xf_bars, 2.0)

    def test_to_dict_includes_seamless_loop(self):
        doc = self._make_doc()
        doc.set_global("seamless_loop", True)
        d = doc.to_dict()
        self.assertIn("seamless_loop", d)
        self.assertTrue(d["seamless_loop"])

    def test_to_dict_includes_loop_xf_bars(self):
        doc = self._make_doc()
        d = doc.to_dict()
        self.assertIn("loop_xf_bars", d)
        self.assertAlmostEqual(d["loop_xf_bars"], 2.0)

    def test_from_dict_round_trip_true(self):
        from forge.document.model import ProjectDoc
        doc = self._make_doc()
        doc.set_global("seamless_loop", True)
        doc2 = ProjectDoc.from_dict(doc.to_dict())
        self.assertTrue(doc2.seamless_loop)

    def test_from_dict_round_trip_false(self):
        from forge.document.model import ProjectDoc
        doc = self._make_doc()
        doc2 = ProjectDoc.from_dict(doc.to_dict())
        self.assertFalse(doc2.seamless_loop)

    def test_from_dict_defaults_when_absent(self):
        """Loading an old doc without the key must still produce default=False."""
        from forge.document.model import ProjectDoc
        d = {"schema_version": "3.0", "title": "t", "bpm": 138.0,
             "channels": [], "sections": []}
        doc = ProjectDoc.from_dict(d)
        self.assertFalse(doc.seamless_loop)
        self.assertAlmostEqual(doc.loop_xf_bars, 2.0)

    def test_set_global_is_undoable(self):
        doc = self._make_doc()
        doc.set_global("seamless_loop", True)
        self.assertTrue(doc.seamless_loop)
        doc.undo()
        self.assertFalse(doc.seamless_loop)


# ---------------------------------------------------------------------------
# Fold helper (control._render_for_fold)

class TestFoldHelper(unittest.TestCase):
    """_render_for_fold must return a buffer of exactly total_bars length."""

    def test_output_length(self):
        from forge import control
        from forge.core.grid import Grid
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        folded = control._render_for_fold(doc, 4, xf_bars=2.0)
        grid = Grid(300.0, 44100)
        expected = grid.n_samples(4)
        self.assertEqual(len(folded), expected)

    def test_deterministic(self):
        from forge import control
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        buf1 = control._render_for_fold(doc, 4, xf_bars=2.0)
        buf2 = control._render_for_fold(doc, 4, xf_bars=2.0)
        np.testing.assert_array_equal(buf1.data, buf2.data)


# ---------------------------------------------------------------------------
# GATE TEST — full_loop_report["ok"] must be True

class TestGateSeamlessLoop(unittest.TestCase):
    """The acceptance gate: folding a steady kick doc must pass full_loop_report."""

    def test_gate_ok(self):
        """Folded steady kick loop passes both seam and flatness checks."""
        from forge import control
        from forge.analysis.loops import full_loop_report

        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        doc.set_global("seamless_loop", True)

        folded = control._render_for_fold(doc, 4, xf_bars=doc.loop_xf_bars)
        report = full_loop_report(folded, seam_tolerance=0.05, max_slope=0.005)

        self.assertTrue(
            report["ok"],
            f"full_loop_report not ok: seam disc={report['seam']['discontinuity']:.5f}, "
            f"slope={report['flatness']['slope']:.5f}",
        )

    def test_gate_seam_disc_below_tolerance(self):
        """Seam discontinuity must be below 0.05."""
        from forge import control
        from forge.analysis.loops import full_loop_report

        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        folded = control._render_for_fold(doc, 4, xf_bars=2.0)
        report = full_loop_report(folded, seam_tolerance=0.05, max_slope=0.005)

        self.assertLess(report["seam"]["discontinuity"], 0.05)

    def test_gate_flatness_slope_below_limit(self):
        """RMS slope must be below 0.005 (no energy build)."""
        from forge import control
        from forge.analysis.loops import full_loop_report

        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        folded = control._render_for_fold(doc, 4, xf_bars=2.0)
        report = full_loop_report(folded, seam_tolerance=0.05, max_slope=0.005)

        self.assertLessEqual(abs(report["flatness"]["slope"]), 0.005)

    def test_folding_improves_seam_over_raw(self):
        """Folded buffer must have a smaller seam disc than the un-folded render."""
        from forge import control
        from forge.analysis.loops import seam_report

        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)

        # Raw (un-folded) render
        raw = control._render_doc_sections(doc, fallback_length_bars=4)
        raw_disc = seam_report(raw)["discontinuity"]

        # Folded render
        folded = control._render_for_fold(doc, 4, xf_bars=2.0)
        folded_disc = seam_report(folded)["discontinuity"]

        self.assertLess(
            folded_disc, raw_disc,
            f"Fold did not improve seam: raw={raw_disc:.4f}, folded={folded_disc:.4f}",
        )


# ---------------------------------------------------------------------------
# loop_seam_report facade

class TestLoopSeamReport(unittest.TestCase):
    def test_returns_dict_with_ok_key(self):
        from forge import control
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        doc.set_global("seamless_loop", True)
        report = control.loop_seam_report(doc)
        self.assertIn("ok", report)
        self.assertIn("seam", report)
        self.assertIn("flatness", report)

    def test_steady_kick_loop_reports_ok(self):
        from forge import control
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        doc.set_global("seamless_loop", True)
        report = control.loop_seam_report(doc)
        self.assertTrue(report["ok"])

    def test_seam_report_passthrough(self):
        from forge import control
        from forge.core.buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer.from_mono(np.zeros(1000))
        r = control.seam_report(buf)
        self.assertIn("discontinuity", r)
        self.assertTrue(r["ok"])


# ---------------------------------------------------------------------------
# Export WAV with loop_fold flag

class TestExportLoopFold(unittest.TestCase):
    """export_wav_from_doc with loop_fold=True or doc.seamless_loop=True."""

    def _make_doc(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc(title="ExportTest", bpm=600.0, seed=0)
        kick = PatternChannel("kick")
        kick.steps[0].on = True
        doc.add_channel(kick)
        doc.add_section("section", 1)
        return doc

    def test_explicit_loop_fold_flag_exports(self):
        from forge import control
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            buf = control.export_wav_from_doc(doc, path, loop_fold=True)
            self.assertTrue(path.exists())
            self.assertGreater(buf.data.shape[0], 0)

    def test_seamless_loop_doc_exports(self):
        from forge import control
        doc = self._make_doc()
        doc.set_global("seamless_loop", True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out_seamless.wav"
            buf = control.export_wav_from_doc(doc, path)
            self.assertTrue(path.exists())
            self.assertGreater(buf.data.shape[0], 0)

    def test_no_fold_when_flag_off(self):
        """Without the flag, export still works normally."""
        from forge import control
        doc = self._make_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out_plain.wav"
            buf = control.export_wav_from_doc(doc, path)
            self.assertTrue(path.exists())
            self.assertGreater(buf.data.shape[0], 0)


# ---------------------------------------------------------------------------
# render_doc_for_playback with seamless_loop

class TestPlaybackFold(unittest.TestCase):
    def test_seamless_playback_renders(self):
        from forge import control
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        doc.set_global("seamless_loop", True)
        buf = control.render_doc_for_playback(doc)
        from forge.core.grid import Grid
        grid = Grid(300.0, 44100)
        expected = grid.n_samples(4)
        # The folded buffer is exactly total_bars long after mastering.
        self.assertEqual(len(buf), expected)

    def test_non_seamless_playback_renders(self):
        from forge import control
        doc = _make_steady_kick_doc(bpm=300.0, length_bars=4)
        buf = control.render_doc_for_playback(doc)
        self.assertGreater(buf.data.shape[0], 0)


if __name__ == "__main__":
    unittest.main()
