# Lesson 06: 测试最佳实践

## 目录
- [Go 测试基础](#go-测试基础)
- [表驱动测试](#表驱动测试)
- [HTTP 测试](#http-测试)
- [数据库测试](#数据库测试)
- [Mock 和 Stub](#mock-和-stub)
- [测试覆盖率](#测试覆盖率)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## Go 测试基础

### 测试文件组织

```go
// 源文件: internal/service/post.go
package service

type PostService struct {
    repo PostRepository
}

func (s *PostService) CreatePost(title, content string) (*Post, error) {
    if title == "" {
        return nil, errors.New("title is required")
    }
    post := &Post{Title: title, Content: content}
    if err := s.repo.Create(post); err != nil {
        return nil, err
    }
    return post, nil
}

// 测试文件: internal/service/post_test.go
package service

import (
    "testing"
)

func TestCreatePost(t *testing.T) {
    // 测试代码
}
```

### 基本测试结构

```go
func TestCreatePost(t *testing.T) {
    // 1. 准备测试数据
    service := NewPostService(mockRepo)
    title := "Test Post"
    content := "Test Content"
    
    // 2. 执行被测试函数
    post, err := service.CreatePost(title, content)
    
    // 3. 验证结果
    if err != nil {
        t.Fatalf("expected no error, got %v", err)
    }
    
    if post.Title != title {
        t.Errorf("expected title %s, got %s", title, post.Title)
    }
    
    if post.Content != content {
        t.Errorf("expected content %s, got %s", content, post.Content)
    }
}
```

### 使用 t.Run 子测试

```go
func TestCreatePost(t *testing.T) {
    tests := []struct {
        name    string
        title   string
        content string
        wantErr bool
    }{
        {
            name:    "valid post",
            title:   "Test Post",
            content: "Test Content",
            wantErr: false,
        },
        {
            name:    "empty title",
            title:   "",
            content: "Test Content",
            wantErr: true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            service := NewPostService(mockRepo)
            post, err := service.CreatePost(tt.title, tt.content)
            
            if (err != nil) != tt.wantErr {
                t.Errorf("CreatePost() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            
            if !tt.wantErr && post.Title != tt.title {
                t.Errorf("expected title %s, got %s", tt.title, post.Title)
            }
        })
    }
}
```

### 测试辅助函数

```go
// setupTestDB 创建测试数据库
func setupTestDB(t *testing.T) *gorm.DB {
    t.Helper()  // 标记为辅助函数
    
    db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
    if err != nil {
        t.Fatalf("failed to create test database: %v", err)
    }
    
    // 运行迁移
    if err := db.AutoMigrate(&Post{}); err != nil {
        t.Fatalf("failed to migrate: %v", err)
    }
    
    return db
}

// assertEqual 比较两个值
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

// assertNoError 检查是否有错误
func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
}
```

---

## 表驱动测试

### 基本模式

```go
func TestValidatePost(t *testing.T) {
    tests := []struct {
        name    string
        post    *Post
        wantErr bool
        errMsg  string
    }{
        {
            name: "valid post",
            post: &Post{
                Title:   "Valid Title",
                Content: "Valid content",
            },
            wantErr: false,
        },
        {
            name: "empty title",
            post: &Post{
                Title:   "",
                Content: "Valid content",
            },
            wantErr: true,
            errMsg:  "title is required",
        },
        {
            name: "short content",
            post: &Post{
                Title:   "Valid Title",
                Content: "Short",
            },
            wantErr: true,
            errMsg:  "content too short",
        },
        {
            name: "missing both",
            post: &Post{
                Title:   "",
                Content: "",
            },
            wantErr: true,
            errMsg:  "title is required",
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidatePost(tt.post)
            
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidatePost() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            
            if tt.wantErr && err.Error() != tt.errMsg {
                t.Errorf("expected error message %q, got %q", tt.errMsg, err.Error())
            }
        })
    }
}
```

### 使用测试构建器

```go
// 测试数据构建器
type PostBuilder struct {
    post *Post
}

func NewPostBuilder() *PostBuilder {
    return &PostBuilder{
        post: &Post{
            Title:      "Default Title",
            Content:    "Default content that is long enough",
            Status:     "draft",
            AuthorID:   1,
        },
    }
}

func (b *PostBuilder) WithTitle(title string) *PostBuilder {
    b.post.Title = title
    return b
}

func (b *PostBuilder) WithContent(content string) *PostBuilder {
    b.post.Content = content
    return b
}

func (b *PostBuilder) WithStatus(status string) *PostBuilder {
    b.post.Status = status
    return b
}

func (b *PostBuilder) Build() *Post {
    return b.post
}

// 在测试中使用
func TestPublishPost(t *testing.T) {
    tests := []struct {
        name    string
        post    *Post
        wantErr bool
    }{
        {
            name:    "draft post",
            post:    NewPostBuilder().WithStatus("draft").Build(),
            wantErr: false,
        },
        {
            name:    "published post",
            post:    NewPostBuilder().WithStatus("published").Build(),
            wantErr: false,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := service.PublishPost(tt.post)
            if (err != nil) != tt.wantErr {
                t.Errorf("PublishPost() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

---

## HTTP 测试

### 使用 httptest

```go
package handlers

import (
    "net/http"
    "net/http/httptest"
    "testing"
    
    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
)

func TestGetPost(t *testing.T) {
    // 设置 Gin 为测试模式
    gin.SetMode(gin.TestMode)
    
    // 创建测试路由
    router := gin.New()
    router.GET("/posts/:id", func(c *gin.Context) {
        id := c.Param("id")
        c.JSON(200, gin.H{"id": id, "title": "Test Post"})
    })
    
    // 创建测试请求
    req := httptest.NewRequest("GET", "/posts/1", nil)
    w := httptest.NewRecorder()
    
    // 执行请求
    router.ServeHTTP(w, req)
    
    // 验证结果
    assert.Equal(t, 200, w.Code)
    assert.Contains(t, w.Body.String(), "Test Post")
}
```

### 完整的 Handler 测试

```go
func TestPostHandler_CreatePost(t *testing.T) {
    gin.SetMode(gin.TestMode)
    
    // 创建 mock service
    mockService := &MockPostService{
        posts: make(map[int64]*Post),
    }
    
    handler := NewPostHandler(mockService)
    
    // 创建测试路由
    router := gin.New()
    router.POST("/posts", handler.CreatePost)
    
    tests := []struct {
        name       string
        body       string
        wantStatus int
        wantErr    bool
    }{
        {
            name:       "valid post",
            body:       `{"title": "Test", "content": "Content"}`,
            wantStatus: 201,
            wantErr:    false,
        },
        {
            name:       "invalid json",
            body:       `invalid json`,
            wantStatus: 400,
            wantErr:    true,
        },
        {
            name:       "empty title",
            body:       `{"title": "", "content": "Content"}`,
            wantStatus: 400,
            wantErr:    true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest("POST", "/posts", strings.NewReader(tt.body))
            req.Header.Set("Content-Type", "application/json")
            w := httptest.NewRecorder()
            
            router.ServeHTTP(w, req)
            
            assert.Equal(t, tt.wantStatus, w.Code)
            
            if tt.wantErr {
                assert.Contains(t, w.Body.String(), "error")
            }
        })
    }
}
```

### 测试中间件

```go
func TestAuthMiddleware(t *testing.T) {
    gin.SetMode(gin.TestMode)
    
    middleware := AuthMiddleware{"secret"}
    
    router := gin.New()
    router.Use(middleware.Authenticate())
    router.GET("/protected", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "success"})
    })
    
    tests := []struct {
        name       string
        token      string
        wantStatus int
    }{
        {
            name:       "valid token",
            token:      generateValidToken(),
            wantStatus: 200,
        },
        {
            name:       "invalid token",
            token:      "invalid",
            wantStatus: 401,
        },
        {
            name:       "no token",
            token:      "",
            wantStatus: 401,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest("GET", "/protected", nil)
            if tt.token != "" {
                req.Header.Set("Authorization", "Bearer "+tt.token)
            }
            w := httptest.NewRecorder()
            
            router.ServeHTTP(w, req)
            
            assert.Equal(t, tt.wantStatus, w.Code)
        })
    }
}
```

---

## 数据库测试

### 使用内存数据库

```go
package repository

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "gorm.io/driver/sqlite"
    "gorm.io/gorm"
)

