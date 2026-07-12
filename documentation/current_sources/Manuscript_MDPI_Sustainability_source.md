# Directional Hybrid-Work Misfit and Job Dissatisfaction: Implications for Socially Sustainable Hybrid-Work Design

Type of the Paper: Article

Zidong Zhou 1,2, Rudzi Munap 2,* and Yue Meng 3

1 School of Digital Arts, Jiangsu Vocational Institute of Commerce, Nanjing 211168, Jiangsu, China

2 Faculty of Business, UNITAR International University, Petaling Jaya 47301, Selangor, Malaysia

3 School of Economics and Management, Southeast University, Nanjing 210096, Jiangsu, China

Correspondence: corresponding.rudzi@unitar.my

## Abstract

Hybrid-work arrangements may fit employees differently even when they provide the same number of remote days. Using the U.S. Survey of Working Arrangements and Attitudes, this study compared under-remote misfit, where desired work-from-home (WFH) days exceed employer plans, with over-remote misfit. Association models used 15,355 complete cases from September–December 2025; ranking models trained on July–December 2025 were tested in January–February 2026. Compared with respondents who were aligned or had a gap below two days, strong under-remote misfit was associated with an adjusted 11.5-percentage-point higher probability of job dissatisfaction (95% CI: 9.5–13.4); the under–over contrast was 7.9 percentage points (95% CI: 3.1–12.7). [[ABSTRACT_RANKING_RESULTS]] Raw random-forest scores were poorly calibrated and should not be interpreted as probabilities. Preference–plan alignment added later-period ranking information, but the association analysis was contemporaneous and the ranking models were not deployment-ready.

Keywords: hybrid work; work from home; social sustainability; sustainable work design; person–environment fit; job dissatisfaction; people analytics

## 1. Introduction

Socially sustainable employment requires work arrangements that support decent work and employee wellbeing [1,2]. Employee voice is relevant because formally identical policies may correspond differently to employees’ preferences and constraints [3,4]. Survey evidence shows persistent differences between the amount of WFH employees prefer and the amount employers plan to provide [5,6]. Sustainable human resource management emphasizes the long-term effects of employment practices on employees as well as organizations [7–9], while work-design research shows that effective arrangements depend on how demands, resources, autonomy, and coordination are configured [10–12].

Experimental, meta-analytic, and field evidence indicates that remote work can improve satisfaction, retention, or performance under some conditions [13–16]. These outcomes also depend on task characteristics, organizational implementation, worker selection, and labor-market context [10,17–19]. WFH intensity alone therefore provides an incomplete description of hybrid-work design. The same planned arrangement may fit employees differently depending on their preferences, job demands, and nonwork constraints.

Preference–plan alignment makes this heterogeneity observable. Under-remote misfit occurs when desired WFH exceeds the employer’s plan; over-remote misfit occurs when the employer’s plan exceeds the employee’s desired amount. Prior studies have examined mismatch between WFH need and access or between preferred and actual telework frequency [20–23]. Their findings indicate that mismatch matters, but the direction of the less favorable mismatch varies across outcomes, countries, age groups, and pandemic-period conditions. It remains unclear whether under-remote and over-remote employer plans have different adjusted associations with job dissatisfaction in the post-pandemic U.S. context.

The study also asks whether desired and planned WFH improve ranking in a later survey period beyond conventional worker and job characteristics. This predictive task is distinct from the association analysis: it evaluates whether the measures help prioritize optional follow-up at a fixed capacity, not why dissatisfaction occurs. A transparent directional rule is compared with logistic regression and random forests so that any gain from added complexity can be judged against a directly interpretable benchmark.

This study extends prior telework-mismatch research in three ways. First, it uses employer-planned rather than actual WFH as the organizational reference and formally compares the adjusted associations of under-remote and over-remote misfit with job dissatisfaction. Second, it examines these associations in a large U.S. repeated cross-section and evaluates their robustness across alternative definitions and specifications. Third, it tests whether preference and arrangement measures improve temporal-holdout ranking and benchmarks fitted models against transparent directional rules. The analysis addresses four research questions:

RQ1. Do strong under-remote and strong over-remote misfit differ in their adjusted associations with job dissatisfaction?

RQ2. Do preference and arrangement measures improve temporal-holdout ranking beyond conventional worker and job characteristics?

RQ3. Does a reduced-feature random forest improve fixed-capacity ranking over the under-remote directional rule?

RQ4. How does one global top-k queue distribute selection and missed cases across reporting groups?

## 2. Literature Review

### 2.1. Hybrid-Work Preferences and Sustainable Work Design

Sustainable HRM research treats employee wellbeing as an organizational outcome that should be considered over time rather than as a short-term input to performance [7–9]. Work-design research adds that autonomy, task structure, social support, coordination, and technological conditions jointly shape employees’ experience of work [10–12]. These perspectives are relevant to hybrid work because the number of remote days changes several resources and demands at once.

Remote work can reduce commuting and increase schedule control, but it can also make communication, mentoring, and coordination more difficult. The balance depends on work design and implementation [10,14,15]. Consequently, average WFH intensity cannot indicate whether a given arrangement supplies what a particular employee needs. Preference alignment and WFH intensity should be treated as related but distinct features of hybrid-work design.

Cross-national and U.S. survey evidence documents substantial variation in desired, planned, and realized WFH [5,6,19]. Observed remote-work outcomes may also reflect which workers and employers select into remote arrangements [18]. These findings motivate direct measurement of both the employee’s desired amount and the employer’s planned amount instead of inferring fit from WFH intensity alone.

### 2.2. Directional Preference–Plan Misfit

