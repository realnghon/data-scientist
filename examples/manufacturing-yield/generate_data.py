"""Generate synthetic manufacturing yield dataset for examples."""

import numpy as np
import pandas as pd

np.random.seed(42)

# 200 production runs
n_runs = 200

# Process parameters (some are drivers, some are noise)
temperature = np.random.normal(350, 15, n_runs)  # Strong driver
pressure = np.random.normal(100, 10, n_runs)     # Moderate driver
humidity = np.random.normal(50, 5, n_runs)       # Weak driver
operator = np.random.choice(['A', 'B', 'C', 'D'], n_runs)  # Confounded
shift = np.random.choice(['Day', 'Night'], n_runs)
material_batch = np.random.choice([f'B{i:03d}' for i in range(1, 21)], n_runs)

# True yield model (hidden from analyst)
# Optimal temperature is 350, pressure 100
temp_effect = -0.3 * (temperature - 350)**2 / 100
pressure_effect = 0.2 * (pressure - 100)
humidity_effect = 0.05 * (humidity - 50)

# Operator C is better (but confounded with shift)
operator_effect = np.where(operator == 'C', 2, 0)

# Night shift slightly worse (confounded with operator)
shift_effect = np.where(shift == 'Night', -1.5, 0)

# Base yield + effects + noise
base_yield = 85
yield_pct = (
    base_yield
    + temp_effect
    + pressure_effect
    + humidity_effect
    + operator_effect
    + shift_effect
    + np.random.normal(0, 2, n_runs)
)

# Clip to realistic range
yield_pct = np.clip(yield_pct, 70, 98)

# Create DataFrame
df = pd.DataFrame({
    'run_id': [f'R{i:04d}' for i in range(1, n_runs + 1)],
    'date': pd.date_range('2024-01-01', periods=n_runs, freq='D'),
    'temperature_c': np.round(temperature, 1),
    'pressure_psi': np.round(pressure, 1),
    'humidity_pct': np.round(humidity, 1),
    'operator': operator,
    'shift': shift,
    'material_batch': material_batch,
    'yield_pct': np.round(yield_pct, 2),
    'defect_count': np.random.poisson(5, n_runs),  # Noise variable
})

# Save
df.to_csv('examples/manufacturing-yield/yield_data.csv', index=False)
print(f"Generated {len(df)} rows")
print(f"Yield range: {df['yield_pct'].min():.1f}% - {df['yield_pct'].max():.1f}%")
print(f"True drivers: temperature (quadratic), pressure (linear), humidity (weak)")
print(f"Confounded: operator C is better but works mostly night shift")
