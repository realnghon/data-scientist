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

每个 case 目录统一为：`prompt.txt + ground_truth.json + generate_data.py + 数据 csv`（已于 2026-06-13 审计并去除 v1/v2/v3 版本混乱；数据信号已逐一用脚本验证与 ground truth 一致）。

| Case | 测试目标 | Ground truth 来源（已验证的信号） |
|---|---|---|
| 01 manufacturing-full | 完整流程：温度主效应 + equipment_age×temperature 交互 + 噪声排除 | 交互项 t=-9.5；噪声变量 \|r\|<0.04 |
| 02 ab-test | 多指标权衡：转化 +2.7pp↑ vs 会话时长 -15.8%↓、跳出 +8pp↑ → 条件性建议 | 各效应均 p<1e-10 |
| 03 time-series-anomaly | 日/周季节性 + 10 尖峰 + day90-95 水平偏移 + day120 后漂移 | 生成器审计修复后 10/10 尖峰落点 |
| 04 spc | 3 产线分层 SPC：L3 在 5/16-17 失控（+0.8mm）；Cp≈1.86/1.16/0.98 | 受控段实测 Cp 与 GT 一致 |
| 05 simpson-interaction | Simpson 悖论：Premium 整体 +23.9/月 vs South -84.2、West -27.1/月 | 市场份额 South→North 迁移 |
| 06 routing-profile-only | 路由：profile 请求不产出 analysis_plan/evidence_matrix，不做统计推断 | 路由约定（humidity 缺失 1.4% 实存） |
| 07 routing-named-method | 路由：指定 t-test 但 revenue 严重偏态（skew=5.95、86.9% 零值）→ 检查假设并给替代 | 路由约定 + 数据实测 |
| 08 readiness-blocked | revenue 缺失 44.4% → readiness=blocked → emit data_request | 实测缺失率 44.4% |
| 09 wafer-rca | 三表整合根因：litho C2 → cd_nm 82 vs 90（spec 85-95）→ 良率 67 vs 90 | C2 与 C1/C3 差 22.5pp；已知良性混杂见 GT notes |

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
