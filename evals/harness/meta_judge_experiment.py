"""
Meta-judge: Compare regex vs LLM scoring and decide if regex can be retired.

Experiment design:
1. Run both regex scorer (existing) and LLM judge on same cases
2. Meta-judge reviews both scores + agent output, decides:
   - Which scorer is more accurate
   - Whether regex adds unique value
   - If regex can be safely retired

Output: Recommendation with evidence.
"""
import json
from pathlib import Path
from typing import Dict, Any
import subprocess
import sys

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from judge_score import LLMJudge

import anthropic
import os


META_JUDGE_PROMPT = """你是评测系统的元评审员。你需要评估两种评分方法的有效性：

## 评分方法 A：正则匹配（Regex）
- 通过关键词模式匹配来评分（如"转化率.*提升.*33"）
- 优点：确定性、零成本、快速
- 缺点：可能被"关键词游戏"（agent 拼凑词汇而非真实分析）

## 评分方法 B：LLM Judge
- 由 Claude 评估分析质量的 5 个维度（correctness/rigor/clarity/anti_gaming等）
- 优点：评估真实逻辑质量、识别关键词堆砌
- 缺点：有成本（~$0.15/case）、可能不稳定

## 案例信息
**Case ID**: {case_id}
**Regex 评分**: {regex_score}/100
  - 检查项: {regex_checks}

**LLM Judge 评分**: {judge_score}/100
  - 维度分数: {judge_dims}
  - 发现的缺陷: {judge_defects}

## Agent 分析输出（摘要）
{agent_summary}

## 你的任务
基于以上信息，回答以下问题（输出 JSON）：

{{
  "regex_accuracy": <0-10>,  // 正则评分的准确性（10=完全准确，0=完全误判）
  "judge_accuracy": <0-10>,  // LLM judge 评分的准确性
  "unique_value_of_regex": <bool>,  // 正则是否提供了 judge 无法提供的独特价值
  "gaming_detected": <bool>,  // 是否检测到"关键词游戏"（agent 为匹配正则而输出特定词汇）
  "recommendation": <"keep_regex" | "retire_regex" | "uncertain">,
  "rationale": "<200字内说明推荐理由>",
  "evidence": ["<支撑判断的具体证据，从 agent 输出或评分差异中提取>"]
}}

评判原则：
1. **Gaming 证据**：如果 agent 输出包含异常精确的数字（如恰好33.0%）、重复关键词（如"tradeoff"出现>3次）、或逻辑矛盾但仍满足正则，则 gaming_detected=true
2. **Regex 独特价值**：仅当正则捕获了 judge 漏检的真实问题，才认为有独特价值
3. **推荐决策**：
   - regex_accuracy < judge_accuracy 且 gaming_detected=true → retire_regex
   - regex_accuracy ≈ judge_accuracy 但 unique_value_of_regex=false → retire_regex
   - regex 明显更准确或提供独特价值 → keep_regex
   - 证据不足 → uncertain
"""


