from __future__ import annotations

import warnings
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class MethodRecommendation:
    primary_method: str
    decision_reason: str
    assumptions: list[str]
    cross_checks: list[str]
    rejected_methods: dict[str, str]
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def recommend_group_comparison(
    *,
    target_type: str,
    group_count: int,
    paired: bool,
    min_group_size: int,
    equal_variance_p: float | None,
    normality_ok: bool | None,
) -> MethodRecommendation:
    """Recommend a group-comparison method with explicit rejection reasons."""

    rejected: dict[str, str] = {}
    assumptions = [
        "observations are independent unless paired=True",
        "target and group columns use the same analysis grain",
    ]

    if target_type in {"binary", "categorical"}:
        if group_count == 2:
            return MethodRecommendation(
                primary_method="fisher_exact_or_two_proportion_test",
                decision_reason="Categorical targets should compare proportions or contingency tables.",
                assumptions=assumptions + ["expected cell counts determine Fisher versus chi-square"],
                cross_checks=["chi_square_test"],
                rejected_methods={"t_test": "T-tests require numeric continuous targets."},
                confidence="medium",
            )
        return MethodRecommendation(
            primary_method="chi_square_test",
            decision_reason="Categorical targets across multiple groups are compared with a contingency-table test.",
            assumptions=assumptions + ["expected counts are not too small"],
            cross_checks=["fisher_exact_if_sparse", "standardized_residuals"],
            rejected_methods={"anova": "ANOVA requires numeric continuous targets."},
            confidence="medium",
        )

    if target_type != "numeric":
        return MethodRecommendation(
            primary_method="readiness_blocked",
            decision_reason=f"Unsupported target type for group comparison: {target_type}.",
            assumptions=[],
            cross_checks=[],
            rejected_methods={},
            confidence="low",
        )

    if paired:
        if group_count != 2:
            return MethodRecommendation(
                primary_method="readiness_blocked",
                decision_reason="Paired numeric comparison is only implemented for two paired conditions in V1.",
                assumptions=assumptions,
                cross_checks=[],
                rejected_methods={"repeated_measures_anova": "Not implemented in the V1 helper."},
                confidence="low",
            )
        return MethodRecommendation(
            primary_method="paired_t_test" if normality_ok is not False else "wilcoxon_signed_rank",
            decision_reason="Paired observations require within-pair comparison rather than independent-group tests.",
            assumptions=assumptions + ["pairs are correctly matched"],
            cross_checks=["wilcoxon_signed_rank", "paired_effect_size"],
            rejected_methods={"welch_t_test": "Welch t-test assumes independent groups, not paired observations."},
            confidence="medium",
        )

    small_groups = min_group_size < 20
    variance_unequal = equal_variance_p is not None and equal_variance_p < 0.05
    non_normal = normality_ok is False

    if group_count == 2:
        if non_normal and small_groups:
            rejected["student_t_test"] = "Small non-normal samples make the classic t-test fragile."
            rejected["welch_t_test"] = "Welch is robust to unequal variance but still compares means."
            return MethodRecommendation(
                primary_method="mann_whitney_u",
                decision_reason="Two independent numeric groups with small non-normal samples should use a robust rank-based check.",
                assumptions=assumptions + ["distributions have comparable shape for median-like interpretation"],
                cross_checks=["welch_t_test", "effect_size_cliffs_delta"],
                rejected_methods=rejected,
                confidence="medium",
            )

        rejected["student_t_test"] = (
            "Welch t-test is safer by default because it does not assume equal variances."
            if variance_unequal
            else "Student t-test is acceptable only when equal variance is credible; Welch is the safer default."
        )
        return MethodRecommendation(
            primary_method="welch_t_test",
            decision_reason="Two independent numeric groups are best compared with Welch t-test by default.",
            assumptions=assumptions + ["target is numeric", "groups are independent"],
            cross_checks=["mann_whitney_u", "mean_difference_ci"],
            rejected_methods=rejected,
            confidence="high" if min_group_size >= 20 else "medium",
        )

    if group_count >= 3:
        if non_normal and small_groups:
            rejected["one_way_anova"] = "ANOVA is fragile with small non-normal groups."
            rejected["welch_anova"] = "Welch ANOVA compares means; use rank-based check as primary for small non-normal groups."
            return MethodRecommendation(
                primary_method="kruskal_wallis",
                decision_reason="Multiple numeric groups with small non-normal samples should use a rank-based comparison.",
                assumptions=assumptions,
                cross_checks=["welch_anova", "dunn_posthoc_with_correction"],
                rejected_methods=rejected,
                confidence="medium",
            )

        if variance_unequal:
            rejected["one_way_anova"] = "Levene/Brown-Forsythe suggests unequal variance; Welch ANOVA is safer."
            return MethodRecommendation(
                primary_method="welch_anova",
                decision_reason="Multiple numeric groups with unequal variances should use Welch ANOVA.",
                assumptions=assumptions + ["target is numeric", "groups are independent"],
                cross_checks=["kruskal_wallis", "games_howell_posthoc"],
                rejected_methods=rejected,
                confidence="high" if min_group_size >= 20 else "medium",
            )

        return MethodRecommendation(
            primary_method="one_way_anova",
            decision_reason="Multiple numeric groups with acceptable variance balance can use one-way ANOVA.",
            assumptions=assumptions + ["approximate normality within groups", "variance balance"],
            cross_checks=["welch_anova", "kruskal_wallis", "tukey_hsd"],
            rejected_methods={},
            confidence="high" if min_group_size >= 20 and not non_normal else "medium",
        )

    return MethodRecommendation(
        primary_method="readiness_blocked",
        decision_reason="At least two groups are required for group comparison.",
        assumptions=[],
        cross_checks=[],
        rejected_methods={},
        confidence="low",
    )


