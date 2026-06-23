# Data Scientist — Gemini CLI Memory

Gemini CLI auto-loads this file as project memory at session start. It is a thin pointer to the shared plugin core — it does not restate the workflow.

## Activation conditions

Engage data-scientist mode whenever the task touches tabular/structured data (`.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`), analysis notebooks/scripts (`.ipynb`, analysis-flavored `.py`/`.sql`), a statistical/comparative/causal question ("does X drive Y?", "is the change significant?"), or manufacturing/process analytics (yield, SPC, OEE, defect attribution). Outside those conditions, behave normally.

## Shared core — read before answering

- Workflow definition (3-stage flow, chart rules, lazy-load map): `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Analysis prompt: `plugins/data-scientist/agents/ds-analyst.md` (single agent, completes intake+readiness → execution → report)
- Slash-command entrypoints: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`
- Reference docs: `plugins/data-scientist/skills/analysis-workflow/references/` — method registry, data readiness, data shaping, chart catalog, manufacturing playbook, report standard, anti-patterns

Do not duplicate workflow content or anti-patterns here. Read those files and follow them.

## Execution

Run the 3-stage flow in a single thread following `ds-analyst.md`. When you invoke a tested helper, cite it as `ds_skill.<module>.<function>`.
