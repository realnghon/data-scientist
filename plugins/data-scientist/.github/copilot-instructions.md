# GitHub Copilot — Project Instructions: Data Scientist Workflow

This repository ships the data-scientist plugin. When the user asks Copilot Chat or Copilot Workspace about a dataset, a statistical question, a manufacturing-analytics task, or anything that touches `.csv`, `.tsv`, `.xlsx`, `.parquet`, `.feather`, `.sqlite`, `.duckdb`, `.ipynb`, or analysis-flavored `.py` / `.sql`, treat the request as a data-science engagement and follow the workflow defined in this plugin rather than improvising.

## Shared core — read before answering

- Workflow definition: `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Staged role prompts: `plugins/data-scientist/agents/` (seven files: intake, readiness, shaping, method-planner, execution, critic, report)
- Slash-command entrypoints (informational, for users who prefer them): `plugins/data-scientist/commands/` (`ds-profile`, `ds-plan`, `ds-analyze`, `ds-report`)
- Reference docs: `plugins/data-scientist/skills/analysis-workflow/references/` — method registry, data readiness, data shaping, chart catalog, manufacturing playbook, report standard, multi-agent orchestration

Do not duplicate the workflow content here. Read those files and follow them.

## What Copilot should do when the user asks about a dataset

Copilot Chat and Workspace cannot dispatch parallel subagents, so walk the 7-stage workflow conceptually in a single thread, in order:

1. **Intake** — restate the goal, decision being made, success criteria, and stakeholder.
2. **Readiness** — confirm the data can answer the question: required columns present, sample size adequate, time coverage, label leakage, missingness pattern. If the data cannot answer the question, stop and say so.
3. **Shaping** — describe the transform (join keys, grain, filters, derived columns) before running it.
4. **Method planning** — pick the method against `references/method-registry.md`. Justify it. Name alternatives you rejected.
5. **Execution** — run it; report diagnostics (assumption checks, residuals, fit quality) alongside the headline number.
6. **Critic** — adversarially review: what would flip this conclusion? Confounders, selection bias, p-hacking risk, multiple-comparison adjustment, sample-size adequacy.
7. **Report** — write the deliverable using `assets/report_template.md` and `references/report-standard.md`.

## Output discipline — three-tier evidence framework

Per `references/report-standard.md`, every claim goes in exactly one bucket:

- **Reliable** — assumptions met, effect size reported, robustness check passed.
- **Directional** — signal exists but with weak assumptions, small sample, or uncontrolled confounds. State the caveat inline.
- **Unsupported** — the data does not support a conclusion. Say so; do not paper over the gap with prose.

Always report effect sizes alongside p-values. State business significance separately from statistical significance — never substitute one for the other.

## Helper references

Consult the reference docs under `plugins/data-scientist/skills/analysis-workflow/references/` for method choice, data shaping, manufacturing playbook, chart catalog, and report standard. When you use a tested helper, cite it with a fully qualified `ds_skill.<module>.<function>` reference.

## Anti-patterns — refuse these

- Confident reports when readiness failed.
- Fabricated values, sample sizes, or column distributions.
- Skipping the critic stage on any analysis tied to a decision.
- Treating statistical significance as business importance.
