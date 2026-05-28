# Changelog

All notable changes to the data-scientist plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[Unreleased]: https://github.com/realnghon/data-scientist/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/realnghon/data-scientist/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/realnghon/data-scientist/releases/tag/v0.1.0

