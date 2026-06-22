---
name: data-scientist
version: 2.0.0
description: "Use when the user wants to _analyze_ or _profile_ a dataset, _reshape_ tables (pivot/melt/join/aggregate), select a statistical _method_, or produce an evidence-backed _report_ with charts."
---

# Data Scientist

## Gates

These override everything else. Skipping any _gate_ invalidates the analysis.

1. **_routed_** — Before any other action, output: `route: full | profile-only | named-method | one-off | blocked — <one-sentence reason>` (see [branch-routing.md](references/branch-routing.md)). Re-route mid-analysis only if new evidence changes the request shape; record the change.
2. **Pre-execution gate** — `data_manifest` + `readiness_report` + `analysis_plan` must exist as artifacts before analysis code runs. Missing → create them first (silently in `auto` mode).
3. **Pre-report gate** — `evidence_matrix` + `critique` must exist before writing the final report. Missing → create them first.
4. **_rigorous_ gate** — Any claim labeled Tier-1 / reliable must have: (a) statistical significance (p < 0.05 after correction, or CI excludes null), (b) a cross-check method agreeing in direction, (c) effect size with units, and (d) a CI. p ≥ 0.05 → _downgrade_ to directional or unsupported. Exception: detection methods (CUSUM, IsolationForest, STL decomposition) are themselves validated — significant detections may be Tier-1 without a second cross-check.
5. **_red_ gate** — `readiness = blocked` stops the pipeline. Emit a `data_request` and report what's answerable instead — never force a conclusion.
6. **Spec/unit sanity** — If data contains spec limits or tolerance ranges, verify they are physically plausible. Flag in `measurement_reliability` dimension and investigate before proceeding.

## Modes

- `guided` (default): proceed automatically, stop at 🔴 _checkpoint_ (max 5 per run; each includes evidence, recommended choice, consequence).
- `auto`: for known/repeatable analyses or golden templates. Stop only if blocked.
- `exploratory`: for unknown datasets. Run data understanding + readiness first; defer method selection until data quality confirmed.

## References — Lazy Load Map

Load on demand. Skip references unrelated to the current analysis.

| Reference | Load when | Skip if |
|-----------|-----------|---------|
| [workflow.md](references/workflow.md) | Starting any non-trivial analysis; need end-to-end sequence | One-shot lookup with no decision branches |
| [branch-routing.md](references/branch-routing.md) | Request is clearly narrow (one-off, profile-only, named-method, blocked) | Full pipeline clearly needed |
| [multi-agent-orchestration.md](references/multi-agent-orchestration.md) | Full 7-stage pipeline; sub-agent dispatch; `/ds-*` commands | One-off stat, profile-only, no stage hand-offs |
| [data-readiness.md](references/data-readiness.md) | Building `readiness_report`; "is this data good enough"; before modeling | Clean curated table; only needs a chart or stat |
| [data-shaping.md](references/data-shaping.md) | Data needs pivot/melt/aggregation/join; grain mismatch; suspected leakage | Data arrives in exact analysis grain |
| [method-registry.md](references/method-registry.md) | Selecting a statistical/ML method; methods disagree; need rejected-alternatives rationale | Method fully prescribed by matched golden template |
| [chart-catalog.md](references/chart-catalog.md) | Producing report charts; choosing visualization | Pure-text answer; user said "no charts" |
| [report-standard.md](references/report-standard.md) | Writing `final_report`; deliverable formatting | Intermediate exploration only |
| [analysis-plan-template.md](references/analysis-plan-template.md) | Generating `analysis_plan` artifact before execution | One-off or profile-only (no plan needed) |
| [golden-templates.md](references/golden-templates.md) | Question matches recurring pattern (yield drop, A/B test, root cause, capability, MTBF) | Question is clearly bespoke |
| [manufacturing-playbook.md](references/manufacturing-playbook.md) | Manufacturing data (lot/batch/line/recipe/SPC/yield/defect); Cpk, MSA, OEE | Non-MFG domain |
| [advanced-techniques.md](references/advanced-techniques.md) | >2 continuous predictors; categorical noise factors; categorical root cause; A/B test | Single predictor; purely descriptive; no experiment |
| [helper-bootstrap.md](references/helper-bootstrap.md) | Need to import `ds_skill` helpers; environment setup | Already bootstrapped; using hand-coded methods only |
| [anti-patterns.md](references/anti-patterns.md) | Before finalizing any report; caught in a failure mode | Still in planning/data-prep stage |
| [failure-recovery.md](references/failure-recovery.md) | Hit a stage failure; import/join/method error; need recovery strategy | Proceeding smoothly with no errors |
| [financial-domain.md](references/financial-domain.md) | Financial time series (OHLCV, returns, factors) | Non-financial domain |

## Core Workflow

