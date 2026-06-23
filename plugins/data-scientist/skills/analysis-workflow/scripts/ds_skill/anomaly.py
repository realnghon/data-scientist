"""Univariate and multivariate anomaly / outlier detection.

All detectors return a uniform dict so reporting code can consume them
interchangeably. Heavy ML dependencies (scikit-learn) are imported lazily
so simple IQR / MAD / z-score pipelines work in minimal environments.

All public functions return dicts (not dataclasses) to minimize calling overhead.
"""

from __future__ import annotations

import warnings
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Univariate detectors
# ---------------------------------------------------------------------------


def detect_iqr(series: pd.Series, k: float = 1.5) -> dict[str, Any]:
    """Tukey IQR fence: flag values outside [Q1 - k*IQR, Q3 + k*IQR]."""
    values, dropped = _prepare_series(series, name="detect_iqr")
    n_total = len(values)

    q1 = float(np.quantile(values, 0.25))
    q3 = float(np.quantile(values, 0.75))
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr

    # Score = distance outside the fence (0 inside).
    scores = np.where(
        values < lower,
        lower - values,
        np.where(values > upper, values - upper, 0.0),
    )
    flagged_mask = scores > 0
    flagged_indices = [int(i) for i in np.where(flagged_mask)[0]]

    assumptions_violated: list[str] = []
    if iqr == 0:
        assumptions_violated.append(
            "IQR is zero – series has too little spread for fence-based detection"
        )

    summary = _format_summary("IQR fence", n_total, len(flagged_indices), dropped)
    return {
        "method": "iqr",
        "n_total": int(n_total),
        "n_flagged": int(len(flagged_indices)),
        "flagged_indices": flagged_indices,
        "scores": [float(s) for s in scores],
        "threshold_used": float(k),
        "summary": summary,
        "assumptions_violated": assumptions_violated,
    }


def detect_mad(series: pd.Series, threshold: float = 3.5) -> dict[str, Any]:
    """Modified z-score using median and MAD (Iglewicz & Hoaglin, 1993).

    Modified z-score = 0.6745 * (x - median) / MAD. Threshold defaults to 3.5
    per the original paper.
    """
    values, dropped = _prepare_series(series, name="detect_mad")
    n_total = len(values)

    median = float(np.median(values))
    abs_dev = np.abs(values - median)
    mad = float(np.median(abs_dev))

    assumptions_violated: list[str] = []
    if mad == 0:
        # Fall back to mean absolute deviation as the divisor; flag everything
        # that deviates if even that is zero.
        meanad = float(np.mean(abs_dev))
        if meanad == 0:
            scores = np.zeros_like(values, dtype=float)
            assumptions_violated.append(
                "MAD and mean absolute deviation are both zero – series is constant"
            )
        else:
            scores = abs_dev / (1.2533 * meanad)
            assumptions_violated.append(
                "MAD is zero – fell back to mean absolute deviation scaling"
            )
    else:
        scores = 0.6745 * abs_dev / mad

    flagged_mask = scores > threshold
    flagged_indices = [int(i) for i in np.where(flagged_mask)[0]]

    summary = _format_summary(
        "modified z-score (MAD)", n_total, len(flagged_indices), dropped
    )
    return {
        "method": "mad",
        "n_total": int(n_total),
        "n_flagged": int(len(flagged_indices)),
        "flagged_indices": flagged_indices,
        "scores": [float(s) for s in scores],
        "threshold_used": float(threshold),
        "summary": summary,
        "assumptions_violated": assumptions_violated,
    }


