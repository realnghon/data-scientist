#!/usr/bin/env bash
# Validate multi-platform plugin configuration files stay in sync

set -e

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔍 Validating plugin configuration synchronization..."
echo

# Core metadata fields to check
CLAUDE_MANIFEST="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CODEX_MANIFEST="$PLUGIN_ROOT/.codex-plugin/plugin.json"

# Check files exist
if [[ ! -f "$CLAUDE_MANIFEST" ]]; then
    echo "❌ Missing: $CLAUDE_MANIFEST"
    exit 1
fi

if [[ ! -f "$CODEX_MANIFEST" ]]; then
    echo "❌ Missing: $CODEX_MANIFEST"
    exit 1
fi

# Extract and compare key fields
extract_field() {
    local file=$1
    local field=$2
    grep -o "\"$field\": *\"[^\"]*\"" "$file" | head -1 || echo ""
}

ERRORS=0

# Compare version
CLAUDE_VERSION=$(extract_field "$CLAUDE_MANIFEST" "version")
CODEX_VERSION=$(extract_field "$CODEX_MANIFEST" "version")

if [[ "$CLAUDE_VERSION" != "$CODEX_VERSION" ]]; then
    echo "❌ Version mismatch:"
    echo "   Claude: $CLAUDE_VERSION"
    echo "   Codex:  $CODEX_VERSION"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Version synchronized: $CLAUDE_VERSION"
fi

# Compare name
CLAUDE_NAME=$(extract_field "$CLAUDE_MANIFEST" "name")
CODEX_NAME=$(extract_field "$CODEX_MANIFEST" "name")

if [[ "$CLAUDE_NAME" != "$CODEX_NAME" ]]; then
    echo "❌ Name mismatch:"
    echo "   Claude: $CLAUDE_NAME"
    echo "   Codex:  $CODEX_NAME"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Name synchronized: $CLAUDE_NAME"
fi

# Check displayName exists in both
CLAUDE_DISPLAY=$(extract_field "$CLAUDE_MANIFEST" "displayName")
CODEX_DISPLAY=$(extract_field "$CODEX_MANIFEST" "displayName")

if [[ -z "$CLAUDE_DISPLAY" ]]; then
    echo "⚠️  Warning: Claude manifest missing displayName"
    ERRORS=$((ERRORS + 1))
elif [[ -z "$CODEX_DISPLAY" ]]; then
    echo "⚠️  Warning: Codex manifest missing displayName"
    ERRORS=$((ERRORS + 1))
elif [[ "$CLAUDE_DISPLAY" != "$CODEX_DISPLAY" ]]; then
    echo "❌ displayName mismatch:"
    echo "   Claude: $CLAUDE_DISPLAY"
    echo "   Codex:  $CODEX_DISPLAY"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ displayName synchronized: $CLAUDE_DISPLAY"
fi

# Validate agent files exist and are referenced
echo
echo "🔍 Checking agent references..."

AGENT_COUNT=$(grep -c '\.md' "$CLAUDE_MANIFEST" | grep agents || echo 0)

for agent_path in "$PLUGIN_ROOT"/agents/*.md; do
    agent_file=$(basename "$agent_path")

    if ! grep -q "$agent_file" "$CLAUDE_MANIFEST"; then
        echo "⚠️  Warning: $agent_file exists but not in Claude manifest"
        ERRORS=$((ERRORS + 1))
    fi

    # Check agent has required frontmatter
    if ! grep -q "^name: " "$agent_path"; then
        echo "❌ Missing 'name:' in $agent_file frontmatter"
        ERRORS=$((ERRORS + 1))
    fi

    if ! grep -q "^description: " "$agent_path"; then
        echo "❌ Missing 'description:' in $agent_file frontmatter"
        ERRORS=$((ERRORS + 1))
    fi

    if ! grep -q "^tools: " "$agent_path"; then
        echo "⚠️  Warning: Missing 'tools:' in $agent_file frontmatter"
    fi
done

echo "✅ Agent file check complete"

# Validate skill structure
echo
echo "🔍 Checking skill structure..."

SKILL_DIR="$PLUGIN_ROOT/skills/analysis-workflow"
if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
    echo "❌ Missing: $SKILL_DIR/SKILL.md"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Main skill file exists"

    # Check skill frontmatter
    if ! grep -q "^name: " "$SKILL_DIR/SKILL.md"; then
        echo "❌ Missing 'name:' in SKILL.md frontmatter"
        ERRORS=$((ERRORS + 1))
    fi

    if ! grep -q "^description: " "$SKILL_DIR/SKILL.md"; then
        echo "❌ Missing 'description:' in SKILL.md frontmatter"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Summary
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $ERRORS -eq 0 ]]; then
    echo "✅ All checks passed! Plugin configuration is synchronized."
    exit 0
else
    echo "❌ Found $ERRORS issue(s). Please fix before publishing."
    exit 1
fi
