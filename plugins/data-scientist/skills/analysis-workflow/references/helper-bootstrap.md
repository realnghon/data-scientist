---
name: helper-bootstrap
description: Import-path bootstrap, module catalog, and environment policy for the ds_skill helper library. Use when needing to import ds_skill helpers or set up the Python environment. Triggers — import helpers, python setup, environment check, which helpers exist.
---

# Helper Bootstrap & Environment Policy

## Environment Policy

Test the active Python environment first: `python --version` plus imports of the key packages the analysis needs (pandas, numpy, scipy; matplotlib/statsmodels/sklearn when relevant). If Python ≥3.8 and the required packages import: **use that environment, do not ask, do not create a venv.** Record `python_executable`, `python_version`, package versions, and `venv_created: false` in the analysis metadata.

Ask about creating a venv ONLY when: (a) required packages are missing, (b) a version conflict affects a selected method, (c) installing would modify a system/global environment, or (d) the user explicitly requests isolation. Never create `.venv` preemptively.

## Import Bootstrap

The helpers are the `ds_skill` package in `scripts/`. When the plugin is installed into a tool cache the package is not on `sys.path` by default, so add it before importing. Paste this self-contained block — it works on Claude Code, Codex, OpenCode, and local dev:

```python
import os, sys

def _ds_scripts_dir():
    # Claude Code / Codex substitute ${CLAUDE_PLUGIN_ROOT} into this skill text:
    p = "${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts"
    if "$" not in p and os.path.isdir(p):
        return p
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("DS_SKILL_ROOT")
    if root and os.path.isdir(os.path.join(root, "skills", "analysis-workflow", "scripts")):
        return os.path.join(root, "skills", "analysis-workflow", "scripts")
    return None  # not needed if you ran `pip install -e .` in the repo

_dir = _ds_scripts_dir()
if _dir and _dir not in sys.path:
    sys.path.insert(0, _dir)

from ds_skill.correlation import pairwise_correlation   # now importable
```

Alternatives: run `pip install -e .` in the repo once (then `import ds_skill` works everywhere with no path setup), or `import ds_bootstrap` from the scripts dir (it self-locates `ds_skill` and reports available optional dependencies). Run `python "$CLAUDE_PLUGIN_ROOT/skills/analysis-workflow/scripts/ds_bootstrap.py"` for a quick environment check.

## Module Catalog

Lazy-import only the module you need. Never `import *` and never preload all modules.

| Module | Use when | Don't bother if |
|--------|----------|-----------------|
| `ds_skill.readiness` | Building the 8-dimension readiness score; checking missingness/coverage/balance/leakage gates before modeling. | User explicitly skipped readiness; data already certified clean. |
| `ds_skill.spc` | Manufacturing data; need X-bar/R, I-MR, p/c charts; Cp/Cpk capability indices; out-of-control rule detection. When out-of-control points detected: MUST report the time window (e.g., "day 15-16") and cluster analysis if violations are grouped. Classify violations by the run rules in [method-registry.md](method-registry.md) §9 (`Nelson-1..8`, `WE-1..4`). | Non-MFG domain; no spec limits available; no time-ordered process data. |
| `ds_skill.correlation` | Ranking drivers; checking pairwise relationships; need Pearson/Spearman/Kendall/MI; need FDR control across many features. | Only one candidate driver; relationships already established. |
| `ds_skill.anomaly` | Detecting outliers; univariate (IQR/MAD) or multivariate (IsolationForest) screening; data cleaning pass. For spike detection: use `detect_univariate(method='mad', threshold=3.0)` or `detect_iqr(k=1.5)` — default k=1.5 catches typical spikes; k=3.0 is too lenient. | Data already deduped + outlier-screened; analysis is distribution-robust by design. |
| `ds_skill.time_series` | Trend detection (Mann-Kendall); seasonal decomposition (STL); change-point in a metric over time. For seasonal analysis: always check multiple periods (daily 24h, weekly 7d, monthly 30d). For trend on seasonal data: if STL strength >0.5, apply Mann-Kendall to trend component only. Rigor checks: Ljung-Box on residuals, ADF stationarity, report both. | Cross-sectional snapshot; no time column; order doesn't matter. |
| `ds_skill.bootstrap` | Need a CI for any statistic (median, ratio, custom); small N (n<30) where parametric CIs are unsafe; report demands uncertainty bands. | Parametric CI from a standard test is already sufficient and assumptions hold. |
| `ds_skill.shaping` | Detecting analysis grain; scanning for leakage columns (post-outcome fields, IDs, target proxies); validating join keys. | Grain is obvious from a single table; no joins; user already vetted columns. |
| `ds_skill.ab_validator` | A/B test analysis; SRM check on arm sizes; MDE feasibility; effect-size with CI; lift estimation. | Not an experiment; observational data only. |
| `ds_skill.regression` | Modeling continuous `Y`; need linear / Ridge / Lasso with diagnostics (residuals, VIF, leverage). | `Y` is categorical; or only descriptive stats needed. |
| `ds_skill.classification` | Modeling categorical `Y`; small-N safe CV; class-imbalanced data. | `Y` is continuous; or pure description requested. |
| `ds_skill.survival` | Time-to-event data (MTBF, churn, time-to-failure); right-censored observations; KM curves, log-rank, Weibull fits. | No time-to-event semantics; no censoring. |
| `ds_skill.report_generator` | Final deliverable stage; have a populated `evidence_matrix`; need to fill the report template. | Mid-analysis; evidence still being gathered. |
| `ds_skill.analysis_methods` | Group comparison (numeric-by-group); driver ranking with 0-1 strength scores; legacy v0 helpers. | Newer dedicated module above better fits the task. |
| `ds_skill.plotting` | Producing report charts. Returns headless matplotlib figures. | Pure-text answer; no chart requested; matplotlib/seaborn unavailable. |
| `ds_skill.validation` / `ds_skill.caching` | Validating analysis inputs; memoizing expensive computations across a session. | One-shot computation; inputs already trusted. |

## CLI Helpers

- `scripts/profile_dataset.py`: standalone CLI + importable profiler. Run `python profile_dataset.py <file>`. CSV/TSV/JSON work out of the box; Excel/Parquet need `pip install -e ".[io]"`.
- `scripts/run_full_workflow.py`: deterministic baseline workflow for smoke tests. Run `python run_full_workflow.py <file> --target <column> --output <dir>`.
- `scripts/ds_bootstrap.py`: import-path bootstrap + dependency check.

Charts require `matplotlib`/`seaborn` (`pip install -e ".[viz]"`); every `plotting` function fails with a clear install hint if they are missing.
