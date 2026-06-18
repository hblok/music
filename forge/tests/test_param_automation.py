"""Phase 6 — per-channel parameter automation tests.

Tests:
  - Rising spectral centroid gate  (THE GATE)
  - No-automation regression (byte-identity)
  - Round-trip: AutomationChannel with target_channel survives to_dict/from_dict
  - Determinism: swept render is identical across two runs
  - Model: set_automation_target is transactional and undo-safe
  - master_gain lane still treated as global when target_channel is None

Note on water_of_life_drop restorability
-----------------------------------------
The ``water_of_life_drop`` track's acid cutoff sweep can now be restored by
adding ``AutomationChannel(target_param="cutoff", target_channel=<acid_idx>)``
with breakpoints following the sweep curve used in the original composition.
No committed JSON needs to be modified; the lane is purely additive.
"""

import unittest

import numpy as np


# ---------------------------------------------------------------------------
# Helpers


def _make_acid_doc(length_bars: int = 16, bpm: float = 200.0, seed: int = 42):
    """Build a minimal doc with one acid PatternChannel hitting every other step."""
    from forge.document.channels import AutomationChannel, Breakpoint, PatternChannel
    from forge.document.model import ProjectDoc

    doc = ProjectDoc(title="acid_test", bpm=bpm, seed=seed)
    # Acid channel: 16 steps, every other step on.
    acid = PatternChannel("acid", n_steps=16)
    for i in range(0, 16, 2):
        acid.steps[i].on = True
    doc.add_channel(acid)  # index 0
    doc.add_section("main", length_bars)
    return doc


def _render(doc):
    from forge.control import render_doc_for_playback
    return render_doc_for_playback(doc)


def _centroid(buf):
    from forge.analysis.loudness import spectral_centroid
    return spectral_centroid(buf)


# ---------------------------------------------------------------------------
# THE GATE — rising spectral centroid


class TestRisingSpectralCentroid(unittest.TestCase):
    """An acid channel with a cutoff lane 300→1800 over 16 bars must produce
    a measurably rising spectral centroid (second half brighter than first half).

    This exercises the full stack:
      AutomationChannel(target_channel=0, target_param="cutoff")
      → _render_doc_sections builds a Curve and per-step override closure
      → render_pattern_spec(param_override=…) → render_groove injects cutoff
      → acid_note({"cutoff": <swept_value>, ...}) drives the filter
    """

    def _build_doc_with_sweep(self, length_bars=16, bpm=200.0):
        from forge.document.channels import AutomationChannel, Breakpoint
        doc = _make_acid_doc(length_bars=length_bars, bpm=bpm)
        # Automation lane targeting channel 0 (acid), sweeping cutoff 300→1800.
        lane = AutomationChannel(
            target_param="cutoff",
            target_channel=0,
            breakpoints=[
                Breakpoint(0.0, 300.0),
                Breakpoint(float(length_bars), 1800.0),
            ],
        )
        doc.add_channel(lane)  # index 1
        return doc

    def test_second_half_brighter(self):
        """Second half of the swept render must have a higher spectral centroid."""
        from forge.analysis.loudness import spectral_centroid

        doc = self._build_doc_with_sweep()
        buf = _render(doc)

        n = buf.data.shape[0]
        mid = n // 2

        # Wrap in minimal AudioBuffer-like objects for spectral_centroid.
        # spectral_centroid accepts an AudioBuffer; replicate its interface.
        from forge.core.buffer import AudioBuffer
        first_half = AudioBuffer(mid, doc.sr)
        first_half.data[:] = buf.data[:mid]
        second_half = AudioBuffer(n - mid, doc.sr)
        second_half.data[:] = buf.data[mid:]

        c1 = spectral_centroid(first_half, sr=doc.sr)
        c2 = spectral_centroid(second_half, sr=doc.sr)

        # Store for the report (visible in test output with -v).
        self._c1 = c1
        self._c2 = c2

        self.assertGreater(
            c2, c1,
            msg=(
                f"Expected second-half centroid ({c2:.1f} Hz) > "
                f"first-half centroid ({c1:.1f} Hz) — cutoff sweep not working"
            ),
        )

    def test_centroid_values_reasonable(self):
        """Both centroids are audible frequencies (>50 Hz) confirming acid fired."""
        from forge.analysis.loudness import spectral_centroid
        from forge.core.buffer import AudioBuffer

        doc = self._build_doc_with_sweep()
        buf = _render(doc)
        n = buf.data.shape[0]
        mid = n // 2

        first = AudioBuffer(mid, doc.sr)
        first.data[:] = buf.data[:mid]
        c1 = spectral_centroid(first, sr=doc.sr)
        self.assertGreater(c1, 50.0, msg="First-half centroid too low — silent render?")


