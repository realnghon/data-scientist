"""
Generate wafer root-cause analysis dataset (long format → wide pivot required).

Scenario:
- 300 wafers across 5 stations (litho, etch, deposition, implant, final_test)
- Each station measures 3-6 parameters → long format (one row per wafer×station×param)
- Final yield (target Y) at station='final_test', param_name='yield_pct'
- Injected root cause: litho station's 'cd_nm' (critical dimension) drives yield
  - cd_nm in [85, 95] → yield ~92-98%
  - cd_nm outside [85, 95] → yield drops to 70-85%
- Noise parameters: etch_rate, dep_thickness, implant_dose (weak/no effect)
- 10% of wafers have cd_nm out-of-spec → yield drops → these are the "failure" wafers

Output: dataset.csv with columns [wafer_id, station, param_name, value, timestamp]
Ground truth: cd_nm (litho) is the dominant driver; agent must pivot then correlate.
"""
import pandas as pd
import numpy as np

np.random.seed(20260611)
n_wafers = 300

# Station definitions: {station: [param1, param2, ...]}
STATIONS = {
    'litho': ['cd_nm', 'focus_um', 'dose_mj'],
    'etch': ['etch_rate_nm_min', 'etch_time_sec', 'pressure_torr'],
    'deposition': ['thickness_nm', 'uniformity_pct', 'temp_c'],
    'implant': ['dose_e14', 'energy_kev', 'tilt_deg'],
    'final_test': ['yield_pct', 'leakage_na', 'speed_mhz'],
}

rows = []
wafer_ids = [f'W{i:03d}' for i in range(1, n_wafers + 1)]

# Generate base parameters
wafer_data = {}
for wid in wafer_ids:
    wafer_data[wid] = {}

    # Litho cd_nm: 10% out-of-spec (root cause)
    if np.random.rand() < 0.10:
        cd_nm = np.random.uniform(78, 84) if np.random.rand() < 0.5 else np.random.uniform(96, 102)
    else:
        cd_nm = np.random.uniform(85, 95)
    wafer_data[wid]['cd_nm'] = cd_nm

    # Other litho params (noise)
    wafer_data[wid]['focus_um'] = np.random.uniform(0.8, 1.2)
    wafer_data[wid]['dose_mj'] = np.random.uniform(28, 32)

    # Etch (noise)
    wafer_data[wid]['etch_rate_nm_min'] = np.random.uniform(45, 55)
    wafer_data[wid]['etch_time_sec'] = np.random.uniform(58, 62)
    wafer_data[wid]['pressure_torr'] = np.random.uniform(4.8, 5.2)

    # Deposition (noise)
    wafer_data[wid]['thickness_nm'] = np.random.uniform(98, 102)
    wafer_data[wid]['uniformity_pct'] = np.random.uniform(94, 99)
    wafer_data[wid]['temp_c'] = np.random.uniform(398, 402)

    # Implant (noise)
    wafer_data[wid]['dose_e14'] = np.random.uniform(4.8, 5.2)
    wafer_data[wid]['energy_kev'] = np.random.uniform(48, 52)
    wafer_data[wid]['tilt_deg'] = np.random.uniform(6.8, 7.2)

    # Yield: driven by cd_nm (root cause signal)
    # In-spec cd_nm (85-95) → yield ~92-98%
    # Out-of-spec → yield drops to 70-85%
    if 85 <= cd_nm <= 95:
        yield_pct = np.random.uniform(92, 98)
    else:
        deviation = max(abs(cd_nm - 85), abs(cd_nm - 95))
        yield_pct = max(70, 92 - deviation * 1.8) + np.random.uniform(-2, 2)
    wafer_data[wid]['yield_pct'] = yield_pct

    # Other final test params (noise)
    wafer_data[wid]['leakage_na'] = np.random.uniform(0.5, 1.5)
    wafer_data[wid]['speed_mhz'] = 800 + (yield_pct - 90) * 2 + np.random.uniform(-5, 5)

# Convert to long format
timestamp_base = pd.Timestamp('2026-06-01 08:00:00')
for wid in wafer_ids:
    t_offset = 0
    for station, params in STATIONS.items():
        t_offset += np.random.randint(30, 90)  # minutes between stations
        for param in params:
            rows.append({
                'wafer_id': wid,
                'station': station,
                'param_name': param,
                'value': round(wafer_data[wid][param], 4),
                'timestamp': timestamp_base + pd.Timedelta(minutes=t_offset)
            })

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle rows
df.to_csv('dataset.csv', index=False)

print(f"Generated {len(df)} rows (300 wafers × {sum(len(p) for p in STATIONS.values())} params)")
print(f"Injected root cause: cd_nm (litho) drives yield_pct")
print(f"- In-spec wafers (cd_nm 85-95): ~90% of data, yield ~92-98%")
print(f"- Out-of-spec wafers (cd_nm <85 or >95): ~10%, yield drops to 70-85%")
print(f"Dataset shape after pivot: 300 rows × ~19 param columns + wafer_id + timestamp")
