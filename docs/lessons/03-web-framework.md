# Lesson 03: Go Web 框架最佳实践

## 📖 概念解释

### 1. 表现层的职责

表现层（Presentation Layer）是应用的入口点，负责：
- 处理 HTTP 请求和响应
- 请求验证和数据绑定
- 路由和 URL 管理
- 中间件处理（认证、日志、CORS 等）
- 错误响应格式化

### 2. Gin 框架简介

Gin 是 Go 语言最流行的 Web 框架之一，特点：
- **高性能**：使用 HttpRouter 路由引擎
- **中间件支持**：类似 Express.js 的中间件机制
- **JSON 验证**：内置 JSON 绑定和验证
- **路由分组**：支持路由组织和版本管理

## 💡 最佳实践

### 1. Handler 设计

```go
type UserHandler struct {
    userService service.UserService
}

func NewUserHandler(userService service.UserService) *UserHandler {
    return &UserHandler{
        userService: userService,
    }
}
```

**Handler 设计原则**：
- **薄层**：Handler 应该很薄，只处理 HTTP 相关逻辑
- **依赖注入**：通过构造函数注入 Service
- **无状态**：Handler 不应该维护状态
- **错误处理**：将业务错误转换为 HTTP 状态码

### 2. 请求验证

```go
type RegisterRequest struct {
    Username string `json:"username" binding:"required"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=6"`
}

func (h *UserHandler) Register(c *gin.Context) {
    var req RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    user := &models.User{
        Username: req.Username,
        Email:    req.Email,
        Password: req.Password,
    }
    
    if err := h.userService.Register(user); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(http.StatusCreated, user)
}
```

**验证标签说明**：
- `required`: 必填字段
- `email`: 邮箱格式验证
- `min=6`: 最小长度验证
- `max=100`: 最大长度验证

### 3. 分页处理

```go
func (h *PostHandler) ListPosts(c *gin.Context) {
    page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
    pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "10"))
    
    if page < 1 {
        page = 1
    }
    if pageSize < 1 || pageSize > 100 {
        pageSize = 10
    }
    
    posts, total, err := h.postService.ListPosts(page, pageSize, "published")
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(http.StatusOK, gin.H{
        "data": posts,
        "pagination": gin.H{
            "page":        page,
            "page_size":   pageSize,
            "total":       total,
            "total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
        },
    })
}
```

**分页最佳实践**：
- 设置合理的默认值
- 限制最大页面大小（防止过大的请求）
- 返回总页数和总记录数
- 计算偏移量：`offset = (page - 1) * pageSize`

### 4. 中间件实现

```go
func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        
        c.Next()
        
        latency := time.Since(start)
        status := c.Writer.Status()
        
        log.Printf("[GIN] %s | %3d | %13v | %s",
            time.Now().Format("2006/01/02 - 15:04:05"),
            status,
            latency,
            path,
        )
    }
}
```

**中间件类型**：
- **日志中间件**：记录请求信息
- **恢复中间件**：捕获 panic
- **CORS 中间件**：跨域资源共享
- **认证中间件**：验证用户身份
- **限流中间件**：防止 API 滥用

### 5. 路由分组

```go
func Setup(userService service.UserService, postService service.PostService) *gin.Engine {
    r := gin.New()
    
    r.Use(middleware.Logger())
    r.Use(middleware.Recovery())
    r.Use(middleware.CORS())
    
    api := r.Group("/api/v1")
    {
        auth := api.Group("/auth")
        {
            auth.POST("/register", userHandler.Register)
            auth.POST("/login", userHandler.Login)
        }
        
        posts := api.Group("/posts")
        {
            posts.GET("", postHandler.ListPosts)
            posts.POST("", postHandler.CreatePost)
            posts.GET("/:id", postHandler.GetPost)
        }
    }
    
    return r
}
```

**路由分组优势**：
- **版本管理**：`/api/v1`、`/api/v2`
- **功能组织**：按功能模块分组
- **中间件应用**：为特定路由组添加中间件
- **URL 清晰**：结构化的 URL 设计

### 6. 优雅关闭

```go
srv := &http.Server{
    Addr:         ":" + cfg.Server.Port,
    Handler:      r,
    ReadTimeout:  10 * time.Second,
    WriteTimeout: 10 * time.Second,
}

go func() {
    if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
        log.Fatalf("Server failed to start: %v", err)
    }
}()

quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

log.Println("Shutting down server...")

ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

