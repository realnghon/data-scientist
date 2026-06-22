---
trigger: glob
globs: "**/*.csv,**/*.xlsx,**/*.parquet,**/*.ipynb"
description: Data Scientist — messy structured data analysis, manufacturing analytics, evidence-backed reporting
---

# Data Scientist Rule (Windsurf)

Activates automatically when the workspace touches structured-data files. Thin pointer to the shared plugin core — it does not restate the workflow.

## When to activate

Tabular/structured data (`.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`), analysis notebooks/scripts (`.ipynb`, analysis-flavored `.py`/`.sql`), any statistical/comparative/causal question ("does X drive Y?", "is the change significant?"), or manufacturing/process analytics (yield, SPC, OEE, defect attribution).

## What to do

1. Read `plugins/data-scientist/skills/analysis-workflow/SKILL.md` and follow it — the single source for the gates, the 7-stage pipeline, modes, evidence tiers, and the lazy-load map of references. Do not duplicate its rules here.
2. Stage role prompts live under `plugins/data-scientist/agents/`. Windsurf Cascade runs stages sequentially — thread the per-stage JSON state envelope from `references/multi-agent-orchestration.md` so artifacts stay inspectable.
3. Slash-command entry points: `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`.

Evidence tiers, report format, and anti-patterns are defined in `references/report-standard.md` and `references/anti-patterns.md`; follow them there rather than from a copy.
