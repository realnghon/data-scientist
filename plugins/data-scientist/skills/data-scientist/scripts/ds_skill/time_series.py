"""Time-series analysis helpers: trend, decomposition, change-points, sampling QA.

All functions are pure (no IO) and have no hard dependency on optional packages.
``statsmodels`` is imported lazily inside :func:`seasonal_decompose`; if it is not
available we fall back to a simple moving-average decomposition.

Output shape matches ``ds_skill.analysis_methods``: small frozen dataclasses with
``as_dict()`` for JSON-friendly downstream consumption.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrendResult:
    trend: Literal["increasing", "decreasing", "no_trend"]
    tau: float
    p_value: float
    slope_sen: float
    n: int
    significant_at_alpha: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecompResult:
    trend: list[float]
    seasonal: list[float]
    residual: list[float]
    period_used: int
    model: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChangePoints:
    method: str
    change_indices: list[int]
    segments: list[dict[str, Any]]
    confidence: list[float] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SamplingQuality:
    n_samples: int
    span_start: Any
    span_end: Any
    median_interval: Any
    irregular: bool
    gaps: list[dict[str, Any]]
    recommendation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Mann-Kendall trend + Sen's slope
# ---------------------------------------------------------------------------


def mann_kendall_trend(series: pd.Series, alpha: float = 0.05) -> TrendResult:
    """Mann-Kendall trend test with Sen's slope estimator.

    Manual implementation (no ``pymannkendall`` dependency). The test statistic
    is normalised via :func:`scipy.stats.norm` and Sen's slope is the median of
    all pairwise slopes.
    """

    values = pd.Series(series).dropna().to_numpy(dtype=float)
    n = int(values.size)
    if n < 3:
        return TrendResult(
            trend="no_trend",
            tau=0.0,
            p_value=1.0,
            slope_sen=0.0,
            n=n,
            significant_at_alpha=False,
        )

    # S statistic
    diff = values[None, :] - values[:, None]
    upper = np.triu_indices(n, k=1)
    signs = np.sign(diff[upper])
    s = float(signs.sum())

    # Tie-corrected variance
    _, counts = np.unique(values, return_counts=True)
    tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

    if var_s <= 0 or s == 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / np.sqrt(var_s)
    else:
        z = (s + 1) / np.sqrt(var_s)

    p_value = float(2 * (1 - stats.norm.cdf(abs(z))))

    # Kendall's tau (tie-aware denominator)
    n_pairs = n * (n - 1) / 2.0
    tau = float(s / n_pairs) if n_pairs > 0 else 0.0

    # Sen's slope: median of all pairwise slopes (i<j)
    i_idx, j_idx = upper
    dy = values[j_idx] - values[i_idx]
    dx = (j_idx - i_idx).astype(float)
    pairwise_slopes = dy / dx
    slope_sen = float(np.median(pairwise_slopes)) if pairwise_slopes.size else 0.0

    significant = bool(p_value < alpha)
    if not significant:
        trend = "no_trend"
    elif s > 0:
        trend = "increasing"
    else:
        trend = "decreasing"

    return TrendResult(
        trend=trend,  # type: ignore[arg-type]
        tau=tau,
        p_value=p_value,
        slope_sen=slope_sen,
        n=n,
        significant_at_alpha=significant,
    )


# ---------------------------------------------------------------------------
# Seasonal decomposition
# ---------------------------------------------------------------------------


def seasonal_decompose(
    series: pd.Series,
    period: int | None = None,
    model: str = "additive",
) -> DecompResult:
    """Decompose a series into trend + seasonal + residual.

    Uses ``statsmodels.tsa.seasonal.STL`` if available; otherwise falls back to
    a simple centred moving-average decomposition. The period is auto-detected
    from the autocorrelation function when not provided.
    """

    values = pd.Series(series).dropna().to_numpy(dtype=float)
    n = values.size
    if n < 4:
        zeros = [0.0] * n
        return DecompResult(
            trend=values.tolist(),
            seasonal=zeros,
            residual=zeros,
            period_used=max(period or 0, 0),
            model=model,
        )

    if period is None:
        period = _detect_period(values)
    period = max(2, min(int(period), n // 2))

    try:
        from statsmodels.tsa.seasonal import STL  # type: ignore

        # STL requires period >= 2 and series length > 2*period.
        if n >= 2 * period:
            stl = STL(values, period=period, robust=True).fit()
            trend = np.asarray(stl.trend, dtype=float)
            seasonal = np.asarray(stl.seasonal, dtype=float)
            residual = np.asarray(stl.resid, dtype=float)
            return DecompResult(
                trend=trend.tolist(),
                seasonal=seasonal.tolist(),
                residual=residual.tolist(),
                period_used=period,
                model=model,
            )
    except ImportError:
        pass
    except Exception:
        # Fall through to moving-average fallback on any STL failure.
        pass

    return _moving_average_decompose(values, period=period, model=model)


def _detect_period(values: np.ndarray) -> int:
    """Detect a plausible seasonal period from the autocorrelation function."""

    n = values.size
    if n < 6:
        return 2
    x = values - values.mean()
    denom = float(np.dot(x, x))
    if denom == 0:
        return 2
    max_lag = min(n // 2, 200)
    acf = np.array(
        [float(np.dot(x[: n - lag], x[lag:]) / denom) for lag in range(1, max_lag + 1)]
    )
    # Pick the first lag >= 2 that is a local maximum and has acf > 0.2.
    best_lag = 2
    best_val = -np.inf
    for lag in range(2, max_lag):
        prev = acf[lag - 2]
        curr = acf[lag - 1]
        nxt = acf[lag]
        if curr > prev and curr > nxt and curr > 0.2 and curr > best_val:
            best_val = curr
            best_lag = lag
    return best_lag


def _moving_average_decompose(
    values: np.ndarray,
    *,
    period: int,
    model: str,
) -> DecompResult:
    """Simple centred MA decomposition used when statsmodels is unavailable."""

    n = values.size
    # Centred moving average for the trend.
    half = period // 2
    trend = np.full(n, np.nan, dtype=float)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        trend[i] = float(np.mean(values[lo:hi]))

    if model == "multiplicative":
        # Avoid divide-by-zero; fall back to additive locally.
        safe_trend = np.where(trend == 0, np.nan, trend)
        detrended = values / safe_trend
        detrended = np.where(np.isnan(detrended), 1.0, detrended)
    else:
        detrended = values - trend

    seasonal = np.zeros(n, dtype=float)
    for phase in range(period):
        idx = np.arange(phase, n, period)
        if idx.size == 0:
            continue
        seasonal[idx] = float(np.mean(detrended[idx]))

    # Normalise seasonal so it sums (additive) or averages (multiplicative) to neutral.
    if model == "multiplicative":
        adj = float(np.mean(seasonal)) if np.mean(seasonal) != 0 else 1.0
        seasonal = seasonal / adj
        residual = values / (trend * seasonal)
    else:
        adj = float(np.mean(seasonal))
        seasonal = seasonal - adj
        residual = values - trend - seasonal

    return DecompResult(
        trend=trend.tolist(),
        seasonal=seasonal.tolist(),
        residual=residual.tolist(),
        period_used=period,
        model=model,
    )


# ---------------------------------------------------------------------------
# Change-point detection
# ---------------------------------------------------------------------------


def detect_change_points(
    series: pd.Series,
    method: str = "cusum",
    min_size: int = 10,
) -> ChangePoints:
    """Detect change points in the mean.

    Supports ``"cusum"`` (default) and ``"binary_segmentation"``. Both methods
    are implemented manually so they work without the ``ruptures`` dependency.
    """

    values = pd.Series(series).dropna().to_numpy(dtype=float)
    n = values.size
    if n < max(4, 2 * min_size):
        return ChangePoints(
            method=method,
            change_indices=[],
            segments=[_segment_dict(0, n, values)] if n > 0 else [],
            confidence=[],
        )

    if method == "cusum":
        change_indices, confidence = _cusum_change_points(values, min_size=min_size)
    elif method == "binary_segmentation":
        change_indices, confidence = _binary_segmentation(values, min_size=min_size)
    else:
        raise ValueError(f"Unknown change-point method: {method!r}")

    segments = _segments_from_indices(values, change_indices)
    return ChangePoints(
        method=method,
        change_indices=sorted(change_indices),
        segments=segments,
        confidence=confidence,
    )


def _cusum_change_points(
    values: np.ndarray,
    *,
    min_size: int,
    threshold_sigma: float = 5.0,
) -> tuple[list[int], list[float]]:
    """Iteratively split on the largest CUSUM deviation."""

    change_indices: list[int] = []
    confidence: list[float] = []

    def _recurse(lo: int, hi: int) -> None:
        if hi - lo < 2 * min_size:
            return
        segment = values[lo:hi]
        mean = float(segment.mean())
        std = float(segment.std(ddof=1)) if segment.size > 1 else 0.0
        if std == 0:
            return
        cumulative = np.cumsum(segment - mean)
        # Restrict the candidate split to interior points respecting min_size.
        interior = slice(min_size, len(cumulative) - min_size)
        if interior.stop <= interior.start:
            return
        interior_vals = cumulative[interior]
        if interior_vals.size == 0:
            return
        local_idx = int(np.argmax(np.abs(interior_vals))) + interior.start
        stat = float(abs(cumulative[local_idx]) / (std * np.sqrt(len(segment))))
        if stat < threshold_sigma / np.sqrt(len(segment)):
            return
        split = lo + local_idx + 1
        change_indices.append(split)
        confidence.append(stat)
        _recurse(lo, split)
        _recurse(split, hi)

    _recurse(0, len(values))
    # Sort change points + confidences together.
    if change_indices:
        paired = sorted(zip(change_indices, confidence), key=lambda p: p[0])
        change_indices = [idx for idx, _ in paired]
        confidence = [c for _, c in paired]
    return change_indices, confidence


def _binary_segmentation(
    values: np.ndarray,
    *,
    min_size: int,
    threshold: float = 1.0,
) -> tuple[list[int], list[float]]:
    """Recursive binary segmentation on the largest absolute mean shift."""

    change_indices: list[int] = []
    confidences: list[float] = []
    overall_std = float(values.std(ddof=1)) if values.size > 1 else 0.0
    if overall_std == 0:
        return [], []

    def _best_split(lo: int, hi: int) -> tuple[int, float] | None:
        best_stat = 0.0
        best_idx: int | None = None
        for split in range(lo + min_size, hi - min_size + 1):
            left = values[lo:split]
            right = values[split:hi]
            if left.size < min_size or right.size < min_size:
                continue
            stat = abs(left.mean() - right.mean()) * np.sqrt(
                (left.size * right.size) / (left.size + right.size)
            )
            if stat > best_stat:
                best_stat = float(stat)
                best_idx = split
        if best_idx is None:
            return None
        # Normalise by overall std for a comparable "z-like" magnitude.
        return best_idx, best_stat / overall_std

    def _recurse(lo: int, hi: int) -> None:
        if hi - lo < 2 * min_size:
            return
        candidate = _best_split(lo, hi)
        if candidate is None:
            return
        idx, stat = candidate
        if stat < threshold:
            return
        change_indices.append(idx)
        confidences.append(stat)
        _recurse(lo, idx)
        _recurse(idx, hi)

    _recurse(0, len(values))
    if change_indices:
        paired = sorted(zip(change_indices, confidences), key=lambda p: p[0])
        change_indices = [idx for idx, _ in paired]
        confidences = [c for _, c in paired]
    return change_indices, confidences


def _segments_from_indices(values: np.ndarray, change_indices: list[int]) -> list[dict[str, Any]]:
    if values.size == 0:
        return []
    boundaries = [0, *sorted(change_indices), values.size]
    segments = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        if end <= start:
            continue
        segments.append(_segment_dict(start, end, values))
    return segments


def _segment_dict(start: int, end: int, values: np.ndarray) -> dict[str, Any]:
    return {
        "start": int(start),
        "end": int(end),
        "mean": float(values[start:end].mean()),
    }


# ---------------------------------------------------------------------------
# Sampling quality
# ---------------------------------------------------------------------------


def sampling_quality(timestamps: pd.Series) -> SamplingQuality:
    """Inspect timestamp spacing: cadence, irregularity, and gaps."""

    ts = pd.to_datetime(pd.Series(timestamps), errors="coerce").dropna().sort_values()
    ts = ts.reset_index(drop=True)
    n = int(ts.size)

    if n < 2:
        recommendation = (
            "Insufficient timestamps (need at least 2) — cadence checks skipped."
        )
        return SamplingQuality(
            n_samples=n,
            span_start=ts.iloc[0] if n else None,
            span_end=ts.iloc[-1] if n else None,
            median_interval=None,
            irregular=False,
            gaps=[],
            recommendation=recommendation,
        )

    diffs = ts.diff().dropna()
    median_interval = diffs.median()
    if isinstance(median_interval, pd.Timedelta):
        median_seconds = median_interval.total_seconds()
        seconds = diffs.dt.total_seconds()
    else:
        median_seconds = float(median_interval)
        seconds = diffs.astype(float)
    mean_seconds = float(seconds.mean()) if seconds.size else 0.0
    std_seconds = float(seconds.std(ddof=1)) if seconds.size > 1 else 0.0
    cv = (std_seconds / mean_seconds) if mean_seconds > 0 else 0.0
    irregular = bool(cv > 0.2)

    gaps: list[dict[str, Any]] = []
    if median_seconds > 0:
        threshold = 3.0 * median_seconds
        for i, sec in enumerate(seconds):
            if sec > threshold:
                gaps.append(
                    {
                        "start": ts.iloc[i],
                        "end": ts.iloc[i + 1],
                        "size_intervals": int(round(sec / median_seconds)),
                    }
                )

    if irregular and gaps:
        recommendation = (
            "Irregular cadence with gaps — resample to a regular grid and document "
            "interpolation/imputation before trend or seasonality work."
        )
    elif irregular:
        recommendation = (
            "Irregular cadence detected — consider resampling to a regular grid."
        )
    elif gaps:
        recommendation = (
            "Regular cadence with isolated gaps — fill or flag the gap windows."
        )
    else:
        recommendation = "Regular cadence — safe for standard time-series methods."

    return SamplingQuality(
        n_samples=n,
        span_start=ts.iloc[0],
        span_end=ts.iloc[-1],
        median_interval=median_interval,
        irregular=irregular,
        gaps=gaps,
        recommendation=recommendation,
    )


__all__ = [
    "mann_kendall_trend",
    "seasonal_decompose",
    "detect_change_points",
    "detect_regime_changes",
    "sampling_quality",
    "TrendResult",
    "DecompResult",
    "ChangePoints",
    "SamplingQuality",
]


# Alias kept for compatibility with the public surface described in the spec.
detect_regime_changes = detect_change_points
