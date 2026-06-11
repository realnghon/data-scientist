"""
Generate case-09 v3: multi-step semiconductor fab data (真实生产场景).

User feedback: "制程分为多个 step，每个 step 有 chamber/recipe/process_time/waiting_time"

Scenario:
- 4 fab steps: litho → etch → deposit → implant
- Each step: chamber_id, recipe, process_time, waiting_time
- Metrology after each step (in-line) + final_test (end-of-line)
- 300 wafers, 30 days
- Root cause: litho chamber C2 cd_nm out-of-spec → yield drop

Complexity vs v2:
- v2: 1 station (litho only) + 1 metrology merge
- v3: 4 stations + 4 in-line metrology + 1 final_test = 6-way data integration
- Requires: join on wafer_id + step, pivot multi-step params, trace multi-stage propagation
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260611)

# 300 wafers, 30 days
wafer_ids = [f'W{i:04d}' for i in range(1, 301)]
start = datetime(2026, 5, 1)

# 4 fab steps
steps = ['litho', 'etch', 'deposit', 'implant']
chambers = {
    'litho': ['C1', 'C2', 'C3'],
    'etch': ['E1', 'E2'],
    'deposit': ['D1', 'D2'],
    'implant': ['I1', 'I2']
}
recipes = {
    'litho': ['R101', 'R102'],
    'etch': ['R201', 'R202'],
    'deposit': ['R301'],
    'implant': ['R401']
}

# Fab log (4 rows per wafer, 1200 total)
fab_log = []
for i, wid in enumerate(wafer_ids):
    day = i // 10
    for step in steps:
        chamber = np.random.choice(chambers[step])
        recipe = np.random.choice(recipes[step])
        process_time = np.random.uniform(5, 15)
        waiting_time = np.random.uniform(0.5, 3)
        ts = start + timedelta(days=day, hours=np.random.uniform(0, 24))
        fab_log.append({
            'wafer_id': wid, 'step': step, 'chamber': chamber, 'recipe': recipe,
            'process_time_min': round(process_time, 1),
            'waiting_time_min': round(waiting_time, 1),
            'timestamp': ts
        })

fab_df = pd.DataFrame(fab_log)

# In-line metrology (after each step, long format)
metrology_inline = []
for _, row in fab_df.iterrows():
    wid, step, chamber = row['wafer_id'], row['step'], row['chamber']

    if step == 'litho':
        cd_nm = 90 + np.random.normal(0, 2)
        if chamber == 'C2':
            cd_nm = 82 + np.random.normal(0, 2)  # Out-of-spec (85-95)
        metrology_inline.append({'wafer_id': wid, 'step': step, 'param': 'cd_nm', 'value': round(cd_nm, 1)})

    elif step == 'etch':
        depth = 1.5 + np.random.normal(0, 0.1)
        metrology_inline.append({'wafer_id': wid, 'step': step, 'param': 'etch_depth_um', 'value': round(depth, 2)})

    elif step == 'deposit':
        thickness = 0.8 + np.random.normal(0, 0.05)
        metrology_inline.append({'wafer_id': wid, 'step': step, 'param': 'film_thickness_um', 'value': round(thickness, 3)})

    elif step == 'implant':
        dose = 1e15 + np.random.normal(0, 1e13)
        metrology_inline.append({'wafer_id': wid, 'step': step, 'param': 'dose_cm2', 'value': f'{dose:.2e}'})

metrology_df = pd.DataFrame(metrology_inline)

# Final test (end-of-line, 1 row per wafer)
final_test = []
for wid in wafer_ids:
    litho_chamber = fab_df[(fab_df['wafer_id'] == wid) & (fab_df['step'] == 'litho')]['chamber'].values[0]

    if litho_chamber == 'C2':
        yield_pct = np.random.uniform(60, 75)  # Low yield due to cd_nm
        speed_mhz = np.random.uniform(1800, 2200)
        leakage_na = np.random.uniform(150, 250)
    else:
        yield_pct = np.random.uniform(85, 95)  # Normal
        speed_mhz = np.random.uniform(2400, 2800)
        leakage_na = np.random.uniform(50, 100)

    final_test.append({
        'wafer_id': wid,
        'yield_pct': round(yield_pct, 1),
        'speed_mhz': round(speed_mhz, 0),
        'leakage_na': round(leakage_na, 1)
    })

final_df = pd.DataFrame(final_test)

# Save
fab_df.to_csv('fab_log_v3.csv', index=False)
metrology_df.to_csv('metrology_inline_v3.csv', index=False)
final_df.to_csv('final_test_v3.csv', index=False)

print(f"Generated fab_log_v3.csv: {len(fab_df)} rows (300 wafers × 4 steps)")
print(f"Generated metrology_inline_v3.csv: {len(metrology_df)} measurements")
print(f"Generated final_test_v3.csv: {len(final_df)} wafers")
print(f"\nComplexity: 3 tables, 6-way integration required")
print(f"Root cause: litho chamber C2 → cd_nm out-of-spec (82±2, spec 85-95) → yield 60-75%")
print(f"Expected: agent must join fab_log + metrology_inline + final_test, trace multi-step")
