#!/usr/bin/env python3
"""
两阶段评分器：Regex 初筛 + Judge 主评

Stage 1: Regex 快速检查 required findings 覆盖率
  - Coverage < 50% → 直接失败
  - Coverage ≥ 50% → 进入 Stage 2

Stage 2: Judge 详细评分（运行 3 次取中位数）
  - 5 维度评分：correctness / completeness / rigor / clarity / anti_gaming
  - 消除 LLM 非确定性影响
"""
import json
import sys
import re
from pathlib import Path
import numpy as np

# 导入现有评分器
sys.path.insert(0, str(Path(__file__).parent))
from judge_score import score_case_with_agent_judge


def check_regex_findings(case_dir: Path, run_dir: Path):
    """
    检查 findings 的 regex 匹配（简化版，只检查匹配情况）

    Returns:
        matched: {finding_id: bool} 字典
    """
    # 加载 ground truth
    gt = json.loads((case_dir / "ground_truth.json").read_text())

    # 收集所有文本内容
    text_content = ""
    for text_file in run_dir.glob("*.md"):
        text_content += text_file.read_text() + "\n\n"
    for json_file in run_dir.glob("*.json"):
        text_content += json_file.read_text() + "\n\n"

    # 检查每个 finding
    matched = {}
    for finding in gt.get("findings", []):
        finding_id = finding["id"]
        regex_pattern = finding.get("evidence_regex", "")

        # 处理 NOT: 前缀（negative assertion）
        if regex_pattern.startswith("NOT:"):
            pattern = regex_pattern[4:].strip()
            # NOT 模式：不匹配才算通过
            matched[finding_id] = not bool(re.search(pattern, text_content, re.IGNORECASE | re.DOTALL))
        else:
            # 正常模式：匹配才算通过
            matched[finding_id] = bool(re.search(regex_pattern, text_content, re.IGNORECASE | re.DOTALL))

    return matched


def score_case_two_stage(case_dir: Path, run_dir: Path, judge_runs: int = 3):
    """
    两阶段评分：Regex 初筛 + Judge 主评

    Args:
        case_dir: Case 目录（包含 ground_truth.json）
        run_dir: 运行目录（包含 final_report.md）
        judge_runs: Judge 运行次数（取中位数消除非确定性）

    Returns:
        评分结果字典
    """
    # 加载 ground truth
    gt_path = case_dir / "ground_truth.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {gt_path}")

    gt = json.loads(gt_path.read_text())
    case_id = gt["case_id"]

    print(f"\n{'='*60}")
    print(f"Scoring: {case_id}")
    print(f"{'='*60}\n")

    # ===== Stage 1: Regex 初筛 =====
    print("Stage 1: Regex 初筛（检查 required findings 覆盖率）")
    print("-" * 60)

    try:
        matched = check_regex_findings(case_dir, run_dir)
    except Exception as e:
        print(f"❌ Regex 评分失败: {e}")
        return {
            "case_id": case_id,
            "overall_score": 0,
            "stage": "regex_failed",
            "error": str(e)
        }

    # 计算 required findings 覆盖率
    all_findings = gt.get("findings", [])
    required_findings = [f for f in all_findings if f.get("tier") == "required"]

    if not required_findings:
        # 如果没有标注 tier，fallback 到所有 findings（兼容旧 GT）
        print("⚠️  Ground truth 未标注 tier，使用所有 findings 作为 required")
        required_findings = all_findings

    matched_findings = [f for f in required_findings
                       if matched.get(f["id"], False)]

    required_count = len(required_findings)
    matched_count = len(matched_findings)
    coverage = matched_count / required_count if required_count > 0 else 0

    print(f"\nRequired findings: {required_count}")
    print(f"Matched: {matched_count}")
    print(f"Coverage: {coverage:.1%}")

    # 显示未匹配的 required findings
    if matched_count < required_count:
        print(f"\n未匹配的 required findings:")
        for f in required_findings:
            if f["id"] not in [mf["id"] for mf in matched_findings]:
                print(f"  ❌ {f['id']} (weight={f.get('weight', 'N/A')})")

    # Coverage < 50% 直接失败
    if coverage < 0.5:
        print(f"\n❌ 初筛失败：Required coverage {coverage:.1%} < 50%")
        print("   不进入 Judge 评分阶段")

        return {
            "case_id": case_id,
            "overall_score": 0,
            "stage": "regex_initial_screen",
            "reason": f"Required findings coverage {coverage:.1%} < 50%",
            "regex_result": {
                "coverage": coverage,
                "required_count": required_count,
                "matched_count": matched_count,
                "unmatched": [f["id"] for f in required_findings
                             if f["id"] not in [mf["id"] for mf in matched_findings]]
            }
        }

    print(f"\n✅ 初筛通过：Coverage {coverage:.1%} ≥ 50%")
    print(f"   进入 Judge 评分阶段...\n")

    # ===== Stage 2: Judge 评分（运行 N 次取中位数）=====
    print("Stage 2: Judge 评分（运行 3 次取中位数消除非确定性）")
    print("-" * 60)

    judge_results = []
    judge_details = []

    for run_idx in range(judge_runs):
        print(f"\nJudge Run {run_idx + 1}/{judge_runs}:")
        try:
            result = score_case_with_agent_judge(case_dir, run_dir)
            score = result["overall_score"]
            judge_results.append(score)
            judge_details.append(result)
            print(f"  Score: {score:.1f}")
        except Exception as e:
            print(f"  ❌ Judge run {run_idx + 1} failed: {e}")
            # 失败的 run 不计入结果
            continue

    if not judge_results:
        print(f"\n❌ 所有 Judge runs 都失败")
        return {
            "case_id": case_id,
            "overall_score": 0,
            "stage": "judge_all_failed",
            "regex_coverage": coverage
        }

    # 取中位数
    median_score = float(np.median(judge_results))
    std_score = float(np.std(judge_results)) if len(judge_results) > 1 else 0.0

    print(f"\n{'='*60}")
    print(f"最终结果:")
    print(f"  Regex coverage: {coverage:.1%}")
    print(f"  Judge scores: {judge_results}")
    print(f"  Median: {median_score:.1f}")
    print(f"  Std: {std_score:.1f}")
    print(f"{'='*60}\n")

    # 选择中位数对应的详细结果
    median_idx = sorted(range(len(judge_results)),
                       key=lambda i: abs(judge_results[i] - median_score))[0]
    median_detail = judge_details[median_idx]

    return {
        "case_id": case_id,
        "overall_score": median_score,
        "judge_std": std_score,
        "judge_scores_raw": judge_results,
        "regex_coverage": coverage,
        "stage": "judge_final",
        "judge_scores": median_detail.get("judge_scores", {}),
        "defects": median_detail.get("defects", [])
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python score_two_stage.py <case_dir> <run_dir> [--runs N] [--json output.json]")
        sys.exit(1)

    case_dir = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])

    # 解析可选参数
    judge_runs = 3
    output_json = None

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--runs" and i + 1 < len(sys.argv):
            judge_runs = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--json" and i + 1 < len(sys.argv):
            output_json = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    result = score_case_two_stage(case_dir, run_dir, judge_runs=judge_runs)

    # 保存结果
    if output_json:
        Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Result saved to: {output_json}")

    sys.exit(0 if result["overall_score"] > 0 else 1)
