---
name: data-scientist
version: 4.0.0
description: "数据分析全流程：数据画像、统计检验、可视化、报告生成。三阶段流程（数据摄入→分析执行→报告生成），单 agent 完成，无需多 agent 编排。当用户提到 CSV/Excel/Parquet 数据分析、假设检验、统计报告、制造业分析（良率/SPC/Cpk）、A/B 测试、或数据质量问题诊断时使用。"
---

# 数据科学家

3 阶段快速分析流程。

## 流程

### 1. 数据摄入

- 读取数据：用 pandas 读 CSV/Excel/Parquet，不用 shell
- 环境：`python --version` + 测试 import pandas/numpy/scipy，能用就不重装
- 探查：每列先确认存在 + dtype；分类列再看 `df[col].unique()`。**从 df 读，不靠记忆**
- 大表：`os.path.getsize` >100MB 时先 `nrows=5` 看 schema，再用 `usecols=` 只读所需列
- 多表 join：单表跳过。需要时记录 grain + join keys，用 `ds_skill.shaping.audit_join` 预估匹配率，详见 [data-shaping.md](references/data-shaping.md)
- 缺失预警：缺失率 >30% → `data_manifest` 标记 `high_missing=true`，相关结论**自动降一档置信度**。永不 impute Y；impute X 须记录策略。详见 [data-readiness.md](references/data-readiness.md)
- 产出：`data_manifest`

**`data_manifest` 最小格式**（后续阶段只能引用这里记录过的列）：
```json
{"source": "path/to/data.csv", "n_rows": 10000, "target": "heart_attack",
 "quality_score": "partial", "columns": [
   {"name": "age", "dtype": "int64", "missing_rate": 0.0, "role": "feature"},
   {"name": "smoker", "dtype": "object", "missing_rate": 0.0, "role": "group", "categories": ["smoker","non_smoker"]},
   {"name": "alcohol", "dtype": "float64", "missing_rate": 0.393, "role": "feature", "high_missing": true}]}
```
字段规则：分类列必列 `categories`；`missing_rate` 0–1；缺失 >0.30 必带 `high_missing`；`quality_score` ∈ `ok|partial|blocked`。

### 2. 分析执行

- 选方法：查 [method-registry.md](references/method-registry.md)
- 数据整形：按需 pivot/melt/aggregate，不单独成阶段
- **跑统计检验**：任何"组间有无差异"的结论都要落到正式检验，不能只凭均值大小。
  - 数值 Y by 组 → `ds_skill.analysis_methods.compare_numeric_by_group`（自动选 Welch t / Mann-Whitney / ANOVA / Kruskal）
  - 分类 Y × 分类组 → `ds_skill.analysis_methods.compare_categorical`（卡方，期望<5 自动转 Fisher，效应量 Cramér's V）
  - 连续关系 → `ds_skill.correlation.pairwise_correlation`
- **建模（按需）**：连续 Y → `ds_skill.regression`，二分类 → `ds_skill.classification`，生存 → `ds_skill.survival`。详见 [method-registry.md](references/method-registry.md) 第 5/6/8 章
- **混杂检查**：报告前先问"有没有第三变量同时驱动两边"（如气温与病例数都随季节变化）。见 [anti-patterns.md](references/anti-patterns.md)
- 画图：用下面的画图规则
- 产出：`evidence_matrix` + 图表

**`evidence_matrix` 最小格式**（每个发现一行）：
```json
[{"claim": "吸烟者高血压比例显著高于非吸烟者", "method": "chi_square_test",
  "statistic": 64.2, "p_value": 0.0001, "effect": {"name": "cramers_v", "value": 0.40},
  "n": 400, "tier": "reliable", "chart": "charts/smoker_hypertension.png", "caveats": []}]
```
字段规则：`method` 用 registry 名字；效应量必填；`tier` ∈ `reliable|directional|unsupported`，用到 `high_missing` 列或单一方法时不得为 `reliable`。

**执行机制：** 多行 Python 写 `.py` 文件再 `python file.py`，不塞入 bash heredoc。每个脚本加 `sys.stdout.reconfigure(encoding="utf-8")` 防 Windows GBK 报错。传列前先校验列存在和类型，让错误在画图前报出：
```python
if "smoker" not in df.columns:
    raise ValueError(f"Column 'smoker' not found. Available: {list(df.columns)}")
if not pd.api.types.is_numeric_dtype(df["age"]):
    raise ValueError(f"Column 'age' must be numeric, got {df['age'].dtype}")
```

### 3. 报告生成

- 结构：执行摘要 → 数据说明 → 关键发现（带图）→ 方法说明 → 局限性
- 产出：`final_report.md`

## 画图规则（确定性）

1. 数值 by 组 → `boxplot`
2. 时间序列 → `line plot`
3. 相关性 → 默认 `hexbin`（n≥1000），可降级到 `scatter`
4. 分布 → `histogram`
5. 排序/重要性 → `horizontal bar`（降序）

阈值是默认值不是死墙：hexbin 是大 N 默认，scatter 仍可用于小样本或刻意取的子集——选择写进图注即可。不用火山图、3D 图、复杂 heatmap，除非用户明确要求。

## 参考资料（按需加载）

多数分析不需加载。按需查：[method-registry.md](references/method-registry.md)（选方法）· [chart-catalog.md](references/chart-catalog.md)（图表）· [manufacturing-playbook.md](references/manufacturing-playbook.md)（SPC/Cpk）· [data-readiness.md](references/data-readiness.md)（质量差/高缺失）· [data-shaping.md](references/data-shaping.md)（多表 reshape/join）· [anti-patterns.md](references/anti-patterns.md)（下结论前自查）· [report-standard.md](references/report-standard.md)（写报告）。

## 辅助函数使用

```python
import sys; sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts")
from ds_skill.correlation import pairwise_correlation
from ds_skill.spc import individuals_mr_chart
from ds_skill.plotting import plot_control_chart
```

首次调用某辅助函数前 `grep -n "def <name>" -A6 scripts/ds_skill/<module>.py` 确认签名。返回值多为 dict，用 `["key"]` 取值。完整模块见 method-registry.md。
