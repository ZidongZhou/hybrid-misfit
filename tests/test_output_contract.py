from __future__ import annotations

import unittest
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


ROOT = Path(os.environ.get("SWAA_OUTPUTS_ROOT", Path(__file__).resolve().parents[1])).resolve()


class OutputContractTests(unittest.TestCase):
    def test_required_generated_csv_files_exist_and_are_nonempty(self):
        if not (ROOT / "tables").exists():
            self.skipTest("generated tables are not present; run code/run_all.py first")
        required = [
            "revision_sample_construction_flow.csv",
            "revision_ablation_temporal_performance.csv",
            "revision_calibration_correction.csv",
            "revision_topk_subgroup_audit.csv",
            "revision_tie_robust_topk.csv",
            "revision_groupwise_calibrated_subgroup_audit.csv",
            "revision_temporal_calibration_sensitivity.csv",
            "revision_remoteability_moderation.csv",
            "revision_misfit_bin_prevalence.csv",
            "revision_planned_only_ranking_validation.csv",
            "revision_monthly_2026q1_validation.csv",
            "revision_weighted_training_sensitivity.csv",
            "revision_ranking_model_governance_summary.csv",
            "revision_subgroup_safeguard_simulation.csv",
            "revision_response_surface_planned_only.csv",
            "revision_response_surface_planned_only_support.csv",
            "revision_calibration_bins.csv",
            "revision_satisfaction_score_robustness.csv",
            "revision_association_sample_months.csv",
        ]
        for name in required:
            path = ROOT / "tables" / name
            if not path.exists():
                self.skipTest(f"{name} not generated yet; run code/run_all.py first")
            self.assertTrue(path.exists(), name)
            self.assertGreater(len(pd.read_csv(path)), 0, name)

    def test_manifested_outputs_are_present_and_csvs_have_data_rows(self):
        manifest_path = ROOT / "outputs_manifest.csv"
        if not manifest_path.exists():
            self.skipTest("outputs manifest is not present; run code/run_all.py first")
        manifest = pd.read_csv(manifest_path)
        self.assertGreater(len(manifest), 0)
        for rel in manifest["relative_path"]:
            path = ROOT / rel
            self.assertTrue(path.exists(), rel)
            self.assertGreater(path.stat().st_size, 0, rel)
            if path.suffix.lower() == ".csv":
                self.assertGreater(len(pd.read_csv(path)), 0, rel)

    def test_generated_holdout_rows_are_locked_to_2026q1(self):
        path = ROOT / "tables" / "revision_temporal_stability_validation.csv"
        if not path.exists():
            self.skipTest("temporal stability table is not present; run code/run_all.py first")
        stability = pd.read_csv(path)
        self.assertEqual(set(stability["period"]), {"January-February 2026"})
        row = stability.iloc[0]
        self.assertEqual(int(row["n"]), 9253)
        self.assertEqual(int(row["events"]), 1104)

        sample_path = ROOT / "tables" / "revision_sample_construction_flow.csv"
        if not sample_path.exists():
            self.skipTest("sample construction table is not present; run code/run_all.py first")
        sample = pd.read_csv(sample_path)
        self.assertEqual((sample["step"] == "January-February 2026 test analytic sample").sum(), 1)

    def test_supplementary_workbook_has_expected_sheets(self):
        path = ROOT / "Supplementary_Tables.xlsx"
        if not path.exists():
            path = ROOT / "manuscript" / "Supplementary_Tables.xlsx"
        if not path.exists():
            self.skipTest("generated supplementary workbook is not present; run code/run_all.py first")
        self.assertTrue(path.exists())
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("xl/workbook.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet_names = {node.attrib["name"] for node in root.findall("m:sheets/m:sheet", ns)}
        for sheet in ["Index", "S01_SampleFlow", "S17_SubgroupAudit", "S31_TieRobust", "S32_CalFair", "S33_Remoteability", "S36_PlannedMiss", "S38_PlannedRank", "S39_JanFeb", "S40_WtdTraining", "S41_ModelGovernance", "S42_Safeguard", "S43_ResponseSurface", "A1_TemporalCal", "A2_CalibrationBins", "A3_AssocMonths"]:
            self.assertIn(sheet, sheet_names)

    def test_supplementary_workbook_copies_are_byte_identical(self):
        root_copy = ROOT / "Supplementary_Tables.xlsx"
        manuscript_copy = ROOT / "manuscript" / "Supplementary_Tables_FINAL.xlsx"
        if not root_copy.exists() or not manuscript_copy.exists():
            self.skipTest("generated supplementary workbook copies are not present; run code/run_all.py first")
        self.assertEqual(root_copy.read_bytes(), manuscript_copy.read_bytes())

    def test_reference_and_response_surface_outputs_are_corrected(self):
        threshold = pd.read_csv(ROOT / "tables" / "revision_threshold_reference_lpm_robustness.csv")
        self.assertEqual(set(threshold["reference"]), {"planned", "combined", "current"})
        at_two = threshold[(threshold["threshold_days"] == 2.0) & (threshold["term"] == "under")]
        self.assertEqual(len(at_two), 3)
        estimates = dict(zip(at_two["reference"], at_two["weighted_lpm_estimate"]))
        self.assertAlmostEqual(estimates["planned"], 0.1145134838, places=6)
        self.assertAlmostEqual(estimates["combined"], 0.112041, places=5)
        self.assertAlmostEqual(estimates["current"], 0.096007, places=5)
        self.assertEqual(len({round(v, 6) for v in estimates.values()}), 3)

        rsa = pd.read_csv(ROOT / "tables" / "revision_response_surface_planned_only.csv")
        centers = rsa["common_center_days"].dropna().unique()
        self.assertEqual(len(centers), 1)
        self.assertAlmostEqual(float(centers[0]), 2.5, places=8)

    def test_core_ranking_numbers_and_bootstrap_uncertainty(self):
        perf = pd.read_csv(ROOT / "tables" / "revision_ablation_temporal_performance.csv")
        rf = perf[(perf["feature_set"] == "gender_children_excluded") & (perf["model"] == "rf")].iloc[0]
        self.assertAlmostEqual(float(rf["precision_at_10"]), 0.2505399568, places=6)
        rules = pd.read_csv(ROOT / "tables" / "revision_strong_rule_baselines.csv")
        rule = rules[rules["rule"] == "under_remote_directional_rule"].iloc[0]
        self.assertAlmostEqual(float(rule["precision_at_10"]), 0.2321814255, places=6)
        boot = pd.read_csv(ROOT / "tables" / "revision_paired_bootstrap_vs_rules.csv")
        row = boot[boot["comparison"].str.contains("under_remote_directional_rule")].iloc[0]
        self.assertLess(float(row["delta_precision10_low"]), 0)
        self.assertGreater(float(row["delta_precision10_high"]), 0)
        inc = boot[boot["comparison"] == "arrangement_rf_minus_conventional_rf"].iloc[0]
        self.assertAlmostEqual(float(inc["delta_precision10_point"]), 0.0701943844, places=6)
        self.assertGreater(float(inc["delta_precision10_low"]), 0)
        self.assertGreater(float(inc["delta_pr_auc_low"]), 0)
        logit = boot[boot["comparison"] == "arrangement_logit_minus_conventional_logit"].iloc[0]
        self.assertGreater(float(logit["delta_precision10_low"]), 0)

    def test_model_governance_has_one_benchmark_and_same_primary_model(self):
        governance = pd.read_csv(ROOT / "tables" / "revision_ranking_model_governance_summary.csv")
        self.assertEqual(int(governance["preferred_transparent_benchmark"].sum()), 1)
        benchmark = governance[governance["preferred_transparent_benchmark"]].iloc[0]
        self.assertEqual(benchmark["model"], "directional_under_remote_rule")
        primary = governance[governance["primary_complex_model"]].iloc[0]
        self.assertEqual(primary["model"], "no_gender_children")
        ablation = pd.read_csv(ROOT / "tables" / "revision_sensitive_variable_ablation.csv")
        row = ablation[ablation["model"] == "no_gender_children"].iloc[0]
        perf = pd.read_csv(ROOT / "tables" / "revision_ablation_temporal_performance.csv")
        main = perf[(perf["feature_set"] == "gender_children_excluded") & (perf["model"] == "rf")].iloc[0]
        self.assertAlmostEqual(float(row["precision_at_10"]), float(main["precision_at_10"]), places=12)
        self.assertTrue((ablation["current_wfh_included"].astype(str).str.lower() == "false").all())


    def test_primary_association_months_and_retention(self):
        path = ROOT / "tables" / "revision_association_sample_months.csv"
        if not path.exists():
            self.skipTest("association sample month table is not present; run code/run_all.py first")
        tab = pd.read_csv(path)
        cc = tab[tab["complete_case_association_n"] > 0].copy()
        self.assertEqual(set(cc["period"]), {"2025-09", "2025-10", "2025-11", "2025-12"})
        self.assertEqual(int(tab["planned_outcome_eligible_n"].sum()), 37434)
        self.assertEqual(int(tab["complete_case_association_n"].sum()), 15355)
        self.assertAlmostEqual(15355 / 37434, 0.4101886, places=6)
        for period in ["2025-07", "2025-08", "2026-01", "2026-02"]:
            row = tab[tab["period"] == period].iloc[0]
            self.assertEqual(int(row["commute_time_nonmissing_n"]), 0)
            self.assertEqual(int(row["complete_case_association_n"]), 0)

    def test_satisfaction_score_is_not_mislabeled_ordered_model(self):
        path = ROOT / "tables" / "revision_satisfaction_score_robustness.csv"
        tab = pd.read_csv(path)
        self.assertTrue(tab["outcome"].str.contains("five_category_satisfaction_score").all())
        self.assertFalse((ROOT / "tables" / "revision_ordered_satisfaction_robustness.csv").exists())


if __name__ == "__main__":
    unittest.main()
