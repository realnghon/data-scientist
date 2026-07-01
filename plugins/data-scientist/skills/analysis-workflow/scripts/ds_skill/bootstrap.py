"""Non-parametric bootstrap confidence intervals.

Wraps :func:`scipy.stats.bootstrap` so callers get properly bias-corrected and
accelerated (BCa) intervals for an arbitrary statistic without re-deriving the
acceleration term by hand. Percentile and basic intervals are also exposed for
cases where BCa is not appropriate (e.g. a statistic with a hard boundary that
the jackknife acceleration handles poorly).

BCa is the default because it corrects for both bias and skew in the bootstrap
distribution and is second-order accurate, which matters most on the small
samples this skill is frequently pointed at.

All public functions return dicts (not dataclasses) to minimize calling overhead.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np


_SUPPORTED_METHODS = {"BCa", "percentile", "basic"}


def bootstrap_ci(
    data: Sequence[float] | np.ndarray,
    statistic_fn: Callable[[np.ndarray], float] = np.mean,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    method: str = "BCa",
    random_state: int | None = 0,
) -> dict[str, Any]:
    """Bootstrap CI for a one-sample statistic.

    Parameters
    ----------
    data:
        1-D sample. NaNs are dropped before resampling.
    statistic_fn:
        Callable mapping a 1-D array to a scalar (default: mean). Must accept an
        ``axis`` argument OR be a plain reducer — we wrap it so scipy's vectorized
        resampling works either way.
    n_bootstrap:
        Number of bootstrap resamples (scipy's ``n_resamples``).
    confidence:
        Two-sided confidence level in (0, 1).
    method:
        ``"BCa"`` (default), ``"percentile"``, or ``"basic"``.
    random_state:
        Seed for reproducibility.

    Returns
    -------
    dict with ``point_estimate``, ``ci_low``, ``ci_high``, ``confidence``,
    ``method``, ``n``, ``n_bootstrap``, and ``standard_error``.
    """
    if method not in _SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported method {method!r}. Choose from {sorted(_SUPPORTED_METHODS)}."
        )
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1).")

    values = np.asarray(data, dtype=float)
    values = values[~np.isnan(values)]
    n = int(values.size)
    if n < 2:
        raise ValueError("bootstrap_ci needs at least 2 non-null observations.")

    point_estimate = float(_apply_1d(statistic_fn, values))

    # A degenerate (constant) sample has a zero-width bootstrap distribution;
    # BCa's acceleration term divides by zero, so short-circuit to a point CI.
    if np.ptp(values) == 0:
        return {
            "point_estimate": point_estimate,
            "ci_low": point_estimate,
            "ci_high": point_estimate,
            "confidence": float(confidence),
            "method": method,
            "n": n,
            "n_bootstrap": int(n_bootstrap),
            "standard_error": 0.0,
            "degenerate": True,
        }

    from scipy import stats as _stats

    def _vectorized(sample: np.ndarray, axis: int = -1) -> np.ndarray:
        return np.apply_along_axis(lambda s: _apply_1d(statistic_fn, s), axis, sample)

    res = _stats.bootstrap(
        (values,),
        _vectorized,
        n_resamples=int(n_bootstrap),
        confidence_level=float(confidence),
        method=method.lower() if method != "BCa" else "BCa",
        vectorized=True,
        random_state=random_state,
    )

    ci_low = float(res.confidence_interval.low)
    ci_high = float(res.confidence_interval.high)
    return {
        "point_estimate": point_estimate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence": float(confidence),
        "method": method,
        "n": n,
        "n_bootstrap": int(n_bootstrap),
        "standard_error": float(res.standard_error),
        "degenerate": False,
    }


def bootstrap_diff_ci(
    a: Sequence[float] | np.ndarray,
    b: Sequence[float] | np.ndarray,
    statistic_fn: Callable[[np.ndarray], float] = np.mean,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    method: str = "BCa",
    random_state: int | None = 0,
) -> dict[str, Any]:
    """Bootstrap CI for the difference ``statistic_fn(b) - statistic_fn(a)``.

    Two-sample independent bootstrap (each arm resampled separately). Useful for
    A/B differences of medians, trimmed means, or any statistic where a
    closed-form SE is awkward.
    """
    if method not in _SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported method {method!r}. Choose from {sorted(_SUPPORTED_METHODS)}."
        )
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1).")

    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    a_arr = a_arr[~np.isnan(a_arr)]
    b_arr = b_arr[~np.isnan(b_arr)]
    if a_arr.size < 2 or b_arr.size < 2:
        raise ValueError("bootstrap_diff_ci needs at least 2 observations per arm.")

    point = float(_apply_1d(statistic_fn, b_arr) - _apply_1d(statistic_fn, a_arr))

    from scipy import stats as _stats

    def _diff(x: np.ndarray, y: np.ndarray, axis: int = -1) -> np.ndarray:
        sx = np.apply_along_axis(lambda s: _apply_1d(statistic_fn, s), axis, x)
        sy = np.apply_along_axis(lambda s: _apply_1d(statistic_fn, s), axis, y)
        return sy - sx

    res = _stats.bootstrap(
        (a_arr, b_arr),
        _diff,
        n_resamples=int(n_bootstrap),
        confidence_level=float(confidence),
        method=method.lower() if method != "BCa" else "BCa",
        vectorized=True,
        random_state=random_state,
    )

    return {
        "point_estimate": point,
        "ci_low": float(res.confidence_interval.low),
        "ci_high": float(res.confidence_interval.high),
        "confidence": float(confidence),
        "method": method,
        "n_a": int(a_arr.size),
        "n_b": int(b_arr.size),
        "n_bootstrap": int(n_bootstrap),
        "standard_error": float(res.standard_error),
    }


def _apply_1d(statistic_fn: Callable[..., float], values: np.ndarray) -> float:
    """Call ``statistic_fn`` on a 1-D array, tolerating an ``axis`` kwarg."""
    try:
        return float(statistic_fn(values))
    except TypeError:
        # Some reducers (e.g. functools.partial(np.mean, axis=...)) need axis.
        return float(statistic_fn(values, axis=0))


__all__ = ["bootstrap_ci", "bootstrap_diff_ci"]
