"""Data readiness assessor.

Scores a DataFrame against the 8-dimension readiness rubric defined in
`references/data-readiness.md` and returns a structured `ReadinessReport`.

Pure: no IO, no logging, no network. Depends only on pandas and numpy.

Output dimensions (canonical keys per data-readiness.md):
    sample_size, missingness, grain, time_coverage, balance,
    leakage, role_clarity, measurement_reliability
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

Status = Literal["ok", "partial", "blocked"]

# Canonical dimension keys, in JSON envelope order
DIMENSION_KEYS: tuple[str, ...] = (
    "sample_size",
    "missingness",
    "grain",
    "time_coverage",
    "balance",
    "leakage",
    "role_clarity",
    "measurement_reliability",
)

_LEAKAGE_PREFIX_PATTERNS = (
    re.compile(r"^post[_\-]", re.IGNORECASE),
    re.compile(r"^outcome[_\-]", re.IGNORECASE),
    re.compile(r"^result[_\-]", re.IGNORECASE),
    re.compile(r"^postevent[_\-]", re.IGNORECASE),
)
_LEAKAGE_SUBSTRINGS = ("root_cause", "rootcause")

# Economic / monetary fields that are frequently realized *after* a conversion or
# outcome event (e.g. `revenue` only accrues once `converted == 1`). Flagged as a
# caveat (partial), not an automatic block, because a pre-period measurement of the
# same name can be a legitimate predictor — the analyst must confirm time ordering.
_PROXY_NAME_SUBSTRINGS = (
    "revenue",
    "sales",
    "amount",
    "ltv",
    "lifetime_value",
    "gmv",
    "turnover",
    "profit",
    "payment",
    "paid",
    "spend",
    "spent",
    "charge",
    "billing",
)

_UNIT_RANGE_HINTS: dict[str, tuple[float, float]] = {
    # suffix -> (min plausible, max plausible) for the named unit
    "_pct": (0.0, 100.0),
    "_percent": (0.0, 100.0),
    "_ratio": (0.0, 1.0),
    "_prob": (0.0, 1.0),
}

_SENTINEL_VALUES = (-999, -9999, 9999, 999, -1)


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single readiness dimension."""

    name: str
    status: Status
    value: float | str
    threshold: str
    evidence: str
    evidence_detail: dict[str, Any] = field(default_factory=dict)

    def to_envelope(self) -> dict[str, Any]:
        """Return the JSON envelope shape expected by data-readiness.md."""
        return {
            "score": self.status,
            "evidence": dict(self.evidence_detail),
            "notes": self.evidence,
        }


