# 评测系统审计与修复 — 进度总结

**日期**：2026-06-13  
**审计报告**：`EVAL_SYSTEM_AUDIT_20260613.md`  
**执行摘要**：`AUDIT_EXECUTIVE_SUMMARY.md`

---

## 已完成工作

### ✅ 阶段 1：全面审计（3 小时）

**审计范围**：
- 3/3 case 数据质量验证
- 3/3 case ground truth 完整性
- 2/2 评分器（regex + judge）
- 8/8 references 文档使用率
- 3/3 golden templates 触发情况

**核心发现**：
1. ❌ Case C 尖峰信号无法稳定检出（声称 10 个，实测 0 个）
2. ⚠️ Ground Truth 定义不完整（缺权重、容差、分级）
3. ⚠️ Regex 评分容易被关键词堆砌欺骗
4. ⚠️ Golden Templates 从未被触发（0 次提到）
5. ⚠️ References 从未因评测而更新

**评测系统可信度**：
- Case A/B: 70%
- Case C: 30%
- 飞轮第 1 轮提升：50%（可能部分来自"学会关键词"）

---

### ✅ 阶段 2：P0 修复（30 分钟）

**P0-1: 修复 Case C 尖峰信号** ✅
- 文件：`generate_data.py`
- 修改：尖峰幅度从 ±20-25 提升到 ±60
- 验证：MAD k=3.0 检出 16 个（符合预期）
- 数据：重新生成 `sensor_readings.csv`

**P0-2: Ground Truth 添加权重和分级** ✅
- 文件：3 个 case 的 `ground_truth.json`
- 添加：`tier` (required/recommended/optional) + `weight` (1.0-5.0)
- Case A: 6 required, 2 recommended, 1 optional
- Case B: 8 required, 1 recommended
- Case C: 6 required, 2 recommended, 1 optional

**P0-3: Regex 评分改为初筛** ✅
- 文件：新增 `score_two_stage.py`
- 架构：
  - Stage 1: Regex 初筛（Coverage < 50% 直接失败）
  - Stage 2: Judge 详细评分（3 次取中位数）
- 状态：脚本已创建，测试运行中

---

## 进行中工作

### 🔄 阶段 3：重建可信 Baseline

**当前状态**：
- 方案 B（快速验证）：测试 Case A 重新评分（PID 90431，进行中）
- 预期完成时间：10-15 分钟

**下一步**：
1. 等待 Case A 评分完成
2. 如果成功，继续评分 Case B 和 Case C
3. 对比新旧评分方法差异
4. 验证 judge 评分稳定性（3 次标准差应 <5）

---

## 待执行工作

### ⬜ 阶段 4：完整 Baseline 重建（1.5-2 小时）

**任务**：
- 使用修复后的 Case C 数据
- 运行 3-case 完整评测
- 使用 `score_two_stage.py` 评分
- 记录为新的可信 baseline

**命令准备**：见 `BASELINE_REBUILD_PLAN.md`

---

### ⬜ 阶段 5：飞轮第 2 轮迭代（1 周）

**前置条件**：可信 baseline 建立

**流程**：
1. 读 judge defects，定位 SKILL.md 薄弱维度
2. 修复一个维度（一次只改一处）
3. 重跑 3-case 验证改进
4. 对比分数：提升 → commit，下降 → revert
5. 更新迭代记录

**目标**：Judge 平均分从 baseline 提升到 >90

---

### ⬜ 阶段 6：P1/P2 改进（并行推进）

**P1 — 高优先级（3-5 天）**：
- [ ] Judge 添加数据真值（验证数值准确性）
- [ ] 验证 Golden Templates 触发逻辑
- [ ] 多次运行稳定性分析

**P2 — 中优先级（1-2 周）**：
- [ ] 添加 workflow_adherence 维度
- [ ] 建立 References 更新触发机制
- [ ] 多选手对比实验

---

## 关键决策点

### ❓ 是否继续使用旧数据的历史分数？

**答案**：❌ 不可以

**理由**：
1. Case C 数据缺陷导致评测失真
2. GT 权重分级缺失导致评分不公平
3. Regex 评分方法缺陷导致关键词堆砌被奖励

**行动**：所有历史分数标记为"审计前数据，仅供参考"

---

### ❓ 飞轮第 1 轮的提升是否有效？

**答案**：⚠️ 部分有效，但可信度 50%

**理由**：
1. Case A/B 的提升可能有效（数据准确）
2. Case C 的提升 62.7 → 82.4 存疑（数据缺陷）
3. 提升可能部分来自"学会说关键词"而非真正能力

**行动**：
1. 保留 SKILL.md 的 5 个修复 commits（逻辑正确）
2. 重建 baseline 后重新验证提升幅度
3. 如果新 baseline 下仍有提升 → 确认有效

---

### ❓ 是否需要重新设计所有 3 个 case？

**答案**：❌ 不需要

**理由**：
1. Case A/B 数据准确，GT 合理
2. Case C 只需数据修复（已完成）
3. GT 权重分级是增强，不是重新设计

**行动**：保持当前 case 设计，继续迭代

---

## 文档索引

**审计报告**：
- `EVAL_SYSTEM_AUDIT_20260613.md` — 完整审计报告（6000+ 字）
- `AUDIT_EXECUTIVE_SUMMARY.md` — 执行摘要（快速阅读）
- `AUDIT_FIX_CHECKLIST.md` — 修复清单（任务列表）

**修复记录**：
- `P0_FIX_COMPLETE.md` — P0 修复完成报告
- `BASELINE_REBUILD_PLAN.md` — Baseline 重建计划

**数据修复**：
- `evals/cases/case-c-timeseries-routing/generate_data.py` — 已修复
- `evals/cases/case-c-timeseries-routing/sensor_readings.csv` — 已重新生成

**评分工具**：
- `evals/harness/score_two_stage.py` — 新增两阶段评分器

---

## 时间线

```
2026-06-13 17:00 - 20:00  ✅ 审计（3 小时）
2026-06-13 20:00 - 20:30  ✅ P0 修复（30 分钟）
2026-06-13 20:30 - 21:00  🔄 Baseline 验证（进行中）
2026-06-13 21:00 - 23:00  ⬜ 完整 Baseline 重建（待执行）
2026-06-14 - 2026-06-20   ⬜ 飞轮第 2 轮迭代（1 周）
2026-06-21 - 2026-06-30   ⬜ P1/P2 改进（并行推进）
```

---

## 当前瓶颈

**技术瓶颈**：
- Judge 评分速度慢（每次 5 分钟 × 3 次 = 15 分钟）
- 无法并行运行多个 judge（共享 claude CLI）

**解决方案**：
- 短期：接受当前速度，3-case 完整评测约 45 分钟
- 中期：考虑使用 API 直接调用（绕过 CLI）
- 长期：建立评分缓存机制（相同报告不重复评分）

---

**更新时间**：2026-06-13 20:15  
**负责人**：Claude Code (Opus 4.8)  
**下一更新**：Case A 评分完成后