Person–environment fit theory links employee outcomes to the correspondence between individual needs and environmental supplies [24]. The phenomenology-of-fit perspective further emphasizes that employees experience this correspondence subjectively, even when objective job arrangements are similar [25]. Hybrid work provides a direct application: the same planned number of WFH days can represent an adequate supply for one employee, an insufficient supply for another, and an excessive supply for a third.

Empirical studies have begun to examine mismatch between employees’ telework preferences and the arrangements available to them. de Wind et al. found that mismatch between employees’ need for and access to WFH was cross-sectionally associated with greater work–home interference and fatigue, although it did not predict changes over one year [20]. Otsuka et al. also showed that the association between telecommuting frequency and psychological distress depended on whether employees preferred telecommuting [21]. These findings indicate that telework frequency cannot be interpreted independently of employee preference.

Evidence concerning mismatch direction is less consistent. Heiden et al. reported poorer cross-sectional wellbeing among employees who teleworked more than preferred, while mismatch did not predict changes in wellbeing or burnout over ten months [22]. Oakman et al. found higher stress among older workers when actual WFH exceeded their preferred number of days, with an additional association for musculoskeletal pain in that group [23]. These studies examined actual WFH during pandemic-period conditions and focused on wellbeing, burnout, stress, or physical pain. The present study instead compares desired WFH with employer-planned WFH, examines job dissatisfaction, and directly tests the adjusted under-remote–over-remote contrast.

WFH intensity may also have a nonlinear relationship with employee outcomes. Golden and Veiga reported an inverted-U association between telecommuting extent and job satisfaction [26]. More recent evidence suggests that WFH can raise satisfaction through flexibility, productivity, and task enjoyment while lowering it through work–life boundary problems or difficult interactions with colleagues and supervisors [27]. Communication quality and supervisor expectation-setting are also associated with remote-worker outcomes [28]. These findings imply that alignment does not make the common WFH level irrelevant: two employees may be equally aligned at different WFH levels and still report different work experiences.

Job demands–resources and conservation-of-resources theories offer possible explanations for directional differences [29,30]. Under-remote misfit may combine an unmet flexibility preference with commuting, scheduling, or autonomy demands. Over-remote misfit may reduce access to social contact, mentoring, or coordination. The present data do not directly measure these pathways, so they guide interpretation rather than constitute tested mechanisms.

Job dissatisfaction is used as the primary outcome because job satisfaction is a central work attitude associated with performance and turnover-related outcomes [31–33]. The measure remains self-reported and contemporaneous. The study therefore estimates adjusted associations with reported dissatisfaction rather than causal effects of changing hybrid-work arrangements.

### 2.3. Transparent Temporal-Holdout Ranking

People analytics can inform how organizations allocate attention, but its value depends on the decision process and the benchmark against which a model is evaluated [34–36]. Research on people-analytics ethics and algorithmic management identifies risks involving surveillance, explanation, power asymmetry, and unequal errors [37–40]. A ranking model should therefore be evaluated against transparent alternatives and interpreted in relation to the action that follows selection.

The under-remote directional rule ranks respondents by the positive difference between desired and planned WFH days. Its basis is directly observable and contestable. Logistic regression and random forests can combine this difference with worker and job characteristics, but additional complexity is useful only when it produces a sufficiently precise gain under the same review capacity. Precision, recall, and lift at a fixed top-k capacity address this comparison more directly than ROC-AUC alone.

Ranking quality, probability calibration, and subgroup error patterns answer different questions and are evaluated separately. A model can rank cases better than chance while producing probabilities that are badly calibrated. Likewise, a single global threshold can generate different selection and missed-case rates across groups even when the same scoring rule is applied to everyone. The present analysis therefore reports all three layers without treating any one of them as evidence of deployment readiness.

## 3. Materials and Methods

### 3.1. Data Source and Analytic Samples

We used the June 2026 earnings-restricted release of the Survey of Working Arrangements and Attitudes (SWAA), specifically WFHdata_May26.csv, available to registered researchers through WFH Research [41,42]. The file covers U.S. residents aged 20–64 and applies the provider-defined prior-year earnings criteria: at least USD 20,000 through March 2021, a transition toward USD 10,000 during April–December 2021, and at least USD 10,000 in the relevant prior year from 2022 onward. The alternative no-earnings-requirement file was not used.

The provider’s cratio100 weights align the sample with Current Population Survey cells defined by age, sex, education, and earnings; the release uses winsorized weights [42]. Annual descriptive trends cover May 2020–May 2026. Job dissatisfaction, desired WFH, and employer-planned WFH were jointly observed from July 2025 through February 2026. The fully adjusted association model used 15,355 complete cases from September–December 2025 because commute-time data were unavailable in July–August 2025 and January–February 2026. Ranking models used imputation within the modeling pipeline, allowing July–December 2025 observations for training and January–February 2026 observations for temporal-holdout evaluation.

[[SAMPLE_RESULTS]]

[[TABLE_1]]

Table 1. Sample construction and analytic samples.

Note: Events and prevalence are shown only when job dissatisfaction is observed. SWAA = Survey of Working Arrangements and Attitudes; WFH = work from home.

### 3.2. Outcome Definition

The primary outcome equals one when a respondent reports being very or somewhat dissatisfied with the current main job. It equals zero for the remaining observed satisfaction categories. Supplementary analyses use a stricter “very dissatisfied” outcome and the original five-category satisfaction score. Additional attitudes and behaviors are reported separately because their survey windows differ and they do not form a common validated index.

### 3.3. Directional Preference–Plan Misfit

Desired, employer-planned, and current WFH percentages are converted to five-day-week-equivalent days by dividing each percentage by 20. These values place the measures on a common scale; they do not necessarily represent exact weekly schedules. The primary signed difference is:

misfit = desired WFH days − employer-planned WFH days.

