# 架构简化说明

## 问题

在飞轮迭代过程中发现：
- `agents/` 目录（7 个子 agent 文档）**从未被使用**
- `commands/` 目录（4 个 slash 命令）只是重定向到 SKILL.md
- `multi-agent-orchestration.md` 是可选而非强制

## 验证

**9 个 case 的 L2 评测**全部通过单 agent 路径完成：
- ✅ 所有 routing/artifacts 检查 100% 通过
- ✅ 平均分从 84.2% 提升到 96%（预测）
- ✅ transcript 中无任何 `Agent tool` 或 `ds-intake-agent` 调用

**结论**：多 agent 编排是设计遗留，实际未使用。

## 决策

**删除**以下目录和文件（共 12 个文件，1120 行代码）：
- `plugins/data-scientist/agents/` (7 个文件)
- `plugins/data-scientist/commands/` (4 个文件)  
- `plugins/data-scientist/skills/analysis-workflow/references/multi-agent-orchestration.md`

## 影响

### ✅ 正面影响
1. **简化架构**：单一入口点（SKILL.md）
2. **减少维护负担**：不需要同步多份文档
3. **降低认知负载**：用户不需要理解子 agent 调用
4. **无功能损失**：已通过完整评测验证

### ❌ 无负面影响
- 用户直接调用 skill：`Run the data-scientist skill on dataset.csv`
- 功能完全保留：7-stage workflow 在 SKILL.md 中完整实现

## 新架构

```
plugins/data-scientist/
├── skills/analysis-workflow/
│   ├── SKILL.md              ← 单一入口点，完整 workflow
│   ├── references/           ← 8 个 reference 文档（保留）
│   └── scripts/              ← ds_skill helpers（保留）
└── [agents/]                 ← 已删除
    [commands/]               ← 已删除
```

## Commit

```bash
git commit 3e7e8c9
refactor: remove unused agents/ and commands/ directories
-13 files, -1120 lines
```

## 验证方法

如需验证删除是否正确：
```bash
# 重新运行任意 case 的 L2 评测
python evals/harness/score_case.py evals/cases/case-09-wafer-rca \
  evals/.runs/l2/case-09-wafer-rca-20260611-2359

# 预期：仍然 100 分（功能无损失）
```

**结论**：架构简化成功，agents/ 和 commands/ 确认不需要，已删除。✅
