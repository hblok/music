"""Phase 2 acceptance tests: TextureChannel + AutomationChannel in the mix.

Verifies that:
1. A doc with a wind texture + kick pattern produces higher RMS than kick alone.
2. A master_gain automation lane with a 0→1 fade-in produces measurable fade-in
   (later bars have higher RMS than the silent opener).
3. Muting the texture channel yields lower RMS than an un-muted render.
"""

import unittest
import numpy as np


# ---------------------------------------------------------------------------
# Helpers

def _make_doc(bpm=600.0, sr=44100, seed=0):
    """Return a fresh, empty ProjectDoc at a high BPM for fast renders."""
    from forge.document.model import ProjectDoc
    return ProjectDoc(title="tex-mix-test", bpm=bpm, sr=sr, seed=seed)


def _rms(data):
    return float(np.sqrt(np.mean(data ** 2)))


# ---------------------------------------------------------------------------

class TestTextureMixedIn(unittest.TestCase):
    """Texture energy is actually summed into the master buffer."""

    def test_texture_adds_energy_over_kick_only(self):
        """wind texture + kick has higher pre-master RMS than kick alone.

        We compare the un-mastered (_render_doc_sections) buffers so that the
        normalising mastering stage cannot equalise the two renders' levels.
        """
        from forge import control
        from forge.document.channels import PatternChannel, StepData, TextureChannel

        # ---- kick-only doc ----
        doc_kick = _make_doc()
        kick = PatternChannel("kick", n_steps=16)
        kick.steps = [StepData(on=True) for _ in range(16)]
        doc_kick.add_channel(kick)
        doc_kick.add_section("main", 4)
        from forge.document.channels import StepData as SD
        doc_kick.set_section_steps(0, 0, [SD(on=True) for _ in range(16)])

        buf_kick = control._render_doc_sections(doc_kick)

        # ---- kick + wind doc (same seed, same kick) ----
        doc_both = _make_doc()
        kick2 = PatternChannel("kick", n_steps=16)
        kick2.steps = [StepData(on=True) for _ in range(16)]
        doc_both.add_channel(kick2)                   # channel 0 → kick
        doc_both.add_channel(TextureChannel("wind"))  # channel 1 → wind
        doc_both.add_section("main", 4)
        doc_both.set_section_steps(0, 0, [SD(on=True) for _ in range(16)])

        buf_both = control._render_doc_sections(doc_both)

        rms_kick = _rms(buf_kick.data)
        rms_both = _rms(buf_both.data)

        self.assertGreater(
            rms_both, rms_kick,
            f"Expected texture+kick pre-master RMS ({rms_both:.6f}) "
            f"> kick-only RMS ({rms_kick:.6f})",
        )

    def test_texture_only_doc_not_silent(self):
        """A doc with only a TextureChannel (no patterns) must still render audio."""
        from forge import control
        from forge.document.channels import TextureChannel

        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))
        doc.add_section("main", 4)

        buf = control.render_doc_for_playback(doc)
        self.assertGreater(
            _rms(buf.data), 0.0,
            "Texture-only doc should have non-zero RMS",
        )


class TestTextureMute(unittest.TestCase):
    """Muting a TextureChannel removes its energy from the mix."""

    def test_muted_texture_yields_lower_rms(self):
        from forge import control
        from forge.document.channels import TextureChannel

        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))  # channel 0
        doc.add_section("main", 4)

        buf_unmuted = control.render_doc_for_playback(doc, muted_channels=set())
        buf_muted = control.render_doc_for_playback(doc, muted_channels={0})

        rms_unmuted = _rms(buf_unmuted.data)
        rms_muted = _rms(buf_muted.data)

        self.assertGreater(
            rms_unmuted, rms_muted,
            f"Un-muted texture RMS ({rms_unmuted:.6f}) should exceed muted RMS ({rms_muted:.6f})",
        )


