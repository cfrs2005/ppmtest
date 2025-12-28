# Lesson 01: Go 数据库设计基础

## 概述

本课程介绍如何在 Go 项目中进行数据库设计，重点关注数据模型定义、ORM 选择和数据库最佳实践。我们将通过博客系统的实际案例，学习如何构建可扩展、高性能的数据层。

## 学习目标

- 理解 Go 项目中的数据模型设计原则
- 掌握 GORM 的核心概念和用法
- 学习数据库关系设计和索引优化
- 了解数据验证和安全最佳实践

## 1. 数据模型基础

### 1.1 模型定义规范

在 Go 中，数据模型通常使用结构体（struct）定义，配合标签（tags）来描述数据库映射规则。

**基本结构**：
```go
type User struct {
    ID        uint      `gorm:"primaryKey" json:"id"`
    Username  string    `gorm:"size:50;uniqueIndex;not null" json:"username"`
    Email     string    `gorm:"size:100;uniqueIndex;not null" json:"email"`
    Password  string    `gorm:"size:255;not null" json:"-"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}
```

**关键要点**：
- 每个字段都有两个标签：`gorm`（数据库映射）和 `json`（API 序列化）
- `gorm:"primaryKey"` - 定义主键
- `gorm:"size:N"` - 限制字段长度
- `gorm:"uniqueIndex"` - 创建唯一索引
- `gorm:"not null"` - 非空约束
- `json:"-"` - 在 JSON 序列化时忽略（敏感字段）

### 1.2 命名约定

Go 和数据库的命名转换：

| Go 字段名 | 数据库字段名 | 说明 |
|-----------|-------------|------|
| `ID` | `id` | 自动转换为蛇形命名 |
| `Username` | `username` | 大写字母转小写加下划线 |
| `CreatedAt` | `created_at` | 驼峰转蛇形 |
| `ViewCount` | `view_count` | 连续大写字母处理 |

## 2. 项目实战：博客系统数据模型

### 2.1 用户模型 (User)

**文件位置**：`internal/models/user.go`

```go
type User struct {
    ID        uint      `gorm:"primaryKey" json:"id"`
    Username  string    `gorm:"size:50;uniqueIndex;not null" json:"username"`
    Email     string    `gorm:"size:100;uniqueIndex;not null" json:"email"`
    Password  string    `gorm:"size:255;not null" json:"-"` // 永不序列化密码
    Role      string    `gorm:"size:20;default:author" json:"role"`
    Status    string    `gorm:"size:20;default:active" json:"status"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}
```

**设计要点**：
1. **密码安全**：使用 `json:"-"` 标签防止密码泄露到 API
2. **角色系统**：支持 admin、author、subscriber 三种角色
3. **状态管理**：active、inactive、banned 状态
4. **唯一约束**：用户名和邮箱必须唯一

### 2.2 文章模型 (Post)

**文件位置**：`internal/models/post.go`

```go
type Post struct {
    ID          uint      `gorm:"primaryKey" json:"id"`
    Title       string    `gorm:"size:255;not null" json:"title"`
    Slug        string    `gorm:"size:255;uniqueIndex;not null" json:"slug"`
    Content     string    `gorm:"type:text" json:"content"`
    Summary     string    `gorm:"type:text" json:"summary"`
    Status      string    `gorm:"size:20;default:draft" json:"status"`
    AuthorID    uint      `gorm:"not null" json:"author_id"`
    ViewCount   int       `gorm:"default:0" json:"view_count"`
    CreatedAt   time.Time `json:"created_at"`
    UpdatedAt   time.Time `json:"updated_at"`
    PublishedAt *time.Time `json:"published_at,omitempty"`
}
```

**设计要点**：
1. **URL 友好**：使用 `slug` 字段创建 SEO 友好的 URL
2. **内容分离**：`content` 存储完整内容，`summary` 存储摘要
3. **状态流**：draft → published → archived
4. **指针字段**：`PublishedAt` 使用指针，可选值
5. **性能字段**：`ViewCount` 用于统计和排序

### 2.3 评论模型 (Comment)

```go
type Comment struct {
    ID        uint      `gorm:"primaryKey" json:"id"`
    PostID    uint      `gorm:"not null;index" json:"post_id"`
    AuthorID  uint      `gorm:"not null" json:"author_id"`
    Content   string    `gorm:"type:text;not null" json:"content"`
    Status    string    `gorm:"size:20;default:pending" json:"status"`
    CreatedAt time.Time `json:"created_at"`
}
```

**设计要点**：
1. **外键关联**：`PostID` 和 `AuthorID` 是外键
2. **索引优化**：`PostID` 添加索引，加速查询
3. **审核机制**：pending → approved/spam 状态流

### 2.4 标签和分类模型

```go
type Tag struct {
    ID   uint   `gorm:"primaryKey" json:"id"`
    Name string `gorm:"size:100;uniqueIndex;not null" json:"name"`
    Slug string `gorm:"size:100;uniqueIndex;not null" json:"slug"`
}

type Category struct {
    ID          uint   `gorm:"primaryKey" json:"id"`
    Name        string `gorm:"size:100;not null" json:"name"`
    Slug        string `gorm:"size:100;uniqueIndex;not null" json:"slug"`
    Description string `gorm:"type:text" json:"description"`
}
```

**设计要点**：
1. **多对多关系**：文章可以有多个标签和分类
2. **规范化**：使用 slug 而不是 ID 作为 URL 标识
3. **描述字段**：Category 有描述，Tag 不需要（保持简洁）

## 3. GORM 核心概念

### 3.1 模型约定

GORM 遵循约定优于配置的原则：

**默认约定**：
- 主键：`ID` 字段自动作为主键
- 表名：结构体名复数化（User → users）
- 字段名：蛇形命名（CreatedAt → created_at）
- 时间戳：自动管理 `CreatedAt` 和 `UpdatedAt`

**自定义配置**：
```go
// 指定表名
func (User) TableName() string {
    return "app_users"
}

// 自定义主键
type Product struct {
    ProductID int `gorm:"primaryKey"`
}
```

### 3.2 字段标签详解

**常用标签**：

```go
// 数据库类型
Type string `gorm:"type:varchar(100)"`
// 等价于
Size string `gorm:"size:100"`

// 约束
Email string `gorm:"uniqueIndex;not null"`
Age   int    `gorm:"default:0;check:age >= 18"`

// 关联
AuthorID uint `gorm:"index:idx_author_id"`

// 忽略字段
TempData string `gorm:"-"`
```

### 3.3 关系定义

**一对多关系**（用户 → 文章）：
```go
type User struct {
    ID     uint   `gorm:"primaryKey"`
    Posts  []Post `gorm:"foreignKey:AuthorID"`
}

type Post struct {
    ID       uint `gorm:"primaryKey"`
    AuthorID uint `gorm:"index"`
    Author   User `gorm:"foreignKey:AuthorID"`
}
```

**多对多关系**（文章 ↔ 标签）：
```go
type Post struct {
    ID   uint    `gorm:"primaryKey"`
    Tags []Tag   `gorm:"many2many:post_tags;"`
}

type Tag struct {
    ID    uint    `gorm:"primaryKey"`
    Posts []Post  `gorm:"many2many:post_tags;"`
}
```

## 4. 数据库最佳实践

### 4.1 索引策略

**何时创建索引**：
1. **经常查询的字段**：`username`、`email`
2. **外键字段**：`author_id`、`post_id`
3. **唯一约束**：自动创建索引
4. **组合查询**：创建复合索引

```go
// 单字段索引
Username string `gorm:"size:50;uniqueIndex"`

// 复合索引
type Post struct {
    Status      string `gorm:"index:idx_status_date"`
    PublishedAt time.Time `gorm:"index:idx_status_date"`
}
```

**避免过度索引**：
- 索引增加写入开销
- 占用额外存储空间
- 只在必要字段上创建

### 4.2 数据完整性

**外键约束**：
```go
AuthorID uint `gorm:"not null;constraint:OnDelete:CASCADE"`
```

**检查约束**：
```go
Age int `gorm:"check:age >= 18"`
Status string `gorm:"check:status IN ('active', 'inactive', 'banned')"`
```

### 4.3 安全考虑

**敏感数据处理**：
```go
// 1. 使用 json:"-" 隐藏密码
Password string `gorm:"size:255;not null" json:"-"`

// 2. 密码哈希存储
func (u *User) SetPassword(password string) error {
    hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return err
    }
    u.Password = string(hashedPassword)
    return nil
}

// 3. SQL 注入防护（GORM 自动参数化查询）
db.Where("email = ?", email).First(&user)  // ✅ 安全
db.Where(fmt.Sprintf("email = '%s'", email)).First(&user)  // ❌ 危险
```

## 5. 性能优化

### 5.1 查询优化

**避免 N+1 查询**：
```go
// ❌ N+1 查询问题
posts := []Post{}
db.Find(&posts)
for _, post := range posts {
    db.Preload("Author").First(&post.Author)  // N 次查询
}

// ✅ 使用 Preload 优化
db.Preload("Author").Find(&posts)  // 2 次查询
```

**选择必要字段**：
```go
// 只选择需要的字段
db.Select("id", "title", "slug").Find(&posts)
```

### 5.2 批量操作

```go
// 批量插入
users := []User{{Username: "user1"}, {Username: "user2"}}
db.CreateInBatches(users, 100)  // 每批 100 条

// 批量更新
db.Model(&User{}).Where("status = ?", "inactive").Update("status", "active")
```

## 6. 常见陷阱和解决方案

### 6.1 时区问题

**问题**：`time.Time` 类型默认使用本地时区

**解决方案**：
```go
import "database/sql/driver"

type CustomTime struct {
    time.Time
}

func (ct *CustomTime) Scan(value interface{}) error {
    if value == nil {
        return nil
    }
    // 转换为 UTC
    ct.Time = value.(time.Time).UTC()
    return nil
}
```

### 6.2 软删除

GORM 支持软删除，数据不会真正删除：

```go
type User struct {
    ID        uint `gorm:"primaryKey"`
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

// 软删除
db.Delete(&user)

// 包含已删除数据
db.Unscoped().Find(&users)

// 永久删除
db.Unscoped().Delete(&user)
```

### 6.3 迁移管理

**版本化迁移**：
```go
func migrate(db *gorm.DB) error {
    // 1. 自动迁移（开发环境）
    return db.AutoMigrate(&User{}, &Post{}, &Comment{})
    
    // 2. SQL 迁移文件（生产环境推荐）
    // migrations/20231228_create_users.sql
    // migrations/20231229_create_posts.sql
}
```

## 7. 实战练习

### 练习 1：创建新的数据模型

为博客系统添加 `Like` 模型（点赞功能）：

```go
// 你的实现
type Like struct {
    // TODO: 定义字段
}
```

**要求**：
- 用户可以点赞文章
- 一个用户对一篇文章只能点赞一次
- 包含创建时间
- 添加必要的索引

### 练习 2：优化查询

给定以下需求，优化查询：

```go
// 获取已发布的文章及其作者信息
// 你的优化实现
func GetPublishedPostsWithAuthor(db *gorm.DB) ([]Post, error) {
    // TODO: 实现
}
```

## 8. 总结

### 核心要点

1. **模型设计**：使用 GORM 标签定义数据库映射
2. **关系设计**：合理设计一对一、一对多、多对多关系
3. **索引优化**：在常用查询字段上创建索引
4. **安全防护**：敏感字段不序列化，使用参数化查询
5. **性能考虑**：避免 N+1 查询，使用批量操作

### 下一步

- [ ] 学习服务层架构设计（Lesson 02）
- [ ] 实现数据访问层（Repository）
- [ ] 编写数据库单元测试
- [ ] 了解高级查询技巧

### 相关资源

- [GORM 官方文档](https://gorm.io/docs/)
- [Go 数据库最佳实践](https://go.dev/doc/database/manage-connections)
- [SQL 索引优化指南](https://www.postgresql.org/docs/current/indexes.html)

---

**作者**: Go 博客系统项目组  
**更新日期**: 2025-12-28  
**难度**: ⭐⭐☆☆☆（初级）  
**预计学习时间**: 2-3 小时