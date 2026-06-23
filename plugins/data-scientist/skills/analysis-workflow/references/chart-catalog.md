---
name: chart-catalog
description: 图表选择速查，5 条默认规则覆盖 90% 场景，含特殊场景 catalog（SPC 控制图、相关性热图、生存曲线等）。当需要选图表类型、确认图表标注规范、或查绘图辅助函数时使用。
---

# 图表目录

## 画图前置（确定性）

画任何图前，所用的列必须已在 `data_manifest` 里记录过名称、dtype、取值。直接对假设存在的列调 `pivot_table` / `boxplot` 是最常见的崩溃源。传列前校验列存在(`if col not in df.columns`)与类型(`pd.api.types.is_numeric_dtype`)，让错误在画图前报出而非中途崩。

## 默认规则（优先使用）

1. **数值 by 组** → `boxplot`
2. **时间序列** → `line plot`
3. **相关性** → 默认 `hexbin`（n≥1000），可按需降级到 `scatter`（画子集、或想看单点/离群点时）
4. **分布** → `histogram`
5. **排序/重要性** → `horizontal bar`（降序）

不用火山图、3D 图、复杂 heatmap，除非用户明确要求。

## 完整目录（特殊场景）

### 分布
- `histogram` — 标准分布形状，N≥30
- `KDE` — 平滑分布，N≥50
- `boxplot` — 稳健汇总 + 离群点
- `violin` — 形状 + 汇总，多组对比

### 组比较
- `boxplot` — 2-15 组
- `dotplot + CI` — 估计值 + 不确定性
- `paired line` — 配对/重复测量

### 相关性
- `hexbin` — 大 N 默认（n≥1000），避免过度绘制
- `scatter + fit` — 小样本或刻意取的子集；想看单点/离群点时按需降级
- `correlation heatmap` — 多变量相关矩阵

### 时间序列
- `line + bands` — 单/少系列 + 不确定性
- `small multiples` — 多系列
- `STL decomposition` — 趋势 + 季节 + 残差

### 过程控制（SPC）
- `I-MR chart` — 个体值
- `X-bar / R chart` — 子组
- `p-chart / c-chart` — 缺陷率
- `Pareto` — 原因排序

## 辅助函数

所有图表函数在 `ds_skill.plotting`（已精简至统计核心）：

```python
from ds_skill.plotting import (
    plot_control_chart,           # SPC 控制图
    plot_correlation_matrix,      # 相关性热图
    plot_regression_diagnostics,  # 回归诊断 4 图
    plot_time_series_decomposition,  # 时序分解
    plot_distribution_comparison, # 分布对比 + QQ图
    plot_kaplan_meier,           # 生存曲线
    plot_pareto,                 # 帕累托图
    plot_capability_histogram,   # 过程能力分析
    plot_flagged_scatter,        # 异常标记散点图
    plot_roc_curve,              # ROC 曲线
    plot_confusion_matrix,       # 混淆矩阵
    plot_calibration_curve,      # 校准曲线
    plot_feature_importance,     # 特征重要性
)
```

每个函数返回 matplotlib figure 对象，保存用 `fig.savefig(path)`。通用图表（直方图、散点图、箱线图）请用 matplotlib/seaborn 直接绘制。

## 图表标注要求

每张图必须包含：
- 标题（问题，不是变量名）
- 轴标签 + 单位
- N= 样本量
- 缺失值计数（如果 >0）
- 不确定性（CI / SE / band）
