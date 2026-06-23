# Data Scientist

Data Scientist is a production-grade, cross-platform AI plugin for rigorous structured data analysis. Starting with manufacturing analytics, it generalizes to operational datasets across domains with evidence-backed statistical rigor.

**Version:** 4.0.0 | **License:** MIT | **Status:** Production Ready

## What It Provides

### Core Components

- **`data-scientist` skill** — A 3-stage flow (intake+readiness → execution → report) with progressive disclosure to lazy-loaded references. No gate ceremony, no multi-agent orchestration
- **1 analysis subagent** — `ds-analyst` completes the whole flow in a single thread
- **4 slash commands** — `/ds-analyze`, `/ds-profile`, `/ds-plan`, `/ds-report` for interactive workflows
- **Tested Python library** — `ds_skill` with 250+ unit tests, 16 analysis modules (dict returns, zero dataclass overhead), and 13 statistical chart functions
- **7 reference documents** — Lazy-load architecture: method registry, chart catalog, data readiness, data shaping, manufacturing playbook, report standard, anti-patterns

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

The plugin follows a 3-stage flow, run by a single agent in one thread:

1. **Intake + Readiness** — Inspect structure, grain, and field roles; large tables are probed (`getsize` → `nrows=5` → `usecols`) before a full read; 8-dimension readiness assessment (sample size, missingness, grain, time coverage, class balance, leakage, variable roles, measurement reliability); columns with >30% missing are flagged and auto-downgrade any conclusion that uses them. Produces `data_manifest`
2. **Execution** — Pick a method (`method-registry.md`), run a formal statistical test (not just descriptive stats), check for confounding, and draw the chart per the deterministic rules. Modeling (regression/classification/survival) lives here too, on demand. Produces `evidence_matrix` + charts
3. **Report** — User-facing markdown with executive answer, evidence tiers, and limitations

`data_manifest` and `evidence_matrix` have minimal field schemas defined in [`SKILL.md`](skills/analysis-workflow/SKILL.md). The authoritative process definition is `SKILL.md`; the analysis prompt is [`agents/ds-analyst.md`](agents/ds-analyst.md).

## Quality Standards

### Evidence Tiers

Every claim is labelled by how much the data supports it:

1. ✅ **reliable** — significance (p < 0.05) + effect size + CI + a second method agreeing in direction; no high-missing column or unaddressed confound it is sensitive to
2. ✅ **directional** — a pattern is present but single-method, borderline, modest N, or carries one caveat (hedged language required)
3. ✅ **unsupported** — explicitly named: what was hoped, why the data cannot support it, what would be needed

See [`report-standard.md`](skills/analysis-workflow/references/report-standard.md) for the full contract.

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
- **[Helper Library](skills/analysis-workflow/scripts/ds_skill/)** — 16 Python modules with 250+ tests

## Support

- **Issues:** [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **Discussions:** [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
- **Author:** [@realnghon](https://github.com/realnghon)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Production-grade data science for AI agents. Evidence-backed. Rigorous. Cross-platform.**
