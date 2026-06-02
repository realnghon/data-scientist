---
name: data-scientist
description: Interactive data science analysis for messy structured datasets (CSV, Excel, Parquet, JSON, SQL results). Use when the user wants to inspect or profile a data file, judge whether the data can answer a business question, reshape long/wide tables, choose a defensible statistical, manufacturing, hypothesis-testing, modeling, or charting method, run the analysis, or get evidence-backed conclusions with charts and data-quality feedback. Typical triggers — analyze this dataset, why did yield or defect rate change, what drives a metric, is the difference significant, is this data good enough, run an A/B test, SPC or Cpk or control chart, find anomalies.
---

# Data Scientist

Use this skill as an analysis decision system, not as a fixed pipeline. The agent should inspect the user's data, frame the question, decide whether the data is fit for analysis, reshape data when needed, choose defensible methods, execute code, and report conclusions with evidence and limitations.

## Operating Modes

- `guided` is the default. Proceed automatically, but stop at checkpoints (🔴) for user confirmation on high-impact decisions.
- `auto` is for known, repeatable analyses or golden templates. Stop only if blocked.
- `exploratory` is for unknown datasets. Run data understanding and readiness first; defer method selection until data quality confirmed.

Stop at a checkpoint maximum 5 times per analysis run. Each checkpoint must include: the evidence, the recommended choice, and the consequence of that choice.

## References — Lazy Load Map

Do not read every reference upfront. Load on demand using this table. Skip references unrelated to the current analysis to keep the context lean.

| Reference | Read when | Skip if |
|-----------|-----------|---------|
| `workflow.md` | Starting any non-trivial analysis; need the canonical end-to-end sequence; user asks "what's the process". | This is a one-shot lookup (single number, single chart) with no decision branches. |
| `multi-agent-orchestration.md` | Analysis spans intake + readiness + shaping + methods + report; user invokes `/ds-*` commands; you plan to spawn sub-agents. | Single-step task; one method; one chart; no hand-off between roles. |
| `data-readiness.md` | Building `readiness_report`; user asks "is this data good enough"; missingness/coverage/leakage looks suspicious; before any modeling. | User supplied a clean curated table and only wants a chart or descriptive stat. |
| `data-shaping.md` | Data is long-form needing pivot; wide-form needing melt; grain mismatch between `Y` and `X`; need to aggregate, dedupe, or join; suspected leakage columns. | Data already arrives in the exact analysis grain with no joins or reshaping required. |
| `method-registry.md` | Selecting a statistical/ML method; user asks "which test should I use"; multiple defensible methods disagree; need rejected-alternatives rationale. | Method is fully prescribed by a golden template you've already matched. |
| `chart-catalog.md` | Producing charts for the report; choosing between bar/box/violin/scatter/heatmap; user asks "best way to visualize this". | Pure-text answer; no visualization required; user explicitly said "no charts". |
| `report-standard.md` | Writing `final_report`; preparing deliverable for the user; need section ordering, evidence-citing format, or limitations template. | Intermediate exploration only; result will not be packaged as a report. |
| `golden-templates.md` | Question matches a recurring pattern (yield drop, A/B test, root cause, capability study, MTBF); before designing a custom plan. | Question is clearly bespoke and no template name matches the user's goal. |
| `manufacturing-playbook.md` | Data contains lot/batch/line/operator/recipe/SPC/yield/defect fields; user mentions Cpk, control charts, MSA, OEE; semiconductor/process/MFG domain. | Domain is finance, marketing, web analytics, healthcare, or general business — none of the MFG vocabulary applies. |

## Code Helpers — Lazy Import Map

Import only the module needed for the current method family. Never `import *` and never preload all modules.

