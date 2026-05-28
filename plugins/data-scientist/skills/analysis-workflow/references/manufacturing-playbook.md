# Manufacturing Playbook

Concrete recipes for the most common manufacturing-data questions. Each recipe is structured as: when to apply -> minimum data -> method -> common failure modes -> recommended cross-checks. Cross-link to `method-registry.md` for method definitions, `chart-catalog.md` for chart selection, `golden-templates.md` for end-to-end workflows.

## Common Field Roles (quick reference)

Targets: yield, pass rate, defect rate, scrap, rework, defect count, defect class, cycle time, takt, throughput, downtime, spec-measurement value, energy, cost.
Drivers: equipment / line / station / cell, product / SKU / recipe, lot / batch / serial, shift / operator / team, supplier / material, process params (temp, pressure, speed, torque, flow, humidity, dwell), time / sequence.

## Recipe 1: SPC Essentials

### When to Apply

Process has ordered observations over time and the question involves stability, drift, special causes, or "is it normal".

### Control Chart Selection

| Data type | Subgroup size | Chart |
|---|---|---|
| Continuous measurement | 1 (individuals) | I-MR |
| Continuous measurement | 2-10 rational subgroup | X-bar / R |
| Continuous measurement | >10 rational subgroup | X-bar / S |
| Defective unit count (binary outcome) | constant n | np-chart |
| Defective unit rate (binary outcome) | variable n | p-chart |
| Defect count, equal opportunity | constant unit | c-chart |
| Defect count, variable opportunity | variable unit | u-chart |

### Minimum Data

- 20-25 in-control subgroups for limit calculation.
- Subgroups must be rationally formed (within-subgroup variation reflects common cause only).
- Order preserved; gaps flagged not silently spanned.

### Special-Cause Rule Sets (apply, do not invent)

Western Electric Rules (classic four):

1. One point beyond 3-sigma.
2. Two of three consecutive points beyond 2-sigma on the same side.
3. Four of five consecutive points beyond 1-sigma on the same side.
4. Eight consecutive points on the same side of centerline.

Nelson Rules (extends to eight) -- add when finer sensitivity is needed:

5. Six points in a row steadily increasing or decreasing.
6. Fourteen points in a row alternating up and down.
7. Fifteen points in a row within 1-sigma (stratification warning).
8. Eight points in a row outside 1-sigma on either side (mixture warning).

### Common Failure Modes

- Limits computed from the same data being judged -> always trips. Mitigation: hold out a known in-control segment.
- Rational subgrouping ignored -> within-subgroup variance polluted by between-subgroup drift; limits too wide. Mitigation: re-design subgroup to capture short-term variation only.
- Variable subgroup size on p-chart with fixed limits -> false alarms. Mitigation: variable-limit p-chart.
- Overdispersion on c/u charts -> false alarms. Mitigation: test for overdispersion; use Laney p' / u' chart if dispersion >1.

### Recommended Cross-Checks

- Trend / change-point analysis on the same data; rules should align with detected breaks.
- Stratify by shift / equipment / operator; verify the chart is not aggregating away the signal.

## Recipe 2: Capability Indices (Cp, Cpk, Pp, Ppk)

### When to Apply

A specification limit exists AND the question is "can this process meet spec". Process MUST be in statistical control first (see Recipe 1) -- capability on unstable process is misleading.

### Formulas

| Index | Formula | Uses |
|---|---|---|
| Cp | (USL - LSL) / (6 * sigma_within) | Potential, two-sided spec |
| Cpk | min((USL - mu) / (3 * sigma_within), (mu - LSL) / (3 * sigma_within)) | Potential, accounts for centering |
| Pp | (USL - LSL) / (6 * sigma_overall) | Overall observed, two-sided spec |
| Ppk | min((USL - mu) / (3 * sigma_overall), (mu - LSL) / (3 * sigma_overall)) | Overall observed, accounts for centering |

`sigma_within` = pooled within-subgroup SD (from R-bar / d2 or S-bar / c4).
`sigma_overall` = total sample SD across all data.

### When Each Applies

- Cp / Cpk: short-term potential; rational subgroups available; process in control.
- Pp / Ppk: long-term overall; subgroups not available OR want to include all sources of variation.
- One-sided spec: drop the missing side; report only the relevant CPU or CPL.

### Minimum Data

