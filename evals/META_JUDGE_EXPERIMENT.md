# 元裁判实验：评估是否可以完全取消正则评分

## 问题背景

当前评测系统使用正则匹配（regex）评分存在 3 个关键问题：
1. **关键词游戏**：agent 学会输出特定词汇（如"33.4%"）而非真实分析
2. **逻辑矛盾放过**：正则可被否定句触发（"交互不显著"仍满足 interaction 模式）
3. **致命缺陷漏检**：case-09 测量泄漏（speed~yield 同源）未被关键词捕获

## 实验设计

**目标**：通过数据证明 LLM judge 是否可以完全替代正则，或正则仍有独特价值。

**方法**：双边评分 + 元裁判验证
1. 对同一案例运行两种评分器：
   - Regex scorer（现有 `score_case.py`，关键词匹配）
   - LLM judge（`judge_score.py`，5 维度质量评估）
2. 元裁判（Claude Opus）对比两种评分 + agent 输出，评估：
   - `regex_accuracy`（0-10）：关键词匹配是否准确
   - `judge_accuracy`（0-10）：LLM 评估是否准确
   - `unique_value_of_regex`：正则是否捕获了 judge 漏检的问题
   - `gaming_detected`：是否检测到关键词游戏
   - `recommendation`：keep_regex | retire_regex | uncertain

**案例选择**：
- case-01 v2（100% regex）：已知逻辑矛盾（交互效应报告前后不一致）
- case-02 v2（100% regex）：已知关键词游戏（33.4% 精确匹配、tradeoff × 5）
- case-09 v2（100% regex）：已知漏检（测量泄漏未被 regex 捕获）

**决策标准**：
- ≥67% 案例推荐 `retire_regex` 且 `judge_accuracy > regex_accuracy` → **取消正则**
- ≥50% 案例显示 `unique_value_of_regex=true` → **保留正则**
- 其他 → 不确定，需更多数据

## 运行实验

### 前置条件
```bash
# 1. 设置 API key
export ANTHROPIC_API_KEY='your-api-key'

# 2. 确保依赖已安装
pip install anthropic
```

### 执行
```bash
cd /path/to/data-scientist
python evals/harness/meta_judge_experiment.py
```

### 预期输出
```
============================================================
Comparing scorers on case-01-manufacturing-yield
============================================================
Running regex scorer on case-01-manufacturing-yield...
Running LLM judge on case-01-manufacturing-yield...
Running meta-judge comparison...

Result:
  Regex: 100.0
  Judge: 78.5
  Delta: 21.5
  Meta recommendation: retire_regex
  Rationale: 报告在 Step 13 段落声称"交互项 F 检验 p > 0.18, 方向零翻转"，但 C4 结论又说...

... (case-02, case-09)

============================================================
EXPERIMENT SUMMARY
============================================================
Total cases: 3
Recommendation: Retire regex: 3, Keep: 0, Uncertain: 0
Gaming detected: 2/3
Avg accuracy: Regex=6.3/10, Judge=8.7/10

✅ RECOMMENDATION: RETIRE REGEX
   Evidence: 3/3 cases support retirement
   LLM judge is more accurate (avg 8.7 vs 6.3)
```

### 结果文件
- `evals/.runs/meta_judge_experiment/case-01_comparison.json`：case-01 详细对比
- `evals/.runs/meta_judge_experiment/case-02_comparison.json`：case-02 详细对比
- `evals/.runs/meta_judge_experiment/case-09_comparison.json`：case-09 详细对比
- `evals/.runs/meta_judge_experiment/experiment_summary.json`：聚合结果 + 最终推荐

## 预期结果

基于审计报告的发现，预期 3/3 案例推荐 `retire_regex`：

1. **Case-01**：元裁判应检测到逻辑矛盾（regex 满足但报告前后不一致），`gaming_detected=true`
2. **Case-02**：元裁判应检测到关键词游戏（33.4% 精确、tradeoff 重复），`gaming_detected=true`
3. **Case-09**：元裁判应发现 regex 漏检（测量泄漏未捕获），`unique_value_of_regex=false`

如果实验结果符合预期（3/3 retire），则：
- **Phase 2 跳过**：无需双轨过渡
- **直接进入 Phase 3**：LLM judge 为主，routing/artifacts 保留轻量 regex（仅结构检查）
- **成本预算**：从 ~$0.75/case（L2 agent）增至 ~$0.90/case（agent + judge），增幅 20%

如果出现意外（有案例推荐 keep_regex），则：
- 人工审核该案例的元裁判 rationale
- 判断是否为 judge 误判，或 regex 确有独特价值
- 调整实验设计（增加案例数、优化 judge prompt）

## 成本估算

- **单案例成本**：
  - Regex scorer：$0（确定性）
  - LLM judge：~$0.15（10k tokens × 5 维度 @ Opus 4）
  - Meta-judge：~$0.05（5k tokens @ Opus 4）
  - 合计：~$0.20/case
- **3 案例实验**：~$0.60
- **未来 9 案例全量**：~$1.80

对比现状（L2 agent ~$0.75/case），总成本增幅：
- 开发阶段（频繁评测）：+20%
- CI 阶段（仅 L1 确定性）：$0（judge 不跑 CI）

## 后续行动（基于实验结果）

### 如果推荐 RETIRE REGEX（预期）
1. 保留 routing/artifact 结构检查（must_produce, must_not_produce）
2. 将 findings/charts/anti_patterns 全部改为 LLM judge
3. 更新 `score_case.py --mode judge`（默认模式）
4. 在 10 个案例上重新评分，建立 judge baseline
5. 记录首次 judge 评分至 `results.tsv`（新列 `judge_score`）

### 如果推荐 KEEP REGEX（意外）
1. 分析哪些案例显示 regex 独特价值
2. 设计"混合评分"：regex 用于快速排查，judge 用于最终质量确认
3. 权重分配：0.3 × regex + 0.7 × judge（初期保守）

### 如果 UNCERTAIN
1. 扩展实验至 6 案例（增加 case-03/04/05）
2. 收集人工标注：找 2-3 人独立评分，作为 golden truth
3. 计算 regex 和 judge 与人工标注的一致性
