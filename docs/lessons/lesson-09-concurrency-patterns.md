# Lesson 09: 并发编程模式

## 目录
- [Goroutine 基础](#goroutine-基础)
- [Channel 模式](#channel-模式)
- [并发模式](#并发模式)
- [Context 使用](#context-使用)
- [同步原语](#同步原语)
- [常见陷阱](#常见陷阱)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)

---

## Goroutine 基础

### 1. 启动 Goroutine

```go
// 基本用法
func sayHello(name string) {
    fmt.Printf("Hello, %s!\n", name)
}

func main() {
    go sayHello("Alice")  // 启动 goroutine
    go sayHello("Bob")
    
    time.Sleep(time.Second)  // 等待 goroutine 完成
}
```

### 2. 匿名 Goroutine

```go
func main() {
    go func() {
        fmt.Println("Anonymous goroutine")
    }()
    
    time.Sleep(time.Second)
}
```

### 3. 带参数的 Goroutine

```go
func main() {
    name := "Alice"
    go func(n string) {
        fmt.Printf("Hello, %s\n", n)
    }(name)  // 传递参数
    
    time.Sleep(time.Second)
}
```

### 4. WaitGroup 等待

```go
import "sync"

func process(id int, wg *sync.WaitGroup) {
    defer wg.Done()  // 完成时调用
    fmt.Printf("Processing %d\n", id)
    time.Sleep(time.Second)
}

func main() {
    var wg sync.WaitGroup
    
    for i := 1; i <= 5; i++ {
        wg.Add(1)  // 增加计数
        go process(i, &wg)
    }
    
    wg.Wait()  // 等待所有 goroutine 完成
    fmt.Println("All done!")
}
```

---

## Channel 模式

### 1. 基本 Channel

```go
// 创建 channel
ch := make(chan int)

// 发送
ch <- 42

// 接收
value := <-ch

// 关闭
close(ch)
```

### 2. 缓冲 Channel

```go
// 缓冲大小为 3
ch := make(chan int, 3)

ch <- 1  // 不会阻塞
ch <- 2
ch <- 3

// ch <- 4  // 会阻塞，因为缓冲区已满
```

### 3. 单向 Channel

```go
// 只发送
func sender(ch chan<- int) {
    ch <- 42
}

// 只接收
func receiver(ch <-chan int) {
    value := <-ch
    fmt.Println(value)
}

func main() {
    ch := make(chan int)
    go sender(ch)
    receiver(ch)
}
```

### 4. Select 语句

```go
func selectExample() {
    ch1 := make(chan int)
    ch2 := make(chan string)
    
    go func() {
        time.Sleep(100 * time.Millisecond)
        ch1 <- 42
    }()
    
    go func() {
        time.Sleep(200 * time.Millisecond)
        ch2 <- "hello"
    }()
    
    for i := 0; i < 2; i++ {
        select {
        case value := <-ch1:
            fmt.Println("Received from ch1:", value)
        case value := <-ch2:
            fmt.Println("Received from ch2:", value)
        case <-time.After(500 * time.Millisecond):
            fmt.Println("Timeout!")
        }
    }
}
```

### 5. 超时模式

```go
func withTimeout(c chan int, timeout time.Duration) (int, error) {
    select {
    case value := <-c:
        return value, nil
    case <-time.After(timeout):
        return 0, errors.New("timeout")
    }
}
```

---

## 并发模式

### 1. Worker Pool

```go
type Task struct {
    ID   int
    Data string
}

func worker(id int, tasks <-chan Task, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for task := range tasks {
        fmt.Printf("Worker %d processing task %d\n", id, task.ID)
        time.Sleep(time.Second)
        results <- task.ID * 2
    }
}

func main() {
    tasks := make(chan Task, 100)
    results := make(chan int, 100)
    
    var wg sync.WaitGroup
    
    // 启动 5 个 worker
    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go worker(i, tasks, results, &wg)
    }
    
    // 发送任务
    for i := 1; i <= 10; i++ {
        tasks <- Task{ID: i}
    }
    close(tasks)
    
    // 等待所有 worker 完成
    go func() {
        wg.Wait()
        close(results)
    }()
    
    // 收集结果
    for result := range results {
        fmt.Println("Result:", result)
    }
}
```

### 2. Pipeline 模式

```go
// 第一步：生成数字
func generator(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

// 第二步：平方
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// 第三步：打印
func print(in <-chan int) {
    for n := range in {
        fmt.Println(n)
    }
}

func main() {
    // Pipeline: generator -> square -> print
    numbers := generator(1, 2, 3, 4, 5)
    squares := square(numbers)
    print(squares)
}
```

### 3. Fan-Out/Fan-In

```go
// Fan-out: 分发任务到多个 worker
func fanOut(in <-chan int, workers int) []<-chan int {
    outs := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        outs[i] = worker(in)
    }
    return outs
}

func worker(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * 2
        }
        close(out)
    }()
    return out
}

// Fan-in: 合并多个 channel
func fanIn(ins ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    
    for _, in := range ins {
        wg.Add(1)
        go func(ch <-chan int) {
            defer wg.Done()
            for n := range ch {
                out <- n
            }
        }(in)
    }
    
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}

func main() {
    in := make(chan int)
    
    // 发送数据
    go func() {
        for i := 1; i <= 10; i++ {
            in <- i
        }
        close(in)
    }()
    
    // Fan-out 到 3 个 worker
    outs := fanOut(in, 3)
    
    // Fan-in 合并结果
    out := fanIn(outs...)
    
    for result := range out {
        fmt.Println(result)
    }
}
```

### 4. Or-Done Channel

```go
// 或是任意一个 channel 完成就退出
func orDone(ch <-chan int, done <-chan struct{}) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        select {
        case v, ok := <-ch:
            if !ok {
                return
            }
            out <- v
        case <-done:
            return
        }
    }()
    return out
}
```

### 5. Tee Channel

```go
// 将一个 channel 的数据发送到多个 channel
func tee(in <-chan int) (_, _ <-chan int) {
    out1 := make(chan int)
    out2 := make(chan int)
    
    go func() {
        defer close(out1)
        defer close(out2)
        for val := range in {
            out1 <- val
            out2 <- val
        }
    }()
    
    return out1, out2
}
```

---

## Context 使用

### 1. Context 基础

```go
func doWork(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("Work cancelled:", ctx.Err())
            return
        default:
            fmt.Println("Working...")
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    
    go doWork(ctx)
    
    time.Sleep(2 * time.Second)
    cancel()  // 取消操作
    time.Sleep(time.Second)
}
```

### 2. 超时 Context

```go
func withTimeout() error {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    ch := make(chan string)
    go func() {
        time.Sleep(3 * time.Second)  // 模拟长时间操作
        ch <- "result"
    }()
    
    select {
    case result := <-ch:
        fmt.Println("Result:", result)
        return nil
    case <-ctx.Done():
        return errors.New("operation timed out")
    }
}
```

### 3. 值传递

```go
type contextKey string

const userIDKey contextKey = "userID"

func withValue() {
    ctx := context.WithValue(context.Background(), userIDKey, 123)
    
    processRequest(ctx)
}

func processRequest(ctx context.Context) {
    userID := ctx.Value(userIDKey)
    fmt.Println("User ID:", userID)
}
```

### 4. HTTP Context

```go
func handler(w http.ResponseWriter, r *http.Request) {
    // 从请求创建带超时的 context
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()
    
    // 调用外部服务
    result, err := externalService(ctx)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    fmt.Fprintf(w, "Result: %v", result)
}
```

---

## 同步原语

### 1. Mutex

```go
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Count() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}
```

### 2. RWMutex

```go
type SafeMap struct {
    mu   sync.RWMutex
    data map[string]int
}

func (m *SafeMap) Get(key string) (int, bool) {
    m.mu.RLock()  // 读锁
    defer m.mu.RUnlock()
    val, ok := m.data[key]
    return val, ok
}

func (m *SafeMap) Set(key string, val int) {
    m.mu.Lock()  // 写锁
    defer m.mu.Unlock()
    m.data[key] = val
}
```

### 3. Once

```go
var (
    instance *Database
    once     sync.Once
)

func GetDatabase() *Database {
    once.Do(func() {  // 只执行一次
        instance = &Database{}
    })
    return instance
}
```

### 4. Cond

```go
type Queue struct {
    items []int
    cond  *sync.Cond
}

func NewQueue() *Queue {
    return &Queue{
        cond: sync.NewCond(&sync.Mutex{}),
    }
}

func (q *Queue) Push(item int) {
    q.cond.L.Lock()
    defer q.cond.L.Unlock()
    
    q.items = append(q.items, item)
    q.cond.Signal()  // 通知一个等待的 goroutine
}

func (q *Queue) Pop() int {
    q.cond.L.Lock()
    defer q.cond.L.Unlock()
    
    for len(q.items) == 0 {
        q.cond.Wait()  // 等待通知
    }
    
    item := q.items[0]
    q.items = q.items[1:]
    return item
}
```

### 5. Pool

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processData(data string) string {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufferPool.Put(buf)
    }()
    
    buf.WriteString("Processed: ")
    buf.WriteString(data)
    return buf.String()
}
```

---

## 常见陷阱

### 1. Goroutine 泄漏

```go
// ❌ 不好：goroutine 泄漏
func leak() {
    ch := make(chan int)
    go func() {
        val := <-ch  // 永远阻塞
        fmt.Println(val)
    }()
    // 如果 ch 永远不发送数据，goroutine 会一直存在
}

// ✅ 好：使用 context 或缓冲 channel
func noLeak(ctx context.Context) {
    ch := make(chan int)
    go func() {
        select {
        case val := <-ch:
            fmt.Println(val)
        case <-ctx.Done():
            return  // 正常退出
        }
    }()
}
```

### 2. 数据竞争

```go
// ❌ 不好：数据竞争
func race() {
    var counter int
    for i := 0; i < 1000; i++ {
        go func() {
            counter++  // 数据竞争
        }()
    }
}

// ✅ 好：使用 Mutex
func noRace() {
    var counter int
    var mu sync.Mutex
    
    for i := 0; i < 1000; i++ {
        go func() {
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }
}

// ✅ 更好：使用 atomic
func noRaceAtomic() {
    var counter int64
    for i := 0; i < 1000; i++ {
        go func() {
            atomic.AddInt64(&counter, 1)
        }()
    }
}
```

### 3. 闭包捕获

```go
// ❌ 不好：错误的闭包捕获
func badClosure() {
    for i := 0; i < 5; i++ {
        go func() {
            fmt.Println(i)  // 可能都打印 5
        }()
    }
}

// ✅ 好：正确传递参数
func goodClosure() {
    for i := 0; i < 5; i++ {
        go func(n int) {
            fmt.Println(n)
        }(i)
    }
}
```

### 4. 忘记关闭 Channel

```go
// ❌ 不好：可能导致死锁
func producer(ch chan int) {
    for i := 0; i < 5; i++ {
        ch <- i
    }
    // 忘记 close(ch)
}

// ✅ 好：记得关闭
func producer(ch chan int) {
    for i := 0; i < 5; i++ {
        ch <- i
    }
    close(ch)  // 重要：让接收方知道没有更多数据
}
```

### 5. 向已关闭的 Channel 发送

```go
// ❌ 不好：向已关闭的 channel 发送会 panic
func badSend() {
    ch := make(chan int, 1)
    close(ch)
    ch <- 1  // panic
}

// ✅ 好：使用 select 和 comma-ok
func safeSend(ch chan int, value int) {
    select {
    case ch <- value:
        // 发送成功
    default:
        // channel 已关闭或缓冲区满
    }
}
```

---

## 最佳实践

### 1. 限制并发数

```go
func limitConcurrency() {
    maxConcurrent := 10
    semaphore := make(chan struct{}, maxConcurrent)
    
    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        semaphore <- struct{}{}  // 获取信号量
        
        go func(id int) {
            defer wg.Done()
            defer func() { <-semaphore }()  // 释放信号量
            
            // 执行任务
            process(id)
        }(i)
    }
    
    wg.Wait()
}
```

### 2. 使用 errgroup

```go
import "golang.org/x/sync/errgroup"

func processWithErrGroup(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)
    
    urls := []string{"url1", "url2", "url3"}
    
    for _, url := range urls {
        url := url  // 闭包捕获
        g.Go(func() error {
            return fetchURL(ctx, url)
        })
    }
    
    return g.Wait()
}
```

### 3. 优雅关闭

```go
type Server struct {
    httpServer *http.Server
    shutdownCh chan struct{}
}

func (s *Server) Start() error {
    go func() {
        <-s.shutdownCh
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        s.httpServer.Shutdown(ctx)
    }()
    
    return s.httpServer.ListenAndServe()
}

func (s *Server) Shutdown() {
    close(s.shutdownCh)
}
```

### 4. 使用 singleflight

```go
import "golang.org/x/sync/singleflight"

var sf singleflight.Group

func getData(key string) (string, error) {
    result, err, shared := sf.Do(key, func() (interface{}, error) {
        // 只会有一个 goroutine 执行这里
        return fetchFromDB(key)
    })
    
    if err != nil {
        return "", err
    }
    
    if shared {
        fmt.Println("Shared result")
    }
    
    return result.(string), nil
}
```

### 5. 监控 Goroutine

```go
func monitorGoroutines() {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        count := runtime.NumGoroutine()
        fmt.Printf("Active goroutines: %d\n", count)
        
        if count > 1000 {
            log.Printf("WARNING: Too many goroutines: %d", count)
        }
    }
}
```

---

## 注意事项

### 1. 不要通过共享内存通信

```go
// ❌ 不好：通过共享内存通信
func badCommunication() {
    var data int
    var mu sync.Mutex
    
    go func() {
        mu.Lock()
        data = 42
        mu.Unlock()
    }()
    
    mu.Lock()
    if data == 42 {
        // 使用 data
    }
    mu.Unlock()
}

// ✅ 好：通过 channel 通信
func goodCommunication() {
    ch := make(chan int)
    
    go func() {
        ch <- 42
    }()
    
    data := <-ch
    // 使用 data
}
```

### 2. 避免使用大缓冲 Channel

```go
// ❌ 不好：大缓冲可能掩盖问题
ch := make(chan int, 100000)

// ✅ 好：使用合理的缓冲或无缓冲
ch := make(chan int)  // 无缓冲，强制同步
```

### 3. 注意 Context 值传递的性能

```go
// ✅ 使用自定义类型作为 key
type contextKey string
const userIDKey contextKey = "userID"

// ❌ 不要使用内置类型
// const userIDKey = "userID"  // 可能冲突
```

---

## 实战案例：博客系统并发处理

### 并发文章处理

```go
package service

type PostProcessor struct {
    repo      PostRepository
    cache     Cache
    indexer   SearchIndexer
    notifier  Notifier
}

func (p *PostProcessor) ProcessPost(ctx context.Context, postID int64) error {
    // 并发执行多个任务
    g, ctx := errgroup.WithContext(ctx)
    
    // 任务 1: 获取文章
    var post *Post
    g.Go(func() error {
        var err error
        post, err = p.repo.FindByID(postID)
        return err
    })
    
    // 任务 2: 检查缓存
    var cached bool
    g.Go(func() error {
        key := fmt.Sprintf("post:%d", postID)
        _, err := p.cache.Get(ctx, key)
        cached = (err == nil)
        return nil
    })
    
    if err := g.Wait(); err != nil {
        return err
    }
    
    // 后续处理...
    return nil
}
```

### 批量文章索引

```go
func (p *PostProcessor) ReindexAll(ctx context.Context) error {
    const batchSize = 100
    const workers = 10
    
    // 创建 worker pool
    sem := make(chan struct{}, workers)
    
    var wg sync.WaitGroup
    errCh := make(chan error, 1)
    
    offset := 0
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }
        
        // 批量获取文章
        posts, err := p.repo.FindBatch(offset, batchSize)
        if err != nil {
            return err
        }
        
        if len(posts) == 0 {
            break
        }
        
        // 并发索引
        for _, post := range posts {
            wg.Add(1)
            sem <- struct{}{}  // 获取信号量
            
            go func(post *Post) {
                defer wg.Done()
                defer func() { <-sem }()  // 释放信号量
                
                if err := p.indexer.Index(post); err != nil {
                    select {
                    case errCh <- fmt.Errorf("index post %d: %w", post.ID, err):
                    default:
                    }
                }
            }(post)
        }
        
        offset += batchSize
    }
    
    // 等待所有索引完成
    wg.Wait()
    close(errCh)
    
    // 检查是否有错误
    if err := <-errCh; err != nil {
        return err
    }
    
    return nil
}
```

---

## 总结

Go 的并发是其最强大的特性之一：

### 关键要点

- ✅ 使用 goroutine 执行并发任务
- ✅ 使用 channel 进行通信
- ✅ 使用 WaitGroup 等待 goroutine
- ✅ 使用 context 管理生命周期
- ✅ 使用 Mutex/RWMutex 保护共享数据
- ✅ 避免并发陷阱（泄漏、竞争、死锁）
- ✅ 使用 errgroup 管理多个 goroutine
- ✅ 限制并发数，避免资源耗尽
- ✅ 监控 goroutine 数量
- ✅ 优雅关闭服务
- ✅ 通过通信共享内存，不要通过共享内存通信

### 学习路径

至此，你已经完成了所有 9 个课程的学习！你已经掌握了：

1. ✅ 数据库设计基础
2. ✅ 服务层架构设计
3. ✅ Web 框架最佳实践
4. ✅ 中间件模式
5. ✅ 错误处理策略
6. ✅ 测试最佳实践
7. ✅ 性能优化技巧
8. ✅ 安全实践
9. ✅ 并发编程模式

继续在实践中应用这些知识，构建高质量的 Go 应用！
