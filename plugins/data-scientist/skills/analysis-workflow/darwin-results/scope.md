# Darwin 优化范围

## 评估组件清单

### 1. 核心 SKILL.md
- `plugins/data-scientist/skills/analysis-workflow/SKILL.md` (已读取)

### 2. References (9个文档)
- `references/workflow.md`
- `references/multi-agent-orchestration.md`
- `references/data-readiness.md`
- `references/data-shaping.md`
- `references/method-registry.md`
- `references/chart-catalog.md`
- `references/report-standard.md`
- `references/golden-templates.md`
- `references/manufacturing-playbook.md`

### 3. Agents (7个子agent定义)
- `agents/ds-intake-agent.md`
- `agents/ds-readiness-agent.md`
- `agents/ds-shaping-agent.md`
- `agents/ds-method-planner-agent.md`
- `agents/ds-execution-agent.md`
- `agents/ds-critic-agent.md`
- `agents/ds-report-agent.md`

### 4. Commands (4个命令入口)
- `commands/ds-analyze.md`
- `commands/ds-plan.md`
- `commands/ds-profile.md`
- `commands/ds-report.md`

### 5. Scripts Docstrings (待评估)
- `scripts/ds_bootstrap.py`
- `scripts/profile_dataset.py`
- `scripts/run_full_workflow.py`
- `scripts/ds_skill/*.py` (13个分析模块)

## 评估策略

**优先级排序**（按对用户体验的影响）：
1. **P0** - SKILL.md（主入口，所有agent都会读）
2. **P0** - workflow.md + multi-agent-orchestration.md（流程骨架）
3. **P1** - 7个 agents（实际执行者）
4. **P1** - method-registry.md + data-readiness.md（决策核心）
5. **P2** - 其他 references（专项指南）
6. **P2** - commands（用户命令入口）
7. **P3** - scripts docstrings（代码可读性）

每个组件独立评分，按 Darwin 9维度 rubric。
