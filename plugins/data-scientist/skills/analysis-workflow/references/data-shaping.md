---
name: data-shaping
description: 数据整形速查：grain 决策、pivot/melt、join、泄漏检查。按需内联到 execution 阶段。
---

# Data Shaping

数据整形操作，不单独成阶段，在 execution 里按需使用。

## Grain 决策（粒度）

**Grain = 一行代表什么。** 先选 grain，再整形。

| Grain | 一行是 | 用途 |
|-------|--------|------|
| raw-event | 单次观测 | 行级建模 |
| entity | 一个产品/客户 | 实体级特征 |
| batch/lot | 一个批次 | 批次良率 |
| time-bucket | (实体?, 时段) | 趋势/SPC |
| group | 一个组 | 组比较 |

**信息丢失：** 聚合会丢失变异性。记录丢失的内容。

## Long ↔ Wide

### Long（长格式）
列：`id, time, metric_name, metric_value`  
用于：多指标流水、新指标频繁增加

### Wide（宽格式）
列：`id, time, metric_1, metric_2, ...`  
用于：建模（每列是特征）、透视表

```python
# Long → Wide
wide = long.pivot_table(index=['id','time'], columns='metric_name', 
                        values='metric_value', aggfunc='mean')
wide = wide.reset_index()

# Wide → Long
long = wide.melt(id_vars=['id','time'], var_name='metric_name', 
                 value_name='metric_value')
```

## Aggregation（聚合）

```python
agg = df.groupby(['line', 'date'], dropna=False).agg(
    yield_pct = ('passed', 'mean'),
    n_units = ('passed', 'size'),
    defects = ('defects', 'sum')
)
```

**规则：** 
- 总是带上 `n_units`（分母）
- 混合 grain 时先分离，再聚合

| 变量类型 | 聚合函数 |
|----------|----------|
| 数值测量 | mean / median |
| 计数 | sum |
| 比率 | weighted mean |
| 二分类 | mean（= 比例） |
| 时间戳 | min / max / first / last |

## Joins（表连接）

**红灯检查：**

| 陷阱 | 症状 | 修复 |
|------|------|------|
| 1:N 爆炸 | 行数暴增 | `merge(..., validate="1:1")` |
| 时间窗口 join | 事件对错批次 | `merge_asof(tolerance=...)` |
| 模糊 key | 空格/大小写 | `df['k'] = df['k'].str.strip().upper()` |
| many-to-many | 组合爆炸 | 至少一侧先聚合 |

```python
# 时间窗口 join
joined = pd.merge_asof(
    inspections.sort_values('ts'),
    sensors.sort_values('ts'),
    on='ts', by='line_id',
    direction='backward',
    tolerance=pd.Timedelta('5min')
)
```

**记录 join 匹配率：** `matched_rows / left_rows`，<80% 要调查。

## Leakage 检查点

整形过程中的泄漏点：

- [ ] 结果后列（root_cause）合并进来 → 删除
- [ ] 滚动窗口包含当前行 → `rolling(w).shift(1)`
- [ ] 按 Y 排序后取 top-k → 删除
- [ ] 全局统计量（mean/std）→ 仅在 train fold 计算
- [ ] Target-mean encoding → 仅在 train fold 计算

## 常见 Grain 决策

| 问题 | 选择的 grain |
|------|--------------|
| "哪些因素影响 Y?" | Y 的分析单元（raw 或 entity） |
| "哪个组不同?" | group_summary |
| "何时变化?" | time_bucket（一致频率） |
| "过程稳定吗?" | time_bucket + 子组 |
| "多久到事件?" | event_pairs（带删失标记） |

## Pandas 常用 idiom

```python
# 检查 grain
assert df.duplicated(subset=['id','time']).sum() == 0

# 宽→长（melt）
long = wide.melt(id_vars=['id','time'])

# 长→宽（pivot）
wide = long.pivot_table(index=['id','time'], columns='var', values='val')

# 时间窗口聚合（避免泄漏）
df['rolling_mean'] = df.groupby('id')['value'].rolling(7).mean().shift(1)

# join 并检查匹配率
result = pd.merge(left, right, on='key', how='left', validate='m:1', indicator=True)
match_rate = (result['_merge'] == 'both').mean()
assert match_rate > 0.8, f"Low match rate: {match_rate:.1%}"
```

## 输出结构

```python
analysis_view = {
    "name": "wafer_wide_features",
    "grain": "one row per wafer_id",
    "source_ops": [
        {"op": "filter", "expr": "stage=='final'"},
        {"op": "join", "on": ["wafer_id"], "validate": "1:1", "match_rate": 0.99},
        {"op": "pivot", "index": "wafer_id", "aggfunc": "mean"}
    ],
    "n_rows": 18432,
    "n_cols": 47,
    "leakage_checks": {"post_event_columns_removed": ["root_cause"]}
}
```
