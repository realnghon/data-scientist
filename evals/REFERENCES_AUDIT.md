# References/Agents/Assets 使用情况分析报告

## 📋 目录状态总览

### 1. `references/` 目录（8个文件）
| 文件 | 最后更新 | 状态 | 使用情况 |
|------|---------|------|----------|
| `workflow.md` | 2026-06-10 | ✅ 活跃 | SKILL.md line 68 强制读取 |
| `data-readiness.md` | 2026-06-11 | ✅ 活跃 | SKILL.md line 72 引用（8维度定义） |
| `method-registry.md` | 2026-06-12 | ✅ 活跃 | SKILL.md line 84 方法选择 |
| `manufacturing-playbook.md` | 2026-06-12 | ✅ 活跃 | SKILL.md line 85 制造领域 |
| `chart-catalog.md` | 2026-06-03 | ⚠️ 较旧 | SKILL.md line 127 图表要求 |
| `data-shaping.md` | 2026-06-02 | ⚠️ 较旧 | SKILL.md line 83 数据重塑 |
| `report-standard.md` | 2026-06-02 | ⚠️ 较旧 | SKILL.md line 127 报告结构 |
| `golden-templates.md` | 2026-06-02 | ⚠️ 较旧 | SKILL.md line 38 模板匹配 |

**总体状态**：✅ **核心有效，部分需更新**

### 2. `agents/` 目录（1个文件）
| 文件 | 最后更新 | 状态 | 使用情况 |
|------|---------|------|----------|
| `openai.yaml` | 2026-05-30 | ❓ 未知 | OpenAI接口配置，无引用 |

**总体状态**：❓ **不清楚用途**

### 3. `assets/` 目录（1个文件）
| 文件 | 最后更新 | 状态 | 使用情况 |
|------|---------|------|----------|
| `report_template.md` | 2026-05-30 | ⚠️ 未使用 | SKILL.md 无引用 |

**总体状态**：⚠️ **未被使用**

---

## 🔍 详细分析

### References 目录：**核心知识库，被充分使用**

**实际作用**：
1. **Lazy Load 设计**（SKILL.md line 29-42）
   - Agent 根据任务类型**按需读取** references
   - 避免所有文档预加载导致 context 爆炸
   - 8个文件对应8种分析场景

2. **被引用统计**：
   ```
   workflow.md:          ✅ 强制读取（line 68）
   data-readiness.md:    ✅ 8维度定义（line 72）
   method-registry.md:   ✅ 方法选择（line 84）
   manufacturing-playbook: ✅ 制造领域（line 85）
   chart-catalog.md:     ✅ 图表要求（line 127）
   data-shaping.md:      ✅ 数据重塑（line 83）
   report-standard.md:   ✅ 报告结构（line 127）
   golden-templates.md:  ✅ 模板匹配（line 38）
   ```

3. **最近更新的文件**（2026-06-10 ~ 06-12）：
   - `workflow.md`：工作流定义
   - `data-readiness.md`：8维度评估（**刚在评测中强化**）
   - `method-registry.md`：方法注册表（**新增SPC/Simpson规则**）
   - `manufacturing-playbook.md`：制造领域手册

**为什么 references 没有全部更新？**
- **部分文件已稳定**：`chart-catalog.md`（39种图表）、`data-shaping.md`（长宽转换规则）等是**基础设施**，不需要频繁改动
- **按需优化原则**：只有当评测发现该领域缺陷时才更新
- **最近3轮迭代聚焦**：统计显著性（Gate 4）、规格合理性（Gate 6）、SPC规则（method-registry）

**是否需要更新？**
- ✅ **核心4个已更新**：workflow、data-readiness、method-registry、manufacturing-playbook
- ⚠️ **其他4个可能需要审查**：
  - `chart-catalog.md`：是否缺少新图表类型？
  - `data-shaping.md`：是否缺少新的重塑模式？
  - `report-standard.md`：报告模板是否需要强化？
  - `golden-templates.md`：是否需要新的分析模板？

---

### Agents 目录：**用途不明**

**内容**：只有 `openai.yaml`（OpenAI 接口配置）

**问题**：
- SKILL.md 无引用
- 评测未使用
- 最后更新：2026-05-30（初始化后未修改）

**可能用途**：
1. OpenAI 兼容的 API 配置（如使用 OpenAI 模型而非 Claude）
2. 历史遗留文件（Claude Code 迁移前的残留）

**建议**：
- ❓ 如果项目不支持 OpenAI 模型，可删除
- ❓ 如果有用，需要文档说明其用途

---

### Assets 目录：**未被使用**

**内容**：只有 `report_template.md`（报告模板）

**问题**：
- SKILL.md 无引用（line 127 引用的是 `references/report-standard.md`）
- 评测未使用
- 最后更新：2026-05-30（初始化后未修改）

**可能原因**：
1. **设计变更**：早期设计用 `assets/report_template.md`，后来改用 `references/report-standard.md`
2. **功能重复**：两个文件都是报告模板，但只用了 `references/` 下的