@dataclass(frozen=True)
class ReadinessReport:
    """Top-level readiness report."""

    overall_status: Status
    dimensions: dict[str, DimensionScore]
    narrowed_scope_suggestions: list[str] = field(default_factory=list)
    data_request: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return the JSON envelope defined in data-readiness.md."""
        envelope: dict[str, Any] = {
            "decision": self.overall_status,
            "dimensions": {
                key: self.dimensions[key].to_envelope()
                for key in DIMENSION_KEYS
                if key in self.dimensions
            },
            "narrowed_scope": list(self.narrowed_scope_suggestions),
            "caveats": list(self.caveats),
            "data_request": None,
        }
        if self.overall_status == "blocked" and self.data_request:
            envelope["narrowed_scope"] = []
            envelope["data_request"] = {
                "blocking_reasons": list(self.data_request),
                "fields_needed": [],
                "grain_needed": "",
                "coverage_needed": "",
                "target_definition": "",
                "methods_unblocked": [],
            }
        return envelope


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_readiness(
    df: pd.DataFrame,
    target: str | None = None,
    group_col: str | None = None,
    time_col: str | None = None,
    candidate_features: list[str] | None = None,
    min_samples_per_group: int = 5,
) -> ReadinessReport:
    """Score the DataFrame against the 8 readiness dimensions.

    Edge cases (empty df, single-row df, all-NaN columns) yield ``blocked``
    dimension scores rather than exceptions.
    """

    candidate_features = list(candidate_features or [])

    dimensions: dict[str, DimensionScore] = {
        "sample_size": _score_sample_size(df, group_col, min_samples_per_group),
        "missingness": _score_missingness(df, target),
        "grain": _score_grain(df, group_col, time_col),
        "time_coverage": _score_time_coverage(df, time_col),
        "balance": _score_balance(df, target, group_col),
        "leakage": _score_leakage(df, target, candidate_features),
        "role_clarity": _score_role_clarity(df, target, candidate_features),
        "measurement_reliability": _score_measurement_reliability(df),
    }

    overall = _roll_up(dimensions)
    narrowed: list[str] = []
    data_request: list[str] = []
    caveats: list[str] = []

    for key, dim in dimensions.items():
        if dim.status == "blocked":
            data_request.append(f"{key}: {dim.evidence}")
        elif dim.status == "partial":
            caveats.append(f"{key}: {dim.evidence}")

    if overall == "partial":
        narrowed = _suggest_narrowed_scope(dimensions)

    return ReadinessReport(
        overall_status=overall,
        dimensions=dimensions,
        narrowed_scope_suggestions=narrowed,
        data_request=data_request if overall == "blocked" else [],
        caveats=caveats,
    )


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------


def _score_sample_size(
    df: pd.DataFrame, group_col: str | None, min_samples_per_group: int
) -> DimensionScore:
    threshold = (
        "per-cell n: >=30 ok, 10-29 partial, 5-9 partial, <5 blocked"
    )

    n_rows = int(len(df))
    if n_rows == 0:
        return DimensionScore(
            name="sample_size",
            status="blocked",
            value=0,
            threshold=threshold,
            evidence="DataFrame has zero rows.",
            evidence_detail={"per_cell_min": 0, "per_cell_median": 0, "rule_violations": ["empty"]},
        )

    if group_col is not None and group_col in df.columns:
        counts = df.groupby(group_col, dropna=False).size()
        per_cell_min = int(counts.min()) if len(counts) else 0
        per_cell_median = int(counts.median()) if len(counts) else 0
        violations: list[str] = []
        if per_cell_min < min_samples_per_group or per_cell_min < 5:
            status: Status = "blocked"
            violations.append(f"min group n = {per_cell_min}")
        elif per_cell_min < 30:
            status = "partial"
            violations.append(f"min group n = {per_cell_min} (<30 -> exploratory)")
        else:
            status = "ok"
        evidence = (
            f"{len(counts)} groups in '{group_col}'; min n = {per_cell_min}, "
            f"median n = {per_cell_median}."
        )
        return DimensionScore(
            name="sample_size",
            status=status,
            value=float(per_cell_min),
            threshold=threshold,
            evidence=evidence,
            evidence_detail={
                "per_cell_min": per_cell_min,
                "per_cell_median": per_cell_median,
                "rule_violations": violations,
            },
        )

    # No group_col: assess total N
    violations = []
    if n_rows < 5:
        status = "blocked"
        violations.append(f"total n = {n_rows} < 5")
    elif n_rows < 30:
        status = "partial"
        violations.append(f"total n = {n_rows} (<30 -> exploratory)")
    else:
        status = "ok"
    return DimensionScore(
        name="sample_size",
        status=status,
        value=float(n_rows),
        threshold=threshold,
        evidence=f"Total rows = {n_rows}.",
        evidence_detail={
            "per_cell_min": n_rows,
            "per_cell_median": n_rows,
            "rule_violations": violations,
        },
    )


def _score_missingness(df: pd.DataFrame, target: str | None) -> DimensionScore:
    threshold = "<10% ok, 10-30% partial, >30% blocked (on Y)"

    if df.empty or df.shape[1] == 0:
        return DimensionScore(
            name="missingness",
            status="blocked",
            value=1.0,
            threshold=threshold,
            evidence="No data to assess missingness.",
            evidence_detail={"overall_pct": 1.0, "by_column_top": [], "mechanism_guess": "unknown"},
        )

    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())
    overall_pct = missing_cells / total_cells if total_cells else 1.0

    by_col_pct = (df.isna().mean()).sort_values(ascending=False)
    worst_col = by_col_pct.index[0] if len(by_col_pct) else None
    worst_pct = float(by_col_pct.iloc[0]) if len(by_col_pct) else 0.0
    top: list[list[Any]] = [
        [str(col), float(pct)] for col, pct in by_col_pct.head(3).items() if pct > 0
    ]

    target_missing_pct: float | None = None
    if target is not None and target in df.columns:
        target_missing_pct = float(df[target].isna().mean())

    # Y-missingness is a hard blocker when >30%
    if target_missing_pct is not None and target_missing_pct > 0.30:
        return DimensionScore(
            name="missingness",
            status="blocked",
            value=round(target_missing_pct, 4),
            threshold=threshold,
            evidence=(
                f"Target '{target}' is {target_missing_pct:.0%} missing "
                f"(>30% blocks downstream conclusions)."
            ),
            evidence_detail={
                "overall_pct": round(overall_pct, 4),
                "by_column_top": top,
                "mechanism_guess": "unknown",
                "target_missing_pct": round(target_missing_pct, 4),
            },
        )

    if overall_pct < 0.10 and worst_pct < 0.30:
        status: Status = "ok"
        notes = f"Overall {overall_pct:.0%} missing; worst column {worst_pct:.0%}."
    elif overall_pct > 0.30 or worst_pct > 0.50:
        status = "blocked"
        notes = (
            f"Overall {overall_pct:.0%} missing; worst column "
            f"'{worst_col}' at {worst_pct:.0%} (>30% / >50% threshold)."
        )
    else:
        status = "partial"
        notes = (
            f"Overall {overall_pct:.0%} missing; worst column "
            f"'{worst_col}' at {worst_pct:.0%}; document imputation."
        )

    return DimensionScore(
        name="missingness",
        status=status,
        value=round(overall_pct, 4),
        threshold=threshold,
        evidence=notes,
        evidence_detail={
            "overall_pct": round(overall_pct, 4),
            "by_column_top": top,
            "mechanism_guess": "unknown",
            "target_missing_pct": (
                None if target_missing_pct is None else round(target_missing_pct, 4)
            ),
        },
    )


def _score_grain(
    df: pd.DataFrame, group_col: str | None, time_col: str | None
) -> DimensionScore:
    threshold = (
        "one row per intended unit -> ok; legitimate repeats -> partial; "
        "mixed grain (duplicate keys) -> blocked"
    )

    if df.empty:
        return DimensionScore(
            name="grain",
            status="blocked",
            value="empty",
            threshold=threshold,
            evidence="No rows to assess grain.",
            evidence_detail={"intended_grain": "unknown", "duplicate_count": 0},
        )

    # Build candidate key columns
    key_cols: list[str] = []
    for col in (group_col, time_col):
        if col is not None and col in df.columns:
            key_cols.append(col)

    # Heuristic: look for entity-like columns when no group_col is given
    if not key_cols:
        for col in df.columns:
            name = str(col).lower()
            if name.endswith("_id") or name in {"id", "entity_id", "key"}:
                key_cols.append(col)
                break

    intended = " + ".join(key_cols) if key_cols else "<all rows>"
    if not key_cols:
        # No key columns -> can't detect duplicates positively. Mark ok with note.
        return DimensionScore(
            name="grain",
            status="ok",
            value="unknown",
            threshold=threshold,
            evidence="No key columns provided/detected; assume one row per record.",
            evidence_detail={"intended_grain": intended, "duplicate_count": 0},
        )

    duplicate_count = int(df.duplicated(subset=key_cols).sum())
    if duplicate_count == 0:
        status: Status = "ok"
        evidence = f"No duplicate keys on {key_cols}."
    elif duplicate_count <= max(1, int(0.05 * len(df))):
        status = "partial"
        evidence = (
            f"{duplicate_count} duplicate key rows on {key_cols} "
            f"(possible repeated measures; flag for aggregation)."
        )
    else:
        status = "blocked"
        evidence = (
            f"{duplicate_count} duplicate key rows on {key_cols} "
            f"({duplicate_count / len(df):.0%}); grain is mixed."
        )

    return DimensionScore(
        name="grain",
        status=status,
        value=float(duplicate_count),
        threshold=threshold,
        evidence=evidence,
        evidence_detail={
            "intended_grain": intended,
            "duplicate_count": duplicate_count,
        },
    )


def _score_time_coverage(df: pd.DataFrame, time_col: str | None) -> DimensionScore:
    threshold = (
        "span >=2 cycles ok; gap_fraction <10% ok, 10-30% partial, >30% blocked"
    )

    if time_col is None:
        return DimensionScore(
            name="time_coverage",
            status="ok",
            value="n/a",
            threshold=threshold,
            evidence="No time column requested; dimension not applicable.",
            evidence_detail={
                "span_days": None,
                "gap_fraction": None,
                "cadence": "n/a",
            },
        )

    if time_col not in df.columns:
        return DimensionScore(
            name="time_coverage",
            status="blocked",
            value="missing",
            threshold=threshold,
            evidence=f"Requested time column '{time_col}' not in DataFrame.",
            evidence_detail={
                "span_days": None,
                "gap_fraction": None,
                "cadence": "n/a",
            },
        )

    series = pd.to_datetime(df[time_col], errors="coerce").dropna().sort_values()
    if len(series) < 2:
        return DimensionScore(
            name="time_coverage",
            status="blocked",
            value=float(len(series)),
            threshold=threshold,
            evidence=f"Time column '{time_col}' has fewer than 2 valid timestamps.",
            evidence_detail={
                "span_days": 0.0,
                "gap_fraction": 1.0,
                "cadence": "unknown",
            },
        )

    span = series.iloc[-1] - series.iloc[0]
    span_days = float(span.total_seconds() / 86400.0)

    diffs = series.diff().dropna().dt.total_seconds()
    median_step = float(diffs.median())
    if median_step <= 0:
        # All same timestamp -> no real coverage
        return DimensionScore(
            name="time_coverage",
            status="blocked",
            value=span_days,
            threshold=threshold,
            evidence=f"Time column '{time_col}' has no positive cadence.",
            evidence_detail={
                "span_days": span_days,
                "gap_fraction": 1.0,
                "cadence": "constant",
            },
        )

    # gap = step > 2 * median step
    gap_count = int((diffs > 2 * median_step).sum())
    gap_fraction = gap_count / len(diffs) if len(diffs) else 0.0

    # cadence label
    if median_step < 60 * 60:
        cadence = "sub-hourly"
    elif median_step < 26 * 3600:
        cadence = "daily"
    elif median_step < 8 * 86400:
        cadence = "weekly"
    elif median_step < 32 * 86400:
        cadence = "monthly"
    else:
        cadence = "irregular"

    if gap_fraction > 0.30:
        status: Status = "blocked"
        evidence = (
            f"Gap fraction {gap_fraction:.0%} > 30% on '{time_col}'; "
            f"span {span_days:.1f} days, cadence {cadence}."
        )
    elif gap_fraction > 0.10:
        status = "partial"
        evidence = (
            f"Gap fraction {gap_fraction:.0%} (10-30%) on '{time_col}'; "
            f"plan resampling."
        )
    else:
        status = "ok"
        evidence = (
            f"Time span {span_days:.1f} days, cadence {cadence}, "
            f"gap fraction {gap_fraction:.0%}."
        )

    return DimensionScore(
        name="time_coverage",
        status=status,
        value=round(gap_fraction, 4),
        threshold=threshold,
        evidence=evidence,
        evidence_detail={
            "span_days": round(span_days, 4),
            "gap_fraction": round(gap_fraction, 4),
            "cadence": cadence,
        },
    )


def _score_balance(
    df: pd.DataFrame, target: str | None, group_col: str | None
) -> DimensionScore:
    threshold = (
        "majority:minority <=3:1 ok, 3-10:1 partial, 10-100:1 partial, >100:1 blocked"
    )

    # Decide which column drives imbalance: prefer binary/categorical target,
    # else group_col.
    driver: str | None = None
    if target is not None and target in df.columns:
        if not pd.api.types.is_numeric_dtype(df[target]) or df[target].nunique() <= 10:
            driver = target
    if driver is None and group_col is not None and group_col in df.columns:
        driver = group_col

    if driver is None:
        return DimensionScore(
            name="balance",
            status="ok",
            value="n/a",
            threshold=threshold,
            evidence="No categorical target or group column; imbalance not applicable.",
            evidence_detail={
                "majority_minority_ratio": None,
                "metric_recommendation": None,
            },
        )

    counts = df[driver].dropna().value_counts()
    if len(counts) < 2:
        return DimensionScore(
            name="balance",
            status="blocked",
            value=float(len(counts)),
            threshold=threshold,
            evidence=f"'{driver}' has fewer than 2 categories.",
            evidence_detail={
                "majority_minority_ratio": None,
                "metric_recommendation": None,
            },
        )

    majority = int(counts.iloc[0])
    minority = int(counts.iloc[-1])
    if minority == 0:
        ratio = float("inf")
    else:
        ratio = majority / minority

    if ratio > 100:
        status: Status = "blocked"
        rec = "reframe as anomaly detection"
    elif ratio > 10:
        status = "partial"
        rec = "resampling or cost-sensitive loss"
    elif ratio > 3:
        status = "partial"
        rec = "balanced metric (PR-AUC, F1)"
    else:
        status = "ok"
        rec = "accuracy is acceptable"

    return DimensionScore(
        name="balance",
        status=status,
        value=round(ratio, 4),
        threshold=threshold,
        evidence=f"'{driver}' majority:minority = {ratio:.2f}:1; {rec}.",
        evidence_detail={
            "majority_minority_ratio": round(ratio, 4),
            "metric_recommendation": rec,
        },
    )


def _detect_target_gated(
    df: pd.DataFrame, target: str | None, candidate_features: list[str]
) -> list[str]:
    """Numeric features that are constant within a target class but vary overall.

    This is the signature of a post-outcome / target-gated field: e.g. ``revenue``
    is identically 0 for every non-converter and only varies among converters, so
    it is a function of the outcome rather than a pre-outcome predictor. Such a
    feature can sit well below the perfect-correlation threshold (revenue ~ 0.82
    with a binary ``converted``) yet still leak, which is exactly the gap the
    correlation check misses.

    Only fires for a low-cardinality (class-structured) target, requires real
    overall variation in the feature, and requires at least two adequately-sized
    classes — one constant, one varying — to avoid flagging sparse columns.
    """
    if target is None or target not in df.columns:
        return []
    y = df[target].dropna()
    n_classes = y.nunique()
    if n_classes < 2 or n_classes > 10:
        return []  # not a class-structured target; correlation check handles continuous Y

    classes = list(y.unique())
    gated: list[str] = []
    for feature in candidate_features:
        if feature == target or feature not in df.columns:
            continue
        x = df[feature]
        if not pd.api.types.is_numeric_dtype(x):
            continue
        pair = pd.concat([x, df[target]], axis=1).dropna()
        if len(pair) < 10:
            continue
        xv = pair.iloc[:, 0]
        yv = pair.iloc[:, 1]
        if xv.nunique() <= 1:
            continue  # constant overall -> uninformative, not leakage (role_clarity covers it)

        constant_classes = 0
        varying_classes = 0
        eligible_classes = 0
        for cls in classes:
            xc = xv[yv == cls]
            if len(xc) < 5:
                continue
            eligible_classes += 1
            if xc.nunique() <= 1:
                constant_classes += 1
            else:
                varying_classes += 1

        if eligible_classes >= 2 and constant_classes >= 1 and varying_classes >= 1:
            gated.append(feature)

    return gated


def _score_leakage(
    df: pd.DataFrame, target: str | None, candidate_features: list[str]
) -> DimensionScore:
    threshold = (
        "post-event/target-derived/perfect-corr/target-gated feature in X -> blocked; "
        "monetary-proxy name -> partial; clean -> ok"
    )

    post_event_cols: list[str] = []
    perfect_corr_cols: list[str] = []

    # Name-based heuristics on the candidate set
    for feature in candidate_features:
        if feature == target:
            continue
        name = str(feature)
        lower = name.lower()
        if any(p.search(name) for p in _LEAKAGE_PREFIX_PATTERNS):
            post_event_cols.append(feature)
            continue
        if any(s in lower for s in _LEAKAGE_SUBSTRINGS):
            post_event_cols.append(feature)

    # Perfect-correlation check (numeric features only)
    if target is not None and target in df.columns and pd.api.types.is_numeric_dtype(df[target]):
        y = df[target]
        for feature in candidate_features:
            if feature == target or feature not in df.columns:
                continue
            x = df[feature]
            if not pd.api.types.is_numeric_dtype(x):
                continue
            pair = pd.concat([x, y], axis=1).dropna()
            if len(pair) < 3:
                continue
            if pair.iloc[:, 0].nunique() <= 1 or pair.iloc[:, 1].nunique() <= 1:
                continue
            corr = float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))
            if not np.isnan(corr) and abs(corr) >= 0.999:
                if feature not in perfect_corr_cols:
                    perfect_corr_cols.append(feature)

    # Class-conditional degeneracy: feature gated by a low-cardinality outcome.
    target_gated_cols = _detect_target_gated(df, target, candidate_features)

    blocked_cols = sorted(
        set(post_event_cols) | set(perfect_corr_cols) | set(target_gated_cols)
    )

    # Monetary-proxy names -> soft caveat (partial) unless already a hard blocker.
    proxy_name_suspects: list[str] = []
    if target is not None:
        for feature in candidate_features:
            if feature == target or feature in blocked_cols:
                continue
            lower = str(feature).lower()
            if any(s in lower for s in _PROXY_NAME_SUBSTRINGS):
                proxy_name_suspects.append(feature)

    if blocked_cols:
        status: Status = "blocked"
        reasons: list[str] = []
        if post_event_cols:
            reasons.append("post-event names")
        if perfect_corr_cols:
            reasons.append("perfect correlation with Y")
        if target_gated_cols:
            reasons.append("constant-within-a-target-class (post-outcome / target-gated)")
        evidence = f"Leakage suspects in X: {blocked_cols} ({'; '.join(reasons)})."
    elif proxy_name_suspects:
        status = "partial"
        evidence = (
            f"Monetary-proxy features {proxy_name_suspects} may be realized after the "
            f"outcome; confirm each is measured strictly before Y before using as a driver."
        )
    else:
        status = "ok"
        evidence = "No leakage suspects in candidate features."

    return DimensionScore(
        name="leakage",
        status=status,
        value=float(len(blocked_cols)),
        threshold=threshold,
        evidence=evidence,
        evidence_detail={
            "post_event_cols": post_event_cols,
            "target_derived": perfect_corr_cols,
            "target_gated_cols": target_gated_cols,
            "proxy_name_suspects": proxy_name_suspects,
            "time_order_violations": 0,
        },
    )


def _score_role_clarity(
    df: pd.DataFrame, target: str | None, candidate_features: list[str]
) -> DimensionScore:
    threshold = (
        "target + candidate X with variation -> ok; partial roles -> partial; "
        "no plausible Y -> blocked"
    )

    if target is None:
        if candidate_features:
            return DimensionScore(
                name="role_clarity",
                status="partial",
                value="no_target",
                threshold=threshold,
                evidence=(
                    f"No target provided but {len(candidate_features)} candidate "
                    f"features set; treat as exploratory profile."
                ),
                evidence_detail={
                    "Y": None,
                    "Y_variation": None,
                    "X_candidates": len(candidate_features),
                },
            )
        return DimensionScore(
            name="role_clarity",
            status="blocked",
            value="no_target",
            threshold=threshold,
            evidence="No target and no candidate features specified.",
            evidence_detail={
                "Y": None,
                "Y_variation": None,
                "X_candidates": 0,
            },
        )

    if target not in df.columns:
        return DimensionScore(
            name="role_clarity",
            status="blocked",
            value="missing_target",
            threshold=threshold,
            evidence=f"Target '{target}' not in DataFrame.",
            evidence_detail={
                "Y": target,
                "Y_variation": None,
                "X_candidates": len(candidate_features),
            },
        )

    target_values = df[target].dropna()
    if len(target_values) == 0:
        return DimensionScore(
            name="role_clarity",
            status="blocked",
            value=0.0,
            threshold=threshold,
            evidence=f"Target '{target}' has no non-null values.",
            evidence_detail={
                "Y": target,
                "Y_variation": 0.0,
                "X_candidates": len(candidate_features),
            },
        )
    unique_y = target_values.nunique()
    if unique_y <= 1:
        return DimensionScore(
            name="role_clarity",
            status="blocked",
            value=float(unique_y),
            threshold=threshold,
            evidence=f"Target '{target}' is constant ({unique_y} unique value).",
            evidence_detail={
                "Y": target,
                "Y_variation": 0.0,
                "X_candidates": len(candidate_features),
            },
        )

    # variation: for numeric, coefficient of variation-ish; for cat, normalised entropy.
    if pd.api.types.is_numeric_dtype(target_values):
        std = float(target_values.std())
        mean = float(target_values.mean())
        variation = float(std / abs(mean)) if mean != 0 else float(std > 0)
    else:
        counts = target_values.value_counts(normalize=True)
        variation = float(1.0 - counts.iloc[0])  # share of non-majority

    if not candidate_features:
        return DimensionScore(
            name="role_clarity",
            status="partial",
            value=variation,
            threshold=threshold,
            evidence=(
                f"Target '{target}' present with variation, but no candidate "
                f"features supplied."
            ),
            evidence_detail={
                "Y": target,
                "Y_variation": round(variation, 4),
                "X_candidates": 0,
            },
        )

    present_features = [f for f in candidate_features if f in df.columns]
    if not present_features:
        return DimensionScore(
            name="role_clarity",
            status="partial",
            value=variation,
            threshold=threshold,
            evidence=(
                f"Target '{target}' present, but none of the candidate "
                f"features are in the DataFrame."
            ),
            evidence_detail={
                "Y": target,
                "Y_variation": round(variation, 4),
                "X_candidates": 0,
            },
        )

    return DimensionScore(
        name="role_clarity",
        status="ok",
        value=variation,
        threshold=threshold,
        evidence=(
            f"Target '{target}' (variation={variation:.3f}) with "
            f"{len(present_features)} candidate features."
        ),
        evidence_detail={
            "Y": target,
            "Y_variation": round(variation, 4),
            "X_candidates": len(present_features),
        },
    )


def _score_measurement_reliability(df: pd.DataFrame) -> DimensionScore:
    threshold = (
        "no issues ok; 1-2 minor (sentinels/unit hints) partial; "
        "sentinels on Y/core X or units mismatch blocked"
    )

    sentinel_values: list[list[Any]] = []
    unit_mismatch: list[str] = []
    saturation_cols: list[str] = []

    if df.empty:
        return DimensionScore(
            name="measurement_reliability",
            status="blocked",
            value="empty",
            threshold=threshold,
            evidence="No rows to assess measurement reliability.",
            evidence_detail={
                "sentinel_values": [],
                "unit_mismatch": [],
                "saturation_cols": [],
            },
        )

    for col in df.columns:
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        non_null = series.dropna()
        if len(non_null) == 0:
            continue

        # Sentinel detection
        for sentinel in _SENTINEL_VALUES:
            count = int((non_null == sentinel).sum())
            # require at least 2 hits AND value clearly outside body of data
            if count >= 2:
                body_low = float(non_null[non_null != sentinel].min()) if (non_null != sentinel).any() else None
                body_high = float(non_null[non_null != sentinel].max()) if (non_null != sentinel).any() else None
                if body_low is None or sentinel < body_low - 1 or sentinel > body_high + 1:
                    sentinel_values.append([str(col), sentinel, count])
                    break  # one sentinel per column is enough

        # Unit-range hints: suffix vs observed range
        lower_name = str(col).lower()
        for suffix, (lo, hi) in _UNIT_RANGE_HINTS.items():
            if lower_name.endswith(suffix):
                vmin = float(non_null.min())
                vmax = float(non_null.max())
                if vmin < lo - 1e-9 or vmax > hi + 1e-9:
                    unit_mismatch.append(str(col))
                break

        # Naive saturation: >=10% of values equal min, plus >=10% equal max
        if len(non_null) >= 10:
            vmin = float(non_null.min())
            vmax = float(non_null.max())
            if vmax > vmin:
                min_share = (non_null == vmin).mean()
                max_share = (non_null == vmax).mean()
                if min_share >= 0.10 and max_share >= 0.10:
                    saturation_cols.append(str(col))

    issue_count = len(sentinel_values) + len(unit_mismatch) + len(saturation_cols)
    if unit_mismatch or sentinel_values:
        # unit mismatch is always blocking per spec; sentinels on core columns are blocking
        if unit_mismatch:
            status: Status = "blocked"
            evidence = f"Unit mismatch in columns {unit_mismatch}; correct at source."
        elif len(sentinel_values) >= 2:
            status = "blocked"
            evidence = f"Sentinel values detected in multiple columns: {sentinel_values}."
        else:
            status = "partial"
            evidence = f"Minor reliability issues: sentinels={sentinel_values}; document fix."
    elif saturation_cols:
        status = "partial"
        evidence = f"Possible saturation in columns {saturation_cols}; document fix."
    else:
        status = "ok"
        evidence = "No sentinel, saturation, or unit-mismatch flags detected."

    return DimensionScore(
        name="measurement_reliability",
        status=status,
        value=float(issue_count),
        threshold=threshold,
        evidence=evidence,
        evidence_detail={
            "sentinel_values": sentinel_values,
            "unit_mismatch": unit_mismatch,
            "saturation_cols": saturation_cols,
        },
    )


# ---------------------------------------------------------------------------
# Roll-up and helpers
# ---------------------------------------------------------------------------


def _roll_up(dimensions: dict[str, DimensionScore]) -> Status:
    statuses = [dim.status for dim in dimensions.values()]
    if "blocked" in statuses:
        return "blocked"
    if "partial" in statuses:
        return "partial"
    return "ok"


def _suggest_narrowed_scope(dimensions: dict[str, DimensionScore]) -> list[str]:
    suggestions: list[str] = []
    for key, dim in dimensions.items():
        if dim.status != "partial":
            continue
        if key == "sample_size":
            suggestions.append(
                "Restrict analysis to groups with adequate n; report descriptives only for the rest."
            )
        elif key == "missingness":
            suggestions.append(
                "Document imputation strategy for the worst-missing columns or drop them."
            )
        elif key == "grain":
            suggestions.append(
                "Aggregate repeated measures to the intended grain before modeling."
            )
        elif key == "time_coverage":
            suggestions.append(
                "Restrict the time window to the continuous span or resample to a coarser cadence."
            )
        elif key == "balance":
            suggestions.append(
                "Use class-balanced metrics (PR-AUC, F1) or resampling; avoid raw accuracy."
            )
        elif key == "leakage":
            suggestions.append(
                "Drop the leakage-suspect features and re-run with the remaining candidates."
            )
        elif key == "role_clarity":
            suggestions.append(
                "Confirm the target and feature set with the requester before proceeding."
            )
        elif key == "measurement_reliability":
            suggestions.append(
                "Recode sentinel values as NaN and document the fix before modeling."
            )
    return suggestions
