# Figure Legends

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
