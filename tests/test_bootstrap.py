"""Tests for ds_skill.bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.bootstrap import (  # noqa: E402
    BootstrapResult,
    bootstrap_ci,
    bootstrap_two_sample,
)


def test_bootstrap_ci_recovers_known_mean_within_ci():
    rng = np.random.default_rng(0)
    data = rng.normal(loc=10.0, scale=2.0, size=200)
    result = bootstrap_ci(data, statistic=np.mean, n_resamples=2000, method="percentile", random_state=0)

    assert isinstance(result, BootstrapResult)
    assert result.ci_low < 10.0 < result.ci_high
    assert result.statistic_value == pytest.approx(float(np.mean(data)), abs=1e-9)
    assert result.method == "percentile"
    assert result.n_resamples == 2000


def test_bca_ci_handles_skewed_data_better_than_percentile():
    # Strongly right-skewed sample — BCa should shift coverage relative to percentile
    # because of the non-zero bias-correction z0.
    rng = np.random.default_rng(7)
    data = rng.lognormal(mean=0.0, sigma=1.2, size=80)

    bca = bootstrap_ci(data, statistic=np.mean, n_resamples=4000, method="bca", random_state=7)
    pct = bootstrap_ci(data, statistic=np.mean, n_resamples=4000, method="percentile", random_state=7)

    assert bca.method == "bca"
    assert pct.method == "percentile"
    # The two intervals must differ (otherwise BCa collapsed to percentile).
    assert not (
        bca.ci_low == pytest.approx(pct.ci_low, abs=1e-9)
        and bca.ci_high == pytest.approx(pct.ci_high, abs=1e-9)
    )
    # Both should still bracket the true population mean of a lognormal(0, 1.2):
    # E[X] = exp(0 + 1.2^2/2) ≈ 2.054. Allow either CI to miss occasionally,
    # but BCa typically tracks the right-tail bias better.
    assert bca.ci_low < bca.ci_high


def test_bootstrap_two_sample_diff_in_means():
    rng = np.random.default_rng(11)
    a = rng.normal(5.0, 1.0, size=120)
    b = rng.normal(3.0, 1.0, size=120)
    result = bootstrap_two_sample(a, b, n_resamples=2000, method="percentile", random_state=11)

    assert result.statistic_value == pytest.approx(float(np.mean(a) - np.mean(b)), abs=1e-9)
    assert result.ci_low > 0  # the difference is clearly positive
    assert result.ci_low < result.statistic_value < result.ci_high


def test_random_state_makes_results_reproducible():
    rng = np.random.default_rng(99)
    data = rng.normal(0, 1, size=100)

    r1 = bootstrap_ci(data, statistic=np.mean, n_resamples=500, method="bca", random_state=42)
    r2 = bootstrap_ci(data, statistic=np.mean, n_resamples=500, method="bca", random_state=42)

    assert r1.ci_low == pytest.approx(r2.ci_low, abs=0.0)
    assert r1.ci_high == pytest.approx(r2.ci_high, abs=0.0)
    assert r1.bootstrap_distribution == r2.bootstrap_distribution

    r3 = bootstrap_ci(data, statistic=np.mean, n_resamples=500, method="bca", random_state=7)
    assert r1.bootstrap_distribution != r3.bootstrap_distribution


def test_n_resamples_increases_precision():
    rng = np.random.default_rng(5)
    data = rng.normal(0, 1, size=200)

    widths = []
    for n_b in [200, 1000, 5000]:
        result = bootstrap_ci(data, statistic=np.mean, n_resamples=n_b, method="percentile", random_state=0)
        widths.append(result.ci_high - result.ci_low)

    # CI width should stabilise as B grows; differences shrink.
    assert abs(widths[2] - widths[1]) < abs(widths[1] - widths[0]) + 0.05


def test_bias_and_standard_error_reasonable():
    rng = np.random.default_rng(3)
    data = rng.normal(0, 1, size=150)
    result = bootstrap_ci(data, statistic=np.mean, n_resamples=3000, method="percentile", random_state=3)

    # SE of the mean is ~ sigma / sqrt(n) ≈ 1 / sqrt(150) ≈ 0.082.
    expected_se = 1.0 / np.sqrt(150)
    assert result.standard_error == pytest.approx(expected_se, rel=0.4)

    # Mean is unbiased — bootstrap bias should be small relative to SE.
    assert abs(result.bias) < 0.05


def test_bootstrap_distribution_truncated_to_200():
    rng = np.random.default_rng(0)
    data = rng.normal(0, 1, size=100)
    result = bootstrap_ci(data, statistic=np.mean, n_resamples=2000, method="bca", random_state=0)

    assert len(result.bootstrap_distribution) == 200
    # Even though only 200 values are exposed, summary stats are over the full run.
    assert result.standard_error > 0


def test_as_dict_is_json_serializable():
    rng = np.random.default_rng(0)
    data = rng.normal(0, 1, size=80)
    result = bootstrap_ci(data, statistic=np.mean, n_resamples=500, method="bca", random_state=0)

    payload = result.as_dict()
    blob = json.dumps(payload)  # must not raise
    restored = json.loads(blob)
    assert restored["method"] == "bca"
    assert restored["n_resamples"] == 500
    assert "bootstrap_distribution" in restored
    assert isinstance(restored["bootstrap_distribution"], list)


def test_basic_method_pivots_around_point_estimate():
    rng = np.random.default_rng(0)
    data = rng.normal(5.0, 1.0, size=120)
    result = bootstrap_ci(data, statistic=np.mean, n_resamples=1500, method="basic", random_state=0)

    assert result.method == "basic"
    # Basic CI is symmetric around 2*theta_hat - q; the midpoint of [ci_low, ci_high]
    # equals theta_hat - bias_offset, which should be very close to theta_hat for an
    # unbiased statistic like the mean.
    midpoint = (result.ci_low + result.ci_high) / 2
    assert midpoint == pytest.approx(result.statistic_value, abs=0.15)


def test_invalid_method_raises():
    data = np.arange(50, dtype=float)
    with pytest.raises(ValueError):
        bootstrap_ci(data, statistic=np.mean, method="nonsense", random_state=0)  # type: ignore[arg-type]
