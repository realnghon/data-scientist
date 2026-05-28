"""Bootstrap confidence intervals: percentile, basic, and BCa.

Pure numpy implementation — no dependency on ``scipy.stats.bootstrap``. The BCa
method uses jackknife-based acceleration as documented in Efron & Tibshirani's
*An Introduction to the Bootstrap* (1993), chapter 14.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd
from scipy import stats


_DISTRIBUTION_KEEP = 200


@dataclass(frozen=True)
class BootstrapResult:
    statistic_value: float
    ci_low: float
    ci_high: float
    confidence: float
    method: str
    n_resamples: int
    bootstrap_distribution: list[float]
    standard_error: float
    bias: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def bootstrap_ci(
    data: np.ndarray | pd.Series,
    statistic: Callable[[np.ndarray], float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    method: Literal["percentile", "bca", "basic"] = "bca",
    random_state: int | None = 0,
) -> BootstrapResult:
    """Bootstrap CI for an arbitrary one-sample statistic.

    ``bootstrap_distribution`` on the result is truncated to the first 200
    resampled values so result objects stay small for JSON serialisation; the
    summary stats (``standard_error``, ``bias``) are still computed on the full
    distribution.
    """

    arr = _as_array(data)
    if arr.size == 0:
        raise ValueError("bootstrap_ci requires a non-empty sample.")

    point = float(statistic(arr))
    rng = np.random.default_rng(random_state)
    boot = _bootstrap_distribution_one_sample(arr, statistic, n_resamples, rng)
    return _build_result(
        point=point,
        boot=boot,
        confidence=confidence,
        method=method,
        n_resamples=n_resamples,
        jackknife=lambda: _jackknife_one_sample(arr, statistic),
    )


def bootstrap_two_sample(
    a: np.ndarray | pd.Series,
    b: np.ndarray | pd.Series,
    statistic: Callable[[np.ndarray, np.ndarray], float] | None = None,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    method: Literal["percentile", "bca", "basic"] = "bca",
    random_state: int | None = 0,
) -> BootstrapResult:
    """Bootstrap CI for a two-sample statistic (defaults to difference in means)."""

    arr_a = _as_array(a)
    arr_b = _as_array(b)
    if arr_a.size == 0 or arr_b.size == 0:
        raise ValueError("bootstrap_two_sample requires both samples to be non-empty.")
    if statistic is None:
        statistic = _diff_in_means

    point = float(statistic(arr_a, arr_b))
    rng = np.random.default_rng(random_state)
    boot = _bootstrap_distribution_two_sample(arr_a, arr_b, statistic, n_resamples, rng)
    return _build_result(
        point=point,
        boot=boot,
        confidence=confidence,
        method=method,
        n_resamples=n_resamples,
        jackknife=lambda: _jackknife_two_sample(arr_a, arr_b, statistic),
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _diff_in_means(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(a) - np.mean(b))


def _as_array(data: np.ndarray | pd.Series) -> np.ndarray:
    arr = np.asarray(data, dtype=float)
    return arr[~np.isnan(arr)]


def _bootstrap_distribution_one_sample(
    arr: np.ndarray,
    statistic: Callable[[np.ndarray], float],
    n_resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    n = arr.size
    out = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sample = arr[rng.integers(0, n, size=n)]
        out[i] = float(statistic(sample))
    return out


def _bootstrap_distribution_two_sample(
    a: np.ndarray,
    b: np.ndarray,
    statistic: Callable[[np.ndarray, np.ndarray], float],
    n_resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    na, nb = a.size, b.size
    out = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sa = a[rng.integers(0, na, size=na)]
        sb = b[rng.integers(0, nb, size=nb)]
        out[i] = float(statistic(sa, sb))
    return out


def _jackknife_one_sample(
    arr: np.ndarray, statistic: Callable[[np.ndarray], float]
) -> np.ndarray:
    n = arr.size
    out = np.empty(n, dtype=float)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        mask[i] = False
        out[i] = float(statistic(arr[mask]))
        mask[i] = True
    return out


def _jackknife_two_sample(
    a: np.ndarray,
    b: np.ndarray,
    statistic: Callable[[np.ndarray, np.ndarray], float],
) -> np.ndarray:
    """Leave-one-out jackknife over the concatenated sample.

    Following Efron & Tibshirani, for a two-sample statistic the BCa
    acceleration is computed from leave-one-out replications across both
    samples, treating the concatenation as a single index space.
    """

    na, nb = a.size, b.size
    out = np.empty(na + nb, dtype=float)
    mask_a = np.ones(na, dtype=bool)
    for i in range(na):
        mask_a[i] = False
        out[i] = float(statistic(a[mask_a], b))
        mask_a[i] = True
    mask_b = np.ones(nb, dtype=bool)
    for i in range(nb):
        mask_b[i] = False
        out[na + i] = float(statistic(a, b[mask_b]))
        mask_b[i] = True
    return out


def _build_result(
    *,
    point: float,
    boot: np.ndarray,
    confidence: float,
    method: str,
    n_resamples: int,
    jackknife: Callable[[], np.ndarray],
) -> BootstrapResult:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1).")

    boot = np.asarray(boot, dtype=float)
    boot = boot[~np.isnan(boot)]
    if boot.size == 0:
        raise ValueError("Bootstrap distribution is empty after filtering NaNs.")

    alpha = (1 - confidence) / 2.0

    if method == "percentile":
        ci_low = float(np.percentile(boot, 100 * alpha))
        ci_high = float(np.percentile(boot, 100 * (1 - alpha)))
    elif method == "basic":
        # Basic / pivotal: 2*theta_hat - q_{1-alpha}, 2*theta_hat - q_{alpha}
        q_low = float(np.percentile(boot, 100 * alpha))
        q_high = float(np.percentile(boot, 100 * (1 - alpha)))
        ci_low = 2 * point - q_high
        ci_high = 2 * point - q_low
    elif method == "bca":
        ci_low, ci_high = _bca_interval(
            point=point,
            boot=boot,
            confidence=confidence,
            jackknife=jackknife,
        )
    else:
        raise ValueError(f"Unknown bootstrap method: {method!r}")

    standard_error = float(boot.std(ddof=1)) if boot.size > 1 else 0.0
    bias = float(boot.mean() - point)

    return BootstrapResult(
        statistic_value=point,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        confidence=float(confidence),
        method=method,
        n_resamples=int(n_resamples),
        bootstrap_distribution=boot[:_DISTRIBUTION_KEEP].tolist(),
        standard_error=standard_error,
        bias=bias,
    )


def _bca_interval(
    *,
    point: float,
    boot: np.ndarray,
    confidence: float,
    jackknife: Callable[[], np.ndarray],
) -> tuple[float, float]:
    """Bias-corrected and accelerated CI (BCa).

    z0 is the bias-correction from the proportion of bootstrap replications
    below the point estimate; a is the acceleration derived from the jackknife
    skewness.
    """

    alpha = (1 - confidence) / 2.0
    # Bias-correction
    prop_below = float(np.mean(boot < point))
    # Guard against 0 / 1 which would push z0 to +/- inf.
    prop_below = min(max(prop_below, 1e-9), 1 - 1e-9)
    z0 = float(stats.norm.ppf(prop_below))

    # Acceleration via jackknife
    try:
        jk = jackknife()
    except Exception:
        jk = np.array([], dtype=float)
    a = 0.0
    if jk.size > 1:
        jk_mean = float(jk.mean())
        diffs = jk_mean - jk
        num = float(np.sum(diffs ** 3))
        den = 6.0 * (float(np.sum(diffs ** 2)) ** 1.5)
        if den > 0:
            a = num / den

    z_alpha_lo = float(stats.norm.ppf(alpha))
    z_alpha_hi = float(stats.norm.ppf(1 - alpha))

    def _adjusted(z_a: float) -> float:
        denom = 1 - a * (z0 + z_a)
        # Avoid blow-up if acceleration pushes denom to 0.
        if abs(denom) < 1e-12:
            denom = np.sign(denom) * 1e-12 if denom != 0 else 1e-12
        return float(stats.norm.cdf(z0 + (z0 + z_a) / denom))

    a1 = _adjusted(z_alpha_lo)
    a2 = _adjusted(z_alpha_hi)

    # Clip percentiles to valid range to keep np.percentile happy.
    a1 = min(max(a1, 1e-6), 1 - 1e-6)
    a2 = min(max(a2, 1e-6), 1 - 1e-6)

    ci_low = float(np.percentile(boot, 100 * min(a1, a2)))
    ci_high = float(np.percentile(boot, 100 * max(a1, a2)))
    return ci_low, ci_high


__all__ = [
    "bootstrap_ci",
    "bootstrap_two_sample",
    "BootstrapResult",
]
