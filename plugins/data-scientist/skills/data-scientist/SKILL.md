---
name: data-scientist
description: Interactive data science analysis for messy structured datasets. Use when the agent needs to inspect CSV, Excel, Parquet, JSON, or SQL-result data; assess whether the data can answer a business question; reshape long/wide tables; select statistical, manufacturing, hypothesis-testing, modeling, or charting methods; generate code; run analyses; produce evidence-backed conclusions, charts, and data-quality feedback.
---

# Data Scientist

Use this skill as an analysis decision system, not as a fixed pipeline. The agent should inspect the user's data, frame the question, decide whether the data is fit for analysis, reshape data when needed, choose defensible methods, execute code, and report conclusions with evidence and limitations.

## Operating Modes

- `guided` is the default. Proceed automatically, but ask the user for high-impact decisions when confidence is low.
- `auto` is for known, repeatable analyses or golden templates. Ask only if blocked.
- `exploratory` is for unknown datasets. Prioritize data understanding, readiness, and an analysis plan before making strong claims.

Ask the user no more than 5 questions in one analysis run. Each question must include the evidence, the recommended answer, and the consequence of choosing it.

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
| `ds_skill.bootstrap` | Need a CI for any statistic (median, ratio, custom); small N where parametric CIs are unsafe; report demands uncertainty bands. | Parametric CI from a standard test is already sufficient and assumptions hold. |
| `ds_skill.shaping` | Detecting analysis grain; scanning for leakage columns (post-outcome fields, IDs, target proxies); validating join keys. | Grain is obvious from a single table; no joins; user already vetted columns. |
| `ds_skill.ab_validator` | A/B test analysis; SRM check on arm sizes; MDE feasibility; effect-size with CI; lift estimation. | Not an experiment; observational data only. |
| `ds_skill.regression` | Modeling continuous `Y`; need linear / Ridge / Lasso with diagnostics (residuals, VIF, leverage). | `Y` is categorical; or only descriptive stats needed. |
| `ds_skill.classification` | Modeling categorical `Y`; small-N safe CV; class-imbalanced data. | `Y` is continuous; or pure description requested. |
| `ds_skill.survival` | Time-to-event data (MTBF, churn, time-to-failure); right-censored observations; KM curves, log-rank, Weibull fits. | No time-to-event semantics; no censoring. |
| `ds_skill.report_generator` | Final deliverable stage; have a populated `evidence_matrix`; need to fill the report template. | Mid-analysis; evidence still being gathered. |
| `ds_skill.analysis_methods` | Group comparison (numeric-by-group); driver ranking with 0-1 strength scores; legacy v0 helpers. | Newer dedicated module above better fits the task (e.g., use `correlation` directly for FDR-controlled ranking). |

## Core Workflow

1. Read `references/workflow.md`.
2. Ingest only enough data to understand structure first: filenames, sheets, columns, row counts, dtypes, and sample rows. For large files, profile with sampling before full reads.
3. If the user did not provide a target metric `Y`, propose candidate targets and ask for confirmation.
4. Build a data profile and readiness assessment before analysis. Use `references/data-readiness.md`.
5. Identify whether the data must be reshaped, pivoted, aggregated, or converted to an analysis view. Use `references/data-shaping.md`.
6. Choose methods by analysis purpose, not by method name. Use `references/method-registry.md`.
7. For manufacturing data, check the domain playbook. Use `references/manufacturing-playbook.md`.
8. For complex work, split responsibilities by `references/multi-agent-orchestration.md`.
9. Execute reproducible code. Prefer scripts in `scripts/` when they fit; otherwise write task-specific Python/R code.
10. Cross-check important findings with at least one alternative method when feasible.
11. Produce charts and a concise report. Use `references/chart-catalog.md` and `references/report-standard.md`.

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

Ask only when the decision materially changes the result:

- Target `Y` is missing, ambiguous, or has multiple plausible candidates.
- Field semantics are uncertain and affect grouping, time, units, or leakage.
- Data shaping requires aggregation, pivoting, dropping rows, or imputing values.
- The data is insufficient for the requested conclusion but can support a narrower analysis.
- Multiple defensible analysis paths disagree.

If asking, provide 2-3 choices and a recommendation. Do not ask open-ended questions without first showing what the data suggests.

## Golden Templates

Check `references/golden-templates.md` before designing a custom analysis. If a template matches the user's goal and data roles, use it as the primary workflow and still run readiness checks. If no template matches, proceed with the general workflow.

Templates are intentionally extensible. Add proven recurring workflows there after real analyses produce stable patterns.

## Reusable Code

Prefer these helpers over hand-rolled statistics. Lazy-import only the module you need — see the "Code Helpers — Lazy Import Map" above for selection guidance.

- `scripts/profile_dataset.py`: lightweight profile for CSV, Excel, Parquet, and JSON files.
- `scripts/ds_skill/`: package of tested method modules.

Available modules in `ds_skill` (import as `from ds_skill.<module> import ...`):

- `readiness`, `spc`, `correlation`, `anomaly`, `time_series`, `bootstrap`
- `shaping`, `ab_validator`, `regression`, `classification`, `survival`
- `report_generator`, `analysis_methods` (legacy: `recommend_group_comparison`, `compare_numeric_by_group`, `rank_numeric_drivers`)

See `scripts/ds_skill/__init__.py` for the one-line description of each module.

## Safety And Quality

- Do not present statistical significance as business significance. Report effect sizes and practical impact whenever possible.
- Do not force a conclusion when data is too sparse, biased, ambiguous, or low quality.
- Separate `reliable conclusions`, `directional signals`, and `unsupported findings`.
- Explain method choices and rejected alternatives in plain language.
- Preserve reproducibility: record transformations, filters, random seeds, and package versions when relevant.
