# Lesson 07: 性能优化技巧

## 目录
- [性能分析工具](#性能分析工具)
- [数据库性能优化](#数据库性能优化)
- [内存优化](#内存优化)
- [并发性能优化](#并发性能优化)
- [缓存策略](#缓存策略)
- [HTTP 性能优化](#http-性能优化)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## 性能分析工具

### 1. pprof 性能分析

```go
import (
    _ "net/http/pprof"
    "net/http"
)

func main() {
    // 启动 pprof HTTP 服务器
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    
    // 你的应用代码
    router := gin.Default()
    router.Run(":8080")
}
```

### 2. CPU 性能分析

```bash
# 采集 CPU 数据
curl http://localhost:6060/debug/pprof/profile?seconds=30 > cpu.prof

# 分析数据
go tool pprof cpu.prof

# 常用命令
(pprof) top10          # 查看 top 10 消耗 CPU 的函数
(pprof) list function  # 查看特定函数的代码
(pprof) web            # 生成可视化图（需要 graphviz）
```

### 3. 内存性能分析

```bash
# 查看堆内存
curl http://localhost:6060/debug/pprof/heap > heap.prof

# 分析内存
go tool pprof heap.prof

# 查看内存分配
(pprof) top
```

### 4. goroutine 泄漏检测

```bash
# 查看 goroutine 数量
curl http://localhost:6060/debug/pprof/goroutine > goroutine.prof

# 分析 goroutine
go tool pprof goroutine.prof

# 查看 goroutine 堆栈
(pprof) traces
```

### 5. 使用基准测试

```go
func BenchmarkPostCreate(b *testing.B) {
    db := setupTestDB(b)
    repo := NewPostRepository(db)
    post := &Post{Title: "Test", Content: "Content"}
    
    b.ResetTimer()  // 重置计时器
    for i := 0; i < b.N; i++ {
        repo.Create(post)
    }
}

func BenchmarkPostCreateParallel(b *testing.B) {
    db := setupTestDB(b)
    repo := NewPostRepository(db)
    
    b.RunParallel(func(pb *testing.PB) {
        post := &Post{Title: "Test", Content: "Content"}
        for pb.Next() {
            repo.Create(post)
        }
    })
}
```

```bash
# 运行基准测试
go test -bench=. -benchmem

# 输出示例
BenchmarkPostCreate-8          100000    10.2 ms/op    1024 B/op    10 allocs/op
```

---

## 数据库性能优化

### 1. 索引优化

```go
// 在模型中定义索引
type Post struct {
    ID        uint   `gorm:"primaryKey"`
    Title     string `gorm:"size:200;index"`
    Status    string `gorm:"size:20;index"`
    AuthorID  uint   `gorm:"index"`
    CreatedAt time.Time `gorm:"index"`
}

// 复合索引
type Post struct {
    // ...
    Status    string `gorm:"index:idx_status_created"`
    CreatedAt time.Time `gorm:"index:idx_status_created"`
}

// 唯一索引
type User struct {
    Email string `gorm:"uniqueIndex"`
}
```

### 2. 查询优化

```go
// ❌ 不好：N+1 查询问题
func (r *PostRepository) GetAllWithComments() ([]Post, error) {
    var posts []Post
    r.db.Find(&posts)
    
    for i := range posts {
        r.db.Where("post_id = ?", posts[i].ID).Find(&posts[i].Comments)
        // 每个文章单独查询评论
    }
    
    return posts, nil
}

// ✅ 好：使用 Preload 预加载
func (r *PostRepository) GetAllWithComments() ([]Post) {
    var posts []Post
    r.db.Preload("Comments").Find(&posts)
    // 只执行两个查询：1. 查询所有文章 2. 查询所有相关评论
    return posts, nil
}

// ✅ 更好：使用 Joins
func (r *PostRepository) GetPostsPagination(page, pageSize int) ([]Post, error) {
    var posts []Post
    offset := (page - 1) * pageSize
    
    err := r.db.
        Select("posts.*, COUNT(comments.id) as comment_count").
        Joins("LEFT JOIN comments ON comments.post_id = posts.id").
        Group("posts.id").
        Limit(pageSize).
        Offset(offset).
        Find(&posts).Error
    
    return posts, err
}
```

### 3. 批量操作

```go
// ❌ 不好：逐条插入
func (r *PostRepository) InsertMany(posts []Post) error {
    for _, post := range posts {
        if err := r.db.Create(&post).Error; err != nil {
            return err
        }
    }
    return nil
}

// ✅ 好：批量插入
func (r *PostRepository) InsertMany(posts []Post) error {
    if len(posts) == 0 {
        return nil
    }
    
    // GORM 会使用单条 INSERT 语句
    return r.db.Create(&posts).Error
}

// 分批插入（大数据量）
func (r *PostRepository) InsertManyInBatches(posts []Post, batchSize int) error {
    return r.db.CreateInBatches(posts, batchSize).Error
}
```

### 4. 选择性查询

```go
// ❌ 不好：查询所有字段
func (r *PostRepository) GetTitles() ([]string, error) {
    var posts []Post
    r.db.Find(&posts)
    
    titles := make([]string, len(posts))
    for i, post := range posts {
        titles[i] = post.Title
    }
    return titles, nil
}

// ✅ 好：只查询需要的字段
func (r *PostRepository) GetTitles() ([]string, error) {
    var titles []string
    err := r.db.Model(&Post{}).
        Pluck("title", &titles).Error
    return titles, err
}

// ✅ 更好：使用 Select
func (r *PostRepository) GetPostSummaries() ([]PostSummary, error) {
    var summaries []PostSummary
    err := r.db.Model(&Post{}).
        Select("id, title, created_at").
        Find(&summaries).Error
    return summaries, err
}
```

### 5. 使用连接池

```go
func InitDB(connectionString string) (*gorm.DB, error) {
    db, err := gorm.Open(mysql.Open(connectionString), &gorm.Config{})
    if err != nil {
        return nil, err
    }
    
    sqlDB, err := db.DB()
    if err != nil {
        return nil, err
    }
    
    // 设置连接池参数
    sqlDB.SetMaxIdleConns(10)           // 最大空闲连接数
    sqlDB.SetMaxOpenConns(100)          // 最大打开连接数
    sqlDB.SetConnMaxLifetime(time.Hour) // 连接最大生存时间
    
    return db, nil
}
```

---

## 内存优化

### 1. 减少内存分配

```go
// ❌ 不好：频繁分配内存
func ProcessData(items []string) []string {
    var result []string
    for _, item := range items {
        result = append(result, strings.ToUpper(item))
    }
    return result
}

// ✅ 好：预分配容量
func ProcessData(items []string) []string {
    result := make([]string, 0, len(items))
    for _, item := range items {
        result = append(result, strings.ToUpper(item))
    }
    return result
}
```

### 2. 使用对象池

```go
import "sync"

var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func ProcessData(data string) string {
    // 从池中获取
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufferPool.Put(buf)  // 归还到池中
    }()
    
    buf.WriteString("Processed: ")
    buf.WriteString(data)
    return buf.String()
}
```

### 3. 避免不必要的拷贝

```go
// ❌ 不好：返回拷贝
func GetUser(id int) User {
    return users[id]  // 拷贝整个结构体
}

// ✅ 好：返回指针
func GetUser(id int) *User {
    return &users[id]  // 只返回指针
}

// ✅ 更好：对于只读操作
func GetUser(id int) (User, error) {
    var user User
    err := db.First(&user, id).Error
    return user, err
}
```

### 4. 字符串优化

```go
// ❌ 不好：不必要的字符串转换
func Process(bytes []byte) string {
    return string(bytes)  // 分配新字符串
}

// ✅ 好：使用 unsafe（谨慎使用）
func Process(bytes []byte) string {
    return *(*string)(unsafe.Pointer(&bytes))
}

// ✅ 更安全：使用 strings.Builder
func BuildString(parts []string) string {
    var builder strings.Builder
    builder.Grow(len(parts) * 10)  // 预分配
    
    for _, part := range parts {
        builder.WriteString(part)
    }
    return builder.String()
}
```

---

## 并发性能优化

### 1. 使用 Worker Pool

```go
type WorkerPool struct {
    tasks   chan Task
    workers int
    wg      sync.WaitGroup
}

type Task func()

func NewWorkerPool(workers int) *WorkerPool {
    return &WorkerPool{
        tasks:   make(chan Task, workers*2),
        workers: workers,
    }
}

func (p *WorkerPool) Start() {
    for i := 0; i < p.workers; i++ {
        p.wg.Add(1)
        go p.worker()
    }
}

func (p *WorkerPool) worker() {
    defer p.wg.Done()
    for task := range p.tasks {
        task()
    }
}

func (p *WorkerPool) Submit(task Task) {
    p.tasks <- task
}

func (p *WorkerPool) Stop() {
    close(p.tasks)
    p.wg.Wait()
}

// 使用
pool := NewWorkerPool(10)
pool.Start()
defer pool.Stop()

for _, item := range items {
    pool.Submit(func() {
        processItem(item)
    })
}
```

### 2. 使用 errgroup

```go
import "golang.org/x/sync/errgroup"

func ProcessConcurrent(items []string) error {
    g, ctx := errgroup.WithContext(context.Background())
    
    for _, item := range items {
        item := item  // 闭包捕获
        g.Go(func() error {
            return processItem(ctx, item)
        })
    }
    
    return g.Wait()
}
```

### 3. 使用 sync.Map

```go
// 适用于读多写少的场景
var cache sync.Map

func GetOrCompute(key string) (string, error) {
    if value, ok := cache.Load(key); ok {
        return value.(string), nil
    }
    
    value, err := computeExpensive(key)
    if err != nil {
        return "", err
    }
    
    cache.Store(key, value)
    return value, nil
}
```

---

## 缓存策略

### 1. 内存缓存

```go
package cache

import (
    "sync"
    "time"
)

type CacheItem struct {
    Value      interface{}
    Expiration time.Time
}

type MemoryCache struct {
    items map[string]CacheItem
    mu    sync.RWMutex
}

func NewMemoryCache() *MemoryCache {
    return &MemoryCache{
        items: make(map[string]CacheItem),
    }
}

func (c *MemoryCache) Set(key string, value interface{}, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.items[key] = CacheItem{
        Value:      value,
        Expiration: time.Now().Add(ttl),
    }
}

func (c *MemoryCache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, exists := c.items[key]
    if !exists {
        return nil, false
    }
    
    if time.Now().After(item.Expiration) {
        return nil, false
    }
    
    return item.Value, true
}

// 定期清理过期项
func (c *MemoryCache) StartCleanup(interval time.Duration) {
    go func() {
        ticker := time.NewTicker(interval)
        defer ticker.Stop()
        
        for range ticker.C {
            c.cleanup()
        }
    }()
}

func (c *MemoryCache) cleanup() {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    now := time.Now()
    for key, item := range c.items {
        if now.After(item.Expiration) {
            delete(c.items, key)
        }
    }
}
```

### 2. 使用 Redis 缓存

```go
package cache

import (
    "context"
    "encoding/json"
    "time"
    
    "github.com/redis/go-redis/v9"
)

type RedisCache struct {
    client *redis.Client
}

func NewRedisCache(addr string) *RedisCache {
    return &RedisCache{
        client: redis.NewClient(&redis.Options{
            Addr: addr,
        }),
    }
}

func (r *RedisCache) Get(ctx context.Context, key string, dest interface{}) error {
    val, err := r.client.Get(ctx, key).Result()
    if err != nil {
        return err
    }
    
    return json.Unmarshal([]byte(val), dest)
}

func (r *RedisCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }
    
    return r.client.Set(ctx, key, data, ttl).Err()
}

func (r *RedisCache) Delete(ctx context.Context, keys ...string) error {
    return r.client.Del(ctx, keys...).Err()
}
```

### 3. 缓存穿透保护

```go
// 使用单飞模式防止缓存击穿
import "golang.org/x/sync/singleflight"

var flight singleflight.Group

func GetPostWithCache(ctx context.Context, id int64) (*Post, error) {
    // 1. 尝试从缓存获取
    cached, err := cache.Get(ctx, fmt.Sprintf("post:%d", id))
    if err == nil {
        return cached.(*Post), nil
    }
    
    // 2. 使用 singleflight 防止并发请求
    result, err, _ := flight.Do(fmt.Sprintf("post:%d", id), func() (interface{}, error) {
        // 3. 从数据库获取
        post, err := repo.FindByID(id)
        if err != nil {
            return nil, err
        }
        
        // 4. 写入缓存
        cache.Set(ctx, fmt.Sprintf("post:%d", id), post, time.Hour)
        
        return post, nil
    })
    
    if err != nil {
        return nil, err
    }
    
    return result.(*Post), nil
}
```

---

## HTTP 性能优化

### 1. 使用 JSON 流式处理

```go
// ❌ 不好：一次性加载所有数据到内存
func ExportPosts(w http.ResponseWriter, r *http.Request) {
    posts, _ := repo.FindAll()
    json.NewEncoder(w).Encode(posts)
}

// ✅ 好：流式处理
func ExportPosts(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    encoder := json.NewEncoder(w)
    encoder.Encode([]byte("["))  // 开始数组
    
    first := true
    err := repo.StreamEach(func(post *Post) error {
        if !first {
            encoder.Encode([]byte(","))
        }
        first = false
        
        return encoder.Encode(post)
    })
    
    if err != nil {
        // 处理错误
    }
    
    encoder.Encode([]byte("]"))  // 结束数组
}
```

### 2. 使用 HTTP/2 推送

```go
func PushResources(w http.ResponseWriter, r *http.Request) {
    if pusher, ok := w.(http.Pusher); ok {
        // 推送 CSS
        pusher.Push("/static/style.css", nil)
        // 推送 JS
        pusher.Push("/static/app.js", nil)
    }
    
    // 返回主页面
    w.Write([]byte("<html>...</html>"))
}
```

### 3. 压缩响应

```go
import (
    "github.com/gin-gonic/gin"
    "github.com/gin-contrib/gzip"
)

func main() {
    r := gin.Default()
    
    // 使用 gzip 压缩
    r.Use(gzip.Gzip(gzip.DefaultCompression))
    
    r.GET("/api/posts", func(c *gin.Context) {
        c.JSON(200, posts)
    })
    
    r.Run(":8080")
}
```

### 4. 连接复用

```go
transport := &http.Transport{
    MaxIdleConns:        100,
    MaxIdleConnsPerHost: 100,
    IdleConnTimeout:     90 * time.Second,
}

client := &http.Client{
    Transport: transport,
    Timeout:   30 * time.Second,
}
```

---

## 最佳实践

### 1. 过早优化是万恶之源

```go
// ✅ 先关注正确性，再优化
func Process() error {
    // 简单、正确的实现
    if err := validate(); err != nil {
        return err
    }
    
    return process()
}

// 然后通过 profiling 找到真正的瓶颈再优化
```

### 2. 使用性能分析指导优化

```bash
# 1. 运行基准测试
go test -bench=. -benchmem > before.txt

# 2. 优化代码

# 3. 再次运行基准测试
go test -bench=. -benchmem > after.txt

# 4. 比较结果
go test -bench=. -benchmem | benchstat before.txt after.txt
```

### 3. 优化热点路径

```go
// ✅ 优化频繁调用的代码
func isPublished(status string) bool {
    // 使用 switch 代替多个 if
    switch status {
    case "published", "live", "public":
        return true
    default:
        return false
    }
}
```

### 4. 避免过早抽象

```go
// ❌ 不好：不必要的抽象
type Processor interface {
    Process(ctx context.Context, data interface{}) (interface{}, error)
}

// ✅ 好：简单直接
func Process(data string) (string, error) {
    return strings.ToUpper(data), nil
}
```

### 5. 使用性能友好的数据结构

```go
// ✅ 根据使用场景选择合适的数据结构

// 频繁查找
lookup := map[string]*Post{}  // O(1)

// 有序遍历
sorted := []Post{}  // 数组

// 快速插入、删除
list := list.New()  // 链表
```

---

## 注意事项

### 1. 不要为了性能牺牲可读性

```go
// ❌ 不好：难以理解
func f(p,q,r)string{return strings.Join([]string{p,q,r},"-")}

// ✅ 好：清晰易懂
func combine(first, middle, last string) string {
    return fmt.Sprintf("%s-%s-%s", first, middle, last)
}
```

### 2. 注意内存泄漏

```go
// ❌ 不好：goroutine 泄漏
func Process() {
    go func() {
        for {
            // 没有退出条件
            time.Sleep(time.Second)
        }
    }()
}

// ✅ 好：可以取消
func Process(ctx context.Context) {
    go func() {
        ticker := time.NewTicker(time.Second)
        defer ticker.Stop()
        
        for {
            select {
            case <-ticker.C:
                // 处理
            case <-ctx.Done():
                return  // 正常退出
            }
        }
    }()
}
```

### 3. 测量，不要猜测

```bash
# 使用 pprof 找到真正的瓶颈
go tool pprof -http=:8080 cpu.prof
```

### 4. 考虑 GC 影响

```go
// ✅ 减少堆分配
var smallBuf [1024]byte

func Process() {
    // 使用栈上的数组
    use(smallBuf[:])
}
```

---

## 实战案例：博客系统性能优化

### 优化文章列表查询

```go
// 优化前
func (r *PostRepository) List(page, pageSize int) ([]Post, error) {
    var posts []Post
    offset := (page - 1) * pageSize
    
    err := r.db.
        Preload("Author").      // N+1 问题
        Preload("Comments").    // N+1 问题
        Limit(pageSize).
        Offset(offset).
        Find(&posts).Error
    
    return posts, err
}

// 优化后
func (r *PostRepository) List(page, pageSize int) ([]PostSummary, error) {
    var posts []PostSummary
    offset := (page - 1) * pageSize
    
    err := r.db.
        Select("posts.id, posts.title, posts.created_at, posts.status, "+
               "authors.name as author_name, COUNT(comments.id) as comment_count").
        Joins("LEFT JOIN authors ON authors.id = posts.author_id").
        Joins("LEFT JOIN comments ON comments.post_id = posts.id").
        Group("posts.id").
        Limit(pageSize).
        Offset(offset).
        Find(&posts).Error
    
    return posts, err
}
```

### 添加缓存层

```go
type CachedPostService struct {
    repo  PostRepository
    cache Cache
}

func (s *CachedPostService) GetPost(ctx context.Context, id int64) (*Post, error) {
    // 1. 尝试从缓存获取
    key := fmt.Sprintf("post:%d", id)
    var cached Post
    if err := s.cache.Get(ctx, key, &cached); err == nil {
        return &cached, nil
    }
    
    // 2. 从数据库获取
    post, err := s.repo.FindByID(id)
    if err != nil {
        return nil, err
    }
    
    // 3. 写入缓存
    s.cache.Set(ctx, key, post, 5*time.Minute)
    
    return post, nil
}
```

---

## 总结

性能优化是一个持续的过程：

### 关键要点

- ✅ 使用 pprof 和基准测试找到真正的瓶颈
- ✅ 优化数据库查询（索引、预加载、批量操作）
- ✅ 减少内存分配（预分配、对象池）
- ✅ 使用缓存减少重复计算
- ✅ 并发处理提高吞吐量
- ✅ 先测量，后优化
- ✅ 不要牺牲可读性换取微小性能提升
- ✅ 注意内存泄漏和 goroutine 泄漏

### 下一步学习

- **Lesson 08**: 安全实践 - 学习如何编写安全的代码
- **Lesson 09**: 并发编程模式 - 深入学习 Go 并发
