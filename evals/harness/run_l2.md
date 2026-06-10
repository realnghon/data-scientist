# L2 评测运行规程（agent-in-the-loop）

L2 用真实 agent 跑案例，评测的是 **SKILL.md 的表述质量与 Agent 的路由/决策行为**——这是 L1 确定性管线覆盖不到的部分。

## 运行方式

在 Claude Code 主会话中，对每个 case spawn 一个 `general-purpose` 子 agent。**子 agent 只拿到 SKILL.md + 用户 prompt + 数据路径，不拿 ground truth。**

### Spawn prompt 模板

```
你是一个安装了 data-scientist 插件的数据分析 agent。

技能文件（必须先读取并遵循）：
<REPO>/plugins/data-scientist/skills/analysis-workflow/SKILL.md
技能引用的 references/ 与 scripts/ 在同一目录下，按 SKILL.md 指引按需加载。

用户请求：
<prompt.txt 的内容，其中 dataset.csv 替换为数据集绝对路径>

硬性约定（评测 harness 要求，不要省略）：
1. 所有产物写入目录：<RUN_DIR>
2. 结构化产物用 SKILL.md 规定的名字保存为独立 JSON 文件：
   data_manifest.json / readiness_report.json / analysis_plan.json /
   evidence_matrix.json / critique.json（按你路由判定实际需要的子集）
3. 最终报告保存为 final_report.md；图表保存为 png 文件
4. 以 auto 模式运行：不要向用户提问，按推荐选项决策并记录在报告的
   Human Decision Log 中
```

`<RUN_DIR>` 约定：`evals/.runs/l2/<case-id>-<YYYYMMDD-HHmm>/`

### 评分

子 agent 完成后：

```bash
python evals/harness/score_case.py evals/cases/<case-id> evals/.runs/l2/<run-dir> \
    --json evals/.runs/l2/<run-dir>/score.json
```

输出 per-check 明细：FAIL 项直接对应要修的 skill 段落（路由 FAIL → Shortcut Routing 表；finding FAIL → 对应 reference / 工作流步骤；anti-pattern FAIL → 反模式黑名单）。

## 推荐的最小回归集

| 目的 | cases |
|---|---|
| 完整流程质量 | case-01（驱动+混淆）、case-04（SPC）、case-05（Simpson） |
| 路由正确性 | case-06（profile-only）、case-07（named-method）、case-08（blocked） |
| 快速冒烟 | case-01 + case-06 |

## 注意事项

- 每轮迭代**一次只改一个维度**，否则无法归因分数变化。
- 子 agent 输出的产物文件名若不规范，评分器会按文件名片段模糊匹配
  （见 score_case.py 的 ARTIFACT_ALIASES），但 spawn prompt 中仍应显式规定命名。
- 评分 FAIL 项需人工抽查一遍正则是否误判，再决定改 skill 还是改 ground truth。
- 记录结果：`python evals/harness/record_result.py --old <旧> --new <新> --dimension <改动> --note <说明> --eval-mode l2`
