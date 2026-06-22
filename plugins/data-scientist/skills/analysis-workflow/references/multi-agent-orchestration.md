---
name: multi-agent-orchestration
description: Multi-agent dispatch rules for the 7-stage data-science pipeline. Use when spawning sub-agents, deciding parallel vs sequential stages, or threading state between agents.
---

# Multi-Agent Orchestration

Rules for running the 7-stage pipeline (`intake → readiness → shaping → method-planner → execution → critic → report`) with sub-agents. Each stage prompt lives under `plugins/data-scientist/agents/ds-*-agent.md`.

## When to stage vs inline

**Use the full staged pipeline when any of these hold:**

- Dataset is unfamiliar (no `data_manifest` yet).
- User goal is ambiguous, multi-part, or answerable by several methods.
- Multiple source files / tables need joins.
- User asked for a written report, not a one-off number.
- Analysis will use 2+ methods that benefit from cross-checks.

**Use an inline shortcut when:**

- Single statistic on a single profiled column — answer directly.
- One named method on data that already cleared readiness — record a one-method plan, execute, return.
- Follow-up tweak to a report already in scope — re-run only the affected stage.

## Stage dependency graph

```
                                  ┌─ (parallel views) ─┐         ┌─ (parallel methods) ─┐
                                  │                    │         │                      │
intake ──→ readiness ──→ shaping ─┼─ shaping ──────────┼─→ planner ─→ execution ────────┼─→ critic ──→ report
                                  │                    │         │                      │
                                  └────────────────────┘         └──────────────────────┘
```

The graph's parallel/sequential rules are defined once in [workflow.md](workflow.md) → "Parallelization"; this graph is their visual form. Do not restate them here.

## Runtime classes

The skill supports two runtime classes.

### A — Claude Code

Claude Code dispatches sub-agents via the `Agent` tool. Place multiple `Agent` calls in the same assistant message to run them in parallel; separate messages run them sequentially.

Example — three execution agents in parallel:

```
Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m1"], "output_dir":"results/", "carry_forward":{...}}')
Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m2"], "output_dir":"results/", "carry_forward":{...}}')
Agent(subagent_type="ds-execution-agent", prompt='{"assigned_methods":["m3"], "output_dir":"results/", "carry_forward":{...}}')
```

Wait for all parallel agents to return, merge their `produced` artifacts, and dispatch the next sequential stage.

### B — All other integrations

Codex CLI, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, and Gemini CLI do **not** have native parallel sub-agent dispatch. Run stages sequentially in the main thread and pass the `carry_forward` envelope explicitly. For a deterministic baseline, use `scripts/run_full_workflow.py`, which writes `baseline_artifacts.json` + `baseline_skeleton.md`; then continue planning/execution/critic/report in the main thread using the same envelopes.

## State-passing contract

Every stage returns the same envelope shape. The parent threads `carry_forward` from one stage to the next; never reconstruct state.

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
- `carry_forward` holds everything downstream needs.
- `produced` holds the stage's new artifacts; downstream agents read them from `carry_forward`.
- `next_stage_hint` is advisory; the parent decides based on runtime class.
- `blockers` non-empty halts the pipeline.
- `human_questions` is a soft halt — answer from context if possible, otherwise ask the user.

## Failure and degradation rules

- **Readiness `blocked`** → stop. Surface `data_request` to the user. Do NOT proceed to shaping.
- **Readiness `partial`** → proceed with `narrowed_scope`. Report must state the narrowing and why.
- **Critic `needs_revision`** → loop back to the `target_stage`. Do not skip to report. Re-run critic after the loop.
- **Parallel execution agent fails** → do not block the others. Record `failed: true`, run critic on the partial matrix, and let the report note "method X attempted but failed; conclusions exclude it."
- **Intake unreadable source** → stop and ask the user. Do not invent a manifest entry.
- **Critic disagrees with planner's method choice** → return a `recommended_revision` with `target_stage: "method-planner"`. Re-run planner with `prior_critique`, then re-execute only changed methods.

## Orchestration anti-patterns

| Anti-pattern | Why it breaks | Do this instead |
|---|---|---|
| Spawn agents for trivial one-step queries | Wastes overhead on inline-answerable questions | Answer inline; reserve agents for multi-stage or ambiguous work |
| Fan out before readiness confirms | Wastes compute and confuses the user | Gate all downstream on `readiness_report.decision: ok/partial` |
| Run critic before any evidence exists | Critic has nothing to evaluate | Wait for at least one execution result |
| Let execution agents pick their own methods | Planner's rejected alternatives resurface | Planner owns method choice; execution only runs assigned methods |
| Run report on critic's `needs_revision` | Surfaces unreviewed results | Close the loop: re-run target stage, re-critic, then report |
| Parallel agents share an output path | File collisions, race conditions | Namespace by `method_id` or `view.name` (e.g. `results/m1/`) |
| Drop `carry_forward` between stages | Downstream re-derives state, errors multiply | Thread full envelope through every dispatch |
| Parallelize views with shared intermediate state | One view waits for another's aggregation | Sequence those views; parallelize only truly independent views |

## Agent envelope supplement

Each `ds-*-agent.md` extends the shared envelope with stage-specific inputs and `produced` schemas. Do not repeat the shared envelope keys in agent prompts; inherit them from this document.
