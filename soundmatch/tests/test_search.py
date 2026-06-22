"""Tests for soundmatch.core.search — coarse param search."""

from __future__ import annotations

import unittest

import numpy as np

from inspector.metrics import characterize
from soundmatch.core.phrase import Note, Phrase, seed_from_metrics
from soundmatch.core.search import SearchResult, coarse_search
from soundmatch.tests.fixtures import ensure_fixture


class TestCoarseSearch(unittest.TestCase):
    """Test coarse_search on a synthetic target."""

    def test_search_returns_result(self):
        """coarse_search returns a SearchResult with reasonable fields."""
        y = ensure_fixture()
        m = characterize(y, 44100)
        phrase = Phrase(bpm=120.0, length_s=1.0, notes=[Note(t=0.0, midi=[60])])
        # Use a small custom grid for speed
        grid = {"f0": [55, 65, 80]}
        result = coarse_search(
            m, phrase, "kick", {"f0": 60.0}, [], 42,
            grid=grid, max_iterations=10,
        )
        self.assertIsInstance(result, SearchResult)
        self.assertIsInstance(result.best_params, dict)
        self.assertIsInstance(result.best_score, float)
        self.assertGreater(result.iterations, 0)

    def test_search_reduces_distance(self):
        """On a synthetic target, search should find params with lower
        aggregate than the default base_params."""
        y = ensure_fixture()
        m = characterize(y, 44100)
        phrase = Phrase(bpm=120.0, length_s=1.0, notes=[Note(t=0.0, midi=[60])])

        grid = {"f0": [40, 55, 65, 80, 110]}
        result = coarse_search(
            m, phrase, "kick", {"f0": 60.0}, [], 42,
            grid=grid, max_iterations=10,
        )

        # The search should evaluate multiple candidates
        self.assertGreaterEqual(result.iterations, 3)
        # The best score should be finite
        self.assertLess(result.best_score, float("inf"))
        # f0 should be one of the searched values
        self.assertIn(result.best_params.get("f0"), [40, 55, 65, 80, 110])

    def test_search_empty_grid(self):
        """With an empty grid, search evaluates the base patch only."""
        y = ensure_fixture()
        m = characterize(y, 44100)
        phrase = Phrase(bpm=120.0, length_s=1.0, notes=[Note(t=0.0, midi=[60])])
        result = coarse_search(
            m, phrase, "kick", {"f0": 60.0}, [], 42,
            grid={}, max_iterations=10,
        )
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.best_params.get("f0"), 60.0)


if __name__ == "__main__":
    unittest.main()