class MetaJudge:
    def __init__(self, model: str = "claude-opus-4"):
        self.model = model
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.llm_judge = LLMJudge(model=model)

    def run_regex_scorer(self, case_dir: Path, run_dir: Path) -> Dict[str, Any]:
        """Run existing regex scorer"""
        result = subprocess.run(
            [
                sys.executable,
                "evals/harness/score_case.py",
                str(case_dir),
                str(run_dir),
                "--json",
                "/tmp/regex_score.json"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Regex scorer failed: {result.stderr}")

        return json.loads(Path("/tmp/regex_score.json").read_text())

    def compare_and_judge(
        self,
        case_dir: Path,
        run_dir: Path
    ) -> Dict[str, Any]:
        """Run both scorers and meta-judge to compare"""

        # 1. Run regex scorer
        print(f"Running regex scorer on {case_dir.name}...")
        regex_result = self.run_regex_scorer(case_dir, run_dir)
        regex_score = regex_result.get("score", 0)
        regex_checks = [
            f"{c['check_id']} ({c['status']})"
            for c in regex_result.get("checks", [])
        ]

        # 2. Run LLM judge
        print(f"Running LLM judge on {case_dir.name}...")
        judge_result = self.llm_judge.score_case(case_dir, run_dir)
        judge_score = judge_result["overall_score"]
        judge_dims = {
            dim: f"{data['score']}/3"
            for dim, data in judge_result["judge_scores"].items()
        }
        judge_defects = [
            f"{d['dimension']}: {d['defect']}"
            for d in judge_result.get("defects", [])
        ]

        # 3. Load agent output summary
        report_path = run_dir / "final_report.md"
        agent_text = report_path.read_text()
        agent_summary = agent_text[:3000]  # First 3k chars

        # 4. Meta-judge comparison
        print(f"Running meta-judge comparison...")
        prompt = META_JUDGE_PROMPT.format(
            case_id=judge_result["case_id"],
            regex_score=regex_score,
            regex_checks="\n    ".join(regex_checks[:10]),
            judge_score=judge_score,
            judge_dims=json.dumps(judge_dims, indent=4, ensure_ascii=False),
            judge_defects="\n    ".join(judge_defects[:5]) if judge_defects else "无",
            agent_summary=agent_summary
        )

        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.0
        )

        meta_result = json.loads(response.content[0].text)

        return {
            "case_id": judge_result["case_id"],
            "regex_score": regex_score,
            "judge_score": judge_score,
            "score_delta": abs(regex_score - judge_score),
            "meta_judgment": meta_result,
            "raw_results": {
                "regex": regex_result,
                "judge": judge_result
            }
        }


def run_experiment(case_dirs: list, run_dirs: list, output_dir: Path):
    """Run meta-judge experiment on multiple cases"""
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_judge = MetaJudge()

    results = []
    for case_dir, run_dir in zip(case_dirs, run_dirs):
        print(f"\n{'='*60}")
        print(f"Comparing scorers on {case_dir.name}")
        print('='*60)

        result = meta_judge.compare_and_judge(case_dir, run_dir)
        results.append(result)

        # Save individual result
        output_file = output_dir / f"{result['case_id']}_comparison.json"
        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

        print(f"\nResult:")
        print(f"  Regex: {result['regex_score']}")
        print(f"  Judge: {result['judge_score']}")
        print(f"  Delta: {result['score_delta']}")
        print(f"  Meta recommendation: {result['meta_judgment']['recommendation']}")
        print(f"  Rationale: {result['meta_judgment']['rationale'][:100]}...")

    # Aggregate summary
    summary = {
        "total_cases": len(results),
        "retire_regex_count": sum(1 for r in results if r["meta_judgment"]["recommendation"] == "retire_regex"),
        "keep_regex_count": sum(1 for r in results if r["meta_judgment"]["recommendation"] == "keep_regex"),
        "uncertain_count": sum(1 for r in results if r["meta_judgment"]["recommendation"] == "uncertain"),
        "gaming_detected_count": sum(1 for r in results if r["meta_judgment"]["gaming_detected"]),
        "avg_regex_accuracy": sum(r["meta_judgment"]["regex_accuracy"] for r in results) / len(results),
        "avg_judge_accuracy": sum(r["meta_judgment"]["judge_accuracy"] for r in results) / len(results),
        "cases": results
    }

    summary_file = output_dir / "experiment_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"\n{'='*60}")
    print("EXPERIMENT SUMMARY")
    print('='*60)
    print(f"Total cases: {summary['total_cases']}")
    print(f"Recommendation: Retire regex: {summary['retire_regex_count']}, Keep: {summary['keep_regex_count']}, Uncertain: {summary['uncertain_count']}")
    print(f"Gaming detected: {summary['gaming_detected_count']}/{summary['total_cases']}")
    print(f"Avg accuracy: Regex={summary['avg_regex_accuracy']:.1f}/10, Judge={summary['avg_judge_accuracy']:.1f}/10")
    print(f"\nFull results saved to {output_dir}/")

    # Final recommendation
    if summary['retire_regex_count'] >= summary['total_cases'] * 0.67:
        print(f"\n✅ RECOMMENDATION: RETIRE REGEX")
        print(f"   Evidence: {summary['retire_regex_count']}/{summary['total_cases']} cases support retirement")
        print(f"   LLM judge is more accurate (avg {summary['avg_judge_accuracy']:.1f} vs {summary['avg_regex_accuracy']:.1f})")
    elif summary['keep_regex_count'] >= summary['total_cases'] * 0.5:
        print(f"\n⚠️  RECOMMENDATION: KEEP REGEX (for now)")
        print(f"   Evidence: Regex still provides unique value in {summary['keep_regex_count']} cases")
    else:
        print(f"\n🤔 RECOMMENDATION: UNCERTAIN - need more data")
        print(f"   Run experiment on more diverse cases")

    return summary


if __name__ == "__main__":
    # Default: run on 3 saturated cases (case-01/02/09 v2)
    case_dirs = [
        Path("evals/cases/case-01-manufacturing-yield"),
        Path("evals/cases/case-02-ab-test"),
        Path("evals/cases/case-09-wafer-rca")
    ]
    run_dirs = [
        Path("evals/.runs/l2/case-01-manufacturing-v2"),
        Path("evals/.runs/l2/case-02-ab-v2"),
        Path("evals/.runs/l2/case-09-v2-final")
    ]

    output_dir = Path("evals/.runs/meta_judge_experiment")
    summary = run_experiment(case_dirs, run_dirs, output_dir)
