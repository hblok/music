"""Tests for soundmatch.core.variants — sweep, render_and_score."""
from __future__ import annotations

import unittest
from typing import Any

from inspector.metrics import Metrics, characterize
from soundmatch.core.phrase import Note, Phrase
from soundmatch.core.scoring import Scorecard
from soundmatch.core.variants import VariantSpec, VariantResult, sweep, render_and_score
from soundmatch.tests.fixtures import ensure_fixture


def _target_metrics() -> Metrics:
    y = ensure_fixture()
    return characterize(y, 44100)


def _simple_phrase() -> Phrase:
    return Phrase(
        bpm=120,
        length_s=1.0,
        notes=[Note(t=0.0, midi=[60]), Note(t=0.5, midi=[64])],
        loop=True,
    )


_BASE_PARAMS = {
    "midi": 60, "duration": 1.0, "attack": 0.01, "perc_decay": 0.05,
    "hp_cutoff": 110, "formant_mix": 0.2, "formant2_hz": 1750,
    "formant2_mix": 1.4, "rolloff": 0.6, "drive": 2.0,
    "lp_cutoff": 9000, "bloom": 0.2, "rasp": 0.18,
}


class TestVariantSpec(unittest.TestCase):
    """Test VariantSpec dataclass."""

    def test_to_dict(self):
        vs = VariantSpec(name="test", param_overrides={"rasp": 0.3})
        d = vs.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["param_overrides"]["rasp"], 0.3)

    def test_from_dict(self):
        d = {"name": "test", "param_overrides": {"drive": 3.0}}
        vs = VariantSpec.from_dict(d)
        self.assertEqual(vs.name, "test")
        self.assertEqual(vs.param_overrides["drive"], 3.0)

    def test_roundtrip(self):
        vs = VariantSpec(name="A", param_overrides={"x": 1})
        vs2 = VariantSpec.from_dict(vs.to_dict())
        self.assertEqual(vs2.name, vs.name)
        self.assertEqual(vs2.param_overrides, vs.param_overrides)


class TestSweep(unittest.TestCase):
    """Test sweep() generates correct variant specs."""

    def test_param_sweep_cardinality(self):
        specs = sweep({"rasp": 0.18}, "rasp", [0.1, 0.2, 0.3])
        self.assertEqual(len(specs), 3)

    def test_param_sweep_names(self):
        specs = sweep({"rasp": 0.18}, "rasp", [0.1, 0.2])
        self.assertEqual(specs[0].name, "rasp=0.1")
        self.assertEqual(specs[1].name, "rasp=0.2")

    def test_param_sweep_overrides(self):
        specs = sweep({"rasp": 0.18}, "rasp", [0.1, 0.3])
        self.assertEqual(specs[0].param_overrides["rasp"], 0.1)
        self.assertEqual(specs[1].param_overrides["rasp"], 0.3)

    def test_macro_sweep_snare(self):
        specs = sweep({}, "snare")
        self.assertGreater(len(specs), 0)
        for s in specs:
            self.assertIn("snap_level", s.param_overrides)

    def test_macro_sweep_staccato(self):
        specs = sweep({}, "staccato")
        self.assertGreater(len(specs), 0)
        for s in specs:
            self.assertIn("perc_decay", s.param_overrides)

    def test_macro_sweep_body(self):
        specs = sweep({}, "body")
        self.assertGreater(len(specs), 0)
        for s in specs:
            self.assertIn("hp_cutoff", s.param_overrides)

    def test_empty_values(self):
        specs = sweep({"x": 1}, "x", [])
        self.assertEqual(len(specs), 0)

    def test_unknown_axis_no_values(self):
        specs = sweep({"x": 1}, "unknown_axis")
        self.assertEqual(len(specs), 0)


class TestRenderAndScore(unittest.TestCase):
    """Test render_and_score produces sorted results."""

    def test_produces_results(self):
        specs = [
            VariantSpec(name="low_drive", param_overrides={"drive": 1.0}),
            VariantSpec(name="high_drive", param_overrides={"drive": 4.0}),
        ]
        phrase = _simple_phrase()
        target = _target_metrics()
        results = render_and_score(
            phrase, "synth_brass", _BASE_PARAMS, specs, target, seed=42, sr=44100,
        )
        self.assertEqual(len(results), 2)

    def test_results_sorted_by_aggregate(self):
        specs = [
            VariantSpec(name="a", param_overrides={"drive": 1.0}),
            VariantSpec(name="b", param_overrides={"drive": 2.0}),
            VariantSpec(name="c", param_overrides={"drive": 4.0}),
        ]
        phrase = _simple_phrase()
        target = _target_metrics()
        results = render_and_score(
            phrase, "synth_brass", _BASE_PARAMS, specs, target, seed=42, sr=44100,
        )
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i].aggregate, results[i+1].aggregate)

    def test_result_has_metrics_and_score(self):
        specs = [VariantSpec(name="test", param_overrides={"drive": 2.0})]
        phrase = _simple_phrase()
        target = _target_metrics()
        results = render_and_score(
            phrase, "synth_brass", _BASE_PARAMS, specs, target, seed=42, sr=44100,
        )
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertIsInstance(r.metrics, Metrics)
        self.assertIsInstance(r.score, Scorecard)
        self.assertIsInstance(r.aggregate, float)


class TestVariantResultSerialization(unittest.TestCase):
    """Test VariantResult round-trip."""

    def test_roundtrip(self):
        from soundmatch.core.scoring import Scorecard, MetricDelta, diff
        t = _target_metrics()
        y = ensure_fixture()
        cand_m = characterize(y, 44100)
        sc = diff(t, cand_m)
        spec = VariantSpec(name="test", param_overrides={"x": 1})
        vr = VariantResult(spec=spec, metrics=cand_m, score=sc, aggregate=sc.aggregate())
        d = vr.to_dict()
        vr2 = VariantResult.from_dict(d)
        self.assertEqual(vr2.spec.name, "test")
        self.assertAlmostEqual(vr2.aggregate, vr.aggregate, places=3)


if __name__ == "__main__":
    unittest.main()
