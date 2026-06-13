# 飞轮迭代 1 失败分析与新方案

**分析时间**：2026-06-13 20:45

---

## 迭代 1 失败总结

### 结果
- Baseline: 84.3 分（Rigor 1/3）
- 迭代 1: 52.9 分（Rigor 1/3）
- **差异**: -31.4 分 ❌

### 修改内容
- 文件：`method-registry.md`
- 位置：Group Comparison + Correlation 章节
- 内容：添加 MANDATORY 假设检验要求

### 为什么失败？

**原因 1：修改位置错误**
- `method-registry.md` 是 references 文档
- Agent 在分析时可能没有读取或应用这个文档
- 需要修改主流程文件（SKILL.md 或 workflow.md）

**原因 2：触发机制缺失**
- 即使 references 有指导，没有明确的触发检查点
- Agent 可能直接使用已知方法，跳过 references 检查

**原因 3：分析输出变短**
- 迭代 1 输出只有 109 行 vs Baseline 的完整报告
- Regex Coverage 从 100% 降到 50%
- 说明分析流程可能被打断或简化了

---

## 新的修复方案

### 方案 A：修改 SKILL.md 主文件（推荐）⭐

**目标**：在主工作流程中强制要求假设检验

**修改位置**：`SKILL.md` L126 附近（交叉验证章节后）

**修改内容**：
```markdown
## Statistical Rigor Requirements

🔴 **MANDATORY before reporting any parametric test result (ANOVA, t-test, Pearson correlation)**:

1. **Check assumptions** BEFORE running the test:
   - Normality: Shapiro-Wilk test (n<50) or Q-Q plot visual (n≥50)
   - Variance homogeneity: Levene test (for ANOVA/t-test)
   - Independence: Check for autocorrelation if time-series data
   
2. **Report the checks** in your analysis:
   ```
   Assumptions checked:
   - Normality: Shapiro-Wilk p=0.XX (normal/non-normal)
   - Variance homogeneity: Levene p=0.XX (equal/unequal)
   ```

3. **If assumptions violated**:
   - Use non-parametric alternative (Mann-Whitney, Kruskal-Wallis, Spearman)
   - OR report violation explicitly in limitations section

**Why this matters**: Parametric tests give invalid p-values when assumptions fail.
A significant ANOVA with violated assumptions is not trustworthy.

Cross-check: `references/method-registry.md` Group Comparison section for detailed guidance.
```

**优势**：
- 在 SKILL.md 主文件中，更容易被 Agent 看到
- 使用 🔴 MANDATORY 强调
- 提供具体的报告格式
- 给出违反假设时的处理方法

---

### 方案 B：在 workflow.md Stage 4 添加检查点

**目标**：在方法选择阶段强制检查

**修改位置**：`workflow.md` Stage 4（method selection）

**修改内容**：
```markdown
### Stage 4: Method Selection & Execution

For each important claim:

1. Select method from `method-registry.md`
2. 🔴 **CHECKPOINT**: If parametric method (ANOVA/t-test/Pearson):
   - Run assumption checks FIRST
   - Document results in analysis_plan
   - If violated → switch to non-parametric
3. Execute analysis
4. Cross-check with alternative method
```

**优势**：
- 在工作流程中明确的检查点
- 强制执行，不能跳过

---

### 方案 C：提供可执行的代码模板

**目标**：降低执行难度，给出具体代码

**修改位置**：`SKILL.md` 或 `method-registry.md`

**修改内容**：
```markdown
## Assumption Check Templates

### For ANOVA:
```python
from scipy import stats

# 1. Normality check (per group)
for group in groups:
    stat, p = stats.shapiro(data[data['group']==group]['value'])
    print(f"{group}: Shapiro-Wilk p={p:.3f} {'✓ normal' if p>=0.05 else '✗ non-normal'}")

# 2. Variance homogeneity
stat, p = stats.levene(*[data[data['group']==g]['value'] for g in groups])
print(f"Levene test p={p:.3f} {'✓ equal variance' if p>=0.05 else '✗ unequal variance'}")

# 3. Decision
if all_normal and equal_variance:
    # Use ANOVA
    stats.f_oneway(...)
else:
    # Use Kruskal-Wallis
    stats.kruskal(...)
```

Report format:
```
Assumptions checked:
- Normality: Shapiro-Wilk p=0.XX for group A, p=0.XX for group B (both normal)
- Variance homogeneity: Levene p=0.XX (equal variance)
- Method: ANOVA is appropriate
```
```

**优势**：
- 具体可执行
- 降低实施难度
- 包含报告格式

---

## 推荐执行顺序

### 立即执行（今晚）

1. ✅ **方案 A**：修改 SKILL.md 主文件
   - 最直接，最容易被看到
   - 强制要求 + 具体格式

### 如果方案 A 仍失败（明天）

2. ⬜ **方案 B**：在 workflow.md 添加检查点
   - 更强的流程控制

3. ⬜ **方案 C**：提供代码模板
   - 降低实施难度

---

## 迭代 2 计划

**修改内容**：方案 A（SKILL.md 主文件）

**验证方法**：
1. 重新运行 Case A
2. 检查报告中是否出现：
   - "Shapiro-Wilk"
   - "Levene test"
   - "Assumptions checked"
3. 对比 Rigor 分数

**成功标准**：
- Rigor 从 1/3 提升到 2/3 或 3/3
- 总分提升 ≥2 分
- 不能让其他维度下降

**如果再次失败**：
- 说明问题不在指导文档
- 可能是 Agent 能力限制
- 需要考虑其他修复维度（Completeness, Clarity）

---

**报告时间**：2026-06-13 20:46  
**下一步**：执行方案 A，启动飞轮迭代 2
