# Baseline 重建计划

**日期**：2026-06-13  
**前置条件**：P0 修复完成 ✅

---

## 目标

使用修复后的数据和 GT，建立新的可信 baseline，替代之前受以下问题影响的历史分数：
1. Case C 尖峰信号不足
2. Ground truth 缺少权重分级
3. 评分方法容易被关键词堆砌欺骗

---

## 方法

### 方案 A：使用修复后的数据重新运行完整评测（推荐）

**步骤**：
1. 用修复后的 Case C 数据，运行 3-case 完整评测
2. 使用 `score_two_stage.py` 评分（Regex 初筛 + Judge 3次取中位数）
3. 记录为可信 baseline

**命令**：
```bash
# 方法 1：使用现有的 run_l2.py（需要修改以使用 score_two_stage.py）
cd /Users/silaswu/Silas_Develop/data-scientist
python evals/harness/run_l2.py case-a case-b case-c \
    --jobs 3 \
    --output-dir evals/.runs/l2/baseline-20260613-fixed

# 方法 2：手动运行每个 case（更可控）
# 2.1 运行分析（生成报告）
for case in case-a case-b case-c; do
    mkdir -p evals/.runs/baseline-20260613/$case
    cd evals/cases/${case}-*
    cat prompt.txt | claude -p > ../../.runs/baseline-20260613/$case/final_report.md
    cd /Users/silaswu/Silas_Develop/data-scientist
done

# 2.2 评分
for case in case-a case-b case-c; do
    python evals/harness/score_two_stage.py \
        evals/cases/${case}-* \
        evals/.runs/baseline-20260613/$case \
        --runs 3 \
        --json evals/.runs/baseline-20260613/${case}-score.json
done
```

**预期时间**：
- 运行分析：3 × 10-15 分钟 = 30-45 分钟
- 评分：3 × (1 分钟初筛 + 3 × 5 分钟 judge) = 48 分钟
- **总计：约 1.5-2 小时**

---

### 方案 B：对现有运行重新评分（快速验证）

**前提**：20260613-1348 的运行使用的是旧 Case C 数据，但可以先验证评分器是否正常工作

**步骤**：
1. 对现有最近运行（20260613-1348）使用新评分器评分
2. 对比新旧评分方法的差异
3. 如果差异显著，说明评分方法改进有效

**命令**：
```bash
cd /Users/silaswu/Silas_Develop/data-scientist

# Case A（已在运行，PID 90431）
python evals/harness/score_two_stage.py \
    evals/cases/case-a-manufacturing-comprehensive \
    evals/.runs/l2/20260613-1348/case-a-manufacturing-comprehensive \
    --runs 3 \
    --json /tmp/recore_case_a.json

# Case B
python evals/harness/score_two_stage.py \
    evals/cases/case-b-business-tradeoff \
    evals/.runs/l2/20260613-1217/case-b-business-tradeoff \
    --runs 3 \
    --json /tmp/rescore_case_b.json

# Case C（注意：使用的是旧数据）
python evals/harness/score_two_stage.py \
    evals/cases/case-c-timeseries-routing \
    evals/.runs/l2/20260613-1217/case-c-timeseries-routing \
    --runs 3 \
    --json /tmp/rescore_case_c_old_data.json
```

**预期时间**：约 45 分钟（3 × 15 分钟）

---

## 推荐方案

**短期（今天）**：方案 B — 验证评分器工作正常

**中期（明天）**：方案 A — 完整重新运行建立可信 baseline

**理由**：
1. 方案 B 可以快速验证 P0-3（两阶段评分器）是否正常工作
2. 如果 judge 评分稳定性良好（3 次标准差 <5），说明评分器设计合理
3. 方案 A 需要较长时间，适合在审计报告完成后进行

---

## 评分指标对比

**旧方法（20260613-1348）**：
- Case A: regex=93.7, judge=76.5
- Case B: regex=93.4, judge=92.2
- Case C: regex=76.0, judge=82.4
- 平均 judge: 83.7

**新方法预期**：
- Regex 初筛：Coverage 检测（不再是 0-100 分数）
- Judge: 3 次取中位数（预期标准差 <5）
- Required findings 权重更高，optional 可以未检出

---

## 当前进度

- [x] P0-1: Case C 数据修复
- [x] P0-2: GT 权重分级
- [x] P0-3: 两阶段评分器
- [ ] 方案 B: 重新评分验证（进行中，PID 90431）
- [ ] 方案 A: 完整重建 baseline（待执行）

---

**更新时间**：2026-06-13 20:10  
**下一步**：等待方案 B 完成，验证评分器稳定性