1. **Load workflow structure.** Read [workflow.md](references/workflow.md) and confirm which stages apply. For narrow requests, declare the route per Gate 1 and load [branch-routing.md](references/branch-routing.md) instead. Completion: route declared, relevant workflow stages identified.
2. **Test environment.** Check `python --version` + key imports. Use existing environment if it works; record versions. Ask about venv ONLY when packages are missing or version conflicts exist (full policy in [helper-bootstrap.md](references/helper-bootstrap.md)). Completion: `python_executable`, `python_version`, key package versions recorded; `venv_created: true/false`.
3. **Shallow-scan data.** Filenames, sheets, columns, row counts, dtypes, sample rows. For large files, profile with sampling. Completion: `data_manifest` produced (n_rows, n_cols, all columns with dtype + role_candidate).
4. 🔴 **Confirm target Y.** If user didn't provide a target metric, propose ranked candidates and ask before proceeding. Completion: `target_Y` identified, recorded in analysis metadata.
5. **Assess readiness.** Score all 8 dimensions per [data-readiness.md](references/data-readiness.md) — that document is the SSoT for the dimension list, thresholds, and envelope. Each dimension scored _tri-score_: `ok` / `partial` / `blocked`. Produce `readiness_report` with: (a) per-dimension score + evidence, (b) overall decision — `ok` → proceed; `partial` → proceed with `narrowed_scope`; `blocked` → emit `data_request` and stop, (c) remediation for every `partial`/`blocked` dimension. Completion: `readiness_report` artifact produced with all 8 dimensions scored; overall decision recorded.
6. **Decide reshaping.** Determine whether data must be reshaped, pivoted, aggregated, or joined. Use [data-shaping.md](references/data-shaping.md) if reshaping needed. Completion: `reshaping_needed: true/false` recorded with reason; `analysis_views` produced if reshaping occurred.
7. **Choose methods by purpose.** Use [method-registry.md](references/method-registry.md). For manufacturing, also check [manufacturing-playbook.md](references/manufacturing-playbook.md). Completion: method selection completed per claim.
8. **Dispatch or emulate stages.** For complex work, load [multi-agent-orchestration.md](references/multi-agent-orchestration.md) before dispatching. Completion: execution strategy decided (sub-agent dispatch vs sequential emulation).
9. **Check helpers before hand-coding.** For each method, check if a `ds_skill.*` helper exists ([helper-bootstrap.md](references/helper-bootstrap.md)). If a helper exists, MUST attempt to import and call it first; fall back to hand-coding only if import fails, signature mismatches, or helper errors after 1 retry. Record decision (used helper vs hand-coded + reason) in `analysis_plan`. Completion: every method has a `helper_decision` recorded.
10. **Generate analysis_plan.** Use the template in [analysis-plan-template.md](references/analysis-plan-template.md). Completion: `analysis_plan` artifact produced as JSON with all fields populated.
11. 🔴 **Checkpoint (guided mode):** present `analysis_plan` for user sign-off: claims, methods, rationale, helpers. Then execute reproducible code. Completion: user confirmed plan (guided) or plan auto-approved (auto); execution started.
12. **Advanced technique checks.** Load [advanced-techniques.md](references/advanced-techniques.md) when trigger conditions fire (>2 predictors, categorical noise factors, categorical root cause, A/B experiment). Run mandatory checks per that document. Completion: every triggered check completed; results recorded in `evidence_matrix`.
13. **Cross-check findings.** Every important claim (p < 0.05 AND effect exceeds practical threshold) must have ≥1 alternative method confirming direction. If none fits → _downgrade_ to directional. Completion: every important claim has cross-check recorded in `evidence_matrix`; claims without cross-check labeled directional.
14. **Produce deliverables.** Charts per [chart-catalog.md](references/chart-catalog.md) "Minimum Required Charts" — produce all required charts for the matched analysis type. Report per [report-standard.md](references/report-standard.md). Must include "Tested but rejected" section. Completion: all required charts saved as files; `final_report` produced with chart references; "Tested but rejected" section present.
15. **Cleanup.** Remove temporary venv (if created for this analysis), intermediate test files, temp scripts. Keep only final deliverables. Completion: working directory contains only final deliverables; cleanup summary logged.

## Required Artifacts

### Tier 0 (Mandatory for non-trivial analyses)
- `data_manifest` — source files, row counts, columns, field roles. JSON.
- `analysis_plan` — methods, alternatives, assumptions, helper decisions, transformations. JSON per [analysis-plan-template.md](references/analysis-plan-template.md).
- `final_report` — conclusions, charts, limitations, next actions. Markdown per [report-standard.md](references/report-standard.md).

### Tier 1 (Strongly Recommended)
- `readiness_report` — 8-dimension _tri-score_ + overall decision + remediation. JSON per [data-readiness.md](references/data-readiness.md).
- `evidence_matrix` — findings by method, agreement, confidence tier. JSON or Markdown table.
- `critique` — self-critique of claims before final report: gaps, alternative explanations, limitations. Free-form Markdown.

### Tier 2 (Situational)
- `analysis_views` — reshaped datasets + information-loss notes. Only if reshaping occurred.
- `execution_log` — which steps executed, skipped, shortcut; reasons. JSON array.

## Human-in-the-Loop

🔴 _checkpoint_ fires when:

| Gate | Trigger | Show before asking |
|------|---------|---------------------|
| Target ambiguous | Y missing or 2+ plausible candidates | ranked candidates + why each fits |
| Semantics uncertain | field meaning affects grouping/time/units/leakage | columns in doubt + best-guess role |
| Destructive shaping | aggregation/pivot/drop rows/impute | row-count delta + what information is lost |
| Narrowable-only | broad question unsupported, narrower one is | the narrower scope that IS answerable, with N |
| Paths disagree | 2+ defensible methods point different directions | disagreement + which you trust and why |

When a _checkpoint_ fires: provide 2-3 concrete choices + a recommendation. Never ask open-ended questions without showing what the data suggests. In `auto` mode: pick the recommended option, record in Human Decision Log, flag visibly.

## Domain — Financial Time Series

When data is stock/crypto/fund/market-factor: see [financial-domain.md](references/financial-domain.md). Key constraints: use returns (not raw price); tag momentum/MA/volatility as `target_derived`; check stationarity; no investment advice unless requested.

## Anti-Patterns

Before reporting any claim, scan [anti-patterns.md](references/anti-patterns.md). When you catch yourself about to commit one: stop, name it, switch to the recovery action.

## Safety

Record transformations, filters, seeds, and package versions for reproducibility.
