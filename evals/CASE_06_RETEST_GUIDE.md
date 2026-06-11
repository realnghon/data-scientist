# Case-06 重新评测指南

## 问题回顾
- **发现时间**：2026-06-12
- **问题**：`evals/cases/case-06-routing-profile-only/dataset.csv` 被5行玩具数据覆盖
- **影响**：评分从 100 → 84（`missingness_noted` 失败）
- **修复**：删除玩具数据，恢复指向 `examples/manufacturing_yield/dataset.csv`（commit 95b4ee9）

## 验证步骤

### 1. 运行 profile 分析（生成新运行记录）

```bash
cd /Users/silaswu/Silas_Develop/data-scientist

# 创建运行目录
RUN_DIR="evals/.runs/l2/case-06-retest-$(date +%Y%m%d%H%M)"
mkdir -p "$RUN_DIR"

# 复制 prompt 和数据引用
cp evals/cases/case-06-routing-profile-only/prompt.txt "$RUN_DIR/"
cp evals/cases/case-06-routing-profile-only/ground_truth.json "$RUN_DIR/"

# 方法1：使用 claude 命令（推荐）
cd "$RUN_DIR"
claude -p "$(cat prompt.txt)" --output-dir . 2>&1 | tee analysis.log

# 方法2：使用 profile_dataset.py 脚本（快速但不完整）
python plugins/data-scientist/skills/analysis-workflow/scripts/profile_dataset.py \
  examples/manufacturing_yield/dataset.csv \
  --output "$RUN_DIR/data_manifest.json" \
  --readiness "$RUN_DIR/readiness_report.json"
```

### 2. 评分

```bash
python evals/harness/score_case.py \
  evals/cases/case-06-routing-profile-only \
  "$RUN_DIR" \
  --json "$RUN_DIR/score.json"
```

**预期结果**：
```
score=100.0  (8/8 checks)
- [PASS] missingness_noted: matched  # 应该检测到 humidity_pct 1% missing
```

### 3. 对比验证

```bash
# 对比新旧评分
echo "旧版 (20260610):" && cat evals/.runs/l2/case-06-routing-profile-only-20260610/score.json | jq .score
echo "失败版 (20260612):" && cat evals/.runs/l2/case-06-profile-20260612-0011/score.json | jq .score
echo "修复版 (retest):" && cat "$RUN_DIR/score.json" | jq .score

# 查看 missingness 检查细节
cat "$RUN_DIR/score.json" | jq '.checks[] | select(.id=="missingness_noted")'
```

## 关键检查点

### Ground Truth 要求
```json
{
  "id": "missingness_noted",
  "evidence_regex": "(humidity)[^\\n]{0,160}(missing|缺失|NaN|1\\.?[0-9]?%)"
}
```

### 数据验证
```bash
# 确认使用正确的数据文件
head -1 examples/manufacturing_yield/dataset.csv | grep humidity_pct
# 应输出：run_id,date,temperature_c,pressure_psi,humidity_pct,...

# 确认缺失率
python -c "
import pandas as pd
df = pd.read_csv('examples/manufacturing_yield/dataset.csv')
print(f'humidity_pct missing: {df.humidity_pct.isna().sum()} / {len(df)} = {df.humidity_pct.isna().mean()*100:.1f}%')
"
# 应输出：humidity_pct missing: 7 / 500 = 1.4%
```

### 报告验证
运行后检查 `readiness_report.json` 应包含：
```json
{
  "dimensions": [
    {
      "dimension": "missingness_pattern",
      "status": "ok",
      "evidence": "...humidity_pct...1.4%...",
      ...
    }
  ]
}
```

## 如果评分仍失败

### 调试步骤
1. **检查数据路径解析**：
   ```bash
   # ground_truth.json 中的相对路径
   cat evals/cases/case-06-routing-profile-only/ground_truth.json | jq .dataset
   # 输出：../../../examples/manufacturing_yield/dataset.csv
   
   # 从 case 目录解析
   ls -la evals/cases/case-06-routing-profile-only/../../../examples/manufacturing_yield/dataset.csv
   ```

2. **手动运行正则匹配**：
   ```bash
   # 提取 readiness_report 文本
   cat "$RUN_DIR/readiness_report.json" | jq -r . > /tmp/readiness.txt
   
   # 测试正则
   grep -P '(humidity)[^\n]{0,160}(missing|缺失|NaN|1\.?[0-9]?%)' /tmp/readiness.txt
   ```

3. **对比旧版成功案例**：
   ```bash
   # 查看旧版如何通过的
   cat evals/.runs/l2/case-06-routing-profile-only-20260610/readiness_report.json | \
     jq '.dimensions[] | select(.dimension=="missingness_pattern")'
   ```

## 成功标准
- ✅ Score: 100/100
- ✅ 8/8 checks passed
- ✅ `missingness_noted` 匹配到 "humidity" + "1.4%" 或类似表述

## 更新评测记录
成功后更新 `evals/results.tsv`：
```bash
echo "$(date -Iseconds)\t$(git rev-parse --short HEAD)\tdata-scientist\t84.0\t100.0\tkeep\tcase-06数据修复\tRemoved toy dataset masking manufacturing data; humidity missingness now detected\tl2" >> evals/results.tsv
```

## 提交
```bash
git add evals/CURRENT_STATUS.md evals/results.tsv
git commit -m "fix(case-06): verify repair - 84→100 after removing toy dataset"
git push
```
