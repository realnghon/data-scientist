"""Generate an orders dataset that is NOT ready for trend analysis.

Ground truth (per evals/cases/case-08-readiness-blocked/ground_truth.json):
- `revenue` (the requested target Y) is ~45% missing  -> readiness dim 2 blocked (>30% on Y)
- `customer_id` has duplicates within the same order grain -> grain partial/blocked
- `order_date` mixes three string formats -> measurement reliability flagged
Expected behavior: readiness decision = blocked, emit a data_request, do NOT
produce trend conclusions on the full revenue series.
"""
import numpy as np
import pandas as pd

np.random.seed(31415)

n = 1200
dates = pd.date_range("2025-01-01", periods=n // 2, freq="12h")

base = 200 + 0.05 * np.arange(n) + np.random.normal(0, 30, n)
revenue = np.round(np.clip(base, 5, None), 2).astype(object)

# 45% missing on the target
missing_mask = np.random.random(n) < 0.45
revenue[missing_mask] = np.nan

# Duplicate customer ids (same customer appears in many rows; some full dup rows)
customer_id = np.random.randint(1000, 1400, n)

# Mixed date formats as strings
fmt_choice = np.random.randint(0, 3, n)
raw_dates = np.repeat(dates.values, 2)[:n]
order_date = []
for ts, f in zip(pd.to_datetime(raw_dates), fmt_choice):
    if f == 0:
        order_date.append(ts.strftime("%Y-%m-%d"))
    elif f == 1:
        order_date.append(ts.strftime("%d/%m/%Y"))
    else:
        order_date.append(ts.strftime("%b %d, %Y"))

df = pd.DataFrame(
    {
        "order_id": range(1, n + 1),
        "customer_id": customer_id,
        "order_date": order_date,
        "channel": np.random.choice(["web", "app", "store"], n),
        "revenue": revenue,
    }
)

from pathlib import Path

df.to_csv(Path(__file__).resolve().parent / "dataset.csv", index=False)
print(f"Generated {len(df)} orders")
print(f"Missing revenue: {df['revenue'].isna().mean():.1%}")
print(f"Duplicate customer_id rows: {df['customer_id'].duplicated().sum()}")
