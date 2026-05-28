"""Tests for ds_skill.spc — control charts, run rules, capability indices."""

from __future__ import annotations

from pathlib import Path
import math
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.spc import (  # noqa: E402
    CapabilityResult,
    ControlChart,
    RuleViolation,
    apply_nelson_rules,
    apply_western_electric_rules,
    c_chart,
    capability_summary,
    cp,
    cpk,
    individuals_mr_chart,
    p_chart,
    pp,
    ppk,
    u_chart,
    xbar_r_chart,
)


# ---------------------------------------------------------------------------
# Chart construction
# ---------------------------------------------------------------------------


def test_xbar_r_chart_matches_textbook_limits():
    """Hand-computed n=5 example.

    Subgroups all have mean 10 except one with mean 12; ranges are
    constant at 2. R-bar = 2, A2(5) = 0.577, so UCL = X-double-bar +
    0.577 * 2 = X-double-bar + 1.154.
    """

    # 5 subgroups of size 5; controlled construction:
    # subgroup k has values [k_mean - 1, k_mean - 0.5, k_mean, k_mean + 0.5, k_mean + 1]
    subgroups = []
    means = [10.0, 10.0, 12.0, 10.0, 10.0]
    for k, m in enumerate(means):
        for v in [m - 1.0, m - 0.5, m, m + 0.5, m + 1.0]:
            subgroups.append({"sg": k, "x": v})
    df = pd.DataFrame(subgroups)

    chart = xbar_r_chart(df, value_col="x", subgroup_col="sg")

    assert chart.chart_type == "xbar_r"
    assert chart.subgroup_size == 5
    assert chart.points == pytest.approx(means)
    expected_x_double_bar = float(np.mean(means))
    assert chart.center_line == pytest.approx(expected_x_double_bar)
    # R = max - min = 2 for every subgroup
    assert chart.extras["r_bar"] == pytest.approx(2.0)
    assert chart.ucl == pytest.approx(expected_x_double_bar + 0.577 * 2.0)
    assert chart.lcl == pytest.approx(expected_x_double_bar - 0.577 * 2.0)
    # sigma_within = R-bar / d2(5) = 2 / 2.326
    assert chart.sigma == pytest.approx(2.0 / 2.326, rel=1e-3)


def test_individuals_mr_chart_limits_match_e2_formula():
    """I-MR limits = mean +/- E2 * MR-bar where E2(2) = 2.660."""

    values = [10.0, 11.0, 10.5, 9.5, 10.2, 10.8, 9.8, 10.1]
    df = pd.DataFrame({"x": values, "t": range(len(values))})

    chart = individuals_mr_chart(df, value_col="x", time_col="t")

    mean = float(np.mean(values))
    mr_bar = float(np.mean(np.abs(np.diff(values))))
    expected_ucl = mean + 2.660 * mr_bar
    expected_lcl = mean - 2.660 * mr_bar

    assert chart.chart_type == "individuals_mr"
    assert chart.subgroup_size == 1
    assert chart.center_line == pytest.approx(mean)
    assert chart.ucl == pytest.approx(expected_ucl, rel=1e-6)
    assert chart.lcl == pytest.approx(expected_lcl, rel=1e-6)
    assert chart.extras["mr_bar"] == pytest.approx(mr_bar)
    # sigma_within = MR-bar / d2(2) = MR-bar / 1.128
    assert chart.sigma == pytest.approx(mr_bar / 1.128, rel=1e-4)


