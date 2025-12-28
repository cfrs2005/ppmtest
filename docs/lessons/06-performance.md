# Lesson 06: Go 性能优化实战

## 📖 概念解释

### 1. Go 性能优化的层次

性能优化应该在以下层面进行：
- **算法优化**：选择更高效的算法和数据结构
- **数据库优化**：索引、查询优化、连接池
- **并发优化**：利用 Goroutine 和 Channel
- **内存优化**：减少内存分配和垃圾回收压力
- **网络优化**：缓存、压缩、CDN

### 2. 性能分析工具

- **pprof**：CPU 和内存分析
- **trace**：执行跟踪
- **benchstat**：基准测试比较
- **go test -bench**：性能基准测试

## 💡 最佳实践

### 1. 数据库查询优化

#### 避免 N+1 问题

**问题代码**：
```go
posts, _ := postRepo.List(0, 10)
for _, post := range posts {
    author, _ := userRepo.FindByID(post.AuthorID)  // N+1 问题
}
```

**解决方案**：
```go
func (r *postRepository) ListWithAuthors() ([]*models.Post, error) {
    var posts []*models.Post
    result := r.db.Preload("Author").Find(&posts)  // 使用 JOIN
    return posts, result.Error
}
```

#### 使用索引

```go
type User struct {
    ID       uint   `gorm:"primaryKey"`
    Email    string `gorm:"size:100;uniqueIndex;not null"`  // 唯一索引
    Username string `gorm:"size:50;index;not null"`         // 普通索引
    Status   string `gorm:"size:20;index:idx_status"`       // 复合索引
    Role     string `gorm:"size:20;index:idx_status"`
}

func (m *User) TableName() string {
    return "users"
}
```

**索引优化要点**：
- 为经常查询的字段添加索引
- 为 WHERE、JOIN、ORDER BY 字段添加索引
- 避免过度索引（影响写入性能）
- 使用复合索引优化多字段查询

### 2. 连接池优化

```go
func NewDatabase(cfg *config.DatabaseConfig) (*Database, error) {
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    
    sqlDB, _ := db.DB()
    
    sqlDB.SetMaxOpenConns(25)        // 最大连接数
    sqlDB.SetMaxIdleConns(10)        // 最大空闲连接
    sqlDB.SetConnMaxLifetime(5 * time.Minute)  // 连接最大生命周期
    sqlDB.SetConnMaxIdleTime(1 * time.Minute)  // 空闲连接最大存活时间
    
    return &Database{DB: db}, nil
}
```

**连接池配置建议**：
- `MaxOpenConns`：根据数据库服务器配置和应用并发量设置
- `MaxIdleConns`：通常是 MaxOpenConns 的 20-50%
- `ConnMaxLifetime`：5-10 分钟，避免长时间连接
- `ConnMaxIdleTime`：1-5 分钟，回收空闲连接

### 3. 并发优化

#### 并发处理请求

```go
func (s *postService) GetPostsMetadata(posts []*models.Post) ([]*PostMetadata, error) {
    var wg sync.WaitGroup
    results := make([]*PostMetadata, len(posts))
    errors := make(chan error, len(posts))
    
    for i, post := range posts {
        wg.Add(1)
        go func(index int, p *models.Post) {
            defer wg.Done()
            
            metadata, err := s.fetchPostMetadata(p)
            if err != nil {
                errors <- err
                return
            }
            results[index] = metadata
        }(i, post)
    }
    
    wg.Wait()
    close(errors)
    
    if len(errors) > 0 {
        return nil, <-errors
    }
    
    return results, nil
}
```

#### 使用 Worker Pool

```go
type WorkerPool struct {
    tasks   chan Task
    workers int
    wg      sync.WaitGroup
}

func NewWorkerPool(workers int) *WorkerPool {
    return &WorkerPool{
        tasks:   make(chan Task, workers*2),
        workers: workers,
    }
}

func (p *WorkerPool) Start() {
    for i := 0; i < p.workers; i++ {
        p.wg.Add(1)
        go p.worker(i)
    }
}

func (p *WorkerPool) worker(id int) {
    defer p.wg.Done()
    for task := range p.tasks {
        task.Execute()
    }
}

func (p *WorkerPool) Submit(task Task) {
    p.tasks <- task
}

func (p *WorkerPool) Shutdown() {
    close(p.tasks)
    p.wg.Wait()
}
```

