from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Restrict numerical libraries to one thread so repeated runs are stable to the
# reported precision across ordinary desktop environments.
for _key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_key, "1")

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SHA256='AEB9F0CFBA280BD8595F1D93897851FADE9274FB5483E99FB8A4F92E5F72734E'

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def _display_arg(value: str) -> str:
    s = str(value)
    try:
        p = Path(s)
        if p.is_absolute():
            if p == ROOT or ROOT in p.parents:
                return f"project/{p.relative_to(ROOT).as_posix()}"
            return p.name
    except Exception:
        pass
    return s

def run_stage(name:str,cmd:list[str],capture=False):
    print(f'\n=== {name} ===',flush=True); print('Running:',' '.join(_display_arg(x) for x in cmd),flush=True)
    t=time.perf_counter()
    if capture:
        p=subprocess.run(cmd,text=True,capture_output=True)
        if p.stdout: print(p.stdout,flush=True)
        if p.stderr: print(p.stderr,file=sys.stderr,flush=True)
        if p.returncode: raise subprocess.CalledProcessError(p.returncode,cmd,p.stdout,p.stderr)
        output=(p.stdout or '')+(p.stderr or '')
    else:
        subprocess.run(cmd,check=True); output=''
    elapsed=time.perf_counter()-t
    print(f'{name} completed in {elapsed:.1f} seconds.',flush=True)
    return elapsed,output

def clean_generated_outputs():
    for name in ['tables','figures','manuscript']:
        p=ROOT/name
        if p.exists(): shutil.rmtree(p)
    for name in ['Supplementary_Tables.xlsx','outputs_manifest.csv','reproducibility_manifest.csv','reproducibility_log.txt']:
        p=ROOT/name
        if p.exists(): p.unlink()

def write_csv_readme():
    t=ROOT/'tables'; t.mkdir(exist_ok=True)
    text='''CSV archive guide

Main manuscript source files:
- revision_annual_misfit_trends.csv -> Figure 1
- revision_job_dissatisfaction_by_misfit_type.csv -> Figure 2
- revision_ablation_temporal_performance.csv -> Table 4 and Figure 3
- revision_strong_rule_baselines.csv -> Table 5
- revision_calibration_correction.csv and revision_calibration_bins.csv -> Figure 4
- revision_topk_subgroup_audit.csv -> Figure 5
- revision_misfit_bin_prevalence.csv -> Figure S1
- revision_response_surface_planned_only_grid.csv and revision_response_surface_planned_only_support.csv -> Figure S2

Supplementary spreadsheet mapping is listed in Supplementary_Tables.xlsx and Supplementary_Material_FINAL.docx.
The main complex comparison is the planned-only reduced-feature random forest. Current WFH is excluded from every model in Supplementary Table S30. The under-remote directional rule is the prespecified transparent benchmark at the evaluated 10% capacity in Supplementary Table S41.
'''
    (t/'CSV_README.txt').write_text(text,encoding='utf-8')

