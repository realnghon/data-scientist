---
name: data-scientist
version: 1.0.0
description: Interactive data science analysis for messy structured datasets (CSV, Excel, Parquet, JSON, SQL results). Use when the user wants to inspect or profile a data file, judge whether the data can answer a business question, reshape long/wide tables, choose a defensible statistical, manufacturing, hypothesis-testing, modeling, or charting method, run the analysis, or get evidence-backed conclusions with charts and data-quality feedback. Typical triggers — analyze this dataset, why did yield or defect rate change, what drives a metric, is the difference significant, is this data good enough, run an A/B test, SPC or Cpk or control chart, find anomalies.
---

# Data Scientist

Use this skill as an analysis decision system, not as a fixed pipeline. The agent should inspect the user's data, frame the question, decide whether the data is fit for analysis, reshape data when needed, choose defensible methods, execute code, and report conclusions with evidence and limitations.

## Non-Negotiable Gates

These override everything else in this document. Skipping any of them invalidates the analysis.

1. **Route first, and say so.** Before any other action, output one line: `route: full | profile-only | named-method | one-off | blocked — <one-sentence reason>` (see Shortcut Routing). Re-route mid-analysis only if new evidence changes the request shape, and record the change.
2. **Before executing analysis code**: `data_manifest` + `readiness_report` + `analysis_plan` must exist as artifacts. Missing → create them first (silently in `auto` mode). **Non-negotiable**: Analysis code cannot run without these three files. If they don't exist in the output directory, generate them immediately using profile_dataset.py and structured templates.
3. **Before writing the final report**: `evidence_matrix` + `critique` (a critic sub-agent's output, or an explicit self-critique pass auditing each claim) must exist. Missing → create them first.
4. **Before labeling any claim Tier-1 / reliable**: it needs (a) **statistical significance** (p < 0.05 after multiple-testing correction, or CI excludes null), (b) a cross-check method agreeing in direction, (c) an effect size with units, and (d) a CI. If p ≥ 0.05, downgrade to directional or unsupported regardless of effect size. **Never label non-significant results (p ≥ 0.05) as Tier-1.** **Exception for specialized detection methods**: CUSUM/binary-segmentation change-point detection, IsolationForest anomaly detection, and STL seasonal decomposition are themselves validated methods — if they produce statistically significant results (e.g., CUSUM detects a change-point with confidence score, or level shift exceeds detection threshold), label as Tier-1 even without a second cross-check method. The "cross-check" requirement applies to hypothesis tests and causal claims, not to detection algorithms designed for that specific purpose.
5. **`readiness = blocked` stops the pipeline.** Emit a `data_request` and report what's answerable instead — never force a conclusion.
6. **Spec/unit sanity check**: If data contains spec limits or tolerance ranges, verify they are physically plausible (e.g., focus_um spec ±0.2 μm vs actual values ~1.0 μm suggests unit mismatch or data error). Flag in `measurement_reliability` dimension and investigate before proceeding.

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
| `multi-agent-orchestration.md` | Running the full 7-stage pipeline; using Claude Code sub-agents; invoking `/ds-*` commands; coordinating staged artifacts across runtimes. | One-off statistic, profile-only request, or any task that can be answered without stage hand-offs. |
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
| `ds_skill.spc` | Manufacturing data; need X-bar/R, I-MR, p/c charts; Cp/Cpk capability indices; out-of-control rule detection. **When out-of-control points detected: MUST report the time window (e.g., "day 15-16", "2025-12-01 to 2025-12-03") and cluster analysis if violations are grouped. Saying "43 violations detected" without time localization is incomplete.** Use Western Electric rules (Rule 1-8) to classify violation types. | Non-MFG domain; no spec limits available; no time-ordered process data. |
| `ds_skill.correlation` | Ranking drivers; checking pairwise relationships; need Pearson/Spearman/Kendall/MI; need FDR control across many features. | Only one candidate driver; relationships already established. |
| `ds_skill.anomaly` | Detecting outliers; univariate (IQR/MAD) or multivariate (IsolationForest) screening; data cleaning pass. **For spike detection in time series: use `detect_univariate(method='mad', threshold=3.0)` or `detect_iqr(k=1.5)` — the default k=1.5 catches typical spikes; k=3.0 is too lenient and misses moderate outliers.** | Data already deduped + outlier-screened; analysis is distribution-robust by design. |
| `ds_skill.time_series` | Trend detection (Mann-Kendall); seasonal decomposition (STL); change-point in a metric over time. **For seasonal analysis: always check multiple periods — daily (24h for hourly data), weekly (7d), monthly (30d) — not just one. Use `seasonal_decompose(period=...)` with different periods and compare seasonal strength scores. If data spans weeks/months, weekly seasonality is often present alongside daily patterns.** **For trend tests on seasonal data**: If STL decomposition shows strong seasonality (strength >0.5), apply Mann-Kendall to the **trend component** (not raw series) to avoid seasonal confounding. If data span <1 full cycle (e.g., 6 months of annual data), acknowledge trend uncertainty due to incomplete seasonality coverage. **Time series rigor checks** (when reporting trend/forecast): (a) Check residuals for autocorrelation with Ljung-Box test (if p<0.05, residuals are autocorrelated → violates independence assumption, consider ARIMA); (b) Check stationarity with ADF test (if p>0.05, series is non-stationary → detrend or difference before trend test); (c) Report these checks in methodology section to demonstrate rigor. | Cross-sectional snapshot; no time column; order doesn't matter. |
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

1. 🔴 **MANDATORY**: Read `references/workflow.md` and confirm the 7-stage sequence applies to this analysis. This is a hard prerequisite — the workflow document defines the complete pipeline architecture, stage handoffs, and artifact schemas. Only proceed after loading the workflow structure into context. If the analysis is a one-off statistic or quick lookup (see Shortcut Routing below), you may skip detailed workflow reading but must still confirm which shortcut applies.
2. **Environment policy — use what exists, never preemptively isolate.** Test the active Python environment first: `python --version` plus imports of the key packages the analysis needs (pandas, numpy, scipy; matplotlib/statsmodels/sklearn when relevant). If Python ≥3.8 and the required packages import: **use that environment, do not ask, do not create a venv.** Record `python_executable`, `python_version`, package versions, and `venv_created: false` in the analysis metadata. Ask about creating a venv ONLY when: (a) required packages are missing, (b) a version conflict affects a selected method, (c) installing would modify a system/global environment, or (d) the user explicitly requests isolation. Never create `.venv` preemptively.
3. Ingest only enough data to understand structure first: filenames, sheets, columns, row counts, dtypes, and sample rows. For large files, profile with sampling before full reads.
4. 🔴 **If the user did not provide a target metric `Y`, propose candidate targets and ask for confirmation before proceeding.**
5. **Build a data profile and readiness assessment before analysis.** Score all 8 dimensions defined in `references/data-readiness.md` — **that document is the single source of truth for the dimension list, thresholds, and output envelope; do not maintain a divergent copy here.** Each dimension is scored **`ok` / `partial` / `blocked`** (a status, not a 0-10 number). **Profile reports (when route is `profile-only`) MUST include**: (a) row count, column count, dtypes; (b) **missingness summary** (list each column's missing %, even if 0%); (c) sample rows; (d) candidate field roles. Example: "Missingness: All columns 0% missing (complete dataset)." The canonical eight are:
   1. **Sample Size Adequacy**: rows per analysis cell (≥30/cell ok, 5–29 partial, <5 blocked)
   2. **Missingness Pattern**: % missing + mechanism (<10% ok, 10–30% partial, >30% on `Y` blocked)
   3. **Grain Consistency**: one row per intended unit (duplicate keys → partial/blocked)
   4. **Time Coverage**: span ≥2 cycles and gap fraction (>10% partial, >30% blocked) for time-aware questions
   5. **Class / Group Balance**: majority:minority ratio (≤3:1 ok … >100:1 blocked)
   6. **Leakage Risk**: post-event / target-derived / target-gated / time-order-violating `X` → blocked
   7. **Variable Role Clarity**: `Y` identified with variation, plausible non-trivial `X` set
   8. **Reliability Of Measurement**: units, sentinel values, sensor saturation
   
   The `ds_skill.readiness.assess_readiness` helper emits exactly this rubric and envelope. Produce the `readiness_report` artifact with: (a) the `ok`/`partial`/`blocked` score + evidence for each dimension, (b) the overall decision — **`ok` → proceed; `partial` → proceed with an explicit `narrowed_scope`; `blocked` → emit `data_request` and stop downstream stages**, (c) remediation steps for every `partial`/`blocked` dimension. Any `blocked` dimension is a hard gate: narrow scope or fix the data before continuing.
   
   **When emitting `data_request` (readiness = `blocked` or `partial` with critical gaps):** The request MUST be explicit and actionable, not vague maintenance advice. Bad: "修复数据采集系统". Good: "需要补充 2025-12-01 至 2026-04-29（后 90 天）的完整小时读数，当前缺失率 43.7% 导致该时段趋势分析不可信。" Include: (1) specific time range or data scope needed, (2) current gap quantified (% missing, # rows, date range), (3) why it blocks the analysis (e.g., "insufficient coverage for trend detection", "missing critical period for seasonality").
6. Identify whether the data must be reshaped, pivoted, aggregated, or converted to an analysis view. Use `references/data-shaping.md`.
7. Choose methods by analysis purpose, not by method name. Use `references/method-registry.md`.
8. For manufacturing data, check the domain playbook. Use `references/manufacturing-playbook.md`.
9. For complex work, load `references/multi-agent-orchestration.md` before dispatching sub-agents or emulating staged hand-offs. In Claude Code, use the plugin's `agents/` directory; in runtimes without native sub-agents, run the same stage contracts sequentially.
10. 🔴 **CHECK ds_skill helpers before hand-coding**: For each method selected in the previous steps, check if a corresponding `ds_skill.*` helper exists in "Code Helpers — Lazy Import Map" above. **Default behavior: if a helper exists, MUST attempt to import and call it first.** Only fall back to hand-coding if: (a) import fails after trying the sys.path bootstrap in "Make the helpers importable"; (b) helper's signature doesn't match this specific use case after reading its docstring; (c) helper returns an error after 1 retry. Record the decision (used helper vs hand-coded, and why) in the analysis_plan artifact below.
11. **Generate analysis_plan artifact** before execution. This is a structured JSON file documenting method selection logic for auditability:
   ```json
   {
     "analysis_goal": {
       "user_question": "原始用户问题",
       "target_Y": "目标变量",
       "candidate_X": ["驱动因素1", "驱动因素2"],
       "analysis_unit": "行的含义",
       "filters_applied": ["过滤条件"]
     },
     "data_transformations": [
       "Joined fab_log + metrology on wafer_id",
       "Pivoted metrology long format to wide (station×param columns)",
       "Filtered outliers beyond 3σ",
       "Created lag features: temperature_lag_1d"
     ],
     "claims": [
       {
         "claim": "要验证的结论描述",
         "primary_method": "主方法名称",
         "rationale": "为什么选这个方法（数据特征 + 假设匹配）",
         "assumptions": ["假设1：正态性", "假设2：独立性"],
         "cross_check": "交叉验证方法",
         "helper_ref": "ds_skill.module.function OR null (hand-coded)",
         "helper_decision": "used helper / hand-coded because: <reason>"
       }
     ],
     "rejected_alternatives": [
       {"method": "被拒方法", "reason": "为什么不用（假设不满足/数据不适配）"}
     ]
   }
   ```
   **data_transformations** field (added 2026-06): list every non-trivial data operation before analysis (joins, pivots, aggregations, feature engineering). If you loaded 2+ tables and joined them, if you pivoted long→wide or wide→long, if you created lag/lead/window features, or if you aggregated to a different grain — record it here. This is essential for reproducibility and for evaluating whether the transformation was correct (e.g., did you join when ground truth expected it?).

   The analysis_plan serves as: (a) pre-execution checklist for the user to review; (b) audit trail for "why this method"; (c) template for reproducibility.
12. 🔴 **CHECKPOINT (guided mode): present the `analysis_plan` and get user sign-off before executing non-trivial analysis code.** Show: (a) what claims will be tested, (b) which methods, (c) why those methods, (d) which helpers will be used. Then execute reproducible code — prefer scripts in `scripts/` when they fit; otherwise write task-specific Python/R code that implements the plan exactly.
13. **Check for interaction effects and confounding.** When analyzing multiple drivers of a target `Y`, check whether: (a) pairs of features interact (e.g., temperature × equipment_age, where the effect of temperature depends on equipment age); (b) a feature's apparent effect disappears or reverses when controlling for another (Simpson's paradox or confounding). Methods: fit a model with interaction terms, compare coefficients before and after adding suspected confounders, or stratify by levels of a potential confounder. **This step is MANDATORY when: (i) >2 continuous predictors exist, or (ii) correlation/feature-importance rankings show contradictions (e.g., a variable ranks high in RF importance but has no significant univariate correlation).** Such contradictions often signal interactions or confounding — investigate explicitly before concluding. Example: "Temperature shows no significant univariate correlation with yield (ρ=0.08, p=0.15), but ranks #2 in RF importance (0.24). Tested temperature×equipment_age interaction: significant (p=0.04), effect amplified 3× in old equipment." Skip this step only if you have a single predictor or the analysis is purely descriptive.
13.5. **Test all categorical variables as potential noise factors.** When the dataset contains categorical features (recipe, chamber, operator, batch, line, region, etc.), explicitly test each one's association with the target `Y` — even if initial correlation screening suggests weak effects. Methods: (a) for categorical `X` vs continuous `Y`: ANOVA or Kruskal-Wallis; (b) for categorical `X` vs binary `Y`: Chi-square or Fisher's exact test; (c) for categorical `X` with many levels (>10): group into meaningful clusters or test top-N frequent levels. Report effect sizes (eta-squared, Cramér's V) alongside p-values. **Mandatory for manufacturing/process data**: test recipe, chamber, operator, shift — these are common confounders that must be ruled out before concluding a continuous parameter is the root cause. Record all tested categorical variables in the "Tested but rejected" section (Step 16), even when p > 0.05. **For continuous parameters, also test non-linear relationships**: (a) bin into 3 quantile groups (low/mid/high) and run ANOVA; (b) if ANOVA significant AND middle group has best/worst outcome → report "optimal range" pattern; (c) fit quadratic term (X²) and check p-value; (d) if either test shows non-linearity (p<0.05), report the optimal zone or U-shape in findings. Example: "Temperature shows optimal zone 180-200°C (ANOVA p=0.001, middle group yield 87% vs extremes 82-83%)." **Why this matters**: concluding "temperature drives yield" without testing recipe means recipe could be a hidden confounder; if recipe R101 always runs at high temperature AND has intrinsic defects, the temperature effect may be spurious. Similarly, only testing linear correlation misses U-shaped or optimal-zone effects.
14. **Trace mechanism when root cause is categorical.** When the dominant driver is a categorical variable (e.g., machine_id='C2', operator='Alice', region='West'), investigate the **underlying continuous parameter** that explains *why* that category differs. Example: if chamber C2 has 100% low yield, check whether C2's cd_nm (critical dimension) or temperature or pressure drifts out-of-spec compared to other chambers. Methods: (a) compute group means of all continuous features by the categorical driver; (b) test which continuous features differ significantly across categories (ANOVA / Kruskal-Wallis); (c) report the mechanism as "categorical_var → continuous_param → Y". **For manufacturing/process parameters with known spec ranges** (e.g., cd_nm 85-95nm, temp 398-402°C), cite the spec range and state whether the failing category is out-of-spec. Skip only when: (i) the categorical variable is inherently binary/final (pass/fail, treated/control) with no upstream features, or (ii) user explicitly asks for categorical-level recommendations only. **Why this matters**: "chamber C2 needs fixing" is less actionable than "chamber C2's cd_nm drifts to 78-84nm (out of 85-95nm spec) → fix the lithography optics."
14.5. **A/B test multi-metric analysis (MANDATORY for experiments).** When the user mentions A/B test, experiment, treatment/control, or variant comparison, **you MUST analyze ALL numeric columns as potential metrics**, not just the primary one. Procedure: (a) Identify primary metric (user-mentioned or converted/conversion_rate); (b) Identify all other numeric columns (revenue, session_duration, bounce_rate, engagement, etc.) as secondary metrics; (c) Run hypothesis tests on EACH metric; (d) Report must include three sections: **Wins** (treatment significantly better, p<0.05), **Losses** (treatment significantly worse, p<0.05), **Neutral** (no significant difference); (e) If both wins and losses exist, add **Tradeoff Analysis** section discussing business implications; (f) Recommendation must be **conditional** if tradeoff exists (e.g., "Deploy if short-term conversion prioritized; hold if long-term engagement matters"). **Never report only the primary metric when secondary metrics exist** — this hides critical tradeoffs. Example bad: "Treatment increases conversion +2.5pp, recommend deploy." Example good: "Treatment increases conversion +2.5pp (win) but decreases session_duration -15% and increases bounce +7pp (losses). Recommend deploy only if conversion gain > engagement loss in LTV model."

**Additional rigor checks for A/B tests:**
(g) **Time confounding**: If data spans >1 month, check whether treatment/control assignment is balanced over time. If treatment was rolled out gradually or seasonality exists, either (i) stratify by time period (e.g., split into quarters and verify effect consistency), or (ii) include time as a covariate in regression. For 24-month data, explicitly test for time×variant interaction or report effect by time cohort to rule out seasonal confounding.
(h) **Revenue analysis**: Analyze revenue **only on converted users** (filter to `converted==1` subset). Analyzing the full sample (including $0 from non-converters) conflates conversion rate and revenue-per-converter, making the metric uninterpretable. Report both: overall revenue-per-user (conversion × revenue|converted) and revenue|converted separately.
(i) **Assumption checks**: Before t-test or ANOVA, verify (i) normality (Shapiro-Wilk for n<5000, or QQ-plot visual check; if p<0.05 reject normality), and (ii) homogeneity of variance (Levene test; if p<0.05 reject equal variance). If either fails, use non-parametric alternatives (Mann-Whitney U) or bootstrap CIs. Report which assumptions were checked and whether they held.
15. Cross-check every important finding with at least one alternative method; if none fits, label the claim directional, not reliable. **Important finding** = any claim where p < 0.05 and the effect size exceeds the minimum practically meaningful threshold (ask the user or use domain defaults: 2% for conversion rates, 0.2 SD for continuous outcomes, 10% relative change for business metrics).
16. Produce charts and a concise report. **Charts are not optional** — every analysis type has a minimum required chart set defined in `references/chart-catalog.md` → "Minimum Required Charts by Analysis Type". Cross-check that section and produce all required charts for the matched analysis type (A/B test, driver ranking, regression, time series, SPC, root cause, or anomaly detection). For each required chart: (a) call the appropriate `ds_skill.plotting` function or generate with matplotlib/seaborn, (b) save the figure to a file with a descriptive name (e.g., `chart_1_timeseries_with_anomalies.png`), (c) reference the saved file path in the report. If a required chart is skipped, state why in the report. Use `references/report-standard.md` for report structure. **Report must include a "Tested but rejected" or "No evidence for" section** listing features/hypotheses that were tested but showed no significant effect (anti-pattern line 303: omitting negative findings hides what was tested). Example: "Tested but rejected: recipe (ρ=0.03, p=0.62), waiting_time (ρ=-0.01, p=0.88) — neither shows significant association with yield."
17. **Clean up temporary artifacts.** After delivering the final report: (a) if a temporary virtual environment was created for this analysis (not a user's existing pyenv/conda environment), remove it with `rm -rf .venv/` or `deactivate && rm -rf $VIRTUAL_ENV`; (b) delete intermediate test files and temporary scripts (e.g., `test.py`, `temp_*.csv`) from the working directory; (c) keep only the final deliverables (report, charts, processed data, reproducible analysis script). List what was cleaned in a brief cleanup summary. Skip cleanup if the user explicitly asks to keep intermediate files or if working in a shared/persistent notebook environment.

### Shortcut Routing — Skip Stages When The Request Is Narrow

Not every request needs all 14 steps. Route these common shapes directly (full rules in `references/workflow.md` → "When To Skip Stages").

**Record the route (Gate 1):** the first line of work is always `route: <route> — <reason>`. The route also determines which artifacts are owed: `full` → all Tier-0 artifacts; `profile-only` → `data_manifest` + `readiness_report` only (no `analysis_plan`, no `evidence_matrix` — no claims are made); `named-method` → `readiness_report` + assumption checks + `final_report`; `blocked` → `data_manifest` + `readiness_report` + `data_request`.

**Trigger condition table** (check user's exact words):

| User request pattern | Route | Execute steps | Rationale |
|---------------------|-------|---------------|-----------|
| "mean of X", "calculate Y", single stat | one-off | inline answer | No readiness/planning needed |
| "quick look", "just profile", "先看看数据", "profile 一下" | profile-only | 1-5, skip 6-14 | Data understanding, no claims |
| "run a t-test on...", explicit method | named-method | 1-5, 7 (assume check), 11-14 | Skip method *selection*, validate assumptions |
| "全套分析", "analyze this data", "分析数据", "找出影响 Y 的因素" | **full pipeline** | 1-14 | Default: complete workflow |
| Readiness scores `blocked` on a gating dimension | blocked | 1-5, then `data_request` + stop | Never force conclusions |

**Boundary rules:**
- **Default to full.** Any analysis verb without an explicit narrowing word ("analyze", "分析", "找原因", "why did X change") → `full`. The shortcuts are exceptions for *clearly* narrow requests, not a way to reduce work on ambiguous tasks.
- A narrowing word only counts when it describes the *whole* request: "快速 profile 一下，然后做全套分析" → `full`.
- `named-method` requires the user to name a concrete statistical method; naming a metric ("compare conversion") is NOT named-method — that's `full` (or one-off if a single descriptive number suffices).
- If torn between two routes → take the wider one.

Detailed shortcut rules:

- **One-off statistic** on an already-profiled column ("mean of X") → answer inline; skip readiness, planning, and critic.
- **User names a specific method** ("run a t-test on Y by line") → respect the choice and skip method *selection*, but still run readiness + shaping, **check the named method's assumptions, and offer the registry alternative if an assumption fails** (unequal variance → Welch t; skewed or n<20/group → Mann-Whitney; >2 groups → ANOVA/Kruskal-Wallis). 🔴 **CHECKPOINT: If assumptions fail, present the alternative and get confirmation before switching** (in `auto` mode: run the alternative as primary, report the named method alongside it with a caveat). Any method switch must be recorded in `analysis_plan.rejected_alternatives` with the failed assumption as the reason. Then execute + critic. Never silently run a method whose assumptions are violated.
- **Profile-only** ("just profile this") → run intake + readiness, emit `data_manifest` + `readiness_report`, then stop before method planning — no claims, so no critic.

## Failure Modes & Recovery

When a stage hits a wall, do not abort the whole analysis. Each row is a three-step fallback: try the first-line fix, escalate to the fallback, and only then stop with a concrete ask.

| Trigger condition | First-line fix | If that still fails |
|---|---|---|
| **File unreadable / wrong encoding** | retry with explicit encoding + delimiter sniff; sample first 1000 rows | return a data-request naming the format needed; do not invent a manifest |
| **No plausible target `Y`** | propose ranked candidates from column roles; ask once (guided) | fall back to `exploratory` profile-only mode; report what's needed to define `Y` |
| **Python environment inadequate** | detect active pyenv/conda/venv with `which python` and test key imports (pandas, numpy, scipy); if imports fail, check if `pip install` is available | 🔴 CHECKPOINT: ask user "Install missing packages to the current environment, or create an isolated venv?"; create a venv only on user confirmation (see Environment policy in step 2) |
| **Virtual environment creation fails** | retry with `python3 -m venv .venv` instead of `virtualenv`; check disk space | ask user to manually create environment or use system Python; document chosen fallback in analysis metadata |
| **Dependency installation fails** | retry with `--no-cache-dir` and `--upgrade pip`; try installing packages individually to isolate the failing one | report missing dependencies + minimal reproduction command; offer to run analysis with available packages only (degraded mode) |
| **Readiness = blocked** (leakage / sparse / mixed grain) | apply the data-readiness narrowing (drop leaked col, restrict to adequate-N subset) | emit the `data_request` artifact and stop downstream stages — never force a conclusion |
| **Shaping collapses sample** (post-filter N too small) | loosen the filter or pick a coarser grain that preserves N | bounce to readiness with the new N; narrow the question to what survives |
| **Join match-rate too low** | normalize keys (strip/case/dtype); try `merge_asof` with tolerance | report per-join match rate; drop the join and analyze sources separately |
| **Every candidate method rejected** | swap to the non-parametric / robust alternative in `method-registry.md` | emit a "method-blocked" note; never run a method whose assumptions fail |
| **Primary method errors at runtime** | run the registered alternative for that claim | mark the claim `unsupported`, keep other claims; record the failure, don't abort |
| **Primary and cross-check disagree** | reconcile (confound, Simpson, sample diff) | downgrade to directional signal with the disagreement stated; never silently pick one |
| **Helper import fails** (`ds_skill` off path) | run the `sys.path` bootstrap in "Make the helpers importable" | fall back to task-specific code and say so; don't skip the analysis |
| **Charts unavailable** (matplotlib/seaborn missing) | `pip install matplotlib seaborn` or `pip install -e ".[viz]"` | deliver text + tables, note charts were skipped and why |
| **Cleanup blocked** (permission denied on .venv) | try with elevated command or check if directory is in use | skip cleanup for that artifact; warn user about leftover files with manual cleanup command |

Stage-to-stage bounces (readiness ↔ shaping, planner → reframe, critic → re-run one claim) are spelled out in `references/workflow.md` → "Loops And Bounces". Loop only the affected stage; never restart from intake.

## Required Artifacts

For non-trivial analyses, create or summarize these artifacts. **Tier 0 artifacts are mandatory for all analyses; Tier 1 are strongly recommended for quality/auditability.**

### Tier 0 (Mandatory)
- `data_manifest`: source files/tables, row counts, columns, sheets, detected field roles. Format: JSON or structured text.
- `analysis_plan`: selected methods, alternatives considered, assumptions, helper usage decisions, charts planned. Format: JSON following the structure in step 11. **This is the audit trail for method selection.**
- `final_report`: conclusions, charts, limitations, and recommended next actions. Format: Markdown with embedded chart references.

### Tier 1 (Strongly Recommended)
- `data_profile`: missingness, uniqueness, ranges, category counts, time coverage, suspicious values. Format: CSV or JSON.
- `analysis_goal`: user goal, target `Y`, candidate drivers `X`, unit of analysis, filters. Format: JSON (embedded in analysis_plan if stand-alone artifact not created).
- `readiness_report`: **8-dimension scores** (`ok`/`partial`/`blocked` per dimension, per `references/data-readiness.md`), overall decision (`ok`/`partial`/`blocked`), plus evidence and remediation per dimension. Format: JSON whose envelope matches `data-readiness.md`. **This gates data quality.**
- `evidence_matrix`: findings by method, agreement/disagreement, confidence level (Tier 1/2/3). Format: JSON or Markdown table.

### Tier 2 (Situational)
- `analysis_views`: any reshaped or aggregated datasets and what information they lose. Only if reshaping occurred.
- `execution_log`: which workflow steps were executed, skipped, or shortcut; reasons for each decision. Format: JSON array. Useful for debugging workflow issues.

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

## Domain Rules — Financial Time Series

When the data is stock / crypto / fund / market-factor data (price columns, OHLCV, tickers, factor panels):

- **Targets**: raw price level (`close`) is valid for *descriptive trend* statements only. For driver ranking, factor analysis, or any predictive claim, default to returns — `log_return_1d`, `forward_return_5d/20d`, or excess return vs a benchmark when one exists. Present the target choice to the user as price-level (descriptive) vs returns (driver/predictive).
- **Target-derived features**: anything computed from the target series (momentum, moving averages, volatility of `Y`) must be tagged `target_derived` and excluded from driver ranking. They may appear only as technical-state descriptors, never as "drivers".
- **Stationarity & autocorrelation**: do not run plain correlation/regression on price levels; use returns or state the non-stationarity caveat and downgrade the claim to directional.
- **No investment advice**: do not produce buy/sell/hold, position-sizing, or stop-loss recommendations unless the user explicitly asks for trading-strategy analysis. Phrase results as analytical scenarios and risk indicators.

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

- `scripts/profile_dataset.py`: standalone CLI + importable profiler for CSV, Excel, Parquet, JSON. Emits the `data_manifest` JSON. Run `python profile_dataset.py <file>`. CSV/TSV/JSON work out of the box; **Excel and Parquet need the optional engines** (`pip install openpyxl pyarrow`, or `pip install -e ".[io]"`) — the script fails with that exact hint if they're missing.
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
- **Cite known spec ranges or optimal zones** when reporting process/manufacturing parameter effects. Example: "temperature shows optimal yield at 180-200°C" not just "temperature affects yield". If the data reveals a range (via binning, quantiles, or piecewise analysis) but no documented spec exists, report the data-driven range with caveat "optimal range observed in data: X-Y, pending process validation."
- Preserve reproducibility: record transformations, filters, random seeds, and package versions for every stochastic or version-sensitive step.

## Anti-Patterns — Red-Flag Blacklist

🚫 These failure modes silently corrupt an analysis. Scan this list before reporting any claim; each maps to a recovery action. If a stakeholder asks for one of these, explain the risk instead of complying silently.

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Report p-value as business impact** | large N (n>1000) makes trivial effects "significant"; significance ≠ magnitude | pair every p with effect size + units + CI |
| **Conclude on leaked features** | post-outcome / target-derived `X` inflates accuracy; won't replicate | run the leakage scan (data-readiness dim 6) first; drop offenders |
| **Force a conclusion on sparse data** | n<5 per cell, >30% missing on `Y`, or constant `Y` → any test is noise | report descriptive-only; route the question to Tier 3 unsupported |
| **Causal language on observational data** | "X causes Y" needs an experiment or quasi-experiment | use "associated with" / "predicts" / "differs by" unless a causal design exists |
| **Correlate against same-row outcomes** | features measured *after* or *alongside* Y (same timestamp, same event) may be effects not causes | verify time order; exclude concurrent/post-event features from driver ranking |
| **Skip pivot on entity×attribute long data** | driver ranking on unpivoted data mixes entity-level signal with measurement-type noise | pivot to entity-level (one row per wafer/patient/customer, attributes as columns) before ranking drivers |
| **Aggregate away the signal** | group-mean hides Simpson's paradox and station-level failure modes | check within-group before declaring a pooled effect |
| **Cp/Cpk on an unstable process** | capability on an out-of-control process is a meaningless number | confirm SPC stability first; compute capability on the in-control segment only |
| **Single method, no cross-check** | one test can fire on an artifact; no triangulation | every Tier-1 claim needs a second method agreeing in direction |
| **Silently impute `Y`** | inventing the target biases every downstream estimate | never impute `Y`; imputing `X` requires a documented, reported strategy |
| **Refit control/CV limits on the judged data** | circular — the limits always "fit" | hold out a known in-control window / keep train-test separation |
| **Pick a method by name or popularity** | impressive ≠ defensible; the data shape decides | choose by purpose + data type + assumption fit (`method-registry.md`) |
| **Create a venv when a working environment exists** | interrupts the user, wastes time, litters the workspace | test the active environment first; use it and record versions (see step 2) |
| **Rank drivers against a raw price level** | non-stationary series produce spurious correlations | use returns / forward returns / excess returns (see Domain Rules) |
| **Call a target-derived feature a "driver"** | mechanically correlated with `Y`; not an independent explanation | tag `target_derived`, exclude from driver ranking |
| **Silently exclude weak features** | omitting "X has no effect" hides what was tested; reader assumes you didn't check | explicitly state negative findings: "recipe, waiting_time tested, no significant effect (p>0.05, ρ<0.1)" |
| **Claim "comprehensive analysis" when readiness = partial** | over-promises; hides what was dropped | state the `narrowed_scope`: what is answerable, what is not, and why |

When you catch yourself about to do any of these: stop, name the anti-pattern, and switch to the "do this instead" column.
