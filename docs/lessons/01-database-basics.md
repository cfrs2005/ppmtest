# Lesson 01: Go 数据库设计基础

## 📖 概念解释

### 1. 数据库层在 Go 应用中的位置

在 Go Web 应用中，数据库层（Data Layer）负责：
- 与数据库建立连接和管理连接池
- 数据的持久化和检索
- 数据库事务管理
- SQL 查询的构建和执行

### 2. Repository 模式

Repository 模式是一种设计模式，它将数据访问逻辑从业务逻辑中分离出来。

**为什么使用 Repository 模式？**
- **单一职责**：每个 repository 只负责一个实体的数据操作
- **易于测试**：可以轻松创建 mock 对象进行单元测试
- **依赖注入**：通过接口注入，降低耦合度
- **可替换性**：更换数据库实现只需修改 repository 层

## 💡 最佳实践

### 1. GORM 配置与连接池管理

```go
import (
    "time"
    "gorm.io/gorm"
    "gorm.io/driver/mysql"
)

func NewDatabase(cfg *config.DatabaseConfig) (*gorm.DB, error) {
    dsn := cfg.DSN()
    
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
        NowFunc: func() time.Time {
            return time.Now().UTC()  // 统一使用 UTC 时间
        },
    })
    
    sqlDB, _ := db.DB()
    
    // 连接池配置
    sqlDB.SetMaxOpenConns(25)        // 最大打开连接数
    sqlDB.SetMaxIdleConns(10)        // 最大空闲连接数
    sqlDB.SetConnMaxLifetime(5 * time.Minute)  // 连接最大生命周期
    
    return db, nil
}
```

**关键配置说明**：
- `SetMaxOpenConns`: 限制数据库连接数，防止连接泄漏
- `SetMaxIdleConns`: 维持一定数量的空闲连接，提高性能
- `SetConnMaxLifetime`: 定期关闭长时间连接，避免数据库侧超时

### 2. Repository 接口设计

```go
type UserRepository interface {
    Create(user *models.User) error
    FindByID(id uint) (*models.User, error)
    FindByEmail(email string) (*models.User, error)
    Update(user *models.User) error
    Delete(id uint) error
    List(offset, limit int) ([]*models.User, int64, error)
}
```

**接口设计原则**：
- 使用接口而非具体实现
- 返回明确的错误类型
- 使用指针传递结构体，避免值拷贝
- 分页查询同时返回总数

### 3. 错误处理

```go
var (
    ErrUserNotFound      = errors.New("user not found")
    ErrUserAlreadyExists = errors.New("user already exists")
)

func (r *userRepository) FindByID(id uint) (*models.User, error) {
    var user models.User
    result := r.db.First(&user, id)
    
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, ErrUserNotFound  // 转换为业务错误
        }
        return nil, result.Error
    }
    
    return &user, nil
}
```

**错误处理要点**：
- 定义业务特定的错误变量
- 使用 `errors.Is()` 检查特定错误
- 将数据库错误转换为业务错误
- 不要忽略任何错误

### 4. 模型定义与 GORM 标签

```go
type User struct {
    ID        uint      `gorm:"primaryKey" json:"id"`
    Username  string    `gorm:"size:50;uniqueIndex;not null" json:"username"`
    Email     string    `gorm:"size:100;uniqueIndex;not null" json:"email"`
    Password  string    `gorm:"size:255;not null" json:"-"`  // json:"-" 不输出密码
    Role      string    `gorm:"size:20;default:author" json:"role"`
    Status    string    `gorm:"size:20;default:active" json:"status"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}
