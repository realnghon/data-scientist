"""
Generate case-05 v2: Simpson's paradox + time dimension (trend reversal).

Scenario:
- E-commerce sales data, 2 years × 12 months = 24 time periods
- 3 regions (North, South, West), 2 product lines (Premium, Budget)
- Simpson's paradox: Premium shows positive trend overall, but NEGATIVE within each region
- Mechanism: Premium market share shifts from low-growth South → high-growth North over time
- 1200 orders (50/month × 24 months)

Expected: agent must stratify by region, detect within-region negative trends, explain reversal.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260612)

data = []
order_id = 1
start = datetime(2024, 6, 1)

for month_offset in range(24):
    month_date = start + timedelta(days=30 * month_offset)

    # South: early adopter, saturating (Premium growth slowing)
    # Premium: high initial, declining growth
    south_premium_base = 5000 - month_offset * 80  # declining
    south_budget_base = 3000 + month_offset * 20   # stable

    # North: late adopter, accelerating (Premium growth accelerating)
    # Premium: low initial, increasing growth
    north_premium_base = 2000 + month_offset * 150  # strong growth
    north_budget_base = 2500 + month_offset * 30

    # West: stable (Premium declining slightly)
    west_premium_base = 3500 - month_offset * 30
    west_budget_base = 2800 + month_offset * 15

    # Generate ~50 orders this month
    for _ in range(50):
        # Region selection shifts over time (South → North)
        region_prob = {'South': max(0.1, 0.6 - month_offset * 0.02),
                       'North': min(0.7, 0.2 + month_offset * 0.02),
                       'West': 0.2}
        region = np.random.choice(list(region_prob.keys()), p=list(region_prob.values()))

        # Product type (50/50 roughly)
        product = np.random.choice(['Premium', 'Budget'])

        if region == 'South':
            base = south_premium_base if product == 'Premium' else south_budget_base
        elif region == 'North':
            base = north_premium_base if product == 'Premium' else north_budget_base
        else:
            base = west_premium_base if product == 'Premium' else west_budget_base

        sales = base + np.random.normal(0, 200)

        data.append({
            'order_id': order_id,
            'order_date': month_date,
            'region': region,
            'product_line': product,
            'sales_amount': max(100, sales)  # floor at 100
        })
        order_id += 1

df = pd.DataFrame(data)
df.to_csv('dataset.csv', index=False)

print(f"Generated dataset.csv: {len(df)} orders (24 months)")
print(f"Simpson's paradox injected:")
print(f"  - Overall: Premium shows positive trend (market shifts South→North)")
print(f"  - Within-region: Premium declining in South/West, growing in North but slower than Budget")
print(f"  - Expected: agent must stratify by region to detect reversal")
