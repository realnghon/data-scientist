---
description: Run an end-to-end data-scientist analysis on a dataset — intake, readiness, plan, execution, and evidence-backed report
argument-hint: <dataset-path> [analysis-goal]
---

# Analyze Dataset

Use the `data-scientist` skill to run a full analysis workflow on the user's dataset.

**Examples:**
- `/ds-analyze data.csv`
- `/ds-analyze sales.xlsx "what drives revenue?"`
- `/ds-analyze dataset.parquet "is yield different between groups?"`

## Required Behavior

1. Identify the dataset source and user goal.
2. Load `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/SKILL.md` and follow its workflow.
3. Start with intake and readiness; do not jump directly to modeling or hypothesis tests.
4. Ask no more than 5 human questions. Ask only when the answer materially changes the analysis.
5. Produce an analysis plan before executing non-trivial analysis code.
6. Separate reliable conclusions from directional signals and unsupported findings.

## Expected Outputs

- Data/profile summary.
- Readiness assessment.
- Analysis plan with rejected methods.
- Executed results and charts when data permits.
- Final report with limitations and next actions.

## Failure Mode

If the data cannot support the requested analysis, stop and produce a concrete data request instead of fabricating a report.
