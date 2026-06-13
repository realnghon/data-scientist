#!/usr/bin/env python3
"""L2 concurrent eval runner: headless contestant agents + independent judges.

设计目标（2026-06-13 审计后引入）：
1. **并发**：每个 case 一个 headless `claude -p` 选手进程，并行跑 N 个 case
2. **裁判独立**：选手完成后自动起 judge（judge_score.py，同样 headless）
3. **上下文隔离**：主会话只需要读本脚本最后输出的 summary（或 summary.json），
   不接触选手的完整对话/报告——选手产物全部落在 .runs/l2/<run-id>/ 里备查

Usage::

    python evals/harness/run_l2.py                       # 全部 9 个 case
    python evals/harness/run_l2.py case-01 case-04       # 按名字过滤
    python evals/harness/run_l2.py --jobs 3 --skip-judge # 只跑选手不打分

输出：evals/.runs/l2/<batch-ts>/summary.json + 终端摘要表。
主流程只消费 judge 给出的分数与 defects，不要读选手的 final_report。
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = EVALS_DIR.parent
SKILL_MD = REPO_ROOT / "plugins/data-scientist/skills/analysis-workflow/SKILL.md"
RUNS_DIR = EVALS_DIR / ".runs" / "l2"

CONTESTANT_TIMEOUT = 1800  # 30 min per case
JUDGE_TIMEOUT = 900


def build_contestant_prompt(case_dir: Path, run_dir: Path) -> str:
    """Spawn prompt per run_l2.md 模板：选手只拿 SKILL.md + 用户请求 + 数据路径。"""
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    user_prompt = (case_dir / "prompt.txt").read_text(encoding="utf-8")
    # 数据文件名替换为绝对路径（prompt 里写的是文件名，GT 里可能是相对路径）
    for ds in gt.get("datasets", []):
        abs_path = (case_dir / ds).resolve()
        name = Path(ds).name
        if str(abs_path) not in user_prompt:
            user_prompt = user_prompt.replace(name, str(abs_path))

    return f"""你是一个安装了 data-scientist 插件的数据分析 agent。

技能文件（必须先读取并遵循）：
{SKILL_MD}
技能引用的 references/ 与 scripts/ 在同一目录下，按 SKILL.md 指引按需加载。

用户请求：
{user_prompt}

硬性约定（评测 harness 要求，不要省略）：
1. 所有产物写入目录：{run_dir}
2. 结构化产物用 SKILL.md 规定的名字保存为独立 JSON 文件：
   data_manifest.json / readiness_report.json / analysis_plan.json /
   evidence_matrix.json / critique.json（按你路由判定实际需要的子集）
3. 最终报告保存为 final_report.md；图表保存为 png 文件
4. 以 auto 模式运行：不要向用户提问，按推荐选项决策并记录在报告的
   Human Decision Log 中
"""


def run_contestant(case_dir: Path, run_dir: Path) -> dict:
    """Run one headless contestant agent; return status dict (no transcript)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_contestant_prompt(case_dir, run_dir)
    t0 = time.time()
    try:
        proc = subprocess.run(
            [
                "claude", "-p",
                "--permission-mode", "bypassPermissions",
                "--add-dir", str(REPO_ROOT),
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CONTESTANT_TIMEOUT,
            cwd=run_dir,
        )
        status = "ok" if proc.returncode == 0 else f"exit={proc.returncode}"
        # transcript 留档但绝不进主会话上下文
        (run_dir / "_contestant_stdout.log").write_text(proc.stdout, encoding="utf-8")
        if proc.stderr.strip():
            (run_dir / "_contestant_stderr.log").write_text(proc.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired:
        status = "timeout"
    return {
        "case": case_dir.name,
        "status": status,
        "elapsed_s": round(time.time() - t0, 1),
        "has_report": (run_dir / "final_report.md").exists(),
    }


def run_judge(case_dir: Path, run_dir: Path) -> dict:
    """Score with regex (free) + agent judge (semantic). Returns compact summary."""
    out: dict = {"case": case_dir.name}

    # 1) deterministic regex score
    score_json = run_dir / "score.json"
    subprocess.run(
        [sys.executable, str(EVALS_DIR / "harness" / "score_case.py"),
         str(case_dir), str(run_dir), "--json", str(score_json)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if score_json.exists():
        regex = json.loads(score_json.read_text(encoding="utf-8"))
        out["regex_score"] = regex["score"]
        out["regex_fails"] = [c["id"] for c in regex["checks"] if not c["passed"]]

    # 2) agent judge (semantic, headless)
    try:
        sys.path.insert(0, str(EVALS_DIR / "harness"))
        from judge_score import score_case_with_agent_judge
        judge = score_case_with_agent_judge(case_dir, run_dir)
        (run_dir / "judge.json").write_text(
            json.dumps(judge, ensure_ascii=False, indent=2), encoding="utf-8")
        out["judge_score"] = judge["overall_score"]
        out["judge_dims"] = {d: s["score"] for d, s in judge["judge_scores"].items()}
        out["defects"] = [f"[{d['dimension']}] {d['defect']}" for d in judge["defects"]]
    except Exception as exc:  # judge 失败不毁掉整个 batch
        out["judge_error"] = str(exc)[:200]
    return out


def run_one(case_dir: Path, batch_dir: Path, skip_judge: bool) -> dict:
    run_dir = batch_dir / case_dir.name
    result = run_contestant(case_dir, run_dir)
    if not skip_judge and result["has_report"]:
        result.update(run_judge(case_dir, run_dir))
    elif not result["has_report"]:
        result["judge_error"] = "no final_report.md produced"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("filters", nargs="*", help="case 名过滤（子串匹配）")
    ap.add_argument("--jobs", type=int, default=3, help="并发选手数（默认 3）")
    ap.add_argument("--skip-judge", action="store_true", help="只跑选手不打分")
    args = ap.parse_args()

    cases = [d for d in sorted((EVALS_DIR / "cases").iterdir())
             if d.is_dir() and (d / "ground_truth.json").exists()]
    if args.filters:
        cases = [c for c in cases if any(f in c.name for f in args.filters)]
    if not cases:
        print("no cases matched", file=sys.stderr)
        return 2

    batch_dir = RUNS_DIR / datetime.now().strftime("%Y%m%d-%H%M")
    batch_dir.mkdir(parents=True, exist_ok=True)
    print(f"batch dir: {batch_dir}\ncases: {[c.name for c in cases]}\n")

    results: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_one, c, batch_dir, args.skip_judge): c for c in cases}
        for fut in cf.as_completed(futures):
            r = fut.result()
            results.append(r)
            print(f"  done {r['case']:<36} {r['status']:<8} "
                  f"regex={r.get('regex_score', '-')} judge={r.get('judge_score', '-')} "
                  f"({r['elapsed_s']}s)")

    results.sort(key=lambda r: r["case"])
    summary_path = batch_dir / "summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print("\n================ L2 SUMMARY ================")
    for r in results:
        print(f"  {r['case']:<36} regex={r.get('regex_score', '-'):<6} "
              f"judge={r.get('judge_score', '-')}")
        for d in r.get("defects", [])[:3]:
            print(f"      defect: {d[:100]}")
        if r.get("judge_error"):
            print(f"      judge_error: {r['judge_error'][:100]}")
    print(f"\nsummary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
