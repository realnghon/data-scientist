---
name: data-scientist
version: 3.2.0
description: "数据分析：profile 数据, 统计检验, 画图, 写报告。3 阶段流程，无需多 agent 编排。"
---

# Data Scientist

3 阶段快速分析流程。

## 流程

### 1. Intake（数据摄入）

- 读取数据：用 pandas 读 CSV/Excel/Parquet，不用 shell 命令
- 检查环境：`python --version` + 测试 import pandas/numpy/scipy。能 import 就直接用，不重装
- 探查实况：用到的每列先确认存在 + dtype；分类列再看 `df[col].unique()`。列名和取值从 df 读出，**不靠记忆或假设**
- 大表先探后读：先 `os.path.getsize(path)`，>100MB 时**不要**直接 `read_csv` 全表。改为 `pd.read_csv(path, nrows=5)` 看 schema → 用 `usecols=` 只读需要的列，或 `chunksize=` 流式聚合。`df.info(memory_usage="deep")` 只在已经读进内存后才有意义，别为了它先付一次全表读取
- 多表才需要：单表分析**跳过** join 逻辑。确有多表要 join 时，每表记录 grain + join keys，用 `ds_skill.shaping.audit_join` 预估匹配率（详见 [data-shaping.md](references/data-shaping.md)）。这是按需扩展，不是单表流程的必经步骤
- 缺失预警：任一列缺失率 >30% → 在 `data_manifest` 标记 `high_missing=true`，且后续任何用到该列的结论**自动降一档置信度**（reliable→directional）。永不 impute Y；impute X 必须记录策略。质量评分细则见 [data-readiness.md](references/data-readiness.md)
- 产出：`data_manifest`（格式见下）

**`data_manifest` 最小格式**（JSON；后续阶段只能引用这里记录过的列名和取值）：

```json
{
  "source": "path/to/data.csv",
  "n_rows": 10000,
  "columns": [
    {"name": "age", "dtype": "int64", "missing_rate": 0.0, "role": "feature"},
    {"name": "smoker", "dtype": "object", "missing_rate": 0.0, "role": "group",
     "categories": ["smoker", "non_smoker"]},
    {"name": "alcohol", "dtype": "float64", "missing_rate": 0.393,
     "role": "feature", "high_missing": true}
  ],
  "target": "heart_attack",
  "quality_score": "partial"
}
```

字段规则：分类列必须列 `categories`；`missing_rate` 是 0–1 小数；缺失率 >0.30 的列必带 `high_missing: true`；`quality_score` ∈ `ok|partial|blocked`，取最差维度。

### 2. Execution（分析执行）

- 选方法：根据问题类型查 [method-registry.md](references/method-registry.md)
- 数据整形：按需 pivot/melt/aggregate，不单独成阶段
- **跑统计检验**（不要只停在描述统计）：任何"组间有无差异"的结论都要落到一个正式检验，不能只凭均值大小说"差异明显"。
  - 数值 Y by 组 → `ds_skill.analysis_methods.compare_numeric_by_group`（内部自动选 Welch t / Mann-Whitney / ANOVA / Kruskal）
  - 分类 Y × 分类组 → `ds_skill.analysis_methods.compare_categorical`（卡方，期望频数<5 自动转 Fisher，效应量 Cramér's V）
  - 量化两连续变量关系 → `ds_skill.correlation.pairwise_correlation`
- **建模（按需，仍在本阶段内，不新增阶段）**：问题是"预测/量化风险因素贡献"而非"组间比较"时，引导到建模 helper —— 连续 Y 用 `ds_skill.regression`，二分类 Y（如心脏病发作 yes/no）用 `ds_skill.classification`，生存/事件时间用 `ds_skill.survival`。详见 [method-registry.md](references/method-registry.md) 第 5/6/8 章
- **混杂检查**：报告相关性/差异前，先问"有没有第三个变量同时驱动两边"（如气温与病例数都随季节变化）。怀疑混杂时分层复算或在局限性里写明，别下因果结论。清单见 [anti-patterns.md](references/anti-patterns.md)
- 画图：用下面的画图规则
- 产出：`evidence_matrix`（格式见下）+ chart 文件

