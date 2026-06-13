# P1/P2 改进任务计划

**目标**：在飞轮迭代的同时，并行推进评测系统的中长期改进

---

## P1 任务（高优先级，3-5 天）

### P1-1: Judge 添加数据真值 ⭐

**目标**：Judge 评分时提供数据真值，用于验证数值准确性

**当前问题**：
- Judge 只看 GT 的 findings 列表
- 不知道实际数据中 cd_nm=82.2, yield=67.4%
- 选手报告 "cd_nm=85nm" 时无法判断准确性

**实现方案**：

1. **GT 添加 expected_values 字段**（已在审计报告中设计）：
   ```json
   {
     "id": "chamber_c2_root_cause",
     "expected_values": {
       "cd_nm_c2": {"value": 82, "tolerance": [80, 84], "unit": "nm"},
       "yield_c2": {"value": 67, "tolerance": [65, 70], "unit": "%"}
     }
   }
   ```

2. **judge_score.py 修改**：
   ```python
   # L72-78，在 gt_context 中添加预期数值
   if dimension in ["correctness", "completeness"]:
       gt_context += "\n\n预期数值（用于验证准确性）:\n"
       for f in ground_truth.get("findings", []):
           if "expected_values" in f:
               gt_context += f"  {f['id']}:\n"
               for key, val in f["expected_values"].items():
                   gt_context += f"    - {key}: {val['value']} {val['unit']} "
                   gt_context += f"(容差 {val['tolerance']})\n"
   ```

**验证**：
- Judge 能检测出数值偏差（如报告 85nm 而实际 82nm）
- Correctness 维度更精准

**工作量**：1-2 天
**优先级**：P1（影响 correctness 评分准确性）

---

### P1-2: 验证 Golden Templates 触发逻辑

**目标**：定位为何 templates 从未被触发，修复或验证其有效性

**当前问题**：
- `golden-templates.md` 有 3 个精心设计的模板
- 所有运行中 0 次提到 "template"
- 不知道 templates 是否真的有效

**实现方案**：

**步骤 1：测试 template 触发**
```bash
# 修改 Case A prompt，明确触发 Template A
cat > /tmp/test_template_trigger.txt << 'EOF'
We have yield data from our manufacturing line. 
What drives yield? Which process parameters affect defect rate?

Data: fab_log.csv, metrology.csv, final_test.csv
EOF

# 运行分析
claude -p < /tmp/test_template_trigger.txt > /tmp/test_template_output.txt

# 检查是否提到 template
grep -i "template\|golden" /tmp/test_template_output.txt
```

**步骤 2：诊断原因**
- 如果触发成功 → prompt 措辞问题，更新 case prompts
- 如果仍未触发 → 检查 SKILL.md L235 指令优先级
- 如果 workflow.md 抢占 → 调整指令顺序

**步骤 3：修复**
- 方案 A：更新 case prompts，使用 template trigger 语言
- 方案 B：SKILL.md 增强 template 检查指令
- 方案 C：如果 templates 不适配，标记为"参考而非强制"

**验证**：
- 至少 1 个 case 触发 template
- 报告中提到 "matched Template X"
- workflow_adherence 维度（如果已添加）提升

**工作量**：1-2 天
**优先级**：P1（验证 references 有效性）

---

### P1-3: Judge 稳定性分析

**目标**：量化 judge 评分的非确定性，优化运行次数

**当前问题**：
- Judge 运行 3 次取中位数（经验值）
- 不知道 3 次是否足够
- 不知道哪些维度的非确定性更高

**实现方案**：

**实验设计**：
1. 选择 Case A（已有报告）
2. 运行 judge 评分 10 次
3. 记录每次的 5 维度分数
4. 计算每个维度的标准差

**分析指标**：
```python
# 对 10 次运行结果分析
for dimension in ['correctness', 'completeness', 'rigor', 'clarity', 'anti_gaming']:
    scores = [run[dimension]['score'] for run in results]
    print(f"{dimension}: mean={np.mean(scores):.2f}, std={np.std(scores):.2f}")
    print(f"  Range: {min(scores)}-{max(scores)}")
    print(f"  3-run vs 5-run vs 10-run median 差异")
```

**决策标准**：
- 如果所有维度 std <0.5 → 3 次足够
- 如果某维度 std >1.0 → 该维度定义模糊，需优化 criteria
- 如果总体 std >5 → 增加到 5 次运行

**验证**：
- 输出稳定性报告
- 更新 `score_two_stage.py` 默认运行次数

**工作量**：1 天
**优先级**：P1（确保评分可靠性）

---

## P2 任务（中优先级，1-2 周）

### P2-1: 添加 workflow_adherence 维度

**目标**：验证 Agent 是否遵循 references 指导

**当前问题**：
- Judge 只评估"结果正确"，不评估"流程正确"
- 不知道 references 是否真的被使用
- Golden templates 从未触发可能与此相关

**实现方案**：

1. **judge_score.py 添加第 6 维度**：
   ```python
   JUDGE_DIMENSIONS = {
       # ... 现有 5 个维度 ...
       "workflow_adherence": {
           "weight": 2.0,
           "criteria": [
               "是否产出 workflow.md 要求的 Tier-0 artifacts",
               "是否执行了 readiness 的 8 维度评估",
               "是否在 analysis_plan 中记录了 method selection 逻辑",
               "是否检查了 golden-templates（如适用）"
           ]
       }
   }
   ```

2. **提供 artifacts 上下文**：
   ```python
   if dimension == "workflow_adherence":
       artifacts_found = list((run_dir).glob("*.json")) + list((run_dir).glob("*.md"))
       gt_context += f"\n\n产出的 artifacts: {[a.name for a in artifacts_found]}\n"
       gt_context += f"期望的 artifacts: {gt['routing']['must_produce_artifacts']}\n"
   ```

