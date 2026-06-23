# Data Scientist — Gemini CLI 记忆

Gemini CLI 在会话启动时自动加载此文件作为项目记忆。本文件是指向共享插件核心的轻量指针，不重复工作流内容。

## 激活条件

当任务涉及以下内容时，启用 data-scientist 模式：表格/结构化数据（`.csv`、`.tsv`、`.xlsx`、`.parquet`、`.feather`、`.sqlite`、`.duckdb`）、分析型笔记本/脚本（`.ipynb`、分析类 `.py`/`.sql`）、统计/比较/因果问题（"X 是否驱动 Y？"、"变化是否显著？"），或制造/工艺分析（良率、SPC、OEE、缺陷归因）。在这些条件之外，正常行为。

## 共享核心 — 回答前请阅读

- 工作流定义（三阶段流程、图表规则、按需加载映射）：`plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- 分析指令：`plugins/data-scientist/agents/ds-analyst.md`（单一 agent，完成 数据摄入+就绪评估 → 分析执行 → 报告生成 全流程）
- 斜杠命令入口：`plugins/data-scientist/commands/` — `ds-profile`、`ds-plan`、`ds-analyze`、`ds-report`
- 参考文档：`plugins/data-scientist/skills/analysis-workflow/references/` — 方法注册表、数据准备度、数据整形、图表目录、制造分析手册、报告标准、反模式

请勿在此重复工作流内容或反模式。请阅读上述文件并遵循之。

## 执行

在单线程中按照 `ds-analyst.md` 运行三阶段流程。调用已测试的辅助函数时，引用格式为 `ds_skill.<模块>.<函数>`。