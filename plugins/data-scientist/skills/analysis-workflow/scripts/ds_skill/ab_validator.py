"""A/B experiment validator: SRM, effect-size with CI, MDE, and a full report.

See `method-registry.md` section "A/B / Experiment Validation".
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


def _lazy_scipy_stats():
    try:
        from scipy import stats  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive
        raise ImportError(
            "scipy is required for A/B validator helpers; install scipy."
        ) from exc
    return stats


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ABValidationReport:
    srm: dict
    groups_summary: dict
    effect_sizes: list[dict] = field(default_factory=list)
    mde: float = float("nan")
    interpretation: str = ""
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # NaN is not json-serializable; replace
        if isinstance(d.get("mde"), float) and math.isnan(d["mde"]):
            d["mde"] = None
        return d


# ---------------------------------------------------------------------------
# SRM
# ---------------------------------------------------------------------------


def sample_ratio_mismatch(
    counts: dict[str, int],
    expected_ratios: dict[str, float] | None = None,
) -> dict:
    """Chi-square goodness-of-fit test for sample ratio mismatch.

    ``counts`` maps arm name -> observed count. ``expected_ratios`` maps arm name
    to expected proportion (must sum to 1); defaults to equal split.
    """
    if not counts or len(counts) < 2:
        raise ValueError("SRM requires counts for at least two arms.")
    if any(v < 0 for v in counts.values()):
        raise ValueError("Counts must be non-negative.")

    arms = list(counts.keys())
    observed = np.array([counts[a] for a in arms], dtype=float)
    total = float(observed.sum())
    if total <= 0:
        raise ValueError("Total count must be > 0 for SRM.")

    if expected_ratios is None:
        ratios = {a: 1.0 / len(arms) for a in arms}
    else:
        missing = [a for a in arms if a not in expected_ratios]
        if missing:
            raise ValueError(f"expected_ratios missing arms: {missing}")
        s = sum(expected_ratios[a] for a in arms)
        if not math.isclose(s, 1.0, abs_tol=1e-6):
            raise ValueError(f"expected_ratios must sum to 1.0 (got {s}).")
        ratios = {a: float(expected_ratios[a]) for a in arms}

    expected = np.array([ratios[a] * total for a in arms], dtype=float)
    stats = _lazy_scipy_stats()
    chi2, p_value = stats.chisquare(observed, expected)

    observed_ratios = {a: float(observed[i] / total) for i, a in enumerate(arms)}
    passed = bool(p_value >= 0.001)  # conventional SRM threshold
    return {
        "chi_square": float(chi2),
        "p_value": float(p_value),
        "observed_counts": {a: int(counts[a]) for a in arms},
        "observed_ratios": observed_ratios,
        "expected_ratios": ratios,
        "total": int(total),
        "passed": passed,
        "threshold": 0.001,
    }


# ---------------------------------------------------------------------------
# Effect size with CI
# ---------------------------------------------------------------------------


def effect_size_with_ci(
    a: np.ndarray,
    b: np.ndarray,
    metric: str = "mean",
    confidence: float = 0.95,
) -> dict:
    """Compute an effect-size estimate with a CI.

    ``metric`` ∈ {"mean", "proportion"}.
    """
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    a_arr = a_arr[~np.isnan(a_arr)]
    b_arr = b_arr[~np.isnan(b_arr)]
    if len(a_arr) < 2 or len(b_arr) < 2:
        raise ValueError("Need at least 2 non-null observations per arm.")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0,1).")

    stats = _lazy_scipy_stats()
    z = float(stats.norm.ppf(0.5 + confidence / 2.0))

    if metric == "mean":
        mean_a = float(np.mean(a_arr))
        mean_b = float(np.mean(b_arr))
        var_a = float(np.var(a_arr, ddof=1))
        var_b = float(np.var(b_arr, ddof=1))
        diff = mean_b - mean_a
        # Welch SE
        se = math.sqrt(var_a / len(a_arr) + var_b / len(b_arr))
        ci = (diff - z * se, diff + z * se)

        # Cohen's d (pooled SD)
        n_a, n_b = len(a_arr), len(b_arr)
        pooled = math.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
        cohens_d = (diff / pooled) if pooled > 0 else float("nan")

        return {
            "metric": "mean",
            "mean_a": mean_a,
            "mean_b": mean_b,
            "difference": float(diff),
            "ci_low": float(ci[0]),
            "ci_high": float(ci[1]),
            "confidence": float(confidence),
            "cohens_d": float(cohens_d),
            "n_a": int(n_a),
            "n_b": int(n_b),
        }

    if metric == "proportion":
        # Treat as 0/1 counts; non-{0,1} values get coerced to bool.
        a_bin = (a_arr != 0).astype(float)
        b_bin = (b_arr != 0).astype(float)
        p_a = float(np.mean(a_bin))
        p_b = float(np.mean(b_bin))
        n_a = len(a_bin)
        n_b = len(b_bin)
        rd = p_b - p_a  # risk difference
        se_rd = math.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
        ci_rd = (rd - z * se_rd, rd + z * se_rd)

        # Relative risk and odds ratio (guard zero)
        rr = (p_b / p_a) if p_a > 0 else float("inf")
        odds_a = p_a / (1 - p_a) if 0 < p_a < 1 else float("nan")
        odds_b = p_b / (1 - p_b) if 0 < p_b < 1 else float("nan")
        if not (math.isnan(odds_a) or math.isnan(odds_b)) and odds_a > 0:
            or_ = odds_b / odds_a
        else:
            or_ = float("nan")

        return {
            "metric": "proportion",
            "p_a": p_a,
            "p_b": p_b,
            "risk_difference": float(rd),
            "ci_low": float(ci_rd[0]),
            "ci_high": float(ci_rd[1]),
            "relative_risk": float(rr) if not math.isinf(rr) else None,
            "odds_ratio": float(or_) if not math.isnan(or_) else None,
            "confidence": float(confidence),
            "n_a": int(n_a),
            "n_b": int(n_b),
        }

    raise ValueError(f"Unknown metric: {metric!r}. Expected 'mean' or 'proportion'.")


# ---------------------------------------------------------------------------
# Minimum detectable effect
# ---------------------------------------------------------------------------


def minimum_detectable_effect(
    baseline: float,
    n_per_group: int,
    alpha: float = 0.05,
    power: float = 0.8,
    metric: str = "proportion",
) -> float:
    """Standard MDE formula.

    For ``proportion``: MDE = (z_{1-α/2} + z_{power}) * sqrt(2*p*(1-p)/n).
    For ``mean``: ``baseline`` is interpreted as the population SD, and
    MDE = (z_{1-α/2} + z_{power}) * sqrt(2/n) * sd.
    """
    if n_per_group <= 1:
        raise ValueError("n_per_group must be > 1.")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0,1).")
    if not 0.0 < power < 1.0:
        raise ValueError("power must be in (0,1).")

    stats = _lazy_scipy_stats()
    z_alpha = float(stats.norm.ppf(1.0 - alpha / 2.0))
    z_beta = float(stats.norm.ppf(power))

    if metric == "proportion":
        if not 0.0 <= baseline <= 1.0:
            raise ValueError("For proportion, baseline must be in [0,1].")
        se = math.sqrt(2.0 * baseline * (1.0 - baseline) / n_per_group)
        return float((z_alpha + z_beta) * se)
    if metric == "mean":
        if baseline < 0:
            raise ValueError("For mean MDE, baseline (interpreted as SD) must be >= 0.")
        se = math.sqrt(2.0 / n_per_group) * baseline
        return float((z_alpha + z_beta) * se)

    raise ValueError(f"Unknown metric: {metric!r}.")


# ---------------------------------------------------------------------------
# Full validator
# ---------------------------------------------------------------------------


def validate_ab_test(
    df: pd.DataFrame,
    group_col: str,
    outcome_col: str,
    expected_ratios: dict | None = None,
) -> ABValidationReport:
    """Run SRM, per-group summary, pairwise effects, and an MDE estimate."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("DataFrame is empty.")
    for c in (group_col, outcome_col):
        if c not in df.columns:
            raise ValueError(f"Column not in DataFrame: {c}")

    warnings_: list[str] = []
    sub = df[[group_col, outcome_col]].dropna(subset=[group_col])
    if sub.empty:
        raise ValueError("No rows after dropping null group assignments.")

    counts = sub[group_col].astype(str).value_counts().to_dict()
    if len(counts) < 2:
        raise ValueError("Need at least 2 arms for A/B validation.")

    srm = sample_ratio_mismatch({str(k): int(v) for k, v in counts.items()}, expected_ratios)
    if not srm["passed"]:
        warnings_.append(
            f"sample ratio mismatch (p={srm['p_value']:.4f} < threshold {srm['threshold']})"
        )

    # detect outcome type
    outcome = sub[outcome_col]
    is_numeric = pd.api.types.is_numeric_dtype(outcome)
    unique_vals = outcome.dropna().unique()
    is_binary = is_numeric and set(np.unique(outcome.dropna()).astype(float)) <= {0.0, 1.0}

    summary: dict[str, dict[str, float]] = {}
    for arm, g in sub.groupby(group_col):
        vals = pd.to_numeric(g[outcome_col], errors="coerce").dropna().to_numpy()
        if len(vals) == 0:
            summary[str(arm)] = {"n": 0, "mean": float("nan")}
            continue
        if is_binary:
            summary[str(arm)] = {"n": int(len(vals)), "proportion": float(np.mean(vals))}
        elif is_numeric:
            summary[str(arm)] = {
                "n": int(len(vals)),
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            }
        else:
            summary[str(arm)] = {"n": int(len(vals))}

    arms = sorted(summary.keys())
    effect_sizes: list[dict] = []
    if is_numeric:
        metric = "proportion" if is_binary else "mean"
        for i, a in enumerate(arms):
            for b in arms[i + 1:]:
                a_arr = pd.to_numeric(sub.loc[sub[group_col].astype(str) == a, outcome_col], errors="coerce").to_numpy()
                b_arr = pd.to_numeric(sub.loc[sub[group_col].astype(str) == b, outcome_col], errors="coerce").to_numpy()
                try:
                    eff = effect_size_with_ci(a_arr, b_arr, metric=metric)
                    eff["arm_a"] = a
                    eff["arm_b"] = b
                    effect_sizes.append(eff)
                except ValueError as e:
                    warnings_.append(f"could not compute effect size {a} vs {b}: {e}")
    else:
        warnings_.append("outcome is non-numeric; skipping effect-size computation")

    # MDE on smallest arm
    n_min = min((summary[a].get("n", 0) for a in arms), default=0)
    mde = float("nan")
    if is_binary and n_min > 1:
        baseline = float(np.mean(pd.to_numeric(sub[outcome_col], errors="coerce").dropna()))
        mde = minimum_detectable_effect(baseline, n_min, metric="proportion")
    elif is_numeric and not is_binary and n_min > 1:
        sd = float(pd.to_numeric(sub[outcome_col], errors="coerce").dropna().std(ddof=1))
        mde = minimum_detectable_effect(sd, n_min, metric="mean")

    # Interpretation
    if not srm["passed"]:
        interp = "SRM FAILED — do not read the result until traffic split is fixed"
    elif not effect_sizes:
        interp = "SRM ok; no numeric outcome to estimate effect"
    else:
        sig = []
        for e in effect_sizes:
            lo, hi = e["ci_low"], e["ci_high"]
            if (lo > 0 and hi > 0) or (lo < 0 and hi < 0):
                sig.append(f"{e['arm_a']} vs {e['arm_b']}")
        if sig:
            interp = f"SRM ok; CI excludes zero for: {', '.join(sig)}"
        else:
            interp = "SRM ok; no pairwise CI excludes zero"

    return ABValidationReport(
        srm=srm,
        groups_summary=summary,
        effect_sizes=effect_sizes,
        mde=mde,
        interpretation=interp,
        warnings=warnings_,
    )
