"""Report generator helpers for the data-scientist skill.

Fills the markdown template at ``assets/report_template.md`` from a
``ReportPayload``. Placeholders use the form ``<<key>>``; any placeholder
without a matching payload field is replaced with ``<<TODO: key>>`` so a
human reviewer can see exactly what is missing rather than silently
shipping an unrendered token.

Also exposes ``build_evidence_block`` to format a single Tier 1 / Tier 2 /
Tier 3 evidence entry in the shape described by
``references/report-standard.md``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "report_template.md"
)


# Lightweight fallback used when the template asset is missing on disk.
# Keeps the three-tier structure so downstream consumers still get valid
# scaffolding.
_FALLBACK_TEMPLATE = """# <<title>>

## 1. TL;DR

<<tldr_bullets>>

## 2. Question & Dataset

- Question asked: <<question>>
- Dataset: <<dataset_summary>>

## 3. Reliable Conclusions (Tier 1)

<<reliable_conclusions>>

## 4. Directional Signals (Tier 2)

<<directional_signals>>

## 5. What We Could Not Conclude (Tier 3)

<<unsupported>>

## 6. Method Summary

<<methods_used>>

## 7. Limitations & Risks

<<limitations>>

## 8. Recommended Next Actions

### Operational

<<next_actions_operational>>

### Analytical

