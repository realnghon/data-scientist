# Phase 2 并行优化任务分配

## 优化策略

使用 pipeline 模式：每个组件独立优化，互不依赖，可以完全并行。

## 批次 1: P0 核心 References（5个文件）

| Agent ID | 组件 | 当前分 | 目标分 | 优化重点 |
|---------|------|--------|--------|---------|
| opt-workflow | workflow.md | 60.9 | 70+ | +frontmatter, +🔴标记, +反例黑名单 |
| opt-multi-agent | multi-agent-orchestration.md | 63.9 | 72+ | +frontmatter, +🔴标记 |
| opt-method | method-registry.md | 60.0 | 70+ | +frontmatter, +🔴标记, +检查点 |
| opt-readiness | data-readiness.md | 60.9 | 70+ | +frontmatter, +🔴标记, +反例 |
| opt-shaping | data-shaping.md | 59.7 | 70+ | +frontmatter, +🔴标记, +反例 |

## 批次 2: P1 专项 References（4个文件）

| Agent ID | 组件 | 当前分 | 目标分 | 优化重点 |
|---------|------|--------|--------|---------|
| opt-chart | chart-catalog.md | 56.1 | 68+ | +frontmatter, +🔴标记, +失败模式, +反例 |
| opt-report | report-standard.md | 55.5 | 68+ | +frontmatter, +🔴标记, +失败模式, +反例 |
| opt-golden | golden-templates.md | 60.1 | 70+ | +frontmatter, +🔴标记, +反例 |
| opt-mfg | manufacturing-playbook.md | 60.7 | 70+ | +frontmatter, +🔴标记 |

## 批次 3: SKILL.md（1个文件，高质量基线）

| Agent ID | 组件 | 当前分 | 目标分 | 优化重点 |
|---------|------|--------|--------|---------|
| opt-skill | SKILL.md | 66.4 | 75+ | 强化 Dim4 检查点(+🔴), Dim5 去软化措辞 |

## 统一优化指令模板

每个 agent 执行：
1. 读取原文件
2. 应用 Darwin rubric 9 维度优化：
   - Dim1: 添加 frontmatter（name, description, triggers）
   - Dim4: 在所有 Stop/Gate/决策点前加 🔴/🛑 标记
   - Dim5: 去除"建议/可以考虑/根据情况"等软化措辞
   - Dim9: 补充"不要做什么"反例黑名单章节
3. 保存优化后文件
4. Git commit
5. 返回优化摘要（改了什么、预估新分数）

## 并行执行计划

**第一波（5 个 P0 并行）** → 等全部完成 → **第二波（4 个 P1 并行）** → 等全部完成 → **第三波（1 个 SKILL.md）**

总共 10 个文件，3 波并行，预计 10-15 分钟完成。
