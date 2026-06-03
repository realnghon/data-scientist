# Data Scientist Skill 深度审计修复方案

## 审计日期
2026-06-03

## 审计发现总结

**核心问题**：Skill 拥有完整的企业级基础设施（12步工作流 + 9个reference文档 + 180+测试函数 + multi-agent编排），但实际执行时**几乎全部未使用**。

**执行率统计**：
- 工作流：12步中只执行了3步（25%）
- ds_skill 辅助库调用：0次
- reference 文档阅读：2/9（22%）
- artifacts 产出：2/8完整（25%）
- multi-agent 编排：0次

## 根因分析（来自审计报告 287-304行）

### 根因1：步骤1被跳过导致连锁反应
**问题**：`Read references/workflow.md` 是"建议"而非"硬性前置"
**后果**：Agent 直接跳到步骤2，后续流程"自由发挥"

### 根因2：Shortcut Routing 触发过于宽松
**问题**：用户说"全套分析"被解读为"exploratory profile-only"
**后果**：激进地跳过了大部分步骤

### 根因3：环境准备失败的连锁反应
**问题**：路径错误 + venv问题（第一份报告）
**后果**：Agent 选择"绕过 ds_skill 直接手写"

### 根因4：无强制 checklist
**问题**：SKILL.md 是"指导手册"不是"强制清单"
**后果**：Agent 可以合理化跳过任何步骤

### 根因5：用户指令被过度解读
**问题**："只要最终报告"被理解为"跳过中间产物、跳过 CHECKPOINT"
**后果**：从"完整流程但只展示最终报告"变成"跳过流程直接出报告"

## 修复策略（采用审计报告推荐的路径C：折中方案）

### Tier 0 - 必须执行（核心保证）
- ✅ 强制读取 `workflow.md`
- ✅ 产出 `data_manifest`
- ✅ 产出 `final_report`

### Tier 1 - 默认执行（质量保证）
- ✅ 完整的 8 维度 `readiness_report`
- ✅ 结构化 `analysis_plan`（含方法选择理由）
- ✅ 优先调用 ds_skill helpers（失败才降级到手写）

### Tier 2 - 可选执行（高级特性）
- ⚠️ Multi-agent 编排
- ⚠️ Golden templates 匹配

## 具体修复行动

### 修复1：强制 workflow.md 为前置步骤
**位置**：SKILL.md Core Workflow 步骤 1
**改动**：
```markdown
- 改前：1. Read `references/workflow.md`.
+ 改后：1. 🔴 **MANDATORY**: Read `references/workflow.md` and confirm the 7-stage sequence applies to this analysis. Only proceed after loading the workflow structure into context.
```

### 修复2：收紧 Shortcut Routing 规则
**位置**：SKILL.md Shortcut Routing 章节
**改动**：增加明确的触发条件表
```markdown
| 用户请求 | 是否走 shortcut | 理由 |
|---------|----------------|------|
| "全套分析" | ❌ 否 | 执行完整 12 步 |
| "快速看一下数据" | ✅ 是 | profile-only |
| "算个平均值" | ✅ 是 | one-off statistic |
| "分析这个数据" | ❌ 否 | 默认完整流程 |
```

### 修复3：强制 ds_skill 调用检查
**位置**：SKILL.md Core Workflow 步骤 6-7 之间
**新增步骤**：
```markdown
6.5 🔴 **CHECK ds_skill helpers**: For each selected method in analysis_plan, check if a corresponding `ds_skill.*` helper exists (consult "Code Helpers — Lazy Import Map"). If helper exists, MUST attempt to import and call it first. Only fall back to hand-coding if:
   - Import fails after trying the sys.path bootstrap
   - Helper's signature doesn't match this specific use case
   - Helper returns an error after 1 retry
   
   Record in analysis_plan whether each method used a helper or hand-coded, and why.
```

### 修复4：增加执行日志 artifact
**位置**：SKILL.md Required Artifacts 章节
**新增 artifact**：
```markdown
- `execution_log`: Which workflow steps were executed, skipped, or shortcut. For each skipped step, record the reason and decision point. Format: JSON array of {step: number, status: "executed"|"skipped"|"shortcut", reason: string, timestamp: ISO8601}
```

### 修复5：CHECKPOINT 默认行为强化
**位置**：SKILL.md Operating Modes 章节
**改动**：
```markdown
- 改前：`guided` is the default. Proceed automatically, but stop at checkpoints (🔴) for user confirmation on high-impact decisions.
+ 改后：`guided` is the **enforced default** unless user explicitly says "auto mode" or "skip confirmations". At each 🔴 CHECKPOINT, MUST stop and present the decision + evidence + recommendation. Proceeding without stopping is a protocol violation.
```

### 修复6：analysis_plan 强制产出
**位置**：SKILL.md Core Workflow 步骤 9
**改动**：
```markdown
- 改前：9. 🔴 CHECKPOINT (guided mode): present the `analysis_plan` and get user sign-off...
+ 改后：9. **Generate analysis_plan artifact** with this structure:
   ```json
   {
     "claims": [
       {
         "claim": "描述",
         "primary_method": "方法名",
         "rationale": "为什么选这个方法",
         "assumptions": ["假设1", "假设2"],
         "cross_check": "备选方法",
         "helper_ref": "ds_skill.module.function OR null if hand-coded"
       }
     ],
     "rejected_alternatives": [{"method": "X", "reason": "不选的原因"}]
   }
   ```
   🔴 CHECKPOINT (guided mode): present the analysis_plan and get user sign-off before executing.
```

