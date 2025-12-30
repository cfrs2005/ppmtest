# Lesson 08: 安全实践

## 目录
- [输入验证](#输入验证)
- [SQL 注入防护](#sql-注入防护)
- [XSS 防护](#xss-防护)
- [CSRF 防护](#csrf-防护)
- [认证和授权](#认证和授权)
- [敏感数据保护](#敏感数据保护)
- [安全 Headers](#安全-headers)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## 输入验证

### 1. 验证所有输入

```go
package validation

import (
    "regexp"
    "unicode"
)

type Validator struct {
    errors map[string]string
}

func NewValidator() *Validator {
    return &Validator{
        errors: make(map[string]string),
    }
}

// 验证字符串长度
func (v *Validator) Length(field, value string, min, max int) *Validator {
    if len(value) < min || len(value) > max {
        v.errors[field] = fmt.Sprintf("length must be between %d and %d", min, max)
    }
    return v
}

// 验证 email 格式
func (v *Validator) Email(field, value string) *Validator {
    emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
    if !emailRegex.MatchString(value) {
        v.errors[field] = "invalid email format"
    }
    return v
}

// 验证密码强度
func (v *Validator) Password(field, password string) *Validator {
    if len(password) < 8 {
        v.errors[field] = "password must be at least 8 characters"
        return v
    }
    
    var (
        hasUpper   bool
        hasLower   bool
        hasNumber  bool
        hasSpecial bool
    )
    
    for _, char := range password {
        switch {
        case unicode.IsUpper(char):
            hasUpper = true
        case unicode.IsLower(char):
            hasLower = true
        case unicode.IsNumber(char):
            hasNumber = true
        case unicode.IsPunct(char) || unicode.IsSymbol(char):
            hasSpecial = true
        }
    }
    
    if !hasUpper || !hasLower || !hasNumber || !hasSpecial {
        v.errors[field] = "password must contain uppercase, lowercase, number, and special character"
    }
    
    return v
}

// 验证用户名（只允许字母数字和下划线）
func (v *Validator) Username(field, value string) *Validator {
    usernameRegex := regexp.MustCompile(`^[a-zA-Z0-9_]{3,20}$`)
    if !usernameRegex.MatchString(value) {
        v.errors[field] = "username must be 3-20 characters, alphanumeric and underscores only"
    }
    return v
}

// 检查是否有验证错误
func (v *Validator) HasErrors() bool {
    return len(v.errors) > 0
}

// 获取所有错误
func (v *Validator) Errors() map[string]string {
    return v.errors
}
```

### 2. 清理输入

```go
package sanitize

import (
    "html"
    "regexp"
    "strings"
)

// 清理 HTML 输入
func HTML(input string) string {
    return html.EscapeString(input)
}

// 清理 SQL 输入
func SQL(input string) string {
    // 移除特殊字符
    reg := regexp.MustCompile(`[;'"]`)
    return reg.ReplaceAllString(input, "")
}

// 清理文件名
func Filename(input string) string {
    // 移除路径遍历字符
    reg := regexp.MustCompile(`[.\./]`)
    cleaned := reg.ReplaceAllString(input, "")
    
    // 限制长度
    if len(cleaned) > 255 {
        cleaned = cleaned[:255]
    }
    
    return strings.TrimSpace(cleaned)
}

// 移除空白字符
func TrimSpace(input string) string {
    return strings.TrimSpace(input)
}
```

### 3. 使用验证中间件

```go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func ValidateRequest(req interface{}) gin.HandlerFunc {
    return func(c *gin.Context) {
        if err := c.ShouldBindJSON(req); err != nil {
            c.JSON(400, gin.H{
                "error": "invalid request",
                "details": err.Error(),
            })
            c.Abort()
            return
        }
        
        // 执行自定义验证
        if v, ok := req.(interface{ Validate() *validation.Validator }); ok {
            if validator := v.Validate(); validator.HasErrors() {
                c.JSON(400, gin.H{
                    "error": "validation failed",
                    "fields": validator.Errors(),
                })
                c.Abort()
                return
            }
        }
        
        c.Set("validatedRequest", req)
        c.Next()
    }
}
```

---

## SQL 注入防护

### 1. 使用参数化查询

```go
// ❌ 不好：直接拼接 SQL（易受 SQL 注入攻击）
func (r *PostRepository) FindByTitle(title string) (*Post, error) {
    var post Post
    query := fmt.Sprintf("SELECT * FROM posts WHERE title = '%s'", title)
    err := r.db.Raw(query).Scan(&post).Error
    return &post, err
}

// ✅ 好：使用参数化查询
func (r *PostRepository) FindByTitle(title string) (*Post, error) {
    var post Post
    err := r.db.Where("title = ?", title).First(&post).Error
    return &post, err
}

// ✅ 更好：使用命名参数
func (r *PostRepository) FindByTitleAndStatus(title, status string) (*Post, error) {
    var post Post
    err := r.db.Where("title = ? AND status = ?", title, status).First(&post).Error
    return &post, err
}
```

### 2. 使用 ORM

```go
// GORM 会自动处理参数化查询
func (r *PostRepository) FindByConditions(title string, authorID uint) (*Post, error) {
    var post Post
    err := r.db.Where("title = ? AND author_id = ?", title, authorID).First(&post).Error
    return &post, err
}

// 使用结构体
func (r *PostRepository) Find(post *Post) error {
    return r.db.Where(post).First(post).Error
}

// 使用 Map
func (r *PostRepository) FindByMap(title string, status string) ([]Post, error) {
    var posts []Post
    err := r.db.Where(map[string]interface{}{
        "title":  title,
        "status": status,
    }).Find(&posts).Error
    return posts, err
}
```

### 3. 避免动态 SQL

```go
// ❌ 不好：动态 SQL
func (r *PostRepository) Search(field, value string) ([]Post, error) {
    var posts []Post
    query := fmt.Sprintf("SELECT * FROM posts WHERE %s = ?", field)
    err := r.db.Raw(query, value).Find(&posts).Error
    return posts, err
}

// ✅ 好：使用白名单
func (r *PostRepository) Search(field, value string) ([]Post, error) {
    allowedFields := map[string]bool{
        "title":  true,
        "status": true,
        "author": true,
    }
    
    if !allowedFields[field] {
        return nil, errors.New("invalid field")
    }
    
    var posts []Post
    err := r.db.Where(field+" = ?", value).Find(&posts).Error
    return posts, err
}
```

---

## XSS 防护

### 1. 转义输出

```go
package html

import "html"

func RenderComment(comment string) string {
    // 转义 HTML 特殊字符
    return html.EscapeString(comment)
}

// 在模板中使用
{{ .Comment | html }}
```

### 2. 使用安全的模板

```go
// Go 的 text/template 和 html/template 默认会转义
import "html/template"

func RenderTemplate(w http.ResponseWriter, data interface{}) {
    tmpl, err := template.New("post").Parse(`
        <div>
            <h1>{{ .Title }}</h1>
            <p>{{ .Content }}</p>  <!-- 自动转义 -->
        </div>
    `)
    
    if err != nil {
        http.Error(w, err.Error(), 500)
        return
    }
    
    tmpl.Execute(w, data)
}
```

### 3. 内容安全策略（CSP）

```go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func ContentSecurityPolicy() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Content-Security-Policy", 
            "default-src 'self'; "+
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.example.com; "+
            "style-src 'self' 'unsafe-inline'; "+
            "img-src 'self' data: https:; "+
            "font-src 'self'; "+
            "connect-src 'self'; "+
            "frame-ancestors 'none';")
        c.Next()
    }
}
```

### 4. 输入过滤

```go
package sanitizer

import (
    "regexp"
    "strings"
)

// 移除危险 HTML 标签
func SanitizeHTML(input string) string {
    // 移除 <script> 标签
    scriptRegex := regexp.MustCompile(`<script[^>]*>.*?</script>`)
    input = scriptRegex.ReplaceAllString(input, "")
    
    // 移除 <iframe> 标签
    iframeRegex := regexp.MustCompile(`<iframe[^>]*>.*?</iframe>`)
    input = iframeRegex.ReplaceAllString(input, "")
    
    // 移除事件处理器（如 onclick）
    eventRegex := regexp.MustCompile(`on\w+="[^"]*"`)
    input = eventRegex.ReplaceAllString(input, "")
    
    return input
}

// 只允许纯文本
func PlainText(input string) string {
    // 移除所有 HTML 标签
    reg := regexp.MustCompile(`<[^>]*>`)
    return reg.ReplaceAllString(input, "")
}

// 限制链接
func SanitizeURL(input string) string {
    // 只允许 http 和 https 协议
    if strings.HasPrefix(input, "http://") || strings.HasPrefix(input, "https://") {
        return input
    }
    return ""
}
```

---

## CSRF 防护

### 1. CSRF Token 中间件

```go
package middleware

import (
    "crypto/rand"
    "encoding/hex"
    "github.com/gin-gonic/gin"
)

// 生成 CSRF Token
func GenerateCSRFToken() (string, error) {
    bytes := make([]byte, 32)
    if _, err := rand.Read(bytes); err != nil {
        return "", err
    }
    return hex.EncodeToString(bytes), nil
}

// 存储 CSRF Token（可以使用 Redis）
type CSRFStore interface {
    GetToken(sessionID string) (string, error)
    SetToken(sessionID, token string) error
    ValidateToken(sessionID, token string) bool
}

type MemoryCSRFStore struct {
    tokens map[string]string
    mu     sync.RWMutex
}

func NewMemoryCSRFStore() *MemoryCSRFStore {
    return &MemoryCSRFStore{
        tokens: make(map[string]string),
    }
}

func (s *MemoryCSRFStore) SetToken(sessionID, token string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.tokens[sessionID] = token
    return nil
}

func (s *MemoryCSRFStore) ValidateToken(sessionID, token string) bool {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.tokens[sessionID] == token
}

// CSRF 中间件
func CSRFMiddleware(store CSRFStore) gin.HandlerFunc {
    return func(c *gin.Context) {
        // 只检查 POST、PUT、DELETE、PATCH 请求
        if c.Request.Method == "GET" || c.Request.Method == "HEAD" || c.Request.Method == "OPTIONS" {
            c.Next()
            return
        }
        
        sessionID := c.GetHeader("X-Session-ID")
        token := c.GetHeader("X-CSRF-Token")
        
        if sessionID == "" || token == "" {
            c.JSON(403, gin.H{"error": "CSRF token missing"})
            c.Abort()
            return
        }
        
        if !store.ValidateToken(sessionID, token) {
            c.JSON(403, gin.H{"error": "Invalid CSRF token"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

### 2. 使用 SameSite Cookie

```go
func SetSecureCookie(c *gin.Context, name, value string) {
    c.SetCookie(name, value, 3600, "/", "", true, true)  // SameSite=Strict
}
```

---

## 认证和授权

### 1. JWT 认证

```go
package auth

import (
    "crypto/rand"
    "encoding/base64"
    "errors"
    "time"
    
    "github.com/golang-jwt/jwt/v5"
)

type Claims struct {
    UserID   int64  `json:"sub"`
    Username string `json:"username"`
    Role     string `json:"role"`
    jwt.RegisteredClaims
}

type AuthService struct {
    secretKey []byte
}

func NewAuthService(secret string) *AuthService {
    return &AuthService{
        secretKey: []byte(secret),
    }
}

// 生成 JWT Token
func (a *AuthService) GenerateToken(userID int64, username, role string) (string, error) {
    claims := Claims{
        UserID:   userID,
        Username: username,
        Role:     role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            NotBefore: jwt.NewNumericDate(time.Now()),
        },
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(a.secretKey)
}

// 验证 JWT Token
func (a *AuthService) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, errors.New("invalid signing method")
        }
        return a.secretKey, nil
    })
    
    if err != nil {
        return nil, err
    }
    
    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }
    
    return nil, errors.New("invalid token")
}

// 生成刷新 Token
func (a *AuthService) GenerateRefreshToken() (string, error) {
    bytes := make([]byte, 32)
    if _, err := rand.Read(bytes); err != nil {
        return "", err
    }
    return base64.URLEncoding.EncodeToString(bytes), nil
}
```

### 2. 权限检查

```go
package middleware

import (
    "github.com/gin-gonic/gin"
)

// 权限常量
const (
    RoleAdmin      = "admin"
    RoleEditor     = "editor"
    RoleAuthor     = "author"
    RoleSubscriber = "subscriber"
)

// 权限检查中间件
func RequireRole(allowedRoles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        role, exists := c.Get("role")
        if !exists {
            c.JSON(401, gin.H{"error": "unauthorized"})
            c.Abort()
            return
        }
        
        userRole := role.(string)
        allowed := false
        for _, r := range allowedRoles {
            if userRole == r {
                allowed = true
                break
            }
        }
        
        if !allowed {
            c.JSON(403, gin.H{"error": "forbidden"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}

// 资源所有权检查
func RequireOwnership() gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := c.GetInt64("userID")
        resourceID := c.Param("id")
        
        // 检查用户是否拥有该资源
        if !ownsResource(userID, resourceID) {
            c.JSON(403, gin.H{"error": "you don't own this resource"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

### 3. 密码哈希

```go
package auth

import (
    "golang.org/x/crypto/bcrypt"
)

// 哈希密码
func HashPassword(password string) (string, error) {
    bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    return string(bytes), err
}

// 验证密码
func CheckPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}
```

---

## 敏感数据保护

### 1. 环境变量管理

```go
package config

import (
    "os"
    "github.com/joho/godotenv"
)

type Config struct {
    DatabaseURL string
    JWTSecret   string
    RedisURL    string
}

func LoadConfig() (*Config, error) {
    // 加载 .env 文件（不提交到版本控制）
    if err := godotenv.Load(); err != nil {
        return nil, err
    }
    
    return &Config{
        DatabaseURL: os.Getenv("DATABASE_URL"),
        JWTSecret:   os.Getenv("JWT_SECRET"),
        RedisURL:    os.Getenv("REDIS_URL"),
    }, nil
}
```

### 2. 加密敏感数据

```go
package encryption

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "encoding/base64"
    "io"
)

// 加密
func Encrypt(plaintext []byte, key []byte) (string, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return "", err
    }
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return "", err
    }
    
    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return "", err
    }
    
    ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)
    return base64.URLEncoding.EncodeToString(ciphertext), nil
}

// 解密
func Decrypt(ciphertext string, key []byte) ([]byte, error) {
    data, err := base64.URLEncoding.DecodeString(ciphertext)
    if err != nil {
        return nil, err
    }
    
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    
    nonceSize := gcm.NonceSize()
    if len(data) < nonceSize {
        return nil, errors.New("ciphertext too short")
    }
    
    nonce, ciphertext := data[:nonceSize], data[nonceSize:]
    return gcm.Open(nil, nonce, ciphertext, nil)
}
```

### 3. 日志脱敏

```go
package logger

import (
    "regexp"
)

// 脱敏函数
func Sanitize(log string) string {
    // 脱敏 email
    emailRegex := regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`)
    log = emailRegex.ReplaceAllString(log, "***@***.***")
    
    // 脱敏手机号
    phoneRegex := regexp.MustCompile(`\b1[3-9]\d{9}\b`)
    log = phoneRegex.ReplaceAllString(log, "***********")
    
    // 脱敏身份证号
    idCardRegex := regexp.MustCompile(`\b\d{17}[\dXx]\b`)
    log = idCardRegex.ReplaceAllString(log, "******************")
    
    return log
}
```

---

## 安全 Headers

### 1. 安全响应头中间件

```go
package middleware

import (
    "github.com/gin-gonic/gin"
)

func SecurityHeaders() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 防止点击劫持
        c.Header("X-Frame-Options", "DENY")
        
        // 防止 MIME 类型嗅探
        c.Header("X-Content-Type-Options", "nosniff")
        
        // 启用浏览器 XSS 保护
        c.Header("X-XSS-Protection", "1; mode=block")
        
        // 内容安全策略
        c.Header("Content-Security-Policy", 
            "default-src 'self'; "+
            "script-src 'self' 'unsafe-inline'; "+
            "style-src 'self' 'unsafe-inline';")
        
        // 严格传输安全（仅 HTTPS）
        c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        
        // 推荐人策略
        c.Header("Referrer-Policy", "strict-origin-when-cross-origin")
        
        // 权限策略
        c.Header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        
        c.Next()
    }
}
```

---

## 最佳实践

### 1. 最小权限原则

```go
// ✅ 只授予必要的权限
func (s *PostService) UpdatePost(userID, postID int64, updates map[string]interface{}) error {
    post, err := s.repo.FindByID(postID)
    if err != nil {
        return err
    }
    
    // 检查所有权
    if post.AuthorID != userID {
        return errors.New("unauthorized")
    }
    
    // 只允许更新特定字段
    allowedFields := map[string]bool{
        "title":   true,
        "content": true,
        "status":  true,
    }
    
    for field := range updates {
        if !allowedFields[field] {
            delete(updates, field)
        }
    }
    
    return s.repo.Update(post, updates)
}
```

### 2. 使用准备好的语句

```go
// ✅ 始终使用准备好的语句
func (r *PostRepository) FindByID(id int64) (*Post, error) {
    var post Post
    err := r.db.Where("id = ?", id).First(&post).Error  // 准备好的语句
    return &post, err
}
```

### 3. 定期更新依赖

```bash
# 检查过期依赖
go list -u -m all

# 更新依赖
go get -u ./...
go mod tidy
```

### 4. 使用安全配置

```go
// ✅ 禁用调试模式
gin.SetMode(gin.ReleaseMode)

// ✅ 使用 HTTPS
func main() {
    // ... 配置 TLS
    router.RunTLS(":443", "cert.pem", "key.pem")
}

// ✅ 限制请求大小
router.MaxMultipartMemory = 8 << 20  // 8 MB
```

### 5. 错误处理不暴露敏感信息

```go
// ❌ 不好：暴露数据库错误
func (h *Handler) CreatePost(c *gin.Context) {
    if err := h.service.CreatePost(req); err != nil {
        c.JSON(500, gin.H{"error": err.Error()})  // 可能包含敏感信息
        return
    }
}

// ✅ 好：返回通用错误
func (h *Handler) CreatePost(c *gin.Context) {
    if err := h.service.CreatePost(req); err != nil {
        log.Printf("Error: %v", err)  // 记录详细错误
        c.JSON(500, gin.H{"error": "internal server error"})  // 返回通用消息
        return
    }
}
```

---

## 注意事项

### 1. 永远不要信任客户端输入

```go
// ❌ 不好：信任客户端
func (h *Handler) CreatePost(c *gin.Context) {
    authorID := c.GetHeader("X-User-ID")  // 客户端可以伪造
    post.AuthorID = authorID
}

// ✅ 好：从认证信息获取
func (h *Handler) CreatePost(c *gin.Context) {
    authorID := c.GetInt64("userID")  // 从 JWT 获取
    post.AuthorID = authorID
}
```

### 2. 不要在 URL 中传递敏感信息

```go
// ❌ 不好：在 URL 中传递密码
GET /api/login?username=user&password=pass

// ✅ 好：使用 POST + HTTPS
POST /api/login
Body: {"username": "user", "password": "pass"}
```

### 3. 使用 HTTPS

```go
// ✅ 始终使用 HTTPS
func main() {
    router := gin.Default()
    
    // 重定向 HTTP 到 HTTPS
    router.Use(func(c *gin.Context) {
        if c.Request.Header.Get("X-Forwarded-Proto") == "http" {
            url := "https://" + c.Request.Host + c.Request.URL.String()
            c.Redirect(http.StatusMovedPermanently, url)
            c.Abort()
            return
        }
        c.Next()
    })
    
    router.RunTLS(":443", "cert.pem", "key.pem")
}
```

### 4. 限制重定向

```go
// ❌ 不好：开放重定向
func Redirect(c *gin.Context) {
    url := c.Query("url")
    c.Redirect(302, url)  // 可以重定向到任何 URL
}

// ✅ 好：白名单重定向
func Redirect(c *gin.Context) {
    url := c.Query("url")
    allowedDomains := []string{"example.com", "www.example.com"}
    
    if isAllowedDomain(url, allowedDomains) {
        c.Redirect(302, url)
    } else {
        c.JSON(400, gin.H{"error": "invalid redirect URL"})
    }
}
```

---

## 实战案例：博客系统安全

### 完整的安全配置

```go
func main() {
    gin.SetMode(gin.ReleaseMode)
    router := gin.Default()
    
    // 安全中间件
    router.Use(
        middleware.SecurityHeaders(),
        middleware.CORS(),
        middleware.CSRFMiddleware(csrfStore),
        middleware.RequestLogger(),
        middleware.Recovery(),
    )
    
    // 公开路由
    public := router.Group("/api/v1/public")
    {
        public.GET("/posts", handlers.GetPosts)
        public.GET("/posts/:id", handlers.GetPostByID)
    }
    
    // 认证路由
    auth := router.Group("/api/v1")
    auth.Use(middleware.Authenticate())
    {
        auth.POST("/posts", middleware.ValidateRequest(&CreatePostRequest{}), handlers.CreatePost)
    }
    
    // 管理员路由
    admin := router.Group("/api/v1/admin")
    admin.Use(middleware.Authenticate(), middleware.RequireRole("admin"))
    {
        admin.DELETE("/posts/:id", handlers.DeletePost)
    }
    
    router.RunTLS(":443", "cert.pem", "key.pem")
}
```

---

## 总结

安全是持续的过程，不是一次性的任务：

### 关键要点

- ✅ 验证和清理所有输入
- ✅ 使用参数化查询防止 SQL 注入
- ✅ 转义输出防止 XSS
- ✅ 使用 CSRF Token
- ✅ 实施强认证和授权
- ✅ 保护敏感数据（加密、哈希）
- ✅ 设置安全响应头
- ✅ 使用 HTTPS
- ✅ 定期更新依赖
- ✅ 记录和监控安全事件
- ✅ 遵循最小权限原则
- ✅ 错误处理不暴露敏感信息

### 下一步学习

- **Lesson 09**: 并发编程模式 - 深入学习 Go 并发编程
