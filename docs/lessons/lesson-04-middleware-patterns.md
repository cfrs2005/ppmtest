# Lesson 04: 中间件模式

## 目录
- [什么是中间件](#什么是中间件)
- [中间件的工作原理](#中间件的工作原理)
- [Gin 中间件系统](#gin-中间件系统)
- [常用中间件实现](#常用中间件实现)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## 什么是中间件

中间件（Middleware）是位于 HTTP 请求处理流程中的拦截器，可以在请求到达最终处理器之前或之后执行特定逻辑。

### 中间件的作用

1. **请求预处理**
   - 身份认证和授权
   - 请求日志记录
   - 请求限流和防护

2. **响应后处理**
   - 响应头设置
   - 错误处理和恢复
   - 响应日志记录

3. **横切关注点**
   - CORS 处理
   - 请求追踪
   - 性能监控

### 中间件链

```
Request → Logger → Auth → CORS → Handler → CORS → Auth → Logger → Response
           ↑         ↑       ↑                ↓       ↓       ↓
         Before   Before  Before          After   After   After
```

---

## 中间件的工作原理

### 基本概念

中间件遵循洋葱模型（Onion Model）：

```go
func Middleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 1. 前置处理（Before）
        fmt.Println("Before handler")
        
        // 2. 调用下一个处理器
        c.Next()
        
        // 3. 后置处理（After）
        fmt.Println("After handler")
    }
}
```

### 执行流程

```go
// 伪代码展示执行顺序
func (c *Context) Next() {
    c.index++
    for c.index < len(c.handlers) {
        c.handlers[c.index](c)  // 执行当前中间件
        c.index++
    }
}
```

**示例执行顺序**：

```go
r := gin.Default()  // 包含 Logger 和 Recovery 中间件

r.Use(MiddlewareA())  // 全局中间件
r.Use(MiddlewareB())

r.GET("/ping", MiddlewareC(), func(c *gin.Context) {
    c.JSON(200, gin.H{"message": "pong"})
})

// 执行顺序：
// Logger → Recovery → MiddlewareA → MiddlewareB → MiddlewareC → Handler
//                                                               ↓
// MiddlewareC → MiddlewareB → MiddlewareA → Recovery → Logger
```

---

## Gin 中间件系统

### 中间件类型

#### 1. 全局中间件

```go
func SetupRouter() *gin.Engine {
    r := gin.Default()
    
    // 全局应用
    r.Use(middleware.CORS())
    r.Use(middleware.RequestID())
    r.Use(middleware.Logger())
    
    return r
}
```

#### 2. 路由组中间件

```go
// API 路由组，需要认证
apiGroup := r.Group("/api")
apiGroup.Use(middleware.Auth())
{
    apiGroup.GET("/posts", handlers.GetPosts)
    apiGroup.POST("/posts", handlers.CreatePost)
}

// 公开路由组，无需认证
publicGroup := r.Group("/public")
{
    publicGroup.GET("/posts/:id", handlers.GetPostByID)
}
```

#### 3. 单路由中间件

```go
r.GET("/admin", middleware.Auth(), middleware.AdminOnly(), handlers.AdminPage)
```

### 中间件配置

```go
// 带配置的中间件
func CORS(allowOrigins []string) gin.HandlerFunc {
    return func(c *gin.Context) {
        origin := c.Request.Header.Get("Origin")
        
        // 检查是否在允许列表中
        allowed := false
        for _, allow := range allowOrigins {
            if origin == allow {
                allowed = true
                break
            }
        }
        
        if allowed {
            c.Header("Access-Control-Allow-Origin", origin)
        }
        
        c.Next()
    }
}

// 使用
r.Use(middleware.CORS([]string{"https://example.com"}))
```

---

## 常用中间件实现

### 1. 请求日志中间件

```go
package middleware

import (
    "log"
    "time"
    
    "github.com/gin-gonic/gin"
)

func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        query := c.Request.URL.RawQuery
        
        // 处理请求
        c.Next()
        
        // 记录日志
        latency := time.Since(start)
        status := c.Writer.Status()
        method := c.Request.Method
        
        log.Printf("[%s] %s %s | Status: %d | Latency: %v",
            method,
            path,
            query,
            status,
            latency,
        )
    }
}
```

### 2. 错误恢复中间件

```go
package middleware

import (
    "log"
    "net/http"
    "runtime/debug"
    
    "github.com/gin-gonic/gin"
)

func Recovery() gin.HandlerFunc {
    return func(c *gin.Context) {
        defer func() {
            if err := recover(); err != nil {
                // 打印堆栈信息
                log.Printf("Panic recovered: %v\n%s", err, debug.Stack())
                
                // 返回 500 错误
                c.JSON(http.StatusInternalServerError, gin.H{
                    "error": "Internal server error",
                })
                
                c.Abort()
            }
        }()
        
        c.Next()
    }
}
```

### 3. CORS 中间件

```go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func CORS() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        c.Header("Access-Control-Max-Age", "86400")
        
        // 处理 OPTIONS 预检请求
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(204)
            return
        }
        
        c.Next()
    }
}
```

### 4. 请求 ID 中间件

```go
package middleware

import (
    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
)

func RequestID() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 从请求头获取或生成新的 Request ID
        requestID := c.GetHeader("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }
        
        // 设置到上下文
        c.Set("RequestID", requestID)
        
        // 设置到响应头
        c.Header("X-Request-ID", requestID)
        
        c.Next()
    }
}
```

### 5. 认证中间件（JWT）

```go
package middleware

import (
    "net/http"
    "strings"
    
    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v5"
)

type AuthMiddleware struct {
    jwtSecret []byte
}

func NewAuthMiddleware(secret string) *AuthMiddleware {
    return &AuthMiddleware{
        jwtSecret: []byte(secret),
    }
}

func (a *AuthMiddleware) Auth() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 获取 Authorization header
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            c.JSON(http.StatusUnauthorized, gin.H{
                "error": "Authorization header required",
            })
            c.Abort()
            return
        }
        
        // 解析 Bearer token
        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            c.JSON(http.StatusUnauthorized, gin.H{
                "error": "Invalid authorization format",
            })
            c.Abort()
            return
        }
        
        tokenString := parts[1]
        
        // 验证 JWT
        token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
            return a.jwtSecret, nil
        })
        
        if err != nil || !token.Valid {
            c.JSON(http.StatusUnauthorized, gin.H{
                "error": "Invalid token",
            })
            c.Abort()
            return
        }
        
        // 提取 claims
        if claims, ok := token.Claims.(jwt.MapClaims); ok {
            c.Set("userID", claims["sub"])
            c.Set("username", claims["username"])
        }
        
        c.Next()
    }
}
```

### 6. 限流中间件

```go
package middleware

import (
    "net/http"
    "sync"
    "time"
    
    "github.com/gin-gonic/gin"
)

type RateLimiter struct {
    visitors map[string]*Visitor
    mu       sync.RWMutex
    rate     int           // 每分钟请求数
    duration time.Duration // 时间窗口
}

type Visitor struct {
    requests  []time.Time
    lastSeen  time.Time
}

func NewRateLimiter(rate int, duration time.Duration) *RateLimiter {
    rl := &RateLimiter{
        visitors: make(map[string]*Visitor),
        rate:     rate,
        duration: duration,
    }
    
    // 清理过期访客
    go rl.cleanupVisitors()
    
    return rl
}

func (rl *RateLimiter) Middleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        ip := c.ClientIP()
        
        rl.mu.Lock()
        visitor, exists := rl.visitors[ip]
        if !exists {
            visitor = &Visitor{
                requests:  []time.Time{},
                lastSeen:  time.Now(),
            }
            rl.visitors[ip] = visitor
        }
        
        // 清理过期请求
        cutoff := time.Now().Add(-rl.duration)
        validRequests := []time.Time{}
        for _, reqTime := range visitor.requests {
            if reqTime.After(cutoff) {
                validRequests = append(validRequests, reqTime)
            }
        }
        visitor.requests = validRequests
        visitor.lastSeen = time.Now()
        
        // 检查是否超过限制
        if len(visitor.requests) >= rl.rate {
            rl.mu.Unlock()
            c.JSON(http.StatusTooManyRequests, gin.H{
                "error": "Rate limit exceeded",
            })
            c.Abort()
            return
        }
        
        // 记录请求
        visitor.requests = append(visitor.requests, time.Now())
        rl.mu.Unlock()
        
        c.Next()
    }
}

func (rl *RateLimiter) cleanupVisitors() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        rl.mu.Lock()
        cutoff := time.Now().Add(-time.Hour)
        
        for ip, visitor := range rl.visitors {
            if visitor.lastSeen.Before(cutoff) {
                delete(rl.visitors, ip)
            }
        }
        rl.mu.Unlock()
    }
}
```

### 7. 响应时间监控中间件

```go
package middleware

import (
    "github.com/gin-gonic/gin"
    "time"
)

func ResponseTime() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        
        c.Next()
        
        duration := time.Since(start)
        
        // 设置响应头
        c.Header("X-Response-Time", duration.String())
        
        // 或记录到监控系统
        // metrics.RecordResponseTime(c.Request.URL.Path, duration)
    }
}
```

---

## 最佳实践

### 1. 中间件顺序很重要

```go
// 推荐的中间件顺序
r.Use(
    middleware.Recovery(),      // 1. 错误恢复（最外层）
    middleware.RequestID(),     // 2. 请求 ID（追踪）
    middleware.Logger(),        // 3. 日志记录
    middleware.CORS(),          // 4. CORS
    middleware.ResponseTime(),  // 5. 响应时间
)
```

**原因**：
- Recovery 应该在最外层，捕获所有 panic
- RequestID 应尽早设置，便于追踪
- Logger 需要记录完整的请求和响应
- CORS 需要处理 OPTIONS 预检请求

### 2. 避免中间件中的重复工作

```go
// ❌ 不好：每次都解析
func BadAuth() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        claims := parseJWT(token)  // 重复解析
        c.Set("claims", claims)
        c.Next()
    }
}

// ✅ 好：缓存解析结果
func GoodAuth() gin.HandlerFunc {
    return func(c *gin.Context) {
        if _, exists := c.Get("claims"); exists {
            c.Next()
            return
        }
        
        token := c.GetHeader("Authorization")
        claims := parseJWT(token)
        c.Set("claims", claims)
        c.Next()
    }
}
```

### 3. 使用 context 传递数据

```go
// ✅ 在中间件中设置数据
func Auth() gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := authenticate(c)
        c.Set("userID", userID)  // 使用 c.Set()
        c.Next()
    }
}

// ✅ 在 handler 中获取数据
func GetHandler(c *gin.Context) {
    userID, exists := c.Get("userID")
    if !exists {
        c.JSON(401, gin.H{"error": "unauthorized"})
        return
    }
    // 使用 userID
}
```

### 4. 合理使用 c.Abort()

```go
// Abort() 会停止后续中间件和 handler
func StrictAuth() gin.HandlerFunc {
    return func(c *gin.Context) {
        if !isAuthenticated(c) {
            c.JSON(401, gin.H{"error": "unauthorized"})
            c.Abort()  // 停止处理链
            return
        }
        c.Next()
    }
}

// 注意：Abort() 后的中间件不会执行，但已执行的 After 逻辑会执行
```

### 5. 中间件应该可配置

```go
// ✅ 带配置的中间件
func NewRateLimiter(rate int, duration time.Duration) gin.HandlerFunc {
    // 使用配置创建中间件
}

// ✅ 使用选项模式
type LoggerConfig struct {
    LogPath string
    SkipPaths []string
}

type LoggerOption func(*LoggerConfig)

func WithLogPath(path string) LoggerOption {
    return func(c *LoggerConfig) {
        c.LogPath = path
    }
}

func Logger(opts ...LoggerOption) gin.HandlerFunc {
    config := &LoggerConfig{
        LogPath: "/var/log/app.log",
        SkipPaths: []string{"/health"},
    }
    
    for _, opt := range opts {
        opt(config)
    }
    
    return func(c *gin.Context) {
        // 实现逻辑
        c.Next()
    }
}
```

---

## 注意事项

### 1. 避免 panic

中间件中必须处理所有可能的错误：

```go
func SafeMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("Middleware panic: %v", r)
            }
        }()
        
        // 中间件逻辑
    }
}
```

### 2. 不要阻塞请求

```go
// ❌ 不好：同步阻塞
func BadLogging() gin.HandlerFunc {
    return func(c *gin.Context) {
        logToDatabase(c)  // 可能很慢
        c.Next()
    }
}

// ✅ 好：异步非阻塞
func GoodLogging() gin.HandlerFunc {
    return func(c *gin.Context) {
        go func() {
            logToDatabase(c)
        }()
        c.Next()
    }
}
```

### 3. 注意内存泄漏

```go
// ❌ 不好：无限制增长
func BadRateLimiter() gin.HandlerFunc {
    visitors := make(map[string]*Visitor)  // 永远不清理
    
    return func(c *gin.Context) {
        ip := c.ClientIP()
        visitors[ip] = updateVisitor(visitors[ip])
        c.Next()
    }
}

// ✅ 好：定期清理
func GoodRateLimiter() gin.HandlerFunc {
    visitors := make(map[string]*Visitor)
    
    // 定期清理过期数据
    go cleanupExpiredVisitors(visitors)
    
    return func(c *gin.Context) {
        ip := c.ClientIP()
        visitors[ip] = updateVisitor(visitors[ip])
        c.Next()
    }
}
```

### 4. 中间件应该是幂等的

```go
// ✅ 幂等中间件：多次调用结果相同
func CORS() gin.HandlerFunc {
    return func(c *gin.Context) {
        if c.GetHeader("Access-Control-Allow-Origin") != "" {
            c.Next()  // 已设置，跳过
            return
        }
        
        c.Header("Access-Control-Allow-Origin", "*")
        c.Next()
    }
}
```

### 5. 注意上下文取消

```go
func TimeoutMiddleware(timeout time.Duration) gin.HandlerFunc {
    return func(c *gin.Context) {
        ctx, cancel := context.WithTimeout(c.Request.Context(), timeout)
        defer cancel()
        
        c.Request = c.Request.WithContext(ctx)
        
        finished := make(chan struct{})
        go func() {
            c.Next()
            close(finished)
        }()
        
        select {
        case <-finished:
            // 正常完成
        case <-ctx.Done():
            c.JSON(http.StatusRequestTimeout, gin.H{
                "error": "request timeout",
            })
            c.Abort()
        }
    }
}
```

---

## 实战案例：博客系统中间件栈

### 完整的中间件配置

```go
// cmd/server/main.go
package main

func main() {
    r := gin.Default()
    
    // 全局中间件
    r.Use(
        middleware.Recovery(),                // 错误恢复
        middleware.RequestID(),               // 请求追踪
        middleware.Logger(),                  // 日志记录
        middleware.CORS(),                    // CORS
        middleware.ResponseTime(),            // 响应时间
    )
    
    // 公开路由
    public := r.Group("/api/v1/public")
    {
        public.GET("/posts", handlers.GetPosts)
        public.GET("/posts/:id", handlers.GetPostByID)
    }
    
    // 需要 API Key 的路由
    api := r.Group("/api/v1")
    api.Use(middleware.APIKeyAuth())
    {
        api.GET("/posts/search", handlers.SearchPosts)
    }
    
    // 需要用户认证的路由
    auth := r.Group("/api/v1")
    auth.Use(middleware.Auth())
    {
        auth.POST("/posts", handlers.CreatePost)
        auth.PUT("/posts/:id", handlers.UpdatePost)
        auth.DELETE("/posts/:id", handlers.DeletePost)
    }
    
    // 需要管理员权限的路由
    admin := r.Group("/api/v1/admin")
    admin.Use(middleware.Auth(), middleware.AdminOnly())
    {
        admin.GET("/users", handlers.ListUsers)
        admin.PUT("/posts/:id/publish", handlers.PublishPost)
    }
    
    r.Run(":8080")
}
```

### 中间件目录结构

```
internal/
├── middleware/
│   ├── auth.go          # 认证中间件
│   ├── cors.go          # CORS 中间件
│   ├── logger.go        # 日志中间件
│   ├── recovery.go      # 恢复中间件
│   ├── ratelimit.go     # 限流中间件
│   └── response_time.go # 响应时间中间件
```

---

## 总结

中间件模式是 Go Web 开发中的核心概念，掌握中间件的使用可以：

1. **提高代码复用性**：通用逻辑提取为中间件
2. **增强可维护性**：关注点分离，职责单一
3. **提升系统安全性**：统一处理认证、授权、限流等
4. **便于监控调试**：统一日志、追踪、性能监控

### 关键要点

- ✅ 理解中间件的洋葱模型执行顺序
- ✅ 合理安排中间件的优先级
- ✅ 中间件应该是轻量级、非阻塞的
- ✅ 使用 context 传递数据，不要滥用全局变量
- ✅ 注意处理错误和 panic，避免系统崩溃
- ✅ 定期清理中间件中的缓存数据，避免内存泄漏

### 下一步学习

- **Lesson 05**: 错误处理策略 - 学习如何在中间件和应用中统一处理错误
- **Lesson 06**: 测试最佳实践 - 学习如何测试中间件和 HTTP 处理器
