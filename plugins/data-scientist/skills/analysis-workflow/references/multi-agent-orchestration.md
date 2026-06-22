---
name: multi-agent-orchestration
description: Multi-agent dispatch patterns for 7-stage pipeline across Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, Copilot, Gemini CLI. Use when spawning sub-agents, need parallelization rules, state-passing contracts, or per-platform dispatch differences. Triggers — how to orchestrate stages, when to parallelize, how state flows between agents, platform-specific patterns.
---

# Multi-Agent Orchestration

Operator's manual for running the 7-stage data-science pipeline across Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, and Gemini CLI. The pipeline is: `intake → readiness → shaping → method-planner → execution → critic → report`. Each stage is a sub-agent prompt under `plugins/data-scientist/agents/`. This document tells the parent (main) agent WHEN to spawn each one, which can run in parallel where supported, and how state flows between them.

## Section 1: Staged orchestration vs single-pass

Use the full staged pipeline when ANY of these hold:

- The dataset is unfamiliar to the session (no `data_manifest` in scope yet).
- The user's goal is ambiguous, multi-part, or could be answered by several methods.
- More than one source file or table is in play and joins are not obvious.
- The user asked for a written report, not a one-off number.
- The analysis will use 2+ methods that benefit from cross-checks.

Use a single-pass shortcut (skip stages) when:

- The user asks for a single statistic on a single column already profiled this session ("give me the mean of column X") — skip everything, answer inline.
- The user named one specific method on data that has already cleared readiness — record a one-method plan inline, run execution, return.
- The request is a follow-up tweak to a report already in scope — re-run only the affected stage.

Anti-rule: do not run the staged pipeline for a question a junior could answer with a one-line pandas call. The pipeline's cost is justified by ambiguity and stakes, not by exhaustiveness.

## Section 2: Stage dependency graph

```
                                  ┌─ (parallel views) ─┐         ┌─ (parallel methods) ─┐
                                  │                    │         │                      │
intake ──→ readiness ──→ shaping ─┼─ shaping ──────────┼─→ planner ─→ execution ────────┼─→ critic ──→ report
                                  │                    │         │                      │
                                  └────────────────────┘         └──────────────────────┘
```

Parallelizable stages:

- **Intake**: one call per source file when sources are disjoint. Merge manifests at the end.
- **Shaping**: one call per analysis view when readiness sanctioned multiple grains and the views do not share intermediate state.
- **Execution**: one call per method when `analysis_plan.parallelizable: true` and each method's `depends_on` is empty.
- **Critic (partial)**: can begin reviewing an evidence_matrix slice while later execution agents finish; re-run on the full matrix.

Stages that MUST stay sequential:

- Readiness must finish before shaping starts.
- Method planner must finish before any execution starts.
- Critic must finish before report starts.
- Report has no successor.

## Section 3: Per-platform fan-out patterns

### Claude Code

Claude Code dispatches sub-agents via the `Agent` (Task) tool. To run agents in parallel, place multiple `Agent` tool calls in the SAME assistant message. Sequential dispatch puts them in separate messages.

Parallel dispatch (three execution agents at once):

```
[assistant message contains three Agent tool calls in one block]

Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m1"], "output_dir":"results/", "carry_forward":{...}}')
Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m2"], "output_dir":"results/", "carry_forward":{...}}')
Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m3"], "output_dir":"results/", "carry_forward":{...}}')
```

The parent waits for all three to return, concatenates their `produced.evidence_matrix` arrays, then dispatches a single critic call sequentially.

Sequential stages use one `Agent` call per message and the parent inspects the JSON envelope before the next dispatch.

### Codex (CLI)

Codex's skill system does not natively spawn parallel sub-agents in the same turn. Emulate the pipeline by:

1. Loading the agent prompts as system/role context for the main thread.
2. Running each stage as a sequential pass, inlining the prior stage's JSON envelope as input.
3. For "parallel" stages, run them one after the other but keep their outputs in separate top-level keys (`evidence_matrix[]` rows are independent and order does not matter).

The skill also ships `scripts/run_full_workflow.py`, a deterministic baseline pipeline that runs `profile_dataset.py` plus tested `ds_skill` helpers (`readiness`, `shaping`, `correlation`) and writes `baseline_artifacts.json` + `baseline_skeleton.md`. Use it as the first sequential hand-off artifact when fan-out is unavailable, then let the main Codex/OpenCode/Gemini thread continue with method-planner → execution → critic → report using the same JSON envelope.

### OpenCode

OpenCode runs the plugin via a Node bootstrap (`.opencode/plugins/data-scientist.js`) that loads the skill into the system prompt. Like Codex, it does not have a native multi-agent dispatch. Treat OpenCode the same as Codex: sequential stages, but use the same JSON envelopes so the orchestrator script remains portable.

### Cursor