func setupTestDB(t *testing.T) *gorm.DB {
    t.Helper()
    
    db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
    assert.NoError(t, err)
    
    // 运行迁移
    err = db.AutoMigrate(&Post{}, &User{})
    assert.NoError(t, err)
    
    return db
}

func TestPostRepository_Create(t *testing.T) {
    db := setupTestDB(t)
    repo := NewPostRepository(db)
    
    post := &Post{
        Title:   "Test Post",
        Content: "Test Content",
    }
    
    err := repo.Create(post)
    assert.NoError(t, err)
    assert.NotZero(t, post.ID)
    assert.NotZero(t, post.CreatedAt)
}

func TestPostRepository_FindByID(t *testing.T) {
    db := setupTestDB(t)
    repo := NewPostRepository(db)
    
    // 先创建一个文章
    post := &Post{
        Title:   "Test Post",
        Content: "Test Content",
    }
    err := repo.Create(post)
    assert.NoError(t, err)
    
    // 测试查找
    found, err := repo.FindByID(post.ID)
    assert.NoError(t, err)
    assert.Equal(t, post.Title, found.Title)
    assert.Equal(t, post.Content, found.Content)
    
    // 测试不存在的文章
    _, err = repo.FindByID(999)
    assert.Error(t, err)
}
```

### 使用测试夹具（Fixtures）

```go
// fixtures_test.go
package test

