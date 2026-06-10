#!/usr/bin/env python3
"""L1 deterministic eval: run the baseline pipeline over scoreable cases.

For each case with a ``target`` defined (case 01-05, 08), runs
``scripts/run_full_workflow.py <dataset> --target <Y> --output <run_dir>`` and
scores the produced artifact bundle with the ``l1`` subset of checks
(artifact existence + schema). Behavioral cases (06, 07 routing) are skipped —
those need a real agent (L2, see run_l2.md).

Zero tokens. Safe for CI.

Usage::

    python evals/harness/run_l1.py            # all L1 cases
    python evals/harness/run_l1.py case-04-spc
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = EVALS_DIR.parent
WORKFLOW = (
    REPO_ROOT
    / "plugins/data-scientist/skills/analysis-workflow/scripts/run_full_workflow.py"
)
RUNS_DIR = EVALS_DIR / ".runs" / "l1"

# Behavioral / routing cases are not runnable by the deterministic pipeline.
SKIP_CASES = {"case-06-routing-profile-only", "case-07-routing-named-method"}


def find_dataset(case_dir: Path, gt: dict) -> Path:
    return (case_dir / gt["dataset"]).resolve()


def explode_bundle(run_dir: Path) -> None:
    """Split baseline_artifacts.json into per-artifact JSON files.

    The baseline pipeline writes one bundle; the scorer (shared with L2)
    expects individually named artifact files.
    """
    bundle_path = run_dir / "baseline_artifacts.json"
    if not bundle_path.exists():
        return
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    produced = bundle.get("produced", {})
    for artifact in ("data_manifest", "readiness_report", "analysis_views"):
        payload = produced.get(artifact) or bundle.get(artifact)
        if payload:
            (run_dir / f"{artifact}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )


def run_case(case_dir: Path) -> dict | None:
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    if case_dir.name in SKIP_CASES or not gt.get("target"):
        print(f"-- skip {case_dir.name} (agent-only case)")
        return None

    dataset = find_dataset(case_dir, gt)
    run_dir = RUNS_DIR / case_dir.name
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(WORKFLOW),
        str(dataset),
        "--target",
        gt["target"],
        "--output",
        str(run_dir),
    ]
    print(f"\n== {case_dir.name}: {' '.join(cmd[1:])}")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode != 0:
        # A "blocked" readiness decision may legitimately stop the pipeline —
        # the scorer decides whether the artifacts that exist are sufficient.
        print(f"   pipeline exited {proc.returncode}")
        if proc.stderr.strip():
            print("   stderr tail:", proc.stderr.strip().splitlines()[-1])

    explode_bundle(run_dir)

    score_cmd = [
        sys.executable,
        str(EVALS_DIR / "harness" / "score_case.py"),
        str(case_dir),
        str(run_dir),
        "--subset",
        "l1",
        "--json",
        str(run_dir / "score.json"),
    ]
    subprocess.run(score_cmd, cwd=REPO_ROOT)
    score_file = run_dir / "score.json"
    if score_file.exists():
        return json.loads(score_file.read_text(encoding="utf-8"))
    return {"case_id": case_dir.name, "score": 0.0, "error": "scoring failed"}


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    cases = sorted((EVALS_DIR / "cases").iterdir())
    results: list[dict] = []
    for case_dir in cases:
        if not case_dir.is_dir():
            continue
        if only and only not in case_dir.name:
            continue
        result = run_case(case_dir)
        if result is not None:
            results.append(result)

    if not results:
        print("no cases run")
        return 1

    print("\n================ L1 SUMMARY ================")
    all_ok = True
    for r in results:
        status = "OK " if r["score"] >= 100.0 else "LOW"
        if r["score"] < 100.0:
            all_ok = False
        print(f"  [{status}] {r['case_id']:<36} {r['score']}")
    mean = round(sum(r["score"] for r in results) / len(results), 1)
    print(f"  mean = {mean}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
