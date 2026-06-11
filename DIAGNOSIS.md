# 诊断报告：为什么只改 SKILL.md 而不更新 agents/commands

## 问题根源

评测系统运行时，spawned agent **没有调用** `agents/` 下的子 agent，而是**自己完成所有工作**。

### 证据

1. **case-09 L2 评测成功（100分）**
   - Agent 产出了所有必需的 artifacts
   - 但整个过程是**单个 agent** 完成的，没有 spawn `ds-intake-agent`, `ds-readiness-agent` 等

2. **SKILL.md 的模糊指令**
   ```markdown
   | `multi-agent-orchestration.md` | ... you plan to spawn sub-agents. | ...
   ```
   - "you **plan to** spawn" ≠ "you **must** spawn"
   - Agent 选择了不 spawn 的路径

3. **设计意图 vs 实际行为**
   - **设计意图**（multi-agent-orchestration.md）：7 stage pipeline，每个 stage spawn 对应的子 agent
   - **实际行为**：单个 agent 通过 `ds_skill` helpers 完成所有工作

### 为什么 agents/ 和 commands/ 没被更新

- `agents/ds-intake-agent.md` 等文档定义了子 agent 的行为
- 但如果主 agent 不 spawn 子 agent，这些文档就**不会被加载到 context**
- 结果：修复只能针对 SKILL.md，因为只有它被加载了

## 双轨设计的矛盾

系统存在两条路径：

### 路径 A：多 agent 编排（设计意图）
```
main agent (读 SKILL.md)
  ↓ spawn
ds-intake-agent (读 agents/ds-intake-agent.md)
  ↓ spawn
ds-readiness-agent (读 agents/ds-readiness-agent.md)
  ↓ spawn
...
```

### 路径 B：单 agent 自完成（实际行为）
```
main agent (读 SKILL.md)
  ↓ 直接调用 ds_skill helpers
完成所有 7 stages
```

**当前 SKILL.md 同时支持两条路径，但没有明确何时必须选择路径 A。**

## 修复方案

### 优先级 1：强制多 agent 编排（高风险）

在 SKILL.md **Non-Negotiable Gates** 中增加：

```markdown
7. **Multi-stage analysis MUST use sub-agent orchestration.** When route is `full` or 
   `named-method` (not one-off/profile-only), you MUST spawn the following sub-agents 
   via Agent tool instead of executing stages inline:
   - ds-intake-agent (stage 1)
   - ds-readiness-agent (stage 2)
   - ds-shaping-agent (stage 3, may spawn multiple)
   - ds-method-planner-agent (stage 4)
   - ds-execution-agent (stage 5, may spawn multiple)
   - ds-critic-agent (stage 6)
   - ds-report-agent (stage 7)
   
   See references/multi-agent-orchestration.md for dispatch patterns. Only inline 
   execution is allowed for one-off statistics or profile-only routes.
```

**风险**：
- 大幅改变行为，可能导致其他 case 失败
- 子 agent 文档可能存在过时/错误的指令
- Token 成本显著上升（7 个子 agent vs 1 个主 agent）

### 优先级 2：统一为单 agent 路径（低风险，推荐）

**删除**多 agent 编排设计，将所有指令整合到 SKILL.md + references：

1. **废弃 `agents/` 目录**
   - 将各 agent 的关键指令合并到对应的 reference 文档
   - `agents/ds-intake-agent.md` → `references/workflow.md` Stage 1
   - `agents/ds-readiness-agent.md` → `references/data-readiness.md`
   - ...

2. **简化 multi-agent-orchestration.md**
   - 重命名为 `workflow-execution-patterns.md`
   - 只保留**并行化提示**（哪些 stage 可以并行），删除 spawn 指令

3. **更新 `commands/` 下的文档**
   - `commands/ds-analyze.md` 保持不变（它只是入口点）
   - 其他 commands 如果存在，改为直接引用 SKILL.md 的对应 section

**优点**：
- 与当前实际行为一致（case-09 已证明可行）
- 降低复杂度，减少需要维护的文档数量
- 减少 token 成本
- 更容易调试（所有逻辑在一个 agent 的 context 内）

**缺点**：
- 失去真正的多 agent 并行能力（但当前也没用上）
- 单个 agent context 可能很大（但 reference lazy load 已缓解）

### 优先级 3：混合模式（中等风险）

保留多 agent 能力，但作为**可选优化**，不作为强制要求：

1. **默认路径**：单 agent 完成（当前行为）
2. **可选优化**：在 SKILL.md 中增加 section：
   ```markdown
   ## Performance Optimization: Multi-Agent Dispatch
   
   For large datasets (>10 files or >1M rows) or complex analyses (>3 methods), 
   consider spawning sub-agents per stage to parallelize work and manage context. 
   See references/multi-agent-orchestration.md for patterns.
   
   When NOT to spawn: simple analyses, single file, <50k rows, or when debugging.
   ```

3. **保持 `agents/` 文档同步**：在每次修改 SKILL.md/references 后，同步更新对应的 agent 文档

**风险**：
- 维护负担最大（两套路径都要保持正确）
- 容易出现不一致

## 推荐行动

**立即执行**：优先级 2（统一为单 agent 路径）

**理由**：
1. **已验证可行**：case-09 获得 100 分，证明单 agent 路径有效
2. **复杂度最低**：减少需要维护的文档和调试难度
3. **风险最小**：与当前实际行为一致，不会破坏已有功能
4. **迭代效率最高**：修复只需关注 SKILL.md + references，不用同步多处

**后续可选**：在单 agent 路径饱和（所有 case 90+）后，再考虑引入多 agent 并行作为性能优化。

## 下一步：系统性评测

在执行修复前，先完成**所有 9 个 case 的 L2 评测**：

1. 跑完所有 case，记录分数
2. 找出失败的 case，分析失败模式
3. 根据失败模式决定修复优先级：
   - 如果都是 SKILL.md/references 的问题 → 优先级 2
   - 如果需要真正的多 agent 并行 → 优先级 1 或 3
   - 如果是 ground truth 问题 → 先修 GT

**目标**：用数据驱动决策，而不是假设。
