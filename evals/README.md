# Evals — data-scientist 插件评测闭环

两层评测体系，用于测量插件能力并驱动 skill 迭代：

| 层 | 跑什么 | 测什么 | 成本 |
|---|---|---|---|
| **L1** | `run_full_workflow.py` 确定性管线 | helper 库 + 产物 envelope 回归（profile/readiness/shaping） | 零 token，可进 CI |
| **L2** | spawn 真实 agent 读 SKILL.md 跑案例 | 路由判断、流程遵循、结论命中 ground truth、图表产出、反模式 | 每案例一次 agent 会话 |

## 目录

```
evals/
├── cases/case-XX-*/        # prompt.txt + ground_truth.json (+ dataset.csv/generate_data.py)
├── harness/
│   ├── score_case.py       # 确定性评分器（产物/结论/图表/反模式四类检查）
│   ├── run_l1.py           # L1 全量运行 + 评分
│   ├── run_l2.md           # L2 运行规程（spawn prompt 模板）
│   └── record_result.py    # 迭代结果追加到 results.tsv
├── results.tsv             # 迭代历史（与 darwin-results/results.tsv 同列）
└── .runs/                  # 运行产物（git-ignored）
```

## 案例清单

| Case | 测试目标 | Ground truth 来源 |
|---|---|---|
| 01 manufacturing-full | 完整流程：驱动排序 + 噪声排除 + equipment_age 混淆检测 | `examples/manufacturing_yield/generate_data.py` 注入系数 |
| 02 ab-test | 完整流程：转化率 lift≈2pp + CI + SRM 检查 | `examples/ab_test/generate_data.py`（12%→14%） |
| 03 time-series-anomaly | 日/周季节性 + 趋势 + 3 类异常（尖峰/漂移/中断）+ 系统性判定 | `examples/time_series/generate_data.py` |
| 04 spc | 失控判定（Rule 2 @501-520、Rule 6 @601-650）+ Cp≈0.81 只在受控段计算 | `cases/case-04-spc/generate_data.py` |
| 05 simpson-interaction | Simpson 悖论（pooled A 最高 vs 分层 B 最高）+ 价格×促销交互 + 噪声排除 | `cases/case-05-simpson-interaction/generate_data.py` |
| 06 routing-profile-only | 路由：profile 请求不应产出 analysis_plan/evidence_matrix，不做统计推断 | 路由约定 |
| 07 routing-named-method | 路由：指定 t-test 但数据严重偏态 → 检查假设并给出替代方法，不静默跑无效检验 | 路由约定 + 数据特性 |
| 08 readiness-blocked | Y 缺失 44% → readiness=blocked → emit data_request，不强行给趋势结论 | `cases/case-08-readiness-blocked/generate_data.py` |

## 快速使用

```bash
# L1（确定性回归，CI 安全）
npm run eval:l1                  # 或 python evals/harness/run_l1.py [case 名过滤]

# L2（agent 实测）— 按 harness/run_l2.md 的模板 spawn 子 agent，然后：
python evals/harness/score_case.py evals/cases/case-01-manufacturing-full \
    evals/.runs/l2/case-01-manufacturing-full-<ts> --json .../score.json
```

## 迭代闭环

```
1. 跑 L1（npm run eval:l1）→ 全绿才进入 2；L1 变红说明 helper/envelope 回归
2. 跑 L2（run_l2.md）→ score_case.py 输出 per-check 明细
3. 定位 FAIL → 改 SKILL.md / references / agents 的具体段落（一次只改一个维度）
   - routing FAIL → SKILL.md「Shortcut Routing」
   - finding FAIL → 对应 reference 或工作流步骤
   - anti-pattern FAIL → 反模式黑名单
4. 重跑失败的 case 验证
5. 记录：python evals/harness/record_result.py --old <旧> --new <新> \
       --dimension <改动维度> --note <说明> --eval-mode l2
6. 提升 → commit（status=keep）；下降/无效 → git revert（status=rollback）
```

注意：评分 FAIL 先人工抽查正则是否误判，再决定改 skill 还是改 ground truth；
ground truth 修正与 skill 修改不要混在同一个 commit。