<<next_actions_analytical>>
"""


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ReportPayload:
    title: str
    tldr_bullets: list[str] = field(default_factory=list)
    question: str = ""
    dataset_summary: str = ""
    reliable_conclusions: list[dict] = field(default_factory=list)
    directional_signals: list[dict] = field(default_factory=list)
    unsupported: list[dict] = field(default_factory=list)
    methods_used: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    next_actions_operational: list[dict] = field(default_factory=list)
    next_actions_analytical: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_PLACEHOLDER_RE = re.compile(r"<<([^<>]+?)>>")


# Map descriptive labels used in the bundled template to ReportPayload fields.
# Keys are normalized (lowercased, whitespace-collapsed) before lookup so the
# template's verbose placeholders ("verbatim user question") resolve cleanly.
_PLACEHOLDER_ALIASES = {
    "report title": "title",
    "title": "title",
    "verbatim user question": "question",
    "question asked": "question",
    "question": "question",
    "name / source": "dataset_summary",
    "dataset": "dataset_summary",
    "dataset summary": "dataset_summary",
}


def fill_report_template(
    payload: ReportPayload, template_path: str | Path | None = None
) -> str:
    """Render the markdown template with values from ``payload``.

    The template path resolution falls back to the bundled
    ``assets/report_template.md`` and, if that is missing, to an inline
    skeleton that preserves the three-tier section structure.

    Unmatched placeholders are rewritten as ``<<TODO: name>>`` so they
    stand out to a human reviewer.
    """
    if payload is None:
        raise ValueError("fill_report_template requires a ReportPayload.")

    template = _load_template(template_path)
    fields = payload.as_dict()

    # First pass: substitute structured payload blocks into the body. The
    # bundled template doesn't have section-level placeholders for these so
    # we append them where the section header sits.
    template = _inject_section_blocks(template, fields)

    def repl(match: re.Match) -> str:
        raw_key = match.group(1).strip()
        # Templates often look like "<<bullet_1: description>>" - we treat
        # the first segment as the lookup key.
        primary_segment = raw_key.split(":", 1)[0].strip()
        # Heuristic: "bullet_1", "bullet_2" etc. should pull from the
        # tldr_bullets list by index.
        bullet_idx = _match_bullet_index(primary_segment)
        if bullet_idx is not None and fields.get("tldr_bullets"):
            bullets = fields["tldr_bullets"]
            if 0 <= bullet_idx < len(bullets):
                return str(bullets[bullet_idx])
            # Fewer bullets than placeholders -> drop the line cleanly.
            return ""
        # Try direct field, then alias lookup using normalized key.
        candidate = primary_segment
        if candidate in fields:
            value = fields[candidate]
        else:
            normalized = re.sub(r"\s+", " ", primary_segment.lower()).strip()
            alias_target = _PLACEHOLDER_ALIASES.get(normalized)
            if alias_target and alias_target in fields:
                value = fields[alias_target]
                candidate = alias_target
            else:
                return f"<<TODO: {primary_segment}>>"
        if value is None or (isinstance(value, (list, dict, str)) and len(value) == 0):
            return f"<<TODO: {primary_segment}>>"
        return _stringify(candidate, value)

    return _PLACEHOLDER_RE.sub(repl, template)


def _inject_section_blocks(template: str, fields: dict[str, Any]) -> str:
    """Inject rendered tier/method/action blocks below their section headers.

    The bundled template documents sample structure under each tier but does
    not carry single-placeholder slots for the *whole* tier. This helper
    inserts the rendered block immediately after the section header so the
    finished report shows the payload contents alongside the original sample.
    """
    injections = [
        ("## 3. Reliable Conclusions (Tier 1)", "reliable_conclusions"),
        ("## 4. Directional Signals (Tier 2)", "directional_signals"),
        ("## 5. What We Could Not Conclude (Tier 3)", "unsupported"),
        ("## 6. Method Summary", "methods_used"),
        ("## 7. Limitations & Risks", "limitations"),
        ("### Operational", "next_actions_operational"),
        ("### Analytical", "next_actions_analytical"),
    ]
    for header, key in injections:
        block_value = fields.get(key)
        if not block_value:
            continue
        rendered = _stringify(key, block_value)
        if not rendered or rendered == "None":
            continue
        marker = f"{header}\n"
        if marker not in template:
            continue
        template = template.replace(
            marker, f"{marker}\n{rendered}\n", 1
        )
    return template


def build_evidence_block(
    method: str,
    statistic: dict,
    chart_ref: str | None = None,
    tier: Literal["reliable", "directional", "unsupported"] = "directional",
) -> str:
    """Format a single evidence entry in the report's three-tier shape."""
    if not method:
        raise ValueError("build_evidence_block requires a method name.")
    if statistic is None or not isinstance(statistic, dict):
        raise ValueError("statistic must be a dict (effect size, CI, p-value, ...).")

    if tier == "reliable":
        header = "**Reliable conclusion** (Tier 1)"
        hedge = ""
    elif tier == "directional":
        header = "**Directional signal** (Tier 2)"
        hedge = " — directional only"
    elif tier == "unsupported":
        header = "**Unsupported** (Tier 3)"
        hedge = ""
    else:
        raise ValueError(
            f"tier must be 'reliable', 'directional', or 'unsupported'; got {tier!r}."
        )

    lines = [header, f"- Method: `{method}`{hedge}"]
    # Stable rendering for common stat keys, then fall back to all others.
    for key in ("statistic", "effect", "effect_size", "ci", "p_value", "n", "n_per_group"):
        if key in statistic:
            lines.append(f"- {key.replace('_', ' ').title()}: {statistic[key]}")
    for key, value in statistic.items():
        if key in {"statistic", "effect", "effect_size", "ci", "p_value", "n", "n_per_group"}:
            continue
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    if chart_ref:
        lines.append(f"- Chart: {chart_ref}")
    if tier == "directional":
        lines.append(
            "- Why directional: <<TODO: state single-method | borderline effect | small n | assumption violated>>"
        )
    if tier == "unsupported":
        lines.append(
            "- Data or design needed: <<TODO: what would upgrade this to Tier 2 or Tier 1>>"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_template(template_path: str | Path | None) -> str:
    """Return template text; fall back to the inline skeleton on any miss."""
    path = Path(template_path) if template_path else DEFAULT_TEMPLATE_PATH
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except OSError:
        pass
    return _FALLBACK_TEMPLATE


def _match_bullet_index(key: str) -> int | None:
    m = re.fullmatch(r"bullet_(\d+)", key)
    if m:
        return int(m.group(1)) - 1
    return None


def _stringify(key: str, value: Any) -> str:
    """Render a payload value as markdown-friendly text."""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return "None"
        # tldr_bullets is rendered as a bullet list.
        if key == "tldr_bullets" or all(isinstance(v, str) for v in value):
            return "\n".join(f"- {v}" for v in value)
        if key in {"reliable_conclusions", "directional_signals"}:
            return "\n\n".join(_render_finding(v, key) for v in value)
        if key == "unsupported":
            return "\n\n".join(_render_unsupported(v) for v in value)
        if key == "methods_used":
            return "\n".join(_render_method(v) for v in value)
        if key in {"next_actions_operational", "next_actions_analytical"}:
            return "\n".join(_render_action(v) for v in value)
        # Generic list-of-dicts fallback.
        return "\n".join(f"- {v}" for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def _render_finding(item: dict, key: str) -> str:
    tier = "reliable" if key == "reliable_conclusions" else "directional"
    method = item.get("method", "<<TODO: method>>")
    chart_ref = item.get("chart_ref")
    statistic_payload = {
        k: v
        for k, v in item.items()
        if k not in {"method", "chart_ref"}
    }
    block = build_evidence_block(method, statistic_payload, chart_ref=chart_ref, tier=tier)
    return block


def _render_unsupported(item: dict) -> str:
    lines = ["**Unsupported** (Tier 3)"]
    if "wanted_to_claim" in item:
        lines.append(f"- Hoped to conclude: {item['wanted_to_claim']}")
    if "why_not" in item:
        lines.append(f"- Why current data does not support it: {item['why_not']}")
    if "data_gap" in item:
        lines.append(f"- Data or design needed: {item['data_gap']}")
    return "\n".join(lines)


def _render_method(item: dict) -> str:
    method = item.get("method", "<<TODO: method>>")
    why = item.get("why_chosen", "")
    rejected = item.get("rejected_alternatives", [])
    line = f"- `{method}`"
    if why:
        line += f" — {why}"
    if rejected:
        if isinstance(rejected, list):
            line += f" (rejected: {', '.join(rejected)})"
        else:
            line += f" (rejected: {rejected})"
    return line


def _render_action(item: dict) -> str:
    parts = []
    priority = item.get("priority")
    if priority:
        parts.append(f"[{priority}]")
    if "action" in item:
        parts.append(str(item["action"]))
    elif "verb" in item:
        parts.append(str(item["verb"]))
    if "owner" in item:
        parts.append(f"(owner: {item['owner']})")
    if "effort" in item:
        parts.append(f"effort={item['effort']}")
    if "payoff" in item:
        parts.append(f"payoff={item['payoff']}")
    return "- " + " ".join(parts) if parts else "- <<TODO: action>>"
