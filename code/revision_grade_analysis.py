from __future__ import annotations

import argparse
import math
import hashlib
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DELIVERY = Path(__file__).resolve().parents[1]
ROOT = DELIVERY.parent
ZIP_PATH = ROOT / "WFH_Code_and_Data_May2020_to_May2026.zip"
TABLES = DELIVERY / "tables"
FIGURES = DELIVERY / "figures"


COLS = [
    "date",
    "cratio100",
    "age_quant",
    "income",
    "female",
    "education_s",
    "work_industry",
    "occupation_clean",
    "region",
    "commutetime_quant",
    "haschildren",
    "live_children",
    "children_household_yesno",
    "worktime_remoteable_pct",
    "wfhcovid_fracmat",
    "numwfh_days_postCOVID_s_u",
    "numwfh_days_postCOVID_boss_s_u",
    "job_satisfaction_qual",
    "quit_qual",
    "labsearch_qual",
    "wbp_react_qual",
    "subj_wellbeing",
    "wfh_feel_quant",
    "wfh_feel_new_qual",
    "wfh_feel_pr_bp_quant0",
    "wfh_feel_pr_hyb_quant0",
    "wfh_eff_COVID_quant",
    "wfh_eff_noCOVID_qual",
]


def read_data() -> pd.DataFrame:
    """Read the verified SWAA release with bounded memory use.

    The 2025-2026 rows retain all analysis columns. Earlier rows retain only
    the fields needed for annual directional-misfit trends and the pre-2025
    occupation remoteability proxy. This is a lossless optimization for the
    reported analyses, not a sample restriction.
    """
    if not ZIP_PATH.exists():
        raise SystemExit(
            "Raw SWAA data zip was not found.\n"
            f"Expected path: {ZIP_PATH}\n"
            "Place WFH_Code_and_Data_May2020_to_May2026.zip in the parent directory of "
            "the project folder, or pass --data-zip PATH."
        )
    keep_early = {
        "date", "cratio100", "occupation_clean", "wfhcovid_fracmat",
        "numwfh_days_postCOVID_s_u", "numwfh_days_postCOVID_boss_s_u",
    }
    chunks = []
    with zipfile.ZipFile(ZIP_PATH) as zf:
        if "WFHdata_May26.csv" not in zf.namelist():
            raise SystemExit("WFHdata_May26.csv was not found inside the supplied SWAA zip file.")
        with zf.open("WFHdata_May26.csv") as fh:
            reader = pd.read_csv(
                fh,
                usecols=lambda c: c in COLS,
                chunksize=50000,
                low_memory=False,
            )
            for chunk in reader:
                years = pd.to_numeric(chunk["date"].astype(str).str.extract(r"(20\d{2})")[0], errors="coerce")
                early = years.lt(2025)
                for col in chunk.columns:
                    if col not in {"date", "region"}:
                        chunk[col] = pd.to_numeric(chunk[col], errors="coerce", downcast="float")
                # Earlier rows are needed only for the annual trend and the
                # occupation-level remoteability proxy.
                for col in chunk.columns:
                    if col not in keep_early and col not in {"date", "region"}:
                        chunk.loc[early, col] = np.nan
                chunk.loc[early, "region"] = np.nan
                chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True, copy=False)
    del chunks
    ym = df["date"].astype(str).str.extract(r"(?P<year>20\d{2})m(?P<month>\d{1,2})")
    df["year"] = pd.to_numeric(ym["year"], errors="coerce", downcast="integer")
    df["month"] = pd.to_numeric(ym["month"], errors="coerce", downcast="integer")
    df["quarter"] = ((df["month"] - 1) // 3 + 1).astype("Int8")
    df["female_binary"] = np.where(df["female"].notna(), (df["female"] > 0).astype(float), np.nan)
    df["gender_group"] = np.select(
        [df["female_binary"] == 1, df["female_binary"] == 0],
        ["female", "not_coded_female"],
        default="gender_missing",
    )
    df["log_income"] = np.log(df["income"].where(df["income"] > 0))
    child_sources = df[["haschildren", "children_household_yesno", "live_children"]]
    child_observed = child_sources.notna().any(axis=1)
    has_child = (df["haschildren"] == 1) | (df["children_household_yesno"] > 1) | (df["live_children"] > 1)
    df["has_children_any"] = np.where(child_observed, has_child.astype(float), np.nan)
    train_scope = df["year"] == 2025
    commute_cutoff_2025 = df.loc[train_scope, "commutetime_quant"].quantile(0.75)
    income_low_cutoff_2025 = df.loc[train_scope, "income"].quantile(1 / 3)
    income_high_cutoff_2025 = df.loc[train_scope, "income"].quantile(2 / 3)
    df["high_commute"] = np.where(
        df["commutetime_quant"].notna(),
        (df["commutetime_quant"] >= commute_cutoff_2025).astype(float),
        np.nan,
    )
    df["income_group"] = np.select(
        [
            df["income"].notna() & (df["income"] <= income_low_cutoff_2025),
            df["income"].notna() & (df["income"] > income_low_cutoff_2025) & (df["income"] <= income_high_cutoff_2025),
            df["income"].notna() & (df["income"] > income_high_cutoff_2025),
        ],
        ["low", "middle", "high"],
        default="income_missing",
    )
    df["high_commute_traincut"] = np.where(
        df["commutetime_quant"].notna(),
        (df["commutetime_quant"] >= commute_cutoff_2025).astype(float),
        np.nan,
    )
    df["income_group_traincut"] = df["income_group"]
    df["commute_group"] = np.select(
        [df["high_commute_traincut"] == 1, df["high_commute_traincut"] == 0],
        ["high_commute", "other"],
        default="commute_missing",
    )
    df["children_group"] = np.select(
        [df["has_children_any"] == 1, df["has_children_any"] == 0],
        ["children", "no_children"],
        default="children_missing",
    )
    df["gender_children"] = df["gender_group"].astype(str) + "_" + df["children_group"].astype(str)
    df["income_commute"] = df["income_group_traincut"].astype(str) + "_" + df["commute_group"].astype(str)
    df["desired_days"] = df["numwfh_days_postCOVID_s_u"] / 20.0
    df["planned_days"] = df["numwfh_days_postCOVID_boss_s_u"] / 20.0
    df["current_days"] = df["wfhcovid_fracmat"] / 20.0
    pre_remote = df[df["year"].lt(2025) & df["occupation_clean"].notna() & df["current_days"].notna()].copy()
    if len(pre_remote):
        occ_remote = pre_remote.groupby("occupation_clean")["current_days"].mean()
        df["occupation_remoteability_proxy"] = df["occupation_clean"].map(occ_remote)
    else:
        df["occupation_remoteability_proxy"] = np.nan
    df["combined_reference_days"] = df["planned_days"].where(df["planned_days"].notna(), df["current_days"])
    df["reference_source_planned"] = df["planned_days"].notna().astype(int)
    for ref, ref_col in {"planned":"planned_days", "combined":"combined_reference_days", "current":"current_days"}.items():
        df[f"misfit_{ref}"] = df["desired_days"] - df[ref_col]
        df[f"abs_misfit_{ref}"] = df[f"misfit_{ref}"].abs()
        df[f"under_gap_{ref}"] = df[f"misfit_{ref}"].clip(lower=0)
        m = df[f"misfit_{ref}"]
        df[f"under_remote_{ref}"] = np.where(m.notna(), (m >= 2).astype(float), np.nan)
        df[f"over_remote_{ref}"] = np.where(m.notna(), (m <= -2).astype(float), np.nan)
    df["dissatisfied_broad"] = np.where(df["job_satisfaction_qual"].notna(), df["job_satisfaction_qual"].isin([1, 2]).astype(int), np.nan)
    df["dissatisfied_strict"] = np.where(df["job_satisfaction_qual"].notna(), (df["job_satisfaction_qual"] == 1).astype(int), np.nan)
    df["satisfaction_score_high_bad"] = np.where(df["job_satisfaction_qual"].notna(), 6 - df["job_satisfaction_qual"], np.nan)
    df["support_recent_quit"] = np.where(df["quit_qual"].notna(), (df["quit_qual"] == 1).astype(int), np.nan)
    df["support_wfh_job_search"] = np.where(df["labsearch_qual"].notna(), df["labsearch_qual"].isin([1, 2]).astype(int), np.nan)
    df["support_rto_resistance"] = np.where(df["wbp_react_qual"].notna(), df["wbp_react_qual"].isin([2, 3]).astype(int), np.nan)
    df["support_low_wellbeing"] = np.where(df["subj_wellbeing"].notna(), (df["subj_wellbeing"] <= 4).astype(int), np.nan)
    return df


def weighted_mean(x, w):
    ok = x.notna()
    if ok.sum() == 0:
        return np.nan
    ww = w[ok].fillna(0)
    return float(np.average(x[ok], weights=ww)) if ww.sum() > 0 else float(x[ok].mean())


def topk(y, score, k=0.1):
    n = len(y)
    m = max(1, int(math.ceil(n * k)))
    order = np.argsort(-score, kind="mergesort")
    selected = order[:m]
    events = y.sum()
    found = y[selected].sum()
    precision = found / m
    recall = found / events if events else np.nan
    prevalence = events / n
    lift = precision / prevalence if prevalence else np.nan
    return precision, recall, lift


def exact_topk_mask(score, k=0.1):
    """Select exactly ceil(n*k) observations using a stable order for score ties."""
    score = np.asarray(score, dtype=float)
    n = len(score)
    m = max(1, int(math.ceil(n * k)))
    order = np.argsort(-score, kind="mergesort")
    selected = np.zeros(n, dtype=bool)
    selected[order[:m]] = True
    return selected


def topk_random_tie(y, score, k=0.1, rng=None):
    rng = rng or np.random.default_rng(0)
    y = np.asarray(y)
    score = np.asarray(score)
    n = len(y)
    m = max(1, int(math.ceil(n * k)))
    tie_breaker = rng.random(n)
    order = np.lexsort((tie_breaker, -score))
    selected = order[:m]
    events = y.sum()
    found = y[selected].sum()
    precision = found / m
    recall = found / events if events else np.nan
    prevalence = events / n
    lift = precision / prevalence if prevalence else np.nan
    return precision, recall, lift


def tie_robust_topk(y, score, k=0.1, n_boot=1000, seed=29):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        vals.append(topk_random_tie(y, score, k, rng))
    arr = np.asarray(vals, dtype=float)
    return {
        "precision_mean": float(np.nanmean(arr[:, 0])),
        "precision_ci_low": float(np.nanpercentile(arr[:, 0], 2.5)),
        "precision_ci_high": float(np.nanpercentile(arr[:, 0], 97.5)),
        "recall_mean": float(np.nanmean(arr[:, 1])),
        "recall_ci_low": float(np.nanpercentile(arr[:, 1], 2.5)),
        "recall_ci_high": float(np.nanpercentile(arr[:, 1], 97.5)),
        "lift_mean": float(np.nanmean(arr[:, 2])),
        "lift_ci_low": float(np.nanpercentile(arr[:, 2], 2.5)),
        "lift_ci_high": float(np.nanpercentile(arr[:, 2], 97.5)),
    }


def weighted_topk(y, score, w, k=0.1):
    order = np.argsort(-score, kind="mergesort")
    y_ord = y[order]
    w_ord = w[order]
    cutoff = np.nansum(w_ord) * k
    csum = np.cumsum(w_ord)
    selected = csum < cutoff
    if len(selected):
        first_over = int(np.argmax(csum >= cutoff)) if np.any(csum >= cutoff) else len(selected) - 1
        selected[first_over] = True
    selected_weight = np.nansum(w_ord[selected])
    weighted_events = np.nansum(y_ord * w_ord)
    found = np.nansum(y_ord[selected] * w_ord[selected])
    precision = found / selected_weight if selected_weight else np.nan
    recall = found / weighted_events if weighted_events else np.nan
    prevalence = weighted_events / np.nansum(w_ord) if np.nansum(w_ord) else np.nan
    lift = precision / prevalence if prevalence else np.nan
    return precision, recall, lift


def bootstrap_ci(y, score, other_score=None, k=0.1, n_boot=500, seed=7):
    rng = np.random.default_rng(seed)
    n = len(y)
    vals = []
    for _ in range(n_boot):
        idx = rng.choice(np.arange(n), size=n, replace=True)
        if other_score is None:
            p, r, l = topk(y[idx], score[idx], k)
            vals.append([p, r, l])
        else:
            p1, r1, l1 = topk(y[idx], score[idx], k)
            p0, r0, l0 = topk(y[idx], other_score[idx], k)
            vals.append([p1 - p0, r1 - r0, l1 - l0])
    arr = np.asarray(vals)
    return np.nanpercentile(arr, [2.5, 50, 97.5], axis=0)


def paired_bootstrap_metrics(y, score, other_score, k=0.1, n_boot=1000, seed=7):
    """Paired bootstrap differences for ranking and fixed-capacity metrics."""
    y = np.asarray(y)
    score = np.asarray(score)
    other_score = np.asarray(other_score)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.choice(np.arange(len(y)), size=len(y), replace=True)
        yb = y[idx]
        s1 = score[idx]
        s0 = other_score[idx]
        p1, r1, l1 = topk(yb, s1, k)
        p0, r0, l0 = topk(yb, s0, k)
        pr1 = average_precision_score(yb, s1)
        pr0 = average_precision_score(yb, s0)
        if np.unique(yb).size > 1:
            roc1 = roc_auc_score(yb, s1)
            roc0 = roc_auc_score(yb, s0)
        else:
            roc1 = roc0 = np.nan
        vals.append([p1-p0, r1-r0, l1-l0, pr1-pr0, roc1-roc0])
    arr = np.asarray(vals, dtype=float)
    return np.nanpercentile(arr, [2.5, 50, 97.5], axis=0)


def subgroup_metrics_under_global_queue(y, selected, subgroup, value):
    """Compute subgroup metrics after a queue is selected on the full sample."""
    y = np.asarray(y)
    selected = np.asarray(selected, dtype=bool)
    subgroup = np.asarray(subgroup)
    in_group = subgroup == value
    gy = y[in_group]
    gs = selected[in_group]
    if len(gy) == 0:
        return np.nan, np.nan, np.nan, np.nan
    selection_rate = float(gs.mean())
    precision = float(gy[gs].mean()) if gs.any() else np.nan
    events = gy == 1
    recall = float(gs[events].mean()) if events.any() else np.nan
    fnr = 1 - recall if not np.isnan(recall) else np.nan
    return selection_rate, precision, recall, fnr


def bootstrap_subgroup_global_topk_ci(y, score, subgroup, value, k=0.1, n_boot=500, seed=7):
    """Bootstrap subgroup metrics using a global top-k queue in every resample.

    Each replicate resamples the complete holdout, rebuilds its global top-k queue,
    and only then evaluates the requested subgroup. This keeps the confidence
    intervals aligned with the fixed-capacity estimand used for the point estimate.
    """
    y = np.asarray(y)
    score = np.asarray(score)
    subgroup = np.asarray(subgroup)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.choice(np.arange(len(y)), size=len(y), replace=True)
        selected = exact_topk_mask(score[idx], k)
        vals.append(subgroup_metrics_under_global_queue(y[idx], selected, subgroup[idx], value))
    arr = np.asarray(vals, dtype=float)
    return np.nanpercentile(arr, [2.5, 97.5], axis=0)


def make_preprocessor(feature_set):
    base_num = ["age_quant", "log_income", "commutetime_quant", "has_children_any"]
    base_cat = ["female_binary", "education_s", "work_industry", "occupation_clean"]
    gender_children_excluded_base_num = ["age_quant", "log_income", "commutetime_quant"]
    gender_children_excluded_base_cat = ["education_s", "work_industry", "occupation_clean"]
    strict_gender_children_excluded_base_num = ["age_quant", "commutetime_quant"]
    strict_gender_children_excluded_base_cat = ["education_s", "work_industry", "occupation_clean"]
    extra = {
        "hris": ([], []),
        "desired": (["desired_days"], []),
        "arrangement": (["desired_days", "planned_days"], []),
        "hris_plus_misfit": (["misfit_planned", "abs_misfit_planned"], ["under_remote_planned", "over_remote_planned"]),
        "minimal_voice": (["desired_days", "planned_days"], []),
        "signed_gap_only": (["misfit_planned"], []),
        "restricted": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
        "gender_children_excluded": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
        "gender_children_income_excluded": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
        "planned_only_restricted": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
        "planned_only_gender_children_excluded": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
    }[feature_set]
    if feature_set in {"gender_children_excluded", "planned_only_gender_children_excluded"}:
        num = gender_children_excluded_base_num + extra[0]
        cat = gender_children_excluded_base_cat + extra[1]
    elif feature_set == "gender_children_income_excluded":
        num = strict_gender_children_excluded_base_num + extra[0]
        cat = strict_gender_children_excluded_base_cat + extra[1]
    else:
        num = base_num + extra[0]
        cat = base_cat + extra[1]
    pre = ColumnTransformer(
        [
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=100))]), cat),
        ]
    )
    return pre, num + cat


