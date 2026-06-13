# L2 评测运行规程（后台并发模式）

L2 用真实 agent 跑案例，评测的是 **SKILL.md 的表述质量与 Agent 的路由/决策行为**——这是 L1 确定性管线覆盖不到的部分。

## 架构（2026-06-13 改造）

```
主会话（飞轮决策）
   │  只消费 summary.json：分数 + FAIL 项 + judge defects
   ▼
run_l2.py ── ThreadPool 并发 ──┬─ 选手₁: claude -p（headless，读 SKILL.md 跑 case）
                               ├─ 选手₂: claude -p
                               └─ 选手ₙ: claude -p
                                    │ 产物落盘 .runs/l2/<batch>/<case>/
                                    ▼
                               judge: score_case.py (regex, 免费)
                                    + judge_score.py (agent 裁判, headless claude -p)
```

关键原则：
- **上下文隔离**：选手的完整输出（`_contestant_stdout.log`、`final_report.md`）只落盘备查，
  主会话**不要读**——只读 `summary.json` 里的分数、regex FAIL 项和 judge defects。
- **裁判独立**：judge 是单独的 headless 进程，看不到选手的对话过程，只看产物。
- **选手无 GT**：选手 prompt 只含 SKILL.md 路径 + 用户请求 + 数据绝对路径。

## 运行

```bash
python evals/harness/run_l2.py                    # 全部 case，默认并发 3
python evals/harness/run_l2.py case-01 case-04    # 子串过滤
python evals/harness/run_l2.py --jobs 5           # 提高并发
python evals/harness/run_l2.py --skip-judge       # 只跑选手（调试用）
```

主会话建议用 `run_in_background` 跑上面的命令，结束后只读：

```bash
cat evals/.runs/l2/<batch-ts>/summary.json
```

## 评分口径

- `regex_score`：score_case.py 确定性检查（产物/结论/图表/反模式）。快、免费、可回归，
  但审计（AUDIT_20260613.md）发现历史上靠放宽正则刷出过虚高分——**只作冒烟参考**。
- `judge_score`：5 维 agent 裁判（correctness/completeness/rigor/clarity/anti_gaming），
  语义评估，**作为飞轮的主要信号**。judge 报告截断已修复（3000→30000 字）。
- 两者显著背离时：人工抽查该 case 的 final_report.md（这是唯一需要人看选手输出的场景）。

## 迭代闭环中的位置

```
1. npm run eval:l1                      # 全绿才继续
2. python evals/harness/run_l2.py &     # 后台并发，主会话不阻塞
3. 读 summary.json → 定位 FAIL/defects → 改 SKILL.md（一次一个维度）
4. 重跑失败 case 验证
5. record_result.py 记录 → 提升 commit / 回退 revert
```

## 注意事项

- 每轮迭代**一次只改一个维度**，否则无法归因分数变化。
- 评分 FAIL 项需人工抽查正则是否误判，再决定改 skill 还是改 ground truth；
  ground truth 修正与 skill 修改不要混在同一个 commit。
- 选手产物文件名不规范时评分器按 ARTIFACT_ALIASES 模糊匹配，但 spawn prompt 已显式规定命名。
