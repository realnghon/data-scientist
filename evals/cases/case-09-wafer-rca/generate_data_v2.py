"""
Generate wafer root-cause analysis dataset v2 — realistic multi-source complexity.

Scenario:
- 2 data sources (process tracking + parametric test), joined by wafer_id
- Process tracking (fab_log.csv): chamber, recipe, process_time, waiting_time per station
- Parametric test (metrology.csv): long format station×param×value (original case-09 data)
- Injected root cause: chamber='C2' at litho station → cd_nm drifts out-of-spec → yield drops
- Noise: recipe variation, waiting time, other chambers (no effect on yield)
- Challenge: agent must join 2 tables, pivot metrology, then isolate chamber effect

Output:
- fab_log.csv: 1500 rows (300 wafers × 5 stations)
- metrology.csv: 4500 rows (300 wafers × 5 stations × 3 avg params per station)
- Final join+pivot: 300 rows × ~25 columns (chamber/recipe/time + pivoted params)
"""
import pandas as pd
import numpy as np

np.random.seed(20260611)
n_wafers = 300
wafer_ids = [f'W{i:03d}' for i in range(1, n_wafers + 1)]

STATIONS = ['litho', 'etch', 'deposition', 'implant', 'final_test']
CHAMBERS = {'litho': ['C1', 'C2', 'C3'], 'etch': ['E1', 'E2'],
            'deposition': ['D1', 'D2'], 'implant': ['I1', 'I2'],
            'final_test': ['T1']}
RECIPES = {'litho': ['R101', 'R102'], 'etch': ['R201'],
           'deposition': ['R301', 'R302'], 'implant': ['R401'],
           'final_test': ['R501']}

# === fab_log.csv ===
fab_rows = []
timestamp_base = pd.Timestamp('2026-06-01 08:00:00')
wafer_chamber_map = {}  # track which chamber each wafer used at litho

for wid in wafer_ids:
    t = timestamp_base
    for station in STATIONS:
        chamber = np.random.choice(CHAMBERS[station])
        recipe = np.random.choice(RECIPES[station])
        process_time_min = np.random.uniform(5, 15)
        waiting_time_min = np.random.uniform(10, 60) if station != 'litho' else 0

        if station == 'litho':
            wafer_chamber_map[wid] = chamber

        fab_rows.append({
            'wafer_id': wid,
            'station': station,
            'chamber': chamber,
            'recipe': recipe,
            'process_time_min': round(process_time_min, 2),
            'waiting_time_min': round(waiting_time_min, 2),
            'start_timestamp': t
        })
        t += pd.Timedelta(minutes=process_time_min + waiting_time_min)

fab_df = pd.DataFrame(fab_rows)
fab_df.to_csv('fab_log.csv', index=False)

# === metrology.csv (pivoted params) ===
metro_rows = []
wafer_params = {}

for wid in wafer_ids:
    wafer_params[wid] = {}
    litho_chamber = wafer_chamber_map[wid]

    # Root cause: chamber C2 → cd_nm systematically drifts LOW (stronger signal)
    if litho_chamber == 'C2':
        cd_nm = np.random.uniform(76, 82)  # Consistently below spec 85-95
    else:
        cd_nm = np.random.uniform(87, 93)  # Normal, centered on spec

    wafer_params[wid]['litho_cd_nm'] = cd_nm
    wafer_params[wid]['litho_focus_um'] = np.random.uniform(-0.15, 0.15)  # within spec -0.2 to +0.2
    wafer_params[wid]['litho_dose_mj'] = np.random.uniform(28, 32)

    wafer_params[wid]['etch_rate_nm_min'] = np.random.uniform(45, 55)
    wafer_params[wid]['etch_time_sec'] = np.random.uniform(58, 62)
    wafer_params[wid]['etch_pressure_torr'] = np.random.uniform(4.8, 5.2)

    wafer_params[wid]['dep_thickness_nm'] = np.random.uniform(98, 102)
    wafer_params[wid]['dep_uniformity_pct'] = np.random.uniform(94, 99)
    wafer_params[wid]['dep_temp_c'] = np.random.uniform(398, 402)

    wafer_params[wid]['implant_dose_e14'] = np.random.uniform(4.8, 5.2)
    wafer_params[wid]['implant_energy_kev'] = np.random.uniform(48, 52)
    wafer_params[wid]['implant_tilt_deg'] = np.random.uniform(6.8, 7.2)

    # Yield driven by cd_nm (root cause)
    if 85 <= cd_nm <= 95:
        yield_pct = np.random.uniform(92, 98)
    else:
        deviation = max(abs(cd_nm - 85), abs(cd_nm - 95))
        yield_pct = max(70, 92 - deviation * 1.8) + np.random.uniform(-2, 2)

    wafer_params[wid]['yield_pct'] = yield_pct
    wafer_params[wid]['final_leakage_na'] = np.random.uniform(0.5, 1.5)
    wafer_params[wid]['final_speed_mhz'] = 800 + (yield_pct - 90) * 2 + np.random.uniform(-5, 5)

# Convert to long format for metrology.csv
PARAM_STATION_MAP = {
    'cd_nm': 'litho', 'focus_um': 'litho', 'dose_mj': 'litho',
    'rate_nm_min': 'etch', 'time_sec': 'etch', 'pressure_torr': 'etch',
    'thickness_nm': 'deposition', 'uniformity_pct': 'deposition', 'temp_c': 'deposition',
    'dose_e14': 'implant', 'energy_kev': 'implant', 'tilt_deg': 'implant',
    'yield_pct': 'final_test', 'leakage_na': 'final_test', 'speed_mhz': 'final_test'
}

for wid in wafer_ids:
    for full_param, value in wafer_params[wid].items():
        parts = full_param.split('_', 1)
        station_prefix = parts[0]
        param_name = parts[1] if len(parts) > 1 else full_param

        # Map back to station
        station = None
        for key, st in PARAM_STATION_MAP.items():
            if key in param_name:
                station = st
                break
        if not station:
            if 'litho' in full_param:
                station = 'litho'
            elif 'etch' in full_param:
                station = 'etch'
            elif 'dep' in full_param:
                station = 'deposition'
            elif 'implant' in full_param:
                station = 'implant'
            else:
                station = 'final_test'

        metro_rows.append({
            'wafer_id': wid,
            'station': station,
            'param_name': param_name,
            'value': round(value, 4),
            'timestamp': fab_df[(fab_df['wafer_id']==wid) & (fab_df['station']==station)]['start_timestamp'].iloc[0]
        })

metro_df = pd.DataFrame(metro_rows)
metro_df = metro_df.sample(frac=1, random_state=42).reset_index(drop=True)
metro_df.to_csv('metrology.csv', index=False)

print(f"Generated fab_log.csv: {len(fab_df)} rows (300 wafers × 5 stations)")
print(f"Generated metrology.csv: {len(metro_df)} rows (long format)")
print(f"Root cause: chamber='C2' at litho → cd_nm out-of-spec → yield drops")
print(f"Challenge: join fab_log + metrology on wafer_id, pivot metrology, isolate chamber effect")
print(f"Expected: litho_chamber='C2' identified as root cause driver")
