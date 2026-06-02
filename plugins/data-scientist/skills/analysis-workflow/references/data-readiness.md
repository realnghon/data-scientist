---
name: data-readiness
description: 8-dimension data quality scorecard (sample size, missingness, grain, time coverage, balance, leakage, role clarity, measurement reliability) run before analysis. Use when need to gate downstream stages, narrow scope, or emit data-request. Triggers — is data good enough, what's missing, can we analyze this, readiness check.
---


Score the data **before** running methods. Output a structured `readiness_report` so downstream stages (shaping, method planning, critic) can react. See [workflow.md](workflow.md) Stage 2.

Each dimension is scored independently as `ok` / `partial` / `blocked`. The overall decision is the worst score *unless* an explicit workaround narrows scope.

---

## Dimensions

### 1. Sample Size Adequacy

Count rows per analysis cell (per group, per group×time bucket, per class).

| Per-cell n | Score | Notes |
|---|---|---|
| ≥ 30 | ok | parametric methods generally safe |
| 10–29 | partial | prefer non-parametric, report effect size + CI, avoid post-hoc multi-comparison |
| 5–9 | partial | exploratory only; bootstrap CIs |
| < 5 | blocked | no parametric test; report descriptive only |

For regression: enforce ≥10 rows per predictor (≥20 with regularization).
For classification: ≥30 in the minority class, or plan resampling.
For SPC: ≥20 ordered subgroups for limit estimation.

### 2. Missingness Pattern

Compute % missing overall, per column, per group, per time bucket.

| Signal | Likely mechanism | Score |
|---|---|---|
| missing uncorrelated with any observed feature | MCAR | ok if total <10%, partial 10–30%, blocked >30% on `Y` |
| missing depends on observed features but not on missing value | MAR | partial; require explicit imputation strategy |
| missing depends on the unobserved value itself | MNAR | blocked for any conclusion sensitive to that variable |

Tests: chi-square of missingness indicator vs candidate predictors; missingness-by-group bar chart.

Rule: never silently impute `Y`. Imputing `X` requires a documented strategy.

### 3. Grain Consistency

Pick **one** analysis grain. A table mixing grains is a red flag.

Diagnostics:
- `df.duplicated(subset=[id_keys]).sum()` — should be 0 at intended grain.
- Compare row count to `len(df.groupby(id_keys))`.
- Inspect random samples; multiple rows per `entity_id` at the same `time` = mixed grain.

| Result | Score |
|---|---|
| one row per intended unit | ok |
| duplicates that are *legitimate* repeated measures (documented) | partial; flag for aggregation in shaping |
| mixed grains (e.g. some unit-level rows + some batch-aggregate rows interleaved) | blocked until split or filtered |

### 4. Time Coverage

For any time-aware question:

| Check | Threshold | Score impact |
|---|---|---|
| total span vs question's cycle | ≥ 2 cycles | required for seasonality; else partial |
| gap fraction | < 10% of cells | gaps > 10% → partial; > 30% → blocked |
| sampling cadence | consistent | irregular cadence → partial, plan resampling |
| before/after window around an event | both ≥ 30 cells (or per-cell n adequate) | otherwise partial |
| time zone / shift boundary clarity | unambiguous | ambiguous → flag in critique |

### 5. Class / Group Balance

| Imbalance ratio (majority : minority) | Score |
|---|---|
| ≤ 3:1 | ok |
| 3:1 – 10:1 | partial; require balanced metric (PR-AUC, F1) |
| 10:1 – 100:1 | partial; require resampling or cost-sensitive loss |
| > 100:1 | blocked for standard methods; reframe as anomaly detection |

For group comparison: imbalance is fine as long as each group has adequate n; the imbalance itself isn't the blocker, small n is.

### 6. Leakage Risk

Inspect every candidate `X` against `Y` in time:

- **Post-event columns:** any field recorded after `Y` (e.g. `defect_root_cause` when predicting `is_defective`). Blocked if present in `X`.
- **Target-derived features:** field is a function of `Y` (e.g. `monthly_revenue` predicting `customer_value`). Blocked.
- **Time order violation:** `X.timestamp > Y.timestamp` for any row. Blocked.
- **Group-level leakage:** entity ID encoded in `X` and target also varies by entity → effectively memorizes. Partial; require entity-aware cross-validation.
- **Pipeline leakage:** scaler/imputer fit on full data before split. Partial; require fit-on-train-only.

Any single blocked sub-check makes the dimension blocked.

### 7. Variable Role Clarity

Confirm:
- `Y` is unambiguously identified (or user-confirmed in `guided`).
- `Y` has variation (constant `Y` → blocked).
- Candidate `X` set is plausible and non-trivial (> 0 fields after leakage check).
- Time, entity, group columns are typed correctly.

| Signal | Score |
|---|---|
| all roles confident, evidence in column names + dtypes + sample | ok |
| `Y` candidate but unconfirmed; or some roles uncertain | partial; ask once in `guided`, default in `auto` and flag |
| no plausible `Y` at all | blocked; redirect to exploratory profile |

### 8. Reliability Of Measurement

Cheap-to-check signals of unreliable input:
- Units mismatch (same column in mixed units — e.g. mm vs in).
- Sensor saturation (capped at min/max).
- Sentinel values (`999`, `-1`, `9999-12-31`) treated as numeric.
- Manual-entry artifacts (clustering on round numbers, typos).
- Timezone confusion across regions.

