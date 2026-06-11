"""
Generate case-03 v2: time series with seasonality + multiple anomaly types.

Scenario:
- IoT sensor data, 180 days (6 months), hourly readings = 4320 points
- Baseline: daily seasonality (peak at noon, low at night)
- Weekly seasonality (weekday vs weekend pattern)
- Injected anomalies:
  - Point outliers: 10 random spikes (sensor glitch)
  - Level shift: day 90-95 (mean +20, system recalibration)
  - Trend change: after day 120 (slow drift +0.1/day, sensor aging)

Expected: agent must decompose seasonality (STL/seasonal_decompose), detect
all 3 anomaly types, distinguish systematic vs sporadic.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260612)

start = datetime(2025, 12, 1)
hours = 180 * 24  # 4320 hours

timestamps = [start + timedelta(hours=h) for h in range(hours)]
baseline = 50

data = []
for i, ts in enumerate(timestamps):
    hour_of_day = ts.hour
    day_of_week = ts.weekday()
    day = i // 24

    # Daily seasonality (sinusoidal, peak at noon)
    daily = 10 * np.sin((hour_of_day - 6) * np.pi / 12)

    # Weekly seasonality (weekend lower by 5)
    weekly = -5 if day_of_week >= 5 else 0

    # Baseline + seasonality + noise
    value = baseline + daily + weekly + np.random.normal(0, 2)

    # Point outliers (10 random spikes)
    if i in np.random.choice(hours, 10, replace=False):
        value += np.random.choice([25, -20])

    # Level shift on day 90-95 (recalibration)
    if 90 * 24 <= i < 96 * 24:
        value += 20

    # Trend change after day 120 (sensor aging)
    if i >= 120 * 24:
        value += 0.1 * (day - 120)

    data.append({'timestamp': ts, 'sensor_value': round(value, 2)})

df = pd.DataFrame(data)
df.to_csv('dataset_v2.csv', index=False)

print(f"Generated dataset_v2.csv: {len(df)} hourly readings (180 days)")
print(f"Injected patterns:")
print(f"  - Daily seasonality (peak at noon, ±10 range)")
print(f"  - Weekly seasonality (weekend -5)")
print(f"  - 10 point outliers (±20~25 spikes)")
print(f"  - Level shift day 90-95 (+20, recalibration)")
print(f"  - Trend drift after day 120 (+0.1/day, aging)")
print(f"Expected: agent decomposes seasonality, detects all 3 anomaly types")