def compare_numeric_by_group(
    df: pd.DataFrame,
    *,
    target: str,
    group: str,
    normality_p_threshold: float = 0.01,
) -> dict[str, Any]:
    data = df[[target, group]].dropna()
    groups = [
        values[target].to_numpy(dtype=float)
        for _, values in data.groupby(group)
        if len(values) > 0
    ]
    group_names = [str(name) for name, values in data.groupby(group) if len(values) > 0]
    group_count = len(groups)
    if group_count < 2:
        return {
            "status": "blocked",
            "reason": "At least two non-empty groups are required.",
        }

    min_group_size = min(len(values) for values in groups)
    equal_variance_p = None
    if group_count >= 2 and all(len(values) >= 2 for values in groups):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                equal_variance_p = float(stats.levene(*groups, center="median").pvalue)
        except Exception:
            equal_variance_p = None

    normality_ok = _normality_ok(groups, normality_p_threshold=normality_p_threshold)
    recommendation = recommend_group_comparison(
        target_type="numeric",
        group_count=group_count,
        paired=False,
        min_group_size=min_group_size,
        equal_variance_p=equal_variance_p,
        normality_ok=normality_ok,
    )

    method_output = _run_group_method(groups, recommendation.primary_method)
    effect = _group_effect(groups, group_names)
    return {
        "status": "ok",
        "target": target,
        "group": group,
        "group_count": group_count,
        "group_sizes": {name: int(len(values)) for name, values in zip(group_names, groups)},
        "equal_variance_p": equal_variance_p,
        "normality_ok": normality_ok,
        "primary_method": recommendation.primary_method,
        "recommendation": recommendation.to_dict(),
        "method_output": method_output,
        "effect": effect,
        "interpretation_label": _interpretation_label(method_output, effect, min_group_size),
    }


