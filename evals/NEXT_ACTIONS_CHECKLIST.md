# 下一步行动清单

**生成时间**：2026-06-13 20:30  
**当前状态**：Baseline 重建进行中（60% 完成）

---

## ⏰ 今晚（20:30 - 22:00）

### [ ] 1. 监控 baseline 完成
```bash
# 每 10 分钟检查一次
bash evals/monitor_baseline.sh
```

### [ ] 2. 验证 baseline 结果
```bash
# 检查 Case A
cat evals/.runs/baseline-20260613/case-a-score.json | python -m json.tool | grep overall_score

# 检查 Case B
cat evals/.runs/baseline-20260613/case-b-score.json | python -m json.tool | grep overall_score

# 检查 Case C 分析
wc -l evals/.runs/baseline-20260613/case-c/analysis_output.md
```

### [ ] 3. 运行 Case C 评分（如果分析完成）
```bash
python evals/harness/score_two_stage.py \
    evals/cases/case-c-timeseries-routing \
    evals/.runs/baseline-20260613/case-c \
    --runs 3 \
    --json evals/.runs/baseline-20260613/case-c-score.json
```

### [ ] 4. 记录 baseline 结果
创建 `BASELINE_RESULTS_20260613.md`：
```markdown
# Baseline 结果（使用修复后数据）

- Case A: X.X (std=Y.Y)
- Case B: X.X (std=Y.Y)
- Case C: X.X (std=Y.Y)
- **平均**: X.X

## 对比旧 baseline
- 旧平均（审计前）: 83.7
- 新平均（修复后）: X.X
- 差异: ΔX.X
```

### [ ] 5. 提交 baseline 到 git
```bash
git add evals/.runs/baseline-20260613/
git add evals/BASELINE_RESULTS_20260613.md
git commit -m "baseline: 建立可信 baseline（修复后数据 + 新评分器）"
```

---

## 📅 明天上午（9:00 - 12:00）

### [ ] 6. 飞轮第 2 轮 - 迭代 1：参数方法假设检验

**目标**：强制要求 ANOVA/Pearson 前检查假设

**步骤**：
1. 修改 `method-registry.md` ANOVA 章节
   ```markdown
   ## ANOVA
   
   ### MANDATORY Checks Before ANOVA
   1. **Normality**: Shapiro-Wilk test (n<5000) or QQ-plot visual
      - If p<0.05: reject normality → use Kruskal-Wallis
   2. **Homogeneity of variance**: Levene test
      - If p<0.05: reject equal variance → use Welch ANOVA
   3. Report: "ANOVA assumptions checked: normality (p=X.XX), variance homogeneity (p=X.XX)"
   ```

2. 修改 `skill.md` 交叉验证章节（可选）

3. 重跑 Case A：
   ```bash
   cd evals/cases/case-a-manufacturing-comprehensive
   cat prompt.txt | claude -p > ../../.runs/iteration1/case-a/final_report.md
   ```

4. 评分并对比：
   ```bash
   python evals/harness/score_two_stage.py \
       evals/cases/case-a-manufacturing-comprehensive \
       evals/.runs/iteration1/case-a \
       --runs 3 \
       --json evals/.runs/iteration1/case-a-score.json
   
   # 对比
   echo "Baseline: $(cat evals/.runs/baseline-20260613/case-a-score.json | python -c 'import sys,json; print(json.load(sys.stdin)["overall_score"])')"
   echo "Iteration1: $(cat evals/.runs/iteration1/case-a-score.json | python -c 'import sys,json; print(json.load(sys.stdin)["overall_score"])')"
   ```

5. 决策：
   - 如果提升 ≥2 分且无其他维度下降 → commit
   - 否则 → revert，分析原因

---

## 📅 明天下午（14:00 - 18:00）

### [ ] 7. 飞轮第 2 轮 - 迭代 2（如果迭代 1 成功）

**目标**：明确要求交叉验证必须展示结果

**步骤**：见 `FLYWHEEL_ROUND2_PLAN.md` 迭代 2 章节

### [ ] 8. P1-2：验证 Golden Templates 触发逻辑（并行）

**步骤**：
1. 测试 template 触发：
   ```bash
   cat > /tmp/test_template.txt << 'EOF'
   We have yield data. What drives yield? 
   Which process parameters affect defect rate?
   Data: fab_log.csv, metrology.csv, final_test.csv
   EOF
   
   claude -p < /tmp/test_template.txt > /tmp/test_output.txt
   grep -i "template" /tmp/test_output.txt
   ```

2. 诊断并修复

---

## 📅 Week 2-4

### [ ] 9-13. 继续飞轮迭代 3-5
- 迭代 3: 独立性假设检查
- 迭代 4: 样本不平衡评估
- 迭代 5: 边界显著性处理

### [ ] 14-16. P1 任务
- P1-1: Judge 添加数据真值
- P1-3: Judge 稳定性分析

### [ ] 17-19. P2 任务
- P2-1: workflow_adherence 维度
- P2-2: References 更新机制
- P2-3: 多选手对比实验

---

## 🎯 成功标准

**Baseline 重建**：
- ✅ 3 个 case 评分完成
- ✅ 平均分数记录
- ✅ 与旧 baseline 对比

**飞轮第 2 轮**：
- ✅ 平均分数 ≥90
- ✅ 至少完成 3 次迭代
- ✅ 每次迭代有明确的 commit 记录

**P1/P2 改进**：
- ✅ 至少完成 2 个 P1 任务
- ✅ 至少完成 1 个 P2 任务

---

## 📞 需要帮助时

**监控命令**：
```bash
bash evals/monitor_baseline.sh
```

**查看文档**：
- 审计报告: `evals/EVAL_SYSTEM_AUDIT_20260613.md`
- 飞轮计划: `evals/FLYWHEEL_ROUND2_PLAN.md`
- P1/P2 计划: `evals/P1_P2_IMPROVEMENT_PLAN.md`
- 完成总结: `evals/GOALS_COMPLETION_SUMMARY.md`

**Git 历史**：
```bash
git log --oneline --since="2026-06-13"
```

---

**清单生成时间**：2026-06-13 20:30  
**预计完成所有行动**：2-3 周
