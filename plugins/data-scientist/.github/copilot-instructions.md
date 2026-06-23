# GitHub Copilot — Project Instructions: Data Scientist Workflow

This repository ships the data-scientist plugin. When the user asks Copilot Chat or Workspace about a dataset, a statistical question, manufacturing analytics, or anything touching `.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`, `.ipynb`, or analysis-flavored `.py` / `.sql`, treat it as a data-science engagement and follow the plugin's workflow rather than improvising. This file is a thin pointer; it does not restate the workflow.

## Shared core — read before answering

- Workflow definition (3-stage flow, chart rules, lazy-load map): `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Analysis prompt: `plugins/data-scientist/agents/ds-analyst.md` (single agent, completes intake+readiness → execution → report)
- Slash-command entrypoints: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`
- Reference docs: `plugins/data-scientist/skills/analysis-workflow/references/` — method registry, data readiness, data shaping, chart catalog, manufacturing playbook, report standard, anti-patterns

Walk the 3-stage flow in a single thread, following SKILL.md and ds-analyst.md. Do not duplicate the workflow or anti-patterns here; read those files and follow them. When you use a tested helper, cite it as `ds_skill.<module>.<function>`.