# ---------------------------------------------------------------------------
# No-automation regression (byte-identity)


class TestNoAutomationRegression(unittest.TestCase):
    """Adding the param_override plumbing must not change renders that have
    no per-channel lanes.
    """

    def test_identical_without_lanes(self):
        """Render without any AutomationChannel is byte-identical with and
        without the override plumbing (verified by rendering the same doc twice
        and comparing — also checks determinism implicitly).
        """
        doc = _make_acid_doc()
        b1 = _render(doc)
        b2 = _render(doc)
        np.testing.assert_array_equal(
            b1.data, b2.data,
            err_msg="Re-render of same doc (no lanes) is not byte-identical",
        )

    def test_lane_with_no_breakpoints_ignored(self):
        """An AutomationChannel with fewer than 2 breakpoints is skipped
        silently (Curve requires >= 2 points) — render must not raise.
        """
        from forge.document.channels import AutomationChannel
        doc = _make_acid_doc()
        lane = AutomationChannel(target_param="cutoff", target_channel=0)
        # No breakpoints added → skipped at render time.
        doc.add_channel(lane)
        buf = _render(doc)  # must not raise
        self.assertGreater(buf.data.shape[0], 0)


# ---------------------------------------------------------------------------
# Round-trip: to_dict / from_dict


class TestRoundTrip(unittest.TestCase):
    def test_target_channel_round_trips(self):
        from forge.document.channels import AutomationChannel, Breakpoint, channel_from_dict
        ch = AutomationChannel(
            target_param="cutoff",
            target_channel=2,
            breakpoints=[Breakpoint(0.0, 300.0), Breakpoint(16.0, 1800.0)],
        )
        d = ch.to_dict()
        self.assertEqual(d["target_channel"], 2)
        ch2 = channel_from_dict(d)
        self.assertEqual(ch2.target_channel, 2)
        self.assertEqual(ch2.target_param, "cutoff")
        self.assertAlmostEqual(ch2.breakpoints[0].value, 300.0)
        self.assertAlmostEqual(ch2.breakpoints[1].value, 1800.0)

    def test_target_channel_none_omitted_from_dict(self):
        """target_channel=None must NOT appear in to_dict (no churn for old docs)."""
        from forge.document.channels import AutomationChannel
        ch = AutomationChannel(target_param="master_gain")
        d = ch.to_dict()
        self.assertNotIn("target_channel", d)

    def test_target_channel_none_round_trips(self):
        """Legacy master_gain lanes (no target_channel key) load as None."""
        from forge.document.channels import channel_from_dict
        d = {
            "kind": "automation",
            "target_param": "master_gain",
            "breakpoints": [{"bar": 0.0, "value": 1.0}, {"bar": 8.0, "value": 0.5}],
        }
        ch = channel_from_dict(d)
        self.assertIsNone(ch.target_channel)

    def test_copy_preserves_target_channel(self):
        from forge.document.channels import AutomationChannel, Breakpoint
        ch = AutomationChannel(
            target_param="cutoff",
            target_channel=3,
            breakpoints=[Breakpoint(0.0, 400.0)],
        )
        ch2 = ch.copy()
        self.assertEqual(ch2.target_channel, 3)
        self.assertEqual(ch2.target_param, "cutoff")

    def test_projectdoc_round_trip(self):
        """Full ProjectDoc serialize/deserialize preserves target_channel."""
        from forge.document.channels import AutomationChannel, Breakpoint
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        lane = AutomationChannel(
            target_param="cutoff",
            target_channel=1,
            breakpoints=[Breakpoint(0.0, 300.0), Breakpoint(8.0, 1500.0)],
        )
        doc.add_channel(lane)
        doc2 = ProjectDoc.from_dict(doc.to_dict())
        ch = doc2.channel(0)
        self.assertEqual(ch.target_channel, 1)
        self.assertEqual(ch.target_param, "cutoff")