def compare_categorical(
    df: pd.DataFrame,
    *,
    target: str,
    group: str,
    fisher_max_cells: int = 4,
) -> dict[str, Any]:
    """Test association between two categorical columns.

    Chi-square test of independence by default. When any expected cell count
    drops below 5 the chi-square approximation is unreliable, so a 2x2 table
    falls back to Fisher's exact test and larger tables are flagged as sparse
    (use a simulated/exact test or collapse categories). Effect size is
    Cramér's V, which the registry pairs with chi-square for magnitude.

    Returns a dict mirroring :func:`compare_numeric_by_group`'s shape so both
    branches of group comparison share one calling convention.
    """
    data = df[[target, group]].dropna()
    if len(data) == 0:
        return {"status": "blocked", "reason": "No complete rows for both columns."}

    table = pd.crosstab(data[group], data[target])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {
            "status": "blocked",
            "reason": "Both columns need at least two observed categories.",
            "table_shape": list(table.shape),
        }

    observed = table.to_numpy(dtype=float)
    n = int(observed.sum())

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        chi2, chi2_p, dof, expected = stats.chi2_contingency(observed, correction=False)
    chi2 = float(chi2)
    chi2_p = float(chi2_p)
    dof = int(dof)
    expected = np.asarray(expected, dtype=float)

    min_expected = float(expected.min())
    expected_ok = min_expected >= 5.0

    # Pick the primary test: chi-square when expected counts are healthy,
    # Fisher's exact for a sparse 2x2, otherwise chi-square with a sparsity caveat.
    method_output: dict[str, Any]
    if expected_ok:
        primary_method = "chi_square_test"
        method_output = {
            "method": "chi_square_test",
            "status": "ok",
            "statistic": float(chi2),
            "p_value": float(chi2_p),
            "dof": int(dof),
        }
    elif observed.shape == (2, 2):
        primary_method = "fisher_exact"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            odds_ratio, fisher_p = stats.fisher_exact(observed)
        method_output = {
            "method": "fisher_exact",
            "status": "ok",
            "statistic": float(odds_ratio),
            "p_value": float(fisher_p),
            "reason": f"Min expected count {min_expected:.1f} < 5; Fisher exact on 2x2.",
        }
    else:
        primary_method = "chi_square_test"
        method_output = {
            "method": "chi_square_test",
            "status": "ok",
            "statistic": float(chi2),
            "p_value": float(chi2_p),
            "dof": int(dof),
            "caveat": (
                f"Min expected count {min_expected:.1f} < 5 in a "
                f"{observed.shape[0]}x{observed.shape[1]} table; chi-square "
                "approximation is fragile. Collapse rare categories or use an "
                "exact/simulated test."
            ),
        }

    cramers_v = _cramers_v(chi2, n, observed.shape)
    effect = {
        "cramers_v": cramers_v,
        "min_expected_count": round(min_expected, 3),
        "table": {
            str(row): {str(col): int(table.loc[row, col]) for col in table.columns}
            for row in table.index
        },
    }

    p_value = method_output.get("p_value")
    if p_value is not None and p_value < 0.05 and n >= 40 and (cramers_v or 0) >= 0.1:
        label = "reliable_conclusion"
    elif cramers_v and cramers_v >= 0.1:
        label = "directional_signal"
    else:
        label = "investigation_candidate"

    return {
        "status": "ok",
        "target": target,
        "group": group,
        "n": n,
        "primary_method": primary_method,
        "expected_counts_ok": expected_ok,
        "method_output": method_output,
        "effect": effect,
        "interpretation_label": label,
    }


def _cramers_v(chi2: float, n: int, shape: tuple[int, ...]) -> float | None:
    """Cramér's V effect size for a contingency table (0 = no association)."""
    if n <= 0:
        return None
    k = min(shape) - 1
    if k <= 0:
        return None
    return float(np.sqrt((chi2 / n) / k))


