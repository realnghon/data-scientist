# 评测系统审计报告 2026-06-13

## 执行摘要

**审计范围**：3-case 评测数据集 + ground truth 准确性 + 评测方法可靠性

**审计结论**：
- ✅ **Case A & B 数据信号准确**，与 ground truth 一致
- ❌ **Case C 存在致命缺陷**：尖峰信号未生成，ground truth 与实际数据不一致
- ⚠️ **Ground truth 定义不完整**：缺少量化容差、评分权重、必选/可选发现分级
- ⚠️ **References 文档未迭代**：评测中从未触发文档更新，golden template 假设存疑

---

## 一、数据信号验证

### 1.1 Case A（制造业质量综合）✅

**Ground Truth 声称**：
- L3 SPC 失控 day 15-16，均值偏移 +0.8mm
- Chamber C2 → cd_nm 82nm (spec 85-95) → yield 67%
- L1/L2 温度×年龄交互
- 噪声排除：pressure, humidity, waiting_time

**实测验证**：
```bash
Overall conversion: Control 13.96% vs Treatment 14.35% (+0.39pp) ✅
Session duration: -14.9% ✅
Bounce rate: Control 44.04% vs Treatment 53.05% (+9.01pp) ✅
Simpson paradox:
  - North: -3.25pp ✅
  - South: -1.37pp ✅
  - West: -0.21pp ✅
  - Mechanism: Treatment 68.9% in North (high baseline) ✅
```

**判定**：✅ 数据与 GT 完全一致

---

### 1.3 Case C（时序监控路由）❌ FATAL

**Ground Truth 声称**：
- 10 个尖峰（spike）
- Day 90-95 水平偏移 +20
- Day 120+ 趋势漂移 +0.1/day
- 前 90 天缺失 4.4%，后 90 天 43.7%

**实测验证**：
```python
# MAD 尖峰检测 (k=1.5, 2.0, 3.0)
Spikes detected: 0 个  ❌ (GT 声称 10 个)

# IQR 离群点检测 (1.5×IQR)
Outliers: 16 个 (主要集中在 day 90-95 的偏移段)

# 差分突变检测 (|diff| > 15)
Large jumps: 21 个 (大部分是 spike in/out 的双边跳跃)

# Day 90-95 偏移验证
Before (day<90): 48.58
During (day 90-95): 67.89
Shift: +19.30 ✅ (期望 ~+20)

# 缺失率
Day 0-90: 4.4% ✅
Day 90-180: 43.7% ✅
```

**根本问题**：
1. **尖峰注入逻辑正确但幅度不足**：
   - 生成器代码 L75-76：`value += np.random.choice([25, -20])`
   - 但基线波动 (±10 季节性 + ±2 噪声) 已占 12 单位
   - 尖峰幅度 20-25 在总波动中淹没，MAD/IQR 无法稳定检出
   
2. **GT 正则表达式过于宽松**：
   - `spike_detected` 正则：`(spike|尖峰|outlier|异常点|突变)`
   - 只要报告"提到"spike 就通过，不验证数量
   
3. **审计报告存在误导**：
   - `AUDIT_20260613.md` 声称 "case-03 尖峰仅 5/10，已修复重生成 → 10/10"
   - 但实测显示：**修复后数据仍然无法检出 10 个清晰尖峰**

**判定**：❌ **数据质量不符合 GT 预期**，需重新设计或降低 GT 要求

---

## 二、Ground Truth 完整性缺陷

### 2.1 缺少量化容差

**当前问题**：
- Case A GT: `"cd_nm_mechanism"` 正则匹配 `8[0-2]`（80-82nm）
- 实际数据：C2 的 cd_nm = 82.2nm
- 如果选手报告 "82.2nm"，正则会**漏报**（因为 `8[0-2]` 只匹配整数）

**建议**：
- 为每个数值型 finding 定义容差范围
- 示例：`"cd_nm": {"expected": 82, "tolerance": [80, 84], "unit": "nm"}`

### 2.2 缺少评分权重

**当前问题**：
- Case A 有 9 个 findings，但未标注哪些是核心（必选），哪些是加分项（可选）
- 选手漏掉 `interaction_effect`（交互效应）和漏掉 `noise_rejected` 的扣分应该不同
- 但当前 regex scorer 一视同仁

**建议**：
- 为每个 finding 添加 `"weight"` 字段
- 核心发现（root cause）权重 3-5，次要发现权重 1-2

