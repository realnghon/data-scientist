<div align="center">

# 🧪 Data Scientist

**AI skill for structured data analysis — from messy CSVs to evidence-backed conclusions**

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platforms-Claude%20%7C%20Cursor%20%7C%20Codex%20%7C%20%2B6-7c3aed.svg" alt="Platforms">
</p>

<p><i>Drop-in data science skill for AI coding assistants</i></p>

</div>

---

## ✨ What it does

Give it a CSV / Excel / Parquet file and a question. It runs a complete analysis pipeline:

```
📥 Intake → ✅ Readiness check → 🔧 Shaping → 📋 Method plan → ⚙️ Execution 
→ 🔍 Critic → 📝 Report with charts & CIs
```

No prompt engineering, no copy-pasting into Jupyter. One command, end-to-end.

---

## 🎯 Use cases

| Area | What it can do | Example command |
|------|---------------|-----------------|
| 🏭 **Manufacturing** | Yield driver ranking, SPC control charts, Cp/Cpk, defect root cause | `/ds-analyze fab_data.csv --target yield_pct` |
| 🧪 **A/B Tests** | Multi-metric tradeoffs, SRM check, Simpson's paradox detection | `/ds-analyze experiment.csv --target conversion_rate` |
| 📈 **Time Series** | Seasonality decomposition, anomaly detection, change-points, trend | `/ds-analyze sensors.csv --target sensor_value` |
| 🔍 **Root Cause** | Multi-source join & pivot, mechanism tracing, negative reporting | `/ds-analyze orders.csv --target defect_rate` |

---

## 🚀 Quick start

### Install

```bash
# Claude Code
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

**Works on** Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, Gemini CLI.  
See [INSTALL.md](INSTALL.md) for per-platform setup.

### Run

```bash
# Analyze a dataset (Claude Code / Codex)
/ds-analyze examples/manufacturing_yield/dataset.csv

# Or just ask in natural language
"Analyze examples/ab_test/dataset.csv — is treatment better than control?"
```

### Output

> 📊 Data profile → ✅ Readiness assessment → 📋 Analysis plan
> → ⚙️ Statistical execution → 🖼️ Charts → 📝 Evidence-backed report

---

## 🧱 Key features

| Feature | What it does for you |
|---------|---------------------|
| **8-dimension data quality gates** | Blocks analysis if data is too small, too missing, wrong grain, or has leakage. No more garbage-in-garbage-out. |
| **3-tier evidence framework** | Separates reliable conclusions (p<0.05, cross-checked, effect size+CI) from directional signals and tested-but-rejected. Never overclaim. |
| **Manufacturing-grade statistics** | SPC (X-bar/R, I-MR, p/c/u charts, Cp/Cpk/Pp/Ppk, Western Electric & Nelson rules), DOE, interaction effects, Weibull reliability. |
| **Tested Python helpers** | 17 modules with 248 unit tests — bootstrap BCa CIs, log-rank, Weibull MLE, Welch ANOVA, Benjamini-Hochberg FDR, and more. |
| **7 staged subagents** | Intake → Readiness → Method planner → Execution → Shaping → Critic → Report. Each role is a dedicated agent with its own system prompt. |
| **Multi-platform** | Same SKILL.md works on Claude Code, Cursor, Windsurf, Copilot, Codex, OpenCode, Gemini CLI. Zero porting. |

---

## 📦 What's included

```
plugins/data-scientist/
├── 📜 SKILL.md                          # 285-line analysis workflow
├── agents/                              # 7 sub-agents (intake → report)
├── commands/                            # 4 slash commands (/ds-analyze etc.)
├── references/                          # 12 reference documents
│   ├── workflow.md                      #    canonical 14-step pipeline
│   ├── method-registry.md               #    method selection guide
│   ├── data-readiness.md                #    8-dimension gate rubric
│   ├── chart-catalog.md                 #    21 chart types
│   ├── golden-templates.md              #    report structure templates
│   ├── manufacturing-playbook.md        #    domain-specific guidance
│   ├── anti-patterns.md                 #    common failures & fixes
│   └── ...                              #    +5 more
└── scripts/ds_skill/                    # 17 tested Python modules
    ├── readiness.py                     #    8-dimension data assessment
    ├── correlation.py                   #    Pearson / Spearman / MI + BH-FDR
    ├── regression.py                    #    OLS / Ridge / Lasso + diagnostics
    ├── ab_validator.py                  #    A/B tests + effect sizes
    ├── bootstrap.py                     #    BCa / percentile bootstrap
    ├── spc.py                           #    X-bar/I-MR/p/c/u + Cp/Cpk
    ├── time_series.py                   #    MK trend / STL / CUSUM
    ├── classification.py                #    Logistic / RF / GBM
    ├── survival.py                      #    KM / log-rank / Weibull MLE
    ├── anomaly.py                       #    IQR / MAD / Isolation Forest
    └── ...                              #    +7 more
```

**11 method families, 21 chart functions, 248 passing tests.**

---

## 🛡️ Safety gates

The analysis pipeline has hard stops that prevent bad conclusions:

1. **🔴 Data too small / too many missing / wrong grain** → Stops analysis, emits structured `data_request`
2. **🔴 p ≥ 0.05** → Downgraded to "directional signal" — never claimed as reliable
3. **🔴 Spec limits look wrong** → Measurement reliability flag before proceeding
4. **🔴 Leakage detected** → Post-outcome / target-derived columns blocked from feature set
5. **🔴 3-tier evidence** compels the agent to report what was *rejected*, not only what worked

---

## 📐 3-tier evidence

| Tier | Label | Requirements | What it means |
|------|-------|-------------|---------------|
| **1** | ✅ Reliable conclusion | p < 0.05, cross-checked, effect size + CI, physically plausible | "We're confident" |
| **2** | 🔶 Directional signal | Signal present but p ≥ 0.05 or assumptions failed | "Worth investigating" |
| **3** | ⚪ Unsupported | Tested but rejected, or data insufficient | "We checked — no evidence" |

Every conclusion is bucketed. Never overclaimed.

---

## 🔧 Development

```bash
# Profile a dataset (deterministic, no AI)
python scripts/profile_dataset.py data.csv

# Install helpers locally
pip install -e ".[io]"

# Run tests (requires local dev setup)
python -m pytest tests/
```

---

## 📄 License & Contributing

MIT — see [LICENSE](LICENSE).

Issues and PRs welcome. High-leverage contributions:
- New method entries (GLM, Bayesian methods, survival regression)
- Domain playbooks (logistics, finance, web analytics)
- Platform integrations (JetBrains, VS Code)

---

<div align="center">
<i>From CSV to conclusion — one command.</i>
</div>