def split_2025_train_2026q1_holdout(df):
    train = df[df["year"] == 2025].copy()
    test = df[(df["year"] == 2026) & (df["quarter"] == 1)].copy()
    assert len(train) > 0
    assert len(test) > 0
    assert train["year"].eq(2025).all()
    assert test["year"].eq(2026).all()
    assert test["quarter"].eq(1).all()
    return train, test


def fit_predict(train, test, feature_set, model_name, sample_weight=False, calibrate=None):
    pre, cols = make_preprocessor(feature_set)
    if model_name == "logit":
        base = LogisticRegression(max_iter=1000, class_weight="balanced")
    else:
        base = RandomForestClassifier(
            n_estimators=240,
            min_samples_leaf=20,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        )
    if calibrate:
        pipe = Pipeline([("pre", pre), ("model", base)])
        calibrated = CalibratedClassifierCV(pipe, method=calibrate, cv=3)
        calibrated.fit(train[cols], train["dissatisfied_broad"].astype(int))
        return calibrated.predict_proba(test[cols])[:, 1], cols, calibrated
    pipe = Pipeline([("pre", pre), ("model", base)])
    fit_params = {}
    if sample_weight and model_name in {"logit", "rf"}:
        fit_params["model__sample_weight"] = train["cratio100"]
    pipe.fit(train[cols], train["dissatisfied_broad"].astype(int), **fit_params)
    return pipe.predict_proba(test[cols])[:, 1], cols, pipe


def ece(y, score, bins=10):
    y = np.asarray(y, dtype=float)
    score = np.asarray(score, dtype=float)
    if np.nanmax(score) == np.nanmin(score):
        return float(abs(np.nanmean(score) - np.nanmean(y)))
    bin_ids = pd.cut(score, bins=np.linspace(0, 1, bins + 1), labels=False, include_lowest=True)
    tmp = pd.DataFrame({"y": y, "score": score, "bin": bin_ids}).dropna()
    total = len(tmp)
    if total == 0:
        return np.nan
    val = 0.0
    for _, g in tmp.groupby("bin"):
        val += len(g) / total * abs(g["score"].mean() - g["y"].mean())
    return float(val)


def calibration_intercept_slope(y, score):
    eps = 1e-6
    s = np.clip(score, eps, 1 - eps)
    logit_s = np.log(s / (1 - s))
    x = sm.add_constant(logit_s)
    try:
        res = sm.GLM(y, x, family=sm.families.Binomial()).fit()
        return float(res.params[0]), float(res.params[1])
    except Exception:
        return np.nan, np.nan


