# Data Scientist Skill Changelog

This file tracks major changes to the `data-scientist` skill structure and behavior.

## Format

```
## [version] - YYYY-MM-DD
### Added
- New features or capabilities
### Changed
- Modifications to existing behavior
### Fixed
- Bug fixes or corrections
### Removed
- Deprecated features
```

---

## [2.1.0] - 2026-06-22

### Changed
- **SKILL.md 重构为 router**：删除 15 步内嵌流程清单（与 workflow.md 三处重复），改为 Gates + Modes + Pipeline 指针 + Required Artifacts 表 + Lazy Load Map + Human-in-the-Loop。SKILL.md 不再承载流程定义，workflow.md 成为唯一流程 SSoT。107 → 78 行。
- **Gates 收敛从 6 → 6 但语义重构**：移除制造业偏置的 Gate 6 (Spec/unit sanity，落入 readiness 的 measurement_reliability 维度，属 no-op)；新增 _ready_ / _planned_ / _critiqued_ 三个状态门，把"artifact 必须 exist before next stage"从嵌入式步骤显式化为 gates，与 _routed_ / _red_ / _rigorous_ 一致使用 leading word。
- **workflow.md 压缩为唯一流程 SSoT**：删除 inline ToC、3-level fallback 表的冗余列、Anti-Patterns 末段（指向 anti-patterns.md）、When To Skip Stages（指向 branch-routing.md）、散落的 parallelization hint 提示。241 → 150 行。
- **anti-patterns 单一真源化**：data-readiness.md / data-shaping.md / method-registry.md 三处 inline anti-patterns 表全部删除，改为 "Checkpoints" 表 + 指向 anti-patterns.md。
- **multi-agent-orchestration.md 平台收敛**：8 个平台逐段描述 → 2 类 runtime（Claude Code 原生 fan-out / 其余顺序执行），删除 6 段重复的 sequential 说明。290 → 128 行。
- **7 个 agent 文档去重**：每个 agent 不再逐字重复完整 envelope 契约（5 个共享键 ×7 = 35 处重复），改为"Stage-specific inputs/produced"+ 指向 multi-agent-orchestration.md 的共享 envelope。description 从啰嗦的"Typical triggers include... See When to invoke section"压缩为单句 leading word 触发式。891 → 572 行。

### Removed
- SKILL.md Gate 6 (Spec/unit sanity) — 属 readiness measurement_reliability 维度的 no-op 重复。
- SKILL.md ## Domain — Financial Time Series 段 — 已在 Lazy Load Map 表项覆盖，重复。
- SKILL.md ## Safety — 记录 transformations/seeds/versions 是默认行为，no-op。
- SKILL.md ## Anti-Patterns — 与 workflow.md / anti-patterns.md 三重重复，收敛为一行 checkpoint 提示。
- SKILL.md 15 步 Core Workflow — 与 workflow.md 7 阶段完全重叠。
- workflow.md inline anti-patterns 段、When To Skip Stages 段。
- data-readiness.md / data-shaping.md / method-registry.md 内嵌 anti-patterns 表。
- multi-agent-orchestration.md 6 段单平台 sequential 重复描述、Section 5 完整 worked example（290→128 行瘦身）。

