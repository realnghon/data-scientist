"""
Generate manufacturing yield dataset v2 with interaction effects.

Scenario:
- 500 production batches across 3 lines, 2 shifts, 5 operators
- True drivers: temperature (optimal 180-200°C), equipment_age × temperature interaction
- Interaction mechanism: old equipment (>8 years) amplifies temperature sensitivity
  → young equipment: yield insensitive to temp; old equipment: yield drops sharply at extremes
- Noise: pressure, humidity, line_speed, operator, shift (no effect)

Output: dataset.csv (500 rows × 9 columns)
"""
import pandas as pd
import numpy as np

np.random.seed(20260611)
n = 500

data = {
    'batch_id': [f'B{i:04d}' for i in range(1, n+1)],
    'line': np.random.choice(['L1', 'L2', 'L3'], n),
    'shift': np.random.choice(['day', 'night'], n),
    'operator': np.random.choice(['Alice', 'Bob', 'Carol', 'Dave', 'Eve'], n),
    'temperature_c': np.random.uniform(160, 220, n),
    'pressure_bar': np.random.uniform(2.8, 3.2, n),
    'humidity_pct': np.random.uniform(40, 60, n),
    'line_speed_mpm': np.random.uniform(8, 12, n),
    'equipment_age_years': np.random.uniform(2, 12, n),
}

df = pd.DataFrame(data)

# Yield model: temperature effect amplified by equipment age
def compute_yield(row):
    temp = row['temperature_c']
    age = row['equipment_age_years']

    # Base yield from temperature (optimal 180-200)
    temp_effect = 0
    if 180 <= temp <= 200:
        temp_effect = 0  # optimal zone
    else:
        deviation = min(abs(temp - 180), abs(temp - 200))
        temp_effect = -deviation * 0.15  # -15% per 10°C deviation

    # Interaction: old equipment amplifies temperature sensitivity
    if age > 8:
        age_amplifier = 1.0 + (age - 8) * 0.3  # 30% more sensitive per year beyond 8
    else:
        age_amplifier = 0.5  # young equipment less sensitive

    yield_base = 85
    yield_pct = yield_base + temp_effect * age_amplifier + np.random.uniform(-2, 2)
    return max(60, min(98, yield_pct))

df['yield_pct'] = df.apply(compute_yield, axis=1)

df.to_csv('dataset.csv', index=False)
print(f"Generated dataset.csv: {len(df)} rows")
print(f"Interaction injected: old equipment (>8y) × extreme temp → yield drop")
print(f"Expected findings:")
print(f"  - temperature main effect: yield drops outside 180-200°C")
print(f"  - equipment_age × temperature interaction: p < 0.01")
print(f"  - noise rejected: pressure, humidity, line_speed, operator, shift")