class TestMasterGainAutomation(unittest.TestCase):
    """master_gain AutomationChannel produces a measurable fade-in."""

    def test_fade_in_later_bar_louder_than_first(self):
        """A 0→1 ramp over 2 bars means the tail (post-ramp) is louder than bar-0."""
        from forge import control
        from forge.document.channels import AutomationChannel, Breakpoint, TextureChannel

        # Use several bars so the split is clear; bpm=600 keeps render fast.
        # Section length: 6 bars.  Automation: 0.0 at bar 0, 1.0 at bar 2,
        # 1.0 at bar 6 (N).
        n_bars = 6
        doc = _make_doc(bpm=600.0)
        doc.add_channel(TextureChannel("wind"))    # channel 0 — provides energy
        doc.add_channel(AutomationChannel(         # channel 1 — master gain ramp
            "master_gain",
            breakpoints=[
                Breakpoint(0, 0.0),
                Breakpoint(2, 1.0),
                Breakpoint(n_bars, 1.0),
            ],
        ))
        doc.add_section("main", n_bars)

        buf = control._render_doc_sections(doc)  # un-mastered so gain curve is visible

        # Split buffer: first 0.5 bar vs last 2 bars.
        from forge.core.grid import Grid
        grid = Grid(doc.bpm, doc.sr)
        half_bar_samples = grid.n_samples(0.5)
        last_two_start = grid.n_samples(n_bars - 2)

        rms_early = _rms(buf.data[:half_bar_samples])
        rms_late = _rms(buf.data[last_two_start:])

        self.assertGreater(
            rms_late, rms_early,
            f"Late RMS ({rms_late:.6f}) should exceed early RMS ({rms_early:.6f}) "
            f"due to fade-in automation",
        )

    def test_no_automation_lane_unchanged(self):
        """A doc with no AutomationChannel is unaffected (no crash, same behaviour)."""
        from forge import control
        from forge.document.channels import TextureChannel

        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))
        doc.add_section("main", 4)

        buf = control.render_doc_for_playback(doc)
        self.assertGreater(_rms(buf.data), 0.0)

    def test_degenerate_automation_bp_skipped(self):
        """An AutomationChannel with < 2 breakpoints does not crash and is ignored."""
        from forge import control
        from forge.document.channels import AutomationChannel, Breakpoint, TextureChannel

        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))
        doc.add_channel(AutomationChannel("master_gain", breakpoints=[
            Breakpoint(0, 1.0),  # only 1 point — Curve() would raise
        ]))
        doc.add_section("main", 4)

        # Should not raise; the degenerate lane is skipped.
        buf = control.render_doc_for_playback(doc)
        self.assertGreater(_rms(buf.data), 0.0)


class TestTextureFallbackPath(unittest.TestCase):
    """Textures and automation also work when doc.sections is empty (fallback path)."""

    def test_texture_in_fallback_path(self):
        """Fallback path (no sections) still mixes textures in."""
        from forge import control
        from forge.document.channels import TextureChannel

        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))
        # No sections added — should use fallback_length_bars path.

        buf = control.render_doc_for_playback(doc)
        self.assertGreater(_rms(buf.data), 0.0)

    def test_automation_in_fallback_path(self):
        """Fallback path also applies master_gain automation."""
        from forge import control
        from forge.document.channels import AutomationChannel, Breakpoint, TextureChannel

        fallback_bars = 8
        doc = _make_doc()
        doc.add_channel(TextureChannel("wind"))
        doc.add_channel(AutomationChannel("master_gain", breakpoints=[
            Breakpoint(0, 0.0),
            Breakpoint(2, 1.0),
            Breakpoint(fallback_bars, 1.0),
        ]))
        # No sections — fallback path.

        buf_automted = control._render_doc_sections(doc, fallback_length_bars=fallback_bars)

        # Compare to a no-automation render.
        doc_plain = _make_doc()
        doc_plain.add_channel(TextureChannel("wind"))

        buf_plain = control._render_doc_sections(doc_plain, fallback_length_bars=fallback_bars)

        # Early portion of automated render should be much quieter (near 0).
        from forge.core.grid import Grid
        grid = Grid(doc.bpm, doc.sr)
        half_bar = grid.n_samples(0.5)

        rms_auto_early = _rms(buf_automted.data[:half_bar])
        rms_plain_early = _rms(buf_plain.data[:half_bar])

        self.assertLess(
            rms_auto_early, rms_plain_early,
            f"Automated early RMS ({rms_auto_early:.6f}) should be less than "
            f"plain early RMS ({rms_plain_early:.6f})",
        )


if __name__ == "__main__":
    unittest.main()
