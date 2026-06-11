# 评测螺旋式优化计划

## 迭代目标

**核心原则**：评测难度 → 暴露 Skill 不足 → 改进 Skill → 重测验证 → 提升评测难度 → 循环往复

## 第一轮迭代（已完成）

### Case-09 v1（单源长格式）
- **难度**：4500 行长格式，需 pivot
- **结果**：86.4%，暴露 same-event leakage 未检测
- **改进**：data-readiness.md 增 same-event measurement 检查
- **状态**：✅ 已推送（commit 846f622）

## 第二轮迭代（进行中）

### Case-09 v2（多源 join + pivot）
**新增复杂度**：
- 2 个数据源：fab_log.csv（1500 行，chamber/recipe/time）+ metrology.csv（4500 行，长格式参数）
- 需要操作：join on wafer_id → pivot metrology → 分析
- 根因注入：litho chamber='C2' → cd_nm 漂移 → yield 下降
- 噪声陷阱：recipe、waiting_time（无效应）

**期待检测**：
- ✅ Join 执行记录
- ✅ Pivot 执行记录
- ✅ Chamber C2 识别为根因
- ✅ cd_nm 超规格机制解释
- ✅ final_test speed/leakage 被标记为 same-event（不作为驱动）
- ✅ Recipe/waiting time 排除为噪声

**文件已生成**：
- generate_data_v2.py
- fab_log.csv (91KB)
- metrology.csv (267KB)
- prompt_v2.txt
- ground_truth_v2.json

**下一步**：
1. 运行 case-09 v2 评测（用 prompt_v2.txt + ground_truth_v2.json）
2. 评分，记录 FAIL 点
3. 根据 FAIL 改进 SKILL.md（可能需要明确"多源 join 协议"）
4. 重跑验证
5. 记录到 results.tsv
6. 推送

## 后续迭代方向

### Case-01 至 Case-08 复杂化

**当前问题**：过于简单（500-3000 行，5-10 列），导致 100% 通过率无法暴露深层问题

**提升方向**：

**Case-01（制造 yield）**：
- 当前：5 列简单表
- v2：增加 equipment_age（设备老化）、operator_shift（班次）、material_lot（物料批次）、环境温湿度
- 注入交互：temperature × equipment_age 交互效应

**Case-04（SPC）**：
- 当前：单列测量值
- v2：多条产线并行（line_id），要求分线做 SPC，识别哪条线失控

**Case-05（Simpson）**：
- 当前：7 列
- v2：增加时间维度（month），Simpson 悖论在时间上也反转（Q1 pooled 看 A 最优，但每月内都是 B 最优）

**Case-08（readiness blocked）**：
- 当前：单一阻断（Y 缺失 44%）
- v2：多维度阻断（Y 缺失 35% + grain 混乱 + leakage 列存在），考验 agent 能否全部识别并综合判断

### 新场景案例

**Case-10（时序 join + lag feature）**：
- 传感器时序数据 + 故障事件表
- 需要 time-series join（asof join），创建滞后特征（lag_1d, lag_7d）
- 根因：lag_3d 的温度峰值预测 7 天后故障

**Case-11（不平衡分类 + 成本敏感）**：
- 欺诈检测，正负样本 1:100
- 需要 SMOTE/class_weight，评估用 PR-AUC 而非 accuracy
- 考验 agent 能否识别不平衡并选对策略

**Case-12（censored survival）**：
- 客户流失分析，部分客户右删失（still active）
- 需要 Kaplan-Meier + Cox proportional hazards
- method-registry 已有 survival 章节，测试能否应用

## 迭代协议

每轮迭代：
1. **选 1-2 个案例**加难度或新增
2. **运行评测**，记录得分与 FAIL 点
3. **改进 Skill**（SKILL.md / data-readiness.md / method-registry.md）
4. **重跑验证**改进有效
5. **记录** results.tsv
6. **审计 + 推送**
7. **更新此文档**，记录本轮发现

## 评测指标跟踪

| 迭代 | 案例 | 版本 | 得分 | 关键 FAIL | Skill 改进 | 验证得分 |
|---|---|---|---|---|---|---|
| R1 | case-09 | v1 | 86.4% | cd_nm 未识别为根因（same-event leakage） | same-event leakage 检查 | - |
| R2 | case-09 | v2 首次 | 57.7% | chamber_c2 正则不匹配、data_transformations 缺失 | - | - |
| R2 | case-09 | v2 正则修正 | 73.1% | data_transformations 缺失、join 未记录、cd_nm 机制未提及、same_event 未标记 | analysis_plan 增 data_transformations 字段 | 进行中 |

## 目标

短期（5 轮）：case-09 v2 通过 95%+，case-01/04/05/08 复杂化版本设计完成
中期（10 轮）：9 个案例平均分从 91% → 80%（难度提升导致分数下降是预期），Skill 稳定性提升
长期（20 轮）：新增 3 个高难场景（case-10/11/12），平均分回升到 85%+，形成生产级评测基准
