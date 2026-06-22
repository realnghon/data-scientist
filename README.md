# Data Scientist

AI skill for structured data analysis — structured data profiling, statistical testing, manufacturing analytics, and evidence-backed reporting.

*Supports: Claude Code · Cursor · Windsurf · Codex · OpenCode · Cline · GitHub Copilot · Gemini CLI*

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platforms](https://img.shields.io/badge/platforms-8%20runtimes-7c3aed)

## Overview

Give it a CSV, Excel, or Parquet file and a question. The skill profiles the data, checks whether analysis is feasible, selects the appropriate statistical method, runs it, and produces a report with charts, confidence intervals, and a clear statement of limitations.

Pipeline: **Intake** → **Readiness** → **Shaping** → **Method selection** → **Execution** → **Critic** → **Report**

---

## Use cases

| Area | Description |
|------|-------------|
| Manufacturing | Yield driver ranking, SPC control charts, Cp/Cpk, defect root cause, equipment anomaly detection |
| Experiments | A/B test evaluation (multi-metric tradeoffs, SRM check, effect size ± CI), interaction effects, Simpson's paradox |
| Time series | Seasonality decomposition, anomaly/change-point detection, trend estimation, stationarity checks |
| Root cause | Multi-source joins, mechanism tracing, negative reporting (tested-but-rejected claims) |

---

## Quick start

### Install

```bash
# Claude Code
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

See [INSTALL.md](INSTALL.md) for platform-specific setup (Cursor, Windsurf, Codex, OpenCode, Cline, Copilot, Gemini CLI).

### Run

```bash
# Analyze a dataset
/ds-analyze examples/manufacturing_yield/dataset.csv

# Or ask in natural language
"Analyze examples/ab_test/dataset.csv — is treatment better than control?"
```

### Output

A structured report containing: data profile, readiness assessment, method rationale with rejected alternatives, evidence matrix with effect sizes and confidence intervals, charts, and a 3-tier conclusions section.

---

## Key capabilities

| Layer | What it does |
|-------|-------------|
| Data quality gates | 8-dimension check before any modeling — sample size, missingness, grain, time coverage, balance, leakage, role clarity, measurement reliability. A `blocked` dimension stops analysis and emits a structured `data_request`. |
| Evidence framework | Three tiers — Tier 1 (p < 0.05, cross-checked, effect size + CI, physically plausible), Tier 2 (signal present but uncertain), Tier 3 (tested but rejected). |
| Manufacturing statistics | SPC: X-bar/R, I-MR, p/c/u charts, Cp/Cpk/Pp/Ppk, Western Electric rules 1-4, Nelson rules 1-8. Capability analysis, interaction effects. |
| Statistical helpers | 16 tested Python modules — bootstrap BCa CIs, log-rank test, Weibull MLE with right-censoring, Welch ANOVA, Benjamini-Hochberg FDR, ridge/lasso regression, and more. |
| Staged subagents | 7 dedicated agents (intake, readiness, method planner, shaper, executor, critic, reporter) with structured handoffs. |
| Cross-platform | Single SKILL.md works across 8 runtimes without porting. |

---

## Package structure

```
plugins/data-scientist/
├── SKILL.md                          Router skill (gates + lazy-load map)
├── agents/                           Seven sub-agents
├── commands/                         Slash commands
├── references/
│   ├── workflow.md                   7-stage pipeline (process SSoT)
│   ├── method-registry.md            Method selection guide
│   ├── data-readiness.md             8-dimension gate rubric
│   ├── chart-catalog.md              21 chart types
│   ├── manufacturing-playbook.md     Domain guidance
│   ├── golden-templates.md           Report templates
│   ├── anti-patterns.md              Failure patterns
│   └── financial-domain.md           Finance-specific methods
└── scripts/ds_skill/                 Python helpers (16 modules)
    ├── readiness.py                  Data quality assessment
    ├── correlation.py                Pairwise + target-feature correlation
    ├── regression.py                 OLS, ridge, lasso with diagnostics
    ├── ab_validator.py               A/B test effect sizes + SRM
    ├── bootstrap.py                  BCa / percentile bootstrap CIs
    ├── spc.py                        Control charts + capability indices
    ├── time_series.py                Trend, STL decomposition, CUSUM
    ├── classification.py             Logistic, random forest, gradient boosting
    ├── survival.py                   Kaplan-Meier, log-rank, Weibull fit
    └── anomaly.py                    IQR, MAD, Isolation Forest
```

11 method families, 21 chart functions, 249 unit tests.

---

## Safety gates

Analysis stops or downgrades conclusions when:

- Data is too small, too missing, or wrong grain — a structured `data_request` is emitted instead of proceeding.
- A test has p ≥ 0.05 or failed assumptions — the conclusion is labeled "directional signal", never "reliable".
- Feature columns contain post-outcome or target-derived data — leakage is flagged and blocked.
- Spec limits appear implausible — measurement reliability is flagged before any capability analysis.
- Only positive results are presented — the 3-tier framework compels the agent to report what was tested and rejected.

---

## Development

```bash
# Profile a dataset (deterministic, no AI)
python scripts/profile_dataset.py data.csv

# Install the helpers locally
pip install -e ".[io]"

# Run tests
python -m pytest tests/
```

---

## License & Contributing

MIT — see [LICENSE](LICENSE).

Contributions welcome. High-leverage areas: new method entries (GLM, Bayesian, survival regression), domain playbooks (logistics, finance, web analytics), platform integrations.
