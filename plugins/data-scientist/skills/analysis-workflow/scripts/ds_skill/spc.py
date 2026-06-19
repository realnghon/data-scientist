"""Statistical Process Control (SPC) primitives.

Provides classical Shewhart control charts (X-bar / R, Individuals / MR,
p, c, u), Western Electric and Nelson run-rule detectors, and capability
indices (Cp, Cpk, Pp, Ppk). All formulas follow the conventions in
Montgomery's *Introduction to Statistical Quality Control* and the
AT&T / Western Electric Statistical Quality Control Handbook.

Design notes
------------
- Functions are pure: they take a DataFrame in, return a dataclass.
- scipy.stats is lazily imported only where strictly necessary; the
  module relies on numpy / pandas for the standard SPC math.
- Edge cases raise ``ValueError`` with an explicit message rather than
  returning silent NaNs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

# -- SPC constants ---------------------------------------------------------
# Source: Montgomery, "Introduction to Statistical Quality Control",
# Appendix VI / Table VI. Values rounded to 3-4 decimal places as is
# standard practice.

_SPC_CONSTANTS: dict[int, dict[str, float]] = {
    2: {"A2": 1.880, "A3": 2.659, "D3": 0.000, "D4": 3.267, "d2": 1.128, "B3": 0.000, "B4": 3.267, "c4": 0.7979, "E2": 2.660},
    3: {"A2": 1.023, "A3": 1.954, "D3": 0.000, "D4": 2.574, "d2": 1.693, "B3": 0.000, "B4": 2.568, "c4": 0.8862, "E2": 1.772},
    4: {"A2": 0.729, "A3": 1.628, "D3": 0.000, "D4": 2.282, "d2": 2.059, "B3": 0.000, "B4": 2.266, "c4": 0.9213, "E2": 1.457},
    5: {"A2": 0.577, "A3": 1.427, "D3": 0.000, "D4": 2.114, "d2": 2.326, "B3": 0.000, "B4": 2.089, "c4": 0.9400, "E2": 1.290},
    6: {"A2": 0.483, "A3": 1.287, "D3": 0.000, "D4": 2.004, "d2": 2.534, "B3": 0.030, "B4": 1.970, "c4": 0.9515, "E2": 1.184},
    7: {"A2": 0.419, "A3": 1.182, "D3": 0.076, "D4": 1.924, "d2": 2.704, "B3": 0.118, "B4": 1.882, "c4": 0.9594, "E2": 1.109},
    8: {"A2": 0.373, "A3": 1.099, "D3": 0.136, "D4": 1.864, "d2": 2.847, "B3": 0.185, "B4": 1.815, "c4": 0.9650, "E2": 1.054},
    9: {"A2": 0.337, "A3": 1.032, "D3": 0.184, "D4": 1.816, "d2": 2.970, "B3": 0.239, "B4": 1.761, "c4": 0.9693, "E2": 1.010},
    10: {"A2": 0.308, "A3": 0.975, "D3": 0.223, "D4": 1.777, "d2": 3.078, "B3": 0.284, "B4": 1.716, "c4": 0.9727, "E2": 0.975},
}

_MIN_SUBGROUP_SIZE = 2
_MAX_SUBGROUP_SIZE = 10


def _get_constants(n: int) -> dict[str, float]:
    if n < _MIN_SUBGROUP_SIZE or n > _MAX_SUBGROUP_SIZE:
        raise ValueError(
            f"Subgroup size {n} is outside the supported range "
            f"[{_MIN_SUBGROUP_SIZE}, {_MAX_SUBGROUP_SIZE}]. "
            "Use I-MR for n=1 or X-bar/S for n>10."
        )
    return _SPC_CONSTANTS[n]


# -- Dataclasses -----------------------------------------------------------


@dataclass
class RuleViolation:
    """A single special-cause rule violation on a control chart."""

    rule_set: Literal["western_electric", "nelson"]
    rule_id: str
    description: str
    affected_points: list[int] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ControlChart:
    """A computed Shewhart control chart.

    ``points`` are the plotted statistic per subgroup / sample, in order.
    ``center_line`` is the chart's centerline (x-double-bar, p-bar, c-bar).
    ``ucl`` / ``lcl`` are the upper / lower control limits (3-sigma).
    For variable-n p / u charts the limits become per-point; in that
    case ``ucl`` and ``lcl`` carry the average-n limit and the
    ``variable_limits`` attribute holds per-point pairs.
    """

    chart_type: str
    points: list[float]
    center_line: float
    ucl: float
    lcl: float
    subgroup_size: int | list[int]
    violations: list[RuleViolation] = field(default_factory=list)
    sigma: float | None = None
    variable_limits: list[tuple[float, float]] | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "points": list(self.points),
            "center_line": self.center_line,
            "ucl": self.ucl,
            "lcl": self.lcl,
            "subgroup_size": self.subgroup_size,
            "violations": [v.as_dict() for v in self.violations],
            "sigma": self.sigma,
            "variable_limits": self.variable_limits,
            "extras": dict(self.extras),
        }


@dataclass
class CapabilityResult:
    """Process-capability summary for a single measurement."""

    name: str
    n: int
    mean: float
    std_short_term: float
    std_long_term: float
    cp: float | None
    cpk: float
    pp: float | None
    ppk: float
    interpretation: str
    min_n_warning: bool
    lsl: float | None = None
    usl: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# -- Helpers ---------------------------------------------------------------


def _validate_frame(df: pd.DataFrame, required_cols: list[str]) -> pd.DataFrame:
    if df is None or len(df) == 0:
        raise ValueError("Input DataFrame is empty.")
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")
    return df[required_cols].copy()


def _clean_numeric(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    values = values[~np.isnan(values)]
    return values


# -- X-bar / R chart -------------------------------------------------------


def xbar_r_chart(
    df: pd.DataFrame,
    value_col: str,
    subgroup_col: str,
) -> ControlChart:
    """X-bar / R chart for rational subgroups of size 2-10.

    Returns the X-bar component (means chart). The within-subgroup
    estimate of sigma is exposed via ``extras['r_bar']`` and the chart's
    ``sigma`` field for downstream use (e.g. capability).
    """

    sub = _validate_frame(df, [value_col, subgroup_col]).dropna()
    if sub.empty:
        raise ValueError("No non-null rows for X-bar/R chart.")

    grouped = sub.groupby(subgroup_col, sort=True)
    sizes = grouped.size()
    unique_sizes = sizes.unique()
    if len(unique_sizes) != 1:
        raise ValueError(
            "X-bar/R requires constant subgroup size; got sizes "
            f"{sorted(set(int(s) for s in unique_sizes))}. "
            "Use individuals_mr_chart for variable / single observations."
        )
    n = int(unique_sizes[0])
    constants = _get_constants(n)

    means = grouped[value_col].mean().to_numpy(dtype=float)
    ranges = (grouped[value_col].max() - grouped[value_col].min()).to_numpy(dtype=float)

    if len(means) < 2:
        raise ValueError("X-bar/R requires at least 2 subgroups.")

    x_double_bar = float(np.mean(means))
    r_bar = float(np.mean(ranges))
    sigma_within = r_bar / constants["d2"] if constants["d2"] > 0 else float("nan")
    ucl = x_double_bar + constants["A2"] * r_bar
    lcl = x_double_bar - constants["A2"] * r_bar

    return ControlChart(
        chart_type="xbar_r",
        points=[float(x) for x in means],
        center_line=x_double_bar,
        ucl=float(ucl),
        lcl=float(lcl),
        subgroup_size=n,
        sigma=float(sigma_within),
        extras={
            "r_bar": r_bar,
            "ranges": [float(r) for r in ranges],
            "r_ucl": float(constants["D4"] * r_bar),
            "r_lcl": float(constants["D3"] * r_bar),
            "sigma_within": float(sigma_within),
        },
    )


# -- Individuals / Moving-Range chart --------------------------------------


def individuals_mr_chart(
    df: pd.DataFrame,
    value_col: str,
    time_col: str | None = None,
) -> ControlChart:
    """Individuals (I) chart with companion moving-range estimate.

    Uses MR-bar / d2 (n=2) to estimate short-term sigma; control limits
    are then mu +/- 3 * sigma_within, equivalent to mu +/- E2 * MR-bar.
    """

    cols = [value_col] + ([time_col] if time_col else [])
    sub = _validate_frame(df, cols)
    if time_col:
        sub = sub.sort_values(time_col, kind="stable")
    sub = sub.dropna(subset=[value_col])

    values = sub[value_col].to_numpy(dtype=float)
    if len(values) < 2:
        raise ValueError("I-MR requires at least 2 observations.")

    moving_ranges = np.abs(np.diff(values))
    mr_bar = float(np.mean(moving_ranges))
    constants = _get_constants(2)  # MR is always pairs
    sigma_within = mr_bar / constants["d2"]
    mean_value = float(np.mean(values))

    ucl = mean_value + constants["E2"] * mr_bar
    lcl = mean_value - constants["E2"] * mr_bar

    return ControlChart(
        chart_type="individuals_mr",
        points=[float(v) for v in values],
        center_line=mean_value,
        ucl=float(ucl),
        lcl=float(lcl),
        subgroup_size=1,
        sigma=float(sigma_within),
        extras={
            "mr_bar": mr_bar,
            "moving_ranges": [float(m) for m in moving_ranges],
            "mr_ucl": float(constants["D4"] * mr_bar),
            "mr_lcl": float(constants["D3"] * mr_bar),
            "sigma_within": float(sigma_within),
        },
    )


# -- p-chart ---------------------------------------------------------------


def p_chart(
    df: pd.DataFrame,
    defect_col: str,
    sample_size_col: str,
    time_col: str | None = None,
) -> ControlChart:
    """Fraction-defective (p) chart. Handles variable sample size."""

    cols = [defect_col, sample_size_col] + ([time_col] if time_col else [])
    sub = _validate_frame(df, cols)
    if time_col:
        sub = sub.sort_values(time_col, kind="stable")
    sub = sub.dropna(subset=[defect_col, sample_size_col])
    if sub.empty:
        raise ValueError("No non-null rows for p-chart.")

    defects = sub[defect_col].to_numpy(dtype=float)
    sizes = sub[sample_size_col].to_numpy(dtype=float)
    if np.any(sizes <= 0):
        raise ValueError("p-chart requires positive sample sizes.")
    if np.any(defects < 0) or np.any(defects > sizes):
        raise ValueError("Defect counts must be between 0 and the sample size.")

    proportions = defects / sizes
    p_bar = float(np.sum(defects) / np.sum(sizes))
    n_bar = float(np.mean(sizes))

    # average-n limits (also exposed) plus per-point variable limits
    base_sigma = np.sqrt(p_bar * (1 - p_bar) / n_bar) if n_bar > 0 else 0.0
    ucl_avg = float(min(1.0, p_bar + 3 * base_sigma))
    lcl_avg = float(max(0.0, p_bar - 3 * base_sigma))

    variable_limits: list[tuple[float, float]] = []
    for n_i in sizes:
        s_i = np.sqrt(p_bar * (1 - p_bar) / n_i) if n_i > 0 else 0.0
        ucl_i = min(1.0, p_bar + 3 * s_i)
        lcl_i = max(0.0, p_bar - 3 * s_i)
        variable_limits.append((float(lcl_i), float(ucl_i)))

    constant_size = bool(np.all(sizes == sizes[0]))
    subgroup_size: int | list[int] = (
        int(sizes[0]) if constant_size else [int(s) for s in sizes]
    )

    return ControlChart(
        chart_type="p",
        points=[float(p) for p in proportions],
        center_line=p_bar,
        ucl=ucl_avg,
        lcl=lcl_avg,
        subgroup_size=subgroup_size,
        sigma=float(base_sigma),
        variable_limits=None if constant_size else variable_limits,
        extras={
            "p_bar": p_bar,
            "n_bar": n_bar,
            "sample_sizes": [int(s) for s in sizes],
        },
    )


# -- c-chart ---------------------------------------------------------------


def c_chart(
    df: pd.DataFrame,
    defect_count_col: str,
    time_col: str | None = None,
) -> ControlChart:
    """Count-of-defects (c) chart. Equal opportunity per unit assumed."""

    cols = [defect_count_col] + ([time_col] if time_col else [])
    sub = _validate_frame(df, cols)
    if time_col:
        sub = sub.sort_values(time_col, kind="stable")
    sub = sub.dropna(subset=[defect_count_col])
    if sub.empty:
        raise ValueError("No non-null rows for c-chart.")

    counts = sub[defect_count_col].to_numpy(dtype=float)
    if np.any(counts < 0):
        raise ValueError("Defect counts must be non-negative.")

    c_bar = float(np.mean(counts))
    sigma = np.sqrt(c_bar)
    ucl = float(c_bar + 3 * sigma)
    lcl = float(max(0.0, c_bar - 3 * sigma))

    return ControlChart(
        chart_type="c",
        points=[float(c) for c in counts],
        center_line=c_bar,
        ucl=ucl,
        lcl=lcl,
        subgroup_size=1,
        sigma=float(sigma),
        extras={"c_bar": c_bar},
    )


# -- u-chart ---------------------------------------------------------------


def u_chart(
    df: pd.DataFrame,
    defect_count_col: str,
    opportunities_col: str,
    time_col: str | None = None,
) -> ControlChart:
    """Defects-per-unit (u) chart. Handles variable opportunity size."""

    cols = [defect_count_col, opportunities_col] + ([time_col] if time_col else [])
    sub = _validate_frame(df, cols)
    if time_col:
        sub = sub.sort_values(time_col, kind="stable")
    sub = sub.dropna(subset=[defect_count_col, opportunities_col])
    if sub.empty:
        raise ValueError("No non-null rows for u-chart.")

    counts = sub[defect_count_col].to_numpy(dtype=float)
    opportunities = sub[opportunities_col].to_numpy(dtype=float)
    if np.any(opportunities <= 0):
        raise ValueError("u-chart opportunities must be positive.")
    if np.any(counts < 0):
        raise ValueError("Defect counts must be non-negative.")

    u_values = counts / opportunities
    u_bar = float(np.sum(counts) / np.sum(opportunities))
    n_bar = float(np.mean(opportunities))

    base_sigma = np.sqrt(u_bar / n_bar) if n_bar > 0 else 0.0
    ucl_avg = float(u_bar + 3 * base_sigma)
    lcl_avg = float(max(0.0, u_bar - 3 * base_sigma))

    variable_limits: list[tuple[float, float]] = []
    for n_i in opportunities:
        s_i = np.sqrt(u_bar / n_i) if n_i > 0 else 0.0
        ucl_i = u_bar + 3 * s_i
        lcl_i = max(0.0, u_bar - 3 * s_i)
        variable_limits.append((float(lcl_i), float(ucl_i)))

    constant_size = bool(np.all(opportunities == opportunities[0]))
    subgroup_size: int | list[int] = (
        int(opportunities[0]) if constant_size else [int(o) for o in opportunities]
    )

    return ControlChart(
        chart_type="u",
        points=[float(u) for u in u_values],
        center_line=u_bar,
        ucl=ucl_avg,
        lcl=lcl_avg,
        subgroup_size=subgroup_size,
        sigma=float(base_sigma),
        variable_limits=None if constant_size else variable_limits,
        extras={
            "u_bar": u_bar,
            "n_bar": n_bar,
            "opportunities": [float(o) for o in opportunities],
        },
    )


# -- Run-rule machinery ----------------------------------------------------


def _zones(chart: ControlChart) -> tuple[float, float, float] | None:
    """Return (sigma_1, sigma_2, sigma_3) widths around the centerline.

    The classic SPC 3-sigma limits split the band into three equal zones. We
    derive sigma from the 3-sigma half-width of the limits. p/c/u charts clamp
    one limit (UCL at 1.0, LCL at 0), which would shrink that side's half-width
    and distort the zones — so we take the *wider* of the two halves, which on a
    clamped chart is the unclamped (correct) side and on a symmetric chart is
    either. (X-bar carries within-subgroup sigma in ``chart.sigma``, not the
    plotted-mean SE, so the limits — not ``chart.sigma`` — are the right source.)
    """

    if chart.ucl is None or chart.lcl is None:
        return None
    half = max(chart.ucl - chart.center_line, chart.center_line - chart.lcl)
    if not np.isfinite(half) or half <= 0:
        return None
    sigma = half / 3.0
    return sigma, 2 * sigma, 3 * sigma


def apply_western_electric_rules(chart: ControlChart) -> ControlChart:
    """Apply Western Electric rules 1-4 to ``chart`` and return the chart.

    Mutates ``chart.violations`` in place (and also returns it for chaining).
    """

    zones = _zones(chart)
    pts = np.asarray(chart.points, dtype=float)
    cl = chart.center_line
    violations: list[RuleViolation] = []

    if zones is None:
        return chart
    one_sigma, two_sigma, three_sigma = zones

    # Rule 1: one point beyond 3-sigma (outside control limits)
    rule1_idx = [
        int(i) for i, v in enumerate(pts)
        if v > cl + three_sigma or v < cl - three_sigma
    ]
    if rule1_idx:
        violations.append(
            RuleViolation(
                rule_set="western_electric",
                rule_id="WE-1",
                description="One point beyond 3-sigma (outside control limits).",
                affected_points=rule1_idx,
            )
        )

    # Rule 2: 2 of 3 consecutive points beyond 2-sigma on the same side
    rule2_idx = _windowed_on_side(pts, cl, two_sigma, window=3, count=2)
    if rule2_idx:
        violations.append(
            RuleViolation(
                rule_set="western_electric",
                rule_id="WE-2",
                description="Two of three consecutive points beyond 2-sigma on the same side of the centerline.",
                affected_points=rule2_idx,
            )
        )

    # Rule 3: 4 of 5 consecutive points beyond 1-sigma on the same side
    rule3_idx = _windowed_on_side(pts, cl, one_sigma, window=5, count=4)
    if rule3_idx:
        violations.append(
            RuleViolation(
                rule_set="western_electric",
                rule_id="WE-3",
                description="Four of five consecutive points beyond 1-sigma on the same side of the centerline.",
                affected_points=rule3_idx,
            )
        )

    # Rule 4: 8 consecutive points on the same side of the centerline
    rule4_idx = _consecutive_on_side(pts, cl, count=8)
    if rule4_idx:
        violations.append(
            RuleViolation(
                rule_set="western_electric",
                rule_id="WE-4",
                description="Eight consecutive points on the same side of the centerline.",
                affected_points=rule4_idx,
            )
        )

    chart.violations = chart.violations + violations
    return chart


def apply_nelson_rules(chart: ControlChart) -> ControlChart:
    """Apply Nelson rules 1-8 to ``chart`` and return the chart.

    Nelson rules (Nelson, 1984):

    1. One point beyond 3-sigma.
    2. Nine points in a row on the same side of the centerline.
    3. Six points in a row, all increasing or all decreasing.
    4. Fourteen points in a row alternating up and down.
    5. Two out of three consecutive points beyond 2-sigma on the same side.
    6. Four out of five consecutive points beyond 1-sigma on the same side.
    7. Fifteen points in a row within 1-sigma (stratification).
    8. Eight points in a row outside 1-sigma on either side (mixture).
    """

    zones = _zones(chart)
    pts = np.asarray(chart.points, dtype=float)
    cl = chart.center_line
    violations: list[RuleViolation] = []

    if zones is None:
        return chart
    one_sigma, two_sigma, three_sigma = zones

    # Nelson-1: one point beyond 3-sigma
    n1 = [int(i) for i, v in enumerate(pts) if v > cl + three_sigma or v < cl - three_sigma]
    if n1:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-1",
                description="One point beyond 3-sigma.",
                affected_points=n1,
            )
        )

    # Nelson-2: nine points in a row on the same side of the centerline
    n2 = _consecutive_on_side(pts, cl, count=9)
    if n2:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-2",
                description="Nine points in a row on the same side of the centerline.",
                affected_points=n2,
            )
        )

    # Nelson-3: six points in a row steadily increasing or decreasing
    n3 = _monotonic_run(pts, count=6)
    if n3:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-3",
                description="Six points in a row, all increasing or all decreasing.",
                affected_points=n3,
            )
        )

    # Nelson-4: fourteen points in a row alternating up and down
    n4 = _alternating_run(pts, count=14)
    if n4:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-4",
                description="Fourteen points in a row alternating up and down.",
                affected_points=n4,
            )
        )

    # Nelson-5: 2 of 3 beyond 2-sigma on the same side
    n5 = _windowed_on_side(pts, cl, two_sigma, window=3, count=2)
    if n5:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-5",
                description="Two of three consecutive points beyond 2-sigma on the same side of the centerline.",
                affected_points=n5,
            )
        )

    # Nelson-6: 4 of 5 beyond 1-sigma on the same side
    n6 = _windowed_on_side(pts, cl, one_sigma, window=5, count=4)
    if n6:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-6",
                description="Four of five consecutive points beyond 1-sigma on the same side of the centerline.",
                affected_points=n6,
            )
        )

    # Nelson-7: 15 points in a row within 1-sigma (either side) -- stratification
    n7 = _consecutive_within_one_sigma(pts, cl, one_sigma, count=15)
    if n7:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-7",
                description="Fifteen points in a row within 1-sigma of the centerline (stratification).",
                affected_points=n7,
            )
        )

    # Nelson-8: 8 points in a row outside 1-sigma on either side -- mixture
    n8 = _consecutive_outside_one_sigma(pts, cl, one_sigma, count=8)
    if n8:
        violations.append(
            RuleViolation(
                rule_set="nelson",
                rule_id="Nelson-8",
                description="Eight points in a row outside 1-sigma on either side (mixture).",
                affected_points=n8,
            )
        )

    chart.violations = chart.violations + violations
    return chart


def _consecutive_on_side(pts: np.ndarray, cl: float, count: int) -> list[int]:
    """Indices participating in any run of ``count`` consecutive points on
    the same side of the centerline (points exactly at cl break the run)."""

    above_streak = 0
    below_streak = 0
    affected: set[int] = set()
    for i, v in enumerate(pts):
        if v > cl:
            above_streak += 1
            below_streak = 0
        elif v < cl:
            below_streak += 1
            above_streak = 0
        else:
            above_streak = 0
            below_streak = 0
        if above_streak >= count or below_streak >= count:
            # mark the current window
            for j in range(i - count + 1, i + 1):
                affected.add(int(j))
    return sorted(affected)


def _windowed_on_side(
    pts: np.ndarray,
    cl: float,
    threshold: float,
    window: int,
    count: int,
) -> list[int]:
    """Indices in any window of length ``window`` where at least ``count``
    points lie beyond ``threshold`` on the SAME side of the centerline."""

    affected: set[int] = set()
    n = len(pts)
    if n < window:
        return []
    above = pts > cl + threshold
    below = pts < cl - threshold
    for start in range(n - window + 1):
        win_above = above[start : start + window]
        win_below = below[start : start + window]
        if win_above.sum() >= count or win_below.sum() >= count:
            # mark only the points that are actually beyond the threshold
            for j in range(start, start + window):
                if above[j] or below[j]:
                    affected.add(int(j))
    return sorted(affected)


def _monotonic_run(pts: np.ndarray, count: int) -> list[int]:
    """Indices in any monotone (strictly inc or dec) run of length ``count``."""

    affected: set[int] = set()
    if len(pts) < count:
        return []
    up_streak = 1
    down_streak = 1
    for i in range(1, len(pts)):
        if pts[i] > pts[i - 1]:
            up_streak += 1
            down_streak = 1
        elif pts[i] < pts[i - 1]:
            down_streak += 1
            up_streak = 1
        else:
            up_streak = 1
            down_streak = 1
        if up_streak >= count or down_streak >= count:
            for j in range(i - count + 1, i + 1):
                affected.add(int(j))
    return sorted(affected)


def _alternating_run(pts: np.ndarray, count: int) -> list[int]:
    """Indices in any alternating-direction run of length ``count``.

    A run of ``count`` points has ``count - 1`` consecutive diffs whose
    signs strictly alternate (no zeros, no two consecutive same-sign
    diffs). We mark every point that participates in any such run.
    """

    affected: set[int] = set()
    if len(pts) < count:
        return []
    diffs = np.sign(np.diff(pts))
    # diff_streak counts the length of the current run of alternating diffs.
    # A diff_streak of k means k+1 consecutive points alternate.
    diff_streak = 0
    for i, d in enumerate(diffs):
        if d == 0:
            diff_streak = 0
            continue
        if i == 0 or diffs[i - 1] == 0:
            diff_streak = 1
        elif d != diffs[i - 1]:
            diff_streak += 1
        else:
            diff_streak = 1
        if diff_streak >= count - 1:
            # run ends at point index i + 1
            end = i + 1
            for j in range(end - count + 1, end + 1):
                affected.add(int(j))
    return sorted(affected)


def _consecutive_within_one_sigma(
    pts: np.ndarray, cl: float, one_sigma: float, count: int
) -> list[int]:
    affected: set[int] = set()
    streak = 0
    for i, v in enumerate(pts):
        if abs(v - cl) < one_sigma:
            streak += 1
        else:
            streak = 0
        if streak >= count:
            for j in range(i - count + 1, i + 1):
                affected.add(int(j))
    return sorted(affected)


def _consecutive_outside_one_sigma(
    pts: np.ndarray, cl: float, one_sigma: float, count: int
) -> list[int]:
    affected: set[int] = set()
    streak = 0
    for i, v in enumerate(pts):
        if abs(v - cl) > one_sigma:
            streak += 1
        else:
            streak = 0
        if streak >= count:
            for j in range(i - count + 1, i + 1):
                affected.add(int(j))
    return sorted(affected)


# -- Capability indices ----------------------------------------------------


_MIN_RECOMMENDED_N = 30


def _short_term_sigma(values: np.ndarray) -> float:
    """Estimate short-term sigma from moving range (MR-bar / d2, n=2)."""

    if len(values) < 2:
        raise ValueError("Cannot estimate short-term sigma with fewer than 2 values.")
    mr_bar = float(np.mean(np.abs(np.diff(values))))
    d2 = _SPC_CONSTANTS[2]["d2"]
    return mr_bar / d2


def _coerce_values(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float).ravel()
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        raise ValueError("No finite values supplied for capability calculation.")
    return arr


def _check_limits(lsl: float | None, usl: float | None) -> None:
    if lsl is None and usl is None:
        raise ValueError("At least one of LSL or USL must be supplied.")
    if lsl is not None and usl is not None and lsl >= usl:
        raise ValueError("LSL must be strictly less than USL.")


def cp(
    values: Any,
    lsl: float | None,
    usl: float | None,
    sigma_short_term: float | None = None,
) -> float:
    """Process potential capability index (short-term)."""

    if lsl is None or usl is None:
        raise ValueError("Cp requires both LSL and USL; use Cpk for one-sided spec.")
    arr = _coerce_values(values)
    _check_limits(lsl, usl)
    sigma = sigma_short_term if sigma_short_term is not None else _short_term_sigma(arr)
    if sigma <= 0:
        raise ValueError("Short-term sigma must be positive.")
    return float((usl - lsl) / (6.0 * sigma))


def cpk(
    values: Any,
    lsl: float | None,
    usl: float | None,
    sigma_short_term: float | None = None,
) -> float:
    """Cpk; works for one- or two-sided specs."""

    arr = _coerce_values(values)
    _check_limits(lsl, usl)
    sigma = sigma_short_term if sigma_short_term is not None else _short_term_sigma(arr)
    if sigma <= 0:
        raise ValueError("Short-term sigma must be positive.")
    mu = float(np.mean(arr))
    candidates: list[float] = []
    if usl is not None:
        candidates.append((usl - mu) / (3.0 * sigma))
    if lsl is not None:
        candidates.append((mu - lsl) / (3.0 * sigma))
    return float(min(candidates))


def pp(values: Any, lsl: float | None, usl: float | None) -> float:
    """Process performance (long-term) potential index."""

    if lsl is None or usl is None:
        raise ValueError("Pp requires both LSL and USL; use Ppk for one-sided spec.")
    arr = _coerce_values(values)
    _check_limits(lsl, usl)
    sigma = float(np.std(arr, ddof=1))
    if sigma <= 0:
        raise ValueError("Long-term sigma must be positive.")
    return float((usl - lsl) / (6.0 * sigma))


def ppk(values: Any, lsl: float | None, usl: float | None) -> float:
    """Ppk; works for one- or two-sided specs."""

    arr = _coerce_values(values)
    _check_limits(lsl, usl)
    sigma = float(np.std(arr, ddof=1))
    if sigma <= 0:
        raise ValueError("Long-term sigma must be positive.")
    mu = float(np.mean(arr))
    candidates: list[float] = []
    if usl is not None:
        candidates.append((usl - mu) / (3.0 * sigma))
    if lsl is not None:
        candidates.append((mu - lsl) / (3.0 * sigma))
    return float(min(candidates))


def _interpret_cpk(value: float) -> str:
    """Standard interpretation buckets (see manufacturing-playbook.md)."""

    if value < 1.0:
        return "incapable"
    if value < 1.33:
        return "marginal"
    if value < 1.67:
        return "adequate"
    return "strong"


def capability_summary(
    values: Any,
    lsl: float | None,
    usl: float | None,
    name: str = "",
) -> CapabilityResult:
    """All-in-one capability summary with interpretation and n-warning."""

    arr = _coerce_values(values)
    _check_limits(lsl, usl)
    n = int(len(arr))
    mean = float(np.mean(arr))
    sigma_long = float(np.std(arr, ddof=1)) if n > 1 else float("nan")
    sigma_short = _short_term_sigma(arr) if n >= 2 else float("nan")

    cp_value: float | None
    pp_value: float | None
    if lsl is not None and usl is not None:
        cp_value = cp(arr, lsl, usl, sigma_short_term=sigma_short)
        pp_value = pp(arr, lsl, usl)
    else:
        cp_value = None
        pp_value = None

    cpk_value = cpk(arr, lsl, usl, sigma_short_term=sigma_short)
    ppk_value = ppk(arr, lsl, usl)

    return CapabilityResult(
        name=name,
        n=n,
        mean=mean,
        std_short_term=sigma_short,
        std_long_term=sigma_long,
        cp=cp_value,
        cpk=cpk_value,
        pp=pp_value,
        ppk=ppk_value,
        interpretation=_interpret_cpk(cpk_value),
        min_n_warning=n < _MIN_RECOMMENDED_N,
        lsl=lsl,
        usl=usl,
    )


__all__ = [
    "ControlChart",
    "RuleViolation",
    "CapabilityResult",
    "xbar_r_chart",
    "individuals_mr_chart",
    "p_chart",
    "c_chart",
    "u_chart",
    "apply_western_electric_rules",
    "apply_nelson_rules",
    "cp",
    "cpk",
    "pp",
    "ppk",
    "capability_summary",
]
