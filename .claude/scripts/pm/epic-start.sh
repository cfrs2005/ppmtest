#!/bin/bash

set -e

EPIC_NAME="$1"
if [ -z "$EPIC_NAME" ]; then
    echo "❌ Usage: epic-start <epic_name>"
    exit 1
fi

EPIC_DIR=".claude/epics/$EPIC_NAME"
EPIC_FILE="$EPIC_DIR/epic.md"

# Check if epic exists
if [ ! -f "$EPIC_FILE" ]; then
    echo "❌ Epic not found: $EPIC_NAME"
    echo "Available epics:"
    ls -la .claude/epics/ | grep "^d" | awk '{print $9}' | grep -v "^\.$" | grep -v "^\.\.$"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ You have uncommitted changes. Please commit or stash them before starting an epic."
    echo ""
    echo "To commit changes:"
    echo "  git add ."
    echo "  git commit -m \"Your commit message\""
    echo ""
    echo "To stash changes:"
    echo "  git stash push -m \"Work in progress\""
    exit 1
fi

# Check if branch exists
BRANCH_NAME="epic/$EPIC_NAME"
if git branch -a | grep -q "$BRANCH_NAME"; then
    echo "✅ Using existing branch: $BRANCH_NAME"
    git checkout "$BRANCH_NAME"
    git pull origin "$BRANCH_NAME"
else
    echo "✅ Creating new branch: $BRANCH_NAME"
    git checkout main
    git pull origin main
    git checkout -b "$BRANCH_NAME"
    git push -u origin "$BRANCH_NAME"
fi

# Get GitHub URL from epic file
GITHUB_URL=$(grep -A 10 "^github:" "$EPIC_FILE" | head -1 | cut -d' ' -f2-)

echo ""
echo "🚀 Epic Started: $EPIC_NAME"
echo "Branch: $BRANCH_NAME"
if [ -n "$GITHUB_URL" ]; then
    echo "GitHub: $GITHUB_URL"
fi
echo ""

# Show available tasks
echo "📋 Available Tasks:"
find "$EPIC_DIR" -name "*.md" -not -name "epic.md" -not -name "*.analysis.md" | sort | while read task_file; do
    task_name=$(basename "$task_file" .md)
    echo "  - $task_name"
done

echo ""
echo "📝 Next steps:"
echo "  1. Use /pm:next to get the next available task"
echo "  2. Use /pm:issue-start <number> to start working on a specific issue"
echo "  3. Use /pm:epic-status $EPIC_NAME to check progress"
echo ""