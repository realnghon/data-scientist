"""Tests for ds_skill.regression."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill.regression import (  # noqa: E402
    DiagnosticReport,
    RegressionResult,
    fit_lasso,
    fit_linear_regression,
    fit_ridge,
    residual_diagnostics,
    response_curves,
)


def _make_linear_data(n=500, seed=0):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x3 = rng.normal(size=n)
    noise = rng.normal(scale=0.5, size=n)
    y = 2.0 * x1 - 1.0 * x2 + 0.0 * x3 + 3.0 + noise
    return pd.DataFrame({"x1": x1, "x2": x2, "x3": x3, "y": y})


def test_linear_recovers_known_coefficients():
    df = _make_linear_data()
    result = fit_linear_regression(df, target="y", features=["x1", "x2", "x3"])
    assert isinstance(result, RegressionResult)
    assert abs(result.coefficients["x1"] - 2.0) < 0.1
    assert abs(result.coefficients["x2"] - (-1.0)) < 0.1
    assert abs(result.coefficients["x3"] - 0.0) < 0.1
    assert abs(result.intercept - 3.0) < 0.1
    assert result.r_squared > 0.9
    assert result.std_errors is not None
    assert result.p_values is not None
    # x1 should be significant, x3 should not
    assert result.p_values["x1"] < 0.001
    assert result.p_values["x3"] > 0.05


def test_ridge_shrinks_toward_zero_on_collinear():
    rng = np.random.default_rng(1)
    n = 200
    x1 = rng.normal(size=n)
    x2 = x1 + 0.01 * rng.normal(size=n)  # near-duplicate of x1
    y = 1.0 * x1 + 1.0 * x2 + 0.1 * rng.normal(size=n)
    df = pd.DataFrame({"x1": x1, "x2": x2, "y": y})

    linear = fit_linear_regression(df, target="y", features=["x1", "x2"])
    ridge = fit_ridge(df, target="y", features=["x1", "x2"], alpha=10.0)
    # Sum of coefficients should be similar, but individual magnitudes smaller under ridge
    total_linear = abs(linear.coefficients["x1"]) + abs(linear.coefficients["x2"])
    total_ridge = abs(ridge.coefficients["x1"]) + abs(ridge.coefficients["x2"])
    assert total_ridge < total_linear
    assert ridge.method == "ridge"
    assert ridge.alpha_used == 10.0


def test_lasso_zeros_out_unimportant_features():
    rng = np.random.default_rng(2)
    n = 500
    x1 = rng.normal(size=n)
    x_noise = [rng.normal(size=n) for _ in range(5)]
    y = 3.0 * x1 + 0.1 * rng.normal(size=n)
    df = pd.DataFrame({"x1": x1, **{f"n{i}": x_noise[i] for i in range(5)}, "y": y})
    features = ["x1"] + [f"n{i}" for i in range(5)]
    result = fit_lasso(df, target="y", features=features, alpha=0.1)
    # At least 2 of the noise features should be exactly zero
    zeros = [f for f in features[1:] if result.coefficients[f] == 0.0]
    assert len(zeros) >= 2
    # x1 should be near 3
    assert abs(result.coefficients["x1"] - 3.0) < 0.3


def test_vif_detects_collinearity():
    rng = np.random.default_rng(3)
    n = 200
    x1 = rng.normal(size=n)
    x2 = x1 + 0.01 * rng.normal(size=n)
    x3 = rng.normal(size=n)
    y = x1 + x3 + 0.5 * rng.normal(size=n)
    df = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3, "y": y})
    result = fit_linear_regression(df, target="y", features=["x1", "x2", "x3"])
    # x1 and x2 should have huge VIF; x3 should be near 1
    assert result.vif["x1"] > 10
    assert result.vif["x2"] > 10
    assert result.vif["x3"] < 2


def test_residual_diagnostics_flags_heteroscedasticity():
    rng = np.random.default_rng(4)
    n = 400
    x = np.linspace(0, 10, n)
    # noise scales with x → heteroscedastic
    y = 2.0 * x + rng.normal(scale=(0.1 + 0.5 * x), size=n)
    df = pd.DataFrame({"x": x, "y": y})
    result = fit_linear_regression(df, target="y", features=["x"])
    diag = residual_diagnostics(result, df)
    assert isinstance(diag, DiagnosticReport)
    assert diag.homoscedasticity_flagged is True
    assert any("homosced" in r.lower() or "weighted" in r.lower() for r in diag.recommendations)


def test_residual_diagnostics_influential_observations():
    rng = np.random.default_rng(5)
    n = 100
    x = rng.normal(size=n)
    y = 1.0 * x + 0.1 * rng.normal(size=n)
    # inject a strong outlier
    x[0] = 10.0
    y[0] = 100.0
    df = pd.DataFrame({"x": x, "y": y})
    result = fit_linear_regression(df, target="y", features=["x"])
    diag = residual_diagnostics(result, df)
    assert 0 in diag.influential_observations or len(diag.influential_observations) >= 1


def test_response_curves_shape_and_values():
    df = _make_linear_data()
    result = fit_linear_regression(df, target="y", features=["x1", "x2", "x3"])
    curves = response_curves(result, df, features=["x1", "x2", "x3"], n_points=50)
    assert curves["stacked"].shape == (3, 50, 2)
    assert set(curves["per_feature"].keys()) == {"x1", "x2", "x3"}
    # along x1 the response should be increasing (coef ~ +2)
    y_x1 = curves["per_feature"]["x1"]["y_hat"]
    assert y_x1[-1] > y_x1[0]
    # along x3 the response should be roughly flat (coef ~ 0)
    y_x3 = curves["per_feature"]["x3"]["y_hat"]
    assert abs(y_x3[-1] - y_x3[0]) < abs(y_x1[-1] - y_x1[0])


def test_as_dict_json_serializable():
    df = _make_linear_data()
    result = fit_linear_regression(df, target="y", features=["x1", "x2"])
    diag = residual_diagnostics(result, df)
    json.dumps(result.as_dict())
    json.dumps(diag.as_dict())


def test_fit_validates_inputs():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    with pytest.raises(ValueError):
        fit_linear_regression(df, target="missing", features=["x"])
    with pytest.raises(ValueError):
        fit_linear_regression(df, target="y", features=[])
    with pytest.raises(ValueError):
        fit_linear_regression(df, target="y", features=["y"])
    # constant feature
    df_const = pd.DataFrame({"x": [1, 1, 1, 1], "y": [1, 2, 3, 4]})
    with pytest.raises(ValueError):
        fit_linear_regression(df_const, target="y", features=["x"])


def test_fit_validates_dataframe_shape_and_feature_presence():
    with pytest.raises(ValueError, match="pandas DataFrame"):
        fit_linear_regression(None, target="y", features=["x"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="empty"):
        fit_linear_regression(pd.DataFrame(), target="y", features=["x"])
    with pytest.raises(ValueError, match="Feature columns"):
        fit_linear_regression(pd.DataFrame({"x": [1, 2], "y": [1, 2]}), target="y", features=["missing"])
    with pytest.raises(ValueError, match="Not enough complete rows"):
        fit_linear_regression(pd.DataFrame({"x1": [1, None], "x2": [2, 3], "y": [1, 2]}), target="y", features=["x1", "x2"])


def test_regularized_regression_validates_alpha_inputs():
    df = _make_linear_data(n=30)
    with pytest.raises(ValueError, match="alpha must be > 0"):
        fit_ridge(df, target="y", features=["x1"], alpha=0)
    with pytest.raises(ValueError, match="alpha list must be non-empty"):
        fit_lasso(df, target="y", features=["x1"], alpha=[])


def test_regularized_regression_cross_validated_alpha_path():
    df = _make_linear_data(n=60)
    result = fit_ridge(df, target="y", features=["x1", "x2"], alpha=[0.1, 1.0], cv_folds=3)
    assert result.method == "ridge"
    assert result.alpha_used in {0.1, 1.0}


def test_response_curves_validates_inputs_and_constant_feature_path():
    result = RegressionResult(
        method="linear",
        coefficients={"x": 2.0},
        intercept=1.0,
        std_errors=None,
        p_values=None,
        r_squared=1.0,
        adjusted_r_squared=None,
        n=3,
        n_features=1,
    )
    df = pd.DataFrame({"x": [5.0, 5.0, 5.0]})

    curves = response_curves(result, df, ["x"], n_points=3)
    assert curves["per_feature"]["x"]["x"] == [5.0, 5.0, 5.0]
    with pytest.raises(ValueError, match="n_points"):
        response_curves(result, df, ["x"], n_points=1)
    with pytest.raises(ValueError, match="Columns not in DataFrame"):
        response_curves(result, df, ["missing"])
    with pytest.raises(ValueError, match="features must be non-empty"):
        response_curves(result, df, [])
    with pytest.raises(ValueError, match="No complete rows"):
        response_curves(result, pd.DataFrame({"x": [None, None]}), ["x"])


def test_residual_diagnostics_validates_residual_payload_and_clean_path():
    bad = RegressionResult(
        method="linear",
        coefficients={},
        intercept=0.0,
        std_errors=None,
        p_values=None,
        r_squared=0.0,
        adjusted_r_squared=None,
        n=3,
        n_features=0,
        fitted_values=[1.0, 2.0, 3.0],
        residuals=[0.0, 0.0],
    )
    with pytest.raises(ValueError, match="residuals"):
        residual_diagnostics(bad, pd.DataFrame())

    clean = RegressionResult(
        method="linear",
        coefficients={"x": 1.0},
        intercept=0.0,
        std_errors=None,
        p_values=None,
        r_squared=1.0,
        adjusted_r_squared=None,
        n=6,
        n_features=1,
        vif={"x": 1.0},
        fitted_values=[1, 2, 3, 4, 5, 6],
        residuals=[0, 0, 0, 0, 0, 0],
    )
    diag = residual_diagnostics(clean, pd.DataFrame())
    assert diag.influential_observations == []
    assert "Diagnostics pass" in diag.recommendations[0]
