---
name: workflow
description: Canonical 7-stage data-analysis pipeline (intake → readiness → shaping → method-planner → execution → critic → report). Use when you need stage contracts, stop conditions, loops, or artifact definitions.
---

# Workflow

This is the authoritative process definition for the data-scientist skill. Stages run: **intake → readiness → shaping → method planning → execution → critic → report**. Each stage is owned by the matching `ds-*-agent` (see [multi-agent-orchestration.md](multi-agent-orchestration.md)).

Named artifacts passed downstream:

`data_manifest` · `readiness_report` · `analysis_views` · `analysis_plan` · `evidence_matrix` · `critique` · `final_report`

Route narrow requests via [branch-routing.md](branch-routing.md). Avoid anti-patterns via [anti-patterns.md](anti-patterns.md).

## Stage 1 — Intake

**Trigger:** new user request OR new data file/path/query arrives.

**Inputs needed:** `data_pointer` (path/query), `user_goal`, optional `target_y`, `mode`, `output_format`.

**Actions:**
1. Shallow-scan data (extension, sheet/table list, row count, columns + dtypes, head, random sample). Do not full-load huge files.
2. Restate the user goal in one sentence; flag ambiguity.
3. Tag field roles with confidence: `target_y`, `time`, `entity_id`, `process_group`, `parameter_x`, `outcome_label`, `measure`.
4. If `Y` missing in `guided` mode: ask once with ranked candidates + recommendation.
5. Frame the goal into one purpose: compare groups · explain drivers · detect change · monitor stability · estimate capability · predict/classify · segment · explore.

**Stop conditions:**
- File unreadable → try alternate parsers; if still blocked, ask for format/encoding or return error + data request.
- No plausible `Y` → present top-3 candidates; if still blocked, fall back to `exploratory` profile-only.

**Outputs:** `data_manifest`, `framed_goal`.

## Stage 2 — Readiness

**Trigger:** `data_manifest` produced.

**Actions:**
1. Score all 8 dimensions per [data-readiness.md](data-readiness.md).
2. Roll up to overall decision: `ok` / `partial` / `blocked`.
3. If `partial`: list which sub-questions are still answerable.
4. If `blocked`: write a concrete `data_request` artifact (fields, grain, span, target definition).

**Stop conditions:**
- Any dimension `blocked` → stop downstream; return `data_request`.
- `partial` in `auto` mode → continue with narrowed scope and record it; in `guided` mode, ask once.

**Outputs:** `readiness_report`.

## Stage 3 — Shaping

**Trigger:** `readiness_report.decision` is `ok` or `partial`.

**Actions:**
1. Pick analysis grain per [data-shaping.md](data-shaping.md).
2. Apply reshape ops: join, pivot/unstack, melt, aggregate, window. Record row/col delta and information loss.
3. Build one or more named `analysis_views`; each carries grain, filters, dropped columns, aggregation rules, leakage check.
4. Validate post-shape: no 1:N inflation, no future-leaked columns, target preserved.

**Stop conditions:**
- Required reshape impossible → try fuzzy key matching / time-window join; if still blocked, bounce to Stage 2 with a data request.
- Post-shape sample collapses (<20 rows) → relax filters / widen window / coarsen grain; if still blocked, narrow to profile-only or stop.

**Outputs:** `analysis_views[]`.

## Stage 4 — Method Planning

**Trigger:** at least one `analysis_view` ready.

**Actions:**
1. For each sub-question, query [method-registry.md](method-registry.md) by purpose.
2. Pick a primary method + alternatives + cross-check per claim.
3. Check method assumptions against readiness flags; swap to alternative if violated.
4. Record rejected methods + reason (assumption fail, sample too small, leakage).
5. Bind each method to its analysis view, chart spec, and confidence-calibration rule.

**Stop conditions:**
- No method group fits → decompose question; if still blocked, return to Stage 1 to re-frame.
- Every candidate method rejected → try non-parametric alternatives; if still blocked, mark method-blocked in report.

**Outputs:** `analysis_plan`.

## Stage 5 — Execution

**Trigger:** `analysis_plan` approved (auto-approved in `auto` mode).

**Actions:**
1. Load only needed columns; preserve raw and create transformed copies.
2. Set fixed random seeds for any stochastic method.
3. Run primary → alternatives → cross-check, in that order, per claim.
4. Capture: estimates, effect sizes, p-values, CIs, assumption diagnostics, warnings, failures.
5. Save charts and tables with deterministic names (`<view>_<method>_<artifact>`).
6. Build `evidence_matrix`: one row per claim with primary, supports, effect, caveats, confidence.

**Stop conditions:**
- Primary method errors → run alternative; if that fails, run cross-check; if all fail, mark claim unsupported and continue.
- Catastrophic data issue (all rows drop) → audit filter chain, relax the most restrictive filter, or bounce to Stage 2/3 with diagnostics.

**Outputs:** `evidence_matrix` + chart/table artifacts.

## Stage 6 — Critic

**Trigger:** `evidence_matrix` populated.

**Actions:**
1. Audit each claim: assumptions vs reality, sample size, multiple-testing exposure, confounding, leakage, aggregation paradoxes (Simpson), chart faithfulness.
2. Reconcile disagreements between primary and cross-check methods.
3. Downgrade confidence where warranted; mark unsupported claims.
4. Propose missing cross-checks or sensitivity tests.

**Stop conditions:**
- Critic forces re-execution → run sensitivity test in Stage 5; if confirmed, downgrade to directional.
- Every important claim unsupported → relax filters/grain or run exploratory profile; if still blocked, escalate to user with data request and skip findings section in Stage 7.

**Outputs:** `critique`.

## Stage 7 — Report

**Trigger:** `critique` finalized.

**Actions:**
1. Render in this order: executive answer → what was analyzed → readiness + caveats → key findings with charts → method summary + cross-checks → unsupported questions + data requests → recommended next actions.
2. Embed only critic-approved claims; surface downgrades visibly.
3. Emit in user-requested formats (md/html/pptx/notebook).
4. Link every chart and table back to its claim in `evidence_matrix`.

**Outputs:** `final_report`.

## Loops And Bounces

| From | To | When |
|------|-----|------|
| Stage 6 | Stage 5 | Critic demands sensitivity re-run for one claim. |
| Stage 3 | Stage 2 | Post-shape sample collapse triggers new readiness check. |
| Stage 4 | Stage 1 | No method fits; re-frame goal with user. |
| Any stage | User | Blocked in `guided` mode. In `auto`, narrow and document. |

## Parallelization

Safe in parallel:
- **Intake** when sources are disjoint (merge manifests after).
- **Shaping** when independent views are requested.
- **Execution** when methods have empty `depends_on`.
- **Critic** claim-by-claim; reconcile sequentially at the end.

Must stay sequential:
- readiness before shaping.
- method planner before execution.
- critic before report.
