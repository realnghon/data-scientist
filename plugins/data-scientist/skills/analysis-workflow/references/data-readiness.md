---
name: data-readiness
description: 8 维数据质量检查。分析前运行，判定 ok / partial / blocked。
---

# Data Readiness

分析前检查数据质量。每维度独立评分，整体决策取最差分。

## 8 维度速查

### 1. Sample Size（样本量）

| 每组 n | 评分 | 操作 |
|--------|------|------|
| ≥30 | ok | 参数方法可用 |
| 10-29 | partial | 用非参数，报告 CI |
| 5-9 | partial | 仅探索，bootstrap CI |
| <5 | blocked | 仅描述统计 |

回归：≥10 行/预测变量。分类：少数类 ≥30。

### 2. Missingness（缺失）

| 缺失率 | 评分 |
|--------|------|
| Y 缺失 >5% | blocked |
| X 缺失 <10% | ok |
| X 缺失 10-30% | partial（需 imputation 策略） |
| X 缺失 >30% | blocked |

**规则：** 永不 impute Y。Impute X 需记录策略。

### 3. Grain Consistency（粒度一致性）

检查 `df.duplicated(subset=[id_keys]).sum()`：
- = 0 → ok
- >0 且是合法重复测量 → partial（标记待聚合）
- 混合粒度 → blocked

### 4. Time Coverage（时间覆盖）

| 检查项 | 阈值 | 评分 |
|--------|------|------|
| 总跨度 vs 周期 | ≥2 cycles | <2 → partial |
| 间隙比例 | <10% | 10-30% → partial, >30% → blocked |
| 采样频率 | 一致 | 不一致 → partial |

### 5. Class Balance（类别平衡）

| 多数:少数 | 评分 |
|-----------|------|
| ≤3:1 | ok |
| 3:1-10:1 | partial（用 PR-AUC/F1） |
| 10:1-100:1 | partial（重采样或 cost-sensitive） |
| >100:1 | blocked（改为异常检测） |

### 6. Leakage（泄漏）

检查清单：
- [ ] 结果后记录的列（root_cause, rework_notes）→ 删除
- [ ] 未来时间戳（滚动窗口包含当前行）→ 加 lag
- [ ] 目标衍生特征（target-mean encoding）→ 仅在 train fold 计算
- [ ] 全局统计量（normalization）→ 仅在 train fold fit
- [ ] 按 Y 排序后取 top-k 作为特征 → 删除

任何泄漏维度 → **blocked**。

### 7. Role Clarity（角色明确性）

必须明确：
- `Y`（目标变量）
- `time`（时间列，如果时序分析）
- `entity_id`（实体标识符）
- `group`（分组维度）

| 状态 | 评分 |
|------|------|
| Y 明确 | ok |
| Y 有 2-3 个候选 | partial（给用户选项） |
| Y 无候选 | blocked（仅 profile） |

### 8. Measurement Reliability（测量可靠性）

| 问题 | 评分 |
|------|------|
| 单位不一致（kg/g 混合） | partial（需转换） |
| 传感器已知故障期 | partial（标记/过滤） |
| 数据录入错误（负年龄） | partial（outlier 检测） |
| 格式不一致（日期格式） | partial（需清洗） |

## 整体决策

```python
overall = max(dim_scores)  # 取最差分
if overall == 'blocked':
    return data_request + narrowed_scope
elif overall == 'partial':
    return narrowed_scope + caveats
else:
    return proceed
```

## Helper

`ds_skill.readiness.assess_readiness(df, target, time_col=None, entity_id=None)` 返回 8 维评分 + 整体决策。
