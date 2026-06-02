---
name: golden-templates
description: Fully-specified executable analysis recipes for recurring patterns (yield drop, A/B test, root cause, capability study, MTBF). Use when user goal matches template trigger, need end-to-end workflow, or pre-baked analysis plan. Triggers — yield analysis, A/B test, root cause, Cpk study, recurring pattern.
---


Fully specified, executable analysis recipes. An agent can run these end-to-end without further design work. Each template lists: trigger conditions, required data roles, template-specific readiness checks, methods sequence, charts, output skeleton, and known failure modes.

Cross-references: roles use the taxonomy in `data-shaping.md`; methods reference sections of `method-registry.md`; readiness checks reference `data-readiness.md`; charts reference intents in `chart-catalog.md`; output format follows `report-standard.md`.

## Template A: Manufacturing Yield-Driver Analysis

### Trigger Conditions

User asks any of: "what drives yield / defect rate / scrap", "why are some lots/lines/shifts worse", "find the top factors hurting yield".

### Required Roles

| Role | Required | Notes |
|---|---|---|
| target | yes | yield %, defect rate, pass/fail, scrap rate |
| candidate drivers | yes (>=3) | process params, equipment, recipe, material, shift |
| time | optional | enables SPC and time-confound checks |
| batch / lot | optional | enables batch-confound check; if absent, flag |

### Template-Specific Readiness Checks (in addition to standard)

- Defect / pass-rate baseline >=1% AND <=99%. Outside this, flag class imbalance and route to rare-event handling.
- Each driver level has n >= 30 rows OR is collapsed to "Other" with documentation.
- Batch confounding check: if `batch` exists, cross-tab batch x each top driver; flag if any single batch supplies >70% of one driver level.
- Leakage scan: any column whose value is set after the inspection event (post-process rework count, final-disposition code) must be excluded. List excluded columns in output.

### Methods Sequence

1. `profile_data` (workflow.md step) -> establish roles, dtypes, missingness.
2. `assess_readiness` -> standard checks + batch-confound check above.
3. `driver_ranking` -> `method-registry.md` Tree-Based Models for mixed-type importance; record top 5.
4. For each of top 3 drivers, run group comparison appropriate to its type:
   - Categorical driver, numeric Y: Welch ANOVA + Kruskal-Wallis cross-check.
   - Categorical driver, pass/fail Y: Chi-square + Fisher Exact cross-check.
   - Numeric driver, numeric Y: Spearman correlation + binned trend with CI.
   - Numeric driver, pass/fail Y: Logistic regression univariate + binned rate plot.
5. If `time` available: SPC chart on Y over time (p-chart for rate; I-MR for numeric).
6. Cross-check: refit driver ranking excluding the top driver; check stability of remaining ranks.

### Charts

- Defect Pareto by category (or by recipe/equipment).
- Boxplot or grouped bar: top-driver vs Y, with n per group.
- Coefficient / importance forest plot for ranked drivers.
- Control chart of Y over time if time available.
- Heatmap: batch x driver, if batch exists (to expose confounding visually).

### Output Skeleton

Use `assets/report_template.md`. Section content:

- TL;DR: top driver, magnitude in pp or units, scope.
- Reliable Conclusions: drivers that passed both ranking AND group comparison cross-check.
- Directional Signals: drivers significant in only one method, or whose effect collapses when a confounder is held constant.
- Unsupported: causal claims, drivers not measured, drivers fully confounded with batch.

### Known Failure Modes

- Batches that switch with shift, recipe, or material -> driver effect is actually batch effect. Mitigation: per-batch stratified comparison; flag if effect disappears within-batch.
- Leakage from final-inspection or rework columns inflating accuracy. Mitigation: column-by-column timestamp audit.
- Class imbalance (<1% defect) -> tree importance dominated by noise. Mitigation: switch to logistic regression with class weights AND require effect size in odds-ratio terms.
- Driver levels with n < 30 ranked as "top" -> unstable. Mitigation: report-time filter; collapse or mark as directional only.

## Template B: Process Parameter -> Defect Rate

### Trigger Conditions

User has continuous process parameters (temperature, pressure, speed, torque, flow, dwell, voltage, etc.) AND a binary defect outcome or defect count. Question form: "which process settings drive defects", "what setpoints minimize defect rate".

### Required Roles

| Role | Required | Notes |
|---|---|---|
| process parameters | yes (>=2 numeric) | actual values, not setpoints (or both, labeled) |
| defect outcome | yes | binary pass/fail OR count per unit OR rate per opportunity |
| time | recommended | for stationarity check |
| unit / equipment | recommended | for stratification |

### Template-Specific Readiness Checks

- Each parameter has >=50 unique values and adequate range (max - min > 3 * within-setpoint SD).
- Defect rate baseline 0.5% - 50%. Below 0.5%, require >=5,000 rows OR route to rare-event method.
- Multicollinearity scan: pairwise |Spearman| < 0.85 OR VIF < 10 across numeric params. Flag offending pairs.
- Setpoint vs actual: if both present, use actual; if only setpoint, flag "setpoint analysis only - real variation unmeasured".
- Stationarity: rolling-window mean of each parameter does not drift >2 SD across the time window without flag.

### Methods Sequence

1. `profile_data`; check parameter ranges and distributions.
2. `assess_readiness` plus checks above.
3. Choose primary model by outcome type:
   - Binary defect: Logistic regression (main effects + 2-way interactions for top 3 params) -> see `method-registry.md` Logistic Regression.
   - Count defect: Poisson or negative-binomial regression.
   - Always cross-check with a tree-based importance fit.
