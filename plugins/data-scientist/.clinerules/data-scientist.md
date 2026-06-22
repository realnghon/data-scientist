# Data Scientist Rule (Cline)

Cline loads every `.md` in `.clinerules/` as a persistent rule; this file is a thin pointer to the plugin's shared core — it does not restate it.

## When to activate

Tabular/structured data (`.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`), analysis notebooks/scripts (`.ipynb`, analysis-flavored `.py`/`.sql`), any statistical/comparative/causal question ("does X drive Y?", "is the change significant?"), or manufacturing/process analytics (yield, SPC, OEE, defect attribution).

## What to do

1. Read `plugins/data-scientist/skills/analysis-workflow/SKILL.md` and follow it. It is the single source for the gates, the 7-stage pipeline, modes, and the lazy-load map of references. Do not duplicate its rules here.
2. Stage role prompts live under `plugins/data-scientist/agents/`. Cline cannot dispatch subagents in parallel — run the stages sequentially in one session, threading the JSON state envelope from `references/multi-agent-orchestration.md`.
3. Slash-command entry points: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`.

Evidence tiers, report format, and anti-patterns are defined in `references/report-standard.md` and `references/anti-patterns.md`; follow them there rather than from a copy.
