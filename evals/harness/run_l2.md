# L2 评测运行规程（真实插件加载 + 多次采样）

L2 用真实 agent 跑案例，评测的是 **skill 在真实环境里会不会被自主触发、被遵循**，
以及 Agent 的路由/决策行为——这是 L1 确定性管线覆盖不到的部分。

## 架构（2026-06-14 修「秤」后）

```
主会话（飞轮决策）
   │  只消费 summary.json：process/outcome 分布 + judge defects
   ▼
run_l2.py ── ThreadPool 并发（case 级）──┬─ case₁: 跑 k 次选手
                                         │     选手 = claude -p --plugin-dir plugins/data-scientist
                                         │     （插件真实加载；prompt 只含用户请求 + 数据路径）
                                         └─ caseₙ: 跑 k 次选手
                                              │ 每 rep 产物落 .runs/l2/<batch>/<case>/rep{i}/
                                              ▼
                                         每 rep 评分：
                                           score_case.py  → process_score（确定性）+ outcome_regex
                                           judge_score.py → outcome_score（语义，judge 5 维）
                                              ▼
                                         aggregate → 每 case 报 mean ± std 分布
```

关键原则：
- **真实加载**：选手用 `--plugin-dir` 真实装载插件，prompt 不再塞 SKILL.md 路径。评测因此
  能测出「skill 到底有没有被触发/遵循」——若没被遵循，选手不产出流程产物，process_score 自然变低。
- **多次采样**：每个 case 跑 k 次（默认 3），把模型随机方差从单点噪声变成可观测分布。
- **上下文隔离**：主会话只读 summary.json 的分布、defects；选手 transcript
  （`_contestant_stdout.log`、`final_report.md`）只落盘备查，**不要读进主会话**。
- **裁判独立**：judge 是单独 headless 进程，只看产物。

## 运行

```bash
python evals/harness/run_l2.py                    # 全部 case，每个 k=3 次，并发 3
python evals/harness/run_l2.py case-a --k 5       # 子串过滤 + 加大采样
python evals/harness/run_l2.py --jobs 5           # 提高 case 并发
python evals/harness/run_l2.py --skip-judge       # 只跑选手（调试）
```

主会话建议 `run_in_background` 跑，结束后只读：

```bash
cat evals/.runs/l2/<batch-ts>/summary.json
```

## 评分口径（双线分数）

每个 case 报告两条**独立**分数的分布（mean ± std over k reps）：

- **`process_score`（流程遵循度 · 确定性 · 零方差）**：score_case.py 的 routing + artifact
  检查——5 个产物（data_manifest / readiness_report / analysis_plan / evidence_matrix /
  final_report）是否存在、schema 是否合法。**这是改 skill 流程/gate 要求时唯一应敏感的干净
  信号**；std 应≈0，若 std 大说明选手时走时不走流程（本身是有价值的真实信号）。
- **`outcome_score`（结论质量 · 语义 · 有方差）**：judge_score.py 的 5 维 agent 裁判
  （correctness / completeness / rigor / clarity / anti_gaming），看结论对不对、推理严不严。
  judge 现在除最终报告外还读 analysis_plan / critique，以区分「真执行 vs 形式填充」。
- `outcome_regex`：score_case.py 的 finding/charts/anti_pattern 确定性命中，作辅助参考。
  历史上靠放宽正则刷过虚高分（见 AUDIT_20260613.md），**只作冒烟**。

> 不再有 50% coverage 硬阈值（2026-06-14 移除）——它把单次方差放大成 0 分悬崖，与 skill
> 改动无因果。低覆盖率现在自然反映在加权分里。

## 迭代闭环（A/B 分布对照）

```
1. python evals/harness/run_l1.py                       # 确定性管线全绿才继续
2. python evals/harness/run_l2.py --k 3 &               # 改 skill 前：基线 batch（before）
3. 改 SKILL.md（一次只改一个维度）
4. python evals/harness/run_l2.py --k 3 &               # 改 skill 后：对照 batch（after）
5. python evals/harness/flywheel_compare.py <before>/summary.json <after>/summary.json
6. 按判定记录：
   - process 确定性 improve / outcome 区间不重叠提升 → keep
   - 区间重叠 → inconclusive（不 revert 不邀功，加大 --k 或换方向）
   - 显著回退 → rollback
   record_result.py --status <keep|inconclusive|rollback> --process .. --outcome .. --k 3 --std ..
```

## 注意事项

- **判定看分布、不看单点**：outcome 仅当改前改后 mean±std 区间不重叠才下结论；重叠即噪声。
- 每轮迭代**一次只改一个维度**，否则无法归因。
- process_score 低 → 先查 skill 是否被触发/遵循（真实加载下这是 skill 表述问题）；
  outcome_score 低但 process 高 → 选手走了流程但结论质量不足，多为底层模型能力或方法选择。
- ground truth 修正与 skill 修改不要混在同一个 commit。
