"""Tests for ``ds_skill.report_generator``."""

from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"))

from ds_skill.report_generator import (  # noqa: E402
    ReportPayload,
    build_evidence_block,
    fill_report_template,
)


def _full_payload() -> ReportPayload:
    return ReportPayload(
        title="Yield differences across production lines",
        tldr_bullets=[
            "Line B yields 3.2 pp lower than Line A.",
            "Temperature drift is the dominant driver.",
            "Directional: shift handover may add 0.5 pp of variance.",
        ],
        question="Why does Line B yield less than Line A?",
        dataset_summary="prod_runs.csv, 2025-01 to 2025-12, 801 rows, one row per lot.",
        reliable_conclusions=[
            {
                "method": "welch_t_test",
                "statistic": "t=4.21",
                "effect": "-3.2 pp",
                "ci": "(-4.3, -2.1) pp",
                "chart_ref": "fig_1: box plot of yield by line",
            }
        ],
        directional_signals=[
            {
                "method": "spearman_correlation",
                "statistic": "rho=0.23",
                "effect": "weak monotonic",
                "chart_ref": "fig_2: scatter",
            }
        ],
        unsupported=[
            {
                "wanted_to_claim": "Operator B causes more defects",
                "why_not": "Operator is confounded with shift and machine.",
                "data_gap": "Need rotated operator schedule or random assignment.",
            }
        ],
        methods_used=[
            {
                "method": "welch_t_test",
                "why_chosen": "Two independent numeric groups, variance unequal.",
                "rejected_alternatives": ["student_t_test", "mann_whitney_u"],
            }
        ],
        limitations=[
            "Limited to 2025 data; capacity expansion mid-year not modeled.",
            "Operator rotation log incomplete after Q3.",
        ],
        next_actions_operational=[
            {"priority": "P1", "action": "Audit Line B temperature calibration", "owner": "Process Eng", "effort": "S", "payoff": "High"},
        ],
        next_actions_analytical=[
            {"priority": "P2", "action": "Collect 6 weeks of randomized operator assignment data", "owner": "Data Team", "effort": "M", "payoff": "Med"},
        ],
    )


def test_fill_report_template_substitutes_known_fields():
    payload = _full_payload()
    rendered = fill_report_template(payload)
    # Title placeholder is gone, real title is present.
    assert "Yield differences across production lines" in rendered
    # Question text appears verbatim.
    assert "Why does Line B yield less than Line A?" in rendered
    # Reliable-conclusions block emits the method name.
    assert "welch_t_test" in rendered
    assert "Reliable conclusion" in rendered or "Tier 1" in rendered


def test_fill_report_template_marks_missing_placeholders_as_todo():
    # Payload missing most of the body - placeholders should become <<TODO: ...>>.
    sparse = ReportPayload(title="Sparse run")
    rendered = fill_report_template(sparse)
    assert "Sparse run" in rendered
    # The template references "row_grain" / "y_column" placeholders that are
    # not payload fields; those should fall through to TODO markers.
    assert "<<TODO:" in rendered


def test_build_evidence_block_for_reliable_tier():
    block = build_evidence_block(
        method="welch_t_test",
        statistic={"effect": "-3.2 pp", "ci": "(-4.3, -2.1) pp", "p_value": 0.0001},
        chart_ref="fig_1",
        tier="reliable",
    )
    assert "Reliable conclusion" in block
    assert "welch_t_test" in block
    assert "fig_1" in block
    assert "directional" not in block.lower()


def test_build_evidence_block_for_directional_tier():
    block = build_evidence_block(
        method="spearman_correlation",
        statistic={"statistic": "rho=0.23", "n": 120},
        chart_ref="fig_2",
        tier="directional",
    )
    assert "Directional" in block
    # Must surface the "why directional" prompt.
    assert "Why directional" in block


def test_build_evidence_block_for_unsupported_tier():
    block = build_evidence_block(
        method="logistic_regression",
        statistic={"reason": "operator confounded with shift"},
        tier="unsupported",
    )
    assert "Unsupported" in block
    assert "Data or design needed" in block


def test_build_evidence_block_rejects_bad_inputs():
    with pytest.raises(ValueError):
        build_evidence_block("", {"effect": 1}, tier="reliable")
    with pytest.raises(ValueError):
        build_evidence_block("logistic", None, tier="reliable")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        build_evidence_block("logistic", {"effect": 1}, tier="bogus")  # type: ignore[arg-type]


def test_payload_as_dict_is_json_serializable():
    payload = _full_payload()
    data = payload.as_dict()
    encoded = json.dumps(data)
    assert "Yield differences" in encoded


def test_fill_report_template_falls_back_when_template_missing(tmp_path):
    payload = _full_payload()
    missing_template = tmp_path / "does_not_exist.md"
    rendered = fill_report_template(payload, template_path=missing_template)
    # Fallback skeleton still produces a sensible report with sections.
    assert "TL;DR" in rendered
    assert "Reliable Conclusions" in rendered
    assert "Directional Signals" in rendered
    assert "Unsupported" in rendered or "What We Could Not Conclude" in rendered


def test_end_to_end_roundtrip_renders_all_tiers_and_actions():
    payload = _full_payload()
    rendered = fill_report_template(payload)
    # Tier 1, 2, 3 all represented.
    assert "welch_t_test" in rendered
    assert "spearman_correlation" in rendered
    assert "Operator B causes more defects" in rendered
    # Next actions reflected.
    assert "Audit Line B temperature calibration" in rendered
    assert "Collect 6 weeks" in rendered
    # Limitations rendered as bullet list.
    assert "Limited to 2025 data" in rendered
