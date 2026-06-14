#!/usr/bin/env python3
"""Deterministic scorer for data-scientist eval cases.

Usage::

    python score_case.py <case_dir> <run_dir> [--json out.json] [--subset l1]

``case_dir`` holds ``ground_truth.json`` (+ prompt.txt, dataset).
``run_dir`` holds whatever the agent (L2) or baseline pipeline (L1) produced:
artifact JSON files, markdown reports, and chart images.

All checks are machine-decidable:

1. routing      — required artifacts exist / forbidden artifacts absent
2. artifacts    — JSON parses and contains required keys / dimension envelope
3. findings     — regex evidence match over all text artifacts (+ numeric tolerance)
4. charts       — chart file count and filename keyword groups
5. anti_patterns— forbidden regex over the final report text

Exit code 0 if total score >= --threshold (default 0, i.e. always 0 unless set).
Prints a per-check table and a JSON summary.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CHART_EXTS = {".png", ".svg", ".jpg", ".jpeg", ".pdf"}
TEXT_EXTS = {".md", ".txt", ".json", ".html"}

# Artifact name -> filename fragments accepted as that artifact.
ARTIFACT_ALIASES: dict[str, list[str]] = {
    "data_manifest": ["data_manifest", "manifest"],
    "readiness_report": ["readiness_report", "readiness"],
    "analysis_plan": ["analysis_plan", "plan"],
    "analysis_views": ["analysis_views", "views"],
    "evidence_matrix": ["evidence_matrix", "evidence"],
    "critique": ["critique", "critic"],
    "final_report": ["final_report", "report"],
}

# Weights per check category (sum need not be 1; normalized at the end).
WEIGHTS = {
    "routing_must": 3.0,
    "routing_must_not": 3.0,
    "artifact_schema": 2.0,
    "finding": 4.0,
    "charts": 2.0,
    "anti_pattern": 3.0,
}


@dataclass
class Check:
    category: str
    check_id: str
    passed: bool
    weight: float
    detail: str = ""


@dataclass
class RunFiles:
    """Indexed view over everything found in the run directory."""

    artifact_files: dict[str, Path] = field(default_factory=dict)
    text_blob: str = ""
    report_blob: str = ""
    chart_files: list[Path] = field(default_factory=list)


def _find_artifact(run_dir: Path, artifact: str) -> Path | None:
    aliases = ARTIFACT_ALIASES.get(artifact, [artifact])
    candidates: list[Path] = []
    for p in sorted(run_dir.rglob("*")):
        if not p.is_file():
            continue
        stem = p.stem.lower()
        for alias in aliases:
            if alias in stem:
                candidates.append(p)
                break
    if not candidates:
        return None
    # Prefer json for structured artifacts, md for the report
    preferred_ext = ".md" if artifact == "final_report" else ".json"
    for c in candidates:
        if c.suffix == preferred_ext:
            return c
    return candidates[0]


def _extract_json(path: Path) -> dict | list | None:
    """Parse JSON from a file, tolerating JSON embedded in a markdown code fence."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback: fenced code blocks
    for m in re.finditer(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL):
        try:
            return json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def index_run_dir(run_dir: Path) -> RunFiles:
    rf = RunFiles()
    text_parts: list[str] = []
    for p in sorted(run_dir.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        if p.suffix.lower() in CHART_EXTS:
            rf.chart_files.append(p)
        elif p.suffix.lower() in TEXT_EXTS:
            try:
                text_parts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    rf.text_blob = "\n\n".join(text_parts)
    for artifact in ARTIFACT_ALIASES:
        found = _find_artifact(run_dir, artifact)
        if found is not None:
            rf.artifact_files[artifact] = found
    report = rf.artifact_files.get("final_report")
    if report is not None:
        rf.report_blob = report.read_text(encoding="utf-8", errors="replace")
    else:
        rf.report_blob = rf.text_blob
    return rf


def _search(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error as exc:
        raise SystemExit(f"Invalid regex in ground truth: {pattern!r}: {exc}")


def score_routing(gt: dict, rf: RunFiles) -> list[Check]:
    checks: list[Check] = []
    routing = gt.get("routing", {})
    for artifact in routing.get("must_produce_artifacts", []):
        found = artifact in rf.artifact_files
        checks.append(
            Check(
                "routing_must",
                f"produce:{artifact}",
                found,
                WEIGHTS["routing_must"],
                str(rf.artifact_files.get(artifact, "MISSING")),
            )
        )
    for artifact in routing.get("must_not_produce", []):
        absent = artifact not in rf.artifact_files
        checks.append(
            Check(
                "routing_must_not",
                f"absent:{artifact}",
                absent,
                WEIGHTS["routing_must_not"],
                "correctly absent" if absent else f"unexpected: {rf.artifact_files[artifact]}",
            )
        )
    return checks


def score_artifacts(gt: dict, rf: RunFiles) -> list[Check]:
    checks: list[Check] = []
    for artifact, spec in gt.get("artifacts", {}).items():
        path = rf.artifact_files.get(artifact)
        if path is None:
            checks.append(
                Check("artifact_schema", f"schema:{artifact}", False,
                      WEIGHTS["artifact_schema"], "artifact not found")
            )
            continue
        data = _extract_json(path)
        if data is None:
            checks.append(
                Check("artifact_schema", f"schema:{artifact}", False,
                      WEIGHTS["artifact_schema"], f"unparseable JSON: {path.name}")
            )
            continue
        problems: list[str] = []
        for key in spec.get("required_keys", []):
            if isinstance(data, dict) and key not in _flatten_keys(data):
                problems.append(f"missing key {key!r}")
        min_dims = spec.get("min_dimensions")
        if min_dims:
            n_dims = _count_dimensions(data)
            if n_dims < min_dims:
                problems.append(f"only {n_dims}/{min_dims} dimensions")
        allowed = spec.get("allowed_scores")
        if allowed:
            blob = json.dumps(data, ensure_ascii=False).lower()
            if not any(s in blob for s in allowed):
                problems.append(f"no {allowed} scores found")
        checks.append(
            Check("artifact_schema", f"schema:{artifact}", not problems,
                  WEIGHTS["artifact_schema"], "; ".join(problems) or "ok")
        )
    return checks


def _flatten_keys(obj: object, depth: int = 0) -> set[str]:
    keys: set[str] = set()
    if depth > 6:
        return keys
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= _flatten_keys(v, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:50]:
            keys |= _flatten_keys(item, depth + 1)
    return keys


def _count_dimensions(data: object) -> int:
    """Count readiness dimensions in common envelope shapes."""
    if isinstance(data, dict):
        for key in ("dimensions", "scores", "dimension_scores"):
            val = data.get(key)
            if isinstance(val, dict):
                return len(val)
            if isinstance(val, list):
                return len(val)
        # nested one level (e.g. {"readiness_report": {...}})
        return max((_count_dimensions(v) for v in data.values() if isinstance(v, (dict, list))), default=0)
    if isinstance(data, list):
        return len(data)
    return 0


def score_findings(gt: dict, rf: RunFiles) -> list[Check]:
    checks: list[Check] = []
    for finding in gt.get("findings", []):
        fid = finding["id"]
        pattern = finding.get("evidence_regex")
        if pattern is None:
            continue  # handled by other categories (see ground truth note)
        hit = _search(pattern, rf.text_blob)
        tier = finding.get("tier", "required")
        detail = "matched" if hit else "no evidence match"
        numeric = finding.get("numeric")
        if hit and numeric:
            m = re.search(numeric["pattern"], rf.text_blob, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1))
                    ok = abs(val - numeric["expected"]) <= numeric["tolerance"]
                    hit = ok
                    detail = f"value={val} expected={numeric['expected']}±{numeric['tolerance']}"
                except (ValueError, IndexError):
                    detail = "numeric group unparseable; keyword evidence accepted"
            else:
                detail = "keyword matched but numeric pattern not found"
        # Use the GT's per-finding weight (required findings carry more weight
        # than optional ones) instead of a flat 4.0. Falls back to the default
        # when a finding omits an explicit weight.
        weight = float(finding.get("weight", WEIGHTS["finding"]))
        checks.append(Check("finding", fid, hit, weight, f"[{tier}] {detail}"))
    return checks


def score_charts(gt: dict, rf: RunFiles) -> list[Check]:
    checks: list[Check] = []
    spec = gt.get("charts", {})
    min_count = spec.get("min_count", 0)
    if min_count > 0:
        ok = len(rf.chart_files) >= min_count
        checks.append(
            Check("charts", f"count>={min_count}", ok, WEIGHTS["charts"],
                  f"found {len(rf.chart_files)} chart files")
        )
    names = " ".join(p.name.lower() for p in rf.chart_files)
    for kw_group in spec.get("required_keywords", []):
        ok = _search(kw_group, names) or _search(kw_group, rf.report_blob)
        checks.append(
            Check("charts", f"type:{kw_group[:30]}", ok, WEIGHTS["charts"],
                  "found" if ok else "missing chart type")
        )
    return checks


def score_anti_patterns(gt: dict, rf: RunFiles) -> list[Check]:
    checks: list[Check] = []
    for ap in gt.get("anti_patterns", []):
        text = rf.report_blob if ap.get("scope") == "final_report" else rf.text_blob
        violated = _search(ap["forbidden_regex"], text)
        checks.append(
            Check("anti_pattern", ap["id"], not violated, WEIGHTS["anti_pattern"],
                  "clean" if not violated else "forbidden pattern present")
        )
    return checks


L1_CATEGORIES = {"routing_must", "artifact_schema"}  # deterministic-pipeline subset
# The baseline pipeline (run_full_workflow.py) only reaches profile → readiness →
# shaping → baseline evidence, so L1 can only judge these artifacts:
L1_ARTIFACTS = {"data_manifest", "readiness_report"}


def _l1_relevant(check: Check) -> bool:
    if check.category not in L1_CATEGORIES:
        return False
    artifact = check.check_id.split(":", 1)[-1]
    return artifact in L1_ARTIFACTS


# Two-line scoring (audit 2026-06-14): keep the process-adherence signal
# (deterministic, ~zero variance — did the agent follow the skill's
# non-negotiable gates?) separate from the outcome-quality signal (did the
# analysis reach the right conclusions?). The flywheel reads process_score when
# tuning skill workflow requirements; outcome_score is dominated by base-model
# capability and must be compared as a distribution, not a single point.
PROCESS_CATEGORIES = {"routing_must", "routing_must_not", "artifact_schema"}
OUTCOME_CATEGORIES = {"finding", "charts", "anti_pattern"}


def _weighted_score(checks: list[Check]) -> float | None:
    """Weighted pass-rate over a check subset; None when the subset is empty."""
    if not checks:
        return None
    total_w = sum(c.weight for c in checks) or 1.0
    earned = sum(c.weight for c in checks if c.passed)
    return round(100.0 * earned / total_w, 1)


def score_case(case_dir: Path, run_dir: Path, subset: str = "full") -> dict:
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    rf = index_run_dir(run_dir)

    checks: list[Check] = []
    checks += score_routing(gt, rf)
    checks += score_artifacts(gt, rf)
    checks += score_findings(gt, rf)
    checks += score_charts(gt, rf)
    checks += score_anti_patterns(gt, rf)

    if subset == "l1":
        checks = [c for c in checks if _l1_relevant(c)]

    total_w = sum(c.weight for c in checks) or 1.0
    earned = sum(c.weight for c in checks if c.passed)
    score = round(100.0 * earned / total_w, 1)

    process_checks = [c for c in checks if c.category in PROCESS_CATEGORIES]
    outcome_checks = [c for c in checks if c.category in OUTCOME_CATEGORIES]
    return {
        "case_id": gt.get("case_id", case_dir.name),
        "run_dir": str(run_dir),
        "subset": subset,
        "score": score,
        "process_score": _weighted_score(process_checks),
        "outcome_score": _weighted_score(outcome_checks),
        "passed": sum(c.passed for c in checks),
        "total": len(checks),
        "checks": [
            {"category": c.category, "id": c.check_id, "passed": c.passed,
             "weight": c.weight, "detail": c.detail}
            for c in checks
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--json", type=Path, default=None, help="write summary JSON here")
    ap.add_argument("--subset", choices=["full", "l1"], default="full")
    ap.add_argument("--mode", choices=["regex", "judge", "hybrid"], default="regex",
                    help="scoring mode: regex (legacy), judge (agent-based), hybrid (both)")
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="exit non-zero if score < threshold")
    args = ap.parse_args()

    if not (args.case_dir / "ground_truth.json").exists():
        print(f"error: no ground_truth.json in {args.case_dir}", file=sys.stderr)
        return 2
    if not args.run_dir.is_dir():
        print(f"error: run dir not found: {args.run_dir}", file=sys.stderr)
        return 2

    # Choose scoring method
    if args.mode == "judge":
        # Agent-based LLM judge only
        from judge_score import score_case_with_agent_judge
        result = score_case_with_agent_judge(args.case_dir, args.run_dir)
        print(f"\n=== {result['case_id']}  judge_score={result['overall_score']} ===")
        for dim, score_data in result["judge_scores"].items():
            score = score_data["score"]
            print(f"  [{dim:15s}] {score}/3  {score_data['rationale'][:60]}...")
        if result.get("defects"):
            print(f"\nDefects: {len(result['defects'])}")
            for d in result["defects"][:5]:
                print(f"  - [{d['dimension']}] {d['defect'][:80]}...")
    elif args.mode == "hybrid":
        # Both regex and judge, weighted average
        regex_result = score_case(args.case_dir, args.run_dir, args.subset)
        from judge_score import score_case_with_agent_judge
        judge_result = score_case_with_agent_judge(args.case_dir, args.run_dir)

        # Combine: 40% regex + 60% judge
        combined_score = 0.4 * regex_result["score"] + 0.6 * judge_result["overall_score"]
        result = {
            "case_id": regex_result["case_id"],
            "mode": "hybrid",
            "regex_score": regex_result["score"],
            "judge_score": judge_result["overall_score"],
            "combined_score": round(combined_score, 1),
            "regex_details": regex_result,
            "judge_details": judge_result
        }
        print(f"\n=== {result['case_id']}  hybrid_score={result['combined_score']} ===")
        print(f"  Regex: {result['regex_score']}")
        print(f"  Judge: {result['judge_score']}")
        print(f"  Combined (0.4×regex + 0.6×judge): {result['combined_score']}")
    else:
        # Deterministic two-line scoring (regex)
        result = score_case(args.case_dir, args.run_dir, args.subset)
        print(f"\n=== {result['case_id']}  score={result['score']}  "
              f"(process={result['process_score']} outcome={result['outcome_score']}; "
              f"{result['passed']}/{result['total']} checks) ===")
        for c in result["checks"]:
            mark = "PASS" if c["passed"] else "FAIL"
            print(f"  [{mark}] {c['category']:<16} {c['id']:<40} {c['detail']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nsummary written to {args.json}")

    score_value = result.get("overall_score") or result.get("combined_score") or result.get("score", 0)
    return 0 if score_value >= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
