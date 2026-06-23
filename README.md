# Data Scientist

AI 技能——结构化数据分析：数据画像、统计检验、制造业分析、循证报告。

*支持：Claude Code · Cursor · Windsurf · Codex · OpenCode · Cline · GitHub Copilot · Gemini CLI*

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platforms](https://img.shields.io/badge/platforms-8%20runtimes-7c3aed)

## 概览

给一个 CSV、Excel 或 Parquet 文件和一个问题。该技能会进行数据画像、检查分析可行性、选择合适的统计方法、运行分析，并生成一份包含图表、置信区间和明确局限性说明的报告。

流程：**数据摄入** → **分析执行** → **报告生成**

---

## 适用场景

| 领域 | 说明 |
|------|------|
| 制造业 | 良率驱动因素排序、SPC 控制图、Cp/Cpk、缺陷根因分析、设备异常检测 |
| 实验分析 | A/B 测试评估（多指标权衡、SRM 检查、效应量 ± 置信区间）、交互效应、Simpson's paradox |
| 时间序列 | 季节性分解、异常/变点检测、趋势估计、平稳性检验 |
| 根因分析 | 多源数据 join、机制追溯、负向发现报告（已检验但被拒绝的假设） |

---

## 快速开始

### 安装

```bash
# Claude Code
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

各平台（Cursor、Windsurf、Codex、OpenCode、Cline、Copilot、Gemini CLI）的安装方式见 [INSTALL.md](INSTALL.md)。

### 运行

```bash
# 分析数据集
/ds-analyze data.csv

# 或以自然语言提问
"分析 data.csv —— 实验组比对照组更好吗？"
```

### 输出

一份结构化报告，包含：数据画像、就绪评估、方法选择理由及被拒绝的替代方案、带效应量和置信区间的证据矩阵、图表，以及三层证据结论。

---

## 核心能力

| 能力层 | 说明 |
|--------|------|
| 数据质量门禁 | 建模前 8 维检查——样本量、缺失率、粒度、时间覆盖、类别平衡、泄漏、角色明确性、测量可靠性。任一维度为 `blocked` 则停止分析并发出结构化 `data_request` |
| 证据框架 | 三层证据——第1层（p < 0.05，交叉验证，效应量 + 置信区间，物理上合理）、第2层（信号存在但不确定）、第3层（已检验但被拒绝） |
| 制造业统计 | SPC：X-bar/R、I-MR、p/c/u 控制图、Cp/Cpk/Pp/Ppk、Western Electric 规则 1-4、Nelson 规则 1-8。能力分析、交互效应 |
| 统计辅助库 | 16 个经过测试的 Python 模块——bootstrap BCa 置信区间、log-rank 检验、Weibull MLE（含右删失）、Welch ANOVA、Benjamini-Hochberg FDR、岭回归/lasso 等 |
| 跨平台 | 单一 SKILL.md 无需移植即可在 8 个运行时上工作 |

---

## 包结构

```
plugins/data-scientist/
├── skills/analysis-workflow/
│   ├── SKILL.md                     三阶段流程（数据摄入 → 分析执行 → 报告生成）
│   ├── references/
│   │   ├── method-registry.md       方法选择指南
│   │   ├── data-readiness.md        8 维质量门禁
│   │   ├── chart-catalog.md         图表选择
│   │   ├── data-shaping.md          粒度、pivot/melt、join
│   │   ├── manufacturing-playbook.md  制造业领域指南
│   │   └── anti-patterns.md         失败模式清单
│   └── scripts/ds_skill/            Python 辅助库（16 模块）
│       ├── readiness.py             数据就绪评估
│       ├── correlation.py           成对 + 目标-特征相关性
│       ├── regression.py            OLS、岭回归、lasso（含诊断）
│       ├── ab_validator.py          A/B 测试效应量 + SRM
│       ├── bootstrap.py             BCa / 百分位 bootstrap 置信区间
│       ├── spc.py                   控制图 + 能力指数
│       ├── time_series.py           趋势、STL 分解、CUSUM
│       ├── classification.py        Logistic、随机森林、梯度提升
│       ├── survival.py              Kaplan-Meier、log-rank、Weibull 拟合
│       └── anomaly.py               IQR、MAD、Isolation Forest
├── agents/ds-analyst.md             分析子 agent
└── commands/                        Slash 命令（ds-analyze、ds-plan、ds-profile、ds-report）
```

---

## 安全门禁

在以下情况下，分析会停止或降级结论：

- 数据过小、缺失过多或粒度错误——不继续而是发出结构化 `data_request`
- 检验的 p ≥ 0.05 或假设不满足——结论标记为"方向性信号"，永远不会标记为"可靠"
- 特征列包含结果后或目标衍生数据——标记为泄漏并阻止分析
- 规格限不合理——在进行能力分析前标记测量可靠性问题
- 只呈现正向结果——三层证据框架强制 agent 报告已检验和被拒绝的发现

---

## 开发

```bash
# 数据集画像（确定性，无需 AI）
python scripts/profile_dataset.py data.csv

# 本地安装辅助库
pip install -e ".[io]"

# 运行测试
python -m pytest tests/
```

---

## 许可证与贡献

MIT — 详见 [LICENSE](LICENSE)。

欢迎贡献。高杠杆方向：新增方法（GLM、贝叶斯、生存回归）、领域手册（物流、金融、Web 分析）、平台集成。
