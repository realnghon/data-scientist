# 飞轮第 2 轮迭代计划

**前置条件**：Baseline 重建完成（进行中）  
**目标**：基于可信 baseline，修复 SKILL.md 薄弱维度，提升平均 judge 分数到 >90

---

## 迭代流程（标准化）

```
1. 读 judge defects → 定位薄弱维度
2. 分析 defects 根因 → 定位 SKILL.md 哪一行需要修改
3. 修复一个维度（一次只改一处）
4. 重跑 3-case 验证改进
5. 对比分数：
   - 提升 ≥2 分 且无其他维度下降 → commit
   - 提升 <2 分 或其他维度下降 → revert，换方向
6. 更新 STATUS.md 记录迭代
7. 重复步骤 1-6
```

---

## 从 Baseline 获取的 Defects（基于 Case A 验证结果）

### Rigor 维度 Defects（4 个）⭐ 最高优先级

**Defect 1：参数方法假设未检验**
- **描述**：ANOVA、Pearson 相关的前提假设（正态性、方差齐性）未检验
- **影响**：核心缺陷，rigor 评分 2/3
- **根因**：SKILL.md 未强制要求假设检验
- **定位**：SKILL.md 可能在 method-registry.md 的 ANOVA/correlation 章节
- **修复方向**：
  ```markdown
  ## ANOVA 使用前提
  **MANDATORY checks before ANOVA**:
  1. Normality: Shapiro-Wilk test (n<5000) or QQ-plot
  2. Homogeneity of variance: Levene test
  3. If violated: use Welch ANOVA (unequal variance) or Kruskal-Wallis (non-normal)
  ```

**Defect 2：交叉验证不完整**
- **描述**：声称做了 Kruskal-Wallis 但未展示结果
- **影响**：rigor 评分扣分
- **根因**：SKILL.md 要求"交叉验证"但未明确"必须展示结果"
- **定位**：SKILL.md L15（交叉验证要求）
- **修复方向**：
  ```markdown
  Cross-check every important finding with at least one alternative method.
  **MUST report both results in evidence_matrix**: primary method + cross-check method with p-values.
  ```

**Defect 3：独立性假设未检查**
- **描述**：wafer 时间序列可能存在自相关，未检查
- **影响**：rigor 评分扣分
- **根因**：SKILL.md 未提及时间序列数据的独立性检查
- **定位**：SKILL.md 或 time_series.md
- **修复方向**：
  ```markdown
  **For time-ordered data**: Check autocorrelation with Ljung-Box test before regression.
  If p<0.05, residuals are autocorrelated → consider ARIMA or add time controls.
  ```

**Defect 4：样本不平衡未评估**
- **描述**：C2 样本量 55% 但未评估对 ANOVA 的影响
- **影响**：rigor 评分扣分
- **根因**：SKILL.md 未提及样本不平衡的影响
- **定位**：method-registry.md ANOVA 章节
- **修复方向**：
  ```markdown
  **Sample size imbalance**: If largest group > 2× smallest group, 
  report the imbalance and consider weighted ANOVA or stratified analysis.
  ```

### Correctness 维度 Defects（2 个）

**Defect 5：边界显著性判定**
- **描述**：p=0.101 判定为"不显著"，但 GT 标注为 optional
- **影响**：correctness 评分 2/3，但这是合理的判定
- **根因**：SKILL.md 对 0.05 < p < 0.10 的边界情况未给指导
- **优先级**：P2（因为 GT 已标注 optional，争议性低）
- **修复方向**：
  ```markdown
  **Borderline significance (0.05 < p < 0.10)**: 
  - Label as "marginally significant" or "borderline"
  - Report with caveat "requires further validation"
  - Do NOT claim as Tier-1 finding
  ```

**Defect 6：SPC 失控与 yield 关联弱**
- **描述**：L3 失控期 vs 正常期 yield 差异 p=0.21 不显著
- **影响**：correctness 评分扣分，但这可能是数据设计问题
- **根因**：数据生成器中 L3 失控未强关联到 wafer yield
- **优先级**：P3（需要先验证数据）