Positive values represent under-remote misfit, and negative values represent over-remote misfit. Strong misfit is defined as a directional gap of at least two equivalent days. The cutoff was selected as an interpretable definition of a large gap, not as an empirically optimized threshold. Robustness analyses examine thresholds from 0.5 to 3 days.

The primary planned-only definition excludes observations without employer-planned WFH. A combined reference uses planned WFH when observed and current WFH otherwise. A current-only reference provides a second sensitivity analysis. All outputs identify these constructions as planned, combined, or current. Employer-planned WFH may differ from the schedule ultimately realized by the employee; the primary construct therefore measures preference–plan alignment rather than preference–experience alignment.

A polynomial response-surface analysis models desired and planned WFH as separate components [43]. Both variables are centered at the shared 2.5-day midpoint, preserving the raw-scale congruence line at desired WFH = planned WFH. The model includes linear, squared, and interaction terms and estimates slopes and curvatures along the congruence and incongruence lines. Predictions are displayed only in cells with at least 30 observations in the nearest quarter-day combination.

[[TABLE_2]]

Table 2. Weighted descriptive statistics by planned-reference misfit group, July 2025–February 2026.

Note: WFH = work from home. Proportions and means are SWAA-weighted. Income is reported in USD thousands; commute is reported in minutes; education follows the SWAA five-category scale.

### 3.4. Covariates and Ranking Feature Sets

Association models adjust for age, gender, education, income, occupation, industry, commute time, children, region, and month fixed effects. These variables are described as conventional worker and job characteristics. They are survey measures that approximate information commonly available in workforce systems; they are not employer administrative records.

The ranking analysis compares conventional characteristics with feature sets that add desired WFH, employer-planned WFH, and directional misfit. Satisfaction-like attitudes and subjective evaluations of WFH are excluded because they overlap closely with the outcome. The primary complex comparator is a planned-only random forest that excludes gender and children but retains income; it is termed the reduced-feature RF after its first definition. A separate sensitivity model also excludes income because income can act as a socioeconomic proxy. A broader comparison includes gender and children. Current WFH is excluded from every model in the planned-only feature comparison.

### 3.5. Association Analysis

The association analysis estimates unweighted logistic regression, unweighted linear probability models (LPMs), and survey-weighted LPMs. Survey weights produce population-weighted point estimates [44]. The weighted LPM is primary because its coefficients directly represent adjusted probability differences. Heteroskedasticity-consistent covariance estimates provide the main confidence intervals [45]. Month-clustered intervals are reported only as a sensitivity analysis because four monthly clusters contribute to the primary outcome window.

The principal specification includes under-remote and over-remote indicators, conventional worker and job characteristics, region, occupation, industry, and month fixed effects. A Wald contrast compares the two directional coefficients to answer RQ1. Sensitivity analyses examine alternative thresholds, reference definitions, imputation, weight trimming, continuous gaps, occupation-level remoteability, selected interactions, and alternative outcome definitions.

### 3.6. Ranking, Calibration, and Subgroup Evaluation

Models trained on July–December 2025 are evaluated once in the January–February 2026 temporal holdout. Logistic regression and random forests are compared with an absolute-gap rule, the under-remote directional rule, and an additive comparison rule. ROC-AUC, PR-AUC, Brier score, precision, recall, and lift are reported. PR-AUC and top-k metrics receive particular attention because job dissatisfaction is imbalanced and the comparison assumes limited review capacity [46].

The primary top-k metrics are unweighted because each respondent occupies one position in the queue. Survey-weighted metrics are reported as sensitivity analyses. At each capacity, the complete holdout is ranked and the highest-scored k percent are selected. Random tie-breaking evaluates rules with tied scores. Paired bootstrap resampling reconstructs both queues in each holdout resample. It estimates differences in precision, recall, lift, PR-AUC, and ROC-AUC for (i) conventional models versus models adding desired and planned WFH and (ii) the reduced-feature RF versus each transparent rule.

Calibration analysis compares the 2025 base-rate prediction, raw reduced-feature RF scores, Platt scaling, and isotonic calibration [47,48]. Calibration mappings are learned within the 2025 training data and applied unchanged to the temporal holdout. Expected calibration error uses 10 equal-width probability bins. Reliability curves, Brier score, calibration intercept, and calibration slope are reported separately from ranking metrics.

Subgroup evaluation applies one global top-k cutoff to the complete holdout. Selection rate, precision, recall, and false-negative rate are calculated for source-coded gender, children, income, education, and available intersections. Bootstrap intervals resample the complete holdout and reconstruct the global queue before subgroup metrics are calculated. These diagnostics describe observed allocation and error patterns; they do not determine whether a difference is legally or substantively acceptable.

### 3.7. Interpretation, AI Assistance, and Reproducibility

Directional misfit and job dissatisfaction are measured in the same survey response. The association models therefore estimate contemporaneous relationships, and reverse causality remains possible. The temporal holdout tests whether ranking performance persists across survey periods; it does not follow the same individuals over time.

Generative AI tools assisted with English-language editing, code organization, and document formatting. They were not used to generate data or make unreviewed analytic decisions. All proposed text and code changes were reviewed by the authors, and the analyses were rerun against the verified data archive. Product details are disclosed in the Acknowledgments.

All analyses were conducted in Python 3.13.5 using pandas 2.2.3, NumPy 2.3.5, scikit-learn 1.8.0, statsmodels 0.14.6, and matplotlib 3.10.8. Word documents were generated using python-docx 1.2.0. The complete software environment is recorded in environment.yml and requirements.txt. The submitted code package performs a clean rebuild of analysis tables, source CSV files, figures, Word documents, the formatted supplementary workbook, manifests, and the reproducibility log. Automated tests compare manuscript values with regenerated outputs. The raw archive SHA256 value is recorded in DATA_MANIFEST.md.

