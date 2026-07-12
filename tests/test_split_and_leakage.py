from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("revision_grade_analysis", ROOT / "code" / "revision_grade_analysis.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SplitAndLeakageTests(unittest.TestCase):
    def test_split_is_2025_train_and_2026q1_holdout(self):
        df = pd.DataFrame(
            {
                "year": [2025, 2025, 2026, 2026, 2026],
                "quarter": [1, 4, 1, 2, 3],
                "dissatisfied_broad": [0, 1, 1, 0, 1],
            }
        )
        train, test = mod.split_2025_train_2026q1_holdout(df)
        self.assertEqual(len(train), 2)
        self.assertEqual(len(test), 1)
        self.assertTrue(train["year"].eq(2025).all())
        self.assertTrue(test["year"].eq(2026).all())
        self.assertTrue(test["quarter"].eq(1).all())

    def test_restricted_feature_sets_exclude_satisfaction_like_variables(self):
        forbidden_tokens = ("satisf", "wellbeing", "well_being", "valuation", "attitude", "quit")
        for feature_set in ["restricted", "gender_children_excluded", "gender_children_income_excluded", "minimal_voice", "signed_gap_only"]:
            _, cols = mod.make_preprocessor(feature_set)
            lowered = " ".join(cols).lower()
            for token in forbidden_tokens:
                self.assertNotIn(token, lowered, feature_set)

    def test_named_feature_sets_exclude_gender_and_children(self):
        _, gc_cols = mod.make_preprocessor("gender_children_excluded")
        _, strict_cols = mod.make_preprocessor("gender_children_income_excluded")
        for cols in [gc_cols, strict_cols]:
            self.assertNotIn("female_binary", cols)
            self.assertNotIn("has_children_any", cols)
        self.assertIn("log_income", gc_cols)
        self.assertNotIn("log_income", strict_cols)

    def test_exact_topk_mask_keeps_fixed_capacity_under_ties(self):
        score = [1, 1, 1, 0, 0, 0]
        selected = mod.exact_topk_mask(score, 0.5)
        self.assertEqual(int(selected.sum()), 3)
        self.assertEqual(selected.tolist(), [True, True, True, False, False, False])

    def test_minimal_voice_avoids_redundant_gap_encodings(self):
        _, cols = mod.make_preprocessor("minimal_voice")
        self.assertIn("desired_days", cols)
        self.assertIn("planned_days", cols)
        for redundant in ["misfit_planned", "abs_misfit_planned", "under_remote_planned", "over_remote_planned", "current_days"]:
            self.assertNotIn(redundant, cols)


if __name__ == "__main__":
    unittest.main()