4. Response curves: partial dependence (or marginal effect) for each parameter with CI band.
5. For top 2 parameters by effect size, compute Cp/Cpk if spec limits exist (see `manufacturing-playbook.md` capability recipe).
6. Stratify by equipment / line if available; check whether parameter effect is consistent across strata.

### Charts

- Response curve per parameter with CI band (one chart per top parameter).
- Partial-dependence plot for tree model (sanity check vs response curve).
- Capability histogram with spec limits for top parameters.
- Coefficient forest plot (odds ratios for logistic; rate ratios for Poisson).
- Pairs / correlation heatmap of parameters (multicollinearity evidence).

### Output Skeleton

- TL;DR: top 1-2 parameters and direction of effect.
- Reliable Conclusions: parameters significant in BOTH logistic/Poisson AND tree importance, with consistent direction across equipment strata.
- Directional Signals: parameters significant in one method only, or whose effect direction flips across strata.
- Unsupported: optimal setpoint recommendations require DOE; observational data cannot prove causation - state explicitly.

### Known Failure Modes

- Imbalanced defect rate -> logistic regression fits intercept dominantly. Mitigation: class weights, focal-loss tree, or downsample-with-reweight.
- Multicollinearity among parameters -> coefficient signs flip arbitrarily. Mitigation: drop or combine collinear pairs; use ridge or PCA pre-step.
- Confounding via recipe / product: same parameter range belongs to one product only. Mitigation: per-product within-product analysis; report scope.
- Time confound: parameter drifted and so did defect rate, but they are independent. Mitigation: include time term in model; detrend.

## Template C: Equipment Time-Series Anomaly Detection

### Trigger Conditions

User has sensor data with timestamps and asks: "find anomalies", "detect when equipment misbehaves", "flag unusual periods", or wants to monitor a sensor stream.

### Required Roles

| Role | Required | Notes |
|---|---|---|
| sensor numeric | yes (>=1) | the signal to monitor |
| timestamp | yes | regular or irregular sampling |
| equipment id | optional | enables per-unit baselines |
| event log / labels | optional | enables supervised validation of flags |

### Template-Specific Readiness Checks

- Sampling rate: median inter-sample interval determined and reported. Flag if CV of intervals > 0.5 (irregular).
- Gap audit: list all gaps > 3x median interval; decide per-gap if interpolate, segment, or exclude.
- Calibration drift indicator: long-run slope of signal mean per equipment vs time. Flag if |slope| > documented sensor tolerance per month.
- Stationarity: ADF test or rolling-mean comparison; if non-stationary, decomposition step is mandatory before residual-based anomaly detection.
- Per-equipment baseline N: >=200 in-control samples required per equipment for individual control limits.

### Methods Sequence

1. `profile_data`; render raw time-series small multiples per equipment.
2. `assess_readiness` plus continuity / sampling / drift checks above.
3. STL decomposition (or seasonal-trend split appropriate to sampling) -> trend, seasonal, residual.
4. Control chart on residual or on raw signal as appropriate:
   - Regular sampling, normal-ish residual: I-MR chart.
   - Count / event-rate sensor: c or u chart.
   - Apply Nelson rules (see `manufacturing-playbook.md` SPC essentials).
5. Change-point detection on the trend component (PELT or CUSUM).
6. Contextual labeling: cross-reference flagged points with event log if present; classify each flag as known-event vs unexplained.

### Charts

- Small multiples: raw signal per equipment with flagged points marked.
- STL decomposition triple (trend / seasonal / residual) for representative equipment.
- Control chart of residual with rules-triggered markers.
- Residual histogram with reference normal overlay.
- Change-point overlay on trend with CI of breakpoint.

### Output Skeleton

- TL;DR: count of flagged periods, count of unexplained anomalies, equipment with highest rate.
- Reliable Conclusions: change points or recurring anomalies confirmed by both SPC rules AND change-point method AND not explained by sampling artifact.
- Directional Signals: anomalies flagged by only one rule or only one method; recurring patterns near sampling-gap boundaries.
- Unsupported: root-cause attribution from sensor data alone; requires linked maintenance / process event records.

### Known Failure Modes

- Irregular sampling treated as regular -> seasonal decomposition artifacts that look like anomalies. Mitigation: resample to regular grid OR use methods that handle irregular series; document choice.
- Sensor calibration drift mistaken for process drift. Mitigation: include calibration / maintenance event markers in chart; require maintenance log cross-check before flagging.
- Regime change (e.g. recipe switch) treated as anomaly. Mitigation: segment by regime; refit baselines per segment.
- Re-fitting control limits on the same data being judged -> circular. Mitigation: hold out a known in-control period for limit calculation.

---

## Anti-Patterns — Template Misuse Red Flags

🚫 These break the template contract:

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| **Force-fit data to template** (missing required fields) | Template assumptions violated, results wrong | Check trigger conditions first; if mismatch, use general workflow |
| **Skip readiness checks** (template says "run ANOVA" so skip validation) | Template assumes clean data; yours may not be | Always run readiness even with templates; narrow if blocked |
| **Apply template to wrong domain** (use MFG template on marketing data) | Vocabulary and failure modes don't match | Templates are domain-specific; check applicability first |
| **Ignore template's rejected alternatives** | Re-introduces methods template already ruled out | Trust the template's method choices; they encode field experience |
| **Reuse template with stale data roles** | Field meanings changed, template now wrong | Re-validate data_manifest matches template's expected roles |

Templates accelerate known patterns — but you still own quality gates and assumption checks.
