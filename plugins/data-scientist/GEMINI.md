# Data Scientist — Gemini CLI Memory

Gemini CLI auto-loads this file as project memory at session start. It is a thin pointer to the shared plugin core — it does not restate the workflow.

## Activation conditions

Engage data-scientist mode whenever the task touches tabular/structured data (`.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`), analysis notebooks/scripts (`.ipynb`, analysis-flavored `.py`/`.sql`), a statistical/comparative/causal question ("does X drive Y?", "is the change significant?"), or manufacturing/process analytics (yield, SPC, OEE, defect attribution). Outside those conditions, behave normally.

## Shared core — read before answering

- Workflow definition (gates, 7-stage pipeline, modes, evidence tiers, lazy-load map): `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Staged role prompts: `plugins/data-scientist/agents/` (intake, readiness, shaping, method-planner, execution, critic, report)
- Slash-command entrypoints: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`
- Reference docs: `plugins/data-scientist/skills/analysis-workflow/references/` — method registry, data readiness, data shaping, chart catalog, manufacturing playbook, report standard, anti-patterns, multi-agent orchestration

Do not duplicate workflow content, evidence tiers, or anti-patterns here. Read those files and follow them.

## Sequential execution — no native parallel dispatch

Gemini CLI does not dispatch subagents in parallel. Run the 7 stages sequentially in a single thread, emitting the per-stage JSON state envelope from `references/multi-agent-orchestration.md` so each artifact stays inspectable and a rerun can resume from any stage. Skip stages only under the single-pass shortcut rules in that same reference. When you invoke a tested helper, cite it as `ds_skill.<module>.<function>`.
