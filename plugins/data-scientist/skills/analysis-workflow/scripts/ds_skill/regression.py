"""Regression helpers: linear / ridge / lasso fits + diagnostics + response curves.

See `method-registry.md` section "Regression".
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------


def _lazy_scipy_stats():
    try:
        from scipy import stats  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "scipy is required for regression diagnostics; install scipy."
        ) from exc
    return stats


def _lazy_sklearn():
    try:
        from sklearn.linear_model import (  # type: ignore
            LinearRegression,
            Ridge,
            RidgeCV,
            Lasso,
            LassoCV,
        )

        return LinearRegression, Ridge, RidgeCV, Lasso, LassoCV
    except Exception as exc:
        raise ImportError(
            "scikit-learn is required for ridge/lasso; install scikit-learn."
        ) from exc


def _lazy_statsmodels():
    try:
        import statsmodels.api as sm  # type: ignore

        return sm
    except Exception:  # pragma: no cover
        return None


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RegressionResult:
    method: str
    coefficients: dict[str, float]
    intercept: float
    std_errors: dict[str, float] | None
    p_values: dict[str, float] | None
    r_squared: float
    adjusted_r_squared: float | None
    n: int
    n_features: int
    vif: dict[str, float] = field(default_factory=dict)
    alpha_used: float | None = None
    fitted_values: list[float] = field(default_factory=list)
    residuals: list[float] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "coefficients": dict(self.coefficients),
            "intercept": float(self.intercept),
            "std_errors": None if self.std_errors is None else dict(self.std_errors),
            "p_values": None if self.p_values is None else dict(self.p_values),
            "r_squared": float(self.r_squared),
            "adjusted_r_squared": (
                None if self.adjusted_r_squared is None else float(self.adjusted_r_squared)
            ),
            "n": int(self.n),
            "n_features": int(self.n_features),
            "vif": dict(self.vif),
            "alpha_used": None if self.alpha_used is None else float(self.alpha_used),
        }


@dataclass
class DiagnosticReport:
    normality_p_value: float
    homoscedasticity_flagged: bool
    linearity_flagged: bool
    influential_observations: list[int]
    multicollinearity_flagged: bool
    recommendations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "normality_p_value": (
                None if math.isnan(self.normality_p_value) else float(self.normality_p_value)
            ),
            "homoscedasticity_flagged": bool(self.homoscedasticity_flagged),
            "linearity_flagged": bool(self.linearity_flagged),
            "influential_observations": [int(i) for i in self.influential_observations],
            "multicollinearity_flagged": bool(self.multicollinearity_flagged),
            "recommendations": list(self.recommendations),
        }


# ---------------------------------------------------------------------------
# Shared prep
# ---------------------------------------------------------------------------


def _prep_xy(
    df: pd.DataFrame, target: str, features: list[str]
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("DataFrame is empty.")
    if target not in df.columns:
        raise ValueError(f"Target column not in DataFrame: {target}")
    if not features:
        raise ValueError("features must be a non-empty list.")
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Feature columns not in DataFrame: {missing}")
    if target in features:
        raise ValueError("Target may not appear in features.")

    sub = df[[target, *features]].copy()
    for c in sub.columns:
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    sub = sub.dropna()
    if len(sub) < max(2, len(features) + 1):
        raise ValueError(
            f"Not enough complete rows ({len(sub)}) for {len(features)} features."
        )

    # constant column check
    for f in features:
        if sub[f].nunique(dropna=True) <= 1:
            raise ValueError(f"Feature {f!r} is constant after dropping NaN.")

    y = sub[target].to_numpy(dtype=float)
    X = sub[list(features)].to_numpy(dtype=float)
    return X, y, list(features)


def _r_squared(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot == 0:
        return 0.0
    return 1.0 - ss_res / ss_tot


def _adj_r_squared(r2: float, n: int, k: int) -> float | None:
    if n - k - 1 <= 0:
        return None
    return 1.0 - (1.0 - r2) * (n - 1) / (n - k - 1)


def _vif(X: np.ndarray, features: list[str]) -> dict[str, float]:
    """Compute VIF by regressing each feature on the rest via lstsq."""
    out: dict[str, float] = {}
    n, k = X.shape
    if k < 2:
        return {features[0]: 1.0} if k == 1 else {}
    for i, name in enumerate(features):
        others = np.delete(X, i, axis=1)
        # add intercept
        A = np.column_stack([np.ones(n), others])
        target = X[:, i]
        try:
            beta, *_ = np.linalg.lstsq(A, target, rcond=None)
            y_hat = A @ beta
            r2 = _r_squared(target, y_hat)
            vif_val = 1.0 / (1.0 - r2) if r2 < 1 - 1e-12 else float("inf")
        except Exception:
            vif_val = float("nan")
        out[name] = float(vif_val)
    return out


# ---------------------------------------------------------------------------
# Linear regression
# ---------------------------------------------------------------------------


def fit_linear_regression(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    robust_se: bool = False,
) -> RegressionResult:
    """OLS via statsmodels (preferred) or numpy lstsq + bootstrap SE."""
    X, y, feats = _prep_xy(df, target, features)
    n, k = X.shape

    sm = _lazy_statsmodels()
    coefficients: dict[str, float]
    std_errors: dict[str, float] | None
    p_values: dict[str, float] | None
    fitted: np.ndarray
    resid: np.ndarray

    if sm is not None:
        X_const = sm.add_constant(X, has_constant="add")
        cov_type = "HC3" if robust_se else "nonrobust"
        model = sm.OLS(y, X_const).fit(cov_type=cov_type)
        intercept = float(model.params[0])
        coefficients = {feats[i]: float(model.params[i + 1]) for i in range(k)}
        std_errors = {feats[i]: float(model.bse[i + 1]) for i in range(k)}
        p_values = {feats[i]: float(model.pvalues[i + 1]) for i in range(k)}
        fitted = np.asarray(model.fittedvalues, dtype=float)
        resid = np.asarray(model.resid, dtype=float)
        r2 = float(model.rsquared)
    else:
        # numpy lstsq path with bootstrap SE
        X_const = np.column_stack([np.ones(n), X])
        beta, *_ = np.linalg.lstsq(X_const, y, rcond=None)
        intercept = float(beta[0])
        coefficients = {feats[i]: float(beta[i + 1]) for i in range(k)}
        fitted = X_const @ beta
        resid = y - fitted
        r2 = _r_squared(y, fitted)

        # bootstrap SE
        rng = np.random.default_rng(0)
        B = 200
        boot = np.empty((B, k + 1))
        for b in range(B):
            idx = rng.integers(0, n, size=n)
            try:
                bb, *_ = np.linalg.lstsq(X_const[idx], y[idx], rcond=None)
                boot[b] = bb
            except Exception:
                boot[b] = np.nan
        ses = np.nanstd(boot, axis=0, ddof=1)
        std_errors = {feats[i]: float(ses[i + 1]) for i in range(k)}
        # crude two-sided z p-value
        z_scores = np.array([beta[i + 1] / ses[i + 1] if ses[i + 1] > 0 else 0.0 for i in range(k)])
        stats = _lazy_scipy_stats()
        p_values = {feats[i]: float(2 * (1 - stats.norm.cdf(abs(z_scores[i])))) for i in range(k)}

    adj_r2 = _adj_r_squared(r2, n, k)
    vif = _vif(X, feats)

    return RegressionResult(
        method="linear",
        coefficients=coefficients,
        intercept=intercept,
        std_errors=std_errors,
        p_values=p_values,
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        n=n,
        n_features=k,
        vif=vif,
        alpha_used=None,
        fitted_values=fitted.tolist(),
        residuals=resid.tolist(),
    )


# ---------------------------------------------------------------------------
# Ridge / Lasso
# ---------------------------------------------------------------------------


def _fit_regularized(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    alpha: float | list[float],
    cv_folds: int,
    kind: str,
) -> RegressionResult:
    X, y, feats = _prep_xy(df, target, features)
    n, k = X.shape

    LinearRegression, Ridge, RidgeCV, Lasso, LassoCV = _lazy_sklearn()

    if isinstance(alpha, (list, tuple, np.ndarray)):
        alphas = list(alpha)
        if len(alphas) == 0:
            raise ValueError("alpha list must be non-empty.")
        if kind == "ridge":
            model = RidgeCV(alphas=alphas, cv=cv_folds)
        else:
            model = LassoCV(alphas=alphas, cv=cv_folds, max_iter=10000)
        model.fit(X, y)
        alpha_used = float(model.alpha_)
    else:
        if alpha <= 0:
            raise ValueError("alpha must be > 0.")
        if kind == "ridge":
            model = Ridge(alpha=float(alpha))
        else:
            model = Lasso(alpha=float(alpha), max_iter=10000)
        model.fit(X, y)
        alpha_used = float(alpha)

    fitted = model.predict(X)
    resid = y - fitted
    coefficients = {feats[i]: float(model.coef_[i]) for i in range(k)}
    intercept = float(model.intercept_)
    r2 = _r_squared(y, fitted)
    adj_r2 = _adj_r_squared(r2, n, k)
    vif = _vif(X, feats)

    return RegressionResult(
        method=kind,
        coefficients=coefficients,
        intercept=intercept,
        std_errors=None,
        p_values=None,
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        n=n,
        n_features=k,
        vif=vif,
        alpha_used=alpha_used,
        fitted_values=fitted.tolist(),
        residuals=resid.tolist(),
    )


def fit_ridge(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    alpha: float | list[float] = 1.0,
    cv_folds: int = 5,
) -> RegressionResult:
    return _fit_regularized(df, target, features, alpha, cv_folds, "ridge")


def fit_lasso(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    alpha: float | list[float] = 1.0,
    cv_folds: int = 5,
) -> RegressionResult:
    return _fit_regularized(df, target, features, alpha, cv_folds, "lasso")


# ---------------------------------------------------------------------------
# Response curves
# ---------------------------------------------------------------------------


def response_curves(
    result: RegressionResult,
    df: pd.DataFrame,
    features: list[str],
    n_points: int = 50,
) -> dict:
    """Marginal response of the model along each feature, others held at median.

    Returns ``{feature: {"x": [...], "y_hat": [...]}}`` plus a stacked array
    of shape (n_features, n_points, 2).
    """
    if n_points < 2:
        raise ValueError("n_points must be >= 2.")
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Columns not in DataFrame: {missing}")
    if not features:
        raise ValueError("features must be non-empty.")

    sub = df[features].copy()
    for c in features:
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    sub = sub.dropna()
    if sub.empty:
        raise ValueError("No complete rows for the requested features.")

    medians = {f: float(sub[f].median()) for f in features}

    per_feature: dict[str, dict[str, list[float]]] = {}
    stacked = np.empty((len(features), n_points, 2), dtype=float)

    coef = result.coefficients
    intercept = result.intercept

    for fi, f in enumerate(features):
        x_min = float(sub[f].min())
        x_max = float(sub[f].max())
        if x_min == x_max:
            xs = np.full(n_points, x_min)
        else:
            xs = np.linspace(x_min, x_max, n_points)
        # build prediction row by row using stored coefficients
        ys = np.full(n_points, intercept, dtype=float)
        for other in features:
            beta = coef.get(other, 0.0)
            if other == f:
                ys = ys + beta * xs
            else:
                ys = ys + beta * medians[other]
        per_feature[f] = {"x": xs.tolist(), "y_hat": ys.tolist()}
        stacked[fi, :, 0] = xs
        stacked[fi, :, 1] = ys

    return {
        "per_feature": per_feature,
        "medians": medians,
        "stacked": stacked,
        "n_points": int(n_points),
        "n_features": len(features),
    }


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def residual_diagnostics(
    result: RegressionResult,
    df: pd.DataFrame,
) -> DiagnosticReport:
    """Compute normality / homoscedasticity / linearity / influence / VIF flags."""
    residuals = np.asarray(result.residuals, dtype=float)
    fitted = np.asarray(result.fitted_values, dtype=float)
    if residuals.size < 4 or fitted.size != residuals.size:
        raise ValueError("Result does not carry residuals to diagnose.")

    stats = _lazy_scipy_stats()

    # Normality
    if residuals.size < 5000:
        try:
            norm_p = float(stats.shapiro(residuals).pvalue)
        except Exception:
            norm_p = float("nan")
    else:
        try:
            result_anderson = stats.anderson(residuals, dist="norm")
            # convert statistic-vs-critical-values to a pseudo-p-value
            sig_levels = np.array(result_anderson.significance_level) / 100.0
            crits = np.array(result_anderson.critical_values)
            stat = float(result_anderson.statistic)
            if stat < crits.min():
                norm_p = float(sig_levels.max())
            elif stat > crits.max():
                norm_p = float(sig_levels.min())
            else:
                # linear interpolation
                norm_p = float(np.interp(stat, crits, sig_levels[::-1]))
        except Exception:
            norm_p = float("nan")

    # Quartile-based homoscedasticity / linearity
    order = np.argsort(fitted)
    sorted_resid = residuals[order]
    sorted_fit = fitted[order]
    n = len(residuals)
    if n >= 8:
        chunks = np.array_split(sorted_resid, 4)
        stds = np.array([float(np.std(c, ddof=1)) if len(c) > 1 else 0.0 for c in chunks])
        means = np.array([float(np.mean(c)) for c in chunks])
        std_ratio = float(stds.max() / stds.min()) if stds.min() > 0 else float("inf")
        homo_flag = bool(std_ratio > 2.0)
        # if any quartile residual mean is > 0.5 sd from the overall mean → linearity issue
        overall_std = float(np.std(residuals, ddof=1)) if n > 1 else 0.0
        if overall_std > 0:
            lin_flag = bool(np.max(np.abs(means - np.mean(residuals))) > 0.5 * overall_std)
        else:
            lin_flag = False
    else:
        homo_flag = False
        lin_flag = False

    # Influence: Cook's distance approximation
    # Standardized residual^2 / k / (1 - h_ii) approximated by using leverage = mean
    # Simpler proxy: scaled squared residual
    k = result.n_features
    sigma_hat = float(np.sqrt(np.sum(residuals ** 2) / max(n - k - 1, 1)))
    if sigma_hat > 0:
        # crude Cook's-like score: r_i^2 / (k+1) / sigma_hat^2 * leverage_factor
        # without X access we approximate leverage as (k+1)/n (uniform)
        h = (k + 1) / n
        cooks = (residuals ** 2) / ((k + 1) * sigma_hat ** 2) * (h / (1 - h) ** 2 if h < 1 else 1.0)
        threshold = 4.0 / n
        influential = [int(i) for i in np.where(cooks > threshold)[0]]
    else:
        influential = []

    # Multicollinearity
    mc_flag = any(v > 10.0 and math.isfinite(v) for v in result.vif.values())

    recs: list[str] = []
    if not math.isnan(norm_p) and norm_p < 0.05:
        recs.append("Residuals fail normality (p<0.05); consider robust SE or transform target.")
    if homo_flag:
        recs.append("Residual std varies across fitted-value quartiles; consider weighted least-squares or transform.")
    if lin_flag:
        recs.append("Residual mean varies across fitted-value quartiles; relationship may be non-linear.")
    if influential:
        recs.append(f"{len(influential)} influential observations flagged (Cook's-like > 4/n); inspect them.")
    if mc_flag:
        recs.append("VIF > 10 on at least one feature; consider ridge or removing collinear features.")
    if not recs:
        recs.append("Diagnostics pass; OLS assumptions look acceptable.")

    return DiagnosticReport(
        normality_p_value=norm_p,
        homoscedasticity_flagged=homo_flag,
        linearity_flagged=lin_flag,
        influential_observations=influential,
        multicollinearity_flagged=mc_flag,
        recommendations=recs,
    )
