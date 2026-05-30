"""Generate synthetic A/B test dataset."""
import pandas as pd
import numpy as np

np.random.seed(123)

# Simulate A/B test with 10,000 users
n_control = 5000
n_treatment = 5000

# Control group (baseline conversion rate: 12%)
control_converted = np.random.binomial(1, 0.12, n_control)
control_revenue = np.where(
    control_converted == 1,
    np.random.lognormal(3.5, 0.8, n_control),  # Average ~$40
    0
)

# Treatment group (improved conversion rate: 14%, higher AOV)
treatment_converted = np.random.binomial(1, 0.14, n_treatment)
treatment_revenue = np.where(
    treatment_converted == 1,
    np.random.lognormal(3.7, 0.8, n_treatment),  # Average ~$50
    0
)

# Create DataFrames
df_control = pd.DataFrame({
    'user_id': range(1, n_control + 1),
    'variant': 'control',
    'converted': control_converted,
    'revenue': np.round(control_revenue, 2),
    'signup_date': pd.date_range('2025-03-01', periods=n_control, freq='5min')
})

df_treatment = pd.DataFrame({
    'user_id': range(n_control + 1, n_control + n_treatment + 1),
    'variant': 'treatment',
    'converted': treatment_converted,
    'revenue': np.round(treatment_revenue, 2),
    'signup_date': pd.date_range('2025-03-01', periods=n_treatment, freq='5min')
})

# Combine
df = pd.concat([df_control, df_treatment], ignore_index=True)

# Add some user attributes
df['device'] = np.random.choice(['mobile', 'desktop', 'tablet'], len(df), p=[0.6, 0.35, 0.05])
df['country'] = np.random.choice(['US', 'UK', 'CA', 'AU'], len(df), p=[0.5, 0.25, 0.15, 0.1])

# Shuffle
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
from pathlib import Path
df.to_csv(Path(__file__).resolve().parent / 'dataset.csv', index=False)
print(f"Generated {len(df)} users")
print(f"Control conversion: {df[df['variant']=='control']['converted'].mean():.2%}")
print(f"Treatment conversion: {df[df['variant']=='treatment']['converted'].mean():.2%}")
print(f"Control avg revenue: ${df[df['variant']=='control']['revenue'].mean():.2f}")
print(f"Treatment avg revenue: ${df[df['variant']=='treatment']['revenue'].mean():.2f}")
