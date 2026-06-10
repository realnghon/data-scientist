#!/usr/bin/env python3
"""Append an eval iteration record to evals/results.tsv.

Usage::

    python evals/harness/record_result.py \
        --old 84.2 --new 88.0 --status keep \
        --dimension "路由表强化" --note "case-06 路由从 profile 误判修复" \
        --eval-mode l2
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results.tsv"


def current_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=RESULTS.parent.parent,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill", default="data-scientist")
    ap.add_argument("--old", required=True, help="score before the change ('-' for baseline)")
    ap.add_argument("--new", required=True, help="score after the change")
    ap.add_argument("--status", default="keep", choices=["baseline", "keep", "rollback"])
    ap.add_argument("--dimension", required=True, help="what dimension/aspect was changed")
    ap.add_argument("--note", required=True)
    ap.add_argument("--eval-mode", default="l2", choices=["l1", "l2", "dry_run", "full_test"])
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    row = "\t".join(
        [ts, current_commit(), args.skill, args.old, args.new,
         args.status, args.dimension, args.note, args.eval_mode]
    )
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(row + "\n")
    print(f"recorded: {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
