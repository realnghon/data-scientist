# P1-2: Golden Templates 触发测试结果

**测试时间**：2026-06-13 20:32  
**测试目的**：验证 Golden Templates 是否被触发

---

## 测试设计

**测试 Prompt**：
```
We have yield data from our manufacturing line.
What drives yield? Which process parameters affect defect rate?

Please analyze the manufacturing data and identify root causes.

Data: fab_log.csv, metrology.csv, final_test.csv (in this directory)
```

**预期行为**：
- 应该匹配 Template A（Manufacturing Yield-Driver Analysis）
- Trigger conditions: "what drives yield", "process parameters", "defect rate"
- 应该在报告中提到 "template" 或 "golden-templates.md"

---

## 测试结果

**状态**：❌ **Template 未被触发**

**证据**：
1. 输出文件：`/tmp/test_template_output.txt`（109 行）
2. 关键词搜索：`grep -i "template\|golden"` → 无结果
3. 分析直接开始，未提及 template 检查

**实际行为**：
- Agent 直接进行了制造良率根因分析
- 使用了正确的方法（特征重要性、相关系数）
- 但没有检查或提及 golden-templates.md
- 报告格式：标准分析报告，非 template 规定格式

---

## 原因诊断

### 可能原因 1：Prompt 措辞不匹配 Trigger Conditions

**Template A Trigger**（来自 golden-templates.md L15）：
```
User asks any of: "what drives yield / defect rate / scrap", 
"why are some lots/lines/shifts worse", 
"find the top factors hurting yield".
```

**测试 Prompt**：
```
"What drives yield? Which process parameters affect defect rate?"
```

**匹配度**：✅ 高度匹配（包含 "what drives yield" 和 "defect rate"）

**结论**：Prompt 措辞应该触发，问题不在这里。

---

### 可能原因 2：SKILL.md 指令优先级问题

**SKILL.md L235**：
```
Check `references/golden-templates.md` before designing a custom analysis.
If a template matches the user's goal and data roles, use it as the primary workflow.
```

**问题**：
- 这是一个 "建议性" 指令（"Check ... before"）
- 可能被 workflow.md 的详细指导抢占
- Agent 可能认为已经知道如何做良率分析，跳过了 template 检查

**证据**：
- 所有历史运行报告中 0 次提到 "template"
- 说明这不是偶然，而是系统性的

---

### 可能原因 3：Templates 要求太具体

**Template A Required Roles**（L21-24）：
```
| Role | Required | Notes |
|---|---|---|
| target | yes | yield %, defect rate, pass/fail, scrap rate |
| candidate drivers | yes (>=3) | process params, equipment, recipe, material, shift |
| time | optional | enables SPC and time-confound checks |
| batch / lot | optional | enables batch-confound check; if absent, flag |
```

**测试数据**：
- 没有提供具体的数据文件（只是提到文件名）
- Agent 可能在数据发现阶段就放弃了 template 匹配

**证据不足**：需要用实际数据文件测试

---

## 修复方案

### 方案 A：增强 SKILL.md 指令强度（推荐）

**修改 SKILL.md L235**：
```markdown
🔴 MANDATORY: Before designing any analysis, check `references/golden-templates.md`:

1. Read the template catalog (Manufacturing, Process Parameter, Time-Series Anomaly, etc.)
2. Match user's question against trigger conditions
3. If ANY template matches:
   - Use it as the PRIMARY workflow
   - Document in analysis_plan: `"template_used": "Template A"`
   - Follow its methods sequence and output skeleton
4. If NO template matches:
   - Document in analysis_plan: `"template_checked": true, "no_match_reason": "..."`
   - Proceed with general workflow.md

**Why this matters**: Templates encode field-proven patterns that prevent common pitfalls.
```

---

### 方案 B：修改 Template Trigger 语言（备选）

让 Template A 的 trigger 更宽松：
```markdown
Trigger Conditions:
User mentions ANY of: yield, defect, quality, scrap, capability, process control
AND mentions ANY of: root cause, driver, analysis, why, what affects
→ ALWAYS check if Template A applies
```

但这可能导致 over-matching。

---

### 方案 C：标记为"参考而非强制"（最后手段）

如果 templates 设计不适合实际使用场景：
```markdown
Note: golden-templates.md 提供参考性模板，但非强制使用。
当用户明确请求"使用模板"或 prompt 完全匹配 trigger 时才应用。
```

但这会降低 templates 的价值。

---

## 推荐行动

**优先级**：
1. ✅ **立即执行**：方案 A（增强 SKILL.md 指令）
2. ⬜ **验证测试**：修改后重新运行测试
3. ⬜ **如果仍失败**：诊断是否是 workflow.md 抢占问题

**预期改进**：
- Template 触发率从 0% 提升到 >80%
- workflow_adherence 维度（如果添加）会检测到 template 使用

---

**报告时间**：2026-06-13 20:35  
**状态**：诊断完成，待修复
