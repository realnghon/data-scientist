---
trigger: glob
globs: "**/*.csv,**/*.xlsx,**/*.parquet,**/*.ipynb"
description: Data Scientist — 结构化数据分析、制造分析、有证据支撑的报告
---

# Data Scientist 规则（Windsurf）

当工作区涉及结构化数据文件时自动激活。指向共享插件核心的轻量指针，不重复工作流内容。

## 何时激活

表格/结构化数据（`.csv`、`.tsv`、`.xlsx`、`.parquet`、`.feather`、`.sqlite`、`.duckdb`）、分析型笔记本/脚本（`.ipynb`、分析类 `.py`/`.sql`）、任何统计/比较/因果问题（"X 是否驱动 Y？"、"变化是否显著？"），或制造/工艺分析（良率、SPC、OEE、缺陷归因）。

## 需要做什么

1. 阅读 `plugins/data-scientist/skills/analysis-workflow/SKILL.md` 并遵循之 — 这是三阶段流程（数据接入+准备度 → 执行 → 报告）、图表规则、证据层级以及按需加载参考文档映射的唯一来源。请勿在此重复其中规则。
2. 分析提示词位于 `plugins/data-scientist/agents/ds-analyst.md` — 单一 agent，在单线程中完成全流程。无需多 agent 编排。
3. 斜杠命令入口：`plugins/data-scientist/commands/` — `ds-profile`、`ds-plan`、`ds-analyze`、`ds-report`。

证据层级、报告格式和反模式在 `references/report-standard.md` 和 `references/anti-patterns.md` 中定义；请直接遵循原文，而非复制。