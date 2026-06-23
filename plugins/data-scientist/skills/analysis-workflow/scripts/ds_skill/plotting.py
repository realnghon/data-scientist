"""Visualization helpers for ds_skill modules.

Optional plotting utilities that wrap matplotlib/seaborn for common charts.
These are convenience functions - the core ds_skill modules return data,
not plots, so they work in headless environments.

Import this module only when you need to generate plots.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


def _check_plotting_available() -> tuple[Any, Any]:
    """Check if matplotlib and seaborn are available.

    Returns:
        Tuple of (matplotlib.pyplot, seaborn) modules

    Raises:
        ImportError: If plotting libraries are not installed
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        # Apply clean default style
        plt.style.use('seaborn-v0_8-darkgrid')
        # CJK-capable font fallback chain: pick the first installed family so
        # Chinese titles/labels render as glyphs (not tofu boxes) on Windows,
        # macOS, and Linux alike. unicode_minus=False keeps the minus sign from
        # rendering as a missing glyph under non-Latin fonts.
        from matplotlib import font_manager
        _installed = {f.name for f in font_manager.fontManager.ttflist}
        _cjk_candidates = [
            'Microsoft YaHei', 'SimHei',        # Windows
            'PingFang SC', 'Hiragino Sans GB',  # macOS
            'Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'Source Han Sans SC',  # Linux
        ]
        _cjk = [f for f in _cjk_candidates if f in _installed]
        plt.rcParams.update({
            'font.sans-serif': _cjk + plt.rcParams.get('font.sans-serif', []),
            'axes.unicode_minus': False,
            'font.size': 11,
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'axes.titleweight': 'bold',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.dpi': 100,
            'figure.figsize': (10, 6),
            'axes.grid': True,
            'grid.alpha': 0.3,
            'axes.facecolor': '#f8f9fa',
            'figure.facecolor': 'white',
        })
        sns.set_palette("husl")

        return plt, sns
    except ImportError as e:
        raise ImportError(
            "Plotting requires matplotlib and seaborn. "
            "Install with: pip install matplotlib seaborn"
        ) from e


