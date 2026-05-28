"""Tests for ds_skill.time_series."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill import time_series as ts_module  # noqa: E402
from ds_skill.time_series import (  # noqa: E402
    ChangePoints,
    DecompResult,
    SamplingQuality,
    TrendResult,
    detect_change_points,
    mann_kendall_trend,
    sampling_quality,
    seasonal_decompose,
)


def test_mann_kendall_detects_increasing_trend():
    rng = np.random.default_rng(0)
    series = pd.Series(np.arange(50) * 0.5 + rng.normal(0, 0.1, size=50))
    result = mann_kendall_trend(series, alpha=0.05)

    assert isinstance(result, TrendResult)
    assert result.trend == "increasing"
    assert result.significant_at_alpha is True
    assert result.p_value < 0.05
    assert result.tau > 0.5
    assert result.slope_sen > 0.4


def test_mann_kendall_no_trend_on_random_data():
    rng = np.random.default_rng(123)
    series = pd.Series(rng.normal(0, 1, size=80))
    result = mann_kendall_trend(series, alpha=0.05)

    assert result.trend == "no_trend"
    assert result.significant_at_alpha is False


def test_sens_slope_matches_least_squares_on_linear():
    x = np.arange(60)
    series = pd.Series(2.5 * x + 1.0)
    result = mann_kendall_trend(series)

    # On a noiseless linear series, Sen's slope equals OLS slope.
    ols_slope = float(np.polyfit(x, series.to_numpy(), 1)[0])
    assert result.slope_sen == pytest.approx(ols_slope, rel=1e-9, abs=1e-9)
    assert result.slope_sen == pytest.approx(2.5, rel=1e-9, abs=1e-9)


def test_seasonal_decompose_recovers_known_period():
    period = 12
    n = 6 * period
    t = np.arange(n)
    seasonal_truth = 5 * np.sin(2 * np.pi * t / period)
    trend_truth = 0.05 * t
    rng = np.random.default_rng(42)
    series = pd.Series(trend_truth + seasonal_truth + rng.normal(0, 0.2, size=n))

    result = seasonal_decompose(series)
    assert isinstance(result, DecompResult)
    assert result.period_used == period or abs(result.period_used - period) <= 1

    seasonal = np.asarray(result.seasonal)
    # The recovered seasonal should strongly correlate with the truth.
    corr = float(np.corrcoef(seasonal, seasonal_truth)[0, 1])
    assert corr > 0.9


def test_cusum_change_point_detects_known_shift():
    rng = np.random.default_rng(7)
    a = rng.normal(0.0, 0.5, size=60)
    b = rng.normal(3.0, 0.5, size=60)
    series = pd.Series(np.concatenate([a, b]))

    result = detect_change_points(series, method="cusum", min_size=10)
    assert isinstance(result, ChangePoints)
    assert result.method == "cusum"
    assert len(result.change_indices) >= 1
    # The dominant change point should be near index 60.
    nearest = min(result.change_indices, key=lambda i: abs(i - 60))
    assert abs(nearest - 60) <= 5
    assert len(result.confidence) == len(result.change_indices)
    assert len(result.segments) == len(result.change_indices) + 1


def test_binary_segmentation_finds_multiple_change_points():
    rng = np.random.default_rng(2024)
    a = rng.normal(0.0, 0.3, size=40)
    b = rng.normal(4.0, 0.3, size=40)
    c = rng.normal(1.0, 0.3, size=40)
    series = pd.Series(np.concatenate([a, b, c]))

    result = detect_change_points(series, method="binary_segmentation", min_size=10)
    assert result.method == "binary_segmentation"
    assert len(result.change_indices) >= 2

    expected = [40, 80]
    for target in expected:
        nearest = min(result.change_indices, key=lambda i: abs(i - target))
        assert abs(nearest - target) <= 6


def test_sampling_quality_flags_irregular():
    rng = np.random.default_rng(0)
    base = pd.Timestamp("2026-01-01")
    # Half the gaps are 1 minute, half are 5 minutes — CV well above 0.2.
    gaps = np.array(
        [60] * 20 + [300] * 20, dtype=float
    )
    rng.shuffle(gaps)
    seconds = np.cumsum(np.concatenate([[0], gaps]))
    timestamps = pd.Series([base + pd.Timedelta(seconds=int(s)) for s in seconds])

    result = sampling_quality(timestamps)
    assert isinstance(result, SamplingQuality)
    assert result.irregular is True
    assert "irregular" in result.recommendation.lower() or "resample" in result.recommendation.lower()
    assert result.n_samples == len(timestamps)


def test_sampling_quality_detects_gaps():
    base = pd.Timestamp("2026-01-01")
    # 40 regular 1-minute samples, then a 30-minute jump, then 10 more.
    regular = [base + pd.Timedelta(minutes=i) for i in range(40)]
    after_gap = [base + pd.Timedelta(minutes=40 + 30 + i) for i in range(10)]
    timestamps = pd.Series(regular + after_gap)

    result = sampling_quality(timestamps)
    assert len(result.gaps) == 1
    gap = result.gaps[0]
    assert gap["size_intervals"] >= 5
    assert gap["start"] < gap["end"]


def test_decompose_falls_back_when_statsmodels_missing(monkeypatch):
    period = 6
    n = 4 * period
    t = np.arange(n)
    series = pd.Series(2 * np.sin(2 * np.pi * t / period) + 0.01 * t)

    # Simulate ImportError when statsmodels.tsa.seasonal is imported.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("statsmodels"):
            raise ImportError("statsmodels disabled for this test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    result = seasonal_decompose(series, period=period)
    assert isinstance(result, DecompResult)
    assert result.period_used == period
    assert len(result.trend) == n
    assert len(result.seasonal) == n
    assert len(result.residual) == n

    # Fallback decomposition is real: trend + seasonal + residual ~ series.
    reconstructed = np.array(result.trend) + np.array(result.seasonal) + np.array(result.residual)
    assert np.allclose(reconstructed, series.to_numpy(), atol=1e-6)


def test_trend_result_as_dict_round_trips():
    series = pd.Series(np.arange(20, dtype=float))
    payload = mann_kendall_trend(series).as_dict()
    assert set(payload) == {"trend", "tau", "p_value", "slope_sen", "n", "significant_at_alpha"}
    assert payload["trend"] == "increasing"


def test_detect_regime_changes_aliases_detect_change_points():
    # Alias keeps the public API surface advertised in the spec stable.
    assert ts_module.detect_regime_changes is ts_module.detect_change_points
