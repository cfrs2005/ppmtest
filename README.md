# PPM 博客系统

基于 Go 语言开发的现代化博客系统，集成 GLM 大模型能力。

## 项目概述

这是一个类似 WordPress 的博客系统，使用 Go 语言构建，提供高性能的内容管理和发布平台。

### 技术栈

- **语言**: Go
- **数据库**: MySQL
- **AI 集成**: GLM 大模型
- **架构**: RESTful API

## 核心特性

- 📝 文章发布和管理
- 🔍 智能内容生成（GLM 大模型）
- 💬 评论系统
- 🏷️ 标签和分类
- 🔐 用户认证和权限管理
- 📊 数据分析和统计

## 快速开始

### 环境要求

- Go 1.21+
- MySQL 8.0+

### 安装

```bash
# 克隆仓库
git clone https://github.com/cfrs2005/ppmtest.git
cd ppmtest

# 安装依赖
go mod download

# 配置数据库
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 运行迁移
go run cmd/migrate/main.go

# 启动服务
go run cmd/server/main.go
```

## 项目结构

```
.
├── cmd/                    # 命令行工具
│   ├── server/            # Web 服务器
│   └── migrate/           # 数据库迁移
├── internal/              # 私有应用代码
│   ├── config/           # 配置管理
│   ├── models/           # 数据模型
│   ├── handlers/         # HTTP 处理器
│   ├── services/         # 业务逻辑
│   └── repository/       # 数据访问层
├── pkg/                   # 公共库
├── api/                   # API 定义
├── migrations/            # 数据库迁移文件
└── web/                   # 前端资源
```

## 开发指南

### 运行测试

```bash
go test ./...
```

### 代码规范

- 遵循 [Effective Go](https://go.dev/doc/effective_go) 指南
- 使用 `gofmt` 格式化代码
- 通过 `golint` 检查代码质量

### 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目主页: https://github.com/cfrs2005/ppmtest
- Issue 跟踪: https://github.com/cfrs2005/ppmtest/issues

---

**注意**: 本项目正在积极开发中，API 可能会有变化。
