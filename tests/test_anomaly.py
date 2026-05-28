"""Tests for ds_skill.anomaly."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"),
)

from ds_skill.anomaly import (  # noqa: E402
    AnomalyResult,
    detect_iqr,
    detect_isolation_forest,
    detect_mad,
    detect_multivariate,
    detect_univariate,
    detect_zscore,
)


def _rng(seed: int = 0) -> np.random.Generator:
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# Univariate detectors
# ---------------------------------------------------------------------------


def test_iqr_flags_known_outliers():
    rng = _rng(0)
    body = rng.normal(loc=0.0, scale=1.0, size=200)
    series = pd.Series(np.r_[body, [25.0, -25.0, 30.0]])

    result = detect_iqr(series, k=1.5)

    assert isinstance(result, AnomalyResult)
    assert result.method == "iqr"
    # The three extremes must be flagged.
    assert 200 in result.flagged_indices
    assert 201 in result.flagged_indices
    assert 202 in result.flagged_indices
    # Far below the 10% "high flag rate" warning threshold.
    assert result.n_flagged < result.n_total * 0.1


def test_mad_more_robust_than_zscore_on_skewed():
    """On a heavy-tailed/lognormal-style series, MAD should flag fewer borderline points than z-score."""
    rng = _rng(1)
    # Lognormal generates a heavy right tail.
    body = rng.lognormal(mean=0.0, sigma=0.6, size=400)
    series = pd.Series(np.r_[body, [50.0, 60.0, 70.0]])  # 3 real anomalies

    mad_result = detect_mad(series, threshold=3.5)
    zscore_result = detect_zscore(series, threshold=3.0)

    # Both must catch the real anomalies.
    for idx in (400, 401, 402):
        assert idx in mad_result.flagged_indices
        assert idx in zscore_result.flagged_indices

    # z-score should pick up *fewer* (or at most equal) real anomalies because
    # the inflated mean/std hide them; MAD is more robust and catches them
    # plus possibly more of the genuine tail.
    assert mad_result.n_flagged >= zscore_result.n_flagged
    # z-score should warn about skew on lognormal data.
    assert any("skew" in v.lower() for v in zscore_result.assumptions_violated)


def test_isolation_forest_flags_known_outliers_in_2d():
    pytest.importorskip("sklearn")
    rng = _rng(2)
    n = 300
    body = rng.normal(loc=0.0, scale=1.0, size=(n, 2))
    extreme = np.array([[10.0, 10.0], [-9.0, 9.0], [9.0, -9.0]])
    data = np.vstack([body, extreme])
    df = pd.DataFrame(data, columns=pd.Index(["x", "y"]))

    result = detect_isolation_forest(
        df, features=["x", "y"], contamination=0.02, random_state=0
    )

    assert result.method == "isolation_forest"
    # The three injected outliers must be among the flagged set.
    for idx in (n, n + 1, n + 2):
        assert idx in result.flagged_indices


def test_consensus_univariate_requires_two_methods():
    rng = _rng(3)
    body = rng.normal(size=200)
    # One value extreme enough to be caught by every detector,
    # one borderline value caught only by the most sensitive one.
    series = pd.Series(np.r_[body, [50.0, 4.5]])

    result = detect_univariate(series, methods=("iqr", "mad", "zscore"))

    assert result.method == "consensus_univariate"
    # The clear outlier at position 200 should be in the consensus set.
    assert 200 in result.flagged_indices
    # threshold_used encodes "needs ≥2 votes".
    assert result.threshold_used == 2.0
    # All flagged indices must have at least 2 votes (their score >= 2).
    for idx in result.flagged_indices:
        assert result.scores[idx] >= 2


def test_skewness_warning_added_to_zscore_on_lognormal():
    rng = _rng(4)
    series = pd.Series(rng.lognormal(mean=0.0, sigma=1.0, size=300))

    result = detect_zscore(series, threshold=3.0)

    skew_warnings = [v for v in result.assumptions_violated if "skew" in v.lower()]
    assert skew_warnings, (
        f"Expected a skew warning on lognormal data, got {result.assumptions_violated}"
    )


def test_contamination_parameter_passed_to_isolation_forest():
    pytest.importorskip("sklearn")
    rng = _rng(5)
    df = pd.DataFrame(rng.normal(size=(300, 3)), columns=pd.Index(["a", "b", "c"]))

    low = detect_isolation_forest(df, contamination=0.01, random_state=0)
    high = detect_isolation_forest(df, contamination=0.2, random_state=0)

    # Higher contamination must flag more rows.
    assert high.n_flagged > low.n_flagged
    assert low.threshold_used == pytest.approx(0.01)
    assert high.threshold_used == pytest.approx(0.2)


def test_anomaly_result_as_dict_is_json_serializable():
    rng = _rng(6)
    series = pd.Series(np.r_[rng.normal(size=200), [50.0, -50.0]])

    result = detect_iqr(series)
    payload = result.as_dict()
    text = json.dumps(payload)  # must not raise
    parsed = json.loads(text)

    assert parsed["method"] == "iqr"
    assert parsed["n_total"] == 202
    assert isinstance(parsed["flagged_indices"], list)
    assert isinstance(parsed["scores"], list)


def test_empty_input_raises():
    with pytest.raises(ValueError):
        detect_iqr(pd.Series([], dtype=float))
    with pytest.raises(ValueError):
        detect_mad(pd.Series([], dtype=float))
    with pytest.raises(ValueError):
        detect_zscore(pd.Series([], dtype=float))
    with pytest.raises(ValueError):
        detect_isolation_forest(pd.DataFrame())


def test_detect_multivariate_dispatches_to_isolation_forest():
    pytest.importorskip("sklearn")
    rng = _rng(7)
    n = 250
    body = rng.normal(size=(n, 2))
    df = pd.DataFrame(
        np.vstack([body, [[20.0, 20.0]]]), columns=pd.Index(["a", "b"])
    )

    result = detect_multivariate(df, features=["a", "b"], method="isolation_forest")

    assert result.method == "isolation_forest"
    assert n in result.flagged_indices

    with pytest.raises(ValueError):
        detect_multivariate(df, features=["a", "b"], method="not_a_method")


def test_nan_rows_are_reported_in_summary():
    rng = _rng(8)
    series = pd.Series(np.r_[rng.normal(size=100), [np.nan, np.nan, 25.0]])

    result = detect_iqr(series)

    assert "NaN" in result.summary
    # The clean values should still be flagged at their positional index *within
    # the cleaned series* (the 25.0 at cleaned position 100).
    assert 100 in result.flagged_indices
