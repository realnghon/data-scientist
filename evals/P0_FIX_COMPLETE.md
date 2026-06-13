# P0 修复完成报告

**日期**：2026-06-13  
**目标**：修复评测系统的 3 个阻断性问题

---

## ✅ P0-1: 修复 Case C 尖峰信号生成

**问题**：尖峰幅度 ±20-25 在基线波动中淹没，无法被标准方法稳定检出

**修复**：
- 文件：`evals/cases/case-c-timeseries-routing/generate_data.py`
- 修改：L75-76，尖峰幅度从 `[25, -20]` 提升到 `[60, -60]`
- 重新生成：`sensor_readings.csv`

**验证结果**：
```
IQR 1.5×IQR: 19 个离群点（包含 day 90-95 偏移段）
MAD k=3.0: 16 个尖峰（纯尖峰，不含偏移段）
前90天: 5 个尖峰（数据质量 ok）
后90天: 14 个离群点（大部分是偏移段）
```

**状态**：✅ 通过（MAD k=3.0 检出 16 个，符合预期 10-20 个）

**更新文档**：
- Ground truth notes 更新，说明实际可检出范围

---

## ✅ P0-2: Ground Truth 添加权重和分级

**问题**：所有 findings 一视同仁，无法区分核心发现和次要发现

**修复**：为所有 3 个 case 的每个 finding 添加：
- `tier`: required / recommended / optional
- `weight`: 1.0-5.0（按重要性）

**Case A (9 findings)**：
- Required (6): spc_stratified_by_line (3.0), l3_out_of_control (5.0), l3_timeframe (3.0), multi_table_join (3.0), chamber_c2_root_cause (5.0), cd_nm_mechanism (4.0)
- Recommended (2): capability_by_line (2.0), noise_rejected (2.0)
- Optional (1): interaction_effect (2.0) — p~0.05 边界不稳定

**Case B (9 findings)**：
- Required (8): conversion_lift (3.0), session_negative (3.0), bounce_negative (3.0), tradeoff_identified (4.0), stratify_by_region (3.0), simpson_detected (5.0), regional_all_negative (4.0), market_shift_explanation (4.0)
- Recommended (1): conditional_recommendation (2.0)

**Case C (9 findings)**：
- Required (6): seasonality_detected (3.0), spike_detected (3.0), level_shift_detected (4.0), data_quality_stratified (3.0), blocked_period_identified (4.0), data_request_emitted (3.0)
- Recommended (2): weekly_pattern (2.0), no_forced_conclusion_late_period (2.0)
- Optional (1): drift_detected (2.0) — 后 90 天数据不足

**状态**：✅ 完成

---

## ✅ P0-3: Regex 评分改为初筛

**问题**：Regex 只能检测"是否提到"，容易被关键词堆砌欺骗，无法验证数量和逻辑一致性

**修复**：
- 新文件：`evals/harness/score_two_stage.py`
- 架构：
  - Stage 1: Regex 初筛（检查 required findings 覆盖率）
    - Coverage < 50% → 直接失败，不进入 Judge
    - Coverage ≥ 50% → 进入 Stage 2
  - Stage 2: Judge 详细评分（运行 3 次取中位数）
    - 消除 LLM 非确定性影响
    - 5 维度评分：correctness / completeness / rigor / clarity / anti_gaming

**使用方法**：
```bash
python evals/harness/score_two_stage.py \
    evals/cases/case-a-manufacturing-comprehensive \
    evals/.runs/some-run \
    --runs 3 \
    --json result.json
```

**状态**：✅ 完成（脚本已创建并测试可运行）

---

## P0 修复总结

**完成情况**：3/3 ✅

**修改文件**：
1. `evals/cases/case-c-timeseries-routing/generate_data.py` — 尖峰幅度提升
2. `evals/cases/case-c-timeseries-routing/ground_truth.json` — notes 更新 + tier/weight 添加
3. `evals/cases/case-a-manufacturing-comprehensive/ground_truth.json` — tier/weight 添加
4. `evals/cases/case-b-business-tradeoff/ground_truth.json` — tier/weight 添加
5. `evals/harness/score_two_stage.py` — 新增两阶段评分器

**数据重新生成**：
- `evals/cases/case-c-timeseries-routing/sensor_readings.csv` ✅

---

## 下一步：重建可信 Baseline

**计划**：
1. 使用修复后的数据和 GT，运行 3-case 评测
2. 使用新的 `score_two_stage.py` 评分器
3. 每个 case 运行 1 次（Judge 内部已经 3 次取中位数）
4. 记录为新的可信 baseline

**预期时间**：30-60 分钟（3 个 case × 10-20 分钟/case）

**命令示例**（需要先有运行产物）：
```bash
# 先运行 case 生成报告（通过 claude -p 或 run_l2.py）
# 然后评分
python evals/harness/score_two_stage.py \
    evals/cases/case-a-manufacturing-comprehensive \
    evals/.runs/baseline-20260613/case-a \
    --runs 3 \
    --json baseline-case-a.json
```

---

**完成时间**：2026-06-13 20:30  
**总耗时**：约 30 分钟
