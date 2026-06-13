"""
LLM-as-Judge evaluation scorer using Agent tool (no API key needed).

Spawns subagent to evaluate analysis quality across 5 dimensions.
Replaces keyword regex matching with semantic quality assessment.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List


JUDGE_DIMENSIONS = {
    "correctness": {
        "weight": 5.0,
        "criteria": [
            "结论是否与 ground truth 中的 finding 一致（方向、效应量级）",
            "关键数值是否在合理范围内（非精确匹配要求）",
            "是否存在与 ground truth 矛盾的结论"
        ]
    },
    "completeness": {
        "weight": 3.0,
        "criteria": [
            "是否覆盖 ground truth 中所有 required findings",
            "是否遗漏关键驱动因素",
            "负向结论（tested-but-rejected）是否明确报告"
        ]
    },
    "rigor": {
        "weight": 4.0,
        "criteria": [
            "方法选择是否适配数据特性（样本量、分布、时序性）",
            "是否执行交叉验证（多方法、sensitivity analysis）",
            "是否识别并处理混杂因素、数据泄漏风险",
            "统计推断的前提假设是否检查（正态性、独立性等）"
        ]
    },
    "clarity": {
        "weight": 2.0,
        "criteria": [
            "因果链条是否清晰（从数据证据到结论的推理路径）",
            "关键发现是否有量化支撑（效应量、CI、p-value）",
            "图表是否与结论呼应"
        ]
    },
    "anti_gaming": {
        "weight": 3.0,
        "criteria": [
            "是否存在关键词堆砌（高频重复特定术语而无实质内容）",
            "数值是否异常精确匹配预期（如恰好 33.0% 而非自然的 32.8%）",
            "结论之间是否存在逻辑矛盾（如同时声称 X 显著与 X 不显著）",
            "是否存在'形似神不似'的分析（提到方法名但未真正执行）"
        ]
    }
}


# Cap report length per judge prompt. 3000 chars (the old cap) truncated most
# reports before their conclusions — audit 2026-06-13 showed judges scoring
# only the data-overview section. 30k chars covers every report produced so far.
MAX_REPORT_CHARS = 30000


def spawn_judge_agent(
    dimension: str,
    agent_output: str,
    ground_truth: Dict[str, Any]
) -> Dict[str, Any]:
    """Spawn subagent to judge single dimension"""

    # Format ground truth context
    gt_context = f"Case ID: {ground_truth['case_id']}\nTarget: {ground_truth.get('target', 'N/A')}"
    if dimension in ["correctness", "completeness"]:
        gt_context += "\n\n预期发现:\n"
        for f in ground_truth.get("findings", []):
            gt_context += f"  - {f['id']}: {f.get('feature', 'N/A')} ({f['type']})\n"

    # Build judge prompt
    criteria_text = "\n".join(f"- {c}" for c in JUDGE_DIMENSIONS[dimension]["criteria"])

    prompt = f"""你是数据科学方法论评审员。评估以下分析在 **{dimension}** 维度的质量。

## 评估标准
{criteria_text}

## 参考标准
{gt_context}

## Agent 分析输出
{agent_output[:MAX_REPORT_CHARS]}

## 任务
评分 0-3：
- 0分：完全不满足或有致命缺陷
- 1分：部分满足但有重大遗漏
- 2分：基本满足标准
- 3分：完全满足且无明显瑕疵

输出 JSON：
{{
  "score": <0-3>,
  "rationale": "<150字内说明评分理由>",
  "evidence": ["<支撑评分的原文片段，最多2条>"],
  "defects": ["<发现的问题，若无则空数组>"]
}}

关键原则：
1. 区分"提到术语"vs"真正执行"
2. 数值异常精确匹配标记为可疑
3. 发现逻辑矛盾必须扣分
4. 关注核心推理链而非冗长形式"""

    # Spawn agent via claude CLI (pass prompt via stdin)
    result = subprocess.run(
        ["claude"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=180
    )

    if result.returncode != 0:
        raise RuntimeError(f"Judge agent failed: {result.stderr}")

    # Extract JSON from agent output
    output = result.stdout.strip()

    # Try multiple extraction methods
    json_text = None

    # Method 1: Look for ```json block
    if "```json" in output:
        json_text = output.split("```json")[1].split("```")[0].strip()
    # Method 2: Look for { ... } block
    elif "{" in output and "}" in output:
        start = output.index("{")
        end = output.rindex("}") + 1
        json_text = output[start:end]

    if not json_text:
        raise ValueError(f"No JSON found in agent output: {output[:500]}")

    # Try to parse, with fallback for common issues
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        # Try to fix common issues: trailing commas, unescaped quotes
        json_text = json_text.replace(",]", "]").replace(",}", "}")
        try:
            return json.loads(json_text)
        except:
            # Last resort: extract fields manually
            import re
            score_match = re.search(r'"score":\s*(\d+)', json_text)
            rationale_match = re.search(r'"rationale":\s*"([^"]+)"', json_text)

            if score_match:
                return {
                    "score": int(score_match.group(1)),
                    "rationale": rationale_match.group(1) if rationale_match else "Parse error",
                    "evidence": [],
                    "defects": []
                }
            else:
                raise ValueError(f"Failed to parse JSON: {e}\nText: {json_text[:300]}")


def score_case_with_agent_judge(
    case_dir: Path,
    run_dir: Path,
    dimensions: List[str] = None
) -> Dict[str, Any]:
    """Score case using agent-spawned LLM judges"""

    if dimensions is None:
        dimensions = list(JUDGE_DIMENSIONS.keys())

    # Load ground truth (canonical single file per case, post-audit 2026-06-13)
    gt_path = case_dir / "ground_truth.json"
    gt = json.loads(gt_path.read_text())

    # Load agent report
    report_path = run_dir / "final_report.md"
    if not report_path.exists():
        raise FileNotFoundError(f"Agent report not found: {report_path}")
    agent_output = report_path.read_text()

    # Score each dimension with spawned agent
    judge_scores = {}
    total_weighted = 0.0
    total_weight = 0.0

    print(f"Scoring {gt['case_id']} with agent judges...")
    for dim in dimensions:
        print(f"  Spawning judge for {dim}...")
        result = spawn_judge_agent(dim, agent_output, gt)
        judge_scores[dim] = result
        total_weighted += result["score"] * JUDGE_DIMENSIONS[dim]["weight"]
        total_weight += JUDGE_DIMENSIONS[dim]["weight"]

    # Aggregate
    overall_score = (total_weighted / (total_weight * 3)) * 100

    all_defects = []
    for dim, result in judge_scores.items():
        for defect in result.get("defects", []):
            all_defects.append({"dimension": dim, "defect": defect})

    return {
        "case_id": gt["case_id"],
        "judge_scores": judge_scores,
        "overall_score": round(overall_score, 1),
        "defects": all_defects,
        "scorer": "agent-judge"
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python judge_score.py <case_dir> <run_dir> [--json output.json]")
        sys.exit(1)

    case_dir = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    output_json = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--json" else None

    result = score_case_with_agent_judge(case_dir, run_dir)

    print(f"\n=== {result['case_id']} judge_score={result['overall_score']} ===")
    for dim, score_data in result["judge_scores"].items():
        score = score_data["score"]
        print(f"  [{dim:15s}] {score}/3  {score_data['rationale'][:60]}...")

    if result["defects"]:
        print(f"\nDefects: {len(result['defects'])}")
        for d in result["defects"][:3]:
            print(f"  - [{d['dimension']}] {d['defect'][:80]}...")

    if output_json:
        Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\nResult: {output_json}")
