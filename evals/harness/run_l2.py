#!/usr/bin/env python3
"""L2 concurrent eval runner: real-plugin contestants + independent judges.

设计目标（2026-06-14 重做，修「秤」）：
1. **真实插件加载**：选手用 ``claude -p --plugin-dir plugins/data-scientist`` 真实加载
   插件，prompt 只含用户请求 + 数据路径（不再把 SKILL.md 路径塞进 prompt）。这样评测的
   是 skill 在真实环境里**会不会被自主触发、被遵循**——正是飞轮要测的对象。
2. **多次采样降方差**：每个 case 跑 ``k`` 次（默认 3），把模型的随机行为方差从单点噪声
   变成可观测的分布（mean ± std），而不是把一次抽样当成 skill 改动的因果效应。
3. **双线分数**：每份产物用 ``score_case.py`` 算确定性的 ``process_score``（流程遵循度，
   零方差）和 regex ``outcome``；judge（``judge_score.py``）给语义 ``outcome_score``（主信号）。
4. **上下文隔离**：主会话只读 summary.json 的分布与 defects，不接触选手 transcript。

Usage::

    python evals/harness/run_l2.py                       # 全部 case，每个跑 k=3 次
    python evals/harness/run_l2.py case-a --k 5          # 过滤 + 加大采样
    python evals/harness/run_l2.py --jobs 3 --skip-judge # 只跑选手不打分

输出：evals/.runs/l2/<batch-ts>/summary.json + 终端摘要表。
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
EVALS_DIR = HARNESS_DIR.parent
REPO_ROOT = EVALS_DIR.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "data-scientist"
RUNS_DIR = EVALS_DIR / ".runs" / "l2"

# 复用同目录评分器（确定性双线 + 语义 judge）
sys.path.insert(0, str(HARNESS_DIR))
from score_case import score_case as regex_score_case  # noqa: E402
from judge_score import score_case_with_agent_judge  # noqa: E402

CONTESTANT_TIMEOUT = 2700  # 45 min per rep — case-a comprehensive 用满 ~29min，30min 太紧
DEFAULT_K = 3


def build_contestant_prompt(case_dir: Path, run_dir: Path) -> str:
    """选手 prompt = 真实用户请求 + 数据绝对路径 + 最小交付约定。

    skill 通过 ``--plugin-dir`` 真实加载，**不再**把 SKILL.md 路径写进 prompt——
    刻意不列举具体中间产物名（data_manifest 等），让 skill 自己驱动选手产出并命名；
    若 skill 没被触发/遵循，选手就不会产出这些产物，process_score 自然变低（真实信号）。
    仅保留 final_report.md + png 两个 harness 抓取必需的命名约定。
    """
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    user_prompt = (case_dir / "prompt.txt").read_text(encoding="utf-8")
    # prompt 里写的是文件名，替换为绝对路径，避免选手在 run_dir 里找不到数据
    for ds in gt.get("datasets", []):
        abs_path = (case_dir / ds).resolve()
        name = Path(ds).name
        if str(abs_path) not in user_prompt:
            user_prompt = user_prompt.replace(name, str(abs_path))

    return f"""{user_prompt}