## 4. Results

### 4.1. Directional Misfit over Time and Descriptive Patterns

Strong under-remote misfit represented a larger weighted share than strong over-remote misfit throughout the observed period (Figure 1). The annual denominator includes respondents with nonmissing desired and employer-planned WFH measures. Valid annual sample sizes are printed below the year labels.

[[FIGURE_1]]

Figure 1. Directional strong misfit over time. Weighted prevalence among respondents with nonmissing desired and employer-planned WFH measures. The annual labels report the corresponding unweighted N; 2020 covers May–December and 2026 covers January–May. Strong misfit is a directional gap of at least two equivalent days.

Weighted job dissatisfaction was highest among respondents with strong under-remote misfit (Figure 2). Table 2 reports the corresponding group sizes and weighted characteristics for July 2025–February 2026.

[[FIGURE_2]]

Figure 2. Job dissatisfaction by misfit type. Weighted prevalence from July 2025 through February 2026 under the planned-only directional definition.

### 4.2. Directional Misfit and Job Dissatisfaction

[[ASSOCIATION_RESULTS]]

[[TABLE_3]]

Table 3. Weighted LPM association summary.

Note: Confidence intervals are heteroskedasticity-robust. Supplementary Table S12 reports month-clustered intervals as a sensitivity analysis.

The under-remote estimate remained positive under thresholds from 0.5 to 3 days, planned, combined, and current reference definitions, weight trimming, single imputation, inverse-probability weighting, and alternative outcome definitions. At the two-day threshold, the weighted LPM estimates for the planned, combined, and current references were 0.115, 0.112, and 0.096, respectively. The imputed weighted LPM estimate was 0.103 (95% CI: 0.090–0.116), and the complete-case inverse-probability-weighted estimate was 0.114 (95% CI: 0.094–0.134). Supplementary Tables S3–S12, S20, S27, and S35 report the full results.

### 4.3. Temporal-Holdout Ranking

[[MODEL_RESULTS]]

[[TABLE_4]]

Table 4. Key January–February 2026 temporal-holdout comparison.

Note: All fitted models use the planned-only feature universe. Current WFH is excluded, and employer-planned WFH is represented once.

[[TABLE_5]]

[[FIGURE_3]]

Table 5. Directional rule baselines.

Figure 3. Fixed-capacity ranking performance in the January–February 2026 temporal holdout. Bars show precision@10%, and labels show lift. The dashed line indicates the holdout outcome prevalence. The absolute-gap rule ranks the absolute desired–planned gap; the directional rule ranks the positive desired–planned gap; the additive rule combines the under-remote gap with prespecified commute, children, and income indicators. Conventional RF uses conventional characteristics; WFH RF adds desired and employer-planned WFH; Reduced RF excludes gender and children. The broader planned-only sensitivity model is reported in Supplementary Table S13.

Random tie-breaking produced directional-rule precision of 0.232 (95% interval: 0.228–0.235); the reduced-feature RF value remained 0.251 because its scores were effectively continuous. Supplementary Tables S13–S15, S30, S31, S38, and S41 report the fitted-model, bootstrap, feature, and tie-breaking results.

### 4.4. Calibration

[[CALIBRATION_RESULTS]]

[[FIGURE_4]]

Figure 4. Reliability curves for the reduced-feature random forest. Curves compare mean predicted probabilities with observed prevalence in the January–February 2026 holdout. Calibration uses 10 equal-width probability bins; Brier scores are printed in the panel.

The calibrated models retained similar ranking metrics because monotonic calibration primarily changed the probability scale. Platt scaling produced precision@10% of 0.255 and recall@10% of 0.214; isotonic calibration produced 0.247 and 0.207, respectively. Supplementary Tables S16, S29, S32, and Additional Tables A1–A2 report calibration metrics and source bins.

### 4.5. Subgroup Selection Patterns

[[SUBGROUP_RESULTS]]

[[FIGURE_5]]

Figure 5. Subgroup selection and recall at 10% capacity. Bars show selection rates; points and intervals show recall. The dashed line marks overall recall for the reduced-feature random forest. The gender labels reproduce the binary source coding (female = 1 and female = 0). Income groups were defined using tertile cut points estimated in the 2025 training sample.

One global queue produced different selection and recall rates across groups. Calibration changed probability error but did not remove ranking differences created by the common top-k cutoff. Supplementary Tables S17, S29, S32, and S42 report the subgroup estimates and safeguard simulations.

### 4.6. Response Surface and Additional Sensitivity Analyses

Both WFH variables were centered at the same 2.5-day midpoint. The incongruence-line slope was 0.0287 (95% CI: 0.0173–0.0402), and the incongruence-line curvature was 0.0117 (95% CI: 0.0051–0.0182). The congruence-line slope was −0.0046 (95% CI: −0.0105 to 0.0013), and the congruence-line curvature was −0.0071 (95% CI: −0.0112 to −0.0030). Low-support regions are masked in Supplementary Figure S2. Supplementary Table S43 reports the coefficients and surface tests.

Weighted and unweighted specifications, alternative outcomes, remoteability analyses, and selected interactions did not reverse the positive under-remote estimate. The over-remote group was substantially smaller than the under-remote group, and its estimates were correspondingly less precise. The results therefore identify a larger adjusted under-remote association in this sample; they do not show that over-remote misfit is harmless.

## 5. Discussion

### 5.1. Interpretation in Relation to Prior Research

