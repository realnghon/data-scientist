<h1 align="center">Data Scientist</h1>

<p align="center"><i>Cross-platform AI plugin for messy structured data analysis, statistical method planning, manufacturing analytics, and evidence-backed reports.</i></p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-informational.svg">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue.svg">
  <img alt="Tests" src="https://img.shields.io/badge/tests-248%20passed-brightgreen.svg">
  <img alt="Coverage" src="https://img.shields.io/badge/coverage-89%25-green.svg">
  <img alt="Platforms" src="https://img.shields.io/badge/platforms-8-success.svg">
  <img alt="Status" src="https://img.shields.io/badge/status-stable-brightgreen.svg">
  <img alt="Built for" src="https://img.shields.io/badge/built%20for-Claude%20%7C%20Codex%20%7C%20Cursor%20%7C%20%2B5-7c3aed.svg">
  <img alt="Code Style" src="https://img.shields.io/badge/code%20style-black-000000.svg">
  <img alt="Maintained" src="https://img.shields.io/badge/maintained-yes-brightgreen.svg">
</p>

---

## ✨ Highlights

- **One skill, eight platforms.** Write the workflow once and run it from Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, or Gemini CLI.
- **7-stage staged orchestration.** Intake → readiness → shaping → method planning → execution → critic → report, with explicit parallel fan-out patterns on platforms that support multi-agent dispatch.
- **Three-tier evidence framework.** Reliable conclusions, directional signals, and unsupported findings are reported separately and never blurred together.
- **Manufacturing-grade reference library.** SPC, Cp/Cpk, MSA, DOE, yield-driver analysis, and 7 recipes baked into the skill — not bolted on.
- **Evaluated on real cases.** 9 case L2 evaluation suite (A/B test, SPC, time series, Simpson paradox, routing scenarios) with iterative optimization loop. Current: **Round 1 - 90%+ average** (2/6 failure modes fixed). See [evals/](evals/) for details.

---

## 🚀 Quick start