def test_p_chart_matches_binomial_limits():
    """p-chart: p-bar = total defects / total sampled.

    Constant n = 100, defect counts [5, 4, 6, 5, 5, 4, 6, 5, 5, 5] ->
    p-bar = 50/1000 = 0.05; sigma = sqrt(0.05*0.95/100) ~= 0.02179.
    """

    defects = [5, 4, 6, 5, 5, 4, 6, 5, 5, 5]
    df = pd.DataFrame({"d": defects, "n": [100] * len(defects)})

    chart = p_chart(df, defect_col="d", sample_size_col="n")

    assert chart.chart_type == "p"
    assert chart.subgroup_size == 100
    assert chart.center_line == pytest.approx(0.05)
    sigma = math.sqrt(0.05 * 0.95 / 100)
    assert chart.ucl == pytest.approx(0.05 + 3 * sigma)
    assert chart.lcl == pytest.approx(max(0.0, 0.05 - 3 * sigma))
    # All points equal to defects / 100
    assert chart.points == pytest.approx([d / 100 for d in defects])


def test_p_chart_variable_size_produces_per_point_limits():
    df = pd.DataFrame(
        {
            "d": [3, 8, 5, 4, 6],
            "n": [100, 200, 150, 100, 120],
        }
    )
    chart = p_chart(df, defect_col="d", sample_size_col="n")
    assert isinstance(chart.subgroup_size, list)
    assert chart.variable_limits is not None
    assert len(chart.variable_limits) == 5
    # Larger n -> tighter limits
    # index 1 has n=200 (largest), index 0 and 3 have n=100 (smallest)
    ucl_largest_n = chart.variable_limits[1][1]
    ucl_smallest_n = chart.variable_limits[0][1]
    assert ucl_largest_n < ucl_smallest_n


def test_c_chart_uses_poisson_limits():
    """c-bar = mean(counts); sigma = sqrt(c-bar)."""

    counts = [5, 4, 6, 5, 5, 4, 6, 5, 5, 5]
    df = pd.DataFrame({"d": counts})
    chart = c_chart(df, defect_count_col="d")

    c_bar = float(np.mean(counts))
    assert chart.chart_type == "c"
    assert chart.center_line == pytest.approx(c_bar)
    assert chart.ucl == pytest.approx(c_bar + 3 * math.sqrt(c_bar))
    assert chart.lcl == pytest.approx(max(0.0, c_bar - 3 * math.sqrt(c_bar)))


def test_u_chart_normalizes_by_opportunity():
    df = pd.DataFrame(
        {
            "d": [5, 8, 3, 6, 4],
            "opp": [10, 20, 10, 15, 10],
        }
    )
    chart = u_chart(df, defect_count_col="d", opportunities_col="opp")

    u_bar_expected = (5 + 8 + 3 + 6 + 4) / (10 + 20 + 10 + 15 + 10)
    assert chart.center_line == pytest.approx(u_bar_expected)
    assert chart.points == pytest.approx([5 / 10, 8 / 20, 3 / 10, 6 / 15, 4 / 10])
    # Variable opportunity -> variable limits filled
    assert chart.variable_limits is not None


# ---------------------------------------------------------------------------
# Western Electric rules
# ---------------------------------------------------------------------------


def _fake_chart(points: list[float], cl: float = 0.0, ucl: float = 3.0) -> ControlChart:
    """Construct a chart object directly for rule-testing.

    sigma is implicit at (UCL - CL) / 3 = 1, so 1-sigma=1, 2-sigma=2, 3-sigma=3.
    """

    return ControlChart(
        chart_type="test",
        points=list(points),
        center_line=cl,
        ucl=ucl,
        lcl=-ucl,
        subgroup_size=1,
        sigma=(ucl - cl) / 3.0,
    )


def test_western_electric_rule_1_detects_out_of_control_point():
    chart = _fake_chart([0.0, 0.5, 4.0, -0.2, 0.1])  # index 2 is > 3-sigma
    apply_western_electric_rules(chart)
    rule_ids = [v.rule_id for v in chart.violations]
    we1 = next(v for v in chart.violations if v.rule_id == "WE-1")
    assert "WE-1" in rule_ids
    assert 2 in we1.affected_points
    # Also a negative spike
    chart2 = _fake_chart([0.0, -3.5, 0.1])
    apply_western_electric_rules(chart2)
    assert any(v.rule_id == "WE-1" for v in chart2.violations)


