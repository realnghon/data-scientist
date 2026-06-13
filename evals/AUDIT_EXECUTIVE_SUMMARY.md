# 评测系统审计 — 执行摘要

**审计日期**：2026-06-13  
**完整报告**：`EVAL_SYSTEM_AUDIT_20260613.md`

---

## 🚨 关键发现

### 1. Case C 数据质量致命缺陷 ❌

**问题**：Ground Truth 声称有 "10 个尖峰"，但实际数据无法稳定检出

**验证结果**：
- MAD 尖峰检测（k=1.5/2.0/3.0）：**0 个**
- IQR 离群点检测：16 个（主要是 day 90-95 的水平偏移，非尖峰）
- 差分突变检测：21 个（spike in/out 双边跳跃）

**根本原因**：
- 尖峰幅度 ±20-25，但基线波动（季节性 ±10 + 噪声 ±2）已占 12 单位
- 信号淹没在噪声中，标准检测方法无法稳定识别

**影响**：
- Case C 的评测结果**不可信**
- 飞轮第 1 轮中 Case C 从 62.7 → 82.4 的提升可能来自"学会说关键词"而非真正检测能力

---

### 2. Ground Truth 定义不完整 ⚠️

**缺失项**：
1. **量化容差**：GT 要求 "cd_nm 8[0-2]"，但实际数据 82.2nm 会漏匹配
2. **评分权重**：9 个 findings 未标注核心/次要，漏掉 root cause 和漏掉噪声排除扣分相同
3. **必选/可选分级**：如 `interaction_effect` 在 notes 中说 "p~0.05 不稳定"，但未标注 optional

**后果**：
- 无法区分"致命遗漏"和"加分项遗漏"
- Judge 评分标准模糊

---

### 3. Regex 评分器容易被欺骗 ⚠️

**缺陷**：
1. **无法验证数量**：GT 要求 "10 个尖峰"，regex 只检测 `(spike|尖峰)`，报告 "3 个" 也通过
2. **关键词堆砌**：写 "SPC, Cpk, L1, L2, L3, stratification" 即使未执行也匹配
3. **无法检测矛盾**：同时声称 "L3 失控" 和 "L3 能力优秀" 都会匹配

**建议**：降级为初筛（coverage check），Judge 作为主评分

---

### 4. Golden Templates 从未被触发 ⚠️

**发现**：
- `golden-templates.md` 有 3 个模板（Manufacturing Yield, Process Parameter, Time-Series Anomaly）
- Case A 应匹配 Template A，Case C 应匹配 Template C
- 实测：所有运行报告中 **0 次提到 "template" 或 "golden"**

**问题**：
1. Prompt 措辞未触发 trigger conditions？
2. SKILL.md 指令优先级问题，Agent 跳过 template 检查？
3. Templates 字段名要求太严格（time vs date, batch vs wafer_id）？

**影响**：
- References 作为 "golden 参考" 的假设**未经验证**
- 不知道 templates 是否真的有效

---

### 5. References 从未因评测而更新 ⚠️

**观察**：
- 最近一个月 references/ 的修改全是框架优化（frontmatter, anti-patterns, TOC）
- **0 次**因为评测发现方法不足而增强内容
- **0 次**因为评测发现覆盖缺口而添加新章节

**可能原因**：
1. 评测只关注"结果正确"，不关注"流程是否遵循 references"
2. Judge 没有 "workflow_adherence" 维度
3. References 已经足够好？（但未验证）

---

## 📊 评测系统可信度评估

| 组件 | 可信度 | 说明 |
|------|--------|------|
| Case A 数据 | ✅ 90% | 信号验证一致 |
| Case B 数据 | ✅ 90% | 信号验证一致 |
| Case C 数据 | ❌ 30% | 尖峰信号不足 |
| Ground Truth | ⚠️ 60% | 定义不完整（缺权重、容差、分级）|
| Regex 评分 | ⚠️ 50% | 只能做初筛，容易被关键词欺骗 |
| Judge 评分 | ⚠️ 70% | 缺数据真值、非确定性、截断已修复 |
| 飞轮第 1 轮 | ⚠️ 50% | 提升可能部分来自"学会关键词"而非真正能力 |

---

## 🔧 修复优先级

### P0 — 立即修复（阻断飞轮）

1. **修复 Case C 尖峰信号**
   ```python
   # 增大幅度：±60（从 ±20-25）
   if i in spike_idx:
       value += np.random.choice([60, -60])
   ```
   - 重新生成数据
   - 验证可检出 8-12 个尖峰
   - 更新 GT notes

2. **Ground Truth 添加权重和分级**
   ```json
   {
     "id": "chamber_c2_root_cause",
     "tier": "required",
     "weight": 5.0,
     "expected_values": {"cd_nm_c2": {"value": 82, "tolerance": [80, 84]}}
   }
   ```

3. **Regex 改为初筛**
   - Coverage < 50% → 直接失败
   - Coverage ≥ 50% → 进入 judge

**时间估算**：2-3 天

---

### P1 — 高优先级（提升评测质量）

4. **Judge 提供数据真值**（用于验证数值准确性）
5. **验证 Golden Templates 触发逻辑**（定位为何从未使用）
6. **Judge 运行 3 次取中位数**（消除非确定性噪音）

**时间估算**：3-5 天

---

### P2 — 中优先级（完善评测）

7. **添加 workflow_adherence 维度**（检查是否遵循 references）
8. **建立 References 更新触发机制**（自动识别覆盖缺口）
9. **多选手对比实验**（建立难度基准）

**时间估算**：1-2 周

---

## 🎯 下一步行动

### 本周

1. ✅ 完成审计报告（已完成）
2. ⬜ 修复 Case C 数据生成器
3. ⬜ 为所有 findings 添加权重和分级
4. ⬜ Regex 改为初筛

### 下周

5. ⬜ 重建可信 baseline（修复后数据 + 完善 GT）
6. ⬜ 验证 Golden Templates 触发逻辑
7. ⬜ Judge 添加数据真值 + 运行 3 次取中位数

### 下月

8. ⬜ 添加 workflow_adherence 维度
9. ⬜ 飞轮第 2 轮迭代（基于可信 baseline）
10. ⬜ 多选手对比实验

---

## 💡 关键建议

1. **不要基于当前数据继续飞轮迭代** — Case C 数据缺陷会误导优化方向
2. **修复后需重建 baseline** — 历史分数不可比
3. **增加 workflow_adherence 维度** — 验证 references 是否真的被使用
4. **Golden Templates 需要明确的触发验证** — 不能假设它们有效

---

## 📋 审计方法

- ✅ 运行所有 case 的 `generate_data.py --verify-only`
- ✅ 独立脚本验证注入信号（MAD, IQR, 差分检测）
- ✅ 对比实测值 vs GT 声称值
- ✅ 审查评分器源码（judge_score.py / regex_score.py）
- ✅ Git log 分析 references 修改历史
- ✅ 搜索运行报告中 template 使用情况

**审计覆盖**：3/3 case 数据质量，3/3 GT，2/2 评分器，8/8 references，3/3 templates

**审计时间**：2026-06-13，约 3 小时

---

**完整报告**：`EVAL_SYSTEM_AUDIT_20260613.md` (6000+ 字，含详细分析和代码示例)
