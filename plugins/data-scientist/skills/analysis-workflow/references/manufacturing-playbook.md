---
name: manufacturing-playbook
description: 制造业数据分析速查：SPC、Cpk、良率分析、根因。
---

# Manufacturing Playbook

制造业常见问题的速查手册。

## 常见字段角色

**目标变量：** yield, pass_rate, defect_rate, defect_count, cycle_time, Cp/Cpk  
**驱动变量：** line, station, lot, batch, shift, operator, supplier, 工艺参数（temp, pressure, speed）, time

---

## Recipe 1: SPC 控制图

### 图表选择

| 数据类型 | 子组大小 | 图表 |
|----------|----------|------|
| 连续测量 | 1 | I-MR |
| 连续测量 | 2-10 | X-bar / R |
| 连续测量 | >10 | X-bar / S |
| 缺陷率 | 可变 n | p-chart |
| 缺陷计数 | 固定 | c-chart |
| 缺陷计数 | 可变 | u-chart |

### 最小数据

20-25 个受控子组用于计算控制限。

### 分层检查（强制）

如果数据有分层变量（line, equipment, operator），**必须**：
1. ANOVA 检验异质性（p < 0.05）
2. 如果异质 → **每层独立控制图**，不合并
3. 报告每层状态 + 违规规则（WE-1..4, Nelson-1..8）

**示例：**
- ✅ 正确：L1/L2/L3 各一张图，报告 "L1: in-control, L2: out-of-control (WE-2 @ day 15-16)"
- ❌ 错误：合并 → 单图 → 掩盖问题源

### Run Rules

使用 Western Electric (`WE-1..4`) 或完整 Nelson (`Nelson-1..8`)。编号对齐 `ds_skill.spc` 实现。

**Helper:** `ds_skill.spc.individuals_mr_chart(data)`（或 `xbar_r_chart` / `p_chart` / `c_chart` / `u_chart`），然后 `apply_western_electric_rules(chart)` / `apply_nelson_rules(chart)`  
**Chart:** `ds_skill.plotting.plot_control_chart`

---

## Recipe 2: 能力分析 (Cp/Cpk)

### 前提

过程必须**先通过稳定性检查**（Recipe 1），不稳定过程的能力指数无意义。

### 公式

| 指数 | 公式 | 含义 |
|------|------|------|
| Cp | (USL - LSL) / (6σ) | 潜在能力 |
| Cpk | min((USL-μ)/(3σ), (μ-LSL)/(3σ)) | 实际能力（考虑偏移） |

### 判定

| Cpk | 判定 |
|-----|------|
| ≥1.33 | 良好 |
| 1.0-1.33 | 可接受 |
| <1.0 | 不可接受 |

**Helper:** `ds_skill.spc.capability_summary(values, lsl, usl)`（返回 Cp/Cpk/Pp/Ppk），或单独的 `cp` / `cpk` / `pp` / `ppk`

---

## Recipe 3: 良率/缺陷驱动因素

### 方法

1. **单因素筛选** — Welch ANOVA（连续 X）或 chi-square（分类 X）
2. **相关性排序** — Spearman 或 Point-Biserial
3. **回归** — Logistic（缺陷 Y）或 Linear（良率 Y）

### 分层 Pareto

按类别（line, product, defect_type）分别统计，找 top 驱动。

**Helper:** `ds_skill.correlation.correlation_with_target(df, target='yield', fdr_alpha=0.05)`  
**Chart:** `ds_skill.plotting.plot_feature_importance`

---

## Recipe 4: 根因分析 — Defect Pareto

### 步骤

1. 按 defect_type 聚合计数
2. 降序排序
3. 累计占比曲线
4. 标记 80% 线（vital few）

**Helper:** 用 pandas + matplotlib，无专用 helper  
**Chart:** `ds_skill.plotting.plot_pareto`（如果有）或手动 bar + line

---

## Recipe 5: MSA（测量系统分析）

### Gage R&R

分解总变异 = 零件变异 + 测量变异（重复性 + 再现性）。

**最小数据：** 10 零件 × 3 操作员 × 2 重复 = 60 测量

**判定：**
- %R&R < 10%：良好
- 10-30%：可接受
- >30%：不可接受

**Helper:** 无专用 helper。用 pandas + ANOVA 分解方差：按 `part` 和 `operator` 分组求方差分量（`ds_skill.analysis_methods.compare_numeric_by_group` 可辅助组间检验）。

---

## Recipe 6: DOE 筛选

### 简单筛选设计

对于 k 个因子，用 2^(k-p) 部分因子设计或 Plackett-Burman。

**分析：** ANOVA 或 Lasso 找显著因子。

---

## Recipe 7: OEE 分解

OEE = Availability × Performance × Quality

| 指标 | 计算 |
|------|------|
| Availability | planned_time / (planned_time - downtime) |
| Performance | actual_output / ideal_output |
| Quality | good_output / total_output |

**找瓶颈：** 三者中最低的优先改进。

---

## 反模式

- ❌ 不稳定过程计算 Cpk
- ❌ 混合不同 line/equipment 的数据到单张控制图
- ❌ 用控制限作为规格限
- ❌ 重新计算控制限用于评判同一批数据
- ❌ 忽略分层变量

**Helper 汇总：**
- `ds_skill.spc.individuals_mr_chart` / `xbar_r_chart` / `p_chart` / `c_chart` / `u_chart`
- `ds_skill.spc.apply_western_electric_rules` / `apply_nelson_rules`
- `ds_skill.spc.capability_summary`（Cp/Cpk/Pp/Ppk）
- `ds_skill.correlation.correlation_with_target`
- `ds_skill.plotting.plot_control_chart`
- `ds_skill.plotting.plot_pareto`
