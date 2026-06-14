#!/usr/bin/env python3
"""Judge-median scorer: run the agent judge N times on one run dir, take the median.

历史上本模块有 Stage-1 regex 初筛硬门（required findings coverage < 50% → 直接判 0 分、
不进 judge）。审计 2026-06-14 移除该硬门：它把选手单次行为方差放大成 0 分悬崖，与 skill
改动毫无因果（flywheel-iter2 的 0 分就是这么误判出来的）。

职责重新划分后：
- 确定性的「流程遵循度 / 结论命中」分数统一由 ``score_case.py`` 的
  ``process_score`` / ``outcome_score`` 提供（加权、无硬门）。
- 本模块只负责消除 agent judge 的 LLM 非确定性——同一份产物跑 N 次 judge 取中位数，
  并报告离散度（``judge_std``），供 ``run_l2.py`` 与飞轮 A/B 对照复用。

Usage::

    python evals/harness/score_two_stage.py <case_dir> <run_dir> [--runs N] [--json out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# 复用同目录下的单次 agent judge
sys.path.insert(0, str(Path(__file__).parent))
from judge_score import score_case_with_agent_judge


def judge_median(case_dir: Path, run_dir: Path, runs: int = 3) -> dict:
    """Run the agent judge ``runs`` times on one run dir; return median + spread.

    取中位数（而非均值）抗单次离群；同时报告 ``judge_std`` 让调用方判断该分数可不可信
    ——std 大说明 judge 本身不稳定，单点比较无意义。
    """
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    case_id = gt.get("case_id", case_dir.name)

    scores: list[float] = []
    details: list[dict] = []
    for i in range(runs):
        try:
            result = score_case_with_agent_judge(case_dir, run_dir)
            scores.append(result["overall_score"])
            details.append(result)
            print(f"  judge run {i + 1}/{runs}: {result['overall_score']:.1f}")
        except Exception as exc:  # 单次失败不毁掉整轮
            print(f"  judge run {i + 1}/{runs} failed: {exc}", file=sys.stderr)
            continue

    if not scores:
        return {"case_id": case_id, "overall_score": 0.0, "judge_std": 0.0,
                "judge_scores_raw": [], "stage": "judge_all_failed"}

    median_score = float(np.median(scores))
    std_score = float(np.std(scores)) if len(scores) > 1 else 0.0
    # 选最贴近中位数的那一次详情（dims / defects）
    median_idx = min(range(len(scores)), key=lambda i: abs(scores[i] - median_score))
    median_detail = details[median_idx]

    return {
        "case_id": case_id,
        "overall_score": round(median_score, 1),
        "judge_std": round(std_score, 1),
        "judge_scores_raw": scores,
        "judge_scores": median_detail.get("judge_scores", {}),
        "defects": median_detail.get("defects", []),
        "stage": "judge_median",
    }


# 向后兼容旧文档 / CLI 里的名字；不再做 regex 硬门，直接走 judge 中位数。
def score_case_two_stage(case_dir: Path, run_dir: Path, judge_runs: int = 3) -> dict:
    return judge_median(case_dir, run_dir, runs=judge_runs)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python score_two_stage.py <case_dir> <run_dir> "
              "[--runs N] [--json out.json]")
        return 1

    case_dir = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])

    runs = 3
    output_json = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--runs" and i + 1 < len(sys.argv):
            runs = int(sys.argv[i + 1]); i += 2
        elif sys.argv[i] == "--json" and i + 1 < len(sys.argv):
            output_json = sys.argv[i + 1]; i += 2
        else:
            i += 1

    result = judge_median(case_dir, run_dir, runs=runs)
    print(f"\n=== {result['case_id']}  judge_median={result['overall_score']} "
          f"(std={result['judge_std']}, raw={result.get('judge_scores_raw')}) ===")

    if output_json:
        Path(output_json).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved: {output_json}")

    return 0 if result["overall_score"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