| Module | Use when | Don't bother if |
|--------|----------|-----------------|
| `ds_skill.readiness` | Building the 8-dimension readiness score; checking missingness/coverage/balance/leakage gates before modeling. | User explicitly skipped readiness; data already certified clean. |
| `ds_skill.spc` | Manufacturing data; need X-bar/R, I-MR, p/c charts; Cp/Cpk capability indices; out-of-control rule detection. | Non-MFG domain; no spec limits available; no time-ordered process data. |
| `ds_skill.correlation` | Ranking drivers; checking pairwise relationships; need Pearson/Spearman/Kendall/MI; need FDR control across many features. | Only one candidate driver; relationships already established. |
| `ds_skill.anomaly` | Detecting outliers; univariate (IQR/MAD) or multivariate (IsolationForest) screening; data cleaning pass. | Data already deduped + outlier-screened; analysis is distribution-robust by design. |
| `ds_skill.time_series` | Trend detection (Mann-Kendall); seasonal decomposition (STL); change-point in a metric over time. | Cross-sectional snapshot; no time column; order doesn't matter. |
| `ds_skill.bootstrap` | Need a CI for any statistic (median, ratio, custom); small N (n<30) where parametric CIs are unsafe; report demands uncertainty bands. | Parametric CI from a standard test is already sufficient and assumptions hold. |
| `ds_skill.shaping` | Detecting analysis grain; scanning for leakage columns (post-outcome fields, IDs, target proxies); validating join keys. | Grain is obvious from a single table; no joins; user already vetted columns. |
| `ds_skill.ab_validator` | A/B test analysis; SRM check on arm sizes; MDE feasibility; effect-size with CI; lift estimation. | Not an experiment; observational data only. |
| `ds_skill.regression` | Modeling continuous `Y`; need linear / Ridge / Lasso with diagnostics (residuals, VIF, leverage). | `Y` is categorical; or only descriptive stats needed. |
| `ds_skill.classification` | Modeling categorical `Y`; small-N safe CV; class-imbalanced data. | `Y` is continuous; or pure description requested. |
| `ds_skill.survival` | Time-to-event data (MTBF, churn, time-to-failure); right-censored observations; KM curves, log-rank, Weibull fits. | No time-to-event semantics; no censoring. |
| `ds_skill.report_generator` | Final deliverable stage; have a populated `evidence_matrix`; need to fill the report template. | Mid-analysis; evidence still being gathered. |
| `ds_skill.analysis_methods` | Group comparison (numeric-by-group); driver ranking with 0-1 strength scores; legacy v0 helpers. | Newer dedicated module above better fits the task (e.g., use `correlation` directly for FDR-controlled ranking). |
| `ds_skill.plotting` | Producing report charts (histogram, ECDF, grouped box/violin, dot-plot+CI, scatter+fit, Pareto, control chart, capability histogram, ROC, confusion matrix, feature importance, ...). Returns headless matplotlib figures. | Pure-text answer; no chart requested; matplotlib/seaborn unavailable and cannot be installed. |
| `ds_skill.validation` / `ds_skill.caching` | Validating analysis inputs; memoizing expensive computations across a session. | One-shot computation; inputs already trusted. |

## Core Workflow

1. Read `references/workflow.md`.
2. Ingest only enough data to understand structure first: filenames, sheets, columns, row counts, dtypes, and sample rows. For large files, profile with sampling before full reads.
3. 🔴 **If the user did not provide a target metric `Y`, propose candidate targets and ask for confirmation before proceeding.**
4. Build a data profile and readiness assessment before analysis. Use `references/data-readiness.md`.
5. Identify whether the data must be reshaped, pivoted, aggregated, or converted to an analysis view. Use `references/data-shaping.md`.
6. Choose methods by analysis purpose, not by method name. Use `references/method-registry.md`.
7. For manufacturing data, check the domain playbook. Use `references/manufacturing-playbook.md`.
8. For complex work, split responsibilities by `references/multi-agent-orchestration.md`.
9. 🔴 **CHECKPOINT (guided mode): present the `analysis_plan` and get user sign-off before executing non-trivial analysis code.** Then execute reproducible code — prefer scripts in `scripts/` when they fit; otherwise write task-specific Python/R code.
10. **Check for interaction effects and confounding.** When analyzing multiple drivers of a target `Y`, check whether: (a) pairs of features interact (e.g., temperature × equipment_age, where the effect of temperature depends on equipment age); (b) a feature's apparent effect disappears or reverses when controlling for another (Simpson's paradox or confounding). Methods: fit a model with interaction terms, compare coefficients before and after adding suspected confounders, or stratify by levels of a potential confounder. Skip this step only if you have a single predictor or the analysis is purely descriptive.
11. Cross-check every important finding with at least one alternative method; if none fits, label the claim directional, not reliable. **Important finding** = any claim where p < 0.05 and the effect size exceeds the minimum practically meaningful threshold (ask the user or use domain defaults: 2% for conversion rates, 0.2 SD for continuous outcomes, 10% relative change for business metrics).
12. Produce charts and a concise report. **Charts are not optional** — every analysis type has a minimum required chart set defined in `references/chart-catalog.md` → "Minimum Required Charts by Analysis Type". Cross-check that section and produce all required charts for the matched analysis type (A/B test, driver ranking, regression, time series, SPC, root cause, or anomaly detection). For each required chart: (a) call the appropriate `ds_skill.plotting` function or generate with matplotlib/seaborn, (b) save the figure to a file with a descriptive name (e.g., `chart_1_timeseries_with_anomalies.png`), (c) reference the saved file path in the report. If a required chart is skipped, state why in the report. Use `references/report-standard.md` for report structure.

### Shortcut Routing — Skip Stages When The Request Is Narrow

