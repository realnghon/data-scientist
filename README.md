<h1 align="center">Data Scientist</h1>

<p align="center"><i>AI skill for structured data analysis — from messy CSVs to evidence-backed reports</i></p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue.svg">
  <img alt="Tests" src="https://img.shields.io/badge/tests-248%20passed-brightgreen.svg">
  <img alt="Platforms" src="https://img.shields.io/badge/platforms-Claude%20%7C%20Cursor%20%7C%20Codex%20%7C%20%2B5-7c3aed.svg">
</p>

---

## What it does

Give it a CSV/Excel/Parquet file and a question. It profiles your data, checks if analysis is possible, picks the right statistical method, runs it, and produces a report with charts, confidence intervals, and limitations.

**Built for**:
- Manufacturing analytics (yield drivers, SPC, Cp/Cpk, defect rates)
- A/B test evaluation (multi-metric tradeoffs, assumption checks)
- Time series (seasonality, anomaly detection, change-points)
- Root cause analysis (multi-source joins, Simpson's paradox)

**Key features**:
- 8-dimension data quality check before analysis (blocks if data is insufficient)
- 3-tier evidence framework (separates reliable findings from directional signals)
- Manufacturing-grade methods (SPC, MSA, DOE, interaction effects)
- Validated on 3 comprehensive test cases with two-line scoring (process adherence + outcome quality)

---

## Quick start

### Install

```bash
# Claude Code
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

Supports Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, Gemini CLI. See [INSTALL.md](INSTALL.md) for platform-specific setup and per-runtime installation.

### Run

```bash
# Claude Code / Codex
/ds-analyze examples/manufacturing_yield/dataset.csv

# Or just ask
"Analyze examples/ab_test/dataset.csv — is treatment better than control?"
```

**Output**: Data profile → readiness check → method plan → execution → charts → report with limitations.

---

## Use cases

**Manufacturing**:
- Yield driver ranking (which process variables affect output?)
- SPC control charts (is the line in control? Cpk calculation)
- Equipment anomaly detection (seasonal patterns, change-points)

**Experiments**:
- A/B test evaluation (multi-metric tradeoffs, SRM check, effect size + CI)
- DOE analysis (interaction effects, optimal parameter ranges)

**Operations**:
- Time series forecasting (decompose seasonality, detect anomalies)
- Root cause analysis (join multiple data sources, trace mechanisms)

---

## What's included

- **1 skill** — 42KB workflow with 8 reference documents and tested helpers
- **11 method families** — regression, A/B tests, SPC, time series, correlation, survival analysis, etc.
- **8 data quality gates** — sample size, missingness, grain, leakage, balance, measurement reliability
- **21 chart functions** — ready-made plots for all analysis types (no hand-written matplotlib)
- **3 evaluation cases** — manufacturing, business, time series (scored on process adherence + outcome quality)

---

## How it works

```
intake → readiness check → data shaping → method selection → execution → critic → report
```

**Gates that stop bad analysis**:
1. If data is too small / too many missing / wrong grain → emits data request, stops analysis
2. If p ≥ 0.05 → downgrade to "directional signal", never claim reliable
3. If spec limits look wrong → flag measurement issue before proceeding

**3-tier evidence**:
- **Tier-1 (reliable)**: p < 0.05, cross-checked, effect size + CI, physically plausible
- **Tier-2 (directional)**: p ≥ 0.05 or failed assumptions, signal present but uncertain
- **Tier-3 (no evidence)**: tested but rejected, reported to show what was checked

---

## Development

```bash
# Run tests
npm test

# Profile a dataset (no AI in the loop)
python plugins/data-scientist/skills/analysis-workflow/scripts/profile_dataset.py data.csv

# Install with Excel/Parquet support
pip install -e ".[io]"
```

**Evaluation**: 3 comprehensive test cases covering manufacturing (multi-table root cause), business analytics (A/B test with Simpson's paradox), and time series (anomaly + seasonality). Scored on two independent lines — `process_score` (deterministic workflow-adherence) and `outcome_score` (agent-judge conclusion quality) — compared as before/after distributions to drive skill iteration. See [`evals/`](evals/) for methodology.

## Plugin Contents

- One Claude Code skill at `plugins/data-scientist/skills/analysis-workflow/SKILL.md`
- Seven staged subagents under `plugins/data-scientist/agents/`
- Four slash commands under `plugins/data-scientist/commands/`
- Shared references under `plugins/data-scientist/skills/analysis-workflow/references/`
- Tested Python helpers under `plugins/data-scientist/skills/analysis-workflow/scripts/ds_skill/`

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Issues and PRs welcome. High-leverage contributions:
- New method entries (logistic regression, GLM, Bayesian methods)
- Golden templates for new domains (logistics, finance, web analytics)
- Platform integrations (JetBrains, VS Code extensions)