if err := srv.Shutdown(ctx); err != nil {
    log.Printf("Server forced to shutdown: %v", err)
}
```

**优雅关闭要点**：
- 捕获系统信号（SIGINT、SIGTERM）
- 设置关闭超时时间
- 等待现有请求完成
- 释放资源（数据库连接等）

## ⚠️ 常见陷阱

### 1. Handler 中包含业务逻辑

**问题代码**：
```go
func (h *UserHandler) Register(c *gin.Context) {
    var req RegisterRequest
    c.ShouldBindJSON(&req)
    
    if req.Password == req.Username {
        c.JSON(400, gin.H{"error": "password cannot be username"})
        return
    }
    
    user := &models.User{...}
    h.userService.Register(user)
}
```

**问题**：Handler 中不应该有业务验证

**解决方案**：
```go
func (h *UserHandler) Register(c *gin.Context) {
    var req RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    user := &models.User{...}
    if err := h.userService.Register(user); err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(201, user)
}
```

### 2. 忽略错误返回

**问题代码**：
```go
func (h *PostHandler) GetPost(c *gin.Context) {
    id, _ := strconv.ParseUint(c.Param("id"), 10, 32)
    post, _ := h.postService.GetPostByID(uint(id))
    c.JSON(200, post)
}
```

**解决方案**：
```go
func (h *PostHandler) GetPost(c *gin.Context) {
    id, err := strconv.ParseUint(c.Param("id"), 10, 32)
    if err != nil {
        c.JSON(400, gin.H{"error": "invalid post id"})
        return
    }
    
    post, err := h.postService.GetPostByID(uint(id))
    if err != nil {
        c.JSON(404, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(200, post)
}
```

### 3. 直接返回内部错误

**问题代码**：
```go
if err := h.userService.Register(user); err != nil {
    c.JSON(500, gin.H{"error": err.Error()})
}
```

**问题**：可能暴露敏感信息

**解决方案 - 错误处理层**：
```go
func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        for _, err := range c.Errors {
            switch e := err.Err.(type) {
            case *BusinessError:
                c.JSON(e.StatusCode, gin.H{"error": e.Message})
            default:
                c.JSON(500, gin.H{"error": "internal server error"})
            }
        }
    }
}
```

### 4. 没有设置超时

**问题**：请求可能永远挂起

**解决方案**：
```go
srv := &http.Server{
    Addr:         ":8080",
    Handler:      r,
    ReadTimeout:  10 * time.Second,
    WriteTimeout: 10 * time.Second,
    IdleTimeout:  60 * time.Second,
}
```

## 🔧 实战示例

### 完整的 Handler 实现

参考 `internal/handlers/user_handler.go` 的实现：

1. **结构体定义**：包含所需的 Service
2. **构造函数**：创建 Handler 实例
3. **请求处理方法**：每个方法处理一个端点
4. **错误处理**：统一错误响应格式
5. **数据绑定**：使用 Gin 的 binding

### 健康检查端点

```go
r.GET("/health", func(c *gin.Context) {
    c.JSON(200, gin.H{
        "status": "ok",
        "timestamp": time.Now().Unix(),
    })
})
```

### 路由参数处理

```go
posts.GET("/:id", postHandler.GetPost)

func (h *PostHandler) GetPost(c *gin.Context) {
    id := c.Param("id")
    // 使用 id 参数
}
```

### 查询参数处理

```go
posts.GET("", postHandler.ListPosts)

func (h *PostHandler) ListPosts(c *gin.Context) {
    page := c.DefaultQuery("page", "1")
    pageSize := c.DefaultQuery("page_size", "10")
    status := c.Query("status")
    // 使用查询参数
}
```

## ✅ 练习任务

### 任务 1：实现 JWT 认证中间件

```go
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "unauthorized"})
            return
        }
        
        claims, err := validateToken(token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }
        
        c.Set("user_id", claims.UserID)
        c.Set("role", claims.Role)
        c.Next()
    }
}
```

### 任务 2：实现限流中间件

```go
func RateLimit(requests int, window time.Duration) gin.HandlerFunc {
    limiter := rate.NewLimiter(rate.Every(window/time.Duration(requests)), requests)
    
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.AbortWithStatusJSON(429, gin.H{"error": "too many requests"})
            return
        }
        c.Next()
    }
}
```

### 任务 3：实现请求日志中间件

```go
func RequestLogger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        
        c.Next()
        
        duration := time.Since(start)
        log.Printf(
            "[%s] %s %s %d %v",
            time.Now().Format(time.RFC3339),
            c.Request.Method,
            c.Request.URL.Path,
            c.Writer.Status(),
            duration,
        )
    }
}
```

### 任务 4：实现 API 版本控制

```go
v1 := r.Group("/api/v1")
v1.Use(V1Middleware())
{
    v1.GET("/posts", postHandler.ListPosts)
}

v2 := r.Group("/api/v2")
v2.Use(V2Middleware())
{
    v2.GET("/posts", postHandlerV2.ListPosts)
}
```

## 📚 延伸阅读

- [Gin 官方文档](https://gin-gonic.com/docs/)
- [RESTful API 设计指南](https://restfulapi.net/)
- [HTTP 状态码完整列表](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status)
- [Go HTTP 服务器最佳实践](https://github.com/golang/go/wiki/HttpServer)

## 🎯 总结

本课程学习了：
- ✅ Gin 框架的使用
- ✅ Handler 设计原则
- ✅ 请求验证和数据绑定
- ✅ 中间件的实现
- ✅ 路由分组和版本管理
- ✅ 优雅关闭实现
- ✅ 错误处理最佳实践

下一步：学习并发编程和 GLM AI 集成（Lesson 04）