### 4. 缓存策略

#### 内存缓存

```go
type Cache struct {
    data map[string]interface{}
    mu   sync.RWMutex
    ttl  map[string]time.Time
}

func NewCache() *Cache {
    cache := &Cache{
        data: make(map[string]interface{}),
        ttl:  make(map[string]time.Time),
    }
    
    go cache.cleanup()
    return cache
}

func (c *Cache) Set(key string, value interface{}, duration time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.data[key] = value
    c.ttl[key] = time.Now().Add(duration)
}

func (c *Cache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    if expiry, ok := c.ttl[key]; ok && time.Now().Before(expiry) {
        value, ok := c.data[key]
        return value, ok
    }
    
    return nil, false
}

func (c *Cache) cleanup() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        c.mu.Lock()
        now := time.Now()
        for key, expiry := range c.ttl {
            if now.After(expiry) {
                delete(c.data, key)
                delete(c.ttl, key)
            }
        }
        c.mu.Unlock()
    }
}
```

#### 使用缓存装饰器

```go
type cachedPostService struct {
    service PostService
    cache   *Cache
}

func NewCachedPostService(service PostService, cache *Cache) PostService {
    return &cachedPostService{
        service: service,
        cache:   cache,
    }
}

func (s *cachedPostService) GetPostByID(id uint) (*models.Post, error) {
    cacheKey := fmt.Sprintf("post:%d", id)
    
    if cached, found := s.cache.Get(cacheKey); found {
        return cached.(*models.Post), nil
    }
    
    post, err := s.service.GetPostByID(id)
    if err != nil {
        return nil, err
    }
    
    s.cache.Set(cacheKey, post, 5*time.Minute)
    return post, nil
}
```

### 5. 内存优化

#### 减少内存分配

```go
func ProcessData(data []string) string {
    var builder strings.Builder  // 使用 strings.Builder 而不是 + 拼接
    builder.Grow(len(data) * 10)
    
    for _, s := range data {
        builder.WriteString(s)
    }
    
    return builder.String()
}
```

#### 使用对象池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func ProcessWithPool() string {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufferPool.Put(buf)
    }()
    
    buf.WriteString("Hello")
    return buf.String()
}
```

#### 避免内存泄漏

```go
func (s *server) handleConnections() {
    for {
        select {
        case conn := <-s.newConnections:
            s.connections[conn.id] = conn
        case id := <-s.closedConnections:
            if conn, ok := s.connections[id]; ok {
                conn.Close()
                delete(s.connections, id)  // 及时删除
            }
        }
    }
}
```

### 6. 性能监控

#### 使用 pprof

```go
import (
    _ "net/http/pprof"
    "net/http"
)

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    
    // 应用代码
}
```

**使用 pprof**：
```bash
# CPU 性能分析
go tool pprof http://localhost:6060/debug/pprof/profile

# 内存分析
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine 分析
go tool pprof http://localhost:6060/debug/pprof/goroutine
```

#### 使用 trace

```go
func main() {
    f, _ := os.Create("trace.out")
    defer f.Close()
    
    trace.Start(f)
    defer trace.Stop()
    
    // 应用代码
}
```

```bash
# 查看 trace
go tool trace trace.out
```

## ⚠️ 常见陷阱

### 1. 过早优化

**问题**：在没有性能问题的地方花费过多时间优化

**解决方案**：
1. 先确保代码正确
2. 使用性能分析工具找出真正的瓶颈
3. 优化瓶颈部分
4. 用基准测试验证优化效果

### 2. 忽略可读性

**问题**：为了性能牺牲代码可读性

**解决方案**：
- 优先选择清晰、简洁的实现
- 只在性能关键部分使用复杂优化
- 添加详细注释解释优化原理

### 3. 内存泄漏

**常见原因**：
- Goroutine 泄漏
- 未关闭的连接
- 全局变量无限增长
- 循环引用

**解决方案**：
- 使用 pprof 定期检查内存使用
- 及时释放资源（defer、Close）
- 使用 Context 控制 Goroutine 生命周期

### 4. 过度缓存

**问题**：缓存所有数据，导致内存占用过高

**解决方案**：
- 只缓存热点数据
- 设置合理的 TTL
- 使用 LRU 策略限制缓存大小
- 监控缓存命中率

## 🔧 实战示例

### 完整的性能优化方案

```go
type OptimizedPostService struct {
    postRepo   repository.PostRepository
    cache      *Cache
    workerPool *WorkerPool
}

