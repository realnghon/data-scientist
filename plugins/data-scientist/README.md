# Data Scientist

Data Scientist is a cross-tool AI plugin for messy structured data analysis. It starts with manufacturing data but is designed to generalize to other operational datasets.

## What It Provides

- A top-level `data-scientist` skill for full-cycle analysis (intake → readiness → shaping → method planning → execution → critic → report).
- Seven staged subagents and four `/ds-*` slash commands.
- A tested Python helper library (`ds_skill`) with 11 analysis method groups and 21 ready-made chart functions — so the model calls helpers instead of re-writing statistics and plots.
- Method-registry, chart-catalog, data-readiness, and manufacturing-playbook reference docs.
- Cross-tool entrypoints for Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, and Gemini CLI.

## Install

Claude Code marketplace install:

```text
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

For per-runtime manual paths (Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, Gemini CLI) and local development, see [`../../INSTALL.md`](../../INSTALL.md). To use the skill as plain reference material without installing, `cat skills/analysis-workflow/SKILL.md` into your agent's context.

## Core Flow

1. Inspect data structure and field roles.
2. Assess readiness and data quality.
3. Reshape into analysis views when needed.
4. Plan methods by analysis purpose.
5. Execute code and save evidence.
6. Critique findings before reporting.
7. Produce a report with limitations and next actions.

See [`../../CHANGELOG.md`](../../CHANGELOG.md) for release history.