import (
    "database/sql"
    "testing"
    
    "github.com/jmoiron/sqlx"
)

type Fixtures struct {
    db *sqlx.DB
}

func NewFixtures(db *sqlx.DB) *Fixtures {
    return &Fixtures{db: db}
}

func (f *Fixtures) LoadPosts(t *testing.T) []Post {
    t.Helper()
    
    posts := []Post{
        {Title: "Post 1", Content: "Content 1", Status: "published"},
        {Title: "Post 2", Content: "Content 2", Status: "draft"},
        {Title: "Post 3", Content: "Content 3", Status: "published"},
    }
    
    for _, post := range posts {
        _, err := f.db.NamedExec(
            "INSERT INTO posts (title, content, status) VALUES (:title, :content, :status)",
            post,
        )
        if err != nil {
            t.Fatalf("failed to load fixture: %v", err)
        }
    }
    
    return posts
}

func (f *Fixtures) Clean(t *testing.T) {
    t.Helper()
    
    _, err := f.db.Exec("DELETE FROM posts")
    if err != nil {
        t.Fatalf("failed to clean fixtures: %v", err)
    }
}

// 在测试中使用
func TestPostService_ListPublished(t *testing.T) {
    db := setupTestDB(t)
    fixtures := NewFixtures(db)
    
    // 加载测试数据
    posts := fixtures.LoadPosts(t)
    defer fixtures.Clean(t)
    
    // 执行测试
    service := NewPostService(db)
    published, err := service.ListPublished()
    
    assert.NoError(t, err)
    assert.Len(t, published, 2) // 只有两个 published
}
```

### 事务回滚测试

```go
func TestWithTransaction(t *testing.T) {
    db := setupTestDB(t)
    
    t.Run("successful transaction", func(t *testing.T) {
        err := db.Transaction(func(tx *gorm.DB) error {
            post := &Post{Title: "Test", Content: "Content"}
            return tx.Create(post).Error
        })
        
        assert.NoError(t, err)
        
        // 验证数据已保存
        var count int64
        db.Model(&Post{}).Count(&count)
        assert.Equal(t, int64(1), count)
    })
    
    t.Run("rollback on error", func(t *testing.T) {
        err := db.Transaction(func(tx *gorm.DB) error {
            post := &Post{Title: "Test", Content: "Content"}
            if err := tx.Create(post).Error; err != nil {
                return err
            }
            
            // 返回错误触发回滚
            return errors.New("rollback")
        })
        
        assert.Error(t, err)
        
        // 验证数据未保存
        var count int64
        db.Model(&Post{}).Count(&count)
        assert.Equal(t, int64(0), count)
    })
}
```

---

## Mock 和 Stub

### 使用接口进行 Mock

```go
// 定义接口
type PostRepository interface {
    FindByID(id int64) (*Post, error)
    Create(post *Post) error
    Update(post *Post) error
    Delete(id int64) error
}

// Mock 实现
type MockPostRepository struct {
    mock.Mock
}

func (m *MockPostRepository) FindByID(id int64) (*Post, error) {
    args := m.Called(id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*Post), args.Error(1)
}