1. **Pick your tool** from the [supported platforms](#-supported-platforms) below.
2. **Install the plugin** following the 2-minute guide in [INSTALL.md](INSTALL.md) for your tool.
3. **Run the workflow** against a dataset.

```bash
# One line — installs the skill on any runtime (Claude Code, Codex, Cursor, OpenCode, ...)
npx skills add realnghon/data-scientist
```

`npx skills add` installs the **skill** — the workflow plus the bundled `ds_skill` helpers and references — and runs on every supported runtime. The `/ds-*` slash commands and the 7 staged subagents are **plugin surfaces** (Claude Code / Codex); to get those, install the *plugin* from the marketplace instead — `/plugin marketplace add realnghon/data-scientist` then `/plugin install data-scientist@data-scientist` (see [INSTALL.md](INSTALL.md)). The analysis workflow is identical either way; the plugin just adds the command + subagent affordances.

Prefer a manual path? Every runtime's 2-minute setup is in the [Install table](#-install) below. Or skip install entirely and use the skill as plain reference material:

```bash
cat plugins/data-scientist/skills/analysis-workflow/SKILL.md
```

Then run it. **If you installed the Claude Code / Codex plugin**, use a slash command:

```text
/ds-analyze examples/manufacturing_yield/dataset.csv
```

On any other runtime — or a skill-only `npx skills add` install — invoke the skill by name:

```text
Run the data-scientist skill on data/my_dataset.csv
```

The first pass returns a profile + readiness check; subsequent stages plan methods, execute analysis, and produce a report with limitations.

---

## 🧩 Supported platforms

**Native plugin surfaces** (strongest affordances; parallelism varies by runtime):

| Platform | Skill | Subagents | Slash commands |
|---|:-:|:-:|:-:|
| **Claude Code** | ✅ | ✅ native parallel | ✅ |
| **Codex** | ✅ | ⚠️ sequential | ✅ |
| **OpenCode** | ✅ | ⚠️ sequential | ✅ |

**Rules-based integration** (skill content surfaced as project rules):

| Platform | Entrypoint | Auto-activates on |
|---|---|---|
| **Cursor** | `.cursor/rules/data-scientist.mdc` | data file globs |
| **Cline** | `.clinerules/data-scientist.md` | manual rule load |
| **Windsurf** | `.windsurf/rules/data-scientist.md` | data file globs |
| **GitHub Copilot** | `.github/copilot-instructions.md` | repo presence |
| **Gemini CLI** | `GEMINI.md` | session start |

Legend: ✅ first-class · ⚠️ partial / emulated · ❌ unavailable. Rules-based integrations expose the shared workflow as instructions or memory, not as native plugin runtimes.

---

## 📦 Install

Pick your tool below — each has a 2-minute install path documented in **[INSTALL.md](INSTALL.md)**.

| Platform | Entrypoint | Install guide |
|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | [→ INSTALL.md#claude-code](INSTALL.md#claude-code) |
| Codex | `.codex-plugin/plugin.json` | [→ INSTALL.md#codex](INSTALL.md#codex) |
| Cursor | `.cursor/rules/data-scientist.mdc` | [→ INSTALL.md#cursor](INSTALL.md#cursor) |
| OpenCode | `.opencode/plugins/data-scientist.js` | [→ INSTALL.md#opencode](INSTALL.md#opencode) |
| Cline | `.clinerules/data-scientist.md` | [→ INSTALL.md#cline](INSTALL.md#cline) |
| Windsurf | `.windsurf/rules/data-scientist.md` | [→ INSTALL.md#windsurf](INSTALL.md#windsurf) |
| GitHub Copilot | `.github/copilot-instructions.md` | [→ INSTALL.md#github-copilot](INSTALL.md#github-copilot) |
| Gemini CLI | `GEMINI.md` | [→ INSTALL.md#gemini-cli](INSTALL.md#gemini-cli) |

---

## ⚙️ How it works

```mermaid
flowchart LR
    A[intake] --> B[readiness]
    B -->|gate| C[shaping]
    C --> D[method plan]
    D --> E[execution]
    E --> F[critic]
    F --> G[report]

    C -.parallel.-> C2[view 2]
    C -.parallel.-> C3[view 3]
    E -.parallel.-> E2[method 2]
    E -.parallel.-> E3[method 3]

    style A fill:#e0f2fe,stroke:#0284c7
    style B fill:#fef3c7,stroke:#d97706
    style C fill:#dcfce7,stroke:#16a34a
    style D fill:#dcfce7,stroke:#16a34a
    style E fill:#fce7f3,stroke:#db2777
    style F fill:#f3e8ff,stroke:#9333ea
    style G fill:#e0e7ff,stroke:#4f46e5
```

**7 stages, parallelizable where the runtime supports it.**

Stages connected by dotted lines can fan out to parallel subagents on platforms that natively dispatch sub-agents (Claude Code). On other platforms the same role runs sequentially without changing the artifact JSON contract. See [`references/multi-agent-orchestration.md`](plugins/data-scientist/skills/analysis-workflow/references/multi-agent-orchestration.md) for state-passing schemas and per-platform fan-out patterns.

---

## 🛠️ Use cases

- **Manufacturing yield-driver analysis.** Rank process variables by their influence on yield, separate confirmed drivers from confounded signals, recommend confirmation experiments.
- **Process parameter → defect rate.** Regression and SPC on noisy line data, with Cp/Cpk and capability commentary.
- **Equipment time-series anomaly detection.** Decompose seasonality, surface change-points, filter alarm storms.
- **A/B / experiment sanity check.** Pre-flight assumptions, run the right test, report effect size with confidence bands and caveats.

---

## 📊 What's inside

- **1 skill** — `data-scientist` end-to-end workflow with bundled scripts and references
- **7 staged subagents** — intake, readiness, shaping, method planner, execution, critic, report
- **4 slash commands** — `/ds-profile`, `/ds-plan`, `/ds-analyze`, `/ds-report`
- **11 method groups** in the method registry, backed by tested `ds_skill` modules
- **21 ready-made chart functions** (`ds_skill.plotting`) covering the 32-chart catalog — no hand-written plotting needed
- **8 readiness dimensions** in the data-readiness rubric
- **7 manufacturing recipes** in the playbook
- **3 golden templates** for common report shapes
- **248 tests** in the pytest suite, with focused coverage on high-value helper branches

---

## 📚 Repository layout

```
data-scientist/
├── .claude-plugin/            # Marketplace manifest (marketplace.json)
├── plugins/data-scientist/
│   ├── .claude-plugin/        # Claude Code plugin manifest
│   ├── .codex-plugin/         # Codex manifest
│   ├── .cursor/rules/         # Cursor auto-activating rule
│   ├── .opencode/plugins/     # OpenCode plugin entry
│   ├── .clinerules/           # Cline workspace rules
│   ├── .windsurf/rules/       # Windsurf workspace rules
│   ├── .github/               # GitHub Copilot instructions
│   ├── GEMINI.md              # Gemini CLI memory
│   ├── agents/                # 7 staged subagents
│   ├── commands/              # 4 slash commands
│   └── skills/analysis-workflow/
│       ├── SKILL.md
│       ├── references/        # workflow, method-registry, chart-catalog, ...
│       ├── scripts/           # profile_dataset.py, ds_skill/
│       └── assets/            # report_template.md
├── tests/                     # pytest suite
├── INSTALL.md
├── LICENSE
└── README.md
```

---

## 🧪 Local development

```bash
# Run the test suite
npm test                       # → pytest tests

# Profile a dataset without an assistant in the loop
npm run profile -- path/to/data.csv
# or directly:
python plugins/data-scientist/skills/analysis-workflow/scripts/profile_dataset.py path/to/data.csv
# CSV/TSV/JSON work out of the box; for Excel/Parquet input also run:
#   pip install -e ".[io]"   # installs openpyxl + pyarrow

# Run the deterministic baseline workflow (profile → readiness → shaping → baseline evidence)
python plugins/data-scientist/skills/analysis-workflow/scripts/run_full_workflow.py path/to/data.csv --target target_column
```

Tests live in [`tests/`](tests/). Scratch work belongs in `.local/` (git-ignored).

## 🧪 Evals — measure & iterate

The plugin ships a two-layer eval harness in [`evals/`](evals/) so changes to the skill text are measured, not guessed:

```bash
# L1 — deterministic regression over 9 scoreable cases (zero tokens, CI-safe)
npm run eval:l1

# L2 — agent-in-the-loop: spawn an agent that only sees SKILL.md + the prompt,
# then machine-score routing, artifact discipline, finding hits, and anti-patterns
python evals/harness/score_case.py evals/cases/<case> evals/.runs/l2/<run> --json score.json
```

**All test cases saturated** (9/9 at 100% ✅, as of 2026-06-12):

**Core analysis capabilities** (6 cases):
- **case-01 v2**: Interaction effects (equipment_age × temperature, 500 batches) — **100%**
- **case-02 v2**: A/B multi-metric tradeoff (conversion vs engagement, 20k users) — **100%**
- **case-03 v2**: Time series seasonality + anomaly classification (4320 hourly readings, STL + CUSUM) — **100%**
- **case-04 v2**: Multi-line SPC stratification (3 production lines, 2160 measurements, Cpk per line) — **100%**
- **case-05 v2**: Simpson's paradox + time dimension (1200 orders, trend reversal by region) — **100%**
- **case-09 v2**: Multi-source wafer RCA (fab_log + metrology join+pivot, 200 wafers) — **100%**

**Routing discipline** (3 cases):
- **case-06**: Profile-only routing (500 batches, no statistical analysis) — **100%**
- **case-07**: Named-method routing (assumption violation detection, alternative suggestion) — **100%**
- **case-08**: Blocked routing (45% missingness triggers data request) — **100%**

**Validated skill improvements** (tracked in [`evals/results.tsv`](evals/results.tsv)):
- Gate 2: Mandatory artifacts before analysis (data_manifest + readiness_report)
- Gate 4: Statistical significance enforcement (p < 0.05 for Tier-1 claims)
- Gate 6: Spec/unit sanity checks (physical plausibility verification)
- Step 13: Interaction term detection + categorical noise testing
- Step 14: Mechanism tracing (categorical → continuous, spec range citation)
- Step 16: Negative findings reporting ("tested-but-rejected" mandatory)

**Iterative flywheel**: Eval → Diagnose → Fix (Skill/GT/Data) → Re-eval → Saturate → Upgrade complexity. Full methodology in [`evals/README.md`](evals/README.md).


---

## 🗺️ Roadmap

- More golden templates — logistics, finance, web analytics
- MCP server wrapper so the skill's helpers can be exposed as native tools
- Inline chart rendering in notebook examples for the A/B and time-series datasets

---

## 🤝 Contributing

Issues and PRs welcome. The highest-leverage contributions are: new entries in the method registry, new golden templates for under-served domains, and new platform integrations.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
