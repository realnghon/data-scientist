---
name: method-registry
description: 统计方法速查表，按分析目的索引。选方法时查阅。
---

# Method Registry

按分析目的查方法。每个方法记录：helper 函数路径、使用条件。

**签名是源码说了算。** 下面的调用串只指路，不是权威签名 —— 参数名、keyword-only、返回类型（多为 dataclass，用 `.attr` 取值，不是 `["key"]`）以源码为准。首次调用某 helper 前，先 `grep -n "def <name>" -A6 scripts/ds_skill/<module>.py` 确认签名和返回字段，能一次性消掉参数名/属性名猜错的连环报错。

**Helper import：**
```python
import sys; sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts")
from ds_skill.<module> import <function>
```

---

## 1. Group Comparison

**目的：** Y 在组间是否有差异？

**方法：**
- 2 组数值 → Welch t-test（或 Mann-Whitney U 如果小样本/偏态）
- 2 组配对 → paired t-test
- 3+ 组数值 → Welch ANOVA（或 Kruskal-Wallis 如果非正态）
- 分类 Y → chi-square（期望频数<5 时用 Fisher exact）

**Helper:**
- 数值 Y → `ds_skill.analysis_methods.compare_numeric_by_group(df, target=..., group=...)`（target/group 为 keyword-only；内部自动选 Welch t / Mann-Whitney / ANOVA / Kruskal）
- 分类 Y → `ds_skill.analysis_methods.compare_categorical(df, target=..., group=...)`（卡方独立性检验；期望频数<5 时 2×2 自动转 Fisher exact、更大表给稀疏告警；效应量 Cramér's V）

**Chart:** `ds_skill.plotting.plot_grouped_boxplot`（数值）

**混杂提醒：** 下结论前先排查是否有第三变量同时驱动 Y 和组别（如季节同时影响气温与病例数）。怀疑混杂 → 分层复算或写进局限性，别下因果。见 [anti-patterns.md](anti-patterns.md) 的 Causal Inference Errors。

---

## 2. Driver Ranking

**目的：** 哪些 X 影响 Y？

**方法：**
- 数值 Y + 数值 X → Spearman 相关
- 混合类型 X → gradient boosting + permutation importance
- 二分类 Y → logistic regression 系数

**Helper:** `ds_skill.correlation.correlation_with_target(df, target, methods=("spearman",), fdr_alpha=0.05)`  
**Chart:** `ds_skill.plotting.plot_feature_importance`

---

## 3. Correlation

**目的：** 量化两变量关系。

**方法：**
- 单调关系 → Spearman（默认，稳健）
- 线性关系 → Pearson
- 分类-分类 → Cramér's V

**Helper:** `ds_skill.correlation.pairwise_correlation(df, methods=("spearman",))` → `CorrelationMatrix`（`.pairs` 为 `CorrelationResult` 列表，字段 `.x .y .coefficient .p_value`）  
**Chart:** `ds_skill.plotting.plot_scatter_fit` 或 `plot_correlation_matrix`

---

## 4. Time Series

**目的：** 趋势/季节性/变点/异常。

**方法：**
- 趋势 → Mann-Kendall
- 季节分解 → STL
- 变点 → CUSUM
- 异常 → MAD 或 IsolationForest

**Helper:**  
- `ds_skill.time_series.mann_kendall_trend(series)`
- `ds_skill.time_series.seasonal_decompose(series, period)`
- `ds_skill.anomaly.detect_univariate(series, method='mad', threshold=3.0)`

**Chart:** `ds_skill.plotting.plot_time_series`

---

## 5. Regression（连续 Y）

**方法：**
- 线性 → OLS
- 多重共线性 → Ridge
- 特征选择 → Lasso

**Helper:** `ds_skill.regression.fit_linear_regression(df, target, features)` → `RegressionResult`（dataclass，用 `.r_squared` `.coefficients`，不是 `["r_squared"]`）  
**Chart:** `ds_skill.plotting.plot_regression_diagnostics`

---

## 6. Classification（分类 Y）

**方法：**
- 小样本 → Logistic Regression + CV
- 类别不平衡 → class_weight='balanced'

**Helper:** `ds_skill.classification.fit_classifier(df, target, features)`

---

## 7. Anomaly Detection

**方法：**
- 单变量 → IQR (k=1.5) 或 MAD (threshold=3.0)
- 多变量 → IsolationForest

**Helper:** `ds_skill.anomaly.detect_univariate(series, method='mad')`

---

## 8. Survival Analysis

**方法：**
- 生存曲线 → Kaplan-Meier
- 组比较 → Log-Rank test
- 参数拟合 → Weibull

**Helper:** `ds_skill.survival.kaplan_meier(durations, events)`  
**Chart:** `ds_skill.plotting.plot_kaplan_meier`

---

## 9. SPC（过程控制）

**方法：**
- 个体值 → I-MR chart
- 子组 → X-bar / R chart
- 缺陷率 → p-chart / c-chart
- 能力 → Cp / Cpk

**Run rules:** Nelson-1..8, WE-1..4（编号对齐 `ds_skill.spc` 实现）

**Helper:** `ds_skill.spc.individuals_mr_chart(data)` / `xbar_r_chart` / `p_chart` / `c_chart` / `u_chart`；规则用 `apply_western_electric_rules` / `apply_nelson_rules`；能力用 `capability_summary(values, lsl, usl)`  
**Chart:** `ds_skill.plotting.plot_control_chart`

---

## 10. A/B Test

**方法：**
- SRM 检查 → chi-square on arm sizes
- 效果估计 → t-test + CI
- 多指标 → Bonferroni 校正

**Helper:** `ds_skill.ab_validator.validate_ab_test(df, arm_col, metric_col)`

---

## 11. Bootstrap（非参数 CI）

**用于：** 任意统计量的 CI，小样本。

**Helper:** `ds_skill.bootstrap.bootstrap_ci(data, statistic_fn, n_bootstrap=1000)`
