# Lesson 05: Go 测试完整指南

## 📖 概念解释

### 1. Go 测试基础

Go 内置了强大的测试框架：
- **testing 包**：标准库提供的测试工具
- **go test 命令**：运行测试的命令行工具
- **表驱动测试**：Go 推荐的测试模式
- **基准测试**：性能测试

### 2. 测试类型

- **单元测试**：测试单个函数或方法
- **集成测试**：测试多个组件的交互
- **基准测试**：测量代码性能
- **示例测试**：既是文档又是测试

## 💡 最佳实践

### 1. 基本测试结构

```go
func TestAdd(t *testing.T) {
    result := Add(2, 3)
    expected := 5
    
    if result != expected {
        t.Errorf("Add(2, 3) = %d; want %d", result, expected)
    }
}
```

**测试文件命名**：
- 文件名以 `_test.go` 结尾
- 与被测试文件在同一包中
- 测试函数以 `Test` 开头

### 2. 表驱动测试

```go
func TestUserService_Register(t *testing.T) {
    tests := []struct {
        name    string
        user    *models.User
        wantErr error
    }{
        {
            name: "valid user",
            user: &models.User{
                Username: "testuser",
                Email:    "test@example.com",
                Password: "password123",
            },
            wantErr: nil,
        },
        {
            name: "duplicate email",
            user: &models.User{
                Username: "testuser2",
                Email:    "test@example.com",
                Password: "password123",
            },
            wantErr: repository.ErrUserAlreadyExists,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockRepo := NewMockUserRepository()
            userService := service.NewUserService(mockRepo)

            err := userService.Register(tt.user)

            if !errors.Is(err, tt.wantErr) {
                t.Errorf("Register() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

**表驱动测试优势**：
- **易于扩展**：添加新测试用例只需添加一行
- **清晰结构**：每个用例的输入和期望一目了然
- **并行执行**：每个子测试可以独立运行

### 3. 使用 Mock 进行测试

```go
type MockUserRepository struct {
    users map[uint]*models.User
}

func NewMockUserRepository() *MockUserRepository {
    return &MockUserRepository{
        users: make(map[uint]*models.User),
    }
}

func (m *MockUserRepository) Create(user *models.User) error {
    user.ID = uint(len(m.users) + 1)
    m.users[user.ID] = user
    return nil
}

func (m *MockUserRepository) FindByEmail(email string) (*models.User, error) {
    for _, user := range m.users {
        if user.Email == email {
            return user, nil
        }
    }
    return nil, repository.ErrUserNotFound
}
```

**Mock 实现要点**：
- 实现 Repository 接口
- 使用内存数据结构（如 map）存储数据
- 简化实现，只关注测试需要的逻辑

### 4. 测试夹具（Test Fixtures）

```go
func setupTestDB(t *testing.T) *gorm.DB {
    t.Helper()
    
    db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
    if err != nil {
        t.Fatalf("failed to create test database: %v", err)
    }
    
    if err := db.AutoMigrate(&models.User{}); err != nil {
        t.Fatalf("failed to migrate: %v", err)
    }
    
    t.Cleanup(func() {
        sqlDB, _ := db.DB()
        sqlDB.Close()
    })
    
    return db
}

func TestUserServiceWithDB(t *testing.T) {
    db := setupTestDB(t)
    userRepo := repository.NewUserRepository(db)
    userService := service.NewUserService(userRepo)
    
    // 测试代码
}
```

**测试夹具优势**：
- **重用性**：多个测试可以共享相同的设置
- **自动清理**：使用 `t.Cleanup()` 确保资源释放
- **隔离性**：每个测试使用独立的数据库

### 5. 基准测试

```go
func BenchmarkPostService_ListPosts(b *testing.B) {
    mockRepo := NewMockPostRepository()
    postService := service.NewPostService(mockRepo, nil)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        postService.ListPosts(1, 10, "published")
    }
}

func BenchmarkUserRepository_FindByID(b *testing.B) {
    mockRepo := NewMockUserRepository()
    user := &models.User{ID: 1, Email: "test@example.com"}
    mockRepo.Create(user)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        mockRepo.FindByID(1)
    }
}
```

**基准测试要点**：
- 使用 `b.N` 循环
- 调用 `b.ResetTimer()` 重置计时器
- 运行：`go test -bench=. -benchmem`

### 6. 集成测试

```go
func TestAPIIntegration(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test")
    }
    
    db := setupTestDB(t)
    container := container.NewContainer(db)
    
    router := router.Setup(container.Users, container.Posts)
    
    req := httptest.NewRequest("POST", "/api/v1/auth/register", strings.NewReader(`{
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }`))
    req.Header.Set("Content-Type", "application/json")
    
    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)
    
    if w.Code != http.StatusCreated {
        t.Errorf("expected status %d, got %d", http.StatusCreated, w.Code)
    }
}
```

**集成测试要点**：
- 测试多个组件的交互
- 可以跳过：使用 `-short` 标志
- 使用 `httptest` 测试 HTTP 处理器

## ⚠️ 常见陷阱

### 1. 测试包含业务逻辑

**问题代码**：
```go
func TestUserService_Register(t *testing.T) {
    userService := NewUserService(realRepo)
    
    user := &models.User{Email: "test@example.com"}
    err := userService.Register(user)
    
    if err != nil {
        t.Error(err)
    }
    
    // 手动检查数据库
    dbUser, _ := realRepo.FindByEmail("test@example.com")
    if dbUser.Status != "active" {
        t.Error("user status should be active")
    }
}
```

**问题**：测试逻辑复杂，依赖数据库

**解决方案**：
```go
func TestUserService_Register(t *testing.T) {
    mockRepo := NewMockUserRepository()
    userService := NewUserService(mockRepo)
    
    user := &models.User{Email: "test@example.com"}
    err := userService.Register(user)
    
    if err != nil {
        t.Errorf("Register() error = %v", err)
    }
    
    if user.Status != "active" {
        t.Errorf("user status = %s, want active", user.Status)
    }
}
```

### 2. 忽略错误检查

**问题代码**：
```go
func TestCreatePost(t *testing.T) {
    post := &models.Post{Title: "Test"}
    postService.CreatePost(post, 1)
    // 没有检查错误
}
```

**解决方案**：
```go
func TestCreatePost(t *testing.T) {
    post := &models.Post{Title: "Test"}
    err := postService.CreatePost(post, 1)
    
    if err != nil {
        t.Fatalf("CreatePost() error = %v", err)
    }
}
```

### 3. 测试之间相互依赖

**问题代码**：
```go
var globalUserID uint

