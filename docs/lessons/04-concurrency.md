# Lesson 04: Go 并发编程实战

## 📖 概念解释

### 1. Goroutine（协程）

Goroutine 是 Go 实现并发的核心，它是轻量级的线程：
- **轻量级**：初始栈大小仅 2KB，可动态扩展
- **高效调度**：Go 运行时使用 M:N 调度器
- **简单创建**：只需 `go` 关键字

### 2. Channel（通道）

Channel 是 Goroutine 之间通信的管道：
- **类型安全**：Channel 有明确的类型
- **阻塞操作**：发送和接收会阻塞，直到有对应的操作
- **内置同步**：Channel 提供了同步机制

### 3. Context（上下文）

Context 用于在 Goroutine 之间传递取消信号、超时和截止时间：
- **取消传播**：可以取消一组相关的 Goroutine
- **超时控制**：设置操作的超时时间
- **值传递**：在调用链中传递请求范围的值

## 💡 最佳实践

### 1. 创建 Goroutine

```go
func processTask(taskID string) {
    fmt.Printf("Processing task %s\n", taskID)
}

func main() {
    // 启动一个 Goroutine
    go processTask("task-1")
    
    // 等待 Goroutine 完成
    time.Sleep(1 * time.Second)
}
```

**最佳实践**：
- 使用 `sync.WaitGroup` 等待多个 Goroutine
- 避免在 Goroutine 中直接使用外部变量（应该作为参数传递）

### 2. 使用 WaitGroup

```go
var wg sync.WaitGroup

for i := 0; i < 5; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        fmt.Printf("Worker %d working\n", id)
        time.Sleep(time.Second)
    }(i)
}

wg.Wait()
fmt.Println("All workers completed")
```

**WaitGroup 使用要点**：
- 在启动 Goroutine 前调用 `Add(1)`
- 在 Goroutine 结束时调用 `Done()`
- 在主 Goroutine 中调用 `Wait()` 等待

### 3. Channel 通信

```go
func producer(ch chan<- int) {
    for i := 0; i < 5; i++ {
        ch <- i
        time.Sleep(100 * time.Millisecond)
    }
    close(ch)
}

func consumer(ch <-chan int) {
    for value := range ch {
        fmt.Printf("Received: %d\n", value)
    }
}

func main() {
    ch := make(chan int, 3)
    
    go producer(ch)
    consumer(ch)
}
```

**Channel 使用要点**：
- 使用带缓冲的 Channel 提高性能：`make(chan int, 10)`
- 发送端负责关闭 Channel
- 使用 `range` 遍历 Channel，自动检测关闭

### 4. Context 使用

```go
func worker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d stopped: %v\n", id, ctx.Err())
            return
        default:
            fmt.Printf("Worker %d working\n", id)
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    for i := 0; i < 3; i++ {
        go worker(ctx, i)
    }
    
    time.Sleep(3 * time.Second)
    fmt.Println("Main completed")
}
```

**Context 使用要点**：
- 使用 `context.WithTimeout` 设置超时
- 使用 `context.WithCancel` 手动取消
- 在 Goroutine 中使用 `select` 监听 `ctx.Done()`
- 始终调用 `cancel()` 释放资源

### 5. Worker Pool 模式

```go
func worker(id int, jobs <-chan Task, results chan<- Result) {
    for job := range jobs {
        fmt.Printf("Worker %d processing job %s\n", id, job.ID)
        result := processJob(job)
        results <- result
    }
}

func main() {
    jobs := make(chan Task, 100)
    results := make(chan Result, 100)
    
    for i := 0; i < 5; i++ {
        go worker(i, jobs, results)
    }
    
    go func() {
        for _, job := range tasks {
            jobs <- job
        }
        close(jobs)
    }()
    
    for i := 0; i < len(tasks); i++ {
        result := <-results
        fmt.Printf("Job %s completed\n", result.ID)
    }
}
```

**Worker Pool 优势**：
- 限制并发数量，避免资源耗尽
- 复用 Goroutine，减少创建开销
- 通过 Channel 传递任务和结果

## ⚠️ 常见陷阱

### 1. Goroutine 泄漏

**问题代码**：
```go
func queryDatabase() {
    rows, _ := db.Query("SELECT * FROM users")
    defer rows.Close()
    
    for rows.Next() {
        go func() {
            // 处理每一行
        }()
    }
}
```

**问题**：如果查询返回大量数据，会创建过多 Goroutine

**解决方案**：
```go
func queryDatabase() {
    rows, _ := db.Query("SELECT * FROM users")
    defer rows.Close()
    
    sem := make(chan struct{}, 10)  // 限制并发数
    
    for rows.Next() {
        sem <- struct{}{}
        go func() {
            defer func() { <-sem }()
            // 处理每一行
        }()
    }
}
```

### 2. 忘略错误处理

**问题代码**：
```go
go func() {
    result, err := processData()
    // 没有处理错误
}()
```

**解决方案 - 使用错误 Channel**：
```go
errCh := make(chan error, 1)
go func() {
    result, err := processData()
    if err != nil {
        errCh <- err
        return
    }
    resultCh <- result
}()

select {
case err := <-errCh:
    return err
case result := <-resultCh:
    return result
}
```

### 3. 数据竞争（Data Race）

