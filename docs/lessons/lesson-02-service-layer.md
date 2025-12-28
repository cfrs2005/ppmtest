# Lesson 02: Go 服务层架构设计

## 概述

本课程介绍 Go 项目中的服务层（Service Layer）架构设计，重点讲解依赖注入、接口设计、错误处理和业务逻辑组织。通过博客系统的实战案例，学习如何构建可测试、可维护的业务逻辑层。

## 学习目标

- 理解服务层在分层架构中的职责
- 掌握 Go 中的接口设计和依赖注入
- 学习业务逻辑的组织和错误处理策略
- 了解事务管理和最佳实践

## 1. 分层架构基础

### 1.1 为什么需要服务层？

**传统单体架构的问题**：
```go
// ❌ 糟糕的设计：HTTP 处理器直接操作数据库
func GetPostsHandler(c *gin.Context) {
    db := c.MustGet("db").(*gorm.DB)
    var posts []Post
    if err := db.Find(&posts).Error; err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }
    
    // 业务逻辑混在处理器中
    for i := range posts {
        posts[i].ViewCount++  // 业务逻辑不该在这里
    }
    
    c.JSON(200, posts)
}
```

**分层架构的优势**：
```
┌─────────────────────────────────────┐
│  Presentation Layer (HTTP Handlers) │  ← 处理 HTTP 请求
├─────────────────────────────────────┤
│  Service Layer (Business Logic)     │  ← 业务逻辑
├─────────────────────────────────────┤
│  Data Layer (Repository/Models)     │  ← 数据访问
└─────────────────────────────────────┘
```

**服务层的职责**：
1. **业务逻辑**：实现核心业务规则
2. **事务协调**：协调多个 Repository 操作
3. **跨模型操作**：处理多个实体之间的交互
4. **外部服务集成**：调用第三方 API

### 1.2 服务层设计原则

**单一职责原则**：
```go
// ✅ 好的设计：每个服务专注一个领域
type PostService interface {
    Create(post *Post) error
    Update(post *Post) error
    Delete(id uint) error
    GetByID(id uint) (*Post, error)
    List(limit, offset int) ([]Post, int64, error)
}

type UserService interface {
    Register(user *User) error
    Login(email, password string) (*User, error)
    UpdateProfile(user *User) error
}
```

**接口隔离原则**：
```go
// ❌ 臃肿的接口
type Service interface {
    PostOperations
    UserOperations
    CommentOperations
    // ... 太多职责
}

// ✅ 分离的接口
type PostService interface {}
type UserService interface {}
type CommentService interface {}
```

## 2. 依赖注入模式

### 2.1 什么是依赖注入？

**定义**：依赖注入（Dependency Injection, DI）是一种实现控制反转（IoC）的技术，对象的依赖关系由外部容器注入，而不是对象自己创建。

**传统方式 vs 依赖注入**：
```go
// ❌ 硬编码依赖
type PostService struct {
    db *gorm.DB
}

func NewPostService() *PostService {
    db, _ := gorm.Open(...)  // 硬编码创建依赖
    return &PostService{db: db}
}

// ✅ 依赖注入
type PostService struct {
    db *gorm.DB
    repo Repository
}

func NewPostService(db *gorm.DB, repo Repository) *PostService {
    return &PostService{db: db, repo: repo}
}
```

### 2.2 接口定义

**定义服务接口**：
```go
package service

import (
    "context"
    "github.com/yourusername/ppmtest/internal/models"
)

// PostService 定义文章服务接口
type PostService interface {
    Create(ctx context.Context, post *models.Post) error
    Update(ctx context.Context, post *models.Post) error
    Delete(ctx context.Context, id uint) error
    GetByID(ctx context.Context, id uint) (*models.Post, error)
    List(ctx context.Context, limit, offset int) ([]models.Post, int64, error)
    Publish(ctx context.Context, id uint) error
}

// UserService 定义用户服务接口
type UserService interface {
    Register(ctx context.Context, user *models.User) error
    Login(ctx context.Context, email, password string) (*models.User, error)
    UpdateProfile(ctx context.Context, user *models.User) error
    GetByID(ctx context.Context, id uint) (*models.User, error)
}
```

**接口设计要点**：
1. **使用 context.Context**：支持超时和取消
2. **返回错误**：所有操作都返回 error
3. **指针 vs 值**：大对象用指针，小对象用值
4. **命名清晰**：方法名清晰表达意图

### 2.3 服务实现