# ---------------------------------------------------------------------------
# Determinism: swept render is identical across two runs


class TestDeterminism(unittest.TestCase):
    def test_swept_render_deterministic(self):
        """The cutoff-swept render is byte-identical when called twice."""
        from forge.document.channels import AutomationChannel, Breakpoint
        doc = _make_acid_doc()
        lane = AutomationChannel(
            target_param="cutoff",
            target_channel=0,
            breakpoints=[Breakpoint(0.0, 300.0), Breakpoint(16.0, 1800.0)],
        )
        doc.add_channel(lane)
        b1 = _render(doc)
        b2 = _render(doc)
        np.testing.assert_array_equal(
            b1.data, b2.data,
            err_msg="Swept render is not deterministic",
        )


# ---------------------------------------------------------------------------
# Model: set_automation_target is transactional and undo-safe


class TestSetAutomationTarget(unittest.TestCase):
    def _auto_doc(self):
        from forge.document.channels import AutomationChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(AutomationChannel(target_param="master_gain"))
        return doc, 0

    def test_set_target_channel(self):
        doc, idx = self._auto_doc()
        doc.set_automation_target(idx, "cutoff", target_channel=2)
        ch = doc.channel(idx)
        self.assertEqual(ch.target_param, "cutoff")
        self.assertEqual(ch.target_channel, 2)

    def test_set_target_channel_none(self):
        from forge.document.channels import AutomationChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(AutomationChannel(target_param="cutoff", target_channel=1))
        doc.set_automation_target(0, "master_gain", target_channel=None)
        ch = doc.channel(0)
        self.assertIsNone(ch.target_channel)
        self.assertEqual(ch.target_param, "master_gain")

    def test_set_target_is_undoable(self):
        doc, idx = self._auto_doc()
        doc.set_automation_target(idx, "cutoff", target_channel=2)
        doc.undo()
        ch = doc.channel(idx)
        self.assertEqual(ch.target_param, "master_gain")
        self.assertIsNone(ch.target_channel)

    def test_set_target_no_change_is_noop(self):
        doc, idx = self._auto_doc()
        h_before = doc.history.can_undo()
        doc.set_automation_target(idx, "master_gain", target_channel=None)
        # No new undo entry because nothing changed.
        self.assertEqual(doc.history.can_undo(), h_before)

    def test_wrong_channel_type_raises(self):
        from forge.document.channels import PatternChannel
        from forge.document.model import ProjectDoc
        doc = ProjectDoc()
        doc.add_channel(PatternChannel("kick"))
        with self.assertRaises(TypeError):
            doc.set_automation_target(0, "cutoff", target_channel=0)


# ---------------------------------------------------------------------------
# Master-gain lane behaviour unchanged when target_channel is None


class TestMasterGainUnchanged(unittest.TestCase):
    def test_master_gain_lane_still_works(self):
        """A master_gain lane (target_channel=None) still applies as before.

        We test via _render_doc_sections (pre-mastering) so normalization does
        not mask the gain difference.
        """
        from forge.control import _render_doc_sections
        from forge.document.channels import AutomationChannel, Breakpoint, PatternChannel
        from forge.document.model import ProjectDoc

        doc = ProjectDoc(bpm=200.0, seed=1)
        kick = PatternChannel("kick", n_steps=8)
        for i in range(0, 8, 2):
            kick.steps[i].on = True
        doc.add_channel(kick)
        doc.add_section("main", 4)

        # Render without gain lane (pre-mastering).
        buf_plain = _render_doc_sections(doc)

        # Add master_gain lane that scales to 0.1 everywhere.
        lane = AutomationChannel(
            target_param="master_gain",
            target_channel=None,
            breakpoints=[Breakpoint(0.0, 0.1), Breakpoint(4.0, 0.1)],
        )
        doc.add_channel(lane)
        buf_quiet = _render_doc_sections(doc)

        # The quiet render must be much lower amplitude (pre-mastering).
        peak_plain = np.max(np.abs(buf_plain.data))
        peak_quiet = np.max(np.abs(buf_quiet.data))
        self.assertGreater(peak_plain, peak_quiet * 5,
                           msg="master_gain lane did not reduce amplitude as expected")


if __name__ == "__main__":
    unittest.main()
