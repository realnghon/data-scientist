---
description: 将已画像的数据集和用户目标转化为可辩护的分析方案，包括选定方法、假设检验和被拒绝的替代方案
argument-hint: <analysis-goal> [target-metric]
---

# 制定分析方案

使用 `data-scientist` 方法规划流程，将已画像的数据集和用户目标转化为可辩护的分析方案。

**示例：**
- `/ds-plan "比较实验组与对照组"`
- `/ds-plan "对转化驱动因素进行排序"`
- `/ds-plan "检测产出下降" yield_pct`

## 执行要求

1. 确认目标指标 `Y`、分析粒度以及允许的分析范围。
2. 读取 `${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/references/method-registry.md`、`${CLAUDE_PLUGIN_ROOT}/skills/analysis-workflow/references/data-readiness.md` 以及相关的领域手册。
3. 根据目的、数据类型、假设条件和业务实用性选择方法。
4. 记录被拒绝的方法及其被拒绝的原因（较弱或无效）。
5. 对重要结论纳入交叉验证。

## 预期输出

- 分析目的
- 选定的方法集
- 假设检验
- 被拒绝的方法
- 执行顺序
- 所需图表
- 仍需人工决策的事项

除非用户明确要求，否则不要执行该方案。