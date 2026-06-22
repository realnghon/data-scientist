---
name: report-standard
description: Final report contract defining structure, evidence-citing format, confidence tiers, limitations template. Use when writing deliverable, need section ordering, or report quality checklist. Triggers — write report, deliverable format, report structure.
---


This file defines the strict contract for the final report produced by the data-scientist skill. An agent writing or reviewing a report MUST conform to this contract. Use `assets/report_template.md` as the fill-in skeleton.

## Three Evidence Tiers (mandatory separation)

Every claim in a report belongs to exactly one of these tiers. Mixing tiers in one section is a defect.

### Tier 1: Reliable Conclusions

Minimum bar: the _rigorous_ gate in `SKILL.md` (significance + cross-check + effect size + CI). Two additional report-tier requirements on top of the gate:

- Method assumptions were checked and met (or the method is assumption-light); N clears the method's documented minimum (see `method-registry.md`).
- No identified leakage, confound, or sampling bias that the conclusion is sensitive to.

Language: declarative. "Yield differs by line; Line B runs 3.2 pp lower than Line A (95% CI 2.1-4.3 pp, n_A=412, n_B=389, Welch t-test p<0.001, confirmed by Mann-Whitney)."

### Tier 2: Directional Signals

Required to qualify:

- A pattern is present but one of: single method only, partial assumption fit, borderline effect, modest N, or one identified caveat the conclusion is sensitive to.

Language: hedged. Must use one of: "appears to", "is consistent with", "suggests", "directional only".
Every directional signal MUST state the specific reason it is not Tier 1 (e.g. "single method", "n=18 per group", "ANOVA assumption of equal variance violated; Welch used but borderline p=0.043").

### Tier 3: Unsupported Findings (explicitly named)

Findings the user or stakeholder might expect to see, but the data does not support. Required structure for each:

- What was hoped to be concluded.
- Why the current data cannot support it (missing variable, insufficient N, confounded design, no causal lever, etc.).
- What data or design would be needed to upgrade to Tier 2 or Tier 1.

This section is non-optional. If empty, state "No claims were attempted that the data could not support" explicitly.

## Required Sections (in this order)

The output MUST contain these sections, in this order, with this content contract. Empty sections are stated explicitly as "None" rather than omitted.

### 1. TL;DR

- At most 3 bullets.
- Business-level language; no statistics, no method names.
- Only Tier 1 conclusions may appear here. Tier 2 may be mentioned only with the word "directional".
- Each bullet must be one sentence.

### 2. Question & Dataset

- Restate the question the user asked (verbatim if possible).
- Dataset: name/source, time range, row count, unit of analysis (one row = ?).
- Roles assigned: target Y, drivers, time, group dimensions (link to `data-shaping.md` taxonomy).
- Any filter or exclusion applied before analysis, with row counts before and after.

### 3. Reliable Conclusions (Tier 1)

For each conclusion:

- Plain-language statement.
- Evidence pointer block: method name (from `method-registry.md`), statistic, effect size with units, CI, N per group, p-value if applicable.
- Reference to the chart that supports it (chart id + caption).
- Reference to the cross-check method that confirmed it.

If zero Tier 1 conclusions, state "No reliable conclusions could be drawn at the required evidence bar" and route remaining findings to Tier 2 / Tier 3.

### 4. Directional Signals (Tier 2)

Same structure as Tier 1 plus a mandatory "Why directional" line stating the specific reason it did not clear Tier 1. Hedge language required.

### 5. What We Could Not Conclude (Tier 3)

Each item: hoped claim -> blocker -> data/design needed. Connect to `data-readiness.md` gap categories where applicable.

### 6. Method Summary

- Methods used, with the section reference in `method-registry.md`.
- Methods considered and rejected, with one-line reason (e.g. "Linear regression rejected: residuals non-normal AND heteroscedastic, used quantile regression instead").
- Any agent-side decisions made by the planner (link to multi-agent decisions if recorded).

### 7. Limitations & Risks

Cover at minimum:

- Leakage risk: any feature observed after the target?
- Confounding: variables that vary with both driver and outcome.
- Sampling: how the analyzed rows differ from the operating population.
- Validity scope: time window, equipment subset, product mix the conclusions apply to.
- Measurement: known sensor / gauge / inspection issues.

### 8. Recommended Next Actions

Each action: concrete verb, owner role, expected effort (S/M/L), expected payoff, priority (P1/P2/P3).
Separate "analytical next steps" (more data, new method) from "operational next steps" (process change, instrument check).

## Writing Rules (enforced)

- Always report effect size with units, not just p-value. A p-value alone is a defect.
- Always state N and missingness for any group-level claim.
- Never write "X causes Y" unless an experimental or quasi-experimental design supports it. Use "associated with", "predicts", "differs by", "is consistent with".
- Always provide chart + table side-by-side for any Tier 1 or Tier 2 finding.
- Cite which `method-registry.md` section produced each statistic.
- Round numbers to the precision the measurement justifies; do not report 4 decimal places on a 2-sig-fig instrument.
- Confidence intervals required for every estimated effect. If the method does not yield one, bootstrap or state "no CI available".
- Use the same group ordering across all charts and tables.
- Units must appear at first use of any numeric quantity and on every axis.

## Human Decision Log

If the user made choices during the run (method selection, exclusion approval, threshold setting), record per choice:

- Question asked to the user.
- Options presented.
- User's choice.
- Effect on the analysis path.

This log lives at the bottom of the output or in an appendix; it is not optional when decisions occurred.

## Cross-References

- Chart selection per method: `chart-catalog.md` "Default chart per method".
- Method definitions and assumptions: `method-registry.md`.
- Readiness gap categories: `data-readiness.md`.
- Manufacturing-specific recipes: `manufacturing-playbook.md`.
- Workflow orchestration: `workflow.md` and `multi-agent-orchestration.md`.

---

## Anti-Patterns

Report-specific red-flags are covered in [anti-patterns.md](anti-patterns.md). Key report violations to watch: p-value without effect size, burying limitations, conclusions without evidence links, no confidence tiers, jargon without translation, charts without N annotation, recommendations without next-actions.
