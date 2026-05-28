# <<Report Title: question in plain language>>

> Fill-in template. Conform to `references/report-standard.md`. Do not delete sections; mark empty sections "None" explicitly.

## 1. TL;DR

- <<bullet_1: Tier 1 conclusion in business language, no stats>>
- <<bullet_2: Tier 1 conclusion in business language, no stats>>
- <<bullet_3: optional; if Tier 2 only, prefix with "Directional:">>

## 2. Question & Dataset

- Question asked: <<verbatim user question>>
- Dataset: <<name / source>>
- Time range: <<start>> to <<end>>
- Rows analyzed: <<N_final>> (from <<N_raw>> after filters)
- Unit of analysis (one row = ?): <<row_grain>>
- Roles:
  - target Y: <<y_column, type, units>>
  - drivers: <<list>>
  - time: <<time_column or "none">>
  - group dimensions: <<list>>
- Filters / exclusions applied: <<rule -> rows removed>>

## 3. Reliable Conclusions (Tier 1)

### Conclusion 1

- Statement: <<plain-language statement with direction and magnitude>>
- Evidence:
  - Method: <<method_name>> (`method-registry.md` section: <<section>>)
  - Statistic: <<stat name = value>>
  - Effect size: <<value with units>>, 95% CI <<lo - hi>>
  - N: <<per group n>>
  - p-value: <<value or "n/a">>
- Chart: <<chart_id, caption>>
- Cross-check method: <<method_name>> -> <<agreement summary>>

### Conclusion 2

<<repeat block; delete if none and mark "None" below>>

If none: state "No conclusions cleared the Tier 1 bar; see Directional Signals."

## 4. Directional Signals (Tier 2)

### Signal 1

- Statement: <<hedged statement using "appears to" / "is consistent with" / "suggests">>
- Evidence:
  - Method: <<method_name>>
  - Statistic: <<stat name = value>>
  - Effect size: <<value with units>>, 95% CI <<lo - hi>>
  - N: <<per group n>>
- Chart: <<chart_id>>
- Why directional (mandatory): <<single method only | borderline effect p=X | assumption Y violated | n=Z too small | confound A not ruled out>>

### Signal 2

<<repeat or mark "None">>

## 5. What We Could Not Conclude (Tier 3)

### Unsupported finding 1

- Hoped to conclude: <<the claim that was attempted>>
- Why current data does not support it: <<missing variable | insufficient N | confounded design | no causal lever | leakage>>
- Data or design needed: <<what would have to change to upgrade this to Tier 2 or 1>>

<<repeat or state: "No claims were attempted that the data could not support.">>

## 6. Method Summary

### Methods used

| Purpose | Method | `method-registry.md` section | Why chosen |
|---|---|---|---|
| <<purpose>> | <<method>> | <<section>> | <<reason>> |

### Methods rejected

| Method | Rejected because |
|---|---|
| <<method>> | <<assumption failed / data insufficient / better alternative available>> |

### Planner decisions

<<list of agent-side decisions, link to multi-agent decision log if present, or "None">>

## 7. Limitations & Risks

- Leakage risk: <<columns excluded as post-outcome | "none identified">>
- Confounding: <<variables co-varying with both driver and outcome>>
- Sampling: <<how analyzed rows differ from operating population>>
- Validity scope: <<time window / equipment subset / product mix the conclusions apply to>>
- Measurement: <<known gauge / sensor / inspection issues>>
- Other: <<assumption violations not fully resolved>>

## 8. Recommended Next Actions

### Operational

| Priority | Action | Owner role | Effort (S/M/L) | Expected payoff |
|---|---|---|---|---|
| P1 | <<verb + object>> | <<role>> | <<S/M/L>> | <<payoff>> |

### Analytical

| Priority | Action | Owner role | Effort (S/M/L) | Expected payoff |
|---|---|---|---|---|
| P1 | <<verb + object>> | <<role>> | <<S/M/L>> | <<payoff>> |

## 9. Charts & Tables (index)

| ID | Type | Supports | Annotation status |
|---|---|---|---|
| <<chart_id>> | <<chart type from chart-catalog.md>> | <<Tier 1 conclusion N / Tier 2 signal N>> | <<units, N, missing, CI all present? Y/N>> |

## 10. Data Gaps For Stronger Conclusions

- <<gap_1: missing field / coverage / labels and which conclusion it would upgrade>>
- <<gap_2>>

## 11. Human Decision Log (if applicable)

| Step | Question to user | Options shown | User choice | Effect on analysis |
|---|---|---|---|---|
| <<step>> | <<question>> | <<options>> | <<choice>> | <<downstream effect>> |

<<If no user decisions occurred, delete this section's table and state "No user decisions during run.">>
