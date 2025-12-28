package service

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/cfrs2005/ppmtest/internal/glm"
)

type GLMService interface {
	GenerateSummary(content string, maxLength int) (string, error)
	GenerateTags(content string, count int) ([]string, error)
	DetectSpamComment(content string) (bool, error)
	GeneratePostContent(topic string) (string, error)
}

type glmService struct {
	client *glm.Client
}

func NewGLMService(client *glm.Client) GLMService {
	return &glmService{
		client: client,
	}
}

func (s *glmService) GenerateSummary(content string, maxLength int) (string, error) {
	if content == "" {
		return "", fmt.Errorf("content cannot be empty")
	}

	summary, err := s.client.SummarizeText(content, maxLength)
	if err != nil {
		return "", fmt.Errorf("failed to generate summary: %w", err)
	}

	return summary, nil
}

func (s *glmService) GenerateTags(content string, count int) ([]string, error) {
	if content == "" {
		return []string{}, fmt.Errorf("content cannot be empty")
	}

	tags, err := s.client.GenerateTags(content, count)
	if err != nil {
		return []string{}, fmt.Errorf("failed to generate tags: %w", err)
	}

	return tags, nil
}

func (s *glmService) DetectSpamComment(content string) (bool, error) {
	if content == "" {
		return false, fmt.Errorf("content cannot be empty")
	}

	isSpam, err := s.client.DetectSpam(content)
	if err != nil {
		return false, fmt.Errorf("failed to detect spam: %w", err)
	}

	return isSpam, nil
}

func (s *glmService) GeneratePostContent(topic string) (string, error) {
	if topic == "" {
		return "", fmt.Errorf("topic cannot be empty")
	}

	prompt := fmt.Sprintf("请写一篇关于\"%s\"的技术博客，要求：\n1. 内容专业且易懂\n2. 包含代码示例\n3. 字数在500-1000字之间", topic)

	content, err := s.client.GenerateContent(prompt)
	if err != nil {
		return "", fmt.Errorf("failed to generate post content: %w", err)
	}

	return content, nil
}

type AsyncGLMService struct {
	client   *glm.Client
	taskChan chan GLMTask
	wg       sync.WaitGroup
	ctx      context.Context
	cancel   context.CancelFunc
}

type GLMTask struct {
	ID     string
	Type   string
	Input  interface{}
	Result chan<- TaskResult
}

type TaskResult struct {
	ID    string
	Data  interface{}
	Error error
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
		service.wg.Add(1)
		go service.worker(i)
	}

	log.Printf("Started %d GLM workers", workers)

	return service
}

func (s *AsyncGLMService) worker(id int) {
	defer s.wg.Done()

	for {
		select {
		case <-s.ctx.Done():
			log.Printf("GLM worker %d stopping", id)
			return
		case task := <-s.taskChan:
			s.processTask(task, id)
		}
	}
}

func (s *AsyncGLMService) processTask(task GLMTask, workerID int) {
	startTime := time.Now()
	
	log.Printf("[Worker %d] Processing task %s (type: %s)", workerID, task.ID, task.Type)

	var result TaskResult
	result.ID = task.ID

	switch task.Type {
	case "summary":
		input := task.Input.(SummaryInput)
		data, err := s.client.SummarizeText(input.Content, input.MaxLength)
		result.Data = data
		result.Error = err
		
	case "tags":
		input := task.Input.(TagsInput)
		data, err := s.client.GenerateTags(input.Content, input.Count)
		result.Data = data
		result.Error = err
		
	case "spam":
		input := task.Input.(SpamInput)
		data, err := s.client.DetectSpam(input.Content)
		result.Data = data
		result.Error = err
		
	default:
		result.Error = fmt.Errorf("unknown task type: %s", task.Type)
	}

	duration := time.Since(startTime)
	
	if result.Error != nil {
		log.Printf("[Worker %d] Task %s failed after %v: %v", workerID, task.ID, duration, result.Error)
	} else {
		log.Printf("[Worker %d] Task %s completed in %v", workerID, task.ID, duration)
	}

	select {
	case task.Result <- result:
	case <-time.After(5 * time.Second):
		log.Printf("[Worker %d] Task %s result channel timeout", workerID, task.ID)
	}
}

type SummaryInput struct {
	Content   string
	MaxLength int
}

type TagsInput struct {
	Content string
	Count   int
}

type SpamInput struct {
	Content string
}

func (s *AsyncGLMService) SubmitSummary(taskID string, content string, maxLength int, resultChan chan<- TaskResult) {
	select {
	case s.taskChan <- GLMTask{
		ID:     taskID,
		Type:   "summary",
		Input:  SummaryInput{Content: content, MaxLength: maxLength},
		Result: resultChan,
	}:
	case <-s.ctx.Done():
		resultChan <- TaskResult{ID: taskID, Error: fmt.Errorf("service is shutting down")}
	}
}

func (s *AsyncGLMService) SubmitTags(taskID string, content string, count int, resultChan chan<- TaskResult) {
	select {
	case s.taskChan <- GLMTask{
		ID:     taskID,
		Type:   "tags",
		Input:  TagsInput{Content: content, Count: count},
		Result: resultChan,
	}:
	case <-s.ctx.Done():
		resultChan <- TaskResult{ID: taskID, Error: fmt.Errorf("service is shutting down")}
	}
}

func (s *AsyncGLMService) SubmitSpamCheck(taskID string, content string, resultChan chan<- TaskResult) {
	select {
	case s.taskChan <- GLMTask{
		ID:     taskID,
		Type:   "spam",
		Input:  SpamInput{Content: content},
		Result: resultChan,
	}:
	case <-s.ctx.Done():
		resultChan <- TaskResult{ID: taskID, Error: fmt.Errorf("service is shutting down")}
	}
}

func (s *AsyncGLMService) Shutdown() {
	log.Println("Shutting down GLM service...")
	
	s.cancel()
	close(s.taskChan)
	
	done := make(chan struct{})
	go func() {
		s.wg.Wait()
		close(done)
	}()
	
	select {
	case <-done:
		log.Println("GLM service shutdown complete")
	case <-time.After(30 * time.Second):
		log.Println("GLM service shutdown timeout")
	}
}