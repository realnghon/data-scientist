"""Data-shaping helpers: grain detection, leakage audit, long/wide reshape, join audit.

See `references/data-shaping.md` for the conceptual spec. All functions are pure
(no IO, no print) and accept pandas DataFrames.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GrainReport:
    keys_tested: list[str]
    is_unique: bool
    n_total_rows: int
    n_unique_keys: int
    duplicate_examples: list[dict]
    inferred_grain: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LeakageReport:
    target: str
    flagged_columns: list[dict] = field(default_factory=list)
    name_based_flags: list[str] = field(default_factory=list)
    correlation_based_flags: list[str] = field(default_factory=list)
    time_based_flags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewSpec:
    name: str
    grain: str
    aggregations: dict[str, str] = field(default_factory=dict)
    drops: list[str] = field(default_factory=list)
    filters_applied: list[str] = field(default_factory=list)
    recommended_method_families: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Grain detection
# ---------------------------------------------------------------------------


def _validate_df(df: pd.DataFrame) -> None:
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Expected a pandas DataFrame.")
    if df.empty:
        raise ValueError("Input DataFrame is empty; cannot infer shape.")


def detect_grain(
    df: pd.DataFrame, candidate_keys: list[str] | None = None
) -> GrainReport:
    """Test whether ``candidate_keys`` uniquely identify rows.

    If ``candidate_keys`` is None, treat all columns as the candidate key set.
    """
    _validate_df(df)
    if candidate_keys is None:
        keys = list(df.columns)
    else:
        missing = [k for k in candidate_keys if k not in df.columns]
        if missing:
            raise ValueError(f"Candidate keys not in DataFrame: {missing}")
        if len(candidate_keys) == 0:
            raise ValueError("candidate_keys must be a non-empty list (or None).")
        keys = list(candidate_keys)

    n_total = int(len(df))
    # group sizes
    grouped = df.groupby(keys, dropna=False).size()
    n_unique = int(len(grouped))
    is_unique = bool(grouped.max() <= 1) if n_unique > 0 else False

    dup_examples: list[dict] = []
    if not is_unique:
        dup_groups = grouped[grouped > 1].sort_values(ascending=False)
        for combo, count in list(dup_groups.items())[:5]:
            if not isinstance(combo, tuple):
                combo_tuple = (combo,)
            else:
                combo_tuple = combo
            example = {k: _safe_val(v) for k, v in zip(keys, combo_tuple)}
            example["_n_rows"] = int(count)
            dup_examples.append(example)

    if is_unique:
        inferred = f"one row per ({', '.join(keys)})"
    else:
        inferred = (
            f"keys {keys} are NOT unique; {n_unique} unique combinations across {n_total} rows"
        )

    return GrainReport(
        keys_tested=keys,
        is_unique=is_unique,
        n_total_rows=n_total,
        n_unique_keys=n_unique,
        duplicate_examples=dup_examples,
        inferred_grain=inferred,
    )


def _safe_val(v: Any) -> Any:
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (pd.Timestamp,)):
        return v.isoformat()
    if pd.isna(v):
        return None
    return v


# ---------------------------------------------------------------------------
# Suggest grain
# ---------------------------------------------------------------------------


_TIME_HINTS = ("time", "date", "ts", "timestamp", "datetime")
_ENTITY_HINTS = ("id", "_id", "serial", "wafer", "unit", "customer", "user", "entity")
_GROUP_HINTS = ("line", "machine", "shift", "supplier", "recipe", "site", "channel", "arm", "group")


def _classify_column(col: str, dtype: Any, role_hints: dict[str, str] | None) -> str:
    if role_hints and col in role_hints:
        return role_hints[col]
    name = col.lower()
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "time"
    if any(name.endswith(h) or name == h for h in _TIME_HINTS):
        return "time"
    if any(h in name for h in _ENTITY_HINTS):
        return "entity"
    if any(h in name for h in _GROUP_HINTS):
        return "group"
    if pd.api.types.is_numeric_dtype(dtype):
        return "measure"
    return "other"


def suggest_grain(
    df: pd.DataFrame, role_hints: dict[str, str] | None = None
) -> list[ViewSpec]:
    """Suggest candidate analysis views based on column roles."""
    _validate_df(df)

    roles: dict[str, list[str]] = {"entity": [], "time": [], "group": [], "measure": [], "other": []}
    for col in df.columns:
        role = _classify_column(col, df[col].dtype, role_hints)
        roles.setdefault(role, []).append(col)

    views: list[ViewSpec] = []

    # raw row view always available
    measure_aggs = {c: "mean" for c in roles["measure"]}
    views.append(
        ViewSpec(
            name="raw_row",
            grain="one row per source observation",
            aggregations={},
            drops=[],
            filters_applied=[],
            recommended_method_families=["regression", "classification", "anomaly"],
        )
    )

    # entity grain
    if roles["entity"]:
        entity_key = roles["entity"][0]
        drops = roles["time"]  # collapse over time
        views.append(
            ViewSpec(
                name="entity_summary",
                grain=f"one row per {entity_key}",
                aggregations=measure_aggs,
                drops=drops,
                filters_applied=[],
                recommended_method_families=["regression", "driver_ranking", "group_comparison"],
            )
        )

    # group × time grain
    if roles["group"] and roles["time"]:
        group_key = roles["group"][0]
        time_key = roles["time"][0]
        views.append(
            ViewSpec(
                name="group_time_bucket",
                grain=f"one row per ({group_key}, {time_key})",
                aggregations=measure_aggs,
                drops=roles["entity"],
                filters_applied=[],
                recommended_method_families=["spc", "time_series", "group_comparison"],
            )
        )

    # group-only
    if roles["group"] and not roles["time"]:
        group_key = roles["group"][0]
        views.append(
            ViewSpec(
                name="group_summary",
                grain=f"one row per {group_key}",
                aggregations=measure_aggs,
                drops=roles["entity"],
                filters_applied=[],
                recommended_method_families=["group_comparison", "ranking"],
            )
        )

    # time-only
    if roles["time"] and not roles["group"]:
        time_key = roles["time"][0]
        views.append(
            ViewSpec(
                name="time_bucket",
                grain=f"one row per {time_key}",
                aggregations=measure_aggs,
                drops=roles["entity"],
                filters_applied=[],
                recommended_method_families=["time_series", "spc", "change_point"],
            )
        )

    return views


# ---------------------------------------------------------------------------
# Leakage detection
# ---------------------------------------------------------------------------


_LEAKY_NAME_PATTERNS = [
    re.compile(r"^post[_-]", re.IGNORECASE),
    re.compile(r"^outcome[_-]", re.IGNORECASE),
    re.compile(r"^result[_-]", re.IGNORECASE),
    re.compile(r"_after$", re.IGNORECASE),
    re.compile(r"_postevent$", re.IGNORECASE),
    re.compile(r"_post$", re.IGNORECASE),
    re.compile(r"root[_-]?cause", re.IGNORECASE),
    re.compile(r"rework", re.IGNORECASE),
    re.compile(r"resolution", re.IGNORECASE),
    re.compile(r"resolved[_-]", re.IGNORECASE),
    re.compile(r"closed[_-]", re.IGNORECASE),
]


def detect_leakage_columns(
    df: pd.DataFrame,
    target: str,
    time_col: str | None = None,
) -> LeakageReport:
    """Audit columns for post-outcome leakage.

    Three lenses:
      - **name-based**: column names that look like post-outcome fields.
      - **correlation-based**: |Pearson r| > 0.98 with the target (near-perfect predictors).
      - **time-based**: if a target-event timestamp is supplied, columns whose timestamps
        are populated strictly after the target's earliest non-null event time.
    """
    _validate_df(df)
    if target not in df.columns:
        raise ValueError(f"Target column not in DataFrame: {target}")
    if time_col is not None and time_col not in df.columns:
        raise ValueError(f"time_col not in DataFrame: {time_col}")

    name_flags: list[str] = []
    corr_flags: list[str] = []
    time_flags: list[str] = []
    flagged: list[dict] = []

    target_series = df[target]
    target_numeric = pd.to_numeric(target_series, errors="coerce")
    target_is_numeric = target_numeric.notna().sum() >= 2

    for col in df.columns:
        if col == target:
            continue

        # name-based
        if any(p.search(col) for p in _LEAKY_NAME_PATTERNS):
            name_flags.append(col)
            flagged.append(
                {
                    "column": col,
                    "reason": "column name matches post-outcome pattern",
                    "severity": "high",
                }
            )

        # correlation-based
        if target_is_numeric and pd.api.types.is_numeric_dtype(df[col]):
            pair = pd.concat([target_numeric, df[col]], axis=1).dropna()
            if len(pair) >= 3 and pair.iloc[:, 1].nunique(dropna=True) > 1:
                with np.errstate(invalid="ignore"):
                    r = pair.corr().iloc[0, 1]
                if r is not None and not np.isnan(r) and abs(r) > 0.98:
                    corr_flags.append(col)
                    flagged.append(
                        {
                            "column": col,
                            "reason": f"|Pearson r| = {abs(r):.4f} > 0.98 with target",
                            "severity": "high",
                        }
                    )

    # time-based
    if time_col is not None:
        try:
            target_times = pd.to_datetime(df[time_col], errors="coerce")
        except Exception:
            target_times = pd.Series([pd.NaT] * len(df))
        if target_times.notna().any():
            # threshold: earliest non-null target-event time among rows where target is not null
            mask = target_series.notna() & target_times.notna()
            if mask.any():
                threshold = target_times[mask].min()
                for col in df.columns:
                    if col in (target, time_col):
                        continue
                    series = df[col]
                    # only consider columns that parse as datetimes
                    try:
                        col_dt = pd.to_datetime(series, errors="coerce")
                    except Exception:
                        continue
                    if col_dt.notna().sum() == 0:
                        continue
                    # if every non-null timestamp is strictly after the target event window
                    non_null = col_dt.dropna()
                    if len(non_null) > 0 and (non_null > threshold).mean() > 0.95:
                        time_flags.append(col)
                        flagged.append(
                            {
                                "column": col,
                                "reason": (
                                    f"timestamps populated after target event time ({threshold})"
                                ),
                                "severity": "medium",
                            }
                        )

    return LeakageReport(
        target=target,
        flagged_columns=flagged,
        name_based_flags=name_flags,
        correlation_based_flags=corr_flags,
        time_based_flags=time_flags,
    )


# ---------------------------------------------------------------------------
# Long ↔ wide
# ---------------------------------------------------------------------------


def long_to_wide(
    df: pd.DataFrame,
    index_cols: list[str],
    columns_col: str,
    values_col: str,
    agg: str = "mean",
) -> pd.DataFrame:
    """Pivot long-format data to wide.

    Uses ``pivot_table`` with explicit ``aggfunc`` so duplicate keys collapse
    deterministically. Resets the index and clears the columns name.
    """
    _validate_df(df)
    missing = [c for c in [*index_cols, columns_col, values_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not in DataFrame: {missing}")
    if not index_cols:
        raise ValueError("index_cols must be non-empty.")

    wide = df.pivot_table(
        index=index_cols,
        columns=columns_col,
        values=values_col,
        aggfunc=agg,
    )
    wide.columns.name = None
    wide = wide.reset_index()
    return wide


def wide_to_long(
    df: pd.DataFrame,
    id_cols: list[str],
    value_cols: list[str],
    var_name: str = "variable",
    value_name: str = "value",
) -> pd.DataFrame:
    """Melt wide-format data to long."""
    _validate_df(df)
    missing = [c for c in [*id_cols, *value_cols] if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not in DataFrame: {missing}")
    if not value_cols:
        raise ValueError("value_cols must be non-empty.")
    return df.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name=var_name,
        value_name=value_name,
    )


# ---------------------------------------------------------------------------
# Join audit
# ---------------------------------------------------------------------------


def audit_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: list[str],
    how: str = "inner",
) -> dict:
    """Run a merge and report multiplicity / match stats / recommendation."""
    if not isinstance(left, pd.DataFrame) or not isinstance(right, pd.DataFrame):
        raise ValueError("left and right must be pandas DataFrames.")
    if not on:
        raise ValueError("`on` must be a non-empty list of key columns.")
    missing_left = [k for k in on if k not in left.columns]
    missing_right = [k for k in on if k not in right.columns]
    if missing_left or missing_right:
        raise ValueError(
            f"Join keys missing — left: {missing_left}, right: {missing_right}"
        )

    before_left = int(len(left))
    before_right = int(len(right))

    # multiplicity on the right side (how many right-rows per join key)
    right_counts = right.groupby(on, dropna=False).size()
    left_counts = left.groupby(on, dropna=False).size()
    multiplicity_max = int(right_counts.max()) if len(right_counts) else 0

    merged = left.merge(right, on=on, how=how, indicator=True)
    after = int(len(merged))

    unmatched_left = int((merged["_merge"] == "left_only").sum()) if how in {"left", "outer"} else int(
        before_left - left.merge(right[on].drop_duplicates(), on=on, how="inner").shape[0]
    )
    unmatched_right = int((merged["_merge"] == "right_only").sum()) if how in {"right", "outer"} else int(
        before_right - right.merge(left[on].drop_duplicates(), on=on, how="inner").shape[0]
    )

    recommendation_parts: list[str] = []
    if multiplicity_max > 1:
        recommendation_parts.append(
            f"right side has up to {multiplicity_max} rows per key — pre-aggregate right "
            "before joining to avoid 1:N inflation"
        )
    if how == "inner" and unmatched_left > 0:
        recommendation_parts.append(
            f"{unmatched_left} left rows were dropped by inner join; consider how='left' or "
            "report join_match_rate"
        )
    if not recommendation_parts:
        recommendation_parts.append("join multiplicity and match rate look healthy")

    join_match_rate = (
        float((before_left - unmatched_left) / before_left) if before_left > 0 else 0.0
    )

    return {
        "before_left": before_left,
        "before_right": before_right,
        "after": after,
        "multiplicity_max": multiplicity_max,
        "left_multiplicity_max": int(left_counts.max()) if len(left_counts) else 0,
        "unmatched_left": unmatched_left,
        "unmatched_right": unmatched_right,
        "join_match_rate": join_match_rate,
        "how": how,
        "on": list(on),
        "recommendation": "; ".join(recommendation_parts),
    }
