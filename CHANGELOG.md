# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.2.0] - 2026-06-19

### 🐛 Fixed — statistical correctness (plugin helpers)
- **regression**: the Anderson-Darling normality p-value was inverted in its interpolation branch on large samples; ridge/lasso now standardize features before fitting (scale-fair L1/L2 penalty, coefficients back-transformed to original units); the residual "influential observations" output is relabeled to reflect that leverage is approximated as uniform.
- **classification**: logistic `feature_importance` now uses standardized-coefficient magnitude (|β|·sd) so it reflects predictive contribution rather than a feature's measurement unit.
- **ab_validator**: pairwise effect-size CIs for 3+ arms carry a Bonferroni adjustment + warning; the mean-difference CI uses Student's t (Welch–Satterthwaite dof) instead of the normal approximation.
- **spc**: control-chart run-rule zones derive σ from the wider control-limit half-width, so a clamped p-chart limit no longer distorts Western Electric / Nelson zones.
- **caching**: the cache key now hashes full content (previously only the first/last three rows, which could silently return one dataset's cached result for a different dataset).

---

## [2.0.0] - 2026-06-13

### ✨ SKILL.md Enhancements

**Correctness Layer**
- Added explicit spike detection thresholds (MAD k=3.0, IQR k=1.5)
- Mandatory multi-period seasonality checks (daily + weekly + monthly)
- Interaction effect detection triggers (contradictions in feature importance)
- SPC out-of-control timeframe localization requirements
- Tier-1 evidence exceptions for specialized algorithms (CUSUM, IsolationForest, STL)

**Rigor Layer**
- A/B test time confounding checks for multi-month data
- A/B test revenue analysis on converted subset only
- A/B test distribution assumption checks (normality, homogeneity of variance)
- Time series autocorrelation checks (Ljung-Box test)
- Time series stationarity checks (ADF test)
- Trend tests on deseasonalized components when seasonality strength >0.5

**Quality Layer**
- Standardized data_request format with explicit deficiencies
- Improved report structure and completeness requirements

---

## [1.0.0] - Initial Release

- 42KB analysis workflow with 8 reference documents
- 11 method families (regression, A/B test, SPC, time series, etc.)
- 8-dimension data quality gates
- 21 ready-made chart functions
- 3-tier evidence framework (Tier-1/2/3)
