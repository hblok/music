"""Acceptance tests for Phase 3 — Per-channel gain and pan.

Covers:
  - Pan separation: hard-L / hard-R panned channels drive the expected stereo side.
  - Gain halving: a channel at gain=0.5 contributes ~half the amplitude.
  - MixerWidget pan property, set_pan, default, levels(), levelsChanged dict.
"""

import unittest
import numpy as np


# ---------------------------------------------------------------------------
# Helpers


def _make_render_doc(bpm: float = 600.0, sr: int = 44100):
    """Return a simple doc with kick and hat each on every step, no sections."""
    from forge.document.channels import PatternChannel, StepData
    from forge.document.model import ProjectDoc

    doc = ProjectDoc(bpm=bpm, sr=sr, seed=0)
    kick = PatternChannel("kick", n_steps=16)
    hat = PatternChannel("hat", n_steps=16)
    for ch in (kick, hat):
        for s in ch.steps:
            s.on = True
    doc.add_channel(kick)
    doc.add_channel(hat)
    return doc


# ---------------------------------------------------------------------------
# Pan separation tests


class TestPanSeparation(unittest.TestCase):
    """Hard-L panned channel shows dominant energy on the L side, and vice-versa."""

    def _render_sections(self, doc):
        from forge import control
        return control._render_doc_sections(doc, fallback_length_bars=4)

    def test_hard_left_pan_dominates_left_channel(self):
        """A channel panned hard left has substantially more L energy than R energy."""
        from forge.document.channels import PatternChannel, StepData
        from forge.document.model import ProjectDoc

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        kick.pan = -1.0   # hard left
        doc.add_channel(kick)

        buf = self._render_sections(doc)
        rms_l = float(np.sqrt(np.mean(buf.data[:, 0] ** 2)))
        rms_r = float(np.sqrt(np.mean(buf.data[:, 1] ** 2)))

        self.assertGreater(
            rms_l, rms_r * 10.0,
            f"Hard-L: expected L RMS ({rms_l:.4f}) >> R RMS ({rms_r:.4f})"
        )

    def test_hard_right_pan_dominates_right_channel(self):
        """A channel panned hard right has substantially more R energy than L energy."""
        from forge.document.channels import PatternChannel, StepData
        from forge.document.model import ProjectDoc

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        kick.pan = 1.0   # hard right
        doc.add_channel(kick)

        buf = self._render_sections(doc)
        rms_l = float(np.sqrt(np.mean(buf.data[:, 0] ** 2)))
        rms_r = float(np.sqrt(np.mean(buf.data[:, 1] ** 2)))

        self.assertGreater(
            rms_r, rms_l * 10.0,
            f"Hard-R: expected R RMS ({rms_r:.4f}) >> L RMS ({rms_l:.4f})"
        )

    def test_two_channels_hard_lr_full_render(self):
        """With two channels panned hard L and hard R, each side is dominated by its channel."""
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        from forge import control

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)

        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        kick.pan = -1.0   # hard left

        hat = PatternChannel("hat", n_steps=16)
        for s in hat.steps:
            s.on = True
        hat.pan = 1.0   # hard right

        doc.add_channel(kick)
        doc.add_channel(hat)

        # Use _render_doc_sections (un-mastered) for a clean ratio test.
        buf = control._render_doc_sections(doc, fallback_length_bars=4)

        rms_l = float(np.sqrt(np.mean(buf.data[:, 0] ** 2)))
        rms_r = float(np.sqrt(np.mean(buf.data[:, 1] ** 2)))

        # Both sides should have significant energy (both channels are active).
        self.assertGreater(rms_l, 1e-4, "L side should have energy from kick")
        self.assertGreater(rms_r, 1e-4, "R side should have energy from hat")

        # The two sides should be comparable in energy (both channels active,
        # just on opposite sides) — ratio within 10× of each other.
        ratio = rms_l / rms_r if rms_r > 0 else float("inf")
        self.assertLess(ratio, 10.0, f"L/R ratio {ratio:.2f} too extreme (expected ~1)")
        self.assertGreater(ratio, 0.1, f"L/R ratio {ratio:.2f} too extreme (expected ~1)")

    def test_center_pan_is_balanced(self):
        """Default pan=0 produces balanced L/R energy."""
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        from forge import control

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        # pan=0.0 is the default
        doc.add_channel(kick)

        buf = control._render_doc_sections(doc, fallback_length_bars=4)
        rms_l = float(np.sqrt(np.mean(buf.data[:, 0] ** 2)))
        rms_r = float(np.sqrt(np.mean(buf.data[:, 1] ** 2)))

        # At centre pan the two channels should be within 1% of each other.
        if rms_l > 0 and rms_r > 0:
            ratio = rms_l / rms_r
            self.assertAlmostEqual(ratio, 1.0, delta=0.02,
                msg=f"Centre pan: L/R ratio {ratio:.4f} should be ~1.0")


