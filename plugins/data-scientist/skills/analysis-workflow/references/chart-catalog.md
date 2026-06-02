---
name: chart-catalog
description: Chart selection guide indexed by intent (distribution, comparison, relationship, time, composition). Maps each chart type to ds_skill.plotting function. Use when choosing visualization, need chart best practices, or plotting patterns. Triggers — visualize this, what chart to use, how to plot.
---


Index charts by analysis intent. Pick the chart that exposes the evidence; reject decoration. Every chart must carry units, N, missing count, and uncertainty where applicable.

## Universal Annotation Requirements

Every chart in any report MUST carry:

- Title stating the question, not the variable.
- Axis labels with units and time window.
- `N=` total, plus per-group `n=` for grouped charts.
- Missing count or percent if >0.
- Uncertainty (CI band, error bar, or stated SE) for any estimated quantity.
- Source/grain note if the data has been aggregated or filtered.

## Intent: Distribution (single variable)

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Histogram | Shape inspection, N >= 30, single var | N < 30 (use dot plot); bin choice changes story | Bin width, N, mean/median line | Default bins hiding multimodality |
| KDE | Smooth shape, comparing 2-3 distributions | N < 50; heavy ties; bounded support without correction | Bandwidth, N | Oversmoothing real bumps |
| ECDF | Compare exact quantiles, tail behavior, spec compliance | Audience unfamiliar with cumulative form | Spec lines, quantile markers, N | Treating step plateaus as zero density |
| Violin | Shape + summary in one, several groups | N < 30 per group; bounded data without trim | Inner box, per-group n | Mirrored kernel implies symmetry that may not exist |
| Boxplot | Robust summary, outliers, many (>5) groups | Need to see modality; very small n (<10 per group) | Whisker rule, outlier rule, n per box | Hiding bimodality; comparing boxes of vastly different n without note |

## Intent: Comparison Across Groups

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Grouped boxplot | 2-15 groups, numeric Y | >20 groups (use ranked dot-plot); very unequal n (>5:1 ratio) without note | Group n, units, reference line | Sorting alphabetically when magnitude-sorted reads better |
| Swarm / strip | Small N per group (5-50), show every point | N > 200 per group (use box+violin); overlapping crush | Jitter amount, n | Hiding overlap with opaque markers |
| Dot-plot with CI | Compare estimated means/medians/rates across groups | Raw distribution matters more than estimate | CI method, CI level, n | Plotting point estimates without CI |
| Paired line | Repeated measures on same unit, before/after | Independent groups; >50 lines without alpha | Slope direction legend, n pairs | Reading group mean shift from a paired chart |
| Forest plot | Many (>5) group estimates with CIs, meta-style | Few groups (<5) (use dot-plot) | Effect metric, CI level, n | Mixing effect metrics on one axis |

## Intent: Correlation / Dependency

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Scatter + fit | Two numerics, N < 5,000 | N > 10,000 (use hexbin); heavy ties | Fit method, R^2 or rho, CI band, N | LOESS over noise; extrapolating fit past data |
| Hexbin / 2D density | High N (>5,000) bivariate | N small enough to show points | Bin count, color scale legend, N | Log-color scale unlabeled |
| Correlation heatmap | Many numerics, scan for structure | Only 2-3 vars (use scatter); mixed types | Method (Pearson/Spearman), N, masking of non-significant | Treating Pearson on skewed data as meaningful |
| Parallel coordinates | Multi-numeric per row, find clusters / outlier rows | >10 dims; >500 rows without alpha | Axis scaling rule, N | Order-dependent reading without justification |
| Pair plot | <=6 numerics, exploratory | Many vars (use focused scatters) | Diagonal type, N | Treating every panel as a finding |

Reject for correlation intent: dual-axis line over time (always misleading); 3D scatter for static reports.

## Intent: Composition

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Stacked bar | <=6 categories, compare composition across few groups | Many categories; need exact part values | Total N per bar, % vs count axis | 100% stacks without showing N differences |
| Treemap | Hierarchical part-of-whole, many parts | Few parts (use bar); precise comparison required | Total, units, hierarchy levels | Color encoding adding a 4th unread dimension |
| Mosaic | Two-way contingency with proportions | More than 2 categorical dims; small cell counts | N, expected vs observed shading | Reading shading without legend |
| Donut / bar | Single-level part-of-whole, <=5 parts | >5 parts; precise ranking needed | N, % labels | Donut over bar (bar reads more precisely) |

