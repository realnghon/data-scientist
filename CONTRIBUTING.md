# Contributing to data-scientist

Thanks for your interest in improving the data-scientist plugin. This document covers how to propose changes, what we accept, and the conventions we follow across the skill docs, agent prompts, and the `ds_skill/` Python helpers.

## How to contribute

Fork the repository, create a feature branch off `main` (e.g. `feat/method-registry-anova` or `fix/profile-helper-nan`), make your changes with tests, and open a pull request describing the motivation and any trade-offs. Keep PRs focused — one logical change per PR makes review faster and rollbacks safer.

## What we welcome

- New entries to `plugins/data-scientist/skills/analysis-workflow/references/method-registry.md` with a corresponding `ds_skill/` helper module and pytest coverage
- New `plugins/data-scientist/skills/analysis-workflow/references/golden-templates.md` templates that include all required sections: trigger, roles, readiness checks, methods sequence, charts, and failure modes
- New platform integrations (a rule file or plugin entrypoint plus an INSTALL.md section for the target platform)
- Bug fixes accompanied by a regression test that fails before the fix and passes after
- Documentation clarifications, especially LLM-targeted phrasing that improves agent behavior

## What we don't accept

- Unverified statistical methods without documented cross-checks (cite the test you ran against an established implementation, or include numerical comparisons in the test suite)
- Helper code without pytest coverage — every public function in `ds_skill/` must have tests
- Platform integrations without a matching INSTALL.md update so users can actually install them

## Development setup

```bash
git clone https://github.com/<your-fork>/data-scientist.git
cd data-scientist
pip install -r requirements-dev.txt
```

Run the full test suite:

```bash
npm test          # runs pytest tests/
```

Run the profile helper against a dataset:

```bash
npm run profile -- <dataset>
```

## Adding a new ds_skill module

1. Create `plugins/data-scientist/skills/analysis-workflow/scripts/ds_skill/<module>.py`
2. Expose a public API built on dataclasses, each with an `as_dict()` method so results serialize cleanly to JSON
3. Lazy-import heavy dependencies (scipy, sklearn, statsmodels) inside the function that needs them, not at module top-level
4. Add `tests/test_<module>.py` with at least 7 tests covering happy path, edge cases, and error modes
5. Update `plugins/data-scientist/skills/analysis-workflow/references/method-registry.md` with the new method group and when to use it
6. Update the "Code Helpers — Lazy Import Map" row in `plugins/data-scientist/skills/analysis-workflow/SKILL.md` so agents can find your helper

## Adding a new platform integration

1. Add a rule or manifest file under `plugins/data-scientist/.<platform>/` following that platform's plugin spec
2. Add a section in `INSTALL.md` showing how a user installs and verifies the integration
3. Add a row in the supported-platforms table in `README.md`
4. Note any limitations in the INSTALL.md section (e.g. no parallel dispatch, no slash commands, single-agent only)

## Style guidelines

### Markdown (skill docs, references, agent prompts)

- Short bullets over long paragraphs — these files are read by LLMs, not just humans
- Decision tables when there's a "use X when Y" mapping
- Explicit triggers — say "use this when the user mentions X" rather than implying it
- Keep sections scannable; nest only when the structure adds clarity

### Python (`ds_skill/`)

- `from __future__ import annotations` at the top of every module
- Type hints on every public function and dataclass field
- Dataclasses with `as_dict()` for any value returned to an agent
- No `print()` calls — return data, let the caller decide how to surface it
- Lazy-import scipy / sklearn / statsmodels inside the function, not at module load

### Tests

- Generate synthetic data inside the test using numpy or pandas
- No network calls, no filesystem reads outside `tmp_path`
- Name tests for the behavior they check, not the function they call

## Commit messages

Short imperative subject lines ("add anova helper to method registry"), focused on the why in the body when the motivation isn't obvious from the diff. Avoid noise commits — squash fixups before opening the PR.

## PR review

- One maintainer approval is required before merge
- CI must be green (pytest suite passes on all supported Python versions)
- Resolve review comments by replying inline or pushing a follow-up commit; don't force-push over an in-flight review unless requested