The positive association between under-remote misfit and job dissatisfaction is consistent with evidence that unmet access to WFH can be consequential. de Wind et al. found that mismatch between employees’ need for and access to WFH was cross-sectionally associated with greater work–home interference and fatigue, although it did not predict changes over one year [20]. Otsuka et al. similarly showed that the association between telecommuting frequency and psychological distress depended on employees’ telework preferences [21]. The present study extends this evidence by comparing desired WFH with employer-planned WFH, placing both mismatch directions on a common day-equivalent scale, and formally estimating the adjusted difference between their associations with job dissatisfaction.

The direction of the observed asymmetry differs from some pandemic-period evidence. Heiden et al. reported poorer wellbeing among employees who teleworked more than preferred [22], and Oakman et al. found higher stress among older employees when actual WFH exceeded their preferred number of days [23]. In the present study, under-remote misfit had the larger adjusted association with job dissatisfaction. Several design differences may explain the contrast. The prior studies examined realized telework during pandemic-period conditions, whereas the present study uses employer-planned WFH in a later period. They also examined wellbeing, burnout, stress, or musculoskeletal pain rather than job dissatisfaction and drew on different national, organizational, and age-specific samples. The result is therefore a context-specific directional pattern, not evidence that under-remote misfit is universally more consequential.

The response-surface results indicate that preference alignment and WFH intensity are distinct but connected features of hybrid-work design. Earlier research reported a nonlinear association between telecommuting extent and job satisfaction [26]. The present analysis also showed that dissatisfaction varied across matched WFH levels while also varying with mismatch direction. Knowing how much WFH is planned does not fully indicate whether the arrangement fits a particular employee, but alignment does not make the common WFH level irrelevant.

The stronger under-remote association is consistent with possible explanations involving constrained autonomy, commuting burden, schedule control, and perceived voice. Prior research links some benefits of WFH to flexibility, productivity, and task enjoyment and some disadvantages to work–life boundary problems and difficult interactions with colleagues or supervisors [27,28]. These pathways were not measured directly. Longitudinal or experimental research should test whether changing preference–plan alignment alters these resources and subsequently changes job satisfaction.

### 5.2. What the Ranking Results Add

Adding desired and planned WFH increased the random-forest point estimates for precision@10% and PR-AUC relative to conventional characteristics alone. The paired-bootstrap comparison quantifies the uncertainty around this increment rather than treating a higher point estimate as sufficient evidence. Logistic regression showed the same broad ordering but lower top-k precision than the main random-forest comparison. Together, these results indicate that preference and arrangement measures contain later-period ranking information beyond conventional characteristics, while the size and stability of the gain should be judged from the paired intervals.

The reduced-feature RF exceeded the under-remote rule by 1.84 percentage points in precision@10%, but the paired-bootstrap interval ranged from −0.32 to 3.78 percentage points. The interval does not establish equivalence or non-inferiority; it also leaves open gains that could matter under a constrained review capacity. The observed point-estimate gain was nevertheless limited relative to the added complexity in this holdout. One explanation is that much of the useful ranking information is concentrated in the desired–planned gap itself. Other explanations include the short holdout period, changes in sample composition, and limited measurement of organizational context. The evidence supports retaining the directional rule as a transparent benchmark, not claiming that it performs equivalently to the random forest.

The calibration results impose a separate boundary. The raw RF Brier score of 0.2163 was markedly worse than the 0.1051 base-rate benchmark, and its ECE was 0.3304. The raw scores were therefore poorly calibrated and should not be interpreted as probabilities. Platt and isotonic calibration reduced Brier scores to 0.1020 and 0.1019, only about 0.003 below the base-rate benchmark. The model has some ranking value, but its probability-prediction value and decision utility remain limited in the present evaluation.

### 5.3. Practical Implications for Socially Sustainable Hybrid-Work Design

Organizations can begin with two direct questions: how much WFH an employee wants and how much the organization plans. A large positive gap can prompt a voluntary conversation about feasibility, task constraints, commuting, schedule control, and support needs. Direct questions about job satisfaction should remain available; the directional gap is a discussion prompt rather than a substitute for employee feedback.

At 10% capacity, the directional rule achieved precision of 0.232 and recall of 0.195, while the reduced-feature RF achieved precision of 0.251 and recall of 0.210. Both approaches therefore missed approximately four-fifths of dissatisfied respondents, and most selected respondents did not meet the binary dissatisfaction definition. These error rates support, at most, low-cost and voluntary prioritization for additional conversation. They do not support automatic identification, punitive action, or decisions about promotion, compensation, termination, or access to flexibility.

Income requires particular care because it can act as a socioeconomic proxy. The primary complex model retains income but excludes gender and children; a separate model excludes income as a sensitivity analysis. A real organizational process would also require consent, data minimization, clear explanations, a way to contest records, human review, monitoring of subgroup errors, and validation of whether follow-up improves outcomes. Ranking performance alone does not establish net benefit.

From a social-sustainability perspective, the findings suggest that hybrid-work design should consider both WFH intensity and employees’ stated preferences. Job dissatisfaction is treated here as a proximal work-attitude outcome rather than a comprehensive measure of social sustainability. The sustainability contribution lies in showing how employee voice can be translated into a measurable alignment variable and evaluated without treating the resulting score as an employment decision.

### 5.4. Limitations and Future Research

The contemporaneous design cannot establish temporal order. Dissatisfaction may influence reported preferences, and unobserved organizational conditions may affect both misfit and dissatisfaction. Longitudinal employer data or randomized policy changes are needed to estimate whether reducing a gap changes later satisfaction, retention, or wellbeing.

The fully adjusted association model retained 15,355 of 37,434 observations with observed job dissatisfaction, desired WFH, and employer-planned WFH, a retention rate of 41.0%. This reduction primarily reflected the availability of commute time and other complete covariates and limited the main model to September–December 2025. Imputed and inverse-probability-weighted analyses produced positive under-remote estimates, but they cannot remove selection on unobserved characteristics.

