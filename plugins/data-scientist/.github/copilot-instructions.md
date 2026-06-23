# GitHub Copilot — 项目指令：Data Scientist 工作流

本仓库发布 data-scientist 插件。当用户在 Copilot Chat 或 Workspace 中询问数据集、统计问题、制造分析，或涉及 `.csv`、`.tsv`、`.xlsx`、`.parquet`、`.feather`、`.sqlite`、`.duckdb`、`.ipynb` 或分析类 `.py`/`.sql` 文件时，应将其视为数据科学任务并遵循插件工作流，而非随意发挥。本文件是轻量指针，不重复工作流内容。

## 共享核心 — 回答前请阅读

- 工作流定义（三阶段流程、图表规则、按需加载映射）：`plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- 分析提示词：`plugins/data-scientist/agents/ds-analyst.md`（单一 agent，完成 数据接入+准备度 → 执行 → 报告 全流程）
- 斜杠命令入口：`plugins/data-scientist/commands/` — `ds-profile`、`ds-plan`、`ds-analyze`、`ds-report`
- 参考文档：`plugins/data-scientist/skills/analysis-workflow/references/` — 方法注册表、数据准备度、数据整形、图表目录、制造分析手册、报告标准、反模式

在单线程中按照 SKILL.md 和 ds-analyst.md 执行三阶段流程。请勿在此重复工作流或反模式内容；请阅读上述文件并遵循之。调用已测试的辅助函数时，引用格式为 `ds_skill.<模块>.<函数>`。