"""Tests for ds_skill.plotting — chart helpers return headless-safe Figures.

Skips entirely when matplotlib is unavailable; forces the Agg backend so the
tests never need a display.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("seaborn")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill import plotting  # noqa: E402


def _is_fig(fig: object) -> bool:
    return isinstance(fig, Figure) and len(fig.axes) >= 1


# ---------------------------------------------------------------------------
# Existing functions
# ---------------------------------------------------------------------------

def test_plot_control_chart() -> None:
    rng = np.random.default_rng(0)
    data = pd.Series(rng.normal(10, 1, 50))
    fig = plotting.plot_control_chart(data, center_line=10, ucl=13, lcl=7)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_correlation_matrix() -> None:
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(30, 3)), columns=["a", "b", "c"])
    fig = plotting.plot_correlation_matrix(df.corr())
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_regression_diagnostics() -> None:
    rng = np.random.default_rng(0)
    y_true = pd.Series(rng.normal(size=40))
    y_pred = y_true + rng.normal(scale=0.3, size=40)
    residuals = y_true - y_pred
    fig = plotting.plot_regression_diagnostics(y_true, y_pred, residuals)
    assert _is_fig(fig)
    assert len(fig.axes) >= 4
    plt.close(fig)


def test_plot_time_series_decomposition() -> None:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=48, freq="D")
    observed = pd.Series(rng.normal(size=48), index=idx)
    trend = observed.rolling(3, min_periods=1).mean()
    seasonal = pd.Series(np.sin(np.arange(48)), index=idx)
    residual = observed - trend - seasonal
    fig = plotting.plot_time_series_decomposition(observed, trend, seasonal, residual)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_distribution_comparison() -> None:
    rng = np.random.default_rng(0)
    data = {
        "A": pd.Series(rng.normal(0, 1, 100)),
        "B": pd.Series(rng.normal(1, 1, 100)),
    }
    fig = plotting.plot_distribution_comparison(data)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_kaplan_meier() -> None:
    pytest.importorskip("lifelines")
    rng = np.random.default_rng(0)
    time = pd.Series(rng.exponential(10, 50))
    event = pd.Series(rng.integers(0, 2, 50))
    fig = plotting.plot_kaplan_meier(time, event)
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# save_figure
# ---------------------------------------------------------------------------

def test_save_figure(tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    fig = plotting.plot_histogram(pd.Series(rng.normal(size=50)))
    out = tmp_path / "fig.png"
    returned = plotting.save_figure(fig, str(out))
    assert returned == str(out)
    assert out.exists() and out.stat().st_size > 0
    plt.close(fig)


# ---------------------------------------------------------------------------
# Distribution intent
# ---------------------------------------------------------------------------

def test_plot_histogram() -> None:
    rng = np.random.default_rng(0)
    data = pd.Series(rng.normal(size=100))
    fig = plotting.plot_histogram(data, title="Widths", xlabel="mm")
    assert _is_fig(fig)
    assert "N=100" in fig.axes[0].get_title()
    plt.close(fig)


def test_plot_ecdf() -> None:
    rng = np.random.default_rng(0)
    data = pd.Series(rng.normal(size=80))
    fig = plotting.plot_ecdf(data, spec_limits=(-2, 2))
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Comparison across groups
# ---------------------------------------------------------------------------

def test_plot_grouped_boxplot_dict() -> None:
    rng = np.random.default_rng(0)
    data = {"A": pd.Series(rng.normal(0, 1, 30)), "B": pd.Series(rng.normal(1, 1, 30))}
    fig = plotting.plot_grouped_boxplot(data)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_grouped_boxplot_dataframe() -> None:
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "val": rng.normal(size=60),
            "grp": ["A", "B", "C"] * 20,
        }
    )
    fig = plotting.plot_grouped_boxplot(df, value_col="val", group_col="grp")
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_violin() -> None:
    rng = np.random.default_rng(0)
    data = {"A": pd.Series(rng.normal(0, 1, 40)), "B": pd.Series(rng.normal(1, 1, 40))}
    fig = plotting.plot_violin(data)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_dotplot_ci_dict() -> None:
    estimates = {"A": (1.0, 0.5, 1.5), "B": (2.0, 1.4, 2.6)}
    fig = plotting.plot_dotplot_ci(estimates)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_dotplot_ci_dataframe() -> None:
    df = pd.DataFrame(
        {"point": [1.0, 2.0], "lo": [0.5, 1.4], "hi": [1.5, 2.6]},
        index=["A", "B"],
    )
    fig = plotting.plot_dotplot_ci(df, point_col="point", lo_col="lo", hi_col="hi")
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Correlation intent
# ---------------------------------------------------------------------------

def test_plot_scatter_fit_linear() -> None:
    rng = np.random.default_rng(0)
    x = pd.Series(np.arange(50, dtype=float))
    y = 2 * x + pd.Series(rng.normal(scale=2, size=50))
    fig = plotting.plot_scatter_fit(x, y, fit="linear")
    assert _is_fig(fig)
    # Strong positive relationship -> r near 1 should be surfaced in legend.
    legend_text = " ".join(t.get_text() for t in fig.axes[0].get_legend().get_texts())
    assert "Pearson r" in legend_text
    plt.close(fig)


def test_plot_scatter_fit_lowess() -> None:
    pytest.importorskip("statsmodels")
    rng = np.random.default_rng(0)
    x = pd.Series(np.linspace(0, 10, 60))
    y = pd.Series(np.sin(x) + rng.normal(scale=0.2, size=60))
    fig = plotting.plot_scatter_fit(x, y, fit="lowess")
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_pareto() -> None:
    counts = {"Scratch": 50, "Dent": 30, "Crack": 15, "Other": 5}
    fig = plotting.plot_pareto(counts)
    assert _is_fig(fig)
    # Pareto adds a secondary axis.
    assert len(fig.axes) >= 2
    plt.close(fig)


# ---------------------------------------------------------------------------
# Time series intent
# ---------------------------------------------------------------------------

def test_plot_time_series_single_with_ci() -> None:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=30, freq="D")
    s = pd.Series(rng.normal(size=30), index=idx)
    lower = s - 1
    upper = s + 1
    fig = plotting.plot_time_series(s, ci=(lower, upper))
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_time_series_dataframe() -> None:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame(rng.normal(size=(30, 2)), columns=["x", "y"], index=idx)
    fig = plotting.plot_time_series(df)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_small_multiples() -> None:
    rng = np.random.default_rng(0)
    data = {f"s{i}": pd.Series(rng.normal(size=20)) for i in range(4)}
    fig = plotting.plot_small_multiples(data)
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Process / capability intent
# ---------------------------------------------------------------------------

def test_plot_capability_histogram() -> None:
    rng = np.random.default_rng(0)
    data = pd.Series(rng.normal(10, 1, 100))
    fig = plotting.plot_capability_histogram(
        data, lsl=7, usl=13, target=10, cp=1.0, cpk=0.95
    )
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Anomaly intent
# ---------------------------------------------------------------------------

def test_plot_flagged_scatter() -> None:
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=50))
    y = pd.Series(rng.normal(size=50))
    flags = (x.abs() > 1.5)
    fig = plotting.plot_flagged_scatter(x, y, flags, rule_label="|z|>1.5")
    assert _is_fig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Classification evaluation intent
# ---------------------------------------------------------------------------

def test_plot_roc_curve() -> None:
    rng = np.random.default_rng(0)
    y_true = pd.Series(rng.integers(0, 2, 100))
    # Score correlated with label so AUC is comfortably above 0.5.
    y_score = pd.Series(y_true + rng.normal(scale=0.5, size=100))
    fig = plotting.plot_roc_curve(y_true, y_score)
    assert _is_fig(fig)
    legend_text = " ".join(t.get_text() for t in fig.axes[0].get_legend().get_texts())
    assert "AUC" in legend_text
    plt.close(fig)


def test_plot_confusion_matrix() -> None:
    rng = np.random.default_rng(0)
    y_true = pd.Series(rng.integers(0, 2, 60))
    y_pred = pd.Series(rng.integers(0, 2, 60))
    fig = plotting.plot_confusion_matrix(y_true, y_pred)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_confusion_matrix_normalized() -> None:
    rng = np.random.default_rng(0)
    y_true = pd.Series(rng.integers(0, 3, 60))
    y_pred = pd.Series(rng.integers(0, 3, 60))
    fig = plotting.plot_confusion_matrix(y_true, y_pred, normalize=True)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_calibration_curve() -> None:
    rng = np.random.default_rng(0)
    y_prob = pd.Series(rng.uniform(size=200))
    y_true = pd.Series((rng.uniform(size=200) < y_prob).astype(int))
    fig = plotting.plot_calibration_curve(y_true, y_prob, n_bins=5)
    assert _is_fig(fig)
    plt.close(fig)


def test_plot_feature_importance() -> None:
    importances = {"f1": 0.5, "f2": 0.3, "f3": 0.15, "f4": 0.05}
    fig = plotting.plot_feature_importance(importances, top_n=3)
    assert _is_fig(fig)
    plt.close(fig)
