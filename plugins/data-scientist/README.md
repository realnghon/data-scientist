# Data Scientist

Data Scientist 是一个生产级、跨平台的 AI 插件，用于严谨的结构化数据分析。从制造业分析起步，可推广至各领域的运营数据集，具备循证的统计严谨性。

**版本：** 4.0.0 | **许可证：** MIT | **状态：** 生产就绪

## 提供的功能

### 核心组件

- **`data-scientist` 技能** — 三阶段流程（数据摄入+就绪评估 → 分析执行 → 报告生成），按需加载参考文档，无需多 agent 编排
- **1 个分析 agent** — `ds-analyst` 在单线程中完成整个流程
- **4 个 Slash 命令** — `/ds-analyze`、`/ds-profile`、`/ds-plan`、`/ds-report`，用于交互式工作流
- **经过测试的 Python 库** — `ds_skill`，包含 250+ 单元测试、16 个分析模块（返回 dict，零 dataclass 开销）和 13 个统计图表函数
- **7 份参考文档** — 按需加载架构：方法注册表、图表目录、数据就绪性、数据整形、制造业手册、报告标准、反模式

### 关键特性

✅ **统计严谨性** — 三级证据框架（可靠/方向性/无法支持），强制交叉验证，反模式清单  
✅ **制造业级** — SPC、MSA、DOE、Cpk、控制图、过程能力分析  
✅ **金融领域支持** — 时间序列分析、收益率与价格水平对比、平稳性检验、目标衍生特征检测  
✅ **按需加载** — 按需加载参考文档，保持上下文精简的同时保留深度  
✅ **多平台** — 支持 Claude Code、Codex、OpenCode、Cursor、Cline、Windsurf、GitHub Copilot、Gemini CLI  
✅ **路径兼容** — 100% 使用 `${CLAUDE_PLUGIN_ROOT}`，兼容各应用市场

## 安装

### Claude Code（推荐）

```bash
/plugin marketplace add realnghon/data-scientist
/plugin install data-scientist@data-scientist
```

### 手动安装

各运行时的手动安装路径和本地开发说明，请参见 [`../../INSTALL.md`](../../INSTALL.md)。

### 独立使用

在未安装插件的情况下将技能作为参考材料使用：
```bash
cat skills/analysis-workflow/SKILL.md
```

## 快速开始

### 数据集画像
```bash
/ds-profile data.csv
```

### 完整分析
```bash
/ds-analyze sales.xlsx "什么因素驱动收入？"
```

### 制定分析方案
```bash
/ds-plan "比较实验组与对照组" conversion_rate
```

### 生成报告
```bash
/ds-report ./analysis_output
```

## 核心工作流

该插件遵循三阶段流程，由单一 agent 在单线程中运行：

1. **数据摄入 + 就绪评估** — 检查结构、粒度和字段角色；对大表先探测（`getsize` → `nrows=5` → `usecols`）再完整读取；8 维就绪评估（样本量、缺失率、粒度、时间覆盖、类别平衡、泄漏、变量角色、测量可靠性）；缺失率 >30% 的列会被标记并自动降低相关结论的可信度。产出 `data_manifest`
2. **分析执行** — 选择方法（`method-registry.md`），运行正式的统计检验（而非仅描述统计），检查混杂因素，按确定性规则绘制图表。建模（回归/分类/生存分析）也在此阶段按需进行。产出 `evidence_matrix` + 图表
3. **报告生成** — 面向用户的 Markdown 报告，包含核心结论、证据分层和局限性说明

`data_manifest` 和 `evidence_matrix` 的最小字段模式定义在 [`SKILL.md`](skills/analysis-workflow/SKILL.md) 中。流程定义以 `SKILL.md` 为准；分析指令见 [`agents/ds-analyst.md`](agents/ds-analyst.md)。

## 质量标准

### 证据层级

每项声明都按数据支持程度进行标注：

1. ✅ **可靠结论** — p < 0.05 + 效应量 + 置信区间 + 第二种方法在方向上一致；不依赖高缺失率列或未解决的敏感混杂
2. ✅ **方向性信号** — 存在某种模式，但仅单一方法、效应处于边缘、样本量有限或存在未排除的注意事项（需使用保留性措辞）
3. ✅ **无法支持** — 明确列出：期望验证的结果、数据无法支持的原因、需要补充什么

完整约定请参见 [`report-standard.md`](skills/analysis-workflow/references/report-standard.md)。

### 反模式防护

12+ 种已记录的失败模式及其恢复措施：
- 仅报告 p 值而不带效应量 → 必须同时报告效应量 + 单位 + 置信区间
- 特征泄漏 → 运行泄漏扫描，剔除问题特征
- 对观测数据使用因果语言 → 改用"与……相关"
- 在不稳定过程上计算 Cpk → 先确认 SPC 稳定性
- 单一方法，无交叉验证 → 每条第1层结论都需要第二种方法交叉验证

参见 [`skills/analysis-workflow/references/anti-patterns.md`](skills/analysis-workflow/references/anti-patterns.md)

## 文档

### 面向用户

- **[SKILL.md](skills/analysis-workflow/SKILL.md)** — 完整工作流指南
- **[方法注册表](skills/analysis-workflow/references/method-registry.md)** — 按用途分类的统计方法
- **[图表目录](skills/analysis-workflow/references/chart-catalog.md)** — 可视化指南
- **[制造业手册](skills/analysis-workflow/references/manufacturing-playbook.md)** — SPC、MSA、DOE 模式

### 面向开发者

- **[Agent 开发](agents/)** — 分析 agent 配置
- **[辅助库](skills/analysis-workflow/scripts/ds_skill/)** — 16 个 Python 模块，250+ 项测试

## 支持

- **问题反馈：** [GitHub Issues](https://github.com/realnghon/data-scientist/issues)
- **讨论：** [GitHub Discussions](https://github.com/realnghon/data-scientist/discussions)
- **作者：** [@realnghon](https://github.com/realnghon)

## 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。

---

**面向 AI agent 的生产级数据科学。循证。严谨。跨平台。**