def detect_zscore(series: pd.Series, threshold: float = 3.0) -> dict[str, Any]:
    """Classic z-score using mean and standard deviation.

    Skewness check: warns when |skew| > 1 that MAD/IQR are better choices.
    """
    values, dropped = _prepare_series(series, name="detect_zscore")
    n_total = len(values)

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if n_total >= 2 else 0.0

    assumptions_violated: list[str] = []
    if std == 0:
        scores = np.zeros_like(values, dtype=float)
        assumptions_violated.append(
            "Standard deviation is zero – cannot compute z-scores"
        )
    else:
        scores = np.abs(values - mean) / std

    if n_total >= 8:
        with warnings.catch_warnings():
            # Near-identical data triggers scipy's catastrophic-cancellation note.
            warnings.simplefilter("ignore", RuntimeWarning)
            skew = float(stats.skew(values, bias=False))
        if abs(skew) > 1:
            assumptions_violated.append(
                f"z-score assumes near-normal – your data is skewed (skew={skew:.2f}); "
                "prefer MAD or IQR"
            )

    flagged_mask = scores > threshold
    flagged_indices = [int(i) for i in np.where(flagged_mask)[0]]

    summary = _format_summary(
        "classic z-score", n_total, len(flagged_indices), dropped
    )
    return {
        "method": "zscore",
        "n_total": int(n_total),
        "n_flagged": int(len(flagged_indices)),
        "flagged_indices": flagged_indices,
        "scores": [float(s) for s in scores],
        "threshold_used": float(threshold),
        "summary": summary,
        "assumptions_violated": assumptions_violated,
    }


def detect_univariate(
    series: pd.Series,
    methods: Iterable[str] = ("iqr", "mad"),
) -> dict[str, Any]:
    """Consensus univariate detection: flag rows agreed on by ≥ 2 methods.

    Falls back to a single-method result when only one method is requested.
    Per-method agreement counts are recorded in ``assumptions_violated`` as
    diagnostic notes (not real violations, but the existing dataclass slot
    is the natural carrier).
    """
    methods = list(methods)
    if not methods:
        raise ValueError("detect_univariate requires at least one method")

    detector_map = {
        "iqr": detect_iqr,
        "mad": detect_mad,
        "zscore": detect_zscore,
    }
    unknown = [m for m in methods if m not in detector_map]
    if unknown:
        raise ValueError(
            f"Unknown univariate method(s): {unknown}. "
            f"Choose from {sorted(detector_map)}"
        )

    per_method: dict[str, dict[str, Any]] = {
        method: detector_map[method](series) for method in methods
    }

    if len(methods) == 1:
        only = per_method[methods[0]]
        return {
            "method": f"consensus({methods[0]})",
            "n_total": only["n_total"],
            "n_flagged": only["n_flagged"],
            "flagged_indices": list(only["flagged_indices"]),
            "scores": list(only["scores"]),
            "threshold_used": only["threshold_used"],
            "summary": only["summary"],
            "assumptions_violated": list(only["assumptions_violated"]),
        }

    n_total = per_method[methods[0]]["n_total"]
    vote_counts = np.zeros(n_total, dtype=int)
    per_method_flags: dict[str, list[int]] = {}
    for method, result in per_method.items():
        per_method_flags[method] = result["flagged_indices"]
        if result["flagged_indices"]:
            vote_counts[result["flagged_indices"]] += 1

    consensus_mask = vote_counts >= 2
    flagged_indices = [int(i) for i in np.where(consensus_mask)[0]]
    scores = vote_counts.astype(float).tolist()

    agreement_notes: list[str] = []
    for method, flags in per_method_flags.items():
        agreement_notes.append(f"{method} flagged {len(flags)} rows")
    union = set().union(*per_method_flags.values()) if per_method_flags else set()
    if union:
        agreement = len(set(flagged_indices)) / len(union)
        agreement_notes.append(
            f"method agreement (consensus / union) = {agreement:.2f}"
        )

    pct = (len(flagged_indices) / n_total * 100) if n_total else 0.0
    summary = (
        f"Consensus ({', '.join(methods)}): {pct:.1f}% rows flagged "
        f"({len(flagged_indices)}/{n_total}) – requires agreement from ≥2 methods"
    )

    # Merge real violations from constituent detectors so callers see them.
    violations: list[str] = []
    for method, result in per_method.items():
        for note in result["assumptions_violated"]:
            violations.append(f"[{method}] {note}")
    violations.extend(agreement_notes)

    return {
        "method": "consensus_univariate",
        "n_total": int(n_total),
        "n_flagged": int(len(flagged_indices)),
        "flagged_indices": flagged_indices,
        "scores": scores,
        "threshold_used": 2.0,
        "summary": summary,
        "assumptions_violated": violations,
    }


# ---------------------------------------------------------------------------
# Multivariate detectors
# ---------------------------------------------------------------------------


