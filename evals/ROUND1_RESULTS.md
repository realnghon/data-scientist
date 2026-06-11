# Round 1: Agent Judge 评测结果

## 评分对比

| Case | Regex | Judge | Δ | 状态 |
|------|-------|-------|---|------|
| Case-01 | 100 | **27.5** | -72.5 | Ground truth vs 数据生成器不匹配 |
| Case-02 | 100 | **82.4** | -17.6 | Rigor + anti-gaming 待改进 |
| Case-09 | 100 | **33.3** | -66.7 | 统计显著性误用（已修复 Skill）|

## 关键发现

### 1. Regex 评分严重高估质量
- 所有案例 regex 100/100，但 judge 平均仅 47.7/100
- Regex 无法检测统计方法论错误、逻辑矛盾、规格异常

### 2. Skill 缺陷（已修复 1 个）

**Case-09 统计显著性误用**（已修复，commit 97d08c2）：
- 问题：将 p>0.15 的结果标记为"Tier-1 可靠结论"
- 修复：Gate 4 强化（Tier-1 必须 p<0.05），Gate 6 新增（规格合理性检查）
- 预期：case-09 从 33.3 → 70+（需重新运行验证）

**Case-02 Rigor 不足**（待修复）：
- 缺少：协变量平衡、分布检验、时序效应、泄漏排查
- 方案：A/B 测试强制检查清单
- 预期：case-02 从 82.4 → 90+

### 3. Ground Truth 问题

**Case-01 数据 vs GT 不匹配**：
- GT 期望：temperature 主效应 + interaction
- Agent 发现：equipment_age 主效应（r=-0.353, p<0.001）
- 数据生成器：temperature × age 交互（age 是 amplifier）
- **问题**：GT 未正确描述数据生成逻辑，导致 agent 正确分析却被判错

## 迭代计划

### Round 2（下次会话）
1. 重新运行 case-09（验证 Skill 修复效果）
2. 修复 case-01 ground truth（对齐数据生成器）
3. 实施 case-02 rigor 改进
4. 目标：3 个案例平均 > 70

### Round 3+
- 继续迭代直到所有案例 > 90
- 扩展到 case-03/04/05/06/07/08
- 案例难度升级（case-09 v3）

## Skill 改进记录

- **commit 97d08c2**：强化统计显著性要求 + 规格合理性检查

## 下次会话起点

```bash
# 1. 验证 case-09 修复
python evals/harness/score_case.py evals/cases/case-09-wafer-rca \
  evals/.runs/l2/case-09-v2-RERUN --mode judge

# 2. 修正 case-01 ground truth
# 编辑 case-01-manufacturing-full/ground_truth_v2.json

# 3. 重新运行 case-01 agent（使用修复后的 Skill）
```