**问题代码**：
```go
var counter int

for i := 0; i < 1000; i++ {
    go func() {
        counter++  // 数据竞争
    }()
}
```

**解决方案 - 使用互斥锁**：
```go
var (
    counter int
    mu      sync.Mutex
)

for i := 0; i < 1000; i++ {
    go func() {
        mu.Lock()
        counter++
        mu.Unlock()
    }()
}
```

或者使用 `sync/atomic`：
```go
var counter int64

for i := 0; i < 1000; i++ {
    go func() {
        atomic.AddInt64(&counter, 1)
    }()
}
```

### 4. 阻塞在 Channel 上

**问题代码**：
```go
ch := make(chan int)
ch <- 1  // 如果没有接收者，会永远阻塞
```

**解决方案**：
```go
// 方案1：使用带缓冲的 Channel
ch := make(chan int, 1)
ch <- 1

// 方案2：使用 select
select {
case ch <- 1:
    fmt.Println("Sent")
default:
    fmt.Println("Channel full")
}

// 方案3：使用超时
select {
case ch <- 1:
    fmt.Println("Sent")
case <-time.After(time.Second):
    fmt.Println("Timeout")
}
```

### 5. 不正确地使用 Context

**问题**：没有检查 Context 的错误

```go
func doWork(ctx context.Context) error {
    result := make(chan string)
    
    go func() {
        result <- slowOperation()
    }()
    
    select {
    case res := <-result:
        fmt.Println(res)
        return nil
    case <-ctx.Done():
        return ctx.Err()  // 返回上下文取消的错误
    }
}
```

## 🔧 实战示例

### 异步 GLM 服务实现

参考 `internal/service/glm_service.go` 中的 `AsyncGLMService` 实现：

1. **Worker Pool**：多个 Goroutine 处理任务
2. **Channel 通信**：任务和结果通过 Channel 传递
3. **Context 控制**：优雅关闭所有 Worker
4. **错误处理**：每个任务的结果包含错误信息

```go
type AsyncGLMService struct {
    client   *glm.Client
    taskChan chan GLMTask
    ctx      context.Context
    cancel   context.CancelFunc
}

func NewAsyncGLMService(client *glm.Client, workers int) *AsyncGLMService {
    ctx, cancel := context.WithCancel(context.Background())
    
    service := &AsyncGLMService{
        client:   client,
        taskChan: make(chan GLMTask, 100),
        ctx:      ctx,
        cancel:   cancel,
    }
    
    for i := 0; i < workers; i++ {
        go service.worker(i)
    }
    
    return service
}
```

### 使用示例

```go
glmService := NewAsyncGLMService(client, 5)
defer glmService.Shutdown()

resultChan := make(chan TaskResult, 1)
glmService.SubmitSummary("task-1", "long content...", 200, resultChan)

select {
case result := <-resultChan:
    if result.Error != nil {
        log.Printf("Task failed: %v", result.Error)
    } else {
        summary := result.Data.(string)
        fmt.Printf("Summary: %s\n", summary)
    }
case <-time.After(10 * time.Second):
    log.Println("Task timeout")
}
```

## ✅ 练习任务

### 任务 1：实现并发限流器

```go
type RateLimiter struct {
    semaphore chan struct{}
}

func NewRateLimiter(maxConcurrent int) *RateLimiter {
    return &RateLimiter{
        semaphore: make(chan struct{}, maxConcurrent),
    }
}

func (r *RateLimiter) Acquire() {
    r.semaphore <- struct{}{}
}

func (r *RateLimiter) Release() {
    <-r.semaphore
}
```

### 任务 2：实现管道（Pipeline）模式

```go
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

func main() {
    for n := range square(generator(1, 2, 3, 4, 5)) {
        fmt.Println(n)
    }
}
```

### 任务 3：实现超时重试机制

```go
func WithRetry(ctx context.Context, maxRetries int, fn func() error) error {
    for i := 0; i < maxRetries; i++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(time.Second * time.Duration(i+1)):
        }
    }
    return fmt.Errorf("max retries exceeded")
}
```

### 任务 4：实现 Fan-Out/Fan-In 模式

```go
func fanOut(input <-chan int, workers int) []<-chan int {
    outputs := make([]<-chan int, workers)
    
    for i := 0; i < workers; i++ {
        outputs[i] = worker(input)
    }
    
    return outputs
}

func fanIn(inputs ...<-chan int) <-chan int {
    out := make(chan int)
    
    var wg sync.WaitGroup
    for _, ch := range inputs {
        wg.Add(1)
        go func(c <-chan int) {
            for n := range c {
                out <- n
            }
            wg.Done()
        }(ch)
    }
    
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}
```

## 📚 延伸阅读

- [Go 并发编程实战](https://go.dev/doc/effective_go#concurrency)
- [Context 包详解](https://go.dev/blog/context)
- [Channel 使用指南](https://go.dev/ref/spec#Channel_types)
- [Go 内存模型](https://go.dev/ref/mem)

## 🎯 总结

本课程学习了：
- ✅ Goroutine 的创建和使用
- ✅ Channel 通信模式
- ✅ Context 的使用场景
- ✅ Worker Pool 模式
- ✅ 常见的并发陷阱和解决方案
- ✅ 异步任务处理实战

下一步：学习测试策略和技巧（Lesson 05）