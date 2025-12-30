# Lesson 05: 错误处理策略

## 目录
- [Go 错误处理基础](#go-错误处理基础)
- [自定义错误类型](#自定义错误类型)
- [HTTP 错误处理](#http-错误处理)
- [错误包装和链式追踪](#错误包装和链式追踪)
- [统一错误处理模式](#统一错误处理模式)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## Go 错误处理基础

### error 接口

Go 的错误处理基于简单的接口：

```go
type error interface {
    Error() string
}
```

### 基本错误处理

```go
// ✅ 立即处理错误
file, err := os.Open("file.txt")
if err != nil {
    log.Printf("Failed to open file: %v", err)
    return
}
defer file.Close()
```

### 创建错误

```go
// 1. 使用 errors.New
err1 := errors.New("something went wrong")

// 2. 使用 fmt.Errorf
err2 := fmt.Errorf("invalid value: %d", value)

// 3. 使用 sentinel errors
var ErrNotFound = errors.New("not found")

// 4. 使用自定义错误类型
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed on field %s: %s", e.Field, e.Message)
}
```

---

## 自定义错误类型

### 1. 领域特定错误

```go
package errors

// 应用错误类型
type AppError struct {
    Code       int
    Message    string
    Underlying error
    StackTrace string
}

func (e *AppError) Error() string {
    if e.Underlying != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Underlying)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Underlying
}

// 创建错误的辅助函数
func NewAppError(code int, message string, underlying error) *AppError {
    return &AppError{
        Code:       code,
        Message:    message,
        Underlying: underlying,
    }
}

// 常用错误构造函数
func NotFound(what string) *AppError {
    return &AppError{
        Code:    404,
        Message: fmt.Sprintf("%s not found", what),
    }
}

func ValidationError(field, message string) *AppError {
    return &AppError{
        Code:    400,
        Message: fmt.Sprintf("validation failed: %s - %s", field, message),
    }
}

func InternalError(underlying error) *AppError {
    return &AppError{
        Code:       500,
        Message:    "internal server error",
        Underlying: underlying,
    }
}
```

### 2. 验证错误

```go
package validation

import (
    "fmt"
    "strings"
)

type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

type ValidationErrors []ValidationError

func (ve ValidationErrors) Error() string {
    var msgs []string
    for _, err := range ve {
        msgs = append(msgs, err.Error())
    }
    return strings.Join(msgs, "; ")
}

func (ve ValidationErrors) HasErrors() bool {
    return len(ve) > 0
}

// 验证器
type Validator struct {
    errors ValidationErrors
}

func NewValidator() *Validator {
    return &Validator{
        errors: make(ValidationErrors, 0),
    }
}

func (v *Validator) Required(field, value string) *Validator {
    if value == "" {
        v.errors = append(v.errors, ValidationError{
            Field:   field,
            Message: "is required",
        })
    }
    return v
}

func (v *Validator) MinLength(field, value string, min int) *Validator {
    if len(value) < min {
        v.errors = append(v.errors, ValidationError{
            Field:   field,
            Message: fmt.Sprintf("must be at least %d characters", min),
        })
    }
    return v
}

func (v *Validator) Email(field, value string) *Validator {
    if !isValidEmail(value) {
        v.errors = append(v.errors, ValidationError{
            Field:   field,
            Message: "must be a valid email",
        })
    }
    return v
}

func (v *Validator) Error() error {
    if v.errors.HasErrors() {
        return v.errors
    }
    return nil
}
```

### 3. 使用自定义错误

```go
// 在 service 中使用
func (s *PostService) CreatePost(req *CreatePostRequest) (*Post, error) {
    // 验证输入
    validator := validation.NewValidator()
    validator.
        Required("title", req.Title).
        MinLength("title", req.Title, 3).
        Required("content", req.Content).
        MinLength("content", req.Content, 10)
    
    if err := validator.Error(); err != nil {
        return nil, errors.ValidationError("input", err.Error())
    }
    
    // 检查重复
    exists, err := s.repo.ExistsByTitle(req.Title)
    if err != nil {
        return nil, errors.InternalError(err)
    }
    if exists {
        return nil, errors.ValidationError("title", "already exists")
    }
    
    // 创建文章
    post := &Post{
        Title:   req.Title,
        Content: req.Content,
    }
    
    if err := s.repo.Create(post); err != nil {
        return nil, errors.InternalError(err)
    }
    
    return post, nil
}
```

---

## HTTP 错误处理

### 1. 错误响应结构

```go
package response

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

// 标准错误响应
type ErrorResponse struct {
    Error   string `json:"error"`
    Code    int    `json:"code,omitempty"`
    Details string `json:"details,omitempty"`
    Path    string `json:"path,omitempty"`
}

// 验证错误响应
type ValidationErrorResponse struct {
    Error  string              `json:"error"`
    Fields map[string]string   `json:"fields,omitempty"`
}

// 发送错误响应
func Error(c *gin.Context, code int, message string) {
    c.JSON(code, ErrorResponse{
        Error: message,
        Code:  code,
        Path:  c.Request.URL.Path,
    })
}

func ErrorWithDetails(c *gin.Context, code int, message, details string) {
    c.JSON(code, ErrorResponse{
        Error:   message,
        Code:    code,
        Details: details,
        Path:    c.Request.URL.Path,
    })
}

func ValidationError(c *gin.Context, fields map[string]string) {
    c.JSON(http.StatusBadRequest, ValidationErrorResponse{
        Error:  "validation failed",
        Fields: fields,
    })
}
```

### 2. 错误处理中间件

```go
package middleware

import (
    "log"
    "net/http"
    
    "github.com/gin-gonic/gin"
)

func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        // 检查是否有错误
        if len(c.Errors) > 0 {
            err := c.Errors.Last()
            
            // 处理不同类型的错误
            switch e := err.Err.(type) {
            case *errors.AppError:
                handleAppError(c, e)
            case validation.ValidationErrors:
                handleValidationError(c, e)
            default:
                handleGenericError(c, err.Err)
            }
        }
    }
}

func handleAppError(c *gin.Context, err *errors.AppError) {
    // 根据 Code 映射到 HTTP 状态码
    statusCode := http.StatusInternalServerError
    switch err.Code {
    case 400:
        statusCode = http.StatusBadRequest
    case 404:
        statusCode = http.StatusNotFound
    case 409:
        statusCode = http.StatusConflict
    }
    
    response.ErrorWithDetails(c, statusCode, err.Message, getDetails(err))
}

func handleValidationError(c *gin.Context, errs validation.ValidationErrors) {
    fields := make(map[string]string)
    for _, err := range errs {
        fields[err.Field] = err.Message
    }
    response.ValidationError(c, fields)
}

func handleGenericError(c *gin.Context, err error) {
    log.Printf("Unhandled error: %v", err)
    response.Error(c, http.StatusInternalServerError, "internal server error")
}

func getDetails(err *errors.AppError) string {
    if err.Underlying != nil {
        return err.Underlying.Error()
    }
    return ""
}
```

### 3. 在 Handler 中使用

```go
package handlers

func (h *PostHandler) CreatePost(c *gin.Context) {
    var req CreatePostRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "invalid request body")
        return
    }
    
    post, err := h.service.CreatePost(&req)
    if err != nil {
        // 错误会通过中间件处理
        c.Error(err)
        return
    }
    
    c.JSON(http.StatusCreated, post)
}
```

---

## 错误包装和链式追踪

### 1. 错误包装（Go 1.13+）

```go
// 使用 %w 包装错误，保留原始错误
if err := db.Query(); err != nil {
    return fmt.Errorf("failed to query posts: %w", err)
}

// 使用 Unwrap 解包错误
err := doSomething()
if wrappedErr := errors.Unwrap(err); wrappedErr != nil {
    fmt.Printf("Original error: %v\n", wrappedErr)
}
```

### 2. 错误链追踪

```go
package service

func (s *PostService) GetPost(id int64) (*Post, error) {
    post, err := s.repo.FindByID(id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, fmt.Errorf("post %d not found: %w", id, err)
        }
        return nil, fmt.Errorf("failed to get post %d: %w", id, err)
    }
    
    return post, nil
}

func (s *PostService) PublishPost(id int64) error {
    post, err := s.GetPost(id)
    if err != nil {
        return fmt.Errorf("failed to get post for publishing: %w", err)
    }
    
    post.Status = "published"
    if err := s.repo.Update(post); err != nil {
        return fmt.Errorf("failed to update post status: %w", err)
    }
    
    return nil
}
```

### 3. 错误判断

```go
// 创建可比较的错误
var ErrPostNotFound = errors.New("post not found")

func (r *PostRepository) FindByID(id int64) (*Post, error) {
    var post Post
    err := r.db.Where("id = ?", id).First(&post).Error
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, fmt.Errorf("%w: %d", ErrPostNotFound, id)
        }
        return nil, err
    }
    return &post, nil
}

// 在上层判断
func (s *PostService) GetPost(id int64) (*Post, error) {
    post, err := s.repo.FindByID(id)
    if err != nil {
        if errors.Is(err, ErrPostNotFound) {
            return nil, errors.NotFound("post")
        }
        return nil, err
    }
    return post, nil
}
```

### 4. 自定义错误的 Is 和 As

```go
type NotFoundError struct {
    Resource string
    ID       int64
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s %d not found", e.Resource, e.ID)
}

// 实现 Is 方法
func (e *NotFoundError) Is(target error) bool {
    _, ok := target.(*NotFoundError)
    return ok
}

// 使用
var errNotFound *NotFoundError
if errors.As(err, &errNotFound) {
    fmt.Printf("Resource: %s, ID: %d\n", errNotFound.Resource, errNotFound.ID)
}
```

---

## 统一错误处理模式

### 1. 错误处理层架构

```
┌─────────────────────────────────────────────────┐
│                    Handler                      │
│  (接收 HTTP 请求，解析参数，调用 Service)        │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│                   Service                       │
│  (业务逻辑，错误包装，返回领域错误)              │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│                Repository                       │
│  (数据访问，数据库错误，返回底层错误)            │
└─────────────────────────────────────────────────┘
```

### 2. 完整示例

```go
// repository/post.go
func (r *PostRepository) FindByID(id int64) (*Post, error) {
    var post Post
    err := r.db.Where("id = ?", id).First(&post).Error
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, ErrNotFound
        }
        return nil, err  // 返回原始数据库错误
    }
    return &post, nil
}

// service/post.go
func (s *PostService) GetPost(id int64) (*Post, error) {
    post, err := s.repo.FindByID(id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, fmt.Errorf("post %d: %w", id, ErrNotFound)
        }
        return nil, fmt.Errorf("failed to get post %d: %w", id, err)
    }
    
    // 检查权限
    if post.AuthorID != s.currentUserID && !post.IsPublished {
        return nil, ErrAccessDenied
    }
    
    return post, nil
}

// handler/post.go
func (h *PostHandler) GetPost(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        response.Error(c, http.StatusBadRequest, "invalid post id")
        return
    }
    
    post, err := h.service.GetPost(id)
    if err != nil {
        // 让中间件处理错误
        c.Error(err)
        return
    }
    
    c.JSON(http.StatusOK, post)
}

// middleware/error.go
func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        for _, err := range c.Errors {
            switch {
            case errors.Is(err.Err, ErrNotFound):
                response.Error(c, http.StatusNotFound, "resource not found")
            case errors.Is(err.Err, ErrAccessDenied):
                response.Error(c, http.StatusForbidden, "access denied")
            default:
                log.Printf("Unhandled error: %v", err.Err)
                response.Error(c, http.StatusInternalServerError, "internal error")
            }
        }
    }
}
```

### 3. 错误日志记录

```go
package middleware

import (
    "log/slog"
    "net/http"
    
    "github.com/gin-gonic/gin"
)

func LoggingErrorHandler(logger *slog.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        for _, err := range c.Errors {
            // 记录完整错误信息
            logger.Error("request error",
                "path", c.Request.URL.Path,
                "method", c.Request.Method,
                "error", err.Error(),
                "stack", err.Stack,
            )
            
            // 返回用户友好的错误
            var statusCode int
            var message string
            
            switch e := err.Err.(type) {
            case *errors.AppError:
                statusCode = mapAppErrorToHTTP(e.Code)
                message = e.Message
            default:
                statusCode = http.StatusInternalServerError
                message = "internal server error"
            }
            
            c.JSON(statusCode, gin.H{"error": message})
        }
    }
}
```

---

## 最佳实践

### 1. 及早返回

```go
// ❌ 不好：深层嵌套
func Bad() error {
    if valid {
        if authorized {
            if exists {
                return doSomething()
            } else {
                return ErrNotFound
            }
        } else {
            return ErrUnauthorized
        }
    } else {
        return ErrInvalid
    }
}

// ✅ 好：及早返回
func Good() error {
    if !valid {
        return ErrInvalid
    }
    
    if !authorized {
        return ErrUnauthorized
    }
    
    if !exists {
        return ErrNotFound
    }
    
    return doSomething()
}
```

### 2. 错误只在需要时包装

```go
// ❌ 不好：过度包装
func Bad() error {
    return fmt.Errorf("failed to do step 1: %w",
        fmt.Errorf("failed to do step 2: %w",
            fmt.Errorf("failed to do step 3: %v", err)))
}

// ✅ 好：有意义地包装
func Good() error {
    if err := step3(); err != nil {
        return fmt.Errorf("failed to process request: %w", err)
    }
    return nil
}
```

### 3. 定义错误哨兵

```go
// 在包级别定义常见错误
var (
    ErrNotFound      = errors.New("resource not found")
    ErrUnauthorized  = errors.New("unauthorized")
    ErrInvalidInput  = errors.New("invalid input")
    ErrConflict      = errors.New("resource conflict")
)

// 使用
if err != nil && errors.Is(err, ErrNotFound) {
    // 处理 not found
}
```

### 4. 不要忽略错误

```go
// ❌ 不好：忽略错误
file, _ := os.Open("file.txt")
defer file.Close()

// ✅ 好：处理错误
file, err := os.Open("file.txt")
if err != nil {
    log.Printf("Failed to open file: %v", err)
    return err
}
defer file.Close()
```

### 5. 提供上下文信息

```go
// ❌ 不好：没有上下文
if err != nil {
    return err
}

// ✅ 好：添加上下文
if err := db.Save(post); err != nil {
    return fmt.Errorf("failed to save post %s: %w", post.Title, err)
}
```

### 6. 区分错误类型

```go
// 可恢复的错误（用户输入错误）
if validationErr := validate(input); validationErr != nil {
    return validationErr  // 返回详细错误信息
}

// 不可恢复的错误（系统错误）
if err := db.Save(data); err != nil {
    return fmt.Errorf("database error: %w", err)  // 不暴露内部细节
}
```

---

## 注意事项

### 1. 避免在错误中包含敏感信息

```go
// ❌ 不好：暴露数据库错误
c.JSON(500, gin.H{"error": err.Error()})

// ✅ 好：记录详细错误，返回通用消息
log.Printf("Database error: %v", err)
c.JSON(500, gin.H{"error": "internal server error"})
```

### 2. 注意错误处理性能

```go
// ❌ 不好：频繁创建错误对象
for i := 0; i < 1000000; i++ {
    if err := process(i); err != nil {
        return errors.New("processing failed")  // 每次都创建
    }
}

// ✅ 好：使用哨兵错误
var ErrProcessingFailed = errors.New("processing failed")
for i := 0; i < 1000000; i++ {
    if err := process(i); err != nil {
        return ErrProcessingFailed  // 复用
    }
}
```

### 3. 正确处理 defer 错误

```go
// ❌ 不好：defer 中的错误被忽略
func process() error {
    file, err := os.Open("file.txt")
    if err != nil {
        return err
    }
    defer file.Close()  // Close() 可能返回错误
    
    return doSomething()
}

// ✅ 好：检查 defer 中的错误
func process() (err error) {
    file, err := os.Open("file.txt")
    if err != nil {
        return err
    }
    defer func() {
        if closeErr := file.Close(); closeErr != nil {
            err = closeErr  // 记录关闭错误
        }
    }()
    
    return doSomething()
}
```

### 4. 避免 panic

```go
// ❌ 不好：在正常流程中使用 panic
func MustGetUser(id int64) *User {
    user, err := repo.FindByID(id)
    if err != nil {
        panic(err)  // 不要这样做
    }
    return user
}

// ✅ 好：返回错误
func GetUser(id int64) (*User, error) {
    user, err := repo.FindByID(id)
    if err != nil {
        return nil, err
    }
    return user, nil
}
```

### 5. 记录错误堆栈

```go
package errors

import (
    "runtime/debug"
)

type AppError struct {
    Code       int
    Message    string
    Underlying error
    Stack      string
}

func NewAppError(code int, message string, underlying error) *AppError {
    return &AppError{
        Code:       code,
        Message:    message,
        Underlying: underlying,
        Stack:      string(debug.Stack()),
    }
}
```

---

## 实战案例：博客系统错误处理

### 完整的错误处理流程

```go
// internal/errors/errors.go
package errors

type AppError struct {
    Code       int
    Message    string
    Underlying error
}

// internal/middleware/error.go
package middleware

func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        if len(c.Errors) > 0 {
            err := c.Errors.Last()
            
            switch e := err.Err.(type) {
            case *errors.AppError:
                c.JSON(getStatusCode(e.Code), gin.H{"error": e.Message})
            default:
                c.JSON(500, gin.H{"error": "internal error"})
            }
        }
    }
}

// internal/service/post.go
func (s *PostService) CreatePost(req *CreatePostRequest) (*Post, error) {
    if req.Title == "" {
        return nil, &errors.AppError{
            Code:    400,
            Message: "title is required",
        }
    }
    
    post := &Post{Title: req.Title}
    if err := s.repo.Create(post); err != nil {
        return nil, &errors.AppError{
            Code:       500,
            Message:    "failed to create post",
            Underlying: err,
        }
    }
    
    return post, nil
}

// internal/handler/post.go
func (h *PostHandler) CreatePost(c *gin.Context) {
    var req CreatePostRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": "invalid request"})
        return
    }
    
    post, err := h.service.CreatePost(&req)
    if err != nil {
        c.Error(err)  // 交给中间件处理
        return
    }
    
    c.JSON(201, post)
}
```

---

## 总结

良好的错误处理是构建可靠系统的关键：

### 关键要点

- ✅ 使用自定义错误类型提供丰富的错误信息
- ✅ 通过错误包装保留错误链
- ✅ 在不同层次转换错误类型
- ✅ 使用中间件统一处理 HTTP 错误响应
- ✅ 记录详细的错误日志，返回友好的用户消息
- ✅ 及早返回，避免深层嵌套
- ✅ 定义错误哨兵，使用 errors.Is 判断
- ✅ 不要忽略错误，不要暴露敏感信息

### 下一步学习

- **Lesson 06**: 测试最佳实践 - 学习如何测试错误处理逻辑
- **Lesson 07**: 性能优化技巧 - 学习错误处理的性能考虑
