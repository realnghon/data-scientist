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


def test_recommend_group_comparison_handles_categorical_and_unsupported_targets():
    binary = recommend_group_comparison(
        target_type="binary",
        group_count=2,
        paired=False,
        min_group_size=20,
        equal_variance_p=None,
        normality_ok=None,
    )
    categorical = recommend_group_comparison(
        target_type="categorical",
        group_count=3,
        paired=False,
        min_group_size=20,
        equal_variance_p=None,
        normality_ok=None,
    )
    unsupported = recommend_group_comparison(
        target_type="text",
        group_count=2,
        paired=False,
        min_group_size=20,
        equal_variance_p=None,
        normality_ok=None,
    )

    assert binary.primary_method == "fisher_exact_or_two_proportion_test"
    assert categorical.primary_method == "chi_square_test"
    assert unsupported.primary_method == "readiness_blocked"


def test_recommend_group_comparison_handles_paired_and_small_non_normal_cases():
    paired = recommend_group_comparison(
        target_type="numeric",
        group_count=2,
        paired=True,
        min_group_size=10,
        equal_variance_p=None,
        normality_ok=False,
    )
    paired_blocked = recommend_group_comparison(
        target_type="numeric",
        group_count=3,
        paired=True,
        min_group_size=10,
        equal_variance_p=None,
        normality_ok=True,
    )
    robust_two_group = recommend_group_comparison(
        target_type="numeric",
        group_count=2,
        paired=False,
        min_group_size=5,
        equal_variance_p=0.5,
        normality_ok=False,
    )
    robust_many_group = recommend_group_comparison(
        target_type="numeric",
        group_count=4,
        paired=False,
        min_group_size=5,
        equal_variance_p=0.5,
        normality_ok=False,
    )
    not_enough_groups = recommend_group_comparison(
        target_type="numeric",
        group_count=1,
        paired=False,
        min_group_size=10,
        equal_variance_p=None,
        normality_ok=True,
    )

    assert paired.primary_method == "wilcoxon_signed_rank"
    assert paired_blocked.primary_method == "readiness_blocked"
    assert robust_two_group.primary_method == "mann_whitney_u"
    assert robust_many_group.primary_method == "kruskal_wallis"
    assert not_enough_groups.primary_method == "readiness_blocked"


def test_compare_numeric_by_group_blocks_single_group_and_handles_three_groups():
    one_group = pd.DataFrame({"line": ["A", "A"], "yield_rate": [1.0, 2.0]})
    many_groups = pd.DataFrame(
        {
            "line": ["A"] * 25 + ["B"] * 25 + ["C"] * 25,
            "yield_rate": list(np.linspace(1, 2, 25)) + list(np.linspace(2, 3, 25)) + list(np.linspace(5, 6, 25)),
        }
    )

    assert compare_numeric_by_group(one_group, target="yield_rate", group="line")["status"] == "blocked"
    result = compare_numeric_by_group(many_groups, target="yield_rate", group="line")
    assert result["status"] == "ok"
    assert result["group_count"] == 3
    assert result["effect"]["highest_mean_group"] == "C"


def test_rank_numeric_drivers_records_sparse_and_missing_features():
    df = pd.DataFrame(
        {
            "target": [1.0, 2.0, 3.0, None],
            "sparse": [1.0, None, None, 4.0],
            "category": ["A", "A", "B", "B"],
        }
    )

    drivers = rank_numeric_drivers(
        df,
        target="target",
        candidate_features=["target", "missing", "sparse", "category"],
    )

    by_feature = {row["feature"]: row for row in drivers}
    assert set(by_feature) == {"sparse", "category"}
    assert by_feature["sparse"]["method"] == "readiness_blocked"
    assert by_feature["category"]["method"] in {"welch_t_test", "mann_whitney_u"}


def test_rank_numeric_drivers_zero_target_scale_for_categorical_feature():
    df = pd.DataFrame({"target": [5.0, 5.0, 5.0, 5.0], "category": ["A", "A", "B", "B"]})

    drivers = rank_numeric_drivers(df, target="target", candidate_features=["category"])

    assert drivers[0]["score"] == 0.0
