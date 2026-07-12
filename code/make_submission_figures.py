from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
FIGS = ROOT / "figures"
FIGS.mkdir(parents=True, exist_ok=True)


PALETTE = {
    "blue": "#0F4D92",
    "blue_light": "#AFC6E9",
    "red": "#B64342",
    "red_light": "#E9A6A1",
    "teal": "#42949E",
    "gold": "#D99A20",
    "black": "#272727",
    "dark": "#4D4D4D",
    "mid": "#8A8A8A",
    "light": "#D8D8D8",
    "grey": "#909090",
}


def apply_publication_style() -> None:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.size"] = 7
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["xtick.major.width"] = 0.7
    plt.rcParams["ytick.major.width"] = 0.7
    plt.rcParams["xtick.major.size"] = 2.5
    plt.rcParams["ytick.major.size"] = 2.5


def save_figure(fig: plt.Figure, stem: str) -> None:
    for ext, kwargs in {
        "svg": {},
        "pdf": {},
        "png": {"dpi": 600},
    }.items():
        fig.savefig(FIGS / f"{stem}.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def fig1_directional_misfit_trend() -> None:
    apply_publication_style()
    annual = pd.read_csv(TABLES / "revision_annual_misfit_trends.csv")
    fig, ax = plt.subplots(figsize=(4.2, 2.75))
    ax.plot(annual["year"], annual["under_remote_strong"], color=PALETTE["blue"], marker="o", linewidth=1.7, markersize=3.4, label="Strong under-remote misfit")
    ax.plot(annual["year"], annual["over_remote_strong"], color=PALETTE["red"], marker="o", linewidth=1.7, markersize=3.4, label="Strong over-remote misfit")
    ax.set_xlabel("Survey year and valid planned-reference N")
    ax.set_ylabel("Weighted share")
    ax.set_ylim(0, 0.35)
    ax.set_xticks(annual["year"])
    ax.set_xticklabels([f"{int(y)}\nN={int(n):,}" for y, n in zip(annual["year"], annual["n"])], fontsize=5.8)
    ax.set_xlim(annual["year"].min() - 0.25, annual["year"].max() + 0.25)
    ax.grid(axis="y", color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    ax.legend(loc="upper left", fontsize=6)
    save_figure(fig, "fig1_directional_misfit_trend")

def fig2_job_dissatisfaction_by_misfit() -> None:
    apply_publication_style()
    support = pd.read_csv(TABLES / "revision_job_dissatisfaction_by_misfit_type.csv")
    job = support[support["outcome"] == "support_job_dissatisfaction"].copy()
    order = ["fit_weak", "under_remote_weak", "under_remote_strong", "over_remote_weak", "over_remote_strong"]
    labels = ["Aligned or\n<1-day gap", "Wants more WFH\n1-<2 days", "Wants more WFH\n>=2 days", "Wants less WFH\n1-<2 days", "Wants less WFH\n>=2 days"]
    job["misfit_type"] = pd.Categorical(job["misfit_type"], categories=order, ordered=True)
    job = job.dropna(subset=["misfit_type"]).sort_values("misfit_type")

    colors = [PALETTE["grey"], PALETTE["blue_light"], PALETTE["blue"], PALETTE["red_light"], PALETTE["red"]]
    fig, ax = plt.subplots(figsize=(3.54, 2.75))
    y = np.arange(len(job))
    ax.barh(y, job["prevalence_weighted"], color=colors, edgecolor="white", linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Weighted prevalence")
    ax.set_xlim(0, max(job["prevalence_weighted"].max() * 1.25, 0.25))
    ax.grid(axis="x", color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    for yi, val in zip(y, job["prevalence_weighted"]):
        ax.text(val + 0.006, yi, f"{val:.2f}", va="center", fontsize=6.5)
    save_figure(fig, "fig2_job_dissatisfaction_by_misfit")


def fig3_capacity_constrained_performance() -> None:
    apply_publication_style()
    ablation = pd.read_csv(TABLES / "revision_ablation_temporal_performance.csv")
    rules = pd.read_csv(TABLES / "revision_strong_rule_baselines.csv")
    rows = []
    for rule, label in [
        ("absolute_gap_rule", "Absolute gap"),
        ("under_remote_directional_rule", "Directional"),
        ("additive_support_rule", "Additive"),
    ]:
        r = rules[rules["rule"] == rule].iloc[0]
        rows.append({"label": label, "precision": r["precision_at_10"], "lift": r["lift_at_10"]})
    for fs, label in [
        ("hris", "Conventional RF"),
        ("arrangement", "WFH RF"),
        ("gender_children_excluded", "Reduced RF"),
    ]:
        r = ablation[(ablation["feature_set"] == fs) & (ablation["model"] == "rf")].iloc[0]
        rows.append({"label": label, "precision": r["precision_at_10"], "lift": r["lift_at_10"]})
    plot = pd.DataFrame(rows)
    main = ablation[(ablation["feature_set"] == "gender_children_excluded") & (ablation["model"] == "rf")].iloc[0]
    prevalence = main["precision_at_10"] / main["lift_at_10"]
    fig, ax = plt.subplots(figsize=(5.0, 2.85))
    x = np.arange(len(plot))
    ax.bar(x, plot["precision"], color=PALETTE["teal"], width=0.62, label="Precision@10%")
    ax.axhline(prevalence, color=PALETTE["mid"], linestyle="--", linewidth=0.9, label="Jan-Feb 2026 prevalence")
    ax.set_xticks(x)
    ax.set_xticklabels(plot["label"], rotation=20, ha="right")
    ax.set_ylabel("Precision@10%")
    ax.set_ylim(0, max(plot["precision"].max() * 1.34, 0.29))
    ax.grid(axis="y", color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    for xi, row in plot.iterrows():
        ax.text(xi, row["precision"] + 0.008, f"{row['lift']:.2f}x", ha="center", va="bottom", fontsize=6)
    ax.legend(loc="upper left", fontsize=6)
    save_figure(fig, "fig3_capacity_constrained_performance")

def fig4_calibration() -> None:
    apply_publication_style()
    bins = pd.read_csv(TABLES / "revision_calibration_bins.csv")
    cal = pd.read_csv(TABLES / "revision_calibration_correction.csv")
    label_map = {
        "raw_rf": "Raw RF",
        "platt_rf": "Platt",
        "isotonic_rf": "Isotonic",
    }
    color_map = {"raw_rf": PALETTE["red"], "platt_rf": PALETTE["blue"], "isotonic_rf": PALETTE["teal"]}
    fig, ax = plt.subplots(figsize=(3.65, 3.05))
    ax.plot([0, 0.55], [0, 0.55], linestyle="--", linewidth=0.9, color=PALETTE["mid"], label="Perfect calibration")
    for model in ["raw_rf", "platt_rf", "isotonic_rf"]:
        g = bins[bins["model"] == model].sort_values("mean_predicted")
        ax.plot(g["mean_predicted"], g["observed_prevalence"], marker="o", markersize=3, linewidth=1.2, color=color_map[model], label=label_map[model])
    null_brier = cal.loc[cal["model"] == "null_2025_base_rate", "brier"].iloc[0]
    raw_brier = cal.loc[cal["model"] == "raw_gender_children_excluded_rf", "brier"].iloc[0]
    platt_brier = cal.loc[cal["model"] == "platt_gender_children_excluded_rf", "brier"].iloc[0]
    iso_brier = cal.loc[cal["model"] == "isotonic_gender_children_excluded_rf", "brier"].iloc[0]
    ax.text(0.02, 0.53, f"Brier: null {null_brier:.3f}; raw {raw_brier:.3f}; Platt {platt_brier:.3f}; isotonic {iso_brier:.3f}", fontsize=5.6, va="top")
    ax.set_xlim(0, 0.55)
    ax.set_ylim(0, 0.55)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed prevalence")
    ax.grid(color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    ax.legend(loc="lower right", fontsize=5.8)
    save_figure(fig, "fig4_calibration")

def fig5_subgroup_audit() -> None:
    apply_publication_style()
    audit = pd.read_csv(TABLES / "revision_topk_subgroup_audit.csv")
    perf = pd.read_csv(TABLES / "revision_ablation_temporal_performance.csv")
    overall_recall = perf[(perf["feature_set"] == "gender_children_excluded") & (perf["model"] == "rf")]["recall_at_10"].iloc[0]
    core_groups = ["gender_group", "has_children_any", "income_group_traincut", "education_s"]
    fair = audit[(audit["k"].round(2) == 0.10) & audit["group"].isin(core_groups)].copy()
    fair["group_order"] = fair["group"].map({g: i for i, g in enumerate(core_groups)})
    fair = fair.sort_values(["group_order", "value"])
    group_label = {"gender_group": "Gender code", "has_children_any": "Children", "income_group_traincut": "Income", "education_s": "Education"}
    edu = {1: "Less than high school", 2: "High school", 3: "1-3 years college", 4: "Four-year degree", 5: "Graduate degree"}
    def readable_value(group, value):
        if group == "education_s":
            try: return edu.get(int(float(value)), str(value))
            except Exception: return str(value)
        mapping = {"female": "female = 1", "not_coded_female": "female = 0", "low": "Low", "middle": "Middle", "high": "High", "1.0": "Has children", "0.0": "No children", 1.0: "Has children", 0.0: "No children"}
        return mapping.get(value, mapping.get(str(value), str(value).replace("_", " ")))
    labels = [f"{group_label.get(r.group, r.group)}: {readable_value(r.group, r.value)}" for r in fair.itertuples(index=False)]
    y = np.arange(len(fair))
    recall_err = np.vstack([(fair["recall_at_k"] - fair["recall_ci_low"]).clip(lower=0), (fair["recall_ci_high"] - fair["recall_at_k"]).clip(lower=0)])
    fig, ax = plt.subplots(figsize=(5.3, max(2.8, 0.32 * len(fair) + 0.65)))
    ax.barh(y, fair["selection_rate"], color=PALETTE["blue_light"], edgecolor="white", label="Selection rate")
    ax.errorbar(fair["recall_at_k"], y, xerr=recall_err, fmt="o", color=PALETTE["blue"], markersize=3.7, elinewidth=0.8, capsize=1.5, zorder=4, label="Recall@10%")
    ax.axvline(overall_recall, color=PALETTE["mid"], linestyle="--", linewidth=0.8, label="Overall recall@10%")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.3)
    ax.invert_yaxis()
    ax.set_xlabel("Rate")
    ax.set_xlim(0, max(0.42, fair[["selection_rate", "recall_at_k"]].max().max() * 1.15))
    ax.grid(axis="x", color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    ax.legend(loc="lower right", fontsize=5.8)
    save_figure(fig, "fig5_subgroup_audit")

def figS1_misfit_bin_prevalence() -> None:
    apply_publication_style()
    path = TABLES / "revision_misfit_bin_prevalence.csv"
    if not path.exists():
        return
    bins = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    x = np.arange(len(bins))
    colors = [PALETTE["red_light"] if str(v).startswith("<") or str(v).startswith("-") else PALETTE["blue_light"] for v in bins["misfit_bin_days"]]
    ax.bar(x, bins["weighted_prevalence"], color=colors, edgecolor="white", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(bins["misfit_bin_days"], rotation=25, ha="right")
    ax.set_xlabel("Desired minus reference WFH days")
    ax.set_ylabel("Weighted dissatisfaction")
    ax.grid(axis="y", color=PALETTE["light"], linewidth=0.5, alpha=0.75)
    save_figure(fig, "figS1_misfit_bin_prevalence")


def figS2_planned_response_surface() -> None:
    apply_publication_style()
    path = TABLES / "revision_response_surface_planned_only_grid.csv"
    if not path.exists():
        return
    grid = pd.read_csv(path)
    pivot = grid.pivot(index="planned_wfh_days", columns="desired_wfh_days", values="predicted_dissatisfaction")
    support_pivot = grid.pivot(index="planned_wfh_days", columns="desired_wfh_days", values="nearest_cell_n")
    x = pivot.columns.to_numpy(dtype=float)
    y = pivot.index.to_numpy(dtype=float)
    xx, yy = np.meshgrid(x, y)
    z = pivot.to_numpy(dtype=float)
    support_n = support_pivot.to_numpy(dtype=float)
    z_masked = np.ma.masked_where(support_n < 30, z)
    fig, ax = plt.subplots(figsize=(4.7, 3.5))
    contour = ax.contourf(xx, yy, z_masked, levels=12, cmap="YlOrRd")
    ax.contour(xx, yy, z_masked, levels=6, colors="white", linewidths=0.45, alpha=0.75)
    line_min, line_max = max(x.min(), y.min()), min(x.max(), y.max())
    ax.plot([line_min, line_max], [line_min, line_max], color=PALETTE["blue"], linewidth=1.2, label="Desired = planned")
    support = pd.read_csv(TABLES / "revision_response_surface_planned_only_support.csv")
    support = support[support["n"] >= 30]
    if not support.empty:
        sizes = 5 + 30 * np.sqrt(support["n"] / support["n"].max())
        ax.scatter(support["desired_bin"], support["planned_bin"], s=sizes, facecolors="none", edgecolors="black", linewidths=0.32, alpha=0.45, label="Observed cells (N >= 30)")
    ax.set_xlabel("Desired WFH days per five-day week")
    ax.set_ylabel("Employer-planned WFH days per five-day week")
    ax.legend(loc="upper left", fontsize=5.6)
    cbar = fig.colorbar(contour, ax=ax, pad=0.02)
    cbar.set_label("Predicted job dissatisfaction", fontsize=6.5)
    cbar.ax.tick_params(labelsize=6)
    save_figure(fig, "figS2_planned_response_surface")

def write_legends() -> None:
    text = """# Figure Legends

## Figure 1 | Directional strong misfit over time.
Weighted survey-year prevalence of strong under-remote and over-remote misfit after converting SWAA work-from-home percentages to days per five-day week; 2020 covers May-December and 2026 covers January-May. Strong misfit is defined as an absolute desired-minus-reference gap of at least two days.

## Figure 2 | Job dissatisfaction by misfit type.
Weighted 2025-2026 prevalence of job dissatisfaction across fit/weak, under-remote and over-remote misfit categories. Job dissatisfaction is defined as being very or somewhat dissatisfied with the current main job.

## Figure 3 | Fixed-capacity ranking performance.
Top-k refers to the highest-scored k percent of cases. The figure reports top-10% precision for rule-based benchmarks and selected models in the January-February 2026 job-dissatisfaction holdout after training on 2025 data. The absolute-gap rule ranks the absolute desired-planned gap; the directional rule ranks the positive desired-planned gap; the additive rule combines the under-remote gap with prespecified commute, children, and income indicators. Conventional RF uses conventional characteristics; WFH RF adds desired and employer-planned WFH; Reduced RF excludes gender and children. The dashed line is the holdout prevalence, and text above each bar reports lift over random selection. The broader planned-only sensitivity model is reported in Supplementary Table S13.

## Figure 4 | Calibration diagnostics.
Reliability curves compare observed prevalence with mean predicted probabilities for the raw, Platt-calibrated, and isotonic-calibrated reduced-feature random forest. Brier scores are shown in the panel. Calibration mappings are learned by internal cross-validation within the 2025 training data and applied unchanged to the January-February 2026 temporal holdout. ECE uses 10 equal-width probability bins.

## Figure 5 | Subgroup selection and recall.
Selection rates and recall are reported under the global top-10% queue for the core reporting groups: gender coding, children, income, and education. The gender labels reproduce the binary source coding (female = 1 and female = 0). Income groups use tertile cut points estimated in the 2025 training sample. Intersection groups and false-negative rates are retained in the supplementary tables. Estimates are diagnostic allocation checks, not legal compliance tests.

## Supplementary Figure S1 | Job dissatisfaction across signed misfit bins.
Weighted job-dissatisfaction prevalence across desired-minus-reference WFH day bins. The plot checks whether the under-remote pattern is visible across the signed gap distribution rather than only at the two-day threshold.

## Supplementary Figure S2 | Planned-only response surface.
Predicted job dissatisfaction from a weighted polynomial model of desired and employer-planned WFH days. The model includes linear, squared, and interaction terms and adjusts for the main conventional worker and job characteristics and month fixed effects. Desired and planned WFH are centered at the common 2.5-day midpoint. The blue diagonal is the congruence line (desired = planned); values outside the observed 1st-99th percentile range are not displayed.
"""
    (FIGS / "figure_legends.md").write_text(text, encoding="utf-8")


def main() -> None:
    for old in FIGS.glob("figure*_misfit_support_need.*"):
        old.unlink(missing_ok=True)
    for old in FIGS.glob("figure*_model_qc_subgroup audit.*"):
        old.unlink(missing_ok=True)
    for old in FIGS.glob("fig4_calibration_subgroup audit.*"):
        old.unlink(missing_ok=True)
    fig1_directional_misfit_trend()
    fig2_job_dissatisfaction_by_misfit()
    fig3_capacity_constrained_performance()
    fig4_calibration()
    fig5_subgroup_audit()
    figS1_misfit_bin_prevalence()
    figS2_planned_response_surface()
    write_legends()
    print("Saved clean publication figures to figures/")


if __name__ == "__main__":
    main()