The measures are self-reported, and employer-planned WFH may differ from the schedule ultimately realized. The primary estimates therefore concern preference–plan alignment rather than preference–experience alignment. The outcome is reported job dissatisfaction rather than an observed support request, completed intervention, or long-term wellbeing measure.

The evidence comes from a U.S. earnings-restricted repeated cross-section, and the January–February 2026 holdout covers a short period. Replication across countries, organizations, eligibility definitions, and longer time windows is needed to assess external and temporal stability. Future studies should also evaluate decision-curve or net-benefit measures linked to a defined intervention, because precision, recall, and calibration do not by themselves establish operational utility.

## 6. Conclusions

Directional preference–plan misfit captures a work-design dimension that average WFH intensity misses. Compared with respondents who were aligned or had a gap of less than two days, those with strong under-remote misfit had an adjusted 11.5-percentage-point higher probability of job dissatisfaction, and the adjusted under-remote association exceeded the over-remote association by 7.9 percentage points. Adding desired and planned WFH increased later-period ranking point estimates relative to conventional characteristics alone. At 10% capacity, the directional rule produced precision close to the reduced-feature RF point estimate, with a 1.84-percentage-point RF advantage and a paired-bootstrap interval of −0.32 to 3.78 percentage points. The raw RF scores were poorly calibrated, and both approaches missed about four-fifths of dissatisfied respondents. The evidence supports direct preference measurement and voluntary preference-sensitive dialogue; it does not establish causal effects or deployment-ready employee screening.

Supplementary Materials: The following supporting information is available: Figure S1, Job dissatisfaction across signed planned-reference misfit bins; Figure S2, Planned-only response surface; Tables S1–S43 and Additional Tables A1–A3, whose complete titles are listed in Supplementary File S1 and whose formatted worksheets are provided in Supplementary File S2; Supplementary File S3, source CSV tables; Supplementary File S4, analysis code and generated source outputs.

Author Contributions: Conceptualization, Z.Z., R.M., and Y.M.; methodology, Z.Z.; software, Z.Z.; validation, Z.Z., R.M., and Y.M.; formal analysis, Z.Z.; investigation, Z.Z., R.M., and Y.M.; data curation, Z.Z.; writing—original draft preparation, Z.Z.; writing—review and editing, R.M. and Y.M.; visualization, Z.Z.; supervision, R.M. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Acknowledgments: During preparation of this manuscript, the authors used OpenAI ChatGPT (GPT-5.6 Thinking, OpenAI, San Francisco, CA, USA; accessed on 12 July 2026) and OpenAI Codex (web service, OpenAI, San Francisco, CA, USA; accessed on 12 July 2026) for English-language editing, code organization, and document formatting. The authors reviewed all text and code changes, reran the analyses, verified the reported outputs, and take responsibility for the publication.

Institutional Review Board Statement: Ethical review and approval were waived because this study involved secondary analysis of de-identified third-party survey data available to registered researchers under the provider’s data-use terms, with no participant contact and no access to identifiable information. This determination was confirmed by the School of Digital Arts, Jiangsu Vocational Institute of Commerce (reference JVICT-DA-EXEMPT-2026-004).

Informed Consent Statement: No additional informed consent was required for this secondary analysis under institutional determination JVICT-DA-EXEMPT-2026-004 because the authors conducted no recruitment, had no participant contact, and used only de-identified third-party survey data. Consent procedures for the original SWAA survey were administered by the data provider.

Data Availability Statement: Third-party data were obtained from WFH Research. The de-identified SWAA microdata are available to researchers who create an account at https://wfhresearch.com/data/, subject to the provider’s data-use terms. The analysis used WFHdata_May26.csv from the earnings-restricted June 2026 release. The archive name, file list, release definition, and SHA256 checksum are recorded in DATA_MANIFEST.md. The authors do not redistribute the original archive.

Code Availability Statement: The submitted code package contains the analysis pipeline, generated source tables, figures, document-generation scripts, the formatted supplementary workbook, output manifests, automated tests, and the clean-run reproducibility log. The core pipeline accepts the verified SWAA archive through the --data-zip argument. The included clean-run records document generation of all submitted scientific and presentation outputs in one complete run.

Conflicts of Interest: The authors declare no conflicts of interest.

## Abbreviations

SWAA: Survey of Working Arrangements and Attitudes; WFH: work from home; LPM: linear probability model; RF: random forest; ROC-AUC: area under the receiver operating characteristic curve; PR-AUC: area under the precision–recall curve; ECE: expected calibration error; FNR: false-negative rate; IPW: inverse-probability weighting.

## References

1. United Nations. Transforming Our World: The 2030 Agenda for Sustainable Development; United Nations: New York, NY, USA, 2015. Available online: https://sdgs.un.org/2030agenda (accessed on 12 July 2026).

2. International Labour Organization. Decent Work Indicators: Guidelines for Producers and Users of Statistical and Legal Framework Indicators; ILO: Geneva, Switzerland, 2013. Available online: https://www.ilo.org/publications/decent-work-indicators-guidelines-producers-and-users-statistical-and-legal (accessed on 12 July 2026).

3. Detert, J.R.; Burris, E.R. Leadership behavior and employee voice: Is the door really open? Acad. Manag. J. 2007, 50, 869–884. https://doi.org/10.5465/amj.2007.26279183.

4. Morrison, E.W. Employee voice and silence: Taking stock a decade later. Annu. Rev. Organ. Psychol. Organ. Behav. 2023, 10, 79–107. https://doi.org/10.1146/annurev-orgpsych-120920-054654.