- 30+ observations absolute minimum; 100+ preferred.
- Subgroups: 20+ subgroups of size 2-5 for sigma_within estimation.
- Normality check on the underlying distribution; if heavily non-normal, transform (Johnson, Box-Cox) or use non-normal capability (Weibull / percentile) and label the result.

### Reading Guide

| Cpk value | Interpretation | Action |
|---|---|---|
| < 1.00 | Process cannot meet spec | Reject; investigate and improve before capability claim |
| 1.00 - 1.33 | Marginal | Tighten control; not safe for high-volume |
| 1.33 - 1.67 | Adequate | Acceptable for most processes |
| > 1.67 | Strong | Often used as supplier qualification bar (>=1.67) |

Cp - Cpk gap = centering loss. Large gap means process is capable in spread but mis-centered.

### Common Failure Modes

- Computing capability on out-of-control data -> meaningless number. Mitigation: SPC first, then capability on the in-control segment only.
- Non-normal data without transform -> tails over/underestimated. Mitigation: distribution test; transform or non-normal capability.
- Reporting Cpk only when Pp/Ppk would be much lower -> hides long-term drift. Mitigation: report both.
- Spec limit confusion (engineering vs customer vs internal) -> argues about the wrong number. Mitigation: explicit spec source citation.

### Recommended Cross-Checks

- Pair with capability histogram + ECDF chart, both showing spec lines.
- Compute % outside spec empirically and compare to capability-implied %.

## Recipe 3: Measurement System Analysis (Gauge R&R)

### When to Apply

Before any other capability or driver analysis on a measurement -- if the gauge cannot distinguish parts, all downstream conclusions are noise. Question form: "is the measurement system good enough".

### Minimum Data

- 10 parts spanning expected variation.
- 2-3 operators.
- 2-3 trials per operator per part.
- Random order; operators blind to prior measurements ideally.

### Interpretation Thresholds

| Metric | Computation | Acceptable | Marginal | Unacceptable |
|---|---|---|---|---|
| %GR&R (of study var) | sigma_gauge / sigma_total * 100 | < 10% | 10-30% | > 30% |
| %GR&R (of tolerance) | 6 * sigma_gauge / (USL - LSL) * 100 | < 10% | 10-30% | > 30% |
| Number of Distinct Categories (NDC) | 1.41 * sigma_part / sigma_gauge | >= 5 | 2-4 | < 2 |

### Common Failure Modes

- Parts span only common-cause range -> %GR&R inflated. Mitigation: select parts spanning realistic variation.
- Operator bias undetected because operators see prior values. Mitigation: blind randomized order.
- Mixing repeatability and reproducibility without ANOVA breakdown. Mitigation: ANOVA gauge R&R, not just X-bar / R.

### Recommended Cross-Checks

- Verify with a second method or reference standard if available.
- Re-run R&R after instrument calibration or maintenance.

## Recipe 4: DOE Result Interpretation

### When to Apply

The data comes from a designed experiment (full factorial, fractional factorial, response surface, Plackett-Burman, mixture). The question is "which factors and interactions matter".

### Minimum Data

- Replication: at least 2-3 replicates at center or corner points for pure-error estimate.
- Center points: 3-5 for curvature detection.
- Balanced or orthogonal design preserved during data collection.

### Interpretation Sequence

1. Plot main effects with CI; flag factors whose CI excludes zero.
2. Plot 2-way interactions; non-parallel lines indicate interaction.
3. Normal-probability plot (or half-normal) of effect estimates -> effects off the line are real.
4. Pareto of standardized effects -> rank importance.
5. Residual diagnostics: residuals vs fitted, residuals vs run order, residual normal-QQ.
6. If center points show curvature, augment to a response-surface design before optimizing.

### Common Failure Modes

- Reading main effect of a factor that has a strong interaction with another -> misleading. Mitigation: always inspect interaction plot before quoting main effect.
- Confounded effects in fractional factorial mis-attributed. Mitigation: state the resolution and alias structure in the output.
- Run order correlated with time / temperature drift -> drift confounded with effect. Mitigation: residual-vs-run-order plot is mandatory.
- Reporting p-value of effect without effect size in the response units. Mitigation: always pair.

### Recommended Cross-Checks

- Confirmation runs at predicted optimum vs predicted center; check prediction interval contains observed.
- Re-fit with reduced model after removing non-significant terms; check R^2 stability.

## Recipe 5: Batch Effect Identification (Confounder vs Driver)

