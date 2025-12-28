# Lesson 02: Go 服务层架构设计

## 📖 概念解释

### 1. 服务层的职责

服务层（Service Layer）是应用的业务逻辑层，它位于数据访问层（Repository）和表现层（HTTP Handler）之间。

**主要职责**：
- 实现业务规则和验证
- 协调多个 Repository 的操作
- 处理事务边界
- 权限检查和业务逻辑
- 提供用例（Use Case）级别的 API

### 2. 依赖注入（Dependency Injection）

依赖注入是一种设计模式，通过将依赖的对象作为参数传递，而不是在对象内部创建。

**为什么使用依赖注入？**
- **可测试性**：可以轻松注入 mock 对象进行测试
- **松耦合**：组件之间通过接口通信，降低耦合度
- **灵活性**：可以方便地替换实现

## 💡 最佳实践

### 1. 服务接口设计

```go
type UserService interface {
    Register(user *models.User) error
    Login(email, password string) (*models.User, error)
    GetUserProfile(id uint) (*models.User, error)
    UpdateProfile(user *models.User) error
    DeleteUser(id uint, requesterID uint) error
}
```

**接口设计原则**：
- **面向用例**：方法名反映业务用例，而非技术操作
- **参数明确**：参数清晰表达业务上下文
- **返回业务错误**：返回业务相关的错误类型
- **单一职责**：每个服务负责一个领域的业务逻辑

### 2. 业务验证

```go
func (s *userService) Register(user *models.User) error {
    // 业务规则验证
    if user.Email == "" {
        return ErrEmailRequired
    }
    
    // 检查业务约束
    existingUser, err := s.userRepo.FindByEmail(user.Email)
    if err == nil && existingUser != nil {
        return ErrUserAlreadyExists
    }
    
    // 应用默认值
    user.Status = "active"
    user.Role = "author"
    
    return s.userRepo.Create(user)
}
```

**验证层次**：
- **输入验证**：检查必填字段、格式等
- **业务规则验证**：检查业务约束和规则
- **数据一致性验证**：检查数据之间的关系

### 3. 权限检查

```go
func (s *userService) DeleteUser(id uint, requesterID uint) error {
    // 获取请求者信息
    requester, err := s.userRepo.FindByID(requesterID)
    if err != nil {
        return err
    }
    
    // 权限检查
    if requester.Role != "admin" && requesterID != id {
        return ErrUnauthorized
    }
    
    return s.userRepo.Delete(id)
}
```

**权限检查要点**：
- 在服务层进行权限验证
- 基于角色的访问控制（RBAC）
- 基于资源的访问控制（用户只能操作自己的资源）

### 4. 依赖注入容器

```go
type Container struct {
	DB       *database.Database
	Users    service.UserService
	Posts    service.PostService
	Comments service.CommentService
}

func NewContainer(db *database.Database) *Container {
    // 创建 Repositories
    userRepo := repository.NewUserRepository(db.DB)
    postRepo := repository.NewPostRepository(db.DB)
    commentRepo := repository.NewCommentRepository(db.DB)
    
    // 创建 Services（注入依赖）
    userService := service.NewUserService(userRepo)
    postService := service.NewPostService(postRepo, userRepo)
    commentService := service.NewCommentService(commentRepo, postRepo, userRepo)
    
    return &Container{
        DB:       db,
        Users:    userService,
        Posts:    postService,
        Comments: commentService,
    }
}
```

**依赖注入容器的作用**：
- 集中管理所有依赖关系
- 简化依赖的创建和传递
- 便于测试时替换依赖

## ⚠️ 常见陷阱

### 1. 业务逻辑泄漏到 Repository

**问题代码**：
```go
func (r *postRepository) FindPublishedPosts() ([]*models.Post, error) {
    return r.db.Where("status = ?", "published").Find(&posts)
}
```

**问题**：Repository 不应该知道什么是"已发布"

**解决方案**：
```go
func (r *postRepository) List(offset, limit int, status string) ([]*models.Post, error) {
    query := r.db.Model(&models.Post{})
    if status != "" {
        query = query.Where("status = ?", status)
    }
    return query.Find(&posts)
}

// 在 Service 层调用
func (s *postService) GetPublishedPosts(page, pageSize int) {
    return s.postRepo.List(offset, limit, "published")
}
```

### 2. 忽略错误处理

**问题代码**：
```go
func (s *postService) PublishPost(id uint) error {
    post, _ := s.postRepo.FindByID(id)  // 忽略错误
    post.Status = "published"
    s.postRepo.Update(post)  // 忽略错误
    return nil
}
```

**解决方案**：
```go
func (s *postService) PublishPost(id uint) error {
    post, err := s.postRepo.FindByID(id)
    if err != nil {
        return err
    }
    
    post.Status = "published"
    if err := s.postRepo.Update(post); err != nil {
        return err
    }
    
    return nil
}
```

### 3. 服务之间直接调用

**问题代码**：
```go
func (s *postService) CreatePost(post *models.Post) error {
    // 直接调用另一个服务
    if err := s.userService.NotifyUser(post.AuthorID); err != nil {
        return err
    }
}
```