func (m *MockPostRepository) Create(post *Post) error {
    args := m.Called(post)
    return args.Error(0)
}
```

### 使用 Mock 进行测试

```go
import (
    "testing"
    "github.com/stretchr/testify/mock"
)

func TestPostService_GetPost(t *testing.T) {
    mockRepo := new(MockPostRepository)
    service := NewPostService(mockRepo)
    
    // 设置期望
    expectedPost := &Post{
        ID:      1,
        Title:   "Test Post",
        Content: "Test Content",
    }
    mockRepo.On("FindByID", int64(1)).Return(expectedPost, nil)
    
    // 执行测试
    post, err := service.GetPost(1)
    
    // 验证结果
    assert.NoError(t, err)
    assert.Equal(t, expectedPost.Title, post.Title)
    
    // 验证 mock 调用
    mockRepo.AssertExpectations(t)
}

func TestPostService_GetPost_NotFound(t *testing.T) {
    mockRepo := new(MockPostRepository)
    service := NewPostService(mockRepo)
    
    // 设置期望返回错误
    mockRepo.On("FindByID", int64(999)).Return(nil, gorm.ErrRecordNotFound)
    
    // 执行测试
    post, err := service.GetPost(999)
    
    // 验证结果
    assert.Error(t, err)
    assert.Nil(t, post)
    
    // 验证 mock 调用
    mockRepo.AssertExpectations(t)
}
```

### 使用 httptest.Server

```go
func TestExternalAPI(t *testing.T) {
    // 创建 mock 服务器
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path != "/api/posts" {
            t.Errorf("expected path /api/posts, got %s", r.URL.Path)
        }
        
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"posts": []}`))
    }))
    defer server.Close()
    
    // 使用 mock 服务器的 URL
    client := NewAPIClient(server.URL)
    posts, err := client.GetPosts()
    
    assert.NoError(t, err)
    assert.NotNil(t, posts)
}
```

---

## 测试覆盖率

### 生成覆盖率报告

```bash
# 运行测试并生成覆盖率
go test ./... -cover

# 生成覆盖率报告（详细）
go test ./... -coverprofile=coverage.out

# 查看覆盖率报告
go tool cover -func=coverage.out

# 生成 HTML 报告
go tool cover -html=coverage.out -o coverage.html
```

### 设置覆盖率目标

```go
// 在 Makefile 中
test:
    go test ./... -coverprofile=coverage.out
    go tool cover -func=coverage.out | grep total | awk '{print $$3}' | \
        awk '{split($$0, a, "%"); if (a[1] < 80) {print "Coverage below 80%"; exit 1}}'

.PHONY: test
```

### 按包查看覆盖率

```bash
# 查看每个包的覆盖率
go test ./... -cover | grep -v "no test files"
```

---

## 最佳实践

### 1. 测试命名

```go
// ✅ 好的命名
func TestPostService_CreatePost_Success(t *testing.T)
func TestPostService_CreatePost_EmptyTitle(t *testing.T)
func TestPostService_CreatePost_DuplicateTitle(t *testing.T)

// ❌ 不好的命名
func TestPost1(t *testing.T)
func TestCreate(t *testing.T)
func TestPostError(t *testing.T)
```

### 2. 使用 t.Helper()

```go
// ✅ 使用 t.Helper() 标记辅助函数
func assertNoError(t *testing.T, err error) {
    t.Helper()  // 重要：标记为辅助函数
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
}

// 这样错误会报告给正确的测试行
func TestSomething(t *testing.T) {
    err := doSomething()
    assertNoError(t, err)  // 错误会报告在这一行，而不是在 assertNoError 内部
}
```

### 3. 测试应该独立

```go
// ❌ 不好：测试之间有依赖
func TestA(t *testing.T) {
    globalVar = 1  // 修改全局状态
}

func TestB(t *testing.T) {
    // 依赖 TestA 的结果
    assert.Equal(t, 1, globalVar)
}

// ✅ 好：每个测试独立
func TestA(t *testing.T) {
    var localVar = 1
    assert.Equal(t, 1, localVar)
}

func TestB(t *testing.T) {
    var localVar = 1
    assert.Equal(t, 1, localVar)
}
```

### 4. 使用测试特定的配置