**PostService 实现**：
```go
package service

import (
    "context"
    "errors"
    "fmt"
    "github.com/yourusername/ppmtest/internal/models"
    "gorm.io/gorm"
)

type postService struct {
    db *gorm.DB
}

// NewPostService 创建文章服务实例
func NewPostService(db *gorm.DB) PostService {
    return &postService{db: db}
}

// Create 创建文章
func (s *postService) Create(ctx context.Context, post *models.Post) error {
    // 1. 业务验证
    if post.Title == "" {
        return errors.New("title cannot be empty")
    }
    
    if post.Slug == "" {
        return errors.New("slug cannot be empty")
    }
    
    // 2. 生成唯一 slug（如果需要）
    if err := s.ensureUniqueSlug(ctx, post); err != nil {
        return fmt.Errorf("failed to generate slug: %w", err)
    }
    
    // 3. 保存到数据库
    if err := s.db.WithContext(ctx).Create(post).Error; err != nil {
        return fmt.Errorf("failed to create post: %w", err)
    }
    
    return nil
}

// Update 更新文章
func (s *postService) Update(ctx context.Context, post *models.Post) error {
    // 1. 检查文章是否存在
    existing, err := s.GetByID(ctx, post.ID)
    if err != nil {
        return fmt.Errorf("post not found: %w", err)
    }
    
    // 2. 业务规则检查
    if existing.Status == "published" && post.Status != "published" {
        return errors.New("cannot change status of published post")
    }
    
    // 3. 更新
    if err := s.db.WithContext(ctx).Save(post).Error; err != nil {
        return fmt.Errorf("failed to update post: %w", err)
    }
    
    return nil
}

// Delete 删除文章
func (s *postService) Delete(ctx context.Context, id uint) error {
    result := s.db.WithContext(ctx).Delete(&models.Post{}, id)
    if result.Error != nil {
        return fmt.Errorf("failed to delete post: %w", result.Error)
    }
    
    if result.RowsAffected == 0 {
        return errors.New("post not found")
    }
    
    return nil
}

// GetByID 获取文章详情
func (s *postService) GetByID(ctx context.Context, id uint) (*models.Post, error) {
    var post models.Post
    err := s.db.WithContext(ctx).
        Preload("Author").  // 预加载作者信息
        First(&post, id).Error
        
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, errors.New("post not found")
        }
        return nil, fmt.Errorf("failed to get post: %w", err)
    }
    
    return &post, nil
}

// List 获取文章列表
func (s *postService) List(ctx context.Context, limit, offset int) ([]models.Post, int64, error) {
    var posts []models.Post
    var total int64
    
    // 1. 统计总数
    if err := s.db.WithContext(ctx).Model(&models.Post{}).Count(&total).Error; err != nil {
        return nil, 0, fmt.Errorf("failed to count posts: %w", err)
    }
    
    // 2. 查询列表
    if err := s.db.WithContext(ctx).
        Preload("Author").
        Order("created_at DESC").
        Limit(limit).
        Offset(offset).
        Find(&posts).Error; err != nil {
        return nil, 0, fmt.Errorf("failed to list posts: %w", err)
    }
    
    return posts, total, nil
}

// Publish 发布文章
func (s *postService) Publish(ctx context.Context, id uint) error {
    return s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        var post models.Post
        if err := tx.First(&post, id).Error; err != nil {
            return fmt.Errorf("post not found: %w", err)
        }
        
        // 业务逻辑：只能发布草稿
        if post.Status != "draft" {
            return errors.New("only draft posts can be published")
        }
        
        // 更新状态
        now := time.Now()
        post.Status = "published"
        post.PublishedAt = &now
        
        if err := tx.Save(&post).Error; err != nil {
            return fmt.Errorf("failed to publish post: %w", err)
        }
        
        // 可以在这里添加其他业务逻辑
        // 例如：发送通知、更新缓存等
        
        return nil
    })
}

// ensureUniqueSlug 确保 slug 唯一
func (s *postService) ensureUniqueSlug(ctx context.Context, post *models.Post) error {
    var count int64
    err := s.db.WithContext(ctx).
        Model(&models.Post{}).
        Where("slug = ? AND id != ?", post.Slug, post.ID).
        Count(&count).Error
        
    if err != nil {
        return err
    }
    
    if count > 0 {
        return errors.New("slug already exists")
    }
    
    return nil
}
```

## 3. 错误处理策略

### 3.1 错误包装

