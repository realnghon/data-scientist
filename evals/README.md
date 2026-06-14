# Evals — data-scientist 插件评测闭环

两层评测体系，用于测量插件能力并驱动 skill 迭代：

| 层 | 跑什么 | 测什么 | 成本 |
|---|---|---|---|
| **L1** | `run_l1.py` → `run_full_workflow.py` 确定性管线 | helper 库 + 产物 envelope 回归（profile/readiness/shaping） | 零 token，可进 CI |
| **L2** | `run_l2.py` 真实插件加载的 agent 选手 + 独立 judge | 流程遵循度、结论命中、完整性、严谨性、clarity、gaming 检测 | 并发 headless，上下文隔离 |

## 目录

```
evals/
├── cases/
│   ├── case-a-manufacturing-comprehensive/  # 制造业质量综合分析（融合 01/04/09）
│   ├── case-b-business-tradeoff/            # 商业决策悖论（融合 02/05）
│   ├── case-c-timeseries-routing/           # 时序异常路由（融合 03/06/07/08）
│   └── _archived-9case-20260613/            # 原 9-case 深度调试套件
├── harness/
│   ├── run_l1.py            # L1 确定性管线回归（零 token，CI 安全）
│   ├── run_l2.py            # L2 并发选手（--plugin-dir 真实加载）+ k 次采样 + 评分
│   ├── score_case.py        # 确定性双线评分：process_score + outcome（regex）
│   ├── judge_score.py       # Agent judge（correctness/completeness/rigor/clarity/anti_gaming）
│   ├── score_two_stage.py   # judge 多次取中位数（消除 LLM 非确定性）
│   ├── flywheel_compare.py  # 改 skill 前后 A/B 分布对照 → keep/inconclusive/rollback
│   ├── record_result.py     # 追加迭代记录到 results.tsv
│   └── run_l2.md            # L2 运行规程与评分口径（权威文档）
├── results.tsv             # 迭代记录（含 process/outcome/k/std 列）
└── .runs/                  # 运行产物（git-ignored）
```

## 评分口径（双线分数）

修「秤」后（2026-06-14），每个 case 报告两条**独立**分数，避免把「流程遵循」和「结论质量」混为一谈：

- **`process_score`（流程遵循度 · 确定性 · 零方差）**：5 个 gate 产物（data_manifest / readiness_report / analysis_plan / evidence_matrix / final_report）是否存在 + schema 是否合法。**改 skill 流程/gate 要求时唯一应敏感的干净信号。**
- **`outcome_score`（结论质量 · 语义 · 有方差）**：5 维 agent judge；judge 现在除最终报告外还读 `analysis_plan`/`critique`，能区分「真执行 vs 形式填充」。
- `outcome_regex`：finding/charts/anti_pattern 确定性命中，作辅助参考（历史上靠放宽正则刷过虚高分，只作冒烟）。

> 不再有 50% coverage 硬阈值——它把单次方差放大成 0 分悬崖。详见 [`harness/run_l2.md`](harness/run_l2.md)。

## 当前评测套件（3-case 压缩版）

**2026-06-13 压缩**：原 9-case → 3 综合 case，token 成本 -60%（200k→80k/轮），能力覆盖 100%。

| Case | 测试目标 | 复杂度 |
|---|---|---|
| **A** | 制造业质量综合分析：多表整合根因 + 分层 SPC + 交互效应（融合 01/04/09） | 4 表，300 wafer，4 层信号 |
| **B** | 商业决策悖论：A/B test 多指标权衡 + Simpson's paradox（融合 02/05） | 2.4 万用户，23 月数据 |
| **C** | 时序异常路由：多周期季节性 + 尖峰 + 变点 + 路由分支（融合 03/06/07/08） | 180 天时序，7 尖峰 + 2 变点 |

**原 9-case 套件**：已归档到 `_archived-9case-20260613/`，保留作深度调试用途。

## 快速使用

```bash
# L1 确定性回归（先全绿再跑 L2）
python evals/harness/run_l1.py

# L2 完整评测：每个 case 跑 k=3 次，记 mean±std 分布
python evals/harness/run_l2.py --k 3 --jobs 3

# 单个 case
python evals/harness/run_l2.py case-a --k 3 --jobs 1

# 结果（主会话只读 summary.json）
cat evals/.runs/l2/<batch-ts>/summary.json
```

**运行要求**：Claude Code 环境（`claude -p` 可用）、Python 3.10+。每个 comprehensive case 单 rep 约 30–45 分钟。

## 迭代闭环（A/B 分布对照）

```
1. python evals/harness/run_l1.py                  # 确定性管线全绿才继续
2. python evals/harness/run_l2.py --k 3 &          # 改 skill 前：基线 batch（before）
3. 改 SKILL.md（一次只改一个维度）
4. python evals/harness/run_l2.py --k 3 &          # 改 skill 后：对照 batch（after）
5. python evals/harness/flywheel_compare.py <before>/summary.json <after>/summary.json
6. 按判定记录（record_result.py）：
   - process 确定性 improve / outcome 区间不重叠提升 → keep
   - 区间重叠 → inconclusive（不 revert 不邀功，加大 --k 或换方向）
   - 显著回退 → rollback
```

**核心纪律**：判定看**分布**不看单点——outcome 仅当改前改后 `mean±std` 区间不重叠才下结论；重叠即噪声。一次只改一个维度；ground truth 修正与 skill 修改不混 commit。