——————
（交付要求 · 评测 harness，非分析内容）：
1. 所有产物写入此目录：{run_dir}
2. 最终报告存为 `final_report.md`；图表存为 `.png` 文件。
3. 分析过程中产生的结构化中间产物，各自存为独立 `.json` 文件（用语义化文件名）。
4. 自主决策、不要向我提问；把关键决策与取舍记录在报告里。
"""


def run_contestant(case_dir: Path, run_dir: Path) -> dict:
    """Run one headless contestant rep with the plugin really loaded."""
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_contestant_prompt(case_dir, run_dir)
    t0 = time.time()
    status = "ok"
    try:
        proc = subprocess.run(
            [
                "claude", "-p",
                "--permission-mode", "bypassPermissions",
                "--add-dir", str(REPO_ROOT),
                "--plugin-dir", str(PLUGIN_DIR),
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
        "status": status,
        "elapsed_s": round(time.time() - t0, 1),
        "has_report": (run_dir / "final_report.md").exists(),
    }


def run_judge(case_dir: Path, run_dir: Path) -> dict:
    """Score one rep: deterministic two-line (regex) + semantic judge."""
    out: dict = {}

    # 1) deterministic two-line score (process + regex-outcome)
    rg = regex_score_case(case_dir, run_dir)
    (run_dir / "score.json").write_text(
        json.dumps(rg, ensure_ascii=False, indent=2), encoding="utf-8")
    out["process_score"] = rg["process_score"]
    out["outcome_regex"] = rg["outcome_score"]
    out["regex_fails"] = [c["id"] for c in rg["checks"] if not c["passed"]]

    # 2) semantic agent judge (single per rep; k reps give the spread)
    try:
        j = score_case_with_agent_judge(case_dir, run_dir)
        (run_dir / "judge.json").write_text(
            json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        out["judge_score"] = j["overall_score"]
        out["judge_dims"] = {d: s["score"] for d, s in j["judge_scores"].items()}
        out["defects"] = [f"[{d['dimension']}] {d['defect']}" for d in j["defects"]]
    except Exception as exc:  # judge 失败不毁掉该 rep
        out["judge_error"] = str(exc)[:200]
    return out


def _dist(values: list) -> dict:
    """Mean/std/values over the non-None entries; None-safe for skipped reps."""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"mean": None, "std": None, "values": []}
    return {
        "mean": round(statistics.fmean(vals), 1),
        "std": round(statistics.pstdev(vals), 1) if len(vals) > 1 else 0.0,
        "values": [round(v, 1) for v in vals],
    }


def aggregate_case(case_name: str, reps: list, k: int) -> dict:
    """Fold k reps into process / outcome distributions for the summary."""
    ok = [r for r in reps if r.get("has_report")]
    agg = {
        "case": case_name,
        "k": k,
        "n_ok": len(ok),
        "statuses": [r.get("status") for r in reps],
        "elapsed_s": round(sum(r.get("elapsed_s", 0) for r in reps), 1),
        # process_score: 确定性流程遵循度，std 应≈0；std 大 = 选手时走时不走流程（真实信号）
        "process_score": _dist([r.get("process_score") for r in ok]),
        # outcome_score: judge 语义主信号
        "outcome_score": _dist([r.get("judge_score") for r in ok]),
        # outcome_regex: 确定性结论命中，作辅助参考
        "outcome_regex": _dist([r.get("outcome_regex") for r in ok]),
    }
    defects: list = []
    for r in ok:
        defects.extend(r.get("defects", []))
    agg["defects"] = defects[:5]
    for r in ok:
        if r.get("judge_dims"):
            agg["judge_dims"] = r["judge_dims"]
            break
    errs = [r["judge_error"] for r in reps if r.get("judge_error")]
    if errs:
        agg["judge_errors"] = errs[:3]
    return agg


def run_one(case_dir: Path, batch_dir: Path, skip_judge: bool, k: int) -> dict:
    """Run a case k times (k independent products) and aggregate distributions."""
    reps: list = []
    for r in range(k):
        rep_dir = batch_dir / case_dir.name / f"rep{r}"
        rep = run_contestant(case_dir, rep_dir)
        rep["rep"] = r
        if not skip_judge and rep["has_report"]:
            rep.update(run_judge(case_dir, rep_dir))
        elif not rep["has_report"]:
            rep["judge_error"] = "no final_report.md produced"
        reps.append(rep)
    return aggregate_case(case_dir.name, reps, k)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("filters", nargs="*", help="case 名过滤（子串匹配）")
    ap.add_argument("--jobs", type=int, default=3, help="并发 case 数（默认 3）")
    ap.add_argument("--k", type=int, default=DEFAULT_K,
                    help=f"每个 case 重复次数（默认 {DEFAULT_K}，降方差）")
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
    print(f"batch dir: {batch_dir}\nk={args.k} jobs={args.jobs} "
          f"plugin-dir={PLUGIN_DIR}\ncases: {[c.name for c in cases]}\n")

    results: list = []
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_one, c, batch_dir, args.skip_judge, args.k): c
                   for c in cases}
        for fut in cf.as_completed(futures):
            r = fut.result()
            ps, os_ = r["process_score"], r["outcome_score"]
            print(f"  done {r['case']:<36} "
                  f"process={ps['mean']}±{ps['std']} "
                  f"outcome={os_['mean']}±{os_['std']} "
                  f"n_ok={r['n_ok']}/{r['k']} ({r['elapsed_s']}s)")
            results.append(r)

    results.sort(key=lambda r: r["case"])
    summary_path = batch_dir / "summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print("\n================ L2 SUMMARY (k-rep distributions) ================")
    for r in results:
        ps, os_, org = r["process_score"], r["outcome_score"], r["outcome_regex"]
        print(f"  {r['case']:<36} "
              f"process={ps['mean']}±{ps['std']}  "
              f"outcome(judge)={os_['mean']}±{os_['std']}  "
              f"outcome(regex)={org['mean']}±{org['std']}  n_ok={r['n_ok']}/{r['k']}")
        for d in r.get("defects", [])[:3]:
            print(f"      defect: {d[:100]}")
        for e in r.get("judge_errors", [])[:1]:
            print(f"      judge_error: {e[:100]}")
    print(f"\nsummary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
