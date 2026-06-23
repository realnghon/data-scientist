---
name: data-scientist
version: 3.1.0
description: "数据分析：profile 数据, 统计检验, 画图, 写报告。3 阶段流程，无需多 agent 编排。"
---

# Data Scientist

3 阶段快速分析流程。

## 流程

### 1. Intake（数据摄入）
- 读取数据：用 pandas 读 CSV/Excel/Parquet，不用 shell 命令
- 检查环境：`python --version` + 测试 import pandas/numpy/scipy。能 import 就直接用，不重装
- 探查实况：用到的每列先确认存在 + dtype；分类列再看 `df[col].unique()`。列名和取值从 df 读出，**不靠记忆或假设**
- 多表时：每表记录 grain + join keys，用 `ds_skill.shaping.audit_join` 预估匹配率（详见 [data-shaping.md](references/data-shaping.md)）
- 规模未知时：先 `df.info(memory_usage="deep")`；表大到聚合更划算就先聚合再分析
- 产出：`data_manifest` —— 必须列出实际用到的每列名称、dtype、分类列取值、样本量、质量评分。后续阶段只能用 manifest 里记录过的列名和取值

### 2. Execution（分析执行）
- 选方法：根据问题类型查 [method-registry.md](references/method-registry.md)
- 数据整形：按需 pivot/melt/aggregate，不单独成阶段
- 跑统计：运行选定方法 + 交叉验证，检查假设
- 画图：用下面的 5 条默认规则
- 产出：`evidence_matrix` + chart 文件

**执行机制：** 多行 Python 写进 `.py` 文件再 `python file.py`，不塞进 bash heredoc 或 `python -c`——delimiter 冲突、引号转义、f-string 变量拼错都是这类内联写法的无谓错误源。每个脚本顶部加 `import sys; sys.stdout.reconfigure(encoding="utf-8")`，否则 Windows 终端默认 GBK 编码，遇到 `²`、emoji、特殊符号会 `UnicodeEncodeError`。传列前先过 helper 的列校验（`validate_column_name` / `validate_numeric_column`），让缺列在画图/pivot 前就报错而非中途崩。

### 3. Report（报告生成）
- 结构：执行摘要 → 数据说明 → 关键发现（带图）→ 方法说明 → 局限性
- 产出：`final_report.md`

## 画图规则（确定性）

1. 数值 by 组 → `boxplot`
2. 时间序列 → `line plot`
3. 相关性 → `scatter` (n<1000) 或 `hexbin` (n≥1000)
4. 分布 → `histogram`
5. 排序/重要性 → `horizontal bar` (降序)

不用火山图、3D 图、复杂 heatmap，除非用户明确要求。

## References（按需加载）

多数分析不需要加载 reference。只在遇到以下情况时查阅：

- **选方法困难** → [method-registry.md](references/method-registry.md)
- **复杂图表** → [chart-catalog.md](references/chart-catalog.md)
- **制造业数据** → [manufacturing-playbook.md](references/manufacturing-playbook.md)
- **数据质量差** → [data-readiness.md](references/data-readiness.md)
- **复杂 reshape** → [data-shaping.md](references/data-shaping.md)

其他 reference 文件已删除或合并。

## Helper 使用

统计函数在 `scripts/ds_skill/` 下，按需 import：

```python
import sys, os
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts")
from ds_skill.correlation import pairwise_correlation
from ds_skill.spc import individuals_mr_chart
from ds_skill.plotting import plot_grouped_boxplot
```

Helper 模块清单见 method-registry.md 各章节的"Reusable helper"行。
