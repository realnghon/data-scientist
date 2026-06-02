#!/usr/bin/env python3
"""
Darwin 批量评估脚本 - 快速评估所有组件的结构维度分数
"""

import json
from pathlib import Path

# 评分逻辑（基于文件特征的启发式评分）
def quick_score_component(filepath, content):
    """快速评估一个组件的 9 维度分数"""
    lines = content.split('\n')

    scores = {}

    # Dim 1: Frontmatter (权重 7)
    has_frontmatter = content.startswith('---\nname:')
    scores['dim1'] = 8 if has_frontmatter else 2

    # Dim 2: 工作流清晰度 (权重 12)
    has_numbered_steps = any('## ' in l or '### ' in l for l in lines[:50])
    has_stages = 'Stage' in content or 'Phase' in content or 'Step' in content
    scores['dim2'] = 9 if has_stages and has_numbered_steps else 7

    # Dim 3: 失败模式 (权重 12)
    has_failure_section = any('failure' in l.lower() or 'error' in l.lower() for l in lines)
    has_if_then = content.count('if ') + content.count('If ') + content.count('→')
    scores['dim3'] = 9 if (has_failure_section and has_if_then > 5) else 6

    # Dim 4: 检查点 (权重 6)
    has_checkpoint_markers = '🔴' in content or 'CHECKPOINT' in content or '🛑' in content
    has_stop_conditions = 'Stop conditions' in content or 'stop when' in content.lower()
    scores['dim4'] = 8 if has_checkpoint_markers else (6 if has_stop_conditions else 4)

    # Dim 5: 具体性 (权重 17)
    soft_words = content.count('建议') + content.count('可以考虑') + content.count('根据情况')
    soft_words += content.count('suggest') + content.count('consider') + content.count('might')
    has_examples = '```' in content
    scores['dim5'] = 9 if (has_examples and soft_words < 5) else 7

    # Dim 6: 资源整合 (权重 4)
    has_references = '[' in content and '](' in content
    scores['dim6'] = 10 if has_references else 8

    # Dim 7: 架构 (权重 12)
    section_count = content.count('\n## ')
    is_organized = section_count >= 3
    scores['dim7'] = 9 if is_organized else 7

    # Dim 9: 反例 (权重 6)
    has_antipatterns = any(s in content.lower() for s in ['anti-pattern', 'do not', 'don\'t', '不要', '禁止', 'avoid'])
    has_blacklist_section = 'blacklist' in content.lower() or 'anti-pattern' in content.lower()
    scores['dim9'] = 9 if has_blacklist_section else (6 if has_antipatterns else 3)

    return scores

def calculate_weighted_score(scores):
    """计算加权总分"""
    weights = {
        'dim1': 7, 'dim2': 12, 'dim3': 12, 'dim4': 6,
        'dim5': 17, 'dim6': 4, 'dim7': 12, 'dim9': 6
    }

    weighted = {}
    total = 0
    for dim, score in scores.items():
        w = weights[dim]
        weighted[dim] = score * w / 10
        total += weighted[dim]

    return weighted, total

# 评估所有组件
base_path = Path('/Users/silaswu/Silas_Develop/data-scientist/plugins/data-scientist')

components = {
    'SKILL.md': 'skills/analysis-workflow/SKILL.md',
    'workflow.md': 'skills/analysis-workflow/references/workflow.md',
    'multi-agent-orchestration.md': 'skills/analysis-workflow/references/multi-agent-orchestration.md',
    'method-registry.md': 'skills/analysis-workflow/references/method-registry.md',
    'data-readiness.md': 'skills/analysis-workflow/references/data-readiness.md',
    'data-shaping.md': 'skills/analysis-workflow/references/data-shaping.md',
    'chart-catalog.md': 'skills/analysis-workflow/references/chart-catalog.md',
    'report-standard.md': 'skills/analysis-workflow/references/report-standard.md',
    'golden-templates.md': 'skills/analysis-workflow/references/golden-templates.md',
    'manufacturing-playbook.md': 'skills/analysis-workflow/references/manufacturing-playbook.md',
}

results = []

for name, rel_path in components.items():
    filepath = base_path / rel_path
    if not filepath.exists():
        continue

    content = filepath.read_text()
    scores = quick_score_component(filepath, content)
    weighted, total = calculate_weighted_score(scores)

    results.append({
        'component': name,
        'scores': scores,
        'weighted': weighted,
        'structure_total': round(total, 1),
        'estimated_total': round(total + 8 * 2.3, 1)  # 假设 dim8 实测为 8 分
    })

# 排序并输出
results.sort(key=lambda x: x['structure_total'])

print("# Phase 1 基线评估 - P0+P1 组件快速扫描\n")
print("| 组件 | 结构分 | 预估总分 | 最弱维度 |")
print("|------|--------|---------|---------|")

for r in results:
    weakest = min(r['weighted'].items(), key=lambda x: x[1])
    print(f"| {r['component']} | {r['structure_total']}/71 | ~{r['estimated_total']}/100 | {weakest[0]}({weakest[1]:.1f}) |")

print(f"\n**平均结构分**: {sum(r['structure_total'] for r in results) / len(results):.1f}/71")
print(f"**平均预估总分**: {sum(r['estimated_total'] for r in results) / len(results):.1f}/100")

# 保存详细结果
output_path = base_path / 'skills/analysis-workflow/darwin-results/baseline-quick-scan.json'
output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"\n详细结果已保存到: {output_path}")