### 修复7：readiness_report 8维强制评分
**位置**：SKILL.md Core Workflow 步骤 4
**改动**：
```markdown
- 改前：4. Build a data profile and readiness assessment before analysis. Use `references/data-readiness.md`.
+ 改后：4. Build a data profile and readiness assessment before analysis. Use `references/data-readiness.md` to score all 8 dimensions:
   1. Sample size adequacy (N per cell)
   2. Missingness pattern (MAR vs MCAR vs MNAR)
   3. Target balance (for classification) or coverage (for regression)
   4. Time/batch coverage (for trend/SPC)
   5. Multicollinearity (VIF < 10)
   6. Leakage (post-outcome columns)
   7. Grain consistency (no mixed aggregation levels)
   8. Outlier burden (% beyond 3 MAD)
   
   Produce `readiness_report` artifact with numeric scores (0-10) for each dimension and overall gate status (ready / narrowable / blocked).
```

### 修复8：增加"为什么不用 ds_skill"的强制提示
**位置**：SKILL.md "Make the helpers importable" 章节后
**新增段落**：
```markdown
### When NOT to use ds_skill helpers

Only hand-code a method if ALL of these conditions are true:
- ✅ No matching helper exists in "Code Helpers — Lazy Import Map"
- ✅ You attempted the sys.path bootstrap and import still failed
- ✅ The helper exists but its signature/assumptions don't fit this specific case

**Default behavior**: If unsure whether a helper exists, check the map first. The 180+ tested functions cover the majority of standard analyses. Preferring hand-coded implementations without checking is a protocol violation.
```

## 同步机制修复

### 问题
当前有两个 SKILL.md 副本：
- 源文件：`plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- 运行时加载：`~/.agents/skills/data-scientist/SKILL.md`

修改源文件后，运行时不会自动更新。

### 解决方案
创建同步脚本 `scripts/sync_skill.sh`：
```bash
#!/usr/bin/env bash
# 将 plugins/ 下的 SKILL.md 同步到 ~/.agents/skills/

SOURCE="plugins/data-scientist/skills/analysis-workflow/SKILL.md"
TARGET="$HOME/.agents/skills/data-scientist/SKILL.md"

if [ ! -f "$SOURCE" ]; then
  echo "错误: 源文件不存在 $SOURCE"
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SOURCE" "$TARGET"
echo "✅ 已同步 SKILL.md 到运行时目录"
echo "   源: $SOURCE"
echo "   目标: $TARGET"
```

## 测试验证计划

### 测试1：workflow.md 强制读取
**场景**：用户说"分析这个数据"
**预期**：Agent 第一步必须输出"Reading references/workflow.md..."

### 测试2：ds_skill 调用
**场景**：需要计算相关性
**预期**：Agent 尝试 `from ds_skill.correlation import pairwise_correlation`，失败后才手写

### 测试3：analysis_plan 产出
**场景**：任何非 one-off 分析
**预期**：步骤9 产出 `analysis_plan.json`，包含 claims 数组和 rejected_alternatives

### 测试4：readiness_report 8维
**场景**：任何数据分析
**预期**：步骤4 产出包含 8 个数值分数的 `readiness_report.json`

### 测试5：execution_log
**场景**：任何分析
**预期**：最终产出 `execution_log.json`，记录 12 步执行情况

## 改进前后对比

### 改进前（审计报告实际执行）
```
用户问题 → 直接手写 4 个 .py → 产出报告
          ↑
          跳过了 workflow、ds_skill、multi-agent、analysis_plan
```

### 改进后（期望执行路径）
```
用户问题
  ↓
🔴 MANDATORY: Read workflow.md
  ↓
步骤 2-3: 数据摄取 + 目标确认
  ↓
步骤 4: readiness (8 维度强制评分) → readiness_report.json
  ↓
🔴 CHECKPOINT: 数据可用性门槛
  ↓
步骤 5-6: shaping + method selection → 查 method-registry.md
  ↓
步骤 6.5: 🔴 CHECK ds_skill helpers（新增）
  ↓
步骤 9: 生成 analysis_plan.json（含 helper_ref 字段）
  ↓
🔴 CHECKPOINT: 展示 analysis_plan
  ↓
步骤 10-11: 执行（优先用 ds_skill） + 交叉验证
  ↓
步骤 12: 产出报告 + charts
  ↓
产出 execution_log.json（新增）
```

## 预期改进效果

| 指标 | 改进前 | 改进后 | 目标 |
|------|--------|--------|------|
| 工作流执行率 | 3/12 (25%) | 10/12 (83%) | ≥80% |
| ds_skill 调用次数 | 0 | ≥5 | ≥3 |
| reference 文档阅读 | 2/9 (22%) | 5/9 (56%) | ≥50% |
| artifacts 完整性 | 2/8 (25%) | 6/8 (75%) | ≥70% |
| 方法选择可追溯性 | ❌ 无 | ✅ 有（analysis_plan） | 必须 |
| CHECKPOINT 执行 | 0/5 | 3/5 | ≥3 |

## 实施优先级

### P0 - 立即修复（阻断性）
1. ✅ 强制 workflow.md 读取（修复1）
2. ✅ analysis_plan 强制产出（修复6）
3. ✅ 同步机制（确保改动生效）

### P1 - 本周完成（重要）
4. ✅ 收紧 Shortcut Routing（修复2）
5. ✅ readiness 8维强制评分（修复7）
6. ✅ ds_skill 调用检查（修复3）

### P2 - 下周完成（增强）
7. ⚠️ execution_log artifact（修复4）
8. ⚠️ CHECKPOINT 强化（修复5）
9. ⚠️ "为什么不用 ds_skill" 提示（修复8）

## 相关文件

- 审计报告：`darwin-results/data-scientist-skill_深度审计报告.md`
- 主 SKILL 文件：`plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- 运行时 SKILL：`~/.agents/skills/data-scientist/SKILL.md`
- 测试场景：`plugins/data-scientist/skills/analysis-workflow/test-prompts.json`