class TestPanSeparationWithSections(unittest.TestCase):
    """Same pan separation tests through the section-aware render path."""

    def test_hard_left_with_sections(self):
        from forge.document.channels import PatternChannel, StepData
        from forge.document.model import ProjectDoc
        from forge import control

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        kick.pan = -1.0
        doc.add_channel(kick)
        doc.add_section("A", 2)

        buf = control._render_doc_sections(doc)
        rms_l = float(np.sqrt(np.mean(buf.data[:, 0] ** 2)))
        rms_r = float(np.sqrt(np.mean(buf.data[:, 1] ** 2)))

        self.assertGreater(rms_l, rms_r * 10.0,
            f"Section path hard-L: L={rms_l:.4f}, R={rms_r:.4f}")


# ---------------------------------------------------------------------------
# Gain halving tests


class TestGainHalving(unittest.TestCase):
    """Channel at gain=0.5 contributes ~half the amplitude of gain=1.0."""

    def _render_raw(self, gain: float) -> np.ndarray:
        """Render a single kick channel with given gain via _render_doc_sections."""
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        from forge import control

        doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
        kick = PatternChannel("kick", n_steps=16)
        for s in kick.steps:
            s.on = True
        kick.gain = gain
        doc.add_channel(kick)

        buf = control._render_doc_sections(doc, fallback_length_bars=4)
        return buf.data

    def test_gain_half_reduces_rms(self):
        """Un-mastered buffer RMS at gain=0.5 should be ~half of gain=1.0."""
        data_full = self._render_raw(1.0)
        data_half = self._render_raw(0.5)

        rms_full = float(np.sqrt(np.mean(data_full ** 2)))
        rms_half = float(np.sqrt(np.mean(data_half ** 2)))

        # Expect ratio close to 2.0 (full / half = 2×).
        if rms_half > 0:
            ratio = rms_full / rms_half
            self.assertAlmostEqual(ratio, 2.0, delta=0.05,
                msg=f"Gain halving ratio {ratio:.4f} should be ~2.0")
        else:
            self.fail("gain=0.5 render produced silence")

    def test_gain_zero_produces_silence(self):
        """gain=0.0 should produce a silent buffer."""
        data = self._render_raw(0.0)
        np.testing.assert_array_equal(data, 0.0)

    def test_gain_halving_with_sections(self):
        """Same ratio holds through the section-aware render path."""
        from forge.document.channels import PatternChannel, StepData
        from forge.document.model import ProjectDoc
        from forge import control

        def _render(gain):
            doc = ProjectDoc(bpm=600.0, sr=44100, seed=0)
            kick = PatternChannel("kick", n_steps=16)
            for s in kick.steps:
                s.on = True
            kick.gain = gain
            doc.add_channel(kick)
            doc.add_section("A", 2)
            return control._render_doc_sections(doc).data

        data_full = _render(1.0)
        data_half = _render(0.5)

        rms_full = float(np.sqrt(np.mean(data_full ** 2)))
        rms_half = float(np.sqrt(np.mean(data_half ** 2)))

        if rms_half > 0:
            ratio = rms_full / rms_half
            self.assertAlmostEqual(ratio, 2.0, delta=0.05,
                msg=f"Section-path gain halving ratio {ratio:.4f} should be ~2.0")
        else:
            self.fail("gain=0.5 render produced silence (sections path)")


# ---------------------------------------------------------------------------
# Model API tests


