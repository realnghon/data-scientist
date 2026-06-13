#!/bin/bash
# 所有任务进度监控

echo "===== 所有任务进度监控 ====="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Baseline 重建任务
echo "【目标 2: Baseline 重建】"
BASELINE_DIR="evals/.runs/baseline-20260613"

if [ -f "$BASELINE_DIR/case-a-score.json" ]; then
    score=$(cat "$BASELINE_DIR/case-a-score.json" | python -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['overall_score']:.1f} (std={d.get('judge_std',0):.1f})\")" 2>/dev/null)
    echo "  ✅ Case A: $score"
else
    echo "  ⏳ Case A 评分进行中..."
fi

if [ -f "$BASELINE_DIR/case-b-score.json" ]; then
    score=$(cat "$BASELINE_DIR/case-b-score.json" | python -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['overall_score']:.1f} (std={d.get('judge_std',0):.1f})\")" 2>/dev/null)
    echo "  ✅ Case B: $score"
else
    echo "  ⏳ Case B 评分进行中..."
fi

if [ -f "$BASELINE_DIR/case-c/analysis_output.md" ] && [ -s "$BASELINE_DIR/case-c/analysis_output.md" ]; then
    lines=$(wc -l < "$BASELINE_DIR/case-c/analysis_output.md")
    echo "  ✅ Case C 分析完成: $lines 行"

    if [ -f "$BASELINE_DIR/case-c-score.json" ]; then
        score=$(cat "$BASELINE_DIR/case-c-score.json" | python -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['overall_score']:.1f} (std={d.get('judge_std',0):.1f})\")" 2>/dev/null)
        echo "  ✅ Case C 评分: $score"
    else
        echo "  ⬜ Case C 评分：待启动"
    fi
else
    echo "  ⏳ Case C 分析进行中..."
fi

echo ""

# 2. 飞轮迭代 1
echo "【目标 3: 飞轮第 2 轮 - 迭代 1】"
ITER1_DIR="evals/.runs/flywheel-iter1/case-a"

if [ -f "$ITER1_DIR/final_report.md" ] && [ -s "$ITER1_DIR/final_report.md" ]; then
    lines=$(wc -l < "$ITER1_DIR/final_report.md")
    echo "  ✅ Case A 分析完成: $lines 行"

    if [ -f "evals/.runs/flywheel-iter1/case-a-score.json" ]; then
        score=$(cat "evals/.runs/flywheel-iter1/case-a-score.json" | python -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['overall_score']:.1f} (std={d.get('judge_std',0):.1f})\")" 2>/dev/null)
        echo "  ✅ Case A 评分: $score"
    else
        echo "  ⬜ Case A 评分：待启动"
    fi
else
    echo "  ⏳ Case A 分析进行中..."
fi

echo ""

# 3. P1-2 Template 测试
echo "【目标 4: P1-2 Template 触发测试】"
if [ -f "/tmp/test_template_output.txt" ] && [ -s "/tmp/test_template_output.txt" ]; then
    lines=$(wc -l < "/tmp/test_template_output.txt")
    echo "  ✅ Template 测试完成: $lines 行"

    # 检查是否提到 template
    if grep -qi "template" /tmp/test_template_output.txt; then
        echo "  ✅ Template 被触发！"
    else
        echo "  ❌ Template 未被触发"
    fi
else
    echo "  ⏳ Template 测试进行中..."
fi

echo ""
echo "【活跃进程】"
ps aux | grep -E "claude -p|score_two_stage" | grep -v grep | wc -l | xargs echo "  claude 进程数:"