---

## 飞轮第 2 轮修复顺序（按优先级）

### 迭代 1：参数方法假设检验（Rigor Defect 1）⭐ 最高优先级

**目标**：强制要求 ANOVA/Pearson 前检查假设

**修改位置**：
1. `plugins/data-scientist/skills/analysis-workflow/references/method-registry.md`
   - ANOVA 章节添加 "MANDATORY checks"
   - Correlation 章节添加假设检验要求

2. `plugins/data-scientist/skills/analysis-workflow/skill.md`
   - 可能在 L126（交叉验证章节）附近添加假设检验提醒

**验证**：
- 重跑 Case A，检查报告中是否出现 Shapiro-Wilk、Levene test 结果
- Judge rigor 维度应从 2/3 提升到 3/3

**预期提升**：+3-5 分

---

### 迭代 2：交叉验证结果展示（Rigor Defect 2）

**目标**：明确要求交叉验证必须展示两个方法的结果

**修改位置**：
1. `skill.md` L15 交叉验证要求
2. `report-standard.md` evidence_matrix 格式

**验证**：
- 报告中 evidence_matrix 包含 primary + cross-check 结果
- Judge rigor/completeness 维度提升

**预期提升**：+2-3 分

---

### 迭代 3：独立性假设检查（Rigor Defect 3）

**目标**：时间序列数据增加自相关检查

**修改位置**：
1. `skill.md` 或 `references/time_series.md`
2. 可能需要添加 Ljung-Box test 指导

**验证**：
- 时序数据分析中出现自相关检查
- Judge rigor 维度提升

**预期提升**：+1-2 分

---

### 迭代 4：样本不平衡评估（Rigor Defect 4）

**目标**：ANOVA 前评估样本不平衡的影响

**修改位置**：
1. `references/method-registry.md` ANOVA 章节

**验证**：
- 报告中提到样本不平衡及其处理方式
- Judge rigor 维度提升

**预期提升**：+1-2 分

---

### 迭代 5：边界显著性处理（Correctness Defect 5）

**目标**：对 0.05 < p < 0.10 给出明确指导

**修改位置**：
1. `skill.md` Tier-1 判定标准章节

**验证**：
- p~0.05 边界结果被标记为 "marginally significant"
- Judge correctness 维度提升

**预期提升**：+1-2 分

---

## 迭代终止条件

1. **目标达成**：平均 judge 分数 ≥90
2. **边际递减**：连续 2 次迭代提升 <1 分
3. **时间限制**：完成 5 次迭代（约 1 周）

---

## 迭代记录模板

```markdown
## 迭代 N：[维度名称]

**日期**：2026-06-XX
**Defect**：[defect 描述]
**修改**：
- 文件：[file_path]
- 行号：[L123-L456]
- 内容：[修改描述]

**验证结果**：
| Case | Before | After | Δ |
|------|--------|-------|---|
| A    | 82.4   | XX.X  | +X.X |
| B    | YY.Y   | YY.Y  | +Y.Y |
| C    | ZZ.Z   | ZZ.Z  | +Z.Z |
| 平均 | XX.X   | XX.X  | +X.X |

**Judge 维度变化**：
- Rigor: 2/3 → 3/3 ✅
- Correctness: 2/3 → 2/3
- ...

**决策**：Commit / Revert
**Commit ID**：[git commit hash]
```

---

## 当前状态

**Baseline**：
- Case A: 82.4（1 次运行，待 3 次确认）
- Case B: 待评分
- Case C: 待重新运行 + 评分
- 平均: 待计算

**下一步**：
1. ⏳ 等待 baseline 完成
2. ⬜ 读取所有 defects
3. ⬜ 启动迭代 1（参数方法假设检验）

---

**更新时间**：2026-06-13 20:20  
**预计启动**：Baseline 完成后（约 1-2 小时）
