# Lesson 03: Go Web 框架最佳实践

## 概述

本课程介绍如何使用 Gin 框架构建 RESTful API，包括路由设计、中间件实现、请求验证和错误处理。通过博客系统的实际案例，学习构建高性能、可扩展的 Web 应用。

## 学习目标

- 掌握 Gin 框架的核心概念
- 学习 RESTful API 设计原则
- 理解中间件模式和实现技巧
- 掌握请求验证和响应格式化

## 1. Gin 框架基础

### 1.1 为什么选择 Gin？

**Gin 的优势**：
- ⚡ **高性能**：使用 HttpRouter，速度极快
- 🎯 **中间件生态**：丰富的中间件支持
- 📝 **JSON 验证**：内置请求验证
- 🛠️ **易于使用**：简洁的 API 设计
- 📚 **文档完善**：社区活跃，资料丰富

**性能对比**（requests per second）：
```
Gin:      300,000+
Echo:     280,000+
FastHTTP: 250,000+
Gorilla Mux: 180,000+
```

### 1.2 基本设置

**项目结构**：
```
internal/
├── handlers/        # HTTP 处理器
│   ├── post.go
│   ├── user.go
│   └── middleware.go
├── service/         # 业务逻辑层
├── models/          # 数据模型
└── config/          # 配置
```

**初始化 Gin**：
```go
package main

import (
    "github.com/gin-gonic/gin"
)

func main() {
    // 1. 创建 Gin 引擎
    r := gin.Default()  // 包含 Logger 和 Recovery 中间件
    
    // 2. 定义路由
    r.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{
            "message": "pong",
        })
    })
    
    // 3. 启动服务器
    r.Run(":8080")  // 默认监听 0.0.0.0:8080
}
```

## 2. RESTful API 设计

### 2.1 REST 原则

**资源命名规范**：
```go
// ✅ 好的设计：使用名词复数
GET    /api/v1/posts          # 获取文章列表
GET    /api/v1/posts/:id      # 获取单个文章
POST   /api/v1/posts          # 创建文章
PUT    /api/v1/posts/:id      # 更新文章
DELETE /api/v1/posts/:id      # 删除文章

// ❌ 不好的设计：使用动词
GET    /api/v1/getPosts
POST   /api/v1/createPost
```

**HTTP 方法语义**：
| 方法 | 语义 | 幂等性 |
|------|------|--------|
| GET | 获取资源 | ✅ 是 |
| POST | 创建资源 | ❌ 否 |
| PUT | 完整更新 | ✅ 是 |
| PATCH | 部分更新 | ❌ 否 |
| DELETE | 删除资源 | ✅ 是 |

### 2.2 路由组织

**模块化路由**：
```go
package handlers

import (
    "github.com/gin-gonic/gin"
    "github.com/yourusername/ppmtest/internal/service"
)

// PostHandler 文章处理器
type PostHandler struct {
    postService service.PostService
}

// NewPostHandler 创建处理器
func NewPostHandler(postService service.PostService) *PostHandler {
    return &PostHandler{postService: postService}
}

// RegisterRoutes 注册路由
func (h *PostHandler) RegisterRoutes(r *gin.Engine) {
    v1 := r.Group("/api/v1")
    {
        posts := v1.Group("/posts")
        {
            posts.GET("", h.ListPosts)           // 获取列表
            posts.GET("/:id", h.GetPost)         // 获取详情
            posts.POST("", h.CreatePost)         // 创建
            posts.PUT("/:id", h.UpdatePost)      // 更新
            posts.DELETE("/:id", h.DeletePost)   // 删除
            
            // 子资源路由
            posts.GET("/:id/comments", h.ListPostComments)
            posts.POST("/:id/comments", h.CreateComment)
        }
    }
}
```

**使用路由组**：
```go
// 1. API 版本组
v1 := r.Group("/api/v1")
v2 := r.Group("/api/v2")

// 2. 认证路由组
auth := v1.Group("")
auth.Use(AuthMiddleware())
{
    auth.GET("/profile", GetProfile)
    auth.PUT("/profile", UpdateProfile)
}

// 3. 公开路由组
public := v1.Group("/public")
{
    public.GET("/posts", ListPosts)
    public.GET("/posts/:id", GetPost)
}
```

## 3. 请求处理

### 3.1 路径参数

