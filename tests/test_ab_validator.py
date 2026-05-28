"""Tests for ds_skill.ab_validator."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill.ab_validator import (  # noqa: E402
    ABValidationReport,
    effect_size_with_ci,
    minimum_detectable_effect,
    sample_ratio_mismatch,
    validate_ab_test,
)


def test_srm_passes_on_balanced_split():
    rep = sample_ratio_mismatch({"A": 5000, "B": 5020})
    assert rep["passed"] is True
    assert rep["p_value"] > 0.001
    assert math.isclose(sum(rep["observed_ratios"].values()), 1.0, abs_tol=1e-9)


def test_srm_fails_on_imbalanced_split():
    rep = sample_ratio_mismatch({"A": 6000, "B": 4000})
    assert rep["passed"] is False
    assert rep["p_value"] < 0.001


def test_srm_respects_expected_ratios():
    # 60/40 traffic is by design — should pass when expected ratios match
    rep = sample_ratio_mismatch(
        {"A": 6000, "B": 4000}, expected_ratios={"A": 0.6, "B": 0.4}
    )
    assert rep["passed"] is True


def test_cohens_d_matches_manual_calc():
    rng = np.random.default_rng(0)
    a = rng.normal(loc=0.0, scale=1.0, size=200)
    b = rng.normal(loc=0.5, scale=1.0, size=200)
    out = effect_size_with_ci(a, b, metric="mean")
    # expect d ~ 0.5
    assert abs(out["cohens_d"] - 0.5) < 0.2
    # CI should be on the difference (b - a)
    assert out["ci_low"] < out["difference"] < out["ci_high"]


def test_risk_difference_for_binary():
    a = np.array([0] * 90 + [1] * 10, dtype=float)  # 10%
    b = np.array([0] * 80 + [1] * 20, dtype=float)  # 20%
    out = effect_size_with_ci(a, b, metric="proportion")
    assert abs(out["risk_difference"] - 0.10) < 1e-9
    assert abs(out["relative_risk"] - 2.0) < 1e-9
    assert out["odds_ratio"] > 1.0
    assert out["ci_low"] < out["risk_difference"] < out["ci_high"]


def test_mde_for_proportion():
    mde = minimum_detectable_effect(0.10, n_per_group=10000, metric="proportion")
    # at n=10k baseline 10%, MDE for 5% alpha 80% power ~ 0.012
    assert 0.01 < mde < 0.02


def test_mde_for_continuous():
    # baseline interpreted as SD; MDE proportional to SD/sqrt(n)
    mde_small = minimum_detectable_effect(1.0, n_per_group=100, metric="mean")
    mde_large = minimum_detectable_effect(1.0, n_per_group=10000, metric="mean")
    assert mde_small > mde_large
    # ratio ~ sqrt(100) = 10
    assert 8 < (mde_small / mde_large) < 12


def test_validate_ab_test_full_integration():
    rng = np.random.default_rng(1)
    df = pd.DataFrame(
        {
            "arm": ["A"] * 1000 + ["B"] * 1000,
            "converted": np.concatenate(
                [
                    rng.binomial(1, 0.10, 1000),
                    rng.binomial(1, 0.13, 1000),
                ]
            ),
        }
    )
    rep = validate_ab_test(df, group_col="arm", outcome_col="converted")
    assert isinstance(rep, ABValidationReport)
    assert rep.srm["passed"] is True
    assert "A" in rep.groups_summary and "B" in rep.groups_summary
    assert rep.effect_sizes
    assert rep.effect_sizes[0]["metric"] == "proportion"
    assert rep.mde > 0


def test_validate_ab_test_flags_srm():
    df = pd.DataFrame(
        {
            "arm": ["A"] * 6000 + ["B"] * 4000,
            "y": [1] * 6000 + [0] * 4000,
        }
    )
    rep = validate_ab_test(df, group_col="arm", outcome_col="y")
    assert rep.srm["passed"] is False
    assert any("SRM" in w or "sample" in w for w in rep.warnings)
    assert "SRM FAILED" in rep.interpretation


def test_as_dict_json_serializable():
    df = pd.DataFrame(
        {
            "arm": ["A"] * 200 + ["B"] * 200,
            "y": [0, 1] * 200,
        }
    )
    rep = validate_ab_test(df, group_col="arm", outcome_col="y")
    d = rep.as_dict()
    json.dumps(d)  # must not raise


def test_srm_raises_on_bad_input():
    with pytest.raises(ValueError):
        sample_ratio_mismatch({"A": 100})  # only one arm
    with pytest.raises(ValueError):
        sample_ratio_mismatch({"A": 100, "B": 100}, expected_ratios={"A": 0.5, "B": 0.6})
