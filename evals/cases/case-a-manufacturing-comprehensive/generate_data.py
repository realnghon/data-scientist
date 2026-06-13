"""
Generate Case A: 制造业质量综合分析（融合 case-01/04/09）

场景：
- 半导体 fab，3 条产线（L1/L2/L3），30 天生产
- 4 工艺站点：litho → etch → deposit → implant
- 每站记录：chamber、recipe、process_time、waiting_time
- 在线测量：每站后测关键参数（cd_nm、etch_depth、film_thickness、dose）
- 每日 SPC：每条产线抽样测最终尺寸（measurement_mm）
- 最终良率：yield_pct

数据输出（3 表）：
1. fab_log.csv — 工艺日志（300 wafer × 4 站 = 1200 行）
2. metrology.csv — 在线测量（300 wafer × 4 站 × 1 参数 = 1200 行）
3. spc_daily.csv — 每日 SPC 抽样（30 天 × 3 产线 × 24 次/天 = 2160 行）
4. final_test.csv — 最终良率（300 wafer）

注入信号（多层复合）：
A. **L3 产线 SPC 失控**（case-04 能力）
   - L3 在 day 15-16 尺寸均值偏移 +0.8mm（Western Electric Rule 2）
   - L1 稳定 Cp=1.8，L2 稳定 Cp=1.2，L3 在受控段 Cp=1.0（barely capable）

B. **Litho chamber C2 根因**（case-09 能力）
   - L3 的失控源于其 litho 使用 chamber C2 比例高（60% vs L1/L2 的 33%）
   - C2 的 cd_nm 偏低（82 vs 90，spec 85-95）→ 最终良率低（67 vs 90）

C. **温度×设备年龄交互**（case-01 能力）
   - L1/L2 正常，但它们的良率受温度×equipment_age 交互影响
   - 老设备（>8 年）在极端温度下良率敏感性放大 3 倍
   - 噪声变量（pressure、humidity、waiting_time）无效应

期望分析路径：
1. 读 3 表 → 识别需要 join（fab_log ⊲⊳ metrology ⊲⊳ final_test）
2. 分产线做 SPC → 发现 L3 day15-16 失控
3. 追溯 L3 失控原因 → litho chamber C2 比例异常
4. 机制验证 → C2 的 cd_nm 与良率相关性
5. L1/L2 的良率驱动因素 → 温度×设备年龄交互
6. 排除噪声（pressure/humidity/waiting_time）
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260613)

# Specs
USL, LSL = 10.5, 9.5
CD_SPEC = (85, 95)  # cd_nm spec range
N_WAFERS = 300
N_DAYS = 30

wafer_ids = [f'W{i:04d}' for i in range(1, N_WAFERS + 1)]
lines = ['L1', 'L2', 'L3']
steps = ['litho', 'etch', 'deposit', 'implant']
start_date = datetime(2026, 5, 1)

# ========== 1. fab_log: 工艺日志 ==========
fab_log = []
wafer_line_map = {}  # 记录每个 wafer 分配到哪条产线

for i, wid in enumerate(wafer_ids):
    day = i // 10
    # L3 分配 1/3 wafer
    line = np.random.choice(lines, p=[0.35, 0.35, 0.30])
    wafer_line_map[wid] = line

    for step in steps:
        if step == 'litho':
            # L3 使用 C2 的概率更高（60% vs 33%）
            if line == 'L3':
                chamber = np.random.choice(['C1', 'C2', 'C3'], p=[0.20, 0.60, 0.20])
            else:
                chamber = np.random.choice(['C1', 'C2', 'C3'], p=[0.33, 0.33, 0.34])
            recipe = np.random.choice(['R101', 'R102'])
        elif step == 'etch':
            chamber = np.random.choice(['E1', 'E2'])
            recipe = np.random.choice(['R201', 'R202'])
        elif step == 'deposit':
            chamber = np.random.choice(['D1', 'D2'])
            recipe = 'R301'
        else:  # implant
            chamber = np.random.choice(['I1', 'I2'])
            recipe = 'R401'

        process_time = np.random.uniform(5, 15)
        waiting_time = np.random.uniform(0.5, 3)
        temperature = np.random.uniform(160, 220)  # 用于交互效应
        pressure = np.random.uniform(2.8, 3.2)
        humidity = np.random.uniform(40, 60)
        equipment_age_years = np.random.uniform(2, 12)

        ts = start_date + timedelta(days=day, hours=np.random.uniform(0, 24))

        fab_log.append({
            'wafer_id': wid,
            'line': line,
            'step': step,
            'chamber': chamber,
            'recipe': recipe,
            'process_time_min': round(process_time, 1),
            'waiting_time_min': round(waiting_time, 1),
            'temperature_c': round(temperature, 1),
            'pressure_bar': round(pressure, 2),
            'humidity_pct': round(humidity, 1),
            'equipment_age_years': round(equipment_age_years, 1),
            'timestamp': ts,
            'day': day
        })

fab_df = pd.DataFrame(fab_log)

# ========== 2. metrology: 在线测量 ==========
metrology = []
for _, row in fab_df.iterrows():
    wid, step, chamber = row['wafer_id'], row['step'], row['chamber']

    if step == 'litho':
        # C2 的 cd_nm 偏低
        if chamber == 'C2':
            cd_nm = 82 + np.random.normal(0, 1.5)
        else:
            cd_nm = 90 + np.random.normal(0, 2)
        metrology.append({
            'wafer_id': wid, 'step': step, 'param': 'cd_nm',
            'value': round(cd_nm, 1)
        })
    elif step == 'etch':
        depth = 1.5 + np.random.normal(0, 0.1)
        metrology.append({
            'wafer_id': wid, 'step': step, 'param': 'etch_depth_um',
            'value': round(depth, 2)
        })
    elif step == 'deposit':
        thickness = 0.8 + np.random.normal(0, 0.05)
        metrology.append({
            'wafer_id': wid, 'step': step, 'param': 'film_thickness_um',
            'value': round(thickness, 3)
        })
    elif step == 'implant':
        dose = 1e15 + np.random.normal(0, 1e13)
        metrology.append({
            'wafer_id': wid, 'step': step, 'param': 'dose_cm2',
            'value': f'{dose:.2e}'
        })

met_df = pd.DataFrame(metrology)

# ========== 3. spc_daily: 每日 SPC 抽样（分产线）==========
# Re-seed after parameter changes to ensure reproducible downstream data
np.random.seed(20260614)  # Changed from 20260613 due to L3 signal enhancement
spc_daily = []
for day in range(N_DAYS):
    for line in lines:
        # L3 在 day 15-16 失控（增强信号到 1.0 mm = ~4σ）
        if line == 'L3' and 15 <= day <= 16:
            mean_shift = 1.0
        else:
            mean_shift = 0.0

        # 不同产线的基础能力
        if line == 'L1':
            sigma = 0.09
        elif line == 'L2':
            sigma = 0.14
        else:  # L3
            sigma = 0.17

        # 每天 24 次抽样
        for hour in range(24):
            measurement = 10.0 + mean_shift + np.random.normal(0, sigma)
            ts = start_date + timedelta(days=day, hours=hour)
            spc_daily.append({
                'timestamp': ts,
                'line': line,
                'measurement_mm': round(measurement, 3),
                'day': day
            })

spc_df = pd.DataFrame(spc_daily)

# ========== 4. final_test: 最终良率 ==========
final_test = []
for wid in wafer_ids:
    # 获取该 wafer 的 litho chamber 和产线
    litho_row = fab_df[(fab_df['wafer_id'] == wid) & (fab_df['step'] == 'litho')].iloc[0]
    chamber = litho_row['chamber']
    line = litho_row['line']
    temp = litho_row['temperature_c']
    age = litho_row['equipment_age_years']

    # 基础良率
    yield_base = 85

    # Signal A: chamber C2 → 低良率
    if chamber == 'C2':
        yield_base = 67 + np.random.uniform(-3, 3)
    else:
        # Signal B: 温度×设备年龄交互（仅对 L1/L2 的非 C2 wafer）
        if line in ['L1', 'L2']:
            # 温度主效应：偏离 180-200 最优区
            if 180 <= temp <= 200:
                temp_effect = 0
            else:
                deviation = min(abs(temp - 180), abs(temp - 200))
                temp_effect = -deviation * 0.25  # 恢复原值

            # 交互：老设备放大温度敏感性
            if age > 8:
                age_amplifier = 3.0 + (age - 8) * 0.6  # 恢复原值
            else:
                age_amplifier = 0.2

            yield_base = 85 + temp_effect * age_amplifier + np.random.uniform(-1, 1)  # 恢复原值
        else:
            # L3 的 C1/C3 wafer 也正常
            yield_base = 90 + np.random.uniform(-3, 3)

    final_test.append({
        'wafer_id': wid,
        'yield_pct': round(max(60, min(98, yield_base)), 1),
        'speed_mhz': round(np.random.uniform(2200, 2800), 0),
        'leakage_na': round(np.random.uniform(50, 150), 1)
    })

ft_df = pd.DataFrame(final_test)

# ========== 保存 ==========
fab_df.to_csv('fab_log.csv', index=False)
met_df.to_csv('metrology.csv', index=False)
spc_df.to_csv('spc_daily.csv', index=False)
ft_df.to_csv('final_test.csv', index=False)

print(f"Generated Case A:")
print(f"  fab_log.csv: {len(fab_df)} rows (300 wafers × 4 steps)")
print(f"  metrology.csv: {len(met_df)} measurements")
print(f"  spc_daily.csv: {len(spc_df)} samples (30 days × 3 lines × 24/day)")
print(f"  final_test.csv: {len(ft_df)} wafers")
print(f"\nInjected signals:")
print(f"  A) L3 SPC out-of-control day 15-16 (mean +0.8mm)")
print(f"  B) Litho chamber C2 → cd_nm 82 (spec 85-95) → yield 67% (vs 90%)")
print(f"  C) L1/L2: temperature × equipment_age interaction")
print(f"  D) Noise: pressure, humidity, waiting_time (no effect)")