| Findings | Score |
|---|---|
| none detected | ok |
| 1–2 minor issues, fixable in shaping | partial; document fix |
| sentinel/saturation on `Y` or core `X`, or units mismatch | blocked until corrected at source |

---

## Overall Decision

Roll up the eight dimensions:

| Rule | Overall |
|---|---|
| any blocked, no workaround | `blocked` |
| any blocked but a scope narrowing makes it `partial` or `ok` | `partial` with `narrowed_scope` |
| all `ok` | `ok` |
| mix of `ok` and `partial` | `partial` with `caveats` |

Scope narrowing examples:
- Drop the time-series question, keep the group comparison.
- Drop the leaked feature, keep the rest.
- Restrict to the subset with adequate sample.

### Decision → downstream action

- `ok` → proceed full plan (Stage 3 shaping).
- `partial` → proceed with narrowed scope; every claim from a partial dimension must show its caveat in the report.
- `blocked` → skip Stages 3–7; emit the data-request artifact and return.

---

## Output Template — `readiness_report`

```json
{
  "decision": "ok | partial | blocked",
  "dimensions": {
    "sample_size":            { "score": "ok|partial|blocked", "evidence": { "per_cell_min": 42, "per_cell_median": 180, "rule_violations": [] }, "notes": "..." },
    "missingness":            { "score": "partial",            "evidence": { "overall_pct": 0.18, "by_column_top": [["sensor_3", 0.42]], "mechanism_guess": "MAR" }, "notes": "..." },
    "grain":                  { "score": "ok",                 "evidence": { "intended_grain": "one row per wafer", "duplicate_count": 0 }, "notes": "..." },
    "time_coverage":          { "score": "ok",                 "evidence": { "span_days": 365, "gap_fraction": 0.02, "cadence": "daily" }, "notes": "..." },
    "balance":                { "score": "partial",            "evidence": { "majority_minority_ratio": 8.4, "metric_recommendation": "PR-AUC" }, "notes": "..." },
    "leakage":                { "score": "blocked",            "evidence": { "post_event_cols": ["root_cause"], "target_derived": [], "time_order_violations": 0 }, "notes": "drop root_cause to recover" },
    "role_clarity":           { "score": "ok",                 "evidence": { "Y": "is_defective", "Y_variation": 0.07, "X_candidates": 23 }, "notes": "..." },
    "measurement_reliability":{ "score": "partial",            "evidence": { "sentinel_values": [["temp", -999, 12]], "unit_mismatch": [], "saturation_cols": [] }, "notes": "replace -999 with NaN in temp" }
  },
  "narrowed_scope": [
    "Drop driver analysis with post-event columns; keep group comparison by line.",
    "Restrict trend analysis to last 6 months due to cadence change."
  ],
  "caveats": [
    "Balance 8.4:1 — use PR-AUC, not accuracy.",
    "18% missingness in sensor_3 — document imputation."
  ],
  "data_request": null
}
```

When `decision == "blocked"`, populate `data_request` instead of `narrowed_scope`:

```json
{
  "data_request": {
    "blocking_reasons": ["post-event column root_cause leaks Y"],
    "fields_needed": ["all X candidates measured strictly before Y timestamp"],
    "grain_needed": "one row per wafer per inspection step",
    "coverage_needed": "at least 6 months continuous, at least 100 wafers per line",
    "target_definition": "is_defective in {0,1} at final-inspection stage",
    "methods_unblocked": ["driver ranking", "classification", "group comparison by line"]
  }
}
```

---

## Critic Hooks

The critic stage (see [workflow.md](workflow.md) Stage 6) re-reads `readiness_report` to:
- Verify every `partial` caveat actually appears next to the matching claim in the final report.
- Reject any conclusion that relied on a blocked-then-narrowed dimension without disclosure.
- Trigger sensitivity tests when readiness is borderline (e.g. min per-cell n in the 10–29 partial band).

---

## Anti-Patterns — Data Readiness Red Flags

🚫 These bypass quality gates and corrupt downstream results:

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| **Skip readiness, go straight to methods** | Quality issues surface mid-analysis after wasted work | Always run readiness first; gate all downstream on `decision: ok/partial` |
| **Force analysis on blocked readiness** | Sparse/leaked/mixed-grain data produces unreliable results | Stop at readiness, emit `data_request`, do not proceed to shaping/methods |
| **Ignore leakage warnings** (Dim 6: post-outcome fields in X) | Inflates accuracy, won't replicate on new data | Drop leaked columns before any modeling; re-run readiness |
| **Aggregate away grain issues** (Dim 3: mixing entity-level and batch-level) | Simpson's paradox hides; pooled result misleading | Reshape to uniform grain first (data-shaping.md); or analyze grains separately |
| **Proceed with <5 samples per cell** | Any statistical test result is noise | Narrow scope to adequate-N subset, or mark claim `unsupported` |
| **Impute target Y** | Inventing the outcome biases every estimate | Never impute Y; imputing X requires documented, reported strategy |
| **Ignore balance warnings** (Dim 5: 10:1 group imbalance) | Majority class dominates; minority effects lost | Stratify analysis, or note the imbalance as a limitation |
| **Run readiness once, reuse for changed data** | New data may have new quality issues | Re-run readiness when data sources or filters change |

When readiness blocks, the correct action is **stop and ask for better data**, not **force a conclusion anyway**.
