# Baseline Analysis: /Users/silaswu/Silas_Develop/data-scientist/evals/cases/case-08-readiness-blocked/dataset.csv

**Generated:** 2026-06-10T15:41:54.093419+00:00
**Target:** `revenue`
**Readiness:** blocked

---

## Data Profile

| Column | Dtype | Non-null % | Sample values |
|--------|-------|------------|---------------|
| order_id | int64 | 100% | 1, 2, 3 |
| customer_id | int64 | 100% | 1144, 1179, 1267 |
| order_date | object | 100% | Jan 01, 2025, Jan 01, 2025, 01/01/2025 |
| channel | object | 100% | app, store, web |
| revenue | float64 | 100% | 192.36, 165.11, 250.79 |

**Row count:** 1200  ·  **Columns:** 5

## Readiness Assessment

| Sample size adequate | ✅ ok | Total rows = 1200. |
| Missingness within acceptable bounds | 🛑 blocked | Target 'revenue' is 44% missing (>30% blocks downstream conclusions). |
| Grain is well-defined | ✅ ok | No duplicate keys on ['order_id']. |
| Time coverage sufficient | ✅ ok | No time column requested; dimension not applicable. |
| Group balance adequate | ✅ ok | No categorical target or group column; imbalance not applicable. |
| No obvious leakage columns | ✅ ok | No leakage suspects in candidate features. |
| Target / feature roles clear | ⚠️ partial | Target 'revenue' present with variation, but no candidate features supplied. |
| Measurement reliability acceptable | ✅ ok | No sentinel, saturation, or unit-mismatch flags detected. |

## Grain & Leakage

- **Recommended grain:** one row per (order_id, customer_id, order_date, channel, revenue)
- **Leaked columns flagged:** none

_No leakage columns detected._

## Baseline Evidence

| Rank | Feature | Strength | Interpretation |
|------|---------|----------|----------------|
| 1 | `order_id` | 0.500 | strong positive |
| 2 | `order_id` | 0.499 | moderate positive |
| 3 | `customer_id` | 0.056 | negligible positive |
| 4 | `customer_id` | 0.054 | negligible positive |
| 5 | `order_id` | 0.052 | weak dependence |
| 6 | `customer_id` | 0.000 | negligible dependence |

*Full correlation matrix is in `baseline_artifacts.json`.*

### Readiness Caveats

- role_clarity: Target 'revenue' present with variation, but no candidate features supplied.

## Next Steps

Baseline pipeline complete. Hand off to method-planner for full method selection, then fan-out execution, critic, and report.
