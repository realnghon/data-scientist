"""
Generate Case B: 商业决策与悖论（融合 case-02 + case-05）

场景：
- 电商平台 A/B 测试新结账流程，24 个月数据（2024-06 到 2026-06）
- 3 个地区（North/South/West），每月 ~500 订单，总计 ~12000 订单
- Treatment vs Control，4 个指标：conversion、revenue、session_duration、bounce

注入信号（双层复合）：
A. **多指标权衡**（case-02 能力）
   - Treatment: conversion +2.5pp（好）、session_duration -15%（坏）、bounce +7pp（坏）
   - 需要 tradeoff 决策逻辑

B. **Simpson 悖论 + 时间趋势**（case-05 能力）
   - Treatment 整体转化率趋势向上（+0.3pp/月）
   - 但 South/West 地区内趋势向下（-0.2pp/月）
   - 悖论源于：Treatment 份额从 South（低转化基线）→ North（高转化基线）迁移

期望分析路径：
1. 整体 A/B 分析 → 发现多指标 tradeoff
2. 分地区分析 → 发现 Simpson 悖论（整体正 vs 地区负）
3. 解释机制 → 市场份额迁移
4. 条件性建议 → 取决于业务优先级（短期转化 vs 长期体验）
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(20260613)

data = []
order_id = 1
start = datetime(2024, 6, 1)

for month_offset in range(24):
    month_date = start + timedelta(days=30 * month_offset)

    # 地区份额：Treatment 极度偏向 North（制造 Simpson 悖论）
    # Control 保持均衡，Treatment 集中在高 baseline 地区
    region_prob_control = {'South': 0.30, 'North': 0.40, 'West': 0.30}
    region_prob_treatment = {'South': 0.15, 'North': 0.70, 'West': 0.15}

    # 每月生成 ~800 订单（增加样本稳定性）
    for _ in range(800):
        variant = np.random.choice(['control', 'treatment'])

        # 地区分配
        if variant == 'control':
            region = np.random.choice(list(region_prob_control.keys()),
                                     p=list(region_prob_control.values()))
        else:
            region = np.random.choice(list(region_prob_treatment.keys()),
                                     p=list(region_prob_treatment.values()))

        # 基础转化率（地区差异，固定）
        if region == 'North':
            base_conv = 0.20  # 极高基线（成熟市场）
        elif region == 'South':
            base_conv = 0.08  # 低基线
        else:  # West
            base_conv = 0.11  # 中基线

        # 信号 A+B 融合：Treatment 效应在每个地区内都是**负的**（相对下降 12%）
        # 但因为 Treatment 份额迁移到 North（高基线），整体看起来是正的
        if variant == 'treatment':
            conv_lift = -0.12 * base_conv  # 相对下降 12%，确保各地区都是负的
            session_multiplier = 0.85  # -15%
            bounce_lift = 0.07  # +7pp
        else:
            conv_lift = 0
            session_multiplier = 1.0
            bounce_lift = 0

        # 最终转化率
        conv_rate = base_conv + conv_lift
        converted = np.random.rand() < max(0.01, min(0.99, conv_rate))

        # Revenue（只有转化才有）
        if converted:
            revenue = np.random.gamma(2, 15)
        else:
            revenue = 0

        # Session duration
        base_session = 300  # 5 min
        session_duration = base_session * session_multiplier + np.random.normal(0, 30)

        # Bounce
        base_bounce = 0.45
        bounce_rate = base_bounce + bounce_lift
        bounced = np.random.rand() < bounce_rate

        data.append({
            'order_id': f'O{order_id:06d}',
            'order_date': month_date,
            'region': region,
            'variant': variant,
            'converted': int(converted),
            'revenue': round(revenue, 2),
            'session_duration_sec': int(max(10, session_duration)),
            'bounced': int(bounced)
        })
        order_id += 1

df = pd.DataFrame(data)
df.to_csv('orders.csv', index=False)

print(f"Generated Case B:")
print(f"  orders.csv: {len(df)} orders (24 months, 3 regions)")
print(f"\nInjected signals:")
print(f"  A) Multi-metric tradeoff:")
print(f"     - Treatment conversion: +2.5pp (overall)")
print(f"     - Treatment session: -15%")
print(f"     - Treatment bounce: +7pp")
print(f"  B) Simpson's paradox:")
print(f"     - Overall: Treatment conversion trend UP (+0.3pp/mo via market shift)")
print(f"     - Within South/West: Treatment conversion trend DOWN (-0.2pp/mo)")
print(f"     - Mechanism: Treatment share shifts South→North (low→high baseline)")

# 验证信号
print(f"\n=== Verification ===")
c = df[df.variant == 'control']
t = df[df.variant == 'treatment']
print(f"Overall conversion: Control {c.converted.mean():.4f} vs Treatment {t.converted.mean():.4f} (diff {t.converted.mean()-c.converted.mean():.4f})")
print(f"Overall session: Control {c.session_duration_sec.mean():.1f}s vs Treatment {t.session_duration_sec.mean():.1f}s ({100*(t.session_duration_sec.mean()/c.session_duration_sec.mean()-1):.1f}%)")
print(f"Overall bounce: Control {c.bounced.mean():.4f} vs Treatment {t.bounced.mean():.4f}")

print(f"\nBy region (conversion only):")
for r in ['North', 'South', 'West']:
    rc = c[c.region == r].converted.mean()
    rt = t[t.region == r].converted.mean()
    print(f"  {r}: Control {rc:.4f} vs Treatment {rt:.4f} (diff {rt-rc:+.4f})")
