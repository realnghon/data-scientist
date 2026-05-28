"""Visualization helpers for ds_skill modules.

Optional plotting utilities that wrap matplotlib/seaborn for common charts.
These are convenience functions - the core ds_skill modules return data,
not plots, so they work in headless environments.

Import this module only when you need to generate plots.
"""

from __future__ import annotations

from typing import Any

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

