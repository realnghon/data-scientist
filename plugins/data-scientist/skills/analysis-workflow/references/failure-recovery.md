# Failure Modes & Recovery

When a stage hits a wall, do not abort the whole analysis. Each row is a three-step fallback: try the first-line fix, escalate to the fallback, and only then stop with a concrete ask.

## Complete Recovery Table

| Trigger condition | First-line fix | If that still fails |
|---|---|---|
| **File unreadable / wrong encoding** | retry with explicit encoding + delimiter sniff; sample first 1000 rows | return a data-request naming the format needed; do not invent a manifest |
| **No plausible target `Y`** | propose ranked candidates from column roles; ask once (guided) | fall back to `exploratory` profile-only mode; report what's needed to define `Y` |
| **Python environment inadequate** | detect active pyenv/conda/venv with `which python` and test key imports (pandas, numpy, scipy); if imports fail, check if `pip install` is available | 🔴 CHECKPOINT: ask user "Install missing packages to the current environment, or create an isolated venv?"; create a venv only on user confirmation (see Environment policy in step 2) |
| **Virtual environment creation fails** | retry with `python3 -m venv .venv` instead of `virtualenv`; check disk space | ask user to manually create environment or use system Python; document chosen fallback in analysis metadata |
| **Dependency installation fails** | retry with `--no-cache-dir` and `--upgrade pip`; try installing packages individually to isolate the failing one | report missing dependencies + minimal reproduction command; offer to run analysis with available packages only (degraded mode) |
| **Readiness = blocked** (leakage / sparse / mixed grain) | apply the data-readiness narrowing (drop leaked col, restrict to adequate-N subset) | emit the `data_request` artifact and stop downstream stages — never force a conclusion |
| **Shaping collapses sample** (post-filter N too small) | loosen the filter or pick a coarser grain that preserves N | bounce to readiness with the new N; narrow the question to what survives |
| **Join match-rate too low** | normalize keys (strip/case/dtype); try `merge_asof` with tolerance | report per-join match rate; drop the join and analyze sources separately |
| **Every candidate method rejected** | swap to the non-parametric / robust alternative in `method-registry.md` | emit a "method-blocked" note; never run a method whose assumptions fail |
| **Primary method errors at runtime** | run the registered alternative for that claim | mark the claim `unsupported`, keep other claims; record the failure, don't abort |
| **Primary and cross-check disagree** | reconcile (confound, Simpson, sample diff) | downgrade to directional signal with the disagreement stated; never silently pick one |
| **Helper import fails** (`ds_skill` off path) | run the `sys.path` bootstrap in "Make the helpers importable" | fall back to task-specific code and say so; don't skip the analysis |
| **Charts unavailable** (matplotlib/seaborn missing) | `pip install matplotlib seaborn` or `pip install -e ".[viz]"` | deliver text + tables, note charts were skipped and why |
| **Cleanup blocked** (permission denied on .venv) | try with elevated command or check if directory is in use | skip cleanup for that artifact; warn user about leftover files with manual cleanup command |

## Stage-to-Stage Bounces

Stage-to-stage bounces (readiness ↔ shaping, planner → reframe, critic → re-run one claim) are spelled out in `references/workflow.md` → "Loops And Bounces". 

**Loop only the affected stage; never restart from intake.**

## Recovery Principles

1. **Try first-line fix immediately** - Most failures have a known automatic recovery
2. **Escalate to fallback** - If first-line doesn't work, use the fallback strategy
3. **Stop with concrete ask** - If fallback also fails, stop and tell user exactly what's needed
4. **Never invent data** - Return data-request instead of fabricating manifests or conclusions
5. **Degrade gracefully** - Continue with available capabilities rather than total abort
6. **Document fallbacks** - Record which recovery path was taken in analysis metadata

## Critical Non-Recoverable Failures

These require user intervention and cannot be automatically recovered:

1. **Readiness = blocked** - Must emit data-request and stop; never force conclusions
2. **Every method rejected** - Cannot proceed without valid method; emit method-blocked note
3. **Primary + cross-check disagree** - Must downgrade to directional or escalate to user

For all other failures, attempt recovery before stopping.
