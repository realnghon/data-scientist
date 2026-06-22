---
name: branch-routing
description: Shortcut routing rules for narrow requests — which stages to skip and which artifacts are owed. Use when: request is clearly narrow (one-off stat, profile-only, named method, blocked readiness). Triggers — quick look, single stat, just profile, run t-test, named method, blocked data.
---

# Branch Routing

Not every request needs the full 7-stage pipeline. Route narrow requests directly to save time and context.

## Route Declaration (the _routed_ gate)

The first line of work is always: `route: <route> — <reason>`. Re-route mid-analysis only if new evidence changes the request shape; record the change.

## Route → Artifacts Owed

| Route | Artifacts owed |
|-------|---------------|
| `full` | All Tier-0 artifacts |
| `profile-only` | `data_manifest` + `readiness_report` only (no `analysis_plan`, no `evidence_matrix` — no claims are made) |
| `named-method` | `readiness_report` + assumption checks + `final_report` |
| `one-off` | Inline answer (no artifacts) |
| `blocked` | `data_manifest` + `readiness_report` + `data_request` |

## Trigger Conditions

| User request pattern | Route | Execute steps | Rationale |
|---------------------|-------|---------------|-----------|
| "mean of X", "calculate Y", single stat | one-off | inline answer | No readiness/planning needed |
| "quick look", "just profile", "先看看数据", "profile 一下" | profile-only | 1-5, skip 6-14 | Data understanding, no claims |
| "run a t-test on...", explicit method | named-method | 1-5, 7 (assume check), 11-14 | Skip method *selection*, validate assumptions |
| "全套分析", "analyze this data", "分析数据", "找出影响 Y 的因素" | full | 1-14 | Default: complete workflow |
| Readiness scores `blocked` on a gating dimension | blocked | 1-5, then `data_request` + stop | Never force conclusions |

## Boundary Rules

- **Default to full.** Any analysis verb without an explicit narrowing word ("analyze", "分析", "找原因", "why did X change") → `full`. Shortcuts are exceptions for *clearly* narrow requests.
- A narrowing word only counts when it describes the *whole* request: "快速 profile 一下，然后做全套分析" → `full`.
- `named-method` requires the user to name a concrete statistical method; naming a metric ("compare conversion") is NOT named-method — that's `full`.
- If torn between two routes → take the wider one.

## Named-Method Detail

When the user names a specific method ("run a t-test on Y by line"):

- Respect the choice and skip method *selection*, but still run readiness + shaping
- **Check the named method's assumptions**; if an assumption fails, offer the registry alternative
- 🔴 CHECKPOINT (guided mode): present the alternative and get confirmation before switching
- In `auto` mode: run the alternative as primary, report the named method alongside with a caveat
- Any method switch must be recorded in `analysis_plan.rejected_alternatives` with the failed assumption as the reason
- Never silently run a method whose assumptions are violated
