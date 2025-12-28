package glm

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

var (
	ErrAPIKeyRequired    = errors.New("GLM API key is required")
	ErrRequestFailed     = errors.New("GLM API request failed")
	ErrInvalidResponse   = errors.New("invalid GLM API response")
	ErrRateLimitExceeded = errors.New("GLM API rate limit exceeded")
)

type Client struct {
	apiKey      string
	baseURL     string
	model       string
	maxTokens   int
	temperature float64
	httpClient  *http.Client
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type Request struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Temperature float64   `json:"temperature,omitempty"`
}

type Response struct {
	ID      string   `json:"id"`
	Object  string   `json:"object"`
	Created int64    `json:"created"`
	Model   string   `json:"model"`
	Choices []struct {
		Index   int     `json:"index"`
		Message Message `json:"message"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

type ErrorResponse struct {
	Error struct {
		Message string `json:"message"`
		Type    string `json:"type"`
		Code    string `json:"code"`
	} `json:"error"`
}

func NewClient(apiKey, baseURL, model string, maxTokens int, temperature float64) (*Client, error) {
	if apiKey == "" {
		return nil, ErrAPIKeyRequired
	}

	if baseURL == "" {
		baseURL = "https://open.bigmodel.cn/api/paas/v4"
	}

	if model == "" {
		model = "glm-4"
	}

	return &Client{
		apiKey:      apiKey,
		baseURL:     baseURL,
		model:       model,
		maxTokens:   maxTokens,
		temperature: temperature,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}, nil
}

func (c *Client) GenerateContent(prompt string) (string, error) {
	if prompt == "" {
		return "", errors.New("prompt cannot be empty")
	}

	req := Request{
		Model: c.model,
		Messages: []Message{
			{
				Role:    "user",
				Content: prompt,
			},
		},
		MaxTokens:   c.maxTokens,
		Temperature: c.temperature,
	}

	resp, err := c.doRequest("/chat/completions", req)
	if err != nil {
		return "", err
	}

	if len(resp.Choices) == 0 {
		return "", ErrInvalidResponse
	}

	return resp.Choices[0].Message.Content, nil
}

func (c *Client) SummarizeText(text string, maxLength int) (string, error) {
	prompt := fmt.Sprintf("请用中文总结以下内容，最多 %d 个字：\n\n%s", maxLength, text)
	return c.GenerateContent(prompt)
}

func (c *Client) GenerateTags(content string, count int) ([]string, error) {
	prompt := fmt.Sprintf("根据以下内容生成 %d 个相关的标签，用逗号分隔：\n\n%s", count, content)
	
	response, err := c.GenerateContent(prompt)
	if err != nil {
		return nil, err
	}

	tags := parseTags(response)
	if len(tags) > count {
		tags = tags[:count]
	}

	return tags, nil
}

func (c *Client) DetectSpam(content string) (bool, error) {
	prompt := fmt.Sprintf("判断以下内容是否为垃圾评论，只回答\"是\"或\"否\"：\n\n%s", content)
	
	response, err := c.GenerateContent(prompt)
	if err != nil {
		return false, err
	}

	return containsSpamKeywords(response), nil
}

func (c *Client) doRequest(endpoint string, req interface{}) (*Response, error) {
	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	url := c.baseURL + endpoint
	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer httpResp.Body.Close()

	body, err := io.ReadAll(httpResp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if httpResp.StatusCode != http.StatusOK {
		var errResp ErrorResponse
		if err := json.Unmarshal(body, &errResp); err == nil {
			if httpResp.StatusCode == http.StatusTooManyRequests {
				return nil, ErrRateLimitExceeded
			}
			return nil, fmt.Errorf("%w: %s", ErrRequestFailed, errResp.Error.Message)
		}
		return nil, fmt.Errorf("%w: status %d", ErrRequestFailed, httpResp.StatusCode)
	}

	var resp Response
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &resp, nil
}

func parseTags(text string) []string {
	var tags []string
	for _, tag := range splitByComma(text) {
		tag := trimSpace(tag)
		if tag != "" {
			tags = append(tags, tag)
		}
	}
	return tags
}

func splitByComma(s string) []string {
	var result []string
	current := ""
	
	for _, ch := range s {
		if ch == ',' || ch == '，' {
			result = append(result, current)
			current = ""
		} else {
			current += string(ch)
		}
	}
	
	if current != "" {
		result = append(result, current)
	}
	
	return result
}

func trimSpace(s string) string {
	start := 0
	end := len(s)
	
	for start < end && (s[start] == ' ' || s[start] == '\t' || s[start] == '\n') {
		start++
	}
	
	for end > start && (s[end-1] == ' ' || s[end-1] == '\t' || s[end-1] == '\n') {
		end--
	}
	
	return s[start:end]
}

func containsSpamKeywords(text string) bool {
	spamKeywords := []string{"是", "垃圾", "spam", "广告"}
	
	for _, keyword := range spamKeywords {
		if contains(text, keyword) {
			return true
		}
	}
	
	return false
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && findSubstring(s, substr)
}

func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}