#!/bin/bash

set -e

ARGUMENTS="$1"

if [ -z "$ARGUMENTS" ]; then
    echo "❌ Usage: $0 <epic_name>"
    exit 1
fi

echo "🚀 Starting epic: $ARGUMENTS"

# 1. Verify epic exists
if [ ! -f ".claude/epics/$ARGUMENTS/epic.md" ]; then
    echo "❌ Epic not found. Run: /pm:prd-parse $ARGUMENTS"
    exit 1
fi

# 2. Check GitHub sync
if ! grep -q "github:" ".claude/epics/$ARGUMENTS/epic.md"; then
    echo "❌ Epic not synced. Run: /pm:epic-sync $ARGUMENTS first"
    exit 1
fi

# 3. Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ You have uncommitted changes. Please commit or stash them before starting an epic."
    exit 1
fi

# 4. Create or enter branch
if ! git branch -a | grep -q "epic/$ARGUMENTS"; then
    echo "📁 Creating branch: epic/$ARGUMENTS"
    git checkout main
    git pull origin main
    git checkout -b epic/$ARGUMENTS
    git push -u origin epic/$ARGUMENTS
else
    echo "📁 Using existing branch: epic/$ARGUMENTS"
    git checkout epic/$ARGUMENTS
    git pull origin epic/$ARGUMENTS
fi

# 5. Identify ready issues
echo "🔍 Analyzing task dependencies..."
READY_ISSUES=()
BLOCKED_ISSUES=()

# Find all task files
for task_file in .claude/epics/$ARGUMENTS/*.md; do
    if [[ "$task_file" =~ ^[0-9]+\.md$ ]] || [[ "$task_file" =~ [0-9]+-analysis\.md$ ]]; then
        continue
    fi
    
    if [ "$task_file" = ".claude/epics/$ARGUMENTS/epic.md" ]; then
        continue
    fi
    
    # Extract issue number from filename
    issue_num=$(basename "$task_file" .md)
    
    # Check if issue is ready (simplified check)
    if grep -q "status: ready" "$task_file" 2>/dev/null || grep -q "status: \"ready\"" "$task_file" 2>/dev/null; then
        READY_ISSUES+=("$issue_num")
    elif grep -q "status: blocked" "$task_file" 2>/dev/null || grep -q "status: \"blocked\"" "$task_file" 2>/dev/null; then
        BLOCKED_ISSUES+=("$issue_num")
    fi
done

echo "✅ Found ${#READY_ISSUES[@]} ready issues"
echo "⏸ Found ${#BLOCKED_ISSUES[@]} blocked issues"

# 6. Launch parallel agents for ready issues
for issue_num in "${READY_ISSUES[@]}"; do
    task_file=".claude/epics/$ARGUMENTS/$issue_num.md"
    
    if [ ! -f "$task_file" ]; then
        echo "❌ Task file not found: $task_file"
        continue
    fi
    
    echo "🚀 Starting issue #$issue_num"
    
    # Extract title from task file
    title=$(grep "^# " "$task_file" | head -1 | sed 's/^# //')
    
    echo "   Title: $title"
    
    # Create updates directory if it doesn't exist
    mkdir -p ".claude/epics/$ARGUMENTS/updates/$issue_num"
    
    # For now, we'll just mark as in-progress (actual agent launching would be done via Claude Code)
    echo "   Status: Ready for agent deployment"
    
    # Update task status
    sed -i '' "s/status: ready/status: in_progress/" "$task_file" 2>/dev/null || sed -i "s/status: ready/status: in_progress/" "$task_file" 2>/dev/null
done

# 7. Create execution status
cat > ".claude/epics/$ARGUMENTS/execution-status.md" << EOF
---
started: $(date -Iseconds)
branch: epic/$ARGUMENTS
---

# Execution Status

## Active Agents
${#READY_ISSUES[@]} issues ready for parallel execution

## Ready Issues
$(for issue in "${READY_ISSUES[@]}"; do echo "- #$issue - Ready for agent deployment"; done)

## Blocked Issues
$(for issue in "${BLOCKED_ISSUES[@]}"; do echo "- #$issue - Blocked by dependencies"; done)

## Completed
- None yet

## Next Steps
- Deploy parallel agents for ready issues
- Monitor progress with /pm:epic-status $ARGUMENTS
- Merge when complete with /pm:epic-merge $ARGUMENTS
EOF

echo ""
echo "✅ Epic execution started: $ARGUMENTS"
echo "📁 Branch: epic/$ARGUMENTS"
echo "🎯 Ready issues: ${#READY_ISSUES[@]}"
echo "⏸ Blocked issues: ${#BLOCKED_ISSUES[@]}"
echo ""
echo "Monitor progress:"
echo "  /pm:epic-status $ARGUMENTS"
echo ""
echo "View branch changes:"
echo "  git status"
echo ""
echo "Merge when complete:"
echo "  /pm:epic-merge $ARGUMENTS"