# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言设置 / Language Settings

**重要：始终使用中文与用户沟通**
- 所有回复、说明、错误信息均使用中文
- 代码注释可以使用英文，但用户交流必须使用中文
- 技术术语可以保留英文，但需要用中文解释

## Project Overview

This is a **Go-based Blog System** (similar to WordPress) with GLM AI model integration, built with MySQL as the database.

**核心目标**: 构建一个功能完整的博客系统，同时作为 Go 语言学习的实战项目，从入门到精通。重点包括：
- 架构设计模式和最佳实践
- Go 语言核心技巧和性能优化
- 数据库设计和优化
- 完整的教学文档体系（docs/lessons/）

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

## 项目文档系统

### todo.md - 待办事项管理
**位置**: `/todo.md`（根目录）

**用途**:
- 记录每次开发会话的待办事项
- 跟踪功能开发进度
- 维护任务清单

**更新要求**:
- 每次开发会话开始时，在文件顶部添加新的会话章节（包含日期）
- 使用 `- [ ]` 表示未完成的任务
- 使用 `- [x]` 表示已完成的任务
- 定期整理和归档已完成的任务
- 保持任务的原子性和可追踪性

**内容结构**:
```markdown
## 当前会话 (YYYY-MM-DD)
### 正在进行
- [ ] 任务描述

### 已完成
- [x] 任务描述

## 功能开发待办
### 核心功能
- [ ] 功能列表
```

### memory.md - 项目记忆档案
**位置**: `/memory.md`（根目录）

**用途**:
- 记录项目开发历史和重要决策
- 技术选型和架构决策的缘由
- 问题解决方案和经验教训
- 学习要点和最佳实践

**更新要求**:
- 每次重要决策或技术选型后更新
- 记录问题时包含：问题描述、解决方案、相关代码位置
- 定期总结和提炼经验教训
- 添加时间戳，保持时序性

**内容结构**:
```markdown
## 项目历史
### YYYY-MM-DD: 事件标题
#### 重大决策
- 决策内容和理由

#### 关键技术决策
- 技术选型和原因

## 技术选型记录
### 技术名称
- **选择**: XXX
- **理由**: 详细说明

## 问题和解决方案
### 问题 N: 问题描述
**问题**: 详细描述
**解决方案**: 具体方案
**参考**: file_path:line_number
```

### 教学文档 (docs/lessons/)
**位置**: `/docs/lessons/`

**用途**:
- 记录 Go 语言学习的核心知识点
- 详细解释架构设计、性能优化技巧
- 提供实战经验和最佳实践
- 作为新人学习的核心教材

**更新要求**:
- 每完成一个重要功能或模块后，编写对应的 Lesson
- Lesson 应包含：理论讲解、实战案例、代码示例、注意事项
- 使用清晰的章节结构，便于查阅
- 添加代码示例和图表辅助说明

**已完成的 Lessons**:
- ✅ Lesson 01: 数据库设计基础
- ✅ Lesson 02: 服务层架构设计
- 🔄 Lesson 03: Web 框架最佳实践（进行中）

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing existing files to creating a new file.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
