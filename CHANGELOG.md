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

### 🧹 Removed
- Internal development infrastructure (`evals/` evaluation harness, `tests/` unit suite, dev-only configs) is no longer published in this repo — end users of the plugin don't need it. It remains in local development only.

---

## [2.1.0] - 2026-06-14

### 🎯 Evaluation System — Fixed the Scale（修「秤」）

The flywheel had been chasing noise: skill changes were judged by a metric decoupled
from what they actually changed, so iterations got reverted on sampling variance.
Reworked the eval harness so the feedback signal tracks the skill.

### ✨ Changed
- **Two-line scoring** (`score_case.py`): split `process_score` (deterministic
  workflow-adherence, ~zero variance) from `outcome_score` (semantic conclusion
  quality). Findings now use per-finding `tier`/`weight` from ground truth.
- **Judge sees the workflow** (`judge_score.py`): feeds `analysis_plan` + `critique`
  to the judge so rigor/anti-gaming can tell real execution from form-filling.
- **Real plugin loading** (`run_l2.py`): contestants spawn with `--plugin-dir` (real
  skill trigger) instead of an injected SKILL.md path; each case runs k times
  (default 3) and reports mean ± std distributions.
- **A/B flywheel discipline** (`flywheel_compare.py`, new): compares before/after
  distributions — `keep` only when intervals don't overlap, `inconclusive` (no
  revert) when noise dominates.

### 🐛 Fixed
- Removed the 50% coverage hard-threshold cliff in `score_two_stage.py` that
  amplified single-run variance into 0 scores.
- `run_l1.py` no longer crashes on non-case directories (e.g. archived suites).

### 🧹 Removed
- 39 iteration-process docs (session summaries, progress/status snapshots, round
  results, failure analyses) — flywheel scaffolding with no lasting value. Eval
  methodology now lives in `evals/README.md` + `evals/harness/run_l2.md`.

---

## [2.0.0] - 2026-06-13

### 🎯 Major Improvements

**Evaluation System Overhaul**
- Compressed evaluation suite from 9 cases to 3 comprehensive cases
- Token cost reduced by 60% (200k → 80k per evaluation round)
- Maintained 100% capability coverage (manufacturing, business, time series)
- Implemented L2 concurrent evaluation architecture with context isolation

**Quality Score Improvements**
- Average agent judge score: 72.5 → **83.7** (+11.2 points)
- Case A (Manufacturing): 70.6 → 76.5 (+5.9)
- Case B (Business): 84.3 → 92.2 (+7.9)
- Case C (Time Series): 62.7 → 82.4 (+19.7)

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

### 🔧 Data Fixes

**Case A (Manufacturing)**
- Enhanced L3 SPC out-of-control signal (+1.0mm = ~4σ, day 15-16 only)
- Accepted cd_nm×age interaction as valid alternative to temperature×age
- Fixed random seed (20260614) for reproducible signal strength

**Case B & C**
- Ground truth syntax corrections
- Optional claim handling for boundary signals (p~0.05)

### 📊 Evaluation Infrastructure

- Background concurrent contestant execution (up to 3 parallel cases)
- Independent judge agents per dimension (correctness, completeness, rigor, clarity, anti_gaming)
- Main session context isolation (eval transcripts don't pollute working memory)
- Archived original 9-case suite as deep debugging toolkit

### 🐛 Bug Fixes

- Fixed case-01 ground_truth regex escaping
- Fixed case-03 spike detection bug (now detects all 7 spikes)
- Fixed judge prompt truncation (8k → full context)
- Normalized ground_truth version field across all cases

### 📝 Documentation

- Updated README with final evaluation scores (83.7/100)
- Comprehensive STATUS.md with audit → compression → iteration history
- Added CHANGELOG.md for version tracking

---

## [1.0.0] - Initial Release

- 42KB analysis workflow with 8 reference documents
- 11 method families (regression, A/B test, SPC, time series, etc.)
- 8-dimension data quality gates
- 21 ready-made chart functions
- 3-tier evidence framework (Tier-1/2/3)