def rank_numeric_drivers(
    df: pd.DataFrame,
    *,
    target: str,
    candidate_features: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_scale = _robust_scale(df[target])
    for feature in candidate_features:
        if feature == target or feature not in df.columns:
            continue
        pair = df[[target, feature]].dropna()
        if len(pair) < 3:
            rows.append(
                {
                    "feature": feature,
                    "method": "readiness_blocked",
                    "score": 0.0,
                    "reason": "Fewer than 3 complete rows.",
                }
            )
            continue

        if pd.api.types.is_numeric_dtype(pair[feature]):
            if pair[feature].nunique(dropna=True) <= 1:
                score = 0.0
                statistic = None
                p_value = None
                reason = "Feature is constant or near-constant in complete rows."
            else:
                statistic, p_value = stats.spearmanr(pair[feature], pair[target])
                score = abs(float(statistic)) if not np.isnan(statistic) else 0.0
                reason = "Spearman correlation captures monotonic numeric relationships."
            rows.append(
                {
                    "feature": feature,
                    "method": "spearman_correlation",
                    "score": score,
                    "statistic": None if statistic is None else float(statistic),
                    "p_value": None if p_value is None else float(p_value),
                    "reason": reason,
                }
            )
        else:
            comparison = compare_numeric_by_group(pair, target=target, group=feature)
            effect = comparison.get("effect", {})
            raw_difference = abs(float(effect.get("max_mean_difference", 0.0) or 0.0))
            score = min(1.0, raw_difference / target_scale) if target_scale > 0 else 0.0
            rows.append(
                {
                    "feature": feature,
                    "method": comparison.get("primary_method", "group_comparison"),
                    "score": score,
                    "raw_difference": raw_difference,
                    "group_count": comparison.get("group_count"),
                    "reason": "Categorical drivers are ranked by normalized group-level target separation.",
                    "comparison": comparison,
                }
            )

    return sorted(rows, key=lambda item: item["score"], reverse=True)


def _robust_scale(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) == 0:
        return 0.0
    q75, q25 = np.percentile(values, [75, 25])
    iqr = float(q75 - q25)
    if iqr > 0:
        return iqr
    value_range = float(values.max() - values.min())
    return value_range if value_range > 0 else 0.0


def _normality_ok(
    groups: list[np.ndarray],
    *,
    normality_p_threshold: float = 0.01,
) -> bool | None:
    """Check Shapiro-Wilk normality for each group.

    Parameters
    ----------
    normality_p_threshold :
        Minimum p-value from Shapiro-Wilk to consider a group normally
        distributed. Default 0.01 (conservative for multiple groups).
    """
    p_values: list[float] = []
    for values in groups:
        if len(values) < 3:
            return None
        if len(values) > 5000:
            sample = np.random.default_rng(42).choice(values, size=5000, replace=False)
        else:
            sample = values
        if np.unique(sample).size <= 2:
            return False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                p_values.append(float(stats.shapiro(sample).pvalue))
        except Exception:
            return None
    return all(p >= normality_p_threshold for p in p_values)


def _run_group_method(groups: list[np.ndarray], method: str) -> dict[str, Any]:
    try:
        # scipy emits moment/precision RuntimeWarnings on near-identical groups;
        # the results are still returned and labelled, so silence the noise.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            if method == "welch_t_test":
                statistic, p_value = stats.ttest_ind(groups[0], groups[1], equal_var=False)
            elif method == "student_t_test":
                statistic, p_value = stats.ttest_ind(groups[0], groups[1], equal_var=True)
            elif method == "mann_whitney_u":
                statistic, p_value = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
            elif method == "one_way_anova":
                statistic, p_value = stats.f_oneway(*groups)
            elif method == "kruskal_wallis":
                statistic, p_value = stats.kruskal(*groups)
            elif method == "welch_anova":
                statistic, p_value = _welch_anova(groups)
            elif method in {"chi_square_test", "fisher_exact_or_two_proportion_test"}:
                return {
                    "method": method,
                    "status": "use_compare_categorical",
                    "hint": "Categorical target: call compare_categorical(df, target=..., group=...).",
                }
            else:
                return {"method": method, "status": "not_implemented"}
    except Exception as exc:
        return {"method": method, "status": "failed", "error": str(exc)}

    return {
        "method": method,
        "status": "ok",
        "statistic": float(statistic),
        "p_value": float(p_value),
    }


def _welch_anova(groups: list[np.ndarray]) -> tuple[float, float]:
    # Welch ANOVA approximation based on group means, variances, and sizes.
    means = np.array([np.mean(g) for g in groups], dtype=float)
    variances = np.array([np.var(g, ddof=1) for g in groups], dtype=float)
    sizes = np.array([len(g) for g in groups], dtype=float)
    weights = sizes / variances
    weighted_mean = np.sum(weights * means) / np.sum(weights)
    k = len(groups)

    numerator = np.sum(weights * (means - weighted_mean) ** 2) / (k - 1)
    correction = 1 + (
        2
        * (k - 2)
        / (k**2 - 1)
        * np.sum((1 / (sizes - 1)) * (1 - weights / np.sum(weights)) ** 2)
    )
    f_stat = numerator / correction
    df1 = k - 1
    df2 = (k**2 - 1) / (
        3 * np.sum((1 / (sizes - 1)) * (1 - weights / np.sum(weights)) ** 2)
    )
    p_value = stats.f.sf(f_stat, df1, df2)
    return float(f_stat), float(p_value)


def _group_effect(groups: list[np.ndarray], group_names: list[str]) -> dict[str, Any]:
    means = {name: float(np.mean(values)) for name, values in zip(group_names, groups)}
    ordered = sorted(means.items(), key=lambda item: item[1])
    max_mean_difference = ordered[-1][1] - ordered[0][1]
    effect: dict[str, Any] = {
        "group_means": means,
        "lowest_mean_group": ordered[0][0],
        "highest_mean_group": ordered[-1][0],
        "max_mean_difference": float(max_mean_difference),
    }
    if len(groups) == 2:
        effect["mean_difference"] = float(np.mean(groups[0]) - np.mean(groups[1]))
        effect["cohens_d"] = _cohens_d(groups[0], groups[1])
    return effect


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2 or len(b) < 2:
        return None
    pooled = np.sqrt(((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1)) / (len(a) + len(b) - 2))
    if pooled == 0:
        return None
    return float((np.mean(a) - np.mean(b)) / pooled)


def _interpretation_label(
    method_output: dict[str, Any],
    effect: dict[str, Any],
    min_group_size: int,
) -> str:
    p_value = method_output.get("p_value")
    magnitude = abs(float(effect.get("max_mean_difference", effect.get("mean_difference", 0.0)) or 0.0))
    if p_value is not None and p_value < 0.05 and min_group_size >= 20 and magnitude > 0:
        return "reliable_conclusion"
    if magnitude > 0:
        return "directional_signal"
    return "investigation_candidate"


def posthoc_pairwise(
    df: pd.DataFrame,
    *,
    target: str,
    group: str,
    method: str | None = None,
    normality_p_threshold: float = 0.01,
) -> dict[str, Any]:
    """Pairwise post-hoc comparisons after a significant omnibus test.

    A significant ANOVA / Kruskal-Wallis only says "at least one group differs";
    it does not say which pairs. This runs the post-hoc test that matches the
    omnibus assumptions and controls the family-wise error across all pairs:

    - ``tukey_hsd``      -- equal-variance parametric (pairs with one-way ANOVA)
    - ``games_howell``   -- unequal-variance parametric (pairs with Welch ANOVA)
    - ``dunn``           -- rank-based, Holm-adjusted (pairs with Kruskal-Wallis)

    When ``method`` is None it is inferred from the same variance/normality
    heuristics used by :func:`compare_numeric_by_group`. Requires statsmodels
    (Tukey) or scikit-posthocs (Games-Howell, Dunn).
    """
    data = df[[target, group]].dropna()
    grouped = [
        (str(name), values[target].to_numpy(dtype=float))
        for name, values in data.groupby(group)
        if len(values) > 0
    ]
    if len(grouped) < 3:
        return {
            "status": "skipped",
            "reason": "Post-hoc pairwise tests apply to 3+ groups; use the two-group effect size instead.",
        }

    names = [n for n, _ in grouped]
    arrays = [a for _, a in grouped]

    if method is None:
        method = _infer_posthoc_method(arrays, normality_p_threshold=normality_p_threshold)

    try:
        if method == "tukey_hsd":
            pairs = _tukey_hsd(data, target, group)
        elif method == "games_howell":
            pairs = _games_howell(data, target, group)
        elif method == "dunn":
            pairs = _dunn(arrays, names)
        else:
            return {"status": "failed", "reason": f"Unknown post-hoc method {method!r}."}
    except ImportError as exc:
        return {"status": "unavailable", "method": method, "reason": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        return {"status": "failed", "method": method, "reason": str(exc)}

    significant = [p for p in pairs if p["p_value"] is not None and p["p_value"] < 0.05]
    return {
        "status": "ok",
        "method": method,
        "correction": "family-wise across all pairs",
        "pairs": pairs,
        "n_significant_pairs": len(significant),
        "significant_pairs": [f"{p['group_a']} vs {p['group_b']}" for p in significant],
    }


def _infer_posthoc_method(
    arrays: list[np.ndarray],
    *,
    normality_p_threshold: float = 0.01,
) -> str:
    """Pick the post-hoc test matching the omnibus assumptions."""
    normality_ok = _normality_ok(arrays, normality_p_threshold=normality_p_threshold)
    small = min(len(a) for a in arrays) < 20
    if normality_ok is False and small:
        return "dunn"
    equal_variance_p = None
    if all(len(a) >= 2 for a in arrays):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                equal_variance_p = float(stats.levene(*arrays, center="median").pvalue)
        except Exception:
            equal_variance_p = None
    if equal_variance_p is not None and equal_variance_p < 0.05:
        return "games_howell"
    return "tukey_hsd"


def _tukey_hsd(data: pd.DataFrame, target: str, group: str) -> list[dict[str, Any]]:
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd  # type: ignore
    except Exception as exc:
        raise ImportError("Tukey HSD requires statsmodels; install statsmodels.") from exc
    res = pairwise_tukeyhsd(
        data[target].to_numpy(dtype=float),
        data[group].astype(str).to_numpy(),
    )
    frame = pd.DataFrame(res._results_table.data[1:], columns=res._results_table.data[0])
    pairs: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        pairs.append(
            {
                "group_a": str(row["group1"]),
                "group_b": str(row["group2"]),
                "mean_difference": float(row["meandiff"]),
                "ci_low": float(row["lower"]),
                "ci_high": float(row["upper"]),
                "p_value": float(row["p-adj"]),
                "reject_null": bool(row["reject"]),
            }
        )
    return pairs


def _games_howell(data: pd.DataFrame, target: str, group: str) -> list[dict[str, Any]]:
    """Games-Howell post-hoc: unequal-variance, unequal-n pairwise comparison.

    Implemented directly against scipy's studentized-range distribution rather
    than a third-party post-hoc package (scikit-posthocs does not ship it). For
    each pair the statistic is q = |mean_i - mean_j| / sqrt((s_i^2/n_i + s_j^2/n_j)/2)
    evaluated at the Welch-Satterthwaite degrees of freedom; p-values come from the
    studentized range with k groups, which controls the family-wise error.
    """
    from scipy.stats import studentized_range  # local: keeps module import light

    grouped = [
        (str(name), sub[target].to_numpy(dtype=float))
        for name, sub in data.groupby(group)
        if len(sub) > 0
    ]
    names = [n for n, _ in grouped]
    arrays = [a for _, a in grouped]
    k = len(arrays)
    means = [float(np.mean(a)) for a in arrays]
    variances = [float(np.var(a, ddof=1)) for a in arrays]
    sizes = [len(a) for a in arrays]

    pairs: list[dict[str, Any]] = []
    for i in range(k):
        for j in range(i + 1, k):
            vi, vj = variances[i], variances[j]
            ni, nj = sizes[i], sizes[j]
            se = np.sqrt(vi / ni + vj / nj)
            diff = means[i] - means[j]
            if se == 0:
                p_val = 1.0
                q = 0.0
                df = float(ni + nj - 2)
            else:
                df = (vi / ni + vj / nj) ** 2 / (
                    (vi / ni) ** 2 / (ni - 1) + (vj / nj) ** 2 / (nj - 1)
                )
                q = abs(diff) / (se / np.sqrt(2.0))
                p_val = float(studentized_range.sf(q, k, df))
            # Games-Howell CI uses the critical q at family-wise alpha=0.05.
            q_crit = float(studentized_range.ppf(0.95, k, df)) if se > 0 else 0.0
            margin = q_crit * se / np.sqrt(2.0)
            pairs.append(
                {
                    "group_a": names[i],
                    "group_b": names[j],
                    "mean_difference": float(diff),
                    "ci_low": float(diff - margin),
                    "ci_high": float(diff + margin),
                    "p_value": min(1.0, p_val),
                    "reject_null": bool(p_val < 0.05),
                }
            )
    return pairs


def _dunn(arrays: list[np.ndarray], names: list[str]) -> list[dict[str, Any]]:
    try:
        import scikit_posthocs as sp  # type: ignore
    except Exception as exc:
        raise ImportError("Dunn's test requires scikit-posthocs; install scikit-posthocs.") from exc
    matrix = sp.posthoc_dunn(arrays, p_adjust="holm")
    # scikit-posthocs labels groups 1..k; remap to the real names.
    matrix.index = names
    matrix.columns = names
    return _matrix_to_pairs(matrix)


def _matrix_to_pairs(matrix: pd.DataFrame) -> list[dict[str, Any]]:
    """Flatten a symmetric p-value matrix into an upper-triangle pair list."""
    labels = list(matrix.index)
    pairs: list[dict[str, Any]] = []
    for i, a in enumerate(labels):
        for b in labels[i + 1 :]:
            p = matrix.loc[a, b]
            p_val = None if pd.isna(p) else float(p)
            pairs.append(
                {
                    "group_a": str(a),
                    "group_b": str(b),
                    "p_value": p_val,
                    "reject_null": bool(p_val is not None and p_val < 0.05),
                }
            )
    return pairs
