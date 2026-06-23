"""Reusable helpers for the data-scientist skill.

Modules (lazy-import only what you need):
    readiness          - 8-dimension data readiness scoring
    spc                - SPC control charts, Cp/Cpk capability indices
    correlation        - Pearson/Spearman/Kendall/mutual information with FDR
    anomaly            - IQR/MAD/IsolationForest univariate + multivariate
    time_series        - Mann-Kendall trend, STL decomposition, change-point
    shaping            - grain detector, leakage column scanner
    ab_validator       - SRM, MDE, effect-size with CI
    regression         - linear/regularized regression with diagnostics
    classification     - small-N safe classification with proper CV
    survival           - Kaplan-Meier, log-rank, Weibull
    analysis_methods   - group comparison, driver ranking
    plotting           - optional visualization helpers (requires matplotlib/seaborn)

Import only what the current analysis needs, e.g.:

    from ds_skill.correlation import pairwise_correlation
    from ds_skill.spc import xbar_r_chart

Submodules are loaded on first attribute access via PEP 562, so
`from ds_skill import correlation` also works without paying for the
other modules. Never `import *` and never eagerly load everything.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

__version__ = "1.0.0"

_SUBMODULES = frozenset({
    "readiness", "spc", "correlation", "anomaly", "time_series",
    "shaping", "ab_validator", "regression", "classification", "survival",
    "analysis_methods", "plotting",
})


def __getattr__(name: str):
    if name in _SUBMODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _SUBMODULES)


if TYPE_CHECKING:
    from . import ab_validator as ab_validator
    from . import analysis_methods as analysis_methods
    from . import anomaly as anomaly
    from . import classification as classification
    from . import correlation as correlation
    from . import plotting as plotting
    from . import readiness as readiness
    from . import regression as regression
    from . import shaping as shaping
    from . import spc as spc
    from . import survival as survival
    from . import time_series as time_series
