---
name: analysis-plan-template
description: JSON template for the analysis_plan artifact — method selection logic, data transformations, claims, rejected alternatives, and helper usage decisions. Use when generating an analysis_plan before execution. Triggers — create analysis plan, plan artifact, method selection documentation.
---

# Analysis Plan Template

This is the canonical JSON structure for the `analysis_plan` artifact. Every non-trivial analysis must produce one before executing code (Gate 2).

## Template

```json
{
  "analysis_goal": {
    "user_question": "原始用户问题",
    "target_Y": "目标变量",
    "candidate_X": ["驱动因素1", "驱动因素2"],
    "analysis_unit": "行的含义",
    "filters_applied": ["过滤条件"]
  },
  "data_transformations": [
    "Joined fab_log + metrology on wafer_id",
    "Pivoted metrology long format to wide (station×param columns)",
    "Filtered outliers beyond 3σ",
    "Created lag features: temperature_lag_1d"
  ],
  "claims": [
    {
      "claim": "要验证的结论描述",
      "primary_method": "主方法名称",
      "rationale": "为什么选这个方法（数据特征 + 假设匹配）",
      "assumptions": ["假设1：正态性", "假设2：独立性"],
      "cross_check": "交叉验证方法",
      "helper_ref": "ds_skill.module.function OR null (hand-coded)",
      "helper_decision": "used helper / hand-coded because: <reason>"
    }
  ],
  "rejected_alternatives": [
    {"method": "被拒方法", "reason": "为什么不用（假设不满足/数据不适配）"}
  ]
}
```

## Field Notes

- **data_transformations**: list every non-trivial data operation before analysis (joins, pivots, aggregations, feature engineering). Essential for reproducibility and for evaluating whether transformations were correct.
- **claims[].helper_ref**: fully qualified reference to `ds_skill.<module>.<function>`; `null` if hand-coded. Record the decision in `helper_decision`.
- **claims[].helper_decision**: must explain why a helper was used or bypassed (import failed, signature mismatch, error after retry).
- **rejected_alternatives**: every method considered but rejected, with one-line reason (assumption fail, sample too small, leakage risk).

## Purpose

The analysis_plan serves as:
- Pre-execution checklist for user review (guided mode checkpoint)
- Audit trail for "why this method"
- Template for reproducibility
