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
