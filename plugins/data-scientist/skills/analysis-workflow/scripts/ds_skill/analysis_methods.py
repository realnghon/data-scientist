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


def compare_numeric_by_group(df: pd.DataFrame, *, target: str, group: str) -> dict[str, Any]:
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

    normality_ok = _normality_ok(groups)
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


def _normality_ok(groups: list[np.ndarray]) -> bool | None:
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
    return all(p >= 0.01 for p in p_values)


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
