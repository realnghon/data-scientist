"""Tests for ``ds_skill.classification``."""

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill.classification import (  # noqa: E402
    ClassificationResult,
    ThresholdSweep,
    class_balance_check,
    fit_classifier,
    tune_threshold,
)


def _make_binary_dataset(n: int = 200, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    # logit = 2*x1 - 1*x2 -> positive coef on x1, negative on x2.
    logit = 2.0 * x1 - 1.0 * x2
    probs = 1 / (1 + np.exp(-logit))
    y = (rng.uniform(0, 1, n) < probs).astype(int)
    return pd.DataFrame({"x1": x1, "x2": x2, "y": y})


def test_class_balance_check_flags_extreme_imbalance():
    y = pd.Series([0] * 200 + [1] * 5)
    result = class_balance_check(y, min_per_class=30)
    assert result["min_class_warning"] is True
    assert result["imbalance_ratio"] >= 10
    assert any("SMOTE" in r or "imbalance" in r.lower() for r in result["recommendations"])


def test_class_balance_check_passes_on_balanced_data():
    y = pd.Series([0] * 100 + [1] * 100)
    result = class_balance_check(y, min_per_class=30)
    assert result["min_class_warning"] is False
    assert result["imbalance_ratio"] == pytest.approx(1.0)


def test_fit_classifier_recovers_known_coefficient_direction():
    df = _make_binary_dataset(n=400, seed=42)
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=5)
    assert isinstance(result, ClassificationResult)
    # Feature importance for logistic is |coef| - so we just check x1 dominates x2.
    assert result.feature_importance is not None
    assert result.feature_importance["x1"] > result.feature_importance["x2"]
    # CV metrics include all required keys.
    for key in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "auc"):
        assert key in result.cv_metrics
        assert "mean" in result.cv_metrics[key]
        assert "std" in result.cv_metrics[key]
    # Binary case has a real AUC.
    assert not np.isnan(result.cv_metrics["auc"]["mean"])
    assert result.cv_metrics["auc"]["mean"] > 0.7  # signal is strong


def test_fit_classifier_multi_class_returns_per_class_metrics():
    rng = np.random.default_rng(7)
    n = 90
    df = pd.DataFrame(
        {
            "x1": np.r_[rng.normal(0, 0.5, n // 3), rng.normal(3, 0.5, n // 3), rng.normal(-3, 0.5, n // 3)],
            "x2": rng.normal(0, 1, n),
            "y": ["a"] * (n // 3) + ["b"] * (n // 3) + ["c"] * (n // 3),
        }
    )
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=3)
    assert len(result.classes) == 3
    for cls in ("a", "b", "c"):
        assert f"class_{cls}" in result.cv_metrics
        per_class = result.cv_metrics[f"class_{cls}"]
        for stat in ("precision", "recall", "f1"):
            assert stat in per_class
    # Macro AUC defined for multi-class via one-vs-rest.
    assert not np.isnan(result.cv_metrics["auc"]["mean"])


def test_fit_classifier_min_class_warning_fires_on_small_class():
    df = _make_binary_dataset(n=80, seed=1)
    # Force a tiny positive class.
    df.loc[df.index[:75], "y"] = 0
    df.loc[df.index[75:], "y"] = 1
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=5)
    assert result.min_class_warning is True
    assert any("smallest class" in r.lower() for r in result.recommendations)


def test_tune_threshold_improves_f1_over_default():
    df = _make_binary_dataset(n=400, seed=12)
    # Skew the labels so 0.5 is not optimal for F1.
    df.loc[df.index[:300], "y"] = 0
    df.loc[df.index[300:], "y"] = 1
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=5)
    sweep = tune_threshold(result, criterion="f1")
    assert isinstance(sweep, ThresholdSweep)
    # The sweep contains thresholds spanning 0..1 with required fields.
    sample = sweep.sweep[0]
    for key in ("threshold", "tpr", "fpr", "precision", "recall"):
        assert key in sample
    # Optimal F1 should be >= F1 at threshold ~ 0.5 (baseline).
    near_half = min(sweep.sweep, key=lambda s: abs(s["threshold"] - 0.5))
    assert sweep.metrics_at_optimum["f1"] >= near_half["f1"]


def test_tune_threshold_supports_cost_criterion():
    df = _make_binary_dataset(n=300, seed=5)
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=3)
    sweep = tune_threshold(result, criterion="cost", cost_matrix={"fp_cost": 1.0, "fn_cost": 10.0})
    assert sweep.criterion_used == "cost"
    assert "expected_cost" in sweep.metrics_at_optimum
    # Heavy FN cost should push the optimal threshold lower than 0.5 (catch more positives).
    assert sweep.optimal_threshold <= 0.5


def test_result_as_dict_is_json_serializable():
    df = _make_binary_dataset(n=200, seed=9)
    result = fit_classifier(df, target="y", features=["x1", "x2"], method="logistic", cv_folds=3)
    data = result.as_dict()
    # Round-trips through JSON.
    encoded = json.dumps(data, default=str)
    assert "method" in encoded
    assert "_probabilities" not in data
    assert "_true_labels" not in data
    sweep = tune_threshold(result, criterion="f1").as_dict()
    assert json.dumps(sweep, default=str)


def test_fit_classifier_rejects_empty_inputs():
    with pytest.raises(ValueError):
        fit_classifier(pd.DataFrame(), target="y", features=["x"], method="logistic")
    df = pd.DataFrame({"x1": [1, 2, 3], "y": [0, 0, 0]})
    with pytest.raises(ValueError):
        fit_classifier(df, target="y", features=["x1"], method="logistic")