```go
// 获取路径参数
func GetPost(c *gin.Context) {
    id := c.Param("id")  // 获取 :id 参数
    
    // 转换类型
    postID, err := strconv.ParseUint(id, 10, 64)
    if err != nil {
        c.JSON(400, gin.H{"error": "invalid post id"})
        return
    }
    
    // 调用服务
    post, err := h.postService.GetByID(c.Request.Context(), uint(postID))
    if err != nil {
        c.JSON(404, gin.H{"error": "post not found"})
        return
    }
    
    c.JSON(200, post)
}
```

### 3.2 查询参数

```go
func ListPosts(c *gin.Context) {
    // 获取查询参数
    page := c.DefaultQuery("page", "1")
    pageSize := c.DefaultQuery("page_size", "10")
    status := c.Query("status")  // 可选参数
    
    // 转换和验证
    pageNum, _ := strconv.Atoi(page)
    sizeNum, _ := strconv.Atoi(pageSize)
    
    if pageNum < 1 {
        pageNum = 1
    }
    if sizeNum < 1 || sizeNum > 100 {
        sizeNum = 10
    }
    
    // 计算偏移量
    offset := (pageNum - 1) * sizeNum
    
    // 调用服务
    posts, total, err := h.postService.List(c.Request.Context(), sizeNum, offset)
    if err != nil {
        c.JSON(500, gin.H{"error": "failed to list posts"})
        return
    }
    
    // 返回分页响应
    c.JSON(200, gin.H{
        "data": posts,
        "pagination": gin.H{
            "page":       pageNum,
            "page_size":  sizeNum,
            "total":      total,
            "total_pages": (total + int64(sizeNum) - 1) / int64(sizeNum),
        },
    })
}
```

### 3.3 请求体验证

**定义请求结构**：
```go
package dto

// CreatePostRequest 创建文章请求
type CreatePostRequest struct {
    Title   string `json:"title" binding:"required,min=3,max=255"`
    Slug    string `json:"slug" binding:"required,min=3,max=255"`
    Content string `json:"content" binding:"required"`
    Summary string `json:"summary"`
    Status  string `json:"status" binding:"omitempty,oneof=draft published"`
}

// UpdatePostRequest 更新文章请求
type UpdatePostRequest struct {
    Title   string `json:"title" binding:"omitempty,min=3,max=255"`
    Content string `json:"content"`
    Summary string `json:"summary"`
    Status  string `json:"status" binding:"omitempty,oneof=draft published archived"`
}
```

**使用验证**：
```go
func CreatePost(c *gin.Context) {
    var req dto.CreatePostRequest
    
    // 绑定和验证
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{
            "error": "invalid request",
            "details": err.Error(),
        })
        return
    }
    
    // 创建模型
    post := &models.Post{
        Title:   req.Title,
        Slug:    req.Slug,
        Content: req.Content,
        Summary: req.Summary,
        Status:  req.Status,
        // 设置默认值
    }
    if post.Status == "" {
        post.Status = "draft"
    }
    
    // 调用服务
    if err := h.postService.Create(c.Request.Context(), post); err != nil {
        c.JSON(500, gin.H{"error": "failed to create post"})
        return
    }
    
    c.JSON(201, post)
}
```

## 4. 响应处理

### 4.1 统一响应格式

**定义响应结构**：
```go
package dto

// Response 统一响应结构
type Response struct {
    Success bool        `json:"success"`
    Data    interface{} `json:"data,omitempty"`
    Error   *ErrorInfo  `json:"error,omitempty"`
}

// ErrorInfo 错误信息
type ErrorInfo struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Details string `json:"details,omitempty"`
}

// PaginationResponse 分页响应
type PaginationResponse struct {
    Data       interface{} `json:"data"`
    Pagination Pagination  `json:"pagination"`
}

// Pagination 分页信息
type Pagination struct {
    Page       int   `json:"page"`
    PageSize   int   `json:"page_size"`
    Total      int64 `json:"total"`
    TotalPages int   `json:"total_pages"`
}

// 辅助函数
func Success(data interface{}) *Response {
    return &Response{
        Success: true,
        Data:    data,
    }
}

func Error(code, message string) *Response {
    return &Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    code,
            Message: message,
        },
    }
}
```

### 4.2 使用统一响应

```go
func GetPost(c *gin.Context) {
    id := c.Param("id")
    postID, _ := strconv.ParseUint(id, 10, 64)
    
    post, err := h.postService.GetByID(c.Request.Context(), uint(postID))
    if err != nil {
        c.JSON(404, dto.Error("POST_NOT_FOUND", "Post not found"))
        return
    }
    
    c.JSON(200, dto.Success(post))
}
```

## 5. 中间件实现

### 5.1 日志中间件

