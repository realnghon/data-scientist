# 评测系统修复清单

基于 2026-06-13 审计报告，按优先级排序的修复任务。

---

## ✅ P0 — 阻断性问题（必须立即修复）

### [ ] 1. 修复 Case C 尖峰信号生成

**文件**：`evals/cases/case-c-timeseries-routing/generate_data.py`

**修改**：
```python
# 行 75-76，将尖峰幅度从 ±20-25 提升到 ±60
if i in spike_idx:
    value += np.random.choice([60, -60])  # 原来是 [25, -20]
```

**验证**：
```bash
cd evals/cases/case-c-timeseries-routing
python generate_data.py
python -c "
import pandas as pd
import numpy as np
df = pd.read_csv('sensor_readings.csv')
valid = df[df['sensor_value'].notna()]
q1, q3 = valid['sensor_value'].quantile([0.25, 0.75])
iqr = q3 - q1
outliers = valid[(valid['sensor_value'] < q1 - 1.5*iqr) | (valid['sensor_value'] > q3 + 1.5*iqr)]
print(f'IQR 离群点: {len(outliers)} 个（期望 8-15）')
"
```

**接受标准**：IQR 方法检出 8-15 个离群点

---

### [ ] 2. Ground Truth 添加权重和分级

**文件**：
- `evals/cases/case-a-manufacturing-comprehensive/ground_truth.json`
- `evals/cases/case-b-business-tradeoff/ground_truth.json`
- `evals/cases/case-c-timeseries-routing/ground_truth.json`

**修改**：为每个 finding 添加 `tier` 和 `weight` 字段

**Case A 示例**：
```json
{
  "findings": [
    {
      "id": "chamber_c2_root_cause",
      "tier": "required",
      "weight": 5.0,
      "type": "claim",
      "feature": "root_cause",
      "evidence_regex": "..."
    },
    {
      "id": "cd_nm_mechanism",
      "tier": "required",
      "weight": 4.0,
      "type": "claim",
      "feature": "mechanism",
      "evidence_regex": "..."
    },
    {
      "id": "interaction_effect",
      "tier": "optional",
      "weight": 2.0,
      "type": "claim",
      "feature": "interaction",
      "evidence_regex": "...",
      "note": "p~0.05 边界不稳定，允许未检出"
    },
    {
      "id": "noise_rejected",
      "tier": "recommended",
      "weight": 2.0,
      "type": "negative_claim",
      "feature": "noise",
      "evidence_regex": "..."
    }
  ]
}
```

**分级标准**：
- `required`: 核心发现，漏掉严重扣分（root cause, 主效应）
- `recommended`: 重要但非致命（noise rejection, 交叉验证）
- `optional`: 加分项（边界不稳定的交互效应，可选深度分析）

**权重建议**：
- Root cause: 5.0
- Mechanism: 4.0
- Quality checks (stratification, multi-table join): 3.0
- Negative findings: 2.0
- Optional deep dives: 1.0-2.0

---

### [ ] 3. Regex 评分改为初筛

**文件**：`evals/harness/run_l2.py` (或创建新的评分编排脚本)

**修改逻辑**：
```python
def score_case_two_stage(case_dir, run_dir):
    """两阶段评分：Regex 初筛 + Judge 主评"""
    
    # Stage 1: Regex 初筛（快速）
    regex_result = regex_score.score_case(case_dir, run_dir)
    
    # 计算 required findings 覆盖率
    gt = json.loads((case_dir / "ground_truth.json").read_text())
    required_findings = [f for f in gt["findings"] if f.get("tier") == "required"]
    required_matched = sum(1 for f in required_findings if regex_result["matched"].get(f["id"]))
    coverage = required_matched / len(required_findings) if required_findings else 0
    
    # Coverage < 50% 直接失败
    if coverage < 0.5:
        return {
            "overall_score": 0,
            "stage": "regex_initial_screen",
            "reason": f"Required findings coverage {coverage:.1%} < 50%",
            "regex_result": regex_result
        }
    
    # Stage 2: Judge 评分（慢但准确）
    print(f"Regex coverage {coverage:.1%} ≥ 50%, entering judge scoring...")
    judge_results = []
    for run in range(3):  # 运行 3 次取中位数
        result = judge_score.score_case_with_agent_judge(case_dir, run_dir)
        judge_results.append(result["overall_score"])
        print(f"  Run {run+1}/3: {result['overall_score']}")
    
    median_score = sorted(judge_results)[1]
    
    return {
        "overall_score": median_score,
        "judge_scores_raw": judge_results,
        "judge_std": np.std(judge_results),
        "regex_coverage": coverage,
        "stage": "judge_final"
    }
```