def test_western_electric_rule_4_detects_8_point_run():
    # 8 consecutive points above centerline
    points = [0.5] * 8 + [-0.5]
    chart = _fake_chart(points)
    apply_western_electric_rules(chart)
    we4 = next((v for v in chart.violations if v.rule_id == "WE-4"), None)
    assert we4 is not None
    # First 8 indices should be flagged
    assert set(range(8)).issubset(set(we4.affected_points))

    # 7 points should not trip rule 4
    chart_short = _fake_chart([0.5] * 7)
    apply_western_electric_rules(chart_short)
    assert not any(v.rule_id == "WE-4" for v in chart_short.violations)


def test_western_electric_rule_2_detects_two_of_three_beyond_2_sigma():
    # Two of three points beyond +2 sigma on same side
    chart = _fake_chart([2.5, 0.0, 2.3, 0.5, 0.5])
    apply_western_electric_rules(chart)
    assert any(v.rule_id == "WE-2" for v in chart.violations)


# ---------------------------------------------------------------------------
# Nelson rules
# ---------------------------------------------------------------------------


def test_nelson_rule_2_detects_9_point_run():
    """Nelson rule 2 fires on 9 consecutive points on the same side."""

    chart = _fake_chart([0.3] * 9 + [-0.1])
    apply_nelson_rules(chart)
    n2 = next((v for v in chart.violations if v.rule_id == "Nelson-2"), None)
    assert n2 is not None
    assert set(range(9)).issubset(set(n2.affected_points))

    # 8-point run does NOT trip Nelson-2 (would trip WE-4 instead)
    chart_short = _fake_chart([0.3] * 8)
    apply_nelson_rules(chart_short)
    assert not any(v.rule_id == "Nelson-2" for v in chart_short.violations)


def test_nelson_rule_3_detects_six_point_increase():
    points = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, -0.1]
    chart = _fake_chart(points)
    apply_nelson_rules(chart)
    assert any(v.rule_id == "Nelson-3" for v in chart.violations)


def test_nelson_rule_4_detects_alternating_run():
    # 14 alternating points
    points = [(-1) ** i * 0.3 for i in range(14)]
    chart = _fake_chart(points)
    apply_nelson_rules(chart)
    assert any(v.rule_id == "Nelson-4" for v in chart.violations)


# ---------------------------------------------------------------------------
# Capability indices
# ---------------------------------------------------------------------------


def test_cp_calculation_matches_textbook():
    """USL=10, LSL=2, sigma=1 -> Cp = (10-2)/(6*1) = 1.333..."""

    # Use sigma_short_term to override estimation
    values = [6.0] * 50  # values don't matter when sigma is supplied
    result = cp(values, lsl=2.0, usl=10.0, sigma_short_term=1.0)
    assert result == pytest.approx(8.0 / 6.0)


def test_cpk_smaller_than_cp_when_off_center():
    rng = np.random.default_rng(0)
    # Process centered at 7 instead of midpoint 6 between 2 and 10
    values = rng.normal(loc=7.0, scale=1.0, size=200)
    cp_val = cp(values, lsl=2.0, usl=10.0, sigma_short_term=1.0)
    cpk_val = cpk(values, lsl=2.0, usl=10.0, sigma_short_term=1.0)
    assert cpk_val < cp_val
    # And specifically, Cpk = min((10-mu)/3, (mu-2)/3) which approaches 1.0
    # when mu approaches 7. With sample noise it sits near 1.0.
    assert cpk_val == pytest.approx(1.0, abs=0.05)


