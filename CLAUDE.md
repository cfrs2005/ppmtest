# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言设置 / Language Settings

**重要：始终使用中文与用户沟通**
- 所有回复、说明、错误信息均使用中文
- 代码注释可以使用英文，但用户交流必须使用中文
- 技术术语可以保留英文，但需要用中文解释

## Project Overview

This is a **Claude Code PM System** - a comprehensive project management and development workflow system that transforms PRDs into shipped code through structured planning, GitHub integration, and parallel AI agent execution.

## System Architecture

### Core Components

**Command System** (`.claude/commands/`):
- `context/` - Project context management commands
- `pm/` - Project management workflow commands 
- `testing/` - Test configuration and execution commands
- Utility commands for code review and system maintenance

**Agent System** (`.claude/agents/`):
- `code-analyzer` - Deep code analysis and bug detection
- `file-analyzer` - Log file and verbose output summarization
- `test-runner` - Test execution with intelligent analysis
- `parallel-worker` - Multi-agent coordination in worktrees

**Project Management**:
- `.claude/epics/` - Implementation plans and task breakdowns
- `.claude/prds/` - Product requirements documents
- `.claude/context/` - Project-wide context documentation
- `.claude/scripts/` - Bash scripts for PM operations

### Key Commands

**Project Management**:
- `/pm:prd-new [feature]` - Create product requirements through guided brainstorming
- `/pm:prd-parse [feature]` - Convert PRD to technical implementation plan
- `/pm:epic-oneshot [feature]` - Decompose epic and sync to GitHub in one command
- `/pm:issue-start [number]` - Begin work with specialized agent
- `/pm:next` - Get next priority task with epic context

**Context Management**:
- `/context:create` - Analyze project and create baseline documentation
- `/context:prime` - Load context into current conversation
- `/context:update` - Refresh context with recent changes

**Testing**:
- `/testing:prime` - Configure testing framework detection
- `/testing:run [target]` - Execute tests with intelligent analysis

**Utilities**:
- `/re-init` - Update CLAUDE.md with PM system rules
- `/code-rabbit` - Process CodeRabbit review comments

## Development Workflow

### 1. Spec-Driven Development
- Every feature starts with PRD creation through brainstorming
- Technical epics break down implementation approach
- Tasks are decomposed with acceptance criteria
- All work traces back to written specifications

### 2. GitHub-Native Execution
- Issues serve as the single source of truth
- Progress updates sync to GitHub as comments
- Team collaboration happens through issue interactions
- Complete audit trail from PRD to production

### 3. Parallel Agent System
- Issues spawn multiple specialized agents working simultaneously
- Agents coordinate through Git commits in worktrees
- Main conversation maintains strategic oversight
- Context optimization prevents window pollution

### 4. Testing Philosophy
- Always use test-runner agent for execution
- No mocking - real services only
- Verbose test output for debugging
- Check test structure before blaming code

## Critical Rules

### Code Quality
- **NO PARTIAL IMPLEMENTATION** - Complete all functionality
- **NO CODE DUPLICATION** - Reuse existing functions and patterns
- **NO DEAD CODE** - Use or delete completely
- **NO OVER-ENGINEERING** - Simple functions over enterprise patterns
- **NO MIXED CONCERNS** - Proper separation of concerns
- **NO RESOURCE LEAKS** - Clean up connections, timeouts, listeners

### Process Requirements
- **Never break userspace** - Maintain backward compatibility
- **Test every function** - Accurate, real usage tests
- **Consistent naming** - Follow existing patterns
- **Fail fast** - Critical configuration errors halt execution
- **Graceful degradation** - Optional features log and continue

## Agent Usage Guidelines

### When to Use Sub-Agents
- **file-analyzer**: Reading files, especially logs and verbose outputs
- **code-analyzer**: Code analysis, bug hunting, logic tracing
- **test-runner**: All test execution and analysis
- **parallel-worker**: Multi-agent coordination in worktrees

### Context Optimization
Main conversation stays strategic - agents handle implementation details. This prevents context window pollution while maintaining full oversight.

## GitHub Integration

### Required Setup
- GitHub CLI with authentication
- gh-sub-issue extension for parent-child relationships
- Proper repository permissions

### Remote Repository
- **Repository URL**: https://github.com/cfrs2005/ppmtest
- **Main Branch**: main

### Sync Strategy
- Local operations first for speed
- Explicit sync when ready
- Issues track sub-task completion automatically
- Labels provide organization (`epic:feature`, `task:feature`)

## File Conventions

### Project Structure
```
.claude/
├── epics/[feature-name]/
│   ├── epic.md          # Implementation plan
│   ├── [#].md           # Individual tasks (by GitHub issue #)
│   └── updates/         # Work-in-progress
├── prds/                # Product requirements documents
├── context/             # Project-wide documentation
├── agents/              # Specialized agent definitions
├── commands/            # Command definitions
├── scripts/             # Bash scripts
└── rules/               # System rules
```

### Task Naming
- Tasks start as `001.md`, `002.md` during decomposition
- After GitHub sync, renamed to `{issue-id}.md`
- Makes navigation intuitive: issue #1234 = file `1234.md`
