"""Generate synthetic time series sensor data with anomalies."""
import pandas as pd
import numpy as np

np.random.seed(456)

# Generate 90 days of hourly sensor readings
hours = 90 * 24
timestamps = pd.date_range('2025-01-01', periods=hours, freq='h')

# Base signal: daily seasonality + weekly pattern + trend
hour_of_day = np.array([t.hour for t in timestamps])
day_of_week = np.array([t.dayofweek for t in timestamps])

base_signal = (
    100  # Baseline
    + 10 * np.sin(2 * np.pi * hour_of_day / 24)  # Daily cycle
    + 5 * np.sin(2 * np.pi * day_of_week / 7)  # Weekly cycle
    + 0.02 * np.arange(hours)  # Slow upward trend
)

# Add noise
noise = np.random.normal(0, 2, hours)
sensor_value = base_signal + noise
sensor_value = sensor_value.copy()  # Make it mutable

# Inject anomalies
anomaly_indices = []

# Type 1: Sudden spikes (equipment malfunction)
spike_times = np.random.choice(hours, 5, replace=False)
for idx in spike_times:
    sensor_value[idx] += np.random.uniform(30, 50)
    anomaly_indices.append(int(idx))

# Type 2: Gradual drift (sensor degradation)
drift_start = hours // 3
drift_end = drift_start + 200
sensor_value[drift_start:drift_end] += np.linspace(0, 15, drift_end - drift_start)
anomaly_indices.extend(range(drift_start, drift_end))

# Type 3: Sudden drop (power outage)
outage_start = 2 * hours // 3
outage_duration = 12
sensor_value[outage_start:outage_start + outage_duration] = 0
anomaly_indices.extend(range(outage_start, outage_start + outage_duration))

# Create DataFrame
df = pd.DataFrame({
    'timestamp': timestamps,
    'sensor_value': np.round(sensor_value, 2),
    'equipment_id': 'SENSOR_001',
    'location': 'Production Line A'
})

# Add a few missing values
missing_mask = np.random.random(hours) < 0.01
df.loc[missing_mask, 'sensor_value'] = np.nan

# Save
df.to_csv('dataset.csv', index=False)
print(f"Generated {len(df)} hourly readings")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Value range: {df['sensor_value'].min():.1f} - {df['sensor_value'].max():.1f}")
print(f"Anomalies injected: {len(set(anomaly_indices))} time points")
print(f"Missing values: {df['sensor_value'].isna().sum()}")
