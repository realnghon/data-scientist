---
name: data-scientist
version: 2.1.0
description: "Use when the user wants to _analyze_, _profile_, _reshape_, select a statistical _method_, or produce an evidence-backed _report_."
---

# Data Scientist

## Gates

These override everything else. Skipping any gate invalidates the analysis.

1. **_routed_** — First output: `route: full | profile-only | named-method | one-off | blocked — <reason>`. Use [branch-routing.md](references/branch-routing.md). Re-route only if new evidence changes the request shape; record the change.
2. **_red_ gate** — If [data-readiness.md](references/data-readiness.md) scores any dimension `blocked`, stop. Emit a `data_request` and report only what is answerable. Never force a conclusion.
3. **_ready_ gate** — `readiness_report` must exist before shaping or methods. If missing, run the readiness stage first.
4. **_planned_ gate** — `analysis_plan` must exist before execution. If missing, run method planning first.
5. **_rigorous_ gate** — Every Tier-1 / reliable claim needs: (a) statistical significance (p < 0.05 after correction, or CI excludes null), (b) a cross-check method agreeing in direction, (c) effect size with units, (d) a CI. p ≥ 0.05 or no cross-check → _downgrade_ to directional or unsupported. Detection methods (CUSUM, IsolationForest, STL) are validated instruments — a significant detection may be Tier-1 without a second cross-check.
6. **_critiqued_ gate** — `critique` must exist before the final report. If missing, run the critic stage first.

## Modes

- `guided` (default): proceed automatically, stop at 🔴 _checkpoint_ (max 5 per run; each includes evidence, recommended choice, consequence).
- `auto`: for known/repeatable analyses or golden templates. Stop only if blocked.
- `exploratory`: for unknown datasets. Run intake + readiness first; defer method selection until data quality is confirmed.

## Pipeline

The canonical pipeline has 7 stages: **intake → readiness → shaping → method planning → execution → critic → report**. The authoritative process definition, stage contracts, stop conditions, and loop rules live in [workflow.md](references/workflow.md). This skill is the router; that file is the map.

For narrow routes, skip stages per [branch-routing.md](references/branch-routing.md).

## Required Artifacts

Every non-trivial analysis produces and carries forward these artifacts. They are defined in the references listed.

| Artifact | Produced by | Defined in |
|----------|-------------|------------|
| `data_manifest` | intake | [workflow.md](references/workflow.md) Stage 1 |
| `readiness_report` | readiness | [data-readiness.md](references/data-readiness.md) |
| `analysis_views` | shaping | [data-shaping.md](references/data-shaping.md) |
| `analysis_plan` | method planning | [analysis-plan-template.md](references/analysis-plan-template.md) |
| `evidence_matrix` | execution | [workflow.md](references/workflow.md) Stage 5 |
| `critique` | critic | [workflow.md](references/workflow.md) Stage 6 |
| `final_report` | report | [report-standard.md](references/report-standard.md) |

## References — Lazy Load Map

Load on demand. Skip references unrelated to the current analysis.

| Reference | Load when | Skip if |
|-----------|-----------|---------|
| [workflow.md](references/workflow.md) | Need the canonical 7-stage process, stage contracts, or loops | One-off lookup with no decision branches |
| [branch-routing.md](references/branch-routing.md) | Request is clearly narrow | Full pipeline clearly needed |
| [multi-agent-orchestration.md](references/multi-agent-orchestration.md) | Spawning sub-agents or dispatching stages | Single-threaded, one-stage work |
| [data-readiness.md](references/data-readiness.md) | Building `readiness_report` | Clean curated table; only needs a chart or stat |
| [data-shaping.md](references/data-shaping.md) | Data needs pivot/melt/aggregation/join | Data arrives in exact analysis grain |
| [method-registry.md](references/method-registry.md) | Selecting a statistical/ML method | Method fully prescribed by a matched golden template |
| [chart-catalog.md](references/chart-catalog.md) | Producing report charts | Pure-text answer; user said "no charts" |
| [report-standard.md](references/report-standard.md) | Writing `final_report` | Intermediate exploration only |
| [analysis-plan-template.md](references/analysis-plan-template.md) | Generating `analysis_plan` | One-off or profile-only |
| [golden-templates.md](references/golden-templates.md) | Question matches a recurring pattern | Question is clearly bespoke |
| [manufacturing-playbook.md](references/manufacturing-playbook.md) | Manufacturing data (lot/batch/line/SPC/yield/defect) | Non-MFG domain |
| [financial-domain.md](references/financial-domain.md) | Financial time series (OHLCV, returns, factors) | Non-financial domain |
| [helper-bootstrap.md](references/helper-bootstrap.md) | Need to import `ds_skill` helpers | Already bootstrapped |
| [anti-patterns.md](references/anti-patterns.md) | Before finalizing any report | Planning/data-prep stage |
| [failure-recovery.md](references/failure-recovery.md) | Hit a stage failure or method error | Proceeding smoothly |

## Human-in-the-Loop

🔴 _checkpoint_ fires when:

- Target `Y` is ambiguous or missing.
- Field semantics affect grouping/time/units/leakage.
- Shaping is destructive (aggregation/pivot/drop/impute).
- Only a narrower scope is answerable.
- Two defensible methods disagree.

At each checkpoint: provide 2–3 concrete choices + a recommendation + the evidence behind it. Never ask an open-ended question without showing what the data suggests. In `auto` mode: pick the recommended option, record it, and flag visibly.
