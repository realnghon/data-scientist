"""Tests for ds_skill.correlation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"),
)

from ds_skill.correlation import (  # noqa: E402
    CorrelationMatrix,
    CorrelationResult,
    correlation_with_target,
    pairwise_correlation,
)
from ds_skill.correlation import _bh_adjust  # noqa: E402


def _rng(seed: int = 0) -> np.random.Generator:
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# pairwise_correlation
# ---------------------------------------------------------------------------


def test_pearson_recovers_known_linear_relationship():
    rng = _rng(1)
    x = rng.normal(size=200)
    noise = rng.normal(scale=0.1, size=200)
    df = pd.DataFrame({"x": x, "y": 2.0 * x + noise, "junk": rng.normal(size=200)})

    matrix = pairwise_correlation(df, methods=("pearson",), min_observations=20)
    coefficients = matrix.coefficients["pearson"]

    assert coefficients.loc["x", "y"] > 0.95
    junk_corr = abs(float(coefficients.loc["x", "junk"]))
    assert junk_corr < 0.3


def test_spearman_handles_monotonic_nonlinear():
    rng = _rng(2)
    x = np.linspace(-3, 3, 200)
    y = np.exp(x) + rng.normal(scale=0.05, size=200)  # strictly monotonic non-linear
    df = pd.DataFrame({"x": x, "y": y})

    matrix = pairwise_correlation(
        df, methods=("pearson", "spearman"), min_observations=20
    )

    pearson = float(matrix.coefficients["pearson"].loc["x", "y"])
    spearman = float(matrix.coefficients["spearman"].loc["x", "y"])
    # Spearman should be ~1 for any monotonic relationship, Pearson lower
    # because of the curvature.
    assert spearman > 0.99
    assert spearman >= pearson - 1e-9


def test_pairwise_correlation_returns_matrices_per_method():
    rng = _rng(3)
    df = pd.DataFrame(rng.normal(size=(100, 4)), columns=pd.Index(list("abcd")))

    matrix = pairwise_correlation(
        df, methods=("pearson", "spearman", "kendall"), min_observations=20
    )

    assert isinstance(matrix, CorrelationMatrix)
    assert set(matrix.coefficients) == {"pearson", "spearman", "kendall"}
    for method, mat in matrix.coefficients.items():
        assert list(mat.index) == list(mat.columns) == list("abcd")
        # Diagonal of symmetric correlation methods is 1.0.
        for col in mat.columns:
            assert mat.loc[col, col] == pytest.approx(1.0)
    # Long-form: 6 unique pairs * 3 methods = 18 rows.
    assert matrix.n_pairs_tested == 18


def test_fdr_adjustment_reduces_false_positives_in_random_data():
    """Generate 100 truly-independent pairs; BH should leave very few significant."""
    rng = _rng(4)
    # 100 independent columns, n=60 per column.
    n_features = 14  # gives 14 choose 2 = 91 ≈ 100 pairs
    data = rng.normal(size=(60, n_features))
    df = pd.DataFrame(data, columns=pd.Index([f"v{i}" for i in range(n_features)]))

    matrix = pairwise_correlation(
        df, methods=("pearson",), fdr_alpha=0.05, min_observations=20
    )

    raw_sig = sum(
        1 for r in matrix.pairs if r.p_value is not None and r.p_value < 0.05
    )
    fdr_sig = sum(1 for r in matrix.pairs if r.significant_after_fdr)
    n_pairs = matrix.n_pairs_tested

    # Under the null we'd expect ~5% raw, but FDR should crush that further.
    # Allow plenty of slack: just require BH to flag fewer than raw and at
    # most ~5% of all tested pairs (often it's 0).
    assert n_pairs == n_features * (n_features - 1) // 2
    assert fdr_sig <= raw_sig
    assert fdr_sig <= max(1, int(0.05 * n_pairs))


def test_bh_adjustment_matches_textbook_example():
    """Hand-checked Benjamini-Hochberg example.

    For sorted p = [0.001, 0.008, 0.039, 0.041, 0.042] with n=5:
      raw BH = p * n / rank = [0.005, 0.02, 0.065, 0.05125, 0.042]
      step-up cummin from the right, clipped at 1 -> [0.005, 0.02, 0.042, 0.042, 0.042]
    """
    raw = np.array([0.001, 0.008, 0.039, 0.041, 0.042])
    adjusted = _bh_adjust(raw)
    expected = np.array([0.005, 0.02, 0.042, 0.042, 0.042])
    np.testing.assert_allclose(adjusted, expected, rtol=1e-6)

    # Order-invariance: shuffling the input must permute the output the same way.
    shuffled = np.array([0.039, 0.001, 0.042, 0.008, 0.041])
    adjusted_shuffled = _bh_adjust(shuffled)
    np.testing.assert_allclose(
        adjusted_shuffled,
        np.array([0.042, 0.005, 0.042, 0.02, 0.042]),
        rtol=1e-6,
    )


# ---------------------------------------------------------------------------
# correlation_with_target
# ---------------------------------------------------------------------------


def test_correlation_with_target_ranks_by_strength():
    rng = _rng(5)
    n = 300
    x_strong = rng.normal(size=n)
    target = 3.0 * x_strong + rng.normal(scale=0.05, size=n)
    x_weak = 0.2 * x_strong + rng.normal(size=n)
    x_noise = rng.normal(size=n)
    df = pd.DataFrame(
        {
            "x_strong": x_strong,
            "x_weak": x_weak,
            "x_noise": x_noise,
            "y": target,
        }
    )

    results = correlation_with_target(
        df, target="y", methods=("pearson",), include_mi=False
    )

    assert results, "Expected at least one correlation result"
    assert results[0].x == "x_strong"
    # The noise feature should land last.
    assert results[-1].x == "x_noise"
    # Effect strengths must be monotonically non-increasing.
    strengths = [r.effect_strength for r in results]
    assert strengths == sorted(strengths, reverse=True)


def test_mutual_info_detects_nonlinear_dependence():
    pytest.importorskip("sklearn")
    rng = _rng(6)
    n = 500
    x = rng.uniform(-3, 3, size=n)
    y = x ** 2 + rng.normal(scale=0.1, size=n)  # symmetric U-shape: Pearson ~ 0
    noise = rng.normal(size=n)
    df = pd.DataFrame({"x": x, "noise": noise, "y": y})

    results = correlation_with_target(
        df, target="y", methods=("pearson",), include_mi=True
    )

    pearson_x = next(r for r in results if r.x == "x" and r.method == "pearson")
    mi_x = next(r for r in results if r.x == "x" and r.method == "mutual_info")
    mi_noise = next(r for r in results if r.x == "noise" and r.method == "mutual_info")

    assert abs(pearson_x.coefficient) < 0.2  # linear correlation should be weak
    assert mi_x.coefficient > mi_noise.coefficient
    assert mi_x.coefficient > 0.05  # detects the non-linear dependency


def test_min_observations_filters_low_n_pairs():
    rng = _rng(7)
    n = 50
    a = rng.normal(size=n)
    b = a + rng.normal(scale=0.1, size=n)
    # Column `c` has only 10 valid observations.
    c = np.full(n, np.nan)
    c[:10] = rng.normal(size=10)
    df = pd.DataFrame({"a": a, "b": b, "c": c})

    matrix = pairwise_correlation(
        df, methods=("pearson",), min_observations=30
    )

    pair_cols = {(r.x, r.y) for r in matrix.pairs}
    assert ("a", "b") in pair_cols or ("b", "a") in pair_cols
    # Pairs involving `c` must be filtered out.
    assert not any("c" in pair for pair in pair_cols)


def test_as_dict_is_json_serializable():
    rng = _rng(8)
    df = pd.DataFrame(rng.normal(size=(80, 3)), columns=pd.Index(["x", "y", "z"]))
    matrix = pairwise_correlation(df, methods=("pearson", "spearman"), min_observations=20)

    payload = matrix.as_dict()
    json_text = json.dumps(payload)  # must not raise
    parsed = json.loads(json_text)

    assert set(parsed["methods"]) == {"pearson", "spearman"}
    assert set(parsed["coefficients"]) == {"pearson", "spearman"}
    assert parsed["coefficients"]["pearson"]["x"]["x"] == 1.0
    # CorrelationResult.as_dict is also serializable.
    one_pair = matrix.pairs[0]
    json.dumps(one_pair.as_dict())


def test_empty_dataframe_raises():
    with pytest.raises(ValueError):
        pairwise_correlation(pd.DataFrame(), methods=("pearson",))
    with pytest.raises(ValueError):
        correlation_with_target(pd.DataFrame(), target="y")


def test_correlation_result_interpretation_bands():
    rng = _rng(9)
    n = 200
    x = rng.normal(size=n)
    df = pd.DataFrame({"x": x, "y": x + rng.normal(scale=0.01, size=n)})
    results = correlation_with_target(
        df, target="y", methods=("pearson",), include_mi=False
    )
    strongest = results[0]
    assert isinstance(strongest, CorrelationResult)
    assert "positive" in strongest.interpretation
    assert strongest.interpretation.startswith("very strong") or strongest.interpretation.startswith("strong")
