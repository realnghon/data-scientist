# 评测结果分析报告

## 核心发现

基于 2 个 case（case-09: 100分，case-01: 89.2分）的评测，得出以下结论：

### 1. **单 agent 路径完全可行** ✅

**证据**：
- 两个 case 都是单个 agent 完成的（没有 spawn 子 agent）
- 所有 routing 和 artifacts 检查都通过
- Agent 通过 `ds_skill` helpers 成功完成了 7-stage pipeline

**结论**：
- ❌ **不需要** 强制多 agent 编排（优先级 1 方案）
- ✅ **采用** 单 agent 路径（优先级 2 方案）
- 架构问题已解决：`agents/` 和 `commands/` 不是必需的，可以简化或废弃

---

### 2. **失败模式：方法覆盖不足，而非架构问题**

**Case-01 失败的唯一检查**：`temperature_main_effect`

**根本原因**：
- 数据注入的是**非线性效应**（最优区间 180-200°C，两侧下降）
- Agent 只测试了**线性相关性**（Spearman/Pearson ρ）
- 线性相关性弱（ρ ≈ 0.1），p_fdr = 0.069（不显著）
- Agent 正确判定为"不显著"，但遗漏了**非线性模式**

**对比数据生成脚本**：
```python
# 真实注入的效应
if 180 <= temp <= 200:
    temp_effect = 0  # optimal zone
else:
    deviation = min(abs(temp - 180), abs(temp - 200))
    temp_effect = -deviation * 0.15  # 偏离越远，yield 越低
```

**需要的检测方法**：
1. 分箱检验（将 temp 分为 <180 / 180-200 / >200 三个区间，ANOVA 检验）
2. 二次项检验（temp + temp² 回归）
3. 可视化（scatter + LOWESS smooth）识别 U 型或倒 U 型

---

## 失败模式分类

基于 2 个 case，识别出 **1 个** 失败模式：

| 失败模式 ID | 描述 | 影响的 case | 严重程度 |
|------------|------|-----------|---------|
| **FM-01** | 缺少非线性关系检测（最优区间、U 型曲线） | case-01 | 中等（-10.8 分） |

**预测**：剩余 7 个 case 可能暴露的失败模式：
- FM-02: 时序异常检测（case-03）
- FM-03: SPC 控制图规则（case-04）
- FM-04: Simpson 悖论识别（case-05）
- FM-05: 路由逻辑（case-06, 07, 08）

---

## 修复优先级

### 优先级 1：修复 FM-01（非线性关系检测）

**目标文件**：`plugins/data-scientist/skills/analysis-workflow/references/manufacturing-playbook.md`

**修复内容**：在 Step 13（驱动因素排序）后增加：

```markdown
### Step 13.6: 检测工艺参数的最优区间

对于温度、压力、流量、时间等工艺参数，不要只测试线性相关性。执行以下检查：

1. **分箱检验**（首选方法）：
   - 将参数分为 3 个区间：低 (0-33%ile)、中 (33-67%ile)、高 (67-100%ile)
   - 用 Kruskal-Wallis 检验三组 yield 差异
   - 如果显著（p < 0.05），比较三组中位数：
     - 中间组最高 → "optimal range"模式
     - 单调趋势 → 线性效应
   
2. **二次项检验**（补充方法）：
   - 拟合 `yield ~ param + param²`
   - 如果 param² 系数显著（p < 0.05）且为负 → 倒 U 型（最优区间）
   - 计算最优值：`optimal = -coef[param] / (2 × coef[param²])`

3. **报告格式**：
   - 如果检测到最优区间：
     ```
     Temperature shows an optimal zone effect: yield is highest at 180-200°C 
     (median 87%), dropping at extremes (<180°C: 82%, >200°C: 83%).
     Kruskal-Wallis p=0.001, binned effect size η²=0.15.
     ```

**何时跳过**：参数已知是单调的（时间、数量、计数），或用户明确只关心线性趋势。
```

**预期效果**：case-01 分数从 89.2 → 100

---

### 优先级 2：完成剩余 7 个 case 的评测

**目标**：在修复 FM-01 之前，先跑完所有 case，收集完整的失败模式列表。

**原因**：
- 避免"补一个漏洞发现另一个"的循环
- 系统性识别所有问题后，一次性修复

**执行计划**：
- 下一会话：跑 case-02, 03, 04（预计 ~250k tokens）
- 第三会话：跑 case-05, 06, 07, 08（预计 ~250k tokens）
- 第四会话：汇总所有失败模式 + 统一修复

---

### 优先级 3：简化架构（可选）

**目标**：废弃未使用的 `agents/` 目录，减少维护负担

**行动**：
1. 将 `agents/ds-*-agent.md` 的关键指令合并到对应的 reference 文档
2. 删除 `agents/` 目录
3. 简化 `multi-agent-orchestration.md` → `workflow-execution-patterns.md`（只保留并行化提示）

**时机**：所有 case 饱和（90+ 分）后再执行

---

## 下一步行动

**立即执行**：
1. ✅ 已完成 case-09（100分）和 case-01（89.2分）评测
2. ⏭️ **下一会话**：继续评测 case-02, 03, 04
3. 📝 记录所有失败模式到 `FAILURE_MODES.md`

**暂缓执行**：
- ⏸️ 修复 FM-01（等待收集完所有失败模式）
- ⏸️ 架构简化（等待所有 case 饱和）

**目标检查点**：
- [ ] 完成 9 个 case 评测（当前 2/9）
- [ ] 识别所有失败模式（当前 1 个）
- [ ] 统一修复后重新评测
- [ ] 平均分数 ≥ 90