**验证**：
- 低覆盖报告应该立即失败
- 高覆盖报告进入 judge，运行 3 次

---

## ⚠️ P1 — 高优先级（提升评测质量）

### [ ] 4. Ground Truth 添加预期数值

**文件**：`evals/cases/case-a-manufacturing-comprehensive/ground_truth.json`

**添加**：
```json
{
  "findings": [
    {
      "id": "chamber_c2_root_cause",
      "expected_values": {
        "cd_nm_c2": {"value": 82, "tolerance": [80, 84], "unit": "nm"},
        "cd_nm_others": {"value": 90, "tolerance": [88, 92], "unit": "nm"},
        "yield_c2": {"value": 67, "tolerance": [65, 70], "unit": "%"},
        "yield_others": {"value": 90, "tolerance": [88, 92], "unit": "%"}
      },
      "...": "..."
    }
  ]
}
```

**同步修改**：`evals/harness/judge_score.py`
```python
# L72-78，在 gt_context 中添加预期数值
if dimension in ["correctness", "completeness"]:
    gt_context += "\n\n预期发现:\n"
    for f in ground_truth.get("findings", []):
        gt_context += f"  - {f['id']}: {f.get('feature', 'N/A')} ({f['type']})\n"
        if "expected_values" in f:
            gt_context += f"    预期数值: {json.dumps(f['expected_values'], ensure_ascii=False)}\n"
```

---

### [ ] 5. 验证 Golden Templates 触发逻辑

**测试脚本**：`evals/test_template_trigger.sh`
```bash
#!/bin/bash
# 测试 Golden Template 是否被触发

cd /path/to/data-scientist

# 修改 Case A prompt，明确触发 Template A
cat > /tmp/test_prompt.txt << 'EOF'
We have yield data from our manufacturing line. What drives yield? 
Which process parameters and equipment settings affect defect rate?

Data: fab_log.csv, metrology.csv, final_test.csv
EOF

# 运行分析
claude -p < /tmp/test_prompt.txt > /tmp/test_output.txt

# 检查是否提到 template
if grep -i "template\|golden" /tmp/test_output.txt; then
    echo "✅ Template 被触发"
else
    echo "❌ Template 未被触发 — 需要调查原因"
fi

# 检查 analysis_plan 是否记录了 template
if grep -r "template_used" /tmp/; then
    echo "✅ analysis_plan 记录了 template 使用"
else
    echo "⚠️ analysis_plan 未记录 template"
fi
```

**调查方向**：
1. SKILL.md L235 的指令是否足够明确？
2. Workflow.md 是否抢占了 template 检查？
3. Prompt 措辞是否匹配 trigger conditions？

---

### [ ] 6. Judge 评分运行 3 次取中位数

**已包含在 P0-3 中**

---

## 🔹 P2 — 中优先级（完善评测）

### [ ] 7. 添加 workflow_adherence 维度

**文件**：`evals/harness/judge_score.py`

**添加第 6 维度**：
```python
JUDGE_DIMENSIONS = {
    # ... 现有 5 个维度 ...
    "workflow_adherence": {
        "weight": 2.0,
        "criteria": [
            "是否产出 workflow.md 要求的 Tier-0 artifacts (data_manifest, analysis_plan, final_report)",
            "是否执行了 readiness 的 8 维度评估（在 readiness_report 或报告中可见）",
            "是否在 analysis_plan 中记录了 data_transformations 和 method selection 逻辑",
            "是否检查了 golden-templates（如适用）或明确说明为何不适用"
        ]
    }
}
```

