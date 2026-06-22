---
name: advanced-techniques
description: Mandatory checks for interaction effects, categorical noise factors, root-cause tracing, and A/B multi-metric analysis. Use when: >2 continuous predictors exist, manufacturing/process data has categorical variables, root cause is categorical, or A/B test requested. Triggers — interaction, confounding, Simpson's paradox, noise factor, categorical driver, A/B test, experiment.
---

# Advanced Techniques

These checks are mandatory when specific conditions are met. Load this reference only when one of the trigger conditions fires.

## Interaction Effects & Confounding (mandatory when >2 continuous predictors)

When analyzing multiple drivers of a target `Y`:

1. Check whether pairs of features interact (e.g., temperature × equipment_age, where the effect of temperature depends on equipment age).
2. Check whether a feature's apparent effect disappears or reverses when controlling for another (Simpson's paradox or confounding).

Methods: fit a model with interaction terms; compare coefficients before and after adding suspected confounders; or stratify by levels of a potential confounder.

**Trigger condition**: (i) >2 continuous predictors exist, or (ii) correlation/feature-importance rankings show contradictions (e.g., a variable ranks high in RF importance but has no significant univariate correlation). Such contradictions often signal interactions or confounding — investigate explicitly before concluding.

Example: "Temperature shows no significant univariate correlation with yield (ρ=0.08, p=0.15), but ranks #2 in RF importance (0.24). Tested temperature×equipment_age interaction: significant (p=0.04), effect amplified 3× in old equipment."

Skip only if you have a single predictor or the analysis is purely descriptive.

## Categorical Noise Factors (mandatory for manufacturing/process data)

When the dataset contains categorical features (recipe, chamber, operator, batch, line, region, etc.), explicitly test each one's association with the target `Y` — even if initial correlation screening suggests weak effects.

Methods:
- For categorical `X` vs continuous `Y`: ANOVA or Kruskal-Wallis
- For categorical `X` vs binary `Y`: Chi-square or Fisher's exact test
- For categorical `X` with many levels (>10): group into meaningful clusters or test top-N frequent levels

Report effect sizes (eta-squared, Cramér's V) alongside p-values. Record all tested categorical variables in the "Tested but rejected" section, even when p > 0.05.

**For continuous parameters, also test non-linear relationships**:
1. Bin into 3 quantile groups (low/mid/high) and run ANOVA
2. If ANOVA significant AND middle group has best/worst outcome → report "optimal range" pattern
3. Fit quadratic term (X²) and check p-value
4. If either test shows non-linearity (p<0.05), report the optimal zone or U-shape in findings

Example: "Temperature shows optimal zone 180-200°C (ANOVA p=0.001, middle group yield 87% vs extremes 82-83%)."

## Root-Cause Tracing (mandatory when dominant driver is categorical)

When the dominant driver is a categorical variable (e.g., machine_id='C2', operator='Alice', region='West'), investigate the **underlying continuous parameter** that explains *why* that category differs.

Methods:
1. Compute group means of all continuous features by the categorical driver
2. Test which continuous features differ significantly across categories (ANOVA / Kruskal-Wallis)
3. Report the mechanism as "categorical_var → continuous_param → Y"

For manufacturing/process parameters with known spec ranges (e.g., cd_nm 85-95nm, temp 398-402°C), cite the spec range and state whether the failing category is out-of-spec.

Example: "chamber C2's cd_nm drifts to 78-84nm (out of 85-95nm spec) → fix the lithography optics."

Skip only when: (i) the categorical variable is inherently binary/final (pass/fail, treated/control) with no upstream features, or (ii) user explicitly asks for categorical-level recommendations only.

## A/B Multi-Metric Analysis (mandatory for experiments)

When the user mentions A/B test, experiment, treatment/control, or variant comparison, **analyze ALL numeric columns as potential metrics**, not just the primary one.

Procedure:
1. Identify primary metric (user-mentioned or converted/conversion_rate)
2. Identify all other numeric columns (revenue, session_duration, bounce_rate, engagement, etc.) as secondary metrics
3. Run hypothesis tests on EACH metric
4. Report three sections: **Wins** (treatment significantly better, p<0.05), **Losses** (treatment significantly worse, p<0.05), **Neutral** (no significant difference)
5. If both wins and losses exist, add **Tradeoff Analysis** section discussing business implications
6. Recommendation must be **conditional** if tradeoff exists

### Additional A/B rigor checks

**(g) Time confounding**: If data spans >1 month, check whether treatment/control assignment is balanced over time. If treatment was rolled out gradually or seasonality exists, either (i) stratify by time period, or (ii) include time as a covariate in regression.

**(h) Revenue analysis**: Analyze revenue **only on converted users** (filter to `converted==1` subset). Analyzing the full sample conflates conversion rate and revenue-per-converter. Report both: overall revenue-per-user and revenue|converted separately.

**(i) Assumption checks**: Before t-test or ANOVA, verify normality (Shapiro-Wilk for n<5000; if p<0.05 reject) and homogeneity of variance (Levene test; if p<0.05 reject). If either fails, use non-parametric alternatives (Mann-Whitney U) or bootstrap CIs. Report which assumptions were checked and whether they held.
