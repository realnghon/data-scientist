---
name: chart-catalog
description: 图表选择速查。5 条默认规则覆盖 90% 场景。
---

# Chart Catalog

## 默认规则（优先使用）

1. **数值 by 组** → `boxplot`
2. **时间序列** → `line plot`
3. **相关性** → `scatter` (n<1000) 或 `hexbin` (n≥1000)
4. **分布** → `histogram`
5. **排序/重要性** → `horizontal bar`（降序）

不用火山图、3D 图、复杂 heatmap，除非用户明确要求。

## 完整 Catalog（特殊场景）

### Distribution（分布）
- `histogram` — 标准分布形状，N≥30
- `KDE` — 平滑分布，N≥50
- `boxplot` — 稳健汇总 + 离群点
- `violin` — 形状 + 汇总，多组对比

### Comparison（组比较）
- `boxplot` — 2-15 组
- `dotplot + CI` — 估计值 + 不确定性
- `paired line` — 配对/重复测量

### Correlation（相关性）
- `scatter + fit` — 两变量，N<5000
- `hexbin` — 高 N (>5000)
- `correlation heatmap` — 多变量相关矩阵

### Time Series（时间序列）
- `line + bands` — 单/少系列 + 不确定性
- `small multiples` — 多系列
- `STL decomposition` — 趋势 + 季节 + 残差

### SPC（过程控制）
- `I-MR chart` — 个体值
- `X-bar / R chart` — 子组
- `p-chart / c-chart` — 缺陷率
- `Pareto` — 原因排序

## Helper 函数

所有图表函数在 `ds_skill.plotting`：

```python
from ds_skill.plotting import (
    plot_grouped_boxplot,
    plot_time_series,
    plot_scatter_fit,
    plot_histogram,
    plot_feature_importance,
    plot_control_chart,
    plot_correlation_matrix,
    plot_kaplan_meier,
)
```

每个函数返回 matplotlib figure 对象，保存用 `fig.savefig(path)`。

## 通用注释要求

每张图必须包含：
- 标题（问题，不是变量名）
- 轴标签 + 单位
- N= 样本量
- 缺失值计数（如果 >0）
- 不确定性（CI / SE / band）
