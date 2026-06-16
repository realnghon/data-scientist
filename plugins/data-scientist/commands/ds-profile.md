---
description: Profile a dataset — inspect structure, columns, dtypes, sample rows, and data-quality risks without drawing business conclusions
argument-hint: <dataset-path>
---

# Profile Dataset

Use the `data-scientist` intake workflow to inspect a dataset without making business conclusions.

**Examples:**
- `/ds-profile data.csv`
- `/ds-profile sales.xlsx`
- `/ds-profile measurements.parquet`

## Required Behavior

1. Identify file type, file size, sheets/tables, columns, row counts, and sample records.
2. Use `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/scripts/profile_dataset.py` for supported local files.
3. Infer candidate field roles: target, time, entity id, group, process parameter, and outcome label.
4. Flag data-quality risks that could block later analysis.

## Expected Outputs

- `data_manifest`
- `data_profile`
- `field_role_candidates`
- `data_risks`
- any questions required to read the source

Do not run statistical tests or produce conclusions in this command.
