# Data Scientist

Data Scientist is a production-grade, cross-platform AI plugin for rigorous structured data analysis. Starting with manufacturing analytics, it generalizes to operational datasets across domains with evidence-backed statistical rigor.

**Version:** 1.2.0 | **License:** MIT | **Status:** Production Ready

## What It Provides

### Core Components

- **Top-level `data-scientist` skill** — Full-cycle analysis pipeline (intake → readiness → shaping → method planning → execution → critic → report) with 6 non-negotiable quality gates
- **7 staged subagents** — Autonomous agents for each pipeline stage with precise triggering and clear responsibilities
- **4 slash commands** — `/ds-analyze`, `/ds-profile`, `/ds-plan`, `/ds-report` for interactive workflows
- **Tested Python library** — `ds_skill` with 180+ unit tests, 17 analysis modules, and 21 chart functions
- **12 reference documents** — Progressive disclosure architecture with method registry, anti-patterns, failure recovery, domain playbooks

### Key Features

✅ **Statistical Rigor** — 3-tier evidence framework (reliable/directional/unsupported), mandatory cross-checks, anti-pattern blacklist  
✅ **Manufacturing Grade** — SPC, MSA, DOE, Cpk, control charts, process capability analysis  
✅ **Financial Domain Support** — Time series analysis, returns vs price levels, stationarity checks, target-derived feature detection  
✅ **Progressive Disclosure** — Lazy-load references to keep context lean while preserving depth  
✅ **Multi-Platform** — Works across Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, Gemini CLI  
✅ **Path Portable** — 100% `${CLAUDE_PLUGIN_ROOT}` usage for marketplace compatibility

## Install

### Claude Code (Recommended)

```bash
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

### Manual Installation

For per-runtime manual paths and local development, see [`../../INSTALL.md`](../../INSTALL.md).

### Standalone Usage

To use the skill as reference material without installing:
```bash
cat skills/analysis-workflow/SKILL.md
```

## Quick Start

### Profile a Dataset
```bash
/ds-profile data.csv
```

### Full Analysis
```bash
/ds-analyze sales.xlsx "what drives revenue?"
```

### Create Analysis Plan
```bash
/ds-plan "compare treatment vs control" conversion_rate
```

### Generate Report
```bash
/ds-report ./analysis_output
```

## Core Workflow

The plugin follows a 7-stage quality-gated pipeline:

1. **Intake** — Inspect data structure, grain, field roles, and schema
2. **Readiness** — 8-dimension assessment (sample size, missingness, grain, time coverage, class balance, leakage, variable roles, measurement reliability)
3. **Shaping** — Transform to analysis-ready views (pivots, aggregations, time windows)
4. **Method Planning** — Select defensible statistical methods, document rejected alternatives
5. **Execution** — Run reproducible code, save structured outputs and charts
6. **Critic** — Challenge claims for weak evidence, leakage, confounds, method mismatches
7. **Report** — User-facing markdown with executive answer, evidence matrix, limitations

Each stage has a dedicated subagent with precise triggering conditions and clear output contracts.

## Quality Standards

### Non-Negotiable Gates

1. ✅ Route analysis type first (full/profile-only/named-method/one-off/blocked)
2. ✅ `data_manifest` + `readiness_report` + `analysis_plan` must exist before execution
3. ✅ `evidence_matrix` + `critique` must exist before final report
4. ✅ Tier-1 claims require: p < 0.05 + effect size + CI + cross-check agreement
5. ✅ `readiness = blocked` stops pipeline (no forced conclusions)
6. ✅ Spec/unit sanity checks before proceeding

### Anti-Pattern Protection

12+ documented failure modes with recovery actions:
- Report p-value as impact → Pair with effect size + units + CI
- Leaked features → Run leakage scan, drop offenders
- Causal language on observational data → Use "associated with"
- Cpk on unstable process → Confirm SPC stability first
- Single method, no cross-check → Every Tier-1 claim needs second method

See [`skills/analysis-workflow/references/anti-patterns.md`](skills/analysis-workflow/references/anti-patterns.md)

## Documentation

### For Users

- **[SKILL.md](skills/analysis-workflow/SKILL.md)** — Complete workflow guide
- **[CHANGELOG](../../CHANGELOG.md)** — Release history
- **[Method Registry](skills/analysis-workflow/references/method-registry.md)** — Statistical methods by purpose
- **[Chart Catalog](skills/analysis-workflow/references/chart-catalog.md)** — Visualization guide
- **[Manufacturing Playbook](skills/analysis-workflow/references/manufacturing-playbook.md)** — SPC, MSA, DOE patterns

### For Developers

- **[Plugin Structure](../../../docs/plugin-structure.md)** — Architecture and organization
- **[Agent Development](agents/)** — 7 subagent implementations
- **[Helper Library](skills/analysis-workflow/scripts/ds_skill/)** — 17 Python modules with 180+ tests

## What's New in 1.2.0

### Enhanced Agent Triggering
- All 7 agents now have specific user query examples in descriptions
- "When to invoke" sections with 2-4 concrete usage scenarios
- Improved autonomous triggering accuracy

### Better Command Usability
- Clearer argument hints with `<required>` vs `[optional]` notation
- Real-world usage examples for all 4 commands
- Improved discoverability

### Expanded References
- `anti-patterns.md` — Complete failure mode catalog
- `failure-recovery.md` — Stage-by-stage recovery strategies
- `financial-domain.md` — Time series and market data rules

### Quality Improvements
- SKILL.md optimized (6,591 → 5,661 words, -14%)
- 100% path portability with `${CLAUDE_PLUGIN_ROOT}`
- Multi-platform configuration fully synchronized

See [`skills/analysis-workflow/SKILL_CHANGELOG.md`](skills/analysis-workflow/SKILL_CHANGELOG.md) for complete version history.

## Support

- **Issues:** [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **Discussions:** [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
- **Author:** [@realnghon](https://github.com/realnghon)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Production-grade data science for AI agents. Evidence-backed. Rigorous. Cross-platform.**
