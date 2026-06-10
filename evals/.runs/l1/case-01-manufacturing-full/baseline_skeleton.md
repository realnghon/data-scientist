# Baseline Analysis: /Users/silaswu/Silas_Develop/data-scientist/examples/manufacturing_yield/dataset.csv

**Generated:** 2026-06-10T15:41:50.870417+00:00
**Target:** `yield_pct`
**Readiness:** partial

---

## Data Profile

| Column | Dtype | Non-null % | Sample values |
|--------|-------|------------|---------------|
| run_id | int64 | 100% | 1, 2, 3 |
| date | datetime64[ns] | 100% | 2025-01-01T00:00:00, 2025-01-02T00:00:00, 2025-01-03T00:00:00 |
| temperature_c | float64 | 100% | 185.9, 181.6, 187.8 |
| pressure_psi | float64 | 100% | 54.6, 59.5, 43.0 |
| humidity_pct | float64 | 100% | 56.2, 52.4, 45.5 |
| line_speed_uph | int64 | 100% | 112, 92, 88 |
| operator | object | 100% | B, C, B |
| shift | object | 100% | Afternoon, Afternoon, Night |
| equipment_age_days | int64 | 100% | 93, 303, 137 |
| yield_pct | float64 | 100% | 79.73, 89.75, 79.5 |

**Row count:** 500  ·  **Columns:** 10

## Readiness Assessment

| Sample size adequate | ✅ ok | Total rows = 500. |
| Missingness within acceptable bounds | ✅ ok | Overall 0% missing; worst column 1%. |
| Grain is well-defined | ✅ ok | No duplicate keys on ['run_id']. |
| Time coverage sufficient | ✅ ok | No time column requested; dimension not applicable. |
| Group balance adequate | ✅ ok | No categorical target or group column; imbalance not applicable. |
| No obvious leakage columns | ✅ ok | No leakage suspects in candidate features. |
| Target / feature roles clear | ⚠️ partial | Target 'yield_pct' present with variation, but no candidate features supplied. |
| Measurement reliability acceptable | ✅ ok | No sentinel, saturation, or unit-mismatch flags detected. |

## Grain & Leakage

- **Recommended grain:** one row per (run_id, date, temperature_c, pressure_psi, humidity_pct, line_speed_uph, operator, shift, equipment_age_days, yield_pct)
- **Leaked columns flagged:** none

_No leakage columns detected._

## Baseline Evidence

| Rank | Feature | Strength | Interpretation |
|------|---------|----------|----------------|
| 1 | `temperature_c` | 0.744 | very strong negative |
| 2 | `temperature_c` | 0.733 | very strong negative |
| 3 | `pressure_psi` | 0.275 | weak positive |
| 4 | `pressure_psi` | 0.251 | weak positive |
| 5 | `temperature_c` | 0.150 | moderate dependence |
| 6 | `humidity_pct` | 0.127 | weak negative |
| 7 | `equipment_age_days` | 0.103 | weak negative |
| 8 | `humidity_pct` | 0.092 | negligible negative |
| 9 | `line_speed_uph` | 0.089 | negligible negative |
| 10 | `equipment_age_days` | 0.086 | negligible negative |

*Full correlation matrix is in `baseline_artifacts.json`.*

### Readiness Caveats

- role_clarity: Target 'yield_pct' present with variation, but no candidate features supplied.

## Next Steps

Baseline pipeline complete. Hand off to method-planner for full method selection, then fan-out execution, critic, and report.
