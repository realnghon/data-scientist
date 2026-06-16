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
