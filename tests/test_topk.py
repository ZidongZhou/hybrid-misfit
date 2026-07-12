from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("revision_grade_analysis", ROOT / "code" / "revision_grade_analysis.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class TopKTests(unittest.TestCase):
    def test_topk_uses_descending_score_and_stable_count(self):
        y = np.array([0, 1, 1, 0, 1])
        score = np.array([0.1, 0.9, 0.8, 0.7, 0.2])
        precision, recall, lift = mod.topk(y, score, 0.4)
        self.assertAlmostEqual(precision, 1.0)
        self.assertAlmostEqual(recall, 2 / 3)
        self.assertAlmostEqual(lift, 1.0 / (3 / 5))

    def test_weighted_topk_includes_first_case_crossing_capacity(self):
        y = np.array([1, 0, 1])
        score = np.array([0.9, 0.8, 0.7])
        weight = np.array([0.6, 0.3, 0.1])
        precision, recall, lift = mod.weighted_topk(y, score, weight, 0.5)
        self.assertAlmostEqual(precision, 1.0)
        self.assertGreater(recall, 0)
        self.assertGreater(lift, 1.0)

    def test_subgroup_metrics_use_the_global_queue(self):
        y = np.array([1, 0, 1, 0])
        score = np.array([0.99, 0.98, 0.20, 0.10])
        group = np.array(["A", "B", "B", "B"])
        selected = mod.exact_topk_mask(score, 0.5)

        selection_rate, precision, recall, fnr = mod.subgroup_metrics_under_global_queue(
            y, selected, group, "B"
        )

        # A global top-50% queue selects one of the three B observations.
        self.assertAlmostEqual(selection_rate, 1 / 3)
        self.assertAlmostEqual(precision, 0.0)
        self.assertAlmostEqual(recall, 0.0)
        self.assertAlmostEqual(fnr, 1.0)

    def test_global_queue_bootstrap_returns_intervals_for_same_estimand(self):
        y = np.array([1, 0, 1, 0, 0, 1])
        score = np.array([0.95, 0.90, 0.60, 0.50, 0.20, 0.10])
        group = np.array(["A", "B", "B", "B", "A", "B"])
        low, high = mod.bootstrap_subgroup_global_topk_ci(y, score, group, "B", k=0.5, n_boot=80, seed=4)

        self.assertEqual(low.shape, (4,))
        self.assertEqual(high.shape, (4,))
        self.assertTrue(np.all(low <= high))


if __name__ == "__main__":
    unittest.main()
