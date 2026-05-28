"""Tests for ds_skill.shaping."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.shaping import (  # noqa: E402
    GrainReport,
    LeakageReport,
    ViewSpec,
    audit_join,
    detect_grain,
    detect_leakage_columns,
    long_to_wide,
    suggest_grain,
    wide_to_long,
)


def test_detect_grain_unique_keys():
    df = pd.DataFrame({"id": [1, 2, 3, 4], "val": [10, 20, 30, 40]})
    rep = detect_grain(df, candidate_keys=["id"])
    assert rep.is_unique is True
    assert rep.n_total_rows == 4
    assert rep.n_unique_keys == 4
    assert rep.duplicate_examples == []
    assert "id" in rep.inferred_grain


def test_detect_grain_non_unique_with_examples():
    df = pd.DataFrame(
        {
            "wafer_id": ["A", "A", "B", "B", "C"],
            "step": [1, 1, 2, 3, 1],
            "val": [10, 11, 20, 21, 30],
        }
    )
    rep = detect_grain(df, candidate_keys=["wafer_id"])
    assert rep.is_unique is False
    assert rep.n_unique_keys == 3
    assert any(ex["_n_rows"] == 2 for ex in rep.duplicate_examples)


def test_detect_grain_validates_input():
    with pytest.raises(ValueError):
        detect_grain(pd.DataFrame())
    with pytest.raises(ValueError):
        detect_grain(pd.DataFrame({"a": [1]}), candidate_keys=["missing"])


def test_detect_leakage_by_name():
    df = pd.DataFrame(
        {
            "x1": [1, 2, 3, 4],
            "post_event_flag": [0, 1, 0, 1],
            "result_label": ["a", "b", "a", "b"],
            "y": [0, 1, 0, 1],
        }
    )
    rep = detect_leakage_columns(df, target="y")
    assert "post_event_flag" in rep.name_based_flags
    assert "result_label" in rep.name_based_flags
    assert all(f["severity"] == "high" for f in rep.flagged_columns if f["column"] in rep.name_based_flags)


def test_detect_leakage_by_correlation():
    rng = np.random.default_rng(0)
    x = rng.normal(size=200)
    y = 3 * x + 0.001 * rng.normal(size=200)  # near-perfect linear with target
    df = pd.DataFrame({"feature_clone": y * 0.5, "noise": rng.normal(size=200), "y": y})
    rep = detect_leakage_columns(df, target="y")
    assert "feature_clone" in rep.correlation_based_flags
    assert "noise" not in rep.correlation_based_flags


def test_detect_leakage_by_time():
    target_time = pd.Timestamp("2024-01-01")
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "event_time": [target_time, target_time, target_time],
            "post_inspection_ts": pd.to_datetime(
                ["2024-01-05", "2024-01-06", "2024-01-07"]
            ),
            "pre_sensor_ts": pd.to_datetime(
                ["2023-12-30", "2023-12-31", "2023-12-29"]
            ),
            "y": [1, 0, 1],
        }
    )
    rep = detect_leakage_columns(df, target="y", time_col="event_time")
    assert "post_inspection_ts" in rep.time_based_flags
    assert "pre_sensor_ts" not in rep.time_based_flags


def test_long_to_wide_round_trip():
    long = pd.DataFrame(
        {
            "id": [1, 1, 2, 2, 3, 3],
            "metric": ["a", "b", "a", "b", "a", "b"],
            "value": [10.0, 20.0, 11.0, 21.0, 12.0, 22.0],
        }
    )
    wide = long_to_wide(long, index_cols=["id"], columns_col="metric", values_col="value")
    assert set(wide.columns) == {"id", "a", "b"}
    assert wide.shape == (3, 3)

    back = wide_to_long(wide, id_cols=["id"], value_cols=["a", "b"], var_name="metric", value_name="value")
    # sort for comparison
    long_sorted = long.sort_values(["id", "metric"]).reset_index(drop=True)
    back_sorted = back.sort_values(["id", "metric"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(
        long_sorted[["id", "metric", "value"]].astype({"value": float}),
        back_sorted[["id", "metric", "value"]].astype({"value": float}),
        check_dtype=False,
    )


def test_audit_join_detects_one_to_many_inflation():
    left = pd.DataFrame({"k": [1, 2, 3], "x": [10, 20, 30]})
    right = pd.DataFrame({"k": [1, 1, 1, 2, 2], "y": [100, 101, 102, 200, 201]})
    rep = audit_join(left, right, on=["k"], how="left")
    assert rep["before_left"] == 3
    assert rep["multiplicity_max"] == 3
    assert rep["after"] > rep["before_left"]
    assert "inflation" in rep["recommendation"].lower() or "1:N" in rep["recommendation"] or "pre-aggregate" in rep["recommendation"].lower()


def test_suggest_grain_returns_views():
    df = pd.DataFrame(
        {
            "wafer_id": [1, 1, 2, 2, 3, 3],
            "shift": ["A", "B", "A", "B", "A", "B"],
            "ts": pd.to_datetime(["2024-01-01"] * 6),
            "temp": [70, 71, 72, 73, 74, 75],
            "yield_pct": [0.95, 0.96, 0.94, 0.93, 0.97, 0.98],
        }
    )
    views = suggest_grain(df)
    names = {v.name for v in views}
    assert "raw_row" in names
    assert "entity_summary" in names
    assert "group_time_bucket" in names
    for v in views:
        assert isinstance(v, ViewSpec)
        assert v.recommended_method_families


def test_as_dict_json_serializable():
    df = pd.DataFrame({"id": [1, 2, 2], "y": [1, 0, 1]})
    grain = detect_grain(df, candidate_keys=["id"])
    leak = detect_leakage_columns(df, target="y")
    view = ViewSpec(
        name="raw", grain="one row per id", aggregations={"y": "mean"}, drops=[], filters_applied=[],
        recommended_method_families=["regression"],
    )
    assert isinstance(grain, GrainReport)
    assert isinstance(leak, LeakageReport)
    # round-trip through json
    json.dumps(grain.as_dict())
    json.dumps(leak.as_dict())
    json.dumps(view.as_dict())