Reject for composition intent: pie chart with >5 slices; 3D pie chart always; exploded pie.

## Intent: Time Series

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Line with bands | Single or few series, uncertainty matters | >5 series (use small multiples); irregular sampling unnoted | Band meaning (CI/PI/SD), units, frequency | Connecting across gaps without break |
| Small multiples | Many series, same scale | Series need direct comparison at instants | Shared y-scale or marked free, n per panel | Free y-scales without warning |
| Calendar heatmap | Daily/sub-daily, seasonal/weekly patterns | Long horizons without zoom; sparse data | Color scale, missing day color | Reading magnitude without scale |
| Change-point overlay | Trend with detected regime shifts | Pre-deciding the breakpoint without method | Detection method, threshold, CI of breakpoint | Annotating breaks that fit one method only |
| Decomposition (STL) | Separate trend / seasonal / residual | Non-stationary sampling | Period, method, residual scale | Reading residual spikes as anomalies without test |

Reject for time intent: dual-axis line (use small multiples); secondary axis bar+line combos.

## Intent: Process / SPC

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| I-MR | Individual continuous measurements, no rational subgroup | Subgroups exist (use Xbar) | UCL/LCL formula, n, rules applied | Recomputing limits on the same data being judged |
| X-bar / R | Rational subgroups of size 2-10, continuous | Subgroup size 1 (use I-MR) or >10 (use Xbar-S) | Subgroup size, period, rule list | Treating out-of-control as bad without cause check |
| p-chart | Defect proportion, variable subgroup size | Defect counts (use c/u) | Subgroup n per point, rules | Constant-limit p-chart when n varies a lot |
| c-chart | Defect counts per equal opportunity unit | Opportunity varies (use u-chart) | Unit definition, period | Mixing defect types into one count without justification |
| u-chart | Defect rate per variable opportunity | Equal opportunity (use c-chart) | Opportunity definition, n | Ignoring overdispersion |
| Pareto | Rank causes / defect types, find vital few | Few categories (use bar); equal magnitudes | Cumulative line, N, 80% reference | Including "Other" as a tall bar that hides specifics |

Cross-link: see `manufacturing-playbook.md` SPC and capability recipes for rule selection.

## Intent: Anomaly / Outlier

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Boxplot residuals | Inspect model fit residuals by group | No model fit yet | Residual definition, n, IQR rule | Treating box outliers as anomalies without context |
| Scatter with flagged points | Bivariate anomalies, show context | High N without aggregation | Flag method, threshold, count flagged | Showing flags without the rule that produced them |
| Control-chart overlay | Time-anchored anomalies | Non-time data (use IQR/IsolationForest plots) | Rules triggered, period | Cherry-picking the rule that fires |
| Residual histogram + QQ | Check residual normality, find fat tails | Non-regression context | Reference line, n, test statistic | Eyeballing normality without test |

## Intent: Hierarchical / Multi-Dimensional

| Chart | Use when | Reject when | Annotation | Common mistakes |
|---|---|---|---|---|
| Faceted grid | Same chart across a categorical dim | >12 facets without paging | Shared scales, per-facet n | Free scales hiding magnitude differences |
| Parallel coordinates | Find row-level multi-dim patterns | High N without sampling | Axis order rationale, n | Confusing axis order with importance |
| Heatmap (group x group) | Two categoricals + one numeric summary | Sparse cells; >30 categories per axis | Cell n, color scale, missing color | Reading color magnitude without legend |
| Sankey | Flow between stages | Static composition (use stacked bar) | Flow units, totals | Visual width not matching value |

## Default Chart Per Method (cross-reference)

Method groups listed below come from `method-registry.md`. Do not edit that file; use this as the lookup for what chart accompanies each method output.