```

**GORM 标签说明**：
- `primaryKey`: 主键
- `size:N`: 字段大小限制
- `uniqueIndex`: 唯一索引
- `not null`: 非空约束
- `default:value`: 默认值
- `json:"field"`: JSON 序列化时的字段名
- `json:"-"`: 不在 JSON 中输出

## ⚠️ 常见陷阱

### 1. N+1 查询问题

**问题代码**：
```go
posts, _ := postRepo.List(0, 10, "")
for _, post := range posts {
    author, _ := userRepo.FindByID(post.AuthorID)  // 每个帖子都查询一次
    // ...
}
```

**解决方案 - 使用 Preload**：
```go
func (r *postRepository) List(offset, limit int) ([]*models.Post, error) {
    var posts []*models.Post
    result := r.db.Preload("Author").  // 预加载关联数据
        Offset(offset).
        Limit(limit).
        Find(&posts)
    return posts, result.Error
}
```

### 2. 忘略事务处理

**问题代码**：
```go
userRepo.Create(user)
postRepo.Create(post)  // 如果这里失败，用户已经创建
```

**解决方案 - 使用事务**：
```go
tx := db.Begin()
defer func() {
    if r := recover(); r != nil {
        tx.Rollback()
    }
}()

if err := tx.Create(user).Error; err != nil {
    tx.Rollback()
    return err
}

if err := tx.Create(post).Error; err != nil {
    tx.Rollback()
    return err
}

tx.Commit()
```

### 3. 连接泄漏

**问题**：忘记关闭数据库连接

```go
db, _ := database.New(cfg)
// 使用 db
// 忘记调用 db.Close()
```

**解决方案**：
```go
db, _ := database.New(cfg)
defer db.Close()  // 确保函数返回时关闭连接
```

### 4. 时间时区混乱

**问题**：使用本地时间导致跨时区问题

```go
CreatedAt time.Time `json:"created_at"`  // 使用服务器本地时间
```

**解决方案**：
```go
// 在 GORM 配置中设置
NowFunc: func() time.Time {
    return time.Now().UTC()  // 统一使用 UTC
}
```

## 🔧 实战示例

### 完整的 Repository 实现

参考 `internal/repository/user_repository.go` 的实现：

1. **定义接口**：声明所有数据操作方法
2. **实现结构体**：包含数据库连接
3. **错误处理**：统一错误转换
4. **分页查询**：返回数据和总数
5. **关联查询**：使用 Preload 避免N+1问题

### 自动迁移

使用 GORM 的 AutoMigrate 功能：

```go
func (d *Database) AutoMigrate() error {
    return d.DB.AutoMigrate(
        &models.User{},
        &models.Post{},
        &models.Comment{},
    )
}
```

**注意**：
- AutoMigrate 只会添加缺失的字段和表，不会删除现有字段
- 生产环境建议使用版本化的迁移脚本
- 复杂的索引和约束需要手动管理

## ✅ 练习任务

### 任务 1：实现软删除

修改 User 模型，添加 `DeletedAt` 字段支持软删除：

```go
type User struct {
    // ... 其他字段
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}
```

然后测试删除操作是否真的删除数据。

### 任务 2：添加全文搜索

在 PostRepository 中添加全文搜索方法：

```go
func (r *postRepository) FullTextSearch(query string, offset, limit int) ([]*models.Post, int64, error)
```

使用 MySQL 的 FULLTEXT 索引或 GORM 的 LIKE 查询。

### 任务 3：实现缓存层

在 Repository 层之上添加缓存层：

```go
type cachedUserRepository struct {
    repo  UserRepository
    cache *redis.Client
}
```

对频繁访问的数据（如当前用户）进行缓存。

### 任务 4：编写单元测试

为 UserRepository 编写表驱动的单元测试：

```go
func TestUserRepository_FindByID(t *testing.T) {
    tests := []struct {
        name    string
        id      uint
        want    *models.User
        wantErr error
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

## 📚 延伸阅读

- [GORM 官方文档](https://gorm.io/docs/)
- [Go database/sql 包设计原理](https://go.dev/doc/database/manage-connections)
- [Repository 模式详解](https://martinfowler.com/eaaCatalog/repository.html)
- [Go 错误处理最佳实践](https://go.dev/doc/tutorial/errors.html)

## 🎯 总结

本课程学习了：
- ✅ GORM 配置和连接池管理
- ✅ Repository 模式的实现
- ✅ 错误处理和最佳实践
- ✅ 避免 N+1 查询问题
- ✅ 事务处理和连接管理

下一步：学习服务层架构设计（Lesson 02）