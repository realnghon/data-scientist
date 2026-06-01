from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "plugins/data-scientist/skills/analysis-workflow/scripts/run_full_workflow.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_full_workflow", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_dataset(path: Path) -> Path:
    df = pd.DataFrame(
        {
            "yield_pct": [91.0, 92.5, 87.0, 88.1, 94.2, 86.4, 90.0, 89.5, 93.1, 85.8, 91.7, 87.9],
            "temp_c": [120.0, 121.0, 130.0, 129.0, 119.5, 131.0, 122.0, 128.0, 120.5, 132.0, 121.5, 129.5],
            "pressure_kpa": [300.0, 302.0, 315.0, 314.0, 301.0, 316.0, 303.0, 313.0, 300.5, 317.0, 302.5, 314.5],
            "line": ["A", "A", "B", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        }
    )
    dataset = path / "mini_yield.csv"
    df.to_csv(dataset, index=False)
    return dataset


def test_run_workflow_writes_json_and_markdown(tmp_path):
    module = load_module()
    dataset = make_dataset(tmp_path)
    out = tmp_path / "out"

    bundle = module.run_workflow(dataset, target="yield_pct", output_dir=out)

    assert bundle["pipeline"] == "run_full_workflow"
    assert bundle["stage"] == "baseline"
    assert bundle["status"] == "ok"
    assert set(["produced", "carry_forward", "next_stage_hint", "blockers", "human_questions"]).issubset(bundle)
    assert bundle["target"] == "yield_pct"
    assert bundle["data_manifest"]["status"] == "ok"
    assert "readiness_report" in bundle
    assert "shaping" in bundle
    assert "baseline_evidence" in bundle
    assert (out / "baseline_artifacts.json").is_file()
    assert (out / "baseline_skeleton.md").is_file()

    payload = json.loads((out / "baseline_artifacts.json").read_text(encoding="utf-8"))
    assert payload["target"] == "yield_pct"
    assert payload["carry_forward"]["data_manifest"]["status"] == "ok"
    assert payload["next_stage_hint"]["can_parallelize"] is False
    assert payload["baseline_evidence"]["correlation"]
    assert "# Baseline Analysis" in (out / "baseline_skeleton.md").read_text(encoding="utf-8")


def test_run_workflow_without_target_skips_driver_ranking(tmp_path):
    module = load_module()
    dataset = make_dataset(tmp_path)
    out = tmp_path / "out"

    bundle = module.run_workflow(dataset, output_dir=out)

    assert bundle["target"] is None
    assert bundle["baseline_evidence"]["correlation"] == []
    assert bundle["baseline_evidence"]["driver_ranking"] == []
    md = (out / "baseline_skeleton.md").read_text(encoding="utf-8")
    assert "No target column specified" in md


def test_cli_none_prints_json_to_stdout(tmp_path):
    dataset = make_dataset(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(dataset),
            "--target",
            "yield_pct",
            "--output",
            str(tmp_path / "out"),
            "--format",
            "none",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["source_file"] == str(dataset)
    assert payload["target"] == "yield_pct"


def test_cli_md_writes_only_markdown_file(tmp_path):
    dataset = make_dataset(tmp_path)
    out = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(dataset),
            "--target",
            "yield_pct",
            "--output",
            str(out),
            "--format",
            "md",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert (out / "baseline_skeleton.md").is_file()
    assert not (out / "baseline_artifacts.json").exists()


def test_missing_target_is_reported_as_blocker(tmp_path):
    module = load_module()
    dataset = make_dataset(tmp_path)

    bundle = module.run_workflow(dataset, target="missing_y", emit_markdown=False, emit_json=False)

    assert bundle["status"] == "partial"
    assert bundle["baseline_evidence"]["correlation"] == []
    assert bundle["blockers"][0]["error_type"] == "MissingTargetColumn"


def test_non_numeric_target_warning_is_visible(tmp_path):
    module = load_module()
    dataset = make_dataset(tmp_path)

    bundle = module.run_workflow(dataset, target="line", emit_markdown=False, emit_json=False)

    assert bundle["status"] == "partial"
    assert bundle["warnings"]
    assert bundle["blockers"] == bundle["warnings"]
    assert bundle["baseline_evidence"]["driver_ranking"] == []


def test_cli_missing_file_exits_with_error(tmp_path):
    missing = tmp_path / "missing.csv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(missing), "--format", "none"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "Dataset not found" in result.stderr
