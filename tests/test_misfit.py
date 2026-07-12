from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("revision_grade_analysis", ROOT / "code" / "revision_grade_analysis.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class MisfitConstructionTests(unittest.TestCase):
    def test_planned_combined_and_current_references_are_distinct(self):
        df = pd.DataFrame(
            {
                "desired_days": [4.0, 1.0, 2.0, np.nan],
                "planned_days": [2.0, 3.5, np.nan, 2.0],
                "current_days": [1.0, 4.0, 1.0, 1.0],
            }
        )
        df["combined_reference_days"] = df["planned_days"].where(df["planned_days"].notna(), df["current_days"])
        for ref, source in [("planned", "planned_days"), ("combined", "combined_reference_days"), ("current", "current_days")]:
            df[f"misfit_{ref}"] = df["desired_days"] - df[source]
            m = df[f"misfit_{ref}"]
            df[f"under_remote_{ref}"] = np.where(m.notna(), (m >= 2).astype(float), np.nan)
            df[f"over_remote_{ref}"] = np.where(m.notna(), (m <= -2).astype(float), np.nan)

        self.assertEqual(df.loc[0, "misfit_planned"], 2.0)
        self.assertEqual(df.loc[0, "misfit_combined"], 2.0)
        self.assertEqual(df.loc[0, "misfit_current"], 3.0)
        self.assertTrue(np.isnan(df.loc[2, "misfit_planned"]))
        self.assertEqual(df.loc[2, "misfit_combined"], 1.0)
        self.assertEqual(df.loc[2, "misfit_current"], 1.0)
        self.assertEqual(df.loc[1, "over_remote_planned"], 1.0)
        self.assertTrue(np.isnan(df.loc[3, "under_remote_combined"]))

    def test_analysis_source_has_no_legacy_fallback_aliases(self):
        text = (ROOT / "code" / "revision_grade_analysis.py").read_text(encoding="utf-8")
        for legacy in ["misfit_fallback", "under_remote_fallback", "over_remote_fallback", "fallback_reference_days"]:
            self.assertNotIn(legacy, text)

    def test_ece_constant_score(self):
        y = np.array([0, 1, 0, 0])
        score = np.repeat(0.25, 4)
        self.assertAlmostEqual(mod.ece(y, score), 0.0)


if __name__ == "__main__":
    unittest.main()