```go
func LoggerMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 1. 记录开始时间
        start := time.Now()
        
        // 2. 生成请求 ID
        requestID := uuid.New().String()
        c.Set("request_id", requestID)
        
        // 3. 记录请求信息
        log.Info("Request started",
            "request_id", requestID,
            "method", c.Request.Method,
            "path", c.Request.URL.Path,
            "ip", c.ClientIP(),
        )
        
        // 4. 处理请求
        c.Next()
        
        // 5. 记录响应信息
        duration := time.Since(start)
        log.Info("Request completed",
            "request_id", requestID,
            "status", c.Writer.Status(),
            "duration", duration,
        )
    }
}
```

### 5.2 认证中间件

```go
func AuthMiddleware(jwtSecret string) gin.HandlerFunc {
    return func(c *gin.Context) {
        // 1. 获取 Token
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(401, dto.Error("UNAUTHORIZED", "Missing authorization token"))
            c.Abort()
            return
        }
        
        // 2. 验证 Token
        if strings.HasPrefix(token, "Bearer ") {
            token = token[7:]
        }
        
        claims, err := validateJWT(token, jwtSecret)
        if err != nil {
            c.JSON(401, dto.Error("INVALID_TOKEN", "Invalid token"))
            c.Abort()
            return
        }
        
        // 3. 设置用户信息到上下文
        c.Set("user_id", claims.UserID)
        c.Set("user_role", claims.Role)
        
        c.Next()
    }
}

// JWT Claims 结构
type Claims struct {
    UserID uint   `json:"user_id"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