**问题**：服务之间直接调用导致紧耦合

**解决方案 - 使用领域事件**：
```go
type PostCreatedEvent struct {
    PostID   uint
    AuthorID uint
}

func (s *postService) CreatePost(post *models.Post) error {
    if err := s.postRepo.Create(post); err != nil {
        return err
    }
    
    // 发布事件
    s.eventBus.Publish(PostCreatedEvent{PostID: post.ID, AuthorID: post.AuthorID})
    return nil
}
```

### 4. 事务边界不清晰

**问题**：跨多个 Repository 的操作没有事务保护

```go
func (s *postService) CreatePostWithTags(post *models.Post, tags []string) error {
    s.postRepo.Create(post)
    for _, tag := range tags {
        s.tagRepo.Create(&models.Tag{Name: tag})  // 如果失败怎么办？
    }
}
```

**解决方案 - 使用事务**：
```go
func (s *postService) CreatePostWithTags(post *models.Post, tags []string) error {
    tx := s.db.Begin()
    defer func() {
        if r := recover(); r != nil {
            tx.Rollback()
        }
    }()
    
    if err := tx.Create(post).Error; err != nil {
        tx.Rollback()
        return err
    }
    
    for _, tag := range tags {
        if err := tx.Create(&models.Tag{Name: tag}).Error; err != nil {
            tx.Rollback()
            return err
        }
    }
    
    return tx.Commit().Error
}
```

## 🔧 实战示例

### 完整的服务实现

参考 `internal/service/post_service.go` 的实现：

1. **接口定义**：声明所有业务用例
2. **依赖注入**：通过构造函数注入所需的 Repository
3. **业务验证**：在执行操作前验证业务规则
4. **权限检查**：确保用户有权限执行操作
5. **错误处理**：将底层错误转换为业务错误

### 复杂业务逻辑示例

创建文章并自动生成摘要：

```go
func (s *postService) CreatePostWithAutoSummary(post *models.Post) error {
    if post.Content == "" {
        return ErrPostContentRequired
    }
    
    post.Summary = generateSummary(post.Content)
    
    if post.Slug == "" {
        post.Slug = generateSlug(post.Title)
    }
    
    return s.postRepo.Create(post)
}

func generateSummary(content string, maxLength int) string {
    runes := []rune(content)
    if len(runes) <= maxLength {
        return content
    }
    return string(runes[:maxLength]) + "..."
}
```

## ✅ 练习任务

### 任务 1：实现文章归档功能

在 PostService 中添加归档功能：

```go
func (s *postService) ArchiveOldPosts(days int) error {
    cutoffDate := time.Now().AddDate(0, 0, -days)
    posts, _ := s.postRepo.FindOlderThan(cutoffDate)
    
    for _, post := range posts {
        post.Status = "archived"
        s.postRepo.Update(post)
    }
    
    return nil
}
```

### 任务 2：实现用户活跃度追踪

添加用户活跃度计算：

```go
func (s *userService) GetUserActivity(userID uint, days int) (*ActivityStats, error) {
    postsCount, _ := s.postRepo.CountByUser(userID, days)
    commentsCount, _ := s.commentRepo.CountByUser(userID, days)
    
    return &ActivityStats{
        PostsCount:    postsCount,
        CommentsCount: commentsCount,
    }, nil
}
```

### 任务 3：实现缓存层

在服务层添加缓存：

```go
type cachedPostService struct {
    service  PostService
    cache    *Cache
    ttl      time.Duration
}

func (s *cachedPostService) GetPostByID(id uint) (*models.Post, error) {
    cacheKey := fmt.Sprintf("post:%d", id)
    
    if cached, found := s.cache.Get(cacheKey); found {
        return cached.(*models.Post), nil
    }
    
    post, err := s.service.GetPostByID(id)
    if err == nil {
        s.cache.Set(cacheKey, post, s.ttl)
    }
    
    return post, err
}
```

### 任务 4：编写单元测试

使用 mock Repository 测试服务层：

```go
type MockUserRepository struct {
    users map[uint]*models.User
}

func (m *MockUserRepository) FindByID(id uint) (*models.User, error) {
    user, ok := m.users[id]
    if !ok {
        return nil, repository.ErrUserNotFound
    }
    return user, nil
}

func TestUserService_GetUserProfile(t *testing.T) {
    mockRepo := &MockUserRepository{users: map[uint]*models.User{
        1: {ID: 1, Username: "test"},
    }}
    
    service := NewUserService(mockRepo)
    user, err := service.GetUserProfile(1)
    
    assert.NoError(t, err)
    assert.Equal(t, "test", user.Username)
}
```

## 📚 延伸阅读

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection Principles](https://github.com/google/wire)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Go Service Patterns](https://medium.com/@benbjohnson/structuring-applications-in-go-3b04be4ff091)

## 🎯 总结

本课程学习了：
- ✅ 服务层的职责和设计
- ✅ 依赖注入的使用
- ✅ 业务验证和权限检查
- ✅ 错误处理最佳实践
- ✅ 避免常见的服务层陷阱
- ✅ 事务边界管理

下一步：学习 HTTP API 层实现（Lesson 03）