def test_ppk_uses_long_term_std():
    """Ppk uses overall sample std, not short-term MR-based sigma.

    Construct data where the overall std is much larger than the
    moving-range short-term sigma (random shuffling versus near-sorted).
    """

    rng = np.random.default_rng(42)
    values = rng.normal(loc=10.0, scale=2.0, size=200)
    # ensure both indices exist
    pp_val = pp(values, lsl=4.0, usl=16.0)
    ppk_val = ppk(values, lsl=4.0, usl=16.0)
    expected_sigma_long = float(np.std(values, ddof=1))
    expected_pp = (16.0 - 4.0) / (6.0 * expected_sigma_long)
    assert pp_val == pytest.approx(expected_pp)
    # Ppk explicitly: min((USL-mu)/(3*sigma), (mu-LSL)/(3*sigma))
    mu = float(np.mean(values))
    expected_ppk = min(
        (16.0 - mu) / (3.0 * expected_sigma_long),
        (mu - 4.0) / (3.0 * expected_sigma_long),
    )
    assert ppk_val == pytest.approx(expected_ppk)


def test_capability_summary_warns_when_n_under_30():
    rng = np.random.default_rng(7)
    small = rng.normal(loc=10.0, scale=1.0, size=20)
    result = capability_summary(small, lsl=4.0, usl=16.0, name="diameter")
    assert isinstance(result, CapabilityResult)
    assert result.min_n_warning is True
    assert result.name == "diameter"

    large = rng.normal(loc=10.0, scale=1.0, size=100)
    result_big = capability_summary(large, lsl=4.0, usl=16.0)
    assert result_big.min_n_warning is False


def test_capability_interpretation_thresholds():
    """Check interpretation buckets at threshold boundaries."""

    # Force sigma=1, lsl/usl positioned to land in each bucket exactly
    # Cpk = min((USL-mu)/3, (mu-LSL)/3). Use symmetric spec.
    rng = np.random.default_rng(0)
    values = rng.normal(loc=10.0, scale=1.0, size=200)
    # Force Cpk just below 1.0 by supplying a tight spec
    # Tight spec: LSL=8, USL=12 -> Cpk ~ (2)/(3*sigma_short)
    res_marginal = capability_summary(values, lsl=8.0, usl=12.0)
    # Wide spec for "strong"
    res_strong = capability_summary(values, lsl=1.0, usl=19.0)
    assert res_strong.interpretation == "strong"
    assert res_strong.cpk > 1.67
    assert res_marginal.interpretation in {"adequate", "marginal", "incapable"}


# ---------------------------------------------------------------------------
# Validation / edge cases
# ---------------------------------------------------------------------------


def test_subgroup_size_outside_2_to_10_raises():
    # n = 11 is unsupported
    rows = []
    for sg in range(3):
        for _ in range(11):
            rows.append({"sg": sg, "x": 1.0})
    df = pd.DataFrame(rows)
    with pytest.raises(ValueError, match="outside the supported range"):
        xbar_r_chart(df, value_col="x", subgroup_col="sg")


def test_xbar_r_requires_constant_subgroup_size():
    df = pd.DataFrame(
        {
            "sg": [0, 0, 1, 1, 1],
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    with pytest.raises(ValueError, match="constant subgroup size"):
        xbar_r_chart(df, value_col="x", subgroup_col="sg")


def test_empty_input_raises():
    df = pd.DataFrame({"x": [], "sg": []})
    with pytest.raises(ValueError):
        xbar_r_chart(df, value_col="x", subgroup_col="sg")


def test_capability_requires_at_least_one_limit():
    with pytest.raises(ValueError, match="LSL or USL"):
        capability_summary([1.0, 2.0, 3.0], lsl=None, usl=None)


def test_cp_requires_both_limits():
    with pytest.raises(ValueError):
        cp([1.0, 2.0, 3.0], lsl=None, usl=10.0)


def test_control_chart_as_dict_is_json_friendly():
    df = pd.DataFrame({"x": list(range(10)), "t": range(10)})
    chart = individuals_mr_chart(df, value_col="x", time_col="t")
    apply_western_electric_rules(chart)
    d = chart.as_dict()
    # Basic sanity: required keys present
    for key in ["chart_type", "points", "center_line", "ucl", "lcl", "violations"]:
        assert key in d
    # All violations also serializable
    assert isinstance(d["violations"], list)