| Method group (method-registry section) | Default chart | Secondary chart |
|---|---|---|
| Compare Groups: Welch / Student / Paired T | Dot-plot with CI; paired line (paired) | Grouped boxplot |
| Compare Groups: Mann-Whitney U | Grouped boxplot | ECDF overlay |
| Compare Groups: One-Way / Welch ANOVA | Dot-plot with CI per group | Grouped boxplot |
| Compare Groups: Kruskal-Wallis | Grouped boxplot | ECDF per group |
| Compare Groups: Chi-Square / Fisher Exact | Mosaic | Proportion bar with CI |
| Explain Drivers: Spearman / Pearson Correlation | Scatter + fit | Correlation heatmap (multi-var) |
| Explain Drivers: Linear Regression | Coefficient forest plot | Residual histogram + QQ |
| Explain Drivers: Logistic Regression | Coefficient forest plot (OR) | Response curve with CI |
| Explain Drivers: Tree-Based Models | Feature importance bar | Partial dependence / ALE |
| Monitor Stability: I-MR | I-MR control chart pair | Run chart with rules |
| Monitor Stability: Xbar-R / Xbar-S | Xbar-R/S chart pair | Subgroup boxplot |
| Monitor Stability: p / np Chart | p-chart | Defect Pareto |
| Monitor Stability: c / u Chart | c or u chart | Defect Pareto |
| Process Capability: Cp/Cpk, Pp/Ppk | Capability histogram with spec lines | ECDF with spec lines |
| Detect Change: Before/After Comparison | Paired line or before/after dot-plot | Time series with marker |
| Detect Change: Change Point Detection | Time series with change-point overlay | Residual chart post-segment |
| Find Anomalies: Robust Z / IQR | Scatter with flagged points | Boxplot with rule annotations |
| Find Anomalies: Isolation Forest | Score histogram + flagged scatter | 2D projection (PCA/UMAP) with flags |
| Predict Outcomes | Calibration / ROC / lift chart | Residual or confusion display |
| Explore Unknown Relationships | Pair plot or correlation heatmap | Parallel coordinates |

## Reporting Rules (apply to every chart)

- Pair every key chart with a small table of the underlying numbers.
- Never use a chart whose only value is decorative color or 3D depth.
- If a transformation is applied (log, standardized), say so in the title or caption.
- If the chart shows estimates, the uncertainty must be visible (band, bar, or stated).
- If groups have widely different n, annotate n directly on the chart.
- If outliers are removed for visual scale, state the rule and count removed.

---

## Anti-Patterns — Chart Selection Red Flags

🚫 These obscure evidence or mislead:

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| **3D charts for 2D data** | Perspective distorts perception, harder to read | Use 2D; add color/size if need 3rd dimension |
| **Pie chart with >5 slices** | Hard to compare angles, clutter | Use horizontal bar chart sorted by value |
| **Dual-axis with different scales** | Visually manipulates relationship strength | Separate charts or normalize to same scale |
| **Chart without units on axes** | Reader can't interpret magnitude | Always label axes with units (%, mm, $, count) |
| **Missing N or missing-count** | Hides sample size, sparse data looks solid | Annotate every chart with N and missing count |
| **Cherry-picked axis range** | Exaggerates small differences | Start Y-axis at 0 for counts/rates; use full data range |
| **Decoration over evidence** (excessive grid, 3D effects, clipart) | Distracts from data | Minimize ink; maximize data-ink ratio |
| **Too many lines on one chart** (>5 series) | Overlapping lines become unreadable spaghetti | Use small multiples (faceted panels), one series per panel |
| **Connecting discrete categories** (line chart for categorical X) | Implies continuity where none exists | Use bar/dot chart for categorical data |
| **Color without legend** | Reader can't decode color meaning | Always include legend or direct labels on chart elements |
| **Too many lines on one chart** (>5 series) | Overlapping lines become unreadable spaghetti | Use small multiples (faceted panels), one series per panel |
| **Connecting discrete categories** (line chart for categorical X) | Implies continuity where none exists | Use bar/dot chart for categorical data |
| **Color without legend** | Reader can't decode color meaning | Always include legend or direct labels on chart elements |

Pick the chart that exposes the evidence; reject decoration.

---

## Minimum Required Charts by Analysis Type

Not every chart is optional. Certain analysis types MUST produce a core set of charts to be considered complete. This section defines the **minimum chart set** for common analysis types.

### A/B Test Analysis

**Required (3 minimum)**:
1. **Conversion rate comparison with CI** — Dot plot showing control vs treatment rates with error bars (Wilson score CI). Annotate absolute lift and relative lift.
2. **Sample size check** — Bar chart showing arm sizes. Include expected 50:50 line if randomized.
3. **Revenue distribution by arm** (if revenue is measured) — Grouped boxplot or violin plot comparing revenue distributions. Include median, IQR, and per-arm N.

