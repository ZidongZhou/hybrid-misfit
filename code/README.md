# SWAA directional hybrid-work misfit analysis

This directory contains the analysis and document-generation pipeline for the manuscript **Directional Hybrid-Work Misfit and Job Dissatisfaction: Implications for Socially Sustainable Hybrid-Work Design**.

## Standard reproduction command

```bash
python code/run_all.py --data-zip /path/to/WFH_Code_and_Data_May2020_to_May2026.zip
```

The command verifies the raw archive hash, starts from empty generated-output folders, and creates:

- all analysis CSV tables;
- five main figures and two supplementary figures as 600 dpi PNG, PDF, and SVG files;
- the MDPI-template manuscript, supplementary file, and cover letter;
- output and reproducibility manifests;
- a clean-run log with stage runtimes and key results;
- automated-test output.

The standard command is a complete submission rebuild. It generates the formatted `Supplementary_Tables.xlsx` workbook with `artifact_tool` and fails clearly if that formatter is unavailable. For a scientific-output-only run, the workbook may be skipped explicitly:

```bash
python code/run_all.py --data-zip /path/to/archive.zip --skip-workbook
```

## Data

The expected archive contains `WFHdata_May26.csv` from the earnings-restricted June 2026 SWAA release available to registered researchers. Researchers can request access to the anonymized microdata by creating an account at `https://wfhresearch.com/data/`. The archive itself is not included. `DATA_MANIFEST.md` records the expected SHA256 value and internal files.

## Main samples

- The fully adjusted association model uses 15,355 complete cases from September–December 2025.
- These cases represent 41.0% of the 37,434 observations with job dissatisfaction, desired WFH, and employer-planned WFH observed from July 2025 through February 2026.
- Ranking models train on July–December 2025 and use January–February 2026 as a temporal holdout.

## Main model identity

The main complex comparison is the planned-only `gender_children_excluded` random forest. It excludes gender, children, and current WFH. The `gender_children_income_excluded` model is a socioeconomic-proxy sensitivity. At the evaluated 10% capacity, the under-remote directional rule is the prespecified transparent benchmark.

## Numerical reproducibility

Random seeds are fixed, random forests use one thread, and the runner sets common BLAS/OpenMP thread counts to one. Outputs are expected to reproduce to the reported precision. Last-decimal floating-point differences can still occur across Python, BLAS, or operating-system builds; the manuscript conclusions do not depend on those differences.

## Tests

```bash
python code/run_tests.py --outputs-root .
```

Tests cover the September–December 2025 complete-case window, temporal splitting, leakage controls, exact top-k capacity, planned/combined/current reference separation, primary association values, the rule-versus-model comparison, paired-bootstrap uncertainty, the single prespecified benchmark, model identity across S30/S41, response-surface centering, satisfaction-score naming, manuscript synchronization, and output completeness.