**验证**：
```bash
# report_template.md 从未被引用
grep -r "assets/report_template" plugins/data-scientist/skills/analysis-workflow/SKILL.md
# (无输出)

# 实际使用的是 report-standard.md
grep -r "report-standard" plugins/data-scientist/skills/analysis-workflow/SKILL.md
# Use `references/report-standard.md` for report structure.
```

**建议**：
- ⚠️ 如果 `assets/report_template.md` 已废弃，应删除
- ⚠️ 或者迁移内容到 `references/report-standard.md`

---

## 🎯 为什么评测只更新 SKILL.md？

### 原因分析

**1. SKILL.md 是"大脑"，references 是"知识库"**
```
SKILL.md (控制流)
   ├── Gate 1-6（执行规则）
   ├── 何时读取 references（调度规则）
   └── 产物要求（质量门禁）

references/ (领域知识)
   ├── 方法选择逻辑（method-registry）
   ├── 数据质量标准（data-readiness）
   └── 工作流步骤（workflow）
```

**2. 最近3轮迭代的缺陷类型**
| 轮次 | 发现的问题 | 修复位置 | 原因 |
|------|-----------|---------|------|
| R1 | 统计显著性误用 | SKILL.md Gate 4 | **执行规则**不足 |
| R2 | 规格合理性缺失 | SKILL.md Gate 6 | **质量门禁**缺失 |
| R3 | SPC分层规则 | method-registry.md | **领域知识**补充 |

**结论**：前2轮是**控制流问题**（Gate规则），只需改 SKILL.md；第3轮是**知识库问题**，才更新 references。

**3. References 的"按需更新"机制**
- 如果评测失败是因为"不知道该用什么方法" → 更新 `method-registry.md`
- 如果评测失败是因为"方法选对了但没执行" → 更新 SKILL.md Gate

**4. 当前9个case覆盖的领域**
- ✅ **已覆盖**：回归、A/B、SPC、时序、Simpson、RCA
- ✅ **已验证的 references**：method-registry、manufacturing-playbook、data-readiness
- ⚠️ **未充分测试**：chart-catalog（图表覆盖度）、golden-templates（模板匹配）

---

## 📋 建议的更新优先级

### 优先级1：审查未更新的 references（4个文件）
```bash
# 检查这4个文件是否需要更新
1. chart-catalog.md (2026-06-03)
   - 验证：9个case的图表是否覆盖catalog中的"最小必需图表"
   - 如果有case缺少必需图表但未被扣分 → catalog定义不足

2. data-shaping.md (2026-06-02)
   - 验证：case-09的 join+pivot 是否符合 shaping 规则
   - 如果有重塑模式未被catalog覆盖 → 需补充

3. report-standard.md (2026-06-02)
   - 验证：9个case的报告结构是否一致
   - 如果报告质量参差不齐 → standard不够明确

4. golden-templates.md (2026-06-02)
   - 验证：case-01/02/04/05/09 是否匹配到了模板
   - 如果模板匹配率低 → 需补充新模板
```

### 优先级2：清理无用文件
```bash
# 删除或明确用途
1. agents/openai.yaml
   - 如果不支持 OpenAI → 删除
   - 如果支持 → 添加文档说明

2. assets/report_template.md
   - 如果已废弃 → 删除
   - 如果有用 → 迁移内容到 references/report-standard.md
```

### 优先级3：扩展评测覆盖（验证 references 完整性）
```bash
# 新增case测试未充分验证的 references
1. 测试 chart-catalog 覆盖度
   - 新增 case-10：要求生成 catalog 中的所有图表类型

2. 测试 golden-templates 匹配率
   - 新增 case-11：明确匹配某个template（如"yield drop RCA"）

3. 测试 data-shaping 复杂度
   - 新增 case-12：需要多次 join + pivot + aggregate
```

---

## 🎯 总结

### References 目录
- **状态**：✅ 核心有效，4/8已更新（workflow、data-readiness、method-registry、manufacturing-playbook）
- **使用情况**：✅ 被 SKILL.md 充分引用，按需读取机制正常
- **是否需要更新**：⚠️ 剩余4个文件（chart-catalog、data-shaping、report-standard、golden-templates）可能需要审查

### Agents 目录
- **状态**：❓ 用途不明，只有 openai.yaml
- **使用情况**：❌ SKILL.md 无引用，评测未使用
- **建议**：删除或添加文档说明

### Assets 目录
- **状态**：⚠️ 未被使用，report_template.md 已被 references/report-standard.md 替代
- **使用情况**：❌ SKILL.md 无引用
- **建议**：删除或迁移内容到 references/

### 为什么只更新 SKILL.md？
- ✅ **合理**：前2轮缺陷是执行规则问题（Gate 4/6），只需改 SKILL.md
- ✅ **按需机制**：第3轮发现知识库缺失（SPC规则），才更新 method-registry
- ✅ **效率优先**：先修"大脑"（控制流），再补"知识库"（领域知识）

**结论**：References 是活跃且有效的，但需要审查未更新的4个文件。Agents 和 Assets 目录可能需要清理。