```go
// config_test.go
func TestConfig(t *testing.T) {
    // 使用测试配置
    cfg := &Config{
        DBHost: "localhost",
        DBPort: 5432,
        DBName: "test_db",  // 测试数据库
    }
    
    service := NewService(cfg)
    // 测试代码
}
```

### 5. 并行测试

```go
func TestParallel(t *testing.T) {
    tests := []struct {
        name string
        input string
    }{
        {"test1", "input1"},
        {"test2", "input2"},
        {"test3", "input3"},
    }
    
    for _, tt := range tests {
        tt := tt  // 闭包捕获
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()  // 标记为可并行
            result := process(tt.input)
            assert.NotNil(t, result)
        })
    }
}
```

### 6. 使用 TestMain 进行设置

```go
var testDB *gorm.DB

func TestMain(m *testing.M) {
    // 设置测试环境
    testDB = setupTestDatabase()
    defer testDB.Close()
    
    // 运行测试
    code := m.Run()
    
    // 清理
    cleanupTestDatabase(testDB)
    
    os.Exit(code)
}
```

---

## 注意事项

### 1. 不要测试第三方代码

```go
// ❌ 不好：测试数据库驱动
func TestGORM(t *testing.T) {
    db, _ := gorm.Open(...)
    db.Create(&Post{})  // 这是在测试 GORM，不是你的代码
}

// ✅ 好：测试你的代码
func TestPostRepository_Create(t *testing.T) {
    // 测试你的 repository 逻辑
}
```

### 2. 避免测试实现细节

```go
// ❌ 不好：测试私有方法
func Test_privateMethod(t *testing.T) {
    // 不要直接测试私有方法
}

// ✅ 好：测试公共接口
func TestPublicMethod(t *testing.T) {
    // 通过公共接口测试
}
```

### 3. 测试应该快速

```go
// ❌ 不好：慢速测试
func TestSlowOperation(t *testing.T) {
    time.Sleep(10 * time.Second)  // 太慢了
}

// ✅ 好：使用 mock
func TestFastOperation(t *testing.T) {
    mockService := &MockService{}
    // 快速测试
}
```

### 4. 使用构建标签

```go
// +build integration

package integration

func TestIntegration(t *testing.T) {
    // 集成测试
}
```

```bash
# 默认不运行集成测试
go test ./...

# 运行集成测试
go test ./... -tags=integration
```

---

## 实战案例：博客系统测试

### 完整的测试套件

```go
// internal/service/post_test.go
package service

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

func TestPostService_CreatePost(t *testing.T) {
    t.Run("success", func(t *testing.T) {
        mockRepo := new(MockPostRepository)
        service := NewPostService(mockRepo)
        
        mockRepo.On("ExistsByTitle", "Test Post").Return(false, nil)
        mockRepo.On("Create", mock.AnythingOfType("*Post")).Return(nil)
        
        post, err := service.CreatePost("Test Post", "Content")
        
        assert.NoError(t, err)
        assert.Equal(t, "Test Post", post.Title)
        mockRepo.AssertExpectations(t)
    })
    
    t.Run("empty title", func(t *testing.T) {
        mockRepo := new(MockPostRepository)
        service := NewPostService(mockRepo)
        
        post, err := service.CreatePost("", "Content")
        
        assert.Error(t, err)
        assert.Nil(t, post)
    })
    
    t.Run("duplicate title", func(t *testing.T) {
        mockRepo := new(MockPostRepository)
        service := NewPostService(mockRepo)
        
        mockRepo.On("ExistsByTitle", "Test Post").Return(true, nil)
        
        post, err := service.CreatePost("Test Post", "Content")
        
        assert.Error(t, err)
        assert.Nil(t, post)
        mockRepo.AssertExpectations(t)
    })
}
```

---

## 总结

良好的测试实践是构建可靠软件的基础：

### 关键要点

- ✅ 使用表驱动测试处理多个场景
- ✅ 使用 t.Helper() 标记辅助函数
- ✅ 测试应该独立、快速、可重复
- ✅ 使用接口和 mock 隔离依赖
- ✅ 使用测试夹具管理测试数据
- ✅ 关注测试覆盖率，但不要追求 100%
- ✅ 测试公共接口，不测试实现细节
- ✅ 使用构建标签分离单元测试和集成测试

### 下一步学习

- **Lesson 07**: 性能优化技巧 - 学习如何优化代码性能
- **Lesson 08**: 安全实践 - 学习如何编写安全的代码
