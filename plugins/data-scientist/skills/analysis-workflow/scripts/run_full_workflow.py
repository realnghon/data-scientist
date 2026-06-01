#!/usr/bin/env python
"""Deterministic baseline pipeline for data-scientist analysis workflows.

Runs a single-shot, dependency-light chain of the *tested* ``ds_skill`` helpers
and emits a JSON artifact bundle plus an optional markdown skeleton. It is the
reference pipeline for sequential platforms (Codex, OpenCode, Gemini CLI) and a
fast baseline even on Claude Code before fan-out to parallel subagents.

Usage::

    python run_full_workflow.py dataset.csv --target yield_pct --output results/
    python run_full_workflow.py dataset.xlsx --sheet Sheet1 --sample-rows 10000
    python run_full_workflow.py dataset.csv --format none  # JSON to stdout only

The artifact bundle includes the envelope fields defined in
``references/multi-agent-orchestration.md`` so a parent agent can pick up the
output and dispatch the remaining stages (method-planner → execution → critic →
report) from where this script leaves off.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — same pattern as ds_bootstrap.py so the script works from
# any directory (plugin cache, local repo clone, pip install).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent


def _setup_path() -> str:
    """Ensure ``ds_skill`` + ``profile_dataset`` are importable."""
    # Already importable (pip install -e . was run in the repo)
    try:
        import ds_skill  # noqa: F401
        return str(Path(ds_skill.__file__).resolve().parent.parent)
    except ImportError:
        pass

    # This file sits next to ds_skill/ and profile_dataset.py
    _resolved = str(_SCRIPTS_DIR.resolve())
    if _resolved not in sys.path:
        sys.path.insert(0, _resolved)

    # Try ds_bootstrap as a fallback (it walks the filesystem)
    try:
        from ds_bootstrap import ensure_importable
        return ensure_importable()
    except ImportError:
        # Last resort: the scripts dir itself
        try:
            import ds_skill  # noqa: F401
            return _resolved
        except ImportError:
            pass

    raise ImportError(
        "Cannot locate ds_skill. Run: pip install -e .  in the repo, or set "
        "CLAUDE_PLUGIN_ROOT / DS_SKILL_ROOT, or put this script's directory on sys.path."
    )


_scripts_path = _setup_path()

import profile_dataset as profiler
from ds_skill.correlation import correlation_with_target
from ds_skill.readiness import assess_readiness
from ds_skill.shaping import detect_grain, detect_leakage_columns

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

# Short descriptions of each ds_skill.readiness dimension for human-readable output
_DIMENSION_LABELS: dict[str, str] = {
    "sample_size": "Sample size adequate",
    "missingness": "Missingness within acceptable bounds",
    "grain": "Grain is well-defined",
    "time_coverage": "Time coverage sufficient",
    "balance": "Group balance adequate",
    "leakage": "No obvious leakage columns",
    "role_clarity": "Target / feature roles clear",
    "measurement_reliability": "Measurement reliability acceptable",
}


def run_workflow(
    path: Path,
    *,
    target: str | None = None,
    sheet: str | int | None = None,
    sample_rows: int = 10_000,
    output_dir: Path | None = None,
    emit_markdown: bool = True,
    emit_json: bool = True,
) -> dict[str, Any]:
    """Run the baseline pipeline and return the artifact bundle.

    Parameters
    ----------
    path:
        CSV, Excel, Parquet, or JSON file to analyse.
    target:
        Column name for the target metric ``Y``. If omitted the pipeline stops
        after readiness + shaping (no driver ranking).
    sheet:
        Excel sheet name or zero-based index.
    sample_rows:
        Max rows to profile (passed to ``profile_dataset.build_profile``).
    output_dir:
        Directory for the JSON + markdown outputs. Defaults to the current
        working directory.
    emit_markdown:
        When True, also write a ``baseline_skeleton.md`` alongside the JSON.
    emit_json:
        When True and ``output_dir`` is set, write ``baseline_artifacts.json``.

    Returns
    -------
    dict
        The full artifact bundle (also written to ``baseline_artifacts.json``).
    """
    out = output_dir or Path.cwd()
    if output_dir is not None and (emit_markdown or emit_json):
        out.mkdir(parents=True, exist_ok=True)

    normalized_sheet = sheet if isinstance(sheet, int) else profiler.normalize_sheet(sheet)

    # ---- Stage 1: Intake / profile ----
    profile = profiler.build_profile(path, normalized_sheet, sample_rows)

    # ---- Stage 2: Readiness ----
    df = profiler.read_table(path, normalized_sheet, sample_rows)[0]
    readiness = assess_readiness(df, target=target)

    # ---- Stage 3: Shaping lite (grain + leakage) ----
    grain = detect_grain(df)
    if target:
        if target in df.columns:
            leakage = detect_leakage_columns(df, target=target, time_col=None)
        else:
            leakage = None
    else:
        leakage = None

    # ---- Stage 4: Baseline evidence (correlation → driver ranking) ----
    correlation_rows: list[dict[str, Any]] = []
    driver_ranking: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    if target and target in df.columns:
        try:
            results = correlation_with_target(df, target=target)
            correlation_rows = [
                {
                    "feature": r.x,
                    "target": r.y,
                    "method": r.method,
                    "coefficient": r.coefficient,
                    "p_value": r.p_value,
                    "p_adjusted": r.p_value_fdr_adjusted,
                    "significant_after_fdr": r.significant_after_fdr,
                    "n": r.n,
                    "effect_strength": r.effect_strength,
                    "interpretation": r.interpretation,
                }
                for r in results
            ]
            # Derive a simple driver ranking from correlation results
            scored = sorted(
                [r for r in correlation_rows if r["effect_strength"] is not None],
                key=lambda r: r["effect_strength"],
                reverse=True,
            )
            driver_ranking = [
                {"rank": i + 1, "feature": r["feature"], "method": r["method"],
                 "strength": r["effect_strength"], "interpretation": r["interpretation"]}
                for i, r in enumerate(scored[:10])
            ]
        except Exception as exc:
            # Correlation may fail if target is non-numeric or sparse; keep the
            # pipeline usable, but make the failed evidence path explicit.
            warnings.append(
                {
                    "stage": "baseline_evidence",
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                }
            )
    elif target:
        warnings.append(
            {
                "stage": "baseline_evidence",
                "error_type": "MissingTargetColumn",
                "message": f"Target column not found: {target}",
            }
        )

    # ---- Assemble artifact bundle ----
    readiness_report = {
        "overall_status": readiness.overall_status,
        "dimensions": {
            key: {"status": dim.status, "evidence": dim.evidence}
            for key, dim in readiness.dimensions.items()
        },
        "caveats": readiness.caveats,
        "narrowed_scope_suggestions": readiness.narrowed_scope_suggestions,
        "data_request": readiness.data_request,
    }
    shaping = {
        "grain": {
            "keys_tested": grain.keys_tested,
            "is_unique": grain.is_unique,
            "n_total_rows": grain.n_total_rows,
            "n_unique_keys": grain.n_unique_keys,
            "duplicate_examples": grain.duplicate_examples,
            "inferred_grain": grain.inferred_grain,
        },
        "leakage": {
            "target": leakage.target if leakage else None,
            "flagged_columns": leakage.flagged_columns if leakage else [],
            "name_based_flags": leakage.name_based_flags if leakage else [],
            "correlation_based_flags": leakage.correlation_based_flags if leakage else [],
            "time_based_flags": leakage.time_based_flags if leakage else [],
        },
    }
    baseline_evidence = {
        "correlation": correlation_rows,
        "driver_ranking": driver_ranking,
    }
    next_stage_hint = {
        "stages": ["method-planner", "execution", "critic", "report"],
        "can_parallelize": False,
        "rationale": (
            "Baseline pipeline complete. Hand off to method-planner for "
            "full method selection, then fan-out execution, critic, and report."
            if target and not warnings
            else "Baseline pipeline completed with warnings; review blockers before method planning."
            if warnings
            else "No target column provided; run exploratory profiling or add --target for driver ranking."
        ),
    }

    bundle: dict[str, Any] = {
        "stage": "baseline",
        "status": "partial" if warnings else "ok",
        "produced": {
            "data_manifest": profile,
            "readiness_report": readiness_report,
            "shaping": shaping,
            "baseline_evidence": baseline_evidence,
            "warnings": warnings,
        },
        "carry_forward": {
            "data_manifest": profile,
            "field_role_candidates": profile.get("role_candidates", []),
            "readiness_report": readiness_report,
            "analysis_views": [],
            "analysis_plan": {},
            "evidence_matrix": correlation_rows,
            "critique": {},
        },
        "next_stage_hint": next_stage_hint,
        "blockers": warnings,
        "human_questions": [],
        "pipeline": "run_full_workflow",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(path),
        "target": target,
        "data_manifest": profile,
        "readiness_report": readiness_report,
        "shaping": shaping,
        "baseline_evidence": baseline_evidence,
        "warnings": warnings,
    }

    # ---- Write JSON ----
    if emit_json and output_dir is not None:
        json_path = out / "baseline_artifacts.json"
        json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ---- Write markdown skeleton ----
    if emit_markdown:
        _write_skeleton_md(out, bundle)

    return bundle


# ---------------------------------------------------------------------------
# Markdown skeleton
# ---------------------------------------------------------------------------

_SKELETON_TEMPLATE = """\
# Baseline Analysis: {source}

