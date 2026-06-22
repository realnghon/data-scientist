---
name: data-shaping
description: Reshape playbook for building analysis views (join, pivot, melt, aggregate, window ops). Pick grain, record information loss, check leakage. Use when raw data doesn't match analysis unit, need to combine sources, or aggregate. Triggers — reshape data, wrong grain, join tables, pivot/unpivot, analysis view.
---

# Data Shaping

Reshape playbook for [workflow.md](workflow.md) Stage 3. Every shaping step produces a **named analysis view** with explicit grain, dropped columns, filters, and aggregation rules. Downstream methods (see [method-registry.md](method-registry.md)) bind to a view, not to the raw table.

Core principle: the source table is *not* the analytical table. Shape it deliberately.

---

## Table of Contents

1. [Grain Decisions](#1-grain-decisions) — what does one row represent?
2. [Aggregations](#2-aggregations) — collapsing rows safely
3. [Pivots and Melts](#3-pivots-and-melts) — wide ↔ long transforms
4. [Filters and Drops](#4-filters-and-drops) — information-loss accounting
5. [Joins](#5-joins) — combining sources
6. [Leakage Points During Shaping](#6-leakage-points-during-shaping) — audit every transform
7. [Resulting `analysis_views` Catalog](#7-resulting-analysis_views-catalog)
8. [Output Template — `analysis_views[]`](#8-output-template--analysis_views)
9. [Decision Quick-Reference](#decision-quick-reference)
10. [Anti-Patterns](#anti-patterns--shaping-red-flags)

---

## 1. Grain Decisions

**Grain = what one row represents** after shaping. Pick it first; everything else follows.

| Grain | One row is | When to use |
|---|---|---|
| raw-event | a single observation (sensor reading, inspection, transaction) | row-level modeling; needs independence |
| entity | a product / wafer / customer / serial | entity-level features, lifetime metrics |
| batch / lot | a production batch | batch-level yield, capability |
| time-bucket | one entity at one (hour/day/week) | trend, SPC, rate metrics |
| group | one (machine / line / shift / supplier) | group comparisons, ranking |
| event-pair | a before/after change of state | event-driven survival, transitions |

**Aggregation collapses information.** Always document what the chosen grain *loses*:

- entity grain over raw-events → loses within-entity variation.
- time-bucket grain → loses sub-bucket cadence; bucket size choice matters.
- group grain → loses entity-level identifiability; can mask Simpson's-paradox.

Rule: when in doubt, build the finer-grain view first and aggregate from it. Never aggregate, lose the raw, then try to recover.

---

## 2. Long ↔ Wide

### Long form

Columns: `id, time, metric_name, metric_value` (plus any group cols).

Use long when:
- many heterogeneous metrics flow through the same analysis (melted EDA).
- new metrics are added often (no schema churn).
- per-metric filtering/aggregation is the main op.

### Wide form

Columns: `id, time, metric_1, metric_2, ...` (one column per variable).

Use wide when:
- modeling: each metric is a feature column (regression, classification, correlation matrix).
- pivot tables, cross-tabs, paired comparisons.
- joining multiple metrics into a single observation.

### Pandas idioms

```python
# Long → wide
wide = (long
    .pivot_table(index=["id", "time"],
                 columns="metric_name",
                 values="metric_value",
                 aggfunc="mean"))     # explicit aggfunc; pivot_table needs it if duplicates exist
wide.columns.name = None
wide = wide.reset_index()

# Wide → long
long = wide.melt(id_vars=["id", "time"],
                 var_name="metric_name",
                 value_name="metric_value")

# Safer: assert grain before reshape
assert wide.duplicated(subset=["id", "time"]).sum() == 0, "wide grain broken"
```

---

## 3. Pivot / Unstack

Pivots collapse rows into columns. Information loss occurs **when duplicates exist at the pivot key** — they get aggregated.

Before pivoting:
1. `df.duplicated(subset=[index_keys, columns_key]).sum()` — must equal 0 for lossless pivot.
2. If non-zero: choose `aggfunc` consciously per metric type:

| Variable role | Default aggfunc | Why |
|---|---|---|
| numeric measure (temperature, pressure) | `mean` (or `median` if skewed) | central tendency |
| numeric count (defects, events) | `sum` | counts add |
| numeric rate (yield %) | weighted mean (denominator-weighted) | unweighted mean is wrong |
| binary outcome | `mean` (= proportion) or `max` (= ever-true) | depends on question |
| categorical / label | `mode` (or first/last) | document tie-break |
| timestamp | `min` / `max` / `first` / `last` | depends on semantics |

Document the choice in the view's aggregation rule.

---

## 4. Aggregation Rules

Aggregating by group / time bucket / entity:

```python
agg = (df
    .groupby(["line", "shift_date"], dropna=False)
    .agg(yield_pct = ("passed", "mean"),
         n_units   = ("passed", "size"),
         defects   = ("defects", "sum"),
         temp_p95  = ("temp",    lambda s: s.quantile(0.95))))
```

Always carry `n_units` (or equivalent denominator) into the aggregated view. Without it, downstream methods can't weight or assess reliability.

Mixed grains: if the source has both unit-level and batch-summary rows, split them with a row-type flag and aggregate them separately to a common grain. Never `groupby` over mixed grains directly.

---

## 5. Joins

🔴 **CHECKPOINT**: 在执行 join 之前，确认 join 类型和验证策略。错误的 join 会导致行数爆炸或数据静默丢失，且难以事后发现。

| Pitfall | Symptom | Fix |
|---|---|---|
| 1:N inflation | row count after join > expected | check `merge(..., validate="one_to_one"|"one_to_many"|"many_to_one")`; aggregate the many-side first |
| time-window join | quality events tied to wrong shift / batch | use `merge_asof` with `tolerance` and `direction` |
| fuzzy keys | trailing whitespace, casing, type mismatch | normalize keys explicitly: `df["k"] = df["k"].str.strip().str.upper()` and assert dtype equality |
| many-to-many | combinatorial explosion | pre-aggregate at least one side |
| left join silently drops | unmatched right side → NaN in critical column | report match rate per join; fail if below threshold (e.g., <95%) |

```python
# Time-window join: align inspection rows to the latest sensor reading <= inspection time
joined = pd.merge_asof(
    inspections.sort_values("ts"),
    sensors.sort_values("ts"),
    on="ts",
    by="line_id",                   # join only within same line
    direction="backward",
    tolerance=pd.Timedelta("5min"),
)
```

Always report `join_match_rate = matched_rows / left_rows` in the view metadata.

---

## 6. Leakage Points During Shaping

The leakage taxonomy and gating rules live in [data-readiness.md](data-readiness.md) dim 6; this section covers the transform-time slips that introduce it. Audit every transform:

- **Post-outcome columns merged in.** If `Y` is `is_defective`, any column populated by the failure-analysis team after defect detection is leaked. Drop or restrict to pre-`Y` snapshot.
- **Future timestamps.** Rolling features computed with a window that includes the current row's outcome time. Use a lag: `rolling(window).shift(1)` before any aggregation that feeds `X`.
- **Target-derived features.** Encodings like target-mean-by-group computed on the full dataset. Compute only on training fold.
- **Global statistics (mean, std) for normalization.** Compute on training fold; apply (not refit) on the rest.
- **Sort-order leakage.** Sorting by `Y` then taking top-k as a feature ranks information about `Y` itself.
- **Aggregation-window leakage.** Daily aggregation that groups by a column also populated by the daily outcome.

Each view records a `leakage_checks` block listing the audits performed.

---

## 7. Resulting `analysis_views` Catalog

Every shaping outputs a named view. Catalog them:

| View name | Grain | Typical methods |
|---|---|---|
| `raw_row` | source row | row-level regression, classification, anomaly |
| `entity_summary` | one row per entity | entity-level driver ranking, group comparison |
| `group_summary` | one row per (group [×period]) | group comparison, ranking |
| `time_bucket` | one row per (entity?, period) | trend, change-point, SPC |
| `event_pairs` | one row per state transition | survival, duration, A/B |
| `long_metrics` | (id, time, metric_name, value) | bulk metric EDA |
| `wide_features` | one row per analysis unit, one col per `X` | regression, classification |

Each entry in `analysis_views[]` carries: name, grain, source ops chain, filters applied, drops, aggregations, leakage checks, n_rows, n_cols, join match rates.

---

## 8. Output Template — `analysis_views[]`

```json
{
  "analysis_views": [
    {
      "name": "wafer_wide_features",
      "grain": "one row per wafer_id",
      "source_ops": [
        {"op": "filter",    "expr": "inspection_stage == 'final'"},
        {"op": "join",      "right": "process_params", "how": "left", "on": ["wafer_id"], "validate": "one_to_one", "match_rate": 0.992},
        {"op": "pivot",     "index": "wafer_id", "columns": "param_name", "values": "param_value", "aggfunc": "mean"},
        {"op": "dropna",    "subset": ["is_defective"]}
      ],
      "filters_applied": ["inspection_stage == 'final'", "fab_site == 'A'"],
      "columns_dropped": ["root_cause", "rework_notes"],
      "drop_reason":     "post-outcome leakage (see data-readiness.md leakage dimension)",
      "aggregations":    [{"column": "temp_zone3", "func": "mean", "rationale": "duplicate sensor reads per wafer"}],
      "leakage_checks": {
        "post_event_columns_removed": ["root_cause", "rework_notes"],
        "future_timestamps_used":     false,
        "target_derived_features":    [],
        "global_stats_fit_on_train_only": true
      },
      "n_rows": 18432,
      "n_cols": 47,
      "y_column": "is_defective",
      "x_candidates": 45,
      "warnings": ["8 wafers had 2+ rows in process_params; mean-aggregated"]
    },
    {
      "name": "line_daily_summary",
      "grain": "one row per (line_id, calendar_date)",
      "source_ops": [
        {"op": "groupby", "by": ["line_id", "calendar_date"]},
        {"op": "agg", "spec": {"yield_pct": ["passed", "mean"], "n_units": ["wafer_id", "size"], "defects": ["defects", "sum"]}}
      ],
      "filters_applied": [],
      "columns_dropped": [],
      "aggregations": [
        {"column": "yield_pct", "func": "denominator_weighted_mean", "rationale": "rate metric"},
        {"column": "defects",   "func": "sum",                       "rationale": "count metric"}
      ],
      "leakage_checks": {"post_event_columns_removed": [], "future_timestamps_used": false},
      "n_rows": 1820,
      "n_cols": 5,
      "y_column": "yield_pct",
      "warnings": []
    }
  ]
}
```

---

## Decision Quick-Reference

| Question | View to build |
|---|---|
| "what affects Y?" | `wide_features` at the analysis unit of Y |
| "which group differs?" | `group_summary` with Y + group + n |
| "when did it change?" | `time_bucket` with consistent cadence |
| "is the process stable?" | `time_bucket` ordered + subgroup view for SPC |
| "is the process capable?" | `raw_row` + spec limits attached |
| "how long until X?" | `event_pairs` with censor flag |
| "what's typical for this metric?" | `long_metrics` for bulk profiling |

Every view emitted into `analysis_views[]` is the contract for Stage 4 method planning.

---

## Shaping Checkpoints

| Check | Why it matters | Action |
|---|---|---|
| **Declare grain explicitly** | Downstream must know the unit of analysis | Every view must state `grain` (row=?, entity=?, time=?) |
| **Log per-join match rate** | Low match rate means data loss or key mismatch | Investigate if match rate < 80% |
| **Record row-count delta** | Sample size collapses, analysis underpowered | Bounce to readiness if N < 20 |
| **Prefer long-form time** | Wide-form breaks time-series analysis | Keep time as rows unless explicitly needed for cross-tab |
| **Check within-group before pooled effects** | Group-mean hides Simpson's paradox | Verify within-group pattern |
| **Document every imputation** | Changes data, biases estimates | Record strategy in `analysis_views`; never impute Y |
| **Validate join-key uniqueness** | 1:N inflation duplicates rows, inflates significance | Ensure at least one side is unique; dedupe or aggregate first |
| **Use lagged rolling windows** | Window including current row leaks future information | Use `rolling(window).shift(1)` before aggregating features |
| **Fit scalers on training fold only** | Test set sees training distribution, overfit | Fit on train; apply (don't refit) to validation/test |

When shaping collapses sample size below readiness thresholds, bounce back to Stage 2 with the new N.

Scan [anti-patterns.md](anti-patterns.md) before finalizing any claim.