Cursor is not a multi-agent runtime — `.cursor/rules/data-scientist.mdc` exposes the skill as an auto-activating rule the main chat consults. The orchestration is user-driven: the user prompts for each stage in turn ("now profile", "now shape", "now run methods"), and the rule keeps the stage contracts consistent. Do not attempt to spawn agents from Cursor; surface the stage hint to the user and wait for their next prompt.

### Cline

Cline is also a rules-based integration, not a native multi-agent runtime. The `.clinerules/data-scientist.md` file mirrors the shared core and should be followed sequentially in one session.

### Windsurf

Windsurf uses a rule file (`.windsurf/rules/data-scientist.md`) to surface the shared workflow. Treat it like Cursor/Cline: sequential stage use, no native subagent dispatch.

### GitHub Copilot

GitHub Copilot reads project instructions from `.github/copilot-instructions.md`. Use the same staged workflow sequentially in chat; do not assume slash commands or native agent fan-out.

### Gemini CLI

Gemini CLI loads `GEMINI.md` as project memory. Run the stages sequentially in one thread and keep the JSON envelope explicit for handoff or rerun.

## Section 4: State-passing contract

Every stage returns the same envelope shape. The parent threads `carry_forward` from one stage's output to the next stage's input, never losing prior produced state.

```json
{
  "stage": "intake | readiness | shaping | method-planner | execution | critic | report",
  "status": "ok | partial | needs_revision | blocked | failed",
  "produced": {},
  "carry_forward": {
    "data_manifest": {},
    "field_role_candidates": {},
    "readiness_report": {},
    "analysis_views": [],
    "analysis_plan": {},
    "evidence_matrix": [],
    "critique": {}
  },
  "next_stage_hint": {
    "stages": ["..."],
    "can_parallelize": false,
    "rationale": ""
  },
  "blockers": [],
  "human_questions": []
}
```

Rules:

- Each stage MUST populate `carry_forward` with everything downstream needs. The parent never reconstructs state from scratch.
- `produced` holds the stage's new artifacts; downstream stages access them via `carry_forward`.
- `next_stage_hint.stages` is advisory. The parent decides whether to honor parallelization based on platform capability.
- `blockers[]` non-empty halts the pipeline. The parent surfaces the blockers to the user.
- `human_questions[]` is a soft halt — the parent may answer them itself if it has the information, otherwise asks the user.

## Section 5: Worked example — manufacturing yield-driver analysis

Goal: "Why did yield drop in Q3? Three CSV files: process_params.csv, defect_log.csv, batch_meta.csv."

### Stage 1: Intake (single call)

Parent dispatches one `ds-intake-agent` call covering all three files. (If the files were on different systems, the parent could fan out three intake calls in parallel and merge manifests.)

Returns:

```json
{
  "stage": "intake",
  "status": "ok",
  "produced": {
    "data_manifest": {
      "sources": [
        {"path": "process_params.csv", "row_count": 412903, "columns": [...]},
        {"path": "defect_log.csv", "row_count": 8821, "columns": [...]},
        {"path": "batch_meta.csv", "row_count": 1204, "columns": [...]}
      ],
      "potential_joins": [
        {"left": "process_params.csv", "right": "batch_meta.csv", "on": ["batch_id"], "confidence": "high"},
        {"left": "defect_log.csv", "right": "batch_meta.csv", "on": ["batch_id"], "confidence": "high"}
      ]
    },
    "field_role_candidates": {
      "target_y": ["yield_pct"],
      "time": ["batch_start_ts"],
      "entity_id": ["batch_id"],
      "groups": ["line_id", "shift"],
      "process_parameters": ["temp_c", "pressure_kpa", "feed_rate"]
    }
  },
  "next_stage_hint": {"stages": ["readiness"], "can_parallelize": false}
}
```

### Stage 2: Readiness

Parent dispatches `ds-readiness-agent` with `analysis_goal: "explain_drivers"`, `target_metric: "yield_pct"`.

Returns `status: ok`, `unit_of_analysis: "one batch"`, all quality checks pass except a `warn` on group balance for `shift=C` (n=82). `next_stage_hint.stages: ["shaping"]`.

### Stage 3: Shaping (PARALLEL ×2)

The user wants driver attribution AND time-trend context. Readiness sanctions two grains. Parent dispatches two `ds-shaping-agent` calls in one message:

```
ds-shaping-agent(view_request={"name":"batch_level", "intended_unit":"batch", ...})
ds-shaping-agent(view_request={"name":"hourly_bucket", "intended_unit":"hour", ...})
```

Each writes a parquet to `results/views/`. Parent merges both `analysis_views[]` entries into the carry_forward.

### Stage 4: Method planner (single call)

Parent dispatches `ds-method-planner-agent`. Returns three methods, marked `parallelizable: true`:

```json
{
  "produced": {
    "analysis_plan": {
      "analysis_purpose": "explain_drivers",
      "methods": [
        {"id": "m1", "method": "group_comparison_anova", "view_name": "batch_level", "depends_on": []},
        {"id": "m2", "method": "random_forest_driver_ranking", "view_name": "batch_level", "depends_on": []},
        {"id": "m3", "method": "stl_time_decomposition", "view_name": "hourly_bucket", "depends_on": []}
      ],
      "rejected_alternatives": [
        {"method": "logistic_regression", "reason": "target is continuous, not binary"},
        {"method": "causal_dag", "reason": "no experimental design or instrument variable available"}
      ],
      "cross_checks": [
        {"between": ["m1", "m2"], "check": "Top-3 drivers from m2 should overlap with significant groups from m1."}
      ],
      "parallelizable": true
    }
  },
  "next_stage_hint": {"stages": ["execution"], "can_parallelize": true}
}
```

### Stage 5: Execution (PARALLEL ×3 on Claude Code)

Parent dispatches three execution agents in one message:

```
ds-execution-agent(assigned_methods=["m1"], output_dir="results/", carry_forward={...})
ds-execution-agent(assigned_methods=["m2"], output_dir="results/", carry_forward={...})
ds-execution-agent(assigned_methods=["m3"], output_dir="results/", carry_forward={...})
```

Each writes to `results/m1/`, `results/m2/`, `results/m3/`. On Codex/OpenCode, run the same three method executions sequentially (optionally after seeding the run with `run_full_workflow.py`'s baseline artifact bundle). Parent concatenates the three returned `evidence_matrix` arrays.

### Stage 6: Critic

Parent dispatches `ds-critic-agent` with the merged `evidence_matrix`. Returns:

```json
{
  "stage": "critic",
  "status": "ok",
  "produced": {
    "critique": {
      "overall_confidence": "medium",
      "claim_assessments": [
        {"claim": "Temperature drop on line 2 drove yield loss", "label": "directional_signal", "risks": ["confound: line 2 also got a new feedstock supplier in week 31"]}
      ],
      "confounds": [
        {"description": "Feedstock supplier change overlaps with the temperature regime shift on line 2.", "affects_method_ids": ["m1", "m2"]}
      ],
      "recommended_revisions": []
    }
  },
  "next_stage_hint": {"stages": ["report"], "can_parallelize": false}
}
```

`recommended_revisions` is empty so the pipeline advances. The confound is recorded for the report.

### Stage 7: Report

Parent dispatches `ds-report-agent` with the full carry_forward and `output_path: "results/final_report.md"`. Markdown is written; pipeline complete.

## Section 6: Failure and degradation rules

- **Readiness returns `blocked`**: stop. The parent surfaces `data_request` to the user as a data-needed artifact. Do NOT proceed to shaping under any condition.
- **Readiness returns `partial`**: proceed with the `narrowed_scope` recorded in `readiness_report`. The report must state the goal was narrowed and why.
- **Critic returns `needs_revision`**: loop back to the `target_stage` of each revision. Do not skip to report. After the loop, re-invoke the critic on the updated evidence_matrix.
- **A parallel execution agent fails**: do NOT block the other methods. The parent records `failed: true` for that method, runs the critic on the partial matrix, and lets the report explicitly note "method X was attempted but failed; conclusions exclude it."
- **Intake reports unreadable source**: stop and ask the user. Do not invent a manifest entry.
- **Critic itself disagrees with the planner's method choice**: it returns a `recommended_revision` with `target_stage: "method-planner"`. The parent re-runs the planner with `prior_critique` populated, then re-executes only the changed methods.

## Section 7: Anti-Patterns — What NOT To Do

🚫 These break the orchestration contract:

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| **Spawn agents for trivial one-step queries** ("mean of column X" on profiled data) | Wastes agent overhead on inline-answerable questions | Inline answer; reserve agents for multi-stage or ambiguous work |
| **Fan out before readiness confirms** | Running shaping/execution on data readiness later blocks wastes compute and confuses user | Gate all downstream stages on `readiness_report.decision: ok/partial` |
| **Run critic before any method produces evidence** | Critic has nothing to evaluate, returns empty or errors | Wait for at least one execution agent to populate evidence_matrix |
| **Let execution agents pick their own methods** | Planner's rejected alternatives resurface, assumptions ignored | Planner owns method choice; execution only runs assigned methods from the plan |
| **Run report on critic's `needs_revision`** | Surfaces unreviewed or wrong results | Always close the loop: re-run target_stage, re-invoke critic, then report |
| **Dispatch parallel agents sharing same output path** | File collisions, race conditions, corrupted results | Namespace by `method_id` or `view.name` (e.g. `results/m1/`, `results/m2/`) |
| **Drop carry_forward between stages** | Downstream stages lose context, must re-derive state | Thread full carry_forward envelope through every dispatch |
| **Parallelize views with shared intermediate state** | One view depends on another's aggregation not yet finished | Sequence those views; only parallelize truly independent views |