def detect_isolation_forest(
    df: pd.DataFrame,
    features: list[str] | None = None,
    contamination: Any = "auto",
    random_state: int = 0,
) -> dict[str, Any]:
    """Isolation Forest on the numeric subset of ``df``.

    sklearn is imported lazily; a clear ImportError is raised if it is not
    installed. Anomaly score is ``-decision_function`` (higher = more
    anomalous) for monotone interpretability.
    """
    if df is None or len(df) == 0:
        raise ValueError("detect_isolation_forest requires a non-empty DataFrame")

    try:
        from sklearn.ensemble import IsolationForest  # noqa: WPS433
    except ImportError as exc:
        raise ImportError(
            "detect_isolation_forest requires scikit-learn; install scikit-learn "
            "to use it"
        ) from exc

    if features is None:
        features = list(df.select_dtypes(include=[np.number]).columns)
    if not features:
        raise ValueError("Isolation Forest requires at least one numeric feature")
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"features not present in DataFrame: {missing}")

    matrix = df[features].apply(pd.to_numeric, errors="coerce")
    matrix = matrix.dropna()
    n_total = len(matrix)
    if n_total < 10:
        raise ValueError(
            "detect_isolation_forest needs at least 10 rows with complete features"
        )

    assumptions_violated: list[str] = []
    if n_total < 200:
        assumptions_violated.append(
            f"Isolation Forest is unreliable on small samples (n={n_total}<200)"
        )

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    model.fit(matrix.to_numpy())
    predictions = model.predict(matrix.to_numpy())  # 1 = inlier, -1 = outlier
    raw_scores = -model.decision_function(matrix.to_numpy())

    flagged_positions = [int(i) for i, p in enumerate(predictions) if p == -1]

    # Map back to dropped-row aware positional indices.
    kept_positions = [df.index.get_loc(idx) for idx in matrix.index]
    flagged_indices = [int(kept_positions[i]) for i in flagged_positions]

    # Score array aligned with df.index (NaN positions get score 0).
    full_scores = np.zeros(len(df), dtype=float)
    for slot, pos in enumerate(kept_positions):
        full_scores[pos] = float(raw_scores[slot])

    threshold = (
        float(contamination)
        if isinstance(contamination, (int, float))
        else float("nan")
    )

    summary = _format_summary(
        "Isolation Forest", len(df), len(flagged_indices), dropped=len(df) - n_total
    )
    return {
        "method": "isolation_forest",
        "n_total": int(len(df)),
        "n_flagged": int(len(flagged_indices)),
        "flagged_indices": flagged_indices,
        "scores": [float(s) for s in full_scores],
        "threshold_used": threshold,
        "summary": summary,
        "assumptions_violated": assumptions_violated,
    }


def detect_multivariate(
    df: pd.DataFrame,
    features: list[str],
    method: str = "isolation_forest",
) -> dict[str, Any]:
    """Dispatch to a multivariate detector by name."""
    if method == "isolation_forest":
        return detect_isolation_forest(df, features=features)
    raise ValueError(
        f"Unknown multivariate method {method!r}. Supported: 'isolation_forest'"
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _prepare_series(series: pd.Series, *, name: str) -> tuple[np.ndarray, int]:
    """Validate, coerce, and drop NaNs from a univariate series.

    Returns (values, dropped_count) and raises ValueError on empty input.
    """
    if series is None or len(series) == 0:
        raise ValueError(f"{name} requires a non-empty series")
    coerced = pd.to_numeric(series, errors="coerce")
    cleaned = coerced.dropna()
    if len(cleaned) == 0:
        raise ValueError(f"{name} has no numeric, non-null observations")
    dropped = int(len(series) - len(cleaned))
    return cleaned.to_numpy(dtype=float), dropped


def _format_summary(label: str, n_total: int, n_flagged: int, dropped: int) -> str:
    """Render the standard one-line anomaly summary string."""
    if n_total == 0:
        return f"{label}: no rows to evaluate"
    pct = n_flagged / n_total * 100
    base = f"{label}: {pct:.1f}% rows flagged ({n_flagged}/{n_total})"
    if pct > 10:
        base += " – flag rate is high; review distribution skew before acting"
    elif n_flagged == 0:
        base += " – no rows exceeded the threshold"
    if dropped:
        base += f"; {dropped} NaN rows skipped"
    return base