**使用 fmt.Errorf 和 %w**：
```go
// ✅ 好的错误包装
if err := db.Create(post).Error; err != nil {
    return fmt.Errorf("failed to create post: %w", err)  // %w 保留原始错误
}

// 错误链可以被检查
if errors.Is(err, gorm.ErrRecordNotFound) {
    // 处理记录未找到
}
```

### 3.2 自定义错误类型

**定义业务错误**：
```go
package errors

import "fmt"

// BusinessError 业务错误
type BusinessError struct {
    Code    string
    Message string
    Err     error
}

func (e *BusinessError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%s] %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func (e *BusinessError) Unwrap() error {
    return e.Err
}

// 预定义错误
var (
    ErrPostNotFound = &BusinessError{Code: "POST_NOT_FOUND", Message: "Post not found"}
    ErrInvalidInput = &BusinessError{Code: "INVALID_INPUT", Message: "Invalid input"}
)
```

**使用自定义错误**：
```go
func (s *postService) GetByID(ctx context.Context, id uint) (*models.Post, error) {
    var post models.Post
    err := s.db.WithContext(ctx).First(&post, id).Error
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, ErrPostNotFound
        }
        return nil, fmt.Errorf("database error: %w", err)
    }
    return &post, nil
}
```

## 4. 事务管理

### 4.1 GORM 事务

**基本事务**：
```go
func (s *postService) CreateWithTags(ctx context.Context, post *models.Post, tagNames []string) error {
    return s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        // 1. 创建文章
        if err := tx.Create(post).Error; err != nil {
            return err  // 返回 error 会自动回滚
        }
        
        // 2. 创建标签关联
        for _, tagName := range tagNames {
            tag := &models.Tag{Name: tagName}
            if err := tx.FirstOrCreate(tag, models.Tag{Name: tagName}).Error; err != nil {
                return err
            }
            
            // 创建关联
            if err := tx.Exec("INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)", post.ID, tag.ID).Error; err != nil {
                return err
            }
        }
        
        return nil  // 返回 nil 提交事务
    })
}
```

### 4.2 手动事务控制

**需要更精细控制时**：
```go
func (s *postService) ComplexOperation(ctx context.Context) error {
    tx := s.db.WithContext(ctx).Begin()
    defer func() {
        if r := recover(); r != nil {
            tx.Rollback()
            panic(r)  // 重新抛出 panic
        }
    }()
    
    if err := tx.Error; err != nil {
        return err
    }
    
    // 业务操作
    if err := step1(tx); err != nil {
        tx.Rollback()
        return err
    }
    
    if err := step2(tx); err != nil {
        tx.Rollback()
        return err
    }
    
    return tx.Commit().Error
}
```

## 5. 依赖注入容器

### 5.1 简单容器实现

**容器结构**：
```go
package container

import (
    "gorm.io/gorm"
    "github.com/yourusername/ppmtest/internal/service"
)

// Container 依赖注入容器
type Container struct {
    DB           *gorm.DB
    PostService  service.PostService
    UserService  service.UserService
}

// NewContainer 创建容器
func NewContainer(db *gorm.DB) *Container {
    c := &Container{DB: db}
    
    // 初始化服务（依赖注入）
    c.PostService = service.NewPostService(db)
    c.UserService = service.NewUserService(db)
    
    return c
}
```

### 5.2 使用容器

**在 main.go 中初始化**：
```go
func main() {
    // 1. 初始化数据库
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    
    // 2. 创建容器
    container := container.NewContainer(db)
    
    // 3. 设置路由
    r := gin.Default()
    
    // 4. 注入服务
    handlers.RegisterPostHandlers(r, container.PostService)
    handlers.RegisterUserHandlers(r, container.UserService)
    
    r.Run(":8080")
}
```

## 6. 测试服务层

### 6.1 单元测试

**表驱动测试**：
```go
func TestPostService_GetByID(t *testing.T) {
    // 1. 设置测试数据库
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)
    
    // 2. 创建测试数据
    post := &models.Post{
        Title: "Test Post",
        Slug:  "test-post",
    }
    db.Create(post)
    
    // 3. 创建服务
    service := NewPostService(db)
    
    // 4. 定义测试用例
    tests := []struct {
        name    string
        id      uint
        want    *models.Post
        wantErr bool
    }{
        {
            name:    "valid id",
            id:      post.ID,
            want:    post,
            wantErr: false,
        },
        {
            name:    "invalid id",
            id:      999,
            want:    nil,
            wantErr: true,
        },
    }
    
    // 5. 运行测试
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := service.GetByID(context.Background(), tt.id)
            if (err != nil) != tt.wantErr {
                t.Errorf("GetByID() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("GetByID() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

### 6.2 Mock 依赖

**使用接口和 Mock**：
```go
// MockRepository 用于测试
type MockRepository struct {
    mock.Mock
}