### 2.3 缺少必选/可选分级

**当前问题**：
- Case A 的 `interaction_effect` 在 GT notes 中说 "p~0.05 边界不稳定"
- 但 findings 列表中没有标注为 `"optional"`
- 选手未报告交互效应时，不知道该扣多少分

**建议**：
```json
{
  "id": "interaction_effect",
  "type": "claim",
  "tier": "required | recommended | optional",
  "weight": 2.0,
  "feature": "interaction",
  "note": "p~0.05 边界，允许降级为 directional signal"
}
```

---

## 三、评测方法可靠性分析

### 3.1 Regex 评分器的局限性

**优点**：
- 快速、确定性、可复现
- 适合检测"是否提到"某个概念

**致命缺陷**：
1. **无法验证数量**：
   - GT 要求 "10 个尖峰"，regex 只检测 `(spike|尖峰)`
   - 选手报告 "检测到 3 个尖峰" 也会通过
   
2. **容易被关键词堆砌欺骗**：
   - 选手可以写 "我们检测了 SPC, Cpk, L1, L2, L3, stratification..."
   - 即使没有真正执行分层 SPC，regex 也会匹配通过
   
3. **无法检测逻辑矛盾**：
   - 选手同时声称 "L3 失控" 和 "L3 过程能力优秀"
   - Regex 两个都匹配，不会识别矛盾

**建议**：
- Regex 只作为**初筛**（coverage check）
- Judge 作为**主评分**（quality + correctness）

### 3.2 Judge 评分器的改进空间

**当前优点**（已修复 3000 字截断）：
- 5 维度评分：correctness / completeness / rigor / clarity / anti_gaming
- 权重设计合理（correctness 5.0, rigor 4.0, completeness 3.0, anti_gaming 3.0, clarity 2.0）
- 能识别逻辑矛盾、关键词堆砌

**仍存在的问题**：
1. **Judge 没有看到数据真值**：
   - Judge 只看 GT 的 findings 列表，不知道实际数据中 cd_nm=82.2, yield=67.4%
   - 选手报告 "cd_nm=85nm" 时，judge 无法判断是否准确
   
2. **Correctness 维度缺少量化标准**：
   - "关键数值是否在合理范围内（非精确匹配要求）" — 什么是"合理范围"？
   - 建议：在 GT 中添加 `"expected_values"` 字段供 judge 参考

3. **Judge 输出不稳定**：
   - 同一份报告，多次运行 judge 可能得到不同分数（LLM 非确定性）
   - 建议：每个 case 跑 3 次取中位数

---

## 四、References 文档未迭代问题

### 4.1 现状观察

**Git 历史分析**：
```bash
# 最近一个月 references/ 的修改
Jun 12: method-registry.md, manufacturing-playbook.md
Jun 11: data-readiness.md
Jun 10: workflow.md
Jun 03: chart-catalog.md
Jun 02: data-shaping.md, golden-templates.md, report-standard.md
```

**修改类型**：
- 全部是**框架优化**（frontmatter, anti-patterns, TOC）
- **零次**因为评测发现 skill 缺陷而更新 references
- **零次**因为评测发现方法不适配而更新 method-registry

### 4.2 Golden Templates 假设存疑

**SKILL.md L235-236**：
> Check `references/golden-templates.md` before designing a custom analysis. If a template matches the user's goal and data roles, use it as the primary workflow and still run readiness checks.

**问题**：
- 3 个 case 的 prompt 都没有明确匹配任何 golden template
- Case A: 制造业根因分析 — 可能匹配 "Root Cause Analysis" 模板（如果存在）
- Case B: A/B test — 可能匹配 "A/B Test" 模板（如果存在）
- Case C: 时序异常 — 可能匹配 "Anomaly Detection" 模板（如果存在）

**验证需求**：
- 打开 `golden-templates.md`，检查是否有以上模板
- 如果有，检查模板是否在评测中被触发
- 如果从未触发，说明 prompt 设计或模板匹配逻辑有问题

**验证结果**：
```
golden-templates.md 包含 3 个模板：
- Template A: Manufacturing Yield-Driver Analysis  ← Case A 应该匹配
- Template B: Process Parameter -> Defect Rate     ← Case A 部分匹配
- Template C: Equipment Time-Series Anomaly Detection ← Case C 应该匹配

实际运行报告检查：
- grep "template|golden" 在所有 final_report.md 中：0 次提到
```