### When to Apply

A batch / lot / run dimension is present and the question is whether batch is masking or causing the apparent driver effects.

### Minimum Data

- >=5 batches with overlapping levels of suspected drivers (e.g. each batch contains both machines being compared).
- Per-batch N adequate for the comparison method.

### Test Sequence

1. Cross-tab batch x each driver. If any driver level is contained within a single batch, the two are fully confounded -> driver effect is not identifiable from batch effect. Report and stop.
2. Within-batch group comparison: re-run the driver comparison restricted to each batch. If the effect direction reverses or disappears, batch was the confounder (Simpson-style).
3. Fit a mixed-effects model with batch as random intercept; compare driver coefficient to the pooled model. Large shrinkage of the coefficient indicates batch absorbed the effect.
4. If batches are time-ordered, also fit a time term; rule out drift as the actual cause.

### Common Failure Modes

- Calling batch a "confounder" when it is actually the driver (e.g. raw-material variation). Mitigation: if batch effect is large AND batches correspond to known input changes, batch IS a driver, not a nuisance.
- Too few batches -> mixed-effects model fails to converge or returns near-zero variance. Mitigation: collapse comparison to fixed-effects per batch and report ranges.

### Recommended Cross-Checks

- Materials / supplier change log: align batch boundaries with documented input changes.
- If a process change date is known, before/after split should align with batch.

## Recipe 6: Yield / Defect Pareto (Vital Few)

### When to Apply

Defects fall into multiple categories / causes / locations and the question is "what to fix first".

### Minimum Data

- Defect classification field with mutually exclusive categories.
- Sufficient total defects (>=100) for category counts to be stable.
- Time window matches the operational decision window (do not Pareto a year for a weekly meeting).

### Method

1. Count defects per category; sort descending; compute cumulative %.
2. Mark 80% cumulative line; categories below the line are the vital few.
3. Annotate each vital-few category with its rate per unit produced, not just count.
4. Split the top 1-3 categories by next-level dimension (equipment / shift / product) to find the dominant contributor.

### Common Failure Modes

- "Other" bucket is the tallest bar -> classification is broken. Mitigation: split "Other" before any Pareto reading.
- Counts dominated by a single high-volume product -> Pareto reflects mix, not process. Mitigation: report defect rate per unit, also stratify.
- Stable historical Pareto used for a new product / process -> wrong vital few. Mitigation: short-window stratified Pareto for new conditions.

### Recommended Cross-Checks

- Pareto by count AND by cost / risk-weighted severity (small count, large cost still matters).
- Repeat in a recent window; vital few should be stable to be actionable.

## Recipe 7: Process Drift Detection

### When to Apply

Question is "did something change", "when did things start getting worse", "is there gradual drift".

### Minimum Data

- Time-ordered observations.
- >=50 observations before and after suspected change point for power.
- No silent gaps; gaps acknowledged.

### Method Combinations

- CUSUM chart: detects small persistent shifts faster than Shewhart.
- EWMA chart: weights recent observations; detects gradual drift.
- PELT or Binary Segmentation change-point detection on the residual (after detrending if needed).
- Pair detection with Nelson rules 5 (six in a row trending) and 6 (alternating) for finer signals.

### Common Failure Modes

- Single method declaring a change point with no corroboration -> false alarm. Mitigation: require at least two methods (e.g. CUSUM + PELT) to agree on direction and approximate location.
- Seasonality mistaken for drift. Mitigation: decompose seasonal component first.
- Sensor calibration event coinciding with apparent drift. Mitigation: cross-reference maintenance log.
- Re-fitting baseline after each suspected change -> drift always "detected". Mitigation: pre-register baseline window.

### Recommended Cross-Checks

- Pair change-point location with operational event log (recipe change, material lot change, maintenance).
- Show pre and post distributions side by side with effect size, not just "change detected".

## Manufacturing Caveats (apply always)

- Product mix can create false equipment effects -- always stratify by product.
- Time drift can masquerade as batch or shift effect -- always include a time check.
- Rework and retest records may duplicate units -- de-dup by serial / lot if possible.
- Aggregated yield can hide station-level failure modes -- drill to station before declaring "yield is fine".
- Operator effects are sensitive and must be anonymized / aggregated when reported externally.
- Root-cause claims require process knowledge or designed experiment; observational analysis names suspects, not culprits.