func (m *MockRepository) GetByID(id uint) (*models.Post, error) {
    args := m.Called(id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*models.Post), args.Error(1)
}

// 测试使用 Mock
func TestPostServiceWithMock(t *testing.T) {
    mockRepo := new(MockRepository)
    mockRepo.On("GetByID", uint(1)).Return(&models.Post{ID: 1}, nil)
    
    service := NewPostServiceWithRepo(mockRepo)
    post, err := service.GetByID(context.Background(), 1)
    
    assert.NoError(t, err)
    assert.Equal(t, uint(1), post.ID)
    mockRepo.AssertExpectations(t)
}
```

## 7. 最佳实践

### 7.1 使用 Context

**所有服务方法都应该接受 context**：
```go
// ✅ 好的设计
func (s *postService) GetByID(ctx context.Context, id uint) (*models.Post, error) {
    // 可以设置超时
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    return s.db.WithContext(ctx).GetByID(id)
}

// ❌ 不好的设计
func (s *postService) GetByID(id uint) (*models.Post, error) {
    // 无法控制超时和取消
}
```

### 7.2 验证输入

**尽早验证，快速失败**：
```go
func (s *postService) Create(ctx context.Context, post *models.Post) error {
    // 1. 参数验证
    if post == nil {
        return errors.New("post cannot be nil")
    }
    
    if post.Title == "" {
        return ErrInvalidInput
    }
    
    // 2. 业务规则验证
    if len(post.Title) > 255 {
        return errors.New("title too long")
    }
    
    // 3. 持久化
    return s.db.Create(post).Error
}
```

### 7.3 日志记录

**记录关键操作**：
```go
func (s *postService) Create(ctx context.Context, post *models.Post) error {
    log.Info("Creating post", "title", post.Title)
    
    if err := s.db.Create(post).Error; err != nil {
        log.Error("Failed to create post", "error", err)
        return err
    }
    
    log.Info("Post created successfully", "id", post.ID)
    return nil
}
```

## 8. 实战练习

### 练习 1：实现 UserService

```go
// 你的实现
type userService struct {
    db *gorm.DB
}

func NewUserService(db *gorm.DB) UserService {
    // TODO: 实现
}

func (s *userService) Register(ctx context.Context, user *models.User) error {
    // TODO: 实现用户注册逻辑
    // 1. 验证邮箱唯一性
    // 2. 哈希密码
    // 3. 创建用户
}
```

### 练习 2：添加文章搜索功能

```go
// 在 PostService 接口中添加
Search(ctx context.Context, keyword string, limit, offset int) ([]models.Post, int64, error)

// 实现搜索逻辑
func (s *postService) Search(ctx context.Context, keyword string, limit, offset int) ([]models.Post, int64, error) {
    // TODO: 实现全文搜索
    // 提示：使用 LIKE 或全文索引
}
```

## 9. 总结

### 核心要点

1. **分层架构**：服务层专注于业务逻辑
2. **接口设计**：定义清晰的接口契约
3. **依赖注入**：松耦合设计，便于测试
4. **错误处理**：正确的错误包装和传递
5. **事务管理**：确保数据一致性
6. **可测试性**：使用 Mock 和表驱动测试

### 常见陷阱

- ❌ 在服务层直接访问 HTTP 请求
- ❌ 业务逻辑分散在多个层次
- ❌ 忽略 context 的使用
- ❌ 错误信息泄露敏感数据

### 下一步

- [ ] 学习 Web 框架最佳实践（Lesson 03）
- [ ] 实现中间件系统
- [ ] 编写集成测试
- [ ] 了解性能优化技巧

### 相关资源

- [Clean Architecture in Go](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection Patterns](https://github.com/golang/go/wiki/CodeReviewComments#dependency-injection)
- [Go Context](https://go.dev/blog/context)

---

**作者**: Go 博客系统项目组  
**更新日期**: 2025-12-28  
**难度**: ⭐⭐⭐☆☆（中级）  
**预计学习时间**: 3-4 小时