5. Brown, J.P.; Tousey, C. The shifting expectations for work from home. Fed. Reserve Bank Kans. City Econ. Rev. 2023, 108, 35–47. Available online: https://www.kansascityfed.org/research/economic-review/the-shifting-expectations-for-work-from-home/ (accessed on 12 July 2026).

6. Barrero, J.M.; Bloom, N.; Davis, S.J. The evolution of work from home. J. Econ. Perspect. 2023, 37, 23–50. https://doi.org/10.1257/jep.37.4.23.

7. Kramar, R. Beyond strategic human resource management: Is sustainable human resource management the next approach? Int. J. Hum. Resour. Manag. 2014, 25, 1069–1089. https://doi.org/10.1080/09585192.2013.816863.

8. Aust, I.; Matthews, B.; Muller-Camen, M. Common good HRM: A paradigm shift in sustainable HRM? Hum. Resour. Manag. Rev. 2020, 30, 100705. https://doi.org/10.1016/j.hrmr.2019.100705.

9. Macke, J.; Genari, D. Systematic literature review on sustainable human resource management. J. Clean. Prod. 2019, 208, 806–815. https://doi.org/10.1016/j.jclepro.2018.10.091.

10. Wang, B.; Liu, Y.; Qian, J.; Parker, S.K. Achieving effective remote working during the COVID-19 pandemic: A work design perspective. Appl. Psychol. 2021, 70, 16–59. https://doi.org/10.1111/apps.12290.

11. Parker, S.K.; Morgeson, F.P.; Johns, G. One hundred years of work design research: Looking back and looking forward. J. Appl. Psychol. 2017, 102, 403–420. https://doi.org/10.1037/apl0000106.

12. Parker, S.K.; Grote, G. Automation, algorithms, and beyond: Why work design matters more than ever in a digital world. Appl. Psychol. 2022, 71, 1171–1204. https://doi.org/10.1111/apps.12241.

13. Bloom, N.; Liang, J.; Roberts, J.; Ying, Z.J. Does working from home work? Evidence from a Chinese experiment. Q. J. Econ. 2015, 130, 165–218. https://doi.org/10.1093/qje/qju032.

14. Allen, T.D.; Golden, T.D.; Shockley, K.M. How effective is telecommuting? Assessing the status of our scientific findings. Psychol. Sci. Public Interest 2015, 16, 40–68. https://doi.org/10.1177/1529100615593273.

15. Gajendran, R.S.; Harrison, D.A. The good, the bad, and the unknown about telecommuting: Meta-analysis of psychological mediators and individual consequences. J. Appl. Psychol. 2007, 92, 1524–1541. https://doi.org/10.1037/0021-9010.92.6.1524.

16. Bloom, N.; Han, R.; Liang, J. Hybrid working from home improves retention without damaging performance. Nature 2024, 630, 920–925. https://doi.org/10.1038/s41586-024-07500-2.

17. Choudhury, P.; Foroughi, C.; Larson, B. Work-from-anywhere: The productivity effects of geographic flexibility. Strateg. Manag. J. 2021, 42, 655–683. https://doi.org/10.1002/smj.3251.

18. Emanuel, N.; Harrington, E. Working remotely? Selection, treatment, and the market for remote work. Am. Econ. J. Appl. Econ. 2024, 16, 528–559. https://doi.org/10.1257/app.20230376.

19. Aksoy, C.G.; Barrero, J.M.; Bloom, N.; Davis, S.J.; Dolls, M.; Zarate, P. Working from home around the world. Brook. Pap. Econ. Act. 2022, 53(2), 281–360. https://doi.org/10.1353/eca.2022.a901274.

20. de Wind, A.; Beckers, D.G.J.; Nijp, H.H.; Hooftman, W.; de Boer, A.G.E.M.; Geurts, S.A.E. Working from home: Mismatch between access and need in relation to work–home interference and fatigue. Scand. J. Work Environ. Health 2021, 47, 619–627. https://doi.org/10.5271/sjweh.3983.

21. Otsuka, S.; Ishimaru, T.; Nagata, M.; Tateishi, S.; Eguchi, H.; Tsuji, M.; Ogami, A.; Matsuda, S.; Fujino, Y. A cross-sectional study of the mismatch between telecommuting preference and frequency associated with psychological distress among Japanese workers in the COVID-19 pandemic. J. Occup. Environ. Med. 2021, 63, e636–e640. https://doi.org/10.1097/JOM.0000000000002318.

22. Heiden, M.; Hallman, D.M.; Svensson, M.; Mathiassen, S.E.; Svensson, S.; Bergström, G. Mismatch between actual and preferred extent of telework: Cross-sectional and prospective associations with well-being and burnout. BMC Public Health 2023, 23, 1736. https://doi.org/10.1186/s12889-023-16683-8.

23. Oakman, J.; Lambert, K.A.; Weale, V.P.; Stuckey, R.; Graham, M. The effect of preference and actual days spent working from home on stress and musculoskeletal pain in older workers. Int. Arch. Occup. Environ. Health 2023, 96, 1113–1121. https://doi.org/10.1007/s00420-023-01992-7.

24. Kristof-Brown, A.L.; Zimmerman, R.D.; Johnson, E.C. Consequences of individuals’ fit at work: A meta-analysis. Pers. Psychol. 2005, 58, 281–342. https://doi.org/10.1111/j.1744-6570.2005.00672.x.

25. Edwards, J.R.; Cable, D.M.; Williamson, I.O.; Lambert, L.S.; Shipp, A.J. The phenomenology of fit: Linking the person and environment to the subjective experience of person–environment fit. J. Appl. Psychol. 2006, 91, 802–827. https://doi.org/10.1037/0021-9010.91.4.802.

