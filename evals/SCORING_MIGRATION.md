# 评测系统迁移：从 Regex 到 Agent Judge

## 决策依据

**元裁判评估结果**（3 个案例）：
- Case-01: regex 6/10（逻辑否定误判）
- Case-02: regex 8/10（边缘问题）
- Case-09: regex 4/10（跨文件不一致漏检）
- **结论**：3/3 案例有问题，2/3 严重误判

**Agent Judge 验证**：
- Case-02: Judge 82.4/100 vs Regex 100/100
- Judge 发现 6 个真实缺陷（rigor 4 个，anti-gaming 2 个）
- Regex 全部通过但未捕获方法论问题

## 新评分系统

### 使用方式

```bash
# Agent judge 模式（推荐，无需 API key）
python evals/harness/score_case.py <case_dir> <run_dir> --mode judge --json score.json

# Regex 模式（legacy，仅用于快速筛查）
python evals/harness/score_case.py <case_dir> <run_dir> --mode regex

# 混合模式（0.4×regex + 0.6×judge）
python evals/harness/score_case.py <case_dir> <run_dir> --mode hybrid
```

### Judge 评分维度

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| correctness | 5.0 | 结论与 ground truth 一致性、数值合理性 |
| completeness | 3.0 | 覆盖所有 required findings、负向结论报告 |
| rigor | 4.0 | 方法适配性、交叉验证、泄漏/混杂处理、假设检查 |
| clarity | 2.0 | 因果链条清晰、量化支撑、图表呼应 |
| anti_gaming | 3.0 | 关键词堆砌检测、数值精确匹配检测、逻辑矛盾检测、"形似神不似"检测 |

每维度 0-3 分，总分归一化至 0-100。

### 技术实现

**Agent spawn 方式**（无需 API key）：
```python
result = subprocess.run(
    ["claude"],
    input=judge_prompt,
    capture_output=True,
    text=True
)
```

每个案例 spawn 5 个 agent（一维度一 agent），每个 agent ~30 秒，总耗时 ~2-3 分钟。

## 迁移路径

### Phase 1: 影子运行（当前）✅
- Judge 与 regex 并行运行，对比结果
- 已完成：case-02 验证（judge 82.4 vs regex 100）
- 发现：judge 更严格，捕获方法论缺陷

### Phase 2: Judge 为主（进行中）
- 默认使用 `--mode judge`
- 在 6 个饱和案例重新评分，建立 judge baseline
- 记录 judge 分数至 `results.tsv`（新列 `judge_score`）

### Phase 3: Regex 退役
- 保留 routing/schema 结构检查（must_produce artifacts）
- 移除 findings/anti_patterns 的 regex 匹配
- Judge 成为唯一语义评分器

## 对比示例：Case-02

### Regex 评分（100/100）
```
[PASS] finding  conversion_positive
[PASS] finding  engagement_negative  
[PASS] finding  tradeoff_acknowledged
[PASS] finding  conditional_recommendation
[PASS] finding  effect_size_with_ci
```
**问题**：全部通过，但未检查方法论深度。

### Judge 评分（82.4/100）
```
[correctness  ] 3/3  完全满足，数值合理有CI
[completeness ] 3/3  覆盖全部发现，负向结论明确
[rigor        ] 2/3  缺协变量平衡、分布检验、泄漏排查、时序讨论
[clarity      ] 2/3  因果清晰、量化完整，但缺图表
[anti_gaming  ] 2/3  声称多方法验证但未独立展示结果（"形似神不似"）
```
**发现**：6 个真实缺陷，包括"声称执行但缺乏证据"的关键问题。

## 成本与收益

### 成本
- 单案例：~2-3 分钟（5 agents × ~30 秒）
- Token：0（使用 claude CLI，继承 session 凭证）
- 开发体验：无需配置 API key

### 收益
- 准确性：捕获 regex 漏检的方法论缺陷
- 反游戏：识别"关键词拼凑"和"形似神不似"
- 可解释性：每维度提供 rationale + evidence + defects

## 后续行动

1. ✅ 实现 agent judge（judge_score.py）
2. ✅ 集成到 score_case.py（--mode flag）
3. ✅ 验证 case-02（82.4/100，发现 6 缺陷）
4. 🔄 在 6 个饱和案例运行 judge，建立 baseline
5. 📝 更新 README/evals/README 文档
6. 🎯 将 `--mode judge` 设为默认