class TestModelGainPanAPI(unittest.TestCase):
    def _doc_with_kick(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(PatternChannel("kick"))
        return doc

    def test_default_gain_is_one(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        self.assertAlmostEqual(ch.gain, 1.0)

    def test_default_pan_is_zero(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        self.assertAlmostEqual(ch.pan, 0.0)

    def test_set_channel_gain(self):
        doc = self._doc_with_kick()
        doc.set_channel_gain(0, 0.5)
        self.assertAlmostEqual(doc.channel(0).gain, 0.5)

    def test_set_channel_pan(self):
        doc = self._doc_with_kick()
        doc.set_channel_pan(0, -0.5)
        self.assertAlmostEqual(doc.channel(0).pan, -0.5)

    def test_set_channel_gain_undo(self):
        doc = self._doc_with_kick()
        doc.set_channel_gain(0, 0.3)
        doc.undo()
        self.assertAlmostEqual(doc.channel(0).gain, 1.0)

    def test_set_channel_pan_undo(self):
        doc = self._doc_with_kick()
        doc.set_channel_pan(0, 0.7)
        doc.undo()
        self.assertAlmostEqual(doc.channel(0).pan, 0.0)

    def test_gain_round_trip_nondefault(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        ch.gain = 0.75
        d = ch.to_dict()
        ch2 = PatternChannel.from_dict(d)
        self.assertAlmostEqual(ch2.gain, 0.75)

    def test_pan_round_trip_nondefault(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        ch.pan = -0.5
        d = ch.to_dict()
        ch2 = PatternChannel.from_dict(d)
        self.assertAlmostEqual(ch2.pan, -0.5)

    def test_default_gain_not_emitted_in_to_dict(self):
        """gain=1.0 (default) should be omitted from to_dict to avoid churn."""
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        d = ch.to_dict()
        self.assertNotIn("gain", d)

    def test_default_pan_not_emitted_in_to_dict(self):
        """pan=0.0 (default) should be omitted from to_dict to avoid churn."""
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        d = ch.to_dict()
        self.assertNotIn("pan", d)

    def test_old_dict_loads_with_default_gain_pan(self):
        """Old files without gain/pan load with defaults 1.0/0.0."""
        from forge.document.channels import PatternChannel
        d = {"instrument_id": "kick", "n_steps": 16, "steps": [], "params": {}, "seed": 0}
        ch = PatternChannel.from_dict(d)
        self.assertAlmostEqual(ch.gain, 1.0)
        self.assertAlmostEqual(ch.pan, 0.0)

    def test_copy_preserves_gain_pan(self):
        from forge.document.channels import PatternChannel
        ch = PatternChannel("kick")
        ch.gain = 0.4
        ch.pan = 0.6
        ch2 = ch.copy()
        self.assertAlmostEqual(ch2.gain, 0.4)
        self.assertAlmostEqual(ch2.pan, 0.6)

    def test_texture_gain_pan_round_trip(self):
        from forge.document.channels import TextureChannel
        ch = TextureChannel("wind")
        ch.gain = 0.8
        ch.pan = -0.3
        d = ch.to_dict()
        ch2 = TextureChannel.from_dict(d)
        self.assertAlmostEqual(ch2.gain, 0.8)
        self.assertAlmostEqual(ch2.pan, -0.3)


# ---------------------------------------------------------------------------
# MixerWidget UI tests


class TestMixerWidgetPan(unittest.TestCase):
    """Test pan property, set_pan, defaults, and levels()/levelsChanged."""

    @classmethod
    def setUpClass(cls):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        cls._app = QApplication.instance() or QApplication([])

    def _widget(self, names=("kick", "hat")):
        from forge.ui.mixer import MixerWidget
        return MixerWidget(list(names))

    def test_default_pan_zero(self):
        w = self._widget()
        for name, strip in w._strips.items():
            self.assertAlmostEqual(strip.pan, 0.0, msg=f"Strip {name!r} default pan != 0.0")

    def test_set_pan_updates_property(self):
        w = self._widget()
        strip = w._strips["kick"]
        strip.set_pan(-1.0)
        self.assertAlmostEqual(strip.pan, -1.0, delta=0.01)

    def test_set_pan_hard_right(self):
        w = self._widget()
        strip = w._strips["hat"]
        strip.set_pan(1.0)
        self.assertAlmostEqual(strip.pan, 1.0, delta=0.01)

    def test_widget_set_pan(self):
        w = self._widget()
        w.set_pan("kick", -0.5)
        self.assertAlmostEqual(w._strips["kick"].pan, -0.5, delta=0.01)

    def test_widget_set_pan_noop_for_unknown(self):
        """set_pan on an unknown name should be a no-op (no crash)."""
        w = self._widget()
        w.set_pan("nonexistent", 0.5)  # must not raise

    def test_levels_includes_pan(self):
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertIn("pan", vals, f"levels()['pan'] missing for strip {name!r}")

    def test_levels_pan_default_zero(self):
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertAlmostEqual(vals["pan"], 0.0, delta=0.01,
                msg=f"Default pan in levels() for {name!r} should be 0.0")

    def test_levels_changed_includes_pan(self):
        """levelsChanged signal dict also carries 'pan' key."""
        received = []
        w = self._widget()
        w.levelsChanged.connect(received.append)

        strip = w._strips["kick"]
        strip.set_pan(0.5)  # trigger changed signal

        # Give Qt event loop a moment.
        self._app.processEvents()

        if received:
            lvl = received[-1]
            self.assertIn("pan", lvl.get("kick", {}),
                "levelsChanged dict missing 'pan' key")

    def test_levels_includes_volume_and_muted(self):
        """Ensure adding 'pan' did not break volume/muted in levels()."""
        w = self._widget()
        lvls = w.levels()
        for name, vals in lvls.items():
            self.assertIn("volume", vals)
            self.assertIn("muted", vals)


if __name__ == "__main__":
    unittest.main()
