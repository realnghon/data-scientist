# Changelog

All notable changes to the data-scientist plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Expanded high-value test coverage for caching, dataset profiling, analysis method selection, correlation validation, regression diagnostics, time-series edge cases, classification, SPC, and readiness rollups.

### Changed
- Updated README test and coverage badges to reflect **245 passing tests** and **89% coverage**.

## [1.0.0] - 2026-05-30

First stable release. The headline fix is that the plugin now **installs cleanly** through the Claude Code marketplace flow (previously it errored), and the bundled helper library is now reliably importable so agents stop re-writing statistics and chart code by hand.

### Fixed
- **Installation no longer errors.** `marketplace.json` moved to the required `.claude-plugin/marketplace.json` location, with the `path` field corrected to `source` (`./plugins/data-scientist`) and the required `owner` block added. The non-standard `_comment` and placeholder homepage were removed.
- **Plugin manifest now validates.** Removed the invalid `agents` path field from `plugin.json` (it failed `claude plugin validate` with `agents: Invalid input`); components are auto-discovered from `commands/`, `agents/`, and `skills/`. Verified end-to-end with `claude plugin marketplace add` + `claude plugin install`.
- Silenced spurious runtime warnings that surfaced during normal analyses: NumPy `matmul` divide/overflow warnings in regression VIF and prediction, the pandas "could not infer datetime format" notice in the profiler, and scipy moment/precision warnings on near-constant columns.
- Replaced the corrupt manufacturing example notebook (invalid JSON) with a valid, fully executed walkthrough.

### Added
- **Import bootstrap** so `ds_skill` works from any runtime (Claude Code, Codex, OpenCode, local dev): a self-locating `scripts/ds_bootstrap.py` plus a copy-paste snippet and `pip install -e .` guidance in `SKILL.md`. Resolves the main reason agents previously re-implemented the helpers.
- **Chart library expanded from 6 to 21 functions** in `ds_skill.plotting`, covering the families in `references/chart-catalog.md`: histogram, ECDF, grouped boxplot, violin, dot-plot with CI, scatter+fit, Pareto, time series with bands, small multiples, capability histogram with spec lines, flagged-anomaly scatter, ROC, confusion matrix, calibration curve, and feature-importance bar — plus a `save_figure` helper. Every function is headless-safe and returns a matplotlib `Figure`.
- `viz` optional dependency extra (`pip install -e ".[viz]"`) for matplotlib/seaborn; both added to dev dependencies and the test suite.
- `$schema` references on `plugin.json` and `marketplace.json` for editor validation.

### Changed
- Consolidated the duplicate `manufacturing-yield/` and `manufacturing_yield/` example directories into a single canonical `manufacturing_yield/` with a working `analysis.ipynb`; example generators now save relative to their own location so they work from any directory.
- Test suite expanded to **202 passing** (1 skipped without the optional `lifelines` package); added 26 chart tests. The suite now runs warning-clean.
- Version unified to `1.0.0` across `plugin.json`, `.codex-plugin/plugin.json`, `marketplace.json`, `package.json`, `pyproject.toml`, and `ds_skill.__version__`.

## [0.2.0] - 2026-05-29

### Added
- **Complete installation guide** (`INSTALL.md`) covering all 8 platforms
  - Step-by-step instructions for Claude Code, Codex, OpenCode, Cursor, Cline, Windsurf, GitHub Copilot, Gemini CLI
  - Troubleshooting section for common issues
  - Platform-specific verification steps
- **Comprehensive contributing guide** (`CONTRIBUTING.md`)
  - Development setup and workflow
  - Testing guidelines and code style
  - PR process and review criteria
  - Contribution ideas by skill level
- **Example datasets** in `examples/` with data generators:
  - `manufacturing_yield/`: 500 production runs with confounded variables (temperature, pressure, humidity, operators)
  - `ab_test/`: 10,000 users A/B test with conversion and revenue metrics
  - `time_series/`: 90 days of hourly sensor data with injected anomalies (spikes, drift, outages)
- **Visualization helpers** (`ds_skill.plotting`) with 7 chart functions:
  - Control charts, correlation matrices, regression diagnostics
  - Time series decomposition, distribution comparison, Kaplan-Meier curves
- **Caching utilities** (`ds_skill.caching`) for expensive computations
  - Disk-based caching with stable DataFrame hashing
  - `@cached_computation` decorator for bootstrap/permutation tests
- **Input validation** (`ds_skill.validation`) with security checks
  - DataFrame validation, column type checking
  - Safe filename validation (path traversal prevention)
  - Probability and positive int validation
- **Package management**:
  - `requirements.txt` and `requirements-dev.txt` with pinned versions
  - `pyproject.toml` for pip-installable package (`pip install -e .`)
- Enhanced `.gitignore` with cache, IDE, and Jupyter patterns
- This CHANGELOG.md

### Changed
- CI now uses `requirements-dev.txt` instead of hardcoded dependencies
- Test suite expanded to 176 tests (31 new validation tests)
- All tests passing with 100% success rate

### Fixed
- Fix Claude Code command and subagent frontmatter so they register correctly
- Replace non-functional `.cursor-plugin/` with proper `.cursor/rules/*.mdc`
- Fix newline bug in OpenCode plugin bootstrap
- Move tests out of `.local/` so the repo is testable after clone

## [0.1.0] - 2024-05-28

### Added
- Initial cross-tool plugin scaffold
- Data-scientist skill with workflow, method registry, readiness checks, manufacturing playbook
- Core analysis modules: readiness, SPC, correlation, anomaly, time series, bootstrap, shaping, A/B testing, regression, classification, survival analysis
- Report generation with evidence matrix
- Multi-platform support: Claude Code, Codex, Cursor, OpenCode, Cline, Windsurf, GitHub Copilot, Gemini CLI
- Comprehensive test suite (145 tests)
- Documentation: README, INSTALL, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT
- CI/CD with GitHub Actions (pytest on 3 OS × 3 Python versions)
- Dependabot for automated dependency updates
- Lightweight profile script and tested method-selection helpers

[Unreleased]: https://github.com/realnghon/data-scientist/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/realnghon/data-scientist/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/realnghon/data-scientist/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/realnghon/data-scientist/releases/tag/v0.1.0
