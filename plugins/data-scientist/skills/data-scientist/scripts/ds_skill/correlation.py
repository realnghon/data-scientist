"""Pairwise correlation and target-feature dependency analysis.

Supports Pearson, Spearman, Kendall (via scipy.stats) and mutual information
(via sklearn, lazy-imported). All multiple-testing adjustment is done with a
hand-rolled Benjamini-Hochberg FDR so we do not depend on statsmodels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CorrelationResult:
    """One pairwise dependency measurement."""

    x: str
    y: str
    method: str
    coefficient: float
    p_value: float | None
    p_value_fdr_adjusted: float | None
    significant_after_fdr: bool
    n: int
    interpretation: str
    effect_strength: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CorrelationMatrix:
    """Bulk pairwise output: per-method matrices + long-form results."""

    methods: list[str]
    coefficients: dict[str, pd.DataFrame]
    pairs: list[CorrelationResult] = field(default_factory=list)
    n_pairs_tested: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "methods": list(self.methods),
            "coefficients": {
                method: _dataframe_to_nested_dict(matrix)
                for method, matrix in self.coefficients.items()
            },
            "pairs": [pair.as_dict() for pair in self.pairs],
            "n_pairs_tested": int(self.n_pairs_tested),
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_SUPPORTED_METHODS = {"pearson", "spearman", "kendall", "mutual_info"}


def pairwise_correlation(
    df: pd.DataFrame,
    methods: Iterable[str] = ("pearson", "spearman"),
    fdr_alpha: float = 0.05,
    min_observations: int = 30,
) -> CorrelationMatrix:
    """Compute pairwise correlations between all numeric columns of ``df``.

    Returns a :class:`CorrelationMatrix` whose ``pairs`` list contains every
    (column_i, column_j, method) combination that had at least
    ``min_observations`` complete rows. Benjamini-Hochberg FDR is applied
    across all p-values returned in the long-form result.
    """

    if df is None or len(df) == 0:
        raise ValueError("pairwise_correlation requires a non-empty DataFrame")

    methods = list(methods)
    if not methods:
        raise ValueError("methods must contain at least one correlation method")

    unknown = [m for m in methods if m not in _SUPPORTED_METHODS]
    if unknown:
        raise ValueError(
            f"Unsupported correlation methods: {unknown}. "
            f"Choose from {sorted(_SUPPORTED_METHODS)}"
        )

    numeric = df.select_dtypes(include=[np.number])
    columns = list(numeric.columns)
    if len(columns) < 2:
        raise ValueError(
            "pairwise_correlation needs at least two numeric columns; "
            f"found {len(columns)}"
        )

    # Build empty per-method matrices, diagonals = 1.0 for symmetric methods.
    col_index = pd.Index(columns)
    matrices: dict[str, pd.DataFrame] = {
        method: pd.DataFrame(
            np.nan, index=col_index, columns=col_index, dtype=float
        )
        for method in methods
    }
    for method in methods:
        diag_value = 1.0 if method != "mutual_info" else np.nan
        for col in columns:
            matrices[method].loc[col, col] = diag_value

    pairs: list[CorrelationResult] = []
    pending: list[tuple[int, float]] = []  # (index in pairs, raw p-value)

    for i, col_x in enumerate(columns):
        for col_y in columns[i + 1 :]:
            pair_df = numeric[[col_x, col_y]].dropna()
            n = len(pair_df)
            if n < min_observations:
                continue

            x_values = np.array(pair_df[col_x], dtype=float)
            y_values = np.array(pair_df[col_y], dtype=float)

            for method in methods:
                coefficient, p_value = _compute_pair(method, x_values, y_values)
                if coefficient is None or np.isnan(coefficient):
                    continue
                matrices[method].loc[col_x, col_y] = coefficient
                matrices[method].loc[col_y, col_x] = coefficient

                result = CorrelationResult(
                    x=col_x,
                    y=col_y,
                    method=method,
                    coefficient=float(coefficient),
                    p_value=None if p_value is None else float(p_value),
                    p_value_fdr_adjusted=None,
                    significant_after_fdr=False,
                    n=int(n),
                    interpretation=_interpret_strength(coefficient, method),
                    effect_strength=_effect_strength(coefficient, method),
                )
                pairs.append(result)
                if p_value is not None and not np.isnan(p_value):
                    pending.append((len(pairs) - 1, float(p_value)))

    _apply_bh_fdr(pairs, pending, fdr_alpha)

    return CorrelationMatrix(
        methods=methods,
        coefficients=matrices,
        pairs=pairs,
        n_pairs_tested=len(pairs),
    )


def correlation_with_target(
    df: pd.DataFrame,
    target: str,
    candidate_features: list[str] | None = None,
    methods: Iterable[str] = ("pearson", "spearman"),
    include_mi: bool = True,
    fdr_alpha: float = 0.05,
) -> list[CorrelationResult]:
    """Score the correlation of each candidate feature against ``target``.

    Returns a flat list of :class:`CorrelationResult` sorted by
    ``effect_strength`` descending. Mutual information is added (one row per
    feature) when ``include_mi`` is True and sklearn is importable.
    """

    if df is None or len(df) == 0:
        raise ValueError("correlation_with_target requires a non-empty DataFrame")
    if target not in df.columns:
        raise ValueError(f"target column {target!r} not in DataFrame")

    methods = list(methods)
    if not methods:
        raise ValueError("methods must contain at least one correlation method")
    if any(m not in {"pearson", "spearman", "kendall"} for m in methods):
        raise ValueError(
            "correlation_with_target methods must be a subset of "
            "{pearson, spearman, kendall}; mutual_info is controlled by include_mi"
        )

    numeric = df.select_dtypes(include=[np.number])
    if target not in numeric.columns:
        raise ValueError(
            f"target column {target!r} must be numeric for correlation_with_target"
        )

    if candidate_features is None:
        candidate_features = [c for c in numeric.columns if c != target]
    else:
        candidate_features = [
            c for c in candidate_features if c in numeric.columns and c != target
        ]

    if not candidate_features:
        return []

    target_values = numeric[target]
    results: list[CorrelationResult] = []
    pending: list[tuple[int, float]] = []

    for feature in candidate_features:
        pair_df = numeric[[feature, target]].dropna()
        n = len(pair_df)
        if n < 3:
            continue
        x_values = np.array(pair_df[feature], dtype=float)
        y_values = np.array(pair_df[target], dtype=float)

        for method in methods:
            coefficient, p_value = _compute_pair(method, x_values, y_values)
            if coefficient is None or np.isnan(coefficient):
                continue
            results.append(
                CorrelationResult(
                    x=feature,
                    y=target,
                    method=method,
                    coefficient=float(coefficient),
                    p_value=None if p_value is None else float(p_value),
                    p_value_fdr_adjusted=None,
                    significant_after_fdr=False,
                    n=int(n),
                    interpretation=_interpret_strength(coefficient, method),
                    effect_strength=_effect_strength(coefficient, method),
                )
            )
            if p_value is not None and not np.isnan(p_value):
                pending.append((len(results) - 1, float(p_value)))

    if include_mi:
        mi_rows = _mutual_info_against_target(
            numeric, target, candidate_features, target_values
        )
        results.extend(mi_rows)

    _apply_bh_fdr(results, pending, fdr_alpha)
    results.sort(key=lambda r: r.effect_strength, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _compute_pair(method: str, x: np.ndarray, y: np.ndarray) -> tuple[float | None, float | None]:
    """Compute coefficient + p-value for one (x, y) pair under a given method."""
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return None, None
    try:
        if method == "pearson":
            stat, pval = stats.pearsonr(x, y)
            return float(stat), float(pval)  # type: ignore[arg-type]
        if method == "spearman":
            stat, pval = stats.spearmanr(x, y)
            return float(stat), float(pval)  # type: ignore[arg-type]
        if method == "kendall":
            stat, pval = stats.kendalltau(x, y)
            return float(stat), float(pval)  # type: ignore[arg-type]
        if method == "mutual_info":
            mi = _mutual_info_pair(x, y)
            return float(mi), None
    except Exception:
        return None, None
    return None, None


def _interpret_strength(coefficient: float, method: str) -> str:
    """Human-readable interpretation of correlation magnitude.

    Bands follow the convention used in the chart catalog: <0.1 negligible,
    0.1–0.3 weak, 0.3–0.5 moderate, 0.5–0.7 strong, ≥0.7 very strong.
    Sign words are dropped for mutual info (it is non-signed).
    """
    if coefficient is None or np.isnan(coefficient):
        return "undefined"
    magnitude = abs(float(coefficient))
    if method == "mutual_info":
        if magnitude < 0.05:
            return "negligible dependence"
        if magnitude < 0.15:
            return "weak dependence"
        if magnitude < 0.30:
            return "moderate dependence"
        if magnitude < 0.50:
            return "strong dependence"
        return "very strong dependence"

    direction = "positive" if coefficient >= 0 else "negative"
    if magnitude < 0.1:
        return f"negligible {direction}"
    if magnitude < 0.3:
        return f"weak {direction}"
    if magnitude < 0.5:
        return f"moderate {direction}"
    if magnitude < 0.7:
        return f"strong {direction}"
    return f"very strong {direction}"


def _effect_strength(coefficient: float, method: str) -> float:
    """Map a coefficient to a comparable [0, 1] strength score."""
    if coefficient is None or np.isnan(coefficient):
        return 0.0
    if method == "mutual_info":
        # _mutual_info_pair already returns a value normalized into [0, 1]
        return float(max(0.0, min(1.0, coefficient)))
    return float(min(1.0, abs(coefficient)))


def _apply_bh_fdr(
    results: list[CorrelationResult],
    pending: list[tuple[int, float]],
    alpha: float,
) -> None:
    """Benjamini-Hochberg FDR adjustment, applied in-place to results.

    ``pending`` is the list of (index_in_results, raw_p_value) that should
    participate in the multiple-testing correction. Results not in pending
    (e.g. mutual info) keep ``p_value_fdr_adjusted = None`` and
    ``significant_after_fdr = False``.
    """
    if not pending:
        return

    raw = np.array([p for _, p in pending], dtype=float)
    indices = [idx for idx, _ in pending]
    adjusted = _bh_adjust(raw)
    for slot, adj_p in zip(indices, adjusted):
        results[slot].p_value_fdr_adjusted = float(adj_p)
        results[slot].significant_after_fdr = bool(adj_p <= alpha)


def _bh_adjust(p_values: np.ndarray) -> np.ndarray:
    """Vectorized Benjamini-Hochberg step-up FDR adjustment.

    Returns the BH-adjusted p-values in the *original* order. Equivalent to
    ``statsmodels.stats.multitest.multipletests(..., method='fdr_bh')[1]``
    but rolled by hand to keep dependencies minimal.
    """
    p = np.asarray(p_values, dtype=float)
    n = p.size
    if n == 0:
        return p

    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    ranks = np.arange(1, n + 1, dtype=float)

    # Raw BH: adjusted[i] = p_(i) * n / rank_i
    raw_adj = ranked * n / ranks

    # Step-up: enforce monotonicity from the largest rank down.
    cumulative_min = np.minimum.accumulate(raw_adj[::-1])[::-1]
    adjusted_sorted = np.minimum(cumulative_min, 1.0)

    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = adjusted_sorted
    return adjusted


def _mutual_info_pair(x: np.ndarray, y: np.ndarray) -> float:
    """Pairwise mutual information normalized by min(H(X), H(Y)).

    Uses sklearn's continuous mutual_info_regression for the raw MI estimate
    and a histogram-based entropy for the normalizer. sklearn is imported
    lazily so the rest of the module works without it.
    """
    try:
        from sklearn.feature_selection import mutual_info_regression  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover - depends on env
        raise ImportError(
            "mutual_info requires scikit-learn; install scikit-learn to use it"
        ) from exc

    if x.size < 5 or y.size < 5:
        return float("nan")

    mi = float(
        mutual_info_regression(
            x.reshape(-1, 1), y, random_state=0, discrete_features=False
        )[0]
    )
    h_x = _histogram_entropy(x)
    h_y = _histogram_entropy(y)
    denom = min(h_x, h_y)
    if denom <= 0:
        return 0.0
    # Clip to [0, 1] – the sklearn estimator is slightly biased and can produce
    # ratios marginally above 1 on small samples.
    return float(max(0.0, min(1.0, mi / denom)))


def _histogram_entropy(values: np.ndarray) -> float:
    """Shannon entropy of ``values`` using Freedman-Diaconis-ish binning."""
    if values.size == 0:
        return 0.0
    bins = max(2, int(np.sqrt(values.size)))
    hist, _ = np.histogram(values, bins=bins)
    probabilities = hist / hist.sum() if hist.sum() > 0 else hist.astype(float)
    nonzero = probabilities[probabilities > 0]
    if nonzero.size == 0:
        return 0.0
    return float(-np.sum(nonzero * np.log(nonzero)))


def _mutual_info_against_target(
    numeric: pd.DataFrame,
    target: str,
    candidate_features: list[str],
    target_values: pd.Series,
) -> list[CorrelationResult]:
    """Mutual information of each feature vs target, normalized per feature."""
    try:
        from sklearn.feature_selection import mutual_info_regression  # noqa: WPS433
    except ImportError:
        return []

    rows: list[CorrelationResult] = []
    for feature in candidate_features:
        pair = numeric[[feature, target]].dropna()
        n = len(pair)
        if n < 5:
            continue
        x = np.array(pair[feature], dtype=float)
        y = np.array(pair[target], dtype=float)
        if np.unique(x).size < 2 or np.unique(y).size < 2:
            continue
        try:
            mi = float(
                mutual_info_regression(
                    x.reshape(-1, 1), y, random_state=0, discrete_features=False  # type: ignore[arg-type]
                )[0]
            )
        except Exception:
            continue
        h_x = _histogram_entropy(x)
        h_y = _histogram_entropy(y)
        denom = min(h_x, h_y)
        normalized = 0.0 if denom <= 0 else max(0.0, min(1.0, mi / denom))
        rows.append(
            CorrelationResult(
                x=feature,
                y=target,
                method="mutual_info",
                coefficient=float(normalized),
                p_value=None,
                p_value_fdr_adjusted=None,
                significant_after_fdr=False,
                n=int(n),
                interpretation=_interpret_strength(normalized, "mutual_info"),
                effect_strength=_effect_strength(normalized, "mutual_info"),
            )
        )
    return rows


def _dataframe_to_nested_dict(frame: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    """JSON-friendly nested-dict serialization of a correlation matrix."""
    out: dict[str, dict[str, float | None]] = {}
    for row in frame.index:
        row_dict: dict[str, float | None] = {}
        for col in frame.columns:
            value = frame.loc[row, col]
            if pd.isna(value):
                row_dict[str(col)] = None
            else:
                row_dict[str(col)] = float(value)
        out[str(row)] = row_dict
    return out
