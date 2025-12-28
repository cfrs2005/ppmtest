# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言设置 / Language Settings

**重要：始终使用中文与用户沟通**
- 所有回复、说明、错误信息均使用中文
- 代码注释可以使用英文，但用户交流必须使用中文
- 技术术语可以保留英文，但需要用中文解释

## Project Overview

This is a **Go-based Blog System** (similar to WordPress) with GLM AI model integration, built with MySQL as the database.

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
- Real database integration for testing
- Verbose test output for debugging
- Table-driven tests for Go code

## Critical Rules

### Code Quality (Go Specific)
- **NO PARTIAL IMPLEMENTATION** - Complete all functionality
- **NO CODE DUPLICATION** - Reuse existing functions and patterns
- **NO DEAD CODE** - Use or delete completely
- **NO OVER-ENGINEERING** - Simple functions over enterprise patterns
- **NO MIXED CONCERNS** - Proper separation of concerns
- **NO RESOURCE LEAKS** - Clean up connections, defer close operations

### Go Best Practices
- Follow standard Go project layout (`cmd/`, `internal/`, `pkg/`)
- Use interfaces for dependency injection
- Handle errors explicitly - don't ignore them
- Use `context.Context` for cancellation and timeouts
- Implement proper graceful shutdown
- Use table-driven tests for comprehensive testing
- Follow [Effective Go](https://go.dev/doc/effective_go) guidelines
- Format code with `gofmt` before committing

### Process Requirements
- **Never break userspace** - Maintain backward compatibility
- **Test every function** - Unit tests with real database when needed
- **Consistent naming** - Follow Go naming conventions (MixedCaps for exported)
- **Fail fast** - Critical configuration errors halt execution
- **Graceful degradation** - Optional features log and continue

## Agent Usage Guidelines

### When to Use Sub-Agents
- **file-analyzer**: Reading files, especially logs and verbose outputs
- **code-analyzer**: Code analysis, bug hunting, logic tracing
- **test-runner**: All test execution and analysis (`go test ./...`)
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

### Project Structure (Go Standard)
```
.
├── cmd/                    # Main applications
│   ├── server/            # Web server entry point
│   └── migrate/           # Database migration tool
├── internal/              # Private application code
│   ├── config/           # Configuration
│   ├── models/           # Data models
│   ├── handlers/         # HTTP handlers
│   ├── services/         # Business logic
│   └── repository/       # Data access layer
├── pkg/                   # Public libraries
├── api/                   # API definitions (OpenAPI/Swagger)
├── web/                   # Static web assets
├── migrations/            # Database migration files
├── go.mod
├── go.sum
└── Makefile
```

### Task Naming
- Tasks start as `001.md`, `002.md` during decomposition
- After GitHub sync, renamed to `{issue-id}.md`
- Makes navigation intuitive: issue #1234 = file `1234.md`

## GLM AI Integration

### AI Features
- Content generation using GLM models
- Intelligent text summarization
- Auto-tagging and categorization
- Comment spam detection
- Content recommendation

### Integration Points
- Service layer for AI operations
- Async job processing for AI tasks
- Configuration for API keys and endpoints
- Fallback mechanisms for AI failures

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing existing files to creating a new file.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
