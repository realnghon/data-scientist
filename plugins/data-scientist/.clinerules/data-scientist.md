# Data Scientist Rule (Cline)

Use this rule when working in a project that needs disciplined data-science behavior on messy structured data. Cline loads every `.md` file in `.clinerules/` as a persistent rule; this file is the entrypoint that points Cline at the plugin's shared core.

## 1. When to activate

Activate whenever the working context involves:

- Tabular or structured data files: `.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`
- Notebook or analysis scripts: `.ipynb`, analysis-flavored `.py` or `.sql`
- A user question that is statistical, comparative, or causal ("does X drive Y?", "is the change significant?", "what's the relationship between...")
- Manufacturing / process analytics (yield, scrap, throughput, SPC, OEE, defect attribution)

## 2. Workflow pointer — do not duplicate, follow the shared core

The full workflow is defined once at `plugins/data-scientist/skills/analysis-workflow/SKILL.md`. Read it before answering. It expands to a 7-stage pipeline whose role prompts live under `plugins/data-scientist/agents/`:

1. `ds-intake-agent.md` — scope and goal capture
2. `ds-readiness-agent.md` — can the data answer the question?
3. `ds-shaping-agent.md` — transform to analysis-ready form
4. `ds-method-planner-agent.md` — pick methods with justification
5. `ds-execution-agent.md` — run them with diagnostics
6. `ds-critic-agent.md` — adversarial review of the result
7. `ds-report-agent.md` — write the deliverable

Cline cannot dispatch subagents in parallel. Run the seven stages sequentially in one session, but keep the per-stage JSON state envelope from `plugins/data-scientist/skills/analysis-workflow/references/multi-agent-orchestration.md` so the artifacts stay inspectable.

Slash-command equivalents (for users who prefer them): see `plugins/data-scientist/commands/` — `ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`.

## 3. Output discipline — three-tier evidence framework

Every finding goes into one of three buckets, per `plugins/data-scientist/skills/analysis-workflow/references/report-standard.md`:

- **Reliable** — assumptions met, effect size reported, replication / robustness check passed.
- **Directional** — signal is present but at least one assumption is weak, sample is small, or confounds are uncontrolled. State the caveat next to the claim.
- **Unsupported** — the data cannot answer this question. Say so and request what would be needed; do not fill the gap with prose.

Always report effect sizes alongside p-values, and call out the practical (business) magnitude separately from the statistical one.

## 4. Anti-patterns — refuse these

- Treating statistical significance as business importance.
- Generating a confident-sounding report when readiness failed. If shaping or readiness blocks the question, stop and surface the blocker.
- Inventing values, distributions, or sample sizes that were not present in the data.
- Skipping the critic stage on any analysis with a decision attached to it.
