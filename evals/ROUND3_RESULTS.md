# Round 3: 数据修复后意外下降

## 结果

| Round | Score | 主要改进 | 主要问题 |
|-------|-------|---------|---------|
| 1 | 33.3 | - | 统计显著性误用 |
| 2 | 39.2 | +5.9 (anti-gaming) | 数据信号弱 |
| 3 | **33.3** | -5.9 ❌ | 报告格式 + GT 遗漏 |

## 数据修复成功但分数下降

### 数据修复验证 ✅
- cd_nm 信号：p=0.37 → p=2.2e-43（极强）
- Agent 正确识别：Chamber C2 → cd_nm 机制（p<0.001）
- 所有 Gate 通过

### 但 Judge 评分下降 ❌

**根本原因**：报告质量问题 + GT 期望不匹配

**Defects（15 个）**：
1. **Anti-gaming (3)**：表格数据重复，yield vs cd_nm 标签混淆
2. **Completeness (4)**：遗漏 recipe 拒绝、same_event leakage 标记
3. **Correctness (4)**：数据展示矛盾，recipe 测试缺失
4. **Rigor (4)**：统计前提未检查（正态性、方差齐性）

## 关键洞察

### 1. 数据修复 ≠ 分数提升

数据信号修复只解决了**必要条件**，但：
- 报告格式规范
- Ground truth 完整性
- 统计方法严谨性

都是**充分条件**，缺一不可。

### 2. GT 期望过于具体

Ground truth 要求：
- `recipe_waiting_noise_rejected`（负向结论）
- `same_event_features_flagged`（泄漏标记）

但这些是**实现细节**，不应作为 correctness 硬要求。

建议：GT 应专注**核心发现**（chamber + 机制），而非强制特定负向结论或质量检查名称。

### 3. Skill 需要格式规范

Agent 报告存在：
- 表格复制粘贴错误
- 变量标签不一致
- 统计前提检查缺失

需要在 Skill 中增加**输出质量检查清单**。

## 下一步修复方案

### 优先级 1：Skill 改进（最快见效）

**1. 报告生成检查**（Gate 7）：
- 禁止表格复制粘贴（每个表格必须从原始数据重新生成）
- 强制变量标签一致性检查
- 数值交叉验证（yield vs cd_nm 范围合理性）

**2. 统计前提检查**（加强 rigor）：
- ANOVA 前：Shapiro-Wilk + Levene's test
- Pearson 前：linearity scatter plot + Q-Q plot
- 如违反：明确说明并使用非参数替代

**3. 负向结论模板**：
```markdown
## Tested But Rejected

- recipe: p=0.89 (Kruskal-Wallis), no effect on yield
- waiting_time: p=0.67, no correlation with yield
- **Verdict**: Both variables rejected as drivers
```

### 优先级 2：GT 简化（宽容性）

将以下从 **required findings** 降级为 **optional quality checks**：
- `recipe_waiting_noise_rejected` → 如果 agent 未明确测试，不扣 correctness
- `same_event_features_flagged` → 仅在 agent 声称检查泄漏时要求

**核心要求**：
- Chamber C2 根因（必需）
- cd_nm 机制（必需）
- 数据转换（必需）

### 优先级 3：Judge 校准

当前 judge 可能过严。考虑：
- 降低 completeness 权重（3.0 → 2.0）
- 提高 correctness 权重（5.0 → 6.0）
- 对格式错误给予 warning 而非 failure

## 预期效果

实施上述修复后：
- **Skill 改进**：rigor 1→2, anti-gaming 1→2 (+2 维度)
- **GT 简化**：completeness 1→2 (+1 维度)
- **总分预期**：33.3 → 55-65

还需 2-3 轮迭代才能达到 90+。

## 飞轮状态

✅ 数据验证环节有效
⚠️ 但暴露新问题：报告质量 + GT 过严

**需要迭代的方面**：
1. 数据信号（已修复）
2. Skill 统计方法（部分修复）
3. **报告格式规范**（待修复）⬅️ 新发现
4. **GT 合理性**（待调整）⬅️ 新发现

飞轮仍在运转，但饱和路径比预期更长。