func TestCreateUser(t *testing.T) {
    user := &models.User{Username: "test"}
    userService.Register(user)
    globalUserID = user.ID
}

func TestGetUser(t *testing.T) {
    user, _ := userService.GetUserProfile(globalUserID)
    // 依赖前面的测试
}
```

**解决方案**：
```go
func TestCreateAndGetUser(t *testing.T) {
    userService := NewUserService(mockRepo)
    
    user := &models.User{Username: "test"}
    if err := userService.Register(user); err != nil {
        t.Fatal(err)
    }
    
    foundUser, err := userService.GetUserProfile(user.ID)
    if err != nil {
        t.Fatal(err)
    }
    
    if foundUser.Username != "test" {
        t.Errorf("username = %s, want test", foundUser.Username)
    }
}
```

### 4. 硬编码测试数据

**问题**：测试数据难以维护

**解决方案**：
```go
func newTestUser(username, email string) *models.User {
    return &models.User{
        Username: username,
        Email:    email,
        Password: "password123",
        Status:   "active",
        Role:     "author",
    }
}

func TestUserService_Register(t *testing.T) {
    user := newTestUser("testuser", "test@example.com")
    // 测试逻辑
}
```

## 🔧 实战示例

### 完整的测试套件

参考 `internal/service/user_service_test.go` 的实现：

1. **Mock Repository**：实现接口用于测试
2. **表驱动测试**：覆盖多种场景
3. **错误验证**：检查错误类型和消息
4. **并行测试**：使用 `t.Parallel()`

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/service

# 运行特定测试
go test -run TestUserService_Register ./internal/service

# 运行测试并显示覆盖率
go test -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# 运行基准测试
go test -bench=. -benchmem ./...

# 运行集成测试（跳过短测试）
go test -short ./...
```

### 子测试

```go
func TestUserService(t *testing.T) {
    mockRepo := NewMockUserRepository()
    userService := NewUserService(mockRepo)
    
    t.Run("Register", func(t *testing.T) {
        t.Run("valid user", func(t *testing.T) {
            // 测试有效用户注册
        })
        
        t.Run("duplicate email", func(t *testing.T) {
            // 测试重复邮箱
        })
    })
    
    t.Run("Login", func(t *testing.T) {
        // 测试登录
    })
}
```

## ✅ 练习任务

### 任务 1：为 PostService 编写测试

```go
func TestPostService_CreatePost(t *testing.T) {
    tests := []struct {
        name      string
        post      *models.Post
        authorID  uint
        wantErr   error
    }{
        // 测试用例
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // 测试逻辑
        })
    }
}
```

### 任务 2：编写 HTTP 处理器测试

```go
func TestUserHandler_Register(t *testing.T) {
    router := setupRouter()
    
    req := httptest.NewRequest("POST", "/api/v1/auth/register", 
        strings.NewReader(`{"username":"test","email":"test@example.com","password":"password123"}`))
    req.Header.Set("Content-Type", "application/json")
    
    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusCreated, w.Code)
}
```

### 任务 3：编写基准测试

```go
func BenchmarkRepository_FindByID(b *testing.B) {
    repo := setupRepository()
    
    b.Run("sqlite", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            repo.FindByID(1)
        }
    })
    
    b.Run("mysql", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            repo.FindByID(1)
        }
    })
}
```

### 任务 4：实现测试覆盖率报告

```bash
# 生成覆盖率报告
go test -coverprofile=coverage.out ./...

# 查看HTML报告
go tool cover -html=coverage.out

# 检查覆盖率是否达标
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total
```

## 📚 延伸阅读

- [Go 测试官方文档](https://go.dev/doc/tutorial/add-a-test)
- [表驱动测试](https://dave.cheney.net/2019/05/07/prefer-table-driven-tests)
- [测试最佳实践](https://go.dev/doc/effective_go#testing)
- [httptest 包](https://go.dev/pkg/net/http/httptest/)

## 🎯 总结

本课程学习了：
- ✅ Go 测试基础
- ✅ 表驱动测试模式
- ✅ Mock 实现和测试夹具
- ✅ 基准测试和性能测试
- ✅ 集成测试编写
- ✅ 测试覆盖率报告
- ✅ 常见测试陷阱和解决方案

下一步：学习性能优化和部署（Lesson 06）