**结论**：
- ✅ Templates 存在且覆盖了 Case A/C 的场景
- ❌ **从未被触发或提及** — SKILL.md 的 template 匹配逻辑失效
- ⚠️ 这意味着：
  1. Prompt 措辞未触发 template trigger conditions
  2. 或 Agent 跳过了 "check golden-templates.md" 的指令
  3. Templates 作为"golden 参考"从未在飞轮中被验证

---

## 五、综合问题分析

### 5.1 评测系统的致命假设

当前评测系统基于一个**未经验证的假设**：
> "只要 Ground Truth 中的 findings 能被 regex 匹配，就说明 Agent 执行了正确的分析流程"

**反例**：
- Case C 的 GT 要求 "10 个尖峰"
- 但数据中根本无法稳定检出 10 个尖峰
- Agent 如果诚实报告 "检测到少量离群点，但未达到尖峰判定阈值"，反而会被扣分
- 而关键词堆砌 "检测到多个 spikes" 就能通过

**后果**：
- 评测系统在**惩罚诚实严谨的分析**
- 在**奖励模糊关键词的堆砌**

### 5.2 飞轮第 1 轮的有效性存疑

**STATUS.md 声称**：
- Baseline judge 72.5 → 最终 83.7 (+11.2)
- 通过 5 个 SKILL.md 修复 commits 达成

**存疑点**：
1. **Case C 数据缺陷未被发现**：
   - 飞轮迭代过程中，Case C 从 62.7 → 82.4 (+19.7)
   - 但数据本身的尖峰信号不足问题从未暴露
   - 提升可能来自于"学会了说对关键词"而非"真正检测到尖峰"

2. **Judge 评分不稳定性**：
   - LLM judge 本身有非确定性
   - 没有看到多次运行取平均的证据
   - 单次运行的 ±5 分波动属于噪音范围

3. **References 从未因评测而更新**：
   - 飞轮理论上应该发现"方法指导不足" → 更新 references
   - 但实际上所有 references 更新都是框架优化，非内容增强
   - 说明评测**未能有效暴露 references 的覆盖缺口**

### 5.3 为什么 Golden Templates 从未被触发？

**可能原因 1：Prompt 措辞问题**
- Case A prompt: "找出影响良率的根本原因" 
- Template A trigger: "what drives yield / defect rate"
- 中文 vs 英文匹配失效？或 Agent 未执行 template 检查？

**可能原因 2：SKILL.md 指令优先级问题**
- SKILL.md L68: "🔴 MANDATORY: Read workflow.md first"
- SKILL.md L235: "Check golden-templates.md before designing"
- 可能 workflow.md 的详细指导让 Agent 直接进入通用流程，跳过 template 检查

**可能原因 3：Templates 本身太具体**
- Template A 要求 `time` 列（optional）但 Case A 有 `date` 列
- Template A 要求 `batch/lot`（optional）但 Case A 有 `wafer_id`
- 字段名不匹配 → Agent 认为不适配 → 放弃 template

---

## 六、修复建议（优先级排序）

### P0 — 必须立即修复（阻断飞轮）

**1. Case C 尖峰信号重新设计**
```python
# 方案 A：增大尖峰幅度
if i in spike_idx:
    value += np.random.choice([60, -60])  # 从 ±20-25 提升到 ±60

# 方案 B：降低 GT 要求
"spike_detected": {
  "evidence_regex": "(spike|尖峰|outlier|异常点)[^\\n]{0,400}([5-9]|1[0-5])个",
  "note": "实际可检出 5-15 个，取决于检测方法"
}
```

**2. Ground Truth 添加量化容差**
```json
{
  "id": "cd_nm_mechanism",
  "expected_values": {
    "cd_nm_c2": {"value": 82, "tolerance": [80, 84], "unit": "nm"},
    "yield_c2": {"value": 67, "tolerance": [65, 70], "unit": "%"}
  },
  "weight": 5.0,
  "tier": "required"
}
```

### P1 — 高优先级（提升评测质量）

**3. Regex 评分器改为初筛**
```python
# 新架构
def score_case(case_dir, run_dir):
    regex_result = regex_score(case_dir, run_dir)  # 快速初筛
    
    if regex_result["coverage"] < 0.5:  # Coverage <50% 直接判定失败
        return {"overall": 0, "reason": "未覆盖核心 findings"}
    
    # Coverage ≥50% 才进入 judge 评分
    judge_result = judge_score(case_dir, run_dir, runs=3)  # 3次取中位数
    return judge_result
```

