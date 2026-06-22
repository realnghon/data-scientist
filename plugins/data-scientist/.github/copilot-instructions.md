# GitHub Copilot — Project Instructions: Data Scientist Workflow

This repository ships the data-scientist plugin. When the user asks Copilot Chat or Workspace about a dataset, a statistical question, manufacturing analytics, or anything touching `.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`, `.ipynb`, or analysis-flavored `.py` / `.sql`, treat it as a data-science engagement and follow the plugin's workflow rather than improvising. This file is a thin pointer; it does not restate the workflow.

## Shared core — read before answering

- Workflow definition (gates, 7-stage pipeline, modes, evidence tiers, lazy-load map): `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Staged role prompts: `plugins/data-scientist/agents/` (intake, readiness, shaping, method-planner, execution, critic, report)
- Slash-command entrypoints: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`
- Reference docs: `plugins/data-scientist/skills/analysis-workflow/references/` — method registry, data readiness, data shaping, chart catalog, manufacturing playbook, report standard, anti-patterns, multi-agent orchestration

Copilot cannot dispatch parallel subagents — walk the 7 stages conceptually in a single thread, in order, following SKILL.md. Do not duplicate the workflow, evidence tiers, or anti-patterns here; read those files and follow them. When you use a tested helper, cite it as `ds_skill.<module>.<function>`.
