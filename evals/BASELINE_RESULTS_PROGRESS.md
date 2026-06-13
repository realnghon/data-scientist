# Baseline 结果记录（进行中）

**更新时间**：2026-06-13 20:30

---

## 已完成的评分

### ✅ Case A: Manufacturing Comprehensive
- **总分**：84.3 / 100
- **标准差**：7.9（3次运行：86.3, 68.6, 84.3）⚠️ 偏高
- **Judge 稳定性**：⚠️ 中等（std < 10，但接近边界）
- **Regex Coverage**：100%（6/6 required findings）
- **结果文件**：`evals/.runs/baseline-20260613/case-a-score.json`

**Judge 维度详情**：
- **Correctness**: 3/3 ✅ — 9个发现全部覆盖，因果链完整
- **Completeness**: 3/3 ✅ — 包括负向结论和局限性
- **Rigor**: 1/3 ❌ — **致命缺陷：ANOVA/Pearson假设未验证**
- **Clarity**: 3/3 ✅ — 因果链清晰，量化完整
- **Anti-gaming**: 3/3 ✅ — 诚实披露局限性

**Defects（5个）**：
1. **Correctness**: ANOVA假设未验证（报告已承认）
2. **Rigor**: 参数检验前提假设零验证（正态性、方差齐性）⭐ 核心缺陷
3. **Rigor**: 非参数交叉验证流于形式（提到Kruskal-Wallis但无结果）
4. **Rigor**: 因果推断逻辑跳跃（观察性数据断言因果）
5. **Rigor**: SPC-wafer分析割裂（时间混杂未探讨）

**对比旧baseline**：
- 旧方法：judge=76.5
- 新方法：judge=84.3（中位数）
- 差异：**+7.8** ✅
- **分析**：Rigor 仅 1/3，但其他维度很好。这正是飞轮迭代 1 要修复的！

---

### ✅ Case B: Business Tradeoff
- **总分**：86.3 / 100
- **标准差**：2.4（3次运行：82.4, 86.3, 88.2）
- **Judge 稳定性**：✅ 优秀（std < 5）
- **Regex Coverage**：87.5%（7/8 required findings）

**Judge 维度详情**：
- **Correctness**: 3/3 ✅
- **Completeness**: 3/3 ✅
- **Rigor**: 2/3 ⚠️ — 独立性和时序性假设未验证
- **Clarity**: 3/3 ✅
- **Anti-gaming**: 2/3 ⚠️

**Defects（3个）**：
1. **Rigor**: 独立性假设未验证（用户聚类效应）
2. **Rigor**: 时序性未分析（690天跨度）
3. **Anti-gaming**: Mantel-Haenszel验证未给出数值

**对比旧baseline**：
- 旧方法：judge=92.2
- 新方法：judge=86.3
- 差异：**-5.9**

---

## 进行中的任务

### Case A: Manufacturing Comprehensive
- **状态**：⏳ 评分进行中（3次取中位数）
- **PID**：94112
- **预计完成**：20:45-21:00

### Case C: Timeseries Routing
- **状态**：⏳ 分析进行中（使用修复后数据）
- **PID**：94387
- **预计完成**：20:40-21:00
- **后续**：分析完成后需要评分（+45分钟）

---

## 对比旧 Baseline（审计前）

| Case | 旧 Baseline | 新 Baseline | 差异 |
|------|-------------|-------------|------|
| A    | 83.7 (judge) | 待测 | - |
| B    | 92.2 (judge) | **86.3** | **-5.9** |
| C    | 82.4 (judge) | 待测 | - |
| 平均 | 86.1 | 待测 | - |

**Case B 下降分析**：
- 旧方法：regex=93.4, judge=92.2
- 新方法：judge=86.3（3次取中位数，std=2.4）
- **可能原因**：
  1. 新 GT 有权重分级，optional findings 权重低
  2. 旧评分可能是单次运行的高值，新评分是 3 次中位数（更可靠）
  3. 需要读取 defects 才能确定是否有新发现的问题

**下一步**：读取 Case B 详细结果，分析 defects

---

**更新者**：Claude Code  
**下次更新**：Case A 或 Case C 完成时
