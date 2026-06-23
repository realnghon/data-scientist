# Data Scientist

Data Scientist is a production-grade, cross-platform AI plugin for rigorous structured data analysis. Starting with manufacturing analytics, it generalizes to operational datasets across domains with evidence-backed statistical rigor.

**Version:** 2.1.0 | **License:** MIT | **Status:** Production Ready

## What It Provides

### Core Components

- **Top-level `data-scientist` skill** — Router with 6 leading-word gates (_routed_ / _red_ / _ready_ / _planned_ / _rigorous_ / _critiqued_) and progressive disclosure to the canonical 7-stage pipeline
- **7 staged subagents** — One per pipeline stage with shared envelope contract and stage-specific schemas
- **4 slash commands** — `/ds-analyze`, `/ds-profile`, `/ds-plan`, `/ds-report` for interactive workflows
- **Tested Python library** — `ds_skill` with 240+ unit tests, 16 analysis modules, and 21 chart functions
- **16 reference documents** — Lazy-load architecture: workflow SSoT, method registry, anti-patterns, domain playbooks

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

Each stage has a dedicated subagent with clear output contracts. The authoritative process definition lives in [`workflow.md`](skills/analysis-workflow/references/workflow.md); `SKILL.md` acts as the router.

## Quality Standards

### Non-Negotiable Gates

1. ✅ **_routed_** — Route analysis type first (full/profile-only/named-method/one-off/blocked)
2. ✅ **_red_** — `readiness = blocked` stops pipeline (no forced conclusions)
3. ✅ **_ready_** — `readiness_report` must exist before shaping or methods
4. ✅ **_planned_** — `analysis_plan` must exist before execution
5. ✅ **_rigorous_** — Tier-1 claims require: p < 0.05 + effect size + CI + cross-check agreement
6. ✅ **_critiqued_** — `critique` must exist before final report

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
- **[Method Registry](skills/analysis-workflow/references/method-registry.md)** — Statistical methods by purpose
- **[Chart Catalog](skills/analysis-workflow/references/chart-catalog.md)** — Visualization guide
- **[Manufacturing Playbook](skills/analysis-workflow/references/manufacturing-playbook.md)** — SPC, MSA, DOE patterns

### For Developers

- **[Agent Development](agents/)** — analysis sub-agent
- **[Helper Library](skills/analysis-workflow/scripts/ds_skill/)** — 16 Python modules with 240+ tests

## Support

- **Issues:** [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **Discussions:** [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
- **Author:** [@realnghon](https://github.com/realnghon)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Production-grade data science for AI agents. Evidence-backed. Rigorous. Cross-platform.**
