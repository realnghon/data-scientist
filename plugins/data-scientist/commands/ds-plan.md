---
description: Turn a profiled dataset and user goal into a defensible analysis plan with selected methods, assumption checks, and rejected alternatives
argument-hint: <analysis-goal> [target-metric]
---

# Plan Analysis

Use the `data-scientist` method-planning workflow to turn a profiled dataset and user goal into a defensible analysis plan.

**Examples:**
- `/ds-plan "compare treatment vs control"`
- `/ds-plan "rank drivers of conversion"`
- `/ds-plan "detect yield drop" yield_pct`

## Required Behavior

1. Confirm the target metric `Y`, analysis grain, and allowed analysis scope.
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/references/method-registry.md`, `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/references/data-readiness.md`, and relevant domain playbooks.
3. Choose methods by purpose, data type, assumptions, and business usefulness.
4. Record rejected methods and why they are weaker or invalid.
5. Include cross-checks for important claims.

## Expected Outputs

- analysis purpose
- selected method set
- assumption checks
- rejected methods
- execution order
- required charts
- human decisions still needed

Do not execute the plan unless the user explicitly asks.
