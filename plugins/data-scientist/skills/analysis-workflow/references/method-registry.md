---
name: method-registry
description: Catalog of statistical and ML methods indexed by analysis purpose (group comparison, driver ranking, correlation, time series, A/B test, modeling, survival, SPC). Use when selecting methods, checking assumptions, or finding alternatives. Pick by purpose + data shape + assumption fit, not by method name. Triggers — which method should I use, what are alternatives, why was X rejected, how to cross-check.
---

# Method Registry

Catalog of method groups, indexed by analysis purpose. Pick by purpose + data shape + assumption fit, **not** by name. Every important claim must record: primary method, cross-check, rejected alternatives + reason, confidence calibration.

**Each group below ends with a `Reusable helper` line naming a *tested* function — call it instead of re-deriving the statistic.** The helpers live in the `ds_skill` package under `scripts/ds_skill/` (one module per method family, lazy-imported). They already handle the edge cases (small N, censoring, FDR control, singular matrices, non-normality). See [helper-bootstrap.md](helper-bootstrap.md) for the one-time `sys.path` snippet and environment policy, then `from ds_skill.<module> import <func>`. Every charting helper named here lives in `ds_skill.plotting` (headless matplotlib). When you cite a method in an `analysis_plan`, put its helper in the `helper_ref` field as `ds_skill.<module>.<func>`.

Cross-references: [workflow.md](workflow.md) Stage 4 calls this; [data-readiness.md](data-readiness.md) supplies the assumption flags that drive accept/reject; [data-shaping.md](data-shaping.md) supplies the analysis view; [chart-catalog.md](chart-catalog.md) maps each chart to a `ds_skill.plotting` function.

---

## Table of Contents