def plot_control_chart(
    data: pd.Series,
    *,
    center_line: float,
    ucl: float,
    lcl: float,
    title: str = "Control Chart",
    xlabel: str = "Sample",
    ylabel: str = "Value",
    figsize: tuple[int, int] = (12, 6),
) -> Any:
    """Plot an SPC control chart.

    Args:
        data: Time series data
        center_line: Center line (mean)
        ucl: Upper control limit
        lcl: Lower control limit
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    fig, ax = plt.subplots(figsize=figsize)

    # Plot data points
    ax.plot(data.index, data.values, 'o-', color='steelblue', label='Data', markersize=4)

    # Control limits
    ax.axhline(center_line, color='green', linestyle='-', linewidth=2, label='Center')
    ax.axhline(ucl, color='red', linestyle='--', linewidth=2, label='UCL')
    ax.axhline(lcl, color='red', linestyle='--', linewidth=2, label='LCL')

    # Highlight out-of-control points
    ooc = (data > ucl) | (data < lcl)
    if ooc.any():
        ax.plot(data.index[ooc], data.values[ooc], 'ro', markersize=8, label='Out of control')

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_correlation_matrix(
    corr_matrix: pd.DataFrame,
    *,
    title: str = "Correlation Matrix",
    figsize: tuple[int, int] = (10, 8),
    cmap: str = "RdBu_r",
    annot: bool = True,
) -> Any:
    """Plot a correlation matrix heatmap.

    Args:
        corr_matrix: Correlation matrix (square DataFrame)
        title: Chart title
        figsize: Figure size (width, height)
        cmap: Colormap name
        annot: Whether to annotate cells with values

    Returns:
        matplotlib Figure object
    """
    plt, sns = _check_plotting_available()

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        corr_matrix,
        annot=annot,
        fmt=".2f" if annot else "",
        cmap=cmap,
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )

    ax.set_title(title)
    plt.tight_layout()
    return fig


def plot_regression_diagnostics(
    y_true: pd.Series,
    y_pred: pd.Series,
    residuals: pd.Series,
    *,
    figsize: tuple[int, int] = (12, 10),
) -> Any:
    """Plot regression diagnostic plots (4-panel).

    Args:
        y_true: Actual values
        y_pred: Predicted values
        residuals: Residuals (y_true - y_pred)
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # 1. Actual vs Predicted
    axes[0, 0].scatter(y_true, y_pred, alpha=0.6)
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    axes[0, 0].plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
    axes[0, 0].set_xlabel('Actual')
    axes[0, 0].set_ylabel('Predicted')
    axes[0, 0].set_title('Actual vs Predicted')
    axes[0, 0].grid(True, alpha=0.3)

    # 2. Residuals vs Fitted
    axes[0, 1].scatter(y_pred, residuals, alpha=0.6)
    axes[0, 1].axhline(0, color='r', linestyle='--', lw=2)
    axes[0, 1].set_xlabel('Fitted values')
    axes[0, 1].set_ylabel('Residuals')
    axes[0, 1].set_title('Residuals vs Fitted')
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Q-Q plot
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=axes[1, 0])
    axes[1, 0].set_title('Normal Q-Q')
    axes[1, 0].grid(True, alpha=0.3)

    # 4. Scale-Location (sqrt of standardized residuals vs fitted)
    standardized_residuals = residuals / residuals.std()
    axes[1, 1].scatter(y_pred, abs(standardized_residuals) ** 0.5, alpha=0.6)
    axes[1, 1].set_xlabel('Fitted values')
    axes[1, 1].set_ylabel('√|Standardized residuals|')
    axes[1, 1].set_title('Scale-Location')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_time_series_decomposition(
    observed: pd.Series,
    trend: pd.Series,
    seasonal: pd.Series,
    residual: pd.Series,
    *,
    figsize: tuple[int, int] = (12, 10),
) -> Any:
    """Plot time series decomposition (4-panel).

    Args:
        observed: Original time series
        trend: Trend component
        seasonal: Seasonal component
        residual: Residual component
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    fig, axes = plt.subplots(4, 1, figsize=figsize, sharex=True)

    axes[0].plot(observed.index, observed.values, color='steelblue')
    axes[0].set_ylabel('Observed')
    axes[0].set_title('Time Series Decomposition')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(trend.index, trend.values, color='orange')
    axes[1].set_ylabel('Trend')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(seasonal.index, seasonal.values, color='green')
    axes[2].set_ylabel('Seasonal')
    axes[2].grid(True, alpha=0.3)

    axes[3].plot(residual.index, residual.values, color='red', alpha=0.6)
    axes[3].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[3].set_ylabel('Residual')
    axes[3].set_xlabel('Time')
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_distribution_comparison(
    data: dict[str, pd.Series],
    *,
    title: str = "Distribution Comparison",
    xlabel: str = "Value",
    figsize: tuple[int, int] = (10, 6),
    kind: str = "kde",
) -> Any:
    """Plot overlaid distributions for multiple groups.

    Args:
        data: Dictionary mapping group names to Series
        title: Chart title
        xlabel: X-axis label
        figsize: Figure size (width, height)
        kind: Plot kind ('kde', 'hist', or 'both')

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    fig, ax = plt.subplots(figsize=figsize)

    for label, series in data.items():
        if kind in ("kde", "both"):
            series.plot.kde(ax=ax, label=label, linewidth=2)
        if kind in ("hist", "both"):
            series.plot.hist(ax=ax, label=label, alpha=0.5, bins=30)

    ax.set_xlabel(xlabel)
    ax.set_ylabel('Density' if kind == 'kde' else 'Count')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_kaplan_meier(
    time: pd.Series,
    event: pd.Series,
    *,
    groups: pd.Series | None = None,
    title: str = "Kaplan-Meier Survival Curve",
    xlabel: str = "Time",
    ylabel: str = "Survival Probability",
    figsize: tuple[int, int] = (10, 6),
) -> Any:
    """Plot Kaplan-Meier survival curves.

    Note: Requires lifelines package. Install with: pip install lifelines

    Args:
        time: Time to event or censoring
        event: Event indicator (1=event, 0=censored)
        groups: Optional grouping variable
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object

    Raises:
        ImportError: If lifelines is not installed
    """
    plt, _ = _check_plotting_available()

    try:
        from lifelines import KaplanMeierFitter
    except ImportError as e:
        raise ImportError(
            "Kaplan-Meier plotting requires lifelines. "
            "Install with: pip install lifelines"
        ) from e

    fig, ax = plt.subplots(figsize=figsize)

    if groups is None:
        # Single curve
        kmf = KaplanMeierFitter()
        kmf.fit(time, event)
        kmf.plot_survival_function(ax=ax, label='All')
    else:
        # Multiple curves by group
        for group_name in groups.unique():
            mask = groups == group_name
            kmf = KaplanMeierFitter()
            kmf.fit(time[mask], event[mask], label=str(group_name))
            kmf.plot_survival_function(ax=ax)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def save_figure(fig: Any, path: str, *, dpi: int = 150) -> str:
    """Save a matplotlib Figure to disk.

    Safe to call without checking plotting availability - if you have a Figure
    object, matplotlib is already imported.

    Args:
        fig: matplotlib Figure object
        path: Output file path (extension determines format, e.g. .png, .pdf)
        dpi: Resolution in dots per inch

    Returns:
        The path the figure was saved to
    """
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def _as_value_groups(
    data: Mapping[str, pd.Series] | pd.DataFrame,
    value_col: str | None,
    group_col: str | None,
) -> dict[str, pd.Series]:
    """Normalize grouped input into an ordered dict of group -> Series.

    Accepts either a mapping of group name to Series, or a DataFrame plus
    value_col and group_col names.
    """
    if isinstance(data, pd.DataFrame):
        if value_col is None or group_col is None:
            raise ValueError(
                "When passing a DataFrame, both value_col and group_col are required."
            )
        groups: dict[str, pd.Series] = {}
        for name, sub in data.groupby(group_col, sort=False):
            groups[str(name)] = pd.Series(sub[value_col]).dropna()
        return groups
    return {str(k): pd.Series(v).dropna() for k, v in data.items()}


