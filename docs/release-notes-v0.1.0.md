# data-scientist v0.1.0

First public release of the `data-scientist` plugin — a manufacturing-grade, multi-platform data-science agent pack that runs across 8 AI coding environments from a single source of truth.

This release packages a staged multi-agent workflow, a tested Python helper library, and a deep set of references (charts, methods, readiness scoring, golden templates) into one drop-in plugin.

If you're upgrading from a pre-release checkout: nothing to migrate. This is v0.1.0 — the baseline. Future releases will document their upgrade paths against this version.

## 🎉 Highlights

The headline items for v0.1.0 — what makes this release worth installing today:

- **8 platforms, one plugin.** Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, and Gemini CLI are all served from a shared skill and agent set, so behavior stays consistent regardless of where you invoke it. Platform-specific manifests live alongside the canonical source.

- **13 production-grade `ds_skill` Python modules.** Readiness, SPC, correlation, anomaly, time-series, bootstrap, shaping, A/B validator, regression, classification, survival, report generator, and legacy methods — all importable from one package, with a consistent return shape.

- **145 pytest tests** covering every helper module, including edge cases for missing optional dependencies, degenerate inputs, and known-bad data shapes.

- **Manufacturing-grade SPC.** Western Electric + Nelson rules, Cp/Cpk capability indices, MSA / Gauge R&R helpers, and Pareto / yield drivers are wired in by default — not bolted on later.

- **7-stage staged orchestration.** Intake → readiness → shaping → method-plan → execution → critic → report, with explicit parallel fan-out patterns and a JSON state contract every agent honors.

## 🧩 What's included

- **1 skill** — `data-scientist`, with 9 reference docs and lazy-load routing so context only grows when a stage needs it.

- **7 staged subagent prompts** — `ds-intake`, `ds-readiness`, `ds-shaping`, `ds-method-planner`, `ds-execution`, `ds-critic`, `ds-report`.

- **4 slash commands** — `/ds-profile`, `/ds-plan`, `/ds-analyze`, `/ds-report`.

- **Method registry** covering 11 method groups: descriptive, inferential, SPC, capability, MSA, DOE, regression, classification, time-series, survival, and anomaly.

- **8-dimension data-readiness scoring rubric** with quantitative thresholds and remediation hints for each dimension.

- **Chart catalog** with 32 charts, each annotated with when-to-use and when-not-to-use guidance.

- **3 golden templates** — manufacturing yield-driver, process-parameter → defect, and equipment time-series anomaly.

- **7 manufacturing recipes** — SPC, capability, MSA, DOE, batch effect, Pareto, and drift.

## 🚀 Install

See [INSTALL.md](../INSTALL.md) for full instructions. One-liner per platform:

- **Claude Code** — see [Claude Code section](../INSTALL.md#claude-code)
- **Codex** — see [Codex section](../INSTALL.md#codex)
- **Cursor** — see [Cursor section](../INSTALL.md#cursor)
- **OpenCode** — see [OpenCode section](../INSTALL.md#opencode)
- **Cline** — see [Cline section](../INSTALL.md#cline)
- **Windsurf** — see [Windsurf section](../INSTALL.md#windsurf)
- **GitHub Copilot** — see [GitHub Copilot section](../INSTALL.md#github-copilot)
- **Gemini CLI** — see [Gemini CLI section](../INSTALL.md#gemini-cli)

## 📦 What this release does NOT include

To set expectations clearly — known gaps that the maintainer is tracking for follow-up releases:

- **No native marketplace publishing on Claude Code.** The manifest is scaffolded for a future submission, but this release is install-by-clone only.

- **No screenshots or video demo.** Text-only docs for v0.1.0; a visual walkthrough is on the roadmap.

- **No CONTRIBUTING.md examples for adding new platforms.** Text guidance is provided, but worked examples will land in a follow-up release.

- **Some optional Python dependencies required for advanced methods.** `statsmodels` and `scikit-learn` are needed for regression, classification, survival, and certain time-series helpers. Modules degrade gracefully when these are missing, but the install steps assume the user has them on `PYTHONPATH`.

- **No telemetry, no auto-update, no phone-home.** This release is fully local; if that changes in the future, it will be opt-in and called out in the release notes.

## 🙏 Acknowledgments

This plugin was itself built using parallel Claude Code subagents — the same staged-orchestration pattern it ships is what produced it. Huge thanks to the multi-agent build crew that drafted the skill content, wrote the 145-test suite, ported the agent prompts across 8 platforms, and reviewed each other's output in flight. Dogfooding works, and the workflow encoded in this plugin is the workflow that shipped this plugin.

Special thanks to early users who stress-tested the staged orchestration on real manufacturing datasets and surfaced the edge cases that now live in the test suite.

## 📚 Links

- [README](../README.md) — overview and quickstart
- [INSTALL.md](../INSTALL.md) — per-platform install instructions
- [CHANGELOG.md](../CHANGELOG.md) — full changelog
- [CONTRIBUTING.md](../CONTRIBUTING.md) *(arriving with this release)* — how to contribute

---

*Cut from `master` at the v0.1.0 tag. Issues and feedback welcome on the repository tracker.*