1. [Group Comparison](#1-group-comparison) — does Y differ across groups?
2. [Driver Ranking / Feature Importance](#2-driver-ranking--feature-importance) — which X drives Y?
   - [2a. Simpson's Paradox & Interaction Detection](#2a-simpsons-paradox--interaction-detection)
3. [Correlation & Dependency Analysis](#3-correlation--dependency-analysis) — relationship strength
4. [Time Series — Trend, Seasonality, Change, Anomaly](#4-time-series--trend-seasonality-change-anomaly)
5. [Regression](#5-regression) — continuous Y
6. [Classification](#6-classification) — categorical Y
7. [Anomaly / Outlier Detection](#7-anomaly--outlier-detection)
8. [Survival / Reliability](#8-survival--reliability) — time-to-event with censoring
9. [Statistical Process Control (SPC)](#9-statistical-process-control-spc) — Nelson run rules + Cp/Cpk workflow
10. [A/B / Experiment Validation](#10-ab--experiment-validation)
11. [Bootstrap & Resampling](#11-bootstrap--resampling)

---

## 1. Group Comparison

**Purpose:** Does `Y` differ by machine, line, batch, shift, supplier, recipe, time bucket?

**Use when:** `Y` is numeric / ordinal / categorical / binary; one or more grouping columns; rows independent within groups.

🔴 **Reject when:** rows are paired/repeated (use paired or mixed-effects); grain mixes entities; single group only.

**Primary methods:**
- 2 numeric groups, unequal/unknown variance → **Welch t-test**.
- 2 numeric groups, paired → **paired t-test**.
- 2 numeric groups, small (n<30 per group) / skewed → **Mann-Whitney U**.
- 3+ numeric groups, balanced variance → **one-way ANOVA**.
- 3+ numeric groups, unequal variance → **Welch ANOVA**.
- 3+ numeric/ordinal, non-normal → **Kruskal-Wallis** (+ Dunn post-hoc).
- Categorical/binary `Y` → **chi-square** (or **Fisher exact** if cells sparse (<5 expected per cell) / 2×2 small (n<20 per cell)).

**Alternatives & rejections:**
- Student t-test → rejected by default (variance equality unverified); keep as sensitivity check only.
- One-way ANOVA → rejected when Levene/Brown-Forsythe flags unequal variance.
- Chi-square → rejected when any expected cell count < 5; fall back to Fisher.

**Cross-checks:** non-parametric counterpart for parametric primary (and vice versa); effect size (Cohen's d, Cliff's delta, Cramér's V); pairwise post-hoc when overall test rejects.

**Confidence calibration:** high if primary and cross-check agree in direction *and* effect size is practically meaningful (Cohen's d>0.5 or Cliff's delta>0.3); medium if p-value supports but effect size small (d<0.3); low if disagreement or n<20 per group.

**Reusable helper:** `ds_skill.analysis_methods.recommend_group_comparison(df, target, group)` picks the right test from the data shape; `ds_skill.analysis_methods.compare_numeric_by_group(df, target=..., group=...)` runs it with effect size and a non-parametric cross-check. Charts: `ds_skill.plotting.plot_grouped_boxplot`, `plot_violin`, `plot_dotplot_ci`.

---

## 2. Driver Ranking / Feature Importance

**Purpose:** Which `X` fields matter most for `Y`?

**Use when:** numeric or binary `Y`; multiple candidate `X` (mixed types ok); rows independent; `X` measured before or concurrently with `Y`.

🔴 **Reject when:** any candidate `X` is computed from `Y` or recorded after `Y` (leakage); n_features ≫ n_rows without regularization; rows are repeated measures of same entity without grouping.

**Primary methods:**
- Numeric `Y` + numeric `X` set → **Spearman rank correlation table** (default; robust).
- Numeric `Y` mixed types → **gradient-boosted tree + permutation importance**.
- Binary `Y` → **logistic regression coefficients** *and* **tree-based permutation importance**.

**Alternatives & rejections:**
- Pearson correlation → rejected as primary for skewed / non-linear; keep as cross-check.
- Raw model `feature_importances_` (gini) → rejected alone; biased toward high-cardinality features; use permutation importance instead.
- Univariate p-values → rejected as ranking signal (don't measure effect size).

**Cross-checks:** stratified group summaries (does the top driver still rank high inside each segment?); partial dependence plots; simpler regression with the top-k drivers only.

**Confidence calibration:** high if rank order stable across two model families and across bootstrap resamples; medium if top-3 stable but tail noisy; low if rank flips between methods.

**Reusable helper:** `ds_skill.correlation.correlation_with_target(df, target, candidate_features=None, methods=("pearson","spearman"), include_mi=True, fdr_alpha=0.05)` ranks every feature against `Y` with BH-FDR-adjusted p-values and a mutual-information row per feature (robust default). `ds_skill.analysis_methods.rank_numeric_drivers(df, target, candidate_features)` gives 0–1 strength scores. For model-based importance, fit `ds_skill.regression.fit_linear_regression` / `fit_ridge` and read coefficients. Chart: `ds_skill.plotting.plot_feature_importance`.

### 2a. Simpson's Paradox & Interaction Detection

**Purpose:** Does a driver ranking or group comparison **reverse direction** when stratified by a lurking variable? Is there an interaction effect that makes pooled analysis misleading?

**Use when:** you have a natural blocking/stratification variable (region, product line, shift, operator, device type) and suspect the pooled relationship hides segment-level heterogeneity.

🔴 **Mandatory check when:** comparing groups (A/B, treatment/control), ranking drivers in manufacturing/ops/sales data with obvious strata, or when domain knowledge suggests the effect "depends on" another variable.

**Primary methods:**
1. **Stratified vs pooled comparison**: compute the effect (correlation, mean difference, regression coefficient) within each stratum separately, then compare to the pooled (all-data) effect. If **pooled and stratified disagree in direction or rank order** → Simpson's paradox.
2. **Interaction term in regression**: fit `Y ~ X + Z + X:Z` where `Z` is the suspected moderator. If `X:Z` coefficient is significant (p < 0.05) and meaningfully sized → interaction present, report stratified results.
3. **Stratified crosstab / contingency table**: for categorical X and Y, build separate 2×2 tables per stratum and check whether the association flips (odds ratio >1 pooled but <1 within strata, or vice versa).

**Simpson detection protocol**:
- For **driver ranking**: rank drivers within each stratum (e.g., region A/B/C separately), then check if the pooled ranking matches. If pooled says "driver X is #1" but X ranks #3+ in every stratum → report the stratified result as primary and flag the paradox.
- For **A/B test**: compute treatment effect within each segment (mobile/desktop, new/returning, etc.). If pooled shows positive lift but all segments show negative (or opposite) → Simpson, investigate sample-composition shift.
- For **group comparison**: compare means of group 1 vs 2 overall, then within each stratum. If overall ranking disagrees with within-stratum ranking → paradox.

**Alternatives & rejections:**
- Reporting only pooled results when strata exist → rejected; always stratify first, then decide pooled vs stratified as primary.
- Ignoring interaction terms in regression → rejected when domain knowledge suggests "effect depends on Z."

**Cross-checks:** visualize stratum-specific effects side-by-side (faceted scatter, grouped bar chart showing effect per stratum + pooled); mixed-effects model with random slopes per stratum (if enough data).

**Confidence calibration:** high if stratified results are consistent across strata and disagree with pooled; medium if only 1-2 strata flip; low if sample sizes per stratum are tiny (<30).

**Reusable helper:** No single-function helper for Simpson detection yet (build crosstabs + stratified correlations manually); `ds_skill.regression.fit_interaction_model(df, target, x, moderator)` fits the interaction term. Chart: `ds_skill.plotting.plot_stratified_effect` (conceptual; implement as faceted scatter or grouped barplot).

---

## 3. Correlation & Dependency Analysis

**Purpose:** Quantify pairwise dependence between two variables.

**Use when:** characterizing relationships before modeling; checking redundancy among `X`; sanity-checking a single hypothesis.

🔴 **Reject when:** confounding obvious and unaddressed; relationship is causal claim (correlation ≠ causation); time order violated.

**Primary methods:**
- Linear association, no outlier dominance → **Pearson**.
- Monotonic but non-linear → **Spearman** (default for messy data).
- Categorical–categorical → **Cramér's V** (from chi-square).
- Numeric–categorical → **eta-squared** or one-way ANOVA effect size.
- Suspected non-monotonic (U-shape, interactions) → **mutual information** (continuous via k-NN MI).

**Alternatives & rejections:**
- Pearson on skewed data → rejected; use Spearman.
- Mutual information on tiny samples → rejected (MI is biased upward at low n); use Spearman.

**Cross-checks:** scatter / hexbin / box-by-bin; bootstrap CI for the correlation coefficient.

**Confidence calibration:** high when |r| or |ρ| > 0.3 AND visual relationship matches AND bootstrap CI excludes 0; low if any one fails.

**Reusable helper:** `ds_skill.correlation.pairwise_correlation(df, columns=None, method="spearman", fdr_alpha=0.05)` returns the full FDR-controlled correlation matrix; `ds_skill.correlation.correlation_with_target(...)` for the single-target case. Both report effect-strength labels. Chart: `ds_skill.plotting.plot_correlation_matrix`, `plot_scatter_fit`.

---

## 4. Time Series — Trend, Seasonality, Change, Anomaly

**Purpose:** Has the metric drifted? Is it seasonal? When did it change? Are there time-point anomalies?

**Use when:** ordered timestamp; enough span to cover at least 2 cycles for seasonality; consistent sampling cadence (or interpolatable).

🔴 **Reject when:** irregular gaps without resampling plan; process mix changes mid-series; aggregated to a grain coarser than the question.

**Primary methods:**
- Trend → **STL decomposition** (trend + seasonal + remainder) or **Theil-Sen slope** for robustness.
- Seasonality → **ACF / PACF**, **STL seasonal component**.
- Change point (unknown timing) → **PELT** or **binary segmentation** on mean/variance.
- Forecasting (only if explicitly asked) → **ETS** / **ARIMA** / **Prophet**; tree models with lag features for mixed exogenous drivers.
- Time-point anomaly → **rolling robust z-score**, **STL remainder + 3σ**, **seasonal hybrid ESD**.

**Anomaly Classification (MANDATORY when anomalies detected):** After flagging anomaly points, classify them: (1) **Isolated spikes/drops** - single points returning to normal (sensor glitch); (2) **Sustained level shift** - permanent mean change (regime change); (3) **Trend change** - slope change; (4) **Systematic vs random** - clustered → systematic (investigate); scattered → random (monitor). Report format: "220 anomalies: 112 isolated spikes, 1 level shift at day 90, 1 trend change at day 120. Systematic (clustered in equipment E3)."

**Alternatives & rejections:**
- Plain linear regression of `Y ~ time` → rejected if residuals show autocorrelation; use Theil-Sen or model residual structure.
- Forecasting when the user only wants to *understand* — rejected (over-scope); use trend + change-point instead.

**Cross-checks:** before/after group comparison around detected change points; SPC control chart over the same window.

**Confidence calibration:** high if trend/change is visible on a chart AND statistic exceeds threshold AND domain context supports timing; low if only the statistic fires.

**Reusable helper:** `ds_skill.time_series.mann_kendall_trend(series, alpha=0.05)` (robust monotonic trend + Sen's slope), `ds_skill.time_series.seasonal_decompose(...)` (STL-style trend/seasonal/remainder), `ds_skill.time_series.detect_change_points(...)` (CUSUM / binary segmentation), `ds_skill.time_series.sampling_quality(timestamps)` (regularity + gap audit before any decomposition). Charts: `ds_skill.plotting.plot_time_series`, `plot_time_series_decomposition`, `plot_small_multiples`.

---

## 5. Regression

**Purpose:** Estimate a continuous `Y` from `X`; quantify interpretable effects.

**Use when:** numeric `Y`; predictors known before `Y`; enough rows per predictor (≥10:1 rule of thumb, more if collinear).

🔴 **Reject when:** `Y` is binary/categorical (use classification); strong leakage; n_features ≫ n_rows without regularization.

**Primary methods:**
- Interpretable effects, few predictors → **OLS linear regression** with full diagnostics.
- Many correlated predictors → **ridge** or **elastic-net**.
- Mixed types, interactions matter → **gradient-boosted trees** (XGBoost / LightGBM).
- Heavy-tailed residuals or influential points → **Huber / quantile regression**.

**Alternatives & rejections:**
- OLS without diagnostics → rejected; always report residual plot, VIF, influential-point check.
- Stepwise selection on p-values → rejected; biased CIs and unstable; use regularization or domain-guided selection.

**Cross-checks:** held-out test R² / RMSE; permutation importance vs coefficients; stratified residuals by key categorical groups.

**Confidence calibration:** high if held-out performance matches train AND residual diagnostics pass AND coefficients align with domain knowledge; low if any one fails.

**Reusable helper:** `ds_skill.regression.fit_linear_regression(df, target, features, robust_se=False)` (OLS with HC3 option, falls back to numpy lstsq + bootstrap SE when statsmodels is absent), `ds_skill.regression.fit_ridge(...)` / `fit_lasso(...)` for correlated/wide predictors, `ds_skill.regression.residual_diagnostics(...)` (VIF, residual structure, influential points), `ds_skill.regression.response_curves(...)` for marginal effects. Charts: `ds_skill.plotting.plot_regression_diagnostics`, `plot_scatter_fit`.

---

## 6. Classification

**Purpose:** Predict a categorical `Y` (binary or multi-class).

**Use when:** discrete outcome; sufficient examples per class; predictors measured before outcome.

🔴 **Reject when:** severe class imbalance with n_minority < 30 and no resampling/cost adjustment planned; leakage suspected; near-perfect separation (suggests a leaked target).

**Primary methods:**
- Binary, interpretability needed → **logistic regression** (+ L2).
- Binary, predictive performance → **gradient-boosted trees** with calibration.
- Multi-class → **multinomial logistic** or **GBT one-vs-rest**.
- Small sample or wide data → **regularized logistic** + cross-validation.
- Imbalanced minority → cost-sensitive loss or **SMOTE on training fold only**.

**Alternatives & rejections:**
- Accuracy as primary metric on imbalanced data → rejected; use PR-AUC, F1, or business-cost matrix.
- k-NN on high-dim wide data → rejected (curse of dimensionality).

**Cross-checks:** confusion matrix at decision threshold from cost analysis; calibration curve; second model family.

**Confidence calibration:** high if held-out PR-AUC and calibration both pass AND second model family agrees on top predictors; low if one passes alone.

**Reusable helper:** `ds_skill.classification.fit_classifier(...)` (small-N-safe CV, logistic or gradient-boosted), `ds_skill.classification.class_balance_check(y, min_per_class=30)` (run this first — flags imbalance), `ds_skill.classification.tune_threshold(...)` (cost-aware decision threshold). Charts: `ds_skill.plotting.plot_roc_curve`, `plot_confusion_matrix`, `plot_calibration_curve`.

---

## 7. Anomaly / Outlier Detection

**Purpose:** Flag rows or windows that don't fit the rest.

**Use when:** investigation candidates needed (not root cause); univariate or multivariate numeric data; enough rows to estimate normal behavior.

🔴 **Reject when:** "anomaly" actually means "rare known class" (use supervised classification); features mostly categorical without encoding strategy.

**Primary methods:**
- Univariate, skewed → **robust z-score (MAD-based)** or **IQR fence**.
- Univariate, time-ordered → **rolling MAD** + control-chart rules.
- Multivariate numeric, unlabeled → **Isolation Forest** or **LOF**.
- Multivariate with known normal cluster → **one-class SVM** or **Mahalanobis distance**.

**Alternatives & rejections:**
- Plain z-score with mean/std → rejected on skewed data (mean and std contaminated by the outliers); use median/MAD.
- Isolation Forest on tiny data → rejected (n < ~200).

**Cross-checks:** flag-rate sanity (expect single-digit %); manual review of top-k flags; second detector agreement.

**Confidence calibration:** anomaly detection outputs are *candidates*, not findings. Confidence is operational (precision of flagged set), not statistical.

**Reusable helper:** `ds_skill.anomaly.detect_univariate(...)` (auto-picks IQR/MAD/z-score by skew), or the specific `detect_iqr` / `detect_mad` / `detect_zscore`; `ds_skill.anomaly.detect_multivariate(...)` / `detect_isolation_forest(...)` for multivariate screening. Each returns flag indices + a flag-rate summary. Chart: `ds_skill.plotting.plot_flagged_scatter`.

---

## 8. Survival / Reliability

**Purpose:** Time-to-event with censoring — time to failure, time to defect, time to churn.

**Use when:** event-time data with some observations censored (event hasn't happened yet by end of window); single event type.

🔴 **Reject when:** all events observed (use regression on duration); competing risks unaddressed (need cause-specific models).

**Primary methods:**
- Non-parametric survival curve → **Kaplan-Meier** by group.
- Group comparison of survival → **log-rank test**.
- Parametric reliability with shape parameter → **Weibull** fit (shape interprets early-life vs wear-out failures).
- Covariate effects on hazard → **Cox proportional hazards** (check PH assumption with Schoenfeld residuals).

**Alternatives & rejections:**
- Treat censored rows as "no event" in logistic regression → rejected; biases the estimate.
- Exponential model when Weibull shape ≠ 1 → rejected; under-fits.

**Cross-checks:** Kaplan-Meier curve vs Weibull fit visually; log-rank vs Cox-derived HR for a single covariate.

**Confidence calibration:** high if KM curves visually separate AND log-rank p-value supports AND sample size adequate per group; low if curves cross (PH violated).

**Reusable helper:** `ds_skill.survival.kaplan_meier(durations, events)` and `kaplan_meier_by_group(...)` (non-parametric curves), `ds_skill.survival.log_rank_test(...)` (group comparison), `ds_skill.survival.fit_weibull(durations, events)` (shape parameter → early-life vs wear-out). Chart: `ds_skill.plotting.plot_kaplan_meier`.

---

## 9. Statistical Process Control (SPC)

**Purpose:** Is the process stable over time? Capable against spec?

**Use when:** ordered measurements; process mix reasonably constant within the window; rational subgrouping possible (for Xbar) or individuals data.

🔴 **Reject when:** process mix changes within the chart; measurements are aggregated rates over inconsistent denominators (without using p/u chart); insufficient ordered subgroups for limit estimation (<20 subgroups).

**Primary methods:**
- Continuous individuals → **I-MR chart** (individuals + moving range).
- Continuous subgroups → **Xbar-R** (subgroup n ≤ 8) or **Xbar-S** (n > 8).
- Proportion defective → **p-chart** (variable denominator) or **np-chart** (constant).
- Defect count per unit → **c-chart** (constant opportunity) or **u-chart** (variable).
- Capability vs spec → **Cp / Cpk** (within-process, short-term) and **Pp / Ppk** (overall, long-term).
- Drift detection → **EWMA** or **CUSUM** for small shifts.
- **Out-of-control detection** → Western Electric / Nelson run rules (8 rules, see below).

**Western Electric / Nelson Run Rules** — canonical list (SSOT for run rules; manufacturing-playbook and helper-bootstrap reference this). Apply to I-MR, Xbar-R/S charts. The numbering below matches the `Nelson-1..8` ids emitted by `ds_skill.spc.apply_nelson_rules`; the classic Western Electric subset is `WE-1..4` (= Nelson rules 1, 5, 6, plus "8 consecutive on one side") via `apply_western_electric_rules`. Report violations by id, not bare number:
1. One point beyond ±3σ from center line (hard limit violation).
2. **Nine consecutive points on same side of center** (sustained shift).
3. Six consecutive increasing or decreasing points (trend/drift).
4. Fourteen consecutive alternating up/down (over-adjustment).
5. Two out of three consecutive points beyond ±2σ on same side (moderate shift).
6. **Four out of five consecutive points beyond ±1σ on same side** (smaller sustained shift).
7. Fifteen consecutive points within ±1σ band (stratification / reduced variation / wrong subgrouping).
8. Eight consecutive points beyond ±1σ on either side (mixture pattern).

**Critical workflow for capability**: ① Run I-MR / Xbar-R chart, ② check rules 1-8, ③ **only if all rules pass** (process is stable), ④ compute Cp/Cpk on the stable segment, ⑤ if unstable, isolate special-cause segments and compute Cp/Cpk only on in-control segments. Never compute capability on a full dataset that contains out-of-control points — the within-subgroup variance estimate is biased by between-shift noise.

**Alternatives & rejections:**
- Cp/Cpk on unstable process → rejected; stability must be established first (run rules 1-8).
- Cp/Cpk on non-normal data without transformation → rejected; use non-normal capability (e.g. Johnson transform) or report Ppk only.
- Pooled/overall Cp when process has shifted mid-window → rejected; use Pp/Ppk or segment the data.

**Cross-checks:** Western Electric / Nelson run rules (all 8) in addition to ±3σ; capability after confirming stability; histogram with spec lines + normality check (Shapiro-Wilk if n<5000, Anderson-Darling otherwise).

**Simpson paradox check for stratified processes**: always stratify by the natural blocking variable (line, shift, operator, machine) before reporting a pooled effect. Full detection protocol in [§2a](#2a-simpsons-paradox--interaction-detection).

**Confidence calibration:** high if both control limits and ≥2 run rules agree the process is in/out; medium if single-rule violation on a noisy chart; low if rule 7/8 fires alone (often false positive without context).

**Reusable helper:** `ds_skill.spc.individuals_mr_chart(...)`, `xbar_r_chart(...)`, `p_chart(...)`, `c_chart(...)`, `u_chart(...)` build the control chart; `ds_skill.spc.apply_nelson_rules(chart)` / `apply_western_electric_rules(chart)` add run-rule violations; `ds_skill.spc.cp/cpk/pp/ppk(...)` and `capability_summary(...)` compute capability after stability is confirmed. Charts: `ds_skill.plotting.plot_control_chart`, `plot_capability_histogram`.

---

## 10. A/B / Experiment Validation

**Purpose:** Did the change cause the metric to move?

**Use when:** explicit intervention/exposure variable; randomization or quasi-randomization; comparable pre-period or control arm.

🔴 **Reject when:** sample ratio mismatch unexplained; outcome window leaks back into treatment assignment; novelty effects untested.

**Primary methods:**
- Sanity → **SRM (sample ratio mismatch) chi-square** before reading the result.
- Continuous outcome → **Welch t-test** + effect size (Cohen's d).
- Binary outcome → **two-proportion z-test** + risk difference and risk ratio.
- Multiple metrics → **Holm-Bonferroni** or **Benjamini-Hochberg FDR**.
- Continuous w/ pre-period → **CUPED** (variance reduction).
- Quasi-experiment → **difference-in-differences** (parallel-trends check) or **interrupted time series**.

**Alternatives & rejections:**
- Reading per-metric p-values without multiple-comparison adjustment → rejected.
- Looking at the result before SRM passes → rejected.
- Stopping early on a peek → rejected unless sequential testing was pre-registered.

**Cross-checks:** segment-level effect (consistent across major segments?); novelty-effect check (first-week vs steady-state).

**Confidence calibration:** high if SRM passes AND primary metric moves AND segments agree AND CI excludes practical-significance threshold; low if any one fails.

**Reusable helper:** `ds_skill.ab_validator.validate_ab_test(df, group_col, outcome_col, expected_ratios=None)` runs SRM → per-arm summary → effect size with CI → MDE in one call (the recommended entrypoint). The pieces are also exposed: `sample_ratio_mismatch(...)`, `effect_size_with_ci(...)`, `minimum_detectable_effect(...)`. Chart: `ds_skill.plotting.plot_dotplot_ci` for per-arm effect bands.

---

## 11. Bootstrap & Resampling

**Purpose:** Quantify uncertainty when parametric assumptions don't hold.

**Use when:** small sample, skewed distribution, complex statistic (median ratio, gini, top-decile difference) with no closed-form CI.

🔴 **Reject when:** data is heavily dependent (time series, clustered) without block bootstrap; n is so small the bootstrap distribution is degenerate.

**Primary methods:**
- CI for any statistic → **percentile bootstrap** (B ≥ 2000).
- Bias-aware CI → **BCa bootstrap**.
- Hypothesis test → **permutation test** (label shuffle under null).
- Time series → **block bootstrap** (preserves autocorrelation).
- Clustered → **cluster bootstrap** (resample clusters, not rows).

**Alternatives & rejections:**
- Normal-approximation CI on small skewed data → rejected; use bootstrap.
- Plain bootstrap on time series → rejected (breaks autocorrelation); use block.

**Cross-checks:** parametric CI (when assumptions barely hold) vs bootstrap CI — large gap = parametric assumption was wrong.

**Confidence calibration:** high if bootstrap CI is narrow and stable across B values; medium if narrow but unstable; low if CI spans zero or the practical-significance threshold.

**Reusable helper:** `ds_skill.bootstrap.bootstrap_ci(data, statistic=np.mean, n_boot=2000, method="bca")` gives a percentile or BCa CI for any one-sample statistic; `ds_skill.bootstrap.bootstrap_two_sample(a, b, statistic=...)` for a difference statistic with a resampled null. (A dedicated block/cluster bootstrap for dependent data is not yet in the package — write it task-specific and note the dependence structure.)

---

## Method Selection Principles

1. Does the method answer the user's question?
2. Does the data satisfy its target type and grain?
3. Are assumptions plausible or testable on this data?
4. Does it produce interpretable evidence (effect size, CI, chart)?
5. Can a second method cross-check the same claim?
6. Is the result actionable for the business?

For every important claim, record: primary, alternative(s), cross-check, **rejected with reason**.

---

## Method Selection Checkpoints

| Check | Why it matters | Action |
|---|---|---|
| **Match purpose + assumptions first** | Popularity is not fit | Choose from this registry by question type, data type, and assumption fit |
| **Validate assumptions** | Violated assumptions inflate false positives or reduce power | Swap to an alternative when assumptions fail (e.g., Welch t, Mann-Whitney) |
| **Cross-check every Tier-1 claim** | One method can fire on an artifact | Use a second method agreeing in direction |
| **Pair p-value with magnitude** | Significance ≠ importance | Report effect size + units + CI |
| **Use non-parametric alternatives for small/skewed data** | Parametric CIs assume normality | Prefer Mann-Whitney, Kruskal-Wallis, bootstrap CI when n < 20/group or heavy tails |
| **Mark sparse claims unsupported** | n < 5 per cell or >30% missing on Y makes any test noise | Route to descriptive-only or collect more data |
| **Correct for multiple tests** | Family-wise error inflates false positives | Apply BH-FDR when testing >5 hypotheses (`ds_skill.correlation` does this) |

Scan [anti-patterns.md](anti-patterns.md) before finalizing any claim.