func NewOptimizedPostService(postRepo repository.PostRepository) *OptimizedPostService {
    return &OptimizedPostService{
        postRepo:   postRepo,
        cache:      NewCache(),
        workerPool: NewWorkerPool(10),
    }
}

func (s *OptimizedPostService) GetPostsBatch(ids []uint) ([]*models.Post, error) {
    cacheKeys := make([]string, len(ids))
    for i, id := range ids {
        cacheKeys[i] = fmt.Sprintf("post:%d", id)
    }
    
    results := make([]*models.Post, len(ids))
    var uncachedIndices []int
    var uncachedIDs []uint
    
    for i, key := range cacheKeys {
        if cached, found := s.cache.Get(key); found {
            results[i] = cached.(*models.Post)
        } else {
            uncachedIndices = append(uncachedIndices, i)
            uncachedIDs = append(uncachedIDs, ids[i])
        }
    }
    
    if len(uncachedIDs) > 0 {
        posts, err := s.postRepo.FindByIDs(uncachedIDs)
        if err != nil {
            return nil, err
        }
        
        for i, post := range posts {
            idx := uncachedIndices[i]
            results[idx] = post
            s.cache.Set(cacheKeys[idx], post, 5*time.Minute)
        }
    }
    
    return results, nil
}
```

## ✅ 练习任务

### 任务 1：优化数据库查询

```go
func (r *postRepository) FindPopularPosts(limit int) ([]*models.Post, error) {
    var posts []*models.Post
    
    result := r.db.
        Preload("Author").
        Preload("Comments").
        Order("view_count DESC").
        Limit(limit).
        Find(&posts)
    
    return posts, result.Error
}
```

### 任务 2：实现限流器

```go
type RateLimiter struct {
    requests map[string][]time.Time
    mu       sync.Mutex
    limit    int
    window   time.Duration
}

func (r *RateLimiter) Allow(key string) bool {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    now := time.Now()
    
    if r.requests[key] == nil {
        r.requests[key] = []time.Time{now}
        return true
    }
    
    var validRequests []time.Time
    for _, t := range r.requests[key] {
        if now.Sub(t) < r.window {
            validRequests = append(validRequests, t)
        }
    }
    
    r.requests[key] = validRequests
    
    if len(validRequests) >= r.limit {
        return false
    }
    
    r.requests[key] = append(r.requests[key], now)
    return true
}
```

### 任务 3：编写性能测试

```go
func BenchmarkPostService_GetPost(b *testing.B) {
    service := setupService()
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        service.GetPostByID(1)
    }
}

func BenchmarkWithParallel(b *testing.B) {
    service := setupService()
    
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            service.GetPostByID(1)
        }
    })
}
```

### 任务 4：监控和告警

```go
type PerformanceMonitor struct {
    metrics map[string]int64
    mu      sync.RWMutex
}

func (m *PerformanceMonitor) RecordOperation(name string, duration time.Duration) {
    m.mu.Lock()
    defer m.mu.Unlock()
    
    key := fmt.Sprintf("%s_duration_ms", name)
    m.metrics[key] = duration.Milliseconds()
}

func (m *PerformanceMonitor) GetMetrics() map[string]int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    
    result := make(map[string]int64)
    for k, v := range m.metrics {
        result[k] = v
    }
    return result
}
```

## 📚 延伸阅读

- [Go Performance](https://go.dev/doc/diagnostics)
- [pprof 使用指南](https://github.com/google/pprof)
- [Go 内存管理](https://go.dev/doc/gc-guide)
- [数据库索引优化](https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html)

## 🎯 总结

本课程学习了：
- ✅ 数据库查询优化
- ✅ 连接池配置
- ✅ 并发和异步处理
- ✅ 缓存策略
- ✅ 内存优化技巧
- ✅ 性能分析工具
- ✅ 常见性能陷阱

至此，Go 博客系统的核心功能已经完成！从数据库设计到性能优化，你已经学习了完整的 Go Web 开发流程。