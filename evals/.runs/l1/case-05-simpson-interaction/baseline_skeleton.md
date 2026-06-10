# Baseline Analysis: /Users/silaswu/Silas_Develop/data-scientist/evals/cases/case-05-simpson-interaction/dataset.csv

**Generated:** 2026-06-10T15:41:53.409615+00:00
**Target:** `sales_amount`
**Readiness:** partial

---

## Data Profile

| Column | Dtype | Non-null % | Sample values |
|--------|-------|------------|---------------|
| order_id | int64 | 100% | 1, 2, 3 |
| region | object | 100% | B, C, A |
| product_type | object | 100% | X, X, X |
| price | float64 | 100% | 36.06, 30.88, 37.89 |
| promotion | int64 | 100% | 0, 0, 0 |
| noise_index | float64 | 100% | 48.98, 42.05, 58.68 |
| sales_amount | float64 | 100% | 53.06, 38.5, 41.45 |

**Row count:** 3000  ·  **Columns:** 7

## Readiness Assessment

| Sample size adequate | ✅ ok | Total rows = 3000. |
| Missingness within acceptable bounds | ✅ ok | Overall 0% missing; worst column 0%. |
| Grain is well-defined | ✅ ok | No duplicate keys on ['order_id']. |
| Time coverage sufficient | ✅ ok | No time column requested; dimension not applicable. |
| Group balance adequate | ✅ ok | No categorical target or group column; imbalance not applicable. |
| No obvious leakage columns | ✅ ok | No leakage suspects in candidate features. |
| Target / feature roles clear | ⚠️ partial | Target 'sales_amount' present with variation, but no candidate features supplied. |
| Measurement reliability acceptable | ⚠️ partial | Possible saturation in columns ['promotion']; document fix. |

## Grain & Leakage

- **Recommended grain:** one row per (order_id, region, product_type, price, promotion, noise_index, sales_amount)
- **Leaked columns flagged:** none

_No leakage columns detected._

## Baseline Evidence

| Rank | Feature | Strength | Interpretation |
|------|---------|----------|----------------|
| 1 | `price` | 0.884 | very strong positive |
| 2 | `price` | 0.586 | strong positive |
| 3 | `price` | 0.250 | moderate dependence |
| 4 | `promotion` | 0.167 | weak positive |
| 5 | `promotion` | 0.151 | moderate dependence |
| 6 | `promotion` | 0.125 | weak positive |
| 7 | `order_id` | 0.014 | negligible positive |
| 8 | `noise_index` | 0.009 | negligible negative |
| 9 | `noise_index` | 0.006 | negligible negative |
| 10 | `order_id` | 0.005 | negligible positive |

*Full correlation matrix is in `baseline_artifacts.json`.*

### Readiness Caveats

- role_clarity: Target 'sales_amount' present with variation, but no candidate features supplied.
- measurement_reliability: Possible saturation in columns ['promotion']; document fix.

## Next Steps

Baseline pipeline complete. Hand off to method-planner for full method selection, then fan-out execution, critic, and report.
