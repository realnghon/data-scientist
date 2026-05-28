<h1 align="center">Data Scientist</h1>

<p align="center"><i>Cross-platform AI plugin for messy structured data analysis, statistical method planning, manufacturing analytics, and evidence-backed reports.</i></p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="CHANGELOG.md"><img alt="Version" src="https://img.shields.io/badge/version-0.1.0-informational.svg"></a>
  <img alt="Platforms" src="https://img.shields.io/badge/platforms-8-success.svg">
  <img alt="Tests" src="https://img.shields.io/badge/tests-passing-brightgreen.svg">
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-orange.svg">
  <img alt="Built for" src="https://img.shields.io/badge/built%20for-Claude%20%7C%20Codex%20%7C%20Cursor%20%7C%20%2B5-7c3aed.svg">
</p>

---

## ✨ Highlights

- **One skill, eight platforms.** Write the workflow once and run it from Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, or Gemini CLI.
- **7-stage staged orchestration.** Intake → readiness → shaping → method planning → execution → critic → report, with explicit parallel fan-out patterns on platforms that support multi-agent dispatch.
- **Three-tier evidence framework.** Reliable conclusions, directional signals, and unsupported findings are reported separately and never blurred together.
- **Manufacturing-grade reference library.** SPC, Cp/Cpk, MSA, DOE, yield-driver analysis, and 7 recipes baked into the skill — not bolted on.

---

## 🚀 Quick start

