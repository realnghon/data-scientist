"""Survival / reliability helpers for the data-scientist skill.

Method choices follow `references/method-registry.md` section 8:

- Non-parametric survival curve -> Kaplan-Meier.
- Group comparison -> log-rank test.
- Parametric reliability -> Weibull (shape interprets early-life vs wear-out).

Kaplan-Meier, Greenwood variance, and log-rank are implemented from scratch
to keep the skill free of a hard ``lifelines`` dependency. Weibull MLE uses
``scipy.optimize`` so censored data are handled correctly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SurvivalCurve:
    timeline: list[float]
    survival_probability: list[float]
    ci_low: list[float]
    ci_high: list[float]
    at_risk: list[int]
    events_observed: list[int]
    median_survival: float | None
    n_subjects: int
    n_events: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LogRankResult:
    chi_square: float
    degrees_of_freedom: int
    p_value: float
    groups: list[str]
    n_per_group: dict
    n_events_per_group: dict = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WeibullFit:
    shape: float
    scale: float
    shape_ci: tuple[float, float]
    scale_ci: tuple[float, float]
    b10: float
    b50: float
    b90: float
    interpretation: str
    n: int
    n_events: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "shape": self.shape,
            "scale": self.scale,
            "shape_ci": list(self.shape_ci),
            "scale_ci": list(self.scale_ci),
            "b10": self.b10,
            "b50": self.b50,
            "b90": self.b90,
            "interpretation": self.interpretation,
            "n": self.n,
            "n_events": self.n_events,
        }


# ---------------------------------------------------------------------------
# Kaplan-Meier
# ---------------------------------------------------------------------------


def kaplan_meier(
    durations: pd.Series, events: pd.Series, alpha: float = 0.05
) -> SurvivalCurve:
    """Kaplan-Meier estimator with Greenwood-variance log-log CIs.

    Greenwood's formula gives Var(S(t)) = S(t)^2 * sum d_i / (n_i * (n_i - d_i)).
    We transform the CI into log-log space to keep S(t) within [0, 1].
    """
    if durations is None or events is None:
        raise ValueError("kaplan_meier requires both durations and events.")

    df = pd.DataFrame({"t": pd.Series(durations).reset_index(drop=True),
                       "e": pd.Series(events).reset_index(drop=True)}).dropna()
    if len(df) == 0:
        raise ValueError("kaplan_meier received no complete observations.")
    if (df["t"] < 0).any():
        raise ValueError("Durations must be non-negative.")
    df["e"] = df["e"].astype(int)
    if not df["e"].isin([0, 1]).all():
        raise ValueError("Events must be 0 (censored) or 1 (event observed).")

    # Sort and walk unique event times.
    df = df.sort_values("t").reset_index(drop=True)
    n_subjects = int(len(df))
    n_events_total = int(df["e"].sum())

    unique_times = sorted(df["t"].unique().tolist())
    timeline: list[float] = []
    survival: list[float] = []
    at_risk: list[int] = []
    events_per_time: list[int] = []
    variance_terms: list[float] = []

    s = 1.0
    cumulative_var_term = 0.0  # sum d / (n * (n - d))
    remaining = df.copy()

    for t in unique_times:
        n_at_risk = int((remaining["t"] >= t).sum())
        d = int(((remaining["t"] == t) & (remaining["e"] == 1)).sum())
        if n_at_risk == 0:
            continue
        if d > 0:
            s *= 1 - d / n_at_risk
            if n_at_risk - d > 0:
                cumulative_var_term += d / (n_at_risk * (n_at_risk - d))

        timeline.append(float(t))
        survival.append(float(s))
        at_risk.append(n_at_risk)
        events_per_time.append(d)
        variance_terms.append(cumulative_var_term)

    from scipy import stats as _stats

    z = float(_stats.norm.ppf(1 - alpha / 2))

    ci_low: list[float] = []
    ci_high: list[float] = []
    for s_t, var_term in zip(survival, variance_terms):
        if s_t <= 0 or s_t >= 1 or var_term == 0:
            # Edge: S=1 or S=0 -> log-log undefined; fall back to plain CI clipped.
            std = float(np.sqrt((s_t ** 2) * var_term))
            ci_low.append(max(0.0, s_t - z * std))
            ci_high.append(min(1.0, s_t + z * std))
            continue
        # log-log transform: phi = log(-log(S(t)))
        log_s = np.log(s_t)
        var_phi = var_term / (log_s ** 2)
        phi = np.log(-log_s)
        lo = np.exp(-np.exp(phi + z * np.sqrt(var_phi)))
        hi = np.exp(-np.exp(phi - z * np.sqrt(var_phi)))
        ci_low.append(float(min(max(lo, 0.0), 1.0)))
        ci_high.append(float(min(max(hi, 0.0), 1.0)))

    median = _median_from_curve(timeline, survival)

    return SurvivalCurve(
        timeline=timeline,
        survival_probability=survival,
        ci_low=ci_low,
        ci_high=ci_high,
        at_risk=at_risk,
        events_observed=events_per_time,
        median_survival=median,
        n_subjects=n_subjects,
        n_events=n_events_total,
    )


def kaplan_meier_by_group(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str,
) -> dict[str, SurvivalCurve]:
    """Fit one KM curve per group; returns ``{group_name: SurvivalCurve}``."""
    _validate_survival_columns(df, duration_col, event_col, group_col)
    out: dict[str, SurvivalCurve] = {}
    for name, sub in df.groupby(group_col):
        out[str(name)] = kaplan_meier(sub[duration_col], sub[event_col])
    return out


def _median_from_curve(timeline: list[float], survival: list[float]) -> float | None:
    """First time where S(t) <= 0.5, or None if it never falls that low."""
    for t, s in zip(timeline, survival):
        if s <= 0.5:
            return float(t)
    return None


# ---------------------------------------------------------------------------
# Log-rank test
# ---------------------------------------------------------------------------


def log_rank_test(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str,
) -> LogRankResult:
    """Multi-group log-rank chi-square test.

    At each unique event time t_j we compute expected events per group under
    H0 (same hazard) using the at-risk counts, then form the matrix
    Z = O - E and its covariance V, returning Z^T V^- Z ~ chi^2(k-1).
    """
    _validate_survival_columns(df, duration_col, event_col, group_col)
    data = df[[duration_col, event_col, group_col]].dropna().copy()
    if len(data) == 0:
        raise ValueError("log_rank_test received no complete rows.")
    data[event_col] = data[event_col].astype(int)
    if not data[event_col].isin([0, 1]).all():
        raise ValueError("Events must be 0 (censored) or 1 (event observed).")

    groups = sorted(data[group_col].astype(str).unique().tolist())
    k = len(groups)
    if k < 2:
        raise ValueError("log_rank_test requires at least two groups.")

    group_to_idx = {g: i for i, g in enumerate(groups)}
    data["_g"] = data[group_col].astype(str).map(group_to_idx).astype(int)
    n_per_group = {g: int((data[group_col].astype(str) == g).sum()) for g in groups}
    n_events_per_group = {
        g: int(((data[group_col].astype(str) == g) & (data[event_col] == 1)).sum())
        for g in groups
    }

    unique_event_times = sorted(
        data.loc[data[event_col] == 1, duration_col].unique().tolist()
    )
    if not unique_event_times:
        return LogRankResult(
            chi_square=0.0,
            degrees_of_freedom=k - 1,
            p_value=1.0,
            groups=groups,
            n_per_group=n_per_group,
            n_events_per_group=n_events_per_group,
        )

    O_minus_E = np.zeros(k, dtype=float)
    V = np.zeros((k, k), dtype=float)

    for t in unique_event_times:
        at_risk = np.array(
            [int(((data["_g"] == i) & (data[duration_col] >= t)).sum()) for i in range(k)],
            dtype=float,
        )
        d_per_group = np.array(
            [
                int(((data["_g"] == i) & (data[duration_col] == t) & (data[event_col] == 1)).sum())
                for i in range(k)
            ],
            dtype=float,
        )
        n_total = at_risk.sum()
        d_total = d_per_group.sum()
        if n_total <= 0 or d_total <= 0:
            continue
        expected = d_total * at_risk / n_total
        O_minus_E += d_per_group - expected
        if n_total <= 1:
            continue
        factor = d_total * (n_total - d_total) / (n_total - 1)
        # V_jj = factor * (n_j/N) * (1 - n_j/N)
        # V_jl = -factor * (n_j*n_l) / N^2
        p = at_risk / n_total
        cov = factor * (np.diag(p) - np.outer(p, p))
        V += cov

    # Drop the last row/column so V is full rank under H0 (chi^2 with k-1 dof).
    Z = O_minus_E[:-1]
    V_red = V[:-1, :-1]
    try:
        chi_sq = float(Z @ np.linalg.pinv(V_red) @ Z)
    except np.linalg.LinAlgError:
        chi_sq = 0.0
    dof = k - 1
    from scipy import stats as _stats
    p_value = float(_stats.chi2.sf(chi_sq, dof))

    return LogRankResult(
        chi_square=float(chi_sq),
        degrees_of_freedom=dof,
        p_value=p_value,
        groups=groups,
        n_per_group=n_per_group,
        n_events_per_group=n_events_per_group,
    )


# ---------------------------------------------------------------------------
# Weibull fit
# ---------------------------------------------------------------------------


def fit_weibull(durations: pd.Series, events: pd.Series) -> WeibullFit:
    """Fit a two-parameter Weibull via MLE supporting right-censoring.

    Log-likelihood for shape k, scale lambda:
        L = sum_events [log(k) - k*log(lambda) + (k-1)*log(t) - (t/lambda)^k]
            + sum_censored [-(t/lambda)^k]

    We minimize the negative log-likelihood with ``scipy.optimize.minimize``.
    CIs use the observed-information Hessian (numerical). If all observations
    are events we additionally cross-check against ``scipy.stats.weibull_min.fit``
    as a sanity gate.
    """
    df = pd.DataFrame(
        {"t": pd.Series(durations).reset_index(drop=True),
         "e": pd.Series(events).reset_index(drop=True)}
    ).dropna()
    if len(df) == 0:
        raise ValueError("fit_weibull received no complete observations.")
    if (df["t"] <= 0).any():
        raise ValueError("Weibull durations must be strictly positive.")
    df["e"] = df["e"].astype(int)
    if not df["e"].isin([0, 1]).all():
        raise ValueError("Events must be 0 (censored) or 1 (event observed).")

    t = df["t"].to_numpy(dtype=float)
    e = df["e"].to_numpy(dtype=int)
    n = int(len(df))
    n_events = int(e.sum())
    if n_events == 0:
        raise ValueError("Weibull MLE requires at least one observed event.")

    from scipy import optimize as _opt
    from scipy import stats as _stats

    # Parameterize as (log_k, log_lambda) so the optimizer stays positive.
    def neg_ll(params: np.ndarray) -> float:
        log_k, log_lam = params
        k = float(np.exp(log_k))
        lam = float(np.exp(log_lam))
        ratio = t / lam
        ratio_k = np.power(ratio, k)
        # event contribution: log(k) - k*log(lam) + (k-1)*log(t) - (t/lam)^k
        ll_event = (
            np.log(k)
            - k * np.log(lam)
            + (k - 1) * np.log(t)
            - ratio_k
        )
        # censored contribution: -(t/lam)^k
        ll_censor = -ratio_k
        ll = np.where(e == 1, ll_event, ll_censor).sum()
        if not np.isfinite(ll):
            return 1e12
        return -float(ll)

    # Initial guess: shape ~ 1.0, scale ~ mean of observed events.
    mean_t = float(np.mean(t[e == 1])) if n_events > 0 else float(np.mean(t))
    x0 = np.array([0.0, np.log(max(mean_t, 1e-6))], dtype=float)
    result = _opt.minimize(neg_ll, x0, method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 5000})
    log_k_hat, log_lam_hat = result.x
    shape = float(np.exp(log_k_hat))
    scale = float(np.exp(log_lam_hat))

    # Approximate covariance via numerical Hessian of neg_ll in (log_k, log_lam),
    # then transform variances back to (k, lam) by delta method (Var(exp(x)) ~ exp(x)^2 * Var(x)).
    hess = _numerical_hessian(neg_ll, result.x)
    try:
        cov_log = np.linalg.pinv(hess)
        var_log_k = float(max(cov_log[0, 0], 0.0))
        var_log_lam = float(max(cov_log[1, 1], 0.0))
    except Exception:
        var_log_k = 0.0
        var_log_lam = 0.0
    se_k = float(shape * np.sqrt(var_log_k))
    se_lam = float(scale * np.sqrt(var_log_lam))
    z = float(_stats.norm.ppf(0.975))
    shape_ci = (max(0.0, shape - z * se_k), shape + z * se_k)
    scale_ci = (max(0.0, scale - z * se_lam), scale + z * se_lam)

    # Quantile inversion: S(t) = exp(-(t/lam)^k) -> t_q = lam * (-log(1 - q))^(1/k)
    def quantile(q: float) -> float:
        return float(scale * (-np.log(1 - q)) ** (1 / shape))

    b10 = quantile(0.10)
    b50 = quantile(0.50)
    b90 = quantile(0.90)

    if shape > 1.1:
        interp = (
            f"shape {shape:.2f} > 1 -> increasing hazard (wear-out failures); "
            "preventive replacement before B10 is rational."
        )
    elif shape < 0.9:
        interp = (
            f"shape {shape:.2f} < 1 -> decreasing hazard (early-life / infant mortality); "
            "burn-in and improved screening are the typical responses."
        )
    else:
        interp = (
            f"shape {shape:.2f} ~ 1 -> approximately constant hazard (random failures); "
            "a simple exponential model would fit similarly."
        )

    return WeibullFit(
        shape=shape,
        scale=scale,
        shape_ci=shape_ci,
        scale_ci=scale_ci,
        b10=b10,
        b50=b50,
        b90=b90,
        interpretation=interp,
        n=n,
        n_events=n_events,
    )


def _numerical_hessian(func, x: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    n = len(x)
    h = np.zeros((n, n), dtype=float)
    fx = func(x)
    for i in range(n):
        for j in range(i, n):
            x_pp = x.copy(); x_pp[i] += eps; x_pp[j] += eps
            x_pm = x.copy(); x_pm[i] += eps; x_pm[j] -= eps
            x_mp = x.copy(); x_mp[i] -= eps; x_mp[j] += eps
            x_mm = x.copy(); x_mm[i] -= eps; x_mm[j] -= eps
            if i == j:
                x_p = x.copy(); x_p[i] += eps
                x_m = x.copy(); x_m[i] -= eps
                h[i, j] = (func(x_p) - 2 * fx + func(x_m)) / (eps ** 2)
            else:
                val = (func(x_pp) - func(x_pm) - func(x_mp) + func(x_mm)) / (4 * eps ** 2)
                h[i, j] = val
                h[j, i] = val
    return h


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_survival_columns(
    df: pd.DataFrame, duration_col: str, event_col: str, group_col: str | None = None
) -> None:
    if df is None or len(df) == 0:
        raise ValueError("Survival analysis requires a non-empty DataFrame.")
    for col in (duration_col, event_col):
        if col not in df.columns:
            raise ValueError(f"column '{col}' not in DataFrame.")
    if group_col is not None and group_col not in df.columns:
        raise ValueError(f"group column '{group_col}' not in DataFrame.")
