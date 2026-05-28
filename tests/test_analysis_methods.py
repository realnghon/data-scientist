from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "analysis-workflow" / "scripts"))

from ds_skill.analysis_methods import (  # noqa: E402
    compare_numeric_by_group,
    rank_numeric_drivers,
    recommend_group_comparison,
)


def test_recommends_welch_for_two_independent_groups_by_default():
    recommendation = recommend_group_comparison(
        target_type="numeric",
        group_count=2,
        paired=False,
        min_group_size=30,
        equal_variance_p=0.01,
        normality_ok=True,
    )

    assert recommendation.primary_method == "welch_t_test"
    assert "student_t_test" in recommendation.rejected_methods
    assert recommendation.decision_reason


def test_recommends_welch_anova_for_three_numeric_groups_with_unequal_variance():
    recommendation = recommend_group_comparison(
        target_type="numeric",
        group_count=3,
        paired=False,
        min_group_size=25,
        equal_variance_p=0.02,
        normality_ok=True,
    )

    assert recommendation.primary_method == "welch_anova"
    assert "one_way_anova" in recommendation.rejected_methods
    assert "kruskal_wallis" in recommendation.cross_checks


def test_compare_numeric_by_group_returns_method_evidence_and_effect_size():
    df = pd.DataFrame(
        {
            "machine": ["A"] * 40 + ["B"] * 40,
            "yield_rate": np.r_[np.repeat(0.96, 40), np.repeat(0.91, 40)],
        }
    )

    result = compare_numeric_by_group(df, target="yield_rate", group="machine")

    assert result["primary_method"] == "welch_t_test"
    assert result["group_count"] == 2
    assert result["effect"]["mean_difference"] > 0.04
    assert result["interpretation_label"] in {
        "reliable_conclusion",
        "directional_signal",
        "investigation_candidate",
    }


def test_rank_numeric_drivers_prioritizes_strong_numeric_relationships():
    df = pd.DataFrame(
        {
            "temperature": [1, 2, 3, 4, 5, 6],
            "pressure": [2, 2, 2, 2, 2, 2],
            "line": ["L1", "L1", "L2", "L2", "L3", "L3"],
            "defect_rate": [2, 4, 6, 8, 10, 12],
        }
    )

    drivers = rank_numeric_drivers(
        df,
        target="defect_rate",
        candidate_features=["temperature", "pressure", "line"],
    )

    assert drivers[0]["feature"] == "temperature"
    assert drivers[0]["method"] == "spearman_correlation"
    assert drivers[-1]["feature"] == "pressure"
