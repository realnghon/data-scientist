"""Generate synthetic SPC dataset with known special causes and capability.

Ground truth (per evals/cases/case-04-spc/ground_truth.json):
- Points 1-500: stable, mean=10.0, sigma=0.2  -> in-control baseline
- Points 501-520: 20 consecutive points shifted +0.3 above center (Rule 2 / shift)
- Points 601-650: upward trend, +0.012/step (Rule 6 / trend)
- Spec limits: LSL=9.5, USL=10.5 -> true Cp = (10.5-9.5)/(6*0.2) = 0.83 (inadequate, <1.33)
"""
import numpy as np
import pandas as pd

np.random.seed(789)

n = 720  # 30 days x 24 hourly measurements
sigma = 0.2
center = 10.0

values = np.random.normal(center, sigma, n)

# Rule 2: sustained shift — 20 consecutive points above the center line
values[500:520] += 0.3

# Rule 6: trend — steadily increasing run
values[600:650] += np.linspace(0.05, 0.65, 50)

timestamps = pd.date_range("2025-04-01", periods=n, freq="h")

df = pd.DataFrame(
    {
        "timestamp": timestamps,
        "measurement_mm": np.round(values, 4),
        "line": "LINE_07",
        "product": "PN-4411",
    }
)

from pathlib import Path

df.to_csv(Path(__file__).resolve().parent / "dataset.csv", index=False)

baseline = values[:500]
cp = (10.5 - 9.5) / (6 * baseline.std(ddof=1))
print(f"Generated {len(df)} measurements")
print(f"Baseline mean={baseline.mean():.4f}, sigma={baseline.std(ddof=1):.4f}")
print(f"True Cp (baseline) = {cp:.3f} (target ground truth ~0.83)")
print("Injected: shift @501-520 (Rule 2), trend @601-650 (Rule 6)")
