#!/usr/bin/env bash
# sync_skill.sh - 将源 SKILL.md 同步到运行时目录
# 用途：修改 plugins/data-scientist/skills/analysis-workflow/SKILL.md 后运行此脚本

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$REPO_ROOT/plugins/data-scientist/skills/analysis-workflow"
TARGET="$HOME/.agents/skills/data-scientist"

echo "🔄 同步 data-scientist skill 到运行时目录..."
echo "   源: $SOURCE"
echo "   目标: $TARGET"

# 检查源目录
if [ ! -d "$SOURCE" ]; then
  echo "❌ 错误: 源目录不存在 $SOURCE"
  exit 1
fi

if [ ! -f "$SOURCE/SKILL.md" ]; then
  echo "❌ 错误: 源文件不存在 $SOURCE/SKILL.md"
  exit 1
fi

# 创建目标目录
mkdir -p "$TARGET"

# 同步整个 skill 目录（包括 references、scripts、agents 等）
rsync -av --delete "$SOURCE/" "$TARGET/"

echo "✅ 同步完成！"
echo ""
echo "同步的文件："
echo "  - SKILL.md"
echo "  - references/ (9 个文档)"
echo "  - scripts/ (ds_skill 辅助库)"
echo "  - agents/"
echo "  - assets/"
echo "  - test-prompts.json"
echo ""
echo "💡 提示: 如果你在 Claude Code 中运行，重启 Claude 后改动会生效"
