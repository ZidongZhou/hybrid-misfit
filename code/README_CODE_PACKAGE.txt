SWAA analysis code package

Primary association model:
- 15,355 complete cases from September-December 2025.
- These are 41.0% of 37,434 records with observed job dissatisfaction and employer-planned WFH.

Temporal ranking evaluation:
- Train: July-December 2025.
- Holdout: January-February 2026.
- Preferred transparent benchmark: positive desired-minus-planned WFH gap at the evaluated 10% capacity.
- Primary complex-model comparison: planned-only random forest excluding gender and children.

Run:
  python code/run_all.py --data-zip /path/to/verified_swaa_archive.zip

The standard complete-submission pipeline generates the formatted supplementary workbook with artifact_tool and fails clearly when the formatter is unavailable. Use --skip-workbook only for a scientific-output-only run; that mode is not the final submission build.