Not every request needs all 12 steps. Route these common shapes directly (full rules in `references/workflow.md` → "When To Skip Stages"):

- **One-off statistic** on an already-profiled column ("mean of X") → answer inline; skip readiness, planning, and critic.
- **User names a specific method** ("run a t-test on Y by line") → respect the choice and skip method *selection*, but still run readiness + shaping, **check the named method's assumptions, and offer the registry alternative if an assumption fails** (unequal variance → Welch t; skewed or n<20/group → Mann-Whitney; >2 groups → ANOVA/Kruskal-Wallis). 🔴 **CHECKPOINT: If assumptions fail, present the alternative and get confirmation before switching.** Then execute + critic. Never silently run a method whose assumptions are violated.
- **Profile-only** ("just profile this") → run intake + readiness, emit `data_manifest` + `readiness_report`, then stop before method planning — no claims, so no critic.

## Failure Modes & Recovery

When a stage hits a wall, do not abort the whole analysis. Each row is a three-step fallback: try the first-line fix, escalate to the fallback, and only then stop with a concrete ask.

| Trigger condition | First-line fix | If that still fails |
|---|---|---|
| **File unreadable / wrong encoding** | retry with explicit encoding + delimiter sniff; sample first 1000 rows | return a data-request naming the format needed; do not invent a manifest |
| **No plausible target `Y`** | propose ranked candidates from column roles; ask once (guided) | fall back to `exploratory` profile-only mode; report what's needed to define `Y` |
| **Readiness = blocked** (leakage / sparse / mixed grain) | apply the data-readiness narrowing (drop leaked col, restrict to adequate-N subset) | emit the `data_request` artifact and stop downstream stages — never force a conclusion |
| **Shaping collapses sample** (post-filter N too small) | loosen the filter or pick a coarser grain that preserves N | bounce to readiness with the new N; narrow the question to what survives |
| **Join match-rate too low** | normalize keys (strip/case/dtype); try `merge_asof` with tolerance | report per-join match rate; drop the join and analyze sources separately |
| **Every candidate method rejected** | swap to the non-parametric / robust alternative in `method-registry.md` | emit a "method-blocked" note; never run a method whose assumptions fail |
| **Primary method errors at runtime** | run the registered alternative for that claim | mark the claim `unsupported`, keep other claims; record the failure, don't abort |
| **Primary and cross-check disagree** | reconcile (confound, Simpson, sample diff) | downgrade to directional signal with the disagreement stated; never silently pick one |
| **Helper import fails** (`ds_skill` off path) | run the `sys.path` bootstrap in "Make the helpers importable" | fall back to task-specific code and say so; don't skip the analysis |
| **Charts unavailable** (matplotlib/seaborn missing) | `pip install matplotlib seaborn` or `pip install -e ".[viz]"` | deliver text + tables, note charts were skipped and why |

Stage-to-stage bounces (readiness ↔ shaping, planner → reframe, critic → re-run one claim) are spelled out in `references/workflow.md` → "Loops And Bounces". Loop only the affected stage; never restart from intake.

## Required Artifacts

For non-trivial analyses, create or summarize these artifacts:

- `data_manifest`: source files/tables, row counts, columns, sheets, detected field roles.
- `data_profile`: missingness, uniqueness, ranges, category counts, time coverage, suspicious values.
- `analysis_goal`: user goal, target `Y`, candidate drivers `X`, unit of analysis, filters.
- `readiness_report`: whether the data can support the requested analysis and what is missing.
- `analysis_views`: any reshaped or aggregated datasets and what information they lose.
- `analysis_plan`: selected methods, alternatives considered, assumptions, charts.
- `evidence_matrix`: findings by method, agreement/disagreement, confidence level.
- `final_report`: conclusions, charts, limitations, and recommended next actions.

## Human-in-the-Loop Rules

🔴 **CHECKPOINT — these are hard gates. STOP and ask the user before proceeding.** Do not silently pick a default and move on when any gate below is triggered.

| 🛑 Gate | Trigger condition | Show this before asking |
|---|---|---|
| **Target ambiguous** | `Y` is missing, ambiguous, or has 2+ plausible candidates | ranked candidate list + why each fits the question |
| **Semantics uncertain** | a field's meaning affects grouping, time, units, or leakage | the columns in doubt + your best-guess role for each |
| **Destructive shaping** | a step aggregates, pivots, drops rows, or imputes values | row-count delta + exactly what information is lost |
| **Narrowable-only** | data can't answer the broad question but supports a narrower one | the narrower scope that *is* answerable, with N |
| **Paths disagree** | 2+ defensible methods point different directions | the disagreement + which result you'd trust and why |

When a gate fires: provide 2-3 concrete choices + a recommendation. Never ask an open-ended question without first showing what the data suggests.

