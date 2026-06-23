# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] - 2026-06-23

### ⚡ Changed — 激进瘦身（流程提速 ~60%）

**BREAKING CHANGE:** agent 接口和流程结构变更。

- **流程 7 阶段 → 3 阶段**：`intake+readiness → execution → report`。readiness 合并到 intake、shaping 内联到 execution、删除独立的 method-planner 和 critic 阶段。
- **7 agents → 1 agent**：单一 `ds-analyst` 完成全流程，消除多 agent spawn、状态传递、context 重建开销。旧的 `ds-intake-agent` 等 7 个 agent 已删除。
- **文档精简 64%**（2585 → 917 行）：删除 9 个低频/编排类 reference（workflow、branch-routing、multi-agent-orchestration、helper-bootstrap、golden-templates、advanced-techniques、financial-domain、failure-recovery、analysis-plan-template）；精简保留的 6 个 reference。
- **确定性画图**：5 条默认图表规则（数值→boxplot、时序→line、相关→scatter、分布→histogram、排序→bar），消除每次出图不一致。
- **画图样式美化**：`ds_skill.plotting` 注入全局 rcParams（darkgrid、dpi 100、husl 调色板、浅灰背景）。
- **环境/IO 策略前置到 SKILL.md**：检测到可用环境直接用（不重装）；CSV/Excel 一律用 pandas（不用 shell/PowerShell）。

### ✅ 保持不变
- 统计内核 `ds_skill/`（248 测试全绿）、helper 函数签名、SPC run-rule 编号（WE-1..4 / Nelson-1..8）。

---

## [2.2.0] - 2026-06-19

### 🐛 Fixed — statistical correctness (plugin helpers)
- **regression**: the Anderson-Darling normality p-value was inverted in its interpolation branch on large samples; ridge/lasso now standardize features before fitting (scale-fair L1/L2 penalty, coefficients back-transformed to original units); the residual "influential observations" output is relabeled to reflect that leverage is approximated as uniform.
- **classification**: logistic `feature_importance` now uses standardized-coefficient magnitude (|β|·sd) so it reflects predictive contribution rather than a feature's measurement unit.
- **ab_validator**: pairwise effect-size CIs for 3+ arms carry a Bonferroni adjustment + warning; the mean-difference CI uses Student's t (Welch–Satterthwaite dof) instead of the normal approximation.
- **spc**: control-chart run-rule zones derive σ from the wider control-limit half-width, so a clamped p-chart limit no longer distorts Western Electric / Nelson zones.
- **caching**: the cache key now hashes full content (previously only the first/last three rows, which could silently return one dataset's cached result for a different dataset).

---

## [2.0.0] - 2026-06-13

### ✨ SKILL.md Enhancements

**Correctness Layer**
- Added explicit spike detection thresholds (MAD k=3.0, IQR k=1.5)
- Mandatory multi-period seasonality checks (daily + weekly + monthly)
- Interaction effect detection triggers (contradictions in feature importance)
- SPC out-of-control timeframe localization requirements
- Tier-1 evidence exceptions for specialized algorithms (CUSUM, IsolationForest, STL)

**Rigor Layer**
- A/B test time confounding checks for multi-month data
- A/B test revenue analysis on converted subset only
- A/B test distribution assumption checks (normality, homogeneity of variance)
- Time series autocorrelation checks (Ljung-Box test)
- Time series stationarity checks (ADF test)
- Trend tests on deseasonalized components when seasonality strength >0.5

**Quality Layer**
- Standardized data_request format with explicit deficiencies
- Improved report structure and completeness requirements

---

## [1.0.0] - Initial Release

- 42KB analysis workflow with 8 reference documents
- 11 method families (regression, A/B test, SPC, time series, etc.)
- 8-dimension data quality gates
- 21 ready-made chart functions
- 3-tier evidence framework (Tier-1/2/3)
