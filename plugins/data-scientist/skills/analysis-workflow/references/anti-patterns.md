---
name: anti-patterns
description: Red-flag blacklist of statistical, causal, data-prep, domain, method, and reporting failure modes, each with a recovery action. Use before finalizing any report or claim. Triggers — is this conclusion safe, sanity check, did I leak, p-value as impact, causal claim, before reporting.
---

# Anti-Patterns — Red-Flag Blacklist

🚫 These failure modes silently corrupt an analysis. Scan this list before reporting any claim; each maps to a recovery action. If a stakeholder asks for one of these, explain the risk instead of complying silently.

## Statistical Rigor Failures

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Report p-value as business impact** | large N (n>1000) makes trivial effects "significant"; significance ≠ magnitude | pair every p with effect size + units + CI |
| **Conclude on leaked features** | post-outcome / target-derived `X` inflates accuracy; won't replicate | run the leakage scan (data-readiness dim 6) first; drop offenders |
| **Force a conclusion on sparse data** | n<5 per cell, >30% missing on `Y`, or constant `Y` → any test is noise | report descriptive-only; route the question to Tier 3 unsupported |
| **Single method, no cross-check** | one test can fire on an artifact; no triangulation | every Tier-1 claim needs a second method agreeing in direction |
| **Silently impute `Y`** | inventing the target biases every downstream estimate | never impute `Y`; imputing `X` requires a documented, reported strategy |

## Causal Inference Errors

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Causal language on observational data** | "X causes Y" needs an experiment or quasi-experiment | use "associated with" / "predicts" / "differs by" unless a causal design exists |
| **Correlate against same-row outcomes** | features measured *after* or *alongside* Y (same timestamp, same event) may be effects not causes | verify time order; exclude concurrent/post-event features from driver ranking |
| **Call a target-derived feature a "driver"** | mechanically correlated with `Y`; not an independent explanation | tag `target_derived`, exclude from driver ranking |

## Data Preparation Mistakes

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Skip pivot on entity×attribute long data** | driver ranking on unpivoted data mixes entity-level signal with measurement-type noise | pivot to entity-level (one row per wafer/patient/customer, attributes as columns) before ranking drivers |
| **Aggregate away the signal** | group-mean hides Simpson's paradox and station-level failure modes | check within-group before declaring a pooled effect |

## Domain-Specific Pitfalls

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Cp/Cpk on an unstable process** | capability on an out-of-control process is a meaningless number | confirm SPC stability first; compute capability on the in-control segment only |
| **Rank drivers against a raw price level** | non-stationary series produce spurious correlations | use returns / forward returns / excess returns |
| **Refit control/CV limits on the judged data** | circular — the limits always "fit" | hold out a known in-control window / keep train-test separation |

## Method Selection Failures

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Pick a method by name or popularity** | impressive ≠ defensible; the data shape decides | choose by purpose + data type + assumption fit (`method-registry.md`) |

## Reporting Failures

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Silently exclude weak features** | omitting "X has no effect" hides what was tested; reader assumes you didn't check | explicitly state negative findings: "recipe, waiting_time tested, no significant effect (p>0.05, ρ<0.1)" |
| **Claim "comprehensive analysis" when readiness = partial** | over-promises; hides what was dropped | state the `narrowed_scope`: what is answerable, what is not, and why |

## Environment Setup Failures

| 🚫 Anti-pattern | Why it corrupts the result | Do this instead |
|---|---|---|
| **Create a venv when a working environment exists** | interrupts the user, wastes time, litters the workspace | test the active environment first; use it and record versions (Environment Policy in SKILL.md) |

---

## Usage

Before finalizing any analysis report, scan this list to ensure no anti-patterns are present in:
1. Method selection rationale
2. Data preparation steps
3. Statistical claim language
4. Effect reporting format
5. Missing data handling
6. Driver ranking methodology

When you catch yourself about to do any of these: stop, name the anti-pattern, and switch to the "do this instead" column.
