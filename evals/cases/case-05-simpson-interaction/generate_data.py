"""Generate synthetic sales dataset with a Simpson's paradox and an interaction effect.

Ground truth (per evals/cases/case-05-simpson-interaction/ground_truth.json):
- Pooled view: region A has the highest average sales (it sells mostly premium product Y).
- Stratified by product type: region B has the highest sales *within each product type*
  (Simpson's paradox — the pooled ranking reverses once product mix is controlled).
- price x promotion interaction: price elasticity is much stronger during promotions.
- `noise_index` is a pure noise column that must NOT be ranked as a driver.
"""
import numpy as np
import pandas as pd

np.random.seed(2024)

n = 3000

regions = np.random.choice(["A", "B", "C"], n, p=[0.34, 0.33, 0.33])

# Product mix is confounded with region: A sells mostly premium Y, B/C mostly budget X
product = np.empty(n, dtype=object)
for i, r in enumerate(regions):
    if r == "A":
        product[i] = np.random.choice(["X", "Y"], p=[0.15, 0.85])
    else:
        product[i] = np.random.choice(["X", "Y"], p=[0.85, 0.15])

is_y = (product == "Y").astype(float)

# Price: product Y is premium
price = np.where(is_y == 1, np.random.normal(95, 8, n), np.random.normal(32, 5, n))
promo = np.random.binomial(1, 0.3, n)

# Region efficiency: B > C > A *within* the same product (Simpson reversal vs pooled)
region_effect = np.select(
    [regions == "A", regions == "B", regions == "C"], [0.0, 14.0, 6.0]
)

# Product baseline dominates the pooled comparison (Y >> X)
product_effect = 70.0 * is_y

# Interaction: discounting below list price lifts sales far more during promotions
price_centered = price - np.where(is_y == 1, 95, 32)
price_effect = -0.4 * price_centered          # mild base elasticity
interaction_effect = -1.6 * price_centered * promo  # promo amplifies elasticity

noise_index = np.random.normal(50, 10, n)      # pure noise driver candidate

sales = (
    40.0
    + product_effect
    + region_effect
    + price_effect
    + 8.0 * promo
    + interaction_effect
    + np.random.normal(0, 6, n)
)

df = pd.DataFrame(
    {
        "order_id": range(1, n + 1),
        "region": regions,
        "product_type": product,
        "price": np.round(price, 2),
        "promotion": promo,
        "noise_index": np.round(noise_index, 2),
        "sales_amount": np.round(sales, 2),
    }
)

from pathlib import Path

df.to_csv(Path(__file__).resolve().parent / "dataset.csv", index=False)

pooled = df.groupby("region")["sales_amount"].mean().sort_values(ascending=False)
print(f"Generated {len(df)} orders")
print("Pooled mean sales by region (A should lead):")
print(pooled.round(2).to_string())
print("\nWithin-product mean sales (B should lead in both X and Y):")
print(df.groupby(["product_type", "region"])["sales_amount"].mean().round(2).to_string())
