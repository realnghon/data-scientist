"""
Generate case-02 v2: A/B test with multi-metric tradeoff.

Scenario:
- New checkout flow A/B test
- Treatment: increases conversion_rate (+2.5pp), but decreases engagement (-15%)
- Tradeoff decision: is the conversion gain worth the engagement loss?
- Sample: 20,000 users (10k control, 10k treatment)
- Metrics: conversion_rate, revenue_per_user, avg_session_duration, bounce_rate

Expected: agent must report BOTH positive (conversion) and negative (engagement) effects,
calculate tradeoff (e.g., LTV impact), and make conditional recommendation.
"""
import pandas as pd
import numpy as np

np.random.seed(20260612)

data = []

# Control: baseline conversion 8%, session 5 min, bounce 45%
for i in range(10000):
    converted = np.random.rand() < 0.08
    revenue = np.random.gamma(2, 15) if converted else 0
    session_duration = np.random.gamma(5, 60)  # ~5 min avg
    bounce = np.random.rand() < 0.45

    data.append({
        'user_id': f'C{i:05d}',
        'variant': 'control',
        'converted': int(converted),
        'revenue': round(revenue, 2),
        'session_duration_sec': int(session_duration),
        'bounced': int(bounce)
    })

# Treatment: conversion 10.5% (+2.5pp), but session 4.25 min (-15%), bounce 52% (+7pp)
for i in range(10000):
    converted = np.random.rand() < 0.105  # +2.5pp
    revenue = np.random.gamma(2, 15) if converted else 0
    session_duration = np.random.gamma(5, 51)  # -15% (~4.25 min)
    bounce = np.random.rand() < 0.52  # +7pp

    data.append({
        'user_id': f'T{i:05d}',
        'variant': 'treatment',
        'converted': int(converted),
        'revenue': round(revenue, 2),
        'session_duration_sec': int(session_duration),
        'bounced': int(bounce)
    })

df = pd.DataFrame(data)
df.to_csv('dataset.csv', index=False)

print(f"Generated dataset.csv: {len(df)} users (10k control, 10k treatment)")
print(f"Injected tradeoff:")
print(f"  - Treatment conversion: 10.5% vs 8.0% control (+2.5pp, +31% relative)")
print(f"  - Treatment session_duration: ~255s vs ~300s control (-15%)")
print(f"  - Treatment bounce: 52% vs 45% control (+7pp)")
print(f"Expected: agent must report BOTH wins and losses, recommend conditionally")
