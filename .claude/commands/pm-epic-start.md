---
allowed-tools: Bash, Read, Write, LS, Task
---

# PM Epic Start

启动 epic 的并行代理执行。

## Usage
```
/pm-epic-start <epic_name>
```

这个命令是 `/pm:epic-start` 的替代版本，用于测试命令识别功能。

## Instructions

直接调用 `.claude/commands/pm/epic-start.md` 中的逻辑。

```bash
# 检查参数
if [ -z "$ARGUMENTS" ]; then
    echo "❌ Usage: /pm-epic-start <epic_name>"
    exit 1
fi

echo "🚀 启动 epic: $ARGUMENTS"

# 检查 epic 是否存在
if [ ! -f ".claude/epics/$ARGUMENTS/epic.md" ]; then
    echo "❌ Epic 不存在。请先运行: /pm:prd-parse $ARGUMENTS"
    exit 1
fi

# 检查 GitHub 同步
if ! grep -q "github:" ".claude/epics/$ARGUMENTS/epic.md"; then
    echo "❌ Epic 未同步。请先运行: /pm:epic-sync $ARGUMENTS"
    exit 1
fi

echo "✅ Epic 准备就绪，可以启动"
echo "📋 完整功能请参考: .claude/commands/pm/epic-start.md"
```