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

## 测试行为记录 / Testing Behavior Records

### 本地验证服务 / Local Validation Services

#### 创建目的 / Creation Purpose
- 在本地创建用于验证的Python服务目录
- 该目录不会提交到Git仓库（已在.gitignore中配置）
- 用于测试第三方服务集成和功能验证

#### DingTalk机器人服务 / DingTalk Bot Service

**服务实现 / Service Implementation**:
- 文件位置：`validation_services/dingtalk_bot.py`
- 完整的钉钉机器人API集成，支持签名验证
- 包含时间戳生成、签名计算、消息发送等功能

**测试过程 / Testing Process**:
1. **初始测试**: 使用access_token `83c93d0b2c3010646fd0b84d08f945ac97cb787a34a7cef471668ecd97c18afc`
   - 遇到签名验证要求，实现完整的签名支持
   - 需要secret_key进行签名计算

2. **密钥更新**: 更换为新的access_token `d5af88b6c4a93cc4b263dae7abc9ad5feacfc286611248ee7b5edd3b65be29c4`
   - 仍然需要签名验证
   - 实现了完整的签名验证机制

3. **依赖问题**: 遇到`ModuleNotFoundError: No module named 'requests'`
   - 需要安装requests库依赖
   - 测试暂停，等待依赖安装

**服务功能 / Service Features**:
- 发送文本消息到钉钉群组
- 支持签名验证确保安全性
- 自动生成时间戳和签名
- 错误处理和日志记录

**测试脚本 / Testing Scripts**:
- `validation_services/dingtalk_bot_demo.py` - 演示版本
- `validation_services/dingtalk_bot.py` - 完整实现版本

#### 环境配置 / Environment Configuration
- Python虚拟环境管理
- 依赖库安装（requests等）
- 本地服务目录结构

#### 后续计划 / Future Plans
- 完成requests库依赖安装
- 测试DingTalk机器人消息发送功能
- 扩展更多本地验证服务
