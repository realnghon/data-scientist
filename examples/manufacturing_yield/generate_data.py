"""Generate synthetic manufacturing yield dataset with confounded variables."""
import pandas as pd
import numpy as np

np.random.seed(42)

# Generate 500 production runs
n = 500

# Process parameters
temperature = np.random.normal(180, 10, n)  # Celsius
pressure = np.random.normal(50, 5, n)  # PSI
humidity = np.random.normal(45, 8, n)  # %
line_speed = np.random.normal(100, 15, n)  # units/hour

# Operator and shift (categorical)
operators = np.random.choice(['A', 'B', 'C', 'D'], n)
shifts = np.random.choice(['Morning', 'Afternoon', 'Night'], n)

# Equipment age (confounded with temperature drift)
equipment_age_days = np.random.randint(0, 365, n)
temperature += equipment_age_days * 0.01  # Older equipment runs hotter

# True causal relationships:
# - Temperature: strong negative effect on yield
# - Pressure: moderate positive effect
# - Humidity: weak negative effect
# - Line speed: no effect (noise)
# - Operator C is better trained
# - Night shift has lower yield (fatigue)

yield_base = 85  # Base yield %

yield_pct = (
    yield_base
    - 0.3 * (temperature - 180)  # Temperature effect
    + 0.2 * (pressure - 50)  # Pressure effect
    - 0.1 * (humidity - 45)  # Humidity effect
    + 0.0 * (line_speed - 100)  # No effect (noise variable)
    + 3 * (operators == 'C')  # Operator C is better
    - 2 * (shifts == 'Night')  # Night shift penalty
    + np.random.normal(0, 2, n)  # Random noise
)

# Clip to realistic range
yield_pct = np.clip(yield_pct, 70, 98)

# Add some missing values (realistic)
missing_mask = np.random.random(n) < 0.02
humidity[missing_mask] = np.nan

# Create DataFrame
df = pd.DataFrame({
    'run_id': range(1, n + 1),
    'date': pd.date_range('2025-01-01', periods=n, freq='D'),
    'temperature_c': np.round(temperature, 1),
    'pressure_psi': np.round(pressure, 1),
    'humidity_pct': np.round(humidity, 1),
    'line_speed_uph': np.round(line_speed, 0).astype(int),
    'operator': operators,
    'shift': shifts,
    'equipment_age_days': equipment_age_days,
    'yield_pct': np.round(yield_pct, 2)
})

# Save next to this script, regardless of the current working directory
from pathlib import Path
df.to_csv(Path(__file__).resolve().parent / 'dataset.csv', index=False)
print(f"Generated {len(df)} rows")
print(f"Yield range: {df['yield_pct'].min():.1f}% - {df['yield_pct'].max():.1f}%")
print(f"Missing values: {df['humidity_pct'].isna().sum()}")
