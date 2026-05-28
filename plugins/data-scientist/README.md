# Data Scientist

Data Scientist is a cross-tool AI plugin for messy structured data analysis. It starts with manufacturing data but is designed to generalize to other operational datasets.

## What It Provides

- A top-level `data-scientist` skill for full-cycle analysis.
- Reusable Python helpers for profiling data and selecting statistical methods.
- Method registry documentation with selection criteria and rejected-method reasoning.
- Multi-agent orchestration prompts for staged analysis.
- Cross-tool plugin manifests for Claude Code, Codex, Cursor, and OpenCode.

## Current Maturity

This is an early V1. It is suitable for local testing and iteration, not yet a polished public release.

## Core Flow

1. Inspect data structure and field roles.
2. Assess readiness and data quality.
3. Reshape into analysis views when needed.
4. Plan methods by analysis purpose.
5. Execute code and save evidence.
6. Critique findings before reporting.
7. Produce a report with limitations and next actions.

## Install Notes

Platform-specific installers are still pending. For development, point your tool at this plugin directory or install the `skills/data-scientist` folder directly where your agent discovers skills.
