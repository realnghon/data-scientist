# Baseline Analysis: /Users/silaswu/Silas_Develop/data-scientist/examples/ab_test/dataset.csv

**Generated:** 2026-06-10T15:41:51.629662+00:00
**Target:** `converted`
**Readiness:** partial

---

## Data Profile

| Column | Dtype | Non-null % | Sample values |
|--------|-------|------------|---------------|
| user_id | int64 | 100% | 6253, 4685, 1732 |
| variant | object | 100% | treatment, control, control |
| converted | int64 | 100% | 0, 0, 0 |
| revenue | float64 | 100% | 0.0, 0.0, 0.0 |
| signup_date | datetime64[ns] | 100% | 2025-03-05T08:20:00, 2025-03-17T06:20:00, 2025-03-07T00:15:00 |
| device | object | 100% | mobile, mobile, mobile |
| country | object | 100% | CA, US, AU |

**Row count:** 10000  ·  **Columns:** 7

## Readiness Assessment

| Sample size adequate | ✅ ok | Total rows = 10000. |
| Missingness within acceptable bounds | ✅ ok | Overall 0% missing; worst column 0%. |
| Grain is well-defined | ✅ ok | No duplicate keys on ['user_id']. |
| Time coverage sufficient | ✅ ok | No time column requested; dimension not applicable. |
| Group balance adequate | ⚠️ partial | 'converted' majority:minority = 6.62:1; balanced metric (PR-AUC, F1). |
| No obvious leakage columns | ✅ ok | No leakage suspects in candidate features. |
| Target / feature roles clear | ⚠️ partial | Target 'converted' present with variation, but no candidate features supplied. |
| Measurement reliability acceptable | ⚠️ partial | Possible saturation in columns ['converted']; document fix. |

## Grain & Leakage

- **Recommended grain:** one row per (user_id, variant, converted, revenue, signup_date, device, country)
- **Leaked columns flagged:** none

_No leakage columns detected._

## Baseline Evidence

| Rank | Feature | Strength | Interpretation |
|------|---------|----------|----------------|
| 1 | `revenue` | 0.997 | very strong positive |
| 2 | `revenue` | 0.990 | very strong dependence |
| 3 | `revenue` | 0.731 | very strong positive |
| 4 | `user_id` | 0.038 | negligible positive |
| 5 | `user_id` | 0.038 | negligible positive |
| 6 | `user_id` | 0.000 | negligible dependence |

*Full correlation matrix is in `baseline_artifacts.json`.*

### Readiness Caveats

- balance: 'converted' majority:minority = 6.62:1; balanced metric (PR-AUC, F1).
- role_clarity: Target 'converted' present with variation, but no candidate features supplied.
- measurement_reliability: Possible saturation in columns ['converted']; document fix.

## Next Steps

Baseline pipeline complete. Hand off to method-planner for full method selection, then fan-out execution, critic, and report.
