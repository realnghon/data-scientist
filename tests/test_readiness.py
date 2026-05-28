"""Tests for ds_skill.readiness — 8-dimension readiness assessor."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.readiness import (  # noqa: E402
    DIMENSION_KEYS,
    DimensionScore,
    ReadinessReport,
    assess_readiness,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _clean_df(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "entity_id": np.arange(n),
            "ts": pd.date_range("2025-01-01", periods=n, freq="D"),
            "machine": (["A", "B", "C"] * ((n // 3) + 1))[:n],
            "temperature": rng.normal(100.0, 5.0, size=n),
            "pressure": rng.normal(50.0, 2.0, size=n),
            "yield_rate": rng.normal(0.95, 0.01, size=n),
        }
    )


# ---------------------------------------------------------------------------
# Per-dimension tests
# ---------------------------------------------------------------------------


def test_sample_size_blocks_when_under_threshold():
    df = pd.DataFrame(
        {
            "machine": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
            "yield_rate": [0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98],
        }
    )
    report = assess_readiness(df, target="yield_rate", group_col="machine")
    dim = report.dimensions["sample_size"]
    assert dim.status == "blocked"
    assert dim.value == 3.0


def test_missingness_partial_when_20_to_50_pct():
    rng = np.random.default_rng(0)
    n = 100
    yield_rate = rng.normal(0.95, 0.01, size=n)
    df = pd.DataFrame(
        {
            "id": np.arange(n),
            "feature_a": rng.normal(0, 1, size=n),
            "feature_b": rng.normal(0, 1, size=n),
            "yield_rate": yield_rate,
        }
    )
    # Drill 30% missingness into feature_a (worst column)
    mask = rng.choice(n, size=30, replace=False)
    df.loc[mask, "feature_a"] = np.nan

    report = assess_readiness(df, target="yield_rate")
    dim = report.dimensions["missingness"]
    assert dim.status == "partial"
    assert 0.0 < float(dim.value) < 0.5


def test_grain_consistency_flags_duplicates():
    df = pd.DataFrame(
        {
            "entity_id": [1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "machine": ["A"] * 10,
            "yield_rate": [0.9] * 10,
        }
    )
    report = assess_readiness(df, target="yield_rate", group_col="entity_id")
    dim = report.dimensions["grain"]
    # 1 duplicate out of 10 -> partial
    assert dim.status in {"partial", "blocked"}
    assert dim.evidence_detail["duplicate_count"] >= 1


def test_time_coverage_ok_when_continuous():
    n = 90
    df = pd.DataFrame(
        {
            "ts": pd.date_range("2025-01-01", periods=n, freq="D"),
            "yield_rate": np.linspace(0.9, 0.95, n),
        }
    )
    report = assess_readiness(df, target="yield_rate", time_col="ts")
    dim = report.dimensions["time_coverage"]
    assert dim.status == "ok"
    assert dim.evidence_detail["cadence"] == "daily"
    assert float(dim.evidence_detail["gap_fraction"]) < 0.10


def test_class_balance_blocked_when_extreme():
    # 200:1 imbalance -> blocked
    df = pd.DataFrame(
        {
            "id": np.arange(201),
            "is_defective": [0] * 200 + [1],
        }
    )
    report = assess_readiness(df, target="is_defective")
    dim = report.dimensions["balance"]
    assert dim.status == "blocked"
    assert float(dim.value) > 100


def test_leakage_detected_when_feature_perfectly_predicts_target():
    n = 50
    rng = np.random.default_rng(1)
    y = rng.normal(0, 1, size=n)
    df = pd.DataFrame(
        {
            "leaky_feature": y * 2.0 + 1.0,  # perfectly correlated
            "noise": rng.normal(0, 1, size=n),
            "yield_rate": y,
        }
    )
    report = assess_readiness(
        df,
        target="yield_rate",
        candidate_features=["leaky_feature", "noise"],
    )
    dim = report.dimensions["leakage"]
    assert dim.status == "blocked"
    assert "leaky_feature" in dim.evidence_detail["target_derived"]


def test_leakage_detected_by_post_event_naming():
    n = 50
    rng = np.random.default_rng(2)
    df = pd.DataFrame(
        {
            "post_event_flag": rng.integers(0, 2, size=n),
            "noise": rng.normal(0, 1, size=n),
            "yield_rate": rng.normal(0.9, 0.01, size=n),
        }
    )
    report = assess_readiness(
        df,
        target="yield_rate",
        candidate_features=["post_event_flag", "noise"],
    )
    dim = report.dimensions["leakage"]
    assert dim.status == "blocked"
    assert "post_event_flag" in dim.evidence_detail["post_event_cols"]


def test_variable_role_clarity_ok_with_target_and_features():
    df = _clean_df(n=60)
    report = assess_readiness(
        df,
        target="yield_rate",
        candidate_features=["temperature", "pressure"],
    )
    dim = report.dimensions["role_clarity"]
    assert dim.status == "ok"
    assert dim.evidence_detail["Y"] == "yield_rate"
    assert dim.evidence_detail["X_candidates"] == 2


def test_role_clarity_blocked_when_target_constant():
    df = pd.DataFrame(
        {
            "feature": np.arange(50),
            "yield_rate": [0.95] * 50,
        }
    )
    report = assess_readiness(df, target="yield_rate", candidate_features=["feature"])
    assert report.dimensions["role_clarity"].status == "blocked"


def test_reliability_blocked_when_sentinel_on_core_column():
    n = 60
    rng = np.random.default_rng(3)
    temperature = rng.normal(100.0, 5.0, size=n)
    temperature[0] = -999
    temperature[1] = -999
    df = pd.DataFrame(
        {
            "temperature": temperature,
            "yield_rate": rng.normal(0.95, 0.01, size=n),
        }
    )
    report = assess_readiness(df, target="yield_rate")
    dim = report.dimensions["measurement_reliability"]
    assert dim.status in {"partial", "blocked"}
    sentinels = dim.evidence_detail["sentinel_values"]
    assert any(row[0] == "temperature" and row[1] == -999 for row in sentinels)


def test_reliability_partial_when_unit_hint_violated():
    # Column ends in _pct but values are outside 0-100 -> unit mismatch -> blocked
    df = pd.DataFrame(
        {
            "score_pct": [0.5, 0.6, 0.55, 0.7],  # looks like ratios, not percent
            "yield_rate": [0.9, 0.92, 0.91, 0.95],
        }
    )
    report = assess_readiness(df, target="yield_rate")
    dim = report.dimensions["measurement_reliability"]
    # values < 0..100 range bound (0.5 still in range here); let's force outside range
    df2 = pd.DataFrame(
        {
            "score_pct": [120.0, 130.0, 140.0, 150.0],  # outside 0..100
            "yield_rate": [0.9, 0.92, 0.91, 0.95],
        }
    )
    report2 = assess_readiness(df2, target="yield_rate")
    dim2 = report2.dimensions["measurement_reliability"]
    assert dim2.status == "blocked"
    assert "score_pct" in dim2.evidence_detail["unit_mismatch"]
    # First df with in-range ratios should be ok or partial (not blocked on unit mismatch)
    assert dim.status in {"ok", "partial"}


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_assess_readiness_overall_status_ok_on_clean_data():
    df = _clean_df(n=120)
    report = assess_readiness(
        df,
        target="yield_rate",
        group_col="machine",
        time_col="ts",
        candidate_features=["temperature", "pressure"],
    )
    assert isinstance(report, ReadinessReport)
    assert report.overall_status == "ok"
    assert report.data_request == []
    assert report.narrowed_scope_suggestions == []


def test_assess_readiness_overall_status_blocked_propagates_data_request():
    # 3 rows per group => sample size blocked
    df = pd.DataFrame(
        {
            "machine": ["A"] * 3 + ["B"] * 3,
            "yield_rate": [0.9, 0.91, 0.92, 0.93, 0.94, 0.95],
        }
    )
    report = assess_readiness(df, target="yield_rate", group_col="machine")
    assert report.overall_status == "blocked"
    assert report.data_request, "blocked report should populate data_request"
    assert any("sample_size" in entry for entry in report.data_request)


def test_assess_readiness_handles_empty_dataframe_without_crashing():
    df = pd.DataFrame()
    report = assess_readiness(df)
    assert report.overall_status == "blocked"
    # All dimensions present
    for key in DIMENSION_KEYS:
        assert key in report.dimensions


def test_assess_readiness_handles_single_row():
    df = pd.DataFrame({"yield_rate": [0.95], "feature": [1.0]})
    report = assess_readiness(df, target="yield_rate", candidate_features=["feature"])
    assert report.overall_status == "blocked"
    assert report.dimensions["sample_size"].status == "blocked"


def test_as_dict_matches_data_readiness_md_schema():
    df = _clean_df(n=90)
    report = assess_readiness(
        df,
        target="yield_rate",
        group_col="machine",
        time_col="ts",
        candidate_features=["temperature", "pressure"],
    )
    envelope = report.as_dict()

    # Top-level keys per data-readiness.md
    assert set(envelope.keys()) == {
        "decision",
        "dimensions",
        "narrowed_scope",
        "caveats",
        "data_request",
    }
    assert envelope["decision"] in {"ok", "partial", "blocked"}

    # Dimension keys must match the canonical eight
    expected_keys = {
        "sample_size",
        "missingness",
        "grain",
        "time_coverage",
        "balance",
        "leakage",
        "role_clarity",
        "measurement_reliability",
    }
    assert set(envelope["dimensions"].keys()) == expected_keys

    # Each dimension envelope has score / evidence / notes
    for key, body in envelope["dimensions"].items():
        assert set(body.keys()) >= {"score", "evidence", "notes"}, key
        assert body["score"] in {"ok", "partial", "blocked"}, key
        assert isinstance(body["evidence"], dict), key
        assert isinstance(body["notes"], str), key


def test_dimension_score_is_immutable_dataclass():
    dim = DimensionScore(
        name="x",
        status="ok",
        value=1.0,
        threshold="t",
        evidence="e",
    )
    with pytest.raises(Exception):
        dim.status = "blocked"  # type: ignore[misc]