**Generated:** {timestamp}
**Target:** {target_summary}
**Readiness:** {readiness_status}

---

## Data Profile

| Column | Dtype | Non-null % | Sample values |
|--------|-------|------------|---------------|
{profile_rows}

**Row count:** {row_count}  ·  **Columns:** {col_count}

## Readiness Assessment

{readiness_table}

## Grain & Leakage

- **Recommended grain:** {grain_label}
- **Leaked columns flagged:** {leakage_summary}

{leakage_detail}

## Baseline Evidence

{evidence_section}

## Next Steps

{next_steps}
"""


def _write_skeleton_md(out_dir: Path, bundle: dict[str, Any]) -> None:
    manifest = bundle["data_manifest"]["manifest"]
    readiness = bundle["readiness_report"]
    shaping = bundle["shaping"]
    evidence = bundle["baseline_evidence"]

    # Profile table rows
    col_profiles = bundle["data_manifest"].get("column_profiles", {})
    if col_profiles:
        profile_row_lines: list[str] = []
        for col_name, cp in col_profiles.items():
            pct = cp.get("non_null_pct", 100)
            samples = ", ".join(str(v) for v in cp.get("sample_values", [])[:3])
            profile_row_lines.append(f"| {col_name} | {cp.get('dtype', '?')} | {pct:.0f}% | {samples} |")
        profile_rows = "\n".join(profile_row_lines)
    else:
        profile_rows = "| (no column profiles) | — | — | — |"

    # Readiness dimensions table
    dim_lines: list[str] = []
    for key, dim in readiness.get("dimensions", {}).items():
        label = _DIMENSION_LABELS.get(key, key)
        status_icon = {"ok": "✅", "partial": "⚠️", "blocked": "🛑"}.get(dim["status"], "❓")
        dim_lines.append(f"| {label} | {status_icon} {dim['status']} | {dim.get('evidence', '')[:120]} |")
    readiness_table = "\n".join(dim_lines) if dim_lines else "| — | — | — |"

    # Grain
    grain_label = shaping["grain"].get("inferred_grain") or "not determined"

    # Leakage
    leaked = shaping["leakage"].get("flagged_columns", [])
    leakage_summary = f"{len(leaked)} column(s)" if leaked else "none"
    if leaked:
        leakage_detail = "\n".join(
            f"- `{c['column']}` — {c.get('reason', 'potential leakage')}" for c in leaked
        )
    else:
        leakage_detail = "_No leakage columns detected._"

    # Evidence
    ranking = evidence.get("driver_ranking", []) or []
    if ranking:
        rank_lines = "\n".join(
            f"| {r['rank']} | `{r['feature']}` | {r.get('strength', '—'):.3f} | {r.get('interpretation', '')} |"
            for r in ranking[:10]
        )
        evidence_section = f"""\
