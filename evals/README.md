# Evals — data-scientist 插件评测闭环

两层评测体系，用于测量插件能力并驱动 skill 迭代：

| 层 | 跑什么 | 测什么 | 成本 |
|---|---|---|---|
| **L1** | `run_full_workflow.py` 确定性管线 | helper 库 + 产物 envelope 回归（profile/readiness/shaping） | 零 token，可进 CI |
| **L2** | 后台并发真实 agent + 独立 judge | 路由判断、流程遵循、结论命中、完整性、严谨性、clarity、gaming检测 | 并发 headless，上下文隔离 |

## 目录

```
evals/
├── cases/
│   ├── case-a-manufacturing-comprehensive/  # 制造业质量综合分析（融合 01/04/09）
│   ├── case-b-business-tradeoff/            # 商业决策悖论（融合 02/05）
│   ├── case-c-timeseries-routing/           # 时序异常路由（融合 03/06/07/08）
│   └── _archived-9case-20260613/            # 原 9-case 深度调试套件
├── harness/
│   ├── run_l2.py           # L2 并发执行 + 独立 judge 评分
│   ├── judge_score.py      # Agent judge（correctness/completeness/rigor/clarity/anti_gaming）
│   └── regex_score.py      # Regex 评分器（ground_truth findings 匹配）
└── .runs/                  # 运行产物（git-ignored）
```

## 当前评测套件（3-case 压缩版）

**2026-06-13 压缩**：原 9-case → 3 综合 case，token 成本 -60%（200k→80k/轮），能力覆盖 100%。

| Case | 测试目标 | 复杂度 | 最新成绩 (regex/judge) |
|---|---|---|---|
| **A** | 制造业质量综合分析<br>多表整合根因 + 分层 SPC + 交互效应<br>融合 case-01/04/09 | 4 表，300 wafer<br>4 层信号 | 93.7 / 76.5 |
| **B** | 商业决策悖论<br>A/B test 多指标权衡 + Simpson's paradox<br>融合 case-02/05 | 2.4 万用户<br>23 月数据 | 93.4 / 92.2 |
| **C** | 时序异常路由<br>多周期季节性 + 尖峰 + 变点 + 路由分支<br>融合 case-03/06/07/08 | 180 天时序<br>7 尖峰 + 2 变点 | 76.0 / 82.4 |
| **平均** | — | — | **87.7 / 83.7** |

**最新结果**：见 [`STATUS.md`](STATUS.md)（含 baseline 对比、修复历史、飞轮迭代记录）。

**原 9-case 套件**：已归档到 `_archived-9case-20260613/`，保留作深度调试用途。

## 快速使用

```bash
# L2（3-case 完整评测，并发运行）
cd /path/to/data-scientist
python evals/harness/run_l2.py case-a case-b case-c --jobs 3

# 单个 case 测试
python evals/harness/run_l2.py case-a --jobs 1

# 结果目录
ls evals/.runs/l2/$(date +%Y%m%d)-*/
```

**运行要求**：
- Claude Code 或兼容环境（支持 Agent tool 的 headless spawn）
- Python 3.10+
- 每次完整运行耗时 ~20-30 分钟（3-case 并发）

## 迭代闭环

```
1. 建立 baseline：python evals/harness/run_l2.py case-a case-b case-c --jobs 3
2. 读 summary.json 中的 defects → 定位 SKILL.md 薄弱维度
3. 修复一个维度（一次只改一处）：
   - correctness → 工作流步骤或方法选择
   - completeness → 产物完整性或发现遗漏
   - rigor → 假设检查、统计严谨性
   - clarity → 报告结构、术语定义
4. 重跑 3-case 验证改进（并发）
5. 对比 judge 分数：提升 → commit，下降 → revert
6. 更新 STATUS.md 记录迭代
```

**飞轮第 1 轮成果**（2026-06-13）：
- Baseline: 平均 judge 72.5
- 6 个 SKILL.md 修复 commits
- 最终: 平均 judge **83.7** (+11.2)
- 详见 [`STATUS.md`](STATUS.md)
