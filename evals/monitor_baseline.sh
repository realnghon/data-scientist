#!/bin/bash
# Baseline 重建进度监控

echo "===== Baseline 重建进度监控 ====="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查运行中的进程
echo "【运行中的任务】"
ps aux | grep -E "score_two_stage|claude -p" | grep -v grep | awk '{print "PID " $2 ": " $11 " " $12 " " $13}' || echo "  无活跃任务"
echo ""

# 检查输出文件
echo "【输出文件状态】"
BASELINE_DIR="evals/.runs/baseline-20260613"

if [ -f "$BASELINE_DIR/case-a-score.json" ]; then
    score=$(cat "$BASELINE_DIR/case-a-score.json" | python -c "import sys, json; print(json.load(sys.stdin)['overall_score'])" 2>/dev/null)
    echo "  ✅ Case A 评分完成: $score"
else
    echo "  ⏳ Case A 评分进行中..."
fi

if [ -f "$BASELINE_DIR/case-b-score.json" ]; then
    score=$(cat "$BASELINE_DIR/case-b-score.json" | python -c "import sys, json; print(json.load(sys.stdin)['overall_score'])" 2>/dev/null)
    echo "  ✅ Case B 评分完成: $score"
else
    echo "  ⏳ Case B 评分进行中..."
fi

if [ -f "$BASELINE_DIR/case-c/analysis_output.md" ]; then
    lines=$(wc -l < "$BASELINE_DIR/case-c/analysis_output.md")
    echo "  ✅ Case C 分析完成: $lines 行"
else
    echo "  ⏳ Case C 分析进行中..."
fi

echo ""
echo "【预计完成时间】"
echo "  Case A & B 评分: ~45 分钟（3次 × 15分钟）"
echo "  Case C 分析: ~10-15 分钟"
echo "  Case C 评分: +45 分钟"
echo "  总计: ~1.5-2 小时"
