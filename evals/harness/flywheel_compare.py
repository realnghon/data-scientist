#!/usr/bin/env python3
"""飞轮 A/B 对照：比较改 skill 前后两个 L2 batch 的分数分布，给出可信判定。

修「秤」后的飞轮纪律（2026-06-14）：不再和历史单点比、不再因单次噪声 revert。

- ``process_score`` 确定性（std≈0）：均值差超过 ``PROCESS_EPS`` 即视为真实改变（流程遵循
  度变了）——改 skill 的流程/gate 要求应在这条线上看到效果。
- ``outcome_score`` 有方差：仅当 after 显著优于 before（两者 mean±std 区间**不重叠**）才判
  ``keep``；区间重叠 = 噪声淹没信号 → ``inconclusive``（既不 keep 也不 revert，应加大 --k 或
  换改动方向）；after 显著低于 before → ``regress``。

Usage::

    # 改 skill 前后各跑一次 run_l2.py（同 --k），再对照两个 summary.json
    python evals/harness/flywheel_compare.py <before_summary.json> <after_summary.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROCESS_EPS = 1.0  # process_score 确定性，>1 分差即视为真实变化


def _verdict_deterministic(before: dict, after: dict) -> str:
    """流程线判定：确定性，小差即可信（仅用 EPS 滤 round 噪声）。"""
    b, a = before.get("mean"), after.get("mean")
    if b is None or a is None:
        return "n/a"
    if a - b > PROCESS_EPS:
        return "improve"
    if b - a > PROCESS_EPS:
        return "regress"
    return "unchanged"


def _verdict_noisy(before: dict, after: dict) -> str:
    """结论线判定：区间不重叠才下结论，否则归为 inconclusive（不让噪声触发动作）。"""
    b, a = before.get("mean"), after.get("mean")
    bs, as_ = before.get("std") or 0.0, after.get("std") or 0.0
    if b is None or a is None:
        return "n/a"
    if a > b and (a - as_) > (b + bs):
        return "keep"
    if a < b and (b - bs) > (a + as_):
        return "regress"
    return "inconclusive"


def _fmt(d: dict) -> str:
    if not d or d.get("mean") is None:
        return "-"
    return f"{d['mean']}±{d.get('std', 0)}"


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python flywheel_compare.py <before_summary.json> <after_summary.json>")
        return 1

    before = {c["case"]: c
              for c in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))}
    after = {c["case"]: c
             for c in json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))}

    cases = sorted(set(before) & set(after))
    if not cases:
        print("no overlapping cases between the two summaries", file=sys.stderr)
        return 2

    print(f"{'case':<34} {'process before→after':<24} {'':<9} "
          f"{'outcome before→after':<24} {'verdict':<13}")
    print("-" * 112)
    proc, outcome = [], []
    for c in cases:
        bp, ap_ = before[c]["process_score"], after[c]["process_score"]
        bo, ao = before[c]["outcome_score"], after[c]["outcome_score"]
        pv, ov = _verdict_deterministic(bp, ap_), _verdict_noisy(bo, ao)
        proc.append(pv)
        outcome.append(ov)
        print(f"{c:<34} {_fmt(bp) + ' → ' + _fmt(ap_):<24} {pv:<9} "
              f"{_fmt(bo) + ' → ' + _fmt(ao):<24} {ov:<13}")

    print("-" * 112)
    print("\n判定汇总：")
    print(f"  process（流程遵循度·确定性）: {proc.count('improve')} improve / "
          f"{proc.count('regress')} regress / {proc.count('unchanged')} unchanged")
    print(f"  outcome（结论质量·judge）  : {outcome.count('keep')} keep / "
          f"{outcome.count('regress')} regress / {outcome.count('inconclusive')} inconclusive")

    if outcome.count("regress") > outcome.count("keep"):
        rec = "ROLLBACK — outcome 显著回退多于提升"
    elif outcome.count("keep") > 0 and outcome.count("regress") == 0:
        rec = "KEEP — 有显著提升且无回退"
    elif "improve" in proc and "regress" not in proc:
        rec = "KEEP — 流程遵循度确定性提升（outcome 未显著但未回退）"
    else:
        rec = "INCONCLUSIVE — 信号被方差淹没；加大 --k 或换改动方向，不要 revert"
    print(f"\n建议：{rec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
