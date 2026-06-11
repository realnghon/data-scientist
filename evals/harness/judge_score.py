"""
LLM-as-Judge evaluation scorer.

Replaces keyword regex matching with multi-dimensional quality assessment by Claude.
Addresses "teaching to the test" problem where agents game regex patterns.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import anthropic
import os

# Judge evaluation dimensions
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

JUDGE_PROMPT_TEMPLATE = """你是数据科学方法论的严格评审员。评估以下分析报告在 **{dimension}** 维度的质量。

## 评估标准
{criteria}

## 参考标准（Ground Truth）
{ground_truth_context}

## Agent 分析输出
{agent_output}

## 评分规则
- 0分：完全不满足标准或存在致命缺陷
- 1分：部分满足但有重大遗漏或错误
- 2分：基本满足标准
- 3分：完全满足标准且无明显瑕疵

输出 JSON 格式：
{{
  "score": <0-3>,
  "rationale": "<150字内说明评分理由>",
  "evidence_quotes": ["<支撑评分的报告原文片段，最多3条>"],
  "defects": ["<发现的问题，若无则为空数组>"]
}}

关键原则：
1. 区分"提到关键词"与"真正执行分析" - 仅列举术语而无证据链，扣分
2. 数值的自然性 - 异常精确匹配（如33.0%而非32.8%）标记为可疑
3. 逻辑一致性 - 交叉检查报告不同部分，发现矛盾必须扣分
4. 不被冗长形式化迷惑 - 关注核心推理链条是否成立
"""


class LLMJudge:
    def __init__(self, model: str = "claude-opus-4", cache_dir: str = ".runs/judge_cache"):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _format_ground_truth(self, gt: Dict[str, Any], dimension: str) -> str:
        """Format ground truth context for judge prompt"""
        lines = [f"Case ID: {gt['case_id']}", f"Target: {gt.get('target', 'N/A')}"]

        if dimension in ["correctness", "completeness"]:
            lines.append("\n预期发现（Findings）:")
            for f in gt.get("findings", []):
                lines.append(f"  - {f['id']}: {f.get('feature', 'N/A')} ({f['type']})")

        if dimension == "rigor" and "routing" in gt:
            lines.append(f"\n路由要求: {gt['routing'].get('expected_route', 'N/A')}")
            lines.append(f"必须产出: {', '.join(gt['routing'].get('must_produce_artifacts', []))}")

        return "\n".join(lines)

    def score_dimension(
        self,
        dimension: str,
        agent_output: str,
        ground_truth: Dict[str, Any],
        case_id: str
    ) -> Dict[str, Any]:
        """Score single dimension with LLM judge (cached)"""
        # Cache key based on content hash
        content_hash = hashlib.sha256(
            f"{case_id}:{dimension}:{agent_output}".encode()
        ).hexdigest()[:12]
        cache_path = self.cache_dir / f"{content_hash}.json"

        if cache_path.exists():
            return json.loads(cache_path.read_text())

        # Format prompt
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            dimension=dimension,
            criteria="\n".join(f"- {c}" for c in JUDGE_DIMENSIONS[dimension]["criteria"]),
            ground_truth_context=self._format_ground_truth(ground_truth, dimension),
            agent_output=agent_output[:8000]  # Truncate to avoid token limit
        )

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.0  # Deterministic scoring
        )

        # Parse JSON response
        result = json.loads(response.content[0].text)

        # Cache result
        cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def score_case(
        self,
        case_dir: Path,
        run_dir: Path,
        dimensions: List[str] = None
    ) -> Dict[str, Any]:
        """Score complete case using LLM judge"""
        if dimensions is None:
            dimensions = list(JUDGE_DIMENSIONS.keys())

        # Load ground truth
        gt_path = case_dir / "ground_truth.json"
        if not gt_path.exists():
            raise FileNotFoundError(f"Ground truth not found: {gt_path}")
        gt = json.loads(gt_path.read_text())

        # Load agent report
        report_path = run_dir / "final_report.md"
        if not report_path.exists():
            raise FileNotFoundError(f"Agent report not found: {report_path}")
        agent_output = report_path.read_text()

        # Score each dimension
        judge_scores = {}
        total_weighted = 0.0
        total_weight = 0.0

        for dim in dimensions:
            result = self.score_dimension(dim, agent_output, gt, gt["case_id"])
            judge_scores[dim] = result
            total_weighted += result["score"] * JUDGE_DIMENSIONS[dim]["weight"]
            total_weight += JUDGE_DIMENSIONS[dim]["weight"]

        # Aggregate score (0-100 scale)
        overall_score = (total_weighted / (total_weight * 3)) * 100  # Normalize to 0-100

        # Collect all defects
        all_defects = []
        for dim, result in judge_scores.items():
            for defect in result.get("defects", []):
                all_defects.append({"dimension": dim, "defect": defect})

        return {
            "case_id": gt["case_id"],
            "judge_scores": judge_scores,
            "overall_score": round(overall_score, 1),
            "defects": all_defects,
            "model": self.model
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python judge_score.py <case_dir> <run_dir> [--json output.json]")
        sys.exit(1)

    case_dir = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    output_json = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--json" else None

    judge = LLMJudge()
    result = judge.score_case(case_dir, run_dir)

    print(f"=== {result['case_id']} judge_score={result['overall_score']} ===")
    for dim, score_data in result["judge_scores"].items():
        score = score_data["score"]
        print(f"  [{dim:15s}] {score}/3  {score_data['rationale'][:60]}...")

    if result["defects"]:
        print(f"\nDefects found: {len(result['defects'])}")
        for d in result["defects"][:5]:
            print(f"  - [{d['dimension']}] {d['defect'][:80]}...")

    if output_json:
        Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\nFull result written to {output_json}")