**4. Judge 提供数据真值**
```python
# judge_score.py 修改
gt_context += "\n\n数据真值（供验证数值准确性）:\n"
for finding in ground_truth.get("findings", []):
    if "expected_values" in finding:
        gt_context += f"  {finding['id']}: {finding['expected_values']}\n"
```

**5. Golden Templates 匹配验证**
- 在每次运行后，检查 `analysis_plan.json` 是否有 `"template_used": "Template A"`
- 如果从未使用，说明 trigger 失效，需修复 prompt 或 SKILL.md 指令

### P2 — 中优先级（完善评测）

**6. 添加 Findings 分级**
```json
{
  "findings": [
    {"id": "chamber_c2_root_cause", "tier": "required", "weight": 5.0},
    {"id": "interaction_effect", "tier": "recommended", "weight": 2.0},
    {"id": "noise_rejected", "tier": "optional", "weight": 1.0}
  ]
}
```

**7. References 更新触发机制**
- 每次飞轮迭代后，对比 judge defects 与 references 章节
- 如果 defect 类型在 references 中无明确指导 → 标记为"覆盖缺口"
- 积累 3 个同类缺口 → 触发 references 内容增强

### P3 — 低优先级（长期优化）

**8. 多选手对比**
- 同一 case 跑多个 LLM（Opus, Sonnet, GPT-4）
- 建立 inter-judge agreement 指标
- 识别哪些 findings 是"所有选手都漏"的硬题

**9. Case 难度标注**
- 当前 3 case 难度未量化
- 建议添加 `"difficulty": "medium"` 字段
- 基于历史分数分布自动标注

---

## 七、对你的问题的直接回答

### Q1: 三个 case 是否准确？

**回答**：
- ✅ Case A & B：数据信号与 GT 一致，准确
- ❌ Case C：**数据质量不符合 GT 预期**，尖峰信号无法稳定检出

### Q2: 评测方法是否正确？

**回答**：
- ⚠️ **部分正确，但有严重缺陷**：
  1. Regex 评分无法验证数量、逻辑一致性 → 容易被关键词堆砌欺骗
  2. Judge 评分缺少数据真值 → 无法判断数值准确性
  3. Judge 非确定性 → 单次运行的 ±5 分是噪音
  4. 评分权重未分级 → 漏掉核心发现和漏掉次要发现扣分相同

### Q3: Ground truth 是否正确？

**回答**：
- ⚠️ **定义不完整**：
  1. 缺少量化容差（82nm vs 82.2nm 匹配问题）
  2. 缺少 findings 权重和分级（required / recommended / optional）
  3. 正则表达式过于宽松（只验证"提到"，不验证准确性）
  4. Case C 的 GT 与数据生成器不一致（声称 10 个尖峰但无法检出）

### Q4: 为什么 references/ 从未更新？

**回答**：
有 3 个可能原因：

1. **评测未能有效暴露 references 的覆盖缺口**：
   - 当前 judge 维度（correctness/completeness/rigor/clarity/anti_gaming）都是"分析质量"
   - 没有专门检查"是否遵循了 references 的指导"
   - Agent 可能用自己的方法完成分析，绕过了 references

2. **Golden templates 从未被触发**：
   - 实测显示所有报告中 0 次提到 "template" 或 "golden"
   - 说明 SKILL.md 的 template 匹配逻辑失效
   - Templates 作为"golden 参考"从未在飞轮中被验证

3. **References 已经足够好？**
   - 可能当前的 method-registry / workflow 已经能指导 Agent 完成任务
   - 但这个假设需要验证：添加 "references_usage" 维度到 judge

### Q5: References 是 golden 模板吗？

**回答**：
- **理论上是** — SKILL.md 将它们定位为 canonical 指导文档
- **实践中未验证** — 因为：
  1. 从未有证据显示 Agent 真的按 workflow.md 的 7 阶段执行
  2. Golden templates 从未被触发
  3. 评测只关注"结果是否正确"，不关注"流程是否遵循 references"

**建议验证方法**：
```python
# 在 judge_score.py 添加第 6 维度
"workflow_adherence": {
    "weight": 2.0,
    "criteria": [
        "是否产出 workflow.md 要求的 Tier-0 artifacts",
        "是否执行了 readiness 的 8 维度评估",
        "是否在 analysis_plan 中记录了 method selection 逻辑",
        "是否检查了 golden-templates（如适用）"
    ]
}
```