def write_outputs_manifest():
    rows=[]
    for folder in [ROOT/'tables',ROOT/'figures',ROOT/'manuscript']:
        if folder.exists():
            for p in sorted(folder.rglob('*')):
                if p.is_file(): rows.append({'relative_path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)})
    p=ROOT/'Supplementary_Tables.xlsx'
    if p.exists(): rows.append({'relative_path':p.name,'bytes':p.stat().st_size,'sha256':sha256(p)})
    with (ROOT/'outputs_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256']); w.writeheader(); w.writerows(rows)

def write_repro_manifest():
    rows=[]
    for folder in ['code','tests','documentation','tables','figures','manuscript','template']:
        path=ROOT/folder
        if path.exists():
            for p in sorted(path.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc': rows.append({'relative_path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)})
    for name in ['DATA_MANIFEST.md','README_FINAL.md','CITATION.cff','LICENSE','environment.yml','outputs_manifest.csv','reproducibility_log.txt','Supplementary_Tables.xlsx','clean_run_stdout.log','clean_run.exit']:
        p=ROOT/name
        if p.exists(): rows.append({'relative_path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p)})
    with (ROOT/'reproducibility_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256']); w.writeheader(); w.writerows(sorted(rows,key=lambda x:x['relative_path']))

def scalar(table,where,col):
    d=pd.read_csv(ROOT/'tables'/table)
    mask=pd.Series(True,index=d.index)
    for k,v in where.items(): mask &= d[k].eq(v)
    return d.loc[mask,col].iloc[0]

def detailed_log(data_zip:Path,timings:dict,test_output:str,started:str,workbook_status:str):
    perf=pd.read_csv(ROOT/'tables'/'revision_ablation_temporal_performance.csv')
    rf=perf[(perf.feature_set=='gender_children_excluded')&(perf.model=='rf')].iloc[0]
    rules=pd.read_csv(ROOT/'tables'/'revision_strong_rule_baselines.csv'); rule=rules[rules.rule=='under_remote_directional_rule'].iloc[0]
    boot=pd.read_csv(ROOT/'tables'/'revision_paired_bootstrap_vs_rules.csv'); b=boot[boot.comparison.str.contains('under_remote_directional_rule')].iloc[0]
    assoc=pd.read_csv(ROOT/'tables'/'revision_association_model_grid.csv'); m4=assoc[(assoc.specification=='M4 conventional characteristics plus month FE')&(assoc.model=='weighted_lpm')]
    under=m4[m4.term=='under_remote_planned'].iloc[0]; contrast=m4[m4.term=='under_minus_over'].iloc[0]
    rsa=pd.read_csv(ROOT/'tables'/'revision_response_surface_planned_only.csv')
    congr=rsa[(rsa.component=='surface_test')&(rsa.term=='congruence_line_curvature')].iloc[0]
    inc=rsa[(rsa.component=='surface_test')&(rsa.term=='incongruence_line_slope')].iloc[0]
    gov=pd.read_csv(ROOT/'tables'/'revision_ranking_model_governance_summary.csv')
    sat=pd.read_csv(ROOT/'tables'/'revision_satisfaction_score_robustness.csv')
    months=pd.read_csv(ROOT/'tables'/'revision_association_sample_months.csv')
    cc_months=months.loc[months.complete_case_association_n.gt(0),'period'].tolist()
    lines=[
        f'clean_run_started_utc: {started}',f'clean_run_finished_utc: {datetime.now(timezone.utc).isoformat()}',
        'clean_run_status: SUCCESS','clean_directory_policy: generated tables, figures, documents, workbook, logs, and manifests were deleted before execution',
        f'python: {sys.version.replace(chr(10)," ")}',f'platform: {platform.platform()}',f'data_zip_name: {data_zip.name}',
        f'data_zip_bytes: {data_zip.stat().st_size}',f'data_zip_sha256: {sha256(data_zip)}',f'data_hash_matches_manifest: {sha256(data_zip).upper()==EXPECTED_SHA256}',
    ]
    for name,seconds in timings.items(): lines.append(f'stage_seconds_{name}: {seconds:.3f}')
    for pkg in ['pandas','numpy','sklearn','statsmodels','matplotlib','docx']:
        try:
            m=importlib.import_module(pkg); lines.append(f'package_{pkg}: {getattr(m,"__version__","installed")}')
        except Exception as e: lines.append(f'package_{pkg}: unavailable ({e})')
    lines += [
        f'primary_under_remote_estimate: {under.estimate}',f'primary_under_remote_ci: [{under.ci_low}, {under.ci_high}]',
        f'under_minus_over_contrast: {contrast.estimate}',f'under_minus_over_ci: [{contrast.ci_low}, {contrast.ci_high}]',
        f'directional_rule_precision10: {rule.precision_at_10}',f'gender_children_excluded_rf_precision10: {rf.precision_at_10}',
        f'rf_minus_rule_point_difference: {rf.precision_at_10-rule.precision_at_10}',
        f'paired_bootstrap_delta_precision10: [{b.delta_precision10_low}, {b.delta_precision10_median}, {b.delta_precision10_high}]',
        f'paired_bootstrap_interval_includes_zero: {b.delta_precision10_low<0<b.delta_precision10_high}',
        f'response_surface_common_center_days: {rsa.common_center_days.dropna().iloc[0]}',
        f'incongruence_line_slope: {inc.estimate}',f'congruence_line_curvature: {congr.estimate}',
        f'governance_preferred_benchmarks: {int(gov.preferred_transparent_benchmark.sum())}',
        f'governance_preferred_model: {gov.loc[gov.preferred_transparent_benchmark,"model"].iloc[0]}',
        f'satisfaction_score_rows: {len(sat)}',f'primary_association_complete_case_months: {cc_months}',f'supplementary_workbook_status: {workbook_status}',
        'core_pipeline_generated_analysis_csv_png_docx_and_tests: true','raw_data_redistributed: false',
        'automated_test_output_begin',test_output.strip(),'automated_test_output_end',
    ]
    (ROOT/'reproducibility_log.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-zip',required=True); ap.add_argument('--no-hash-check',action='store_true'); ap.add_argument('--reuse-analysis',action='store_true'); ap.add_argument('--skip-workbook',action='store_true',help='Skip the formatted XLSX build; all analysis CSV outputs are still generated, but the run is not a complete submission rebuild.'); args=ap.parse_args()
    data_zip=Path(args.data_zip).expanduser().resolve()
    if not data_zip.exists(): raise SystemExit(f'Raw SWAA zip not found: {data_zip}')
    actual=sha256(data_zip).upper()
    if actual!=EXPECTED_SHA256 and not args.no_hash_check: raise SystemExit(f'Data SHA256 mismatch. Expected {EXPECTED_SHA256}; actual {actual}')
    started=datetime.now(timezone.utc).isoformat(); timings={}
    if not args.reuse_analysis:
        clean_generated_outputs(); timings['analysis'],_=run_stage('Analysis',[sys.executable,str(ROOT/'code'/'revision_grade_analysis.py'),'--data-zip',str(data_zip)])
    else:
        if not (ROOT/'tables').exists(): raise SystemExit('--reuse-analysis requires tables')
    timings['figures'],_=run_stage('Figures',[sys.executable,str(ROOT/'code'/'make_submission_figures.py')])
    timings['documents'],_=run_stage('MDPI documents',[sys.executable,str(ROOT/'code'/'generate_submission_documents.py')])
    if args.skip_workbook:
        workbook_status='skipped_by_flag'
        timings['workbook']=0.0
        print('Supplementary workbook step skipped by explicit --skip-workbook flag. This is a scientific-output run, not a complete submission rebuild.',flush=True)
    else:
        if importlib.util.find_spec('artifact_tool') is None:
            raise SystemExit('artifact_tool is required for a complete submission rebuild. Install the formatter or use --skip-workbook for scientific outputs only.')
        timings['workbook'],_=run_stage('Supplementary workbook',[sys.executable,str(ROOT/'code'/'build_supplementary_workbook.py')])
        workbook_status='generated'
    write_csv_readme(); write_outputs_manifest()
    timings['tests'],test_output=run_stage('Automated tests',[sys.executable,str(ROOT/'code'/'run_tests.py'),'--outputs-root',str(ROOT)],capture=True)
    detailed_log(data_zip,timings,test_output,started,workbook_status)
    write_outputs_manifest(); write_repro_manifest()
    print('\nFull clean reproduction pipeline completed successfully.',flush=True)

if __name__=='__main__': main()
