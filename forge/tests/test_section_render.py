"""Acceptance tests for Phase 1 — Section-aware playback & export.

Tests that per-section channel_steps overrides are honoured by both
render_doc_for_playback and export_wav_from_doc.
"""

import tempfile
import unittest
from pathlib import Path


def _make_two_section_doc(bpm: float = 600.0, sr: int = 44100):
    """Build a doc with two equal-length sections and one kick channel.

    Section 0: kick is DISABLED (all steps off).
    Section 1: kick hits on every step.

    At bpm=600 each bar is 4*60/600 = 0.4 s.  With 2 bars per section the
    total render is 4 bars = 1.6 s.
    """
    from forge.document.channels import PatternChannel, StepData
    from forge.document.model import ProjectDoc

    doc = ProjectDoc(title="Section Test", bpm=bpm, sr=sr, seed=0)

    # Channel 0: kick — default steps all OFF
    kick = PatternChannel("kick", n_steps=16)
    # Default steps are all off (StepData() has on=False)
    doc.add_channel(kick)

    # Two sections, each 2 bars
    doc.add_section("silent", 2)
    doc.add_section("loud", 2)

    # Section 0: override kick so all steps are explicitly OFF (already default,
    # but make the override explicit so the test exercises the override path).
    silent_steps = [StepData(on=False) for _ in range(16)]
    doc.set_section_steps(0, 0, silent_steps)

    # Section 1: override kick so every step is ON.
    loud_steps = [StepData(on=True) for _ in range(16)]
    doc.set_section_steps(1, 0, loud_steps)

    return doc


class TestSectionRenderRMS(unittest.TestCase):
    """Per-section steps are honoured: silent section has lower RMS than loud."""

    def test_section_rms_differ(self):
        import numpy as np
        from forge import control

        doc = _make_two_section_doc()
        buf = control.render_doc_for_playback(doc)

        # Split at the midpoint (each section is 2 bars = half of 4 bars total).
        n = len(buf.data)
        mid = n // 2
        rms_first = float(np.sqrt(np.mean(buf.data[:mid] ** 2)))
        rms_second = float(np.sqrt(np.mean(buf.data[mid:] ** 2)))

        # The second half (loud section) should be substantially louder.
        self.assertGreater(
            rms_second, rms_first * 2.0,
            f"Expected second half RMS ({rms_second:.6f}) >> first half RMS ({rms_first:.6f})",
        )

    def test_export_total_length(self):
        """Export length in frames should equal sum(section length_bars) in samples."""
        import wave
        from forge import control
        from forge.core.grid import Grid

        doc = _make_two_section_doc()
        grid = Grid(doc.bpm, doc.sr)
        expected_bars = sum(s["length_bars"] for s in doc.sections)  # 4 bars
        expected_samples = grid.n_samples(expected_bars)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            control.export_wav_from_doc(doc, path)
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()

        # Allow ±1 sample rounding tolerance (mastering does not change length).
        self.assertAlmostEqual(frames, expected_samples, delta=2,
            msg=f"Expected ~{expected_samples} frames, got {frames}")

    def test_export_rms_differ(self):
        """export_wav_from_doc also honours section step overrides."""
        import numpy as np
        from forge import control

        doc = _make_two_section_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.wav"
            buf = control.export_wav_from_doc(doc, path)

        n = len(buf.data)
        mid = n // 2
        rms_first = float(np.sqrt(np.mean(buf.data[:mid] ** 2)))
        rms_second = float(np.sqrt(np.mean(buf.data[mid:] ** 2)))

        self.assertGreater(
            rms_second, rms_first * 2.0,
            f"Expected second half RMS ({rms_second:.6f}) >> first half RMS ({rms_first:.6f})",
        )

    def test_section_gain_applied(self):
        """A section with gain=0.5 renders at half amplitude."""
        import numpy as np
        from forge.document.channels import PatternChannel, StepData
        from forge.document.model import ProjectDoc
        from forge import control

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        doc.add_channel(kick)
        doc.add_section("A", 2)
        doc.add_section("B", 2)

        # Both sections: kick on every step.
        loud = [StepData(on=True) for _ in range(16)]
        doc.set_section_steps(0, 0, loud[:])
        doc.set_section_steps(1, 0, loud[:])

        # Render at full gain (both sections gain=1.0, the default).
        buf_full = control.render_doc_for_playback(doc)

        # Now halve section 1's gain in the underlying section dict.
        # (The facade doesn't expose a set_section_gain yet, so we mutate
        # the raw list entry as the scheduler would.)
        doc._sections[1]["gain"] = 0.5

        buf_half = control.render_doc_for_playback(doc)

        n = len(buf_full.data)
        mid = n // 2
        rms_full_second = float(np.sqrt(np.mean(buf_full.data[mid:] ** 2)))
        rms_half_second = float(np.sqrt(np.mean(buf_half.data[mid:] ** 2)))

        # After mastering, the ratio won't be exactly 0.5 but the quieter
        # section should be clearly quieter.
        self.assertGreater(rms_full_second, rms_half_second,
            "Section with gain=0.5 should be quieter than gain=1.0")


if __name__ == "__main__":
    unittest.main()