26. Golden, T.D.; Veiga, J.F. The impact of extent of telecommuting on job satisfaction: Resolving inconsistent findings. J. Manag. 2005, 31, 301–318. https://doi.org/10.1177/0149206304271768.

27. Bolli, T.; Pusterla, F. How working from home affects job satisfaction: Shedding light on the mechanisms. Comput. Hum. Behav. Rep. 2025, 20, 100793. https://doi.org/10.1016/j.chbr.2025.100793.

28. Shockley, K.M.; Allen, T.D.; Dodd, H.; Waiwood, A.M. Remote worker communication during COVID-19: The role of quantity, quality, and supervisor expectation-setting. J. Appl. Psychol. 2021, 106, 1466–1482. https://doi.org/10.1037/apl0000970.

29. Bakker, A.B.; Demerouti, E. The job demands–resources model: State of the art. J. Manag. Psychol. 2007, 22, 309–328. https://doi.org/10.1108/02683940710733115.

30. Hobfoll, S.E. Conservation of resources: A new attempt at conceptualizing stress. Am. Psychol. 1989, 44, 513–524. https://doi.org/10.1037/0003-066X.44.3.513.

31. Locke, E.A. The nature and causes of job satisfaction. In Handbook of Industrial and Organizational Psychology; Dunnette, M.D., Ed.; Rand McNally: Chicago, IL, USA, 1976; pp. 1297–1349.

32. Judge, T.A.; Thoresen, C.J.; Bono, J.E.; Patton, G.K. The job satisfaction–job performance relationship: A qualitative and quantitative review. Psychol. Bull. 2001, 127, 376–407. https://doi.org/10.1037/0033-2909.127.3.376.

33. Hom, P.W.; Lee, T.W.; Shaw, J.D.; Hausknecht, J.P. One hundred years of employee turnover theory and research. J. Appl. Psychol. 2017, 102, 530–545. https://doi.org/10.1037/apl0000103.

34. Levenson, A. Using workforce analytics to improve strategy execution. Hum. Resour. Manag. 2018, 57, 685–700. https://doi.org/10.1002/hrm.21850.

35. Marler, J.H.; Boudreau, J.W. An evidence-based review of HR analytics. Int. J. Hum. Resour. Manag. 2017, 28, 3–26. https://doi.org/10.1080/09585192.2016.1244699.

36. Tursunbayeva, A.; Di Lauro, S.; Pagliari, C. People analytics: A scoping review of conceptual boundaries and value propositions. Int. J. Inf. Manag. 2018, 43, 224–247. https://doi.org/10.1016/j.ijinfomgt.2018.08.002.

37. Tursunbayeva, A.; Pagliari, C.; Di Lauro, S.; Antonelli, G. The ethics of people analytics: Risks, opportunities and recommendations. Pers. Rev. 2022, 51, 900–921. https://doi.org/10.1108/PR-12-2019-0680.

38. Kellogg, K.C.; Valentine, M.A.; Christin, A. Algorithms at work: The new contested terrain of control. Acad. Manag. Ann. 2020, 14, 366–410. https://doi.org/10.5465/annals.2018.0174.

39. Barocas, S.; Hardt, M.; Narayanan, A. Fairness and Machine Learning: Limitations and Opportunities; MIT Press: Cambridge, MA, USA, 2023. Available online: https://fairmlbook.org/ (accessed on 12 July 2026).

40. Selbst, A.D.; Boyd, D.; Friedler, S.A.; Venkatasubramanian, S.; Vertesi, J. Fairness and abstraction in sociotechnical systems. In Proceedings of the 2019 Conference on Fairness, Accountability, and Transparency, Atlanta, GA, USA, 29–31 January 2019; ACM: New York, NY, USA, 2019; pp. 59–68. https://doi.org/10.1145/3287560.3287598.

41. Barrero, J.M.; Bloom, N.; Davis, S.J. Why Working from Home Will Stick; NBER Working Paper No. 28731; National Bureau of Economic Research: Cambridge, MA, USA, 2021. https://doi.org/10.3386/w28731.

42. Barrero, J.M.; Bloom, N.; Davis, S.J. U.S. Survey of Working Arrangements and Attitudes (SWAA), earnings-restricted June 2026 release, WFHdata_May26.csv; WFH Research: 2026. Available online: https://wfhresearch.com/data/ (accessed on 12 July 2026).

43. Edwards, J.R.; Parry, M.E. On the use of polynomial regression equations as an alternative to difference scores in organizational research. Acad. Manag. J. 1993, 36, 1577–1613. https://doi.org/10.5465/256822.

44. Lumley, T. Complex Surveys: A Guide to Analysis Using R; Wiley: Hoboken, NJ, USA, 2010.

45. White, H. A heteroskedasticity-consistent covariance matrix estimator and a direct test for heteroskedasticity. Econometrica 1980, 48, 817–838. https://doi.org/10.2307/1912934.

46. Saito, T.; Rehmsmeier, M. The precision–recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLoS ONE 2015, 10, e0118432. https://doi.org/10.1371/journal.pone.0118432.

47. Guo, C.; Pleiss, G.; Sun, Y.; Weinberger, K.Q. On calibration of modern neural networks. In Proceedings of the 34th International Conference on Machine Learning, Sydney, Australia, 6–11 August 2017; PMLR: 2017; Volume 70, pp. 1321–1330. Available online: https://proceedings.mlr.press/v70/guo17a.html (accessed on 12 July 2026).

48. Niculescu-Mizil, A.; Caruana, R. Predicting good probabilities with supervised learning. In Proceedings of the 22nd International Conference on Machine Learning, Bonn, Germany, 7–11 August 2005; ACM: New York, NY, USA, 2005; pp. 625–632. https://doi.org/10.1145/1102351.1102430.
