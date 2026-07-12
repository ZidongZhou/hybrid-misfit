from __future__ import annotations

import shutil

import csv
import math
import re
from pathlib import Path

from artifact_tool import Workbook, SpreadsheetFile

ROOT=Path(__file__).resolve().parents[1]
TABLES=ROOT/'tables'
MAN=ROOT/'manuscript'
OUT=ROOT/'Supplementary_Tables.xlsx'

FILES=[
("Table S1. Sample construction flow","revision_sample_construction_flow.csv","S01_SampleFlow"),
("Table S2. Weighted descriptive statistics by misfit group","revision_table1_descriptives_by_misfit.csv","S02_Descriptives"),
("Table S3. Full weighted/unweighted association models","revision_weighted_unweighted_association.csv","S03_AssocBasic"),
("Table S4. Association model grid with controls","revision_association_model_grid.csv","S04_AssocControls"),
("Table S5. Single-imputation and missingness-indicator association robustness","revision_imputed_association_robustness.csv","S05_ImputedAssoc"),
("Table S6. Threshold and reference-arrangement robustness","revision_threshold_reference_lpm_robustness.csv","S06_ThresholdRef"),
("Table S7. Reference construction summary","revision_reference_construction_summary.csv","S07_Reference"),
("Table S8. Outcome-definition and misfit-definition robustness","revision_outcome_misfit_definition_robustness.csv","S08_OutcomeMisfit"),
("Table S9. Five-category satisfaction-score robustness","revision_satisfaction_score_robustness.csv","S09_SatisfactionScore"),
("Table S10. Planned-WFH missingness profile","revision_planned_wfh_missingness_profile.csv","S10_Missingness"),
("Table S11. Weight-trimming robustness","revision_weight_trimming_lpm.csv","S11_WeightTrim"),
("Table S12. Month-cluster robust uncertainty for the M4 model","revision_wave_clustered_lpm.csv","S12_ClusterSE"),
("Table S13. Temporal-holdout feature ablation","revision_ablation_temporal_performance.csv","S13_Validation"),
("Table S14. Directly interpretable rule definitions","revision_rule_definitions.csv","S14_Rules"),
("Table S15. Paired-bootstrap temporal-holdout comparisons","revision_paired_bootstrap_vs_rules.csv","S15_PairedBoot"),
("Table S16. Calibration correction metrics","revision_calibration_correction.csv","S16_Calibration"),
("Table S17. Top-k subgroup audit","revision_topk_subgroup_audit.csv","S17_SubgroupAudit"),
("Table S18. Weighted top-k sensitivity","revision_weighted_topk_sensitivity.csv","S18_WeightedTopK"),
("Table S19. Heterogeneity interaction results","revision_heterogeneity_interactions.csv","S19_Heterogeneity"),
("Table S20. Reverse-causality sensitivity checks","revision_reverse_causality_sensitivity.csv","S20_Reverse"),
("Table S21. Supplementary dissatisfaction-related outcomes","revision_supplementary_outcomes_summary.csv","S21_ProxyOutcomes"),
("Table S22. Outcome coding audit","revision_outcome_coding_audit.csv","S22_CodingAudit"),
("Table S23. Model tuning and preprocessing details","revision_model_tuning_details.csv","S23_Tuning"),
("Table S24. Practical ranking simulation","revision_practical_ranking_simulation.csv","S24_RankSim"),
("Table S25. Permutation importance","revision_permutation_importance.csv","S25_Importance"),
("Table S26. Continuous directional-misfit robustness","revision_continuous_misfit_lpm.csv","S26_Continuous"),
("Table S27. Complete-case inverse-probability weighting sensitivity","revision_ipw_complete_case_sensitivity.csv","S27_IPW"),
("Table S28. January-February 2026 temporal-holdout check","revision_temporal_stability_validation.csv","S28_Stability"),
("Table S29. Raw-score group-wise calibration diagnostics","revision_groupwise_calibration.csv","S29_GroupCal"),
("Table S30. Planned-only feature ablation","revision_sensitive_variable_ablation.csv","S30_FeatureAblation"),
("Table S31. Tie-robust top-k sensitivity","revision_tie_robust_topk.csv","S31_TieRobust"),
("Table S32. Calibrated subgroup audit","revision_groupwise_calibrated_subgroup_audit.csv","S32_CalFair"),
("Table S33. Remoteability moderation and stratification","revision_remoteability_moderation.csv","S33_Remoteability"),
("Table S34. Signed misfit-bin prevalence","revision_misfit_bin_prevalence.csv","S34_MisfitBins"),
("Table S35. Complete-case balance","revision_complete_case_balance.csv","S35_CCBalance"),
("Table S36. Planned-WFH missingness model","revision_planned_missingness_model.csv","S36_PlannedMiss"),
("Table S37. SWAA weight distribution by analytic sample","revision_weight_distribution.csv","S37_Weights"),
("Table S38. Planned-only ranking validation","revision_planned_only_ranking_validation.csv","S38_PlannedRank"),
("Table S39. Month-by-month January-February 2026 validation","revision_monthly_2026q1_validation.csv","S39_JanFeb"),
("Table S40. Weighted-training sensitivity","revision_weighted_training_sensitivity.csv","S40_WtdTraining"),
("Table S41. Ranking-model governance summary","revision_ranking_model_governance_summary.csv","S41_ModelGovernance"),
("Table S42. Subgroup safeguard simulation","revision_subgroup_safeguard_simulation.csv","S42_Safeguard"),
("Table S43. Planned-only polynomial response-surface analysis","revision_response_surface_planned_only.csv","S43_ResponseSurface"),
("Additional Table A1. Temporal calibration sensitivity","revision_temporal_calibration_sensitivity.csv","A1_TemporalCal"),
("Additional Table A2. Calibration-bin source data","revision_calibration_bins.csv","A2_CalibrationBins"),
("Additional Table A3. Primary association sample by survey month","revision_association_sample_months.csv","A3_AssocMonths"),
]