def weighted_models(df):
    d = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    controls = [
        "under_remote_planned",
        "over_remote_planned",
        "age_quant",
        "female_binary",
        "log_income",
        "commutetime_quant",
        "has_children_any",
    ]
    cats = ["education_s", "year"]
    dd = d[["dissatisfied_broad", "cratio100"] + controls + cats].dropna()
    x = pd.get_dummies(dd[controls + cats], columns=cats, drop_first=True, dummy_na=True).astype(float)
    x = sm.add_constant(x)
    y = dd["dissatisfied_broad"].astype(float)
    rows = []
    specs = [
        ("unweighted_logit", sm.GLM(y, x, family=sm.families.Binomial()).fit()),
        ("unweighted_lpm", sm.OLS(y, x).fit(cov_type="HC1")),
        ("weighted_lpm", sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="HC1")),
    ]
    for name, res in specs:
        for term in ["under_remote_planned", "over_remote_planned"]:
            est = res.params.get(term, np.nan)
            lo, hi = res.conf_int().loc[term].tolist()
            rows.append(
                {
                    "model": name,
                    "term": term,
                    "estimate": float(est),
                    "ci_low": float(lo),
                    "ci_high": float(hi),
                    "odds_ratio_if_logit": float(np.exp(est)) if "logit" in name else np.nan,
                    "or_ci_low": float(np.exp(lo)) if "logit" in name else np.nan,
                    "or_ci_high": float(np.exp(hi)) if "logit" in name else np.nan,
                    "n": len(dd),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "revision_weighted_unweighted_association.csv", index=False)


def association_model_grid(df):
    d = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    specs = [
        ("M1 unadjusted", [], []),
        ("M2 demographics family commute", ["age_quant", "female_binary", "commutetime_quant", "has_children_any"], []),
        (
            "M3 conventional characteristics",
            ["age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"],
            ["education_s", "work_industry", "occupation_clean", "region"],
        ),
        (
            "M4 conventional characteristics plus month FE",
            ["age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"],
            ["education_s", "work_industry", "occupation_clean", "region", "date"],
        ),
    ]
    rows = []
    for spec_name, numeric, categorical in specs:
        base_terms = ["under_remote_planned", "over_remote_planned"]
        cols = ["dissatisfied_broad", "cratio100"] + base_terms + numeric + categorical
        dd = d[cols].dropna().copy()
        if len(dd) < 500:
            continue
        x = pd.get_dummies(dd[base_terms + numeric + categorical], columns=categorical, drop_first=True, dummy_na=True).astype(float)
        x = sm.add_constant(x)
        y = dd["dissatisfied_broad"].astype(float)
        models = [
            ("unweighted_logit", sm.GLM(y, x, family=sm.families.Binomial()).fit()),
            ("unweighted_lpm", sm.OLS(y, x).fit(cov_type="HC1")),
            ("weighted_lpm", sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="HC1")),
        ]
        if spec_name == "M4 conventional characteristics plus month FE":
            models.append(("weighted_lpm_month_cluster", sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="cluster", cov_kwds={"groups": dd["date"]})))
        for model_name, res in models:
            for term in base_terms:
                est = res.params.get(term, np.nan)
                lo, hi = res.conf_int().loc[term].tolist()
                rows.append(
                    {
                        "specification": spec_name,
                        "model": model_name,
                        "term": term,
                        "estimate": est,
                        "ci_low": lo,
                        "ci_high": hi,
                        "odds_ratio": np.exp(est) if model_name == "unweighted_logit" else np.nan,
                        "or_ci_low": np.exp(lo) if model_name == "unweighted_logit" else np.nan,
                        "or_ci_high": np.exp(hi) if model_name == "unweighted_logit" else np.nan,
                        "n": len(dd),
                        "controls": "under/over remote misfit + " + (", ".join(numeric + categorical) if numeric or categorical else "no additional controls"),
                    }
                )
            contrast = pd.Series(0.0, index=res.params.index)
            contrast["under_remote_planned"] = 1.0
            contrast["over_remote_planned"] = -1.0
            test = res.t_test(contrast.to_numpy())
            lo, hi = np.asarray(test.conf_int()).reshape(-1)[:2]
            rows.append(
                {
                    "specification": spec_name,
                    "model": model_name,
                    "term": "under_minus_over",
                    "estimate": float(np.asarray(test.effect).squeeze()),
                    "ci_low": float(lo),
                    "ci_high": float(hi),
                    "odds_ratio": np.nan,
                    "or_ci_low": np.nan,
                    "or_ci_high": np.nan,
                    "p_value": float(np.asarray(test.pvalue).squeeze()),
                    "n": len(dd),
                    "controls": "Wald contrast: under-remote minus over-remote; " + (", ".join(numeric + categorical) if numeric or categorical else "no additional controls"),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "revision_association_model_grid.csv", index=False)


def imputed_association_robustness(df):
    d = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    controls_num = ["age_quant", "log_income", "commutetime_quant", "has_children_any"]
    controls_cat = ["female_binary", "education_s", "work_industry", "occupation_clean", "region", "date"]
    base = ["under_remote_planned", "over_remote_planned"]
    dd = d[["dissatisfied_broad", "cratio100"] + base + controls_num + controls_cat].copy()
    for c in controls_num:
        dd[c + "_missing"] = dd[c].isna().astype(float)
        dd[c] = dd[c].fillna(dd[c].median())
    for c in controls_cat:
        dd[c] = dd[c].astype("object").where(dd[c].notna(), "missing")
    x = pd.get_dummies(dd[base + controls_num + [c + "_missing" for c in controls_num] + controls_cat], columns=controls_cat, drop_first=True, dummy_na=False).astype(float)
    x = sm.add_constant(x)
    y = dd["dissatisfied_broad"].astype(float)
    rows = []
    for model_name, res in [
        ("imputed_unweighted_lpm", sm.OLS(y, x).fit(cov_type="HC1")),
        ("imputed_weighted_lpm", sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="HC1")),
        ("imputed_weighted_lpm_month_cluster", sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="cluster", cov_kwds={"groups": dd["date"]})),
    ]:
        for term in base:
            lo, hi = res.conf_int().loc[term].tolist()
            rows.append(
                {
                    "model": model_name,
                    "term": term,
                    "estimate": res.params[term],
                    "ci_low": lo,
                    "ci_high": hi,
                    "n": len(dd),
                    "controls": "conventional worker and job characteristics + month FE + numeric missingness indicators; categorical missingness as explicit level",
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "revision_imputed_association_robustness.csv", index=False)


def sample_construction_and_descriptives(df):
    rows = []
    d = df[df["year"].isin([2025, 2026])].copy()
    rows.append(
        {
            "panel": "A outcome and analytic sample construction",
            "step": "SWAA 2025-2026 loaded rows",
            "n_unweighted": len(d),
            "events": np.nan,
            "weighted_prevalence": np.nan,
            "unweighted_prevalence": np.nan,
            "purpose": "loaded rows before applying outcome availability",
        }
    )
    steps = [
        ("Nonmissing job dissatisfaction", d[d["dissatisfied_broad"].notna()].index, "outcome coverage"),
        ("Nonmissing desired WFH", d[d["dissatisfied_broad"].notna() & d["desired_days"].notna()].index, "outcome plus stated preference"),
        (
            "Nonmissing employer-planned WFH",
            d[d["dissatisfied_broad"].notna() & d["desired_days"].notna() & d["planned_days"].notna()].index,
            "planned-only descriptive and ranking eligible",
        ),
        (
            "Complete-case association sample, September-December 2025",
            d[
                d["dissatisfied_broad"].notna()
                & d["desired_days"].notna()
                & d["planned_days"].notna()
                & d[["age_quant", "income", "commutetime_quant", "female_binary", "education_s", "work_industry", "occupation_clean", "region"]].notna().all(axis=1)
            ].index,
            "fully adjusted association model; listwise deletion; September-December 2025",
        ),
    ]
    for step, idx, purpose in steps:
        g = d.loc[idx]
        rows.append(
            {
                "panel": "A outcome and analytic sample construction",
                "step": step,
                "n_unweighted": len(g),
                "events": int(g["dissatisfied_broad"].fillna(0).sum()),
                "weighted_prevalence": weighted_mean(g["dissatisfied_broad"], g["cratio100"]) if g["dissatisfied_broad"].notna().any() else np.nan,
                "unweighted_prevalence": float(g["dissatisfied_broad"].mean()) if g["dissatisfied_broad"].notna().any() else np.nan,
                "purpose": purpose,
            }
        )
    analytic = d[d["dissatisfied_broad"].notna() & d["misfit_planned"].notna()].copy()
    train_pred, test_pred = split_2025_train_2026q1_holdout(analytic)
    for g, label in [(train_pred, "2025 train analytic sample"), (test_pred, "January-February 2026 test analytic sample")]:
        rows.append(
            {
                "panel": "B ranking sample with imputation",
                "step": label,
                "n_unweighted": len(g),
                "events": int(g["dissatisfied_broad"].sum()),
                "weighted_prevalence": weighted_mean(g["dissatisfied_broad"], g["cratio100"]),
                "unweighted_prevalence": float(g["dissatisfied_broad"].mean()),
                "purpose": "temporal holdout ranking; covariate missingness handled by model pipeline imputation",
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "revision_sample_construction_flow.csv", index=False)

    analytic["misfit_group"] = np.select(
        [analytic["misfit_planned"] >= 2, analytic["misfit_planned"] <= -2],
        ["under_remote_strong", "over_remote_strong"],
        default="fit_or_weak",
    )
    desc_rows = []
    for group, g in analytic.groupby("misfit_group"):
        desc_rows.append(
            {
                "misfit_group": group,
                "n": len(g),
                "events": int(g["dissatisfied_broad"].sum()),
                "job_dissatisfaction_weighted": weighted_mean(g["dissatisfied_broad"], g["cratio100"]),
                "female_share_weighted": weighted_mean(g["female_binary"], g["cratio100"]),
                "children_share_weighted": weighted_mean(g["has_children_any"], g["cratio100"]),
                "income_mean_weighted": weighted_mean(g["income"], g["cratio100"]),
                "commute_mean_weighted": weighted_mean(g["commutetime_quant"], g["cratio100"]),
                "education_mean_weighted": weighted_mean(g["education_s"], g["cratio100"]),
                "desired_wfh_days_weighted": weighted_mean(g["desired_days"], g["cratio100"]),
                "planned_wfh_days_weighted": weighted_mean(g["planned_days"], g["cratio100"]),
                "current_wfh_days_weighted": weighted_mean(g["current_days"], g["cratio100"]),
                "remoteable_pct_weighted": weighted_mean(g["worktime_remoteable_pct"], g["cratio100"]),
            }
        )
    pd.DataFrame(desc_rows).to_csv(TABLES / "revision_table1_descriptives_by_misfit.csv", index=False)

    outcome = d[d["dissatisfied_broad"].notna()].copy()
    pred = analytic.copy()
    weight_rows = []
    association_cc_vars = ["age_quant", "income", "commutetime_quant", "female_binary", "education_s", "work_industry", "occupation_clean", "region"]
    association_cc = analytic[analytic[association_cc_vars].notna().all(axis=1)].copy()
    month_rows = []
    month_index = sorted(set(zip(analytic["year"].dropna().astype(int), analytic["month"].dropna().astype(int))))
    for year, month in month_index:
        eligible_month = analytic[(analytic["year"] == year) & (analytic["month"] == month)]
        cc_month = association_cc[(association_cc["year"] == year) & (association_cc["month"] == month)]
        commute_n = int(eligible_month["commutetime_quant"].notna().sum())
        month_rows.append(
            {
                "period": f"{year}-{month:02d}",
                "planned_outcome_eligible_n": len(eligible_month),
                "commute_time_nonmissing_n": commute_n,
                "complete_case_association_n": len(cc_month),
                "complete_case_retention": len(cc_month) / len(eligible_month) if len(eligible_month) else np.nan,
            }
        )
    pd.DataFrame(month_rows).to_csv(TABLES / "revision_association_sample_months.csv", index=False)
    for sample_name, g in {
        "full_swaa_2020_2026": df[df["cratio100"].notna()],
        "job_satisfaction_2025_2026": outcome,
        "ranking_eligible_reference_sample": analytic,
        "complete_case_association": association_cc,
        "ranking_train_2025": train_pred,
        "ranking_test_January-February 2026": test_pred,
    }.items():
        w = g["cratio100"].dropna().astype(float)
        if len(w) == 0:
            continue
        weight_rows.append(
            {
                "sample": sample_name,
                "n": len(w),
                "min_weight": w.min(),
                "p1_weight": w.quantile(0.01),
                "median_weight": w.median(),
                "p99_weight": w.quantile(0.99),
                "max_weight": w.max(),
                "effective_n": (w.sum() ** 2) / (w.pow(2).sum()) if w.pow(2).sum() else np.nan,
            }
        )
    pd.DataFrame(weight_rows).to_csv(TABLES / "revision_weight_distribution.csv", index=False)


def figure_source_tables(df):
    annual_rows = []
    d_all = df[df["year"].notna() & df["misfit_planned"].notna()].copy()
    for year, g in d_all.groupby("year"):
        annual_rows.append(
            {
                "year": int(year),
                "under_remote_strong": weighted_mean(g["under_remote_planned"], g["cratio100"]),
                "over_remote_strong": weighted_mean(g["over_remote_planned"], g["cratio100"]),
                "n": len(g),
            }
        )
    annual = pd.DataFrame(annual_rows).sort_values("year")
    annual.to_csv(TABLES / "revision_annual_misfit_trends.csv", index=False)

    job = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    job["misfit_type"] = np.select(
        [
            job["misfit_planned"] >= 2,
            job["misfit_planned"].between(1, 2, inclusive="left"),
            job["misfit_planned"] <= -2,
            job["misfit_planned"].between(-2, -1, inclusive="right"),
        ],
        ["under_remote_strong", "under_remote_weak", "over_remote_strong", "over_remote_weak"],
        default="fit_weak",
    )
    rows = []
    for mtype, g in job.groupby("misfit_type"):
        rows.append(
            {
                "outcome": "support_job_dissatisfaction",
                "misfit_type": mtype,
                "n": len(g),
                "events": int(g["dissatisfied_broad"].sum()),
                "prevalence_weighted": weighted_mean(g["dissatisfied_broad"], g["cratio100"]),
                "prevalence_unweighted": float(g["dissatisfied_broad"].mean()),
            }
        )
    job_table = pd.DataFrame(rows)
    job_table.to_csv(TABLES / "revision_job_dissatisfaction_by_misfit_type.csv", index=False)


def weighted_lpm_for_ref(df, ref="planned", threshold=2.0, weight_col="cratio100", cluster=False):
    d = df[df["dissatisfied_broad"].notna() & df[f"misfit_{ref}"].notna()].copy()
    d["under_tmp"] = (d[f"misfit_{ref}"] >= threshold).astype(float)
    d["over_tmp"] = (d[f"misfit_{ref}"] <= -threshold).astype(float)
    controls = ["under_tmp", "over_tmp", "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"]
    if ref == "combined":
        controls.append("reference_source_planned")
    cats = ["education_s", "work_industry", "occupation_clean", "region", "date"]
    dd = d[["dissatisfied_broad", weight_col, "date"] + controls + cats].dropna()
    x = pd.get_dummies(dd[controls + cats], columns=cats, drop_first=True, dummy_na=True).astype(float)
    x = sm.add_constant(x)
    y = dd["dissatisfied_broad"].astype(float)
    if cluster:
        return sm.WLS(y, x, weights=dd[weight_col]).fit(cov_type="cluster", cov_kwds={"groups": dd["date"]}), len(dd)
    return sm.WLS(y, x, weights=dd[weight_col]).fit(cov_type="HC1"), len(dd)


def robustness_coefficients(df):
    rows = []
    for ref in ["planned", "combined", "current"]:
        for threshold in [0.5, 1, 1.5, 2, 2.5, 3]:
            try:
                res, n = weighted_lpm_for_ref(df, ref, threshold)
            except Exception:
                continue
            for term in ["under_tmp", "over_tmp"]:
                lo, hi = res.conf_int().loc[term].tolist()
                rows.append(
                    {
                        "reference": ref,
                        "threshold_days": threshold,
                        "term": term.replace("_tmp", ""),
                        "weighted_lpm_estimate": res.params[term],
                        "ci_low": lo,
                        "ci_high": hi,
                        "n": n,
                    }
                )
    pd.DataFrame(rows).to_csv(TABLES / "revision_threshold_reference_lpm_robustness.csv", index=False)

    trim_rows = []
    for trim in [0, 0.01, 0.025, 0.05]:
        d = df.copy()
        w = d["cratio100"].copy()
        if trim > 0:
            lo, hi = w.quantile(trim), w.quantile(1 - trim)
            w = w.clip(lo, hi)
        d["weight_trimmed"] = w
        res, n = weighted_lpm_for_ref(d, "planned", 2.0, "weight_trimmed")
        for term in ["under_tmp", "over_tmp"]:
            lo, hi = res.conf_int().loc[term].tolist()
            trim_rows.append(
                {
                    "weight_trim": trim,
                    "term": term.replace("_tmp", ""),
                    "weighted_lpm_estimate": res.params[term],
                    "ci_low": lo,
                    "ci_high": hi,
                    "n": n,
                }
            )
    pd.DataFrame(trim_rows).to_csv(TABLES / "revision_weight_trimming_lpm.csv", index=False)

    cluster_rows = []
    base_terms = ["under_remote_planned", "over_remote_planned"]
    numeric = ["age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"]
    categorical = ["education_s", "work_industry", "occupation_clean", "region", "date"]
    cluster_sample = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    dd = cluster_sample[["dissatisfied_broad", "cratio100"] + base_terms + numeric + categorical].dropna().copy()
    x = pd.get_dummies(dd[base_terms + numeric + categorical], columns=categorical, drop_first=True, dummy_na=True).astype(float)
    x = sm.add_constant(x)
    y = dd["dissatisfied_broad"].astype(float)
    cluster_models = [
        ("heteroskedasticity_robust", np.nan, sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="HC1")),
        ("month_cluster_robust", dd["date"].nunique(), sm.WLS(y, x, weights=dd["cratio100"]).fit(cov_type="cluster", cov_kwds={"groups": dd["date"]})),
    ]
    for uncertainty, n_clusters, res in cluster_models:
        for term in base_terms:
            lo, hi = res.conf_int().loc[term].tolist()
            cluster_rows.append(
                {
                    "uncertainty": uncertainty,
                    "n_clusters": n_clusters,
                    "term": term.replace("_remote_planned", ""),
                    "weighted_lpm_estimate": res.params[term],
                    "ci_low": lo,
                    "ci_high": hi,
                    "n": len(dd),
                    "specification": "M4 conventional characteristics plus month FE",
                }
            )
    pd.DataFrame(cluster_rows).to_csv(TABLES / "revision_wave_clustered_lpm.csv", index=False)


def heterogeneity_interactions(df):
    d = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    d["low_income_ind"] = d["income_group_traincut"].astype(str).eq("low").astype(float)
    d["high_income_ind"] = d["income_group_traincut"].astype(str).eq("high").astype(float)
    moderators = {
        "high_commute": "high_commute_traincut",
        "children": "has_children_any",
        "female": "female_binary",
        "low_income": "low_income_ind",
    }
    rows = []
    for label, mod in moderators.items():
        cols = list(dict.fromkeys(["dissatisfied_broad", "cratio100", "under_remote_planned", mod, "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any", "education_s", "year"]))
        dd = d[cols].dropna().copy()
        dd["interaction"] = dd["under_remote_planned"] * dd[mod]
        controls = list(dict.fromkeys(["under_remote_planned", mod, "interaction", "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"]))
        x = pd.get_dummies(dd[controls + ["education_s", "year"]], columns=["education_s", "year"], drop_first=True, dummy_na=True).astype(float)
        x = sm.add_constant(x)
        res = sm.WLS(dd["dissatisfied_broad"].astype(float), x, weights=dd["cratio100"]).fit(cov_type="HC1")
        for term in ["under_remote_planned", mod, "interaction"]:
            lo, hi = res.conf_int().loc[term].tolist()
            rows.append(
                {
                    "moderator": label,
                    "term": term,
                    "estimate": res.params[term],
                    "ci_low": lo,
                    "ci_high": hi,
                    "n": len(dd),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "revision_heterogeneity_interactions.csv", index=False)


def outcome_and_misfit_robustness(df):
    rows = []
    for outcome in ["dissatisfied_broad", "dissatisfied_strict"]:
        for ref in ["combined", "planned", "current"]:
            for threshold in [0.5, 1, 1.5, 2, 2.5, 3]:
                d = df[df[outcome].notna() & df[f"misfit_{ref}"].notna()].copy()
                if len(d) < 500:
                    continue
                under = (d[f"misfit_{ref}"] >= threshold).astype(float)
                over = (d[f"misfit_{ref}"] <= -threshold).astype(float)
                rows.append(
                    {
                        "outcome": outcome,
                        "reference": ref,
                        "threshold_days": threshold,
                        "n": len(d),
                        "events": int(d[outcome].sum()),
                        "weighted_prevalence": weighted_mean(d[outcome], d["cratio100"]),
                        "under_share": weighted_mean(under, d["cratio100"]),
                        "over_share": weighted_mean(over, d["cratio100"]),
                        "prevalence_under": weighted_mean(d.loc[under == 1, outcome], d.loc[under == 1, "cratio100"]),
                        "prevalence_not_under": weighted_mean(d.loc[under == 0, outcome], d.loc[under == 0, "cratio100"]),
                        "prevalence_over": weighted_mean(d.loc[over == 1, outcome], d.loc[over == 1, "cratio100"]),
                        "prevalence_not_over": weighted_mean(d.loc[over == 0, outcome], d.loc[over == 0, "cratio100"]),
                    }
                )
    pd.DataFrame(rows).to_csv(TABLES / "revision_outcome_misfit_definition_robustness.csv", index=False)

    # Ordered satisfaction association via weighted LPM on 1-5 badness scale as directly interpretable robustness.
    d = df[df["satisfaction_score_high_bad"].notna() & df["misfit_planned"].notna()].copy()
    x = sm.add_constant(d[["under_remote_planned", "over_remote_planned", "age_quant", "female_binary", "log_income"]].dropna())
    y = d.loc[x.index, "satisfaction_score_high_bad"]
    w = d.loc[x.index, "cratio100"]
    res = sm.WLS(y, x, weights=w).fit(cov_type="HC1")
    ordered = []
    for term in ["under_remote_planned", "over_remote_planned"]:
        lo, hi = res.conf_int().loc[term].tolist()
        ordered.append({"outcome": "five_category_satisfaction_score_high_bad", "term": term, "estimate": res.params[term], "ci_low": lo, "ci_high": hi, "n": len(x)})
    pd.DataFrame(ordered).to_csv(TABLES / "revision_satisfaction_score_robustness.csv", index=False)


def missingness_model(df):
    rows = []
    scopes = [
        ("full_2020_2026_desired_wfh_sample", df[df["desired_days"].notna()].copy()),
        (
            "job_satisfaction_2025_2026_sample",
            df[df["desired_days"].notna() & df["dissatisfied_broad"].notna() & df["year"].isin([2025, 2026])].copy(),
        ),
    ]
    for scope, d in scopes:
        d["planned_missing"] = d["planned_days"].isna().astype(int)
        total_weight = d["cratio100"].sum()
        for flag, label in [(1, "planned_missing"), (0, "planned_observed")]:
            g = d[d["planned_missing"] == flag]
            rows.append(
                {
                    "scope": scope,
                    "group": label,
                    "n": len(g),
                    "weighted_share": float(g["cratio100"].sum() / total_weight) if total_weight else np.nan,
                    "age_mean": weighted_mean(g["age_quant"], g["cratio100"]),
                    "income_mean": weighted_mean(g["income"], g["cratio100"]),
                    "commute_mean": weighted_mean(g["commutetime_quant"], g["cratio100"]),
                    "children_share": weighted_mean(g["has_children_any"], g["cratio100"]),
                    "female_share": weighted_mean(g["female_binary"], g["cratio100"]),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES / "revision_planned_wfh_missingness_profile.csv", index=False)


def reference_construction_summary(df):
    rows = []
    for ref in ["combined", "planned", "current"]:
        d = df[df["dissatisfied_broad"].notna() & df[f"misfit_{ref}"].notna()].copy()
        if len(d) < 500:
            continue
        under = (d[f"misfit_{ref}"] >= 2).astype(float)
        try:
            res, n = weighted_lpm_for_ref(df, ref, 2.0)
            lo, hi = res.conf_int().loc["under_tmp"].tolist()
            est = res.params["under_tmp"]
        except Exception:
            n, lo, hi, est = len(d), np.nan, np.nan, np.nan
        rows.append(
            {
                "reference": ref,
                "n": len(d),
                "under_remote_prevalence_weighted": weighted_mean(under, d["cratio100"]),
                "dissatisfaction_prevalence_under_weighted": weighted_mean(d.loc[under == 1, "dissatisfied_broad"], d.loc[under == 1, "cratio100"]),
                "dissatisfaction_prevalence_not_under_weighted": weighted_mean(d.loc[under == 0, "dissatisfied_broad"], d.loc[under == 0, "cratio100"]),
                "weighted_lpm_under_estimate": est,
                "ci_low": lo,
                "ci_high": hi,
                "lpm_n": n,
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "revision_reference_construction_summary.csv", index=False)


def supplementary_outcomes_and_reverse_sensitivity(df):
    outcomes = [
        ("support_recent_quit", "Recent quit"),
        ("support_low_wellbeing", "Low wellbeing"),
        ("support_rto_resistance", "RTO resistance"),
        ("support_wfh_job_search", "WFH job-search preference"),
    ]
    rows = []
    for outcome, label in outcomes:
        d = df[df[outcome].notna() & df["misfit_planned"].notna()].copy()
        if len(d) < 500 or d[outcome].nunique() < 2:
            rows.append({"outcome": label, "status": "insufficient usable data", "n": len(d)})
            continue
        d["under_tmp"] = d["under_remote_planned"]
        controls = ["under_tmp", "over_remote_planned", "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"]
        dd = d[[outcome, "cratio100"] + controls + ["education_s", "year"]].dropna()
        x = pd.get_dummies(dd[controls + ["education_s", "year"]], columns=["education_s", "year"], drop_first=True, dummy_na=True).astype(float)
        x = sm.add_constant(x)
        res = sm.WLS(dd[outcome].astype(float), x, weights=dd["cratio100"]).fit(cov_type="HC1")
        lo, hi = res.conf_int().loc["under_tmp"].tolist()
        rows.append(
            {
                "outcome": label,
                "status": "ok",
                "years_available": ",".join(map(str, sorted(d["year"].dropna().astype(int).unique()))),
                "n": len(dd),
                "events": int(dd[outcome].sum()),
                "weighted_prevalence": weighted_mean(dd[outcome], dd["cratio100"]),
                "under_remote_weighted_lpm": res.params["under_tmp"],
                "ci_low": lo,
                "ci_high": hi,
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "revision_supplementary_outcomes_summary.csv", index=False)
    audit_rows = []
    interp = {
        "Recent quit": ("quit_qual == 1", "higher coded support proxy means respondent quit or voluntarily left a job", "ambiguous relative to under-remote dissatisfaction"),
        "Low wellbeing": ("subj_wellbeing <= 4", "higher coded support proxy means lower subjective wellbeing", "positive expected if under-remote misfit creates strain"),
        "RTO resistance": ("wbp_react_qual in [2, 3]", "higher coded support proxy means stronger resistance to full return-to-office", "positive expected if workers want more WFH, but period differs from main outcome"),
        "WFH job-search preference": ("labsearch_qual in [1, 2]", "higher coded support proxy means job search requires or prefers WFH availability", "positive expected if workers want more WFH, but high base rate may weaken signal"),
    }
    for row in rows:
        label = row["outcome"]
        ok = row.get("status") == "ok"
        estimate = row.get("under_remote_weighted_lpm", np.nan)
        observed = ("positive" if estimate > 0 else "negative") if ok else "not estimated"
        audit_rows.append(
            {
                "outcome": label,
                "status": row.get("status", "unknown"),
                "coding_rule": interp[label][0],
                "higher_value_means": interp[label][1],
                "expected_direction": interp[label][2],
                "observed_direction": observed,
                "under_remote_estimate": estimate,
                "interpretation": "coding retained; supplementary outcomes are heterogeneous and not combined into a single index" if ok else "coding documented; available observations were insufficient for the planned adjusted model",
            }
        )
    pd.DataFrame(audit_rows).to_csv(TABLES / "revision_outcome_coding_audit.csv", index=False)

    sens_rows = []
    base_df = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()
    specs = []
    specs.append(("broad_main", base_df, "dissatisfied_broad", []))
    specs.append(("strict_very_dissatisfied", base_df[base_df["dissatisfied_strict"].notna()].copy(), "dissatisfied_strict", []))
    if "support_wfh_job_search" in base_df:
        specs.append(
            (
                "exclude_wfh_job_search_preference_observed_no",
                base_df[base_df["support_wfh_job_search"].notna() & (base_df["support_wfh_job_search"] == 0)].copy(),
                "dissatisfied_broad",
                [],
            )
        )
    attitude_controls = [c for c in ["wfh_feel_quant", "wfh_feel_pr_bp_quant0", "wfh_feel_pr_hyb_quant0", "wfh_eff_COVID_quant"] if c in base_df.columns]
    if attitude_controls:
        specs.append(("control_wfh_attitude_valuation", base_df.copy(), "dissatisfied_broad", attitude_controls))
    for name, d, outcome, extra in specs:
        controls = ["under_remote_planned", "over_remote_planned", "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"] + extra
        dd = d[[outcome, "cratio100"] + controls + ["education_s", "year"]].dropna()
        if len(dd) < 500 or dd[outcome].nunique() < 2:
            sens_rows.append({"specification": name, "status": "insufficient usable data", "n": len(dd)})
            continue
        x = pd.get_dummies(dd[controls + ["education_s", "year"]], columns=["education_s", "year"], drop_first=True, dummy_na=True).astype(float)
        x = sm.add_constant(x)
        res = sm.WLS(dd[outcome].astype(float), x, weights=dd["cratio100"]).fit(cov_type="HC1")
        lo, hi = res.conf_int().loc["under_remote_planned"].tolist()
        sens_rows.append(
            {
                "specification": name,
                "status": "ok",
                "n": len(dd),
                "events": int(dd[outcome].sum()),
                "weighted_prevalence": weighted_mean(dd[outcome], dd["cratio100"]),
                "under_remote_estimate": res.params["under_remote_planned"],
                "ci_low": lo,
                "ci_high": hi,
                "extra_controls": ",".join(extra),
            }
        )
    pd.DataFrame(sens_rows).to_csv(TABLES / "revision_reverse_causality_sensitivity.csv", index=False)


def model_tuning_details():
    rows = [
        {"component": "numeric preprocessing", "setting": "median imputation followed by standard scaling"},
        {"component": "categorical preprocessing", "setting": "most-frequent imputation and one-hot encoding; rare levels pooled with min_frequency=100"},
        {"component": "logistic regression", "setting": "max_iter=1000; class_weight=balanced"},
        {"component": "random forest", "setting": "n_estimators=240; min_samples_leaf=20; max_features=sqrt; class_weight=balanced_subsample; random_state=42; n_jobs=1"},
        {"component": "calibrated RF", "setting": "calibration-only internal CV: CalibratedClassifierCV with 3-fold cross-validation inside 2025 training data; sigmoid for Platt, isotonic for isotonic calibration"},
        {"component": "tuning strategy", "setting": "conservative pre-specified hyperparameters; no 2026 test-set tuning"},
        {"component": "top-k ranking", "setting": "unweighted top-k by respondent count in main ranking metrics; weighted top-k reported as sensitivity"},
    ]
    pd.DataFrame(rows).to_csv(TABLES / "revision_model_tuning_details.csv", index=False)


def temporal_calibration_sensitivity(train_2025, test_2026q1, y_test):
    early = train_2025[train_2025["quarter"].isin([1, 2, 3])].copy()
    calibration = train_2025[train_2025["quarter"] == 4].copy()
    rows = []
    if len(early) < 200 or len(calibration) < 100 or calibration["dissatisfied_broad"].nunique() < 2:
        pd.DataFrame(
            [
                {
                    "protocol": "2025Q1-Q3 train, 2025Q4 calibrate, January-February 2026 test",
                    "model": "not_estimated",
                    "n_train": len(early),
                    "n_calibration": len(calibration),
                    "n_test": len(test_2026q1),
                    "note": "insufficient temporal calibration sample",
                }
            ]
        ).to_csv(TABLES / "revision_temporal_calibration_sensitivity.csv", index=False)
        return

    raw_cal, cols, fitted = fit_predict(early, calibration, "gender_children_excluded", "rf")
    raw_test = fitted.predict_proba(test_2026q1[cols])[:, 1]
    y_cal = calibration["dissatisfied_broad"].astype(int).to_numpy()
    rows.append(
        {
            "protocol": "2025Q1-Q3 train, no calibration, January-February 2026 test",
            "model": "raw_gender_children_excluded_rf_temporal_train",
            "n_train": len(early),
            "n_calibration": len(calibration),
            "n_test": len(test_2026q1),
            "roc_auc": roc_auc_score(y_test, raw_test),
            "pr_auc": average_precision_score(y_test, raw_test),
            "brier": brier_score_loss(y_test, raw_test),
            "ece": ece(y_test, raw_test),
            "precision_at_10": topk(y_test, raw_test, 0.1)[0],
            "recall_at_10": topk(y_test, raw_test, 0.1)[1],
            "lift_at_10": topk(y_test, raw_test, 0.1)[2],
            "note": "ranking model fit on earlier 2025 waves only",
        }
    )
    platt = LogisticRegression(max_iter=1000)
    platt.fit(raw_cal.reshape(-1, 1), y_cal)
    platt_test = platt.predict_proba(raw_test.reshape(-1, 1))[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(raw_cal, y_cal)
    iso_test = iso.predict(raw_test)
    for label, score in [("platt_gender_children_excluded_rf_temporal_calibration", platt_test), ("isotonic_gender_children_excluded_rf_temporal_calibration", iso_test)]:
        p, r, l = topk(y_test, score, 0.1)
        rows.append(
            {
                "protocol": "2025Q1-Q3 train, 2025Q4 calibrate, January-February 2026 test",
                "model": label,
                "n_train": len(early),
                "n_calibration": len(calibration),
                "n_test": len(test_2026q1),
                "roc_auc": roc_auc_score(y_test, score),
                "pr_auc": average_precision_score(y_test, score),
                "brier": brier_score_loss(y_test, score),
                "ece": ece(y_test, score),
                "precision_at_10": p,
                "recall_at_10": r,
                "lift_at_10": l,
                "note": "calibration map learned on later 2025 holdout wave, then applied unchanged to January-February 2026",
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "revision_temporal_calibration_sensitivity.csv", index=False)


def model_experiments(df):
    d = df[df["dissatisfied_broad"].notna() & df["year"].isin([2025, 2026]) & df["misfit_planned"].notna()].copy()
    train, test = split_2025_train_2026q1_holdout(d)
    commute_cutoff = train["commutetime_quant"].quantile(0.75)
    income_cutoff = train["income"].quantile(1 / 3)
    train["high_commute_traincut"] = np.where(train["commutetime_quant"].notna(), (train["commutetime_quant"] >= commute_cutoff).astype(float), 0.0)
    test["high_commute_traincut"] = np.where(test["commutetime_quant"].notna(), (test["commutetime_quant"] >= commute_cutoff).astype(float), 0.0)
    train["low_income_traincut"] = np.where(train["income"].notna(), (train["income"] <= income_cutoff).astype(float), 0.0)
    test["low_income_traincut"] = np.where(test["income"].notna(), (test["income"] <= income_cutoff).astype(float), 0.0)
    y = test["dissatisfied_broad"].astype(int).to_numpy()
    w = test["cratio100"].fillna(test["cratio100"].median()).to_numpy(float)
    rows = []
    scores = {}
    feature_sets = [
        "hris",
        "desired",
        "arrangement",
        "hris_plus_misfit",
        "minimal_voice",
        "signed_gap_only",
        "restricted",
        "gender_children_excluded",
        "gender_children_income_excluded",
    ]
    for fs in feature_sets:
        for model in ["logit", "rf"]:
            score, _, fitted = fit_predict(train, test, fs, model)
            p, r, l = topk(y, score, 0.1)
            ci = bootstrap_ci(y, score, k=0.1, n_boot=500)
            rows.append(
                {
                    "feature_set": fs,
                    "model": model,
                    "roc_auc": roc_auc_score(y, score),
                    "pr_auc": average_precision_score(y, score),
                    "brier": brier_score_loss(y, score),
                    "precision_at_10": p,
                    "recall_at_10": r,
                    "lift_at_10": l,
                    "precision10_ci_low": ci[0, 0],
                    "precision10_ci_high": ci[2, 0],
                    "lift10_ci_low": ci[0, 2],
                    "lift10_ci_high": ci[2, 2],
                }
            )
            scores[(fs, model)] = score
    pd.DataFrame(rows).to_csv(TABLES / "revision_ablation_temporal_performance.csv", index=False)

    # Strong rule-based benchmarks and paired bootstrap.
    absolute_gap = test["abs_misfit_planned"].fillna(0).to_numpy()
    under_directional = test["under_gap_planned"].fillna(0).to_numpy()
    additive = (
        test["under_gap_planned"].fillna(0) / 5
        + test["under_remote_planned"].fillna(0)
        + test["high_commute_traincut"].fillna(0)
        + test["has_children_any"].fillna(0)
        + test["low_income_traincut"].fillna(0)
    ).to_numpy()
    rules = {"absolute_gap_rule": absolute_gap, "under_remote_directional_rule": under_directional, "additive_support_rule": additive}
    pd.DataFrame(
        [
            {
                "rule": "absolute_gap_rule",
                "formula": "score = abs(desired WFH days - reference WFH days)",
                "role": "comparison rule; not the main theory-aligned rule",
                "cutoffs": "primary reference = employer-planned WFH days; combined planned-primary/current-WFH reference is reported as a sensitivity definition",
                "ranking": "descending score; deterministic top-k reported for the main table; random tie-breaking sensitivity reported separately",
                "designed_on": "defined from the 2025 training feature definitions and applied unchanged to 2026",
            },
            {
                "rule": "under_remote_directional_rule",
                "formula": "score = max(desired WFH days - reference WFH days, 0)",
                "role": "main directional rule aligned with the under-remote mechanism",
                "cutoffs": "under-remote gap measured in days per five-day week",
                "ranking": "descending score; deterministic top-k reported for the main table; random tie-breaking sensitivity reported separately",
                "designed_on": "defined from the 2025 training feature definitions and applied unchanged to 2026",
            },
            {
                "rule": "additive_support_rule",
                "formula": "score = under_remote_gap/5 + I(under_remote_gap >= 2 days) + I(commute >= 75th percentile) + I(any children in household) + I(income in bottom tercile)",
                "role": "interpretable ranking rule",
                "cutoffs": f"strong under-remote = 2+ days; high commute = 2025 training-sample 75th percentile of commute time ({commute_cutoff:.3f}); low income = 2025 training-sample bottom tercile ({income_cutoff:.3f}); has children = any child indicator from SWAA child variables",
                "ranking": "descending score; deterministic top-k reported for the main table; random tie-breaking sensitivity reported separately",
                "designed_on": "defined from the 2025 training feature definitions and applied unchanged to 2026",
            },
        ]
    ).to_csv(TABLES / "revision_rule_definitions.csv", index=False)
    rule_rows = []
    for name, score in rules.items():
        p, r, l = topk(y, score, 0.1)
        rule_rows.append(
            {
                "rule": name,
                "roc_auc": roc_auc_score(y, score),
                "pr_auc": average_precision_score(y, score),
                "precision_at_10": p,
                "recall_at_10": r,
                "lift_at_10": l,
            }
        )
    pd.DataFrame(rule_rows).to_csv(TABLES / "revision_strong_rule_baselines.csv", index=False)

    rf_score = scores[("gender_children_excluded", "rf")]
    full_rf_score = scores[("restricted", "rf")]

    # Clean planned-only main-model audit: no current-WFH feature and no
    # duplicate representation of employer-planned WFH.
    planned_pred = d[d["misfit_planned"].notna()].copy()
    planned_rows = []
    if len(planned_pred) > 1000:
        planned_train, planned_test = split_2025_train_2026q1_holdout(planned_pred)
        planned_y = planned_test["dissatisfied_broad"].astype(int).to_numpy()
        planned_rule = planned_test["under_gap_planned"].fillna(0).to_numpy()
        p, r, l = topk(planned_y, planned_rule, 0.10)
        planned_rows.append(
            {
                "model": "under_remote_planned_only_rule",
                "n_train": len(planned_train),
                "n_test": len(planned_test),
                "events_test": int(planned_y.sum()),
                "prevalence_test": float(planned_y.mean()),
                "roc_auc": roc_auc_score(planned_y, planned_rule),
                "pr_auc": average_precision_score(planned_y, planned_rule),
                "precision_at_10": p,
                "recall_at_10": r,
                "lift_at_10": l,
                "note": "clean planned-only main-model audit; observations with missing employer-planned WFH are excluded",
            }
        )
        for feature_set, label_prefix in [
            ("planned_only_gender_children_excluded", "gender_children_excluded"),
            ("planned_only_restricted", "full_restricted_comparison"),
        ]:
            for model in ["logit", "rf"]:
                planned_score, _, _ = fit_predict(planned_train, planned_test, feature_set, model)
                p, r, l = topk(planned_y, planned_score, 0.10)
                planned_rows.append(
                    {
                        "model": f"{label_prefix}_{model}_planned_only",
                        "n_train": len(planned_train),
                        "n_test": len(planned_test),
                        "events_test": int(planned_y.sum()),
                        "prevalence_test": float(planned_y.mean()),
                        "roc_auc": roc_auc_score(planned_y, planned_score),
                        "pr_auc": average_precision_score(planned_y, planned_score),
                        "precision_at_10": p,
                        "recall_at_10": r,
                        "lift_at_10": l,
                        "note": "clean planned-only model; gender-and-children-excluded model excludes gender and children, while the full restricted model is retained only for comparison",
                    }
                )
    pd.DataFrame(planned_rows).to_csv(TABLES / "revision_planned_only_ranking_validation.csv", index=False)

    # Month-by-month January-February 2026 validation checks that holdout performance is not driven by one month.
    monthly_rows = []
    test_month = test.copy()
    test_month["_rf_score"] = rf_score
    test_month["_rule_score"] = under_directional
    for month in [1, 2, 3]:
        g = test_month[test_month["month"] == month]
        if len(g) < 200 or g["dissatisfied_broad"].nunique() < 2:
            monthly_rows.append(
                {
                    "test_month": f"2026-{month:02d}",
                    "status": "no usable observations in analytic holdout",
                    "n": len(g),
                    "events": int(g["dissatisfied_broad"].fillna(0).sum()) if len(g) else 0,
                    "prevalence": np.nan,
                    "rf_roc_auc": np.nan,
                    "rf_pr_auc": np.nan,
                    "rf_precision_at_10": np.nan,
                    "rf_recall_at_10": np.nan,
                    "rf_lift_at_10": np.nan,
                    "rule_precision_at_10": np.nan,
                    "rule_recall_at_10": np.nan,
                    "rule_lift_at_10": np.nan,
                }
            )
            continue
        gy = g["dissatisfied_broad"].astype(int).to_numpy()
        rf_s = g["_rf_score"].to_numpy()
        rule_s = g["_rule_score"].to_numpy()
        rf_p, rf_r, rf_l = topk(gy, rf_s, 0.10)
        rule_p, rule_r, rule_l = topk(gy, rule_s, 0.10)
        monthly_rows.append(
            {
                "test_month": f"2026-{int(month):02d}",
                "status": "ok",
                "n": len(g),
                "events": int(gy.sum()),
                "prevalence": float(gy.mean()),
                "rf_roc_auc": roc_auc_score(gy, rf_s),
                "rf_pr_auc": average_precision_score(gy, rf_s),
                "rf_precision_at_10": rf_p,
                "rf_recall_at_10": rf_r,
                "rf_lift_at_10": rf_l,
                "rule_precision_at_10": rule_p,
                "rule_recall_at_10": rule_r,
                "rule_lift_at_10": rule_l,
            }
        )
    pd.DataFrame(monthly_rows).to_csv(TABLES / "revision_monthly_2026q1_validation.csv", index=False)

    # Training-weight sensitivity separates population-weighted fitting from the unweighted case-review target.
    weighted_train_rows = []
    for model in ["logit", "rf"]:
        for use_weight in [False, True]:
            wt_score, _, _ = fit_predict(train, test, "gender_children_excluded", model, sample_weight=use_weight)
            p, r, l = topk(y, wt_score, 0.10)
            weighted_train_rows.append(
                {
                    "model": model,
                    "training_weight": "survey_weighted" if use_weight else "unweighted",
                    "n_train": len(train),
                    "n_test": len(test),
                    "roc_auc": roc_auc_score(y, wt_score),
                    "pr_auc": average_precision_score(y, wt_score),
                    "brier": brier_score_loss(y, wt_score),
                    "precision_at_10": p,
                    "recall_at_10": r,
                    "lift_at_10": l,
                    "note": "top-k evaluation remains unweighted because the review queue treats one respondent as one case",
                }
            )
    pd.DataFrame(weighted_train_rows).to_csv(TABLES / "revision_weighted_training_sensitivity.csv", index=False)

    tie_rows = []
    for name, score in {**rules, "gender_children_excluded_rf": rf_score}.items():
        out = tie_robust_topk(y, score, 0.10, n_boot=1000)
        out.update({"method": name, "k": 0.10, "tie_method": "random tie-breaking over equal scores; 1,000 repetitions"})
        tie_rows.append(out)
    pd.DataFrame(tie_rows).to_csv(TABLES / "revision_tie_robust_topk.csv", index=False)

    paired = []
    comparisons = [
        ("arrangement_rf_minus_conventional_rf", scores[("arrangement", "rf")], scores[("hris", "rf")], "RQ2 incremental preference/arrangement information"),
        ("arrangement_logit_minus_conventional_logit", scores[("arrangement", "logit")], scores[("hris", "logit")], "logistic-regression sensitivity for RQ2"),
    ]
    comparisons.extend(
        (f"gender_children_excluded_rf_minus_{rule_name}", rf_score, rule_score, "RQ3 rule-model comparison")
        for rule_name, rule_score in rules.items()
    )
    for comparison, score1, score0, role in comparisons:
        ci = paired_bootstrap_metrics(y, score1, score0, k=0.1, n_boot=1000)
        p1, r1, l1 = topk(y, score1, 0.1)
        p0, r0, l0 = topk(y, score0, 0.1)
        paired.append(
            {
                "comparison": comparison,
                "role": role,
                "delta_precision10_point": p1-p0,
                "delta_precision10_low": ci[0, 0],
                "delta_precision10_median": ci[1, 0],
                "delta_precision10_high": ci[2, 0],
                "delta_recall10_point": r1-r0,
                "delta_recall10_low": ci[0, 1],
                "delta_recall10_median": ci[1, 1],
                "delta_recall10_high": ci[2, 1],
                "delta_lift10_point": l1-l0,
                "delta_lift10_low": ci[0, 2],
                "delta_lift10_median": ci[1, 2],
                "delta_lift10_high": ci[2, 2],
                "delta_pr_auc_point": average_precision_score(y, score1)-average_precision_score(y, score0),
                "delta_pr_auc_low": ci[0, 3],
                "delta_pr_auc_median": ci[1, 3],
                "delta_pr_auc_high": ci[2, 3],
                "delta_roc_auc_point": roc_auc_score(y, score1)-roc_auc_score(y, score0),
                "delta_roc_auc_low": ci[0, 4],
                "delta_roc_auc_median": ci[1, 4],
                "delta_roc_auc_high": ci[2, 4],
            }
        )
    pd.DataFrame(paired).to_csv(TABLES / "revision_paired_bootstrap_vs_rules.csv", index=False)

    # Calibration
    cal_rows = []
    base_rate = float(train["dissatisfied_broad"].mean())
    null_score = np.repeat(base_rate, len(y))
    cal_rows.append(
        {
            "model": "null_2025_base_rate",
            "roc_auc": 0.5,
            "pr_auc": float(y.mean()),
            "brier": brier_score_loss(y, null_score),
            "ece": ece(y, null_score),
            "calibration_intercept": np.nan,
            "calibration_slope": np.nan,
            "precision_at_10": float(y.mean()),
            "recall_at_10": 0.10,
            "lift_at_10": 1.0,
            "ece_bins": 10, "ece_binning": "equal-width probability bins",
            "calibration_protocol": "constant 2025 training prevalence applied to 2026",
        }
    )
    calibrated_scores = {}
    for label, calibrate in [("raw_gender_children_excluded_rf", None), ("platt_gender_children_excluded_rf", "sigmoid"), ("isotonic_gender_children_excluded_rf", "isotonic")]:
        score, _, _ = fit_predict(train, test, "gender_children_excluded", "rf", calibrate=calibrate)
        calibrated_scores[label] = score
        p, r, l = topk(y, score, 0.1)
        intercept, slope = calibration_intercept_slope(y, score)
        cal_rows.append(
            {
                "model": label,
                "roc_auc": roc_auc_score(y, score),
                "pr_auc": average_precision_score(y, score),
                "brier": brier_score_loss(y, score),
                "ece": ece(y, score),
                "calibration_intercept": intercept,
                "calibration_slope": slope,
                "precision_at_10": p,
                "recall_at_10": r,
                "lift_at_10": l,
                "ece_bins": 10, "ece_binning": "equal-width probability bins",
                "calibration_protocol": "raw RF fit on 2025 only" if calibrate is None else "calibration-only internal CV: mapping learned by 3-fold CV inside 2025 training data, then applied unchanged to January-February 2026",
            }
        )
    pd.DataFrame(cal_rows).to_csv(TABLES / "revision_calibration_correction.csv", index=False)

    calibration_bin_rows = []
    probability_scores = {
        "null_2025_base_rate": null_score,
        "raw_rf": calibrated_scores["raw_gender_children_excluded_rf"],
        "platt_rf": calibrated_scores["platt_gender_children_excluded_rf"],
        "isotonic_rf": calibrated_scores["isotonic_gender_children_excluded_rf"],
    }
    edges = np.linspace(0.0, 1.0, 11)
    for model_label, probability_score in probability_scores.items():
        probability_score = np.asarray(probability_score, dtype=float)
        bin_id = np.clip(np.digitize(probability_score, edges[1:-1], right=True), 0, 9)
        for b in range(10):
            mask = bin_id == b
            if not mask.any():
                continue
            calibration_bin_rows.append({
                "model": model_label,
                "bin": b + 1,
                "bin_lower": edges[b],
                "bin_upper": edges[b + 1],
                "n": int(mask.sum()),
                "mean_predicted": float(probability_score[mask].mean()),
                "observed_prevalence": float(y[mask].mean()),
            })
    pd.DataFrame(calibration_bin_rows).to_csv(TABLES / "revision_calibration_bins.csv", index=False)

    temporal_calibration_sensitivity(train, test, y)

    # Individual bootstrap for the ranking RF top-k metrics. Month-cluster bootstrap is not reported
    # because the declared holdout contains only January and February 2026.
    cluster_rows = []
    individual = bootstrap_ci(y, rf_score, k=0.1, n_boot=1000)
    cluster_rows.append(
        {
            "bootstrap_type": "individual",
            "precision10_low": individual[0, 0],
            "precision10_median": individual[1, 0],
            "precision10_high": individual[2, 0],
            "lift10_low": individual[0, 2],
            "lift10_median": individual[1, 2],
            "lift10_high": individual[2, 2],
        }
    )
    pd.DataFrame(cluster_rows).to_csv(TABLES / "revision_bootstrap_uncertainty_topk.csv", index=False)

    weighted_rows = []
    for name, score in {"absolute_gap_rule": absolute_gap, "under_remote_directional_rule": under_directional, "additive_support_rule": additive, "gender_children_excluded_rf": rf_score, "full_restricted_rf_comparison": full_rf_score}.items():
        for k in [0.05, 0.10, 0.20]:
            p, r, l = weighted_topk(y, score, w, k)
            weighted_rows.append({"method": name, "k": k, "weighted_precision_at_k": p, "weighted_recall_at_k": r, "weighted_lift_at_k": l})
    pd.DataFrame(weighted_rows).to_csv(TABLES / "revision_weighted_topk_sensitivity.csv", index=False)

    # Group-wise subgroup audit and calibration, connecting calibrated scores to subgroup metrics.
    def empirical_rule_probability(train_rule, train_y, test_rule):
        train_rule = np.asarray(train_rule, dtype=float)
        test_rule = np.asarray(test_rule, dtype=float)
        train_y = np.asarray(train_y, dtype=float)
        if np.nanmax(train_rule) == np.nanmin(train_rule):
            return np.repeat(np.nanmean(train_y), len(test_rule))
        qs = np.unique(np.nanquantile(train_rule, np.linspace(0, 1, 6)))
        if len(qs) < 3:
            qs = np.linspace(np.nanmin(train_rule), np.nanmax(train_rule), 6)
        qs[0] -= 1e-9
        qs[-1] += 1e-9
        train_bin = pd.cut(train_rule, bins=qs, labels=False, include_lowest=True)
        test_bin = pd.cut(test_rule, bins=qs, labels=False, include_lowest=True)
        means = pd.DataFrame({"bin": train_bin, "y": train_y}).groupby("bin")["y"].mean()
        base = float(np.nanmean(train_y))
        return np.asarray([means.get(b, base) if not pd.isna(b) else base for b in test_bin], dtype=float)

    train_under_directional = train["under_gap_planned"].fillna(0).to_numpy()
    directional_prob = empirical_rule_probability(train_under_directional, train["dissatisfied_broad"].astype(int).to_numpy(), under_directional)
    gf_scores = {
        "raw_gender_children_excluded_rf": calibrated_scores["raw_gender_children_excluded_rf"],
        "platt_gender_children_excluded_rf": calibrated_scores["platt_gender_children_excluded_rf"],
        "isotonic_gender_children_excluded_rf": calibrated_scores["isotonic_gender_children_excluded_rf"],
        "under_remote_directional_rule": under_directional,
    }
    gf_prob_scores = {
        "raw_gender_children_excluded_rf": calibrated_scores["raw_gender_children_excluded_rf"],
        "platt_gender_children_excluded_rf": calibrated_scores["platt_gender_children_excluded_rf"],
        "isotonic_gender_children_excluded_rf": calibrated_scores["isotonic_gender_children_excluded_rf"],
        "under_remote_directional_rule": directional_prob,
    }
    gf_rows = []
    gf_groups = ["gender_group", "has_children_any", "income_group_traincut", "education_s", "gender_children"]
    for model_name, rank_score in gf_scores.items():
        prob_score = gf_prob_scores[model_name]
        selected_all = exact_topk_mask(rank_score, 0.10)
        for group in gf_groups:
            for value, idx in test.groupby(group, dropna=False).groups.items():
                gpos = np.asarray(list(idx))
                loc = test.index.get_indexer(gpos)
                gy = y[loc]
                gs = rank_score[loc]
                gp = prob_score[loc]
                selected = selected_all[loc]
                if len(gy) < 100 or gy.sum() < 10:
                    continue
                precision = gy[selected].mean() if selected.any() else np.nan
                recall = selected[gy == 1].mean() if gy.sum() else np.nan
                gf_rows.append(
                    {
                        "group": group,
                        "value": str(value),
                        "model": model_name,
                        "n": len(gy),
                        "events": int(gy.sum()),
                        "selection_at_10": float(selected.mean()),
                        "precision_at_10": precision,
                        "recall_at_10": recall,
                        "fnr_at_10": 1 - recall if not np.isnan(recall) else np.nan,
                        "brier": brier_score_loss(gy, np.clip(gp, 0, 1)),
                        "ece": ece(gy, np.clip(gp, 0, 1)),
                    }
                )
    pd.DataFrame(gf_rows).to_csv(TABLES / "revision_groupwise_calibrated_subgroup_audit.csv", index=False)

    # Subgroup audit top-k at fixed review thresholds.
    fair_rows = []
    score = rf_score
    test2 = test.copy()
    test2["_score"] = score
    test2["_y"] = y
    groups = ["gender_group", "female_binary", "has_children_any", "income_group_traincut", "education_s", "gender_children"]
    for k in [0.05, 0.10, 0.20]:
        selected_global = exact_topk_mask(score, k)
        test2["_selected"] = selected_global.astype(int)
        for group in groups:
            for value, g in test2.groupby(group, dropna=False):
                if len(g) < 100 or g["_y"].sum() < 10:
                    continue
                selected = g["_selected"].to_numpy(dtype=bool)
                gy = g["_y"].to_numpy()
                selection_rate, precision, recall, fnr = subgroup_metrics_under_global_queue(
                    y, selected_global, test2[group].to_numpy(), value
                )
                seed_str = f"{group}_{value}_{k}"
                seed = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest()[:8], 16)
                ci_low, ci_high = bootstrap_subgroup_global_topk_ci(
                    y, score, test2[group].to_numpy(), value, k=k, n_boot=500, seed=seed
                )
                fair_rows.append(
                    {
                        "k": k,
                        "group": group,
                        "value": str(value),
                        "n": len(g),
                        "events": int(g["_y"].sum()),
                        "prevalence": g["_y"].mean(),
                        "selection_rate": selection_rate,
                        "precision_at_k": precision,
                        "precision_ci_low": ci_low[1],
                        "precision_ci_high": ci_high[1],
                        "recall_at_k": recall,
                        "recall_ci_low": ci_low[2],
                        "recall_ci_high": ci_high[2],
                        "fnr_at_k": fnr,
                        "fnr_ci_low": ci_low[3],
                        "fnr_ci_high": ci_high[3],
                        "roc_auc": roc_auc_score(g["_y"], g["_score"]) if g["_y"].nunique() == 2 else np.nan,
                        "pr_auc": average_precision_score(g["_y"], g["_score"]) if g["_y"].nunique() == 2 else np.nan,
                    }
                )
    pd.DataFrame(fair_rows).to_csv(TABLES / "revision_topk_subgroup_audit.csv", index=False)

    # Subgroup safeguard simulation: reserve part of the queue for within-subgroup ranking.
    def top_n_indices(score, n, eligible=None):
        score = np.asarray(score, dtype=float)
        eligible = np.ones(len(score), dtype=bool) if eligible is None else np.asarray(eligible, dtype=bool)
        idx = np.where(eligible)[0]
        if n <= 0 or len(idx) == 0:
            return np.array([], dtype=int)
        order = idx[np.argsort(-score[idx], kind="mergesort")]
        return order[: min(n, len(order))]

    def subgroup_metrics(frame, selected_mask, group):
        vals = []
        for value, g in frame.groupby(group, dropna=False):
            if len(g) < 100 or g["_y"].sum() < 10:
                continue
            loc = frame.index.get_indexer(g.index)
            selected = selected_mask[loc]
            gy = g["_y"].to_numpy()
            events = gy == 1
            recall = selected[events].mean() if events.any() else np.nan
            precision = gy[selected].mean() if selected.any() else np.nan
            vals.append({"value": str(value), "recall": recall, "fnr": 1 - recall if not np.isnan(recall) else np.nan, "precision": precision})
        return vals

    safeguard_rows = []
    capacity = max(1, int(math.ceil(len(test2) * 0.10)))
    global_n = int(math.floor(capacity * 0.80))
    reserve_n = capacity - global_n
    base_selected = np.zeros(len(test2), dtype=bool)
    base_selected[top_n_indices(test2["_score"].to_numpy(), capacity)] = True
    for group in ["gender_group", "has_children_any", "income_group_traincut", "education_s", "gender_children"]:
        base_group = subgroup_metrics(test2, base_selected, group)
        if base_group:
            safeguard_rows.append(
                {
                    "group": group,
                    "strategy": "global_top_10",
                    "review_capacity": 0.10,
                    "selected_n": int(base_selected.sum()),
                    "overall_precision": float(test2.loc[base_selected, "_y"].mean()),
                    "overall_recall": float(base_selected[test2["_y"].to_numpy() == 1].mean()),
                    "min_subgroup_recall": float(np.nanmin([v["recall"] for v in base_group])),
                    "max_subgroup_fnr": float(np.nanmax([v["fnr"] for v in base_group])),
                    "subgroup_recall_range": float(np.nanmax([v["recall"] for v in base_group]) - np.nanmin([v["recall"] for v in base_group])),
                    "note": "single global queue; subgroup metrics are diagnostic",
                }
            )
        selected = np.zeros(len(test2), dtype=bool)
        selected[top_n_indices(test2["_score"].to_numpy(), global_n)] = True
        group_sizes = test2[group].astype(str).value_counts(dropna=False)
        group_quota = (group_sizes / group_sizes.sum() * reserve_n).round().astype(int)
        while group_quota.sum() < reserve_n:
            group_quota.loc[group_sizes.idxmax()] += 1
        while group_quota.sum() > reserve_n:
            drop_label = group_quota[group_quota > 0].idxmax()
            group_quota.loc[drop_label] -= 1
        for value, quota in group_quota.items():
            eligible = (test2[group].astype(str).to_numpy() == value) & (~selected)
            selected[top_n_indices(test2["_score"].to_numpy(), int(quota), eligible)] = True
        sg = subgroup_metrics(test2, selected, group)
        if not sg:
            continue
        safeguard_rows.append(
            {
                "group": group,
                "strategy": "global_80pct_subgroup_reserved_20pct",
                "review_capacity": 0.10,
                "selected_n": int(selected.sum()),
                "overall_precision": float(test2.loc[selected, "_y"].mean()),
                "overall_recall": float(selected[test2["_y"].to_numpy() == 1].mean()),
                "min_subgroup_recall": float(np.nanmin([v["recall"] for v in sg])),
                "max_subgroup_fnr": float(np.nanmax([v["fnr"] for v in sg])),
                "subgroup_recall_range": float(np.nanmax([v["recall"] for v in sg]) - np.nanmin([v["recall"] for v in sg])),
                "note": "illustrative safeguard; not a implementation recommendation without legal and organizational review",
            }
        )
    pd.DataFrame(safeguard_rows).to_csv(TABLES / "revision_subgroup_safeguard_simulation.csv", index=False)

    # Practical ranking simulation per 1,000 holdout respondents.
    sim_rows = []
    prevalence = y.mean()
    methods = {
        "random": np.zeros_like(y, dtype=float),
        "absolute_gap_rule": absolute_gap,
        "under_remote_directional_rule": under_directional,
        "additive_support_rule": additive,
        "gender_children_excluded_rf": rf_score,
    }
    for k in [0.05, 0.10, 0.20]:
        for name, score in methods.items():
            if name == "random":
                precision = prevalence
                recall = k
            else:
                precision, recall, _ = topk(y, score, k)
            identified = precision * k * 1000
            random_identified = prevalence * k * 1000
            sim_rows.append(
                {
                    "method": name,
                    "review_capacity": k,
                    "reviewed_per_1000": int(k * 1000),
                    "expected_true_dissatisfied_identified": identified,
                    "additional_vs_random": identified - random_identified,
                    "approx_false_negatives_per_1000": prevalence * 1000 - identified,
                    "interpretability": "high" if name in ["random", "absolute_gap_rule", "under_remote_directional_rule", "additive_support_rule"] else "moderate",
                }
            )
    pd.DataFrame(sim_rows).to_csv(TABLES / "revision_practical_ranking_simulation.csv", index=False)

    # Permutation importance for the gender-and-children-excluded ranking RF.
    _, cols, model = fit_predict(train, test, "gender_children_excluded", "rf")
    result = permutation_importance(model, test[cols], y, n_repeats=8, random_state=42, scoring="average_precision")
    imp = pd.DataFrame({"feature": cols, "importance_mean": result.importances_mean, "importance_sd": result.importances_std})
    imp.sort_values("importance_mean", ascending=False).to_csv(TABLES / "revision_permutation_importance.csv", index=False)


def additional_sensitivity_tables(df):
    d = df[df["dissatisfied_broad"].notna() & df["misfit_planned"].notna()].copy()

    # Continuous directional misfit keeps the signed gap instead of imposing a strong-misfit threshold.
    cont = d[
        [
            "dissatisfied_broad",
            "cratio100",
            "under_gap_planned",
            "over_remote_planned",
            "age_quant",
            "female_binary",
            "log_income",
            "commutetime_quant",
            "has_children_any",
            "education_s",
            "date",
        ]
    ].dropna().copy()
    cont["over_gap_days"] = (-d.loc[cont.index, "misfit_planned"].clip(upper=0)).astype(float)
    x = pd.get_dummies(
        cont[
            [
                "under_gap_planned",
                "over_gap_days",
                "age_quant",
                "female_binary",
                "log_income",
                "commutetime_quant",
                "has_children_any",
                "education_s",
                "date",
            ]
        ],
        columns=["education_s", "date"],
        drop_first=True,
        dummy_na=True,
    ).astype(float)
    x = sm.add_constant(x)
    res = sm.WLS(cont["dissatisfied_broad"].astype(float), x, weights=cont["cratio100"]).fit(cov_type="HC1")
    rows = []
    for term in ["under_gap_planned", "over_gap_days"]:
        lo, hi = res.conf_int().loc[term].tolist()
        rows.append({"model": "continuous_gap_weighted_lpm", "term": term, "estimate": res.params[term], "ci_low": lo, "ci_high": hi, "n": len(cont)})
    pd.DataFrame(rows).to_csv(TABLES / "revision_continuous_misfit_lpm.csv", index=False)

    # Binned signed-gap robustness avoids assuming linearity and shows whether the two-day cutoff is arbitrary.
    bins = [-np.inf, -3, -2, -1, 1, 2, 3, np.inf]
    labels = ["<= -3", "-3 to < -2", "-2 to < -1", "-1 to < +1", "+1 to < +2", "+2 to < +3", ">= +3"]
    binned = d[d["year"].isin([2025, 2026]) & d["misfit_planned"].notna() & d["dissatisfied_broad"].notna()].copy()
    binned["misfit_bin"] = pd.cut(binned["misfit_planned"], bins=bins, labels=labels, right=False)
    bin_rows = []
    for bin_label, g in binned.groupby("misfit_bin", observed=True):
        bin_rows.append(
            {
                "misfit_bin_days": str(bin_label),
                "n": len(g),
                "events": int(g["dissatisfied_broad"].sum()),
                "weighted_prevalence": weighted_mean(g["dissatisfied_broad"], g["cratio100"]),
                "weighted_share": float(g["cratio100"].sum() / binned["cratio100"].sum()),
                "mean_misfit_days": weighted_mean(g["misfit_planned"], g["cratio100"]),
            }
        )
    pd.DataFrame(bin_rows).to_csv(TABLES / "revision_misfit_bin_prevalence.csv", index=False)

    # Remoteability moderation and stratification check.
    remote = d[
        [
            "dissatisfied_broad",
            "cratio100",
            "under_remote_planned",
            "over_remote_planned",
            "worktime_remoteable_pct",
            "occupation_remoteability_proxy",
            "age_quant",
            "female_binary",
            "log_income",
            "commutetime_quant",
            "has_children_any",
            "education_s",
            "work_industry",
            "occupation_clean",
            "date",
        ]
    ].dropna().copy()
    source_col = "worktime_remoteable_pct"
    remote_all = d[
        [
            "dissatisfied_broad",
            "cratio100",
            "under_remote_planned",
            "over_remote_planned",
            "worktime_remoteable_pct",
            "occupation_remoteability_proxy",
            "age_quant",
            "female_binary",
            "log_income",
            "commutetime_quant",
            "has_children_any",
            "education_s",
            "work_industry",
            "occupation_clean",
            "date",
        ]
    ].copy()
    if len(remote) < 500 or remote["worktime_remoteable_pct"].nunique() <= 2:
        source_col = "occupation_remoteability_proxy"
        remote = remote_all.dropna(subset=[
            "dissatisfied_broad",
            "cratio100",
            "under_remote_planned",
            "over_remote_planned",
            source_col,
            "age_quant",
            "female_binary",
            "log_income",
            "commutetime_quant",
            "has_children_any",
            "education_s",
            "work_industry",
            "occupation_clean",
            "date",
        ]).copy()
    remote_rows = []
    if len(remote) >= 500 and remote[source_col].nunique() > 2:
        remote["remoteable_scaled"] = remote[source_col] / (100 if remote[source_col].max() > 1.5 else 1)
        remote["under_x_remoteable"] = remote["under_remote_planned"] * remote["remoteable_scaled"]
        controls = [
            "under_remote_planned",
            "over_remote_planned",
            "remoteable_scaled",
            "under_x_remoteable",
            "age_quant",
            "female_binary",
            "log_income",
            "commutetime_quant",
            "has_children_any",
            "education_s",
            "work_industry",
            "occupation_clean",
            "date",
        ]
        x = pd.get_dummies(remote[controls], columns=["education_s", "work_industry", "occupation_clean", "date"], drop_first=True, dummy_na=True).astype(float)
        x = sm.add_constant(x)
        res = sm.WLS(remote["dissatisfied_broad"].astype(float), x, weights=remote["cratio100"]).fit(cov_type="HC1")
        for term in ["under_remote_planned", "over_remote_planned", "remoteable_scaled", "under_x_remoteable"]:
            lo, hi = res.conf_int().loc[term].tolist()
            remote_rows.append({"analysis": "interaction", "remoteability_source": source_col, "remoteability_group": "continuous", "term": term, "estimate": res.params[term], "ci_low": lo, "ci_high": hi, "n": len(remote)})
        remote["remoteability_group"] = pd.qcut(remote["remoteable_scaled"].rank(method="first"), 3, labels=["low", "middle", "high"])
        for grp, g in remote.groupby("remoteability_group", observed=True):
            if len(g) < 500 or g["dissatisfied_broad"].nunique() < 2:
                continue
            xg = pd.get_dummies(
                g[["under_remote_planned", "over_remote_planned", "age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any", "education_s", "date"]],
                columns=["education_s", "date"],
                drop_first=True,
                dummy_na=True,
            ).astype(float)
            xg = sm.add_constant(xg)
            rg = sm.WLS(g["dissatisfied_broad"].astype(float), xg, weights=g["cratio100"]).fit(cov_type="HC1")
            for term in ["under_remote_planned", "over_remote_planned"]:
                lo, hi = rg.conf_int().loc[term].tolist()
                remote_rows.append({"analysis": "stratified", "remoteability_source": source_col, "remoteability_group": str(grp), "term": term, "estimate": rg.params[term], "ci_low": lo, "ci_high": hi, "n": len(g)})
    else:
        remote_rows.append({"analysis": "remoteability", "remoteability_source": source_col, "remoteability_group": "not_estimated", "term": "insufficient_nonmissing_remoteability", "estimate": np.nan, "ci_low": np.nan, "ci_high": np.nan, "n": len(remote)})
    pd.DataFrame(remote_rows).to_csv(TABLES / "revision_remoteability_moderation.csv", index=False)

    # Inverse-probability weighted complete-case check: estimate complete-case membership from broad covariates.
    ipw_scope = d[d["year"].isin([2025, 2026])].copy()
    cc_vars = ["age_quant", "income", "commutetime_quant", "female_binary", "education_s", "work_industry", "occupation_clean", "region"]
    ipw_scope["complete_case"] = ipw_scope[cc_vars].notna().all(axis=1).astype(int)
    pred_cols = ["year", "desired_days", "planned_days", "under_remote_planned", "over_remote_planned"]
    tmp = ipw_scope[["complete_case", "cratio100"] + pred_cols].copy()
    for c in pred_cols:
        tmp[c] = tmp[c].fillna(tmp[c].median())
    sel_x = sm.add_constant(tmp[pred_cols].astype(float))
    sel = sm.GLM(tmp["complete_case"], sel_x, family=sm.families.Binomial()).fit()
    ipw_scope["cc_prob"] = np.clip(sel.predict(sel_x), 0.05, 0.95)
    cc = ipw_scope[ipw_scope["complete_case"] == 1].copy()
    cc["ipw_weight"] = cc["cratio100"] / cc["cc_prob"]
    ipw_res, ipw_n = weighted_lpm_for_ref(cc, "planned", 2.0, "ipw_weight")
    ipw_rows = []
    for term in ["under_tmp", "over_tmp"]:
        lo, hi = ipw_res.conf_int().loc[term].tolist()
        ipw_rows.append(
            {
                "model": "complete_case_inverse_probability_weighted_lpm",
                "term": term.replace("_tmp", ""),
                "estimate": ipw_res.params[term],
                "ci_low": lo,
                "ci_high": hi,
                "n": ipw_n,
                "selection_model": "complete-case probability estimated from year, WFH voice/reference variables, directional misfit, and planned-reference source",
            }
        )
    pd.DataFrame(ipw_rows).to_csv(TABLES / "revision_ipw_complete_case_sensitivity.csv", index=False)

    # Temporal stability is intentionally locked to the declared January-February 2026 temporal holdout.
    pred = d[d["year"].isin([2025, 2026])].copy()
    train, test = split_2025_train_2026q1_holdout(pred)
    score, _, _ = fit_predict(train, test, "gender_children_excluded", "rf")
    test["_score"] = score
    stability = []
    for q, g in test.groupby("quarter", dropna=False):
        if len(g) < 200 or g["dissatisfied_broad"].nunique() < 2:
            continue
        y = g["dissatisfied_broad"].astype(int).to_numpy()
        s = g["_score"].to_numpy()
        p, r, l = topk(y, s, 0.1)
        stability.append({"period": "January-February 2026", "n": len(g), "events": int(y.sum()), "roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s), "precision_at_10": p, "recall_at_10": r, "lift_at_10": l})
    pd.DataFrame(stability).to_csv(TABLES / "revision_temporal_stability_validation.csv", index=False)

    # Group-wise raw-score calibration diagnostics are retained as a descriptive fallback; calibrated subgroup audit is reported separately.
    cal_rows = []
    for group in ["gender_group", "income_group_traincut", "children_group", "education_s"]:
        for value, g in test.groupby(group, dropna=False):
            if len(g) < 100 or g["dissatisfied_broad"].sum() < 10:
                continue
            y = g["dissatisfied_broad"].astype(int).to_numpy()
            s = g["_score"].to_numpy()
            intercept, slope = calibration_intercept_slope(y, s)
            cal_rows.append({"group": group, "value": str(value), "n": len(g), "events": int(y.sum()), "brier": brier_score_loss(y, s), "ece": ece(y, s), "calibration_intercept": intercept, "calibration_slope": slope})
    pd.DataFrame(cal_rows).to_csv(TABLES / "revision_groupwise_calibration.csv", index=False)

    # Protected/proxy-variable ablations check whether ranking depends on socioeconomic or occupational proxies.
    def rf_score_custom(train_df, test_df, num_cols, cat_cols):
        pre = ColumnTransformer(
            [
                ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
                ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=100))]), cat_cols),
            ]
        )
        model = RandomForestClassifier(
            n_estimators=240,
            min_samples_leaf=20,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        )
        pipe = Pipeline([("pre", pre), ("model", model)])
        cols = num_cols + cat_cols
        pipe.fit(train_df[cols], train_df["dissatisfied_broad"].astype(int))
        return pipe.predict_proba(test_df[cols])[:, 1]

    y = test["dissatisfied_broad"].astype(int).to_numpy()
    full_restricted_score, _, _ = fit_predict(train, test, "restricted", "rf")
    specs = {
        "restricted_rf_full": (
            ["age_quant", "log_income", "commutetime_quant", "has_children_any", "desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["female_binary", "education_s", "work_industry", "occupation_clean", "under_remote_planned", "over_remote_planned"],
        ),
        "no_gender_children": (
            ["age_quant", "log_income", "commutetime_quant", "desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["education_s", "work_industry", "occupation_clean", "under_remote_planned", "over_remote_planned"],
        ),
        "no_sensitive_family_income": (
            ["age_quant", "commutetime_quant", "desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["education_s", "work_industry", "occupation_clean", "under_remote_planned", "over_remote_planned"],
        ),
        "no_socioeconomic": (
            ["age_quant", "has_children_any", "desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["female_binary", "work_industry", "occupation_clean", "under_remote_planned", "over_remote_planned"],
        ),
        "no_occupation_industry": (
            ["age_quant", "log_income", "commutetime_quant", "has_children_any", "desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["female_binary", "education_s", "under_remote_planned", "over_remote_planned"],
        ),
        "voice_only": (
            ["desired_days", "planned_days", "misfit_planned", "abs_misfit_planned"],
            ["under_remote_planned", "over_remote_planned"],
        ),
        "minimal_voice_hris_desired_reference": (
            ["age_quant", "log_income", "commutetime_quant", "has_children_any", "desired_days", "planned_days"],
            ["female_binary", "education_s", "work_industry", "occupation_clean"],
        ),
        "signed_gap_only_hris": (
            ["age_quant", "log_income", "commutetime_quant", "has_children_any", "misfit_planned"],
            ["female_binary", "education_s", "work_industry", "occupation_clean"],
        ),
    }
    ablation_rows = []
    for label, (num_cols, cat_cols) in specs.items():
        s = full_restricted_score if label == "restricted_rf_full" else rf_score_custom(train, test, num_cols, cat_cols)
        p, r, l = topk(y, s, 0.1)
        ablation_rows.append({"model": label, "feature_universe": "planned-only", "current_wfh_included": False, "roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s), "precision_at_10": p, "recall_at_10": r, "lift_at_10": l})
    p, r, l = topk(y, test["under_gap_planned"].fillna(0).to_numpy(), 0.10)
    directional_score = test["under_gap_planned"].fillna(0).to_numpy()
    ablation_rows.append(
        {
            "model": "directional_under_remote_rule",
            "feature_universe": "planned-only directional gap",
            "current_wfh_included": False,
            "roc_auc": roc_auc_score(y, directional_score),
            "pr_auc": average_precision_score(y, directional_score),
            "precision_at_10": p,
            "recall_at_10": r,
            "lift_at_10": l,
        }
    )
    ablation_df = pd.DataFrame(ablation_rows)
    ablation_df.to_csv(TABLES / "revision_sensitive_variable_ablation.csv", index=False)
    governance_roles = {
        "directional_under_remote_rule": "prespecified transparent benchmark at the evaluated 10% capacity; uses only the observed positive desired-minus-planned WFH gap",
        "signed_gap_only_hris": "conventional-characteristics comparison with the signed planned-reference gap",
        "restricted_rf_full": "broader planned-only random-forest comparison",
        "no_gender_children": "planned-only random forest excluding gender and children; primary complex-model comparison",
        "no_sensitive_family_income": "planned-only random forest excluding gender, children, and income; socioeconomic-proxy sensitivity",
    }
    governance = ablation_df[ablation_df["model"].isin(governance_roles)].copy()
    governance["governance_role"] = governance["model"].map(governance_roles)
    governance["preferred_transparent_benchmark"] = governance["model"].eq("directional_under_remote_rule")
    governance["primary_complex_model"] = governance["model"].eq("no_gender_children")
    governance["feature_universe"] = "planned-only; current WFH excluded"
    governance.to_csv(TABLES / "revision_ranking_model_governance_summary.csv", index=False)

    # Richer missingness sensitivity and inclusion balance.
    miss_scope = d[d["year"].isin([2025, 2026]) & d["dissatisfied_broad"].notna()].copy()
    miss_scope["complete_case"] = miss_scope[cc_vars].notna().all(axis=1).astype(int)
    balance_rows = []
    for status, g in miss_scope.groupby("complete_case"):
        label = "complete_case" if status == 1 else "excluded_in_complete_case"
        balance_rows.append(
            {
                "sample": label,
                "n": len(g),
                "weighted_dissatisfaction": weighted_mean(g["dissatisfied_broad"], g["cratio100"]),
                "weighted_under_remote": weighted_mean(g["under_remote_planned"], g["cratio100"]),
                "age_mean": weighted_mean(g["age_quant"], g["cratio100"]),
                "income_mean": weighted_mean(g["income"], g["cratio100"]),
                "commute_mean": weighted_mean(g["commutetime_quant"], g["cratio100"]),
                "female_share": weighted_mean(g["female_binary"], g["cratio100"]),
                "children_share": weighted_mean(g["has_children_any"], g["cratio100"]),
            }
        )
    pd.DataFrame(balance_rows).to_csv(TABLES / "revision_complete_case_balance.csv", index=False)

    # This model must be estimated before imposing the planned-only primary
    # analytic restriction; otherwise every retained observation has planned
    # WFH observed and the missingness outcome is constant.
    planned = df[
        df["year"].isin([2025, 2026])
        & df["dissatisfied_broad"].notna()
        & df["desired_days"].notna()
    ].copy()
    planned["planned_missing"] = planned["planned_days"].isna().astype(int)
    plan_cols = ["age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any", "desired_days", "year"]
    pp = planned[["planned_missing"] + plan_cols].copy()
    for col in plan_cols:
        pp[col] = pp[col].fillna(pp[col].median())
    plan_rows = []
    if len(pp) > 500 and pp["planned_missing"].nunique() == 2:
        px = sm.add_constant(pp[plan_cols].astype(float))
        pres = sm.GLM(pp["planned_missing"], px, family=sm.families.Binomial()).fit()
        for term in plan_cols:
            lo, hi = pres.conf_int().loc[term].tolist()
            plan_rows.append({"term": term, "logit_coef": pres.params[term], "ci_low": lo, "ci_high": hi, "odds_ratio": np.exp(pres.params[term]), "n": len(pp)})
    pd.DataFrame(plan_rows).to_csv(TABLES / "revision_planned_missingness_model.csv", index=False)


def response_surface_analysis(df):
    """Planned-only polynomial response-surface analysis of WFH preference fit."""
    required = [
        "dissatisfied_broad", "cratio100", "desired_days", "planned_days", "age_quant",
        "female_binary", "log_income", "commutetime_quant", "has_children_any",
        "education_s", "work_industry", "occupation_clean", "region", "date",
    ]
    d = df[required].dropna().copy()
    # A common center preserves the raw-scale congruence line desired == planned.
    common_center_days = 2.5
    d["desired_centered"] = d["desired_days"] - common_center_days
    d["planned_centered"] = d["planned_days"] - common_center_days
    d["desired_sq"] = d["desired_centered"] ** 2
    d["desired_x_planned"] = d["desired_centered"] * d["planned_centered"]
    d["planned_sq"] = d["planned_centered"] ** 2
    terms = ["desired_centered", "planned_centered", "desired_sq", "desired_x_planned", "planned_sq"]
    controls_num = ["age_quant", "female_binary", "log_income", "commutetime_quant", "has_children_any"]
    controls_cat = ["education_s", "work_industry", "occupation_clean", "region", "date"]
    x = pd.get_dummies(d[terms + controls_num + controls_cat], columns=controls_cat, drop_first=True, dummy_na=True).astype(float)
    x = sm.add_constant(x)
    res = sm.WLS(d["dissatisfied_broad"].astype(float), x, weights=d["cratio100"]).fit(cov_type="HC1")

    rows = []
    for term in terms:
        lo, hi = res.conf_int().loc[term].tolist()
        rows.append({"component": "coefficient", "term": term, "estimate": res.params[term], "ci_low": lo, "ci_high": hi, "p_value": res.pvalues[term], "n": len(d), "common_center_days": common_center_days})
    contrasts = {
        "congruence_line_slope": {"desired_centered": 1, "planned_centered": 1},
        "congruence_line_curvature": {"desired_sq": 1, "desired_x_planned": 1, "planned_sq": 1},
        "incongruence_line_slope": {"desired_centered": 1, "planned_centered": -1},
        "incongruence_line_curvature": {"desired_sq": 1, "desired_x_planned": -1, "planned_sq": 1},
    }
    for label, weights in contrasts.items():
        contrast = pd.Series(0.0, index=res.params.index)
        for term, weight in weights.items():
            contrast[term] = weight
        test = res.t_test(contrast.to_numpy())
        lo, hi = np.asarray(test.conf_int()).reshape(-1)[:2]
        rows.append({"component": "surface_test", "term": label, "estimate": float(np.asarray(test.effect).squeeze()), "ci_low": float(lo), "ci_high": float(hi), "p_value": float(np.asarray(test.pvalue).squeeze()), "n": len(d), "common_center_days": common_center_days})
    pd.DataFrame(rows).to_csv(TABLES / "revision_response_surface_planned_only.csv", index=False)

    desired_grid = np.linspace(d["desired_days"].quantile(0.01), d["desired_days"].quantile(0.99), 61)
    planned_grid = np.linspace(d["planned_days"].quantile(0.01), d["planned_days"].quantile(0.99), 61)
    means = x.drop(columns="const").mul(d["cratio100"], axis=0).sum().div(d["cratio100"].sum())
    grid_rows = []
    desired_mean = common_center_days
    planned_mean = common_center_days
    for desired in desired_grid:
        for planned in planned_grid:
            row = means.copy()
            dc = desired - desired_mean
            pc = planned - planned_mean
            row["desired_centered"] = dc
            row["planned_centered"] = pc
            row["desired_sq"] = dc ** 2
            row["desired_x_planned"] = dc * pc
            row["planned_sq"] = pc ** 2
            design = pd.concat([pd.Series({"const": 1.0}), row]).reindex(x.columns).fillna(0.0)
            grid_rows.append({"desired_wfh_days": desired, "planned_wfh_days": planned, "predicted_dissatisfaction": float(np.dot(design.to_numpy(), res.params.to_numpy()))})
    grid_df = pd.DataFrame(grid_rows)
    support = d[["desired_days", "planned_days"]].copy()
    support["desired_bin"] = (support["desired_days"] * 4).round() / 4
    support["planned_bin"] = (support["planned_days"] * 4).round() / 4
    support = support.groupby(["desired_bin", "planned_bin"], as_index=False).size().rename(columns={"size": "n"})
    support_lookup = {(float(r.desired_bin), float(r.planned_bin)): int(r.n) for r in support.itertuples(index=False)}
    grid_df["nearest_quarter_desired"] = (grid_df["desired_wfh_days"] * 4).round() / 4
    grid_df["nearest_quarter_planned"] = (grid_df["planned_wfh_days"] * 4).round() / 4
    grid_df["nearest_cell_n"] = [
        support_lookup.get((float(a), float(b)), 0)
        for a, b in zip(grid_df["nearest_quarter_desired"], grid_df["nearest_quarter_planned"])
    ]
    grid_df.to_csv(TABLES / "revision_response_surface_planned_only_grid.csv", index=False)
    support.to_csv(TABLES / "revision_response_surface_planned_only_support.csv", index=False)


def configure_paths(data_zip: str | None = None, out_dir: str | None = None) -> None:
    global ZIP_PATH, DELIVERY, TABLES, FIGURES
    if data_zip:
        ZIP_PATH = Path(data_zip).expanduser().resolve()
    if out_dir:
        DELIVERY = Path(out_dir).expanduser().resolve()
        TABLES = DELIVERY / "tables"
        FIGURES = DELIVERY / "figures"


def parse_args():
    parser = argparse.ArgumentParser(description="Regenerate SWAA hybrid-work misfit analysis tables.")
    parser.add_argument("--data-zip", default=None, help="Path to WFH_Code_and_Data_May2020_to_May2026.zip")
    parser.add_argument("--out", default=None, help="Project output directory containing tables/ and figures/. Defaults to the delivery folder.")
    return parser.parse_args()


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = read_data()
    # Revised coverage table with missing rates.
    cov_rows = []
    for outcome in ["dissatisfied_broad", "dissatisfied_strict"]:
        y = df[outcome]
        cov_rows.append(
            {
                "outcome": outcome,
                "years_available": ",".join(map(str, sorted(df.loc[y.notna(), "year"].dropna().astype(int).unique()))),
                "nonmissing_n": int(y.notna().sum()),
                "event_n": int(y.fillna(0).sum()),
                "unweighted_prevalence": float(y.mean()),
                "weighted_prevalence": weighted_mean(y, df["cratio100"]),
                "missing_rate": float(y.isna().mean()),
            }
        )
    pd.DataFrame(cov_rows).to_csv(TABLES / "revision_outcome_coverage_main.csv", index=False)
    sample_construction_and_descriptives(df)
    figure_source_tables(df)
    model_tuning_details()
    weighted_models(df)
    association_model_grid(df)
    imputed_association_robustness(df)
    outcome_and_misfit_robustness(df)
    robustness_coefficients(df)
    heterogeneity_interactions(df)
    missingness_model(df)
    reference_construction_summary(df)
    supplementary_outcomes_and_reverse_sensitivity(df)
    model_experiments(df)
    additional_sensitivity_tables(df)
    response_surface_analysis(df)
    print("Revision-grade analysis tables written to tables/")


if __name__ == "__main__":
    args = parse_args()
    configure_paths(args.data_zip, args.out)
    main()