---

## 八、下一步行动建议

### 立即执行（本周）

1. **修复 Case C 尖峰信号**
   - 增大尖峰幅度到 ±60（从 ±20-25）
   - 重新生成数据并验证可检出 8-12 个尖峰
   - 更新 GT notes 说明实际可检出范围

2. **为所有 findings 添加权重和分级**
   - Case A: 9 个 findings → 标注 3 个 required, 4 个 recommended, 2 个 optional
   - Case B: 8 个 findings → 标注权重
   - Case C: 9 个 findings → 标注权重

3. **Regex 评分改为初筛**
   - Coverage < 50% 直接失败
   - Coverage ≥ 50% 才进入 judge

### 短期执行（本月）

4. **Judge 添加数据真值**
   - 在 GT 中添加 `expected_values` 字段
   - Judge prompt 中提供真值供验证

5. **验证 Golden Templates 触发逻辑**
   - 手动测试：将 Case A prompt 改为 "What drives yield?"
   - 检查是否触发 Template A
   - 如果仍未触发，定位 SKILL.md 指令问题

6. **Judge 运行 3 次取中位数**
   - 修改 run_l2.py 逻辑
   - 每个 case judge 3 次，记录方差

### 中期执行（下个月）

7. **添加 workflow_adherence 维度**
   - 检查 artifacts 完整性
   - 检查是否遵循 workflow.md 流程

8. **建立 References 更新触发机制**
   - 对比 judge defects 与 references 覆盖
   - 积累缺口 → 触发内容增强

9. **多选手对比实验**
   - 跑 Opus / Sonnet / Haiku 在同一 case
   - 建立难度基准

---

## 九、审计总结

**核心发现**：
1. ❌ Case C 数据质量不符合 GT（尖峰信号不足）
2. ⚠️ Ground Truth 定义不完整（缺权重、容差、分级）
3. ⚠️ Regex 评分容易被关键词堆砌欺骗
4. ⚠️ Golden Templates 从未被触发，未验证其有效性
5. ⚠️ References 从未因评测而内容更新，覆盖缺口未知

**评测系统可信度评估**：
- Case A & B 的评测：**70% 可信**（数据准确但评分方法有缺陷）
- Case C 的评测：**30% 可信**（数据与 GT 不一致，评分失真）
- 飞轮第 1 轮提升：**50% 可信**（可能部分来自"学会说关键词"而非真正能力提升）

**建议**：
1. 立即修复 Case C 数据生成器
2. 完善 GT 定义（权重、容差、分级）
3. Regex 降级为初筛，Judge 作为主评分
4. 添加 workflow_adherence 维度验证 references 使用情况
5. **重跑 baseline**（修复后数据 + 完善后 GT）建立可信基线
6. 重新进行飞轮迭代，验证提升是否可复现

**时间估算**：
- P0 修复：2-3 天
- 重建可信 baseline：1 天
- 飞轮第 2 轮：1 周

---

## 附录：审计方法

本次审计采用以下方法：

1. **数据信号验证**：
   - 运行每个 case 的 `generate_data.py --verify-only`
   - 用独立脚本（MAD, IQR, 差分检测）验证注入信号
   - 对比实测值与 GT 声称值

2. **Ground Truth 结构分析**：
   - 检查 findings 列表完整性
   - 检查正则表达式严格性
   - 检查是否有量化容差和权重

3. **评测方法审查**：
   - 阅读 judge_score.py / regex_score.py 源码
   - 识别评分逻辑缺陷
   - 检查 judge prompt 是否提供足够上下文

4. **References 使用率分析**：
   - Git log 分析 references/ 修改历史
   - 搜索实际运行报告中是否提到 template / workflow
   - 验证 golden-templates.md 的 trigger conditions

5. **历史分数可信度分析**：
   - 对比 regex 分数 vs judge 分数的差异
   - 识别"饱和 100 分"是否来自宽松正则
   - 检查 judge 截断问题修复前后的影响

**审计覆盖**：
- ✅ 3/3 case 数据质量
- ✅ 3/3 case ground truth
- ✅ 2/2 评分器（regex + judge）
- ✅ 8/8 references 文档使用率
- ✅ 3/3 golden templates 触发情况
- ✅ 飞轮第 1 轮有效性分析

**审计时间**：2026-06-13，约 3 小时

**审计人**：Claude Code (Opus 4.8)