**验证**：
- Judge 能识别缺失的 artifacts
- 能识别未执行的 workflow 步骤
- 提升对 references 使用情况的可见性

**工作量**：2-3 天
**优先级**：P2（提升流程质量，但不影响结果正确性）

---

### P2-2: 建立 References 更新触发机制

**目标**：自动识别 references 覆盖缺口，触发内容增强

**当前问题**：
- References 从未因评测而更新
- 不知道哪些方法指导缺失
- 无法系统性提升 references 质量

**实现方案**：

**脚本**：`evals/detect_references_gaps.py`
```python
"""
分析 judge defects 并识别 references 覆盖缺口
"""
import json
from pathlib import Path
from collections import Counter

def analyze_defects(runs_dir: Path):
    """统计所有运行中的 defects，按 dimension 分组"""
    defects_by_dim = {}
    
    for summary in runs_dir.glob("*/summary.json"):
        data = json.loads(summary.read_text())
        for case_result in data.get("cases", []):
            for defect in case_result.get("defects", []):
                dim = defect["dimension"]
                text = defect["defect"]
                if dim not in defects_by_dim:
                    defects_by_dim[dim] = []
                defects_by_dim[dim].append(text)
    
    # 聚类相似 defects
    for dim, defects in defects_by_dim.items():
        print(f"\n=== {dim} 维度高频缺陷 ===")
        counter = Counter(defects)
        for defect, count in counter.most_common(5):
            print(f"  [{count}x] {defect[:80]}...")
            
            # 映射到 references 章节
            if "假设" in defect or "assumption" in defect.lower():
                print(f"    → 检查 method-registry.md 假设检验章节")
            elif "季节性" in defect or "seasonal" in defect.lower():
                print(f"    → 检查 time_series.md 季节性分析章节")
            # ... 更多启发式规则
```

**触发规则**：
- 同一类 defect 出现 ≥3 次 → 标记为"系统性缺口"
- 积累 3 个系统性缺口 → 触发 references 内容增强
- 更新后重新评测验证修复效果

**验证**：
- 输出 references 覆盖缺口报告
- 触发至少 1 次 references 更新
- 验证更新后 defects 减少

**工作量**：2-3 天
**优先级**：P2（长期质量提升）

---

### P2-3: 多选手对比实验

**目标**：建立难度基准，识别哪些 findings 是所有选手都漏的硬题

**当前问题**：
- 只有 Claude Opus 4.8 一个选手
- 不知道某些 defects 是 model 问题还是 SKILL 问题
- 无法建立跨模型的难度基准

**实现方案**：

**脚本**：`evals/multi_model_comparison.sh`
```bash
#!/bin/bash
# 对比不同模型在同一 case 上的表现

CASE="case-a"
MODELS=("opus" "sonnet" "haiku")

for MODEL in "${MODELS[@]}"; do
    echo "=== Running $MODEL on $CASE ==="
    
    # 设置模型（需要环境变量或配置）
    export CLAUDE_MODEL=$MODEL
    
    # 运行评测
    python evals/harness/run_single_case.py $CASE \
        --output-dir evals/.runs/multi-model/$MODEL
    
    # 评分
    python evals/harness/score_two_stage.py \
        evals/cases/$CASE \
        evals/.runs/multi-model/$MODEL/$CASE \
        --runs 3 \
        --json evals/.runs/multi-model/${MODEL}_score.json
done

# 对比结果
python evals/compare_models.py evals/.runs/multi-model
```

**分析输出**：
```
Model Comparison Report:
  Opus 4.8: 82.4 (correctness=2, rigor=2)
  Sonnet 4.6: 78.1 (correctness=2, rigor=1)
  Haiku 4.5: 65.3 (correctness=1, rigor=1)

Common defects (all models):
  - 参数方法假设未检验 (3/3 models)
  - 交叉验证不完整 (3/3 models)
  → 这些是 SKILL 问题，需要增强指导

Model-specific defects:
  - 交互效应检测 (0/3 Haiku, 1/3 Sonnet, 2/3 Opus)
  → 这是 model capability 问题，不是 SKILL 问题
```

**验证**：
- 识别 SKILL 问题 vs model capability 问题
- 建立跨模型的难度基准
- 优先修复"所有模型都漏"的 defects

**工作量**：3-4 天
**优先级**：P2（研究性质，非紧急）

---

## 任务优先级总结

| 任务 | 优先级 | 工作量 | 影响 | 建议时间 |
|------|--------|--------|------|----------|
| P1-1: Judge 数据真值 | ⭐⭐⭐ | 1-2 天 | Correctness 准确性 | Week 2 |
| P1-2: Templates 触发验证 | ⭐⭐⭐ | 1-2 天 | References 有效性 | Week 2 |
| P1-3: Judge 稳定性分析 | ⭐⭐ | 1 天 | 评分可靠性 | Week 2 |
| P2-1: workflow_adherence | ⭐⭐ | 2-3 天 | 流程质量 | Week 3 |
| P2-2: References 更新机制 | ⭐ | 2-3 天 | 长期质量 | Week 3 |
| P2-3: 多选手对比 | ⭐ | 3-4 天 | 研究洞察 | Week 4 |

---

## 并行执行策略

**Week 2（飞轮第 2 轮 + P1 并行）**：
- 白天：飞轮迭代（修复 SKILL.md）
- 晚上：P1 任务（judge 数据真值、templates 验证）

**Week 3（P2 任务）**：
- workflow_adherence 维度添加
- References 更新机制建立

**Week 4（可选）**：
- 多选手对比实验

---

**更新时间**：2026-06-13 20:25  
**预计启动**：Baseline 完成后，与飞轮第 2 轮并行