func validateJWT(tokenString, secret string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        return []byte(secret), nil
    })
    
    if err != nil {
        return nil, err
    }
    
    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }
    
    return nil, errors.New("invalid token")
}
```

### 5.3 CORS 中间件

```go
func CORSMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Authorization")
        c.Header("Access-Control-Max-Age", "86400")
        
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }
        
        c.Next()
    }
}
```

### 5.4 错误恢复中间件

```go
func RecoveryMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        defer func() {
            if err := recover(); err != nil {
                // 记录 panic
                log.Error("Panic recovered",
                    "error", err,
                    "stack", debug.Stack(),
                )
                
                // 返回友好错误
                c.JSON(500, dto.Error("INTERNAL_ERROR", "Internal server error"))
                c.Abort()
            }
        }()
        
        c.Next()
    }
}
```

### 5.5 速率限制中间件

```go
func RateLimitMiddleware(requestsPerMinute int) gin.HandlerFunc {
    limiter := rate.NewLimiter(rate.Every(time.Minute/time.Duration(requestsPerMinute)), requestsPerMinute)
    
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.JSON(429, dto.Error("RATE_LIMIT_EXCEEDED", "Too many requests"))
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

## 6. 错误处理

### 6.1 自定义错误处理

```go
func ErrorHandlerMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        // 检查是否有错误
        if len(c.Errors) > 0 {
            err := c.Errors.Last()
            
            // 根据错误类型返回不同的响应
            switch e := err.Err.(type) {
            case *errors.BusinessError:
                c.JSON(getHTTPStatus(e.Code), dto.Error(e.Code, e.Message))
            default:
                c.JSON(500, dto.Error("INTERNAL_ERROR", "Internal server error"))
            }
        }
    }
}

func getHTTPStatus(code string) int {
    statusMap := map[string]int{
        "POST_NOT_FOUND":    404,
        "INVALID_INPUT":     400,
        "UNAUTHORIZED":      401,
        "FORBIDDEN":         403,
        "RATE_LIMIT_EXCEEDED": 429,
    }
    
    if status, ok := statusMap[code]; ok {
        return status
    }
    return 500
}
```

## 7. 文件上传

### 7.1 单文件上传

```go
func UploadImage(c *gin.Context) {
    // 1. 获取文件
    file, err := c.FormFile("image")
    if err != nil {
        c.JSON(400, dto.Error("INVALID_FILE", "No file uploaded"))
        return
    }
    
    // 2. 验证文件类型
    if !strings.HasPrefix(file.Header.Get("Content-Type"), "image/") {
        c.JSON(400, dto.Error("INVALID_FILE_TYPE", "Only images are allowed"))
        return
    }
    
    // 3. 验证文件大小（5MB）
    if file.Size > 5*1024*1024 {
        c.JSON(400, dto.Error("FILE_TOO_LARGE", "File size exceeds 5MB"))
        return
    }
    
    // 4. 生成唯一文件名
    ext := filepath.Ext(file.Filename)
    filename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
    
    // 5. 保存文件
    if err := c.SaveUploadedFile(file, fmt.Sprintf("./uploads/%s", filename)); err != nil {
        c.JSON(500, dto.Error("UPLOAD_FAILED", "Failed to save file"))
        return
    }
    
    c.JSON(200, dto.Success(gin.H{
        "filename": filename,
        "url":      fmt.Sprintf("/uploads/%s", filename),
    }))
}
```

## 8. 完整示例

### 8.1 main.go

```go
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/yourusername/ppmtest/internal/handlers"
    "github.com/yourusername/ppmtest/internal/container"
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

func main() {
    // 1. 初始化数据库
    dsn := "user:password@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True&loc=Local"
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        panic("Failed to connect to database")
    }
    
    // 2. 创建容器（依赖注入）
    appContainer := container.NewContainer(db)
    
    // 3. 创建 Gin 引擎
    r := gin.New()
    
    // 4. 全局中间件
    r.Use(handlers.RecoveryMiddleware())
    r.Use(handlers.CORSMiddleware())
    r.Use(handlers.LoggerMiddleware())
    
    // 5. 注册路由
    postHandler := handlers.NewPostHandler(appContainer.PostService)
    postHandler.RegisterRoutes(r)
    
    userHandler := handlers.NewUserHandler(appContainer.UserService)
    userHandler.RegisterRoutes(r)
    
    // 6. 启动服务器
    if err := r.Run(":8080"); err != nil {
        panic("Failed to start server")
    }
}
```

## 9. 最佳实践

### 9.1 配置管理

```go
func main() {
    // 开发模式：详细日志
    if os.Getenv("GIN_MODE") == "debug" {
        gin.SetMode(gin.DebugMode)
    } else {
        gin.SetMode(gin.ReleaseMode)
    }
    
    // 使用环境变量配置端口
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    r.Run(":" + port)
}
```

### 9.2 优雅关闭

```go
func main() {
    r := gin.Default()
    
    srv := &http.Server{
        Addr:    ":8080",
        Handler: r,
    }
    
    // 在 goroutine 中启动服务器
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server failed: %v", err)
        }
    }()
    
    // 等待中断信号
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    // 优雅关闭
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }
}
```

## 10. 测试

### 10.1 API 测试

```go
func TestGetPost(t *testing.T) {
    // 1. 设置测试路由
    r := gin.Default()
    mockService := new(MockPostService)
    handler := NewPostHandler(mockService)
    
    r.GET("/posts/:id", handler.GetPost)
    
    // 2. 创建测试请求
    req, _ := http.NewRequest("GET", "/posts/1", nil)
    w := httptest.NewRecorder()
    
    // 3. 执行请求
    r.ServeHTTP(w, req)
    
    // 4. 验证响应
    assert.Equal(t, 200, w.Code)
    assert.Contains(t, w.Body.String(), "title")
}
```

## 11. 实战练习

### 练习 1：实现文章搜索 API

```go
// 在 PostHandler 中添加
func (h *PostHandler) SearchPosts(c *gin.Context) {
    // TODO: 实现搜索功能
    // 1. 获取查询参数 keyword
    // 2. 调用 postService.Search()
    // 3. 返回搜索结果
}
```

### 练习 2：实现缓存中间件

```go
func CacheMiddleware(duration time.Duration) gin.HandlerFunc {
    // TODO: 实现缓存中间件
    // 1. 检查缓存
    // 2. 缓存命中则直接返回
    // 3. 缓存未命中则处理请求并缓存结果
}
```

## 12. 总结

### 核心要点

1. **RESTful 设计**：使用名词复数，正确的 HTTP 方法
2. **路由组织**：模块化路由，使用路由组
3. **请求验证**：使用 binding 标签验证输入
4. **统一响应**：标准化的响应格式
5. **中间件模式**：横切关注点的实现
6. **错误处理**：友好的错误信息和适当的 HTTP 状态码

### 性能优化

- 使用连接池
- 启用 gzip 压缩
- 实现缓存
- 数据库查询优化

### 安全考虑

- 输入验证和清理
- CSRF 防护
- 速率限制
- 安全头设置

### 下一步

- [ ] 学习中间件模式（Lesson 04）
- [ ] 实现完整的认证授权系统
- [ ] 添加 API 文档（Swagger）
- [ ] 性能测试和优化

### 相关资源

- [Gin 官方文档](https://gin-gonic.com/docs/)
- [RESTful API 设计指南](https://restfulapi.net/)
- [Go HTTP 最佳实践](https://go.dev/doc/effective_go#http)

---

**作者**: Go 博客系统项目组  
**更新日期**: 2025-12-28  
**难度**: ⭐⭐⭐☆☆（中级）  
**预计学习时间**: 4-5 小时