**`evidence_matrix` 最小格式**（每个发现一行）：

```json
[
  {
    "claim": "吸烟者高血压比例显著高于非吸烟者",
    "method": "chi_square_test",
    "statistic": 64.2,
    "p_value": 0.0001,
    "effect": {"name": "cramers_v", "value": 0.40},
    "n": 400,
    "tier": "reliable",
    "chart": "charts/smoker_hypertension.png",
    "caveats": []
  }
]
```

字段规则：`method` 用 registry 里的名字；效应量必填（只有 p 值不算证据）；`tier` ∈ `reliable|directional|unsupported`，用到 `high_missing` 列或单一方法时不得为 `reliable`；无值的字段写 `null`，不要省略键。

**执行机制：** 多行 Python 写进 `.py` 文件再 `python file.py`，不塞进 bash heredoc 或 `python -c`——delimiter 冲突、引号转义、f-string 变量拼错都是这类内联写法的无谓错误源。每个脚本顶部加 `import sys; sys.stdout.reconfigure(encoding="utf-8")`，否则 Windows 终端默认 GBK 编码，遇到 `²`、emoji、特殊符号会 `UnicodeEncodeError`。传列前先校验列存在，让缺列在画图/pivot 前就报错而非中途崩：

```python
# 列存在检查(直接内联,无需 helper)
if "smoker" not in df.columns:
    raise ValueError(f"Column 'smoker' not found. Available: {list(df.columns)}")

# 数值列检查
if not pd.api.types.is_numeric_dtype(df["age"]):
    raise ValueError(f"Column 'age' must be numeric, got {df['age'].dtype}")
```

### 3. Report（报告生成）

- 结构：执行摘要 → 数据说明 → 关键发现（带图）→ 方法说明 → 局限性
- 产出：`final_report.md`

## 画图规则（确定性）

1. 数值 by 组 → `boxplot`
2. 时间序列 → `line plot`
3. 相关性 → 默认 `hexbin`（n≥1000），可按需降级到 `scatter`（画子集、或想看单点/离群点时）
4. 分布 → `histogram`
5. 排序/重要性 → `horizontal bar` (降序)

阈值是默认值不是死墙：hexbin 是大 N 默认，scatter 仍可用于小样本或刻意取的子集——选择写进图注即可。不用火山图、3D 图、复杂 heatmap，除非用户明确要求。

## References（按需加载）

多数分析不需要加载 reference。只在遇到以下情况时查阅（括号内是该文件**确实覆盖**的内容，省去先打开才知道相关与否的成本）：

- **选方法 / 检验 / 建模** → [method-registry.md](references/method-registry.md)（11 类方法的 helper 入口、假设、混杂提示）
- **图表选择** → [chart-catalog.md](references/chart-catalog.md)（默认 5 规则 + 特殊场景图、注释要求）
- **制造业数据** → [manufacturing-playbook.md](references/manufacturing-playbook.md)（SPC、Cp/Cpk、良率根因、MSA）
- **数据质量差 / 高缺失 / 小样本** → [data-readiness.md](references/data-readiness.md)（8 维评分 + ok/partial/blocked 决策）
- **多表 reshape / join** → [data-shaping.md](references/data-shaping.md)（grain、pivot/melt、join 匹配率、泄漏）
- **下结论前自查** → [anti-patterns.md](references/anti-patterns.md)（混杂、p 值当影响、泄漏等红线）
- **写报告** → [report-standard.md](references/report-standard.md)（证据分层、章节契约）

## Helper 使用

统计函数在 `scripts/ds_skill/` 下，按需 import：

```python
import sys, os
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts")
from ds_skill.correlation import pairwise_correlation
from ds_skill.spc import individuals_mr_chart
from ds_skill.plotting import plot_control_chart
```

返回值多为 dict，用 `["key"]` 取值不是 `.attr`；首次调用某 helper 前 `grep -n "def <name>" -A6 scripts/ds_skill/<module>.py` 确认签名。完整模块清单见 method-registry.md 各章节的"Helper"行。