**修改 prompt**：
```python
# L88-92，添加 artifacts 上下文
if dimension == "workflow_adherence":
    artifacts_found = list((run_dir).glob("*.json")) + list((run_dir).glob("*.md"))
    gt_context += f"\n\n产出的 artifacts: {[a.name for a in artifacts_found]}\n"
    gt_context += f"期望的 artifacts: {ground_truth['routing']['must_produce_artifacts']}\n"
```

---

### [ ] 8. 建立 References 更新触发机制

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
            
            # 检查是否在 references 中有明确指导
            if "交互效应" in defect:
                print(f"    → 检查 method-registry.md 是否有交互效应检测指导")
            elif "季节性" in defect:
                print(f"    → 检查 workflow.md 时序分析部分是否完整")
            # ... 更多启发式规则

if __name__ == "__main__":
    analyze_defects(Path("evals/.runs/l2"))
```

**手动流程**：
1. 运行脚本识别高频缺陷
2. 对于出现 3+ 次的同类缺陷，检查对应 reference 是否有指导
3. 如果缺失，添加到 reference 对应章节
4. 重新运行评测验证修复效果

---

### [ ] 9. 多选手对比实验

**脚本**：`evals/multi_model_comparison.sh`
```bash
#!/bin/bash
# 对比不同模型在同一 case 上的表现

CASE="case-a"
MODELS=("opus" "sonnet" "haiku")

for MODEL in "${MODELS[@]}"; do
    echo "=== Running $MODEL on $CASE ==="
    
    # 设置模型
    export CLAUDE_MODEL=$MODEL
    
    # 运行评测
    python evals/harness/run_l2.py $CASE --jobs 1 --output-suffix $MODEL
    
    echo ""
done

# 对比结果
echo "=== Model Comparison ==="
python -c "
import json
from pathlib import Path

for model in ['opus', 'sonnet', 'haiku']:
    result_file = Path(f'evals/.runs/l2/latest-{model}/summary.json')
    if result_file.exists():
        data = json.load(open(result_file))
        score = data['cases'][0]['overall_score']
        print(f'{model:10s}: {score:.1f}')
"
```

---

## 📝 完成后检查清单

### P0 完成标准
- [ ] Case C 生成器验证通过（8-15 个离群点）
- [ ] 所有 findings 都有 tier 和 weight
- [ ] Regex 初筛逻辑上线并测试通过
- [ ] 重新运行 3-case baseline，得到新的可信分数

### P1 完成标准
- [ ] Ground Truth 包含 expected_values
- [ ] Judge prompt 中提供了数据真值
- [ ] Golden Templates 触发逻辑被验证或修复
- [ ] Judge 运行 3 次，记录了标准差

### P2 完成标准
- [ ] workflow_adherence 维度上线
- [ ] 至少 1 次 references 更新来自评测发现的缺口
- [ ] 完成 1 次多模型对比实验

---

## 时间估算

- **P0（阻断性）**：2-3 天
- **P1（高优先级）**：3-5 天
- **P2（中优先级）**：1-2 周
- **重建 baseline + 飞轮第 2 轮**：1 周

**总计**：约 3-4 周完成全部修复并验证

---

## 依赖关系

```
P0-1 (修复 Case C) 
  ↓
P0-2 (添加权重分级)
  ↓
P0-3 (Regex 初筛)
  ↓
重建 Baseline ← P1-4 (添加预期数值) 并行
  ↓
P1-5 (验证 Templates) 并行
  ↓
飞轮第 2 轮
  ↓
P2-7/8/9 (workflow_adherence + references gap + 多模型) 并行
```

建议：**先完成 P0，立即重建 baseline，再并行推进 P1/P2**

---

**审计报告**：`EVAL_SYSTEM_AUDIT_20260613.md`  
**执行摘要**：`AUDIT_EXECUTIVE_SUMMARY.md`  
**本清单**：`AUDIT_FIX_CHECKLIST.md`
