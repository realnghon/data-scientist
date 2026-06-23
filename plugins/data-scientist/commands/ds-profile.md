---
description: 对数据集进行画像——检查结构、列、数据类型、样本行以及数据质量风险，不做出业务结论
argument-hint: <dataset-path>
---

# 数据集画像

使用 `data-scientist` 数据摄入流程检查数据集，不做出业务结论。

**示例：**
- `/ds-profile data.csv`
- `/ds-profile sales.xlsx`
- `/ds-profile measurements.parquet`

## 执行要求

1. 识别文件类型、文件大小、工作表/表、列、行数以及样本记录。
2. 对于支持的本地文件，使用 `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts/profile_dataset.py`。
3. 推断候选字段角色：目标变量、时间、实体 ID、分组、过程参数和结果标签。
4. 标记可能阻碍后续分析的数据质量风险。

## 预期输出

- `data_manifest`
- `data_profile`
- `field_role_candidates`
- `data_risks`
- 读取数据源所需的任何问题

在本命令中不要运行统计检验或做出结论。