🛑 In `auto` mode the gates do not block: pick the recommended option, record the decision in the report's Human Decision Log, and flag it visibly instead of stopping. Cap at 5 questions per analysis run (see Operating Modes).

## Golden Templates

Check `references/golden-templates.md` before designing a custom analysis. If a template matches the user's goal and data roles, use it as the primary workflow and still run readiness checks. If no template matches, proceed with the general workflow.

Templates are intentionally extensible. Add proven recurring workflows there after real analyses produce stable patterns.

## Reusable Code

The plugin ships a **tested** helper library (180+ passing unit tests). Call it instead of re-deriving statistics or chart code by hand — the helpers already handle edge cases (small N, censoring, FDR control, singular matrices, headless plotting). Re-implement only when no helper fits, and say so. Use fully qualified helper references in analysis plans and notes: `ds_skill.<module>.<function>`.

### Make the helpers importable (do this once per analysis)

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

### What's available

- `scripts/profile_dataset.py`: standalone CLI + importable profiler for CSV, Excel, Parquet, JSON. Emits the `data_manifest` JSON. Run `python profile_dataset.py <file>`.
- `scripts/run_full_workflow.py`: deterministic baseline workflow for sequential runtimes and smoke tests. Runs profile → readiness → grain/leakage scan → target correlation baseline, then writes `baseline_artifacts.json` and `baseline_skeleton.md`. Run `python run_full_workflow.py <file> --target <column> --output <dir>`.
- `scripts/ds_bootstrap.py`: import-path bootstrap + dependency check (above).
- `scripts/ds_skill/`: the tested method + chart library. Lazy-import only the module you need (see the "Code Helpers — Lazy Import Map" above):
  - Analysis: `readiness`, `spc`, `correlation`, `anomaly`, `time_series`, `bootstrap`, `shaping`, `ab_validator`, `regression`, `classification`, `survival`
  - Charts: `plotting` (headless matplotlib figures covering the families in `references/chart-catalog.md`)
  - Reporting & utils: `report_generator`, `validation`, `caching`, `analysis_methods` (legacy: `recommend_group_comparison`, `compare_numeric_by_group`, `rank_numeric_drivers`)

See `scripts/ds_skill/__init__.py` for the one-line description of each module. Charts require `matplotlib`/`seaborn` (`pip install matplotlib seaborn`, or `pip install -e ".[viz]"`); every `plotting` function fails with a clear install hint if they are missing.

## Safety And Quality

- Do not present statistical significance as business significance. Report effect sizes with units, CIs, and practical impact for every estimated effect — a p-value alone is a defect.
- Do not force a conclusion when data is too sparse, biased, ambiguous, or low quality.
- Separate `reliable conclusions`, `directional signals`, and `unsupported findings`.
- Explain method choices and rejected alternatives in plain language.
- Preserve reproducibility: record transformations, filters, random seeds, and package versions for every stochastic or version-sensitive step.

## Anti-Patterns — Red-Flag Blacklist

🚫 These failure modes silently corrupt an analysis. Scan this list before reporting any claim; each maps to a recovery action. If a stakeholder asks for one of these, explain the risk instead of complying silently.

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Report p-value as business impact** | large N (n>1000) makes trivial effects "significant"; significance ≠ magnitude | pair every p with effect size + units + CI |
| **Conclude on leaked features** | post-outcome / target-derived `X` inflates accuracy; won't replicate | run the leakage scan (data-readiness dim 6) first; drop offenders |
| **Force a conclusion on sparse data** | n<5 per cell, >30% missing on `Y`, or constant `Y` → any test is noise | report descriptive-only; route the question to Tier 3 unsupported |
| **Causal language on observational data** | "X causes Y" needs an experiment or quasi-experiment | use "associated with" / "predicts" / "differs by" unless a causal design exists |
| **Aggregate away the signal** | group-mean hides Simpson's paradox and station-level failure modes | check within-group before declaring a pooled effect |
| **Cp/Cpk on an unstable process** | capability on an out-of-control process is a meaningless number | confirm SPC stability first; compute capability on the in-control segment only |
| **Single method, no cross-check** | one test can fire on an artifact; no triangulation | every Tier-1 claim needs a second method agreeing in direction |
| **Silently impute `Y`** | inventing the target biases every downstream estimate | never impute `Y`; imputing `X` requires a documented, reported strategy |
| **Refit control/CV limits on the judged data** | circular — the limits always "fit" | hold out a known in-control window / keep train-test separation |
| **Pick a method by name or popularity** | impressive ≠ defensible; the data shape decides | choose by purpose + data type + assumption fit (`method-registry.md`) |

When you catch yourself about to do any of these: stop, name the anti-pattern, and switch to the "do this instead" column.