def parse(v):
    s=v.strip()
    if s=='' or s.lower()=='nan': return None
    if re.fullmatch(r'[-+]?\d+',s):
        try:return int(s)
        except:return s
    if re.fullmatch(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?',s):
        try:
            x=float(s); return None if math.isnan(x) else x
        except:return s
    if s.lower() in {'true','false'}: return s.lower()=='true'
    return s

def col_name(n):
    out=''
    while n:
        n,rem=divmod(n-1,26); out=chr(65+rem)+out
    return out

def build():
    wb=Workbook.create()
    idx=wb.worksheets.add('Index')
    idx_rows=[['Supplementary item','CSV source','Worksheet']]+[[a,b,c] for a,b,c in FILES]
    idx.get_range_by_indexes(0,0,len(idx_rows),3).values=idx_rows
    idx.get_range('A1:C1').format={'fill':'#1F4E78','font':{'bold':True,'color':'#FFFFFF'},'wrap_text':True,'vertical_alignment':'center'}
    idx.get_range(f'A1:C{len(idx_rows)}').format.borders={'top':{'style':'thin','color':'#D9E2F3'},'bottom':{'style':'thin','color':'#D9E2F3'},'left':{'style':'thin','color':'#D9E2F3'},'right':{'style':'thin','color':'#D9E2F3'}}
    idx.get_range(f'A2:C{len(idx_rows)}').format.wrap_text=True
    idx.get_range('A:A').format.column_width=80; idx.get_range('B:B').format.column_width=55; idx.get_range('C:C').format.column_width=30
    idx.freeze_panes.freeze_rows(1); idx.tables.add(f'A1:C{len(idx_rows)}',True,'SupplementaryIndex')
    for i,(title,filename,sheet_name) in enumerate(FILES,1):
        path=TABLES/filename
        if not path.exists(): raise FileNotFoundError(path)
        with path.open(encoding='utf-8-sig',newline='') as f: raw=list(csv.reader(f))
        rows=[[parse(x) for x in r] for r in raw]
        nrows=len(rows); ncols=max((len(r) for r in rows), default=0)
        if ncols == 0:
            rows=[["No data rows generated"]]; nrows=1; ncols=1
        rows=[r+[None]*(ncols-len(r)) for r in rows]
        sh=wb.worksheets.add(sheet_name[:31])
        sh.get_range_by_indexes(0,0,nrows,ncols).values=rows
        last=col_name(ncols)
        sh.get_range(f'A1:{last}1').format={'fill':'#1F4E78','font':{'bold':True,'color':'#FFFFFF'},'wrap_text':True,'vertical_alignment':'center','horizontal_alignment':'center'}
        sh.get_range(f'A1:{last}{nrows}').format.borders={'top':{'style':'thin','color':'#D9E2F3'},'bottom':{'style':'thin','color':'#D9E2F3'},'left':{'style':'thin','color':'#D9E2F3'},'right':{'style':'thin','color':'#D9E2F3'}}
        if nrows>1: sh.get_range(f'A2:{last}{nrows}').format.wrap_text=True
        for c in range(ncols):
            vals=[rows[r][c] for r in range(1,min(nrows,151)) if rows[r][c] is not None]
            max_len=max([len(str(rows[0][c]))]+[len(str(v)) for v in vals])
            width=min(max(max_len+2,10),38)
            sh.get_range_by_indexes(0,c,nrows,1).format.column_width=width
            nums=[v for v in vals if isinstance(v,(int,float)) and not isinstance(v,bool)]
            if vals and len(nums)==len(vals):
                fmt='0' if all(isinstance(v,int) for v in nums) else '0.000'
                if nrows>1: sh.get_range_by_indexes(1,c,nrows-1,1).format.number_format=fmt
        sh.freeze_panes.freeze_rows(1)
        sh.tables.add(f'A1:{last}{nrows}',True,f'T{i:02d}_{re.sub(r"[^A-Za-z0-9]","",sheet_name)[:20]}')
    SpreadsheetFile.export_xlsx(wb).save(str(OUT))
    MAN.mkdir(exist_ok=True)
    shutil.copyfile(OUT, MAN/'Supplementary_Tables_FINAL.xlsx')
    check=wb.inspect({'kind':'table','range':'S41_ModelGovernance!A1:J10','include':'values,formulas','table_max_rows':10,'table_max_cols':10})
    print(check.ndjson)
    errors=wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':100},'summary':'formula error scan'})
    print(errors.ndjson)
    print(OUT.relative_to(ROOT))

if __name__=='__main__': build()