1. **Pick your tool** from the [supported platforms](#-supported-platforms) below.
2. **Install the plugin** with the one-line snippet for your tool — Claude Code shown here, others in collapsible blocks under [Install](#-install).
3. **Run the workflow** against a dataset.

```bash
# Claude Code — primary entrypoint
git clone https://github.com/your-org/data_scientist.git
ln -s "$PWD/data_scientist/plugins/data-scientist" "$HOME/.claude/plugins/data-scientist"
```

```text
# In Claude Code, then:
/ds-analyze data/my_dataset.csv
```

On platforms without slash commands, invoke the skill by name:

```text
Run the data-scientist skill on data/my_dataset.csv
```

The first pass returns a profile + readiness check; subsequent stages plan methods, execute analysis, and produce a report with limitations.

---

## 🧩 Supported platforms

| Platform | Entrypoint | Skill | Subagents | Slash commands | Install |
|---|---|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | ✅ | ✅ native dispatch | ✅ | [↓](#claude-code) |
| Codex | `.codex-plugin/plugin.json` | ✅ | ⚠️ sequential | ✅ | [↓](#codex) |
| Cursor | `.cursor/rules/data-scientist.mdc` | ✅ | ⚠️ sequential | ⚠️ as rules | [↓](#cursor) |
| OpenCode | `.opencode/plugins/data-scientist.js` | ✅ | ⚠️ sequential | ✅ | [↓](#opencode) |
| Cline | `.clinerules/` | ✅ | ⚠️ sequential | ⚠️ as rules | [↓](#cline) |
| Windsurf | `.windsurf/rules/` | ✅ | ⚠️ sequential | ⚠️ as rules | [↓](#windsurf) |
| GitHub Copilot | `.github/copilot-instructions.md` | ✅ | ➖ | ➖ | [↓](#github-copilot) |
| Gemini CLI | `GEMINI.md` | ✅ | ⚠️ sequential | ⚠️ as prompts | [↓](#gemini-cli) |

Legend: ✅ first-class · ⚠️ partial (works, fewer affordances) · ➖ not available on this surface.

---

## 📦 Install

Full per-platform details live in [INSTALL.md](INSTALL.md). The snippets below are the minimum to get running.

<details>
<a id="claude-code"></a>
<summary><b>Claude Code</b> — native skill + subagents + slash commands</summary>

```bash
ln -s "$PWD/plugins/data-scientist" "$HOME/.claude/plugins/data-scientist"
```

Verify:

```bash
ls "$HOME/.claude/plugins/data-scientist/.claude-plugin/plugin.json"
```

See [INSTALL.md#claude-code](INSTALL.md#claude-code).
</details>

<details>
<a id="codex"></a>
<summary><b>Codex</b> — skill, commands, subagent prompts (sequential)</summary>

```bash
ln -s "$PWD/plugins/data-scientist" "$HOME/.codex/plugins/data-scientist"
```

Verify:

```bash
cat "$HOME/.codex/plugins/data-scientist/.codex-plugin/plugin.json"
```

See [INSTALL.md#codex](INSTALL.md#codex).
</details>

<details>
<a id="cursor"></a>
<summary><b>Cursor</b> — auto-activating rule on data file globs</summary>

```bash
mkdir -p "$PWD/.cursor/rules"
cp plugins/data-scientist/.cursor/rules/data-scientist.mdc "$PWD/.cursor/rules/data-scientist.mdc"
```

Verify by opening any `*.csv` / `*.parquet` file — Cursor should surface the rule.

See [INSTALL.md#cursor](INSTALL.md#cursor).
</details>

<details>
<a id="opencode"></a>
<summary><b>OpenCode</b> — bundled plugin entry</summary>

```bash
mkdir -p "$HOME/.opencode/plugins"
ln -s "$PWD/plugins/data-scientist/.opencode/plugins/data-scientist.js" \
      "$HOME/.opencode/plugins/data-scientist.js"
```

Verify:

```bash
opencode plugins list | grep data-scientist
```

See [INSTALL.md#opencode](INSTALL.md#opencode).
</details>

<details>
<a id="cline"></a>
<summary><b>Cline</b> — workspace rules</summary>

```bash
mkdir -p "$PWD/.clinerules"
cp -r plugins/data-scientist/.clinerules/* "$PWD/.clinerules/"
```

Verify by reopening the project — Cline lists active rules in its panel.

See [INSTALL.md#cline](INSTALL.md#cline).
</details>

<details>
<a id="windsurf"></a>
<summary><b>Windsurf</b> — workspace rules</summary>

```bash
mkdir -p "$PWD/.windsurf/rules"
cp -r plugins/data-scientist/.windsurf/rules/* "$PWD/.windsurf/rules/"
```

Verify in Windsurf settings → Rules.

See [INSTALL.md#windsurf](INSTALL.md#windsurf).
</details>

<details>
<a id="github-copilot"></a>
<summary><b>GitHub Copilot</b> — repo instructions</summary>

```bash
mkdir -p "$PWD/.github"
cp plugins/data-scientist/.github/copilot-instructions.md "$PWD/.github/"
```

Verify Copilot Chat picks up the instructions on the next session.

See [INSTALL.md#github-copilot](INSTALL.md#github-copilot).
</details>

<details>
<a id="gemini-cli"></a>
<summary><b>Gemini CLI</b> — persistent memory file</summary>

```bash
cp plugins/data-scientist/GEMINI.md "$PWD/GEMINI.md"
```

Verify:

```bash
gemini --show-memory | grep data-scientist
```

See [INSTALL.md#gemini-cli](INSTALL.md#gemini-cli).
</details>

---

## ⚙️ How it works

```
                  ┌──────────────┐
                  │   intake     │   parse request, locate data
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  readiness   │   8-dim rubric, gate decision
                  └──────┬───────┘
                         │  (gate)
                  ┌──────▼───────┐
                  │   shaping    │   ◀── ⓟ parallel views possible
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ method plan  │   pick from 11 method groups
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  execution   │   ◀── ⓟ parallel per method
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │   critic     │   stress-test conclusions
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │   report     │   three-tier evidence framework
                  └──────────────┘
```

Stages marked ⓟ can fan out to parallel subagents on platforms that support multi-agent dispatch (Claude Code). On platforms that don't, the same role is executed sequentially without changing the artifact contract — the report you get out the other end is shaped identically.

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
- **11 method groups** in the method registry
- **8 readiness dimensions** in the data-readiness rubric
- **32 charts** catalogued with selection guidance
- **7 manufacturing recipes** in the playbook
- **3 golden templates** for common report shapes

---

## 📚 Repository layout

```
data_scientist/
├── plugins/data-scientist/
│   ├── .claude-plugin/        # Claude Code manifest
│   ├── .codex-plugin/         # Codex manifest
│   ├── .cursor/rules/         # Cursor auto-activating rule
│   ├── .opencode/plugins/     # OpenCode plugin entry
│   ├── .clinerules/           # Cline workspace rules
│   ├── .windsurf/rules/       # Windsurf workspace rules
│   ├── .github/               # GitHub Copilot instructions
│   ├── GEMINI.md              # Gemini CLI memory
│   ├── agents/                # 7 staged subagents
│   ├── commands/              # 4 slash commands
│   └── skills/data-scientist/
│       ├── SKILL.md
│       ├── references/        # workflow, method-registry, chart-catalog, ...
│       ├── scripts/           # profile_dataset.py, ds_skill/
│       └── assets/            # report_template.md
├── tests/                     # pytest suite
├── INSTALL.md
├── CHANGELOG.md
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
python plugins/data-scientist/skills/data-scientist/scripts/profile_dataset.py path/to/data.csv
```

Tests live in [`tests/`](tests/). Scratch work belongs in `.local/` (git-ignored).

---

## 🗺️ Roadmap

- More golden templates — logistics, finance, web analytics
- MCP server wrapper so the skill's helpers can be exposed as native tools
- Native Claude Code marketplace publication
- Quality and coverage CI on the pytest suite

---

## 🤝 Contributing

Issues and PRs welcome. The highest-leverage contributions are: new entries in the method registry, new golden templates for under-served domains, and new platform integrations. A full contributing guide is on the way — see `CONTRIBUTING.md` (coming soon).

---

## 📄 License

MIT — see [LICENSE](LICENSE).
