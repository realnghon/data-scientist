"""Tests for ``ds_skill.survival``."""

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.survival import (  # noqa: E402
    LogRankResult,
    SurvivalCurve,
    WeibullFit,
    fit_weibull,
    kaplan_meier,
    kaplan_meier_by_group,
    log_rank_test,
)


def test_kaplan_meier_uncensored_matches_empirical_survival():
    # All events observed -> KM curve is just 1 - ECDF at each time.
    durations = pd.Series([1, 2, 2, 3, 4, 5])
    events = pd.Series([1, 1, 1, 1, 1, 1])
    curve = kaplan_meier(durations, events)
    assert isinstance(curve, SurvivalCurve)
    # After all events, survival must be 0.
    assert curve.survival_probability[-1] == pytest.approx(0.0)
    # After the first event (t=1) of n=6, S = 5/6.
    assert curve.survival_probability[0] == pytest.approx(5 / 6)
    # After t=2 (two events): S = (5/6) * (3/5) = 1/2.
    assert curve.survival_probability[1] == pytest.approx(0.5)


def test_kaplan_meier_ci_bounds_survival_in_unit_interval():
    rng = np.random.default_rng(0)
    durations = pd.Series(rng.exponential(5, size=50))
    events = pd.Series(rng.binomial(1, 0.7, size=50))
    curve = kaplan_meier(durations, events)
    for lo, s, hi in zip(curve.ci_low, curve.survival_probability, curve.ci_high):
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0
        assert lo <= s + 1e-9
        assert s <= hi + 1e-9


def test_kaplan_meier_by_group_returns_curve_per_group():
    df = pd.DataFrame(
        {
            "t": [1, 2, 3, 1, 2, 3],
            "e": [1, 1, 1, 1, 1, 1],
            "g": ["A", "A", "A", "B", "B", "B"],
        }
    )
    curves = kaplan_meier_by_group(df, "t", "e", "g")
    assert set(curves.keys()) == {"A", "B"}
    for c in curves.values():
        assert isinstance(c, SurvivalCurve)
        assert c.survival_probability[-1] == pytest.approx(0.0)


def test_log_rank_detects_known_group_difference():
    rng = np.random.default_rng(0)
    n = 80
    df = pd.DataFrame(
        {
            "t": np.r_[rng.exponential(2, n), rng.exponential(8, n)],
            "e": np.ones(2 * n, dtype=int),
            "g": ["fast"] * n + ["slow"] * n,
        }
    )
    result = log_rank_test(df, "t", "e", "g")
    assert isinstance(result, LogRankResult)
    assert result.degrees_of_freedom == 1
    assert result.p_value < 0.05
    assert result.chi_square > 0


def test_log_rank_fails_to_reject_on_identical_groups():
    rng = np.random.default_rng(3)
    n = 60
    times = rng.exponential(5, n)
    df = pd.DataFrame(
        {
            "t": np.r_[times, times],
            "e": np.ones(2 * n, dtype=int),
            "g": ["A"] * n + ["B"] * n,
        }
    )
    result = log_rank_test(df, "t", "e", "g")
    # Identical samples -> chi-square should be exactly 0 (or numerically tiny)
    # and p-value far from significant.
    assert result.chi_square < 1e-6
    assert result.p_value > 0.5


def test_fit_weibull_shape_greater_than_one_on_wear_out_data():
    # Weibull with shape=3 has increasing hazard (wear-out).
    rng = np.random.default_rng(42)
    n = 500
    shape_true = 3.0
    scale_true = 10.0
    u = rng.uniform(0, 1, n)
    times = scale_true * (-np.log(1 - u)) ** (1 / shape_true)
    durations = pd.Series(times)
    events = pd.Series(np.ones(n, dtype=int))
    fit = fit_weibull(durations, events)
    assert isinstance(fit, WeibullFit)
    assert fit.shape > 1.5
    assert "wear-out" in fit.interpretation


def test_fit_weibull_b50_close_to_empirical_median():
    rng = np.random.default_rng(7)
    n = 800
    shape_true = 2.0
    scale_true = 12.0
    u = rng.uniform(0, 1, n)
    times = scale_true * (-np.log(1 - u)) ** (1 / shape_true)
    durations = pd.Series(times)
    events = pd.Series(np.ones(n, dtype=int))
    fit = fit_weibull(durations, events)
    empirical_median = float(np.median(times))
    # B50 should land within ~15% of the empirical median.
    assert abs(fit.b50 - empirical_median) / empirical_median < 0.15


def test_dataclasses_as_dict_are_json_serializable():
    durations = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    events = pd.Series([1, 1, 1, 0, 1])
    curve = kaplan_meier(durations, events)
    json.dumps(curve.as_dict())

    df = pd.DataFrame(
        {"t": [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
         "e": [1, 1, 1, 1, 1, 1],
         "g": ["A", "A", "A", "B", "B", "B"]}
    )
    lr = log_rank_test(df, "t", "e", "g")
    json.dumps(lr.as_dict())

    fit = fit_weibull(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
                      pd.Series([1, 1, 1, 1, 1, 1, 1, 1]))
    json.dumps(fit.as_dict())


def test_survival_helpers_reject_invalid_inputs():
    with pytest.raises(ValueError):
        kaplan_meier(pd.Series([], dtype=float), pd.Series([], dtype=int))
    with pytest.raises(ValueError):
        log_rank_test(pd.DataFrame({"t": [], "e": [], "g": []}), "t", "e", "g")
    with pytest.raises(ValueError):
        fit_weibull(pd.Series([1.0, 2.0]), pd.Series([0, 0]))  # no events