**Optional but recommended**:
- Funnel chart showing drop-off at each stage (if multi-step conversion)
- Time-series of daily conversion rates by arm (if duration > 7 days)

### Driver Ranking / Correlation Analysis

**Required (2 minimum)**:
1. **Correlation heatmap** — Show all numeric features vs target. Mask non-significant cells (post-FDR correction). Annotate method (Pearson/Spearman) and N.
2. **Top drivers chart** — Horizontal bar chart of top 5-10 features by |correlation| or standardized coefficient. Include uncertainty (CI or SE bars).

**Optional but recommended**:
- Scatter plots for top 3 drivers vs target (with fit line and R²)
- Pair plot if dimensionality ≤ 6 and exploratory analysis requested

### Regression / Prediction Modeling

**Required (4 minimum)**:
1. **Actual vs Predicted scatter** — Y-axis = actual, X-axis = predicted. Include y=x reference line, R², and RMSE.
2. **Residuals vs Fitted** — Check homoscedasticity. Flag patterns indicating non-linearity or heteroscedasticity.
3. **Residuals Q-Q plot** — Check normality assumption. Include reference line.
4. **Feature importance** — Bar chart of standardized coefficients (linear) or permutation importance (tree-based). Include sign and magnitude.

**Optional but recommended**:
- Residuals by group (if categorical features exist)
- Learning curve (train vs validation score by sample size) if overfitting suspected

### Time Series Analysis

**Required (3 minimum)**:
1. **Raw time series line plot** — Show original data with any detected change-points or anomalies overlaid. Include N, frequency, and missing periods.
2. **Seasonal decomposition** — STL or similar showing trend, seasonal, and residual components. Annotate period and method.
3. **Autocorrelation (ACF) plot** — Show lag structure up to lag 40 or 2 periods, whichever is shorter. Include significance bands.

**Optional but recommended**:
- Forecast with prediction interval (if forecasting requested)
- Rolling mean/std to show variance stability
- Calendar heatmap for daily/hourly patterns

### Manufacturing / SPC Analysis

**Required (3 minimum)**:
1. **Control chart** — I-MR, X-bar/R, p-chart, or c-chart depending on data type. Include UCL/LCL, center line, out-of-control points flagged with rule number.
2. **Capability histogram** — Show process distribution overlaid with spec limits (LSL/USL) and normal curve. Annotate Cp, Cpk, and % out-of-spec.
3. **Pareto chart** — Rank defect types or root causes. Include cumulative % line and 80% reference.

**Optional but recommended**:
- Box plot by operator / line / shift (if categorical factors present)
- Run chart (chronological order without control limits) if process is evolving

### Root Cause / Group Comparison

**Required (2 minimum)**:
1. **Grouped box/violin plot** — Show target variable (Y) by suspected driver groups. Include per-group N, median, and F-statistic or p-value from ANOVA/Kruskal-Wallis.
2. **Effect size with CI** — Dot plot showing mean difference (or median difference) between groups with 95% CI. Include practical significance threshold line.

**Optional but recommended**:
- Interaction plot if two categorical factors suspected to interact
- Paired line chart if repeated measures (before/after)

### Anomaly Detection

**Required (2 minimum)**:
1. **Scatter or time series with flagged anomalies** — Show original data with detected anomalies highlighted. Annotate detection method, threshold, and count flagged.
2. **Score distribution** — Histogram of anomaly scores (e.g., IsolationForest score). Show threshold cutoff and % flagged.

**Optional but recommended**:
- Bivariate scatter (if 2D anomaly detection)
- Control chart overlay (if time-ordered data)

---

### Enforcement Rule

When completing an analysis, cross-check the **Required** charts for the analysis type. If any are missing, explain why they were skipped (e.g., "control chart skipped because process is non-stationary") or produce them before finalizing the report.

**Default**: If unsure which analysis type fits, produce at minimum:
1. Distribution of target variable (histogram or boxplot)
2. Top 3 relationships (scatter or grouped comparison)
3. One diagnostic chart (residuals, control chart, or Q-Q plot depending on method used)
