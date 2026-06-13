"""
Generate Case C: 时序监控与路由（融合 case-03 + case-06/07/08）

场景：
- IoT 传感器监控，180 天小时读数（4320 时点）
- 带数据质量问题：前 90 天缺失率 5%（ok），后 90 天缺失率 45%（blocked）
- 3 类异常：10 个尖峰 + day 90-95 水平偏移 + day 120 后漂移
- 用户请求模式可变（通过 prompt 控制）：
   - Mode A: profile only（不做推断）
   - Mode B: 指定 t-test（但数据偏态，需检查假设给替代）
   - Mode C: 完整分析（时序分解 + 异常检测）

数据输出（单表）：
- sensor_readings.csv（4320 行）
  - timestamp（小时粒度）
  - sensor_value（带日/周季节性 + 异常 + 噪声）
  - data_quality_flag（前 90 天 ok，后 90 天 45% 缺失）

注入信号：
A. **时序季节性**（case-03 能力）
   - 日季节性：noon 峰值±10
   - 周季节性：weekend -5

B. **异常分类**（case-03 能力）
   - 10 个随机尖峰（±20-25）
   - day 90-95 水平偏移（+20，系统重校准）
   - day 120+ 趋势漂移（+0.1/day，传感器老化）

C. **数据就绪性分层**（case-08 能力）
   - day 0-90：缺失率 5%（ok for 时序分析）
   - day 90-180：缺失率 45%（blocked，需 data_request）

D. **路由判定**（case-06/07 能力）
   - 根据 prompt 中的请求类型触发不同路由
   - profile-only → 不产出 analysis_plan
   - 指定方法但假设不满足 → 检查并给替代
   - 完整分析 → 正常流程但后半段 blocked

期望分析路径（Mode C）：
1. 读数据 → 识别时序特征（小时粒度 + 180 天）
2. 数据就绪性 → 前 90 天 ok，后 90 天 blocked
3. 前 90 天分析 → STL 分解 + 异常检测（尖峰 + 偏移起点）
4. 后 90 天 → emit data_request，不强行给趋势结论
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260613)

# 180 days, hourly
hours = 180 * 24
timestamps = pd.date_range(datetime(2025, 11, 1), periods=hours, freq='H')
baseline = 50

data = []
spike_idx = set(np.random.choice(hours, 10, replace=False))

for i, ts in enumerate(timestamps):
    hour_of_day = ts.hour
    day_of_week = ts.weekday()
    day = i // 24

    # 日季节性（noon 峰值）
    daily = 10 * np.sin((hour_of_day - 6) * np.pi / 12)

    # 周季节性（weekend 低）
    weekly = -5 if day_of_week >= 5 else 0

    # Baseline + 季节性 + 噪声
    value = baseline + daily + weekly + np.random.normal(0, 2)

    # Signal B: 异常
    # 尖峰
    if i in spike_idx:
        value += np.random.choice([25, -20])

    # day 90-95 水平偏移（重校准）
    if 90 * 24 <= i < 96 * 24:
        value += 20

    # day 120+ 趋势漂移（老化）
    if i >= 120 * 24:
        value += 0.1 * (day - 120)

    # Signal C: 数据质量分层
    if day < 90:
        missing_prob = 0.05  # ok
    else:
        missing_prob = 0.45  # blocked

    if np.random.rand() < missing_prob:
        value = np.nan
        quality_flag = 'missing'
    else:
        quality_flag = 'ok'

    data.append({
        'timestamp': ts,
        'sensor_value': round(value, 2) if not np.isnan(value) else None,
        'data_quality_flag': quality_flag,
        'day': day
    })

df = pd.DataFrame(data)
df.to_csv('sensor_readings.csv', index=False)

print(f"Generated Case C:")
print(f"  sensor_readings.csv: {len(df)} hourly readings (180 days)")
print(f"\nInjected signals:")
print(f"  A) Daily + weekly seasonality")
print(f"  B) 10 spikes + day 90-95 level shift (+20) + day 120+ drift (+0.1/day)")
print(f"  C) Missingness: day 0-90 ~5% (ok), day 90-180 ~45% (blocked)")
print(f"  D) Routing: prompt-driven (profile-only / named-method / full)")

# 验证
print(f"\n=== Verification ===")
print(f"Total missing: {df.sensor_value.isna().mean():.1%}")
print(f"Day 0-90 missing: {df[df.day<90].sensor_value.isna().mean():.1%}")
print(f"Day 90-180 missing: {df[df.day>=90].sensor_value.isna().mean():.1%}")
print(f"Spikes detected: {(df.sensor_value.diff().abs() > 15).sum()} (expected ~20, spike in/out)")
