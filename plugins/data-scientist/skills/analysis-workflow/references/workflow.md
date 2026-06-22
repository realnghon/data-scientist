---
name: workflow
description: 7-stage decision-tree workflow for data analysis (intake → readiness → shaping → method-planner → execution → critic → report). Use when need canonical pipeline structure, stage dependencies, parallelization patterns, or stage-to-stage contracts. Triggers — what's the process, how do stages connect, when can I parallelize, what are the loops.
---

# Workflow

Decision-tree workflow for messy structured data analysis. Each stage is a node: enter on **Trigger**, leave on **Outputs** or **Stop conditions**. Stages are owned by the matching `ds-*-agent` (see [multi-agent-orchestration.md](multi-agent-orchestration.md)).

Pipeline: **intake → readiness → shaping → method planning → execution → critic → report**.

Named artifacts (passed downstream as JSON or markdown blocks):
`data_manifest` · `readiness_report` · `analysis_views` · `analysis_plan` · `evidence_matrix` · `critique` · `final_report`.

---

## Table of Contents

1. [Stage 1 — Intake](#stage-1--intake) — profile data and understand user goal
2. [Stage 2 — Readiness](#stage-2--readiness) — 8-dimension quality gate
3. [Stage 3 — Shaping](#stage-3--shaping) — build analysis views
4. [Stage 4 — Method Planning](#stage-4--method-planning) — select methods by purpose
5. [Stage 5 — Execution](#stage-5--execution) — run code, collect evidence
6. [Stage 6 — Critic](#stage-6--critic) — validate findings before reporting
7. [Stage 7 — Report](#stage-7--report) — assemble final deliverable
8. [Stop Conditions Reference](#stop-conditions-reference-for-all-stages)
9. [Anti-Patterns](#anti-patterns--workflow-red-flags)

---

## Stage 1 — Intake

**Trigger:** new user request OR new data file/path/query arrives.

**Inputs needed:**

| Field | Type | Description |
|-------|------|-------------|
| `data_pointer` | string | Path, SQL query, or upload reference |
| `user_goal` | string | User's question / analysis request |
| `target_y` | string (optional) | Explicitly named target metric |
| `mode` | enum | `guided` / `auto` / `exploratory` |
| `output_format` | enum | `md` / `html` / `pptx` / `notebook` / `all` |

**Actions:**
1. Shallow-scan data (extension, sheet/table list, row count, columns + dtypes, head, random sample). Do **not** full-load huge files.
2. Restate the user goal in one sentence; flag ambiguity.
3. Tag field roles with confidence: `target_y`, `time`, `entity_id`, `process_group`, `parameter_x`, `outcome_label`, `measure`.
4. If `Y` missing in `guided` mode: ask once with ranked candidates + recommendation.
5. Frame the goal into one purpose: compare groups · explain drivers · detect change · monitor stability · estimate capability · predict/classify · segment · explore.

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| File unreadable | Try alternate parsers (`.read_csv(encoding='latin1')`, `.read_excel(engine='openpyxl')`) | Ask user for correct format/encoding | Return error + data request template |
| No plausible `Y` | Scan column names + sample for target keywords (yield, defect, pass, fail) | In `guided` mode, present top-3 candidates for user confirmation | Fall back to `exploratory` mode (profile-only) |

**Parallelization hint:** none. Sequential gate.

**Outputs:**

| Artifact | Type | Schema |
|----------|------|--------|
| `data_manifest` | JSON | `{file_path, n_rows, n_cols, columns: [{name, dtype, role_candidate, confidence}], sample_rows: [...]}` |
| `framed_goal` | string | One-sentence restatement mapped to analysis purpose (compare/explain/detect/monitor/predict/segment/explore) |

---

## Stage 2 — Readiness

**Trigger:** `data_manifest` produced.

**Inputs needed:**

| Field | Type | Source |
|-------|------|--------|
| `data_manifest` | JSON | Stage 1 output |
| `framed_goal` | string | Stage 1 output |

**Actions:**
1. Score each readiness dimension (see [data-readiness.md](data-readiness.md)): sample size, missingness, grain, time coverage, balance, leakage, role clarity, measurement reliability.
2. Roll up to overall decision: `ok` / `partial` / `blocked`.
3. If `partial`: list which sub-questions are still answerable and which must be dropped.
4. If `blocked`: write a concrete data-request artifact (fields, grain, span, target definition).

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| Any dimension scored `blocked` | Apply narrowing: drop leaked columns, filter to adequate-N subset, restrict time span | Try alternate analysis grain (e.g., daily → weekly aggregation) | Emit `readiness_report` with `decision: blocked`, stop downstream stages, return data request |
| `partial` in `auto` mode | Continue with narrowed scope, record which sub-questions dropped | Surface limitations in all downstream outputs | In `guided` mode, ask user whether to proceed or stop |

**Parallelization hint:** dimensions are independent — score in parallel (see [multi-agent-orchestration.md](multi-agent-orchestration.md) `parallel_readiness_scan`).

**Outputs:** `readiness_report` (per-dimension scores + overall decision + narrowed-scope list).

---

## Stage 3 — Shaping

**Trigger:** `readiness_report.decision in {ok, partial}`.

**Inputs needed:** `data_manifest`, `readiness_report`, framed `goal`.

**Actions:**
1. Pick analysis grain (row, entity, batch, time bucket, group) per [data-shaping.md](data-shaping.md).
2. Apply reshape ops: join, pivot/unstack, melt, aggregate, window. Record each op's row/col delta and information loss.
3. Build one or more **named** analysis views; each carries grain, filters, dropped columns, aggregation rules, leakage check.
4. Validate post-shape: no 1:N inflation, no future-leaked columns, target preserved.

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| Required reshape impossible (no valid join key) | Try fuzzy key matching (normalize whitespace, case, strip suffixes) | Use alternative join strategy (time-window join, nearest-neighbor) | Bounce back to Stage 2 with data request specifying missing join keys |
| Post-shape sample size collapses (<20 rows) | Relax filters, widen time window, coarsen aggregation grain (daily → weekly) | Present descriptive stats only (no inference) | Narrow scope to profile-only or stop |

**Parallelization hint:** independent views (e.g. group-summary + time-window + raw-row) can be built in parallel.

**Outputs:** `analysis_views[]` (each: name, grain, source ops, filters, leakage flags, row/col counts).

---

## Stage 4 — Method Planning

**Trigger:** at least one `analysis_view` ready.

**Inputs needed:** `analysis_views`, framed `goal`, `readiness_report` (for assumption flags).

**Actions:**
1. For each sub-question, query [method-registry.md](method-registry.md) by purpose.
2. Pick a **primary method** + **alternatives** + **cross-check** per claim.
3. Check method assumptions against readiness flags; swap to alternative if violated.
4. Record **rejected** methods + reason (assumption fail, sample too small, leakage).
5. Bind each method to its analysis view, chart spec, and confidence-calibration rule.

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| No method group fits user's question | Decompose question into sub-questions, map each to method-registry purpose | Suggest closest-match method with caveats | Return to Stage 1 to re-frame goal |
| Every candidate method rejected (assumptions fail) | Try non-parametric alternatives (e.g., Mann-Whitney instead of t-test) | Descriptive stats only (no inference) | Stop and emit "method-blocked" note in report |

**Parallelization hint:** sub-questions are independent — plan in parallel.

**Outputs:** `analysis_plan` (ordered method calls, with primary/alternative/cross-check/rejected slots, view binding, expected outputs).

---

## Stage 5 — Execution

**Trigger:** `analysis_plan` approved (auto-approved in `auto` mode).

**Inputs needed:** `analysis_plan`, `analysis_views`, reusable helpers in `scripts/ds_skill/`.

**Actions:**
1. Load only needed columns; preserve raw and create transformed copies.
2. Set fixed random seeds for any stochastic method.
3. Run primary → alternatives → cross-check, in that order, per claim.
4. Capture: estimates, effect sizes, p-values, CIs, assumption diagnostics, warnings, failures.
5. Save charts and tables with deterministic names (`<view>_<method>_<artifact>`).
6. Build the `evidence_matrix`: one row per claim with primary, supports, effect, caveats, confidence.

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| Primary method errors | Run alternative method from plan (e.g., Welch t-test → Mann-Whitney) | If alternative also fails, run cross-check method for directional signal | Mark claim `unsupported`, record error, continue with other claims |
| Catastrophic data issue (all rows drop) | Audit filter chain, identify which filter dropped everything | Relax most restrictive filter, re-run Stage 3 shaping | Bounce to Stage 2/3 with diagnostic report |

**Parallelization hint:** independent claims and independent views run in parallel; downstream cross-checks depend on primaries (see [multi-agent-orchestration.md](multi-agent-orchestration.md) `fan_out_methods`).

**Outputs:** `evidence_matrix` + chart/table artifacts.

---

## Stage 6 — Critic

**Trigger:** `evidence_matrix` populated.

**Inputs needed:** `evidence_matrix`, `analysis_plan`, `readiness_report`, charts/tables.

**Actions:**
1. For each claim, audit: assumptions vs reality, sample size, multiple-testing exposure, confounding, leakage, aggregation paradoxes (Simpson), chart faithfulness.
2. Reconcile disagreements between primary and cross-check methods; explain the likely cause.
3. Downgrade `confidence` labels where warranted; mark unsupported claims.
4. Propose missing cross-checks or sensitivity tests that should have been run.

🔴 **Stop conditions (3-level fallback):**

| Trigger | First-line fix | If still blocked | Final fallback |
|---------|---------------|------------------|----------------|
| Critic forces re-execution (assumption violation found) | Run sensitivity test (e.g., bootstrap CI, stratified analysis) in Stage 5 | If sensitivity test confirms artifact, downgrade to directional signal | Loop back to Stage 5 for that claim only, mark as conditional |
| Every important claim marked `unsupported` | Check if relaxing filters/grain in Stage 3 recovers sample size | Run exploratory profile to identify what *can* be answered | Escalate to user with data request, skip Stage 7 findings section |

**Parallelization hint:** claim-by-claim audit is parallelizable; reconciliation is sequential at the end.

**Outputs:** `critique` (per-claim verdicts, downgrades, requested sensitivity tests, residual risks).

---

## Stage 7 — Report

**Trigger:** `critique` finalized.

**Inputs needed:** all prior artifacts.

**Actions:**
1. Render in this order: executive answer → what was analyzed → readiness + caveats → key findings with charts → method summary + cross-checks → unsupported questions + data requests → recommended next actions.
2. Embed only critic-approved claims; surface downgrades visibly.
3. Emit in user-requested formats (md/html/pptx/notebook).
4. Link every chart and table back to its claim in `evidence_matrix`.

🔴 **Stop conditions:** none — final stage. Errors here are formatting bugs, not analytical.

**Parallelization hint:** format renderers (md, html, pptx) run in parallel.

**Outputs:** `final_report` (+ artifact bundle).

---

## When To Skip Stages

Shortcut routing rules, trigger conditions, and boundary rules are defined in [branch-routing.md](branch-routing.md). Route declaration is Gate 1 in `SKILL.md` — the first line of work is always `route: <route> — <reason>`.

---

## Loops And Bounces

- Stage 6 → Stage 5: critic-driven sensitivity re-run (single claim).
- Stage 3 → Stage 2: post-shape sample collapse triggers new readiness check.
- Stage 4 → Stage 1: no method fits → re-frame goal with user.
- Any stage → user: ask once when blocked in `guided` mode; in `auto`, narrow and document.

---

## Anti-Patterns

Workflow red-flags are defined in [anti-patterns.md](anti-patterns.md). The key workflow-specific violations: skipping readiness before shaping, running methods before plan approval, dropping carry-forward between stages, re-running full pipeline for a single claim, forcing conclusions when blocked, parallelizing dependent stages, letting execution agents override planner method choices.