def plot_pareto(
    counts: Mapping[str, float] | pd.Series,
    *,
    title: str = "Pareto Chart",
    ylabel: str = "Count",
    figsize: tuple[int, int] = (10, 6),
) -> Any:
    """Plot a Pareto chart: sorted bars plus a cumulative-percent line.

    Args:
        counts: Mapping of category to count, or a Series.
        title: Chart title (the question/metric); N is appended automatically
        ylabel: Y-axis label for the bar (count) axis
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    series = pd.Series(counts).sort_values(ascending=False)
    total = float(series.sum())
    cumulative_pct = series.cumsum() / total * 100 if total > 0 else series.cumsum() * 0

    fig, ax = plt.subplots(figsize=figsize)

    x_pos = np.arange(len(series))
    ax.bar(x_pos, series.values, color="steelblue", label=ylabel)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(i) for i in series.index], rotation=45, ha="right")
    ax.set_ylabel(ylabel)

    ax2 = ax.twinx()
    ax2.plot(x_pos, cumulative_pct.values, color="red", marker="o", linewidth=2,
             label="Cumulative %")
    ax2.axhline(80, color="green", linestyle="--", linewidth=1.5, label="80% reference")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 105)

    ax.set_title(f"{title} (N={int(total)})")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="center right")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    return fig


def plot_capability_histogram(
    data: pd.Series,
    *,
    lsl: float | None = None,
    usl: float | None = None,
    target: float | None = None,
    cp: float | None = None,
    cpk: float | None = None,
    title: str = "Process Capability",
    xlabel: str = "Value",
    figsize: tuple[int, int] = (10, 6),
) -> Any:
    """Plot a capability histogram with spec lines and a Cp/Cpk annotation box.

    Args:
        data: Measured values
        lsl: Lower spec limit (optional)
        usl: Upper spec limit (optional)
        target: Target value (optional)
        cp: Cp index to annotate (optional)
        cpk: Cpk index to annotate (optional)
        title: Chart title (the question/metric); N is appended automatically
        xlabel: X-axis label (include units)
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    series = pd.Series(data).dropna()
    n = len(series)

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(series.values, bins="auto", color="steelblue", alpha=0.7, edgecolor="white")

    if lsl is not None:
        ax.axvline(lsl, color="red", linestyle="--", linewidth=2, label=f"LSL = {lsl:.3g}")
    if usl is not None:
        ax.axvline(usl, color="red", linestyle="--", linewidth=2, label=f"USL = {usl:.3g}")
    if target is not None:
        ax.axvline(target, color="green", linestyle="-", linewidth=2, label=f"Target = {target:.3g}")

    annotations = []
    if cp is not None:
        annotations.append(f"Cp = {cp:.3f}")
    if cpk is not None:
        annotations.append(f"Cpk = {cpk:.3f}")
    if annotations:
        ax.text(
            0.02,
            0.97,
            "\n".join(annotations),
            transform=ax.transAxes,
            va="top",
            ha="left",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.set_title(f"{title} (N={n})")
    if lsl is not None or usl is not None or target is not None:
        ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_flagged_scatter(
    x: pd.Series,
    y: pd.Series,
    flags: pd.Series,
    *,
    rule_label: str = "Flagged",
    title: str = "Anomaly Detection",
    xlabel: str = "X",
    ylabel: str = "Y",
    figsize: tuple[int, int] = (10, 6),
) -> Any:
    """Plot a scatter with flagged points highlighted.

    Args:
        x: Numeric x values
        y: Numeric y values
        flags: Boolean Series marking anomalous points.
        rule_label: Description of the rule/threshold used for flagging.
        title: Chart title (the question/metric); N is appended automatically
        xlabel: X-axis label (include units)
        ylabel: Y-axis label (include units)
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    xv = pd.Series(x).reset_index(drop=True)
    yv = pd.Series(y).reset_index(drop=True)
    fl = pd.Series(flags).reset_index(drop=True).astype(bool)
    n = len(xv)
    n_flagged = int(fl.sum())

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(xv[~fl], yv[~fl], alpha=0.5, color="steelblue", label="Normal")
    ax.scatter(
        xv[fl],
        yv[fl],
        color="red",
        edgecolor="black",
        s=70,
        zorder=3,
        label=f"{rule_label} (n={n_flagged})",
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} (N={n})")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_roc_curve(
    y_true: pd.Series,
    y_score: pd.Series,
    *,
    title: str = "ROC Curve",
    figsize: tuple[int, int] = (8, 8),
) -> Any:
    """Plot an ROC curve with AUC in the legend and a chance diagonal.

    Args:
        y_true: Binary ground-truth labels (0/1).
        y_score: Predicted scores or probabilities for the positive class.
        title: Chart title (the question/metric); N is appended automatically
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    from sklearn.metrics import auc, roc_curve

    yt = np.asarray(y_true)
    ys = np.asarray(y_score)
    n = len(yt)
    fpr, tpr, _ = roc_curve(yt, ys)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(fpr, tpr, color="steelblue", linewidth=2, label=f"ROC (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1, label="Chance")

    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_title(f"{title} (N={n})")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_confusion_matrix(
    y_true: pd.Series,
    y_pred: pd.Series,
    *,
    labels: Sequence[Any] | None = None,
    normalize: bool = False,
    title: str = "Confusion Matrix",
    figsize: tuple[int, int] = (8, 6),
) -> Any:
    """Plot a confusion-matrix heatmap.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        labels: Explicit label order (optional).
        normalize: Normalize rows to proportions if True.
        title: Chart title (the question/metric); N is appended automatically
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, sns = _check_plotting_available()

    from sklearn.metrics import confusion_matrix

    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    n = len(yt)
    cm = confusion_matrix(yt, yp, labels=labels)
    tick_labels = labels if labels is not None else sorted(set(yt) | set(yp))

    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        cm_display = np.divide(cm, row_sums, where=row_sums != 0)
        fmt = ".2f"
    else:
        cm_display = cm
        fmt = "d"

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        cm_display,
        annot=True,
        fmt=fmt,
        cmap="Blues",
        cbar=True,
        xticklabels=tick_labels,
        yticklabels=tick_labels,
        ax=ax,
    )

    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"{title} (N={n})")

    plt.tight_layout()
    return fig


def plot_calibration_curve(
    y_true: pd.Series,
    y_prob: pd.Series,
    *,
    n_bins: int = 10,
    title: str = "Calibration (Reliability) Curve",
    figsize: tuple[int, int] = (8, 8),
) -> Any:
    """Plot a reliability diagram with a perfect-calibration diagonal.

    Args:
        y_true: Binary ground-truth labels (0/1).
        y_prob: Predicted probabilities for the positive class.
        n_bins: Number of probability bins.
        title: Chart title (the question/metric); N is appended automatically
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    from sklearn.calibration import calibration_curve

    yt = np.asarray(y_true)
    yp = np.asarray(y_prob)
    n = len(yt)
    frac_pos, mean_pred = calibration_curve(yt, yp, n_bins=n_bins)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(mean_pred, frac_pos, "o-", color="steelblue", linewidth=2, label="Model")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1, label="Perfect calibration")

    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed fraction positive")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"{title} (N={n})")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_feature_importance(
    importances: Mapping[str, float] | pd.Series,
    *,
    top_n: int = 20,
    title: str = "Feature Importance",
    xlabel: str = "Importance",
    figsize: tuple[int, int] = (10, 8),
) -> Any:
    """Plot a horizontal bar chart of feature importances, most important on top.

    Args:
        importances: Mapping of feature name to importance, or a Series.
        top_n: Show only the top-N features by importance.
        title: Chart title (the question/metric)
        xlabel: X-axis label (importance units)
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object
    """
    plt, _ = _check_plotting_available()

    series = pd.Series(importances).sort_values(ascending=False).head(top_n)
    # Reverse so the most important ends up on top of a horizontal bar chart.
    series = series.iloc[::-1]

    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(len(series))
    ax.barh(y_pos, series.values, color="steelblue")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([str(i) for i in series.index])

    ax.set_xlabel(xlabel)
    ax.set_title(f"{title} (top {len(series)})")
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    return fig

