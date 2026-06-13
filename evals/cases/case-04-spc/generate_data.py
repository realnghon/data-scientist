"""
Generate multi-line SPC dataset v2.

Scenario:
- 3 production lines (L1, L2, L3) running in parallel
- 30 days × 24 hours × 3 lines = 2160 measurements
- Spec: 9.5-10.5 mm
- Line L1: stable, Cp=1.8, Cpk=1.7 (excellent)
- Line L2: stable, Cp=1.2, Cpk=1.1 (capable but marginal)
- Line L3: out-of-control on day 15-16 (mean shift +0.8mm), Cp=1.0 (barely capable)

Expected: agent must stratify by line, run SPC per line, identify L3 as problem.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260611)

USL = 10.5
LSL = 9.5
target = 10.0

data = []
start = datetime(2026, 5, 1)

# Line L1: excellent process
for day in range(30):
    for hour in range(24):
        ts = start + timedelta(days=day, hours=hour)
        measurement = np.random.normal(target, 0.09)  # tight control
        data.append({'timestamp': ts, 'line': 'L1', 'measurement_mm': measurement})

# Line L2: capable but marginal
for day in range(30):
    for hour in range(24):
        ts = start + timedelta(days=day, hours=hour)
        measurement = np.random.normal(target, 0.14)  # wider variation
        data.append({'timestamp': ts, 'line': 'L2', 'measurement_mm': measurement})

# Line L3: out-of-control on day 15-16 (mean shift)
for day in range(30):
    for hour in range(24):
        ts = start + timedelta(days=day, hours=hour)
        if 15 <= day <= 16:
            # Mean shift +0.8mm (special cause)
            measurement = np.random.normal(target + 0.8, 0.17)
        else:
            measurement = np.random.normal(target, 0.17)
        data.append({'timestamp': ts, 'line': 'L3', 'measurement_mm': measurement})

df = pd.DataFrame(data)
df = df.sort_values('timestamp').reset_index(drop=True)
df.to_csv('dataset.csv', index=False)

print(f"Generated dataset.csv: {len(df)} rows (30 days × 24h × 3 lines)")
print(f"Spec: {LSL}-{USL} mm")
print(f"Expected findings:")
print(f"  - L1: stable, Cp~1.8, Cpk~1.7 (excellent)")
print(f"  - L2: stable, Cp~1.2, Cpk~1.1 (capable)")
print(f"  - L3: out-of-control day 15-16 (mean shift +0.8mm), Cp~1.0 (barely capable)")
print(f"  - Root cause: Line L3 特殊原因（day 15-16 失控）")