| Rank | Feature | Strength | Interpretation |
|------|---------|----------|----------------|
{rank_lines}

*Full correlation matrix is in `baseline_artifacts.json`.*"""
    else:
        if bundle.get("target"):
            evidence_section = "_No baseline driver ranking produced; review warnings in `baseline_artifacts.json`._"
        else:
            evidence_section = "_No target column specified; driver ranking skipped. Add `--target <column>` to enable._"

    # Caveats
    caveats = readiness.get("caveats", []) or []
    if caveats:
        evidence_section += "\n\n### Readiness Caveats\n\n" + "\n".join(f"- {c}" for c in caveats)

    # Next steps
    next_steps = bundle.get("next_stage_hint", {}).get("rationale", "")

    target = bundle.get("target")
    target_summary = f"`{target}`" if target else "_(not specified — exploratory mode)_"

    md = _SKELETON_TEMPLATE.format(
        source=str(bundle.get("source_file", "unknown")),
        timestamp=bundle.get("generated_at", ""),
        target_summary=target_summary,
        readiness_status=readiness.get("overall_status", "unknown"),
        profile_rows=profile_rows,
        row_count=manifest.get("sampled_rows", 0),
        col_count=len(manifest.get("columns", [])),
        readiness_table=readiness_table,
        grain_label=grain_label,
        leakage_summary=leakage_summary,
        leakage_detail=leakage_detail,
        evidence_section=evidence_section,
        next_steps=next_steps,
    )

    (out_dir / "baseline_skeleton.md").write_text(md, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic baseline pipeline — profile → readiness → shaping → baseline evidence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python run_full_workflow.py data.csv --target yield_pct
              python run_full_workflow.py data.xlsx --sheet Sheet1 --target defect_rate
              python run_full_workflow.py data.csv --format none   # JSON only
        """),
    )
    parser.add_argument("path", type=Path, help="CSV, Excel, Parquet, or JSON file.")
    parser.add_argument("--target", default=None, help="Target metric column (Y).")
    parser.add_argument("--sheet", default=None, help="Excel sheet name or 0-based index.")
    parser.add_argument(
        "--sample-rows", type=int, default=10_000, help="Max rows to profile (default: 10000)."
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output directory (default: current dir)."
    )
    parser.add_argument(
        "--format",
        choices=["all", "json", "md", "none"],
        default="all",
        help="Output format: all (json+md), json, md, or none (JSON to stdout only).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.format == "none":
        args.output = None

    try:
        bundle = run_workflow(
            path=args.path,
            target=args.target,
            sheet=args.sheet,
            sample_rows=args.sample_rows,
            output_dir=args.output,
            emit_markdown=args.format in ("all", "md"),
            emit_json=args.format in ("all", "json"),
        )
        if args.format == "none":
            print(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))
        elif args.format == "json":
            json_path = (args.output or Path.cwd()) / "baseline_artifacts.json"
            print(f"JSON written to {json_path}")
        else:
            out = args.output or Path.cwd()
            print(f"Artifacts written to {out.resolve()}")
            if args.format in ("all", "json"):
                print(f"  baseline_artifacts.json  — full JSON bundle")
            if args.format in ("all", "md"):
                print(f"  baseline_skeleton.md    — markdown skeleton")
        return 0
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