### Fixed
- agents/*.md 中对 references/ 与 SKILL.md 的相对路径全部错误（写成 `../references/` 实际应为 `../skills/analysis-workflow/references/`），批量修正并通过断链校验。

---

## [2.0.0] - 2026-06-22

### Changed
- **SKILL.md rewritten**: Reduced from 285 lines to 110 lines (61% reduction). Introduced leading words (_gate_, _tri-score_, _routed_, _rigorous_, _downgrade_, _red_, _checkpoint_) for predictability and token efficiency.
- **Description collapsed**: From ~90-word dense paragraph to 4 branching triggers with leading words, ≤30 words.
- **Steps re-numbered**: Eliminated patch numbering (13.5, 14.5) → continuous 1-15. Added checkable completion criteria for every step.
- **Duplication eliminated**: 6 SSoT violations removed — readiness dimension table, anti-patterns summary, failure recovery table, shortcut routing detail, helper import code block, analysis_plan JSON template all pushed to dedicated references.
- **No-ops removed**: Motivation paragraphs ("Why this matters"), explanatory sentences, redundant emphasis all deleted.
- **workflow.md deduplicated**: Removed inline anti-patterns table → pointer to anti-patterns.md; removed "When To Skip Stages" → pointer to branch-routing.md.
- **report-standard.md deduplicated**: Removed inline report anti-patterns table → pointer to anti-patterns.md; Tier-1 definition now explicitly references Gate 4 in SKILL.md.

### Added
- `references/analysis-plan-template.md`: JSON template for analysis_plan artifact (extracted from SKILL.md)
- `references/helper-bootstrap.md`: Import-path bootstrap, module catalog, and environment policy (extracted from SKILL.md)
- `references/advanced-techniques.md`: Interaction/confounding checks, categorical noise factors, root-cause tracing, A/B multi-metric (extracted from SKILL.md steps 13/13.5/14/14.5)
- `references/branch-routing.md`: Shortcut routing rules, trigger conditions, boundary rules (extracted from SKILL.md)

### Removed
- Inline readiness dimension table (now SSoT in data-readiness.md)
- Inline anti-patterns summary paragraph (now SSoT in anti-patterns.md)
- Inline failure recovery table (now SSoT in failure-recovery.md)
- Inline shortcut routing detail (now in branch-routing.md)
- Inline helper import code block and module catalog (now in helper-bootstrap.md)
- Inline analysis_plan JSON template (now in analysis-plan-template.md)
- Inline advanced technique instructions (now in advanced-techniques.md)
- workflow.md inline anti-patterns table (replaced by pointer)
- workflow.md "When To Skip Stages" table (replaced by pointer)
- report-standard.md inline anti-patterns table (replaced by pointer)

---

## [1.2.0] - 2025-06-16

### Changed
- **Agent descriptions enhanced**: All 7 agents now follow agent-development best practices with "Typical triggers include" examples and specific user query scenarios
- **Agent "When to invoke" sections**: Converted all "Trigger" sections to "When to invoke" with 2-4 concrete usage scenarios in prose format
- **Command argument hints improved**: Added specific examples and clearer parameter format for all 4 commands (ds-analyze, ds-plan, ds-profile, ds-report)

### Added
- Usage examples in all command files showing typical invocations
- Detailed scenario descriptions in all agent "When to invoke" sections

---

## [1.1.0] - 2025-06-16

### Changed
- **Description format**: Rewritten to third-person format ("This skill provides..." instead of "Use when...") per skill-development best practices
- **Skill length optimization**: Reduced SKILL.md from 6,591 to ~5,600 words by extracting detailed content to references/
- **Progressive disclosure enhancement**: Added 3 new reference documents for better context management

### Added
- `references/anti-patterns.md`: Complete catalog of statistical failure modes with recovery actions (extracted from SKILL.md)
- `references/failure-recovery.md`: Comprehensive stage failure recovery strategies (extracted from SKILL.md)
- `references/financial-domain.md`: Specialized rules for financial time series analysis (extracted from SKILL.md)
- Lazy-load table entries for the 3 new reference documents

### Fixed
- Path portability: All hardcoded relative paths in commands/ and agents/ now use `${CLAUDE_PLUGIN_ROOT}` variable
- openai.yaml relocated from skills/analysis-workflow/agents/ to .codex-plugin/ for better organization

---

## [1.0.0] - 2025-06-16

### Baseline Release
- Complete 7-stage analysis pipeline (intake → readiness → shaping → method-planner → execution → critic → report)
- 6 non-negotiable gates for evidence quality
- 3 operating modes (guided, auto, exploratory)
- 9 reference documents with lazy-load map
- 17 code helper modules with lazy-import map
- Manufacturing-grade methods (SPC, MSA, DOE)
- 3-tier evidence framework (reliable, directional, unsupported)
- 8-dimension data readiness assessment
- Anti-patterns blacklist
- Shortcut routing for simple queries

---

## Versioning Policy

**When to bump version:**
- **Patch (1.0.x)**: Bug fixes, typo corrections, minor clarifications that don't change behavior
- **Minor (1.x.0)**: New methods added, new reference docs, expanded capabilities, non-breaking changes
- **Major (x.0.0)**: Breaking changes to workflow structure, gate requirements, or output contracts

**Sync with plugin version:** When skill version changes, consider whether plugin version should also bump.

---

## Change Tracking

To add an entry:
1. Add a new `## [version]` section at the top (below this section)
2. Use ISO date format (YYYY-MM-DD)
3. Group changes by type (Added/Changed/Fixed/Removed)
4. Be specific about what changed and why
5. Update the `version:` field in SKILL.md frontmatter to match

Example:
```markdown
## [1.1.0] - 2025-07-01
### Added
- New `ds_skill.forecasting` module for time series prediction
- Golden template for demand forecasting analysis
### Changed
- Readiness gate: sample size threshold lowered to 20/cell for exploratory mode
### Fixed
- Typo in method-registry.md Welch's t-test description
```
